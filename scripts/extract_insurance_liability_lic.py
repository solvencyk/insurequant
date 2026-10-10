# -*- coding: utf-8 -*-
"""
Extract 발생사고요소(LIC: liability for incurred claims) BEL / RA and 잔여보장요소(LRC) closing
balances of 보험계약부채 from the DART 사업/반기/분기보고서 (and 감사보고서 for 비상장사) XML and add them
to insurance_liability_portfolio.json as NEW items 10..17 (owner 2026-10-10: no new master file).

Source of truth = the "보험계약부채(자산)의 변동" note table (잔여보장요소 / 발생사고요소 변동),
closing row of the LIABILITY side ("부채인 보험계약의 기말 장부금액"), separate-statement scope,
current period, insurance contracts issued only (재보험 보유분 제외).  The liability basis is the
one that closes against IFRS17_BS.json item 20 (보험계약부채, 별도 기준, 백만원).

Rows added to insurance_liability_portfolio.json (same fields as items 1-9, unit 억원 = DART 백만원/100,
two decimals, closing balance = stock; section 보험부채_발생사고요소; a source-absent cell has NO row):
  10 발생사고요소_합계                 L1  liability basis; = 합계열 - 잔여보장열 (independent of 11/12/13)
  11 발생사고요소_최선추정부채         L2  sum of "미래현금흐름의 현재가치 추정치" columns under 발생사고 (직접 공시분)
  12 발생사고요소_위험조정             L2  sum of "비금융위험에 대한 위험조정" columns under 발생사고 (직접 공시분)
  13 발생사고요소_미분리               L2  sum of single "발생사고" columns that are NOT split into BEL/RA
  14 잔여보장요소_합계                 L1  손실요소 포함 (DART 부채 기준; NOT the 2-4 net LRC of item 8)
  15 보험계약부채_합계                 L1  = 10 + 14  (검산 항목: IFRS17_BS item 20 +-0.1 %)
  16 발생사고요소_최선추정_간접(비PAA) L3  stage 2 only (derived: 측정요소별 BEL - 경영공시 2-4 BEL), never mixed with 11
  17 발생사고요소_위험조정_간접(비PAA) L3  stage 2 only

Items 11/12 are ABSENT (not 0) for a (company, quarter) whose table has no BEL/RA split at all
(단일열 공시, class "T"); item 13 is 0 for a company that splits everything (class "A1").  Items 16/17 are
registered here but NOT written by stage 1.

How the cells are chosen (all rules are recorded per cell in insurance_liability_portfolio_provenance.json):
  * scope: 별도 (nearest section marker without "연결"); tagged tables use the XBRL member
    (SeparateMember / ConsolidatedMember) and every tagged column role is cross-checked.
  * period: current period only; tagged tables use the CFY..e.. period token, untagged ones the
    table caption (당기/당분기/당반기), a carried caption cue, or the headingless second table of a pair.
  * insurer vs reinsurance: 보유(출재) 재보험계약 tables are dropped; 수재 stays (it is part of the issued book).
  * duplicates: equal-total tables (alternative cuts) and a parent table followed by its parts are
    reduced to one view (see reduce_tables); the choice is verified against item 20 and recorded.
  * units: explicit cue ("단위 : 백만원|천원|원", carried within a note); when the cue is missing, or
    contradicts the anchor by an exact power of ten, the scale is inferred from IFRS17_BS item 20
    (else from the filing's own 재무상태표) and the cell is marked unit_source="inferred_from_...".
  * a cell is "closed" when item 15 equals the anchor within +-0.1 %.  A filer whose tables show only
    the NET row (KB손해보험, 하나생명) cannot give a liability basis: loaded with basis="net".
  * a net-asset table (NET-only, negative total) contributes 0 to the liability basis (AXA, 카카오페이).

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_insurance_liability_lic.py            (dry run)
  ... --write     back up insurance_liability_portfolio.json, then add items 10..15 cell by cell (abort if a
                  key already exists) and write insurance_liability_portfolio_provenance.json
This script READS data/dart/FY*/raw/*.xml, IFRS17_BS.json and insurance_liability_portfolio.json and
WRITES only (with --write) insurance_liability_portfolio.json (append-only), the provenance file and the
backup under data/_derived/.  It never touches any other master.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import html
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DART = REPO / "data" / "dart"
IFRS17_BS = REPO / "IFRS17_BS.json"
ILP = REPO / "insurance_liability_portfolio.json"
OUT_PROV = REPO / "insurance_liability_portfolio_provenance.json"
BACKUP_DIR = REPO / "data" / "_derived"

FY_DIRS = ["FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4", "FY2026_Q1", "FY2026_Q2"]
# 2026-10-10 backfill (ticket 20261010T1600Z): the same engine reads the 2023-2024 filings.  FY_DIRS (the default of
# build_all / --write) stays the stage-1 set so the existing 158 cells are never re-derived by accident.
FY_DIRS_PRE2025 = ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2023_Q4",
                   "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"]
QMAP = {"FY2023_Q1": "2023.1Q", "FY2023_Q2": "2023.2Q", "FY2023_Q3": "2023.3Q", "FY2023_Q4": "2023.4Q",
        "FY2024_Q1": "2024.1Q", "FY2024_Q2": "2024.2Q", "FY2024_Q3": "2024.3Q", "FY2024_Q4": "2024.4Q",
        "FY2025_Q1": "2025.1Q", "FY2025_Q2": "2025.2Q", "FY2025_Q3": "2025.3Q",
        "FY2025_Q4": "2025.4Q", "FY2026_Q1": "2026.1Q", "FY2026_Q2": "2026.2Q"}
QUARTER_END = {"1Q": "03-31", "2Q": "06-30", "3Q": "09-30", "4Q": "12-31"}

LIC_SECTION = "보험부채_발생사고요소"
# item number -> (항목명, 섹션, 레벨).  Registered once; do not silently renumber.
ITEM_CATALOG = {
    10: ("발생사고요소_합계", LIC_SECTION, 1),
    11: ("발생사고요소_최선추정부채", LIC_SECTION, 2),
    12: ("발생사고요소_위험조정", LIC_SECTION, 2),
    13: ("발생사고요소_미분리", LIC_SECTION, 2),
    14: ("잔여보장요소_합계", LIC_SECTION, 1),
    15: ("보험계약부채_합계", LIC_SECTION, 1),
    16: ("발생사고요소_최선추정_간접(비PAA)", LIC_SECTION, 3),
    17: ("발생사고요소_위험조정_간접(비PAA)", LIC_SECTION, 3),
}
STAGE1_ITEMS = (10, 11, 12, 13, 14, 15)

# unit label -> multiplier to 백만원
UNIT_SCALE = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0, "억원": 100.0}

# --------------------------------------------------------------------------------------
# generic XML / table helpers
# --------------------------------------------------------------------------------------
TAB_RE = re.compile(r"<TABLE\b.*?</TABLE>", re.S | re.I)
TR_RE = re.compile(r"<TR\b.*?</TR>", re.S | re.I)
CELL_RE = re.compile(r"<(T[DHE])\b([^>]*)>(.*?)</T[DHE]>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[\s\u00a0\u3000]+")
SEC_RE = re.compile(r"<!-- ===== (\d+): ([^=]*?) =====")
TITLE_RE = re.compile(r"<TITLE[^>]*>([^<]*)</TITLE>")
NUM_RE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?$")


def clean(s: str) -> str:
    s = TAG_RE.sub(" ", s)
    s = html.unescape(s).replace("\u00a0", " ")
    return WS_RE.sub(" ", s).strip()


def comp(s: str) -> str:
    """compact: drop all whitespace"""
    return re.sub(r"\s+", "", s or "")


def read_xml(path) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


def parse_num(s):
    """DART number cell -> float, '-' -> 0.0, non-numeric -> None.  (x) and △x are negative."""
    s = (s or "").strip().replace(" ", "")
    if s in ("-", "－", "—", "–"):
        return 0.0
    if not s:
        return None
    neg = False
    if s[0] in "△▲":
        neg, s = True, s[1:]
    if not NUM_RE.match(s):
        return None
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _attr(a: str, name: str):
    m = re.search(name + r'="([^"]*)"', a)
    return m.group(1) if m else None


def _span(a: str, name: str) -> int:
    m = re.search(name + r"\s*=\s*['\"]?(\d+)", a, re.I)
    return int(m.group(1)) if m else 1


def parse_table(tab_html: str):
    """-> (grid, attrs).  grid: rectangular list[list[str]] with colspan/rowspan expanded;
    attrs: same shape, (ACODE, ACONTEXT) for tagged <TE> origin cells else None."""
    grid, atts = [], []
    pending = {}
    for r_i, tr in enumerate(TR_RE.finditer(tab_html)):
        row, arow = [], []
        c = 0

        def fill_pending():
            nonlocal c
            while (r_i, c) in pending:
                t_, a_ = pending.pop((r_i, c))
                row.append(t_)
                arow.append(a_)
                c += 1

        fill_pending()
        for m in CELL_RE.finditer(tr.group(0)):
            attrs, inner = m.group(2), m.group(3)
            cs, rs = _span(attrs, "colspan"), _span(attrs, "rowspan")
            txt = clean(inner)
            ac, cx = _attr(attrs, "ACODE"), _attr(attrs, "ACONTEXT")
            tag = (ac, cx) if (ac and cx) else None
            for k in range(cs):
                row.append(txt)
                arow.append(tag if k == 0 else None)
                for rr in range(1, rs):
                    pending[(r_i + rr, c)] = (txt, None)
                c += 1
            fill_pending()
        fill_pending()
        grid.append(row)
        atts.append(arow)
    w = max((len(r) for r in grid), default=0)
    grid = [r + [""] * (w - len(r)) for r in grid]
    atts = [r + [None] * (w - len(r)) for r in atts]
    return grid, atts


# --------------------------------------------------------------------------------------
# header paths / column roles / row classes
# --------------------------------------------------------------------------------------
PRIOR_COL = re.compile(r"(전분기|전반기|전기말|전기|전년)")
UMB_RE = re.compile(r"(잔여보장부채별그리고발생사고부채별보험계약|잔여보장부채와발생사고부채|잔여보장요소와발생사고요소|잔여보장요소및발생사고요소)(합계)?")


def split_header_rows(g):
    """index of the first data row = first row with >=2 numeric cells beyond the first two columns
    and a non-numeric label in column 0."""
    for i, r in enumerate(g):
        nums = sum(1 for c in r[1:] if parse_num(c) is not None and c.strip() != "")
        if nums >= 2 and parse_num(r[0]) is None and r[0].strip() != "":
            return i
    return len(g)


def _uniform_row(row) -> bool:
    """a row whose non-empty cells (col>=1) all carry the same text, e.g. a '기초금액' section row"""
    vals = [comp(x) for x in row[1:] if comp(x)]
    return len(vals) >= 3 and len(set(vals)) == 1


def col_paths(g, h):
    """compact header text per column (last 3 header rows, umbrella phrase removed), '|'-joined.
    Trailing uniform rows (section titles such as '기초금액' repeated over every column) are not
    column headers and are skipped."""
    paths = []
    w = len(g[0]) if g else 0
    while h > 0 and _uniform_row(g[h - 1]):
        h -= 1
    for c in range(w):
        seen = []
        for r in range(max(0, h - 3), h):
            x = UMB_RE.sub("", comp(g[r][c]))
            if x and (not seen or seen[-1] != x):
                seen.append(x)
        paths.append("|".join(seen))
    return paths


def role_of(path: str, loose: bool = False):
    """column role from the compact header path.
    LRC/LC            잔여보장요소 (손실요소 제외 / 손실요소)
    LIC_BEL/LIC_RA    발생사고요소 미래현금흐름의 현재가치 추정치 / 비금융위험에 대한 위험조정
    LIC_TOT           발생사고요소 단일열 (BEL/RA 미분리)
    TOT               합계열        SUB   소계열 (never summed)
    CSM / BEL_LRC / RA_LRC   measurement-element tables only (kind 'ME')
    loose=True is the REPAIR reading (assemble_cell tries it only after the plain reading failed to close a cell):
    a BEL/RA leaf whose 발생사고 group cell is blank, and a single 발생사고 column headed by the model name."""
    p = path
    if PRIOR_COL.search(p):
        return None
    parts = p.split("|")
    leaf = parts[-1]
    if leaf in ("", "합계", "계", "총계") or leaf.endswith("합계"):
        # a 합계 under ONE of the groups 잔여보장 / 발생사고 is that group's subtotal, not the grand total
        above = "|".join(parts[:-1])
        if ("잔여보장" in above) != ("발생사고" in above):
            return "SUB"
        return "TOT"
    if leaf == "소계":
        return "SUB"
    if re.fullmatch(r"(순)?보험계약(부채|자산)(\((자산|부채)\))?", leaf):
        return "TOT"        # the total column is sometimes headed '보험계약부채(자산)'
    if "보험계약마진" in p:
        return "CSM"
    lic = "발생사고" in p
    # BEL: "미래현금흐름의 현재가치 추정치" / "기대현금흐름현가" / "최선추정"
    bel = ("현금흐름" in p and "취득" not in p) or "최선추정" in p
    ra = "위험조정" in p
    if lic and ra:
        return "LIC_RA"
    if lic and bel:
        return "LIC_BEL"
    if lic and "발생사고" in leaf:
        return "LIC_TOT"
    if "잔여보장" in p and not lic:
        if bel:
            return "BEL_LRC"
        if ra:
            return "RA_LRC"
        # non-loss part: "손실요소를 제외한 / 손실요소 외 / 비손실요소 / 비손실회수요소"
        if "비손실" in p or "제외" in p or re.search(r"손실(회수)?요소(이)?외", p):
            return "LRC"
        if "손실요소" in p or "손실회수요소" in p:
            return "LC"
        return "LRC"
    if loose:
        if "잔여보장" not in p and "마진" not in p:
            if ra:
                return "LIC_RA"
            if bel:
                return "LIC_BEL"
        if lic and re.search(r"일반모형|변동수수료|보험료배분", leaf):
            return "LIC_TOT"
    return None


def classify_open(label: str):
    """opening-balance row class (기초/기시 ...): NET / LIAB / ASSET, the counterpart of classify_row for the closing
    rows; used only by the roll-forward continuity repair (this year's opening == last year's closing)"""
    l = comp(label)
    if not re.search(r"기초|기시", l) or "재보험" in l:
        return None
    if "자산및부채" in l or "자산과부채" in l:
        return "NET"
    if "부채인" in l:
        return "LIAB"
    if "자산인" in l:
        return "ASSET"
    if "보험계약자산" in l:
        return "ASSET"
    if ("순장부금액" in l or "순보험계약부채" in l or "보험계약부채(자산)" in l or "순부채" in l
            or "총장부금액" in l):
        return "NET"
    if "보험계약부채" in l:
        return "LIAB"
    return None


def classify_row(label: str):
    """closing-balance row class: LIAB / ASSET / NET / RE (reinsurance)"""
    l = comp(label)
    if "말" not in l:
        return None
    if "재보험" in l:
        return "RE"
    if "자산및부채" in l or "자산과부채" in l:
        return "NET"         # '기말 보험계약자산 및 부채' = the combined (net) closing row
    if "부채인" in l:
        return "LIAB"
    if "자산인" in l:
        return "ASSET"
    if "보험계약자산" in l:
        return "ASSET"
    if ("순장부금액" in l or "순보험계약부채" in l or "보험계약부채(자산)" in l or "순부채" in l
            or "총장부금액" in l):
        return "NET"
    if "보험계약부채" in l:
        return "LIAB"
    if "보험계약" in l or "장부금액" in l:
        return "NET"
    return None


BARE_ASSET = {"보험계약자산", "자산인보험계약", "자산인보험계약의장부금액"}
BARE_LIAB = {"보험계약부채", "부채인보험계약", "부채인보험계약의장부금액"}
BARE_RE = {"재보험계약자산", "재보험계약부채"}


def classify_bare(lab: str):
    """rows labelled just '보험계약자산' / '보험계약부채' that follow a '...말 순장부금액' row"""
    l = re.sub(r"^[\(\d\)\.\-\s]+", "", lab)
    if l in BARE_ASSET:
        return "ASSET"
    if l in BARE_LIAB:
        return "LIAB"
    if l in BARE_RE:
        return "RE"
    return None


def label_cols(g, h) -> int:
    """number of leading label columns: the first column whose non-empty data cells are mostly numeric
    (a '-' counts as numeric)."""
    data = g[h:]
    if not data:
        return 1
    for c in range(len(g[0])):
        vals = [x[c] for x in data if x[c].strip() != ""]
        if vals and sum(1 for v in vals if parse_num(v) is not None) / len(vals) >= 0.5:
            return max(1, c)
    return 1


def row_label(r, nl: int = 2) -> str:
    """compact label of a data row from its leading label cells (consecutive duplicates from
    rowspan/colspan expansion are collapsed)"""
    out = []
    for c in range(min(nl, len(r))):
        x = comp(r[c])
        if x and (not out or out[-1] != x) and parse_num(x) is None:
            out.append(x)
    return "".join(out)


ROW_CUR = re.compile(r"(당분기|당반기|당기|\(당\))")
ROW_PRIOR = re.compile(r"(전분기|전반기|전기|\(전\))")


def row_period(lab: str):
    """period named inside the row label of a table that stacks 당기 and 전기 blocks"""
    if ROW_PRIOR.search(lab):
        return "prior"
    if ROW_CUR.search(lab):
        return "cur"
    return None


# --------------------------------------------------------------------------------------
# section markers / period & unit cues
# --------------------------------------------------------------------------------------
def markers(t: str):
    ms = [(m.start(), m.group(2).strip()) for m in SEC_RE.finditer(t)]
    ms += [(m.start(), m.group(1).strip()) for m in TITLE_RE.finditer(t)]
    ms.sort()
    return ms


def scope_at(ms, pos):
    cur = ""
    for sp, st in ms:
        if sp <= pos:
            cur = st
        else:
            break
    return cur


COMPAR = re.compile(r"(당분기|당반기|당기)\s*(와|및|과)\s*(전분기|전반기|전기)")


def explicit_period(ctx: str):
    """last explicit current/prior marker in the preceding text (comparison phrases removed)"""
    ctx = COMPAR.sub("", ctx or "")
    last = None
    for m in re.finditer(r"\((당|전)\)|(당)(분기|반기|기)|(전)(분기|반기|기)", ctx):
        last = "cur" if "당" in m.group(0) else "prior"
    return last


def unit_of(ctx: str):
    m = re.findall(r"단위\s*:\s*(백만원|천원|원|억원|백만 원)", ctx or "")
    return m[-1].replace(" ", "") if m else None


# --------------------------------------------------------------------------------------
# XBRL tag layer (only some filers tag the note tables -- see harvest census in the runlog)
# --------------------------------------------------------------------------------------
RC_AXIS = re.compile(r"InsuranceContractsByRemainingCoverageAndIncurredClaimsAxis_(?:ifrs-full|dart|entity\d+)_(\w+?Member)")


def tag_dims(ctx: str):
    """(period_token, scope, tag_role) from an ACONTEXT string"""
    tok = ctx.split("_")[0]
    scope = "sep" if "SeparateMember" in ctx else ("con" if "ConsolidatedMember" in ctx else None)
    m = RC_AXIS.search(ctx)
    role = None
    if m:
        mem = m.group(1)
        if "ExcludingLossComponent" in mem:
            role = "LRC"
        elif "LossComponent" in mem:
            role = "LC"
        elif "EstimatesOfPresentValueOfFutureCashFlows" in mem:
            role = "LIC_BEL"
        elif "RiskAdjustmentForNonfinancialRisk" in mem:
            role = "LIC_RA"
        elif "LiabilitiesForIncurredClaims" in mem:
            role = "LIC_TOT"
        elif "LiabilitiesForRemainingCoverage" in mem:
            role = "LRC_GROUP"
        else:
            role = "OTHER:" + mem
    else:
        role = "TOT"
    return tok, scope, role


def tag_period(tok: str):
    """'CFY2025eHYA' -> cur ; 'PFY2024eHYA'/'BPFY..' -> prior"""
    if re.match(r"^CFY\d{4}e", tok):
        return "cur"
    if re.match(r"^(B?P)FY\d{4}e", tok):
        return "prior"
    return None


# --------------------------------------------------------------------------------------
# harvest: every LRC/LIC roll-forward table of one XML file
# --------------------------------------------------------------------------------------
def harvest_file(path) -> list:
    """Return one dict per LRC/LIC roll-forward candidate table (header paths, column roles and the
    closing rows).  Pure function of the file bytes."""
    t = read_xml(path)
    ms = markers(t)
    tops = [(m.start(), m.group(1).strip()) for m in TITLE_RE.finditer(t)
            if re.search(r"재무제표|재무상태표|주석|감사보고서", m.group(1))]
    out = []
    prev_small = ""
    prev_unit = None
    last_end = 0
    for i, m in enumerate(TAB_RE.finditer(t)):
        body = m.group(0)
        s_pos = m.start()
        ntr = body.upper().count("<TR")
        if "발생사고" in body and "잔여보장" in body and ntr >= 6:
            g, atts = parse_table(body)
            pre = clean(t[max(last_end, s_pos - 1500):s_pos])[-260:]
            h = split_header_rows(g)
            nl = label_cols(g, h)
            flat = comp(" ".join(" ".join(r) for r in g))
            has_open = any(re.search(r"기초|기시", row_label(r, nl)) for r in g[h:])
            if "발생사고" in flat and "잔여보장" in flat and has_open:
                paths = col_paths(g, h)
                roles = [role_of(p) if k >= nl else None for k, p in enumerate(paths)]
                roles_loose = [role_of(p, loose=True) if k >= nl else None for k, p in enumerate(paths)]
                hdrflat = comp(" ".join(" ".join(r) for r in g[:max(h, 1)]))
                rows, rows_p = {}, {}
                open_rows = {}
                tag_ctx, tag_ctx_p = {}, {}
                mode = None
                for ri in range(h, len(g)):
                    r = g[ri]
                    lab = row_label(r, nl)
                    if re.search(r"기초|기시", lab):
                        mode = "open"
                    elif "말" in lab:
                        mode = "close"
                    if mode == "open":
                        ocls = classify_open(lab)
                        if ocls and ocls not in open_rows:
                            ovals = [parse_num(c) if k >= nl else None for k, c in enumerate(r)]
                            if any(v is not None for v in ovals):
                                open_rows[ocls] = {"label": lab[:60], "vals": ovals}
                    cls = classify_row(lab)
                    bare = False
                    if not cls and mode == "close":
                        cls = classify_bare(lab)
                        bare = bool(cls)
                    if not cls:
                        continue
                    rp = row_period(lab)
                    vals = [parse_num(c) if k >= nl else None for k, c in enumerate(r)]
                    if not any(v is not None for v in vals):
                        continue          # a section-title row ('9.기말순장부금액') carries no number
                    rec_r = {"label": lab[:60], "vals": vals}
                    if bare:
                        rec_r["bare"] = True
                    ta = {k: a for k, a in enumerate(atts[ri]) if a is not None and vals[k] is not None}
                    if rp:
                        rows_p.setdefault(rp, {})
                        if cls not in rows_p[rp]:
                            rows_p[rp][cls] = rec_r
                            if ta:
                                tag_ctx_p[(rp, cls)] = ta
                    elif cls not in rows:
                        rows[cls] = rec_r
                        if ta:
                            tag_ctx[cls] = ta
                if len(rows_p) < 2:
                    # '당기말' etc. is only a period-end word of a single-period table, not a stacked table
                    for rp_, rr in rows_p.items():
                        for cls_, rec_r in rr.items():
                            if cls_ not in rows:
                                rows[cls_] = rec_r
                                if (rp_, cls_) in tag_ctx_p:
                                    tag_ctx[cls_] = tag_ctx_p[(rp_, cls_)]
                    rows_p = {}
                in_table_unit = unit_of(" ".join(r[0] for r in g[:min(h, 2)]))
                rec = {
                    "i": i, "pos": s_pos,
                    "note": scope_at(ms, s_pos), "top": scope_at(tops, s_pos),
                    "pre": (prev_small + " " + pre)[-200:],
                    "unit_cue": in_table_unit or prev_unit or unit_of(prev_small + " " + pre),
                    "nrows": len(g), "ncols": len(g[0]), "h": h, "nl": nl,
                    "hdr": hdrflat[:300],
                    "paths": paths, "roles": roles, "rows": rows,
                    "roles_loose": roles_loose, "open_rows": open_rows,
                    "period_cue": explicit_period(prev_small + " " + pre[-140:]),
                }
                if rows_p:
                    rec["rows_p"] = rows_p
                if tag_ctx:
                    # tag summary of the closing LIAB row (or NET if there is no LIAB row)
                    key = "LIAB" if "LIAB" in tag_ctx else ("NET" if "NET" in tag_ctx else next(iter(tag_ctx)))
                    scopes, periods, trole = set(), set(), {}
                    acodes = set()
                    for k, (ac, cx) in tag_ctx[key].items():
                        tok, sc, rl = tag_dims(cx)
                        scopes.add(sc)
                        periods.add(tag_period(tok))
                        trole[k] = rl
                        acodes.add(ac.split("_", 1)[-1][:60])
                    rec["tag"] = {"row": key, "scopes": sorted(x or "?" for x in scopes),
                                  "periods": sorted(x or "?" for x in periods),
                                  "roles": {str(k): v for k, v in trole.items()},
                                  "acodes": sorted(acodes)}
                out.append(rec)
            prev_small, prev_unit = "", None
        else:
            if ntr <= 3:
                sp = clean(t[max(last_end, s_pos - 1500):s_pos])[-200:]
                small_txt = clean(body)
                prev_small = sp + " " + small_txt[:200]
                prev_unit = unit_of(small_txt)
            else:
                prev_small, prev_unit = "", None
        last_end = m.end()
    return out


# --------------------------------------------------------------------------------------
# independent anchor: 보험계약부채 on the filing's own 재무상태표 (별도)
# --------------------------------------------------------------------------------------
_NUMBERING = re.compile(r"^(?:[IVXⅠⅡⅢⅣⅤⅥ]+|\d+|[가-힣])[\.\)]\s*")


def _bs_label(lab: str) -> str:
    lab = re.sub(r"\(주석[^)]*\)", "", lab)
    lab = re.sub(r"\(주\d*[^)]*\)", "", lab)
    return _NUMBERING.sub("", lab)


def filing_bs_anchor(path) -> list:
    """Every 재무상태표-like table of an XML that carries a 보험계약부채 line.  Returns one dict per
    table: {idx, scope ('sep'|'con'), unit, label_lines, value (원/천원/백만원 as printed), value_mm}.
    An exact '보험계약부채' line is used as is; without it the 보험계약부채 component lines (유배당/
    유배당외/변액 ...; 재보험계약부채 excluded) are summed.  The current-period column is located from
    the header (당 / 당기 / 당분기 / 당반기) so that a 주석번호 column is never read as a value."""
    t = read_xml(path)
    tops = [(m.start(), m.group(1).strip()) for m in TITLE_RE.finditer(t)]
    out = []
    prev_small, prev_unit, last_end = "", None, 0
    for i, m in enumerate(TAB_RE.finditer(t)):
        body = m.group(0)
        ntr = body.upper().count("<TR")
        pre = clean(t[max(last_end, m.start() - 600):m.start()])[-200:]
        last_end = m.end()
        if ntr <= 6:
            small_txt = clean(body)
            prev_small, prev_unit = small_txt[:200], unit_of(small_txt)
            continue
        flat = comp(clean(body))
        if not ("자산총계" in flat and "부채총계" in flat and "보험계약부채" in flat) or ntr < 14:
            prev_small, prev_unit = "", None
            continue
        g, _ = parse_table(body)
        # current-period column from the header rows
        ccur = None
        for pat in (r"\(당\)|당기|당분기|당반기", r"제\s*\d+\s*(?:기|분기|반기)"):
            for r in g[:4]:
                for k, c in enumerate(r):
                    if k >= 1 and re.search(pat, c) and "주석" not in c and "기초" not in c:
                        ccur = k
                        break
                if ccur is not None:
                    break
            if ccur is not None:
                break
        if ccur is None:
            for r in g:
                if comp(r[0]) in ("자산총계", "자산총계"):
                    for k, c in enumerate(r):
                        v_ = parse_num(c)
                        if k >= 1 and v_ is not None and abs(v_) >= 1000:
                            ccur = k
                            break
                    break
        total_line, parts = None, []
        for r in g:
            lab = _bs_label(comp(r[0]))
            if "보험계약부채" not in lab or lab.startswith("재보험"):
                continue
            if ccur is not None and ccur < len(r):
                v = parse_num(r[ccur])
            else:
                nums = [parse_num(c) for c in r[1:] if parse_num(c) is not None and c.strip() not in ("",)]
                v = nums[0] if nums else None
            if v is None:
                continue
            if lab == "보험계약부채":
                total_line = (lab, v)
            else:
                parts.append((lab, v))
        if total_line is not None:
            lines, val = [total_line], total_line[1]
        elif parts:
            lines, val = parts, sum(v for _, v in parts)
        else:
            continue
        unit = prev_unit or unit_of(prev_small + " " + pre + " " + " ".join(" ".join(r) for r in g[:3]))
        scope = scope_at(tops, m.start())
        out.append({"idx": i, "scope": "con" if "연결" in comp(scope) else "sep", "scope_title": scope[:40],
                    "unit": unit, "lines": [(a[:30], b) for a, b in lines], "value": val,
                    "value_mm": (val * UNIT_SCALE[unit]) if unit in UNIT_SCALE else None})
        prev_small, prev_unit = "", None
    return out


# --------------------------------------------------------------------------------------
# raw inventory
# --------------------------------------------------------------------------------------
def inventory(fy_dirs=None, codes=None):
    """-> list of dict(fy, code, dir, files=[path...], meta) in (fy, code) order.
    files are the XML(s) of one DART directory (main report first, 감사보고서 _00760/_00761 after)."""
    inv = []
    for fy in (fy_dirs or FY_DIRS):
        base = DART / fy / "raw"
        if not base.is_dir():
            continue
        for d in sorted(os.listdir(base)):
            p = base / d
            if not p.is_dir():
                continue
            code = d[:6]
            if codes and code not in codes:
                continue
            meta = {}
            mp = p / "meta.json"
            if mp.exists():
                with open(mp, encoding="utf-8") as fh:
                    meta = json.load(fh)
            top = sorted(glob.glob(str(p / "*.xml")))
            sub = sorted(glob.glob(str(p / "xml" / "*.xml")))
            seen_top = {(os.path.basename(f), os.path.getsize(f)) for f in top}
            files = top + [f for f in sub if (os.path.basename(f), os.path.getsize(f)) not in seen_top]
            inv.append({"fy": fy, "code": code, "dir": d, "files": [f.replace("\\", "/") for f in files], "meta": meta})
    return inv


# --------------------------------------------------------------------------------------
# table annotation: reinsurance / scope / period / unit
# --------------------------------------------------------------------------------------
def closing_rows(t: dict) -> dict:
    """closing-row records (cls -> {label, vals}) of the CURRENT period of a table; section-title rows
    without a single number are ignored"""
    rows = t["rows_p"].get("cur", {}) if t.get("rows_p") else t["rows"]
    return {c: r for c, r in rows.items() if any(v is not None for v in r["vals"])}


REINS_RE = re.compile(r"(?<![수원])재보험|출재")
UNIT_BOX = re.compile(r"\(\s*단위[^)]*(?:\)|$)")


GENERIC_BOTH = re.compile(r"(원수|수재|보험계약|발행한\s*보험계약)\s*(및|와|과|,)\s*(출재|재보험계약|재보험)|(출재|재보험계약|재보험)\s*(및|와|과)\s*(원수|수재)")
SUBCOUNT = re.compile(r"\(\d+\)|\d+\)")


def caption_of(pre: str) -> str:
    """The heading that directly captions the table.
    * text after the last '다음과 같습니다' (the generic section sentence before it can mention 재보험계약
      for every sub-table); when the caption sentence itself ends with '다음과 같습니다(단위:...)'
      the part before it is used;
    * generic headings naming the issued AND the ceded book together ('원수 및 출재') are dropped;
    * only the text after the last numeric sub-heading counter ('1)', '(2)') is kept."""
    txt = UNIT_BOX.sub(" ", pre or "")
    parts = re.split(r"다음과\s*같습니다\.?", txt)
    last = parts[-1].strip()
    if len(last) < 6 and len(parts) >= 2:
        cap = (parts[-2][-110:] + " " + last).strip()
    else:
        cap = last
    cap = GENERIC_BOTH.sub(" ", cap)
    ms = list(SUBCOUNT.finditer(cap))
    if ms:
        cap = cap[ms[-1].end():]
    return cap


def is_reins(t: dict) -> bool:
    """reinsurance HELD (출재/보유 재보험계약) table.  '수재보험'(assumed, part of the issued book) and
    '원수재 보험부채' do not count; the regex is applied to the RAW text (compaction would glue
    '원수재 보험' into '재보험')."""
    rows = closing_rows(t)
    if "RE" in rows and "LIAB" not in rows:
        return True
    if REINS_RE.search(t["note"]):
        return True
    tg = t.get("tag")
    if tg and any("Reinsurance" in a for a in tg["acodes"]):
        return True
    if REINS_RE.search(caption_of(t["pre"])):
        return True
    hdr = t["hdr"][:300]
    if "발행한보험계약" not in hdr and "보유재보험계약" in hdr:
        return True
    return False


def is_con(t: dict) -> bool:
    tg = t.get("tag")
    if tg:
        sc = [s for s in tg["scopes"] if s != "?"]
        if sc == ["con"]:
            return True
        if sc == ["sep"]:
            return False
    return ("연결" in t["note"]) or ("연결" in t["top"])


INTRO_RE = re.compile(r"다음과\s*같")


def _intro_is_reins(pre: str):
    """True/False when the text in front of the table holds an '... 다음과 같습니다' sentence and that sentence
    does / does not name the reinsurance book (재보험계약, 출재); None when there is no such sentence"""
    ms = list(INTRO_RE.finditer(pre or ""))
    if not ms:
        return None
    seg = GENERIC_BOTH.sub(" ", pre[:ms[-1].start()][-140:])
    return bool(REINS_RE.search(seg))


def _mark_reins_by_sentence(tabs: list) -> None:
    """repair 'reins_sentence': a table WITHOUT a 부채인/자산인 row (NET-only) that follows an introducing sentence
    naming the 재보험계약 (the sentence is carried over the headingless tables of the same run) is a held-reinsurance
    table.  The plain reading only inspects the caption AFTER the sentence and misses it."""
    carry = None
    for t in tabs:
        v = _intro_is_reins(t["pre"])
        if v is not None:
            carry = v
        rows = closing_rows(t)
        if carry and "LIAB" not in rows and "ASSET" not in rows:
            t["reins"] = True
            t["reins_src"] = "sentence"


def _table_totals(t: dict, which: str) -> dict:
    """{class: total column value} of the opening ('open') or closing ('close') rows of the table, in its own unit"""
    rows = closing_rows(t) if which == "close" else (t.get("open_rows") or {})
    return {c: _roles_sum(t, r["vals"])["tot"] for c, r in rows.items()}


def _chains(oa: dict, cb: dict) -> bool:
    """opening balances of table A == closing balances of table B (B is A's prior-year table): every class present in
    both with a non-trivial value agrees within rounding, and at least one of them is >= 1000 (own unit)"""
    common = [c for c in ("NET", "LIAB", "ASSET") if c in oa and c in cb]
    live = [c for c in common if max(abs(oa[c]), abs(cb[c])) >= 1.0]
    if not any(max(abs(oa[c]), abs(cb[c])) >= 1000.0 for c in live):
        return False
    return all(abs(oa[c] - cb[c]) <= max(2.0, 2e-6 * abs(cb[c])) for c in live)


def _apply_continuity(tabs: list) -> None:
    """repair 'continuity' (year-end filings): a roll-forward runs 1 Jan -> 31 Dec, so the CURRENT-year table opens with
    the balances the PRIOR-year table closed with.  Where table A opens with what table B closed with (A and B in the
    same unit, the match unique both ways), A is 'cur' and B is 'prior' -- whatever the captions say (a footnote that
    mentions '전기말' must not turn a whole section into prior-period tables)."""
    cand = [t for t in tabs if not t["reins"] and not t["con"] and t["kind"] == "RF" and not t.get("rows_p")]
    op = {t["i"]: _table_totals(t, "open") for t in cand}
    cl = {t["i"]: _table_totals(t, "close") for t in cand}
    prior_of, claimed = {}, {}
    for a in cand:
        hits = [b for b in cand if b["i"] != a["i"] and b["unit"] == a["unit"] and _chains(op[a["i"]], cl[b["i"]])]
        if len(hits) == 1:
            prior_of[a["i"]] = hits[0]["i"]
            claimed.setdefault(hits[0]["i"], []).append(a["i"])
    for a_i, b_i in prior_of.items():
        if len(claimed[b_i]) != 1:
            continue                          # B closes into several A's: ambiguous, leave as is
        for t in tabs:
            if t["i"] == a_i:
                t["period"], t["period_src"] = "cur", "continuity"
            elif t["i"] == b_i:
                t["period"], t["period_src"] = "prior", "continuity"


def annotate_tables(tabs: list, repair=frozenset()) -> list:
    """period (cur/prior), unit, reinsurance, scope and kind per table, in document order.
    period: tag > explicit cue in the table caption > carried cue (same note) > headingless second-of-a-pair > cur.
    Tables that stack 당기 and 전기 row blocks (rows_p) are 'cur' and read from their cur block.
    repair (assemble_cell only, after the plain reading failed to close the cell): any of 'loose_roles',
    'reins_sentence', 'continuity' -- see role_of(loose=True), _mark_reins_by_sentence, _apply_continuity."""
    out = []
    last_note, prev, expl, last_unit = None, None, None, None
    for t in tabs:
        t = dict(t)
        if t["note"] != last_note:
            prev, expl, last_unit, last_note = None, None, None, t["note"]
        cue = explicit_period(caption_of(t["pre"]))
        shape = (t["nrows"], t["ncols"])
        tg = t.get("tag")
        tgp = [p for p in tg["periods"] if p != "?"] if tg else []
        heading = re.sub(r"[\s\-\.\(\)]+", "", UNIT_BOX.sub(" ", t["pre"]))
        if t.get("rows_p"):
            p, src = "cur", "rows_p"
        elif len(tgp) == 1:
            p, src = tgp[0], "tag"
            expl = p
        elif cue is not None:
            p, src = cue, "cue"
            expl = p
        elif expl is not None:
            p, src = expl, "carry_marker"
        elif prev is not None and prev[0] == shape and len(heading) < 3:
            p, src = ("prior" if prev[1] == "cur" else "cur"), "pair"
        else:
            p, src = "cur", "default"
        t["period"], t["period_src"] = p, src
        prev = (shape, p)
        u = t["unit_cue"]
        if u:
            last_unit = u
            t["unit"], t["unit_src"] = u, "cue"
        elif last_unit:
            t["unit"], t["unit_src"] = last_unit, "carry"
        else:
            t["unit"], t["unit_src"] = None, "none"
        t["reins"] = is_reins(t)
        t["con"] = is_con(t)
        t["kind"] = "ME" if "CSM" in t["roles"] else "RF"
        out.append(t)
    if "loose_roles" in repair:
        for t in out:
            t["roles"] = list(t.get("roles_loose") or t["roles"])
            t["kind"] = "ME" if "CSM" in t["roles"] else "RF"
    if "reins_sentence" in repair:
        _mark_reins_by_sentence(out)
    if "continuity" in repair:
        _apply_continuity(out)
    return out


# --------------------------------------------------------------------------------------
# aggregation of one table / one cell
# --------------------------------------------------------------------------------------
def _roles_sum(t: dict, vals) -> dict:
    s = {"LRC": 0.0, "LC": 0.0, "LIC_BEL": 0.0, "LIC_RA": 0.0, "LIC_TOT": 0.0, "TOT": 0.0,
         "SUB": 0.0, "CSM": 0.0, "BEL_LRC": 0.0, "RA_LRC": 0.0}
    n = {k: 0 for k in s}
    for c, role in enumerate(t["roles"]):
        if role is None or c >= len(vals) or vals[c] is None:
            continue
        s[role] += vals[c]
        n[role] += 1
    if t.get("kind") == "ME":
        role_sum = s["LIC_BEL"] + s["LIC_RA"] + s["BEL_LRC"] + s["RA_LRC"] + s["CSM"]
    else:
        role_sum = s["LRC"] + s["LC"] + s["LIC_BEL"] + s["LIC_RA"] + s["LIC_TOT"]
    has_tot = n["TOT"] > 0
    return {"lrc": s["LRC"], "lc": s["LC"], "bel": s["LIC_BEL"], "ra": s["LIC_RA"], "lt": s["LIC_TOT"],
            "tot": s["TOT"] if has_tot else role_sum, "role_sum": role_sum, "has_tot": has_tot,
            "csm": s["CSM"], "bel_lrc": s["BEL_LRC"], "ra_lrc": s["RA_LRC"], "ncol": n}


def agg_table(t: dict):
    """Closing-balance aggregate of one table, in the table's own unit.

    The LIABILITY row ('부채인 보험계약' / '...말 보험계약부채') is used.  A LIAB row that was found only by
    its bare label ('보험계약부채' after a closing-section row) must also be consistent with the NET row
    (NET = LIAB +- ASSET on the total); otherwise (e.g. a pre-계약이전 sub-block followed by a
    transfer-out row) the NET row is used.  net_lrc / net_tot are the NET-row
    figures (after offsetting 보험계약자산), kept for the 2-4 cross-check.  -> dict or None"""
    rows = closing_rows(t)
    liab, net, asset = rows.get("LIAB"), rows.get("NET"), rows.get("ASSET")
    if liab is None and net is None:
        return None
    flags = []
    use = "LIAB" if liab else "NET"
    sums = _roles_sum(t, rows[use]["vals"])
    nsums = _roles_sum(t, net["vals"]) if net else None
    if liab and net and asset and liab.get("bare"):
        asums = _roles_sum(t, asset["vals"])
        d1 = nsums["tot"] - (sums["tot"] + asums["tot"])
        d2 = nsums["tot"] - (sums["tot"] - asums["tot"])
        tol = max(3.0, 2e-4 * abs(nsums["tot"]))
        if abs(d1) > tol and abs(d2) > tol:
            # LIAB row does not belong to the closing NET row
            flags.append("liab_row_inconsistent_with_net")
            use, sums = "NET", nsums
    # net-of-asset LRC for the 2-4 cross-check: the NET row if the table has a numeric one; otherwise the liability
    # LRC adjusted by the ASSET row.  The sign convention of the ASSET row differs between filers (NET = LIAB - ASSET
    # when assets are printed positive, NET = LIAB + ASSET when printed negative), so both candidates are kept.
    liab_lrc = sums["lrc"] + sums["lc"] if use == "LIAB" else None
    alt = None
    if nsums:
        net_lrc, net_tot = nsums["lrc"] + nsums["lc"], nsums["tot"]
    elif liab and asset:
        asums = _roles_sum(t, asset["vals"])
        a_lrc = asums["lrc"] + asums["lc"]
        if abs(a_lrc) > 1e-9:
            net_lrc, alt = liab_lrc - a_lrc, liab_lrc + a_lrc
        else:
            net_lrc = liab_lrc
        net_tot = sums["tot"]
    else:
        net_lrc, net_tot = sums["lrc"] + sums["lc"], sums["tot"]
    out = {"basis": use, "lrc": sums["lrc"], "lc": sums["lc"], "bel": sums["bel"], "ra": sums["ra"],
           "lt": sums["lt"], "tot": sums["tot"], "role_sum": sums["role_sum"], "has_tot": sums["has_tot"],
           "csm": sums["csm"], "bel_lrc": sums["bel_lrc"], "ra_lrc": sums["ra_lrc"], "ncol": sums["ncol"],
           "net_lrc": net_lrc, "net_lrc_alt": alt if alt is not None else net_lrc, "net_has_alt": alt is not None,
           "net_tot": net_tot, "flags": flags}
    return out


NUM_KEYS = ("lrc", "lc", "bel", "ra", "lt", "tot", "role_sum", "csm", "bel_lrc", "ra_lrc", "net_lrc", "net_lrc_alt", "net_tot")


def scaled(a: dict, k: float) -> dict:
    out = dict(a)
    for x in NUM_KEYS:
        out[x] = a[x] * k
    return out


def reduce_tables(aggs, tol_abs=3.0, tol_rel=2e-6, min_equal=1000.0):
    """De-duplicate the closing totals of the eligible tables of one cell (aggs are in 백만원).

    1. equal tables: two tables with the same total (>= min_equal 백만원) or the identical column
       vector are alternative cuts of the same book (e.g. 상품라인별 vs 배당유무별) -> keep the first.
    2. parent/children: a table whose total equals the sum of a contiguous run (>= 2) of neighbouring
       tables is the PARENT of that run (a '전체' table followed by 유배당/무배당/변액 parts) -> keep the
       parent, drop the run.  Largest totals first so nesting resolves top-down.

    Pure arithmetic on the closing totals; the outcome is later verified against IFRS17_BS item 20
    and every dropped table is recorded in the provenance.  -> (keep_flags, notes)"""
    n = len(aggs)
    totals = [a["tot"] for a in aggs]
    keep = [True] * n
    notes = []

    def vec(a):
        return tuple(round(a[k], 3) for k in ("lrc", "lc", "bel", "ra", "lt", "tot"))

    for i in range(n):
        if not keep[i] or abs(totals[i]) < 1e-9:
            continue
        for j in range(i + 1, n):
            if not keep[j]:
                continue
            same_vec = vec(aggs[i]) == vec(aggs[j])
            same_tot = abs(totals[i]) >= min_equal and abs(totals[j] - totals[i]) <= max(tol_abs, tol_rel * abs(totals[i]))
            if same_vec or same_tot:
                keep[j] = False
                notes.append(("equal", i, [j]))
    order = sorted(range(n), key=lambda i: -abs(totals[i]))
    for i in order:
        if not keep[i] or abs(totals[i]) < 1e-9:
            continue
        for direction in (1, -1):
            found = None
            for length in range(2, n):
                lo, hi = (i + 1, i + 1 + length) if direction == 1 else (i - length, i)
                if lo < 0 or hi > n:
                    break
                run = list(range(lo, hi))
                if not all(keep[j] for j in run):
                    break
                ssum = sum(totals[j] for j in run)
                if abs(ssum - totals[i]) <= max(tol_abs, tol_rel * abs(totals[i])):
                    found = run
                    break
            if found:
                for j in found:
                    keep[j] = False
                notes.append(("parent", i, found))
                break
    return keep, notes


# --------------------------------------------------------------------------------------
# cell assembly: (company, quarter) -> items, checks, provenance
# --------------------------------------------------------------------------------------
TOL_CLOSE = 0.001            # R-LIC1: item 15 within +-0.1 % of IFRS17_BS item 20
POWERS = (1e3, 1e-3, 1e6, 1e-6)
UNIT_CANDIDATES = (1e-6, 1e-3, 1.0)   # 원 / 천원 / 백만원 -> 백만원
UNIT_NAME = {1e-6: "원", 1e-3: "천원", 1.0: "백만원"}


def file_priority(fn: str):
    b = os.path.basename(fn)
    return (1 if "_00760" in b else (2 if "_00761" in b else 0), fn)


def eligible_tables(tabs: list, kind: str = "RF") -> list:
    """separate-statement, current-period, insurance-contracts-issued tables with a closing balance row"""
    out = []
    for t in tabs:
        if t["kind"] != kind or t["reins"] or t["con"] or t["period"] != "cur":
            continue
        if "위험관리" in t["note"]:
            continue
        rows = closing_rows(t)
        if "LIAB" not in rows and "NET" not in rows:
            continue
        out.append(t)
    return out


def tag_crosscheck(t: dict):
    """XBRL member of every numeric cell of the closing row vs the role derived from the header text"""
    tg = t.get("tag")
    if not tg:
        return None
    n = bad = 0
    cols = []
    for k_str, trole in tg["roles"].items():
        k = int(k_str)
        hrole = t["roles"][k] if k < len(t["roles"]) else None
        tr = "SUB" if trole == "LRC_GROUP" else trole
        if tr.startswith("OTHER:"):
            continue
        n += 1
        if hrole != tr:
            bad += 1
            if len(cols) < 5:
                cols.append((k, hrole, tr))
    return {"cells": n, "mismatch": bad, "cols": cols}


def _evaluate(rows_t: list, kvals: list, floor_neg: bool = False):
    """scale every table to 백만원, apply the net-asset floor, de-duplicate
    -> (aggs, keep, floor, notes, total).  floor_neg (repair 'floor_neg'): a table whose liability-basis total is
    negative (the filer printed the net ASSET in the liability row, e.g. 카카오페이 일반모형 계약) counts 0 as well"""
    aggs = [scaled(r["a"], k) for r, k in zip(rows_t, kvals)]
    floor = [a["basis"] == "NET" and a["tot"] < -1e-9 for a in aggs]
    if floor_neg:
        floor = [f or a["tot"] < -1e-9 for f, a in zip(floor, aggs)]
    idx = [i for i, f in enumerate(floor) if not f]
    keep_sub, notes = reduce_tables([aggs[i] for i in idx]) if idx else ([], [])
    keep = [False] * len(aggs)
    for j, i in enumerate(idx):
        keep[i] = keep_sub[j]
    notes_m = [(kind, idx[a_], [idx[b_] for b_ in run]) for kind, a_, run in notes]
    total = sum(a["tot"] for a, kp in zip(aggs, keep) if kp)
    return aggs, keep, floor, notes_m, total


def _close(a, b, tol=TOL_CLOSE):
    """a within +-tol of b (b == 0: both are zero up to 1 백만원)"""
    if b is None:
        return False
    if b == 0:
        return abs(a) <= 1.0
    return abs(a / b - 1.0) <= tol


def _me_split(ann: list, k_default: float, lic_tot: float):
    """LIC BEL / RA from the measurement-element tables (BEL x LRC/LIC, RA x LRC/LIC, CSM) of the same
    filing -- only for filers whose roll-forward table shows LIC as one column.  Accepted when
    BEL + RA of the LIC equals the roll-forward LIC total."""
    el = eligible_tables(ann, "ME")
    rows = []
    for t in el:
        a = agg_table(t)
        if a is None:
            continue
        k = UNIT_SCALE.get(t["unit"], k_default)
        rows.append({"t": t, "a": a, "k": k})
    if not rows:
        return None
    aggs, keep, floor, notes, _ = _evaluate(rows, [r["k"] for r in rows])
    kept = [i for i, kp in enumerate(keep) if kp]
    bel = sum(aggs[i]["bel"] for i in kept)
    ra = sum(aggs[i]["ra"] for i in kept)
    ok = abs(bel + ra - lic_tot) <= max(3.0, 1e-6 * abs(lic_tot))
    return {"bel": bel, "ra": ra, "ok": ok, "tables": [rows[i]["t"]["i"] for i in kept],
            "gap_mm": bel + ra - lic_tot}


def _assemble_cell(code: str, fy: str, files: list, bs20_mm, filing_anchor_mm, repair=frozenset()):
    """files = [(relpath, harvested tabs)] of one DART directory.  Returns the cell record.
    status: loaded | not_loaded.  Every decision is recorded in rec['flags'] / rec['tables'].
    repair: frozenset of repair names (see REPAIR_ORDER); empty = the plain reading used for every stage-1 cell."""
    quarter = QMAP[fy]
    fneg = "floor_neg" in repair
    rec = {"code": code, "fy": fy, "quarter": quarter, "status": "not_loaded", "reason": None,
           "flags": [], "bs20_mm": bs20_mm, "filing_anchor_mm": filing_anchor_mm}
    used = None
    for fn, tabs in sorted(files, key=lambda x: file_priority(x[0])):
        ann = annotate_tables(tabs or [], repair)
        el = eligible_tables(ann, "RF")
        if el:
            used = (fn, ann, el)
            break
    if used is None:
        rec["reason"] = "no separate/current LRC-LIC roll-forward table in any file"
        return rec
    fn, ann, el = used
    rec["file"] = fn
    rows_t = []
    for t in el:
        a = agg_table(t)
        if a is not None:
            rows_t.append({"t": t, "a": a, "k": UNIT_SCALE.get(t["unit"])})
    if not rows_t:
        rec["reason"] = "no closing row"
        return rec
    anchor = bs20_mm if bs20_mm is not None else filing_anchor_mm
    anchor_name = "BS20" if bs20_mm is not None else ("filing_BS" if filing_anchor_mm is not None else None)

    # ---- scale resolution: explicit/carried cue first, anchor only to fill or to contradict ----
    unit_source = "cue"
    unknown = [i for i, r in enumerate(rows_t) if r["k"] is None]
    kvals = [r["k"] if r["k"] is not None else 1.0 for r in rows_t]
    if unknown:
        if anchor is None:
            rec["reason"] = "unit cue missing and no anchor (BS item 20 / filing balance sheet) to infer it"
            return rec
        hits = []
        for cand in UNIT_CANDIDATES:
            kv = [r["k"] if r["k"] is not None else cand for r in rows_t]
            if _close(_evaluate(rows_t, kv, fneg)[4], anchor):
                hits.append((cand, kv))
        if len(hits) != 1:
            rec["reason"] = f"unit cue missing; {len(hits)} candidate scales close to {anchor_name}"
            return rec
        kvals = hits[0][1]
        unit_source = f"inferred_from_{anchor_name}"
        rec["flags"].append("unit_inferred:" + UNIT_NAME[hits[0][0]])
    aggs, keep, floor, notes, total = _evaluate(rows_t, kvals, fneg)
    if anchor and not _close(total, anchor):
        for pw in POWERS:      # a wrong unit cue shows up as an exact power-of-ten ratio
            if _close(total / pw, anchor):
                kvals = [k / pw for k in kvals]
                aggs, keep, floor, notes, total = _evaluate(rows_t, kvals, fneg)
                unit_source = f"inferred_from_{anchor_name}(cue contradicted x{pw:g})"
                rec["flags"].append("unit_cue_contradicted")
                break
    rec["unit_source"] = unit_source
    units = sorted({UNIT_NAME.get(round(k, 9) if k != 1.0 else 1.0, "?") for k, kp in zip(kvals, keep) if kp})
    rec["unit"] = "/".join(units)

    # ---- items (백만원) ----------------------------------------------------------------
    kept = [i for i, kp in enumerate(keep) if kp]
    lrc_tot = sum(aggs[i]["lrc"] + aggs[i]["lc"] for i in kept)
    lic_tot = 0.0
    for i in kept:
        a = aggs[i]
        lic_tot += (a["tot"] - a["lrc"] - a["lc"]) if a["has_tot"] else (a["bel"] + a["ra"] + a["lt"])
    tot = sum(aggs[i]["tot"] for i in kept)
    bel = sum(aggs[i]["bel"] for i in kept)
    ra = sum(aggs[i]["ra"] for i in kept)
    lt = sum(aggs[i]["lt"] for i in kept)
    split_cols = sum(aggs[i]["ncol"]["LIC_BEL"] + aggs[i]["ncol"]["LIC_RA"] for i in kept)
    single_cols = sum(aggs[i]["ncol"]["LIC_TOT"] for i in kept)
    if split_cols and single_cols and abs(lt) > 1e-9:
        klass = "A2"
    elif split_cols:
        klass = "A1"
    elif single_cols:
        klass = "T"
    else:
        klass = "N"
    bel_ra_source = "RF" if split_cols else "none"
    if klass == "T":
        me = _me_split(ann, kvals[0], lic_tot)
        if me is not None:
            rec["me_split"] = me
            if me["ok"]:
                bel, ra, lt = me["bel"], me["ra"], 0.0
                klass, bel_ra_source = "A1", "ME"
                rec["flags"].append("bel_ra_from_measurement_tables")
            else:
                rec["flags"].append("me_split_disagrees_with_roll_forward")
    net_lrc = sum(aggs[i]["net_lrc"] for i in range(len(aggs)) if keep[i] or floor[i])
    net_alt = None
    if any(aggs[i]["net_has_alt"] for i in range(len(aggs)) if keep[i] or floor[i]):
        net_alt = sum(aggs[i]["net_lrc_alt"] for i in range(len(aggs)) if keep[i] or floor[i])
    row_basis = sorted({aggs[i]["basis"] for i in kept})
    if any(floor):
        rec["flags"].append("net_asset_tables_floored:" + ",".join(f"T{rows_t[i]['t']['i']}" for i, f in enumerate(floor) if f))
    rec.update({
        "class": klass, "bel_ra_source": bel_ra_source, "row_basis": row_basis,
        "items_mm": {"lic_total": lic_tot, "bel": bel, "ra": ra, "single": lt,
                     "lrc_total": lrc_tot, "total": tot},
        "net_lrc_mm": net_lrc, "net_lrc_alt_mm": net_alt, "n_tables": len(rows_t), "n_kept": len(kept),
        "ratio_bs20": (tot / bs20_mm) if bs20_mm else None,
        "ratio_filing": (tot / filing_anchor_mm) if filing_anchor_mm else None,
        "dedupe": [(k_, rows_t[a_]["t"]["i"], [rows_t[b_]["t"]["i"] for b_ in run]) for k_, a_, run in notes],
    })
    rec["tables"] = []
    for i, r in enumerate(rows_t):
        t, a = r["t"], aggs[i]
        rec["tables"].append({
            "i": t["i"], "note": t["note"][:40], "unit": t["unit"], "unit_src": t["unit_src"],
            "period_src": t["period_src"], "row_basis": a["basis"], "kept": bool(keep[i]), "floored": bool(floor[i]),
            "tot_mm": a["tot"], "lrc_mm": a["lrc"] + a["lc"], "bel_mm": a["bel"], "ra_mm": a["ra"], "single_mm": a["lt"],
            "has_tot": a["has_tot"], "gap_mm": (a["tot"] - a["role_sum"]) if a["has_tot"] else 0.0,
            "tag": tag_crosscheck(t), "flags": list(a["flags"]),
        })

    # ---- checks and decision ------------------------------------------------------------
    tol3 = max(3.0, 1e-6 * abs(lic_tot))
    split_sum = bel + ra + lt
    rec["r_lic3_gap_mm"] = split_sum - lic_tot
    bad_gap = [x for x in rec["tables"] if x["kept"] and abs(x["gap_mm"]) > max(3.0, 1e-6 * abs(x["tot_mm"]))]
    if bad_gap:
        rec["flags"].append("table_total_vs_columns_gap:" + ",".join(f"T{x['i']}" for x in bad_gap))
    if any(x["flags"] for x in rec["tables"] if x["kept"]):
        rec["flags"].append("liab_row_inconsistent_with_net")
    if klass == "N":
        rec["reason"] = "no LIC column recognised"
        return rec
    if anchor is None:
        rec["reason"] = "no anchor (BS item 20 / filing balance sheet) to verify the total"
        return rec
    ok_total = _close(tot, anchor)
    ok_split = abs(rec["r_lic3_gap_mm"]) <= tol3
    if ok_total and ok_split:
        rec["status"], rec["basis"] = "loaded", "liability"
        rec["r_lic1"] = "pass" if bs20_mm is not None else "pass_filing_anchor"
    elif row_basis == ["NET"] and anchor and 0.90 <= tot / anchor < 1.0 and ok_split:
        rec["status"], rec["basis"] = "loaded", "net"
        rec["r_lic1"] = "net_basis_below_anchor"
        rec["flags"].append("net_basis_only_table_rows")
    else:
        rec["reason"] = (f"R-LIC1 fail vs {anchor_name}: ratio {(tot / anchor) if anchor else float('inf'):.4f}" if not ok_total
                         else f"R-LIC3 fail: columns {split_sum:,.1f} vs total {lic_tot:,.1f}")
    return rec


# --------------------------------------------------------------------------------------
# filing balance-sheet anchor choice, per-cell exclusion rules
# --------------------------------------------------------------------------------------
def pick_filing_anchor(anchors_by_file: list):
    """anchors_by_file = [(filename, [anchor dicts from filing_bs_anchor])] -> value_mm or None.
    Separate-scope statements only.  A table is the primary 재무상태표 when its section title names the
    statement (4-1. 재무상태표 / (첨부)재 무 제 표) and is neither a 요약재무정보 nor a 연결 table; the
    2026.2Q filings carry no section titles at all -- then the last separate-scope table (the 별도
    재무상태표 follows the summaries in document order) is used."""
    untitled = []
    for fn, anchors in sorted(anchors_by_file, key=lambda x: file_priority(x[0])):
        for a in anchors:
            if a.get("value_mm") is None or a.get("scope") != "sep":
                continue
            title = comp(a.get("scope_title", ""))
            if not title:
                untitled.append(a["value_mm"])
                continue
            if "요약" in title or "연결" in title:
                continue
            if "재무상태표" in title or "재무제표" in title:
                return a["value_mm"]
    return untitled[-1] if untitled else None


# (company, quarter) -> reason.  Recorded exclusions: the number is NOT wrong, but it would be
# misleading next to the other masters, so the cell is left empty and the reason is reported.
NOT_LOADED_RULES = {
    ("KR0004", "2025.4Q"): "계약이전(2025-09-03) 뒤라 DART 감사보고서의 2025.12.31 보험계약부채는 0(전기말 4.18조)이다. "
                           "같은 마스터의 경영공시 2-4(item 8)는 이전 전 범위이고 BS 마스터에는 2025.4Q 항목 20 이 없어, "
                           "0 을 적재하면 한 마스터 안에서 범위가 어긋난다 (perimeter break)",
}


# Repairs are tried ONLY for a cell the plain reading could not close (so every stage-1 cell is untouched), smallest
# combination first; the first combination that closes item 15 against the anchor on the LIABILITY basis (and passes
# R-LIC3) wins and is recorded in rec['repair'] / rec['flags'].  Each one fixes a documented, content-based defect:
#   loose_roles     header variants: a BEL/RA leaf under a blank 발생사고 group cell; a 발생사고 column headed by the model name
#   continuity      current/prior tables paired by roll-forward continuity (opening == last year's closing), not captions
#   reins_sentence  NET-only tables introduced by a sentence naming the 재보험계약 are held-reinsurance tables
#   floor_neg       a table whose liability row is negative is a net asset (counts 0 on the liability side)
REPAIR_ORDER = ("loose_roles", "continuity", "reins_sentence", "floor_neg")


def assemble_cell(code: str, fy: str, files: list, bs20_mm, filing_anchor_mm):
    """_assemble_cell + the repair ladder (REPAIR_ORDER) for cells the plain reading could not close
    + the recorded per-cell exclusion rules (NOT_LOADED_RULES)."""
    import itertools
    rec = _assemble_cell(code, fy, files, bs20_mm, filing_anchor_mm)
    if rec["status"] != "loaded" and (code, rec["quarter"]) not in NOT_LOADED_RULES:
        plain_reason = rec["reason"]
        done = False
        for n in range(1, len(REPAIR_ORDER) + 1):
            for combo in itertools.combinations(REPAIR_ORDER, n):
                r2 = _assemble_cell(code, fy, files, bs20_mm, filing_anchor_mm, frozenset(combo))
                if r2["status"] == "loaded" and r2.get("basis") == "liability":
                    r2["repair"] = list(combo)
                    r2["flags"].append("repair:" + "+".join(combo))
                    r2["plain_reason"] = plain_reason
                    rec, done = r2, True
                    break
            if done:
                break
    why = NOT_LOADED_RULES.get((code, rec["quarter"]))
    if why and rec["status"] == "loaded":
        rec["withheld_items_mm"] = rec.get("items_mm")
        rec["status"], rec["reason"] = "not_loaded", why
    return rec


# --------------------------------------------------------------------------------------
# build all cells
# --------------------------------------------------------------------------------------
def load_bs20() -> dict:
    """{(code, quarter): 백만원} from IFRS17_BS.json item 20 (보험계약부채, 별도)"""
    with open(IFRS17_BS, encoding="utf-8") as f:
        rows = json.load(f)
    return {(r["원보험사코드"], r["공시분기"]): r["값"] for r in rows if r["항목번호"] == 20}


def build_all(codes=None, fys=None, verbose=True):
    """harvest every raw XML, assemble every (company, quarter) cell -> list of records"""
    bs20 = load_bs20()
    by_cell = {}
    t0 = time.time()
    for e in inventory(fys, codes):
        for f in e["files"]:
            if not os.path.isfile(f):
                continue
            rel = f.split("/raw/", 1)[-1]
            tabs = harvest_file(f)
            anchors = filing_bs_anchor(f)
            by_cell.setdefault((e["fy"], e["code"]), {"files": [], "anchors": [], "meta": {}, "dirs": {}})
            c = by_cell[(e["fy"], e["code"])]
            c["files"].append((rel, tabs))
            c["anchors"].append((rel, anchors))
            c["dirs"][rel] = e["meta"]
        if not e["files"]:
            by_cell.setdefault((e["fy"], e["code"]), {"files": [], "anchors": [], "meta": e["meta"], "dirs": {}})
    recs = []
    for (fy, code), c in sorted(by_cell.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        q = QMAP[fy]
        if not c["files"]:
            continue          # no_filing directory: source-absent cell, no row
        fa = pick_filing_anchor(c["anchors"])
        rec = assemble_cell(code, fy, c["files"], bs20.get((code, q)), fa)
        meta = c["dirs"].get(rec.get("file", ""), {})
        rec["meta"] = {k: meta.get(k) for k in ("rcept_no", "report_kind", "corp_code") if meta.get(k)}
        recs.append(rec)
    if verbose:
        print(f"harvested+assembled {len(recs)} cells in {time.time() - t0:.0f}s", file=sys.stderr)
    return recs


# --------------------------------------------------------------------------------------
# ILP rows
# --------------------------------------------------------------------------------------
def eok(mm: float) -> float:
    """백만원 -> 억원, two decimals (no precision loss for 백만원 integers); never -0.0"""
    return round(mm / 100.0, 2) + 0.0


def cell_item_values(rec: dict) -> dict:
    """{item_no: 억원} written for one loaded cell (stage 1: items 10..15)"""
    it = rec["items_mm"]
    out = {10: eok(it["lic_total"]), 14: eok(it["lrc_total"]), 15: eok(it["total"])}
    if rec["class"] in ("A1", "A2"):
        out[11], out[12], out[13] = eok(it["bel"]), eok(it["ra"]), eok(it["single"])
    else:                                    # class T: LIC disclosed in one column only
        out[13] = eok(it["single"])
    return dict(sorted(out.items()))


def ilp_registry(rows: list) -> dict:
    reg = {}
    for r in rows:
        reg.setdefault(r["원보험사코드"], {"원수사명": r["원수사명"], "티커": r["티커"], "생손보여부": r["생손보여부"]})
    return reg


def new_ilp_rows(recs: list, reg: dict) -> list:
    rows = []
    for rec in sorted((r for r in recs if r["status"] == "loaded"), key=lambda r: (r["code"], r["quarter"])):
        info = reg[rec["code"]]
        for n, v in cell_item_values(rec).items():
            name, section, level = ITEM_CATALOG[n]
            rows.append({"원보험사코드": rec["code"], "원수사명": info["원수사명"], "티커": info["티커"],
                         "생손보여부": info["생손보여부"], "항목번호": n, "항목명": name, "섹션": section,
                         "레벨": level, "공시분기": rec["quarter"], "값": v})
    return rows


def _dump_ilp(rows: list, crlf: bool) -> str:
    out = json.dumps(rows, indent=2, ensure_ascii=False)
    return out.replace("\n", "\r\n") if crlf else out


def merge_into_ilp(new_rows: list, path: Path = ILP, tag: str = "pre_lic") -> Path:
    """Append-only, guarded insert (same discipline as the earlier ilp merge): abort when ANY key
    (company, quarter, item) already exists, back the file up first, refuse to rewrite a file that
    does not round-trip byte for byte, and re-check that the file did not change while we worked.
    Existing rows are never touched.  -> backup path"""
    raw0 = path.read_bytes()
    txt = raw0.decode("utf-8")
    crlf = "\r\n" in txt
    rows = json.loads(txt)
    if _dump_ilp(rows, crlf) != txt:
        raise SystemExit(f"abort: {path.name} does not round-trip byte-for-byte; refusing to rewrite it")
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows}
    clash = sorted((r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in new_rows
                   if (r["원보험사코드"], r["공시분기"], r["항목번호"]) in have)
    if clash:
        raise SystemExit(f"abort: {len(clash)} key(s) already exist in {path.name}, e.g. {clash[:3]}")
    dup = len(new_rows) - len({(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in new_rows})
    if dup:
        raise SystemExit(f"abort: {dup} duplicate key(s) inside the new rows")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    backup = BACKUP_DIR / f"ilp_backup_{stamp}_{tag}.json"
    k = 2
    while backup.exists():
        backup = BACKUP_DIR / f"ilp_backup_{stamp}_{tag}_{k}.json"
        k += 1
    shutil.copyfile(path, backup)
    if hashlib.sha256(backup.read_bytes()).hexdigest() != hashlib.sha256(raw0).hexdigest():
        raise SystemExit("abort: backup does not match the source file")
    out_txt = _dump_ilp(rows + new_rows, crlf)
    if path.read_bytes() != raw0:
        raise SystemExit(f"abort: {path.name} changed while the merge was prepared")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(out_txt.encode("utf-8"))
    os.replace(tmp, path)
    after = json.loads(path.read_text(encoding="utf-8"))
    if after[:len(rows)] != rows or after[len(rows):] != new_rows:
        raise SystemExit("post-write verification FAILED -- restore from " + str(backup))
    return backup


# --------------------------------------------------------------------------------------
# provenance sidecar
# --------------------------------------------------------------------------------------
def as_of_date(quarter: str) -> str:
    return f"{quarter[:4]}-{QUARTER_END[quarter[5:]]}"


def bs20_snapshot_sha256() -> str:
    """sha256 over the sorted (company, quarter, value) of IFRS17_BS item 20 -- the anchor R-LIC1 was run against"""
    items = sorted((k[0], k[1], repr(v)) for k, v in load_bs20().items())
    return hashlib.sha256(json.dumps(items, ensure_ascii=False).encode("utf-8")).hexdigest()


def build_provenance(recs: list, generated_at: str) -> dict:
    cells, absent = [], []
    for rec in recs:
        if rec["status"] != "loaded":
            absent.append({"company_code": rec["code"], "quarter": rec["quarter"], "reason": rec["reason"]})
            continue
        kept = [t for t in rec["tables"] if t["kept"]]
        tg_t = [t["tag"] for t in rec["tables"] if t["kept"] and t.get("tag")]
        cells.append({
            "company_code": rec["code"], "quarter": rec["quarter"], "item_block": "lic_dart_note",
            "source_id": "DART", "as_of_date": as_of_date(rec["quarter"]),
            "source_file": f"data/dart/{rec['fy']}/raw/{rec['file']}",
            **rec.get("meta", {}),
            "scope": "separate", "period": "current", "class": rec["class"], "bel_ra_source": rec["bel_ra_source"],
            "basis": rec["basis"], "row_basis": rec["row_basis"], "unit": rec["unit"], "unit_source": rec["unit_source"],
            "tables": [{"table": t["i"], "note": t["note"], "unit": t["unit"], "unit_src": t["unit_src"],
                        "period_src": t["period_src"], "row": t["row_basis"], "tot_eok": eok(t["tot_mm"])} for t in kept],
            "dropped_tables": [{"table": t["i"], "floored_net_asset": t["floored"]} for t in rec["tables"] if not t["kept"]],
            "dedupe": [{"rule": k, "keeps": a, "drops": b} for k, a, b in rec["dedupe"]],
            "flags": rec["flags"],
            "checks": {
                "r_lic1": rec.get("r_lic1"), "bs20_eok": eok(rec["bs20_mm"]) if rec["bs20_mm"] is not None else None,
                "ratio_bs20": round(rec["ratio_bs20"], 6) if rec.get("ratio_bs20") is not None else None,
                "filing_bs_eok": eok(rec["filing_anchor_mm"]) if rec["filing_anchor_mm"] is not None else None,
                "ratio_filing_bs": round(rec["ratio_filing"], 6) if rec.get("ratio_filing") is not None else None,
                "r_lic3_gap_eok": round(rec["r_lic3_gap_mm"] / 100.0, 4),
                "tag_tables": len(tg_t), "tag_cells": sum(x["cells"] for x in tg_t),
                "tag_mismatch": sum(x["mismatch"] for x in tg_t),
            },
            "net_lrc_eok": eok(rec["net_lrc_mm"]),
            **({"net_lrc_alt_eok": eok(rec["net_lrc_alt_mm"])} if rec.get("net_lrc_alt_mm") is not None else {}),
            "items_eok": {str(n): v for n, v in cell_item_values(rec).items()},
        })
    return {
        "master": "insurance_liability_portfolio", "scope": "items 10-17 (보험부채_발생사고요소) only; items 1-9 are the 경영공시 2-4/2-5 extract",
        "generated_at": generated_at, "emitter": "parser", "emitted_by": "scripts/extract_insurance_liability_lic.py",
        "inputs": {"IFRS17_BS_item20_sha256": bs20_snapshot_sha256(), "dart_cells_assembled": len(recs)},
        "key": ["company_code", "quarter", "item_block"],
        "source_id_values": {"DART": "source_file = the DART 사업/반기/분기보고서 (or 감사보고서 for 비상장사) XML the closing row was read from"},
        "note": ("values in the master are 억원 (DART 백만원 / 100, 2 decimals); checks.* are in 억원. basis=liability means item 15 "
                 "closes against IFRS17_BS item 20 (부채인 보험계약, 별도); basis=net means the filer prints only NET (순부채(자산)) rows "
                 "so item 15 is below item 20 by the 보험계약자산 offset. A source-absent (company, quarter) has no row and no cell here."),
        "cells": cells, "not_loaded": absent,
    }


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------
def summarize(recs: list) -> str:
    import collections
    st = collections.Counter((r["status"], r.get("class")) for r in recs)
    lines = [f"cells assembled: {len(recs)}"]
    for (status, klass), n in sorted(st.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        lines.append(f"  {status:11s} class={klass}: {n}")
    for r in recs:
        if r["status"] != "loaded":
            lines.append(f"  NOT LOADED {r['code']} {r['quarter']}: {r['reason']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1] if __doc__ else "")
    ap.add_argument("--write", action="store_true", help="append items 10..15 to insurance_liability_portfolio.json (backed up) and write the provenance file")
    ap.add_argument("--provenance-only", action="store_true", help="re-emit only the provenance file from a fresh full extraction (master untouched)")
    ap.add_argument("--codes", nargs="*", help="restrict to these company codes (debug; never combine with --write)")
    ap.add_argument("--fy", nargs="*", help="restrict to these FY dirs, e.g. FY2026_Q2 (debug; never combine with --write)")
    ap.add_argument("--dump", help="write the assembled cell records to this JSON path (debug)")
    args = ap.parse_args(argv)
    if (args.write or args.provenance_only) and (args.codes or args.fy):
        raise SystemExit("--write / --provenance-only need the full run (no --codes/--fy)")
    if args.write and args.provenance_only:
        raise SystemExit("choose --write or --provenance-only")
    recs = build_all(args.codes, args.fy)
    print(summarize(recs))
    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as f:
            json.dump(recs, f, ensure_ascii=False, indent=1, default=str)
    if args.provenance_only:
        prov = build_provenance(recs, datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"))
        with open(OUT_PROV, "w", encoding="utf-8", newline="\n") as f:
            json.dump(prov, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"re-emitted {OUT_PROV.name} ({len(prov['cells'])} cells); master untouched")
        return 0
    if not args.write:
        print("dry run: nothing written (use --write)")
        return 0
    with open(ILP, encoding="utf-8") as f:
        reg = ilp_registry(json.load(f))
    new_rows = new_ilp_rows(recs, reg)
    backup = merge_into_ilp(new_rows)
    prov = build_provenance(recs, datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"))
    with open(OUT_PROV, "w", encoding="utf-8", newline="\n") as f:
        json.dump(prov, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"appended {len(new_rows)} rows to {ILP.name}; backup {backup.name}; provenance {OUT_PROV.name} ({len(prov['cells'])} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
