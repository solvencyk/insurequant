"""Pipeline harness entry point.

Three harness families share this single CLI:

* ``--stage quality``: markdown quality gate. Scores every ``*.md`` under
  ``md_inbox/`` and writes the review queue CSV so borderline Docling
  output gets human review before it is parsed into the masters.
* ``--stage pdf``: downloaded-PDF accessibility gate. Walks
  ``data/disclosure/<period>/pdf/`` (defaults to FY2025_Q4), normalises
  the ACL on every file so the local desktop session can read it, runs
  the multi-level ``verify_pdf`` chain (magic + read + size + keyword +
  pypdf), and prints a per-company table. Fails when any file is in the
  ``failed`` level.
* ``--stage parse``: walk ``data/disclosure/<period>/pdf/`` (or
  ``--pdf-root``), build ``PdfInput`` rows (manifest + period-end
  disclosure date), detect solvency-keyword pages and parse only those
  pages (+-window), write ``*.md`` under ``<period>/parsed/`` and
  ``md_inbox/<period>/``. Use ``--companies`` / ``--limit`` for a dry run.

The harness is intentionally lightweight - it is the orchestrator that
calls the modules under ``src/solvency``. Add new gates by writing a
function and wiring it up in ``_quality_stage``, ``_pdf_stage`` or
``_parse_stage``.

Removed 2026-07-21: the ``perf`` / ``data`` / ``all`` stages built and
validated the deprecated ``kics_data.json`` (retired 2026-05-30). The
live K-ICS master is ``kics_disclosure.json``; its gate is
``scripts/validate_kics_disclosure.py``.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from solvency.config import settings
from solvency.parser import docling_parser, quality_check
from solvency.verification import (
    VerificationLevel,
    normalize_tree,
    verify_directory,
)

logger = logging.getLogger("harness")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _list_md(md_root: Path) -> list[Path]:
    return sorted(md_root.rglob("*.md"))


def _quality_stage(args: argparse.Namespace) -> dict:
    """Score md_inbox markdown and write the review queue CSV."""
    md_root = Path(args.md_root) if args.md_root else settings.md_inbox_dir
    md_paths = _list_md(md_root) if md_root.exists() else []
    if not md_paths:
        return {
            "ok": False,
            "skipped": True,
            "stage": "quality",
            "reason": f"no markdown found under {md_root}",
        }

    reports = [quality_check.score(p) for p in md_paths]
    review_path = quality_check.write_review_queue(reports, _now())
    review_count = sum(1 for r in reports if r.decision == "review")

    # Page-selection guard (inbox 20260831T0700Z request 2). Until 2026-09-01
    # nothing read source_page_ranges, so a docling window that skipped the
    # 6-4 시장위험 / 6-8 위험민감도 pages produced a markdown that simply looked
    # like a filer who had not disclosed them.
    flag_counts: dict[str, int] = {}
    flagged: list[dict] = []
    for r in reports:
        if not r.page_flags:
            continue
        flagged.append(
            {
                "md_path": str(r.md_path),
                "company_code": r.company_code,
                "page_flags": r.page_flags,
            }
        )
        for f in r.page_flags:
            key = f.split("=", 1)[0]
            flag_counts[key] = flag_counts.get(key, 0) + 1

    lines = [
        "",
        f"=== MD quality gate ({md_root}) ===",
        f"  total={len(md_paths)}  accepted={len(md_paths) - review_count}"
        f"  review={review_count}",
        f"  page-selection flags: {len(flagged)} file(s)",
    ]
    for key, n in sorted(flag_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"    {key:<26} {n}")
    lines.append(f"  queue={review_path}")
    lines.append("")
    print("\n".join(lines))

    return {
        "ok": True,
        "stage": "quality",
        "md_root": str(md_root),
        "total_md": len(md_paths),
        "review_md": review_count,
        "review_queue": str(review_path),
        "page_flag_counts": flag_counts,
        "page_flagged_files": flagged,
    }


def _pdf_stage(args: argparse.Namespace) -> dict:
    """Verify every PDF under a period directory is openable by the user.

    Steps:
      1. Walk ``data/disclosure/<period>/pdf/``
      2. ``normalize_tree`` to clear admin-owner ACEs that block the
         desktop session
      3. ``verify_pdf`` on every file (magic / read / size / keyword /
         pypdf)
      4. Group by ``failed`` / ``verified_basic`` / ``verified_full``
         and print a table
    """
    period = args.period or "FY2025_Q4"
    pdf_root = (
        Path(args.pdf_root)
        if args.pdf_root
        else settings.disclosure_dir / period / "pdf"
    )

    if not pdf_root.exists():
        return {
            "ok": False,
            "skipped": True,
            "reason": f"pdf root not found: {pdf_root}",
        }

    normalised = normalize_tree(pdf_root, glob="*.pdf")
    results = verify_directory(pdf_root, glob="*.pdf")

    rows: list[dict] = []
    failed: list[str] = []
    basic: list[str] = []
    full: list[str] = []
    for r in results:
        company = r.path.stem
        rows.append(
            {
                "company": company,
                "level": r.level.value,
                "size_bytes": r.size_bytes,
                "user_can_read": r.user_can_read,
                "has_magic": r.has_magic,
                "has_keyword": r.has_keyword,
                "pypdf_ok": r.pypdf_ok,
                "reasons": r.reasons,
            }
        )
        if r.level is VerificationLevel.FAILED:
            failed.append(company)
        elif r.level is VerificationLevel.VERIFIED_BASIC:
            basic.append(company)
        else:
            full.append(company)

    table_lines = ["", f"=== PDF verification ({pdf_root}) ===", ""]
    for row in rows:
        marker = {
            "verified_full": "OK ",
            "verified_basic": "BASIC",
            "failed": "FAIL",
        }[row["level"]]
        table_lines.append(
            f"  [{marker}] {row['company']:<40} "
            f"size={row['size_bytes']:>10}  "
            f"read={row['user_can_read']}  "
            f"magic={row['has_magic']}  "
            f"reasons={row['reasons']}"
        )
    table_lines.append("")
    table_lines.append(
        f"Total: {len(results)}  | full={len(full)}  basic={len(basic)}  failed={len(failed)}"
    )
    if failed:
        table_lines.append(f"Failed companies: {', '.join(sorted(failed))}")
    print("\n".join(table_lines))

    return {
        "ok": not failed,
        "stage": "pdf",
        "period": period,
        "pdf_root": str(pdf_root),
        "normalised_files": normalised,
        "totals": {
            "all": len(results),
            "verified_full": len(full),
            "verified_basic": len(basic),
            "failed": len(failed),
        },
        "failed_companies": sorted(failed),
        "rows": rows,
    }


def _parse_stage(args: argparse.Namespace) -> dict:
    """Docling: PDFs under a period (or custom root) to Markdown."""

    period = args.period or "FY2025_Q4"
    pdf_root = Path(args.pdf_root) if args.pdf_root else None
    items = docling_parser.discover_inputs(period, pdf_root=pdf_root)
    kw_terms = tuple(
        s.strip()
        for s in (
            args.keywords.split(",")
            if args.keywords
            else docling_parser.DEFAULT_RATIO_KEYWORDS
        )
        if s.strip()
    )
    items = [
        dataclasses.replace(
            i,
            keyword_window=max(0, int(args.keyword_window)),
            fallback_scan_pages=max(1, int(args.fallback_scan_pages)),
            max_keyword_hit_pages=max(1, int(args.max_hit_pages)),
            keyword_terms=kw_terms,
        )
        for i in items
    ]
    if args.companies:
        want = {c.strip().upper() for c in args.companies.split(",") if c.strip()}
        items = [i for i in items if i.company_code.upper() in want]
    if args.limit is not None:
        items = items[: int(args.limit)]

    if not items:
        return {
            "ok": False,
            "skipped": True,
            "stage": "parse",
            "reason": "no pdf inputs (check period, --pdf-root, --companies)",
        }

    workers = max(1, int(args.workers))
    t0 = time.perf_counter()
    results = list(docling_parser.parse_parallel(items, workers=workers))
    elapsed = time.perf_counter() - t0
    failed = [r for r in results if r.status == "failed"]

    lines: list[str] = [
        "",
        f"=== Docling parse ({period}, workers={workers}) ===",
        f"  keyword_window={max(0, int(args.keyword_window))}"
        f"  fallback_scan_pages={max(1, int(args.fallback_scan_pages))}"
        f"  max_hit_pages={max(1, int(args.max_hit_pages))}"
        f"  keywords={','.join(kw_terms)}",
        f"  inputs={len(items)}  ok={sum(1 for r in results if r.status == 'ok')}"
        f"  skip={sum(1 for r in results if r.status == 'skipped_idempotent')}"
        f"  fail={len(failed)}  elapsed_s={elapsed:.1f}",
        "",
    ]
    lost = [r for r in results if getattr(r, "unrecovered_pages", ())]
    for r in sorted(results, key=lambda x: x.company_code):
        st = r.status
        conf = r.parse_confidence
        c = f" conf={conf:.2f}" if conf is not None else ""
        lines.append(
            f"  [{st}] {r.company_code}  {r.elapsed_seconds:.1f}s{c}  {r.pdf_path.name}"
        )
        if st == "failed" and r.error_message:
            lines.append(f"       {r.error_message}")
        # Docling drops pages it was asked to convert (std::bad_alloc in its
        # preprocess stage) and reports only PARTIAL_SUCCESS. Say so here, at
        # the moment it happens, rather than leaving it for the quality gate.
        if getattr(r, "dropped_pages", ()):
            lines.append(
                f"       docling={r.docling_status} dropped={list(r.dropped_pages)}"
                f" recovered={list(r.recovered_pages)}"
                f" STILL-LOST={list(r.unrecovered_pages)}"
            )
    if lost:
        lines.append("")
        lines.append(
            f"  !! {len(lost)} file(s) still missing pages after single-page retry: "
            + ", ".join(f"{r.company_code}{list(r.unrecovered_pages)}" for r in lost)
        )
        lines.append(
            "     Those pages are absent from the markdown. Check them against the raw PDF"
        )
        lines.append(
            "     before trusting any 'the filer did not disclose it' conclusion."
        )
    print("\n".join(lines))

    return {
        "ok": not failed,
        "stage": "parse",
        "period": period,
        "pdf_root": str(
            pdf_root or (settings.disclosure_dir / period / "pdf").resolve()
        ),
        "workers": workers,
        "keyword_window": max(0, int(args.keyword_window)),
        "fallback_scan_pages": max(1, int(args.fallback_scan_pages)),
        "max_hit_pages": max(1, int(args.max_hit_pages)),
        "keywords": list(kw_terms),
        "total": len(results),
        "ok_count": sum(1 for r in results if r.status == "ok"),
        "skipped_idempotent": sum(1 for r in results if r.status == "skipped_idempotent"),
        "failed": len(failed),
        "elapsed_seconds": round(elapsed, 3),
        "rows": [
            {
                "company_code": r.company_code,
                "pdf_path": str(r.pdf_path),
                "md_path": str(r.md_path) if r.md_path else "",
                "status": r.status,
                "parse_confidence": r.parse_confidence,
                "elapsed_seconds": r.elapsed_seconds,
                "error_message": r.error_message,
                "docling_status": getattr(r, "docling_status", ""),
                "dropped_pages": list(getattr(r, "dropped_pages", ())),
                "recovered_pages": list(getattr(r, "recovered_pages", ())),
                "unrecovered_pages": list(getattr(r, "unrecovered_pages", ())),
            }
            for r in results
        ],
    }


def _write_report(stage: str, result: dict) -> Path:
    target = settings.artifacts_dir / "reports" / f"harness_{stage}_{_now()}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=["quality", "pdf", "parse"],
        required=True,
        help="which harness family to run",
    )
    parser.add_argument(
        "--md-root",
        help="override md_inbox path (defaults to SOLVENCY_MD_INBOX_DIR)",
    )
    parser.add_argument(
        "--period",
        help="period label for --stage pdf/parse (defaults to FY2025_Q4)",
    )
    parser.add_argument(
        "--pdf-root",
        help="override PDF directory for --stage pdf, or for --stage parse (else <period>/pdf)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="process pool size for --stage parse (default: 4)",
    )
    parser.add_argument(
        "--companies",
        help="for --stage parse: comma-separated KR codes (e.g. KR0008,KR0011)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="for --stage parse: parse at most this many PDFs (dry-run)",
    )
    parser.add_argument(
        "--keyword-window",
        type=int,
        default=1,
        help="for --stage parse: parse hit page +-N pages (default: 1)",
    )
    parser.add_argument(
        "--fallback-scan-pages",
        type=int,
        default=20,
        help="for --stage parse: when no keyword hit, parse first N pages (default: 20)",
    )
    parser.add_argument(
        "--max-hit-pages",
        type=int,
        default=20,
        help="for --stage parse: cap keyword-hit pages before +-window expansion (default: 20)",
    )
    parser.add_argument(
        "--keywords",
        help="for --stage parse: comma-separated keywords overriding defaults",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")
    settings.ensure_dirs()

    stages = {"quality": _quality_stage, "pdf": _pdf_stage, "parse": _parse_stage}
    result = stages[args.stage](args)
    report_path = _write_report(args.stage, result)
    logger.info("%s report: %s", args.stage, report_path)

    overall_ok = bool(result.get("ok") or result.get("skipped"))
    print(
        json.dumps(
            {"ok": overall_ok, "summaries": {args.stage: result}},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
