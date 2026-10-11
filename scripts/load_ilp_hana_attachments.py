# -*- coding: utf-8 -*-
"""
ILP leftovers (ticket 20261011T1000Z, task 1): 하나손해보험(KR0050) items 10-15 for the 11 quarters whose 경영공시 PDF left the financial statements to an attachment
(2023.1Q-3Q, 2024.1Q-3Q, 2025.1Q-3Q, 2026.1Q-2Q).  Source = the separate 재무제표 및 주석 PDFs the downloader fetched into data/disclosure/FY*/attachments/
(reader: scripts/extract_insurance_liability_hana_attachment.py).  The three year-ends (2023.4Q, 2024.4Q, 2025.4Q) are already in the master from the DART 감사보고서; this loader
re-reads them from the Q4 감사보고서 attachment and only VERIFIES that the two sources agree (nothing is written for them).

Cell definition = the master's (class A2, DART 부채 기준, 별도, 억원 = 천원 / 100,000):
  14 잔여보장요소_합계 · 10 발생사고요소_합계 · 11 PAA BEL · 12 PAA RA · 13 GMM 단일열 · 15 보험계약부채_합계 (= the 재무상태표 보험계약부채).

Every cell must pass ALL of these or nothing is written (the whole run aborts):
  period      the 재무상태표 header date of the PDF is the quarter end
  foot        per table 잔여보장(손실요소 제외 + 손실요소) + 발생사고 = 합계 (rounding <= 1 천원 per table)
  anchor      sum of the table totals = the filing's own separate 재무상태표 보험계약부채 (원), <= max(3 천원, 1 ppm)  (R-LIC1 against the filing itself; the gap is recorded)
  R-LIC3      11 + 12 + 13 = 10 and 10 + 14 = 15 on the rounded 억원 values (0.0301)
  R-LIC2      net LRC of the notes vs item 8 of the master (2-4 table) where item 8 exists, max(0.5억, 0.5 %)   -> also shows that Hana's 2-4 does NOT contain the LIC
  CSM         GMM net CSM of the 측정요소별 table vs items 3 + 6, max(2억, 0.5 %)                              (informational: recorded, not a gate)
  comparative the next-year filing's 전분기/전기 column of the same quarter equals this reading (informational; the 2024.1Q filing prints the FULL-YEAR 2023 as 「전분기」)
Informational only (recorded in provenance, never a gate): IFRS17_BS item 20 of the BS lane, consolidated 재무상태표 line, the 보험계약자산 side (asset_side_eok).

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_hana_attachments.py [--write] [--report out.json]
Writes (with --write only): insurance_liability_portfolio.json (append-only, backed up) and insurance_liability_portfolio_provenance.json (cells + backfills, backed up).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_hana_attachment as hx  # noqa: E402
import extract_insurance_liability_lic as lic  # noqa: E402

PROV = REPO / "insurance_liability_portfolio_provenance.json"
TICKET = "inbox/parser/20261011T1000Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_leftovers_hana_attachments.md"
MANIFEST = "data/disclosure/_meta/attachments_manifest.json"
ITEMS = (10, 11, 12, 13, 14, 15)
TOL_ROUND = 0.0301


def items_from(c: dict) -> dict:
    return {10: hx.eok(c["lic"]), 11: hx.eok(c["bel"]), 12: hx.eok(c["ra"]), 13: hx.eok(c["single"]), 14: hx.eok(c["lrc"]), 15: hx.eok(c["total"])}


def evaluate(q: str, rec: dict, nxt: dict | None, M: dict, bs20: dict, consol_won: float | None) -> dict:
    """all checks of one quarter -> {'why': [...], ...numbers...}; an empty 'why' = the cell may be written"""
    c = rec["cur"]
    why = []
    it = items_from(c)
    if rec["period_ok"] is not True:
        why.append(f"period: 재무상태표 header dates {[d['date'] for d in rec['bs_dates']][:2]} != {hx.as_of(q)}")
    if c["n_tables"] < 2 or c["problems"]:
        why.append(f"tables: {c['n_tables']} issued-contract tables, problems {c['problems']}")
    if abs(c["foot_gap"]) > 1.0 * max(c["n_tables"], 1) + 1:
        why.append(f"foot: sum of (LRC + LIC - total) = {c['foot_gap']:.0f} 천원")
    bs = rec["bs_liab"]
    anchor_gap = None
    if bs is None:
        why.append("anchor: 재무상태표 보험계약부채 line not read")
    else:
        anchor_gap = c["total"] - bs["cur_won"] / 1000.0
        # 2026 filings print table totals a few 천원 away from the 재무상태표 (note 18 (1) itself shows the same gap, e.g. 2026.2Q 834,360,531 vs 834,360,515): tolerance 1 ppm
        if abs(anchor_gap) > max(3.0, 1e-6 * c["total"]):
            why.append(f"anchor: table totals {c['total']:,.0f} 천원 vs 재무상태표 {bs['cur_won'] / 1000:,.1f} 천원 (gap {anchor_gap:+.1f})")
    if abs((it[11] + it[12] + it[13]) - it[10]) > TOL_ROUND or abs(it[10] + it[14] - it[15]) > TOL_ROUND:
        why.append(f"R-LIC3 on rounded values: {it}")
    net_lrc = hx.eok(c["net_lrc"])
    i8 = M.get(q, {}).get(8)
    r2 = None
    if i8 is not None:
        d = i8 - net_lrc
        tol = max(0.5, 0.005 * abs(net_lrc))
        r2 = {"item8": i8, "net_lrc_eok": net_lrc, "diff": round(d, 2), "tol": round(tol, 2), "pass": abs(d) <= tol}
        if not r2["pass"]:
            why.append(f"R-LIC2: item 8 {i8} vs net LRC of the notes {net_lrc} (diff {d:+.2f}, tol {tol:.2f})")
    csm = None
    i3, i6 = M.get(q, {}).get(3), M.get(q, {}).get(6)
    if i3 is not None:
        n_csm = hx.eok(c["meas_net_csm"])
        d = (i3 + (i6 or 0.0)) - n_csm
        csm = {"item3_plus_6": i3 + (i6 or 0.0), "notes_net_csm_eok": n_csm, "diff": round(d, 2), "pass": abs(d) <= max(2.0, 0.005 * abs(n_csm))}
    cmpv = None
    if nxt is not None:
        keys = ("lrc", "lic", "bel", "ra", "single", "total")
        diffs = {k: round(c[k] - nxt["prior"][k], 1) for k in keys}
        cmpv = {"next_filing": nxt["file"], "tables_prior": nxt["prior"]["n_tables"], "max_abs_diff_chonwon": max(abs(v) for v in diffs.values()), "same": all(abs(v) <= 3 for v in diffs.values())}
    b = bs20.get(q)
    bsm = None
    if b is not None:
        ratio = c["total"] / 1000.0 / b if b else None
        bsm = {"bs20_mm": b, "ratio": round(ratio, 6) if ratio else None, "within_0_1pct": bool(ratio and abs(ratio - 1) <= lic.TOL_CLOSE)}
    return {"why": why, "items": it, "net_lrc_eok": net_lrc, "anchor_gap_chonwon": anchor_gap, "r_lic2": r2, "csm": csm, "comparative": cmpv, "bs_master": bsm,
            "consol_bs_liab_eok": None if consol_won is None else round(consol_won / 1e8, 4)}


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
        if r["원보험사코드"] == hx.CODE:
            M.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]
    bs20 = {q: v for (cc, q), v in lic.load_bs20().items() if cc == hx.CODE}
    reads = {q: hx.read_quarter(q) for q in hx.QUARTERS}
    consol = {}
    for q in hx.QUARTERS:
        rc = hx.read_pdf(hx.attachment_path(q, "consol"))
        consol[q] = rc["bs_liab"][0]["cur_won"] if rc["bs_liab"] else None

    plan, verify, bad = [], [], []
    for q in hx.QUARTERS:
        nq = f"{int(q[:4]) + 1}{q[4:]}"
        ev = evaluate(q, reads[q], reads.get(nq), M, bs20, consol[q])
        have = [n for n in ITEMS if n in M.get(q, {})]
        if have:
            same = len(have) == len(ITEMS) and all(abs(M[q][n] - ev["items"][n]) <= 0.011 for n in ITEMS)
            verify.append((q, same, ev))
            continue
        (bad if ev["why"] else plan).append((q, ev))

    print(f"quarters to fill: {len(plan)}  rejected: {len(bad)}  verify-only (already in master): {len(verify)}")
    for q, ev in plan:
        it = ev["items"]
        print(f"OK   {q}  10 {it[10]:>8,.2f} | 11 {it[11]:>8,.2f} | 12 {it[12]:>7,.2f} | 13 {it[13]:>7,.2f} | 14 {it[14]:>9,.2f} | 15 {it[15]:>9,.2f}   netLRC {ev['net_lrc_eok']:,.2f} item8 {None if not ev['r_lic2'] else ev['r_lic2']['item8']}"
              f"  CSM diff {None if not ev['csm'] else ev['csm']['diff']}  cmp-next {None if not ev['comparative'] else ev['comparative']['same']}  BS-master {None if not ev['bs_master'] else ev['bs_master']['ratio']}")
    for q, ev in bad:
        print(f"REJ  {q}: {ev['why']}")
    for q, same, ev in verify:
        print(f"VER  {q}: cell already in the master -> {'SAME as the attachment reading' if same else 'DIFFERENT (see report)'}  {ev['items']}")
    if args.report:
        Path(args.report).write_text(json.dumps({"plan": [{"q": q, **ev} for q, ev in plan], "rejected": [{"q": q, **ev} for q, ev in bad],
                                                 "verify": [{"q": q, "same": s, **ev} for q, s, ev in verify]}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if bad or any(not s for _, s, _ in verify):
        print("abort: rejected cells or a year-end disagreement -- nothing written")
        return 1
    if not args.write:
        print("dry run: nothing written (use --write)")
        return 0

    info = reg[hx.CODE]
    new_rows = []
    for q, ev in plan:
        for n in ITEMS:
            name, section, level = lic.ITEM_CATALOG[n]
            new_rows.append({"원보험사코드": hx.CODE, "원수사명": info["원수사명"], "티커": info["티커"], "생손보여부": info["생손보여부"], "항목번호": n, "항목명": name, "섹션": section,
                             "레벨": level, "공시분기": q, "값": ev["items"][n]})
    new_rows.sort(key=lambda r: (r["공시분기"], r["항목번호"]))
    backup = lic.merge_into_ilp(new_rows, tag="pre_hana_attachments")

    # ---------------- provenance (cell-level append; whole-file write only after the round-trip proof) ----------------
    raw0 = PROV.read_bytes()
    txt = raw0.decode("utf-8")
    prov = json.loads(txt)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance does not round-trip")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_hana_attachments.json"
    k = 2
    while pback.exists():
        pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_hana_attachments_{k}.json"
        k += 1
    shutil.copyfile(PROV, pback)
    have_cells = {(c["company_code"], c["quarter"]) for c in prov["cells"]}
    recs = []
    for q, ev in plan:
        if (hx.CODE, q) in have_cells:
            raise SystemExit(f"abort: provenance cell exists {(hx.CODE, q)}")
        rd, c = reads[q], reads[q]["cur"]
        b = bs20.get(q)
        bs_won = rd["bs_liab"]["cur_won"]
        total_mm = c["total"] / 1000.0
        bsm = ev["bs_master"]
        if b is not None and bsm and bsm["within_0_1pct"]:
            r_lic1, flags = "pass", ["pdf_source_no_dart_filing", "attachment_separate_fs"]
        else:
            r_lic1, flags = "pass_filing_anchor", ["pdf_source_no_dart_filing", "attachment_separate_fs", "bs20_master_absent_filing_anchor_used" if b is None else "bs20_master_disagrees_filing_anchor_used"]
        checks = {"r_lic1": r_lic1, "bs20_eok": None if b is None else lic.eok(b), "ratio_bs20": None if not bsm else bsm["ratio"],
                  "filing_bs_eok": round(bs_won / 1e8, 2), "ratio_filing_bs": round(c["total"] * 1000.0 / bs_won, 6), "filing_anchor_gap_chonwon": round(ev["anchor_gap_chonwon"], 1),
                  "r_lic3_gap_eok": round(ev["items"][10] + ev["items"][14] - ev["items"][15], 4),
                  "tag_tables": 0, "tag_cells": 0, "tag_mismatch": 0, "bs20_master_disagrees": bool(b is not None and not (bsm and bsm["within_0_1pct"])),
                  "r_lic2_vs_2_4": ev["r_lic2"], "csm_vs_2_4": ev["csm"], "comparative_in_next_year_filing": ev["comparative"]}
        recs.append({
            "company_code": hx.CODE, "quarter": q, "item_block": "lic_pdf_note", "source_id": "PDF", "as_of_date": lic.as_of_date(q), "source_file": rd["file"],
            "page": sorted({t["page"] for t in c["tables"]}), "scope": "separate", "period": "current", "class": "A2", "bel_ra_source": "RF", "basis": "liability",
            "row_basis": ["LIAB"], "unit": "천원", "unit_source": "cue",
            "tables": [{"table": None, "page": t["page"], "note": "18. 보험계약자산 및 보험계약부채", "unit": "천원", "unit_src": "cue", "period_src": "cue", "row": "LIAB",
                        "tot_eok": hx.eok(t["nums"][-1]), "model": t["model"], "lob": t["lob"], "section": t["section"]} for t in c["tables"]],
            "dropped_tables": [], "dedupe": [], "flags": flags, "checks": checks,
            "net_lrc_eok": ev["net_lrc_eok"], "items_eok": {str(n): ev["items"][n] for n in ITEMS},
            "asset_side_eok": {"total": hx.eok(c["asset_total"]), "lrc": hx.eok(c["asset_lrc"]), "lic": hx.eok(c["asset_lic"]),
                               "note": "보험계약자산 side of the same notes (signed as printed: asset rows); NOT in items 10-15 (liability basis). Liability-basis LIC understates the economic LIC "
                                       "when groups with a large incurred-claims balance sit in an asset position (2026.1Q-2Q: LIC asset side about -495 / -512억)."},
            "consolidated_bs_liab_eok": ev["consol_bs_liab_eok"],
            "attachment": {"kind": "separate_fs" if not q.endswith("4Q") else "audit_separate", "sha256": rd["sha256"], "manifest": MANIFEST, "ticket_downloader": "inbox/downloader/20261011T0830Z"},
            "evidence": "closing rows 「(2) 기말/분기말/반기말 보험계약부채」 of the issued-contract LRC/LIC movement tables (note 18; GMM and PAA 일반·자동차), 천원; "
                        + "; ".join(f"p{t['page']} {t['kind']} {t['nums']}" for t in c["tables"]),
            "note": "Hana's quarterly 경영공시 PDF leaves the financial statements to an attachment (별도 재무제표 및 주석); read from that attachment. Same definitions as the DART cells (class A2)."})
    prov["cells"] = prov["cells"] + recs
    prov["backfills"] = prov.get("backfills", []) + [{
        "stage": "hana-attachments-lic", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/load_ilp_hana_attachments.py", "ticket": TICKET,
        "note": f"items 10-15 of {len(recs)} KR0050 cells ({', '.join(q for q, _ in plan)}) from the 별첨 별도 재무제표 및 주석; backup {backup.name}",
        "year_end_crosscheck": {q: {"same_as_dart_master": s, "attachment_reading": ev["items"]} for q, s, ev in verify}}]
    out = json.dumps(prov, ensure_ascii=False, indent=1) + "\n"
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, PROV)
    print(f"appended {len(new_rows)} rows ({len(plan)} cells x {len(ITEMS)}); master backup {backup.name}; provenance backup {pback.name}; {len(recs)} provenance cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
