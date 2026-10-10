# -*- coding: utf-8 -*-
"""
Self-check for the 발생사고요소(LIC) items 10..17 of insurance_liability_portfolio.json
(stage 1 loads items 10..15 from the DART 보험계약부채 변동표).  Standalone, NOT a push gate
(precedent: validate_insurance_liability_portfolio.py); it does not import the extractor, so an
extraction bug cannot hide behind shared code.

Inputs (read only): insurance_liability_portfolio.json (items 8, 10..15), IFRS17_BS.json (item 20),
insurance_liability_portfolio_provenance.json (basis / class / net LRC / not-loaded reasons),
data/_derived/ilp_includes_lic.json (companies whose 2-4 total already contains the LIC),
data/dart/FY*/raw/*/meta.json (which cells have a DART filing at all).

Rules (units: ILP 억원, BS 백만원):
  R-LIC1  item 15 (보험계약부채_합계) x100 == IFRS17_BS item 20, +-0.1 %.  basis=net cells (the filer prints only
          NET rows) must sit 0..10 % BELOW item 20 (보험계약자산 offset); a cell without a BS item 20 is checked
          against the filing's own 재무상태표 recorded in the provenance (ratio_filing_bs, +-0.1 % or net band).
  R-LIC2  2-4 total (item 8) vs DART: item 8 ~ net LRC (provenance net_lrc_eok, +-0.5 % or 0.5억; where a table has no
          NET row and the ASSET row's sign convention is unknown the alternate net_lrc_alt_eok is also tried); for the
          companies in the sidecar ilp_includes_lic.json item 8 ~ item 15 (LRC+LIC) instead.  A mismatch is YELLOW
          (asset offsets / perimeter), not RED: the 2-4 table and the DART note are independent sources.
  R-LIC3  items 11+12+13 == item 10 (+-0.03억; class T: item 13 == item 10) and items 10+14 == item 15.
  CENSUS  expected grid = every (company, quarter) with a DART filing XML; each must be loaded or listed in the
          provenance with a reason; cells whose DART directory is no_filing are reported separately as SOURCE-ABSENT
          (normal blank, not a gap).
  R-LIC6  provenance <-> master: every item 10..15 row has a provenance cell with the same value and vice versa.
  R-LIC7  XBRL cross-check recorded by the extractor: tag_mismatch must be 0 on every tagged table.
  R-LIC8  every provenance source_file exists on disk (YELLOW if the raw was purged).

Exit code 1 when any RED.

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_insurance_liability_lic.py [--markdown OUT.md]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ILP = REPO / "insurance_liability_portfolio.json"
BS = REPO / "IFRS17_BS.json"
PROV = REPO / "insurance_liability_portfolio_provenance.json"
SIDECAR = REPO / "data" / "_derived" / "ilp_includes_lic.json"
RESTATED = REPO / "data" / "_derived" / "ilp_restated_comparative.json"
DART = REPO / "data" / "dart"

# 2026-10-10 backfill (ticket 20261010T1600Z): the grid grows with every pre-2025 quarter that is loaded (staged: the year-end
# points first, the six interim quarters in a later round).  Add a quarter here only together with its rows.
# 2026-10-11 (ticket 20261011T0320Z): the interim quarters follow, each added together with its rows.
QUARTERS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q",
            "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]
FY_OF = {"2023.1Q": "FY2023_Q1", "2023.2Q": "FY2023_Q2", "2023.3Q": "FY2023_Q3", "2023.4Q": "FY2023_Q4",
         "2024.1Q": "FY2024_Q1", "2024.2Q": "FY2024_Q2", "2024.3Q": "FY2024_Q3", "2024.4Q": "FY2024_Q4",
         "2025.1Q": "FY2025_Q1", "2025.2Q": "FY2025_Q2", "2025.3Q": "FY2025_Q3",
         "2025.4Q": "FY2025_Q4", "2026.1Q": "FY2026_Q1", "2026.2Q": "FY2026_Q2"}
LIC_ITEMS = (10, 11, 12, 13, 14, 15)
TOL_R1 = 0.001
TOL_ROUND = 0.0301        # 억원: three values each rounded to 0.01; the engine's own tolerance is 3 백만원 = 0.03억 (a hair of slack: 0.030 must not read as 0.0300000001)
NET_BAND = (0.90, 1.0)


def load(p: Path):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dart_inventory() -> dict:
    """{(code, quarter): 'filing' | 'no_filing'} from the raw directories"""
    out = {}
    for q, fy in FY_OF.items():
        base = DART / fy / "raw"
        if not base.is_dir():
            continue
        for d in sorted(os.listdir(base)):
            p = base / d
            if not p.is_dir():
                continue
            code = d[:6]
            has_xml = bool(glob.glob(str(p / "*.xml")) or glob.glob(str(p / "xml" / "*.xml")))
            nof = False
            mp = p / "meta.json"
            if mp.exists():
                try:
                    nof = bool(load(mp).get("no_filing"))
                except Exception:
                    nof = False
            state = "filing" if (has_xml and not nof) else "no_filing"
            if out.get((code, q)) != "filing":
                out[(code, q)] = state
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", help="also write the result tables as markdown to this path")
    args = ap.parse_args()

    ilp = load(ILP)
    bs = load(BS)
    prov = load(PROV)
    sidecar = load(SIDECAR) if SIDECAR.exists() else {"cells": []}
    # cells whose items 1-15 are on the LATEST filing's (restated) basis: the anchor of R-LIC1 is the sidecar's restated balance, not IFRS17_BS item 20
    # (original basis).  For the three 2023.4Q cells that value is the FY2024 balance sheet's prior-year column; for the interim cells (2024.1Q-3Q) it is derived
    # (the 2025 interim filings print no prior-year-quarter balance sheet) and the independent check is R-LIC2 against the restated DART net LRC.
    restated = {(c["company_code"], c["quarter"]): c for c in (load(RESTATED).get("cells", []) if RESTATED.exists() else [])}

    val = collections.defaultdict(dict)          # (code, q) -> {item: value}
    for r in ilp:
        val[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]
    bs20 = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in bs if r["항목번호"] == 20}
    pcell = {(c["company_code"], c["quarter"]): c for c in prov["cells"]}
    absent = {(c["company_code"], c["quarter"]): c["reason"] for c in prov.get("not_loaded", [])}
    incl = {(c["company_code"], c["quarter"]): c for c in sidecar.get("cells", [])}
    sidecar_cos = set(sidecar.get("companies", {}))
    indirect = {(c["company_code"], c["quarter"]): c for c in prov.get("indirect_lic_cells", [])}
    r9_cells = r9_adj = 0
    inv = dart_inventory()

    red, yellow, info = [], [], []
    cells = sorted(k for k, v in val.items() if any(n in v for n in LIC_ITEMS))
    rows_r1, rows_r2, rows_r3 = [], [], []

    for (code, q) in cells:
        v = val[(code, q)]
        pc = pcell.get((code, q))
        if pc is None:
            red.append(f"R-LIC6 {code} {q}: LIC rows without a provenance cell")
            continue
        # ---------------- R-LIC1 ----------------
        i15 = v.get(15)
        b = bs20.get((code, q))
        basis = pc["basis"]
        rs = restated.get((code, q))
        if i15 is None:
            red.append(f"R-LIC1 {code} {q}: item 15 missing")
        else:
            if rs is not None:
                rb = rs["restated_bs_insurance_contract_liability_eok"]
                ratio = i15 / rb if rb else float("inf")
                anchor = "restated_sidecar" + ("(derived)" if "derived" in str(rs.get("restated_bs_source", "")) else "")
                b = rb * 100.0
            elif pc["checks"].get("bs20_master_disagrees"):
                # IFRS17_BS item 20 disagrees with the filing's OWN separate balance sheet (which the note tables close with to < 1 ppm): the filing is the anchor
                ratio = pc["checks"].get("ratio_filing_bs")
                anchor = "filing_BS"
                b = (pc["checks"].get("filing_bs_eok") or 0.0) * 100.0 or None
                yellow.append(f"R-LIC1 {code} {q}: IFRS17_BS item 20 = {bs20.get((code, q), 0) / 100.0:,.2f}억 disagrees with the filing's own 별도 재무상태표 "
                              f"{pc['checks'].get('filing_bs_eok'):,.2f}억 (note tables close with the filing); anchor = filing -- BS-lane item")
            elif b is not None:
                ratio = i15 * 100.0 / b if b else float("inf")
                anchor = "BS20"
                rf_ = pc["checks"].get("ratio_filing_bs")
                if basis == "liability" and abs(ratio - 1) > TOL_R1 and rf_ is not None and abs(rf_ - 1) <= TOL_R1:
                    # the BS master moved after the cell was loaded (another lane writes IFRS17_BS.json) and now disagrees with the filing's own balance sheet that the
                    # note tables closed with: report it as a BS-lane item, anchor on the filing
                    yellow.append(f"R-LIC1 {code} {q}: IFRS17_BS item 20 = {b / 100.0:,.2f}억 disagrees with the filing's own 재무상태표 "
                                  f"{(pc['checks'].get('filing_bs_eok') or 0):,.2f}억 that item 15 = {i15:,.2f}억 closes with; anchor = filing -- BS-lane item")
                    ratio, anchor = rf_, "filing_BS"
            else:
                rf = pc["checks"].get("ratio_filing_bs")
                ratio = rf
                anchor = "filing_BS"
            if ratio is None:
                red.append(f"R-LIC1 {code} {q}: no anchor (no BS item 20 and no filing balance-sheet ratio)")
                status = "NO_ANCHOR"
            elif basis == "liability":
                status = "pass" if abs(ratio - 1) <= TOL_R1 else "FAIL"
                if status == "FAIL":
                    red.append(f"R-LIC1 {code} {q}: item 15 / {anchor} = {ratio:.5f} (basis=liability, tol 0.1 %)")
            else:
                status = "net_band" if NET_BAND[0] <= ratio < NET_BAND[1] else "FAIL"
                if status == "FAIL":
                    red.append(f"R-LIC1 {code} {q}: basis=net but item 15 / {anchor} = {ratio:.5f} outside 0.90..1.00")
                else:
                    yellow.append(f"R-LIC1 {code} {q}: basis=net, item 15 is {(1 - ratio) * 100:.2f} % below {anchor} (보험계약자산 offset not recoverable from the filer's NET-only rows)")
            rows_r1.append((code, q, basis, anchor, i15, b / 100.0 if b is not None else None, ratio, status))
        # ---------------- R-LIC3 ----------------
        i10, i11, i12, i13, i14 = (v.get(n) for n in (10, 11, 12, 13, 14))
        gap_a = None
        if i10 is not None and i13 is not None:
            split_sum = (i11 or 0.0) + (i12 or 0.0) + i13
            gap_a = split_sum - i10
            if abs(gap_a) > TOL_ROUND:
                red.append(f"R-LIC3 {code} {q}: items 11+12+13 = {split_sum:,.2f} vs item 10 = {i10:,.2f} (gap {gap_a:+.2f})")
        gap_b = None
        if None not in (i10, i14, i15):
            gap_b = i10 + i14 - i15
            if abs(gap_b) > TOL_ROUND:
                red.append(f"R-LIC3 {code} {q}: item 10 + item 14 = {i10 + i14:,.2f} vs item 15 = {i15:,.2f} (gap {gap_b:+.2f})")
        if pc["class"] == "T" and (i11 is not None or i12 is not None):
            red.append(f"R-LIC3 {code} {q}: class T must not carry items 11/12 (no BEL/RA split disclosed)")
        if pc["class"] in ("A1", "A2") and (i11 is None or i12 is None):
            red.append(f"R-LIC3 {code} {q}: class {pc['class']} must carry items 11 and 12")
        rows_r3.append((code, q, pc["class"], i10, i11, i12, i13, gap_a, gap_b))
        # RA / BEL plausibility (YELLOW)
        if pc["class"] in ("A1", "A2") and i11 and i12 is not None and i11 > 0:
            rt = i12 / i11
            if rt > 0.45:
                yellow.append(f"R-LIC3 {code} {q}: RA/BEL = {rt * 100:.1f} % (> 45 %) -- check column roles")
        # ---------------- R-LIC2 ----------------
        i8 = v.get(8)
        if i8 is not None:
            if (code, q) in incl:
                ref, refname = i15, "item 15 (LRC+LIC, sidecar: 2-4 already contains LIC)"
                tol = max(5.0, 1e-4 * abs(ref))
            else:
                ref, refname = pc.get("net_lrc_eok"), "DART net LRC"
                chk = (pc.get("checks_restated") or {}).get("chk_item8_minus_net_lrc")
                if rs is not None and chk is not None:
                    # 2023.4Q restated cells: the provenance keeps the ORIGINAL-basis net LRC; the restated one was recorded by the unify step
                    ref, refname = round(i8 - chk, 2), "DART net LRC (restated prior-year column)"
                alt = pc.get("net_lrc_alt_eok")
                if ref is not None and alt is not None and abs(i8 - alt) < abs(i8 - ref):
                    # the table has no NET row and an ASSET row of unknown sign convention: the closer candidate
                    ref, refname = alt, "DART net LRC (LIAB + ASSET row)"
                tol = max(0.5, 0.005 * abs(ref)) if ref is not None else None
            if ref is None or tol is None:
                rows_r2.append((code, q, i8, None, refname, None, "no_ref"))
            else:
                d = i8 - ref
                ok = abs(d) <= tol
                rows_r2.append((code, q, i8, ref, refname, d, "pass" if ok else "DIFF"))
                if not ok:
                    yellow.append(f"R-LIC2 {code} {q}: item 8 = {i8:,.1f} vs {refname} = {ref:,.2f} (diff {d:+,.1f}억, tol {tol:,.1f})")
        # ---------------- R-LIC6 / R-LIC7 ----------------
        for n in LIC_ITEMS:
            pv = pc["items_eok"].get(str(n))
            mv = v.get(n)
            if (pv is None) != (mv is None) or (pv is not None and abs(pv - mv) > 1e-9):
                red.append(f"R-LIC6 {code} {q} item {n}: master {mv} vs provenance {pv}")
        if not (REPO / pc["source_file"]).exists():
            yellow.append(f"R-LIC8 {code} {q}: source_file not on disk: {pc['source_file']}")
        if pc["checks"].get("tag_mismatch"):
            red.append(f"R-LIC7 {code} {q}: {pc['checks']['tag_mismatch']} XBRL role mismatch(es) recorded")
        # ---------------- R-LIC9: items 16/17 (stage 2, indirect BEL/RA, owner 2026-10-10 「계산값 사용」) ----------------
        i16, i17, i13 = v.get(16), v.get(17), v.get(13)
        if i16 is not None or i17 is not None:
            ic = indirect.get((code, q))
            if i16 is None or i17 is None:
                red.append(f"R-LIC9 {code} {q}: only one of items 16/17 present")
            elif ic is None:
                red.append(f"R-LIC9 {code} {q}: items 16/17 without an indirect_lic_cells provenance record")
            else:
                r9_cells += 1
                r9_adj += 1 if ic.get("asset_offset_adjusted") else 0
                if code in sidecar_cos:
                    red.append(f"R-LIC9 {code} {q}: items 16/17 for a company whose 2-4 total contains the LIC (never derived)")
                if ic.get("basis") != "derived":
                    red.append(f"R-LIC9 {code} {q}: provenance basis {ic.get('basis')!r} is not 'derived'")
                if i13 is None:
                    red.append(f"R-LIC9 {code} {q}: items 16/17 present but no direct single-column LIC (item 13) to reproduce")
                else:
                    tol9 = max(5.0, 5e-4 * abs(i13)) + 0.03      # owner criterion max(500 백만원, 0.05 %) + the rounding of two 0.01억 values
                    if abs(i16 + i17 - i13) > tol9:
                        red.append(f"R-LIC9 {code} {q}: item 16 + 17 = {i16 + i17:,.2f} vs item 13 = {i13:,.2f} (tol {tol9:.2f}억)")
                for n, mv in ((16, i16), (17, i17)):
                    pv = (ic.get("items_eok") or {}).get(str(n))
                    if pv is None or abs(pv - mv) > 1e-9:
                        red.append(f"R-LIC9 {code} {q} item {n}: master {mv} vs provenance {pv}")
    for k in pcell:
        if k not in set(cells):
            red.append(f"R-LIC6 {k[0]} {k[1]}: provenance cell without master rows")
    for k in indirect:
        if (v_ := val.get(k, {})).get(16) is None or v_.get(17) is None:
            red.append(f"R-LIC9 {k[0]} {k[1]}: indirect_lic_cells record without master items 16/17")

    # ---------------- CENSUS ----------------
    codes = sorted({r["원보험사코드"] for r in bs})          # the 39-company universe of IFRS17_BS.json
    expected = [(c, q) for c in codes for q in QUARTERS if inv.get((c, q)) == "filing"]
    # source-absent = every grid cell without a DART filing: an explicit no_filing marker (meta.json) or no DART
    # directory at all (the 비상장사 have no 분기/반기보고서; they file only the 사업보고서/감사보고서 = 4Q)
    source_absent = [(c, q) for c in codes for q in QUARTERS if inv.get((c, q)) != "filing"]
    absent_marked = [k for k in source_absent if inv.get(k) == "no_filing"]
    loaded = set(cells)
    gaps, documented = [], []
    for k in expected:
        if k in loaded:
            continue
        if k in absent:
            documented.append((k, absent[k]))
        else:
            gaps.append(k)
    for k in gaps:
        red.append(f"CENSUS {k[0]} {k[1]}: DART filing exists but the cell is neither loaded nor documented as not loaded")
    # cells of the two non-listed filers whose 경영공시 PDF carries the incurred-claims component (stage 3: 라이나 notes, 처브 balance sheet) have no DART filing by
    # design: their provenance says source_id = "PDF"
    pdf_cells = {k for k, c in pcell.items() if c.get("source_id") == "PDF"}
    extra = sorted(loaded - set(expected) - pdf_cells)
    for k in extra:
        red.append(f"CENSUS {k[0]} {k[1]}: rows loaded for a cell without a DART filing")
    grid_cells = len(codes) * len(QUARTERS)

    # ---------------- report ----------------
    cls = collections.Counter(pcell[k]["class"] for k in cells if k in pcell)
    r1 = collections.Counter(x[7] for x in rows_r1)
    r2 = collections.Counter(x[6] for x in rows_r2)
    out = []
    out.append("=== insurance_liability_portfolio.json  LIC items 10-15 self-check ===")
    out.append(f"cells with LIC rows: {len(cells)}  by class: {dict(sorted(cls.items()))}")
    out.append(f"census: grid {len(codes)} companies x {len(QUARTERS)} quarters = {grid_cells}; DART filing {len(expected)}; "
               f"loaded {len(loaded & set(expected))}; documented not-loaded {len(documented)}; "
               f"source-absent (normal blank, not a gap) {len(source_absent)} = {len(absent_marked)} with a no_filing marker + "
               f"{len(source_absent) - len(absent_marked)} without any DART directory; undocumented gaps {len(gaps)}; PDF-sourced cells (no DART filing by design) {len(pdf_cells)}")
    for k, why in documented:
        out.append(f"  documented not-loaded {k[0]} {k[1]}: {why}")
    out.append(f"R-LIC1 results: {dict(r1)}")
    out.append(f"R-LIC2 results: {dict(r2)}  (sidecar cells: {len(incl)})")
    out.append(f"R-LIC3 checked cells: {len(rows_r3)}")
    out.append(f"R-LIC9 (items 16/17, indirect BEL/RA) checked cells: {r9_cells}  (of which 보험계약자산 상계 보정 {r9_adj})")
    out.append(f"\n--- RED ({len(red)}) ---")
    out += ["  " + x for x in red]
    out.append(f"\n--- YELLOW ({len(yellow)}) ---")
    out += ["  " + x for x in yellow[:60]]
    if len(yellow) > 60:
        out.append(f"  ... and {len(yellow) - 60} more")
    out.append(f"\nSUMMARY RED={len(red)} YELLOW={len(yellow)} documented_not_loaded={len(documented)} source_absent={len(source_absent)}")
    text = "\n".join(out)
    print(text)

    if args.markdown:
        md = ["# LIC items 10-15 self-check result tables (generated by scripts/validate_insurance_liability_lic.py)", "",
              "## R-LIC1  item 15 x100 vs IFRS17_BS item 20 (백만원)", "",
              "| company | quarter | basis | anchor | item 15 (억) | anchor (억) | ratio | status |", "|---|---|---|---|---|---|---|---|"]
        for code, q, basis, anchor, i15, b, ratio, status in rows_r1:
            md.append(f"| {code} | {q} | {basis} | {anchor} | {i15:,.2f} | {'' if b is None else f'{b:,.2f}'} | {'' if ratio is None else f'{ratio:.5f}'} | {status} |")
        md += ["", "## R-LIC2  2-4 item 8 vs DART net LRC (or item 15 for the sidecar companies)", "",
               "| company | quarter | item 8 (억) | reference (억) | reference | diff | status |", "|---|---|---|---|---|---|---|"]
        for code, q, i8, ref, refname, d, status in rows_r2:
            md.append(f"| {code} | {q} | {i8:,.1f} | {'' if ref is None else f'{ref:,.2f}'} | {refname} | {'' if d is None else f'{d:+,.2f}'} | {status} |")
        md += ["", "## R-LIC3  split identity", "",
               "| company | quarter | class | item 10 | item 11 | item 12 | item 13 | 11+12+13-10 | 10+14-15 |", "|---|---|---|---|---|---|---|---|---|"]
        f2 = lambda x: "" if x is None else f"{x:,.2f}"
        for code, q, k, i10, i11, i12, i13, ga, gb in rows_r3:
            md.append(f"| {code} | {q} | {k} | {f2(i10)} | {f2(i11)} | {f2(i12)} | {f2(i13)} | {'' if ga is None else f'{ga:+.2f}'} | {'' if gb is None else f'{gb:+.2f}'} |")
        with open(args.markdown, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(md) + "\n")
    return 1 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
