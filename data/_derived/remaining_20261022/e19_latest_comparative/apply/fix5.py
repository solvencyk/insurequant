from pathlib import Path
p = Path("e19_verify_plans.py")
s = p.read_text(encoding="utf-8")
bs = chr(92)
s = s.replace(chr(8), bs + "b")
s = s.replace("PFY" + bs + bs + "d{4}", "PFY" + bs + "d{4}")
p.write_text(s, encoding="utf-8", newline="\n")
for l in s.split("\n"):
    if "TE_INLINE =" in l or "re.match" in l:
        print(l)
