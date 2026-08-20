#!/usr/bin/env python3
"""Golden-output gate for scripts/build_dividend.py.

Pins dividend.json's output bytes (sha256 + row/company/item counts) so a refactor can't
silently change what gets written. The builder is a pure function of
data/dart/_alotmatter_cache/*.json + data/_derived/alotmatter_fetch_census.json (both
committed, offline) -- no network I/O, no randomness, no timestamps -- so a byte-identical
rerun is expected, same pattern as tests/test_ifrs17_bs_golden.py.

Runs unconditionally (fast, offline); restores the prior artefact from backup on drift or
exception so a broken change can't leave the working tree half-written.

When the OUTPUT LEGITIMATELY CHANGES -- a new quarter's disclosure lands, an se-mapping fix --
regenerate instead of hand-editing the hash:

    python scripts/build_dividend.py
    python tests/test_dividend_golden.py --update

and say in the commit message why the numbers moved.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "fixtures" / "dividend_golden.json"
BUILDER = REPO / "scripts" / "build_dividend.py"
OUT = REPO / "dividend.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    rows = json.loads(OUT.read_text(encoding="utf-8"))
    items = Counter(r["항목번호"] for r in rows)
    return {
        "sha256": _sha256(OUT),
        "rows": len(rows),
        "companies": len({r["원보험사코드"] for r in rows}),
        "quarters": len({r["공시분기"] for r in rows}),
        "rows_per_item": {str(k): v for k, v in sorted(items.items())},
    }


def _run_builder() -> None:
    proc = subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, f"{BUILDER.name} failed:\n{proc.stdout}\n{proc.stderr}"


def test_builder_output_matches_golden():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    backup = OUT.read_bytes() if OUT.exists() else None
    try:
        _run_builder()
        actual = _manifest()
    except Exception:
        if backup is not None:
            OUT.write_bytes(backup)
        raise

    drift = {k: (expected.get(k), actual[k]) for k in actual if expected.get(k) != actual[k]}
    if drift and backup is not None:
        OUT.write_bytes(backup)
    assert not drift, (
        "build_dividend.py output moved (expected, actual):\n"
        + "\n".join(f"  {k}: {e} -> {a}" for k, (e, a) in drift.items())
        + f"\nIf the change is intended, regenerate: python {GOLDEN.name} --update"
    )


def _update() -> int:
    if not OUT.exists():
        print("run scripts/build_dividend.py first", file=sys.stderr)
        return 1
    man = _manifest()
    man["_what"] = (
        "Refactor safety net for scripts/build_dividend.py (2026-08-14, "
        "inbox/parser/20260814T0938Z). Pins sha256 + row/company/quarter/per-item counts "
        "for dividend.json."
    )
    GOLDEN.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {GOLDEN}: {man['rows']} rows, {man['companies']} companies")
    return 0


if __name__ == "__main__":
    raise SystemExit(_update() if "--update" in sys.argv else 0)
