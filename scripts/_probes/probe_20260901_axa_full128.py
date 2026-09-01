import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
rows = json.loads(open("kics_disclosure.json", encoding="utf-8").read())
for q in ("2024.3Q","2024.4Q","2025.1Q"):
    print(f"=== 악사(KR0049) {q} items 1-28 ===")
    sub = [r for r in rows if r["원보험사코드"]=="KR0049" and r["공시분기"]==q]
    have = sorted({int(r["항목번호"]) for r in sub if str(r["항목번호"]).isdigit()})
    print("  items present:", have)
    for it in (15,16,17,18,19,20,21,22,23,24,25,26,27,28):
        r = next((r for r in sub if str(r["항목번호"])==str(it)), None)
        print(f"    item{it}: {r.get('값') if r else 'ABSENT'}")
