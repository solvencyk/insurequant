# -*- coding: utf-8 -*-
"""
LIC items 10-15 of the reinsurer branches (ticket 20261011T0320Z stage 4, second half): 「LIC(항목 10~15)는 재보사는 DART 가 없으므로 경영공시/감사보고서에서 나오는 만큼만(없으면 빈칸)」.

Source = the 업무보고서식 재무상태표 detail that the quarterly 경영공시 of 뮌헨재보험(KR1101), 하노버재보험(KR1104) and 퍼시픽라이프리(KR1107) carry (천원), the same block that
scripts/load_ilp_lic_stage3_pdf.py reads for 처브라이프:
    1. 보험계약자산      가. 잔여보장요소 (1)최선추정 (2)위험조정 (3)보험계약마진 (4)PAA   나. 발생사고요소 (1)최선추정 (2)위험조정
    1. 보험계약부채      (same rows)
Items (억원, liability basis = the 보험계약부채 side, as in the DART cells of the domestic filers):
    10 = 보험계약부채 / 나. 발생사고요소   11 = (1) 최선추정   12 = (2) 위험조정   13 = 10 - 11 - 12 (0 here)   14 = 보험계약부채 / 가. 잔여보장요소   15 = 1. 보험계약부채 (= 10 + 14)
The 보험계약자산 side is NOT in the items; it is kept in the provenance (asset_side_eok) because the 2-4 table (item 8) is the NET of both sides.
Checks per cell:
    R-LIC3     11 + 12 + 13 = 10 and 10 + 14 = 15 (0.0301억)                      -> a failing cell is not written
    R-LIC1     item 15 == the filing's own summary line 「(보험계약부채)」 of the 부채총계 block (0.011억)   -> a failing cell is not written
    R-LIC2     item 8 of the same cell == net remaining-coverage liability (LRC of 보험계약부채 - LRC of 보험계약자산) within max(0.5억, 0.5 %); this also fixes the unit.
               A failure is REPORTED (the LIC cell is internally consistent; it is the 2-4 total that disagrees with the balance sheet) and scripts/load_ilp_reinsurers.py
               withholds the items 1-8 of that cell.
    columns    the prior-year-end column of the quarterly filings (2024.12.31 / 2025.12.31) gives the 2024.4Q / 2025.4Q cells; the latest filing's column wins and every other
               reading of the same quarter must agree to 0.011억.
Additive rows only (lic.merge_into_ilp), provenance cells (source_id PDF, basis liability), backups first.  Nothing is written without --write.

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_reinsurers_lic.py [--dump] [--write] [--report out.json]
"""
from __future__ import annotations

import argparse
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
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

