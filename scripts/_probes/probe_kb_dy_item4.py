import json, io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent.parent
data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
by_cq = {}
for r in data:
    by_cq.setdefault((r["원수사명"], r["공시분기"]), {})[r["항목번호"]] = r
for name, q in [("KB라이프생명", "2024.2Q"), ("동양생명", "2024.1Q")]:
    items = by_cq[(name, q)]
    r4 = items.get(4)
    print(name, q, "item4 값=", r4.get("값"), "값_적용후=", r4.get("값_적용후"))
