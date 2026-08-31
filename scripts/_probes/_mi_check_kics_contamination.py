import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "kics_disclosure.json", encoding="utf-8") as f:
    data = json.load(f)

codes = ["KR0011", "KR0029", "KR0150"]
for code in codes:
    print(f"=== {code} ===")
    rows = [r for r in data if r.get("원보험사코드") == code and r.get("항목번호") in (1, 14, 27)]
    by_q = {}
    for r in rows:
        by_q.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]
    for q in sorted(by_q):
        print(f"  {q}: {by_q[q]}")
