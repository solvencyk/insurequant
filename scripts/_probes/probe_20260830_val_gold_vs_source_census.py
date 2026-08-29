"""validation 2026-08-30 — gold override redundancy / mask census (read-only, offline).

Question this answers: for every entry in data/_gold/user_csm_cells.json::set,
does the BUILDER SOURCE that build_root_masters.build_csm() consumes
(data/dart/viz/csm_waterfall_master_diag.json) already carry the same value?

  * SAME_EXACT / SAME_AT_1DP -> the code reproduces gold (the latter only at the
        diag's own 1-decimal grid). The override is redundant TODAY but still
        silently MASKS any future builder regression on that cell, because
        _apply_csm_overrides() upserts 값 unconditionally and never compares.
  * LOAD_BEARING -> the screen value comes from gold and the builder value is
        invisible to every downstream gate.
  * ROW_ABSENT_IN_SOURCE / NULL_IN_SOURCE -> the builder produces nothing there;
        gold is the only source.

No writes. Imports nothing from the build/validate pipeline.

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/_probes/probe_20260830_val_gold_vs_source_census.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "data" / "_gold" / "user_csm_cells.json"
SRC = ROOT / "data" / "dart" / "viz" / "csm_waterfall_master_diag.json"
OUT = ROOT / "CSM_waterfall.json"

# 억원. Two tiers, because the two files have DIFFERENT granularity:
#   csm_waterfall_master_diag.json rounds to 1 decimal, the gold cells carry 2.
#   So "the code already reproduces gold" can only ever mean "equal at the diag's
#   own 1-decimal grid" (|diff| <= 0.05), never a byte-identical 0.00.
TOL_EXACT = 0.005
TOL_ROUND = 0.05


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def index(rows):
    out = {}
    for r in rows:
        out[(r.get("원보험사코드"), r.get("항목번호"), r.get("공시분기"))] = r
    return out


def main() -> int:
    gold = load(GOLD)
    src = index(load(SRC))
    cur = index(load(OUT))

    tally = Counter()
    rows = []
    for s in gold.get("set", []):
        key = (s["원보험사코드"], s["항목번호"], s["공시분기"])
        gv = s.get("값")
        srow = src.get(key)
        sv = srow.get("값") if srow else None
        crow = cur.get(key)
        cv = crow.get("값") if crow else None
        if srow is None:
            verdict = "ROW_ABSENT_IN_SOURCE"
        elif sv is None:
            verdict = "NULL_IN_SOURCE"
        elif isinstance(sv, (int, float)) and isinstance(gv, (int, float)) \
                and abs(sv - gv) <= TOL_EXACT:
            verdict = "SAME_EXACT"
        elif isinstance(sv, (int, float)) and isinstance(gv, (int, float)) \
                and abs(sv - gv) <= TOL_ROUND:
            verdict = "SAME_AT_1DP"
        else:
            verdict = "LOAD_BEARING"
        tally[verdict] += 1
        rows.append((key, gv, sv, cv, verdict, s.get("was")))

    print(f"gold set entries : {len(gold.get('set', []))}")
    print(f"source rows      : {len(src)}   (csm_waterfall_master_diag.json)")
    print(f"root master rows : {len(cur)}   (CSM_waterfall.json)")
    print()
    for k, v in sorted(tally.items()):
        print(f"  {k:<22} {v}")
    print()
    print("-- LOAD_BEARING / NULL / ABSENT (gold is the only or a differing source) --")
    for key, gv, sv, cv, verdict, was in rows:
        if verdict in ("SAME_EXACT", "SAME_AT_1DP"):
            continue
        d = "" if not isinstance(sv, (int, float)) or not isinstance(gv, (int, float)) \
            else f"  diff={gv - sv:+.2f}"
        print(f"  {key[0]} {key[2]} item{key[1]:<2} verdict={verdict:<22} "
              f"gold={gv} src={sv} root={cv}{d}  was={was}")
    print()
    print("-- SAME_EXACT / SAME_AT_1DP by company/quarter (code reproduces gold) --")
    per = Counter()
    for key, gv, sv, cv, verdict, was in rows:
        if verdict in ("SAME_EXACT", "SAME_AT_1DP"):
            per[(key[0], key[2], verdict)] += 1
    for (co, q, v), n in sorted(per.items()):
        print(f"  {co} {q} {v}: {n} item(s)")

    print()
    print("-- root master vs source, for EVERY gold key (is the screen value gold or code?) --")
    mism = 0
    for key, gv, sv, cv, verdict, was in rows:
        if isinstance(cv, (int, float)) and isinstance(gv, (int, float)) \
                and abs(cv - gv) > TOL_EXACT:
            mism += 1
            print(f"  [!] {key} root={cv} != gold={gv}  (override did not land?)")
    print(f"  root==gold for {len(rows) - mism}/{len(rows)} gold keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
