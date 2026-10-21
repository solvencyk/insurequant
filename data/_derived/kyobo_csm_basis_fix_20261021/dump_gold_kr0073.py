"""Read-only: list KR0073 entries in data/_gold/user_csm_cells.json `set` with full why text."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
with open(ROOT / "data/_gold/user_csm_cells.json", "r", encoding="utf-8") as f:
    gold = json.load(f)
sets = gold["set"]
print("total set entries:", len(sets))
kr = [(i, e) for i, e in enumerate(sets) if e.get("원보험사코드") == "KR0073"]
print("KR0073 entries:", len(kr))
keys = set()
for i, e in kr:
    keys.update(e.keys())
print("keys:", sorted(keys))
for i, e in kr:
    print(f"--- set[{i}] q={e.get('공시분기')} item={e.get('항목번호')} 값={e.get('값')} 값_당분기={e.get('값_당분기')} was={e.get('was')!r}")
    for k, v in e.items():
        if k in ("원보험사코드", "항목번호", "공시분기", "값", "was"):
            continue
        print(f"    {k}: {v}")
