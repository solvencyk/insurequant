#!/usr/bin/env python3
"""Full cell-key combo-diff of PL_breakdown.json before/after the KR0083 2024.3Q sign fix.
Compares EVERY (원보험사코드, 항목번호, 공시분기) row's 값 and 값_당분기 between the pre-fix
backup and the current on-disk file. Prints every changed cell and asserts row count / key-set
are otherwise identical (no cell lost, no cell added, no unrelated cell moved)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BEFORE = Path(sys.argv[1])
AFTER = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("PL_breakdown.json")


def _idx(rows):
    return {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}


def main():
    before = json.loads(BEFORE.read_text(encoding="utf-8"))
    after = json.loads(AFTER.read_text(encoding="utf-8"))
    print(f"before rows: {len(before)}  after rows: {len(after)}")
    bi, ai = _idx(before), _idx(after)
    print(f"before keys: {len(bi)}  after keys: {len(ai)}")
    missing = set(bi) - set(ai)
    added = set(ai) - set(bi)
    print(f"keys missing after (LOST cells): {len(missing)}")
    for k in sorted(missing):
        print("  LOST", k)
    print(f"keys added after (NEW cells): {len(added)}")
    for k in sorted(added):
        print("  NEW", k)

    changed = []
    for k in sorted(set(bi) & set(ai), key=lambda t: tuple(str(x) for x in t)):
        b, a = bi[k], ai[k]
        if b.get("값") != a.get("값") or b.get("값_당분기") != a.get("값_당분기"):
            changed.append((k, b.get("값"), a.get("값"), b.get("값_당분기"), a.get("값_당분기")))

    print(f"\ncells with 값 or 값_당분기 changed: {len(changed)}")
    for k, bv, av, bd, ad in changed:
        print(f"  {k}: 값 {bv} -> {av}   |   값_당분기 {bd} -> {ad}")

    other_field_diffs = 0
    for k in sorted(set(bi) & set(ai), key=lambda t: tuple(str(x) for x in t)):
        b, a = bi[k], ai[k]
        for field in ("원수사명", "티커", "생손보여부", "항목명"):
            if b.get(field) != a.get(field):
                other_field_diffs += 1
                print(f"  OTHER-FIELD-DIFF {k} {field}: {b.get(field)!r} -> {a.get(field)!r}")
    print(f"\nother-field diffs (원수사명/티커/생손보여부/항목명): {other_field_diffs}")


if __name__ == "__main__":
    main()
