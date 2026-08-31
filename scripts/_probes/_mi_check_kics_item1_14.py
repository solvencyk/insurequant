import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8"))
for item_no in (1, 14, 27):
    rows = [r for r in d if r["원보험사코드"] == "KR0001" and r["항목번호"] == item_no and r["공시분기"] in ("2026.1Q", "2026.2Q")]
    for r in rows:
        print(item_no, r["항목명"], r["공시분기"], r["값"], "적용후=", r.get("값_적용후"))
