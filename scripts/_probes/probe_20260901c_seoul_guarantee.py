# -*- coding: utf-8 -*-
import json, io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
qs = sorted({r["공시분기"] for r in data if r["원보험사코드"] == "KR0150"})
print("KR0150 서울보증보험 all quarters in master:", qs)
