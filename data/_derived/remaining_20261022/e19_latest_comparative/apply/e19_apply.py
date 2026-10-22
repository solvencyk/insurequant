#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-company cell-level applier (parser/ifrs17, ticket 20261022T0900Z, owner go 2026-10-22): 19 PL_breakdown buckets of 7 companies
(KR0005 KR0032 KR0070 KR0082 KR0083 KR0087 KR0104) refreshed to the latest-comparative (separate basis, prior cumulative column) values.
Generalised from data/_derived/remaining_20261022/a_oci/apply_kr0073_oci.py (Kyobo precedent).  Input = e19_manifest.json (built from plan_KR*.json).

Writes (only these, each guarded + backed up to the session scratchpad):
  data/_gold/user_pl_cells.json            +171 set entries (was/note evidence), +17 null_dangi cells, +20 set_dangi cells (existing entries never modified)
  PL_breakdown.json                        ONLY the cells where a REAL build_pl() run (temp copy) with the new gold differs from the same run with the live gold
                                           (= the 171 planned 값 cells + the 값_당분기 cells that follow), proven by a cell-level diff
  PL_breakdown_provenance.json             blocks whose emitter output changes (sandbox copy of scripts/emit_pl_provenance.py; never imported) + one new merge note key
  tests/test_rule_coverage_manifest.py     GOLD_OVERLAY_CENSUS PL tuple

  --snapshot-drift   read-only: live master vs a fresh build_pl() with the LIVE gold (all companies) -> pl_drift_before.json (run BEFORE --apply)
  --check            read-only plan + post-condition checks (+ identity residuals, headline on-screen table -> e19_plan_report.txt)
  --out-dir DIR      write post-apply files under DIR (repo untouched)
  --apply            write the repo files
  --verify           read-only: fresh build from the LIVE gold vs LIVE master; no new drift; planned cells equal
  --revert --apply   restore the scratchpad backups (only while the live files still carry the post-apply hashes)
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
OLD_EV = ROOT / "data" / "_derived" / "kyobo_pl_restate_dryrun_20261021"
EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e19_latest_comparative" / "apply"
BACKUP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e19_backup")
CSM_EV = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
CODES = ["KR0005", "KR0032", "KR0070", "KR0082", "KR0083", "KR0087", "KR0104"]
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")
for p in (str(ROOT / "scripts"), str(ROOT), str(OLD_EV), str(EV)):
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
TOL = 5e-4
EXPECT = {"gold_added": 171, "null_dangi_added": 17, "set_dangi_added": 20, "census_old": (495, 29), "census_new": (666, 29)}
MERGE_NOTE_KEY = "merge_note_20261022_e19_latest_comparative"
MERGE_NOTE = ("PL Tier-1 items of 19 buckets of 7 companies (KR0005 2023.3Q-2024.2Q, KR0032 2023.4Q-2024.3Q, KR0070 2024.1Q-3Q, KR0082 2023.3Q, KR0083 2024.1Q-2Q, KR0087 2023.4Q-2024.3Q, KR0104 2023.3Q) "
              "refreshed to the latest-comparative (separate basis, prior cumulative column of the next-year filing) via data/_gold/user_pl_cells.json (+171 set, +17 null_dangi, +20 set_dangi). "
              "The blocks that changed are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. Evidence data/_derived/remaining_20261022/e19_latest_comparative/apply/")
SUBS = [
    ('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")'),
    ('PL_SRC = ROOT / "PL_breakdown.json"', 'PL_SRC = Path(os.environ["EMIT_PL_SRC"])'),
    ('PL_OVR = ROOT / "data" / "_gold" / "user_pl_cells.json"', 'PL_OVR = Path(os.environ["EMIT_PL_OVR"])'),
    ('PL_OUT = ROOT / "PL_breakdown_provenance.json"', 'PL_OUT = Path(os.environ["EMIT_PL_OUT"])'),
]
DOC_NULL = ("2026-10-22 ticket 20261022T0900Z (parser/ifrs17, owner go 2026-10-22 'latest comparative for the other companies, same as Kyobo'): 값_당분기 forced blank for KR0032 2023.4Q items 17/19/20/22/23/24/25/27 "
            "and KR0087 2023.4Q items 17/19/20/22/23/24/25/27/31. The 4Q cumulative is now the restated annual comparative while the 9M cumulative of the same year is still the original print "
            "(the FY2024 Q1-Q3 reports still print the pre-change 2023 columns) and the annual report prints no 3-month Q4 column, so the builder difference would mix two vintages. Blank beats wrong; "
            "re-derive when a restated 9M-2023 comparative exists.")
