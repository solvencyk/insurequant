# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
with open(ROOT + r"\kics_disclosure.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

code = "KR0029"
quarters = ["2025.2Q", "2025.3Q", "2025.4Q", "2026.2Q"]

for q in quarters:
    print(f"===== {code} {q} =====")
    sub = [r for r in rows if r.get("원보험사코드") == code and r.get("공시분기") == q]
    sub.sort(key=lambda r: (int(r.get("항목번호", 0)) if str(r.get("항목번호","")).isdigit() else 999))
    print(f"  row count: {len(sub)}")
    for r in sub:
        item = r.get("항목번호")
        name = r.get("항목명")
        val = r.get("값")
        val_post = r.get("값_적용후", None)
        print(f"  [{item}] {name} = {val}  (적용후={val_post})")
    print()
