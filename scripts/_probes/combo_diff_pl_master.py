#!/usr/bin/env python3
"""Combo-diff: compare a 'before' and 'after' PL master JSON cell-by-cell, keyed by
(code, item, quarter). Reports: new cells added, cells changed (should be 0 for items 1-24
if this run only ADDED new OCI items), cells removed (should be 0)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in d}


def main(before_path, after_path):
    before = load(before_path)
    after = load(after_path)
    before_keys, after_keys = set(before), set(after)
    added = after_keys - before_keys
    removed = before_keys - after_keys
    common = before_keys & after_keys
    changed = [(k, before[k], after[k]) for k in common if before[k] != after[k]]
    print(f"before: {len(before)} cells   after: {len(after)} cells")
    print(f"added (new cells): {len(added)}")
    added_items = {}
    for c, it, q in added:
        added_items[it] = added_items.get(it, 0) + 1
    for it, n in sorted(added_items.items(), key=lambda x: str(x[0])):
        print(f"   item {it}: +{n}")
    print(f"removed (cells that disappeared): {len(removed)}")
    for k in sorted(removed)[:20]:
        print(f"   REMOVED {k}")
    print(f"changed (same key, different value) among items 1-24: "
          f"{sum(1 for k,_,_ in changed if isinstance(k[1], int) and k[1] <= 24)}")
    print(f"changed (same key, different value) TOTAL (incl new items): {len(changed)}")
    for k, b, a in changed[:30]:
        print(f"   CHANGED {k}: {b} -> {a}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
