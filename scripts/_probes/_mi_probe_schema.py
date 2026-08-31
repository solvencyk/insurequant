import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("IFRS17_BS.json", encoding="utf-8") as f:
    d = json.load(f)

print("type", type(d), "len", len(d) if isinstance(d, list) else None)
row = d[0]
print("keys in order:", list(row.keys()))
print(json.dumps(row, ensure_ascii=False, indent=2))
# a row with 값_적용후 if any, and check for 섹션/레벨 usage variety
sections = set()
levels = set()
for r in d[:2000]:
    sections.add(r.get("섹션"))
    levels.add(r.get("레벨"))
print("sample sections:", sections)
print("sample levels:", levels)
