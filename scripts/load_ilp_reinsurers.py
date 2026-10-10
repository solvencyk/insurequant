# -*- coding: utf-8 -*-
"""
Reinsurer branches KR1101-KR1108: insurance_liability_portfolio.json items 1-8 (+ item 9 where the filing says 해당사항 없음)
(ticket 20261011T0320Z stage 4).  Source = the company's own 정기경영공시 PDF (no DART filing exists for these eight):
  year-end   4-6-2) 회계모형별, 포트폴리오별 보험부채 현황   (2024.4Q, 2025.4Q; the next year-end prints the prior-year table)
  quarterly  2-4)   회계모형별, 포트폴리오별 보험부채 현황   (2025.1Q-2026.2Q; the next year's filing prints the prior-year-same-quarter table, which is
                      the only source of 2024.1Q-3Q)
ADDITIVE rows only, 억원, nothing is written without --write, everything recorded in the provenance sidecar.

Mapping (the ILP item meaning is kept, the reinsurers' 수재 portfolios simply sit in the same columns):
  items 1-7  the 합계 row of the table, column order  [일반모형 BEL, RA, CSM | 변동수수료접근법 BEL, RA, CSM | 보험료배분접근법]; item 8 = sum of items 1-7
  signs as printed (negative = 잔여보장자산); all eight reinsurers print GMM and PAA only (VFA = 0)
  스위스리아시아 prints two sections [생명보험] and [손해보험], each with its own 합계: the company value is the slot-wise SUM of the two 합계 rows
  마이브라운 prints PAA only; its 2025.2Q/3Q zeros are the issuer's own statement 「상품 출시 전으로 보험부채 없음」 (loaded as printed)
Rules per cell
  * every table is footed against its detail rows (footing_mixed: rows placed by their own token count); a table that does not foot is NOT loaded unless the
    exception is written in ALLOW_FOOTING with the arithmetic that explains it
  * two readings of one quarter (own filing, later filing's prior-year column): equal or within 1억 -> the finer print (백만원 beats 억원, tie -> later filing);
    a real difference -> the LATEST filing's prior-year column (owner rule 2026-10-09 for reinsurers), the other reading stays in the provenance
  * MANUAL tables are readings of rendered pages (text layer garbled) or hand-footed text; each carries its evidence
  * nothing is interpolated: a cell without a footed table stays empty and is listed in lrc_model_not_loaded with the reason

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_reinsurers.py [--write] [--report out.json]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as lic  # noqa: E402
import extract_insurance_liability_model_pdf_interim as I  # noqa: E402
import load_ilp_backfill_pre2025 as L  # noqa: E402
import load_ilp_reinsurers_lic as LL  # noqa: E402  (balance-sheet block of the same filings: independent cross-check of item 8)

WORK = REPO / "data" / "disclosure" / "_meta" / "ilp_round3_20261011"
TICKET = "inbox/parser/20261011T0320Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_remaining_backfill_lic23_reinsurers.md"
CODES = [f"KR11{n:02d}" for n in range(1, 9)]
FYS = ["FY2024_Q4", "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4", "FY2026_Q1", "FY2026_Q2"]
QUARTERS = ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]
OWNER_RULE = "공시 간 값 상충은 최신 공시의 전기 칸 채택 (owner 2026-10-09, 재보사·마이브라운)"


def per(q: str):
    """'2025.1Q' -> (2025, 1); the year-end label has no quarter: (2024, None) is what the reader reports for '<2024년>'"""
    return int(q[:4]), int(q[5])


def label_period(q: str):
    y, n = per(q)
    return (y, None if n == 4 else n)


# ---------------------------------------------------------------------------------------------------------------------------------
# hand readings (values in 억원).  key = (code, filing FY, quarter the table describes)
# ---------------------------------------------------------------------------------------------------------------------------------
MANUAL = {
    ("KR1103", "FY2025_Q3", "2025.3Q"): dict(
        vec=[-605.48, 88.01, 317.16, 0, 0, 0, 0], unit="억원", page=5, label="2025년 3분기", src="PDF_image",
        evidence=("합계 row printed '(605.48) 88.01 317.16' (the text layer splits the BEL cell onto the next line as '(6 05.48)'); confirmed on the page rendered at 120 dpi. "
                  "RA 6.35+76.11+5.54=87.99 and CSM 35.93+233.00+48.24=317.17 foot to the printed totals; the BEL column does not (see flag bel_rows_do_not_foot_to_total)"),
        flags=["manual_reading_text_layer_garbled", "bel_rows_do_not_foot_to_total"]),
    ("KR1107", "FY2025_Q3", "2024.3Q"): dict(
        vec=[-2403, 494, 874, 0, 0, 0, 0], unit="억원", page=11, label="<2024년 3분기>", src="PDF_image",
        evidence=("the text layer prints the 합계 GMM cells on a separate line behind the four zero cells (the generic reader put -2,403/494/874 into slots 5-7); "
                  "the pages 10-11 rendered at 110 dpi show 무배당질병 and 합계 = -2,403 / 494 / 874 in the 일반모형 columns and 0 in every other column; "
                  "the only non-zero detail row equals the 합계"),
        flags=["manual_reading_text_layer_order"]),
    ("KR1104", "FY2024_Q4", "2024.4Q"): dict(
        vec=[-380.75, 70.60, 144.49, 0, 0, 0, 0], unit="백만원", page=16, label="<2024년>", src="PDF",
        evidence=("digits are split by spaces in the text layer; 합계 (38,075) 7,060 14,449 백만원; detail rows (3,714)+(35,026)+665=(38,075); RA 1,133+5,743+183=7,059 vs 7,060; "
                  "CSM 1,633+12,588+227=14,448 vs 14,449"),
        flags=["manual_reading_spaced_digits"]),
    ("KR1104", "FY2025_Q1", "2025.1Q"): dict(
        vec=[-287.30, 68.76, 143.49, 0, 0, 0, 0], unit="백만원", page=9, label="<2025년 1분기>", src="PDF",
        evidence=("digits split by spaces; 합계 (28,730) 6,876 14,349 백만원; detail rows (3,707)+(27,961)+2,938=(28,730); RA 1,081+5,457+338=6,876; CSM 1,598+184+12,567=14,349"),
        flags=["manual_reading_spaced_digits"]),
    ("KR1104", "FY2025_Q1", "2024.1Q"): dict(
        vec=[-653.37, 77.99, 259.43, 0, 0, 0, 0], unit="백만원", page=9, label="<2024년 1분기>", src="PDF",
        evidence=("digits split by spaces; 합계 (65,337) 7,799 25,943 백만원; detail rows (5,577)+(59,760)=(65,337); RA 1,264+6,535=7,799; CSM 2,931+23,012=25,943"),
        flags=["manual_reading_spaced_digits"]),
    ("KR1104", "FY2025_Q4", "2025.4Q"): dict(
        vec=[-496, 77, 213, 0, 0, 0, 0], unit="억원", page=16, label="<2025년>", src="PDF",
        evidence=("the 합계 row is split by the text layer ('합계 0 0 0 0' / '(496) 77 213'); the generic reader took the page footer '16 | Page' as a fourth token (PAA 16). "
                  "Detail rows (58)+(438)=(496); RA 7+70=77; CSM 39+174=213; PAA column all 0"),
        flags=["manual_reading_page_footer_token"]),
    ("KR1106", "FY2025_Q1", "2025.1Q"): dict(
        vec=[-14794, 1918, 4638, 0, 0, 0, 0], unit="억원", page=6, label="<2025년 1분기>", src="PDF",
        evidence=("the text layer separates the minus sign from every BEL number ('- 14,794'); the generic reader took the lone '-' as a zero token and read the BEL as +14,794. "
                  "Detail rows 236+1,400+3,327+4+587+9,240=14,794; RA 1,917 vs 1,918; CSM 4,639 vs 4,638; PAA printed '-' (0) in this filing"),
        flags=["manual_reading_split_minus_sign"]),
    ("KR1106", "FY2026_Q1", "2026.1Q"): dict(
        vec=[-14635, 1620, 3886, 0, 0, 0, -94], unit="억원", page=7, label="<2026 년 1 분기>", src="PDF_image",
        evidence=("scanned PDF (no text layer); page 7 rendered at 190 dpi and read by eye. Detail rows (405)+(958)+(2,298)+(4)+(779)+(10,191)=(14,635); RA 12+299+130+0+204+976=1,621 vs 1,620; "
                  "CSM 118+106+194+2+313+3,154=3,887 vs 3,886; PAA 일반 (94) = 합계 (94)"),
        flags=["manual_reading_image_pdf"]),
    ("KR1106", "FY2026_Q1", "2025.1Q"): dict(
        vec=[-14794, 1918, 4638, 0, 0, 0, -222], unit="억원", page=7, label="<2025 년 1 분기>", src="PDF_image",
        evidence=("scanned PDF (no text layer); page 7 rendered at 190 dpi and read by eye. Detail rows (236)+(1,400)+(3,327)+(4)+(587)+(9,240)=(14,794); RA 11+371+197+0+247+1,091=1,917 vs 1,918; "
                  "CSM 73+296+716+2+280+3,272=4,639 vs 4,638; PAA 일반 (222) = 합계 (222)"),
        flags=["manual_reading_image_pdf"]),
}

# tables whose detail rows do not foot for a reason that was checked by hand (the table itself is read correctly)
ALLOW_FOOTING = {
    ("KR1101", "FY2024_Q4", "2024.4Q"): "PAA rows are one-token lines: 일반 -49.09 + 자동차 -20.90 = -69.99 vs printed -70; GMM columns foot (BEL diff 1 = rounding)",
    ("KR1101", "FY2025_Q1", "2024.1Q"): "PAA rows are one-token lines: 일반 -138 + 자동차 15 = -123 = printed; GMM columns foot to +-1",
    ("KR1101", "FY2025_Q1", "2025.1Q"): "PAA rows are one-token lines: 일반 -52 + 자동차 26 = -26 = printed; GMM columns foot",
    ("KR1101", "FY2026_Q1", "2025.1Q"): "same table as the 2025.1Q filing (identical vector); PAA rows 일반 -52 + 자동차 26 = -26",
    ("KR1103", "FY2025_Q2", "2025.2Q"): "RA and CSM foot; the BEL rows do not: the 무배당장기재물 row (-612.99) repeats the sum of the three life rows (-56.27-526.73-29.99=-613.00). The printed 합계 is kept",
    ("KR1103", "FY2026_Q1", "2026.1Q"): "RA and CSM foot; the BEL rows do not: 무배당장기재물 (-482) repeats the sum of the three life rows (-53-393-35=-481). The printed 합계 is kept",
    ("KR1103", "FY2026_Q2", "2025.2Q"): "the prior-year table printed in the 2026.2Q filing repeats the 2025.2Q filing's rows (same BEL inconsistency); the printed 합계 equals the 2025.2Q filing to the rounding",
    ("KR1106", "FY2025_Q3", "2025.3Q"): "PAA row is a one-token line: 일반 (70) = 합계 PAA (70); GMM columns foot (BEL 14,948; RA 2,002 vs 2,001; CSM 4,130)",
}
FOOTING_FLAGS = {("KR1103", "FY2025_Q2", "2025.2Q"): "bel_rows_do_not_foot_to_total", ("KR1103", "FY2026_Q1", "2026.1Q"): "bel_rows_do_not_foot_to_total",
                 ("KR1103", "FY2026_Q2", "2025.2Q"): "bel_rows_do_not_foot_to_total"}

# item 9 from a rendered page (scanned PDF, no text layer)
MANUAL_ITEM9 = {("KR1106", "2026.1Q"): (0, "p7 rendered at 55 and 190 dpi: '2-5) 무·저해지상품 해지율 예외모형 사용에 관한 사항 -- 해당사항 없음' (scanned PDF, read by eye)")}

# cells deliberately left empty although a table exists
WITHHOLD = {
    ("KR1102", "2026.1Q"): ("the printed 합계 rows of BOTH sections omit the Indirect-Par portfolio: life 합계 (2,664) 313 197 = 무배당사망 (297) 19 30 + 무배당건강 (2,367) 294 166 only "
                            "(rows incl. Indirect sum to (7,506) 363 1,403); non-life 합계 (2,801) 411 487 = 상해 + 질병 + 일반 + 자동차 without 무배당질병 Indirect (1,914) 20 310 "
                            "(all rows sum to (4,715) 431 797). Neither the printed totals (incomplete) nor a row sum (derived) is loaded: owner decision")
}
SKIP_PRE_EXISTENCE = {("KR1108", "2024.2Q"): "the 2025.2Q filing prints zeros for 2024.2Q although the company was only authorised in 2025.6 (no filing exists for that period); not loaded"}
NO_PDF_NOTE = {("KR1104", "FY2025_Q3"): "KR1104 하노버 FY2025_Q3 경영공시 PDF is not in data/disclosure (list page did not show it; downloader item)",
               ("KR1108", "FY2024_Q4"): "마이브라운 had no filing before 2025.2Q", ("KR1108", "FY2025_Q1"): "마이브라운: no 2025.1Q filing was provided/collected; the company was authorised 2025.6"}


# ---------------------------------------------------------------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------------------------------------------------------------
def pdf_of(code: str, fy: str):
    g = sorted(glob.glob(str(REPO / "data" / "disclosure" / fy / "raw" / f"{code}_*.pdf")))
    g = [p for p in g if "_v2" not in Path(p).name] or g
    return g[0] if g else None


_CACHE = {}


def read_fy(fy: str):
    """{code: read_interim result} for the eight reinsurers of one filing period; the workspace cache t84_reins_<FY>.json (made by t84_reins_read.py) is used when present"""
    if fy in _CACHE:
        return _CACHE[fy]
    p = WORK / f"t84_reins_{fy}.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
    else:
        d = {}
        for code in CODES:
            pdf = pdf_of(code, fy)
            if pdf:
                r = I.read_interim(pdf, max_pages=45, lookahead=5)
                r["pdf"] = str(Path(pdf).relative_to(REPO)).replace("\\", "/")
                d[code] = r
    _CACHE[fy] = d
    return d


def vec_of(t: dict, div: float):
    sl = t.get("slots")
    if not sl:
        return None
    return {i: round(float(sl[str(i)] if str(i) in sl else sl[i]) / div, 4) for i in range(1, 8)}


def foot_state(t: dict) -> str:
    fm = t.get("footing_mixed")
    if fm is None:
        return "n/a"
    return "ok" if fm["ok"] else "BAD"


def periodic_tables(code: str, fy: str):
    """[(period (year, n|None), section|None, table, entry)] of one filing: labelled companies by the table label, 스위스리 by (생명, 손해) pairs, 제네럴 by order"""
    e = read_fy(fy).get(code)
    if not e or e.get("status") != "ok":
        return []
    tabs = [t for t in e["tables"]]
    fy_y, fy_n = int(fy[2:6]), int(fy[-1])
    cur = (fy_y, None if fy_n == 4 else fy_n)
    prior = (fy_y - 1, cur[1])
    out = []
    if code == "KR1102":
        good = [t for t in tabs if t.get("slots")]
        if len(good) % 2:
            raise SystemExit(f"KR1102 {fy}: odd number of tables")
        for k in range(0, len(good), 2):
            p = [cur, prior][k // 2]
            for sec, t in zip(("life", "nonlife"), good[k:k + 2]):
                if sec == "life" and t["label_year"] is not None and t["label_year"] != p[0]:
                    raise SystemExit(f"KR1102 {fy}: pair {k // 2} label {t['label']} != {p}")
                out.append((p, sec, t, e))
    elif code == "KR1103":
        good = [t for t in tabs if t.get("slots")]
        # 2025.3Q: the generic reader mis-reads the garbled 합계 row; the table is supplied by MANUAL
        if fy == "FY2025_Q3":
            return []
        for k, t in enumerate(good[:2]):
            out.append(([cur, prior][k], None, t, e))
    else:
        seen = set()
        for t in tabs:
            if t["label_year"] is None:
                continue
            p = (t["label_year"], t["label_quarter"])
            key = (p, tuple(t.get("run") or ()))
            if key in seen:
                continue
            seen.add(key)
            out.append((p, None, t, e))
    return out


def candidates(code: str, q: str):
    """all readings of (code, q): own filing and the next year's filing (prior-year column), MANUAL tables replacing the generic reading of the same table"""
    y, n = per(q)
    lp = label_period(q)
    res = []
    for role, fy in (("own", f"FY{y}_Q{n}"), ("comp", f"FY{y + 1}_Q{n}")):
        if fy not in FYS:
            continue
        man = MANUAL.get((code, fy, q))
        if man:
            e = read_fy(fy).get(code) or {}
            res.append(dict(role=role, fy=fy, vec={i + 1: float(v) for i, v in enumerate(man["vec"])}, unit=man["unit"], page=man["page"], label=man["label"], run=man["vec"],
                            kind="manual", foot="manual", src=man["src"], file=e.get("pdf") or str(Path(pdf_of(code, fy)).relative_to(REPO)).replace("\\", "/"),
                            text_source="manual", evidence=man["evidence"], flags=list(man["flags"]), sections=None))
            continue
        tabs = [x for x in periodic_tables(code, fy) if x[0] == lp]
        if not tabs:
            continue
        e = tabs[0][3]
        div = e["unit_div"]
        if code == "KR1102":
            sec = {s: t for _p, s, t, _e in tabs}
            if set(sec) != {"life", "nonlife"}:
                continue
            vl, vn = vec_of(sec["life"], div), vec_of(sec["nonlife"], div)
            if vl is None or vn is None:
                continue
            vec = {i: round(vl[i] + vn[i], 4) for i in range(1, 8)}
            foot = "ok" if all(foot_state(t) == "ok" for t in sec.values()) else "BAD"
            res.append(dict(role=role, fy=fy, vec=vec, unit=e["unit"], page=sec["life"]["page"], label=sec["life"]["label"], run=None, kind="two_sections",
                            foot=foot, src="PDF", file=e["pdf"], text_source=e["source"], evidence=None, flags=["sum_of_life_and_nonlife_sections"],
                            sections={s: dict(page=t["page"], run=t["run"], vec=vec_of(t, div), footing=foot_state(t)) for s, t in sec.items()}))
            continue
        _p, _s, t, _e = tabs[0]
        v = vec_of(t, div)
        if v is None:
            continue
        res.append(dict(role=role, fy=fy, vec=v, unit=e["unit"], page=t["page"], label=t["label"], run=[round(x / div, 4) for x in t["run"]], kind=t["kind"],
                        foot=foot_state(t), src="PDF", file=e["pdf"], text_source=e["source"], evidence=None, flags=[] if e["source"] == "pdfplumber" else ["text_via_fitz"],
                        sections=None, footing_detail=t.get("footing_mixed")))
    # a MANUAL table whose generic counterpart does not exist (key not found by period) is still a candidate
    return res


