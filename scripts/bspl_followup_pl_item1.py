#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 6: why the 17 held PL item-1 (보험손익) cells do not close the pl_bridge (read-only).

For every PL candidate still held (status CAND, item 1) it prints the bucket the gate sees: the three standard LOB legs (items 2 / 13 / 14), the extra
LOB legs (2-N), 기타영업수익 / 기타사업비용, the lineage id of the bucket (DISCLOSURE-only buckets with all three legs blank are NOT TESTABLE and skip;
any other lineage is checked strictly with the missing legs filled by 0), the residual the gate would compute with the candidate in place, and the
neighbouring quarters' legs of the same company (to see whether the DART legs exist elsewhere).
Output: data/_derived/bspl_followup_20261011/pl_item1_holds.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_master_tables as V  # noqa: E402  (import only: main() is guarded; nothing is built)

CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "pl_candidates"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "pl_item1_holds.json"
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]


def main():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    name_of = {}
    for r in rows:
        name_of[r["원보험사코드"]] = r["원수사명"]
    pl = V.load_long(V.PL_PATH)
    extra, unk = V.load_pl_extra_lob(V.PL_PATH)
    src = V.pl_cell_source_ids()
    out = []
    for f in sorted(CAND.glob("KR*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        code = d["code"]
        for c in d.get("candidates", []):
            if c.get("item") != 1 or c.get("status") != "CAND":
                continue
            co, q = name_of[code], c["quarter"]
            m = dict(pl.get((co, q), {}))
            leg = {k: m.get(k) for k in V.LOB_KEYS}
            zf = [k for k, v in leg.items() if v is None]
            xlob = extra.get((co, q), 0.0)
            lineage = src.get((co, q))
            cv = c["value_mn"]
            bare = sum(0.0 if v is None else v for v in leg.values()) + xlob
            oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
            cands = [bare] + ([bare + oi - oe] if oi is not None and oe is not None else [])
            diff = min((x - cv for x in cands), key=abs)
            floor = max(0.001 * abs(cv), V.DEFAULT_FLOOR)
            not_testable = lineage == V.PL_DISCLOSURE_SOURCE_ID and len(zf) == len(V.LOB_KEYS) and not xlob
            verdict = "NOT_TESTABLE_SKIP" if not_testable else ("PASS" if abs(diff) <= floor else "FAIL")
            # what the gate would say if the blank 기타영업수익 (item 15) were an explicit 0.0 (the adj form needs both 15 and 16 in the bucket)
            diff_oi0 = (bare + 0.0 - oe - cv) if (oi is None and oe is not None) else None
            # group: which DART leg is missing
            if len(zf) == len(V.LOB_KEYS):
                grp = "C_ALL_LOB_LEGS_BLANK"
            elif leg.get("생명장기손익") is None and (leg.get("자동차손익") or 0.0) == 0.0 and (leg.get("일반손익") or 0.0) == 0.0 and leg.get("자동차손익") is not None:
                grp = "A_LIFE_LEG_2_BLANK_13_14_ZERO"
            elif diff_oi0 is not None and abs(diff_oi0) <= floor:
                grp = "B_ONLY_ITEM15_BLANK"
            else:
                grp = "C_OTHER"
            neigh = {}
            for qq in QS:
                mm = pl.get((co, qq), {})
                neigh[qq] = [mm.get(k) is not None for k in V.LOB_KEYS]
            non_disc = sorted(k for k, v in m.items() if v is not None and k in ("영업이익", "영업외손익", "투자손익", "투자이익", "보험금융손익", "기타포괄손익", "총포괄손익"))
            out.append({"key": f"{code}|1|{q}", "company": co, "candidate_mn": cv, "label": c.get("label"), "how": c.get("how"), "lineage": lineage, "legs": leg, "legs_missing": zf,
                        "extra_lob_sum": xlob, "기타영업수익": oi, "기타사업비용": oe, "residual_if_loaded": round(diff, 1), "floor": round(floor, 1), "verdict": verdict,
                        "group": grp, "residual_if_item15_were_0": None if diff_oi0 is None else round(diff_oi0, 1),
                        "other_cells_in_bucket": non_disc, "neighbour_legs_present(2,13,14)": {qq: v for qq, v in neigh.items()}})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for o in out:
        print(f"{o['key']:<16} {o['company'][:8]:<8} cand={o['candidate_mn'] / 100:>9,.1f}억 lineage={o['lineage']!s:<12} legs_missing={len(o['legs_missing'])}/3 xlob={o['extra_lob_sum']:,.0f} "
              f"기타영업수익={o['기타영업수익']} 기타사업비용={o['기타사업비용']} -> residual {o['residual_if_loaded']:,.1f} (floor {o['floor']:,.1f}) {o['verdict']}  "
              f"[{o['group']}] residual if item15 were 0: {o['residual_if_item15_were_0']}  bucket DART-ish cells: {o['other_cells_in_bucket']}")


if __name__ == "__main__":
    main()
