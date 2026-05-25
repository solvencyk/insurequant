# -*- coding: utf-8 -*-
"""Apply B3 row alias map to extracted liability skim JSON.

Reads:  ``data/ifrs17/extracted/*_liability.json``
Writes: ``data/ifrs17/normalized/*_liability_normalized.json``

Each ``rows[*]`` becomes ``{\"cells\": [...], \"canonical_key\": str | null}``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _normalize_tables(
    tables: list,
    nz,
    *,
    aliases_version: int | None,
    source_rel: str,
) -> tuple[list[dict], dict]:
    out_tables: list[dict] = []
    total_rows = 0
    tagged = 0
    counts_by_key: dict[str, int] = {}

    for tbl in tables:
        if not isinstance(tbl, dict):
            continue
        copy = dict(tbl)
        rows = copy.get("rows")
        new_rows = []
        if isinstance(rows, list):
            for item in rows:
                if isinstance(item, dict) and "cells" in item:
                    cells = item.get("cells")
                elif isinstance(item, list):
                    cells = item
                else:
                    cells = []
                if not isinstance(cells, list):
                    cells = []
                wrapped = nz.tag_row_cells(cells)
                total_rows += 1
                if wrapped["canonical_key"] is not None:
                    tagged += 1
                    k = wrapped["canonical_key"]
                    counts_by_key[k] = counts_by_key.get(k, 0) + 1
                new_rows.append(wrapped)
            copy["rows"] = new_rows
        out_tables.append(copy)

    meta = {
        "source_file_rel": source_rel,
        "aliases_yaml_version": aliases_version,
        "aliases_scope_effective": nz.scope,
        "row_statistics": {
            "rows_total": total_rows,
            "rows_with_canonical": tagged,
            "rows_unresolved": total_rows - tagged,
            "counts_by_canonical_key": counts_by_key,
        },
    }
    return out_tables, meta


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize IFRS17 liability skim JSON.")
    ap.add_argument(
        "--aliases",
        type=Path,
        default=None,
        help="Path to row_aliases.yaml (repo default if omitted)",
    )
    ap.add_argument(
        "--extracted-dir",
        type=Path,
        default=None,
        help="Override extracted directory (default: data/ifrs17/extracted)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override output directory (default: data/ifrs17/normalized)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print stats only, do not write files",
    )
    ns = ap.parse_args()

    from src.ifrs17.row_normalizer import (
        DEFAULT_ROW_ALIASES_PATH,
        load_row_aliases,
    )

    aliases_path = ns.aliases or DEFAULT_ROW_ALIASES_PATH
    nz = load_row_aliases(aliases_path)
    aliases_version = nz.version
    aliases_scope = nz.scope

    repo = REPO
    extracted_dir = ns.extracted_dir or (repo / "data" / "ifrs17" / "extracted")
    out_dir = ns.out_dir or (repo / "data" / "ifrs17" / "normalized")
    if not ns.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(extracted_dir.glob("*_liability.json"))
    if not sources:
        print(f"No *_liability.json under {extracted_dir}", file=sys.stderr)
        return 1

    agg = {
        "files": len(sources),
        "rows_total": 0,
        "rows_with_canonical": 0,
        "per_file": [],
    }

    for src in sources:
        rel_src = src.relative_to(repo).as_posix()
        payload = json.loads(src.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            print(f"Skip (not JSON array): {src.name}", file=sys.stderr)
            continue
        norm_tables, meta = _normalize_tables(
            payload,
            nz,
            aliases_version=aliases_version,
            source_rel=rel_src,
        )
        agg["rows_total"] += meta["row_statistics"]["rows_total"]
        agg["rows_with_canonical"] += meta["row_statistics"]["rows_with_canonical"]
        agg["per_file"].append(
            {
                "file": src.name,
                **meta["row_statistics"],
            }
        )

        stem = src.stem
        if stem.endswith("_liability"):
            out_name = stem + "_normalized.json"
        else:
            out_name = stem + "_liability_normalized.json"
        dst = out_dir / out_name
        try:
            aliases_rel = aliases_path.relative_to(repo).as_posix()
        except ValueError:
            aliases_rel = str(aliases_path)
        envelope = {
            "normalization_engine": {
                "script": Path(__file__).name,
                "aliases_file": aliases_rel,
                "aliases_version": aliases_version,
                "aliases_scope": aliases_scope,
            },
            **meta,
            "tables": norm_tables,
        }
        if not ns.dry_run:
            dst.write_text(
                json.dumps(envelope, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    print(json.dumps({"summary": agg}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
