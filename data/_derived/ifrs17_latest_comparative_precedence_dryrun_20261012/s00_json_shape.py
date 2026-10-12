"""Read-only helper: print the shape of JSON files (keys, lengths, a few samples).

usage: python s00_json_shape.py <path> [<path> ...] [--n 3]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def shape(obj, depth=0, maxdepth=3, n=3):
    pad = "  " * depth
    if isinstance(obj, dict):
        print(f"{pad}dict len={len(obj)}")
        if depth >= maxdepth:
            return
        kmax = max(n, 14) if depth == 0 else n
        for i, (k, v) in enumerate(obj.items()):
            if i >= kmax:
                print(f"{pad}  ... (+{len(obj) - kmax} more keys)")
                break
            print(f"{pad}  key={k!r}:", end=" ")
            if isinstance(v, (dict, list)):
                print()
                shape(v, depth + 2, maxdepth, n)
            else:
                s = repr(v)
                print(s[:200])
    elif isinstance(obj, list):
        print(f"{pad}list len={len(obj)}")
        if depth >= maxdepth:
            return
        for i, v in enumerate(obj[:n]):
            if isinstance(v, (dict, list)):
                shape(v, depth + 1, maxdepth, n)
            else:
                print(f"{pad}  {repr(v)[:200]}")
    else:
        print(f"{pad}{repr(obj)[:200]}")


def main():
    args = sys.argv[1:]
    n = 3
    if "--n" in args:
        i = args.index("--n")
        n = int(args[i + 1])
        del args[i:i + 2]
    for a in args:
        p = Path(a)
        print("=" * 100)
        print(p, p.stat().st_size if p.exists() else "MISSING")
        if not p.exists():
            continue
        obj = json.loads(p.read_text(encoding="utf-8"))
        shape(obj, n=n)


if __name__ == "__main__":
    main()