DOC_SET = ("2026-10-22 ticket 20261022T0900Z (parser/ifrs17): 값_당분기 = the 3-month column printed in the later filing for single quarters whose two cumulatives are on different vintages: "
           "KR0005 2023.3Q items 20/22/23/24 (FY2024 Q3 3-month column, restated), KR0082 2023.3Q items 1/16/17/18 (FY2024 Q3 prior 3-month column), KR0083 2024.3Q items 17/19/20/22/23/24/25/27 "
           "(FY2025 Q3 prior 3-month column PFY2024dTQQ), KR0104 2023.3Q items 16/22/23/24 (FY2024 Q3 prior 3-month column). 5th element = the cell line / derivation; 값 (cumulative) is kept.")


def rkey(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def load_json(rel_or_path):
    p = Path(rel_or_path)
    if not p.is_absolute():
        p = ROOT / rel_or_path
    return json.loads(p.read_text(encoding="utf-8"))


MAN = json.loads((EV / "e19_manifest.json").read_text(encoding="utf-8"))


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOL


# --------------------------------------------------------------------------- plan pieces
def guard_live_matches_plan(live_rows, gold_obj):
    cur = {rkey(r): r for r in live_rows}
    have = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in gold_obj["set"]}
    bad = []
    for g in MAN["gold_set"]:
        k = (g["원보험사코드"], g["항목번호"], g["공시분기"])
        r = cur.get(k)
        if r is None:
            bad.append(("row missing", k))
        elif not same(r.get("값"), g["was"]):
            bad.append(("expected old value", k, g["was"], r.get("값")))
        if k in have:
            bad.append(("gold already has", k))
    if bad:
        raise SystemExit(f"ABORT: live PL cells moved since the plan was made (concurrent session?) or gold overlap: {bad[:6]} ... ({len(bad)})")


def build_gold(live_gold):
    g = copy.deepcopy(live_gold)
    for e in MAN["gold_set"]:
        g["set"].append({"원보험사코드": e["원보험사코드"], "항목번호": e["항목번호"], "공시분기": e["공시분기"], "값": e["값"], "was": e["was"], "note": e["note"]})
    nd = g.setdefault("null_dangi", {"cells": []})
    sd = g.setdefault("set_dangi", {"cells": []})
    have_n = {tuple(x) for x in nd["cells"]}
    have_s = {(x[0], x[1], int(x[2])) for x in sd["cells"]}
    for c, q, i in MAN["null_dangi"]:
        if (c, q, i) in have_n or (c, q, i) in have_s:
            raise SystemExit(f"ABORT: dangi list already has {(c, q, i)}")
        nd["cells"].append([c, q, i])
    for c, q, i, v, src in MAN["set_dangi"]:
        if (c, q, i) in have_n or (c, q, i) in have_s:
            raise SystemExit(f"ABORT: dangi list already has {(c, q, i)}")
        sd["cells"].append([c, q, i, v, src])
    nd["_doc_e19_20261022"] = DOC_NULL
    sd["_doc_e19_20261022"] = DOC_SET
    return g


