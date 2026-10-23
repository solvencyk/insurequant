import sys, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as E
code, fy = sys.argv[1], sys.argv[2]
pat = sys.argv[3] if len(sys.argv) > 3 else "보험계약마진"
import e21_t2 as T
path = T.main_path(code, fy)
lines, s0, tabs = E.tables_sep(path)
print(path, "sep start", s0, "tables", len(tabs))
for t, rows in tabs:
    labs = [E.lab(r) for r in rows]
    if not any(re.search(pat, x) for x in labs): continue
    cap = E.nl(t["caption"] or "")[:60]
    hdr = E.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))[:90]
    nr = len(rows)
    print(f"--- table@L{t['start']} rows={nr} cap={cap!r} hdr={hdr!r}")
    for r in rows[:int(sys.argv[4]) if len(sys.argv) > 4 else 14]:
        nums = [(c["text"]) for c in r["cells"][1:]]
        print("   ", E.lab(r)[:40], nums[:8])
