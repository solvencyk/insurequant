#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level applier (parser/ifrs17, ticket 20261022T1800Z STEP 1, owner go 2026-10-22 「쭉 진행」): 21 PL_breakdown buckets of 11 companies refreshed to the latest-comparative
(separate basis, prior cumulative column) values; 9 owner-gold cells replaced (gold == original-vintage print), 75 new gold cells.  Generalised from e19_apply.py (round 18).
Input = e20_plan.json (apply_contract) produced by e20_plan.py and re-read independently by e20_verify_plans.py.

Writes (only these, each guarded + backed up to the session scratchpad):
  data/_gold/user_pl_cells.json            replaced set entries (값/was/note), +new set entries, +null_dangi / +set_dangi cells, -redundant set_dangi cells
  PL_breakdown.json                        ONLY the cells where a REAL build_pl() run (temp copy) with the new gold differs from the same run with the live gold (cell-level)
  PL_breakdown_provenance.json             blocks whose emitter output changes (sandbox copy of scripts/emit_pl_provenance.py; never imported) + one merge note key
  data/_gold/gold_overlay_ledger.json      pins of replaced owner-gold cells that were masked (gold == builder source) and are load-bearing now (3e53aef8 precedent): REMOVED, never added
  tests/test_rule_coverage_manifest.py     GOLD_OVERLAY_CENSUS PL tuple + _TAX22_LATEST_COMPARATIVE_ONLY

  --snapshot-drift   read-only: live master vs a fresh build_pl() with the LIVE gold (all companies) -> pl_drift_before.json (run BEFORE --apply)
  --check            read-only plan + post-condition checks (+ identity residuals, headline on-screen table -> e20_plan_report_apply.txt)
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
EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e20_held_and_remaining" / "apply"
BACKUP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e20_backup")
CSM_EV = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
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

PIN_REL = "data/_gold/gold_overlay_ledger.json"
F = {"PL": "PL_breakdown.json", "GOLD": "data/_gold/user_pl_cells.json", "PROV": "PL_breakdown_provenance.json", "PIN": PIN_REL}
TEST_REL = "tests/test_rule_coverage_manifest.py"
PL_MASTER_SRC = "data/dart/viz/pl_breakdown_master.json"
TOL = 5e-4
PLAN = json.loads((EV / "e20_plan.json").read_text(encoding="utf-8"))
C = PLAN["apply_contract"]
ADOPTED = [(b["code"], b["quarter"]) for b in PLAN["buckets"] if "error" not in b and b.get("cells") and not any(h["code"] == b["code"] and h["quarter"] == b["quarter"] for h in C["held"])]
CODES = sorted({c for c, _q in ADOPTED})
CENSUS_OLD = (666, 29)
MERGE_NOTE_KEY = "merge_note_20261022_e20_latest_comparative_held_remaining"
MERGE_NOTE = ("PL Tier-1 items of 21 buckets of 11 companies (KR0082 2023.1Q-2Q, KR0083 2024.3Q, KR0087 2024.4Q-2025.2Q, KR0032 2023.1Q, KR0104 2024.4Q-2025.2Q, KR0069 2025.1Q-2Q, KR0094 2025.2Q, "
              "KR0070 2025.1Q-2Q, KR0072 2024.4Q (OCI only), KR0068 2024.4Q-2025.2Q, KR0071 2025.1Q-2Q) refreshed to the latest-comparative (separate basis, prior cumulative column of the next-year filing) via "
              "data/_gold/user_pl_cells.json (9 owner-gold cells replaced: gold == original-vintage print; 75 new set cells; null_dangi/set_dangi pins per e20_plan.json). The blocks that changed are the output of "
              "scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. Evidence data/_derived/remaining_20261022/e20_held_and_remaining/apply/")
