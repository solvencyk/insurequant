p = "n01_notes.py"
s = open(p, encoding="utf-8").read()
old = """    nums = []
    for c in cells[k:]:
        if isnum(c):
            nums.append((0.0 if c["val"] is None else c["val"], c["line"], c["text"]))
    return E.nl("".join(labs)), nums"""
new = """    nums = []
    rest = cells[k:]
    while rest and not isnum(rest[-1]):
        rest = rest[:-1]
    for c in rest:
        if isnum(c):
            nums.append((0.0 if c["val"] is None else c["val"], c["line"], c["text"]))
        elif c["text"].strip() == "":
            nums.append((0.0, c["line"], ""))      # empty printed cell inside the numeric block keeps the column index aligned
    return E.nl("".join(labs)), nums"""
assert old in s
open(p, "w", encoding="utf-8").write(s.replace(old, new))