def close(a: dict, b: dict, tol: float = 1.0) -> bool:
    return all(abs(a[i] - b[i]) <= tol + 1e-9 for i in range(1, 8))


_NET = None


def net_components():
    global _NET
    if _NET is None:
        _NET = LL.net_components_by_quarter()
    return _NET


def decimals(v: dict) -> int:
    """how many decimals the printed values carry (0 for an integer 억원 print, 2 for 백만원/100 or a two-decimal 억원 print)"""
    return max((len(f"{abs(x):.4f}".rstrip("0").split(".")[1]) if abs(x - round(x)) > 1e-9 else 0) for x in v.values())


def usable(c: dict, code: str, q: str):
    if c["foot"] in ("ok", "manual"):
        return True, None
    why = ALLOW_FOOTING.get((code, c["fy"], q))
    if why:
        return True, why
    return False, f"footing {c['foot']}" + (f" diffs {c['footing_detail']['diffs']}" if c.get("footing_detail") else "")


def decide(code: str, q: str):
    """-> dict(status loaded|withheld|absent, chosen, alts, reason)"""
    if (code, q) in WITHHOLD:
        cs = candidates(code, q)
        return dict(status="withheld", reason=WITHHOLD[(code, q)], alts=cs, chosen=None)
    if (code, q) in SKIP_PRE_EXISTENCE:
        return dict(status="absent", reason=SKIP_PRE_EXISTENCE[(code, q)], alts=[], chosen=None)
    cs = candidates(code, q)
    for c in cs:
        c["usable"], c["footing_exception"] = usable(c, code, q)
    ok = [c for c in cs if c["usable"]]
    if not ok:
        if cs:
            return dict(status="withheld", reason="; ".join(f"{c['role']} {c['fy']} p{c['page']}: {c['footing_exception']}" for c in cs), alts=cs, chosen=None)
        y, n = per(q)
        parts = []
        for role, fy in (("own", f"FY{y}_Q{n}"), ("later filing", f"FY{y + 1}_Q{n}")):
            if (code, fy) in NO_PDF_NOTE:
                parts.append(f"{fy}: {NO_PDF_NOTE[(code, fy)]}")
            elif fy not in FYS:
                parts.append(f"{fy}: not in scope" + (" (the 2024 quarterly 경영공시 had no 2-4 table)" if y == 2024 and n < 4 else " (not published yet)"))
            elif pdf_of(code, fy) is None:
                parts.append(f"{fy}: no PDF collected")
            else:
                parts.append(f"{fy}: no table for {q} in the filing" + (" (the filing prints only the current period)" if role == "later filing" else ""))
        return dict(status="absent", reason="; ".join(parts), alts=[], chosen=None)
    own = [c for c in ok if c["role"] == "own"]
    comp = [c for c in ok if c["role"] == "comp"]
    flags = []
    if own and comp:
        o, c = own[0], comp[0]
        if close(o["vec"], c["vec"]):
            if o["vec"] == c["vec"]:
                chosen = c
                flags.append("own_and_latest_comparative_agree")
            else:
                # within 1억 (the granularity of an integer print): the finer print wins, a tie goes to the later filing
                chosen = o if decimals(o["vec"]) > decimals(c["vec"]) else c
                flags.append("own_and_latest_comparative_agree_within_1eok")
                flags.append("finer_print_of_own_filing_kept" if chosen is o else "latest_comparative_kept")
        else:
            chosen = c
            flags.append("latest_comparative_adopted_over_own")
            diff = {i: round(c["vec"][i] - o["vec"][i], 4) for i in range(1, 8) if abs(c["vec"][i] - o["vec"][i]) > 1.0}
            flags.append("own_vs_comparative_diff_" + ",".join(f"item{i}:{d:+g}" for i, d in diff.items()))
    else:
        chosen = (comp or own)[0]
    flags += chosen["flags"]
    fk = FOOTING_FLAGS.get((code, chosen["fy"], q))
    if fk:
        flags.append(fk)
    if chosen["role"] == "comp" and not own:
        flags.append("latest_filing_comparative_only")
    # independent cross-check against the filing's OWN balance sheet (보험계약부채 LRC minus 보험계약자산 LRC = the net the 2-4 table is about), where the filing carries it
    bs = net_components().get((code, q))
    if bs is not None:
        i8 = round(sum(chosen["vec"][i] for i in range(1, 8)), 4)
        tol = max(0.5, 0.005 * abs(bs["net"]))
        chk = {"item8": i8, "balance_sheet_net_lrc_eok": bs["net"], "diff": round(i8 - bs["net"], 2), "tol": round(tol, 2), "balance_sheet_file": bs["file"],
               "balance_sheet_components_eok": {k: bs[k] for k in ("bel", "ra", "csm")}}
        chosen["bs_check"] = chk
        if abs(i8 - bs["net"]) > tol:
            comp = "; ".join(f"{nm} 2-4 {chosen['vec'][a] + chosen['vec'][b]:,.2f} vs balance sheet {bs[k]:,.2f}" for nm, k, a, b in
                             (("BEL", "bel", 1, 4), ("RA", "ra", 2, 5), ("CSM", "csm", 3, 6)) if bs[k] is not None)
            return dict(status="withheld", alts=cs, chosen=None, flags=flags,
                        reason=(f"item 8 = {i8:,.2f} (2-4 합계, {chosen['fy']} p{chosen['page']}) disagrees with the net remaining-coverage liability of the same filing's balance sheet "
                                f"{bs['net']:,.2f} (diff {i8 - bs['net']:+,.2f}, tol {tol:,.2f}); {comp}. The 2-4 table foots to its own detail rows, the balance sheet block is internally "
                                f"consistent; which one is wrong cannot be settled from the filing: not loaded, owner decision"))
        flags.append("balance_sheet_net_lrc_agrees")
    return dict(status="loaded", chosen=chosen, alts=cs, flags=flags, reason=None)


