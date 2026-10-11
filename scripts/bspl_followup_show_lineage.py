#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
k = sys.argv[1]
ov = json.loads((ROOT / "data/dart/viz/bs_manual_overrides.json").read_text(encoding="utf-8"))["cells"].get(k)
sd = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"].get(k)
print("OVERLAY:", json.dumps(ov, ensure_ascii=False, indent=1)[:1500])
print("SIDECAR:", json.dumps(sd, ensure_ascii=False, indent=1)[:1500])
