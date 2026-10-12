import re
p = "lib_kics.py"
s = open(p, encoding="utf-8").read()
s = s.replace('''    if "지급여력기준금액" not in flat or "기본요구자본" not in flat:
        return None''', '''    if "지급여력기준금액" not in flat or "기본요구자본" not in flat or "분산효과" not in flat or "건전성감독기준" not in flat:
        return None
    phase = "single"
    m = re.search(r"경과조치적용(전|후)지급여력비율", flat)
    if m: phase = "pre" if m.group(1) == "전" else "post"''')
s = s.replace('return {"rows": allrows, "heads": heads, "title": title, "page": pno}', 'return {"rows": allrows, "heads": heads, "title": title, "page": pno, "phase": phase}')
open(p, "w", encoding="utf-8", newline="\n").write(s)
p = "a4b_pages.py"
s = open(p, encoding="utf-8").read()
s = s.replace('hp.append((p, pg["title"][:70], [h[1] for h in pg["heads"]]))', 'hp.append((p, pg["phase"], [h[1] for h in pg["heads"]]))')
s = s.replace("out.write(f\"       p{h[0]} {h[1]!r} heads={h[2]}\n\")", "out.write(f\"       p{h[0]} phase={h[1]} heads={h[2]}\n\")")
open(p, "w", encoding="utf-8", newline="\n").write(s)
