#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level applier (parser/ifrs17, ticket 20261021T1310Z follow-up, coordinator approval 2026-10-22):
KR0073 (Kyobo Life) PL_breakdown 2023.1Q-2024.2Q refreshed to the latest-comparative (restated) separate-basis columns.

Writes (only these, each guarded + backed up):
  data/_gold/user_pl_cells.json          +122 KR0073 entries (the PL gold overlay is applied LAST by build_root_masters.build_pl, so a later build cannot revert them)
  PL_breakdown.json                      KR0073 cells only (122 값 + 30 derived-only 값_당분기), produced by the REAL build_pl() run on a temp copy
  PL_breakdown_provenance.json           the 12 KR0073 target blocks = output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply files + merge note
  tests/test_rule_coverage_manifest.py   GOLD_OVERLAY_CENSUS PL tuple (360, 29) -> (482, 29) + one comment line
Everything the apply writes is compared with the candidate files that were gated in the dry run (sim/cand_pl.json, sim/gold_pl_cand.json, sim/prov_pl_cand_emitter.json).

  --snapshot-drift       read-only: record which non-KR0073 cells a fresh build_pl() already disagrees with (pre-existing drift) -> pl_drift_before.json (run BEFORE --apply)
  --check                read-only plan + post-condition checks
  --out-dir DIR          write the post-apply files under DIR (repo untouched)
  --apply                write the repo files (backups in backup_before_apply_PL/, manifest apply_manifest_PL.json)
  --revert --apply       restore the backups (only while the live files still carry the post-apply hashes)
  --verify               read-only: fresh real build_pl() from the LIVE gold + LIVE master == LIVE master for every KR0073 row; non-KR0073 drift == snapshot;
                         the provenance emitter reproduces all KR0073 provenance blocks
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "kyobo_pl_restate_dryrun_20261021"
CSM_EV = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
CODE = "KR0073"
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")
for p in (str(ROOT / "scripts"), str(ROOT), str(EV)):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ak = _load(CSM_EV / "apply_kr0073_fix.py", "ak_helpers")      # JsonFile (exact-format JSON), write_atomic, sha
import sim_pl_builder as S  # noqa: E402  (real build_pl() on a temp copy; repo untouched)

F = {"PL": "PL_breakdown.json", "GOLD": "data/_gold/user_pl_cells.json", "PROV": "PL_breakdown_provenance.json"}
PIN_REL = "data/_gold/gold_overlay_ledger.json"
TEST_REL = "tests/test_rule_coverage_manifest.py"
PL_MASTER_SRC = "data/dart/viz/pl_breakdown_master.json"
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]
BLOCKS = ("contract_notes", "income_statement")
TARGET_BLOCKS = {(CODE, q, b) for q in QS for b in BLOCKS}
LATER = {"2023.1Q": ("FY2024_Q1", "20240516001553"), "2023.2Q": ("FY2024_Q2", "20240814004365"), "2023.3Q": ("FY2024_Q3", "20241114003039"),
         "2023.4Q": ("FY2024_Q4", "20250331004015"), "2024.1Q": ("FY2025_Q1", "20250515002967"), "2024.2Q": ("FY2025_Q2", "20250814004112")}
TOL = 5e-4
EXPECT = {"gold_added": 122, "val_changed": 122, "dangi_changed": 152, "census_old": (360, 29), "census_new": (482, 29), "prov_blocks": 12}
MERGE_NOTE = ("KR0073 PL 2023.1Q-2024.2Q refreshed to the latest-comparative (restated) separate-basis columns via data/_gold/user_pl_cells.json (+122 cells). "
              "The 12 affected blocks are the output of scripts/emit_pl_provenance.py for the post-apply masters (touched items moved to the owner_gold_overlay entry; "
              "blocks whose published items are all gold-overlaid become OWNER_GOLD). Evidence data/_derived/kyobo_pl_restate_dryrun_20261021/")
SUBS = [
    ('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")'),
    ('PL_SRC = ROOT / "PL_breakdown.json"', 'PL_SRC = Path(os.environ["EMIT_PL_SRC"])'),
    ('PL_OVR = ROOT / "data" / "_gold" / "user_pl_cells.json"', 'PL_OVR = Path(os.environ["EMIT_PL_OVR"])'),
    ('PL_OUT = ROOT / "PL_breakdown_provenance.json"', 'PL_OUT = Path(os.environ["EMIT_PL_OUT"])'),
]


