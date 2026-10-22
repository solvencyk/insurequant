from pathlib import Path
p = Path("e19_verify_plans.py")
s = p.read_text(encoding="utf-8")
a = s.index("                    # contribution_mn already signed")
b = s.index("                    computed = t2")
new = '''                    t2 = 0.0
                    for e in lst:
                        v = parse_num(cell_at(rel, e["line"]))
                        pv = parse_num(e["printed"])
                        if v is None or pv is None:
                            t2 = None
                            break
                        sg = 1 if (e["contribution_mn"] * pv) >= 0 else -1
                        t2 += sg * v / scale
'''
s = s[:a] + new + s[b:]
p.write_text(s, encoding="utf-8", newline="\n")
