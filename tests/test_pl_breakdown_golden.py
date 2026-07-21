#!/usr/bin/env python3
"""Golden-output gate for scripts/build_pl_breakdown.py.

The builder is 4.9k lines of per-company DART note handlers, so the only
trustworthy way to refactor it is to prove the outputs did not move. This
test reruns the builder and compares both artefacts against a manifest
captured before the change:

    data/dart/viz/pl_breakdown_master.json
    data/_derived/pl_breakdown_coverage.json

The builder is deterministic and offline (the DART FS API responses are
cached under data/dart/_fs_api_cache/), so a byte-identical rerun is the
expected result.

It takes ~95s and overwrites the live artefacts, so it is opt-in:

    RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py

The artefacts are restored on failure, so a broken refactor cannot leave
the masters in a half-written state.

When the OUTPUT LEGITIMATELY CHANGES -- new quarter of DART raw, a real
extraction fix -- regenerate the manifest instead of editing the hashes:

    python scripts/build_pl_breakdown.py
    python tests/test_pl_breakdown_golden.py --update

and say in the commit message why the numbers moved.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "fixtures" / "pl_breakdown_golden.json"
MASTER = REPO / "data" / "dart" / "viz" / "pl_breakdown_master.json"
COVERAGE = REPO / "data" / "_derived" / "pl_breakdown_coverage.json"
BUILDER = REPO / "scripts" / "build_pl_breakdown.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    cov = json.loads(COVERAGE.read_text(encoding="utf-8"))
    return {
        "sha256_master": _sha256(MASTER),
        "sha256_coverage": _sha256(COVERAGE),
        "master_rows": len(rows),
        "company_quarters": len({(r["원보험사코드"], r["공시분기"]) for r in rows}),
        "coverage_rows": len(cov),
        "non_null_values": sum(1 for r in rows if r["값"] is not None),
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
    assert proc.returncode == 0, f"builder failed:\n{proc.stdout}\n{proc.stderr}"


@pytest.mark.skipif(
    not os.environ.get("RUN_PL_GOLDEN"),
    reason="slow (~95s) and rewrites the live masters; set RUN_PL_GOLDEN=1",
)
def test_builder_output_matches_golden():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    backups = {p: p.read_bytes() for p in (MASTER, COVERAGE)}
    try:
        _run_builder()
        actual = _manifest()
    except Exception:
        for path, blob in backups.items():
            path.write_bytes(blob)
        raise

    drift = {
        k: (expected[k], actual[k]) for k in actual if expected.get(k) != actual[k]
    }
    if drift:
        for path, blob in backups.items():
            path.write_bytes(blob)
    assert not drift, (
        "build_pl_breakdown.py output moved (expected, actual):\n"
        + "\n".join(f"  {k}: {e} -> {a}" for k, (e, a) in drift.items())
        + f"\nIf the change is intended, regenerate: python {GOLDEN.name} --update"
    )


def _update() -> int:
    """Rewrite the manifest from the artefacts currently on disk."""
    if not MASTER.exists() or not COVERAGE.exists():
        print("run scripts/build_pl_breakdown.py first", file=sys.stderr)
        return 1
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    golden.update(_manifest())
    GOLDEN.write_text(
        json.dumps(golden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"updated {GOLDEN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_update() if "--update" in sys.argv else 0)