def simulate_rows(gold_obj, tag):
    tmpdir = BACKUP / "tmp_apply"
    tmpdir.mkdir(parents=True, exist_ok=True)
    gp, mp = tmpdir / f"gold_{tag}.json", tmpdir / f"master_{tag}.json"
    gp.write_text(json.dumps(gold_obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    sim_rows, _n = S.simulate(gp, mp)
    for p in (gp, mp):
        try:
            p.unlink()
        except OSError:
            pass
    return sim_rows


def drift_vs_live(live_rows, sim_rows):
    sim_by = {rkey(r): r for r in sim_rows}
    if len(sim_rows) != len(live_rows):
        raise SystemExit(f"ABORT: builder row count {len(sim_rows)} != live {len(live_rows)}")
    out = []
    for r in live_rows:
        s = sim_by.get(rkey(r))
        if s is None:
            raise SystemExit(f"ABORT: {rkey(r)} missing from the builder simulation")
        if (r["값"], r.get("값_당분기")) != (s["값"], s.get("값_당분기")):
            out.append(rkey(r))
    return out


def build_master(live_rows, base_rows, new_rows_sim):
    """Cell-level: delta = cells where the sim with the NEW gold differs from the sim with the LIVE gold; those cells (both 값 and 값_당분기) are taken from the new sim."""
    base_by = {rkey(r): r for r in base_rows}
    new_by = {rkey(r): r for r in new_rows_sim}
    if set(base_by) != set(new_by):
        raise SystemExit("ABORT: base and new builder simulations have different row sets")
    delta = {k for k in base_by if (base_by[k]["값"], base_by[k].get("값_당분기")) != (new_by[k]["값"], new_by[k].get("값_당분기"))}
    out, val_changed, dangi_changed, pre_drift_on_delta = [], [], [], []
    for r in live_rows:
        k = rkey(r)
        if k in delta:
            s = new_by[k]
            b = base_by[k]
            if (r["값"], r.get("값_당분기")) != (b["값"], b.get("값_당분기")):
                pre_drift_on_delta.append((k, r["값"], r.get("값_당분기"), b["값"], b.get("값_당분기")))
            nr = dict(r)
            nr["값"], nr["값_당분기"] = s["값"], s["값_당분기"]
            out.append(nr)
            if nr["값"] != r["값"]:
                val_changed.append(k)
            if nr["값_당분기"] != r.get("값_당분기"):
                dangi_changed.append(k)
        else:
            out.append(r)
    return out, delta, val_changed, dangi_changed, pre_drift_on_delta


def emitter_copy_is_current():
    src = (ROOT / "scripts" / "emit_pl_provenance.py").read_text(encoding="utf-8")
    for old, new in SUBS:
        if src.count(old) != 1:
            return False
        src = src.replace(old, new)
    return src == (OLD_EV / "emit_pl_provenance_sandbox_copy.py").read_text(encoding="utf-8")


def run_emitter(rows_sub, gold_obj, tag):
    d = BACKUP / "tmp_emit"
    d.mkdir(parents=True, exist_ok=True)
    src, gold, out = d / f"src_{tag}.json", d / f"gold_{tag}.json", d / f"prov_{tag}.json"
    src.write_text(json.dumps(rows_sub, ensure_ascii=False), encoding="utf-8", newline="\n")
    gold.write_text(json.dumps(gold_obj, ensure_ascii=False), encoding="utf-8", newline="\n")
    if out.exists():
        out.unlink()
    env = dict(os.environ, EMIT_PL_SRC=str(src), EMIT_PL_OVR=str(gold), EMIT_PL_OUT=str(out), PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, str(OLD_EV / "emit_pl_provenance_sandbox_copy.py")], cwd=str(ROOT), env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    (d / f"emit_{tag}.log").write_text((p.stdout or "") + "\n--- stderr ---\n" + (p.stderr or ""), encoding="utf-8", newline="\n")
    if p.returncode != 0 or not out.exists():
        raise SystemExit(f"ABORT: sandbox emitter failed (rc={p.returncode}), see {d / f'emit_{tag}.log'}")
    return json.loads(out.read_text(encoding="utf-8"))


def build_prov(live_prov, emit_new, emit_live):
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_new["cells"]}
    el = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_live["cells"]}
    targets = sorted(k for k in ek if el.get(k) != ek[k])
    new = copy.deepcopy(live_prov)
    lk = {(c["company_code"], c["quarter"], c["item_block"]): i for i, c in enumerate(new["cells"])}
    replaced, live_not_equal_emit = 0, []
    for k in targets:
        if k not in lk:
            raise SystemExit(f"ABORT: provenance block {k} missing from the live sidecar")
        if live_prov["cells"][lk[k]] != el.get(k):
            live_not_equal_emit.append(k)
        new["cells"][lk[k]] = ek[k]
        replaced += 1
    if MERGE_NOTE_KEY in new:
        raise SystemExit("ABORT: merge note key already present")
    new[MERGE_NOTE_KEY] = MERGE_NOTE
    return new, targets, live_not_equal_emit


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
    comment = ("# 2026-10-22 ticket 20261022T0900Z (parser/ifrs17, 19 buckets of 7 companies refreshed to the latest comparative): PL gold %d->%d cells, masked %d->%d (no new pins).\n"
               % (census_old[0], census_new[0], census_old[1], census_new[1]))
    return raw[:m.start()] + comment + m.group(1) + "(%d, %d)" % census_new + m.group(4) + raw[m.end():]


