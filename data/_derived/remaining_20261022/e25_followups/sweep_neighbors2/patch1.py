import re
p = "b01_stmt.py"
s = open(p, encoding="utf-8").read()
s = s.replace('R.Stmt.pick_cell = pick_cell\n', '''R.Stmt.pick_cell = pick_cell
_orig_norm = R.norm
def norm2(label):
    s = (label or "").replace("\u3000", "").replace(" ", "").replace("\xa0", "")
    s = re.sub(r"^[XIVⅠ-ↈ]+\.", "", s)   # mixed ASCII/roman numerals such as 'XⅡ.'
    return _orig_norm(s)
R.norm = norm2
''', 1)
s = s.replace('if c == "KR0032" and q != "2024.4Q": continue', 'if c == "KR0032" and q != "2024.4Q": continue  # other KR0032 quarters are read by sweep 1')
open(p, "w", encoding="utf-8").write(s)
