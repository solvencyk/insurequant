s = open("n00_lib.py", encoding="utf-8").read()
old = """            reg = None
            for p, rg in PFX:
                if lab.startswith(p):
                    reg = rg
                    break
            reg = reg or region"""
new = """            reg = None
            for p, rg in PFX:
                if lab.startswith(p):
                    reg = rg
                    region = rg          # a labelled section row (even with totals) opens its section
                    break
            reg = reg or region"""
assert old in s
open("n00_lib.py", "w", encoding="utf-8").write(s.replace(old, new))
