#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the lineage-sidecar record of BS cell keys (read-only).  usage: bspl_apply_sidecar_cell.py KR1000|10|2023.1Q ..."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sd = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
for k in sys.argv[1:]:
    r = sd.get(k)
    print(k, "->", json.dumps(r, ensure_ascii=False, indent=1)[:1500] if r else None)
