# -*- coding: utf-8 -*-
import json, sys, collections
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
rep = json.loads((ROOT/"artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))
s = rep["summary"]
print("== summary ==")
print(json.dumps(s, ensure_ascii=False, indent=2)[:3000])
for sec in ("tier2_issuer_inconsistent_exception","life8_issuer_inconsistent_exception"):
    v = rep.get(sec)
    print(f"\n== {sec} ==")
    print(json.dumps(v, ensure_ascii=False, indent=2)[:2500])
