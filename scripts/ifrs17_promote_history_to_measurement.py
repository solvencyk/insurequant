"""Run measurement_extractor on historical raw XMLs.

Inputs:  data/ifrs17/raw_history/<canonical>/<period>/xml/<rcept_no>.xml
Outputs: data/ifrs17/extracted_history/<canonical>__<period>_measurement.json

This is the historical analog of scripts/ifrs17_batch_measurement.py (which
only handles the single FY2024 annual cohort). The viz builder
``viz_build_csm_waterfall_history.py`` consumes the resulting _measurement.json
files.
"""
from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.measurement_extractor import (  # noqa: E402
    extract_measurement_tables,
    to_jsonable,
)

HIST_RAW = REPO / "data" / "ifrs17" / "raw_history"
HIST_EXTRACTED = REPO / "data" / "ifrs17" / "extracted_history"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    if not HIST_RAW.exists():
        print(f"no raw_history dir under {HIST_RAW}")
        return 1
    HIST_EXTRACTED.mkdir(parents=True, exist_ok=True)

    targets: list[tuple[Path, str, str]] = []  # (xml_path, canonical, period)
    for canonical_dir in sorted(HIST_RAW.iterdir()):
        if not canonical_dir.is_dir():
            continue
        canonical = canonical_dir.name
        for period_dir in sorted(canonical_dir.iterdir()):
            if not period_dir.is_dir():
                continue
            period = period_dir.name
            xml_dir = period_dir / "xml"
            if not xml_dir.exists():
                continue
            xmls = sorted(xml_dir.glob("*.xml"))
            if not xmls:
                continue
            # Many filings ship a single big XML; some annuals have multiple.
            # measurement_extractor works per-XML; we union the table lists.
            targets.append((xml_dir, canonical, period))

    print(f"[promote] targets={len(targets)}")
    summary: list[dict] = []
    for i, (xml_dir, canonical, period) in enumerate(targets, 1):
        out_json = HIST_EXTRACTED / f"{canonical}__{period}_measurement.json"
        # Skip if already exists with non-trivial content
        if out_json.is_file() and out_json.stat().st_size > 64:
            summary.append({"canonical": canonical, "period": period,
                            "status": "cached"})
            if i % 30 == 0:
                print(f"  [{i}/{len(targets)}] cached: {canonical} {period}")
            continue

        all_tables: list[dict] = []
        err: str | None = None
        for xml_path in sorted(xml_dir.glob("*.xml")):
            try:
                tables = extract_measurement_tables(xml_path, canonical, min_score=5)
            except Exception as exc:
                err = f"{xml_path.name}: {exc}"
                traceback.print_exc()
                continue
            for t in tables:
                d = to_jsonable(t)
                d["_source_xml"] = xml_path.name
                all_tables.append(d)

        if all_tables:
            out_json.write_text(
                json.dumps(all_tables, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            status = "ok"
        else:
            # Write empty file to mark "extracted but no measurement tables"
            out_json.write_text("[]", encoding="utf-8")
            status = "no_measurement_tables"

        summary.append({
            "canonical": canonical, "period": period,
            "status": status, "n_tables": len(all_tables),
            "error": err,
        })
        if i % 20 == 0:
            print(f"  [{i}/{len(targets)}] {canonical} {period}: {status} ({len(all_tables)} tables)")

    summary_path = HIST_EXTRACTED / "_promote_summary.json"
    summary_path.write_text(
        json.dumps({"generated_at": _stamp(), "results": summary},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    statuses: dict[str, int] = {}
    for r in summary:
        s = r["status"]
        statuses[s] = statuses.get(s, 0) + 1
    print(f"\n[summary] total={len(summary)}")
    for s, n in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  {s}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