# ---------------------------------------------------------------------------------------------------------------------------------
# item 9 (own filing only)
# ---------------------------------------------------------------------------------------------------------------------------------
def item9_reins(pdf):
    """0 when the 무·저해지상품 해지율 예외모형 section of the filing says 해당사항 없음, else (None, why)"""
    import fitz
    if pdf is None:
        return None, None
    doc = fitz.open(str(pdf))
    try:
        for i in range(min(doc.page_count, 90)):
            tn = re.sub(r"\s+", "", doc[i].get_text("text") or "")
            tn = re.sub(r"([^\d,.\s])\1", r"\1", tn)
            m = re.search(r"무[·∙ㆍ.,]?저해지상품해지율예외모형사용에관한사항", tn)
            if m and i + 1 > 3:
                tail = tn[m.end(): m.end() + 60]
                if "해당사항없음" in tail or "해당사항이없" in tail:
                    return 0, f"p{i + 1}: …{tn[m.start(): m.end() + 20]}"
                return None, f"p{i + 1}: section present but not 'none' ({tail[:30]})"
        return None, None
    except Exception as ex:  # noqa: BLE001  (scanned PDFs may refuse the text call)
        return None, f"unreadable: {ex}"
    finally:
        doc.close()


# ---------------------------------------------------------------------------------------------------------------------------------
# registry, rows, provenance
# ---------------------------------------------------------------------------------------------------------------------------------
def registry():
    ks = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    reg = {}
    for r in ks:
        c = r.get("원보험사코드")
        if c in CODES and c not in reg:
            reg[c] = {"원수사명": r["원수사명"], "티커": r["티커"], "생손보여부": r["생손보여부"]}
    miss = [c for c in CODES if c not in reg]
    if miss:
        raise SystemExit(f"registry fields missing in kics_disclosure.json for {miss}")
    return reg