SUBS = [
    ('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")'),
    ('PL_SRC = ROOT / "PL_breakdown.json"', 'PL_SRC = Path(os.environ["EMIT_PL_SRC"])'),
    ('PL_OVR = ROOT / "data" / "_gold" / "user_pl_cells.json"', 'PL_OVR = Path(os.environ["EMIT_PL_OVR"])'),
    ('PL_OUT = ROOT / "PL_breakdown_provenance.json"', 'PL_OUT = Path(os.environ["EMIT_PL_OUT"])'),
]
DOC_NULL = ("2026-10-22 ticket 20261022T1800Z STEP 1 (parser/ifrs17, owner 「쭉 진행」): 값_당분기 forced blank for single quarters whose two cumulatives sit on different filings / vintages after the adoption. "
            "(a) 2024.4Q: the annual comparative is restated while the 9M cumulative comes from another filing and annual reports print no 3-month Q4 column: KR0083 17/19/20/22/23/24/25/27 (2024.4Q itself is still the original "
            "annual print, only the 9M moved), KR0087 25/26/31/32, KR0104 25/26/31, KR0072 25/26/31, KR0068 25/26/29/31/32. (b) 2025.3Q: the 9M cumulative is still the original print while the 6M is restated and the FY2026 Q3 "
            "report is not filed yet: KR0087 25/26/31/32, KR0104 25/26/31, KR0069 25/26/29/31, KR0094 25/26/31, KR0070 25/26/31, KR0068 25/26/31/32, KR0071 25/26/29/31/32. (c) KR0032 2023.2Q item 16: the live single quarter was "
            "already blank; the 2023.2Q cumulative 41,900 is the 경영공시 0.01억-rounded 6M and the FY2024 Q2 report prints a 3-month 19,796.578 that does not match 6M - restated Q1 (the blank is kept). "
            "Blank beats wrong; re-derive when the FY2025 filings restate the 2024 quarters / the FY2026 Q3 report restates 2025.3Q.")
DOC_SET = ("2026-10-22 ticket 20261022T1800Z STEP 1 (parser/ifrs17): added KR0094 2025.2Q items 25/26/31 = the restated 3-month column printed in the FY2026 half-year report (96,393 / (428,618) / 276,028; "
           "6M restated, the unrestated Q1 comparative of the FY2026 Q1 report is subtracted otherwise: difference -184). REMOVED the e19 pins of KR0082 2023.3Q items 1/16/17/18 and KR0083 2024.3Q items "
           "17/19/20/22/23/24/25/27: after the adoption of KR0082 2023.1Q/2Q and KR0083 2024.3Q both cumulatives of those single quarters are on the latest vintage and the builder derivation equals the printed "
           "3-month value to the won (diff 0.000000, e20_plan.json seams).")


def rkey(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def load_json(rel_or_path):
    p = Path(rel_or_path)
    if not p.is_absolute():
        p = ROOT / rel_or_path
    return json.loads(p.read_text(encoding="utf-8"))


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOL


PLANNED = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}


