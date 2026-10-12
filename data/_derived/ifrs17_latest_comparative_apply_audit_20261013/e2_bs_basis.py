import sys, os, csv, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e1_bs.py"), encoding="utf-8").read().split("out = open(here")[0])
out = open(here + "/e2_bs_basis.txt", "w", encoding="utf-8")
groups = {}
for c in cells:
    m = re.search(r"rcept (\d+) \((FY\d{4}_Q\d)\)", c["source_ref"])
    groups.setdefault((c["code"], c["quarter"], m.group(1), m.group(2)), []).append(c)
for (code, q, rc, fyq), cs in sorted(groups.items()):
    p = find_xml(code, fyq, rc)[0]
    tabs = [t for t in load_tables(p) if is_bs(t)]
    out.write(f"===== {code} {q} {fyq}: {len(tabs)} BS-like tables\n")
    for t in tabs:
        rows = stmt_rows(t)
        v1 = bs_vec(rows, 1); v2 = bs_vec(rows, 2)
        out.write(f"   table {t['idx']} line {t['line']} cap={t['caption'][:70]!r} 자산총계={v1[:2] if v1 else None} 부채총계={v2[:2] if v2 else None}\n")
    for c in cs[:1]:
        pass