def lrc_record(code, q, d, item9, ev9):
    c = d["chosen"]
    y, n = per(q)
    items = {str(i): round(c["vec"][i], 4) for i in range(1, 8)}
    items["8"] = round(sum(c["vec"][i] for i in range(1, 8)), 4)
    block = {("own", True): "lrc_model_table_4-6-2", ("own", False): "lrc_model_table_2-4", ("comp", True): "lrc_model_table_4-6-2_prior_year",
             ("comp", False): "lrc_model_table_2-4_prior_year_quarter"}[(c["role"], n == 4)]
    alts = [{"role": a["role"], "fy": a["fy"], "page": a["page"], "label": a["label"], "unit": a["unit"], "vec_eok": {str(i): a["vec"][i] for i in range(1, 8)}, "footing": a["foot"],
             "footing_exception": a.get("footing_exception"), "usable": a.get("usable"), "used": a is c} for a in d["alts"]]
    r = {"company_code": code, "quarter": q, "item_block": block, "source_id": c["src"], "as_of_date": lic.as_of_date(q), "source_file": c["file"], "page": c["page"], "table": None,
         "table_label": c["label"], "table_year": y, "table_year_src": "label" if c["kind"] != "manual" else "manual", "unit_in_source": c["unit"], "printed_run": c["run"],
         "run_kind": c["kind"], "text_source": c["text_source"], "items_eok": items, "item9": item9, "item9_evidence": ev9, "flags": d["flags"], "evidence": c.get("evidence"),
         "published_in": f"{c['fy']} 경영공시 " + ("4-6-2" if c["fy"].endswith("Q4") else "2-4") + (" (전기 칸)" if c["role"] == "comp" else ""),
         "basis": "latest_filing_comparative" if c["role"] == "comp" else "own_filing", "owner_rule": OWNER_RULE, "alternatives": alts}
    if c.get("sections"):
        r["sections"] = c["sections"]
    if c.get("bs_check"):
        r["balance_sheet_cross_check"] = c["bs_check"]
    if c.get("footing_exception"):
        r["footing_exception"] = c["footing_exception"]
    return r


