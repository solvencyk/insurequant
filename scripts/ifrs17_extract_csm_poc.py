# -*- coding: utf-8 -*-
"""PoC: extract CSM amortisation tables from a downloaded filing XML.

Default target: the Samsung Fire 2024 annual report fetched by
scripts/ifrs17_fetch_one_filing.py.

Writes the normalised JSON to data/ifrs17/extracted/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.csm_extractor import extract_csm_tables, to_jsonable  # noqa: E402


def extract_dir(filing_dir: Path) -> Path:
    xmls = sorted(filing_dir.glob("*.xml"))
    if not xmls:
        raise SystemExit(f"no XML files under {filing_dir}")

    all_results: list[dict] = []
    for xml in xmls:
        print(f"[scan] {xml.name} ({xml.stat().st_size:,} bytes)")
        try:
            tables = extract_csm_tables(xml)
        except Exception as exc:  # PoC: catch & report rather than abort
            print(f"  ! error: {exc}")
            continue
        print(f"  -> {len(tables)} CSM-candidate table(s)")
        for t in tables:
            print(f"     score={t.score} line={t.line_no} "
                  f"caption={t.caption[:60]!r}")
            print(f"     reasons={t.reasons}")
            print(f"     rows={len(t.rows)} cols={len(t.rows[0]) if t.rows else 0}")
            d = to_jsonable(t)
            d["_source_xml"] = xml.name
            all_results.append(d)

    out = settings.extracted_dir / f"{filing_dir.name}_csm.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[wrote] {out}  ({len(all_results)} table(s))")
    return out


if __name__ == "__main__":
    target = settings.raw_dir / "KR0008_20250311001055"
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    extract_dir(target)
