"""c1: list CSM roll-forward-like tables of a filing (READ-ONLY).
usage: c1_csm_tables.py <code> <FY_Q> [<maxrows>]
A table qualifies when it has a row label starting with 기초 and one starting with 기말/기초 ... and the table text (caption/labels) mentions 보험계약마진."""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
maxrows = int(sys.argv[3]) if len(sys.argv) > 3 else 30
out = []
for path in M.main_xmls(code, fy):
    if path.name.endswith("_00761.xml"):
        continue
    lines = M.read_lines(path)
    out.append(f"##### {M.rel(path)} lines={len(lines)}")
    for t in M.iter_tables(lines):
        labels = [M.norm_label(r["cells"][0]["text"]) for r in t["rows"] if r["cells"]]
        blob = " ".join(labels) + " " + t["caption"] + " " + t["title"]
        has_open = any(l.startswith("기초") or l.startswith("전기초") or l.startswith("당기초") for l in labels)
        has_close = any(l.startswith("기말") for l in labels)
        if "보험계약마진" in blob and has_open and has_close:
            out.append(f"--- TABLE L{t['start']}-L{t['end']} title[{t['title_line']}]={t['title'][:40]!r} caption[{t['caption_line']}]={t['caption'][:70]!r} nrows={len(t['rows'])}")
            for r in t["rows"][:maxrows]:
                vs = [c["text"] for c in r["cells"]]
                out.append(f"    R{r['tr_line']}: " + " | ".join(v[:28] for v in vs[:9]))
txt = "\n".join(out)
M.MEASURE.joinpath(f"c1_csm_tables_{code}_{fy}.txt").write_text(txt, encoding="utf-8")
print(txt.count("--- TABLE"), "tables ->", f"c1_csm_tables_{code}_{fy}.txt")
