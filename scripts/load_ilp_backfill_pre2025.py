# -*- coding: utf-8 -*-
"""
Backfill of insurance_liability_portfolio.json before 2025.1Q (ticket 20261010T1600Z, owner doubt "BEL/RA are not
disclosed only from 2025.1Q").  STAGED: this run loads the two year-end points only (2024.4Q first, then 2023.4Q); the six
interim quarters 2023.1Q-2023.3Q / 2024.1Q-2024.3Q are a separate round and are refused here.

Rows added (append only, same schema/units as stage 1: 억원):
  items 1-8  LRC by measurement model (BEL/RA/CSM of 일반모형 and 변동수수료접근법, 보험료배분접근법 liability, total) =
             the 경영공시 year-end table 4-6-2 "회계모형별, 포트폴리오별 보험부채 현황" (net of 잔여보장자산)
               2024.4Q  <2024년> table of the FY2024 year-end PDF; the DART 사업보고서 note table of the same name is the
                        second reading (and the source where the PDF page is an image)
               2023.4Q  the <2023년> comparative table printed in the SAME FY2024 year-end PDF (most filers), else the 전기말
                        table of the FY2024 DART note.  The FY2023 filings themselves do not contain the table at all.
  item 9     해지율 예외모형 사용 여부 (4-6-6 "해당사항 없음" -> 0), only where the text says so
  items 10-15 발생사고요소(LIC) / 잔여보장요소 / 합계 from the DART roll-forward note of the year itself
             (scripts/extract_insurance_liability_lic.py, unchanged stage-1 engine + its repair ladder)

Every cell is reconciled before anything is written (nothing is written when --write is absent):
  R-LIC1  item 15 x100 vs IFRS17_BS item 20 (+-0.1 %)                          [done by the LIC engine, re-checked here]
  R-LIC3  items 11+12+13 = 10 and 10+14 = 15                                    [engine + here]
  R1      item 8 = sum of items 1..7
  R-LIC2  item 8 vs the DART NET remaining-coverage liability of the same year end (+-0.5 % or 0.5억; the three
          companies whose 2-4 total already contains the LIC are compared with item 15 instead)
  CSM     items 3+6 vs CSM_waterfall closing CSM (item 6), max(2억, 0.5 %)      [YELLOW only]
Cells that cannot be sourced are NOT written; each gets a recorded reason (provenance `not_loaded_lrc`).

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_backfill_pre2025.py --quarter 2024.4Q [--write]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
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
import extract_insurance_liability_model_pdf as mp  # noqa: E402
import extract_insurance_liability_model_xml as mx  # noqa: E402

STAGES = {"2024.4Q": {"lic_fy": "FY2024_Q4", "year": 2024}, "2023.4Q": {"lic_fy": "FY2023_Q4", "year": 2023}}
PDF_FY = "FY2024_Q4"                       # the year-end 경영공시 that carries 4-6-2 (and, for most filers, the 2023 comparative)
REINS = {f"KR11{n:02d}" for n in range(1, 9)}
ILP = REPO / "insurance_liability_portfolio.json"
PROV = REPO / "insurance_liability_portfolio_provenance.json"
BS = REPO / "IFRS17_BS.json"
CSMW = REPO / "CSM_waterfall.json"
SIDECAR_COS = {"KR0070", "KR0072", "KR0083"}   # 2-4 total already contains the LIC (data/_derived/ilp_includes_lic.json)
TOL_PDF_XML = 2.0                           # 억원: rounding between the PDF 합계 row and the exact note total
TOL_ITEM8_ABS, TOL_ITEM8_REL = 0.5, 0.005   # R-LIC2

MODEL_ITEMS = {
    1: ("일반모형_최선추정부채", 2), 2: ("일반모형_위험조정", 2), 3: ("일반모형_보험계약마진", 2),
    4: ("변동수수료접근법_최선추정부채", 2), 5: ("변동수수료접근법_위험조정", 2), 6: ("변동수수료접근법_보험계약마진", 2),
    7: ("보험료배분접근법_보험부채", 2), 8: ("보험부채_합계", 1),
}
SEC_MODEL = "보험부채_모형별구성"
SEC_LAPSE = "해지율_예외모형"
ITEM9_NAME = "무저해지상품_해지율_예외모형_사용여부"

# ---- cell-level decisions, each with its evidence (a rule per cell, never a silent patch) ---------------------------
# (code, year) -> dict(kind=..., ...)
OVERRIDES = {
    # 카카오페이손해보험 FY2024_Q4 경영공시 (image-only PDF, p15 rendered at 170 dpi and read by eye): 4-6-2 <2024년> 합계 row =
    # 일반모형 BEL (11.83) / RA 1.80 / CSM 4.61, 변동수수료 0.00 x3, 보험료배분접근법 3,313,095.  The PAA cell is printed under the
    # header (단위: 억원) but is in 천원: DART note T90 (PAA contracts) closes at 1,816,358 + 1,496,737 = 3,313,095 천원 and
    # (11.83)+1.80+4.61 = -5.42억 equals the DART roll-forward net LRC of the 일반모형 table T92 (-542,443 천원).  -> PAA 33.13095억.
    # The <2023년> table of the same page is all dashes while DART shows 27.7억 of liabilities at 2023-12-31 (first-year filer):
    # not read as zero, left empty.
    ("KR1098", 2024): {"kind": "manual", "items": {1: -11.83, 2: 1.80, 3: 4.61, 4: 0.0, 5: 0.0, 6: 0.0, 7: 33.13095},
                       "src": "PDF_image", "file": "data/disclosure/FY2024_Q4/raw/KR1098_카카오페이손해보험.pdf", "page": 15,
                       "evidence": "rendered p15 (170 dpi): 합계 (11.83) 1.80 4.61 0.00 0.00 0.00 3,313,095; PAA cell is 천원 under a 억원 header (DART T90 = 3,313,095 천원)"},
    ("KR1098", 2023): {"kind": "absent", "reason": "FY2024 경영공시 4-6-2 <2023년> table (p15) is all dashes, but DART shows 보험계약부채 27.7억 at 2023-12-31 "
                                                  "(LRC 16.9억 + LIC 10.8억): the dashes mean 'not prepared', not zero -> left empty"},
    # 캐롯손해보험: the filing says 4-6-2 .. 4-6-6 are 해당사항 없음 (장기손해보험 미영위), p20 text layer; no DART filing at all
    ("KR1059", 2024): {"kind": "absent", "reason": "FY2024 경영공시 p20: '당사 장기손해보험 미영위로 4-6-2) ~ 4-6-6) 해당사항 없음' (section not applicable); no DART filing"},
    ("KR1059", 2023): {"kind": "absent", "reason": "same filing: 4-6-2 not applicable (장기손해보험 미영위); no DART filing"},
}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def eok(x):
    return None if x is None else round(x + 0.0, 4)


def pdf_of(code, fy=PDF_FY):
    g = glob.glob(str(REPO / "data" / "disclosure" / fy / "raw" / f"{code}_*.pdf"))
    return Path(g[0]) if g else None


# --------------------------------------------------------------------------------------------------------------------
# readings
# --------------------------------------------------------------------------------------------------------------------
def read_pdf(code):
    """4-6-2 tables of the FY2024 year-end PDF: {'pdf', 'start', 'tables':[{year,page,run,slots(억원),kind,...}], 'source'} or None"""
    pdf = pdf_of(code)
    if pdf is None:
        return None
    start = mp.find_start_page(pdf)
    if start is None:
        return {"pdf": pdf, "start": None, "tables": [], "source": None, "unit": None}
    r = mp.read_tables(pdf, start)
    tabs = []
    for t in r["tables"]:
        tabs.append({"year": t["year"], "page": t["page"], "run": t["run"], "kind": t["kind"],
                     "items": mp.eok(t["slots"], t["unit_div"]) if t["slots"] else None, "unit": t["unit"], "unit_div": t["unit_div"]})
    return {"pdf": pdf, "start": start, "tables": tabs, "source": r["source"], "unit": r["unit"], "marks": r["marks"]}


def pdf_table_for(rd, year):
    """the table of the wanted year of one PDF reading, or None.  Year markers decide; without markers the filer prints the
    current year first and the prior year second (verified against the DART note tables for every filer that has both)."""
    if not rd or not rd["tables"]:
        return None, None
    tabs = rd["tables"]
    marked = [t for t in tabs if t["year"] == year]
    if marked:
        return marked[0], "marker"
    if all(t["year"] is None for t in tabs):
        idx = 0 if year == 2024 else 1
        if idx < len(tabs) and tabs[idx]["items"] is not None:
            return tabs[idx], "order"
    return None, None


def xml_candidates(code):
    """classified DART note tables of the FY2024 filings: {'cur': (rank,file,t,items), 'prior': ...}; main report before the
    separate-audit file, the consolidated audit file (_00761) is skipped, consolidated / reinsurance / value-less tables too"""
    out = {}
    base = REPO / "data" / "dart" / PDF_FY / "raw"
    cands = []
    for d in sorted(os.listdir(base)):
        if d[:6] != code:
            continue
        files = sorted(glob.glob(str(base / d / "*.xml"))) + sorted(glob.glob(str(base / d / "xml" / "*.xml")))
        seen = set()
        for f in files:
            k = (os.path.basename(f), os.path.getsize(f))
            if k in seen or f.endswith("_00761.xml"):
                continue
            seen.add(k)
            main = 0 if not f.endswith("_00760.xml") else 1
            for t in mx.classify(mx.harvest_file(f)):
                if t["con"] or t["reins"] or not any(x for m in t["vals"].values() for x in m.values()):
                    continue
                sc = mx.UNIT_TO_EOK.get(t["unit"])
                if sc is None:
                    continue
                items = mx.model_totals(t, sc)
                if all(items[i] is None for i in range(1, 8)):
                    continue            # a table with only a grand-total / unmapped columns is not the model table
                cands.append((main, -sum(len(m) for m in t["vals"].values()), t["i"], os.path.relpath(f, REPO).replace("\\", "/"), t, items))
    cands.sort(key=lambda x: x[:3])
    for per in ("cur", "prior"):
        sel = [c for c in cands if c[4]["period"] == per]
        if sel:
            main, _, i, f, t, items = sel[0]
            out[per] = {"file": f, "table": i, "unit": t["unit"], "period_src": t["period_src"], "items": items, "n_candidates": len(sel)}
    return out


def item9_from_pdf(pdf):
    """item 9 from the 4-6-6 section '무·저해지상품 해지율 예외모형 사용에 관한 사항': 0 when the section says 해당사항 없음.
    Returns (value|None, evidence).  Text layer only; an unreadable section stays empty."""
    import fitz
    if pdf is None:
        return None, None
    doc = fitz.open(str(pdf))
    try:
        for i in range(min(doc.page_count, 90)):
            t = doc[i].get_text("text") or ""
            tn = re.sub(r"\s+", "", t)
            tn = re.sub(r"([^\d,.\s])\1", r"\1", tn)
            m = re.search(r"무[·∙ㆍ.]?저해지상품해지율예외모형사용에관한사항", tn)
            if m and i + 1 > 3:
                tail = tn[m.end(): m.end() + 60]
                if "해당사항없음" in tail or "해당사항이없" in tail:
                    return 0, f"p{i + 1}: …{tn[m.start(): m.end() + 20]}"
                return None, f"p{i + 1}: section present but not 'none' ({tail[:30]})"
        return None, None
    finally:
        doc.close()


# --------------------------------------------------------------------------------------------------------------------
# one (company, year) LRC cell
# --------------------------------------------------------------------------------------------------------------------
def lrc_cell(code, year, rd, xc):
    ov = OVERRIDES.get((code, year))
    flags = []
    if ov and ov["kind"] == "absent":
        return {"status": "absent", "reason": ov["reason"]}
    if ov and ov["kind"] == "manual":
        items = dict(ov["items"])
        return {"status": "loaded", "items": items, "src": ov["src"], "file": ov["file"], "page": ov["page"], "table_year": year,
                "unit_in_source": "억원(+천원 PAA cell)", "run": None, "xml": None, "flags": ["manual_reading", "paa_cell_unit_chonwon"],
                "evidence": ov["evidence"]}
    pt, how = pdf_table_for(rd, year)
    xml = xc.get("cur" if year == 2024 else "prior")
    if pt is not None and pt["items"] is not None:
        items = {k: v for k, v in pt["items"].items()}
        cell = {"status": "loaded", "items": items, "src": "PDF", "file": os.path.relpath(rd["pdf"], REPO).replace("\\", "/"),
                "page": pt["page"], "table_year": year, "table_year_src": how, "unit_in_source": pt["unit"], "run": pt["run"],
                "run_kind": pt["kind"], "text_source": rd["source"], "xml": None, "flags": [] if rd["source"] == "pdfplumber" else ["text_via_fitz"]}
        if xml:
            d = max(abs((items.get(i) or 0.0) - (xml["items"].get(i) or 0.0)) for i in range(1, 8))
            cell["xml"] = {"file": xml["file"], "table": xml["table"], "unit": xml["unit"], "items": {k: eok(v) for k, v in xml["items"].items()},
                           "max_abs_diff_eok": round(d, 2)}
            if d > TOL_PDF_XML:
                cell["flags"].append(f"pdf_vs_dart_note_conflict_{d:.1f}eok")
        return cell
    if xml:
        items = {k: (v if v is not None else 0.0) for k, v in xml["items"].items()}
        return {"status": "loaded", "items": {k: eok(v) for k, v in items.items()}, "src": "DART_note", "file": xml["file"], "page": None,
                "table": xml["table"], "table_year": year, "unit_in_source": xml["unit"], "run": None, "xml": None,
                "flags": ["pdf_not_readable" if rd is None or not rd["tables"] else "pdf_table_missing_for_year"]}
    why = ("FY2024 경영공시 4-6-2 and FY2024 DART 사업보고서 note show no table for " + ("2024-12-31" if year == 2024 else "2023-12-31")
           + (" (text-layer pages read; 2023 comparative not printed)" if year == 2023 else ""))
    return {"status": "absent", "reason": why}


# --------------------------------------------------------------------------------------------------------------------
# provenance + writing helpers
# --------------------------------------------------------------------------------------------------------------------
def append_provenance(new_cells, new_not_loaded, new_lrc, new_lrc_absent, stage, tag, backup_dir):
    """additive, guarded merge into insurance_liability_portfolio_provenance.json (back up first, byte round-trip check)"""
    raw0 = PROV.read_bytes()
    txt = raw0.decode("utf-8")
    prov = json.loads(txt)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance file does not round-trip byte for byte; refusing to rewrite it")
    have = {(c["company_code"], c["quarter"]) for c in prov["cells"]}
    clash = [(c["company_code"], c["quarter"]) for c in new_cells if (c["company_code"], c["quarter"]) in have]
    if clash:
        raise SystemExit(f"abort: provenance cells already exist: {clash[:3]}")
    backup = backup_dir / f"ilp_provenance_backup_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{tag}.json"
    k = 2
    while backup.exists():
        backup = backup_dir / f"ilp_provenance_backup_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{tag}_{k}.json"
        k += 1
    shutil.copyfile(PROV, backup)
    prov["cells"] = prov["cells"] + new_cells
    prov["not_loaded"] = prov.get("not_loaded", []) + new_not_loaded
    prov["lrc_model_cells"] = prov.get("lrc_model_cells", []) + new_lrc
    prov["lrc_model_not_loaded"] = prov.get("lrc_model_not_loaded", []) + new_lrc_absent
    prov["backfills"] = prov.get("backfills", []) + [{
        "stage": stage, "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/load_ilp_backfill_pre2025.py",
        "ticket": "inbox/parser/20261010T1600Z__orchestrator__MULTI_2023.1Q-2024.4Q__ilp_backfill_pre2025.md",
        "note": ("items 1-8(/9) from the FY2024 year-end 경영공시 4-6-2 (PDF; DART note where the PDF is an image or unreadable) -> "
                 "lrc_model_cells; items 10-15 from the DART roll-forward of the year -> cells (same schema as stage 1)")}]
    out = json.dumps(prov, ensure_ascii=False, indent=1) + "\n"
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, PROV)
    return backup


def row(reg, code, q, n, name, section, level, value):
    info = reg[code]
    return {"원보험사코드": code, "원수사명": info["원수사명"], "티커": info["티커"], "생손보여부": info["생손보여부"],
            "항목번호": n, "항목명": name, "섹션": section, "레벨": level, "공시분기": q, "값": value}


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--quarter", required=True, help="2024.4Q or 2023.4Q (the interim quarters are a separate round)")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report", help="write the per-cell report json here")
    args = ap.parse_args(argv)
    if args.quarter not in STAGES:
        raise SystemExit(f"refused: only {sorted(STAGES)} are in scope of this round (owner priority); got {args.quarter}")
    st = STAGES[args.quarter]
    q, year = args.quarter, st["year"]
    lic.QMAP.update({"FY2023_Q4": "2023.4Q", "FY2024_Q4": "2024.4Q"})

    ilp = load(ILP)
    reg = lic.ilp_registry(ilp)
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in ilp}
    bs20 = lic.load_bs20()
    csmw = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in load(CSMW) if r["항목번호"] == 6}

    # ---- LIC (items 10-15) from the DART roll-forward of the year -----------------------------------------------------
    recs = lic.build_all(None, [st["lic_fy"]], verbose=True)
    rec_of = {r["code"]: r for r in recs}

    # ---- LRC (items 1-8, 9) --------------------------------------------------------------------------------------------
    codes = sorted(c for c in reg if c not in REINS)
    cells, absent = {}, {}
    for code in codes:
        rd = read_pdf(code)
        xc = xml_candidates(code)
        cell = lrc_cell(code, year, rd, xc)
        if cell["status"] == "loaded":
            if year == 2024:
                v9, ev9 = item9_from_pdf(pdf_of(code))
                cell["item9"], cell["item9_evidence"] = v9, ev9
            cells[code] = cell
        else:
            absent[code] = cell["reason"]
        print(f"{code} {q} LRC: {cell['status']:6s} {cell.get('src', ''):9s} " + (" ".join(f"{cell['items'][i]:.1f}" for i in range(1, 8)) if cell["status"] == "loaded" else cell["reason"][:100]),
              ("| " + ",".join(cell["flags"])) if cell.get("flags") else "", flush=True)

    # ---- reconciliation --------------------------------------------------------------------------------------------------
    red, yellow, table = [], [], []
    withheld = {}
    new_rows = []
    new_prov_cells, new_prov_notloaded = [], []
    loaded_lic = [r for r in recs if r["status"] == "loaded"]
    for r in recs:
        if r["status"] != "loaded":
            new_prov_notloaded.append({"company_code": r["code"], "quarter": r["quarter"], "reason": r["reason"]})
            red.append(f"LIC {r['code']} {q}: not loaded ({r['reason']})")
    lic_vals = {r["code"]: lic.cell_item_values(r) for r in loaded_lic}
    lic_rows = lic.new_ilp_rows(loaded_lic, reg)
    for code in codes:
        d = {}
        cell = cells.get(code)
        if cell:
            items = {i: round(cell["items"].get(i, 0.0), 4) for i in range(1, 8)}
            items[8] = round(sum(items[i] for i in range(1, 8)), 4)
            cell["items_final"] = items
            d.update(items)
            if cell.get("item9") is not None:
                d[9] = cell["item9"]
        lv = lic_vals.get(code, {})
        for n, vv in lv.items():
            d[n] = vv
        # reconciliation lines
        i8, i14, i15 = d.get(8), lv.get(14), lv.get(15)
        b = bs20.get((code, q))
        rec = rec_of.get(code)
        line = {"code": code, "item8": i8, "item15": i15, "bs20": None if b is None else round(b / 100.0, 2)}
        if i15 is not None and b:
            line["r_lic1_ppm"] = round((i15 * 100.0 / b - 1) * 1e6, 1)
        if lv:
            gap_a = (lv.get(11, 0.0) + lv.get(12, 0.0) + lv.get(13, 0.0)) - lv[10]
            gap_b = lv[10] + lv[14] - lv[15]
            if abs(gap_a) > 0.03 or abs(gap_b) > 0.03:
                red.append(f"R-LIC3 {code} {q}: gaps {gap_a:+.3f} / {gap_b:+.3f}")
        if cell and rec and rec["status"] == "loaded":
            net = rec["net_lrc_mm"] / 100.0
            alt = (rec["net_lrc_alt_mm"] / 100.0) if rec.get("net_lrc_alt_mm") is not None else None
            if code in SIDECAR_COS:
                ref, refname = i15, "item15 (2-4 contains LIC)"
                tol = max(5.0, 1e-4 * abs(ref))
            else:
                ref, refname = net, "DART net LRC"
                if alt is not None and abs(i8 - alt) < abs(i8 - net):
                    ref, refname = alt, "DART net LRC (alt asset sign)"
                tol = max(TOL_ITEM8_ABS, TOL_ITEM8_REL * abs(ref))
            diff = i8 - ref
            line.update({"ref": round(ref, 2), "ref_name": refname, "diff": round(diff, 2), "tol": round(tol, 2), "r_lic2": "pass" if abs(diff) <= tol else "DIFF"})
        elif cell and (rec is None or rec["status"] != "loaded"):
            line["r_lic2"] = "no_dart_lrc"
        cs = csmw.get((code, q))
        csm_bad = False
        if cell and cs is not None:
            c2 = d[3] + d[6]
            line.update({"csm_2_4": round(c2, 2), "csm_wf": round(cs, 2)})
            csm_bad = abs(c2 - cs) > max(2.0, 0.005 * abs(cs))
        # 2023.4Q only: the 2023-12-31 balances come from the COMPARATIVE column of the FY2024 filing, the other items of the same
        # cell (10-15, BS item 20, CSM_waterfall) from the FY2023 filing.  A filer that restated its comparative would put two
        # bases into one cell -- such a cell is withheld (values kept in provenance), never mixed.
        if year == 2023 and cell and (line.get("r_lic2") == "DIFF" or csm_bad):
            why = []
            if line.get("r_lic2") == "DIFF":
                why.append(f"item 8 {i8:,.1f} vs {line['ref_name']} of the FY2023 filing {line['ref']:,.2f} (diff {line['diff']:+,.1f}, tol {line['tol']:,.1f})")
            if csm_bad:
                why.append(f"CSM items 3+6 {c2:,.1f} vs CSM_waterfall closing {cs:,.1f}")
            withheld[code] = {"reason": "FY2024 comparative (2023-12-31) disagrees with the FY2023 original basis of the other items of this cell -> restated comparative "
                                        "or other basis, not mixed in: " + "; ".join(why),
                              "withheld_items_eok": {str(k): v for k, v in cell["items_final"].items()}, "source": cell["src"], "file": cell.get("file"), "page": cell.get("page")}
            line["withheld"] = True
        else:
            if line.get("r_lic2") == "DIFF":
                yellow.append(f"R-LIC2 {code} {q}: item 8 {i8:,.1f} vs {line['ref_name']} {line['ref']:,.2f} (diff {line['diff']:+,.1f}, tol {line['tol']:.1f})")
            if csm_bad:
                yellow.append(f"CSM {code} {q}: items 3+6 {c2:,.1f} vs CSM_waterfall closing {cs:,.1f}")
            if cell and cell.get("flags"):
                for fl in cell["flags"]:
                    if fl.startswith("pdf_vs_dart_note_conflict"):
                        yellow.append(f"CONFLICT {code} {q}: {fl} (PDF kept; DART note value in provenance)")
        if cell:
            cell["recon"] = {k: line.get(k) for k in ("ref_name", "ref", "diff", "tol", "r_lic2", "csm_2_4", "csm_wf", "item15", "bs20", "r_lic1_ppm") if line.get(k) is not None}
        table.append(line)
    for code, w in withheld.items():
        cells.pop(code, None)
        absent[code] = w["reason"]
        yellow.append(f"WITHHELD {code} {q}: {w['reason'][:230]}")

    # ---- rows to write -------------------------------------------------------------------------------------------------------
    for code in codes:
        cell = cells.get(code)
        if not cell:
            continue
        for n in range(1, 9):
            name, level = MODEL_ITEMS[n]
            new_rows.append(row(reg, code, q, n, name, SEC_MODEL, level, cell["items_final"][n]))
        if cell.get("item9") is not None:
            new_rows.append(row(reg, code, q, 9, ITEM9_NAME, SEC_LAPSE, 1, cell["item9"]))
    new_rows += lic_rows
    new_rows.sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))
    clash = [(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in new_rows if (r["원보험사코드"], r["공시분기"], r["항목번호"]) in have]
    if clash:
        raise SystemExit(f"abort: {len(clash)} key(s) already exist, e.g. {clash[:3]}")

    # provenance records
    gen = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    lic_prov = lic.build_provenance(recs, gen)
    new_prov_cells = lic_prov["cells"]
    lrc_prov = []
    for code, cell in sorted(cells.items()):
        lrc_prov.append({
            "company_code": code, "quarter": q, "item_block": "lrc_model_table_4-6-2", "source_id": cell["src"],
            "as_of_date": lic.as_of_date(q), "source_file": cell.get("file"), "page": cell.get("page"), "table": cell.get("table"),
            "table_year": cell["table_year"], "table_year_src": cell.get("table_year_src"), "unit_in_source": cell["unit_in_source"],
            "printed_run": cell.get("run"), "run_kind": cell.get("run_kind"), "text_source": cell.get("text_source"),
            "items_eok": {str(k): v for k, v in cell["items_final"].items()}, "item9": cell.get("item9"), "item9_evidence": cell.get("item9_evidence"),
            "dart_note_crosscheck": cell.get("xml"), "reconciliation": cell.get("recon"), "flags": cell.get("flags", []), "evidence": cell.get("evidence"),
            "published_in": ("FY2024 year-end 경영공시 / 사업보고서 (comparative column)" if year == 2023 else "FY2024 year-end 경영공시 / 사업보고서"),
        })
    lrc_absent = [{"company_code": c, "quarter": q, "items": "1-8", "reason": why, **({"detail": {k: v for k, v in withheld[c].items() if k != "reason"}} if c in withheld else {})}
                  for c, why in sorted(absent.items())]

    n_lrc = len(cells)
    print(f"\n{q}: LIC cells loaded {len(loaded_lic)}/{len(recs)}; LRC (1-8) cells {n_lrc}/{len(codes)}; rows to add {len(new_rows)}")
    print(f"RED {len(red)}  YELLOW {len(yellow)}")
    for x in red:
        print("  RED   ", x)
    for x in yellow:
        print("  YELLOW", x)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump({"quarter": q, "table": table, "red": red, "yellow": yellow, "absent_lrc": lrc_absent,
                       "lrc": lrc_prov, "lic_cells": new_prov_cells, "lic_not_loaded": new_prov_notloaded}, f, ensure_ascii=False, indent=1, default=str)
    if red:
        print("RED present: nothing written")
        return 1
    if not args.write:
        print("dry run: nothing written (use --write)")
        return 0
    tag = "pre_backfill_" + q.replace(".", "")
    backup = lic.merge_into_ilp(new_rows, tag=tag)
    pbackup = append_provenance(new_prov_cells, new_prov_notloaded, lrc_prov, lrc_absent, q, tag, lic.BACKUP_DIR)
    print(f"appended {len(new_rows)} rows to {ILP.name}; backup {backup.name}; provenance backup {pbackup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
