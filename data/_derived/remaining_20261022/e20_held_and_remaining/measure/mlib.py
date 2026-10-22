# -*- coding: utf-8 -*-
"""mlib: shared READ-ONLY helpers for the e20 measurement (no repo writes, no imports from scripts/ at import time).

* masters are read from the session scratchpad snapshot (snap/), so a concurrent STEP-1 apply cannot move the baseline
* DART XML is read line-oriented so every value carries its exact filing line number
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
SNAP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/"
            "429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/snap")
MEASURE = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/measure"
D_CENSUS = ROOT / "data/_derived/remaining_20261022/d_census"
DART = ROOT / "data/dart"

QUARTERS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q",
            "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]


def fy_of(q: str) -> str:
    """'2023.3Q' -> 'FY2023_Q3'"""
    y, qq = q.split(".")
    return f"FY{y}_Q{qq[0]}"


def later_fy(q: str) -> str:
    """filing whose PRIOR-year column prints quarter q: '2023.3Q' -> 'FY2024_Q3'"""
    y, qq = q.split(".")
    return f"FY{int(y) + 1}_Q{qq[0]}"


def jload(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def itn(x):
    """item number: int when numeric, else the string ('2-1' extra-LOB legs)."""
    try:
        return int(x)
    except (TypeError, ValueError):
        return str(x)


def load_pl(snap: bool = True):
    """-> dict[(code, q)] -> {item(int): value}, plus name map"""
    rows = jload((SNAP if snap else ROOT) / "PL_breakdown.json")
    pl, names, item_names = {}, {}, {}
    for r in rows:
        k = (r["원보험사코드"], r["공시분기"])
        pl.setdefault(k, {})[itn(r["항목번호"])] = r["값"]
        names[r["원보험사코드"]] = r["원수사명"]
        item_names[itn(r["항목번호"])] = r["항목명"]
    return pl, names, item_names


def load_pl_dangi(snap: bool = True):
    rows = jload((SNAP if snap else ROOT) / "PL_breakdown.json")
    out = {}
    for r in rows:
        out.setdefault((r["원보험사코드"], r["공시분기"]), {})[itn(r["항목번호"])] = r.get("값_당분기")
    return out


def load_csm(snap: bool = True):
    rows = jload((SNAP if snap else ROOT) / "CSM_waterfall.json")
    csm = {}
    for r in rows:
        csm.setdefault((r["원보험사코드"], r["공시분기"]), {})[itn(r["항목번호"])] = r["값"]
    return csm


def load_csm_dangi(snap: bool = True):
    rows = jload((SNAP if snap else ROOT) / "CSM_waterfall.json")
    csm = {}
    for r in rows:
        csm.setdefault((r["원보험사코드"], r["공시분기"]), {})[itn(r["항목번호"])] = r.get("값_당분기")
    return csm


# ----------------------------------------------------------------------------------------------------------------------
# filing location
# ----------------------------------------------------------------------------------------------------------------------
def filing_dirs(code: str, fy: str):
    base = DART / fy / "raw"
    return sorted(base.glob(f"{code}_*")) if base.exists() else []


def main_xmls(code: str, fy: str):
    """main-body XML(s) of a filing, biggest first (excludes the audit-report attachments _00760/_00761)."""
    out = []
    for d in filing_dirs(code, fy):
        for p in list(d.glob("*.xml")) + list(d.glob("xml/*.xml")):
            out.append(p)
    out = sorted(set(out), key=lambda p: p.stat().st_size, reverse=True)
    return out


def rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(p)


# ----------------------------------------------------------------------------------------------------------------------
# line-oriented DART XML table reader
# ----------------------------------------------------------------------------------------------------------------------
RE_ATTR = re.compile(r'(ACODE|ACONTEXT|ADECIMAL|COLSPAN|ROWSPAN)="([^"]*)"')
RE_P = re.compile(r"<P[^>]*>(.*?)</P>")
RE_TAG = re.compile(r"<[^>]+>")


def num(t: str):
    t = (t or "").replace(",", "").replace("\u3000", " ").strip()
    if t in ("", "-"):
        return None
    neg = (t.startswith("(") and t.endswith(")")) or t.startswith("-") or t.startswith("△") or t.startswith("▽")
    t2 = t.strip("()-△▽ ")
    try:
        v = float(t2)
    except ValueError:
        return None
    return -v if neg else v


def read_lines(path) -> list[str]:
    return Path(path).read_text(encoding="utf-8", errors="replace").split("\n")


def iter_tables(lines: list[str]):
    """Yield dict(start, end, title, title_line, caption, rows=[{tr_line, cells=[{text,val,line,acode,ctx,colspan}]}])
    for every <TABLE> in document order.  `caption` = last non-empty <P> text seen before the table (outside any table)
    that is not a pure period tag; `title` = last <TITLE>."""
    n = len(lines)
    i = 0
    title, title_line = "", 0
    caption, caption_line = "", 0
    while i < n:
        l = lines[i]
        if l.startswith("<TITLE"):
            title = RE_TAG.sub("", l).strip()
            title_line = i + 1
        if l.startswith("<TABLE"):
            start = i + 1
            rows, cur = [], None
            j = i
            while j < n and not lines[j].startswith("</TABLE"):
                lj = lines[j]
                if lj.startswith("<TR"):
                    cur = {"tr_line": j + 1, "cells": []}
                elif lj.startswith("</TR"):
                    if cur is not None and cur["cells"]:
                        rows.append(cur)
                    cur = None
                elif cur is not None and (lj.startswith("<TE") or lj.startswith("<TH") or lj.startswith("<TD")):
                    attrs = dict(RE_ATTR.findall(lj))
                    k, txt, pline = j + 1, [], None
                    inline = re.search(r">([^<]*)</T[EHD]>\s*$", lj)
                    if inline:
                        txt.append(inline.group(1).replace("\u3000", " ").strip())
                        pline = j + 1
                        k = j
                    while not inline and k < n and not lines[k].startswith("</TE") and not lines[k].startswith("</TH") \
                            and not lines[k].startswith("</TD"):
                        m = RE_P.search(lines[k])
                        if m:
                            txt.append(RE_TAG.sub("", m.group(1)).replace("\u3000", " ").strip())
                            if pline is None:
                                pline = k + 1
                        k += 1
                    text = " ".join(t for t in txt if t).strip()
                    cur["cells"].append({"text": text, "val": num(text), "line": pline or (j + 1),
                                         "acode": attrs.get("ACODE"), "ctx": attrs.get("ACONTEXT", ""),
                                         "colspan": int(attrs.get("COLSPAN", "1") or 1)})
                    j = k
                j += 1
            yield {"start": start, "end": j + 1, "title": title, "title_line": title_line,
                   "caption": caption, "caption_line": caption_line, "rows": rows}
            i = j
        else:
            m = RE_P.search(l)
            if m:
                tx = RE_TAG.sub("", m.group(1)).replace("\u3000", " ").strip()
                if tx:
                    caption, caption_line = tx, i + 1
        i += 1


def short_ctx(c: str) -> str:
    m = re.match(r"([CP]FY\d{4}d[A-Z]+)_", c or "")
    sep = "SEP" if "SeparateMember" in (c or "") else ("CON" if "ConsolidatedMember" in (c or "") else "---")
    return (m.group(1) if m else (c or "")[:20]) + ":" + sep


def norm_label(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").replace("\u3000", ""))


def fmt(v, nd=1):
    if v is None:
        return "None"
    return f"{v:,.{nd}f}"
