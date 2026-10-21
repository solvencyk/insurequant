"""Read-only: multi-line-cell row reader for DART XML (statements use <TE><P>text</P></TE>, notes use single-line <TD>text</TD>).

rows_in_range(path, lo, hi) -> [{"tr": line_of_<TR>, "cells": [(text, line_of_text), ...]}]
sections(path)              -> {"sep_fs": (start, end), "sep_notes": (start, end), "cons_fs": ..., "cons_notes": ...}  by ATOC TITLE lines
"""
import re
from pathlib import Path

TAG = re.compile(r"<[^>]+>")
OPEN = re.compile(r"<(TD|TE|TH|TU)\b")
CLOSE = re.compile(r"</(TD|TE|TH|TU)>")


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ")).strip()


def read_lines(path):
    return Path(path).read_text(encoding="utf-8", errors="replace").split("\n")


def sections(lines):
    """major sections by ATOC TITLE lines; each ends at the next MAJOR title (not at an inner sub-title)."""
    titles = []
    for i, ln in enumerate(lines, start=1):
        if "<TITLE" in ln:
            titles.append((i, clean(ln)))
    kinds = []
    for ln, t in titles:
        if re.search(r"\d+\.\s*연결재무제표$", t):
            kinds.append((ln, "cons_fs"))
        elif re.search(r"\d+\.\s*연결재무제표 주석$", t):
            kinds.append((ln, "cons_notes"))
        elif re.search(r"\d+\.\s*재무제표$", t):
            kinds.append((ln, "sep_fs"))
        elif re.search(r"\d+\.\s*재무제표 주석$", t):
            kinds.append((ln, "sep_notes"))
        elif re.match(r"^[IVX]+\.\s", t) and kinds:
            kinds.append((ln, "other_major"))
    names = {}
    for i, (ln, k) in enumerate(kinds):
        if k == "other_major":
            continue
        nxt = kinds[i + 1][0] if i + 1 < len(kinds) else len(lines)
        names[k] = (ln, nxt)
    return names


def rows_in_range(lines, lo, hi):
    rows, cur, cell = [], None, None
    for i in range(lo, min(hi, len(lines)) + 1):
        ln = lines[i - 1]
        if "<TR" in ln:
            cur = {"tr": i, "cells": []}
        if cur is None:
            continue
        # a line may open/close several single-line cells; handle sequentially
        pos = 0
        while pos < len(ln):
            if cell is None:
                m = OPEN.search(ln, pos)
                if not m:
                    break
                cell = {"text": [], "line": None, "start": i}
                gt = ln.find(">", m.end())
                pos = (gt + 1) if gt >= 0 else len(ln)
            m2 = CLOSE.search(ln, pos)
            seg = ln[pos:m2.start()] if m2 else ln[pos:]
            t = clean(seg)
            if t:
                cell["text"].append(t)
                if cell["line"] is None:
                    cell["line"] = i
            if m2:
                cur["cells"].append((" ".join(cell["text"]), cell["line"] or cell["start"]))
                cell = None
                pos = m2.end()
            else:
                break
        if "</TR>" in ln and cur is not None:
            rows.append(cur)
            cur = None
    return rows


def num(s):
    s = s.replace(",", "").strip()
    if s in ("-", ""):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v