IDENT = [
    ("20-(1+17)", lambda v: _d(v, 20, (1, 17))),
    ("22-(20+21)", lambda v: _d(v, 22, (20, 21))),
    ("|22-24|-|23|", lambda v: None if any(v.get(i) is None for i in (22, 23, 24)) else abs(abs(v[22] - v[24]) - abs(v[23]))),
    ("31-(24+25)", lambda v: _d(v, 31, (24, 25))),
    ("25-(26+27+28+29+30+32)", lambda v: None if v.get(25) is None else v[25] - sum((v.get(i) or 0) for i in (26, 27, 28, 29, 30, 32))),
    ("17-(18+19)", lambda v: _d(v, 17, (18, 19))),
]


def _d(v, a, bs):
    if v.get(a) is None or any(v.get(b) is None for b in bs):
        return None
    return v[a] - sum(v[b] for b in bs)


def vec(rows_by, code, q):
    return {i: rows_by[(code, i, q)]["값"] for i in range(1, 33) if (code, i, q) in rows_by}


def identity_report(live_rows, new_rows):
    lb = {rkey(r): r for r in live_rows}
    nb = {rkey(r): r for r in new_rows}
    lines, worst = [], 0.0
    for code, q in MAN["adopted_buckets"]:
        vo, vn = vec(lb, code, q), vec(nb, code, q)
        parts = []
        for name, f in IDENT:
            a, b = f(vo), f(vn)
            parts.append(f"{name}: {('-' if a is None else f'{a:+.3f}')} -> {('-' if b is None else f'{b:+.3f}')}")
            if b is not None:
                worst = max(worst, abs(b))
        lines.append(f"  {code} {q}: " + "; ".join(parts))
    return lines, worst


def headline_report(live_rows, new_rows):
    lb = {rkey(r): r for r in live_rows}
    nb = {rkey(r): r for r in new_rows}
    nm = {1: "보험손익", 17: "투자손익", 24: "당기순이익", 25: "기타포괄손익"}
    f = lambda v: "blank" if v is None else f"{v / 100:,.2f}"
    lines = ["adopted buckets, 억원 (1억 = 100백만). 누계(값) before -> after | 단일분기(값_당분기) before -> after"]
    for code, q in MAN["adopted_buckets"]:
        for it, name in nm.items():
            a, b = lb.get((code, it, q)), nb.get((code, it, q))
            if a is None or b is None:
                continue
            if a["값"] == b["값"] and a.get("값_당분기") == b.get("값_당분기"):
                continue
            lines.append(f"  {code} {q} {name:6s}: 누계 {f(a['값']):>12s} -> {f(b['값']):>12s} | 단일분기 {f(a.get('값_당분기')):>12s} -> {f(b.get('값_당분기')):>12s}")
    return lines


EXPECTED_EXPLAINED = {("KR0104", 32, "2023.4Q")}   # plan assumed the item-32 refresh of 2023.3Q; that single cell is excluded (masked gold), its 2023.4Q single quarter stays as before


