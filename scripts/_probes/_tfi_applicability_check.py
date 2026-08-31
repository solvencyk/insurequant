# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "data" / "_derived" / "kics_transition_applicability.json"
d = json.loads(p.read_text(encoding="utf-8"))
print(type(d), len(d) if hasattr(d, "__len__") else "")
if isinstance(d, dict):
    print(list(d.items())[:3])
elif isinstance(d, list):
    print(d[:3])
