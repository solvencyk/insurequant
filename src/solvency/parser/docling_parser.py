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
# v5 (2026-09-01, inbox 20260831T0700Z): (a) PRIORITY_KEYWORDS pages are exempt
# from the top-N cap — measured, the 6-4 시장위험 opening page scores only 1 and
# was evicted at ranks 21-36 on 8 pages across KR0002/0032/0049/0050/0074/0083/
# 0150; (b) docling PARTIAL_SUCCESS is now inspected and pages it silently
# dropped (std::bad_alloc in the preprocess stage) are re-converted one page at
# a time; (c) source_total_pages / docling_status / docling_*_pages recorded in
# the front matter so the quality gate can see a truncated parse.
_PARSE_PROFILE_VERSION = "docling_partial_v5"

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
    "장해",       # 장해·질병위험 / 장해질병위험 변형
    "장기재물",   # 장기재물·기타위험 / 장기재물기타위험 변형
    "해지위험",
    "사업비위험",
    "대재해위험",
    # sub-items of 시장위험액 (36-40) — each disclosed under its own "N) OOO위험액
    # 현황" heading that does NOT repeat the parent string "시장위험액" verbatim
    # (삼성생명 2026.2Q p.31 "3) 주식위험액현황": literal "시장위험액" occurs 0 times
    # on that page). Without these, a sub-risk page can fall in the gap between two
    # unrelated hits' +-window and get silently excluded from source_page_ranges —
    # confirmed real for 주식위험액 (Samsung 2026.2Q; item37 695,426억, ~94% of
    # item19, entirely missing pre-fix). inbox 20260831T0700Z reports the same
    # class of gap (whole 6-4 section dropped) on 5 other 2026.2Q filers.
    # 2026-09-01: "금리위험액" (item36's own sibling term) was missing from this
    # very list — the previous fix added the other 4 but not this one, so p.29-30
    # ("2) 금리위험액현황") never became a hit page in their own right and stayed
    # dependent on window-bleed from the neighboring 생명장기 (p.27) and 자산집중
    # (p.34) hits, which left a real 2-page hole (p.30-31) that swallowed both
    # 금리위험액 AND 주식위험액 in the same MD run (source_page_ranges "...6-29;
    # 32-47" — the md/master gap the inbox 20260831T0700Z follow-up flagged for
    # KR0069). Confirmed via raw-PDF fitz dump: p.29-30 "Ⅳ.금리위험액" =
    # 1,037,118백만 = item36 exactly; p.31 "3)주식위험액현황 Ⅲ.합계"=69,542,621백만
    # = item37 exactly. Adding this term (plus its own 가./나./다. sub-item labels
    # already on p.29-30) makes p.29 AND p.30 genuine hits at the CLI default
    # keyword_window=1, and p.30's own +-1 window reaches p.31 without p.31 needing
    # its own hit (it uses "(1)(2)(3)" parenthesized numbering, not 가./나./다., so
    # it still can't self-qualify under the weak-single-hit heuristic).
    "금리위험액",
    "주식위험액",
    "부동산위험액",
    "외환위험액",
    "자산집중위험액",
    # 2026-09-01: closing the KR0069 gap above (금리위험액+window=1) still dropped
    # p.32 (③④OOO위험액현황 표의 부동산 leg) — that table's rows are "1.직접소유/
    # 2.간접소유/3.의무보유부동산" (plain Arabic-dot numbering, not 가./나./다.), so
    # even with "부동산위험액" already listed, the page only ever gets matched_count
    # ==1 and fails the weak-single-hit 가/나/다 check, staying dependent on window-
    # bleed from a neighboring hit. Raising keyword_window to bridge it instead
    # (tried 2) pulled docling into a much wider single-page-range and triggered
    # `std::bad_alloc` on 3 unrelated pages, losing MORE items than it recovered
    # (see this session's KR0069 probes). "의무보유부동산" is this table's own
    # 3rd row label and — confirmed via raw-PDF fitz scan — the SAME regulatory
    # template phrase on the 부동산위험액 page for KR0002/KR0032/KR0068/KR0104 too
    # (all 4 independently hit the identical gap in this session's 2026.2Q census),
    # so it crosses the matched_count>=2 hit threshold directly, at keyword_window=1,
    # without widening the window or risking the bad_alloc pages.
    "의무보유부동산",
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

