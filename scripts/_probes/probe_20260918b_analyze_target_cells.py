# -*- coding: utf-8 -*-
"""20260918 disclosure PL backfill - Phase 1a 준비: 실제 PL_breakdown.json 결손 (company,quarter)
집합을 계산하고, 기존 프로브 산출(_probe_20260918_disclosure_pl.json) 상태와 교차한다.

목적: 티켓 표를 맹신하지 않고 마스터에서 직접 재확인 -> 정확한 target cell 리스트를 만든다.
산출: data/_derived/_probe_20260918b_target_cells.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MISSING_CODES = ["KR0004", "KR0029", "KR0049", "KR0050", "KR0051", "KR0074", "KR0075", "KR0076",
                  "KR0080", "KR0095", "KR0097", "KR0100", "KR0150", "KR1010", "KR1011", "KR1098"]

# 회사명 (참고용, PL_breakdown.json 원보험사명 필드 확인용)
QUARTERS_STD = [f"{fy}.{q}Q" for fy in (2023, 2024, 2025) for q in (1, 2, 3)] + ["2026.1Q", "2026.2Q"]
ALL_QUARTERS = [f"{fy}.{q}Q" for fy in (2023, 2024, 2025) for q in (1, 2, 3, 4)] + ["2026.1Q", "2026.2Q"]


def main():
    pl_path = os.path.join(ROOT, "PL_breakdown.json")
    rows = json.loads(open(pl_path, encoding="utf-8").read())
    present = set()
    names = {}
    for r in rows:
        code = r.get("원보험사코드")
        q = r.get("공시분기")
        if code in MISSING_CODES:
            present.add((code, q))
            names[code] = r.get("원보험사명", names.get(code, ""))

    missing_cells = []
    for code in MISSING_CODES:
        for q in ALL_QUARTERS:
            if (code, q) not in present:
                missing_cells.append({"code": code, "quarter": q})

    # 확인: 4Q 는 전부 존재해야 정상 (KR0150 제외 가능성 있음)
    q4_missing = [c for c in missing_cells if c["quarter"].endswith("4Q")]

    # 프로브 상태 병합
    probe_path = os.path.join(ROOT, "data", "_derived", "_probe_20260918_disclosure_pl.json")
    probe = json.loads(open(probe_path, encoding="utf-8").read())
    pmap = {(c["code"], c["quarter"]): c for c in probe["cells"]}

    out_cells = []
    for c in missing_cells:
        key = (c["code"], c["quarter"])
        p = pmap.get(key, {})
        out_cells.append({
            "code": c["code"], "name": names.get(c["code"], ""), "quarter": c["quarter"],
            "probe_status": p.get("status", "NOT_PROBED"),
            "source_file": p.get("source_file"),
            "n_fields": p.get("n_fields"),
        })

    by_status = {}
    for c in out_cells:
        by_status.setdefault(c["probe_status"], []).append(f"{c['code']}/{c['quarter']}")

    print("total missing (company,quarter) cells:", len(missing_cells))
    print("q4 missing cells (unexpected unless KR0150-like):", len(q4_missing))
    for c in q4_missing:
        print("  Q4 MISSING:", c["code"], c["quarter"])
    print()
    print("status breakdown:")
    for st, lst in sorted(by_status.items(), key=lambda kv: -len(kv[1])):
        print(f"  {st}: {len(lst)}")
        if st != "OK":
            for item in lst:
                print("     ", item)

    outp = os.path.join(ROOT, "data", "_derived", "_probe_20260918b_target_cells.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump({"note": "PL_breakdown.json 실측 결손 (company,quarter) x probe status 교차",
                    "total_missing": len(missing_cells), "cells": out_cells}, f,
                   ensure_ascii=False, indent=1)
    print("\nwrote:", outp)


if __name__ == "__main__":
    main()
