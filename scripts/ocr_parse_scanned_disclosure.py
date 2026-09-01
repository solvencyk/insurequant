#!/usr/bin/env python3
"""OCR parse for 경영공시 PDFs published WITHOUT a text layer.

The parser's docling converter runs with `do_ocr=False` on purpose (text-layer PDFs
only -- OCR off avoids torch and large page RAM spikes). Some insurers publish a
raster-only PDF; for those the normal path yields nothing parseable and
`verify_q2_disclosure_content.py` flags `near-zero text layer`.

This reuses the parser's own plumbing (frontmatter, fingerprints, both output paths,
page-range selection) and only swaps in an OCR-enabled converter (EasyOCR, ko+en).

> [!warning] OCR output is a LEAD, not a source of truth.
> On 미래에셋(KR0079) 2026.2Q, EasyOCR systematically misread the digit '1' as '7'
> (155.3% -> 755.3%, 13,473 -> 73,473, 10,265 -> 70,265, 12,052 -> 72,052) and six
> loaded items were contaminated before a page-render review caught it. Always confirm
> figures against the rendered page (240dpi) and against rule-engine identities before
> writing them into a master.

> [!decision] 2026-09-01 -- do NOT promote --ocr-scale to a pipeline default; prefer
> direct render + vision reading over this script for SCANNED_SECTION cells.
> Measured (inbox `20260901T0420Z`): docling-routed EasyOCR tops out at **5/9** correct
> even at its least-bad scale (2=144dpi; scale 1=3/9, 3=2/9, 4=2/9 -- see
> `_ocr_converter` docstring below). No scale is good enough to trust unattended.
> The 6 newly-flagged `SCANNED_SECTION` cells (KR0071 2024.4Q, KR0079 2023.4Q/2024.4Q/
> 2025.4Q, KR0010 2025.4Q, KR0080 2025.2Q) were resolved WITHOUT running this script at
> all: `fitz.Matrix(dpi/72, dpi/72)` page renders at 150-200dpi, read directly (Claude
> vision, no OCR-engine text pass), cross-checked against K-ICS identities. Measured
> accuracy across ~150 cross-checked cells: 0 mismatches vs the existing master (one
> single-digit misread on the *reader's* side, caught and corrected by the item48==
> item14x50% identity check -- not a scan-quality problem). See
> `scripts/fix_20260901_kr0079_scanned_section_tier2.py` docstring for the full
> per-cell page/render/identity provenance. Keep this script for bulk/unattended
> conversion where nobody will manually verify every page; for a *specific* small cohort
> of scanned cells, direct render+read is both more accurate and faster (no docling
> layout/table-model overhead, no torch inference).

usage:
  python scripts/ocr_parse_scanned_disclosure.py --period FY2026_Q2 --company KR0010
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from solvency.parser import docling_parser as dp  # noqa: E402


def _ocr_converter(ocr_scale: int = 2):
    """Docling OCR converter, with the render scale forced down from docling's default.

    `docling/models/stages/ocr/easyocr_model.py` hardcodes `self.scale = 3` (216 dpi) and
    no pipeline option exposes it (`PdfPipelineOptions.images_scale` does NOT reach the OCR
    path -- verified: scales 1.0/2.0/3.0 produced byte-identical output). 216 dpi is exactly
    where EasyOCR misreads a leading '1' as '7' in the font 미래에셋(KR0079) publishes.

    Measured on KR0079 2026.2Q p19, nine ground-truth figures read off the rendered page:

        ocr scale=1 ( 72 dpi)  3/9 correct
        ocr scale=2 (144 dpi)  5/9 correct     <- default here
        ocr scale=3 (216 dpi)  2/9 correct     <- docling's default
        ocr scale=4 (288 dpi)  2/9 correct

    So scale 2 is the least-bad setting, not a fix: 5/9 still means the MD lies. The
    docstring warning above stands -- confirm every figure against the rendered page.
    """
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.models.stages.ocr import easyocr_model as _em

    _orig_init = _em.EasyOcrModel.__init__

    def _scaled_init(self, *a, **k):
        _orig_init(self, *a, **k)
        self.scale = ocr_scale

    _em.EasyOcrModel.__init__ = _scaled_init  # type: ignore[method-assign]

    opts = PdfPipelineOptions(
        do_ocr=True,
        ocr_options=EasyOcrOptions(lang=["ko", "en"], force_full_page_ocr=True),
        document_timeout=7200.0,
        ocr_batch_size=1,
        layout_batch_size=1,
        table_batch_size=1,
        queue_max_size=8,
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--period", required=True)
    ap.add_argument("--company", required=True, help="KR#### code")
    ap.add_argument(
        "--all-pages", action="store_true",
        help=("Convert every page instead of the keyword window. REQUIRED for scanned "
              "PDFs: page selection reads the PRE-OCR text layer, so a raster-only file "
              "yields keyword_hit_pages='' and falls back to pages 1-20. KB손해(KR0010) "
              "2026.2Q came out at 5,181 chars that way -- 기본자본/보완자본/시장위험 all "
              "0 hits -- because everything past p20 was never converted."))
    ap.add_argument(
        "--ocr-scale", type=int, default=2,
        help="docling OCR 렌더 배율 (72dpi 단위). 기본 2=144dpi, 근거는 _ocr_converter docstring")
    args = ap.parse_args()

    conv = _ocr_converter(args.ocr_scale)
    dp._DOCLING_CONVERTER = conv
    dp._get_docling_converter = lambda: conv  # type: ignore[assignment]

    orig_spec = dp._parse_spec_hash
    dp._parse_spec_hash = lambda item: f"{orig_spec(item)}+easyocr-ko"  # type: ignore[assignment]

    if args.all_pages:
        import fitz

        def _all_pages(item):
            with fitz.open(item.pdf_path) as d:
                n = d.page_count
            return [(1, n)], "all_pages_ocr", []

        dp._select_page_ranges = _all_pages  # type: ignore[assignment]
        dp._parse_spec_hash = lambda item: f"{orig_spec(item)}+easyocr-ko+allpages"  # type: ignore[assignment]

    items = [i for i in dp.discover_inputs(period=args.period)
             if i.company_code == args.company]
    if not items:
        print(f"{args.company} {args.period}: PDF 를 찾지 못했다")
        return 2
    print(f"OCR 변환 시작: {items[0].pdf_path.name} (EasyOCR ko+en, full-page)", flush=True)

    res = dp._convert_one(items[0], run_id=dp._make_run_id())
    print(f"status={res.status} md={res.md_path} elapsed={res.elapsed_seconds:.0f}s")
    if res.md_path and Path(res.md_path).exists():
        print(f"MD chars={len(Path(res.md_path).read_text(encoding='utf-8')):,}")
    print("주의: 이 MD 의 숫자는 확정값이 아니다. 페이지 렌더링과 항등식으로 반드시 재확인할 것.")
    return 0 if res.status != "failed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
