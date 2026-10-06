# -*- coding: utf-8 -*-
"""Re-run the PL builder's PARSE step (read-only) for the 29 orphan-parent buckets and dump
the tier1/tier2 dicts, especially the hidden keys that feed item3/item8.

Writes nothing to any master. Pure diagnosis.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_pl_breakdown as B  # noqa: E402

BUCKETS = {
    "KR0002": ["2023.1Q", "2023.2Q"],
    "KR0003": ["2023.2Q", "2023.3Q"],
    "KR0004": ["2023.4Q", "2024.4Q", "2025.4Q"],
    "KR0005": ["2023.2Q"],
    "KR0029": ["2023.4Q", "2024.4Q", "2025.4Q"],
    "KR0068": ["2023.1Q", "2023.2Q"],
    "KR0069": ["2023.1Q", "2023.2Q"],
    "KR0071": ["2023.1Q", "2023.2Q"],
    "KR0073": ["2023.1Q", "2023.2Q"],
    "KR0074": ["2023.4Q"],
    "KR0075": ["2023.4Q"],
    "KR0083": ["2023.1Q", "2023.2Q"],
    "KR0094": ["2023.1Q", "2023.2Q"],
    "KR0095": ["2023.4Q"],
    "KR0097": ["2023.4Q"],
    "KR0104": ["2023.1Q", "2023.2Q"],
}

HIDDEN = ("_jang_rev", "_jang_cost", "_jang_rerev", "_jang_recost", "_jang_net",
          "_life_rev", "_life_cost", "_life_rerev", "_life_recost",
          "_is_rev", "_is_cost", "_is_rerev", "_is_recost", "_extra_lob")

uni = B.load_universe()
filings = B.discover_filings()

out = {}
for code, quarters in BUCKETS.items():
    name, life_flag = uni.get(code, (code, None))
    is_life = (life_flag == "생명보험")
    for q in quarters:
        dirs = filings.get(code, {}).get(q)
        print(f"=== {code} {name} ({life_flag}) {q} ===")
        if not dirs:
            print("   !! not discovered by discover_filings()")
            continue
        print(f"   dirs: {[str(d) for d in dirs]}")
        t1_html, t2 = B.parse_filing(dirs, is_life, code=code, name=name, quarter=q)
        t1_api = B._fs_tier1(name, q, code)
        t1 = t1_api if t1_api else t1_html
        print(f"   t1 source: {'FS-API' if t1_api else ('HTML' if t1_html else 'NONE')}")
        for tag, d in (("t1", t1), ("t1_html", t1_html), ("t2", t2)):
            if d is None:
                print(f"   {tag}: None")
                continue
            hid = {k: d.get(k) for k in HIDDEN if k in d}
            num = {k: v for k, v in d.items() if isinstance(k, int)}
            print(f"   {tag}: items={ {k: (round(v,1) if isinstance(v,float) else v) for k,v in sorted(num.items())} }")
            print(f"   {tag}: hidden={hid}")
        out[f"{code}|{q}"] = {
            "t1_src": "api" if t1_api else ("html" if t1_html else None),
            "t2_keys": sorted([str(k) for k in (t2 or {}).keys()]),
            "hidden_t1": {k: (t1 or {}).get(k) for k in HIDDEN if k in (t1 or {})},
            "hidden_t1_html": {k: (t1_html or {}).get(k) for k in HIDDEN if k in (t1_html or {})},
            "hidden_t2": {k: (t2 or {}).get(k) for k in HIDDEN if k in (t2 or {})},
        }
        print()

dest = ROOT / "data" / "_derived" / "_probe_20260918_orphan_t1t2.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("written:", dest)
