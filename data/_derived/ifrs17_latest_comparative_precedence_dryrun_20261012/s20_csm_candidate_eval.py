"""Read-only dry run, CSM_waterfall domain: current master vs LATEST comparative column (prior-year column of the next-year filing).

Inputs   csm_prior_scan_v2.csv (s11b)  - per later filing: prior-column vector (production builder pickers), master vector, builder re-extraction of
         the same filing's CURRENT column (fidelity self-test).
Rules    strict closure = lib_dryrun.strict_violations (WFY / CONT / SPIKE / ZAMORT, no exemption sets) on the whole company chain
Unit     closure is judged per (company x fiscal-year) BUNDLE of overlay blocks, because the verification unit contains inter-period
         continuity (within-FY opening, previous-year closing): a single quarter can never close on its own.  For every company all
         2^k subsets of its fiscal-year bundles are tried (k <= 4); a subset is FEASIBLE when it creates no strict violation that the
         current master does not already have and worsens none it has (magnitude +10% & +0.2pp); among feasible subsets the one that resolves
         the most baseline violations (then the most blocks) is adopted.  Nothing infeasible is adopted ("검증 단위까지 닫히지 않으면 이전 값").
Candidate pool: TRUSTED = scan status DIFF, picker verified (fidelity SAME, or SAME on every item that carries no gold overlay cell in the
         same filing's quarter) and plausible (opening and closing within +-25% of the master block; beyond that the read is suspect).
Gold     blocks carrying owner overlay cells (data/_gold/user_csm_cells.json) are never replaced (verdict 'gold 충돌'); a second run with the
         gold blocks released tells whether the gold cell is the only obstacle.
Verdict labels (ticket decision table):
  최신 채택(진짜 재작성 †)  latest closes, current closes too, values differ
  최신 채택(예외 해소)     latest closes, current has a strict violation touching the block that the adopted bundle removes
  현행 유지               the block's bundle cannot close (it creates/worsens a violation) while the current block closes
  둘 다 불가              neither closes (current has a violation that no feasible bundle removes)
  gold 충돌               owner overlay cell inside the block
  후보 미검증             DIFF but the picker could not be verified or the read is implausible (tool/extraction doubt, not a rule verdict)
  변화 없음               comparative equals master
  비교 컬럼 추출 불가      no prior-period block / picker returned nothing (tool gap, not a rule gap) or no master block to compare
"""
from __future__ import annotations

import csv
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib_dryrun as D  # noqa: E402

ROOT = D.ROOT
sys.path.insert(0, str(ROOT / "scripts"))
import build_root_masters as BR  # noqa: E402  (pure helpers only; main() is never called)

scan = list(csv.DictReader(open(HERE / "csm_prior_scan_v2.csv", encoding="utf-8-sig")))
rows_master = D.load_json("CSM_waterfall.json")
chain0 = D.csm_chain(rows_master)
NAMES = D.names()
gold_blocks, excl_cos = D.gold_csm_blocks()

ilp = D.load_json("insurance_liability_portfolio.json")
i3 = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in ilp if r["항목번호"] == 3 and r["값"] is not None}
i6 = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in ilp if r["항목번호"] == 6 and r["값"] is not None}
PL_AMORT = {}
for r in D.load_json("PL_breakdown.json"):
    if r["항목번호"] in (4, "4") and r["값"] is not None:
        PL_AMORT[(r["원보험사코드"], r["공시분기"])] = r["값"]


def ilp_stock(kr, q):
    if (kr, q) in i3 or (kr, q) in i6:
        return (i3.get((kr, q)) or 0) + (i6.get((kr, q)) or 0)
    return None


def vec(row, pref):
    out = {}
    for k in range(1, 7):
        v = row.get(f"{pref}{k}")
        out[k] = float(v) if v not in (None, "") else None
    return out


def rcept_of(dirname, later_q):
    p = ROOT / "data/dart" / f"FY{later_q[:4]}_Q{later_q[5]}" / "raw" / dirname / "meta.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("rcept_no")
        except Exception:
            return None
    return None


