"""Docling-based PDF -> Markdown parser.

Design notes:

- Memory: PDFs are processed one file at a time, the Docling document
  and its dataframes are explicitly ``del``'d after writing the markdown,
  and ``gc.collect()`` is invoked between files. This is the contract
  enforced by the ``Stage 6-1: Memory Leak`` harness gate.
- Idempotency: each input PDF is fingerprinted (sha256 + size + mtime).
  If a matching markdown exists with the same ``source_sha256`` *and* the
  same ``parse_spec_hash`` (parser profile + keyword window/cap + keyword
  list), the conversion is skipped. If only the PDF bytes match but the
  profile changed, the file is re-parsed. This is the contract enforced
  by the ``Stage 6-3: Idempotency`` harness gate.
- I/O: parsing is the slowest stage in the pipeline. The function below
  yields per-file metrics; ``scripts/run_harness.py`` wraps it with a
  process pool when the user opts into parallel mode.
- Front Matter: every output markdown includes a YAML front matter block
  describing the source PDF, the run id, the parse confidence and the
  effective settings. This metadata is what the JSON build stage keys
  off of.
"""

from __future__ import annotations

import csv
import dataclasses
import gc
import hashlib
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from solvency.config import settings

logger = logging.getLogger(__name__)

# ../.. from this file = <repo>/src (package root for solvency)
_SRC_DIR = Path(__file__).resolve().parents[2]
_MANIFEST_CSV_GLOB = "*_download_cache.csv"
_PERIOD_RE = re.compile(r"^FY(?P<y>\d{4})_Q(?P<q>[1-4])$")
_COMPANY_PDF_STEM = re.compile(r"^(?P<code>KR\d{4})_")
_NUMERIC_RE = re.compile(r"\d")
# Bump when page-selection or docling options change so idempotency re-runs.
# v3: added sub-item keywords (사망/장수/장해/장기재물/해지/사업비/대재해 위험)
# so the sub-item detail tables for 생명장기손해보험위험액 are not skipped.
# v4: added 위험/금리/환율 민감도 keywords + hit-page cap 16→20 — the 6-8 위험민감도
# page only scores ~3 on ratio keywords and fell outside the top-16 cap
# (KR0075 FY2025_Q4: rank 18), dropping the 금리민감도 table from the MD.
_PARSE_PROFILE_VERSION = "docling_partial_v4"

DEFAULT_RATIO_KEYWORDS: tuple[str, ...] = (
    "지급여력비율",
    "지급여력금액",
    "지급여력기준금액",
    "보완자본",
    "생명장기손해보험위험액",
    "일반손해보험위험액",
    "시장위험액",
    "신용위험액",
    "운영위험액",
    # sub-items of 생명장기손해보험위험액
    "사망위험",
    "장수위험",
    "장해",       # 장해·질병위험 / 장해질병위험 variants
    "장기재물",   # 장기재물·기타위험 / 장기재물기타위험 variants
    "해지위험",
    "사업비위험",
    "대재해위험",
    # IFRS 17 assumption-sensitivity / LIC–CSM grid cues (narrow window parse)
    "가정민감도",
    "IFRS17",
    "IFRS 17",
    "보험계약마진",
    "이행현금흐름",
    "잔여보장요소",
    # K-ICS 6-8 위험민감도 (지급여력 금리/환율 민감도 표) — whitespace-normalized
    # matching, so these also hit "위험 민감도" / "금리 민감도 분석" headings.
    "위험민감도",
    "금리민감도",
    "환율민감도",
)


def _mp_worker_init() -> None:
    """Ensure spawned workers can import ``solvency`` (Windows ``spawn``)."""

    if str(_SRC_DIR) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(_SRC_DIR))


@dataclasses.dataclass(frozen=True)
class PdfInput:
    """One PDF queued for conversion.

    ``period`` and ``company_dirname`` jointly determine where the
    output markdown lands under the *quarter-first* layout:

        data/disclosure/<period>/parsed/<company_dirname>.md

    A copy is also written under ``md_inbox/<period>/`` for the JSON
    build stage.
    """

    company_code: str
    company_dirname: str
    period: str
    pdf_path: Path
    fiscal_year: str | None = None
    quarter: str | None = None
    disclosure_date: str | None = None
    keyword_window: int = 1
    fallback_scan_pages: int = 20
    # Increased from 8→16 in v3 so the page picker keeps room for the
    # sub-item detail table (사망/장수/...) when it lives a few pages away
    # from the primary K-ICS detail table. 16→20 in v4 so adding the 민감도
    # page never evicts a page that the v3 top-16 would have kept.
    max_keyword_hit_pages: int = 20
    keyword_terms: tuple[str, ...] = DEFAULT_RATIO_KEYWORDS


