# -*- coding: utf-8 -*-
"""fsapi: READ-ONLY access to the committed DART FS-API cache with the production Tier-1 parser (scripts/fetch_dart_fs._parse).
same(code,q)  = the filing of quarter q itself (thstrm / thstrm_add)
prior(code,q) = the NEXT-year filing's prior column (frmtrm / frmtrm_add)  == 'latest comparative'
Never writes anything.  Importing fetch_dart_fs needs cwd = repo root (it inserts Path.cwd() into sys.path); we chdir in-process only."""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_dart_fs as fdf  # noqa: E402

CACHE = ROOT / "data/dart/_fs_api_cache"
_KR2CC = {}
for mp in sorted((ROOT / "data/dart").glob("FY*_Q*/raw/KR*_*/meta.json")):
    code = mp.parent.name.split("_")[0]
    if code not in _KR2CC:
        try:
            cc = json.loads(mp.read_text(encoding="utf-8")).get("corp_code")
            if cc:
                _KR2CC[code] = cc
        except Exception:
            pass


def corp(code: str):
    return _KR2CC.get(code)


def load(code: str, year: str, reprt: str, div: str):
    cc = _KR2CC.get(code)
    if not cc:
        return None
    p = CACHE / f"{cc}_{year}_{reprt}_{div}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def same(code: str, q: str, divs=("OFS", "CFS")):
    reprt = fdf.REPRT[q[5:]]
    annual = q[5:] == "4Q"
    for div in divs:
        d = load(code, q[:4], reprt, div)
        if d is None:
            continue
        t = fdf._parse(d, annual)
        if t:
            return t, div
    return None, None


def prior_raw(code: str, q: str, div: str):
    """the next-year response rewritten so that thstrm_* = the prior column (YTD)"""
    reprt = fdf.REPRT[q[5:]]
    annual = q[5:] == "4Q"
    nxt = str(int(q[:4]) + 1)
    d = load(code, nxt, reprt, div)
    if d is None:
        return None
    d = copy.deepcopy(d)
    for a in d.get("list", []) or []:
        if annual:
            a["thstrm_amount"], a["thstrm_add_amount"] = a.get("frmtrm_amount"), ""
        else:
            a["thstrm_amount"] = a.get("frmtrm_q_amount")
            a["thstrm_add_amount"] = a.get("frmtrm_add_amount")
    return d


def prior(code: str, q: str, divs=("OFS", "CFS")):
    reprt = fdf.REPRT[q[5:]]
    annual = q[5:] == "4Q"
    for div in divs:
        d = prior_raw(code, q, div)
        if d is None:
            continue
        t = fdf._parse(d, annual)
        if t:
            return t, div
    return None, None


def prior_3m(code: str, q: str, div: str = "OFS"):
    """3-month (single-quarter) prior print for quarterly filings: frmtrm_q_amount (None for Q1 annual)."""
    reprt = fdf.REPRT[q[5:]]
    nxt = str(int(q[:4]) + 1)
    d = load(code, nxt, reprt, div)
    if d is None or q[5:] == "4Q":
        return None
    d = copy.deepcopy(d)
    for a in d.get("list", []) or []:
        a["thstrm_amount"] = a.get("frmtrm_q_amount")
        a["thstrm_add_amount"] = a.get("frmtrm_q_amount")
    return fdf._parse(d, False)


def rows(code: str, year: str, q: str, div: str = "OFS"):
    d = load(code, year, fdf.REPRT[q[5:]], div)
    return (d or {}).get("list", []) if d else []
