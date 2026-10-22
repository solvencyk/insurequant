"""JOB 2 simulation (read-only): PL_OCI_VS_BS_AOCI counting, current vs corrected, over every bucket,
for the working tree and for the masters at each commit of the latest-comparative loads.

  python sim_oci_counting.py > sim_oci_counting.txt

For each state: universe (item-25 buckets), blank (값_당분기 None), bs_missing, compared, flagged,
comparable-within-tol as the gate prints it today (len(pl_dangi) - n_skip - flagged) vs corrected
(compared - flagged).  Asserts the flagged set is identical under both countings (the fix must not
change which real mismatches are flagged).  Then, between consecutive states, lists YELLOW rows that
disappeared and whether the cell is blank in the later state (disappeared only because it went blank).
Also a SHADOW estimate (informational only, not a gate input): blank cells re-derived as
YTD(q) - YTD(prev q in the same FY), to show what the blanks are hiding.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_master_tables as V  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COMMITS = ["b8c37fff", "3e53aef8", "5f818b59", "e01f1395", "59e6e459", "acdb2fe9", "5419a817", "afea4342", "WORKTREE"]


def load_rows(commit: str, path: str):
    if commit == "WORKTREE":
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    raw = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, check=True).stdout
    return json.loads(raw.decode("utf-8"))


def evaluate(pl_rows, bs_rows):
    bs = {}
    for r in bs_rows:
        bs.setdefault((r["원수사명"], r["공시분기"]), {})[V.norm(r["항목명"])] = r["값"]
    dangi, ytd = {}, {}
    for r in pl_rows:
        if r["항목번호"] == 25:
            dangi[(r["원수사명"], r["공시분기"])] = r.get("값_당분기")
            ytd[(r["원수사명"], r["공시분기"])] = r.get("값")
    flagged, blank, bsmiss, compared = {}, [], [], 0
    shadow_flag = {}
    shadow_n = 0
    for (co, q), d in sorted(dangi.items()):
        cur = bs.get((co, q), {}).get("기타포괄손익누계액")
        pq = V.prev_quarter(q)
        prev = bs.get((co, pq), {}).get("기타포괄손익누계액") if pq else None
        if d is None:
            blank.append((co, q))
            # shadow (informational): YTD difference within the FY
            if cur is not None and prev is not None and ytd.get((co, q)) is not None:
                if q.endswith("1Q"):
                    sd = ytd[(co, q)]
                else:
                    p_y = ytd.get((co, pq))
                    sd = None if p_y is None else ytd[(co, q)] - p_y
                if sd is not None:
                    shadow_n += 1
                    dbs = cur - prev
                    res = dbs - sd
                    if abs(res) > max(V.OCI_AOCI_TOL_REL * abs(dbs), V.OCI_AOCI_TOL_ABS_MN):
                        shadow_flag[(co, q)] = (dbs, sd, res)
            continue
        if cur is None or prev is None:
            bsmiss.append((co, q))
            continue
        compared += 1
        dbs = cur - prev
        res = dbs - d
        if abs(res) > max(V.OCI_AOCI_TOL_REL * abs(dbs), V.OCI_AOCI_TOL_ABS_MN):
            flagged[(co, q)] = (dbs, d, res)
    n = len(dangi)
    return {
        "universe": n, "blank": blank, "bs_missing": bsmiss, "compared": compared, "flagged": flagged,
        "old_comparable_within_tol": n - len(bsmiss) - len(flagged),      # what the gate prints today
        "new_comparable_within_tol": compared - len(flagged),
        "dangi": dangi, "shadow_flag": shadow_flag, "shadow_n": shadow_n,
    }


states = {}
for c in COMMITS:
    states[c] = evaluate(load_rows(c, V.PL_PATH), load_rows(c, V.BS_PATH))

print(f"{'state':10s} {'universe':>8s} {'blank':>6s} {'bs_miss':>7s} {'compared':>8s} {'flagged':>7s} "
      f"{'comparable(old print)':>22s} {'comparable(corrected)':>22s} {'overstated_by':>13s}")
for c in COMMITS:
    s = states[c]
    print(f"{c:10s} {s['universe']:8d} {len(s['blank']):6d} {len(s['bs_missing']):7d} {s['compared']:8d} "
          f"{len(s['flagged']):7d} {s['old_comparable_within_tol']:22d} {s['new_comparable_within_tol']:22d} "
          f"{s['old_comparable_within_tol'] - s['new_comparable_within_tol']:13d}")

# the old counting formula's `flagged` can differ from the corrected one only if the fix touched the flag test; both use the
# same test here by construction, so this assertion checks the bookkeeping identity instead.
for c in COMMITS:
    s = states[c]
    assert s["universe"] == len(s["blank"]) + len(s["bs_missing"]) + s["compared"], c
    assert s["old_comparable_within_tol"] - s["new_comparable_within_tol"] == len(s["blank"]), c
print("\nidentity universe = blank + bs_missing + compared holds in every state; "
      "overstatement == blank count in every state")

print("\n=== YELLOW rows that left the list between consecutive states ===")
for a, b in zip(COMMITS, COMMITS[1:]):
    sa, sb = states[a], states[b]
    gone = sorted(set(sa["flagged"]) - set(sb["flagged"]))
    new = sorted(set(sb["flagged"]) - set(sa["flagged"]))
    only_blank = [k for k in gone if sb["dangi"].get(k) is None and k in set(sb["blank"])]
    other_gone = [k for k in gone if k not in only_blank]
    print(f"\n{a} -> {b}: Y {len(sa['flagged'])} -> {len(sb['flagged'])}  gone={len(gone)} new={len(new)}  "
          f"gone-because-blank={len(only_blank)}")
    for k in only_blank:
        dbs, d, res = sa["flagged"][k]
        print(f"   BLANKED  {k[0]:12s} {k[1]}  was resid={res:+12.1f} (dBS={dbs:.1f}, PL당분기={d:.1f})  now 값_당분기=None")
    for k in other_gone:
        dbs, d, res = sa["flagged"][k]
        print(f"   resolved {k[0]:12s} {k[1]}  was resid={res:+12.1f}  now compared/within-tol or bs-missing")
    for k in new:
        dbs, d, res = sb["flagged"][k]
        print(f"   NEW-Y    {k[0]:12s} {k[1]}  resid={res:+12.1f}")

print("\n=== cumulative: baseline (b8c37fff) vs worktree ===")
sa, sb = states["b8c37fff"], states["WORKTREE"]
gone = sorted(set(sa["flagged"]) - set(sb["flagged"]))
print(f"Y {len(sa['flagged'])} -> {len(sb['flagged'])}; gone {len(gone)}; of them now blank: "
      f"{sum(1 for k in gone if k in set(sb['blank']))}")
print("newly blank cells (populated in b8c37fff, None in worktree):",
      sorted(set(sb['blank']) - set(sa['blank'])))
print("newly populated cells (None in b8c37fff, populated in worktree):",
      sorted(set(sa['blank']) - set(sb['blank'])))

print("\n=== SHADOW (informational, not a gate input): today's blank cells re-derived as YTD difference ===")
w = states["WORKTREE"]
print(f"blank cells with both BS AOCI quarters and YTD pair available: {w['shadow_n']} of {len(w['blank'])}; "
      f"would exceed tol: {len(w['shadow_flag'])}")
by_q = {}
for (co, q) in w["blank"]:
    by_q[q[-2:]] = by_q.get(q[-2:], 0) + 1
print("blank cells by quarter-of-year:", dict(sorted(by_q.items())))
for k, (dbs, sd, res) in sorted(w["shadow_flag"].items(), key=lambda kv: -abs(kv[1][2]))[:40]:
    print(f"   shadow-Y {k[0]:12s} {k[1]}  dBS={dbs:12.1f} YTDdiff={sd:12.1f} resid={res:+12.1f}")

print("\n=== worktree blank list by company ===")
cnt = {}
for co, q in w["blank"]:
    cnt.setdefault(co, []).append(q)
for co, qs in sorted(cnt.items(), key=lambda kv: -len(kv[1])):
    print(f"   {co:12s} {len(qs):3d}  {','.join(qs)}")
print("\nworktree bs_missing:", w["bs_missing"])
print("\nworktree flagged (", len(w["flagged"]), "):")
for k, (dbs, d, res) in sorted(w["flagged"].items(), key=lambda kv: -abs(kv[1][2])):
    print(f"   {k[0]:12s} {k[1]}  resid={res:+12.1f}")
