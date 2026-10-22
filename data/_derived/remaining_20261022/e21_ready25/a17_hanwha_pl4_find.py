"""a17_hanwha_pl4_find: locate the printed cells equal to a target PL4 value (mn) inside the notes of a later filing (own reader mlib); READ-ONLY.  usage: a17 CODE FY_Q target [target ...]"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_t2 as T
sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
targets = [float(x) for x in sys.argv[3:]]
M = T.M
path = T.main_path(code, fy)
lines = M.read_lines(path)
s0 = T.sep_notes_from(lines)
print(path, "sep notes from", s0)
for t in M.iter_tables(lines):
    unit = None
    for r in t["rows"]:
        for k, c in enumerate(r["cells"]):
            if c["val"] is None:
                continue
            for tg in targets:
                if abs(abs(c["val"]) - tg) < 0.5 or abs(abs(c["val"]) - tg * 1e6) < 0.5 * 1e6 * 1e-6 + 0.5 or abs(abs(c["val"]) - tg * 1e3) < 0.5:
                    lab = " | ".join(x["text"] for x in r["cells"][:3])
                    print(f"  target {tg}: table@L{t['start']} (sep={t['start'] >= s0}) cap={t['caption'][:50]!r} row L{r['tr_line']} label={lab[:90]!r} cell#{k} L{c['line']} text={c['text']}")
