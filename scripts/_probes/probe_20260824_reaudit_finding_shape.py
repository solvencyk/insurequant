# -*- coding: utf-8 -*-
import json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
from solvency.validation.kics_json_rules import run_validation
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
r = run_validation(data)
print("KEYS:", list(r.keys()))
for k, v in r.items():
    print(k, type(v), (len(v) if hasattr(v, "__len__") else v))
    if isinstance(v, list) and v:
        print("  sample:", json.dumps(v[0], ensure_ascii=False, default=str)[:600])
