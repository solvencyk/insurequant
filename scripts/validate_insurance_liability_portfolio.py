# -*- coding: utf-8 -*-
"""
Gate for insurance_liability_portfolio.json (2-4 회계모형별·포트폴리오별 보험부채 현황 +
2-5 무·저해지상품 해지율 예외모형 마스터). Mirrors the kics_disclosure.json gate contract:
RED must be 0, or every RED is a documented exception below (company, quarter, rule, reason).

Rules:
  R1_IDENTITY        item8(보험부채_합계) == round(sum(item1..item7), tol) per (company,quarter)
  R2_CENSUS          every company in the expected grid (md_inbox/<period>/*.md filenames,
                      restricted to 공시분기 >= FIRST_PERIOD_WITH_SECTION="2025.1Q" -- section
                      2-4/2-5 is confirmed absent from the 정기경영공시 template before that,
                      not a parsing gap; see the constant's docstring) has SOME row for that
                      (company,quarter) in the master, unless listed in DOCUMENTED_EXCEPTIONS
  R3_CROSS_CHECK      item8 vs IFRS17_BS.json item20 (보험계약부채) for overlapping
                      (company,quarter). item8 covers 잔여보장요소 (LRC) ONLY -- every 2-4
                      table sampled during reconnaissance carries the explicit footnote
                      "원수보험 및 수재보험계약의 잔여보장요소에 대하여 작성되었습니다" --
                      while IFRS17_BS item20 is the full BS 보험계약부채 = LRC + LIC
                      (지급준비금/발생사고요소, liability for incurred claims). So item20 is
                      expected to be >= item8, not equal to it; the gap is reported and only
                      flagged RED if item20 < item8 by more than a small rounding-noise slack
                      (independent pipelines, each already rounded to whole 억원 before
                      summing) or the gap is implausibly large (> 10x item8 -- a reinsurer's
                      LIC-heavy book can legitimately run several multiples, confirmed on
                      KR1000/코리안리재보험 at 4.64x by hand-checking the raw PDF table, so
                      the cutoff is set well above that, wide enough to still catch an actual
                      unit-scale bug like a 억원/백만원 mixup).
  R4_NA_VS_MISSING   item9 (해지율_예외모형_사용여부) must be 0 or 1 whenever items 1-8 exist
                      for that (company,quarter) -- a silent absence of item9 alongside a
                      present item1-8 is flagged (2-5 section located but N/A-vs-used could
                      not be determined; distinct from "company genuinely not censused").

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/validate_insurance_liability_portfolio.py [--period FY2026_Q2]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER = REPO_ROOT / "insurance_liability_portfolio.json"
MD_INBOX = REPO_ROOT / "md_inbox"
IFRS17_BS = REPO_ROOT / "IFRS17_BS.json"

TOL = 0.05  # 억원, rounding tolerance for the item1..7 -> item8 identity

# ---------------------------------------------------------------------------
# Documented exceptions (company, quarter, rule) -- "*" quarter = every quarter.
# Populate only with reconnaissance-confirmed root causes; never blanket-suppress.
# ---------------------------------------------------------------------------
DOCUMENTED_EXCEPTIONS = [
    # (원보험사코드, 공시분기 or "*", rule, reason)
    ("KR0010", "*", "R2_CENSUS",
     "KB손해보험: PDF has 0 extractable chars across every page in every period sampled "
     "(scan-only image PDF). No native text layer to parse; OCR out of scope for this "
     "master's V1 (see extractor module docstring)."),
    ("KR0087", "*", "R2_CENSUS",
     "동양생명: PDF has near-zero extractable text (258 chars / 59 pages at 2026.2Q; "
     "matches the pre-existing project finding in reference_pdf_wrong_document_false_alarm "
     "-- this is a known scan-only filer, not a wrong-document false alarm)."),
    ("KR0079", "*", "R2_CENSUS",
     "미래에셋생명: PDF has near-zero extractable native text (246 chars / 25 prefix pages "
     "at 2026.2Q, 65 pages total). Same failure class already logged against this company's "
     "item47-54 TFI table in inbox/parser/20260831T0800Z (docling OCR-scale finding) -- the "
     "filing is scan-adjacent and needs OCR, out of scope for this master's V1 text-extraction "
     "path (see extract_insurance_liability_portfolio.py module docstring)."),
]


def is_documented(code: str, period_label: str, rule: str) -> str | None:
    for exc_code, exc_q, exc_rule, reason in DOCUMENTED_EXCEPTIONS:
        if exc_code == code and exc_rule == rule and (exc_q == "*" or exc_q == period_label):
            return reason
    return None


def period_dir_to_label(period_dir_name: str) -> str:
    m = re.match(r"FY(\d{4})_Q(\d)", period_dir_name)
    if not m:
        return period_dir_name
    return f"{m.group(1)}.{m.group(2)}Q"


FILENAME_RE = re.compile(r"^(KR\d+)_")

# Section 2-4/2-5 do not exist in the 정기경영공시 template before 2025.1Q -- confirmed
# by hand-checking raw PDFs for 3 companies spanning life/non-life/surety (KR0068/한화
# 생명, KR0009/현대해상, KR0150/서울보증보험): all three jump straight from "2-2. 요약
# 재무상태표" to "3-1. 자산건전성" through FY2024_Q4 (no 2-3/2-4/2-5 at all -- not a
# parsing gap, the section is genuinely absent from the disclosure requirement), then
# all three carry a clean "2-4. 회계모형별..." header starting FY2025_Q1. This is a
# report-wide regulatory template change, not a per-company quirk, so the census here
# only expects coverage from 2025.1Q onward -- treating 2023.1Q-2024.4Q as "missing" would
# manufacture ~300 false RED census gaps for a section that could not have existed yet.
FIRST_PERIOD_WITH_SECTION = "2025.1Q"


def expected_grid() -> dict:
    """{period_label: set(원보험사코드)} from md_inbox filenames, restricted to periods
    from FIRST_PERIOD_WITH_SECTION onward (see note above)."""
    grid = {}
    if not MD_INBOX.exists():
        return grid
    for period_dir in sorted(MD_INBOX.iterdir()):
        if not period_dir.is_dir() or not period_dir.name.startswith("FY"):
            continue
        label = period_dir_to_label(period_dir.name)
        if label < FIRST_PERIOD_WITH_SECTION:
            continue
        codes = set()
        for f in period_dir.glob("*.md"):
            m = FILENAME_RE.match(f.name)
            if m:
                codes.add(m.group(1))
        grid[label] = codes
    return grid


def load_master() -> list:
    if not MASTER.exists():
        return []
    with open(MASTER, encoding="utf-8") as f:
        return json.load(f)


def load_item20_registry() -> dict:
    """{(원보험사코드, 공시분기): 값} from IFRS17_BS.json item20 (보험계약부채, 백만원)."""
    reg = {}
    if not IFRS17_BS.exists():
        return reg
    with open(IFRS17_BS, encoding="utf-8") as f:
        data = json.load(f)
    for r in data:
        if r.get("항목번호") == 20:
            reg[(r["원보험사코드"], r["공시분기"])] = r["값"]
    return reg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", help="restrict to one 공시분기 label, e.g. 2026.2Q")
    args = ap.parse_args()

    rows = load_master()
    if args.period:
        rows = [r for r in rows if r["공시분기"] == args.period]

    by_cq = {}
    for r in rows:
        key = (r["원보험사코드"], r["공시분기"])
        by_cq.setdefault(key, {})[r["항목번호"]] = r

    findings = {"RED": [], "YELLOW": [], "exceptions": []}

    # --- R1 IDENTITY ---
    for (code, q), items in by_cq.items():
        if 8 not in items:
            continue
        have_1_7 = all(i in items for i in range(1, 8))
        if not have_1_7:
            findings["RED"].append(
                f"R1_IDENTITY {code} {q}: item8 present but item1..7 incomplete "
                f"({sorted(k for k in items if 1 <= k <= 7)})"
            )
            continue
        s = sum(items[i]["값"] for i in range(1, 8))
        disclosed = items[8]["값"]
        if abs(s - disclosed) > TOL:
            findings["RED"].append(
                f"R1_IDENTITY {code} {q}: sum(item1..7)={s:.4f} != item8={disclosed:.4f} "
                f"(diff={s - disclosed:.4f})"
            )

    # --- R2 CENSUS ---
    grid = expected_grid()
    periods_to_check = [args.period] if args.period else sorted(grid.keys())
    for q in periods_to_check:
        expected_codes = grid.get(q, set())
        for code in sorted(expected_codes):
            has_any = (code, q) in by_cq
            if has_any:
                continue
            reason = is_documented(code, q, "R2_CENSUS")
            if reason:
                findings["exceptions"].append(f"R2_CENSUS {code} {q}: SKIP (documented) -- {reason}")
            else:
                findings["RED"].append(f"R2_CENSUS {code} {q}: no row in master, not documented")

    # --- R3 CROSS_CHECK vs IFRS17_BS item20 ---
    item20_reg = load_item20_registry()
    for (code, q), items in by_cq.items():
        if 8 not in items:
            continue
        my_total_eok = items[8]["값"]  # 억원
        item20_mm = item20_reg.get((code, q))  # 백만원
        if item20_mm is None:
            continue  # no overlapping IFRS17_BS row for this (company,quarter); not an error
        item20_eok = item20_mm / 100.0  # 백만원 -> 억원
        gap = item20_eok - my_total_eok
        gap_pct = (gap / my_total_eok * 100.0) if my_total_eok else float("inf")
        line = (
            f"R3_CROSS_CHECK {code} {q}: item8(LRC-only)={my_total_eok:,.1f}억 "
            f"item20(BS full)={item20_eok:,.1f}억 gap={gap:,.1f}억 ({gap_pct:+.1f}%)"
        )
        # Negative-gap slack: this compares two INDEPENDENT extraction pipelines (this
        # master's own PDF table parse vs IFRS17_BS's DART XML parse) built from
        # different source documents, each already rounded to whole 억원 per line
        # before summing -- a few 억원 of rounding noise is expected even when both
        # sides are correct. Confirmed on KR0070 (-0.6억, -0.0003%) and KR0072 (-1.5억,
        # -0.001%) at 2026.2Q: both negligible, not real violations. TOL (0.05억) stays
        # for R1 (single-pipeline arithmetic identity, which should be exact).
        neg_slack = max(5.0, 0.005 * my_total_eok)  # 억원, or 0.5% of item8
        # Upper bound: item20=LRC+LIC can legitimately run several multiples of item8
        # (LRC-only) for LIC-heavy books -- confirmed on KR1000/코리안리재보험 (a
        # reinsurer: item8=20,327억 vs item20=94,297억, 4.64x) by hand-checking the raw
        # PDF table (합계 5,457 2,507 9,470 2,893 -- matches exactly, not a parse error).
        # Reinsurance and claims-heavy non-life books can carry LIC far larger than
        # LRC. Only flag RED past a wide safety margin that would instead suggest a
        # unit-scale bug (e.g. 억원/백만원 confusion, ~100x).
        if gap < -neg_slack:
            findings["RED"].append(
                line + f" -- item20 < item8 by more than rounding slack "
                f"(-{neg_slack:.1f}억); expected item20 >= item8 since item20 = LRC+LIC"
            )
        elif my_total_eok > 0 and gap > 10 * my_total_eok:
            findings["RED"].append(
                line + " -- gap > 10x item8, implausible even for an LIC-heavy "
                "reinsurer/claims book -- check for a unit-scale bug"
            )
        else:
            findings["YELLOW"].append(line)

    # --- R4 NA_VS_MISSING ---
    for (code, q), items in by_cq.items():
        if 8 in items and 9 not in items:
            findings["YELLOW"].append(
                f"R4_NA_VS_MISSING {code} {q}: item1-8 present but item9 (해지율 예외모형 "
                f"사용여부) not resolved -- 2-5 section located but N/A-vs-used undetermined, "
                f"or 2-5 header not found within lookahead window"
            )

    print(f"=== insurance_liability_portfolio.json gate ===")
    print(f"rows={len(rows)}  (company,quarter) pairs={len(by_cq)}")
    print(f"\n--- RED ({len(findings['RED'])}) ---")
    for l in findings["RED"]:
        print(" ", l)
    print(f"\n--- YELLOW ({len(findings['YELLOW'])}) ---")
    for l in findings["YELLOW"][:50]:
        print(" ", l)
    if len(findings["YELLOW"]) > 50:
        print(f"  ... and {len(findings['YELLOW']) - 50} more")
    print(f"\n--- documented exceptions applied ({len(findings['exceptions'])}) ---")
    for l in findings["exceptions"]:
        print(" ", l)

    print(f"\nSUMMARY RED={len(findings['RED'])} YELLOW={len(findings['YELLOW'])} "
          f"exceptions={len(findings['exceptions'])}")
    raise SystemExit(1 if findings["RED"] else 0)


if __name__ == "__main__":
    main()
