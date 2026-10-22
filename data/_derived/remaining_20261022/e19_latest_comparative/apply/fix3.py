from pathlib import Path
p = Path("e19_verify_plans.py")
s = p.read_text(encoding="utf-8")
s = s.replace("<TE\x08([^>]*)>", "<TE\b([^>]*)>")
s = s.replace('re.match(r"PFY\d{4}', 're.match(r"PFY\d{4}')
p.write_text(s, encoding="utf-8", newline="\n")
print(s.count("\x08"), [l for l in s.split("\n") if "PFY" in l and "match" in l])
