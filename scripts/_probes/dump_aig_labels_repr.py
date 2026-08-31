# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
with open(ROOT + r"\kics_disclosure.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

code = "KR0029"
targets = [28, 37, 38, 39, 40, 47, 49, 50, 51]
for q in ["2025.3Q", "2025.4Q", "2026.2Q"]:
    print(f"===== {q} =====")
    for r in rows:
        if r.get("원보험사코드") == code and r.get("공시분기") == q and int(r.get("항목번호", -1)) in targets:
            print(f"  item{r['항목번호']}: repr={r['항목명']!r}")
