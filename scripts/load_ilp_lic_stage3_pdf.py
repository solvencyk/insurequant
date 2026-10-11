# -*- coding: utf-8 -*-
"""
LIC stage 3 (ticket 20261011T0320Z): the two non-listed filers that print the incurred-claims component in their 경영공시 PDF although DART has no 분기·반기보고서.
Adds items 10-15 (same definitions, 억원, section 보험부채_발생사고요소) to insurance_liability_portfolio.json, additive, one provenance cell per (company, quarter)
(source_id = "PDF"):

  KR0074 라이나생명  the PDF carries the full notes (천원).  Note 「보험계약부채 내 잔여보장부채와 발생사고부채의 변동 내역」 has a <당분기> table and a <전분기> table
                     (= the same quarter one year earlier); the closing row 「기말 보험계약부채」 (liability basis) gives  LRC = 손실요소 이외 + 손실요소,  LIC = 발생사고부채 (ONE
                     column -> class T: items 10, 13, 14, 15),  total = 합계.  <당분기> of FY2025_Q1..Q3, FY2026_Q1..Q2 -> 2025.1Q..2026.2Q; <전분기> of FY2025_Q1..Q3 -> 2024.1Q..3Q.
  KR0100 처브라이프  the 업무보고서식 재무상태표 lists 「보험계약부채 / 나. 발생사고요소 / (1) 최선추정 (2) 위험조정」 (원) -> class A1 (items 10-15, 13 = 0), FY2025_Q1..Q3 only
                     (the 2026 PDFs are summaries without the balance sheet).

Checks per cell (all must pass, nothing is written otherwise):  item 15 x100 = IFRS17_BS item 20 within 0.1 % (R-LIC1) · 11+12+13 = 10, 10+14 = 15 (R-LIC3) · for 라이나 the
net closing row 「기말 잔액」 = item 8 of the 2-4 table within max(0.5억, 0.5 %) (R-LIC2).

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_lic_stage3_pdf.py [--write] [--report out.json]
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

import pdfplumber

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as lic  # noqa: E402
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

PROV = REPO / "insurance_liability_portfolio_provenance.json"
TICKET = "inbox/parser/20261011T0320Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_remaining_backfill_lic23_reinsurers.md"
NUM = r"\(?-?[\d,]+\)?"


def pdf_of(code, fy):
    g = disclosure_pdfs(fy, code)
    return g[0] if g else None


def to_num(tok):
    tok = tok.strip()
    neg = tok.startswith("(") and tok.endswith(")")
    v = float(tok.strip("()").replace(",", ""))
    return -v if neg else v


def row_numbers(line, n):
    """the last n number tokens of a text line, or None"""
    toks = re.findall(r"\(?-?\d[\d,]*\)?|(?<=\s)-(?=\s|$)", line)
    if len(toks) < n:
        return None
    out = []
    for t in toks[-n:]:
        out.append(0.0 if t == "-" else to_num(t))
    return out


# ------------------------------------------------------------------------------------------------------------------------------
# 라이나
# ------------------------------------------------------------------------------------------------------------------------------
def lina_tables(pdf_path):
    """{'cur': {...}, 'prior': {...}} closing rows (천원) of the issued-contract LRC/LIC note; the first <당분기>/<전분기> pair that follows the heading"""
    out = {}
    with pdfplumber.open(str(pdf_path)) as pdf:
        n = len(pdf.pages)
        heading_page = None
        for i in range(n):
            t = pdf.pages[i].extract_text() or ""
            flat = re.sub(r"\s+", "", t)
            if "보험계약부채내잔여보장부채와발생사고부채의변동" in flat and "출재" not in flat[:flat.find("보험계약부채내잔여보장부채와발생사고부채의변동") + 60]:
                heading_page = i
                break
        if heading_page is None:
            return out, None
        # the note may be split by product section ('① 유배당 보험', '② 유배당 외 보험'; 2026): the closing rows of every section are added up.  The note ends where the
        # next numbered note heading '(5) ... 측정요소별' starts.
        sec, which, secs = "0", None, {}
        for i in range(heading_page, min(heading_page + 14, n)):
            t = pdf.pages[i].extract_text() or ""
            stop = False
            for line in t.split("\n"):
                s = line.strip()
                if re.match(r"^\(5\)\s", s) or re.match(r"^\(\d+\)\s*당(분|반)기 및 전(분|반)기 중 .*측정요소", s):
                    stop = True
                    break
                m_sec = re.match(r"^([①②③④⑤⑥⑦⑧⑨])\s", s)
                if m_sec:
                    sec, which = m_sec.group(1), None
                if re.match(r"^<\s*(당분기|당반기)\s*>", s):
                    which = "cur"
                elif re.match(r"^<\s*(전분기|전반기)\s*>", s):
                    which = "prior"
                if which is None:
                    continue
                m = re.match(r"^(기말\s*보험계약자산|기말\s*보험계약부채|기말\s*잔액)\s+(.*)$", s)
                key = re.sub(r"\s+", "", m.group(1)) if m else None
                rec = secs.setdefault((sec, which), {})
                if key and key not in rec:
                    nums = row_numbers(s, 4)
                    if nums:
                        rec[key] = {"lrc_ex_loss": nums[0], "loss": nums[1], "lic": nums[2], "total": nums[3], "line": s[:140], "page": i + 1}
            if stop:
                break
        for (sec_, which_), rec in secs.items():
            agg = out.setdefault(which_, {"_sections": []})
            agg["_sections"].append(sec_)
            for key, r in rec.items():
                a = agg.get(key)
                if a is None:
                    agg[key] = dict(r)
                else:
                    for f in ("lrc_ex_loss", "loss", "lic", "total"):
                        a[f] += r[f]
                    a["line"] += " + " + r["line"][:60]
    return out, heading_page + 1


def lina_cells(M, bs20):
    cells, notes = [], []
    plan = [("FY2025_Q1", "cur", "2025.1Q"), ("FY2025_Q1", "prior", "2024.1Q"), ("FY2025_Q2", "cur", "2025.2Q"), ("FY2025_Q2", "prior", "2024.2Q"),
            ("FY2025_Q3", "cur", "2025.3Q"), ("FY2025_Q3", "prior", "2024.3Q"), ("FY2026_Q1", "cur", "2026.1Q"), ("FY2026_Q2", "cur", "2026.2Q")]
    cache = {}
    for fy, which, q in plan:
        pdf = pdf_of("KR0074", fy)
        if pdf is None:
            notes.append((q, "no PDF"))
            continue
        if fy not in cache:
            cache[fy] = lina_tables(pdf)
        tabs, page = cache[fy]
        t = tabs.get(which)
        if not t or "기말보험계약부채" not in t:
            notes.append((q, f"closing liability row not read ({fy} {which})"))
            continue
        L = t["기말보험계약부채"]
        net = t.get("기말잔액")
        lrc_mm = (L["lrc_ex_loss"] + L["loss"]) / 1000.0           # 천원 -> 백만원
        lic_mm = L["lic"] / 1000.0
        tot_mm = L["total"] / 1000.0
        gap = lrc_mm + lic_mm - tot_mm
        anchor = bs20.get(("KR0074", q))
        item8 = M.get(("KR0074", q), {}).get(8)
        cell = {"code": "KR0074", "quarter": q, "fy": fy, "which": which, "file": str(pdf.relative_to(REPO)).replace("\\", "/"), "page": L["page"],
                "lrc_mm": lrc_mm, "lic_mm": lic_mm, "total_mm": tot_mm, "foot_gap_mm": gap, "bs20_mm": anchor, "item8": item8,
                "net_lrc_mm": ((net["lrc_ex_loss"] + net["loss"]) / 1000.0) if net else None, "line": L["line"], "class": "T"}
        cells.append(cell)
    return cells, notes


# ------------------------------------------------------------------------------------------------------------------------------
# 처브라이프
# ------------------------------------------------------------------------------------------------------------------------------
def chubb_cells(M, bs20):
    cells, notes = [], []
    for fy, q in (("FY2025_Q1", "2025.1Q"), ("FY2025_Q2", "2025.2Q"), ("FY2025_Q3", "2025.3Q")):
        pdf = pdf_of("KR0100", fy)
        if pdf is None:
            notes.append((q, "no PDF"))
            continue
        with pdfplumber.open(str(pdf)) as doc:
            txt, pg = "", []
            for i in range(len(doc.pages)):
                t = doc.pages[i].extract_text() or ""
                if "발생사고요소" in t and "보험계약부채" in t:
                    txt += "\n" + t
                    pg.append(i + 1)
        # liability side: the block that starts at '1. 보험계약부채' (not 재보험계약부채), 잔여보장요소 ... 발생사고요소 (1) (2)
        lines = txt.split("\n")
        idx = next((k for k, s in enumerate(lines) if re.match(r"^1\.\s*보험계약부채\s", s)), None)
        if idx is None:
            notes.append((q, "liability block '1. 보험계약부채' not found"))
            continue
        blk = lines[idx: idx + 16]
        rec = {}
        for s in blk:
            ss = s.strip()
            if ss.startswith("1. 보험계약부채"):
                rec["total"] = row_numbers(ss, 2)
            elif ss.startswith("가. 잔여보장요소"):
                rec["lrc"] = row_numbers(ss, 2)
            elif ss.startswith("나. 발생사고요소"):
                rec["lic"] = row_numbers(ss, 2)
            elif ss.startswith("(1) 최선추정") and "lic" in rec and "bel" not in rec:
                rec["bel"] = row_numbers(ss, 2)
            elif ss.startswith("(2) 위험조정") and "bel" in rec and "ra" not in rec:
                rec["ra"] = row_numbers(ss, 2)
            if "ra" in rec:
                break
        if not all(k in rec and rec[k] for k in ("total", "lrc", "lic", "bel", "ra")):
            notes.append((q, f"incomplete block {rec}"))
            continue
        # column 0 = 당분기말, column 1 = 전기말 (원)
        won = lambda k: rec[k][0] / 1e6                     # 원 -> 백만원
        cell = {"code": "KR0100", "quarter": q, "fy": fy, "file": str(pdf.relative_to(REPO)).replace("\\", "/"), "page": pg[:3],
                "lrc_mm": won("lrc"), "lic_mm": won("lic"), "total_mm": won("total"), "bel_mm": won("bel"), "ra_mm": won("ra"),
                "foot_gap_mm": won("lrc") + won("lic") - won("total"), "bs20_mm": bs20.get(("KR0100", q)), "item8": M.get(("KR0100", q), {}).get(8), "net_lrc_mm": None,
                "class": "A1", "prior_col_check": {"lic_prior_mm": rec["lic"][1] / 1e6, "bel_prior_mm": rec["bel"][1] / 1e6, "ra_prior_mm": rec["ra"][1] / 1e6}}
        cells.append(cell)
    return cells, notes


def eok(mm):
    return round(mm / 100.0, 2) + 0.0


def evaluate(cells, M):
    """decide each cell; returns (accepted, rejected, red)"""
    acc, rej = [], []
    for c in cells:
        why = []
        if abs(c["foot_gap_mm"]) > 0.5:
            why.append(f"LRC + LIC != total by {c['foot_gap_mm']:.2f} 백만원")
        b = c["bs20_mm"]
        if b is None:
            why.append("no IFRS17_BS item 20 to close against")
        elif abs(c["total_mm"] / b - 1) > 0.001:
            why.append(f"item 15 / BS item 20 = {c['total_mm'] / b:.5f} (> 0.1 %)")
        if c.get("item8") is not None and c.get("net_lrc_mm") is not None:
            ref = c["net_lrc_mm"] / 100.0
            if abs(c["item8"] - ref) > max(0.5, 0.005 * abs(ref)):
                why.append(f"item 8 {c['item8']:,.1f} vs net closing row {ref:,.2f}")
        (rej if why else acc).append((c, why))
    return acc, rej


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report")
    args = ap.parse_args(argv)
    ilp = json.loads(lic.ILP.read_text(encoding="utf-8"))
    reg = lic.ilp_registry(ilp)
    M = {}
    for r in ilp:
        M.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    bs20 = lic.load_bs20()
    cells, notes = [], []
    for fn in (lina_cells, chubb_cells):
        c, n = fn(M, bs20)
        cells += c
        notes += n
    for q, why in notes:
        print("NOTE", q, why)
    acc, rej = evaluate(cells, M)
    for c, _ in acc:
        print(f"OK   {c['code']} {c['quarter']} {c['class']:2s} LIC {eok(c['lic_mm']):,.2f} LRC {eok(c['lrc_mm']):,.2f} total {eok(c['total_mm']):,.2f} vs BS20 {c['bs20_mm'] / 100:,.2f} "
              f"| item8 {c['item8']} net row {None if c['net_lrc_mm'] is None else round(c['net_lrc_mm'] / 100, 2)} ({c['file'].split('/')[-3]} p{c['page']})")
    for c, why in rej:
        print(f"REJ  {c['code']} {c['quarter']}: {why}")
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in ilp}
    new_rows = []
    for c, _ in acc:
        info = reg[c["code"]]
        vals = {10: eok(c["lic_mm"]), 14: eok(c["lrc_mm"]), 15: eok(c["total_mm"])}
        if c["class"] == "A1":
            vals.update({11: eok(c["bel_mm"]), 12: eok(c["ra_mm"]), 13: 0.0})
        else:
            vals[13] = eok(c["lic_mm"])
        for n, v in sorted(vals.items()):
            if (c["code"], c["quarter"], n) in have:
                raise SystemExit(f"abort: key exists {(c['code'], c['quarter'], n)}")
            name, section, level = lic.ITEM_CATALOG[n]
            new_rows.append({"원보험사코드": c["code"], "원수사명": info["원수사명"], "티커": info["티커"], "생손보여부": info["생손보여부"], "항목번호": n, "항목명": name,
                             "섹션": section, "레벨": level, "공시분기": c["quarter"], "값": v})
        # R-LIC3 on the rounded values (the validator's own tolerance)
        v = vals
        if abs((v.get(11, 0.0) + v.get(12, 0.0) + v[13]) - v[10]) > 0.0301 or abs(v[10] + v[14] - v[15]) > 0.0301:
            raise SystemExit(f"abort: rounded identity broken for {c['code']} {c['quarter']}: {v}")
    new_rows.sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))
    print(f"accepted cells {len(acc)}, rejected {len(rej)}, rows to add {len(new_rows)}")
    if args.report:
        Path(args.report).write_text(json.dumps({"accepted": [c for c, _ in acc], "rejected": [{"cell": c, "why": w} for c, w in rej], "notes": notes}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if rej or not args.write:
        print("dry run / rejected cells present: nothing written" if rej else "dry run: nothing written (use --write)")
        return 1 if rej and args.write else 0
    backup = lic.merge_into_ilp(new_rows, tag="pre_lic_stage3")
    raw0 = PROV.read_bytes()
    txt = raw0.decode("utf-8")
    prov = json.loads(txt)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance does not round-trip")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_lic_stage3.json"
    k = 2
    while pback.exists():
        pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_lic_stage3_{k}.json"
        k += 1
    shutil.copyfile(PROV, pback)
    have_cells = {(c["company_code"], c["quarter"]) for c in prov["cells"]}
    recs = []
    for c, _ in acc:
        if (c["code"], c["quarter"]) in have_cells:
            raise SystemExit(f"abort: provenance cell exists {(c['code'], c['quarter'])}")
        vals = {10: eok(c["lic_mm"]), 14: eok(c["lrc_mm"]), 15: eok(c["total_mm"])}
        if c["class"] == "A1":
            vals.update({11: eok(c["bel_mm"]), 12: eok(c["ra_mm"]), 13: 0.0})
        else:
            vals[13] = eok(c["lic_mm"])
        b = c["bs20_mm"]
        recs.append({
            "company_code": c["code"], "quarter": c["quarter"], "item_block": "lic_pdf_note" if c["code"] == "KR0074" else "lic_pdf_bs", "source_id": "PDF",
            "as_of_date": lic.as_of_date(c["quarter"]), "source_file": c["file"], "page": c["page"], "scope": "separate", "period": "current" if c.get("which", "cur") == "cur" else "prior-year same quarter (<전분기> table of the later filing)",
            "class": c["class"], "bel_ra_source": "RF" if c["class"] == "A1" else "none", "basis": "liability", "row_basis": ["LIAB"], "unit": "천원" if c["code"] == "KR0074" else "원", "unit_source": "cue",
            "tables": [], "dropped_tables": [], "dedupe": [], "flags": ["pdf_source_no_dart_filing"] + (["comparative_of_later_filing"] if c.get("which") == "prior" else []),
            "checks": {"r_lic1": "pass", "bs20_eok": eok(b), "ratio_bs20": round(c["total_mm"] / b, 6), "filing_bs_eok": None, "ratio_filing_bs": None,
                       "r_lic3_gap_eok": round(c["foot_gap_mm"] / 100.0, 4), "tag_tables": 0, "tag_cells": 0, "tag_mismatch": 0},
            "net_lrc_eok": (eok(c["net_lrc_mm"]) if c.get("net_lrc_mm") is not None else None),       # 처브: no net closing row (R-LIC2 not applicable: its 2-4 holds the 변액연금 Direct-Par book)
            "items_eok": {str(n): v for n, v in sorted(vals.items())}, "evidence": c.get("line"),
            "note": ("closing row 「기말 보험계약부채」 of the issued-contract LRC/LIC note in the 경영공시 PDF (천원)" if c["code"] == "KR0074" else
                     "업무보고서식 재무상태표 「1. 보험계약부채 / 나. 발생사고요소 / (1) 최선추정 (2) 위험조정」 (원); the prior-year-end column of the same page equals the DART 2024.4Q cell")})
    prov["cells"] = prov["cells"] + recs
    prov["backfills"] = prov.get("backfills", []) + [{"stage": "lic-stage3-pdf", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"),
                                                      "emitted_by": "scripts/load_ilp_lic_stage3_pdf.py", "ticket": TICKET,
                                                      "note": f"items 10-15 of {len(recs)} cells of two non-listed filers from the 경영공시 PDF (라이나 notes, 처브 balance sheet)"}]
    out = json.dumps(prov, ensure_ascii=False, indent=1) + "\n"
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, PROV)
    print(f"appended {len(new_rows)} rows; backup {backup.name}; provenance backup {pback.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
