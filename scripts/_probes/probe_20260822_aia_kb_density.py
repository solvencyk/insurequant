# -*- coding: utf-8 -*-
"""AIA(KR0080) 6분기 + KB손해(KR0010) 5분기 raw PDF 페이지별 텍스트밀도 + 키워드 스캔.
결과를 파일로 덤프(콘솔 cp949 인코딩 문제 회피)."""
from __future__ import annotations

import json
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
DISCLOSURE = REPO / "data" / "disclosure"
OUT = REPO / "scripts" / "_probes" / "aia_kb_density_out.json"

TARGETS = [
    ("KR0080", "2024.4Q", "FY2024_Q4"),
    ("KR0080", "2025.1Q", "FY2025_Q1"),
    ("KR0080", "2025.2Q", "FY2025_Q2"),
    ("KR0080", "2025.3Q", "FY2025_Q3"),
    ("KR0080", "2025.4Q", "FY2025_Q4"),
    ("KR0080", "2026.1Q", "FY2026_Q1"),
    ("KR0010", "2024.1Q", "FY2024_Q1"),
    ("KR0010", "2024.3Q", "FY2024_Q3"),
    ("KR0010", "2025.3Q", "FY2025_Q3"),
    ("KR0010", "2025.4Q", "FY2025_Q4"),
    ("KR0010", "2026.1Q", "FY2026_Q1"),
]

KEYWORDS = ["공통적용", "보완자본", "한도", "기본자본", "경과조치", "지급여력기준금액",
            "해약환급금", "선택적용"]


def _pdf(period_dir: str, code: str):
    raw = DISCLOSURE / period_dir / "raw"
    pdfs = sorted(raw.glob(f"{code}_*.pdf"))
    if not pdfs:
        return None
    am = [p for p in pdfs if "_amended" in p.name]
    return max(am or pdfs, key=lambda p: p.stat().st_size)


def main():
    results = []
    for code, q, period_dir in TARGETS:
        pdf = _pdf(period_dir, code)
        entry = {"code": code, "quarter": q, "pdf": str(pdf) if pdf else None}
        if pdf is None:
            entry["status"] = "NO_RAW"
            results.append(entry)
            continue
        doc = fitz.open(pdf)
        try:
            n = doc.page_count
            page_info = []
            for i in range(n):
                t = doc[i].get_text()
                kw_hits = [k for k in KEYWORDS if k in t]
                page_info.append({"page0": i, "chars": len(t), "kw": kw_hits})
            total_chars = sum(p["chars"] for p in page_info)
            density = total_chars / n if n else 0
            entry["n_pages"] = n
            entry["total_chars"] = total_chars
            entry["density_per_page"] = round(density, 1)
            entry["pages_with_공통적용+보완자본+한도"] = [
                p["page0"] for p in page_info
                if "공통적용" in p["kw"] and "보완자본" in p["kw"] and "한도" in p["kw"]
            ]
            entry["pages_with_경과조치"] = [p["page0"] for p in page_info if "경과조치" in p["kw"]]
            entry["pages_with_기본자본_only_noKW47"] = [
                p["page0"] for p in page_info if "기본자본" in p["kw"] and "공통적용" not in p["kw"]
            ]
            entry["page_char_counts"] = [p["chars"] for p in page_info]
        finally:
            doc.close()
        results.append(entry)

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