def guard_live_matches_plan(live_rows, gold_obj):
    cur = {rkey(r): r for r in live_rows}
    gold_by = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold_obj["set"]}
    nd = {tuple(x) for x in gold_obj["null_dangi"]["cells"]}
    sd = {(x[0], x[1], int(x[2])) for x in gold_obj["set_dangi"]["cells"]}
    bad = []
    for e in C["gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        r = cur.get(k)
        if r is None:
            bad.append(("row missing", k))
        elif not same(r.get("값"), e["was"]):
            bad.append(("expected old value", k, e["was"], r.get("값")))
        if k in gold_by:
            bad.append(("gold already has", k))
    for e in C["gold_replace"]:
        k = (e["code"], e["item"], e["quarter"])
        ge = gold_by.get(k)
        oe = e["old_entry"]
        if ge is None:
            bad.append(("gold entry missing", k))
            continue
        if ge != oe:
            bad.append(("gold entry moved since the plan", k))
        r = cur.get(k)
        if r is None or not same(r.get("값"), e["was"]):
            bad.append(("master cell != old gold value", k, e["was"], None if r is None else r.get("값")))
    for c, q, i in C["null_dangi_add"]:
        if (c, q, i) in nd or (c, q, i) in sd:
            bad.append(("null_dangi_add: dangi list already has", (c, q, i)))
    for c, q, i, v, s in C["set_dangi_add"]:
        if (c, q, i) in nd or (c, q, i) in sd:
            bad.append(("set_dangi_add: dangi list already has", (c, q, i)))
    for c, q, i in C["set_dangi_remove"]:
        if (c, q, i) not in sd:
            bad.append(("set_dangi_remove: pin missing", (c, q, i)))
    if bad:
        raise SystemExit(f"ABORT: live files moved since the plan was made (concurrent session?) or overlap: {bad[:6]} ... ({len(bad)})")


def build_gold(live_gold):
    g = copy.deepcopy(live_gold)
    idx = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): i for i, e in enumerate(g["set"])}
    for e in C["gold_replace"]:
        ent = g["set"][idx[(e["code"], e["item"], e["quarter"])]]
        ent["값"], ent["was"], ent["note"] = e["value"], e["was"], e["note"]
    for e in C["gold_new"]:
        g["set"].append({"원보험사코드": e["code"], "항목번호": e["item"], "공시분기": e["quarter"], "값": e["value"], "was": e["was"], "note": e["note"]})
    nd, sd = g["null_dangi"], g["set_dangi"]
    for c, q, i in C["null_dangi_add"]:
        nd["cells"].append([c, q, i])
    for c, q, i, v, src in C["set_dangi_add"]:
        sd["cells"].append([c, q, i, v, src])
    rm = {(c, q, i) for c, q, i in C["set_dangi_remove"]}
    sd["cells"] = [x for x in sd["cells"] if (x[0], x[1], int(x[2])) not in rm]
    nd["_doc_e20_20261022"] = DOC_NULL
    sd["_doc_e20_20261022"] = DOC_SET
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
            if (r["값"], r.get("값_당분기")) != (b["값"], b.get("값_당분기")) and (r["값"], r.get("값_당분기")) != (s["값"], s.get("값_당분기")):
                # live differs from the baseline build (pre-existing drift) AND the apply would change the live cell: not caused by the gold change alone
                pre_drift_on_delta.append((k, r["값"], r.get("값_당분기"), b["값"], b.get("값_당분기"), s["값"], s.get("값_당분기")))
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
    live_not_equal_emit = []
    for k in targets:
        if k not in lk:
            raise SystemExit(f"ABORT: provenance block {k} missing from the live sidecar")
        if live_prov["cells"][lk[k]] != el.get(k):
            live_not_equal_emit.append(k)
        new["cells"][lk[k]] = ek[k]
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


def tax22_sets(rows):
    """failing (company, quarter) keys of the TAX22 source cross-check on `rows`: with the next-year-prior branch (must be empty) and without it (= the latest-comparative-only buckets)"""
    import validate_master_tables as V
    _p, fails, _s = V._check_tax22_crosscheck(rows, quiet=True)
    on = {(f[0], f[1]) for f in fails}
    orig = V._tax22_prior_tier1
    V._tax22_prior_tier1 = lambda *a, **k: None
    try:
        _p2, fails2, _s2 = V._check_tax22_crosscheck(rows, quiet=True)
    finally:
        V._tax22_prior_tier1 = orig
    return on, {(f[0], f[1]) for f in fails2}


DECL_RE = re.compile(r'^(GOLD_OVERLAY_CENSUS = \{"CSM": \(\d+, \d+\), "PL": )\((\d+), (\d+)\)(\})$', re.M)
TAX_OLD = '''{("푸본현대생명보험", q) for q in ("2024.1Q", "2024.2Q")} | {'''
TAX_NEW = '''{("푸본현대생명보험", q) for q in ("2024.1Q", "2024.2Q", "2024.3Q")} | {'''