# Section anchors that must never lose their page to the top-N cap.
#
# ``_select_page_ranges`` ranks candidate pages by ``matched_count`` and keeps
# only the best ``max_keyword_hit_pages``. That ordering systematically punishes
# exactly the pages this lane needs most: the 요약/총괄 pages repeat five or six
# ratio keywords each and score 5-8, while a 시장위험/민감도 *detail* page names
# its own risk once and scores 1-2. Measured over md_inbox/FY2026_Q2 (39 filers,
# scripts/_probes/probe_20260901_formA_rootcause.py): 8 pages that carry
# "6-4. 시장위험 관리" and/or "금리위험액 현황" were genuine keyword hits but were
# ranked 21-36 out of 22-62 candidates and fell outside the cap of 20 —
# KR0002 p33 (rank 31/62), KR0032 p32 (22/24), KR0049 p35+p36 (26/26),
# KR0050 p34 (31/35), KR0074 p25 (36/47), KR0083 p30 (21/26), KR0150 p28.
# Raising the cap for everyone widens every conversion (and docling's memory
# use with it, see ``_pages_missing_content``); exempting the handful of pages
# that carry a required section costs 1-3 extra pages per filer instead.
#
# Keep this list to *section-defining* terms. A term that also appears in the
# high-scoring summary tables (e.g. bare "시장위험액", a row label in the 요구자본
# breakdown) would mark half the document priority and defeat the cap entirely.
PRIORITY_KEYWORDS: tuple[str, ...] = (
    "시장위험관리",   # "6-4. 시장위험 관리" — whitespace-normalized before matching
    "금리위험액현황",
    "주식위험액현황",
    "부동산위험액현황",
    "외환위험액현황",
    "자산집중위험액현황",
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
    # Page-loss bookkeeping so the operator sees a truncated parse in the
    # harness output, not only later in the quality gate.
    docling_status: str = ""
    dropped_pages: tuple[int, ...] = ()
    recovered_pages: tuple[int, ...] = ()
    unrecovered_pages: tuple[int, ...] = ()


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
) -> tuple[list[tuple[int, int, bool]], int | None]:
    """Return (1-based hit pages, total pages) using a cheap text scan.

    Each hit is ``(page_no, matched_count, is_priority)``. ``is_priority`` marks
    a page that names one of ``PRIORITY_KEYWORDS`` (a required section anchor);
    such a page is kept even when ``matched_count`` is 0, because several filers
    open "6-4. 시장위험 관리" on a page whose only other content is prose.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        total = len(reader.pages)
        if total <= 0:
            return [], 0
        terms = tuple("".join(t.split()) for t in keyword_terms if t.strip())
        prio_terms = tuple("".join(t.split()) for t in PRIORITY_KEYWORDS)
        hits: list[tuple[int, int, bool]] = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            normalized = "".join(text.split())
            matched_count = sum(1 for term in terms if term and term in normalized)
            is_priority = any(t in normalized for t in prio_terms)
            if matched_count >= 2 or is_priority:
                hits.append((i, matched_count, is_priority))
                continue
            # Weak single-keyword page still accepted only when it looks table-like.
            if (
                matched_count == 1
                and _NUMERIC_RE.search(text)
                and any(tok in text for tok in ("가.", "나.", "다.", "|"))
            ):
                hits.append((i, 1, False))
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

    Pages flagged ``is_priority`` by ``_find_keyword_pages`` bypass the top-N
    cap (see ``PRIORITY_KEYWORDS``); everything else competes for the cap by
    ``matched_count`` as before.
    """
    scored_hits, total = _find_keyword_pages(item.pdf_path, item.keyword_terms)
    if total is None:
        # pypdf failure: fall back to full conversion.
        return [(1, sys.maxsize)], "pypdf_unavailable_full_fallback", []
    if scored_hits:
        ranked = sorted(scored_hits, key=lambda x: (-x[1], x[0]))
        capped = {p for p, _, _ in ranked[: max(1, int(item.max_keyword_hit_pages))]}
        forced = {p for p, _, prio in scored_hits if prio}
        top_pages = sorted(capped | forced)
        mode = "keyword_window_priority" if (forced - capped) else "keyword_window"
        pages = _expand_pages(top_pages, total, item.keyword_window)
        return _pages_to_ranges(pages), mode, top_pages
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


def _total_pages(pdf_path: Path) -> int:
    """Page count of the source PDF, or 0 when it cannot be read.

    Written into the front matter so the quality gate can compute the
    selected/total coverage ratio without reopening the PDF (inbox
    20260831T0700Z request 2).
    """

    try:
        from pypdf import PdfReader

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:  # noqa: BLE001
        try:
            import fitz

            with fitz.open(str(pdf_path)) as doc:
                return int(doc.page_count)
        except Exception:  # noqa: BLE001
            return 0