def tol(v):
    return max(0.15, abs(v) * 0.0005) if v is not None else 0.15


def fidelity_ok(r):
    """picker verified on the same filing's CURRENT column: all six items equal the master, or equal on every item without a gold cell."""
    if r["fidelity"] == "SAME":
        return True
    kr, lq = r["kr"], r["later_q"]
    cv, mv = vec(r, "c"), chain0.get(kr, {}).get(lq)
    if not mv or all(v is None for v in cv.values()):
        return False
    gitems = set(gold_blocks.get((kr, lq), []))
    for k in range(1, 7):
        if k in gitems or cv.get(k) is None or mv.get(k) is None:
            continue
        if abs(cv[k] - mv[k]) > tol(mv[k]):
            return False
    return bool(gitems)          # a mismatch fully explained by gold cells (otherwise the DIFF has another cause)


def plausible(pv, mv):
    for k in (1, 6):
        a, b = pv.get(k), mv.get(k)
        if a is None or b is None or abs(b) < 1.0:
            continue
        if abs(a / b - 1.0) > 0.25:
            return False
    return True


# ------------------------------------------------------------------ pools
trusted_all, unverified, implaus = {}, {}, {}
for r in scan:
    if r["status"] != "DIFF":
        continue
    key = (r["kr"], r["prior_q"])
    pv = vec(r, "p")
    mv = chain0.get(r["kr"], {}).get(r["prior_q"], {})
    if not fidelity_ok(r):
        unverified[key] = pv
    elif not plausible(pv, mv):
        implaus[key] = pv
    else:
        trusted_all[key] = pv

trusted = {k: v for k, v in trusted_all.items() if k not in gold_blocks}
gold_trusted = {k: v for k, v in trusted_all.items() if k in gold_blocks}


def apply(chain, overlay):
    out = {co: {q: dict(m) for q, m in qs.items()} for co, qs in chain.items()}
    for (kr, q), v in overlay.items():
        if kr in out and q in out[kr]:
            for k, x in v.items():
                if x is not None:
                    out[kr][q][k] = x
    return out


viol0 = {co: D.strict_violations(qs) for co, qs in chain0.items()}


def best_subset(co, pool):
    blocks = {k: v for k, v in pool.items() if k[0] == co}
    fys = sorted({q[:4] for (_c, q) in blocks})
    base = viol0.get(co, [])
    best, best_score = (), None
    for n in range(len(fys) + 1):
        for sub in itertools.combinations(fys, n):
            ov = {k: v for k, v in blocks.items() if k[1][:4] in sub}
            ch = apply({co: chain0[co]}, ov)[co]
            new = D.strict_violations(ch)
            if D.created_or_worse(base, new):
                continue
            score = (len(D.resolved(base, new)), len(ov))
            if best_score is None or score > best_score:
                best, best_score = sub, score
    return best


def run(pool):
    chosen = {}
    for co in sorted({k[0] for k in pool}):
        chosen[co] = set(best_subset(co, pool))
    adopt = {k: v for k, v in pool.items() if k[1][:4] in chosen.get(k[0], set())}
    return adopt, chosen


adopt, chosen = run(trusted)
adopt_g, chosen_g = run({**trusted, **gold_trusted})
chain_final = apply(chain0, adopt)
viol_final = {co: D.strict_violations(qs) for co, qs in chain_final.items()}

