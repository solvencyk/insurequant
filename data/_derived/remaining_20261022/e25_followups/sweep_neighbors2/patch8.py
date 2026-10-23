s = open("n00_lib.py", encoding="utf-8").read()
old = """            reg = None
            for p, rg in PFX:
                if lab.startswith(p):"""
new = """            reg = None
            labp = re.sub(r"^((\(\d+\))|(\d+[\.\)])|([가-하]\.))+", "", lab)
            for p, rg in PFX:
                if labp.startswith(p):"""
assert old in s
s = s.replace(old, new)
old2 = """            if not nums:
                for p, reg in PFX:
                    if lab == p:
                        region = reg
                continue"""
new2 = """            if not nums:
                labp0 = re.sub(r"^((\(\d+\))|(\d+[\.\)])|([가-하]\.))+", "", lab)
                for p, reg in PFX:
                    if labp0 == p:
                        region = reg
                continue"""
assert old2 in s
s = s.replace(old2, new2)
open("n00_lib.py", "w", encoding="utf-8").write(s)
