# independent reader for DART xml (stdlib only)
import re, html
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
FILES_OLD = {
 "FY2024_Q1": ROOT + "/data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험/20240516002045.xml",
 "FY2024_Q2": ROOT + "/data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험/20240814004092.xml",
 "FY2024_Q3": ROOT + "/data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험/20241114002738.xml",
 "FY2024_Q4": ROOT + "/data/dart/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358/20250331001358.xml",
}
_cache = {}
def load(fy):
    if fy in _cache: return _cache[fy]
    txt = open(FILES[fy], encoding="utf-8", errors="replace").read()
    lines = txt.split("\n")
    _cache[fy] = lines
    return lines
def tables(fy):
    """list of dict(start, end, rows=[(line, [cells])], thead_rows)"""
    lines = load(fy)
    out = []; cur = None
    for i, ln in enumerate(lines, 1):
        u = ln
        if "<TABLE" in u and cur is None:
            cur = {"start": i, "rows": [], "cell": None, "row": None}
        if cur is not None:
            # process tokens in order
            for m in re.finditer(r"<(/?)(TR|TD|TH|TE)\b[^>]*>|<[^>]*>|([^<]+)", u):
                if m.group(0).startswith("<") and not m.group(2):
                    continue
                if m.group(2):
                    tag = m.group(2); close = bool(m.group(1))
                    if tag == "TR" and not close:
                        cur["row"] = {"line": i, "cells": []}
                    elif tag == "TR" and close:
                        if cur["row"] is not None: cur["rows"].append(cur["row"])
                        cur["row"] = None
                    elif tag in ("TD", "TH", "TE") and not close:
                        cur["cell"] = {"line": i, "t": ""}
                    elif tag in ("TD", "TH", "TE") and close:
                        if cur["cell"] is not None and cur["row"] is not None:
                            cur["row"]["cells"].append((cur["cell"]["line"], html.unescape(cur["cell"]["t"]).replace("\u3000", " ").strip()))
                        cur["cell"] = None
                elif m.group(3) and cur["cell"] is not None:
                    cur["cell"]["t"] += m.group(3)
            if "</TABLE>" in u:
                cur["end"] = i
                out.append(cur); cur = None
    return out
def num(s):
    """parse printed number; parentheses/triangle = negative; returns float or None"""
    s = s.strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "－", "—"): return None
    neg = False
    if s.startswith("(") and s.endswith(")"): neg = True; s = s[1:-1]
    if s.startswith("△") or s.startswith("▲"): neg = True; s = s[1:]
    if s.startswith("-"): neg = True; s = s[1:]
    try: v = float(s)
    except ValueError: return None
    return -v if neg else v

D = ROOT + "/data/dart/"
FILES = {
 "FY2023_Q1": D + "FY2023_Q1/raw/KR0009_현대해상/xml/20230515002873.xml",
 "FY2023_Q2": D + "FY2023_Q2/raw/KR0009_현대해상/xml/20230814003156.xml",
 "FY2023_Q3": D + "FY2023_Q3/raw/KR0009_현대해상/xml/20231114002737.xml",
 "FY2023_Q4": D + "FY2023_Q4/raw/KR0009_현대해상_20240314001515/xml/20240314001515.xml",
 "FY2024_Q1": D + "FY2024_Q1/raw/KR0009_현대해상/20240516002153.xml",
 "FY2024_Q2": D + "FY2024_Q2/raw/KR0009_현대해상/20240814004187.xml",
 "FY2024_Q3": D + "FY2024_Q3/raw/KR0009_현대해상/20241114003026.xml",
 "FY2024_Q4": D + "FY2024_Q4/raw/KR0009_현대해상_20250313001346/20250313001346.xml",
 "FY2025_Q4": D + "FY2025_Q4/raw/KR0009_현대해상_20260312001448/20260312001448.xml",
}
