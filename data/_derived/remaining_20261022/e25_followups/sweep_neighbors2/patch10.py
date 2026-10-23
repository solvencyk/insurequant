s = open("b04_life_is.py", encoding="utf-8").read()
old = """    if cal:
        for k, v in pri.items():"""
new = """    for k, v in pri.items():
        if pl.get((c, k, mq)) is not None and abs(cur[k] - pl.get((c, k, mq))) <= 1.5:"""
assert old in s
s = s.replace(old, new)
open("b04_life_is.py", "w", encoding="utf-8").write(s)
