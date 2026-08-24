"""READ-ONLY. KR1000(코리안리) 면제 재감사용 raw PDF 판독.

7개 필링에서 ① `경과조치 적용 전 지급여력비율` 헤드라인표 ② `공통적용 경과조치` TFI 표가
있는 페이지를 찾아, 그 페이지의 텍스트를 **행 단위(y좌표 클러스터링)** 로 재구성해 인쇄한다.
컬럼 순서를 사람이 직접 확인할 수 있게 x좌표도 같이 찍는다. PDF 는 읽기만 한다.

사용: probe_20260824_reaudit_kr1000_raw.py --out <utf8 파일> [--pages FY2023_Q2:8,9 ...]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]

QUARTERS = [
    ("2023.2Q", "FY2023_Q2"),
    ("2023.3Q", "FY2023_Q3"),
    ("2023.4Q", "FY2023_Q4"),
    ("2024.1Q", "FY2024_Q1"),
    ("2024.2Q", "FY2024_Q2"),
    ("2024.3Q", "FY2024_Q3"),
    ("2024.4Q", "FY2024_Q4"),
]

KEYS = ("경과조치", "보완자본", "기본자본", "순자산", "재분류", "지급여력비율")


def rows_of(page) -> list[tuple[float, list[tuple[float, str]]]]:
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    buckets: dict[int, list[tuple[float, str]]] = {}
    for w in words:
        y = round(w[1] / 3.0)
        buckets.setdefault(y, []).append((w[0], w[4]))
    out = []
    for y in sorted(buckets):
        ws = sorted(buckets[y], key=lambda t: t[0])
        out.append((y * 3.0, ws))
    return out


def fmt_row(y, ws, with_x: bool) -> str:
    if with_x:
        return "  y=%-7.1f | %s" % (y, "  ".join("%s@%.0f" % (t, x) for x, t in ws))
    return "  y=%-7.1f | %s" % (y, " ".join(t for _, t in ws))


def main() -> None:
    out_path = sys.argv[sys.argv.index("--out") + 1]
    forced: dict[str, list[int]] = {}
    if "--pages" in sys.argv:
        for spec in sys.argv[sys.argv.index("--pages") + 1].split():
            fy, pages = spec.split(":")
            forced[fy] = [int(p) for p in pages.split(",")]
    buf: list[str] = []
    for q, fy in QUARTERS:
        pdf = ROOT / "data" / "disclosure" / fy / "raw" / "KR1000_코리안리.pdf"
        buf.append("#" * 90)
        buf.append("### %s  %s" % (q, pdf))
        if not pdf.exists():
            buf.append("  MISSING FILE")
            continue
        doc = fitz.open(pdf)
        buf.append("  pages=%d" % doc.page_count)
        # page census: text length + keyword hits
        cand: list[int] = []
        for i in range(doc.page_count):
            t = doc[i].get_text("text")
            flat = t.replace(" ", "")
            hits = {k: flat.count(k) for k in KEYS}
            if hits["경과조치"] > 0 or (hits["보완자본"] > 0 and hits["기본자본"] > 0):
                cand.append(i)
            buf.append("    p%-3d len=%-6d %s" % (
                i + 1, len(t), " ".join("%s=%d" % (k, v) for k, v in hits.items() if v)))
        pages = forced.get(fy) or [p + 1 for p in cand]
        buf.append("  --- candidate pages (1-base): %s" % pages)
        for p1 in pages:
            page = doc[p1 - 1]
            buf.append("  " + "=" * 84)
            buf.append("  PAGE %d  (text chars=%d)" % (p1, len(page.get_text("text"))))
            for y, ws in rows_of(page):
                line = " ".join(t for _, t in ws)
                flat = line.replace(" ", "")
                mark = "*" if any(k in flat for k in KEYS) or re.search(r"\d", line) else " "
                buf.append(mark + fmt_row(y, ws, with_x=True))
        doc.close()
    io.open(out_path, "w", encoding="utf-8").write("\n".join(buf))
    print("written", out_path)


if __name__ == "__main__":
    main()
