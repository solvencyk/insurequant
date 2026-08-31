#!/usr/bin/env python3
"""One-off OCR parse for 미래에셋생명(KR0079) FY2026_Q2.

Why this exists: the parser's docling converter runs with `do_ocr=False` on purpose
(text-layer PDFs only -- OCR off avoids torch and large page RAM spikes). 미래에셋's
2026.2Q 경영공시 is published without an OCR layer: 65 pages yield **530 words total /
179 numeric**, with 51-290 images per page. Coordinate reconstruction returns fragments
like '-682당기순이'. So the normal path cannot parse this filing at all.

This reuses the parser's own plumbing -- frontmatter, fingerprints, both output paths,
page-range selection -- and only swaps the converter for an OCR-enabled one (EasyOCR,
Korean+English). Scope is one company and one period; nothing else changes.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/ocr_parse_kr0079_2026q2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from solvency.parser import docling_parser as dp  # noqa: E402

COMPANY = "KR0079"
PERIOD = "FY2026_Q2"


def _ocr_converter():
    """Same converter settings as the parser, with OCR turned on."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions(
        do_ocr=True,
        ocr_options=EasyOcrOptions(lang=["ko", "en"], force_full_page_ocr=True),
        document_timeout=7200.0,   # OCR on 65 image-heavy pages is slow
        ocr_batch_size=1,
        layout_batch_size=1,
        table_batch_size=1,
        queue_max_size=8,
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )


def main() -> int:
    conv = _ocr_converter()

    # Swap the module-level converter so _convert_one uses OCR, and make the cached
    # fingerprint miss (the previous run, if any, was a non-OCR parse of the same bytes).
    dp._DOCLING_CONVERTER = conv
    dp._get_docling_converter = lambda: conv  # type: ignore[assignment]

    orig_spec = dp._parse_spec_hash

    def spec_with_ocr(item):
        return f"{orig_spec(item)}+easyocr-ko"

    dp._parse_spec_hash = spec_with_ocr  # type: ignore[assignment]

    items = [i for i in dp.discover_inputs(period=PERIOD)
             if i.company_code == COMPANY]
    if not items:
        print(f"{COMPANY} {PERIOD}: PDF 를 찾지 못했다")
        return 2
    print(f"OCR 변환 시작: {items[0].pdf_path.name} (EasyOCR ko+en, full-page)", flush=True)

    res = dp._convert_one(items[0], run_id=dp._make_run_id())
    print(f"status={res.status} md={res.md_path} "
          f"conf={res.parse_confidence} elapsed={res.elapsed_seconds:.0f}s")
    if res.md_path and Path(res.md_path).exists():
        txt = Path(res.md_path).read_text(encoding="utf-8")
        print(f"MD chars={len(txt):,}")
    return 0 if res.status not in ("failed",) else 2


if __name__ == "__main__":
    raise SystemExit(main())
