from pathlib import Path
p = Path("e19_verify_plans.py")
b = p.read_bytes()
b = b.replace(b"<TE\x08(", b"<TE\b(").replace(b"<TE(", b"<TE\b(")
b = b.replace(b'r"PFY\\d{4}d(TQA|HYA|FQA|FY)_"', b'r"PFY\d{4}d(TQA|HYA|FQA|FY)_"')
p.write_bytes(b)
for l in b.decode("utf-8").split("\n"):
    if "TE_INLINE =" in l or "re.match" in l:
        print(repr(l))