def new_test_bytes(raw, census_old, census_new, tax_count):
    crlf = b"\r\n" in raw
    s = raw.decode("utf-8").replace("\r\n", "\n")
    ms = list(DECL_RE.finditer(s))
    if len(ms) != 1:
        raise SystemExit(f"ABORT: GOLD_OVERLAY_CENSUS declaration found {len(ms)} times in {TEST_REL}")
    m = ms[0]
    if (int(m.group(2)), int(m.group(3))) != census_old:
        raise SystemExit(f"ABORT: declared PL census {(int(m.group(2)), int(m.group(3)))} != expected old {census_old}")
    comment = ("# 2026-10-22 ticket 20261022T1800Z (parser/ifrs17, STEP 1: 21 held/remaining buckets of 11 companies refreshed to the latest comparative; 9 owner-gold cells replaced in place): "
               "PL gold %d->%d cells, masked %d->%d (no new pins).\n" % (census_old[0], census_new[0], census_old[1], census_new[1]))
    s = s[:m.start()] + comment + m.group(1) + "(%d, %d)" % census_new + m.group(4) + s[m.end():]
    if s.count(TAX_OLD) != 1:
        raise SystemExit("ABORT: the TAX22 푸본현대 2024.1Q/2Q line was not found exactly once")
    s = s.replace(TAX_OLD, TAX_NEW)
    old_c = "분기를 빼면 이 22칸이 FAIL 로 돌아온다(실측).\n"
    if s.count(old_c) != 1:
        raise SystemExit("ABORT: the TAX22 22-cell comment was not found exactly once")
    s = s.replace(old_c, "분기를 빼면 이 22칸이 FAIL 로 돌아온다(실측).\n# 2026-10-22 ticket 20261022T1800Z: 푸본현대생명 2024.3Q 도 최신 비교열로 갱신(세금 불변이 아니다) -> 총 %d칸(실측).\n" % tax_count)
    old_a = "    # (a) 분기를 빼면 최신 비교열로만 통과하는 22칸(교보 4 + 다른 6사 18)이 RED 로 돌아온다 = 이 분기가 실제로 읽힌다"
    if s.count(old_a) != 1:
        raise SystemExit("ABORT: the TAX22 (a) comment was not found exactly once")
    s = s.replace(old_a, "    # (a) 분기를 빼면 최신 비교열로만 통과하는 %d칸(교보 4 + 다른 6사 %d)이 RED 로 돌아온다 = 이 분기가 실제로 읽힌다" % (tax_count, tax_count - 4))
    out = s.replace("\n", "\r\n") if crlf else s
    return out.encode("utf-8")


