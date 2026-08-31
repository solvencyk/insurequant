# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
print("total rows now:", len(rows))
for code in ("KR0011", "KR0029", "KR0094", "KR0004"):
    matches = [r for r in rows if r["원보험사코드"] == code and r["공시분기"] == "2026.2Q"]
    print(code, "2026.2Q rows:", len(matches))
    if matches:
        print("   sample:", matches[0])
    any_rows = [r for r in rows if r["원보험사코드"] == code]
    print(code, "total rows any quarter:", len(any_rows))
