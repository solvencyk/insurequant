import re, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
F24 = R + "data/dart/FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml"
L = open(F24, encoding="utf-8").read().split("\n")
# collect text cells with line numbers in 75082..75480
cells = []
for i in range(75081, 75480):
    t = re.sub(r"<[^>]+>", "", L[i]).strip()
    if t: cells.append((i + 1, t))
want = ("자산총계", "보험계약부채", "부채총계", "이익잉여금", "자본총계", "수정전", "수정후", "증감", "전기초", "전기말", "(단위")
for k, (ln, t) in enumerate(cells):
    if any(w in t for w in want) and t in ("자산총계", "　자산총계", "보험계약부채", "　　보험계약부채", "부채총계", "　부채총계", "이익잉여금", "　　이익잉여금", "자본총계", "　자본총계") or "전기초" in t or "전기말" in t or "단위" in t or t in ("수정전", "수정후", "증감"):
        print(ln, " | ".join(x[1] for x in cells[k:k+4]))
