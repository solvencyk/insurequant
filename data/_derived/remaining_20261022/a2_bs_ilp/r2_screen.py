"""IFRS17.html Panel 1 on-screen strings (fmtEokKR on value/100) and 억원 values, before (git HEAD) vs after."""
import json, subprocess, sys, math
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
head = json.loads(subprocess.run(["git", "show", "HEAD:IFRS17_BS.json"], cwd=R, capture_output=True, check=True).stdout.decode("utf-8"))
cur = json.load(open(R + "IFRS17_BS.json", encoding="utf-8"))
def fmt(eok):
    neg = eok < 0; v = math.floor(abs(eok) + 0.5); jo, rem = divmod(v, 10000)
    s = (f"{jo:,}조" + (f" {rem:,}억원" if rem > 0 else "")) if jo > 0 else f"{v:,}억원"
    return ("△" if neg else "") + s
get = lambda bs, it, q: next(r["값"] for r in bs if r["원보험사코드"] == "KR0073" and r["항목번호"] == it and r["공시분기"] == q)
names = {1: "자산총계", 2: "부채총계", 3: "자본총계", 20: "보험계약부채", 31: "이익잉여금"}
for q, items in (("2023.4Q", (1, 2, 3, 20, 31)), ("2024.4Q", (1,))):
    for it in items:
        a, b = get(head, it, q) / 100, get(cur, it, q) / 100
        print(f"{q} item{it} {names[it]}: {a:,.2f}억 -> {b:,.2f}억 | screen {fmt(a)} -> {fmt(b)}")