def _front_matter(
    item: PdfInput,
    fingerprint: dict[str, str],
    parse_spec_hash: str,
    parse_confidence: float | None,
    run_id: str,
    selected_ranges: list[tuple[int, int]],
    selection_mode: str,
    hit_pages: list[int],
    total_pages: int = 0,
    docling_status: str = "",
    dropped_pages: list[int] | None = None,
    recovered_pages: list[int] | None = None,
    unrecovered_pages: list[int] | None = None,
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
        "source_total_pages": str(total_pages or ""),
        "keyword_hit_pages": ",".join(str(p) for p in hit_pages),
        # Recovery bookkeeping for the quality gate — see _pages_missing_content.
        "docling_status": docling_status,
        "docling_dropped_pages": ",".join(str(p) for p in (dropped_pages or [])),
        "docling_recovered_pages": ",".join(str(p) for p in (recovered_pages or [])),
        "docling_unrecovered_pages": ",".join(str(p) for p in (unrecovered_pages or [])),
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


def _conversion_status(conversion: object) -> str:
    """``ConversionStatus.PARTIAL_SUCCESS`` -> ``"PARTIAL_SUCCESS"``."""

    status = getattr(conversion, "status", None)
    if status is None:
        return ""
    return str(getattr(status, "name", status)).rsplit(".", 1)[-1]


def _pages_missing_content(document: object) -> list[int]:
    """Pages docling kept in the page index but produced no content for.

    Docling converts a page range in batches; when a batch raises it logs the
    failure, marks the document ``PARTIAL_SUCCESS`` and returns the document
    *without that page's items*. The page number still appears in
    ``document.pages``, so the drop is invisible unless you compare the page
    index against the provenance of the exported items.

    Measured 2026-09-01 on ``KR0051_신한이지손해보험.pdf`` page_range=(5,35):

        ERROR docling.pipeline.standard_pdf_pipeline:
              Stage preprocess failed for run 1, pages [29]: std::bad_alloc
              ... pages [30] ... pages [33] ... pages [34]
        status = ConversionStatus.PARTIAL_SUCCESS
        MISSING from document.pages: []          <- page index looks complete
        p29 0  p30 0  p33 0  p34 0               <- but four pages export nothing

    Page 34 is that filer's "6-8. 위험민감도" table, i.e. this silent drop is the
    third failure form reported in inbox 20260831T0700Z (page inside
    ``source_page_ranges`` *and* inside ``keyword_hit_pages``, content absent
    from the MD, fitz reads the table fine).
    """

    pages = getattr(document, "pages", None)
    try:
        page_nos = sorted(int(p) for p in (pages or {}))
    except (TypeError, ValueError):
        return []
    if not page_nos:
        return []
    with_content: set[int] = set()
    for attr in ("texts", "tables", "pictures"):
        for element in getattr(document, attr, []) or []:
            for prov in getattr(element, "prov", []) or []:
                page_no = getattr(prov, "page_no", None)
                if page_no is not None:
                    with_content.add(int(page_no))
    return [p for p in page_nos if p not in with_content]


def _single_page_markdown(converter: object, pdf_path: Path, page_no: int) -> str:
    """Re-convert one page on its own; returns "" when it fails again.

    A one-page conversion has a far smaller peak footprint than the enclosing
    range, so the ``std::bad_alloc`` pages come back. Measured on KR0051
    pages 25/29/30/33/34: 5/5 returned ``ConversionStatus.SUCCESS`` with the
    full table (p34 = "6-8. 위험민감도 / 6-8-1) 민감도 분석 개요", 1,049 chars).
    """

    # The retry runs inside the same worker whose heap just triggered the
    # bad_alloc, so reclaim first — KR0004 FY2026_Q2 p.46-47 (its whole
    # 6-8 위험민감도 section) failed the retry too on the 2026-09-01 run.
    gc.collect()
    try:
        conversion = converter.convert(str(pdf_path), page_range=(page_no, page_no))
        markdown = conversion.document.export_to_markdown()
        del conversion
        return markdown or ""
    except Exception:  # noqa: BLE001 - a failed retry must not kill the file
        logger.warning("single-page retry failed: %s p%s", pdf_path.name, page_no)
        return ""


def _markdown_with_recovery(
    converter: object,
    document: object,
    pdf_path: Path,
    missing_pages: list[int],
) -> tuple[str, list[int], list[int]]:
    """Rebuild a range's markdown, substituting re-converted pages in order.

    Returns ``(markdown, recovered_pages, unrecovered_pages)``. Page order is
    preserved by exporting the surviving pages one at a time
    (``export_to_markdown(page_no=...)``) and splicing the retried pages into
    their slot — verified lossless against the plain whole-range export on
    KR0051 5-35 (both 51,124 chars, 276/276 grouped numbers retained,
    ``scripts/_probes/probe_20260901_pagewise_export_check.py``). If the
    page-wise reassembly ever comes out *shorter* than the plain export we keep
    the plain export and append the recovered pages, so this can never lose
    content relative to the previous behaviour.
    """

    plain = document.export_to_markdown()
    recovered: list[int] = []
    unrecovered: list[int] = []
    retried: dict[int, str] = {}
    for page_no in missing_pages:
        markdown = _single_page_markdown(converter, pdf_path, page_no)
        if markdown.strip():
            retried[page_no] = markdown
            recovered.append(page_no)
        else:
            unrecovered.append(page_no)

    if not retried:
        return plain, recovered, unrecovered

    parts: list[str] = []
    try:
        page_nos = sorted(int(p) for p in (getattr(document, "pages", None) or {}))
        for page_no in page_nos:
            if page_no in retried:
                parts.append(retried[page_no])
                continue
            segment = document.export_to_markdown(page_no=page_no)
            if segment and segment.strip():
                parts.append(segment)
    except Exception:  # noqa: BLE001
        logger.warning("page-wise reassembly failed for %s; appending instead", pdf_path.name)
        parts = []

    reassembled = "\n\n".join(parts)
    if len(reassembled) >= len(plain):
        return reassembled, recovered, unrecovered
    return (
        "\n\n".join([plain] + [retried[p] for p in sorted(retried)]),
        recovered,
        unrecovered,
    )


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
        statuses: list[str] = []
        dropped_pages: list[int] = []
        recovered_pages: list[int] = []
        unrecovered_pages: list[int] = []
        for r_start, r_end in selected_ranges:
            conversion = converter.convert(str(item.pdf_path), page_range=(r_start, r_end))
            document = conversion.document
            status = _conversion_status(conversion)
            if status:
                statuses.append(status)
            # Only pay for the page-by-page audit when docling itself admits a
            # problem; a clean SUCCESS keeps the previous export path verbatim.
            missing = _pages_missing_content(document) if status and status != "SUCCESS" else []
            if missing:
                dropped_pages.extend(missing)
                logger.warning(
                    "docling %s dropped pages %s from %s (range %s-%s); retrying one page at a time",
                    status,
                    missing,
                    item.pdf_path.name,
                    r_start,
                    r_end,
                )
                markdown, recovered, unrecovered = _markdown_with_recovery(
                    converter, document, item.pdf_path, missing
                )
                recovered_pages.extend(recovered)
                unrecovered_pages.extend(unrecovered)
                markdown_parts.append(markdown)
            else:
                markdown_parts.append(document.export_to_markdown())
            confidences.append(_estimate_confidence(document))
            del document
            del conversion

        if not markdown_parts:
            raise RuntimeError("no markdown extracted from selected page ranges")

        markdown_body = "\n\n".join(markdown_parts)
        confidence = sum(confidences) / len(confidences) if confidences else None

        # Worst status wins, then the recovery outcome refines it:
        #   SUCCESS   nothing was dropped
        #   RECOVERED docling dropped pages, every one came back on retry
        #   PARTIAL_SUCCESS  at least one dropped page is still missing
        if unrecovered_pages:
            docling_status = "PARTIAL_SUCCESS"
        elif recovered_pages:
            docling_status = "RECOVERED"
        elif any(s != "SUCCESS" for s in statuses):
            docling_status = next(s for s in statuses if s != "SUCCESS")
        else:
            docling_status = statuses[0] if statuses else ""

        front_matter = _front_matter(
            item,
            fingerprint,
            spec,
            confidence,
            run_id,
            selected_ranges=selected_ranges,
            selection_mode=selection_mode,
            hit_pages=hit_pages,
            total_pages=_total_pages(item.pdf_path),
            docling_status=docling_status,
            dropped_pages=sorted(set(dropped_pages)),
            recovered_pages=sorted(set(recovered_pages)),
            unrecovered_pages=sorted(set(unrecovered_pages)),
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
            docling_status=docling_status,
            dropped_pages=tuple(sorted(set(dropped_pages))),
            recovered_pages=tuple(sorted(set(recovered_pages))),
            unrecovered_pages=tuple(sorted(set(unrecovered_pages))),
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

