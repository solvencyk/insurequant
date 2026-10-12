"""Read-only: compact dump of a registry JSON (entries/cells dicts or lists), one line per entry.

usage: python s04_dump_registry.py <path> [--w 260]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]


def short(v, w):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    s = s.replace("\n", " ")
    return s if len(s) <= w else s[:w] + "…"


def main():
    a = sys.argv[1:]
    w = 260
    if "--w" in a:
        i = a.index("--w")
        w = int(a[i + 1])
        del a[i:i + 2]
    p = ROOT / a[0]
    d = json.loads(p.read_text(encoding="utf-8"))
    print("FILE", p.name, "type", type(d).__name__, "len", len(d))
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (dict, list)) and len(v) > 0 and k not in ("_tolerance", "_pin_tolerance", "_population", "_threshold"):
                print(f"[{k}] {type(v).__name__} len={len(v)}")
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        print("   ", kk, "=>", short(vv, w))
                else:
                    for vv in v:
                        print("   ", short(vv, w))
            else:
                print(f"[{k}]", short(v, w))
    else:
        for vv in d:
            print("  ", short(vv, w))


if __name__ == "__main__":
    main()
