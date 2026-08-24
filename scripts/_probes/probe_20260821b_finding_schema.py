# -*- coding: utf-8 -*-
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.loads((REPO / "artifacts" / "kics_validation" / "report_latest.json").read_text(encoding="utf-8"))
findings = data["findings"]
for f in findings:
    if f.get("rule") == "3_tier2_composition" and f.get("status") == "RED":
        print(json.dumps(f, ensure_ascii=False, indent=2))
        break
