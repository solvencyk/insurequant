# -*- coding: utf-8 -*-
"""v06: independently re-read every cite of every changed PL cell in the raw XML. Read-only."""
import csv, json, re, sys, collections, os
sys.stdout.reconfigure(encoding="utf-8")
import xmlrd

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
HERE = ROOT + "data/_derived/remaining_20261022/e21_ready25/verify/"
cells = json.load(open(HERE + "v01_PL_breakdown_cells.json", encoding="utf-8"))
chg = {}
for k, f, a, b in cells:
    if f == "값":
        chg[tuple(k)] = (a, b)
rows = list(csv.DictReader(open(ROOT + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv", encoding="utf-8-sig")))
csvidx = {}
for r in rows:
    if r["sheet"] == "PL":
        csvidx[(r["code"], r["quarter"], int(r["item"]))] = r

CITE = re.compile(r"([^|;]+?)\|L(\d+)\|([^;]*?)(?=\s*(?:;|$|\())")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def basis_of(doc, t):
    """nearest preceding section title that names a financial-statement section."""
    for pos, ln, txt in reversed([x for x in doc.titles if x[0] < t["pos"]]):
        if re.search(r"재무제표", txt) and not re.search(r"요약", txt):
            return txt, ("연결" if "연결" in txt else "별도")
    return None, None


def colinfo(doc, t, row, cell):
    """index of the numeric cell among the row's numeric cells + header chain texts."""
    nums = [c for c in row["cells"] if xmlrd.parse_num(c["t"]) is not None or c["t"] in ("-",)]
    idx = None
    for i, c in enumerate(row["cells"]):
        if c is cell:
            idx = i
    # compare by position among cells after the label cell
    ncell = len(row["cells"])
    # header rows: rows before the first row whose first cell equals row-labels of bodies; collect rows with no numeric cells
    hdr = []
    for r in t["rows"]:
        if r is row:
            break
        if not any(xmlrd.parse_num(c["t"]) is not None and len(c["t"]) > 3 and re.search(r"\d,\d", c["t"]) for c in r["cells"]):
            hdr.append([c["t"] for c in r["cells"]])
    return idx, ncell, hdr[-4:]


out = []
bad = []
sumry = collections.Counter()
doccache = {}
for k in sorted(chg):
    r = csvidx[k]
    cite = r["cite(label|line|text)"]
    flt = r["later_filing"]
    path = flt.split(" (")[0].strip()
    if not cite:
        sumry["nocite"] += 1
        continue
    path_abs = ROOT + path
    if not os.path.exists(path_abs):
        bad.append((k, "file missing", path))
        continue
    doc = xmlrd.get(path_abs)
    parts = []
    for seg in cite.split(" ; "):
        mm = re.match(r"^(.*?)\|L(\d+)\|(.*)$", seg.strip())
        if mm:
            tx = mm.group(3).strip()
            tx = re.split(r"\s+(?=[\(\[]?item|=>|\+)", tx)[0].strip()
            parts.append((mm.group(1).strip(), int(mm.group(2)), tx))
    for label, ln, txt in parts:
        res = xmlrd.row_at_line(doc, ln)
        rec = {"key": k, "file": path, "cite_label": label, "line": ln, "cite_text": txt}
        if res is None:
            rec["err"] = "line not in any table cell"
            bad.append((k, rec["err"], label, ln))
            out.append(rec)
            continue
        ti, t, row, cell = res
        rec["table_start"] = t["start"]
        rec["row_label"] = row["cells"][0]["t"] if row["cells"] else None
        rec["printed"] = cell["t"]
        rec["match_text"] = (norm(cell["t"]) == norm(txt)) or (norm(cell["t"]).replace("(", "-").replace(")", "") == norm(txt).replace("(", "-").replace(")", ""))
        rec["match_label"] = norm(rec["row_label"]) == norm(label) or norm(label) in norm(rec["row_label"]) or norm(rec["row_label"]) in norm(label)
        bt, b = basis_of(doc, t)
        rec["section"], rec["basis"] = bt, b
        rec["unit"] = doc.unit_before(t)
        idx, ncell, hdr = colinfo(doc, t, row, cell)
        rec["col_idx"], rec["ncell"] = idx, ncell
        rec["hdr"] = hdr
        rec["val"] = xmlrd.parse_num(cell["t"])
        out.append(rec)
        problems = []
        if not rec["match_text"]:
            problems.append("text mismatch")
        if not rec["match_label"]:
            problems.append("label mismatch")
        if b != "별도":
            problems.append("basis=%s" % b)
        if xmlrd.unit_div(rec["unit"]) is None:
            problems.append("unit=%s" % rec["unit"])
        if problems:
            bad.append((k, problems, rec))
json.dump(out, open(HERE + "v06_cites.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("cites read:", len(out), "problems:", len(bad), "cells without cite:", sumry["nocite"])
for b in bad[:60]:
    print(b)
