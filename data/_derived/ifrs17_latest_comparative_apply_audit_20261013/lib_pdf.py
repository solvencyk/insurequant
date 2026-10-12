"""Independent PDF row reader (validation audit 20261013). Written from scratch; no parser code imported."""
import re, fitz

NUMRE = re.compile(r"^\(?[△▲\-−–]?[\d,]+(\.\d+)?\)?$")
DASHES = {"-", "–", "—", "−", "―"}

def page_rows(doc, pno, ytol=3.0):
    """rows of (y, [(x0, x1, text)...]) for 1-based page"""
    page = doc[pno - 1]
    words = page.get_text("words")
    words.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    rows = []
    for w in words:
        yc = (w[1] + w[3]) / 2
        for r in rows:
            if abs(r[0] - yc) <= ytol:
                r[1].append((w[0], w[2], w[4])); break
        else:
            rows.append([yc, [(w[0], w[2], w[4])]])
    rows.sort(key=lambda r: r[0])
    return [(y, sorted(ws)) for y, ws in rows]

def is_num(t):
    return bool(NUMRE.match(t)) and any(c.isdigit() for c in t)

def to_num(tok):
    t = tok.strip(); neg = False
    if t.startswith("(") and t.endswith(")"): neg = True; t = t[1:-1]
    if t and t[0] in "△▲-−–": neg = True; t = t[1:]
    t = t.replace(",", "")
    try: v = float(t)
    except ValueError: return None
    return -v if neg else v
