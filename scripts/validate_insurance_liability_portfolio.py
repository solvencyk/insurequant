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
                      A RED here can be released ONLY through R3_PINNED_EXEMPTIONS (below):
                      the pin holds the exact item8 / item20 values the owner-approved
                      reconnaissance saw, so any data move re-raises RED, and a pin that is
                      no longer needed is itself RED (R3_EXEMPTION_INERT).
  R4_NA_VS_MISSING   item9 (해지율_예외모형_사용여부) must be 0 or 1 whenever items 1-8 exist
                      for that (company,quarter) -- a silent absence of item9 alongside a
                      present item1-8 is flagged (2-5 section located but N/A-vs-used could
                      not be determined; distinct from "company genuinely not censused").
  R5_COPY            items 1-7 identical to the company's previous loaded quarter -> RED
                      (a filer copy / mis-picked table; R1 cannot see it: it is a tautology).
  R6_JUMP            |item 8| moves > 50 % against the previous loaded quarter -> YELLOW.

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
    # 2026-10-10 (validation 단계 8): 스캔 3사 KR0010 KB손해 · KR0079 미래에셋 · KR0087 동양생명
    # 의 R2_CENSUS "*" 예외 3건을 지웠다 — 세 회사 모두 2025.1Q~2026.2Q 6분기에 행이 적재돼
    # (분기당 8~9행) 예외가 한 번도 발동하지 않는 죽은 면제였다(실행 결과 exceptions applied 0).
    # 죽은 면제를 남기면 나중에 그 회사 행이 빠져도 RED 대신 SKIP 으로 조용히 넘어간다.
]

# R3_CROSS_CHECK 박제 등재부 (2026-10-12, owner 「확인된 것만 등재」 승인, 티켓 20261012T1400Z).
# 키 (원보험사코드, 공시분기) -> 원문 재확인으로 본 값 + 사유. **값을 박제한다**: 등재는 "이 칸이 이 값일 때만"
# 면제이고, item8 이나 item20 이 움직이면 RED 로 되돌아온다(근거 재확인 없이 영원히 빠지는 키 집합 방식 금지).
# 면제가 더는 필요 없어지면(10배 규칙에 안 걸림) R3_EXEMPTION_INERT RED 로 알려 죽은 면제를 남기지 않는다.
# item20_mm 은 IFRS17_BS.json 항목 20 (백만원), item8_eok 은 이 마스터 항목 8 (억원).
R3_PINNED_EXEMPTIONS = {
    ("KR0029", "2024.4Q"): {
        "item8_eok": 31.0,
        "item20_mm": 291767.640554,
        "reason": (
            "AIG손해보험 2024.4Q: 2-4 표의 순 LRC 가 잔여보장자산 상계로 0 근처(+31.0억, DART 순 LRC 30.23)이고 "
            "BS 항목 20 은 부채 기준 LRC 884.60 + LIC 2,033.08 = 2,917.7억이라 10배 규칙에 걸린다. 값은 맞고 "
            "구조적이다(원문 재확인 parser-ifrs17, data/disclosure/_meta/ifrs17_owner_followups_runlog_20261012.md "
            "§4 ⑧; 단위 오류 아님)."),
    },
}
R3_PIN_TOL_EOK = 1e-6
R3_PIN_TOL_MM = 1e-3

# R2 census 범위 밖 코드 — **다음 round 에서 재보사 IFRS17(2-4/2-5) 을 적재하기 전까지만.**
# 2026-10-10 재보사·마이브라운(KR1101~KR1108) K-ICS 적재로 md_inbox 2025.1Q~2026.2Q 에 이 8사 MD 가
# 생겼지만 이 마스터의 2-4/2-5 추출은 아직 그 회사들을 대상으로 돌지 않았다(재보사 스윕 1~8단계는
# K-ICS 만). 그대로 두면 46칸이 "추출 누락" RED 로 뜨는데 그건 결함이 아니라 아직 범위에 넣지 않은
# 것이다. 조용히 빼지 않는다 — 제외한 칸 수를 매 실행 인쇄한다. 재보사 IFRS17 적재 때 이 집합을 비운다.
# 2026-10-11 (parser-ifrs17, ticket 20261011T0320Z stage 4): 재보사 8곳의 2-4/4-6-2 가 적재됐다(scripts/load_ilp_reinsurers.py, 63칸) -> 집합을 비웠다.
# 적재하지 않은 칸(예: KR1102 2026.1Q, 총괄표가 Indirect 행을 빠뜨린 발행사 오류 -- provenance lrc_model_not_loaded 에 사유)은 이제 R2_CENSUS RED 로 뜬다.
R2_CENSUS_NOT_YET_IN_SCOPE = frozenset()


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


