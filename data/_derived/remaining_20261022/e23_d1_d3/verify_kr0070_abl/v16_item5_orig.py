import re, glob
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
for q, pat in (("2023.1Q", "FY2023_Q1/raw/KR0070_*/xml/20230515002903.xml"), ("2023.2Q", "FY2023_Q2/raw/KR0070_*/xml/20230814002908.xml"), ("2023.3Q", "FY2023_Q3/raw/KR0070_*/xml/20231114002934.xml"), ("2023.4Q", "FY2023_Q4/raw/KR0070_*/xml/20240329001518.xml")):
    f = glob.glob(ROOT + "/data/dart/" + pat)[0]
    lines = open(f, encoding="utf-8", errors="replace").read().split("\n")
    out = []
    for i, ln in enumerate(lines, 1):
        s = re.sub(r"<[^>]*>", "", ln).strip()
        if s in ("위험조정변동", "위험조정 변동"):
            vals = []
            for j in range(i, i + 40):
                t = re.sub(r"<[^>]*>", "", lines[j]).strip()
                if t: vals.append(t)
                if len(vals) >= 5: break
            out.append((i, vals))
    print(q, out[:4])
