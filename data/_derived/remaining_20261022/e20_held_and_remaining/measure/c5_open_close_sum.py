"""c5: sum the CSM opening/closing/amort/new/interest over given product tables of one period block; the CSM column = the numeric cell at position `col` (0-based among the cells AFTER the label).
usage: c5_open_close_sum.py <code> <FY_Q> <file_suffix> <col> <cur_starts> <prior_starts> [unit_div=100]   labels matched: opening ~ '기초' (first '기초순' / 'I.기초' / '기초 순장부금액'), closing ~ '기말순' etc. (READ-ONLY)"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
code, fy, suffix, col = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
blocks = {"cur": [int(x) for x in sys.argv[5].split(",")], "prior": [int(x) for x in sys.argv[6].split(",")]}
div = float(sys.argv[7]) if len(sys.argv) > 7 else 100.0
path = [p for p in M.main_xmls(code, fy) if p.name.endswith(suffix)][0]
lines = M.read_lines(path)
tabs = {t["start"]: t for t in M.iter_tables(lines)}
RULES = [("open", ("기초순보험계약부채", "기초순재보험", "I.기초", "기초순장부금액")), ("amort", ("보험계약마진상각", "서비스제공에따른보험계약마진")),
         ("new", ("최초인식계약", "신계약", "처음인식")), ("int", ("보험금융손익",)), ("close", ("기말순보험계약부채", "기말순재보험", "기말순장부금액"))]
for per, starts in blocks.items():
    tot, det = {}, {}
    for s in starts:
        t = tabs[s]
        seen = set()
        for r in t["rows"]:
            if not r["cells"]:
                continue
            lab = M.norm_label(r["cells"][0]["text"])
            cells = r["cells"][1:]
            if len(cells) <= col:
                continue
            for key, pats in RULES:
                if key in seen:
                    continue
                if any(lab.startswith(p) for p in pats):
                    v = cells[col]["val"] or 0.0
                    tot[key] = tot.get(key, 0.0) + v
                    det.setdefault(key, []).append((s, v, cells[col]["line"]))
                    seen.add(key)
    print(per, {k: round(v / div, 1) for k, v in tot.items()}, "(억원; 백만원/%g)" % div)
    for k in ("open", "close", "amort", "new", "int"):
        print("    ", k, [(a, f"{b:,.0f}", f"@L{c}") for a, b, c in det.get(k, [])])
