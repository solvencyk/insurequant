#!/usr/bin/env python3
"""Golden-output gate for scripts/viz_build_csm_waterfall.py.

The builder is 1.3k lines of per-company CSM-rollforward-table heuristics
(stage-label matching, product-segmented-table detection, transition/
reconciliation new-business overrides, unit-scale inference) with no test
coverage, so the only trustworthy way to refactor it is to prove the single
artefact it writes did not move:

    data/dart/viz/csm_waterfall.json

The builder is a pure function of data/dart/extracted/*_measurement.json,
all committed/present on disk, and does no network I/O, no randomness, and
writes no timestamps into its output -- so a byte-identical rerun is the
expected result (verified: two consecutive runs during test authoring
produced identical sha256). Nothing is excluded from the hash.

It takes ~1-2s and overwrites the live artefact in place, so it runs
unconditionally (no RUN_*_GOLDEN opt-in needed). The artefact is restored
from backup if a drift or exception occurs, so a broken refactor cannot
leave it in a half-written or diverged state; on a clean pass the rebuilt
bytes are identical to what was already committed, so the working tree
stays clean either way.

When the OUTPUT LEGITIMATELY CHANGES -- new quarter of DART extracts, a real
extraction fix -- regenerate the manifest instead of editing the hashes:

    python scripts/viz_build_csm_waterfall.py
    python tests/test_viz_csm_waterfall_golden.py --update

and say in the commit message why the numbers moved.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "fixtures" / "viz_csm_waterfall_golden.json"
BUILDER = REPO / "scripts" / "viz_build_csm_waterfall.py"
OUT = REPO / "data" / "dart" / "viz" / "csm_waterfall.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    companies = payload.get("companies") or []
    statuses: dict[str, int] = {}
    for c in companies:
        s = str(c.get("status"))
        statuses[s] = statuses.get(s, 0) + 1
    return {
        "sha256": _sha256(OUT),
        "companies": len(companies),
        "status_counts": statuses,
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


def test_builder_output_matches_golden():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    backup = OUT.read_bytes()
    try:
        _run_builder()
        actual = _manifest()
    except Exception:
        OUT.write_bytes(backup)
        raise

    drift = {k: (expected.get(k), actual[k]) for k in actual if expected.get(k) != actual[k]}
    if drift:
        OUT.write_bytes(backup)
    assert not drift, (
        "viz_build_csm_waterfall.py output moved (expected, actual):\n"
        + "\n".join(f"  {k}: {e} -> {a}" for k, (e, a) in drift.items())
        + f"\nIf the change is intended, regenerate: python {GOLDEN.name} --update"
    )


def _update() -> int:
    """Rewrite the manifest from the artefact currently on disk."""
    if not OUT.exists():
        print("run scripts/viz_build_csm_waterfall.py first", file=sys.stderr)
        return 1
    man = _manifest()
    man["_what"] = (
        "Refactor safety net for scripts/viz_build_csm_waterfall.py. Captured "
        "before the 1,344-line builder was touched. Pins sha256 + company/status "
        "counts for data/dart/viz/csm_waterfall.json."
    )
    GOLDEN.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {GOLDEN}: {man['companies']} companies {man['status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_update() if "--update" in sys.argv else 0)
