"""n1: list tables of a filing whose caption/title/first-column labels match all given substrings; print captions, headers and chosen rows
usage: n1_find_tables.py <code> <FY_Q> <cap_substr[,cap_substr]> [row_label_substr[,..]] [maxtables]
READ-ONLY.  Output also written to n1_<code>_<fy>.txt"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
import stmtlib as S

sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
caps = [c for c in sys.argv[3].split(",") if c]
rowsubs = [c for c in (sys.argv[4].split(",") if len(sys.argv) > 4 else []) if c]
maxt = int(sys.argv[5]) if len(sys.argv) > 5 else 40
out = []
for path in M.main_xmls(code, fy):
    if path.name.endswith("_00761.xml"):
        continue
    lines = M.read_lines(path)
    s, e = S.sep_section(lines)
    ss, ee = None, None
    # note section of the separate basis: from '5. 재무제표 주석' TITLE on
    for ln, t in S.titles(lines):
        import re
        if re.match(r"^\d+\.재무제표주석$", re.sub(r"\s+", "", t)):
            ss = ln
    out.append(f"##### {M.rel(path)} lines={len(lines)} sep_stmt=({s},{e}) sep_notes_from={ss}")
    n = 0
    for t in M.iter_tables(lines):
        blob = t["caption"] + " " + t["title"]
        labels = [M.norm_label(r["cells"][0]["text"]) for r in t["rows"] if r["cells"]]
        full = blob + " " + " ".join(labels) + " " + " ".join(c["text"] for r in t["rows"][:3] for c in r["cells"])
        if all(c in full for c in caps):
            basis = "SEP" if (ss and t["start"] >= ss) or (s <= t["start"] <= e) else "CONS?"
            out.append(f"--- {basis} TABLE L{t['start']}-L{t['end']} caption[{t['caption_line']}]={t['caption'][:80]!r} nrows={len(t['rows'])}")
            for r in t["rows"][:3]:
                out.append("      HDR R%d: " % r["tr_line"] + " | ".join(c["text"][:22] for c in r["cells"][:12]))
            for r in t["rows"]:
                lab = M.norm_label(r["cells"][0]["text"]) if r["cells"] else ""
                if rowsubs and any(x in lab for x in rowsubs):
                    out.append("      R%d: " % r["tr_line"] + " | ".join(c["text"][:20] + f"@{c['line']}" for c in r["cells"][:14]))
            n += 1
            if n >= maxt:
                break
txt = "\n".join(out)
M.MEASURE.joinpath(f"n1_{code}_{fy}.txt").write_text(txt, encoding="utf-8")
print(txt[:12000])
