import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
g = json.load(open("p2_generic.json", encoding="utf-8")); s1 = json.load(open("p1_stmt.json", encoding="utf-8"))
def clean(l): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", l)).strip()
def show(path, ln, w=0, back=0):
    L = open(ROOT + path, encoding="utf-8").read().split("\n")
    # label: scan back to the TR start
    k = ln - 1
    while k > 0 and not L[k].lstrip().startswith("<TR"): k -= 1
    row = []
    j = k
    while j < len(L) and not L[j].lstrip().startswith("</TR"):
        c = clean(L[j]);
        if c: row.append(f"L{j+1}:{c}")
        j += 1
    print(path.split("/")[-1], f"cited L{ln}", " | ".join(row)[:330])
chk = [("KR0087|2024.4Q", "4", 121698), ("KR0087|2024.4Q", "10", 122195), ("KR0068|2023.1Q", "5", 77315), ("KR0070|2024.1Q", "9", 43146), ("KR0070|2024.1Q", "10", 43140),
       ("KR0070|2025.1Q", "5", 38248), ("KR0070|2025.1Q", "10", 43235), ("KR0072|2024.4Q", "5", 21721), ("KR0009|2023.1Q", "5", 43909), ("KR0104|2025.1Q", "4", None)]
for k, it, ln in chk:
    f = g[k]["file"]
    if ln is None:
        x = g[k]["prior"][it][0]; ln = x["line"]
    print("==", k, "item", it)
    show(f, ln)
for k, it, ln in [("KR0072|2024.4Q", "17", 4859), ("KR0082|2023.1Q", "25", 24260)]:
    print("==", k, "item", it); show(s1[k]["file"], ln)
