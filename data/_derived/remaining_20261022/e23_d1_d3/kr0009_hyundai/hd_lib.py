# -*- coding: utf-8 -*-
"""KR0009 현대해상 (ticket 20261023T0900Z D3): raw DART-XML table machinery used by the independent verifier.  Standard library only (no e21_* / e23_* / scripts / src import).
Adapted from the audited machinery of the ABL verifier (kr0070_verify.py); the Hyundai-specific readers (statement labels, 보험수익 note, CSM roll-forward, IR factsheet via zipfile) are new code."""
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
TAG = re.compile(r"<[^>]+>")
_cache = {}


def lines_of(rel):
    if rel not in _cache:
        _cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return _cache[rel]


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("\u3000", " ").replace("\xa0", " ")).strip()


def nspace(s):
    return re.sub(r"\s+", "", (s or "").replace("\u3000", ""))


def parse_num(t):
    t = (t or "").strip().replace(",", "").replace(" ", "")
    if t == "":
        return None
    if t in ("-", "\u2212"):
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    t2 = t.strip("()")
    try:
        v = float(t2)
    except ValueError:
        return None
    return -v if neg else v


UNIT_MN = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0}


def mn(printed, unit):
    v = parse_num(printed)
    return None if v is None else v * UNIT_MN[unit]


def close(a, b, tol=2e-6):
    return a is not None and b is not None and abs(a - b) <= tol


def parse_tr(L, i, j):
    out = []
    k = i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", L[k], re.I)
        if m:
            attrs = m.group(2)
            cs = re.search(r'COLSPAN="(\d+)"', attrs, re.I)
            rs = re.search(r'ROWSPAN="(\d+)"', attrs, re.I)
            rest = m.group(3)
            base = dict(tag=m.group(1).upper(), colspan=int(cs.group(1)) if cs else 1, rowspan=int(rs.group(1)) if rs else 1)
            if re.search(r"</(TD|TE|TH)>\s*$", rest, re.I):
                out.append(dict(base, text=clean(rest), line=k + 1))
            else:
                buf, tl, q = ([clean(rest)] if clean(rest) else []), (k + 1 if clean(rest) else None), k + 1
                while q <= j and not re.match(r"\s*</(TD|TE|TH)", L[q], re.I):
                    t = clean(L[q])
                    if t:
                        buf.append(t)
                        if tl is None:
                            tl = q + 1
                    q += 1
                out.append(dict(base, text=" ".join(buf).strip(), line=tl or (k + 1)))
                k = q
        k += 1
    return out


def table_rows(L, a, b):
    rows, k = [], a
    while k <= b:
        if re.match(r"\s*<TR\b", L[k], re.I):
            j = k
            while not re.match(r"\s*</TR", L[j], re.I):
                j += 1
            rows.append(dict(tr=k + 1, cells=parse_tr(L, k, j)))
            k = j
        k += 1
    return rows


def all_tables(L):
    out, stack = [], []
    for k, s in enumerate(L):
        if re.match(r"\s*<TABLE\b", s, re.I):
            if stack:
                stack[-1][1] = True
            stack.append([k, False])
        elif re.match(r"\s*</TABLE", s, re.I) and stack:
            a, has_child = stack.pop()
            if not has_child:
                out.append((a, k))
    return out


def header_paths(L, a, b):
    h0 = next((k for k in range(a, b + 1) if re.match(r"\s*<THEAD", L[k], re.I)), None)
    h1 = next((k for k in range(h0 or a, b + 1) if re.match(r"\s*</THEAD", L[k], re.I)), None)
    if h0 is None or h1 is None:
        return None
    trs, k = [], h0
    while k <= h1:
        if re.match(r"\s*<TR", L[k], re.I):
            i0 = k
            while not re.match(r"\s*</TR", L[k], re.I):
                k += 1
            trs.append((i0, k))
        k += 1
    grid, occ, ncols = {}, set(), 0
    for r, (i0, j0) in enumerate(trs):
        col = 0
        for c in parse_tr(L, i0, j0):
            while (r, col) in occ:
                col += 1
            for dr in range(c["rowspan"]):
                for dc in range(c["colspan"]):
                    occ.add((r + dr, col + dc))
                    grid[(r + dr, col + dc)] = c["text"]
            col += c["colspan"]
        ncols = max(ncols, col)
    paths = []
    for col in range(ncols):
        path = []
        for r in range(len(trs)):
            t = grid.get((r, col))
            if t is not None and (not path or path[-1] != t):
                path.append(t)
        paths.append(path)
    return paths


def body_rows(L, a, b):
    h1 = next((k for k in range(a, b + 1) if re.match(r"\s*</THEAD", L[k], re.I)), None)
    rows = table_rows(L, a, b)
    return [r for r in rows if h1 is None or r["tr"] - 1 > h1]


def titles(L):
    return [(k, clean(s)) for k, s in enumerate(L) if s.startswith("<TITLE")]


def section(L, title_re, nth=0):
    ts = titles(L)
    hits = [n for n, (k, t) in enumerate(ts) if re.search(title_re, t)]
    if len(hits) <= nth:
        raise RuntimeError(f"title {title_re!r} (#{nth}) not found")
    n = hits[nth]
    return ts[n][0], (ts[n + 1][0] if n + 1 < len(ts) else len(L) - 1)


def unit_above(L, ln, span=400):
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", L[k]))
        if m:
            return m.group(1), k + 1
    return None, None


# ---------------------------------------------------------------------------------------------- IR factsheet (xlsx via zipfile + ElementTree; no openpyxl)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def read_xlsx_sheet(rel, sheet_name):
    """-> dict coordinate -> value (str for text cells, float for numeric cells, taken from the raw cell XML <v>), unit-free"""
    with zipfile.ZipFile(ROOT / rel) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid = None
        for s in wb.find("m:sheets", NS):
            if s.get("name") == sheet_name:
                rid = s.get("{%s}id" % NS["r"])
        if rid is None:
            raise RuntimeError(f"{rel}: sheet {sheet_name!r} not found")
        target = next(r.get("Target") for r in rels if r.get("Id") == rid)
        path = "xl/" + target.lstrip("/").replace("xl/", "") if not target.startswith("/xl/") else target.lstrip("/")
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        sh = ET.fromstring(z.read(path))
        out = {}
        for c in sh.iter("{%s}c" % NS["m"]):
            coord, t = c.get("r"), c.get("t")
            v = c.find("m:v", NS)
            if t == "s" and v is not None:
                out[coord] = shared[int(v.text)]
            elif t == "inlineStr":
                out[coord] = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            elif v is not None and v.text is not None:
                try:
                    out[coord] = float(v.text)
                except ValueError:
                    out[coord] = v.text
        return out