def build(reg):
    rows, prov, notl, table = [], [], [], []
    for code in CODES:
        for q in QUARTERS:
            d = decide(code, q)
            if d["status"] != "loaded":
                notl.append({"company_code": code, "quarter": q, "items": "1-8", "reason": d["reason"],
                             **({"detail": {"readings": [{"role": a["role"], "fy": a["fy"], "page": a["page"], "vec_eok": {str(i): a["vec"][i] for i in range(1, 8)}} for a in d["alts"]]}}
                                if d.get("alts") else {})})
                table.append((code, q, d["status"], None, None))
                continue
            c = d["chosen"]
            item9 = ev9 = None
            y, n = per(q)
            own_fy = f"FY{y}_Q{n}"
            if (code, q) in MANUAL_ITEM9:
                item9, ev9 = MANUAL_ITEM9[(code, q)]
            elif y >= 2024 and own_fy in FYS:
                item9, ev9 = item9_reins(pdf_of(code, own_fy))
            vals = {i: round(c["vec"][i], 4) for i in range(1, 8)}
            vals[8] = round(sum(vals[i] for i in range(1, 8)), 4)
            for nn in range(1, 9):
                name, level = L.MODEL_ITEMS[nn]
                rows.append(L.row(reg, code, q, nn, name, L.SEC_MODEL, level, vals[nn]))
            if item9 is not None:
                rows.append(L.row(reg, code, q, 9, L.ITEM9_NAME, L.SEC_LAPSE, 1, item9))
            prov.append(lrc_record(code, q, d, item9, ev9))
            table.append((code, q, "loaded", vals, d["flags"]))
    rows.sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))
    return rows, prov, notl, table


