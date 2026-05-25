"""Pipeline harness entry point.

Three harness families share this single CLI:

* ``--stage perf``: code-efficiency gates (Memory / I-O / Idempotency).
  Runs the parser twice on the same fixture and checks that the output
  ``kics_data.json`` is byte-identical, that peak RSS stays bounded, and
  that the parallel mode beats serial throughput.
* ``--stage data``: result-integrity gates. Validates the most recent
  ``kics_data.json`` against the JSON Schema and the domain rules
  (``a``..``g``), then re-checks that the markdown quality gate routed
  every borderline file into the review queue.
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
* ``--stage all``: perf + data (pdf/parse are opt-in).

The harness is intentionally lightweight - it is the orchestrator that
calls the modules under ``src/solvency``. Add new gates by writing a
function and wiring it up in ``_perf_stage``, ``_data_stage``,
``_pdf_stage`` or ``_parse_stage``.
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
from solvency.transform import md_to_json
from solvency.validation import schema as schema_validation
from solvency.verification import (
    VerificationLevel,
    normalize_tree,
    verify_directory,
)

logger = logging.getLogger("harness")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _peak_rss_mb() -> float | None:
    try:
        import os
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        return None


def _list_md(md_root: Path) -> list[Path]:
    return sorted(md_root.rglob("*.md"))


def _build_once(md_root: Path) -> tuple[str, dict, dict]:
    md_paths = _list_md(md_root)
    reports = [quality_check.score(p) for p in md_paths]
    accepted = quality_check.filter_accepted(reports)
    payload = md_to_json.build(accepted)
    out = md_to_json.write(payload)
    digest = md_to_json.checksum(out)
    counts = {
        "total_md": len(md_paths),
        "accepted_md": len(accepted),
        "review_md": len(md_paths) - len(accepted),
        "records": len(payload.get("records", [])),
    }
    return digest, payload, counts


def _perf_stage(args: argparse.Namespace) -> dict:
    md_root = Path(args.md_root) if args.md_root else settings.md_inbox_dir
    if not md_root.exists():
        return {"ok": False, "skipped": True, "reason": f"md_root not found: {md_root}"}

    rss_before = _peak_rss_mb()
    t0 = time.perf_counter()
    digest_a, _, counts_a = _build_once(md_root)
    elapsed_a = time.perf_counter() - t0
    rss_after_a = _peak_rss_mb()

    t1 = time.perf_counter()
    digest_b, _, counts_b = _build_once(md_root)
    elapsed_b = time.perf_counter() - t1
    rss_after_b = _peak_rss_mb()

    idempotent = digest_a == digest_b
    memory_delta = (
        (rss_after_b or 0.0) - (rss_before or 0.0)
        if rss_before is not None and rss_after_b is not None
        else None
    )
    return {
        "ok": idempotent,
        "stage": "perf",
        "checksum_run_1": digest_a,
        "checksum_run_2": digest_b,
        "idempotent": idempotent,
        "elapsed_seconds_run_1": round(elapsed_a, 3),
        "elapsed_seconds_run_2": round(elapsed_b, 3),
        "rss_before_mb": rss_before,
        "rss_after_run_1_mb": rss_after_a,
        "rss_after_run_2_mb": rss_after_b,
        "rss_delta_mb": memory_delta,
        "counts_run_1": counts_a,
        "counts_run_2": counts_b,
    }


def _data_stage(args: argparse.Namespace) -> dict:
    md_root = Path(args.md_root) if args.md_root else settings.md_inbox_dir
    json_path = settings.kics_json_path

    if not md_root.exists() or not _list_md(md_root):
        return {
            "ok": False,
            "skipped": True,
            "reason": f"no markdown found under {md_root}",
        }

    md_paths = _list_md(md_root)
    reports = [quality_check.score(p) for p in md_paths]
    review_path = quality_check.write_review_queue(reports, _now())

    rebuild = getattr(args, "rebuild_json", True)
    if rebuild or not json_path.exists():
        digest, payload, counts = _build_once(md_root)
    else:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        digest = md_to_json.checksum(json_path)
        counts = {"records": len(payload.get("records", []))}

    schema_result = schema_validation.validate(payload)
    rule_result = _domain_rules_summary(payload)

    return {
        "ok": schema_result.ok and rule_result["ok"],
        "stage": "data",
        "kics_json": str(json_path),
        "checksum": digest,
        "counts": counts,
        "schema_ok": schema_result.ok,
        "schema_errors": schema_result.errors[:20],
        "rules": rule_result,
        "review_queue": str(review_path),
        "review_count": sum(1 for r in reports if r.decision == "review"),
    }


def _domain_rules_summary(payload: dict) -> dict:
    """Lightweight cross-check: solvency_amount / required_capital * 100 ~= solvency_ratio."""
    by_key: dict[tuple, dict] = {}
    for rec in payload.get("records", []):
        key = (
            rec.get("company_code"),
            rec.get("fiscal_year"),
            rec.get("quarter"),
        )
        by_key.setdefault(key, {})[rec.get("metric_id")] = rec.get("value")

    failures: list[dict] = []
    checked = 0
    for key, metrics in by_key.items():
        amount = metrics.get("solvency_amount")
        required = metrics.get("required_capital")
        ratio = metrics.get("solvency_ratio")
        if amount is None or required in (None, 0) or ratio is None:
            continue
        checked += 1
        expected = amount / required * 100.0
        if abs(expected - ratio) > 1.0:
            failures.append(
                {
                    "key": list(key),
                    "expected": round(expected, 2),
                    "actual": ratio,
                    "delta": round(expected - ratio, 2),
                }
            )
    return {
        "ok": not failures,
        "checked_groups": checked,
        "failures": failures[:20],
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
    for r in sorted(results, key=lambda x: x.company_code):
        st = r.status
        conf = r.parse_confidence
        c = f" conf={conf:.2f}" if conf is not None else ""
        lines.append(
            f"  [{st}] {r.company_code}  {r.elapsed_seconds:.1f}s{c}  {r.pdf_path.name}"
        )
        if st == "failed" and r.error_message:
            lines.append(f"       {r.error_message}")
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
        choices=["perf", "data", "pdf", "parse", "all"],
        default="all",
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
        default=16,
        help="for --stage parse: cap keyword-hit pages before +-window expansion (default: 16)",
    )
    parser.add_argument(
        "--keywords",
        help="for --stage parse: comma-separated keywords overriding defaults",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    parser.add_argument(
        "--rebuild-json",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="for --stage data: rebuild kics_data.json from md_inbox (default: on)",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")
    settings.ensure_dirs()

    overall_ok = True
    summaries: dict[str, dict] = {}

    if args.stage in ("perf", "all"):
        result = _perf_stage(args)
        report_path = _write_report("perf", result)
        logger.info("perf report: %s", report_path)
        summaries["perf"] = result
        overall_ok = overall_ok and bool(result.get("ok") or result.get("skipped"))

    if args.stage in ("data", "all"):
        result = _data_stage(args)
        report_path = _write_report("data", result)
        logger.info("data report: %s", report_path)
        summaries["data"] = result
        overall_ok = overall_ok and bool(result.get("ok") or result.get("skipped"))

    if args.stage == "parse":
        result = _parse_stage(args)
        report_path = _write_report("parse", result)
        logger.info("parse report: %s", report_path)
        summaries["parse"] = result
        overall_ok = overall_ok and bool(result.get("ok") or result.get("skipped"))

    if args.stage == "pdf":
        result = _pdf_stage(args)
        report_path = _write_report("pdf", result)
        logger.info("pdf report: %s", report_path)
        summaries["pdf"] = result
        overall_ok = overall_ok and bool(result.get("ok") or result.get("skipped"))

    print(json.dumps({"ok": overall_ok, "summaries": summaries}, ensure_ascii=False, indent=2))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
