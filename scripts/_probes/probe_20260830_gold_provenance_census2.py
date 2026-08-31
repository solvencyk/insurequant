import sys, json
sys.stdout.reconfigure(encoding="utf-8")

GOLD_PATH = "data/_gold/user_csm_cells.json"

d = json.load(open(GOLD_PATH, encoding="utf-8"))
s = d["set"]
print("total set entries:", len(s))

empty = []
for i, e in enumerate(s):
    why = (e.get("why") or "").strip()
    note = (e.get("note") or "").strip()
    if not why and not note:
        empty.append((i, e))

print("empty why/note total:", len(empty))
by_company = {}
for i, e in empty:
    by_company.setdefault(e.get("원보험사코드"), []).append((i, e))

for code in sorted(by_company, key=lambda x: (x is None, x)):
    print(f"{code}: {len(by_company[code])} empty")

print()
for code in ["KR0079", "KR0003", "KR0072"]:
    lst = by_company.get(code, [])
    print(f"\n########## {code} ({len(lst)} entries) ##########")
    for i, e in sorted(lst, key=lambda p: (p[1].get("공시분기",""), p[1].get("항목번호",0))):
        print(json.dumps({"idx": i, **e}, ensure_ascii=False))