TICKET = "inbox/parser/20261011T0320Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_remaining_backfill_lic23_reinsurers.md"
PROV = REPO / "insurance_liability_portfolio_provenance.json"
SOURCES = {
    "KR1101": ["FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4", "FY2026_Q1", "FY2026_Q2"],
    "KR1104": ["FY2025_Q1", "FY2025_Q2", "FY2026_Q1", "FY2026_Q2"],
    "KR1107": ["FY2024_Q4", "FY2025_Q1", "FY2025_Q2"],
}
UNITS = {"천원": 1e-5, "원": 1e-8, "백만원": 1e-2}      # -> 억원 factor
UNIT = {"KR1101": "천원", "KR1104": "천원", "KR1107": "천원"}      # confirmed per company by R-LIC2 (net LRC vs the 2-4 item 8) in every cell that can be checked
SCOPE_Q = ["2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]
SIDE_KEYS = ("total", "lrc", "lic", "bel", "ra")
RE_NUM = re.compile(r"(?:(?<=\s)|^)(-?\d[\d,]*(?:\.\d+)?|-)(?=\s|$)")


def pdf_of(code, fy):
    g = [str(p) for p in disclosure_pdfs(fy, code)]
    g = [p for p in g if "_v2" not in Path(p).name] or g
    return Path(g[0]) if g else None


def page_lines(pdf_path):
    """[(page, line)] of the whole filing: pdfplumber text, fitz when pdfplumber cannot read the page"""
    import fitz
    import pdfplumber
    out = []
    try:
        pdf = pdfplumber.open(str(pdf_path))
        for i, p in enumerate(pdf.pages):
            try:
                t = p.extract_text() or ""
            except Exception:  # noqa: BLE001
                t = ""
            if not t.strip():
                try:
                    doc = fitz.open(str(pdf_path))
                    t = doc[i].get_text("text") or ""
                    doc.close()
                except Exception:  # noqa: BLE001
                    t = ""
            for ln in t.split("\n"):
                out.append((i + 1, ln))
        pdf.close()
    except Exception:  # noqa: BLE001
        doc = fitz.open(str(pdf_path))
        for i in range(doc.page_count):
            for ln in (doc[i].get_text("text") or "").split("\n"):
                out.append((i + 1, ln))
        doc.close()
    return out


def numbers_of(tail: str):
    """number columns of a line tail; a lone '-' directly before a number is its minus sign ('- 21,209,437'), a lone '-' otherwise is zero"""
    toks = RE_NUM.findall(tail)
    out, k = [], 0
    while k < len(toks):
        t = toks[k]
        if t == "-":
            if k + 1 < len(toks) and toks[k + 1] != "-":
                out.append(-float(toks[k + 1].replace(",", "")))
                k += 2
                continue
            out.append(0.0)
        else:
            out.append(float(t.replace(",", "")))
        k += 1
    return out


def parse_blocks(pdf_path):
    """({'asset': {...}, 'liab': {...}}, summary) read from the FIRST 「1. 보험계약자산」 / 「1. 보험계약부채」 block of the filing.
    Each side: {'total', 'lrc', 'lic', 'bel', 'ra': [columns], 'pages': [..]}; summary = (page, [columns]) of the first 「(보험계약부채)」 line"""
    lines = page_lines(pdf_path)
    blocks = {}
    cur = None
    sub = None
    summary = None
    for page, raw in lines:
        s = raw.strip()
        if not s:
            continue
        flat = re.sub(r"\s+", "", s)
        m_lab = re.match(r"^(.*?[가-힣\]\)A-Za-z])\s+(-?\d[\d,]*(?:\.\d+)?|-)(\s.*|$)", s)
        if m_lab:
            label = re.sub(r"\s+", "", m_lab.group(1))
            nums = numbers_of(m_lab.group(2) + (m_lab.group(3) or ""))
        else:
            label, nums = flat, []
        if re.match(r"^\(보험계약부채\)", label) and summary is None and nums:
            summary = (page, nums)
        if re.match(r"^1\.보험계약자산", label) and nums:
            cur = None if "asset" in blocks else blocks.setdefault("asset", {"pages": set()})
            if cur is not None:
                cur["total"] = nums
            sub = None
        elif re.match(r"^1\.보험계약부채", label) and nums:
            cur = None if "liab" in blocks else blocks.setdefault("liab", {"pages": set()})
            if cur is not None:
                cur["total"] = nums
            sub = None
        elif re.match(r"^2\.재보험계약(자산|부채)", label):
            cur, sub = None, None
        elif cur is not None:
            if re.match(r"^가\.잔여보장요소", label):
                cur["lrc"], sub = nums, "lrc"
            elif re.match(r"^나\.발생사고요소", label):
                cur["lic"], sub = nums, "lic"
            elif sub == "lrc" and re.match(r"^\(1\)최선추정", label):
                cur["lrc_bel"] = nums
            elif sub == "lrc" and re.match(r"^\(2\)위험조정", label):
                cur["lrc_ra"] = nums
            elif sub == "lrc" and re.match(r"^\(3\)보험계약마진", label):
                cur["lrc_csm"] = nums
            elif sub == "lic" and re.match(r"^\(1\)최선추정", label):
                cur["bel"] = nums
            elif sub == "lic" and re.match(r"^\(2\)위험조정", label):
                cur["ra"] = nums
            elif re.match(r"^다\.사전인식", label):
                sub = None
        if cur is not None:
            cur["pages"].add(page)
    for b in blocks.values():
        b["pages"] = sorted(b["pages"])
    return blocks, summary


def fy_quarter(fy: str):
    return int(fy[2:6]), int(fy[-1])


def readings():
    """one reading per (company, filing, column): current quarter (column 0) and the prior-year-end column (column 1, quarterly filings only), values in 억원"""
    out, notes = [], []
    for code, fys in SOURCES.items():
        f = UNITS[UNIT[code]]
        for fy in fys:
            pdf = pdf_of(code, fy)
            if pdf is None:
                notes.append((code, fy, "no PDF"))
                continue
            blocks, summary = parse_blocks(pdf)
            liab, asset = blocks.get("liab"), blocks.get("asset")
            if not liab or not all(k in liab for k in SIDE_KEYS):
                notes.append((code, fy, "liability block 1. 보험계약부채 / 가. 잔여보장요소 / 나. 발생사고요소 (1)(2) not found in the text layer"))
                continue
            if not asset or not all(k in asset for k in ("total", "lrc", "lic")):
                notes.append((code, fy, "asset block 1. 보험계약자산 not found"))
                continue
            y, n = fy_quarter(fy)
            ncol = len(liab["total"])
            cols = [(0, f"{y}.{n}Q")] + ([(1, f"{y - 1}.4Q")] if ncol >= 2 else [])
            for col, q in cols:
                if q not in SCOPE_Q:
                    continue

                def g(d, k, col=col):
                    return round(d[k][col] * f, 4) if len(d[k]) > col else None

                def comp(d, col=col):
                    return {k: (round(d[f"lrc_{k}"][col] * f, 4) if f"lrc_{k}" in d and len(d[f"lrc_{k}"]) > col else None) for k in ("bel", "ra", "csm")}

                out.append({"code": code, "fy": fy, "col": col, "quarter": q, "file": str(pdf.relative_to(REPO)).replace("\\", "/"),
                            "pages": {"liab": liab["pages"], "asset": asset["pages"]},
                            "liab": {k: g(liab, k) for k in SIDE_KEYS}, "asset": {k: g(asset, k) for k in ("total", "lrc", "lic")},
                            "lrc_components": {"liab": comp(liab), "asset": comp(asset)},
                            "summary": (round(summary[1][col] * f, 4) if summary and len(summary[1]) > col else None), "summary_page": summary[0] if summary else None})
    return out, notes


def net_lrc_by_quarter(rs=None):
    """{(code, quarter): net remaining-coverage liability in 억원 (보험계약부채 LRC - 보험계약자산 LRC)} of the LATEST reading of each quarter"""
    rs = rs if rs is not None else readings()[0]
    best = {}
    for r in sorted(rs, key=lambda r: r["fy"]):
        best[(r["code"], r["quarter"])] = round(r["liab"]["lrc"] - r["asset"]["lrc"], 2)
    return best


def net_components_by_quarter(rs=None):
    """{(code, quarter): {'net', 'bel', 'ra', 'csm'}} net remaining-coverage components in 억원 (liability LRC minus asset LRC, each of BEL / RA / CSM) of the latest reading"""
    rs = rs if rs is not None else readings()[0]
    best = {}
    for r in sorted(rs, key=lambda r: r["fy"]):
        lc, ac = r["lrc_components"]["liab"], r["lrc_components"]["asset"]
        comp = {k: (None if lc[k] is None or ac[k] is None else round(lc[k] - ac[k], 2)) for k in ("bel", "ra", "csm")}
        best[(r["code"], r["quarter"])] = {"net": round(r["liab"]["lrc"] - r["asset"]["lrc"], 2), "file": r["file"], "fy": r["fy"], **comp}
    return best


def cell_items(r):
    v10, v11, v12 = round(r["liab"]["lic"], 2), round(r["liab"]["bel"], 2), round(r["liab"]["ra"], 2)
    v13 = round(v10 - v11 - v12, 2)
    v13 = 0.0 if abs(v13) <= 0.0301 else v13
    return {10: v10, 11: v11, 12: v12, 13: v13, 14: round(r["liab"]["lrc"], 2), 15: round(r["liab"]["total"], 2)}


def build(ilp):
    M = {}
    for r in ilp:
        M.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    rs, notes = readings()
    by = {}
    for r in rs:
        by.setdefault((r["code"], r["quarter"]), []).append(r)
    cells, rejected = [], []
    for (code, q), grp in sorted(by.items()):
        grp.sort(key=lambda r: r["fy"], reverse=True)          # latest filing first (owner rule: latest filing's prior-year column wins)
        r = grp[0]
        items = cell_items(r)
        why = []
        if abs(items[10] + items[14] - items[15]) > 0.0301:
            why.append(f"R-LIC3: 10 + 14 = {items[10] + items[14]:,.2f} vs 15 = {items[15]:,.2f}")
        if abs(items[11] + items[12] + items[13] - items[10]) > 0.0301:
            why.append("R-LIC3: 11 + 12 + 13 != 10")
        if r["summary"] is None:
            why.append("R-LIC1: no 「(보험계약부채)」 summary line to anchor item 15")
        elif abs(r["summary"] - items[15]) > 0.011:
            why.append(f"R-LIC1: item 15 {items[15]:,.2f} vs the filing's 「(보험계약부채)」 line {r['summary']:,.2f}")
        net = round(r["liab"]["lrc"] - r["asset"]["lrc"], 2)
        i8 = M.get((code, q), {}).get(8)
        r2 = None
        if i8 is not None:
            d = i8 - net
            tol = max(0.5, 0.005 * abs(net))
            r2 = {"item8": i8, "net_lrc_eok": net, "diff": round(d, 2), "tol": round(tol, 2), "pass": abs(d) <= tol}
        agree = [{"fy": o["fy"], "col": o["col"], "items": cell_items(o)} for o in grp[1:]]
        for a in agree:
            if any(abs(a["items"][k] - items[k]) > 0.011 for k in items):
                why.append(f"readings of {q} in {a['fy']} differ from the latest filing {r['fy']}")
        cell = {"code": code, "quarter": q, "reading": r, "items": items, "net_lrc_eok": net, "r_lic2": r2, "other_readings": agree, "why": why}
        (rejected if why else cells).append(cell)
    return cells, rejected, notes


def provenance_record(c):
    r = c["reading"]
    items = c["items"]
    own = r["col"] == 0
    return {
        "company_code": r["code"], "quarter": r["quarter"], "item_block": "lic_pdf_bs", "source_id": "PDF", "as_of_date": lic.as_of_date(r["quarter"]), "source_file": r["file"],
        "page": r["pages"]["liab"], "scope": "separate", "period": "current" if own else "prior-year-end column of the later filing",
        "class": "A1", "bel_ra_source": "RF", "basis": "liability", "row_basis": ["LIAB"], "unit": UNIT[r["code"]], "unit_source": "validated_by_r_lic2_vs_2-4_net_lrc",
        "tables": [], "dropped_tables": [], "dedupe": [],
        "flags": ["pdf_source_no_dart_filing", "reinsurer_branch_balance_sheet_block"] + ([] if own else ["prior_year_end_column_of_later_filing"]),
        "checks": {"r_lic1": "pass", "bs20_eok": None, "ratio_bs20": None, "filing_bs_eok": r["summary"],
                   "ratio_filing_bs": round(r["liab"]["total"] / r["summary"], 6) if r["summary"] else None,
                   "r_lic3_gap_eok": round(items[10] + items[14] - items[15], 4), "tag_tables": 0, "tag_cells": 0, "tag_mismatch": 0, "r_lic2_vs_2_4": c["r_lic2"]},
        "net_lrc_eok": c["net_lrc_eok"], "items_eok": {str(n): v for n, v in sorted(items.items())},
        "asset_side_eok": {"total": r["asset"]["total"], "lrc": r["asset"]["lrc"], "lic": r["asset"]["lic"],
                           "note": "보험계약자산 side of the same balance sheet; NOT in items 10-15 (liability basis), kept because the 2-4 item 8 is the net of both sides"},
        "other_readings": c["other_readings"],
        "evidence": f"liability block pages {r['pages']['liab']}, asset block pages {r['pages']['asset']}; 「(보험계약부채)」 summary line p{r['summary_page']} = {r['summary']}",
        "note": ("업무보고서식 재무상태표 「1. 보험계약부채 / 가. 잔여보장요소 / 나. 발생사고요소 (1) 최선추정 (2) 위험조정」 of the 경영공시 PDF (천원); "
                 "LIC = 나. 발생사고요소, LRC = 가. 잔여보장요소 (can be negative inside a liability-position group), total = 1. 보험계약부채")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    ilp = json.loads(lic.ILP.read_text(encoding="utf-8"))
    reg = lic.ilp_registry(ilp)
    cells, rejected, notes = build(ilp)
    for n in notes:
        print("NOTE", n)
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in ilp}
    print(f"cells accepted {len(cells)}  rejected {len(rejected)}")
    for c in cells:
        v = c["items"]
        r2 = c["r_lic2"]
        r2s = "no item 8" if r2 is None else (f"R-LIC2 ok (diff {r2['diff']:+.2f})" if r2["pass"] else f"R-LIC2 DIFF {r2['diff']:+.2f} (tol {r2['tol']})")
        print(f"  {c['code']} {c['quarter']} {c['reading']['fy']} col{c['reading']['col']} | 10 {v[10]:,.2f} 11 {v[11]:,.2f} 12 {v[12]:,.2f} 13 {v[13]:,.2f} "
              f"14 {v[14]:,.2f} 15 {v[15]:,.2f} | net LRC {c['net_lrc_eok']:,.2f} | {r2s} | other readings {len(c['other_readings'])}")
    for c in rejected:
        print("  REJECTED", c["code"], c["quarter"], c["why"])
    if args.report:
        Path(args.report).write_text(json.dumps({"cells": cells, "rejected": rejected, "notes": notes}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if not args.write:
        print("(dry run: nothing written; add --write)")
        return
    if rejected:
        raise SystemExit("rejected cells present: nothing written")
    new_rows, recs = [], []
    for c in cells:
        for n, val in sorted(c["items"].items()):
            if (c["code"], c["quarter"], n) in have:
                raise SystemExit(f"abort: key exists {(c['code'], c['quarter'], n)}")
            name, section, level = lic.ITEM_CATALOG[n]
            info = reg[c["code"]]
            new_rows.append({"원보험사코드": c["code"], "원수사명": info["원수사명"], "티커": info["티커"], "생손보여부": info["생손보여부"], "항목번호": n, "항목명": name,
                             "섹션": section, "레벨": level, "공시분기": c["quarter"], "값": val})
        recs.append(provenance_record(c))
    new_rows.sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))
    backup = lic.merge_into_ilp(new_rows, tag="pre_reinsurers_lic")
    raw0 = PROV.read_bytes()
    txt = raw0.decode("utf-8")
    prov = json.loads(txt)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance does not round-trip (master rows ARE written; add provenance by hand)")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_reinsurers_lic.json"
    k = 2
    while pback.exists():
        pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_reinsurers_lic_{k}.json"
        k += 1
    shutil.copyfile(PROV, pback)
    have_cells = {(c["company_code"], c["quarter"]) for c in prov["cells"]}
    for rc in recs:
        if (rc["company_code"], rc["quarter"]) in have_cells:
            raise SystemExit(f"abort: provenance cell exists {(rc['company_code'], rc['quarter'])}")
    prov["cells"] = prov["cells"] + recs
    prov["backfills"] = prov.get("backfills", []) + [{
        "stage": "reinsurers_lic_pdf_bs", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/load_ilp_reinsurers_lic.py", "ticket": TICKET,
        "note": f"items 10-15 of {len(recs)} reinsurer cells (뮌헨 KR1101, 하노버 KR1104, 퍼시픽 KR1107) from the 업무보고서식 재무상태표 block of the 경영공시 PDF"}]
    out = json.dumps(prov, ensure_ascii=False, indent=1) + "\n"
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, PROV)
    print(f"appended {len(new_rows)} rows; backup {backup.name}; provenance backup {pback.name}")


if __name__ == "__main__":
    main()
