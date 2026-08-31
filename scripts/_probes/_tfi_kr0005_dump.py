# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
for r in rows:
    if r["원보험사코드"] == "KR0005" and r["공시분기"] == "2026.2Q" and 1 <= r["항목번호"] <= 54:
        print(r["항목번호"], r["항목명"], "값=", r.get("값"), "값_적용후=", r.get("값_적용후"))
