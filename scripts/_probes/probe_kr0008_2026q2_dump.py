import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

with open(ROOT / "kics_disclosure.json", encoding="utf-8") as f:
    data = json.load(f)

rows = [
    r for r in data
    if r.get("원보험사코드") == "KR0008" and r.get("공시분기") == "2026.2Q"
]
rows.sort(key=lambda r: r.get("항목번호", 0))

out = {
    "count": len(rows),
    "rows": rows,
}

with open(ROOT / "scripts" / "_probes" / "_out_kr0008_2026q2_rows.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("wrote", len(rows), "rows")

# also dump neighboring quarters for comparison (2026.1Q, 2025.4Q)
for q in ["2026.1Q", "2025.4Q", "2025.3Q"]:
    rows_q = [
        r for r in data
        if r.get("원보험사코드") == "KR0008" and r.get("공시분기") == q
    ]
    rows_q.sort(key=lambda r: r.get("항목번호", 0))
    with open(ROOT / "scripts" / "_probes" / f"_out_kr0008_{q.replace('.', '')}_rows.json", "w", encoding="utf-8") as f:
        json.dump({"count": len(rows_q), "rows": rows_q}, f, ensure_ascii=False, indent=2)
    print("wrote", q, len(rows_q), "rows")