out = []
verd = Counter()
cells = Counter()
amort_break = []
for r in scan:
    kr, pq, lq = r["kr"], r["prior_q"], r["later_q"]
    if kr in excl_cos:
        continue
    key = (kr, pq)
    row = {"domain": "CSM_waterfall", "kr": kr, "name": NAMES.get(kr, r["name"]), "quarter": pq, "later_filing_q": lq,
           "later_dir": r["dir"], "later_rcept": rcept_of(r["dir"], lq), "scan_status": r["status"], "fidelity": r["fidelity"],
           "gold_cells": ",".join(map(str, gold_blocks.get(key, []))) or ""}
    mv = {k: chain0.get(kr, {}).get(pq, {}).get(k) for k in range(1, 7)}
    pv = vec(r, "p")
    row["current"] = json.dumps([mv[k] for k in range(1, 7)])
    row["latest"] = json.dumps([pv[k] for k in range(1, 7)]) if r["status"] in ("SAME", "DIFF") else ""
    if r["status"] in ("NO_PRIOR", "NO_MASTER", "ERR"):
        row["verdict"] = "비교 컬럼 추출 불가" if r["status"] != "NO_MASTER" else "마스터 칸 없음"
        row["note"] = f"prior blocks={r['n_prior_blocks']} src={r['src']}"
        out.append(row)
        verd[row["verdict"]] += 1
        continue
    if r["status"] == "SAME":
        row["verdict"] = "변화 없음"
        out.append(row)
        verd[row["verdict"]] += 1
        continue
    items = set(r["diff_items"].split(",")) if r["diff_items"] else set()
    row["diff_items"] = r["diff_items"]
    row["small_reclass_only"] = bool(items) and items <= {"3", "4"}
    c0 = D.touching(viol0.get(kr, []), pq)
    row["current_violations"] = D.fmt_viol(c0)
    st = ilp_stock(kr, pq)
    if st is not None:
        t_ = max(1.0, 0.005 * abs(st))
        row["ilp_3plus6"] = round(st, 1)
        row["ilp_agrees_current"] = (mv[6] is not None) and abs(mv[6] - st) <= t_
        row["ilp_agrees_latest"] = (pv[6] is not None) and abs(pv[6] - st) <= t_
    if key in gold_blocks:
        row["tier"] = "gold"
        row["verdict"] = "gold 충돌"
        row["note"] = ("gold 해제 시 채택 가능(번들 닫힘)" if key in adopt_g else "gold 해제해도 번들이 안 닫힘")
    elif key in unverified:
        row["tier"] = "unverified"
        row["verdict"] = "후보 미검증(추출 확인 필요)"
        row["note"] = "picker does not reproduce the master from the same filing's current column"
    elif key in implaus:
        row["tier"] = "implausible"
        row["verdict"] = "후보 미검증(추출 확인 필요)"
        row["note"] = "prior vector opening/closing differs >25% from the master block: block-selection suspect"
    elif key in adopt:
        row["tier"] = "trusted"
        c1 = D.touching(viol_final.get(kr, []), pq)
        row["latest_violations"] = D.fmt_viol(c1)
        row["verdict"] = "최신 채택(예외 해소)" if (c0 and not c1) else "최신 채택(진짜 재작성 †)"
        # PL companion check: amortisation identity needs the PL item 4 (원수CSM상각) of the same quarter
        pl4 = PL_AMORT.get(key)
        if pl4 is not None and pv[5] is not None and mv[5] is not None:
            ident_cur = abs(abs(pl4) / 100.0 - abs(mv[5])) <= max(0.1, 0.0005 * abs(mv[5]))
            ident_lat = abs(abs(pl4) / 100.0 - abs(pv[5])) <= max(0.1, 0.0005 * abs(pv[5]))
            row["pl_amort_identity_current"] = ident_cur
            row["pl_amort_identity_latest_with_PL_unchanged"] = ident_lat
            if ident_cur and not ident_lat:
                amort_break.append(key)
                row["verdict"] = "조건부(PL 동반 필요)"
                row["note"] = ("CSM 번들은 닫히지만 PL 원수CSM상각(원 공시값)이 최신 워터폴 상각과 안 맞아 CSM_AMORT_IDENTITY 가 깨진다 — "
                               "PL 블록(전기 컬럼 Tier-2)을 같이 채택해야 닫힌다. 이 칸 전에는 현행 유지.")
    else:
        row["tier"] = "trusted"
        ov = {k: v for k, v in trusted.items() if k[0] == kr and k[1][:4] == pq[:4]}
        ch = apply({kr: chain0[kr]}, ov)[kr]
        created = D.created_or_worse(viol0.get(kr, []), D.strict_violations(ch))
        row["latest_violations"] = D.fmt_viol(created) or "(none created alone)"
        row["verdict"] = "현행 유지" if not c0 else "둘 다 불가(현행 유지+목록)"
        row["note"] = "FY bundle alone creates/worsens: " + row["latest_violations"][:220]
    out.append(row)
    verd[row["verdict"]] += 1
    cells[row["verdict"]] += len(items)

