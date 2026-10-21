import json
for f in ["IFRS17_BS.json", "insurance_liability_portfolio.json"]:
    d = json.load(open(f, encoding="utf-8"))
    print(f, len(d), list(d[0].keys()) if isinstance(d, list) else list(d.keys())[:6])
    rows = [r for r in d if isinstance(r, dict) and any(str(v) == "교보생명보험" for v in r.values())] if isinstance(d, list) else []
    print(len(rows))
    seen = set()
    for r in rows:
        k = (r.get("항목번호"), r.get("항목명") or r.get("항목"))
        seen.add(k)
    print(sorted(seen, key=str)[:30])
    for r in rows:
        if r.get("공시분기") in ("2023.4Q",) : print(r)
