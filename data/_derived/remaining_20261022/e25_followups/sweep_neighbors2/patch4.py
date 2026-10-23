p = "c01_csm.py"
s = open(p, encoding="utf-8").read()
old = """            if "보험계약마진" in x:
                return k - 1 if k >= 1 else None   # numeric index among cells after the label cell"""
new = """            if "보험계약마진" in x:
                has_label = labs[0] in ("구분", "") if labs else False
                return (k - 1) if has_label else k   # numeric index among the numeric cells after the label cell"""
assert old in s
open(p, "w", encoding="utf-8").write(s.replace(old, new))
