import io
p = "KR0005_s7_xml.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('put(1, pick(rows, r"Ⅰ\.보험손익"))', 'put(1, pick(rows, r"Ⅰ\.(보험손익|보험서비스결과)"))')
old = s[s.index("    for r in leaves:"):s.index("    for k, r in claimed.items():")]
new = '''    for r in leaves:
        l = r["lab"]
        if "신용손실" in l:
            rest.append(r); continue
        if "재보험계약자산" in l:
            claimed[30] = r
        elif "보험계약자산" in l:
            claimed[27] = r
        elif "공정가치측정금융자산" in l and ("평가손익" in l or "관련손익" in l):
            claimed[26] = r
        elif "현금흐름위험회피" in l:
            claimed[28] = r
        else:
            rest.append(r)
'''
s = s.replace(old, new)
s = s.replace(' ("orig", "2023.3Q", "FY2023_Q3", 1, 0),', ' ("later2", "2023.4Q", "FY2025_Q4", 2, None), ("later2", "2024.4Q", "FY2025_Q4", 1, None),\n ("orig", "2023.3Q", "FY2023_Q3", 1, 0),')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
