# -*- coding: utf-8 -*-
"""v15: CSM cells with single-cell cites (Lotte, Hanwha): independent re-read of cited cell, header/marker, basis, unit, value vs master."""
import csv, json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
HERE = R + "data/_derived/remaining_20261022/e21_ready25/verify/"
rows = list(csv.DictReader(open(R + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_csm_cells.csv", encoding="utf-8-sig")))
master = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.load(open(R + "CSM_waterfall.json", encoding="utf-8"))}
head = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.load(open(HERE + "head/CSM_waterfall.json", encoding="utf-8"))}
MK = re.compile(r"전분기|전반기|전3분기|\(전\)|전기|당분기|당반기|당3분기|\(당\)|당기")
import glob, os

def resolve(code, quarter, later):
    # later like FY2025_Q1/20250515002628.xml  -> find file
    m = re.match(r"(FY\d{4}_Q\d)/(.+\.xml)$", later)
    if m:
        fy, fn = m.groups()
        c = glob.glob(R + f"data/dart/{fy}/raw/{code}*/{fn}") + glob.glob(R + f"data/dart/{fy}/raw/{code}*/xml/{fn}")
        return c[0] if c else None
    m = re.search(r"(data/dart/.+\.xml)$", later)
    return R + m.group(1) if m else None

def basis(doc, t):
    for pos, ln, txt in reversed([x for x in doc.titles if x[0] < t["pos"]]):
        if "재무제표" in txt and "요약" not in txt:
            return txt
    return None

def marker(doc, t):
    for win in (3000, 20000):
        seg = xmlrd.strip(doc.text[max(0, t["pos"] - win):t["pos"]])
        ms = list(MK.finditer(seg))
        if ms:
            return seg[max(0, ms[-1].start() - 6):ms[-1].end() + 6]
    return None

res = []
for r in rows:
    c, q, it = r["code"], r["quarter"], int(r["item"])
    if c not in ("KR0003", "KR0068"):
        continue
    f = resolve(c, q, r["later_filing"])
    cite = r["cite(label|line|text)"]
    mm = re.match(r"^(.*?)\|L(\d+)\|(.*)$", cite)
    lab, ln, txt = mm.group(1), int(mm.group(2)), mm.group(3).strip()
    doc = xmlrd.get(f)
    ti, t, row, cell = xmlrd.row_at_line(doc, ln)
    v = xmlrd.parse_num(cell["t"])
    unit = xmlrd.unit_div(doc.unit_before(t))
    eok = None if v is None or unit is None else v / unit / 100.0
    m = master[(c, q, str(it) if False else it)]
    ok_val = eok is not None and abs(abs(eok) - abs(m)) <= 0.051 + 1e-9
    sign_ok = eok is not None and (eok >= 0) == (m >= 0)
    # open/close: positive; adj/amort negative in master
    res.append({"key": (c, q, it), "file": f.split("/")[-1], "table": t["start"], "row_label": row["cells"][0]["t"], "printed": cell["t"], "unit": doc.unit_before(t),
                "eok": eok, "master": m, "head": head.get((c, q, it)), "val_ok": ok_val, "sign_ok": sign_ok, "section": basis(doc, t), "marker": marker(doc, t), "label_cited": lab})
bad = [x for x in res if not (x["val_ok"] and x["sign_ok"]) or "연결" in (x["section"] or "")]
print("single-cell CSM cites read:", len(res), "problems:", len(bad))
for x in res:
    print(x["key"], x["file"], "T%s" % x["table"], "|", x["row_label"][:28], "|", x["printed"], x["unit"], "->", None if x["eok"] is None else round(x["eok"], 3), "master", x["master"], "head", x["head"],
          "|", (x["section"] or "")[:12], "|", (x["marker"] or "")[:20], "" if (x["val_ok"] and x["sign_ok"]) else "  <== PROBLEM")