cols = ["domain", "kr", "name", "quarter", "later_filing_q", "later_dir", "later_rcept", "scan_status", "fidelity", "tier", "diff_items",
        "small_reclass_only", "gold_cells", "current", "latest", "current_violations", "latest_violations", "ilp_3plus6", "ilp_agrees_current",
        "ilp_agrees_latest", "pl_amort_identity_current", "pl_amort_identity_latest_with_PL_unchanged", "verdict", "note"]
with open(HERE / "csm_block_verdicts.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(out)
print("verdicts:", dict(verd))
print("differing item-cells by verdict:", dict(cells))
n_adopt_cells = sum(1 for k, v in adopt.items() for x, y in v.items() if y is not None and chain0[k[0]][k[1]].get(x) != y)
print("adopted blocks:", len(adopt), " cells:", n_adopt_cells)
print("adopted blocks whose PL amortisation identity (PL item 4 vs waterfall item 5) holds now but breaks if only the CSM side moves:", len(amort_break), sorted(amort_break))
print("chosen FY bundles (gold fixed):", {co: sorted(s) for co, s in chosen.items() if s})
print("chosen FY bundles (gold released):", {co: sorted(s) for co, s in chosen_g.items() if s})
nb = sum(len(D.fmt_viol(v)) > 0 for v in viol0.values())
print("baseline strict violations:", sum(len({D.vsig(x) for x in v}) for v in viol0.values()), " after adoption:", sum(len({D.vsig(x) for x in v}) for v in viol_final.values()))
for co in sorted(chain0):
    a, b = {D.vsig(x) for x in viol0[co]}, {D.vsig(x) for x in viol_final[co]}
    if a or b:
        print(f"  {co} {NAMES.get(co,'')[:8]:8s} base={sorted(a)} -> final={sorted(b)}")


def candidate_rows(overlay):
    cand = json.loads(json.dumps(rows_master))
    idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cand}
    changed = 0
    for (kr, q), v in overlay.items():
        for k, x in v.items():
            key = (kr, k, q)
            if x is not None and key in idx and idx[key]["값"] != x:
                idx[key]["값"] = x
                changed += 1
    ytd = defaultdict(dict)
    for r in cand:
        ytd[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
    touched_cos = {k[0] for k in overlay}
    for r in cand:
        code, item, q, v = r["원보험사코드"], r["항목번호"], r["공시분기"], r["값"]
        if code not in touched_cos:                 # untouched companies keep the live 값_당분기 byte for byte
            continue
        if v is None:
            dangi = None
        elif item == BR.CSM_CLOSE:
            dangi = v
        elif item == BR.CSM_OPEN:
            p = BR._prev_q(q)
            dangi = v if p is None else ytd[(code, BR.CSM_CLOSE)].get(p)
        else:
            dangi = BR._flow_dangi(ytd[(code, item)], q)
        r["값_당분기"] = round(dangi, 6) if isinstance(dangi, (int, float)) else dangi
    return cand, changed


(HERE / "cand").mkdir(exist_ok=True)
for tag, ov in (("ADOPT", adopt), ("ALLTRUSTED", {**trusted, **gold_trusted})):
    cand, ch = candidate_rows(ov)
    (HERE / "cand" / f"CSM_waterfall.{tag}.json").write_text(json.dumps(cand, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"candidate {tag}: blocks {len(ov)} cells changed {ch}")
json.dump({f"{k[0]}|{k[1]}": v for k, v in adopt.items()}, open(HERE / "cand" / "csm_adopt_overlay.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({f"{k[0]}|{k[1]}": v for k, v in unverified.items()}, open(HERE / "cand" / "csm_unverified_overlay.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({f"{k[0]}|{k[1]}": v for k, v in implaus.items()}, open(HERE / "cand" / "csm_implausible_overlay.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
