# -*- coding: utf-8 -*-
"""4Q 교차검증: 16개사의 2024.4Q/2025.4Q 를 같은 추출기로 뽑아 PL_breakdown.json(DART 마스터)
과 대조한다. 백필 품질 증거(ticket 자체검산 요청).

산출: data/_derived/_probe_20260918j_4q_crosscheck.json + stdout 표.
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import extract_pl_backfill_disclosure as ex

QUARTERS = ["2024.4Q", "2025.4Q"]


def load_master():
    rows = json.loads(open(os.path.join(ROOT, "PL_breakdown.json"), encoding="utf-8").read())
    idx = {}
    for r in rows:
        code, q = r.get("원보험사코드"), r.get("공시분기")
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        v = r.get("값")
        if v is not None:
            idx[(code, q, it)] = v
    return idx


def main():
    master = load_master()
    results = []
    for code in ex.COMPANIES:
        for q in QUARTERS:
            pdf_path = ex.find_pdf(code, q)
            if pdf_path is None:
                results.append({"code": code, "quarter": q, "status": "NO_PDF"})
                continue
            status, page_no, found, warnings, bbox = ex.find_and_extract(pdf_path)
            manual = ex.MANUAL_VISION_CELLS.get((code, q))
            if manual is not None and not found:
                found = {it: {"value_eok": float(v)} for it, v in manual["values"].items()}
                status = "OK_VISION_MANUAL"
            if not found:
                results.append({"code": code, "quarter": q, "status": status})
                continue
            row = {"code": code, "quarter": q, "status": status, "items": {}}
            for it in ex.ITEM_ORDER:
                if it not in found:
                    continue
                disc_mn = found[it]["value_eok"] * 100  # 백만원
                mast_mn = master.get((code, q, it))
                cell = {"disclosure_mn": round(disc_mn, 3), "master_mn": mast_mn}
                if mast_mn is not None:
                    diff = disc_mn - mast_mn
                    denom = abs(mast_mn) if abs(mast_mn) > 1e-9 else None
                    cell["diff_mn"] = round(diff, 3)
                    cell["pct_err"] = round(100.0 * diff / denom, 2) if denom else None
                results_item = cell
                row["items"][str(it)] = results_item
            results.append(row)

    outp = os.path.join(ROOT, "data", "_derived", "_probe_20260918j_4q_crosscheck.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump({"note": "16개사 x 2024.4Q/2025.4Q x 8항목, 경영공시 추출값 vs PL_breakdown.json(DART) 대조",
                    "results": results}, f, ensure_ascii=False, indent=1)

    # 회사별 오차율 표 (항목1 보험손익, 항목24 당기순이익 대표 + 최대오차 항목)
    print(f"{'code':8}{'quarter':9}{'status':16}{'max_abs_pct_err':>16}  worst_item")
    for r in results:
        if "items" not in r:
            print(f"{r['code']:8}{r['quarter']:9}{r['status']:16}")
            continue
        worst_it, worst_pct = None, -1
        for it, c in r["items"].items():
            pe = c.get("pct_err")
            if pe is not None and abs(pe) > worst_pct:
                worst_pct, worst_it = abs(pe), it
        wstr = f"item{worst_it}={worst_pct:.1f}%" if worst_it else "n/a(no master overlap)"
        print(f"{r['code']:8}{r['quarter']:9}{r['status']:16}{'':16}  {wstr}")
    print("\nwrote:", outp)


if __name__ == "__main__":
    main()