def plan_dangi_check(new_by):
    """Every single-quarter value a plan lists (auto_follow_cells / neighbour_effects / side_effect_single_quarters) must equal the real build with the new gold."""
    E = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
    bad, n = [], 0
    for code in CODES:
        plan = json.loads((E / f"plan_{code}.json").read_text(encoding="utf-8"))
        for lst, key in (("auto_follow_cells", "derived_after"), ("auto_follow_cells", "derived_after_adoption"), ("neighbour_effects", "derived_after_adoption"),
                         ("side_effect_single_quarters", "new_dangi")):
            for e in plan.get(lst) or []:
                if key not in e:
                    continue
                k = (code, e["item"], e["quarter"])
                if k in EXPECTED_EXPLAINED:
                    continue
                n += 1
                got = new_by[k].get("값_당분기")
                exp = e[key]
                if not (same(got, exp)):
                    bad.append((k, exp, got))
    print(f"plan single-quarter expectations checked: {n}, differing: {len(bad)}")
    return bad


def plan_all():
    live = {k: ak.JsonFile(rel) for k, rel in F.items()}
    guard_live_matches_plan(live["PL"].obj, live["GOLD"].obj)
    new_gold = build_gold(live["GOLD"].obj)
    base_rows = simulate_rows(live["GOLD"].obj, "base")
    new_sim = simulate_rows(new_gold, "new")
    new_rows, delta, val_changed, dangi_changed, pre_drift_on_delta = build_master(live["PL"].obj, base_rows, new_sim)

    errs = []
    want = {(g["원보험사코드"], g["항목번호"], g["공시분기"]): g["값"] for g in MAN["gold_set"]}
    base_by = {rkey(r): r for r in base_rows}
    new_by = {rkey(r): r for r in new_sim}
    if set(val_changed) != set(want):
        errs.append(f"값 changed set != plan set: only-in-sim {sorted(set(val_changed) - set(want))[:6]} only-in-plan {sorted(set(want) - set(val_changed))[:6]}")
    # the builder's baseline for a planned cell must be the plan 'was' value, the new one the plan value
    for g in MAN["gold_set"]:
        k = (g["원보험사코드"], g["항목번호"], g["공시분기"])
        if not same(base_by[k]["값"], g["was"]):
            errs.append(f"baseline build value {k}: {base_by[k]['값']} != was {g['was']}")
        if new_by[k]["값"] != g["값"]:
            errs.append(f"new build value {k}: {new_by[k]['값']} != plan {g['값']}")
    if len(val_changed) != EXPECT["gold_added"]:
        errs.append(f"counts: 값 {len(val_changed)} (exp {EXPECT['gold_added']})")
    bad_codes = sorted({k[0] for k in delta} - set(CODES))
    if bad_codes:
        errs.append(f"delta touches other companies: {bad_codes}")
    for c, q, i in MAN["null_dangi"]:
        r = new_by[(c, i, q)]
        if r["값_당분기"] is not None or r["값"] is None:
            errs.append(f"null_dangi cell {(c, q, i)} not blank/with cumulative: {(r['값'], r['값_당분기'])}")
    for c, q, i, v, _src in MAN["set_dangi"]:
        r = new_by[(c, i, q)]
        if r["값_당분기"] != float(v) or r["값"] is None:
            errs.append(f"set_dangi cell {(c, q, i)}: {(r['값'], r['값_당분기'])} != {v}")
    # per-company expectation from the plans (where a plan states one)
    by_co = {}
    for k in dangi_changed:
        by_co[k[0]] = by_co.get(k[0], 0) + 1
    exp_dangi = {"KR0032": 40, "KR0070": 32, "KR0087": 41, "KR0082": 8, "KR0083": 24, "KR0104": 21}   # KR0104: plan 22 minus 2023.4Q item 32 (item 32 of 2023.3Q is not adopted, see EXCLUDE)
    for c, n in exp_dangi.items():
        if by_co.get(c, 0) != n:
            errs.append(f"{c}: 값_당분기 cells changed {by_co.get(c, 0)} != plan expectation {n}")

    exp_bad = plan_dangi_check(new_by)
    if exp_bad:
        errs.append(f"plan single-quarter expectations differ from the build on {len(exp_bad)} cells: {exp_bad[:8]}")
    if not emitter_copy_is_current():
        errs.append("the sandbox emitter copy no longer matches scripts/emit_pl_provenance.py")
    sub_new = [r for r in new_rows if r["원보험사코드"] in CODES]
    sub_live = [r for r in live["PL"].obj if r["원보험사코드"] in CODES]
    emit_new = run_emitter(sub_new, new_gold, "apply_new")
    emit_live = run_emitter(sub_live, live["GOLD"].obj, "apply_live")
    new_prov, prov_targets, prov_live_ne = build_prov(live["PROV"].obj, emit_new, emit_live)

    pin_obj = load_json(PIN_REL)
    census_old, un0, dr0, st0 = census_pl(live["GOLD"].obj, pin_obj)
    census_new, un1, dr1, st1 = census_pl(new_gold, pin_obj)
    if census_old != EXPECT["census_old"] or census_new != EXPECT["census_new"] or un1 or dr1 or st1:
        errs.append(f"census {census_old}->{census_new} (expected {EXPECT['census_old']}->{EXPECT['census_new']}); unpinned={un1} drift={dr1} stale={st1}")
    test_raw = (ROOT / TEST_REL).read_text(encoding="utf-8")
    new_test = new_test_text(test_raw, census_old, census_new)

    snap_path = EV / "pl_drift_before.json"
    other_drift_now = [k for k in drift_vs_live(live["PL"].obj, base_rows)]
    if not snap_path.exists():
        errs.append("pl_drift_before.json missing: run --snapshot-drift before the apply")
    else:
        before = {tuple(x) for x in json.loads(snap_path.read_text(encoding="utf-8"))["drift_all"]}
        if before != set(other_drift_now):
            errs.append(f"live-vs-baseline drift changed vs snapshot: {len(before)} -> {len(other_drift_now)}")
    return dict(live=live, new_gold=new_gold, new_rows=new_rows, delta=delta, val_changed=val_changed, dangi_changed=dangi_changed,
                pre_drift_on_delta=pre_drift_on_delta, new_prov=new_prov, prov_targets=prov_targets, prov_live_ne=prov_live_ne,
                census=(census_old, census_new), test_raw=test_raw, new_test=new_test, errs=errs, by_co=by_co, drift_now=other_drift_now)


