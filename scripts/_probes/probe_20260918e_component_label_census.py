# -*- coding: utf-8 -*-
"""구성 행 라벨 변형 전수 census -- 수용 등식 E1/E2/E4 를 돌리려면 보험수익/보험서비스비용/
재보험수익/재보험서비스비용/투자수익/투자비용/영업외수익/영업외비용 8개 구성 행을 읽어야 한다.
분류기를 쓰기 전에 실제 라벨 문자열이 회사·연도별로 어떻게 생겼는지 먼저 센다.

산출: data/_derived/_probe_20260918e_component_labels.json
실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260918e_component_label_census.py
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz  # noqa: E402

from extract_pl_backfill_disclosure import (  # noqa: E402
    COMPANIES, ROOT, _core_label_hits, _find_idx_cur, _label_col_text,
    classify, find_pdf, target_cells,
)

fitz.TOOLS.mupdf_display_errors(False)
OUT = os.path.join(ROOT, "data", "_derived", "_probe_20260918e_component_labels.json")


def labels_of(pdf_path, max_pages=40):
    """표를 찾아 (라벨, 값) 쌍의 라벨 문자열을 전부 뱉는다 -- classify() 가 못 잡는 것만."""
    out = []
    doc = fitz.open(pdf_path)
    try:
        n = min(max_pages, doc.page_count)
        for i in range(n):
            page = doc[i]
            t = page.get_text()
            if "포괄손익계산서" not in t or _core_label_hits(t) < 3:
                continue
            try:
                tabs = page.find_tables()
            except Exception:
                continue
            for tab in tabs.tables:
                rows = tab.extract()
                if not rows or len(rows) < 5:
                    continue
                idx_cur = _find_idx_cur(rows)
                if idx_cur is None:
                    continue
                anchored = False
                for row in rows[1:]:
                    if idx_cur >= len(row):
                        continue
                    lab_text = _label_col_text(row, idx_cur)
                    if lab_text is None:
                        continue
                    val_text = row[idx_cur]
                    lab_lines = lab_text.split("\n")
                    val_lines = val_text.split("\n") if isinstance(val_text, str) else []
                    if len(lab_lines) == len(val_lines) and len(lab_lines) > 1:
                        pairs = list(zip(lab_lines, val_lines))
                    else:
                        pairs = [(lab_lines[0], val_lines[0] if val_lines else None)]
                    for lab, val in pairs:
                        lab = (lab or "").strip()
                        if not lab:
                            continue
                        if classify(lab) is not None:
                            anchored = True
                            continue
                        out.append((lab, val))
                if anchored:
                    return out
    finally:
        doc.close()
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    counts = {}
    per_label_cells = {}
    n_seen = 0
    for code, q in target_cells():
        pdf = find_pdf(code, q)
        if pdf is None:
            continue
        n_seen += 1
        try:
            labs = labels_of(pdf)
        except Exception as exc:
            counts.setdefault(f"<ERR {type(exc).__name__}>", 0)
            counts[f"<ERR {type(exc).__name__}>"] += 1
            continue
        for lab, _val in labs:
            counts[lab] = counts.get(lab, 0) + 1
            per_label_cells.setdefault(lab, []).append(f"{code} {q}")
    ordered = sorted(counts.items(), key=lambda kv: -kv[1])
    doc = {
        "n_pdf_cells_scanned": n_seen,
        "n_distinct_unclassified_labels": len(ordered),
        "labels": [{"label": k, "count": v, "sample_cells": per_label_cells.get(k, [])[:3]}
                   for k, v in ordered],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("scanned pdf cells:", n_seen, " distinct labels:", len(ordered))
    for k, v in ordered[:60]:
        print(f"{v:5d}  {k!r}")
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
