# -*- coding: utf-8 -*-
"""R2_순자산합 회사단위 원문 대조용 덤프. 지정한 (회사코드, 분기) 각각에 대해 raw PDF에서
"건전성감독기준 재무상태표 상의 순자산" 표가 있는 페이지를 찾아 텍스트를 그대로 출력한다.

읽기 전용 — 아무것도 쓰지 않는다. 사람(에이전트)이 출력을 직접 읽고 판정한다.

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_r2_item4_source_dump.py <CODE> <QUARTER>
  예: ... probe_r2_item4_source_dump.py KR0069 2024.4Q
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

import fitz  # noqa: E402


def quarter_to_period(q: str) -> str:
    m = re.match(r"^(\d{4})\.(\d)Q$", q)
    if not m:
        raise SystemExit(f"bad quarter: {q}")
    return f"FY{m.group(1)}_Q{m.group(2)}"


def find_pdf(code: str, period: str) -> Path | None:
    raw_dir = ROOT / "data" / "disclosure" / period / "raw"
    if not raw_dir.is_dir():
        return None
    hits = sorted(raw_dir.glob(f"{code}_*.pdf"))
    return hits[0] if hits else None


KEYWORDS = ["재무상태표 상의 순자산", "순자산", "지급여력금액"]


def dump(code: str, quarter: str) -> None:
    period = quarter_to_period(quarter)
    pdf_path = find_pdf(code, period)
    print(f"===== {code} {quarter}  ({period}) =====")
    if pdf_path is None:
        print("  raw PDF 없음")
        return
    print(f"  {pdf_path.relative_to(ROOT)}")
    doc = fitz.open(pdf_path)
    target_pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if "재무상태표 상의 순자산" in text or ("건전성감독기준" in text and "순자산" in text):
            target_pages.append(i)
    if not target_pages:
        # fallback: any page mentioning "순자산" AND "조정준비금" (item11 label, distinctive)
        for i, page in enumerate(doc):
            text = page.get_text()
            if "순자산" in text and "조정준비금" in text:
                target_pages.append(i)
    if not target_pages:
        print("  키워드 매칭 페이지 없음 (재무상태표 상의 순자산 / 조정준비금)")
        doc.close()
        return
    for i in target_pages[:2]:
        page = doc[i]
        text = page.get_text()
        char_count = len(text.strip())
        print(f"  --- page {i+1} (1-indexed), chars={char_count} ---")
        if char_count < 60:
            print("  [텍스트 밀도 낮음 — 스캔 가능성, 렌더링 필요]")
        print(text)
    doc.close()


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2 != 0:
        print("usage: probe_r2_item4_source_dump.py CODE1 Q1 [CODE2 Q2 ...]")
        return 1
    for i in range(0, len(args), 2):
        dump(args[i], args[i + 1])
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