def report(P):
    out = []
    pr = out.append
    pr(f"gold: set +{len(P['new_gold']['set']) - len(P['live']['GOLD'].obj['set'])} -> {len(P['new_gold']['set'])}; null_dangi cells {len(P['new_gold']['null_dangi']['cells'])}; set_dangi cells {len(P['new_gold']['set_dangi']['cells'])}")
    pr(f"master: 값 changed {len(P['val_changed'])}, 값_당분기 changed {len(P['dangi_changed'])} (dangi-only {len(set(P['dangi_changed']) - set(P['val_changed']))}); delta cells {len(P['delta'])}")
    pr(f"  dangi changed per company: {dict(sorted(P['by_co'].items()))}")
    pr(f"  live differs from the fresh baseline build on {len(P['pre_drift_on_delta'])} delta cells (pre-existing; the apply replaces them with the new build): ")
    for x in P["pre_drift_on_delta"][:40]:
        pr(f"     {x}")
    only_q = sorted(set(P["dangi_changed"]) - set(P["val_changed"]), key=lambda k: (k[0], k[2], k[1]))
    by_q = {}
    for c, i, q in only_q:
        by_q.setdefault((c, q), []).append(i)
    pr("  derived-only 당분기 cells: " + json.dumps({f"{c} {q}": sorted(v) for (c, q), v in sorted(by_q.items())}, ensure_ascii=False))
    pr(f"provenance: {len(P['prov_targets'])} blocks replaced (live sidecar != emitter(live) on {len(P['prov_live_ne'])} of them) + merge note")
    pr(f"census PL (gold cells, masked): {P['census'][0]} -> {P['census'][1]}")
    il, worst = identity_report(P["live"]["PL"].obj, P["new_rows"])
    pr(f"identity residuals before -> after per adopted bucket (백만원); worst |after| = {worst:.4f}")
    out += il
    out += headline_report(P["live"]["PL"].obj, P["new_rows"])
    pr("errors: " + (str(P["errs"]) if P["errs"] else "none"))
    txt = "\n".join(out)
    print(txt)
    return txt


