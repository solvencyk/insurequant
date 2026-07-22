#!/usr/bin/env python3
"""Golden-output gate for scripts/viz_build_ifrs17_panels.py.

The builder is 1.3k lines of per-table extraction heuristics (year-bucket
classification, CSM/PL/BS/sensitivity table picking, unit normalization) with
no test coverage, so the only trustworthy way to refactor it is to prove the
four panels it writes did not move. This test reruns the builder and compares
all four artefacts against a manifest captured before the change:

    data/dart/viz/csm_amort_schedule.json
    data/dart/viz/insurance_pl_breakdown.json
    data/dart/viz/bs_snapshot.json
    data/dart/viz/sensitivity_heatmap.json

The builder is a pure function of data/dart/extracted/*.json (+ the root
CSM_waterfall.json for unit cross-checks and data/dart/viz/sensitivity_
overrides.json), all committed/present on disk, and does no network I/O, no
randomness, and writes no timestamps into its output — so a byte-identical
rerun is the expected result (verified: two consecutive runs during test
authoring produced identical sha256 for all four files). Nothing is excluded
from the hash.

It takes ~1-2s and overwrites the four live artefacts in place, so it runs
unconditionally (no RUN_*_GOLDEN opt-in needed). The artefacts are restored
from backup if a drift or exception occurs, so a broken refactor cannot leave
them in a half-written or diverged state; on a clean pass the rebuilt bytes
are identical to what was already committed, so the working tree stays clean
either way.

When the OUTPUT LEGITIMATELY CHANGES -- new quarter of DART extracts, a real
extraction fix -- regenerate the manifest instead of editing the hashes:

    python scripts/viz_build_ifrs17_panels.py
    python tests/test_viz_ifrs17_panels_golden.py --update

and say in the commit message why the numbers moved.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "fixtures" / "viz_ifrs17_panels_golden.json"
BUILDER = REPO / "scripts" / "viz_build_ifrs17_panels.py"

OUTPUTS = [
    REPO / "data" / "dart" / "viz" / "csm_amort_schedule.json",
    REPO / "data" / "dart" / "viz" / "insurance_pl_breakdown.json",
    REPO / "data" / "dart" / "viz" / "bs_snapshot.json",
    REPO / "data" / "dart" / "viz" / "sensitivity_heatmap.json",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    companies = payload.get("companies") or []
    statuses: dict[str, int] = {}
    for c in companies:
        s = str(c.get("status"))
        statuses[s] = statuses.get(s, 0) + 1
    return {
        "sha256": _sha256(path),
        "companies": len(companies),
        "status_counts": statuses,
    }


def _manifest() -> dict:
    return {p.name: _file_manifest(p) for p in OUTPUTS}


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
    backups = {p: p.read_bytes() for p in OUTPUTS}
    try:
        _run_builder()
        actual = _manifest()
    except Exception:
        for path, blob in backups.items():
            path.write_bytes(blob)
        raise

    drift = {
        fname: (expected["files"].get(fname), actual[fname])
        for fname in actual
        if expected["files"].get(fname) != actual[fname]
    }
    if drift:
        for path, blob in backups.items():
            path.write_bytes(blob)
    assert not drift, (
        "viz_build_ifrs17_panels.py output moved (expected, actual):\n"
        + "\n".join(f"  {k}: {e} -> {a}" for k, (e, a) in drift.items())
        + f"\nIf the change is intended, regenerate: python {GOLDEN.name} --update"
    )


def _update() -> int:
    """Rewrite the manifest from the artefacts currently on disk."""
    missing = [p for p in OUTPUTS if not p.exists()]
    if missing:
        print(f"run scripts/viz_build_ifrs17_panels.py first (missing {missing})", file=sys.stderr)
        return 1
    man = {"files": _manifest()}
    man["_what"] = (
        "Refactor safety net for scripts/viz_build_ifrs17_panels.py. Captured "
        "before the 1,309-line builder was touched. Pins sha256 + company/status "
        "counts for all four panel JSONs it writes under data/dart/viz/."
    )
    GOLDEN.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {GOLDEN}")
    for fname, info in man["files"].items():
        print(f"  {fname}: {info['companies']} companies {info['status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_update() if "--update" in sys.argv else 0)