def checks(rows, table):
    """R1 identity, sign sanity (RA/CSM >= 0), quarter-on-quarter jumps; -> (red, yellow)"""
    red, yellow = [], []
    by = {}
    for code, q, st, vals, flags in table:
        if st != "loaded":
            continue
        by.setdefault(code, []).append((q, vals))
        if abs(sum(vals[i] for i in range(1, 8)) - vals[8]) > 0.05:
            red.append(f"R1 {code} {q}: item8 {vals[8]} != sum")
        for i in (2, 3, 5, 6):
            if vals[i] < -0.005:
                red.append(f"SIGN {code} {q}: item {i} = {vals[i]} < 0 (RA/CSM cannot be negative)")
    for code, lst in by.items():
        lst.sort()
        for (q0, v0), (q1, v1) in zip(lst, lst[1:]):
            for i, nm in ((1, "BEL"), (3, "CSM")):
                a, b = v0[i], v1[i]
                if a and b and (a * b < 0 or abs(b) / abs(a) > 1.5 or abs(b) / abs(a) < 1 / 1.5):
                    yellow.append(f"QOQ {code} {q0}->{q1} item {i} {nm}: {a:,.2f} -> {b:,.2f}")
    return red, yellow


def append_provenance(prov_cells, notl, tag):
    raw0 = L.PROV.read_bytes()
    txt = raw0.decode("utf-8")
    prov = json.loads(txt)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance file does not round-trip byte for byte")
    have = {(c["company_code"], c["quarter"]) for c in prov.get("lrc_model_cells", [])}
    clash = [(c["company_code"], c["quarter"]) for c in prov_cells if (c["company_code"], c["quarter"]) in have]
    if clash:
        raise SystemExit(f"abort: lrc_model_cells already exist: {clash[:3]}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    backup = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_{tag}.json"
    k = 2
    while backup.exists():
        backup = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_{tag}_{k}.json"
        k += 1
    shutil.copyfile(L.PROV, backup)
    prov["lrc_model_cells"] = prov.get("lrc_model_cells", []) + prov_cells
    prov["lrc_model_not_loaded"] = prov.get("lrc_model_not_loaded", []) + notl
    prov["backfills"] = prov.get("backfills", []) + [{
        "stage": "reinsurers_KR1101-KR1108", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/load_ilp_reinsurers.py", "ticket": TICKET,
        "note": ("items 1-8 (+9) of the eight reinsurer branches from their own 경영공시 4-6-2 / 2-4 tables (no DART filing exists); latest-filing prior-year column wins on conflict "
                 "(owner 2026-10-09); items 10-15 are NOT loaded (the 경영공시 carries no LRC/LIC split)")}]
    out = json.dumps(prov, ensure_ascii=False, indent=1) + "\n"
    tmp = L.PROV.with_name(L.PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, L.PROV)
    return backup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    reg = registry()
    rows, prov, notl, table = build(reg)
    red, yellow = checks(rows, table)
    print(f"cells loaded {sum(1 for t in table if t[2] == 'loaded')}  not loaded {len(notl)}  rows {len(rows)}  (item 9 rows {sum(1 for r in rows if r['항목번호'] == 9)})")
    print("registry:", {c: (v["원수사명"], v["티커"], v["생손보여부"]) for c, v in reg.items()})
    for code, q, st, vals, flags in table:
        if st == "loaded":
            v = [vals[i] for i in range(1, 9)]
            print(f"  {code} {q} LOADED  {v}  {[f for f in flags if not f.startswith('manual_')][:4]}")
        else:
            print(f"  {code} {q} {st.upper()}")
    print(f"RED {len(red)}")
    for s in red:
        print("  RED   ", s)
    print(f"YELLOW {len(yellow)}")
    for s in yellow:
        print("  YELLOW", s)
    print("not loaded:")
    for n in notl:
        print("  ", n["company_code"], n["quarter"], "|", n["reason"][:230])
    if args.report:
        Path(args.report).write_text(json.dumps({"rows": len(rows), "loaded": [(t[0], t[1], t[3], t[4]) for t in table if t[2] == "loaded"], "not_loaded": notl,
                                                 "red": red, "yellow": yellow}, ensure_ascii=False, indent=1), encoding="utf-8")
    if red:
        raise SystemExit("RED present: nothing written")
    if not args.write:
        print("\n(dry run: nothing written; add --write)")
        return
    backup = lic.merge_into_ilp(rows, tag="pre_reinsurers")
    pb = append_provenance(prov, notl, "pre_reinsurers")
    print("written: master", len(rows), "rows; backups:", backup.name, pb.name)


if __name__ == "__main__":
    main()