def outputs(P):
    L = P["live"]
    return {F["GOLD"]: ak.JsonFile._dump(P["new_gold"], *L["GOLD"].fmt), F["PL"]: ak.JsonFile._dump(P["new_rows"], *L["PL"].fmt),
            F["PROV"]: ak.JsonFile._dump(P["new_prov"], *L["PROV"].fmt), TEST_REL: P["new_test"].encode("utf-8")}


def snapshot_drift():
    live_rows = load_json(F["PL"])
    gold = load_json(F["GOLD"])
    base = simulate_rows(gold, "snapshot")
    drift = drift_vs_live(live_rows, base)
    by = {}
    for k in drift:
        by[k[0]] = by.get(k[0], 0) + 1
    out = {"made_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "drift_all": [list(k) for k in drift], "by_company": by,
           "drift_in_target_companies": sorted([list(k) for k in drift if k[0] in CODES], key=lambda x: (x[0], x[2], x[1]))}
    (EV / "pl_drift_before.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"snapshot: cells where a fresh build_pl() with the live gold differs from the live master: {len(drift)} (target companies {sum(v for c, v in by.items() if c in CODES)})")
    print("  by company:", dict(sorted(by.items())))
    for k in out["drift_in_target_companies"]:
        print("   target-company drift", k)


def verify():
    live_rows = load_json(F["PL"])
    gold = load_json(F["GOLD"])
    base = simulate_rows(gold, "verify")
    drift_now = set(drift_vs_live(live_rows, base))
    snap = {tuple(x) for x in json.loads((EV / "pl_drift_before.json").read_text(encoding="utf-8"))["drift_all"]}
    planned = {(g["원보험사코드"], g["항목번호"], g["공시분기"]) for g in MAN["gold_set"]}
    nd = {(c, i, q) for c, q, i in MAN["null_dangi"]} | {(c, i, q) for c, q, i, _v, _s in MAN["set_dangi"]}
    by = {rkey(r): r for r in live_rows}
    bs = {rkey(r): r for r in base}
    ok1 = all(by[k]["값"] == bs[k]["값"] for k in planned)
    ok1b = all(by[k]["값_당분기"] == bs[k]["값_당분기"] for k in nd)
    new_drift = drift_now - snap
    ok2 = not new_drift
    fixed = snap - drift_now
    print(f"verify: planned 값 cells equal to a fresh build ({len(planned)}) -> {'OK' if ok1 else 'FAIL'}; null/set dangi cells equal ({len(nd)}) -> {'OK' if ok1b else 'FAIL'}")
    print(f"verify: drift now {len(drift_now)} vs snapshot {len(snap)}; new drift {len(new_drift)} -> {'OK' if ok2 else 'FAIL ' + str(sorted(new_drift)[:6])}; drift cells that the apply fixed {len(fixed)}")
    other = sorted(k for k in drift_now if k[0] not in CODES)
    print(f"verify: non-target-company drift now {len(other)} (must equal the snapshot's {sum(1 for k in snap if k[0] not in CODES)})")
    ok3 = len(other) == sum(1 for k in snap if k[0] not in CODES)
    sub = [r for r in live_rows if r["원보험사코드"] in CODES]
    emit_doc = run_emitter(sub, gold, "verify")
    live_prov = load_json(F["PROV"])
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live_prov["cells"] if c["company_code"] in CODES}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_doc["cells"] if c["company_code"] in CODES}
    bad = [k for k in lk if lk[k] != ek.get(k)]
    print(f"verify: provenance emitter reproduces {len(lk) - len(bad)}/{len(lk)} target-company blocks")
    for k in sorted(bad)[:10]:
        print("   provenance block differs from emitter:", k)
    return ok1 and ok1b and ok2 and ok3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-drift", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--out-dir")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    backup = BACKUP
    manifest_path = EV / "apply_manifest_e19.json"

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
    txt = report(P)
    (EV / "e19_plan_report.txt").write_text(txt + "\n", encoding="utf-8", newline="\n")
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