@dataclasses.dataclass
class ParseResult:
    """Outcome of a single Docling conversion."""

    company_code: str
    pdf_path: Path
    md_path: Path | None
    status: str
    parse_confidence: float | None
    elapsed_seconds: float
    peak_rss_mb: float | None
    error_message: str | None = None


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint(pdf_path: Path) -> dict[str, str]:
    stat = pdf_path.stat()
    return {
        "sha256": _sha256_of(pdf_path),
        "size": str(stat.st_size),
        "mtime": str(int(stat.st_mtime)),
    }


def _parse_spec_hash(item: PdfInput) -> str:
    """Stable hash of parser options + keyword list (not page ranges)."""

    payload = {
        "profile": _PARSE_PROFILE_VERSION,
        "keywords": list(item.keyword_terms),
        "keyword_window": item.keyword_window,
        "max_keyword_hit_pages": item.max_keyword_hit_pages,
        "fallback_scan_pages": item.fallback_scan_pages,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def _find_keyword_pages(
    pdf_path: Path, keyword_terms: tuple[str, ...]
) -> tuple[list[tuple[int, int]], int | None]:
    """Return (1-based hit pages, total pages) using a cheap text scan."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        total = len(reader.pages)
        if total <= 0:
            return [], 0
        terms = tuple("".join(t.split()) for t in keyword_terms if t.strip())
        hits: list[tuple[int, int]] = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            normalized = "".join(text.split())
            matched_count = sum(1 for term in terms if term and term in normalized)
            if matched_count >= 2:
                hits.append((i, matched_count))
                continue
            # Weak single-keyword page still accepted only when it looks table-like.
            if (
                matched_count == 1
                and _NUMERIC_RE.search(text)
                and any(tok in text for tok in ("가.", "나.", "다.", "|"))
            ):
                hits.append((i, 1))
        return hits, total
    except Exception:
        return [], None


def _expand_pages(hit_pages: list[int], total_pages: int, window: int) -> list[int]:
    if not hit_pages:
        return []
    padded: set[int] = set()
    pad = max(0, int(window))
    for p in hit_pages:
        start = max(1, p - pad)
        end = min(total_pages, p + pad)
        padded.update(range(start, end + 1))
    return sorted(padded)


def _pages_to_ranges(pages: list[int]) -> list[tuple[int, int]]:
    if not pages:
        return []
    ranges: list[tuple[int, int]] = []
    start = pages[0]
    prev = pages[0]
    for p in pages[1:]:
        if p == prev + 1:
            prev = p
            continue
        ranges.append((start, prev))
        start = p
        prev = p
    ranges.append((start, prev))
    return ranges


def _select_page_ranges(item: PdfInput) -> tuple[list[tuple[int, int]], str, list[int]]:
    """Pick page ranges for Docling conversion.

    Priority:
    1) keyword hit pages expanded by +-``keyword_window``
    2) first ``fallback_scan_pages`` pages
    """
    scored_hits, total = _find_keyword_pages(item.pdf_path, item.keyword_terms)
    if total is None:
        # pypdf failure: fall back to full conversion.
        return [(1, sys.maxsize)], "pypdf_unavailable_full_fallback", []
    if scored_hits:
        ranked = sorted(scored_hits, key=lambda x: (-x[1], x[0]))
        top_pages = sorted(
            p for p, _ in ranked[: max(1, int(item.max_keyword_hit_pages))]
        )
        pages = _expand_pages(top_pages, total, item.keyword_window)
        return _pages_to_ranges(pages), "keyword_window", top_pages
    if total <= 0:
        return [(1, 1)], "empty_pdf_guard", []
    last = min(total, max(1, int(item.fallback_scan_pages)))
    return [(1, last)], "head_fallback", []


def _format_ranges(ranges: list[tuple[int, int]]) -> str:
    return ";".join(f"{s}-{e}" for s, e in ranges)


def _parse_period(period: str) -> tuple[int, int]:
    """Return (fiscal year int, quarter 1..4) for ``FY2025_Q4`` style labels."""

    m = _PERIOD_RE.match(period.strip())
    if not m:
        raise ValueError(f"unrecognised period: {period!r} (expected FYnnnn_Q[1-4])")
    return int(m.group("y")), int(m.group("q"))


def _period_to_disclosure_date(period: str) -> str:
    """Map period to the reporting-period end date (KICS quarter-end convention).

    Q1 -> June 30 (same calendar year as FY label), Q2 -> Sep 30, Q3 -> Dec 31,
    Q4 -> Mar 31 of the following year.
    """

    y, q = _parse_period(period)
    if q == 1:
        return f"{y:04d}-06-30"
    if q == 2:
        return f"{y:04d}-09-30"
    if q == 3:
        return f"{y:04d}-12-31"
    return f"{y + 1:04d}-03-31"


def _load_manifest_rows(meta_dir: Path) -> list[dict[str, str]]:
    """Load every ``*_download_cache.csv`` under ``_meta/`` (NONLIFE, LIFE, …)."""

    rows: list[dict[str, str]] = []
    if not meta_dir.is_dir():
        return rows
    for path in sorted(meta_dir.glob(_MANIFEST_CSV_GLOB)):
        try:
            with path.open(newline="", encoding="utf-8") as fp:
                reader = csv.DictReader(fp)
                for raw in reader:
                    rows.append({k: (v or "").strip() for k, v in raw.items()})
        except OSError as exc:
            logger.warning("manifest read failed %s: %s", path, exc)
    return rows


def _index_manifest_for_period(
    rows: list[dict[str, str]], period: str
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """(by company_dirname, by company_code) for rows matching ``period``."""

    by_stem: dict[str, dict[str, str]] = {}
    by_code: dict[str, dict[str, str]] = {}
    for r in rows:
        if r.get("period", "") != period:
            continue
        stem = r.get("company_dirname", "")
        code = r.get("company_code", "")
        if stem:
            by_stem[stem] = r
        if code:
            by_code[code] = r
    return by_stem, by_code


def discover_inputs(
    period: str, pdf_root: Path | None = None, disclosure_dir: Path | None = None
) -> list[PdfInput]:
    """Build ``PdfInput`` list from ``<period>/pdf/*.pdf`` plus manifest metadata.

    Filenames must start with ``KRnnnn_``. Amended PDFs (``…_amended``) match
    manifest rows by ``company_code`` when the full stem is not in the cache.
    """

    ddir = disclosure_dir or settings.disclosure_dir
    y, qn = _parse_period(period)
    fy_label = f"FY{y}"
    q_label = f"Q{qn}"
    disc_date = _period_to_disclosure_date(period)
    root = pdf_root or (ddir / period / "pdf")
    if not root.is_dir():
        logger.warning("pdf root missing: %s", root)
        return []

    rows = _load_manifest_rows(ddir / "_meta")
    by_stem, by_code = _index_manifest_for_period(rows, period)
    out: list[PdfInput] = []

    for pdf in sorted(root.glob("*.pdf")):
        stem = pdf.stem
        m = _COMPANY_PDF_STEM.match(stem)
        if not m:
            logger.warning("skip pdf (no KRxxxx_ prefix): %s", pdf.name)
            continue
        code = m.group("code")
        row = by_stem.get(stem) or by_code.get(code)
        fiscal_year = (row or {}).get("fiscal_year") or fy_label
        quarter = (row or {}).get("quarter") or q_label
        out.append(
            PdfInput(
                company_code=code,
                company_dirname=stem,
                period=period,
                pdf_path=pdf.resolve(),
                fiscal_year=fiscal_year,
                quarter=quarter,
                disclosure_date=disc_date,
            )
        )
    return out


def _md_output_path(item: PdfInput) -> Path:
    """Primary markdown output (sits next to the PDF under the period)."""
    return settings.disclosure_parsed_path(
        period=item.period,
        company_dirname=item.company_dirname,
        ext=".md",
    )


def _md_inbox_path(item: PdfInput) -> Path:
    """Mirror copy used by the JSON build stage as a stable inbox."""
    return settings.md_inbox_dir / item.period / f"{item.company_dirname}.md"


def _existing_fingerprint(md_path: Path) -> dict[str, str] | None:
    """Read the front matter of an existing markdown to find its fingerprint."""
    if not md_path.exists():
        return None
    try:
        with md_path.open("r", encoding="utf-8") as fp:
            first = fp.readline()
            if first.strip() != "---":
                return None
            buf: list[str] = []
            for line in fp:
                if line.strip() == "---":
                    break
                buf.append(line)
        meta: dict[str, str] = {}
        for raw in buf:
            if ":" not in raw:
                continue
            key, _, value = raw.partition(":")
            meta[key.strip()] = value.strip().strip('"')
        if "source_sha256" in meta:
            return {
                "sha256": meta["source_sha256"],
                "size": meta.get("source_size", ""),
                "mtime": meta.get("source_mtime", ""),
                "parse_spec_hash": meta.get("parse_spec_hash", ""),
            }
    except OSError:
        return None
    return None


def _peak_rss_mb() -> float | None:
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        return None


def _front_matter(
    item: PdfInput,
    fingerprint: dict[str, str],
    parse_spec_hash: str,
    parse_confidence: float | None,
    run_id: str,
    selected_ranges: list[tuple[int, int]],
    selection_mode: str,
    hit_pages: list[int],
) -> str:
    payload = {
        "run_id": run_id,
        "parse_profile": _PARSE_PROFILE_VERSION,
        "parse_spec_hash": parse_spec_hash,
        "company_code": item.company_code,
        "company_dirname": item.company_dirname,
        "period": item.period,
        "fiscal_year": item.fiscal_year or "",
        "quarter": item.quarter or "",
        "disclosure_date": item.disclosure_date or "",
        "source_pdf": str(item.pdf_path),
        "source_sha256": fingerprint["sha256"],
        "source_size": fingerprint["size"],
        "source_mtime": fingerprint["mtime"],
        "parser": "docling",
        "parser_version": _docling_version(),
        "parse_confidence": parse_confidence if parse_confidence is not None else "",
        "parse_scope": selection_mode,
        "source_page_ranges": _format_ranges(selected_ranges),
        "keyword_hit_pages": ",".join(str(p) for p in hit_pages),
    }
    lines = ["---"]
    for key, value in payload.items():
        lines.append(f'{key}: "{value}"')
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _docling_version() -> str:
    try:
        import docling

        return getattr(docling, "__version__", "unknown")
    except Exception:
        return "not-installed"


# Process-local cached converter so docling layout/TableFormer models are
# loaded once per worker, then reused across every PDF that worker handles.
_DOCLING_CONVERTER = None


def _get_docling_converter():
    global _DOCLING_CONVERTER
    if _DOCLING_CONVERTER is not None:
        return _DOCLING_CONVERTER
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pdf_opts = PdfPipelineOptions(
        do_ocr=False,
        document_timeout=1800.0,
        ocr_batch_size=1,
        layout_batch_size=1,
        table_batch_size=1,
        queue_max_size=8,
    )
    _DOCLING_CONVERTER = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts),
        }
    )
    return _DOCLING_CONVERTER


def _convert_one(item: PdfInput, run_id: str) -> ParseResult:
    """Run Docling on a single PDF and write the markdown output.

    Heavy imports are kept inside the function so the module remains
    importable even when ``docling`` is not installed (e.g. during unit
    testing of the surrounding plumbing).
    """
    start = time.perf_counter()
    md_path = _md_output_path(item)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    fingerprint = _fingerprint(item.pdf_path)
    spec = _parse_spec_hash(item)
    cached = _existing_fingerprint(md_path)
    if (
        cached
        and cached.get("sha256") == fingerprint["sha256"]
        and cached.get("parse_spec_hash") == spec
    ):
        return ParseResult(
            company_code=item.company_code,
            pdf_path=item.pdf_path,
            md_path=md_path,
            status="skipped_idempotent",
            parse_confidence=None,
            elapsed_seconds=time.perf_counter() - start,
            peak_rss_mb=_peak_rss_mb(),
        )

    try:
        # Text-layer PDFs: OCR off avoids RapidOCR/torch and large page RAM spikes.
        # Scanned (image-only) PDFs will yield thin text; quality_check routes to review.
        converter = _get_docling_converter()
        selected_ranges, selection_mode, hit_pages = _select_page_ranges(item)
        markdown_parts: list[str] = []
        confidences: list[float] = []
        for r_start, r_end in selected_ranges:
            conversion = converter.convert(str(item.pdf_path), page_range=(r_start, r_end))
            document = conversion.document
            markdown_parts.append(document.export_to_markdown())
            confidences.append(_estimate_confidence(document))
            del document
            del conversion

        if not markdown_parts:
            raise RuntimeError("no markdown extracted from selected page ranges")

        markdown_body = "\n\n".join(markdown_parts)
        confidence = sum(confidences) / len(confidences) if confidences else None

        front_matter = _front_matter(
            item,
            fingerprint,
            spec,
            confidence,
            run_id,
            selected_ranges=selected_ranges,
            selection_mode=selection_mode,
            hit_pages=hit_pages,
        )
        md_path.write_text(front_matter + markdown_body, encoding="utf-8")

        # Mirror into md_inbox so the JSON build stage has a single
        # place to scan regardless of period.
        inbox_path = _md_inbox_path(item)
        inbox_path.parent.mkdir(parents=True, exist_ok=True)
        inbox_path.write_text(front_matter + markdown_body, encoding="utf-8")

        gc.collect()

        return ParseResult(
            company_code=item.company_code,
            pdf_path=item.pdf_path,
            md_path=md_path,
            status="ok",
            parse_confidence=confidence,
            elapsed_seconds=time.perf_counter() - start,
            peak_rss_mb=_peak_rss_mb(),
        )
    except Exception as exc:
        logger.exception("docling convert failed: %s", item.pdf_path)
        return ParseResult(
            company_code=item.company_code,
            pdf_path=item.pdf_path,
            md_path=None,
            status="failed",
            parse_confidence=None,
            elapsed_seconds=time.perf_counter() - start,
            peak_rss_mb=_peak_rss_mb(),
            error_message=str(exc),
        )


def _estimate_confidence(document: object) -> float:
    """Best-effort confidence score derived from Docling's document tree.

    Docling does not expose a direct confidence number; we approximate it
    by checking how much of the document was recognised as structured
    content (tables, headings) vs. raw text. The returned score is only
    used as a soft signal for the quality gate downstream.
    """
    try:
        tables = getattr(document, "tables", []) or []
        texts = getattr(document, "texts", []) or []
        if not texts:
            return 0.0
        return min(1.0, 0.5 + 0.05 * len(tables))
    except Exception:
        return 0.5


def _make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_serial(items: Iterable[PdfInput]) -> Iterator[ParseResult]:
    """Run docling sequentially. Used by the perf harness as baseline."""
    run_id = _make_run_id()
    for item in items:
        yield _convert_one(item, run_id)
        gc.collect()


def parse_parallel(
    items: Iterable[PdfInput], workers: int = 4
) -> Iterator[ParseResult]:
    """Run docling in a process pool.

    Each PDF is converted in its own process so memory cannot leak
    across files. The pool size is capped by ``workers``; the harness
    decides what value to pass.
    """
    items = list(items)
    if not items:
        return
    if workers <= 1:
        run_id = _make_run_id()
        for item in items:
            yield _convert_one(item, run_id)
            gc.collect()
        return
    run_id = _make_run_id()
    with ProcessPoolExecutor(
        max_workers=workers, initializer=_mp_worker_init
    ) as pool:
        futures = {pool.submit(_convert_one, item, run_id): item for item in items}
        for future in as_completed(futures):
            yield future.result()


def write_metrics(results: Iterable[ParseResult], path: Path) -> None:
    """Persist per-file timing/memory metrics for the perf harness."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "company_code": r.company_code,
            "pdf_path": str(r.pdf_path),
            "md_path": str(r.md_path) if r.md_path else "",
            "status": r.status,
            "parse_confidence": r.parse_confidence,
            "elapsed_seconds": r.elapsed_seconds,
            "peak_rss_mb": r.peak_rss_mb,
            "error_message": r.error_message,
        }
        for r in results
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
