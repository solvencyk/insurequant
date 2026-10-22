"""Independent DART XML table reader for the e19 verification (own code, not parser code)."""
import re, glob, html, os

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
PER2DIR = {"2022.4Q": "FY2022_Q4"}
for y in (2023, 2024, 2025, 2026):
    for q in (1, 2, 3, 4):
        PER2DIR["%d.%dQ" % (y, q)] = "FY%d_Q%d" % (y, q)

TAG = re.compile(r"<[^>]+>")
TITLE_RE = re.compile(r"<TITLE[^>]*>(.*?)</TITLE>", re.S)
TABLE_RE = re.compile(r"<TABLE[^>]*>(.*?)</TABLE>", re.S)
TR_RE = re.compile(r"<TR[^>]*>(.*?)</TR>", re.S)
CELL_RE = re.compile(r"<(TD|TE|TU|TH)([^>]*)>(.*?)</\1>", re.S)


def clean(s):
    s = TAG.sub("", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def find_xml(code, per):
    d = ROOT + "/data/dart/" + PER2DIR[per] + "/raw/"
    cands = glob.glob(d + code + "_*")
    out = []
    for c in cands:
        out += glob.glob(c + "/*.xml") + glob.glob(c + "/xml/*.xml")
    return sorted(out)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def tables(text):
    """list of dict(title, line, rows[[cell,..]]) ; title = last TITLE before the table"""
    # title positions
    titles = [(m.start(), clean(m.group(1))) for m in TITLE_RE.finditer(text)]
    tp = [t[0] for t in titles]
    import bisect
    res = []
    for m in TABLE_RE.finditer(text):
        i = bisect.bisect_right(tp, m.start()) - 1
        title = titles[i][1] if i >= 0 else ""
        line = text.count("\n", 0, m.start()) + 1
        rows = []
        for tr in TR_RE.finditer(m.group(1)):
            cells = []
            for c in CELL_RE.finditer(tr.group(1)):
                attrs = c.group(2)
                cs = re.search(r'COLSPAN="(\d+)"', attrs)
                txt = clean(c.group(3))
                cells.append(txt)
                if cs and int(cs.group(1)) > 1:
                    cells += [""] * (int(cs.group(1)) - 1)
            rows.append(cells)
        res.append({"title": title, "line": line, "rows": rows, "pos": m.start()})
    return res


NUM = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?$")


def num(s):
    s = s.replace(" ", "")
    if s in ("", "-", "―"):
        return None
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-") or s.startswith("△") or s.startswith("▲")
    t = s.strip("()-△▲").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v
