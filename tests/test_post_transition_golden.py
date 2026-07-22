#!/usr/bin/env python3
"""Golden gate for scripts/fill_post_transition_to_disclosure.py.

This script writes `값_적용후` into the live kics_disclosure.json in place, and
_extract_post_values is 569 lines of per-company transition-table quirks
(KR0082 unit-fix vote, KR0004 stale-tag inheritance, KR0073 multi-breakdown
selection, …). The only safe way to touch it is to prove the値 it would write
do not move.

Rather than run the whole writer, this drives the pure core directly — for
every md_inbox period it re-derives {(code, quarter, item_no): (pre, post,
source)} exactly as _process_period does — and hashes the result. No master is
touched. Deterministic and offline (~8s), so it runs unconditionally.

If the numbers legitimately change (new quarter of MD, a real extraction fix),
regenerate and say why in the commit:

    python tests/test_post_transition_golden.py --update
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "fixtures" / "post_transition_golden.json"
SCRIPT = REPO / "scripts" / "fill_post_transition_to_disclosure.py"


def _load_module():
    sys.path.insert(0, str(REPO))
    spec = importlib.util.spec_from_file_location("fill_post_transition", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _derive() -> dict:
    """Every (code, quarter, item) → (pre, post, source) the script would write."""
    mod = _load_module()
    rows = json.loads(mod.JSON_PATH.read_text(encoding="utf-8"))
    index = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in rows}

    periods = sorted(p.name for p in mod.MD_INBOX.glob("FY*_Q?") if p.is_dir())
    out: dict[str, list] = {}
    for period in periods:
        quarter = mod._md_period_to_quarter(period)
        md_dir = mod.MD_INBOX / period
        if not md_dir.is_dir():
            continue
        for md_path in sorted(md_dir.glob("*.md")):
            code = md_path.stem.split("_", 1)[0]
            text = md_path.read_text(encoding="utf-8")
            tables = mod._scan_tables_with_context(text)
            existing = {
                item_no: row.get("값")
                for (c, q, item_no), row in index.items()
                if c == code and q == quarter
            }
            post_map, provenance, _dbg, _uf = mod._extract_post_values(tables, code, existing)
            for item_no, (pre, post) in sorted(post_map.items()):
                out.setdefault(f"{code}|{quarter}", []).append(
                    [item_no, pre, post, provenance.get(item_no)]
                )
    return out


def _manifest(derived: dict) -> dict:
    blob = json.dumps(derived, ensure_ascii=False, sort_keys=True)
    cells = sum(len(v) for v in derived.values())
    return {
        "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "company_quarters": len(derived),
        "cells": cells,
    }


def test_post_transition_extraction_matches_golden():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    actual = _manifest(_derive())
    drift = {k: (expected.get(k), actual[k]) for k in actual if expected.get(k) != actual[k]}
    assert not drift, (
        "fill_post_transition_to_disclosure extraction moved (expected, actual):\n"
        + "\n".join(f"  {k}: {e} -> {a}" for k, (e, a) in drift.items())
        + f"\nIf intended, regenerate: python {GOLDEN.name} --update"
    )


def _update() -> int:
    derived = _derive()
    man = _manifest(derived)
    man["_what"] = ("Refactor safety net for _extract_post_values. Captured before the "
                    "569-line function was split. Hash covers every (code, quarter, item) "
                    "→ (pre, post, source) it would write into kics_disclosure.json.")
    GOLDEN.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {GOLDEN}: {man['cells']} cells / {man['company_quarters']} company-quarters")
    return 0


if __name__ == "__main__":
    raise SystemExit(_update() if "--update" in sys.argv else 0)
