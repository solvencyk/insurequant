from pathlib import Path
p = Path("e19_verify_plans.py")
s = p.read_text(encoding="utf-8")
old = 'vals.append(parse_num(raw) if raw is not None else (0.0 if raw is not None and raw.strip() == "" else None))'
new = 'vals.append(0.0 if (raw is not None and raw.strip() == "") else (parse_num(raw) if raw is not None else None))'
assert s.count(old) == 1
s = s.replace(old, new)
p.write_text(s, encoding="utf-8", newline="\n")
