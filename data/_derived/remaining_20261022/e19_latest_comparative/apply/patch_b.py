from pathlib import Path
p = Path("e19_diff_vs_head.py")
s = p.read_text(encoding="utf-8")
s = s.replace('''    return open(f"{ROOT}/{rel}", "rb").read()''', '''    return open(f"{ROOT}/{rel}", "rb").read().replace(b"\r\n", b"\n")   # working tree is CRLF (core.autocrlf=true), git blobs are LF''')
s = s.replace('''chk("provenance: every changed PL cell belongs to a replaced (company, quarter) block", all((k[0], k[2]) in cover for k in set(chg_val) | set(chg_dangi)))''',
 '''chk("provenance: every cell whose 값 changed belongs to a replaced (company, quarter) block", all((k[0], k[2]) in cover for k in set(chg_val)))
nocover = sorted(k for k in set(chg_dangi) - set(chg_val) if (k[0], k[2]) not in cover)
out.append(f"   dangi-only cells in quarters without a changed provenance block (the sidecar records sources, not 값_당분기): {len(nocover)}")''')
p.write_text(s, encoding="utf-8", newline="\n")
