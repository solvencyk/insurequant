"""Dump 1-28 (값 / 값_적용후) for the 5 SANDWICHED (company, quarter) + KR0071 2023.1Q."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

TARGETS = [
    ("KR0050", "2023.2Q"),
    ("KR0097", "2023.2Q"),
    ("KR1011", "2023.2Q"),
    ("KR0049", "2024.3Q"),
    ("KR0100", "2024.3Q"),
    ("KR0071", "2023.1Q"),
]

for code, q in TARGETS:
    sub = [r for r in rows if r["원보험사코드"] == code and r["공시분기"] == q]
    sub.sort(key=lambda r: r["항목번호"])
    name = sub[0]["원수사명"] if sub else "?"
    print(f"\n===== {code} {name} {q}  (rows={len(sub)}) =====")
    for r in sub:
        if r["항목번호"] > 28:
            continue
        after = r.get("값_적용후")
        mark = "   <<< MISSING" if after in (None, "") else ""
        print(f"  {r['항목번호']:>2} {r['항목명'][:34]:<34} 전={r.get('값')!s:>12}  후={after!s:>12}{mark}")
    extra = [r for r in sub if r["항목번호"] > 28]
    if extra:
        print(f"  (items>28: {sorted(set(r['항목번호'] for r in extra))})")
