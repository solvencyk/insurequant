# -*- coding: utf-8 -*-
"""v07: column/period + value comparison for every cite read in v06. Read-only."""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
import xmlrd

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
HERE = ROOT + "data/_derived/remaining_20261022/e21_ready25/verify/"
cites = json.load(open(HERE + "v06_cites.json", encoding="utf-8"))
MK = re.compile(r"전분기|전반기|전3분기|\(전\)|전기|당분기|당반기|당3분기|\(당\)|당기")


def grid(row):
    g = []
    c0 = 0
    for c in row["cells"]:
        g.append((c0, c0 + c["span"] - 1, c))
        c0 += c["span"]
    return g


def total(row):
    return sum(c["span"] for c in row["cells"])


def hdr_chain(t, row, cell):
    """header texts (top->bottom) above `row` covering the grid column of `cell`; right-aligned for rowspan-shifted rows."""
    g = None
    for a, b, c in grid(row):
        if c is cell:
            g = a
    dt = total(row)
    res = []
    for r in t["rows"]:
        if r is row:
            break
        if any(re.search(r"\d,\d{3}", c["t"]) for c in r["cells"]):
            continue
        off = dt - total(r)
        txt = [c["t"] for a, b, c in grid(r) if a + off <= g <= b + off and c["t"]]
        if txt:
            res.append(txt[0])
    return res


recs = []
for c in cites:
    doc = xmlrd.get(ROOT + c["file"])
    ti, t, row, cell = xmlrd.row_at_line(doc, c["line"])
    chain = hdr_chain(t, row, cell)
    htxt = " | ".join(chain)
    nums_in_chain = [int(x) for x in re.findall(r"제\s*(\d+)\s*기", htxt)]
    # all period numbers in table header rows
    allp = []
    for r in t["rows"]:
        if r is row:
            break
        for cc in r["cells"]:
            allp += [int(x) for x in re.findall(r"제\s*(\d+)\s*기", cc["t"])]
    prior_col = bool(re.search(r"전기|전분기|전반기|전년", htxt)) or (bool(nums_in_chain) and bool(allp) and min(nums_in_chain) < max(allp))
    # marker before table (for note tables without period columns)
    marker = None
    if not prior_col:
        for win in (3000, 20000):
            seg = xmlrd.strip(doc.text[max(0, t["pos"] - win):t["pos"]])
            ms = list(MK.finditer(seg))
            if ms:
                marker = seg[max(0, ms[-1].start() - 4):ms[-1].end() + 8]
                break
    prior_marker = bool(marker and re.search(r"전", marker[:marker.find(ms[-1].group(0)) + len(ms[-1].group(0))][-6:]))
    cum_col = bool(re.search(r"누적|누계", htxt))
    unit = xmlrd.unit_div(c["unit"])
    val = xmlrd.parse_num(cell["t"])
    c2 = dict(c)
    c2.update({"chain": chain, "prior_col": prior_col, "marker": marker, "prior_marker": prior_marker, "cum_col": cum_col,
               "val_mn": (val / unit) if (val is not None and unit) else None})
    recs.append(c2)
json.dump(recs, open(HERE + "v07_cites.json", "w", encoding="utf-8"), ensure_ascii=False)
np = [c for c in recs if not (c["prior_col"] or c["prior_marker"])]
print("cites", len(recs), "neither prior-col nor prior-marker:", len(np))
for c in np[:60]:
    print(c["key"], c["cite_label"][:20], c["line"], "|".join(c["chain"])[:140], "|", c["marker"], "|", c["printed"])
ncum = [c for c in recs if not c["cum_col"] and (c["prior_col"])]
print("prior-col but no explicit 누적:", len(ncum))
cc = collections.Counter(" | ".join(c["chain"]) for c in ncum)
for k, v in cc.most_common(15): print(v, k[:200])
