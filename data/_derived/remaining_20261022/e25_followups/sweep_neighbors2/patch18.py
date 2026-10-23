s = open("x05_kr0079.py", encoding="utf-8").read()
old = '''                                  source="custom_kr0079b", confidence="high",
                                  note=f"sum of all 25 columns of the row; current table@L{vv[ok_idx[0]][3]} reproduces master {mq} = {m_cur}"))'''
new = '''                                  source="custom_kr0079b", confidence=("high" if it == "4" else "low"),
                                  note=f"sum of all 25 columns of the row; current table@L{vv[ok_idx[0]][3]} reproduces master {mq} = {m_cur}" + ("" if it == "4" else "; LOW: the same one-row RA definition fails calibration for 2025.4Q (reader 37,616 vs master 43,953), so a second RA row may exist")))'''
assert old in s
open("x05_kr0079.py", "w", encoding="utf-8").write(s.replace(old, new))
p = open("p20_compile.py", encoding="utf-8").read()
p = p.replace('"b04_life_is.json", "x04_kr0087.json")', '"b04_life_is.json", "x05_kr0079.json")')
open("p20_compile.py", "w", encoding="utf-8").write(p)
