# -*- coding: utf-8 -*-
"""Key-level diff of my masters (working tree) against git HEAD: added / deleted / changed per master, and which companies the additions belong to.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe keydiff_vs_head.py [out.txt]
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")


def head(path):
    return json.loads(subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))


def live(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


SPECS = [
    ("CSM_waterfall.json", lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"])),
    ("CSM_amortization.json", lambda r: (r["원보험사코드"], r["공시분기"], r["경과차년"])),
    ("CSM_sensitivity.json", lambda r: (r["원보험사코드"], r["공시분기"], r["순번"])),
    ("insurance_liability_portfolio.json", lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"])),
]


def main() -> int:
    lines = []
    for path, key in SPECS:
        h, l = head(path), live(path)
        hk, lk = {key(r): r for r in h}, {key(r): r for r in l}
        assert len(hk) == len(h) and len(lk) == len(l), f"{path}: duplicate keys"
        added = [k for k in lk if k not in hk]
        deleted = [k for k in hk if k not in lk]
        changed = [k for k in lk if k in hk and lk[k] != hk[k]]
        prefix = l[: len(h)] == h
        who = Counter((k[0], k[1]) for k in added)
        lines.append(f"{path}: HEAD {len(h)} -> live {len(l)} | added {len(added)} | deleted {len(deleted)} | changed {len(changed)} | HEAD rows are an exact list prefix: {prefix}")
        lines.append(f"    added by (company, quarter): " + ", ".join(f"{c}/{q}:{n}" for (c, q), n in sorted(who.items())))
        if deleted or changed:
            lines.append(f"    !! deleted {deleted[:5]} changed {changed[:5]}")
    # sidecars
    for path, keyf in (("CSM_waterfall_provenance.json", lambda c: (c["company_code"], c["quarter"], c["item_block"])),
                       ("insurance_liability_portfolio_provenance.json", lambda c: json.dumps(c, sort_keys=True, ensure_ascii=False))):
        h, l = head(path), live(path)
        hc, lc = h["cells"], l["cells"]
        hk, lk = {keyf(c) for c in hc}, {keyf(c) for c in lc}
        lines.append(f"{path}: cells HEAD {len(hc)} -> live {len(lc)} | added {len(lk - hk)} | deleted {len(hk - lk)} | HEAD cells exact prefix: {lc[:len(hc)] == hc}")
        for k in h:
            if k == "cells":
                continue
            if isinstance(h[k], list) and isinstance(l.get(k), list):
                lines.append(f"    list key {k}: HEAD {len(h[k])} -> live {len(l[k])} | HEAD entries exact prefix: {l[k][:len(h[k])] == h[k]}")
            else:
                lines.append(f"    key {k}: unchanged = {h[k] == l.get(k)}")
        lines.append(f"    new top-level keys: {sorted(set(l) - set(h))}")
    txt = "\n".join(lines)
    print(txt)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(txt + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
