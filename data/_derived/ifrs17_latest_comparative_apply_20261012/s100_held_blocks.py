"""Build held_blocks.csv (UTF-8 with BOM): every dry-run block / cell / finding that was NOT written by the apply, with the reason.

Sections
  A  dry-run 'adopt' verdict blocks that were not applied (block level)
  B  cells removed from blocks that WERE applied (cell level)
  C  all other dry-run census verdicts except '변화 없음' (nothing to change): gold conflict, 현행 유지, 둘 다 불가, 조건부, 후보 미검증, 추출 불가, 재판정 안 함
  D  the 9 'new findings' of the dry run and what became of each
  E  3-month-as-cumulative scan: what could not be verified directly (listed, not changed)
  F  other observations (not changed, outside this ticket)
Read-only on every input; writes only held_blocks.csv in this folder.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DR = ROOT / "data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012"
plan = json.loads((HERE / "plan_final.json").read_text(encoding="utf-8"))
census = list(csv.DictReader(open(DR / "census_blocks.csv", encoding="utf-8-sig")))
applied_blocks = {(c["master"], c["code"], c["quarter"]) for c in plan["cells"] if c["kind"] == "latest_comparative"}
COLS = ["section", "master", "code", "company", "quarter", "items", "dryrun_verdict", "decision", "reason", "dryrun_note"]
out = []


def add(section, master, code, company, quarter, items, verdict, decision, reason, note=""):
    out.append({"section": section, "master": master, "code": code, "company": company, "quarter": quarter, "items": items,
                "dryrun_verdict": verdict, "decision": decision, "reason": reason, "dryrun_note": note})


# ---------------------------------------------------------------- A: adopt verdicts not applied
A = {
    ("CSM_waterfall", "KR1000", "2025.1Q"): (
        "items 3,4", "hold (dropped after cell check)",
        "Independent re-read of the later filing (20260529002207.xml, tables #569/#688/#1467): items 1,2,5,6 print exactly the live values (no change). The two changed cells "
        "(item 3 이자 부리 84.1 -> 79.8, item 4 가정·경험 206.0 -> 210.3) have no printed counterpart (matched 4/6) - the dry-run vector counts the FX (환율변동효과) leg twice, so it is a "
        "4.3억 re-split between items 3 and 4 with an unchanged closing identity, not a verified restatement. Unchanged."),
    ("IFRS17_BS", "KR0075", "2023.4Q"): (
        "items 1,2", "hold",
        "Live 자산총계/부채총계 are a vision-read value cross-confirmed by three independent filings (2024.1Q / 2024.3Q comparatives) and kept on purpose by the "
        "2026-09-11 parser pass (bs_manual_overrides _readme: 'held, 정정공시 가능성'); the DART original and its latest comparative agree with each other and are "
        "2,411.95 백만원 lower, items 3/4 are identical. The latest comparative therefore adds no new information; this is a basis/amended-filing question for the "
        "downloader/owner, not a precedence case. Unchanged."),
    ("IFRS17_BS", "KR0009", "2024.4Q"): (
        "item 21", "hold",
        "The later filing (FY2025 FS-API cache, OFS) carries no value for 재보험계약부채 (ifrs-full_ReinsuranceContractsHeldThatAreLiabilities): the candidate would blank "
        "the live 0.0. A blank is not a latest comparative value. Unchanged."),
    ("IFRS17_BS", "KR0099", "2024.4Q"): (
        "item 20", "hold",
        "The later filing (FY2025 FS-API cache, OFS) carries no value for 보험계약부채 (ifrs-full_InsuranceContractsIssuedThatAreLiabilities): the candidate would "
        "blank the live 27,209,738. A blank is not a latest comparative value. Unchanged."),
    ("ILP", "KR0097", "2024.4Q"): (
        "ILP items (CSM/BEL/RA)", "hold",
        "The restated comparative exists only as integer 억원 in the FY2025_Q4 경영공시 PDF (4-6-2, p23); the precise DART XML comparative is not readable (Hana Life has no "
        "FS-API/BS reader for the later year), and the matching 17BS item 20 cannot be restated, so an ILP-only change would open a new ILP-vs-BS tie (R-LIC1) "
        "difference. Needs the coupled ILP+BS block with a precise source. Unchanged."),
}
for r in census:
    if not r["verdict"].startswith("최신 채택"):
        continue
    master = r["domain"]
    key = (master, r["code"], r["quarter"])
    if key in applied_blocks:
        continue
    items, decision, reason = A.get(key, ("", "hold", "not applied (no recorded reason)"))
    add("A_adopt_not_applied", master, r["code"], r["company"], r["quarter"], items, r["verdict"], decision, reason, r["note"])

# ---------------------------------------------------------------- B: cells removed from applied blocks
B = [
    ("PL_breakdown", "KR0008", "삼성화재해상보험", "2023.1Q", "item 16", "92608.0 -> 92608.042127",
     "Sub-0.05 백만원 precision difference (master carries the FS-API 1-백만원 rounding, the later filing prints 92,608.042127). Writing it would make the existing "
     "owner gold cell for this key redundant (GOLD_OVERLAY_NEWLY_REDUNDANT, a new gate finding) for no information gain. Unchanged."),
    ("PL_breakdown", "KR0011", "DB손해보험", "2023.3Q", "item 18", "968520.161043 -> 968520.1610430001",
     "Floating-point noise (1e-10) of the derived item 18 = 17 - 19 (recomputed by the builder anyway). Not a value change. Unchanged."),
    ("IFRS17_BS", "KR0071", "흥국생명보험", "2024.4Q", "item 4 (AOCI)", "-421112.448184 -> (blank)",
     "The later filing's FS-API cache has no AOCI account for this company/year, so the candidate would blank the live value; items 1,2,3 of the same block (restated "
     "자산/부채/자본) are applied (3 of the 4 stale cells)."),
]
for m, code, co, q, it, chg, why in B:
    add("B_cell_removed_from_applied_block", m, code, co, q, it, "최신 채택", "hold (cell)", f"{chg}: {why}")

# ---------------------------------------------------------------- C: remaining verdicts
WHY = {
    "gold 충돌": ("hold", "An owner gold-overlay cell of this block (data/_gold/user_pl_cells.json / user_csm_cells.json) differs from the latest comparative column. "
                  "The ticket holds all gold conflicts: replacing or releasing an owner gold value is an owner decision."),
    "현행 유지": ("hold", "The dry run kept the current master: the latest comparative column does not close the strict gates better than the live values "
                  "(or would worsen a neighbouring identity/continuity). No write."),
    "둘 다 불가(현행 유지+목록)": ("hold", "Neither the current nor the latest column satisfies the strict gates on its own; the block needs its siblings (Q1/Q2) first. Unchanged."),
    "조건부(동반 블록 필요)": ("hold", "Adoption needs a companion block (ILP latest comparative) that was not read; adopting the 17BS block alone opens a new R-LIC1 difference. Unchanged."),
    "후보 미검증(도구 공백)": ("hold", "A candidate for this block was not verified against the original filing table (reader gap listed in the dry-run blind-spot column). "
                              "The ticket applies only directly verified values. Unchanged."),
    "비교 컬럼 추출 불가": ("hold", "The comparative (prior-period) column could not be extracted from the later filing for this block (no prior block / unsupported layout / no later filing). Nothing to compare. Unchanged."),
    "재판정 안 함(이전 라운드)": ("hold", "Decided in an earlier round (owner override cell / owner sidecar decision); the ticket says not to re-judge. Unchanged."),
}
for r in census:
    v = r["verdict"]
    if v == "변화 없음" or v.startswith("최신 채택"):
        continue
    dec, why = WHY[v]
    extra = ""
    if r["blind_spots"]:
        extra = f" [blind spot: {r['blind_spots']}]"
    if r["gold_conflict"] == "Y" and v != "gold 충돌":
        extra += " [gold conflict flag Y]"
    add("C_dryrun_verdict", r["domain"], r["code"], r["company"], r["quarter"], f"n_diff={r['n_diff']}", v, dec, why + extra, r["note"])

# ---------------------------------------------------------------- D: the 9 new findings
D = [
    ("NEW-01", "PL_breakdown", "KR0005", "흥국화재", "2023.2Q", "1,19,20,21,22,23,24", "APPLIED (7 cells; the dry run listed 5)",
     "Tier-1 HTML fallback loaded the 2Q 3-month column as the cumulative; corrected to the printed cumulative column, verified in the original 반기보고서 XML (see applied_cells.csv kind=3m_as_cumulative)."),
    ("NEW-02", "PL_breakdown", "KR0068", "한화생명", "2023.2Q", "21", "APPLIED (1 cell; the dry run listed 4)",
     "Direct read of the statement table shows items 20/22/23/24 already equal the printed CUMULATIVE column (435,963 / 625,431 / 112,101 / 513,329 are the 반기 누적, the 3-month "
     "values are 60,255 / 159,110 / 2,706 / 156,404 and the prior-year cumulative 987,882 ...). The dry-run claim for those four cells is wrong; only item 21 (영업외손익) carries the 3-month "
     "figure (98,854) instead of the cumulative 189,467. Fixed item 21 only."),
    ("NEW-03", "PL_breakdown", "KR0008", "삼성화재", "2023.2Q (prior-column read)", "item 14", "HOLD (no data error)",
     "Latent reader issue (companies._old_lobcum irregular 8-cell reinsurance total row) that only bites when a prior-period column is read; the production path (current column) is unaffected "
     "and the plan blocks for KR0008 were verified item by item against the statement and notes. No data cell is wrong; a code change is not part of this ticket."),
    ("NEW-04", "PL_breakdown", "KR0001", "메리츠화재해상보험", "2023.1Q", "item 16", "HOLD (owner gold)",
     "assemble() normalises item 16 with abs(); the owner gold cell keeps the sign (-12,370.22, original filing) deliberately. The block is a gold conflict; no change."),
    ("NEW-05", "gate", "", "(validate_master_tables)", "2023~", "tax22_src", "NO ACTION (gate artifact)",
     "27 spurious tax22_src FAILs appeared only in the dry-run's full Tier-1 latest-comparative candidate. The applied set (7 PL blocks) produced 0 new FAIL in the candidate gate run "
     "(pl_bridge 3660P/29F -> 3676P/23F, 0 new). Changing the gate's source comparison would be a new mechanism, not allowed here."),
    ("NEW-06", "gate", "", "(BS_KICS_BASELINE_BREAK, PL_OCI_VS_BS_AOCI, R-LIC1)", "2023.4Q etc.", "-", "CONSEQUENCE (documented, YELLOW only)",
     "Restating year-end BS blocks moves YELLOW findings by design (BS_KICS_BASELINE_BREAK +11/-3, PL_OCI_VS_BS_AOCI 14 -> 22). No RED. R-LIC1 risk was avoided by holding the 롯데손해보험/교보생명 2023.4Q BS blocks."),
    ("NEW-07", "ILP", "KR0074", "라이나생명보험", "2023.2Q-2023.4Q", "items 14,15", "HOLD (owner basis decision, filing-faithful)",
     "ILP 2023.3Q items 14/15 (2,297.78 / 2,843.84) are the FY2024_Q3 filing's restated 전분기 comparative (4-column layout), flagged restated_comparative_not_closable_with_bs20 in the ILP sidecar; "
     "the own 2023.3Q filing prints 440,519 백만원 (4,405.19억). 2023.4Q was unified on the restated column by ticket 20261011T0100Z. The jump is the restatement, not a parse error; "
     "a jump rule would be a new mechanism. Lina 17BS 2023.4Q stays 'not re-judged' (owner 2026-10-10)."),
    ("NEW-08", "IFRS17_BS", "(10 non-FS-API companies)", "AXA, Hana Non-life, Shinhan EZ, Lina, iM Life, AIA, MetLife, Chubb, Kyobo Planet, IBK Pension", "2022.4Q", "30 cells", "HOLD (outside the ticket range)",
     "The masters carry the FY2022 IFRS4 originals while the FY2023 audit report comparatives are IFRS17 restated (e.g. AIA assets 17.51 -> 16.54조). The ticket range is 2023.1Q-2026.1Q; a basis change for 2022.4Q is an owner decision."),
    ("NEW-09", "CSM_waterfall", "KR0069 / KR0082", "삼성생명 2024.2Q / DB생명 2024.1Q", "yoy warnings", "2 warnings", "RESOLVED AS CONSEQUENCE (1 gone, 1 reduced)",
     "The 삼성생명 2024.2Q 이자부리 yoy warning (900 -> 2,276, +152.9%) disappears because 삼성생명 2023.2Q is applied (1,916 -> 2,276); the DB생명 2024.1Q one drops from +87.9% to +24.8% (82 -> 154 becomes "
     "124 -> 154, still above the 20% threshold, so it stays flagged). qoq_scan on live vs candidate: 267 -> 266 flagged, no new row; 삼성화재 2024.1Q-3Q 이자부리 move by <1 pt."),
]
for fid, m, code, co, q, it, dec, why in D:
    add("D_new_findings", m, code, co, q, it, fid, dec, why)

# ---------------------------------------------------------------- E: 3-month scan, not directly verifiable
E = [
    ("KR0010", "KB손해보험", "2023.2Q", "no statement table recognised in the 반기보고서 XML (scan class NO_STATEMENT_TABLE)",
     "Not scanned at statement level. Independent cross-check: the dry-run census compares items 20/22/23/24 with the FY2024_Q2 comparative cumulative column -> CUM_OK (<= 1.4 % apart); item 1 CUM_RESTATED. No sign of a 3-month load. Unchanged, listed."),
    ("KR0087", "동양생명", "2023.2Q", "no statement table recognised (NO_STATEMENT_TABLE)",
     "Cross-check against the FY2024_Q2 comparative: items 1,20,22,23,24 CUM_OK (exact). Unchanged, listed."),
    ("KR0094", "신한라이프생명보험", "2023.2Q", "no statement table recognised (NO_STATEMENT_TABLE)",
     "Cross-check against the FY2024_Q2 comparative: items 1,20,22,23,24 CUM_OK (exact). Unchanged, listed."),
    ("KR0099", "KB라이프생명", "2023.2Q", "no statement table recognised (NO_STATEMENT_TABLE)",
     "Cross-check against the FY2024_Q2 comparative: items 22,23,24 CUM_OK (<= 0.1 %). Unchanged, listed."),
]
for code, co, q, what, why in E:
    add("E_3m_scan_not_verifiable", "PL_breakdown", code, co, q, "Tier-1 items 1,16,17,19-24", "scan", "hold (listed)", f"{what}. {why}")
add("E_3m_scan_not_verifiable", "PL_breakdown", "(PDF-lineage, 41 companies)", "all companies whose Tier-1 comes from the 경영공시 요약 포괄손익계산서 PDF", "2023.1Q-2026.2Q", "1,426 cells in 317 buckets", "scan",
    "checked: 1,310 decisive, 116 undecided (listed, unchanged)",
    "Independent PyMuPDF re-read of the source PDF of every disclosure_summary_pl cell (pdf_scan_final.csv): 1,310 cells equal a printed column of their own source PDF - 1,246 own-filing PDFs = current-period column, "
    "45 later-filing PDFs = prior-year comparative column (the latest-comparative path, correct), 2 cells = the later filing's CURRENT column (KR0002 item 16 2023.1Q/2Q: wrong year, fixed, kind=wrong_year_column), "
    "the rest 4-column audited-statement layouts (3M, cumulative, prior 3M, prior cumulative) where the master equals the cumulative column. 116 cells (label not found / odd layout, mostly 법인세비용 and 세전이익 rows) "
    "could not be decided automatically and are NOT verified: they are listed in pdf_scan_final.csv (final_class NOLABEL/NONE). A whole-master cross-check against the OWN-filing PDF (4,678 cells, pdf_vs_master.csv / "
    "pdf_classified.csv) found no further cell whose master value equals the PDF's prior-year column or the PDF's own Q-vs-Q-1 3-month difference except those already fixed; the remaining gaps are 감독회계-vs-재무제표 basis, "
    "restated vintage (롯데손보 2023, DB손보 2023) or PDF layout artefacts and are not column confusions. The AXA 2025.3Q shrink is real (PDF p4 26억).")
add("E_3m_scan_not_verifiable", "PL_breakdown", "KR0003/KR0070/KR0002/KR0001/KR0079/KR0082/KR0083 etc.", "(scan NO_MATCH rows)", "2023.2Q-2026.2Q", "67 rows",
    "scan", "no action (not a 3-month pattern)",
    "In 67 statement-line rows the master matches none of the four printed columns. Only two of them lie within 1 % of the 3-month column (KR0005 and KR0083 item 19, both fixed). "
    "The rest are other bases (restated vintage, note-derived, sign or consolidation conventions) or item 15 (see F); scan_nomatch_classified.csv lists each with its distance to the 3M and cumulative columns.")

# ---------------------------------------------------------------- F: other observations
add("E_3m_scan_not_verifiable", "PL_breakdown", "KR0099", "KB라이프생명", "2025.1Q", "items 1,16,17,20,21,22,23,24,25,31", "scan", "no action (scan false positive)",
    "The scan class 3M_AS_CUM fired on 10 cells because the 2025.1Q statement prints only TWO numbers per row [current period, prior-year period] (no 3-month/cumulative pair); the master equals the first "
    "(current) number in all 10 rows (e.g. item 24: 90,315 vs prior 96,237). Not a 3-month load. Unchanged.")
add("F_other_observation", "PL_breakdown", "KR0008/KR0009/KR0069/KR0070/KR0072/KR0073/KR1000", "삼성화재, 현대해상, 삼성생명, 에이비엘생명, 케이디비생명, 교보생명, 코리안리", "2023.3Q-2026.2Q", "item 15 기타영업수익 (23 cells)", "observation", "no action (outside ticket)",
    "Item 15 is 0.0 in the master although the statement prints a non-zero 기타영업수익 line (22 NO_MATCH rows in scan_nomatch_classified.csv + the KR0069 2026.2Q row, which the scan labelled 3M_AS_CUM only because 0.0 sits inside its matching tolerance). The cause was not investigated "
    "(the 보험손익 bridge adds item 15 only when present, so the gates stay closed); a builder convention/coverage question for a separate ticket, not a column confusion.")
add("F_other_observation", "PL_breakdown", "KR0003/KR0070/KR0002/KR0068", "롯데손해보험, 에이비엘생명, 한화손해보험, 한화생명", "2023.2Q", "items 1,20,22,23,24 / 1 / 23 / 20", "observation",
    "no action",
    "The dry-run Q2 census marks these 'OTHER' (master differs from the FY2024_Q2 comparative 6-month column by 38-52 %, KR0002 item 23 by sign only). The statement-level scan of the original 반기보고서 shows the master "
    "equals the printed CUMULATIVE column for KR0003 (items 1,20,22,23,24), KR0002 item 23 and KR0068 item 20 (e.g. 롯데 item 1 102,897.6 = col 2); the difference is the later restatement (vintage), i.e. a "
    "latest-comparative question handled by the PL gold/candidate blocks, not a 3-month load. KR0070 item 1 (ABL): the 2023 filing is not in the XML scan (lineage DART builder rule); not verified at statement level, unchanged.")
add("F_other_observation", "PL_breakdown", "Tier-2 items 2-14", "(all)", "2023.2Q-2023.3Q", "Tier-2 note items", "observation", "not scanned at table level",
    "The systematic statement-level scan covers Tier-1. For Tier-2 note items only the YTD monotonicity indicator was run (989 flags, almost all sign-mixed net items such as 9/10/12/21); "
    "no flagged Tier-2 cell showed the 3-month pattern against a printed table, so none was changed. A table-level Tier-2 scan would need the per-company note handlers and is left open.")

# ---------------------------------------------------------------- write
path = HERE / "held_blocks.csv"
with open(path, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    w.writerows(out)
print("held_blocks.csv rows:", len(out))
print(Counter(r["section"] for r in out))
print(Counter(r["dryrun_verdict"] for r in out if r["section"] == "C_dryrun_verdict"))