def rkey(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def load_json(rel_or_path):
    p = Path(rel_or_path)
    if not p.is_absolute():
        p = ROOT / rel_or_path
    return json.loads(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- plan pieces
def plan_cells():
    plan = load_json(EV / "pl_plan.json")["plan"]
    if len(plan) != EXPECT["gold_added"]:
        raise SystemExit(f"ABORT: plan has {len(plan)} cells, expected {EXPECT['gold_added']}")
    return plan


def guard_live_matches_plan(live_rows, plan):
    cur = {rkey(r): r for r in live_rows if r["원보험사코드"] == CODE}
    bad = []
    for c in plan:
        r = cur.get((CODE, c["item"], c["quarter"]))
        if r is None:
            bad.append(("row missing", c["quarter"], c["item"]))
            continue
        v = r.get("값")
        if c["old"] is None:
            if v is not None:
                bad.append(("expected empty", c["quarter"], c["item"], v))
        elif v is None or abs(v - c["old"]) > TOL:
            bad.append(("expected old value", c["quarter"], c["item"], c["old"], v))
    if bad:
        raise SystemExit(f"ABORT: live PL cells moved since the plan was made (concurrent session?): {bad[:6]} ... ({len(bad)})")


def build_gold(live_gold, plan):
    g = copy.deepcopy(live_gold)
    existing = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in g["set"]}
    for c in plan:
        k = (CODE, c["item"], c["quarter"])
        if k in existing:
            raise SystemExit(f"ABORT: gold already has {k}")
        fy, rc = LATER[c["quarter"]]
        note = (f"2026-10-22 parser/ifrs17 (KR0073 PL refresh, coordinator instruction 2026-10-21 after owner rejected the amortization pins): latest-comparative, 별도 기준. "
                f"{fy} rcept {rc} 의 전기(누적) 열 = 재작성 값. 값 근거·원문 줄 번호 data/_derived/kyobo_pl_restate_dryrun_20261021/pl_cell_changes.csv"
                + (" (item 6/7: 같은 행이 이 필링에서 '발생한 보험서비스수익' 로 인쇄돼 생산 판독기가 못 읽는다 — 같은 행을 같은 산식으로 읽음)" if "ALT_LABEL_ITEM6" in c["flags"] else ""))
        g["set"].append({"원보험사코드": CODE, "항목번호": c["item"], "공시분기": c["quarter"], "값": c["new"], "was": c["old"], "note": note})
    return g


def build_master(live_rows, new_gold, tag):
    """REAL build_pl() on a temp copy (seeded with the live master) against the candidate gold; splice ONLY the KR0073 rows into the live rows."""
    tmpdir = EV / "tmp_apply"
    tmpdir.mkdir(exist_ok=True)
    gp, mp = tmpdir / f"gold_{tag}.json", tmpdir / f"master_{tag}.json"
    gp.write_text(json.dumps(new_gold, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    sim_rows, _n = S.simulate(gp, mp)
    for p in (gp, mp):
        try:
            p.unlink()
        except OSError:
            pass
    sim_by = {rkey(r): r for r in sim_rows}
    if len(sim_rows) != len(live_rows):
        raise SystemExit(f"ABORT: builder row count {len(sim_rows)} != live {len(live_rows)}")
    new_rows, val_changed, dangi_changed, other_drift = [], [], [], []
    for r in live_rows:
        s = sim_by.get(rkey(r))
        if s is None:
            raise SystemExit(f"ABORT: {rkey(r)} missing from the builder simulation")
        if r["원보험사코드"] == CODE:
            nr = dict(r)
            nr["값"], nr["값_당분기"] = s["값"], s["값_당분기"]
            new_rows.append(nr)
            if nr["값"] != r["값"]:
                val_changed.append(rkey(r))
            if nr["값_당분기"] != r.get("값_당분기"):
                dangi_changed.append(rkey(r))
        else:
            if (r["값"], r.get("값_당분기")) != (s["값"], s.get("값_당분기")):
                other_drift.append(rkey(r))
            new_rows.append(r)
    return new_rows, val_changed, dangi_changed, other_drift


def emitter_copy_is_current():
    src = (ROOT / "scripts" / "emit_pl_provenance.py").read_text(encoding="utf-8")
    for old, new in SUBS:
        if src.count(old) != 1:
            return False
        src = src.replace(old, new)
    return src == (EV / "emit_pl_provenance_sandbox_copy.py").read_text(encoding="utf-8")


def run_emitter(rows_kr, gold_obj, tag):
    d = EV / "tmp_emit"
    d.mkdir(exist_ok=True)
    src, gold, out = d / f"src_{tag}.json", d / f"gold_{tag}.json", d / f"prov_{tag}.json"
    src.write_text(json.dumps(rows_kr, ensure_ascii=False), encoding="utf-8", newline="\n")
    gold.write_text(json.dumps(gold_obj, ensure_ascii=False), encoding="utf-8", newline="\n")
    if out.exists():
        out.unlink()
    env = dict(os.environ, EMIT_PL_SRC=str(src), EMIT_PL_OVR=str(gold), EMIT_PL_OUT=str(out), PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, str(EV / "emit_pl_provenance_sandbox_copy.py")], cwd=str(ROOT), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (d / f"emit_{tag}.log").write_text((p.stdout or "") + "\n--- stderr ---\n" + (p.stderr or ""), encoding="utf-8", newline="\n")
    if p.returncode != 0 or not out.exists():
        raise SystemExit(f"ABORT: sandbox emitter failed (rc={p.returncode}), see {d / f'emit_{tag}.log'}")
    return json.loads(out.read_text(encoding="utf-8"))


def build_prov(live_prov, emit_doc):
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_doc["cells"]}
    new = copy.deepcopy(live_prov)
    n = 0
    for i, c in enumerate(new["cells"]):
        k = (c["company_code"], c["quarter"], c["item_block"])
        if k in TARGET_BLOCKS:
            new["cells"][i] = ek[k]
            n += 1
    if n != EXPECT["prov_blocks"]:
        raise SystemExit(f"ABORT: replaced {n} provenance blocks, expected {EXPECT['prov_blocks']}")
    new["merge_note_20261022_kr0073_pl_refresh"] = MERGE_NOTE
    return new


def census_pl(gold_obj, pin_obj):
    import validate_data_contract as G
    rows = G.gold_overlay_census("PL", gold_obj["set"], load_json(PL_MASTER_SRC))
    masked = [r for r in rows if r["verdict"] in G._GOLD_MASKED]
    pins = pin_obj.get("entries", {})
    unpinned = [r["key"] for r in masked if r["key"] not in pins]
    drift = [r["key"] for r in rows if r["key"] in pins and r["verdict"] not in G._GOLD_MASKED]
    seen = {r["key"] for r in rows}
    stale = [k for k in pins if k.startswith("PL|") and k not in seen]
    return (len(rows), len(masked)), unpinned, drift, stale


DECL_RE = re.compile(r'^(GOLD_OVERLAY_CENSUS = \{"CSM": \(\d+, \d+\), "PL": )\((\d+), (\d+)\)(\})$', re.M)


def new_test_text(raw, census_old, census_new):
    ms = list(DECL_RE.finditer(raw))
    if len(ms) != 1:
        raise SystemExit(f"ABORT: GOLD_OVERLAY_CENSUS declaration found {len(ms)} times in {TEST_REL}")
    m = ms[0]
    if (int(m.group(2)), int(m.group(3))) != census_old:
        raise SystemExit(f"ABORT: declared PL census {(int(m.group(2)), int(m.group(3)))} != expected old {census_old}")
    comment = ("# 2026-10-22 ticket 20261021T1310Z (parser/ifrs17, KR0073 PL refresh to the latest comparative): PL gold %d->%d cells, masked %d->%d (no new pins).\n"
               % (census_old[0], census_new[0], census_old[1], census_new[1]))
    return raw[:m.start()] + comment + m.group(1) + "(%d, %d)" % census_new + m.group(4) + raw[m.end():]


def plan_all():
    live = {k: ak.JsonFile(rel) for k, rel in F.items()}
    plan = plan_cells()
    guard_live_matches_plan(live["PL"].obj, plan)
    new_gold = build_gold(live["GOLD"].obj, plan)
    new_rows, val_changed, dangi_changed, other_drift = build_master(live["PL"].obj, new_gold, "plan")

    errs = []
    want = {(CODE, c["item"], c["quarter"]): c["new"] for c in plan}
    if set(val_changed) != set(want):
        errs.append(f"값 changed set != plan set: only-in-sim {sorted(set(val_changed) - set(want))[:5]} only-in-plan {sorted(set(want) - set(val_changed))[:5]}")
    by = {rkey(r): r for r in new_rows}
    for k, v in want.items():
        if by[k]["값"] != v:
            errs.append(f"value {k}: built {by[k]['값']} != plan {v}")
    if len(val_changed) != EXPECT["val_changed"] or len(dangi_changed) != EXPECT["dangi_changed"]:
        errs.append(f"counts: 값 {len(val_changed)} (exp {EXPECT['val_changed']}), 당분기 {len(dangi_changed)} (exp {EXPECT['dangi_changed']})")

    # what is applied == what was gated in the dry run
    cand_master = load_json(EV / "sim" / "cand_pl.json")
    if cand_master != new_rows:
        diff = [rkey(a) for a, b in zip(cand_master, new_rows) if a != b]
        errs.append(f"post-apply master differs from the gated candidate sim/cand_pl.json in {len(diff)} rows (e.g. {diff[:3]})")
    if load_json(EV / "sim" / "gold_pl_cand.json") != new_gold:
        errs.append("post-apply gold differs from the gated candidate sim/gold_pl_cand.json")

    if not emitter_copy_is_current():
        errs.append("the sandbox emitter copy no longer matches scripts/emit_pl_provenance.py")
    emit_doc = run_emitter([r for r in new_rows if r["원보험사코드"] == CODE], new_gold, "apply")
    new_prov = build_prov(live["PROV"].obj, emit_doc)
    if load_json(EV / "sim" / "prov_pl_cand_emitter.json") != new_prov:
        errs.append("post-apply provenance differs from the gated candidate sim/prov_pl_cand_emitter.json")

    pin_obj = load_json(PIN_REL)
    census_old, un0, dr0, st0 = census_pl(live["GOLD"].obj, pin_obj)
    census_new, un1, dr1, st1 = census_pl(new_gold, pin_obj)
    if census_old != EXPECT["census_old"] or census_new != EXPECT["census_new"] or un1 or dr1 or st1:
        errs.append(f"census {census_old}->{census_new} (expected {EXPECT['census_old']}->{EXPECT['census_new']}); unpinned={un1} drift={dr1} stale={st1}")
    test_raw = (ROOT / TEST_REL).read_text(encoding="utf-8")
    new_test = new_test_text(test_raw, census_old, census_new)

    snap_path = EV / "pl_drift_before.json"
    if not snap_path.exists():
        errs.append("pl_drift_before.json missing: run --snapshot-drift before the apply")
    else:
        before = {tuple(x) for x in json.loads(snap_path.read_text(encoding="utf-8"))["non_kr0073_drift"]}
        if before != set(other_drift):
            errs.append(f"non-KR0073 drift changed vs snapshot: {len(before)} -> {len(other_drift)}")
    return dict(live=live, plan=plan, new_gold=new_gold, new_rows=new_rows, val_changed=val_changed, dangi_changed=dangi_changed, other_drift=other_drift,
                new_prov=new_prov, census=(census_old, census_new), test_raw=test_raw, new_test=new_test, errs=errs)


def report(P):
    print(f"gold: +{len(P['new_gold']['set']) - len(P['live']['GOLD'].obj['set'])} entries -> {len(P['new_gold']['set'])}")
    print(f"master KR0073: 값 changed {len(P['val_changed'])}, 값_당분기 changed {len(P['dangi_changed'])} (derived-only {len(set(P['dangi_changed']) - set(P['val_changed']))}); "
          f"other-company drift cells (pre-existing, untouched) {len(P['other_drift'])}")
    only_q = sorted(set(P["dangi_changed"]) - set(P["val_changed"]), key=lambda k: (k[2], k[1]))
    by_q = {}
    for c, i, q in only_q:
        by_q.setdefault(q, []).append(i)
    print("  derived-only 당분기:", {q: sorted(v) for q, v in sorted(by_q.items())})
    print(f"provenance: {EXPECT['prov_blocks']} blocks replaced + merge note")
    print(f"census PL (gold cells, masked): {P['census'][0]} -> {P['census'][1]}")
    print("errors:", P["errs"] or "none")


def outputs(P):
    L = P["live"]
    return {F["GOLD"]: ak.JsonFile._dump(P["new_gold"], *L["GOLD"].fmt), F["PL"]: ak.JsonFile._dump(P["new_rows"], *L["PL"].fmt),
            F["PROV"]: ak.JsonFile._dump(P["new_prov"], *L["PROV"].fmt), TEST_REL: P["new_test"].encode("utf-8")}


def snapshot_drift():
    live_rows = load_json(F["PL"])
    gold = load_json(F["GOLD"])
    # KR0073 stale cells = KR0073 cells where a fresh build with the LIVE gold already differs from the live master
    _rows, vc, dc, other = build_master(live_rows, gold, "snapshot")
    out = {"made_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "non_kr0073_drift": [list(k) for k in other],
           "kr0073_stale_before": sorted([list(k) for k in set(vc) | set(dc)], key=lambda x: (x[2], x[1]))}
    (EV / "pl_drift_before.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"snapshot: non-KR0073 drift cells {len(other)}; KR0073 cells where the fresh build already differs from live: {len(out['kr0073_stale_before'])}")
    for k in out["kr0073_stale_before"]:
        print("   stale", k)


def verify():
    live_rows = load_json(F["PL"])
    gold = load_json(F["GOLD"])
    _rows, vc, dc, other = build_master(live_rows, gold, "verify")
    snap = {tuple(x) for x in json.loads((EV / "pl_drift_before.json").read_text(encoding="utf-8"))["non_kr0073_drift"]}
    kr_rows = sum(1 for r in live_rows if r["원보험사코드"] == CODE)
    ok1 = not vc and not dc
    ok2 = set(other) == snap
    print(f"verify: KR0073 rows {kr_rows}; fresh build_pl() differs from live in {len(set(vc) | set(dc))} KR0073 cells -> {'OK' if ok1 else 'FAIL'}")
    print(f"verify: non-KR0073 drift now {len(other)} vs snapshot {len(snap)} -> {'OK (identical set)' if ok2 else 'FAIL'}")
    emit_doc = run_emitter([r for r in live_rows if r["원보험사코드"] == CODE], gold, "verify")
    live_prov = load_json(F["PROV"])
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live_prov["cells"] if c["company_code"] == CODE}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_doc["cells"] if c["company_code"] == CODE}
    bad = [k for k in lk if lk[k] != ek.get(k)]
    ok3 = set(lk) == set(ek) and not bad
    print(f"verify: provenance emitter reproduces {len(lk) - len(bad)}/{len(lk)} KR0073 blocks -> {'OK' if ok3 else 'FAIL ' + str(bad[:4])}")
    return ok1 and ok2 and ok3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-drift", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--out-dir")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    backup = EV / "backup_before_apply_PL"
    manifest_path = EV / "apply_manifest_PL.json"

    if a.snapshot_drift:
        snapshot_drift()
        return
    if a.verify:
        raise SystemExit(0 if verify() else 2)
    if a.revert:
        if not a.apply:
            raise SystemExit("--revert needs --apply")
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rel, h in man["after_sha256"].items():
            if ak.sha((ROOT / rel).read_bytes()) != h:
                raise SystemExit(f"ABORT revert: {rel} changed since apply (post-apply hash mismatch)")
        for rel in man["before_sha256"]:
            ak.write_atomic(ROOT / rel, (backup / rel).read_bytes())
        print("reverted", list(man["before_sha256"]))
        return

    P = plan_all()
    report(P)
    if P["errs"]:
        raise SystemExit("ABORT: " + " | ".join(P["errs"]))
    outs = outputs(P)
    if a.out_dir:
        od = Path(a.out_dir)
        for rel, b in outs.items():
            ak.write_atomic(od / rel, b)
        print("simulated post-apply files under", od)
        return
    if not a.apply:
        print("(--check only; nothing written)")
        return

    before = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    expect = {F["GOLD"]: P["live"]["GOLD"].sha0, F["PL"]: P["live"]["PL"].sha0, F["PROV"]: P["live"]["PROV"].sha0,
              TEST_REL: ak.sha(P["test_raw"].encode("utf-8"))}
    for rel, h in before.items():
        if expect[rel] != h:
            raise SystemExit(f"ABORT: {rel} changed between read and write (concurrent session?)")
    backup.mkdir(parents=True, exist_ok=True)
    for rel in outs:
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    written = []
    try:
        for rel, b in outs.items():
            ak.write_atomic(ROOT / rel, b)
            written.append(rel)
    except BaseException:
        for rel in written:
            ak.write_atomic(ROOT / rel, (backup / rel).read_bytes())
        raise
    after = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    manifest_path.write_text(json.dumps({"before_sha256": before, "after_sha256": after, "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                        ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("APPLIED:", list(outs))


if __name__ == "__main__":
    main()