def check_r3(by_cq: dict, item20_reg: dict, findings: dict, pins: dict | None = None) -> None:
    """R3_CROSS_CHECK vs IFRS17_BS item20. `pins` defaults to R3_PINNED_EXEMPTIONS (the reader of the registry)."""
    pins = R3_PINNED_EXEMPTIONS if pins is None else pins
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
        red_msg = None
        if gap < -neg_slack:
            red_msg = (line + f" -- item20 < item8 by more than rounding slack "
                       f"(-{neg_slack:.1f}억); expected item20 >= item8 since item20 = LRC+LIC")
        elif my_total_eok > 0 and gap > 10 * my_total_eok:
            red_msg = (line + " -- gap > 10x item8, implausible even for an LIC-heavy "
                       "reinsurer/claims book -- check for a unit-scale bug")

        pin = pins.get((code, q))
        if pin is not None:
            if red_msg is None:
                findings["RED"].append(
                    f"R3_EXEMPTION_INERT {code} {q}: pinned exemption but the cross-check no longer fails "
                    f"({line}) -- remove the dead exemption from R3_PINNED_EXEMPTIONS")
                continue
            if (abs(my_total_eok - pin["item8_eok"]) > R3_PIN_TOL_EOK
                    or abs(item20_mm - pin["item20_mm"]) > R3_PIN_TOL_MM):
                findings["RED"].append(
                    f"R3_PIN_DRIFT {code} {q}: values moved since the pinned reconnaissance "
                    f"(pinned item8={pin['item8_eok']} 억 item20={pin['item20_mm']} 백만원; "
                    f"now item8={my_total_eok} 억 item20={item20_mm} 백만원) -- re-confirm against the source; {red_msg}")
                continue
            findings["exceptions"].append(f"R3_CROSS_CHECK {code} {q}: SKIP (pinned) -- {pin['reason']}")
            continue
        if red_msg is not None:
            findings["RED"].append(red_msg)
        else:
            findings["YELLOW"].append(line)


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
    not_in_scope = []
    for q in periods_to_check:
        expected_codes = grid.get(q, set())
        for code in sorted(expected_codes):
            has_any = (code, q) in by_cq
            if has_any:
                continue
            if code in R2_CENSUS_NOT_YET_IN_SCOPE:
                not_in_scope.append((code, q))
                continue
            reason = is_documented(code, q, "R2_CENSUS")
            if reason:
                findings["exceptions"].append(f"R2_CENSUS {code} {q}: SKIP (documented) -- {reason}")
            else:
                findings["RED"].append(f"R2_CENSUS {code} {q}: no row in master, not documented")

    # --- R3 CROSS_CHECK vs IFRS17_BS item20 ---
    check_r3(by_cq, load_item20_registry(), findings)

    # --- R4 NA_VS_MISSING ---
    for (code, q), items in by_cq.items():
        if 8 in items and 9 not in items:
            findings["YELLOW"].append(
                f"R4_NA_VS_MISSING {code} {q}: item1-8 present but item9 (해지율 예외모형 "
                f"사용여부) not resolved -- 2-5 section located but N/A-vs-used undetermined, "
                f"or 2-5 header not found within lookahead window"
            )

    # --- R5 COPY / R6 JUMP ---
    # (ticket 20261011T0320Z stage 5; ilp_gap_runlog_textlayer_20261010.md defect 6.)  R1 is a tautology (the extractor computes item 8 as the sum of items 1-7), so a copied or
    # mis-picked table passes it.  R5: items 1-7 identical to the company's previous loaded quarter (a filer copy, 3 found in the 2026-10-10 audit, all patched) -> RED.
    # R6: |item 8| moves by more than 50 % against the previous loaded quarter (previous |item 8| >= 10억; KR0097 44,246 -> -53 was a mis-picked row) -> YELLOW, because net
    # remaining-coverage balances around zero (AIG, reinsurers) and growing start-ups jump legitimately.  'previous' = the nearest earlier quarter with items 1-8, at most
    # two quarters back; quarter labels sort chronologically.
    qorder = sorted({q for (_c, q) in by_cq})
    for code in sorted({c for (c, _q) in by_cq}):
        have = [q for q in qorder if (code, q) in by_cq and all(i in by_cq[(code, q)] for i in range(1, 9))]
        for prev, q in zip(have, have[1:]):
            if qorder.index(q) - qorder.index(prev) > 2:
                continue
            a, b = by_cq[(code, prev)], by_cq[(code, q)]
            va, vb = [a[i]["값"] for i in range(1, 8)], [b[i]["값"] for i in range(1, 8)]
            if va == vb and any(va):
                reason = is_documented(code, q, "R5_COPY")
                if reason:
                    findings["exceptions"].append(f"R5_COPY {code} {q}: SKIP (documented) -- {reason}")
                else:
                    findings["RED"].append(f"R5_COPY {code} {q}: items 1-7 identical to {prev} ({va}) -- a copied or mis-picked table")
            elif abs(a[8]["값"]) >= 10 and abs(b[8]["값"] - a[8]["값"]) > 0.5 * abs(a[8]["값"]):
                findings["YELLOW"].append(f"R6_JUMP {code} {q}: item 8 {a[8]['값']:,.1f} ({prev}) -> {b[8]['값']:,.1f} (> 50 %): confirm against the PDF / BS")

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
    print(f"\n--- R2_CENSUS not yet in scope (재보사 IFRS17 미적재, {len(not_in_scope)}칸) ---")
    for code in sorted({c for c, _q in not_in_scope}):
        qs = sorted(q for c, q in not_in_scope if c == code)
        print(f"  {code}: {len(qs)}칸 {qs[0]}~{qs[-1]}")

    print(f"\nSUMMARY RED={len(findings['RED'])} YELLOW={len(findings['YELLOW'])} "
          f"exceptions={len(findings['exceptions'])} not_in_scope={len(not_in_scope)}")
    raise SystemExit(1 if findings["RED"] else 0)


if __name__ == "__main__":
    main()