IDENT = [
    ("20-(1+17)", lambda v: _d(v, 20, (1, 17))),
    ("22-(20+21)", lambda v: _d(v, 22, (20, 21))),
    ("|22-24|-|23|", lambda v: None if any(v.get(i) is None for i in (22, 23, 24)) else abs(abs(v[22] - v[24]) - abs(v[23]))),
    ("31-(24+25)", lambda v: _d(v, 31, (24, 25))),
    ("25-(26+27+28+29+30+32)", lambda v: None if v.get(25) is None or v.get(27) is None else v[25] - sum((v.get(i) or 0) for i in (26, 27, 28, 29, 30, 32))),
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
    for code, q in ADOPTED:
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
    nm = {1: "보험손익", 17: "투자손익", 24: "당기순이익", 25: "기타포괄손익", 31: "총포괄손익"}
    f = lambda v: "blank" if v is None else f"{v / 100:,.2f}"  # noqa: E731
    lines = ["adopted buckets, 억원 (1억 = 100백만). 누계(값) before -> after | 단일분기(값_당분기) before -> after"]
    for code, q in ADOPTED:
        for it, name in nm.items():
            a, b = lb.get((code, it, q)), nb.get((code, it, q))
            if a is None or b is None:
                continue
            if a["값"] == b["값"] and a.get("값_당분기") == b.get("값_당분기"):
                continue
            lines.append(f"  {code} {q} {name:6s}: 누계 {f(a['값']):>12s} -> {f(b['값']):>12s} | 단일분기 {f(a.get('값_당분기')):>12s} -> {f(b.get('값_당분기')):>12s}")
    return lines


def expected_dangi():
    """{(code, item, quarter): expected 값_당분기 after the apply} from the seam analysis"""
    exp = {}
    for s in PLAN["seams"]:
        k = (s["code"], s["item"], s["quarter"])
        if s["proposal"] in ("null_dangi",):
            exp[k] = None
        elif s["proposal"] == "set_dangi":
            exp[k] = s["printed_3m"]["value"]
        elif s["cls"] in ("q1_equals_cumulative", "consistent_both_latest"):
            exp[k] = s["derived_after"]
        # derived_none_before_and_after: not expected to move
    return exp


def plan_all():
    live = {k: ak.JsonFile(rel) for k, rel in F.items()}
    guard_live_matches_plan(live["PL"].obj, live["GOLD"].obj)
    new_gold = build_gold(live["GOLD"].obj)
    base_rows = simulate_rows(live["GOLD"].obj, "base")
    new_sim = simulate_rows(new_gold, "new")
    new_rows, delta, val_changed, dangi_changed, pre_drift_on_delta = build_master(live["PL"].obj, base_rows, new_sim)
    errs = []
    want = {k: e["value"] for k, e in PLANNED.items()}
    base_by = {rkey(r): r for r in base_rows}
    new_by = {rkey(r): r for r in new_sim}
    if set(val_changed) != set(want):
        errs.append(f"값 changed set != plan set: only-in-sim {sorted(set(val_changed) - set(want))[:6]} only-in-plan {sorted(set(want) - set(val_changed))[:6]}")
    for k, e in PLANNED.items():
        if not same(base_by[k]["값"], e["was"]):
            errs.append(f"baseline build value {k}: {base_by[k]['값']} != was {e['was']}")
        if new_by[k]["값"] != e["value"]:
            errs.append(f"new build value {k}: {new_by[k]['값']} != plan {e['value']}")
    bad_codes = sorted({k[0] for k in delta} - set(CODES))
    if bad_codes:
        errs.append(f"delta touches other companies: {bad_codes}")
    exp = expected_dangi()
    # single quarters: every changed cell must be a planned one, with the planned value
    unexpected = sorted(k for k in dangi_changed if (k[0], k[1], k[2]) not in exp and k not in want)
    if unexpected:
        errs.append(f"值_당분기 changed outside the seam plan: {unexpected[:10]} ({len(unexpected)})")
    mism = []
    for (c, i, q), ev in exp.items():
        r = new_by[(c, i, q)]
        got = r["값_당분기"]
        if ev is None:
            if got is not None:
                mism.append(((c, i, q), ev, got))
        elif got is None or abs(got - ev) > 1e-6:
            mism.append(((c, i, q), ev, got))
    if mism:
        errs.append(f"new build 값_당분기 != planned on {len(mism)} cells: {mism[:8]}")
    for c, q, i in C["set_dangi_remove"]:
        pinned = next(float(x[3]) for x in live["GOLD"].obj["set_dangi"]["cells"] if x[0] == c and x[1] == q and int(x[2]) == i)
        got = new_by[(c, i, q)]["값_당분기"]
        if got is None or abs(got - pinned) > 1e-6:
            errs.append(f"removed pin {(c, q, i)}: derived {got} != pinned {pinned}")
    if pre_drift_on_delta:
        errs.append(f"pre-existing live-vs-fresh-build drift on {len(pre_drift_on_delta)} delta cells (the apply would overwrite them): {pre_drift_on_delta[:6]}")
    if not emitter_copy_is_current():
        errs.append("the sandbox emitter copy no longer matches scripts/emit_pl_provenance.py")
    sub_new = [r for r in new_rows if r["원보험사코드"] in CODES]
    sub_live = [r for r in live["PL"].obj if r["원보험사코드"] in CODES]
    emit_new = run_emitter(sub_new, new_gold, "apply_new")
    emit_live = run_emitter(sub_live, live["GOLD"].obj, "apply_live")
    new_prov, prov_targets, prov_live_ne = build_prov(live["PROV"].obj, emit_new, emit_live)
    census_old, un0, dr0, st0 = census_pl(live["GOLD"].obj, live["PIN"].obj)
    census_mid, un1, dr1, st1 = census_pl(new_gold, live["PIN"].obj)
    replaced_keys = {f"PL|{e['code']}|{e['quarter']}|{e['item']}" for e in C["gold_replace"]}
    # a replaced owner-gold cell that WAS masked (gold == builder source, ledger pin) becomes load-bearing once it carries the latest comparative: its pin must go (Kyobo precedent 3e53aef8)
    drop = sorted(dr1)
    if un1 or st1 or not set(drop) <= replaced_keys:
        errs.append(f"ledger: unpinned masked cells {un1} / stale pins {st1} / drifting pins {drop} not all replaced cells")
    new_pin = copy.deepcopy(live["PIN"].obj)
    for k in drop:
        new_pin["entries"].pop(k)
    census_new, un2, dr2, st2 = census_pl(new_gold, new_pin)
    census_expected = (CENSUS_OLD[0] + len(C["gold_new"]), CENSUS_OLD[1] - len(drop))
    if census_old != CENSUS_OLD or census_new != census_expected or un2 or dr2 or st2:
        errs.append(f"census {census_old}->{census_new} (expected {CENSUS_OLD}->{census_expected}); unpinned={un2} drift={dr2} stale={st2}")
    tax_on, tax_off = tax22_sets(new_rows)
    tax_on0, tax_off0 = tax22_sets(live["PL"].obj)
    if tax_on:
        errs.append(f"TAX22 FAIL with the vintage branch on the candidate master: {sorted(tax_on)[:6]}")
    test_raw = (ROOT / TEST_REL).read_bytes()
    new_test = new_test_bytes(test_raw, census_old, census_new, len(tax_off))
    expected_off = tax_off0 | {("푸본현대생명보험", "2024.3Q")}
    if tax_off != expected_off:
        errs.append(f"TAX22 branch-off set != old + 푸본현대 2024.3Q: only-new {sorted(tax_off - expected_off)} only-old {sorted(expected_off - tax_off)}")
    snap_path = EV / "pl_drift_before.json"
    other_drift_now = drift_vs_live(live["PL"].obj, base_rows)
    if not snap_path.exists():
        errs.append("pl_drift_before.json missing: run --snapshot-drift before the apply")
    else:
        before = {tuple(x) for x in json.loads(snap_path.read_text(encoding="utf-8"))["drift_all"]}
        if before != set(other_drift_now):
            errs.append(f"live-vs-baseline drift changed vs snapshot: {len(before)} -> {len(other_drift_now)}")
    by_co = {}
    for k in dangi_changed:
        by_co[k[0]] = by_co.get(k[0], 0) + 1
    return dict(live=live, new_gold=new_gold, new_rows=new_rows, delta=delta, val_changed=val_changed, dangi_changed=dangi_changed, pre_drift_on_delta=pre_drift_on_delta,
                new_prov=new_prov, prov_targets=prov_targets, prov_live_ne=prov_live_ne, census=(census_old, census_new), test_raw=test_raw, new_test=new_test, new_pin=new_pin, pins_dropped=drop,
                errs=errs, by_co=by_co, drift_now=other_drift_now, tax=(len(tax_off0), len(tax_off)))


def report(P):
    out = []
    pr = out.append
    g0, g1 = P["live"]["GOLD"].obj, P["new_gold"]
    pr(f"gold: set {len(g0['set'])} -> {len(g1['set'])} (+{len(g1['set']) - len(g0['set'])}, {len(C['gold_replace'])} replaced in place); null_dangi cells {len(g0['null_dangi']['cells'])} -> {len(g1['null_dangi']['cells'])}; "
       f"set_dangi cells {len(g0['set_dangi']['cells'])} -> {len(g1['set_dangi']['cells'])}")
    pr(f"master: 값 changed {len(P['val_changed'])}, 값_당분기 changed {len(P['dangi_changed'])} (dangi-only {len(set(P['dangi_changed']) - set(P['val_changed']))}); delta cells {len(P['delta'])}")
    pr(f"  dangi changed per company: {dict(sorted(P['by_co'].items()))}")
    pr(f"  live differs from the fresh baseline build on {len(P['pre_drift_on_delta'])} delta cells (pre-existing): {P['pre_drift_on_delta'][:10]}")
    pr(f"provenance: {len(P['prov_targets'])} blocks replaced (live sidecar != emitter(live) on {len(P['prov_live_ne'])} of them) + merge note")
    pr(f"census PL (gold cells, masked): {P['census'][0]} -> {P['census'][1]}; ledger pins dropped (replaced cells that were masked): {P['pins_dropped']}")
    pr(f"tax22 branch-off failing buckets: {P['tax'][0]} -> {P['tax'][1]}")
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
            F["PROV"]: ak.JsonFile._dump(P["new_prov"], *L["PROV"].fmt), F["PIN"]: ak.JsonFile._dump(P["new_pin"], *L["PIN"].fmt), TEST_REL: P["new_test"]}


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
    by = {rkey(r): r for r in live_rows}
    bs = {rkey(r): r for r in base}
    ok1 = all(by[k]["값"] == bs[k]["값"] for k in PLANNED)
    exp = expected_dangi()
    ok1b = all((by[k]["값_당분기"] is None) if v is None else (by[k]["값_당분기"] is not None and abs(by[k]["값_당분기"] - v) <= 1e-6) for k, v in exp.items())
    ok1c = all(by[k]["값_당분기"] == bs[k]["값_당분기"] for k in exp)
    new_drift = drift_now - snap
    ok2 = not new_drift
    fixed = snap - drift_now
    print(f"verify: planned 값 cells equal to a fresh build ({len(PLANNED)}) -> {'OK' if ok1 else 'FAIL'}; planned single-quarter cells equal the plan ({len(exp)}) -> {'OK' if ok1b else 'FAIL'}; equal to a fresh build -> {'OK' if ok1c else 'FAIL'}")
    print(f"verify: drift now {len(drift_now)} vs snapshot {len(snap)}; new drift {len(new_drift)} -> {'OK' if ok2 else 'FAIL ' + str(sorted(new_drift)[:6])}; drift cells that the apply fixed {len(fixed)}")
    other = sorted(k for k in drift_now if k[0] not in CODES)
    snap_other = sum(1 for k in snap if k[0] not in CODES)
    print(f"verify: non-target-company drift now {len(other)} (must equal the snapshot's {snap_other})")
    ok3 = len(other) == snap_other
    sub = [r for r in live_rows if r["원보험사코드"] in CODES]
    emit_doc = run_emitter(sub, gold, "verify")
    live_prov = load_json(F["PROV"])
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live_prov["cells"] if c["company_code"] in CODES}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_doc["cells"] if c["company_code"] in CODES}
    bad = [k for k in lk if lk[k] != ek.get(k)]
    print(f"verify: provenance emitter reproduces {len(lk) - len(bad)}/{len(lk)} target-company blocks")
    for k in sorted(bad)[:10]:
        print("   provenance block differs from emitter:", k)
    return ok1 and ok1b and ok1c and ok2 and ok3


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
    manifest_path = EV / "apply_manifest_e20.json"
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
    (EV / "e20_plan_report_apply.txt").write_text(txt + "\n", encoding="utf-8", newline="\n")
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
    expect = {F["GOLD"]: P["live"]["GOLD"].sha0, F["PL"]: P["live"]["PL"].sha0, F["PROV"]: P["live"]["PROV"].sha0, F["PIN"]: P["live"]["PIN"].sha0, TEST_REL: ak.sha(P["test_raw"])}
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
    manifest_path.write_text(json.dumps({"before_sha256": before, "after_sha256": after, "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, indent=2),
                             encoding="utf-8", newline="\n")
    print("APPLIED:", list(outs))


if __name__ == "__main__":
    main()
