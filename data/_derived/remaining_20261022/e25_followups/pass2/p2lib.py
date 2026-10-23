# -*- coding: utf-8 -*-
"""pass2 shared READ-ONLY helpers (parser/ifrs17, ticket 20261024T0300Z).
Own thin layer over the measure-phase line reader (mlib) and the e21/e23 row readers; handles both DART dialects (the classic tag-per-line XML and the plain-HTML 2026 filings that indent <TD>/<TR>).
No import of scripts/ or src/ handlers.  Every value carries its physical xml line number (1-based)."""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/sweep_neighbors2")
import s2lib  # noqa: E402  (patches mlib.read_lines: left-strip so indented <TR>/<TD> are seen; physical line numbers unchanged)

E = s2lib.E
T = s2lib.T
M = T.M
W = E.W
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EVP = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass2"
nl = T.nl

QFY_LATER = lambda q: M.later_fy(q)           # filing whose PRIOR-year column prints quarter q   # noqa: E731
QFY_OWN = lambda q: M.fy_of(q)                # filing of the quarter itself (current-period column)   # noqa: E731


def main_path(code, fy):
    return T.main_path(code, fy)


def load(code, fy):
    """-> (path, lines, s0, [(table, rows)]) of the separate-basis notes of the main filing"""
    path = main_path(code, fy)
    lines, s0, tabs = s2lib.tables_sep2(path)
    return path, lines, s0, tabs


def load_all(code, fy):
    """all tables of the filing (statement + notes), rows = rows_full23"""
    path = main_path(code, fy)
    lines = M.read_lines(path)
    out = []
    for t in M.iter_tables(lines):
        out.append((t, E.rows_full23(lines, t["start"], t["end"])))
    return path, lines, out


def nums(row, skip=1):
    """[(val, line, text)] numeric cells after the first `skip` cells ('-' = 0)"""
    out = []
    for c in row["cells"][skip:]:
        if c["val"] is not None:
            out.append((c["val"], c["line"], c["text"]))
        elif c["text"].strip() in ("-", "\u2212"):
            out.append((0.0, c["line"], c["text"]))
    return out


def lab(r):
    return E.lab(r)


def rowtext(r):
    return r["cells"][0]["text"] if r["cells"] else ""


def show(t, rows, lines=None, unit=None, maxn=14, tag=""):
    u = unit or (T.find_unit(lines, t, span=2500) if lines is not None else "?")
    print(f"  --- {tag} table@L{t['start']}-{t['end']} unit={u} title={t['title']!r} caption={nl(t['caption'] or '')[:70]!r}")
    for r in rows:
        if not r["cells"]:
            continue
        n = nums(r)
        print(f"    R{r['tr_line']:>6} {rowtext(r)[:40]:40s} " + " | ".join(f"{tx}@{ln}" for _v, ln, tx in n[:maxn]))


def find_tables(tabs, pred):
    return [(t, rows) for t, rows in tabs if pred(t, rows, [lab(r) for r in rows])]


_TAGRE = re.compile(r"<[^>]+>")


def tables_with(code, fy, kw_all, sep_only=True, extra_any=None):
    """-> (path, lines, s0, [(table, rows)]) for the tables whose raw text (tags stripped, whitespace removed) contains ALL needles `kw_all` (and any of `extra_any`).
    Cheap prefilter before rows_full23, so big annual filings stay fast."""
    path = main_path(code, fy)
    lines = M.read_lines(path)
    s0 = s2lib.sep_start2(lines)
    need = [nl(k) for k in kw_all]
    anyk = [nl(k) for k in (extra_any or [])]
    out = []
    for t in M.iter_tables(lines):
        if sep_only and t["start"] < s0:
            continue
        blob = nl(_TAGRE.sub("", " ".join(lines[t["start"] - 1:t["end"]])).replace("&nbsp;", ""))
        if all(k in blob for k in need) and (not anyk or any(k in blob for k in anyk)):
            out.append((t, E.rows_full23(lines, t["start"], t["end"])))
    return path, lines, s0, out
