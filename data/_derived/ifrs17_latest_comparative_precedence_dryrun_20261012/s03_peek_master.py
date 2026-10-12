"""Read-only: print master rows filtered by company code / quarter / item.

usage: python s03_peek_master.py <file.json> [--co KR0074] [--q 2023.4Q] [--item 1] [--limit 60]
file is a repo-root-relative path (CSM_waterfall.json, PL_breakdown.json, IFRS17_BS.json, ...).
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


def main():
    a = sys.argv[1:]
    path = a[0]
    opts = {}
    i = 1
    while i < len(a):
        opts[a[i].lstrip("-")] = a[i + 1]
        i += 2
    d = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if isinstance(d, dict):
        print("dict keys", list(d.keys())[:20])
        rows = d.get("cells") or d.get("rows") or []
    else:
        rows = d
    n = 0
    lim = int(opts.get("limit", 60))
    for r in rows:
        if "co" in opts and opts["co"] not in (r.get("원보험사코드"), r.get("원수사명"), r.get("company"), r.get("company_code")):
            continue
        if "q" in opts and opts["q"] != r.get("공시분기") and opts["q"] != r.get("quarter"):
            continue
        if "item" in opts and str(opts["item"]) != str(r.get("항목번호", r.get("item"))):
            continue
        print(json.dumps(r, ensure_ascii=False))
        n += 1
        if n >= lim:
            print("... limit")
            break
    print("matched", n, "of", len(rows))


if __name__ == "__main__":
    main()
