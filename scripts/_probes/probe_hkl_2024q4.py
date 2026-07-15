import json, io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent.parent
data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
for r in data:
    if r["원보험사코드"] == "KR0071" and r["공시분기"] == "2024.4Q" and 1 <= r["항목번호"] <= 28:
        print(r["항목번호"], r.get("항목명"), "값=", r.get("값"), "값_적용후=", r.get("값_적용후", "<absent>"))
