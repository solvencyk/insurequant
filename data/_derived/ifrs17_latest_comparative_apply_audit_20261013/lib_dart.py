"""Independent DART XML table reader for the 20261013 IFRS17 audit (own code; parser code is not imported)."""
import re, os, glob
from lxml import etree

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
CELLTAGS = {"TD", "TH", "TU", "TE"}

def norm(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()

_cache = {}
def find_xml(code, fy_q, rcept=None):
    """fy_q like 'FY2024_Q1'. returns list of main-document xml paths for the company in that folder"""
    base = f"{REPO}/data/dart/{fy_q}/raw"
    paths = []
    for d in sorted(glob.glob(f"{base}/{code}_*")):
        paths += sorted(glob.glob(d + "/*.xml")) + sorted(glob.glob(d + "/xml/*.xml"))
    if rcept:
        paths = [p for p in paths if p.replace("\\", "/").endswith(f"/{rcept}.xml")]
    else:
        paths = [p for p in paths if re.search(r"/\d{14}\.xml$", p.replace("\\", "/"))] or paths
    return paths

def load_tables(path):
    if path in _cache: return _cache[path]
    parser = etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False)
    root = etree.parse(path, parser).getroot()
    tables = []
    # iterate in document order: remember last text paragraphs as caption
    last_text = []
    for el in root.iter():
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag == "TABLE":
            rows = []
            for tr in el.iter("TR"):
                a = tr.getparent()
                while a is not None and a.tag != "TABLE": a = a.getparent()
                if a is not el: continue
                cells = []
                for c in tr:
                    if c.tag in CELLTAGS:
                        cells.append(norm("".join(c.itertext())))
                if cells: rows.append(cells)
            tables.append({"idx": len(tables), "line": el.sourceline, "rows": rows, "caption": " | ".join(last_text[-4:])})
            last_text = []
        elif tag in ("P", "TITLE", "SUBTITLE", "SECTION-1", "SECTION-2", "SECTION-3", "H1", "H2", "H3"):
            t = norm("".join(el.itertext())) if tag != "P" or len(el) == 0 else ""
            if t and len(t) < 400: last_text.append(t)
    _cache[path] = tables
    return tables

NUMPAT = re.compile(r"^\(?[△▲\-−–]?\s*[\d,]+(\.\d+)?\s*\)?$")
def is_num(t): return bool(NUMPAT.match(t.strip())) and any(c.isdigit() for c in t)
def to_num(t):
    t = t.strip(); neg = False
    if t.startswith("(") and t.endswith(")"): neg = True; t = t[1:-1].strip()
    if t and t[0] in "△▲-−–": neg = True; t = t[1:].strip()
    t = t.replace(",", "")
    try: v = float(t)
    except ValueError: return None
    return -v if neg else v
DASH = {"-", "–", "—", "−", ""}
def row_vals(row):
    """(label, [values]) : label = first non-numeric cell(s), values = numeric/dash cells after label"""
    label = []; vals = []
    for c in row:
        if is_num(c): vals.append(to_num(c))
        elif c.strip() in ("-", "–", "—", "−") and label: vals.append(0.0)
        elif not vals: label.append(c)
    return " ".join(label), vals
