# -*- coding: utf-8 -*-
"""KR1104 하노버 2023.3Q ILP items 10-15: the FY2023_Q3 경영공시 PDF is a scan (32 image pages, no text layer).  Pages 23-24 (AI801 재무상태표 detail, 단위 천원) were rendered
at 170 dpi and read by eye (2026-10-12):
    1. 보험계약부채 38,030,466 | 가. 잔여보장요소 944,004 = (1) 최선추정 (36,248,315) + (2) 위험조정 4,651,137 + (3) 보험계약마진 32,541,182 + (4) PAA -
    나. 발생사고요소 37,086,462 = (1) 최선추정 36,505,511 + (2) 위험조정 580,951      (보험계약자산 side: all '-')
Checks (same as load_ilp_reinsurers_lic.py): R-LIC1 item 15 == the filing's own 「(보험계약부채)」 line 38,030,466; R-LIC3 10 + 14 = 15 and 11 + 12 + 13 = 10.
Additive, guarded (lic.merge_into_ilp), provenance cell appended.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_hannover_2023_3q_20261012.py [--write]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_insurance_liability_lic as lic  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROV = ROOT / "insurance_liability_portfolio_provenance.json"
sys.stdout.reconfigure(encoding="utf-8")
TICKET = "inbox/parser/20261012T0120Z__orchestrator__KR1101-KR1108_2023.1Q-2026.2Q__reinsurer_csm_ilp_sensitivity_resweep.md"
F = 1e-5      # 천원 -> 억원
PRINTED = {"total": 38030466, "lrc": 944004, "lrc_bel": -36248315, "lrc_ra": 4651137, "lrc_csm": 32541182, "lic": 37086462, "bel": 36505511, "ra": 580951, "summary": 38030466}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    p = PRINTED
    assert p["lrc_bel"] + p["lrc_ra"] + p["lrc_csm"] == p["lrc"], "LRC components"
    assert p["bel"] + p["ra"] == p["lic"], "LIC components"
    assert p["lic"] + p["lrc"] == p["total"] == p["summary"], "total"
    items = {10: round(p["lic"] * F, 2), 11: round(p["bel"] * F, 2), 12: round(p["ra"] * F, 2), 14: round(p["lrc"] * F, 2), 15: round(p["total"] * F, 2)}
    items[13] = round(items[10] - items[11] - items[12], 2)
    items[13] = 0.0 if abs(items[13]) <= 0.0301 else items[13]
    assert abs(items[10] + items[14] - items[15]) <= 0.0301
    items = dict(sorted(items.items()))
    print(items)
    ilp = json.loads(lic.ILP.read_text(encoding="utf-8"))
    reg = lic.ilp_registry(ilp)
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in ilp}
    rows = []
    for n, v in items.items():
        if ("KR1104", "2023.3Q", n) in have:
            raise SystemExit("key exists")
        name, section, level = lic.ITEM_CATALOG[n]
        info = reg["KR1104"]
        rows.append({"원보험사코드": "KR1104", "원수사명": info["원수사명"], "티커": info["티커"], "생손보여부": info["생손보여부"], "항목번호": n, "항목명": name,
                     "섹션": section, "레벨": level, "공시분기": "2023.3Q", "값": v})
    rec = {"company_code": "KR1104", "quarter": "2023.3Q", "item_block": "lic_pdf_bs", "source_id": "PDF", "as_of_date": lic.as_of_date("2023.3Q"),
           "source_file": "data/disclosure/FY2023_Q3/raw/KR1104_하노버재보험.pdf", "page": [23, 24], "scope": "separate", "period": "current", "class": "A1", "bel_ra_source": "RF",
           "basis": "liability", "row_basis": ["LIAB"], "unit": "천원", "unit_source": "printed 단위: 천원 on p20 (AI801 재무상태표); scanned PDF read by eye at 170 dpi",
           "tables": [], "dropped_tables": [], "dedupe": [],
           "flags": ["pdf_source_no_dart_filing", "reinsurer_branch_balance_sheet_block", "scanned_pdf_no_text_layer_read_by_eye"],
           "checks": {"r_lic1": "pass", "filing_bs_eok": round(p["summary"] * F, 4), "r_lic3_gap_eok": round(items[10] + items[14] - items[15], 4), "r_lic2_vs_2_4": None},
           "net_lrc_eok": items[14], "items_eok": {str(n): v for n, v in items.items()},
           "asset_side_eok": {"total": 0.0, "lrc": 0.0, "lic": 0.0, "note": "보험계약자산 side printed '-' on the same pages"},
           "other_readings": [],
           "evidence": "pages 23-24 rendered at 170 dpi: 1. 보험계약부채 38,030,466 = 가. 잔여보장요소 944,004 (최선추정 -36,248,315 + 위험조정 4,651,137 + 보험계약마진 32,541,182) + 나. 발생사고요소 37,086,462 (최선추정 36,505,511 + 위험조정 580,951); 「(보험계약부채)」 line 38,030,466",
           "note": "scanned 경영공시 (원본 as filed, before the FY2024 restatement of the 2023 year-end); same block definition as the other reinsurer cells"}
    if not a.write:
        print("(dry run)")
        return 0
    backup = lic.merge_into_ilp(rows, tag="pre_hannover_2023_3q")
    raw0 = PROV.read_bytes()
    txt = raw0.decode("utf-8")
    prov = json.loads(txt)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("provenance does not round-trip (master rows ARE written)")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    shutil.copyfile(PROV, lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_hannover_2023_3q.json")
    if any(c.get("company_code") == "KR1104" and c.get("quarter") == "2023.3Q" and c.get("item_block") == "lic_pdf_bs" for c in prov["cells"]):
        raise SystemExit("provenance cell exists")
    prov["cells"] = prov["cells"] + [rec]
    prov["backfills"] = prov.get("backfills", []) + [{"stage": "reinsurers_lic_resweep_scan", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"),
                                                        "emitted_by": "scripts/load_ilp_hannover_2023_3q_20261012.py", "ticket": TICKET,
                                                        "note": "KR1104 2023.3Q items 10-15 read by eye from the scanned FY2023_Q3 경영공시"}]
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes((json.dumps(prov, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    os.replace(tmp, PROV)
    print(f"written {len(rows)} rows; backup {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
