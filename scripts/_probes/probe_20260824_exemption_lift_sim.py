"""Read-only: in-memory simulation — what does the gate print if the assigned
exemptions are lifted (registry emptied)?  Nothing is written to disk; the module
globals are patched inside this process only.

Axes measured:
  _transition_mmult_after            (mmult 3 axes on 값_적용후)
  _parent_present_child_incomplete_after
  _diversification_negative
  _post_transition_parent_census
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_kics_disclosure as V  # noqa: E402

TARGETS = {("KR0097", "2024.4Q"), ("KR0049", "2024.3Q"), ("KR0079", "2023.2Q")}


def run(tag):
    recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    mm, sm, skipped, unver = V._transition_mmult_after(recs)
    census = V._parent_present_child_incomplete_after(recs)
    div = V._diversification_negative(recs)
    pred, prev = V._post_transition_parent_census(recs)
    print(f"--- {tag} ---")
    print(f"  mmult_after mismatch total = {len(mm)}")
    for row in mm:
        if (row[0], row[1]) in TARGETS:
            print(f"     * {row}")
    print(f"  mmult_after sub_missing total = {len(sm)}")
    for row in sm:
        if (row[0], row[1]) in TARGETS:
            print(f"     * {row}")
    print(f"  parent_child_after_census total = {len(census)}")
    for row in census:
        if (row[0], row[1]) in TARGETS:
            print(f"     * {row}")
    print(f"  diversification_negative total = {len(div)}")
    for row in div:
        if (row[0], row[1]) in TARGETS:
            print(f"     * {row}")
    print(f"  post_parent_census red={len(pred)} review={len(prev)}")
    for row in pred:
        if (row[0], row[1]) in TARGETS:
            print(f"     * RED {row}")
    for row in prev:
        if (row[0], row[1]) in TARGETS:
            print(f"     * REV {row}")
    dx = {k: v for k, v in skipped.items() if "DOCUMENTED_EXEMPT" in k}
    print(f"  skipped[DOCUMENTED_EXEMPT] = {dx}")


def main():
    run("BASELINE (exemptions in force)")
    V._AFTER_SUBRISK_NOT_DISCLOSED = set()
    V._POST_PARENT_NOT_DISCLOSED = frozenset()
    run("LIFTED (_AFTER_SUBRISK_NOT_DISCLOSED and _POST_PARENT_NOT_DISCLOSED emptied)")


if __name__ == "__main__":
    main()
