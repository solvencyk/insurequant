# -*- coding: utf-8 -*-
"""Check existing item47/48/49/50/51 rows (other companies) for value precision convention,
and dump KR0005 2024Q4 item1/item2/item3/item14 for anchor cross-check."""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\kr0005_tfi")

d = json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8"))

# 1) any existing item 47/48/49/50/51 rows anywhere (precision convention check)
targets = {47, 48, 49, 50, 51}
existing = [r for r in d if r.get("항목번호") in targets]
print("existing item47/48/49/50/51 rows count:", len(existing))
for r in existing[:20]:
    print(r.get("원수사명"), r.get("공시분기"), r.get("항목번호"), r.get("항목명"), r.get("값"), r.get("값_적용후"))

# 2) KR0005 2024Q4 anchors: item1,2,3,14
kr5 = [r for r in d if r.get("원보험사코드") == "KR0005" and r.get("공시분기") in ("2024.4Q", "2024_4Q", "2024Q4", "FY2024_Q4")]
print("\nKR0005 rows matching quarter-guess count:", len(kr5))
# broader: just KR0005 all quarters, show distinct 공시분기 values
kr5_all = [r for r in d if r.get("원보험사코드") == "KR0005"]
quarters = sorted(set(r.get("공시분기") for r in kr5_all))
print("KR0005 distinct 공시분기 values:", quarters)

(OUT / "master_check.json").write_text(
    json.dumps({"existing_47_51": existing, "kr0005_quarters": quarters}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("wrote", OUT / "master_check.json")
