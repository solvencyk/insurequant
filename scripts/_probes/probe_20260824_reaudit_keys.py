# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
OUT = ROOT / "artifacts" / "validation" / "reaudit_20260824_keys.txt"
OUT.write_text(json.dumps(recs[0], ensure_ascii=False, indent=2) + "\n" + repr(list(recs[0].keys())), encoding="utf-8")
print("ok")
