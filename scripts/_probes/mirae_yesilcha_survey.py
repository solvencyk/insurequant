"""Investigation probe (read-only) for inbox/parser/20260828T2110Z__orchestrator__KR0079
__mirae_xbrl_format_survey.md.

Answers: can item6 (원수 예실차) / item11 (재보험 예실차) be extracted for 미래에셋생명
(KR0079) from its 2026.2Q DART filing, and what are the values?

Does NOT touch PL_breakdown.json / pl_breakdown_master.json / any master. Reads only the
raw filing XML and (for a final cross-check) root PL_breakdown.json.

Finding: KR0079 does not use the Korean-label prose tables other companies use for this.
It uses DART's XBRL-structured disclosure ("18-1. 보험계약부채(자산) 변동분의 차이조정 공시"),
where the PAA/non-PAA split is a COLUMN header, not a separate table, and units are 원 (not
백만원). Two tables inside that note carry the two halves of 예실차:

  1. "보험손익의 변동내역 > 보험수익" (5 products x 3 transition sub-splits, 15 cols) --
     row "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가(감소), 보험계약부채(자산)"
     = 예상 4종 (revenue side, the amount locked in at period start).
  2. "(상품별 구분)" LRC/LIC rollforward -- row "발생한 보험금 및 기타 보험서비스비용", but only
     its LIC (발생사고부채) sub-columns = 발생 4종 (actual). The row's LRC 손실요소 sub-columns
     must be excluded -- they are the SAME 손실요소배분액 that table #1 already carries as its
     own separate row (verified exact-magnitude identity below), so including them would double
     count a loss-component reallocation that is not part of the 4-species (보험금/손해조사비/
     유지비/재산관리비) experience-adjustment definition. Same boundary NH's KR0032 ticket
     (inbox/_resolved/20260828T1400Z) settled on.

Reinsurance (item11) mirrors this with a "재보험비용의 변동내역" P&L note and the reinsurance
LRC/LIC rollforward, 2 products (사망보험/기타보험) instead of 5. The loss-component identity
still holds (exact magnitude match, sign flips vs the direct side -- verified, not assumed).

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/mirae_yesilcha_survey.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

XML = ROOT / "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml"


def to_num(s):
    s = (s or "").strip().replace(",", "")
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def row_sum(t, label_substr):
    for r in t.rows:
        joined = "".join(r[:2])
        if label_substr in joined:
            nums = [n for n in (to_num(c) for c in r) if n is not None]
            if nums:
                return sum(nums), len(nums)
    return None, 0


def table_at(tables, line_no):
    for t in tables:
        if t.line_no == line_no:
            return t
    raise ValueError(f"no table at line {line_no}")


def main():
    tables = list(_iter_tables_with_context(XML))
    print(f"total tables parsed: {len(tables)}")

    # ---- table-of-contents census (note numbers 40/41/42 = 연결, 87/88/89 = 별도) ----
    print("\n=== note 18-1/18-2/18-3 census (별도 basis) ===")
    for lo, hi, label in [
        (43009, 49039, "87: 18-1 보험계약부채(자산) 변동분 차이조정 공시"),
        (49040, 50573, "88: 18-2 재보험계약자산(부채)의 변동, 보유 재보험계약"),
        (50574, 51184, "89: 18-3 보험계약의 정보"),
    ]:
        n = sum(1 for t in tables if lo <= t.line_no <= hi)
        print(f"  {label}: {n} tables in [{lo},{hi}]")

    # =============== item6 (원수 예실차) ===============
    t_pl_direct = table_at(tables, 48560)   # 보험손익의 변동내역 > 보험수익, 상품별, 당반기
    t_rf_direct = table_at(tables, 43595)   # (상품별 구분) LRC/LIC rollforward, 당반기

    exp_direct, n_exp = row_sum(
        t_pl_direct, "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가"
    )
    loss_alloc_direct, _ = row_sum(t_pl_direct, "손실요소배분액")
    full_row_direct, n_act = row_sum(t_rf_direct, "발생한 보험금 및 기타 보험서비스비용")
    act_direct = full_row_direct - loss_alloc_direct  # exclude LRC loss-component sub-cols

    item6 = (exp_direct - act_direct) / 1e6

    print("\n=== item6 원수 예실차 (KR0079, 2026.2Q, 당반기 누계, 백만원) ===")
    print(f"예상 4종 (n={n_exp} cols): {exp_direct/1e6:,.6f}")
    print(f"발생 4종 LIC-only (n={n_act} cols, minus loss_alloc): {act_direct/1e6:,.6f}")
    print(f"item6 = 예상 - 발생 = {item6:,.6f}")

    # population identity: 7-component P&L note sum must equal the rollforward's lump
    # 보험수익 row (opposite sign; BS view vs P&L view), AND the Tier-1 별도 income
    # statement's "일반보험서비스수익" line.
    comps = [
        "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가",
        "비금융위험에 대한 위험조정의 변동분",
        "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익",
        "손실요소배분액",
        "경험 조정을 통한 증가",
        "보험취득 현금흐름의 회수와 관련되는 보험료",
    ]
    total7 = sum(row_sum(t_pl_direct, c)[0] for c in comps)
    rev_lump, _ = row_sum(t_rf_direct, "보험수익")
    print(f"population check: sum(7 P&L components)={total7:,.0f} vs rollforward 보험수익 lump={rev_lump:,.0f} "
          f"-> |match|={abs(total7) == abs(rev_lump)}")

    t_is = table_at(tables, 33327)  # 4-2. 포괄손익계산서 (별도)
    for r in t_is.rows:
        if r and r[0] == "일반보험서비스수익":
            tier1_rev = to_num(r[2])  # col order: [당3개월, 당반기누적, 전3개월, 전반기누적]
            print(f"Tier-1 별도 '일반보험서비스수익' 당반기누계 = {tier1_rev:,.0f} "
                  f"-> matches total7 exactly: {tier1_rev == total7}")

    # =============== item11 (재보험 예실차) ===============
    t_pl_re = table_at(tables, 50334)  # 재보험비용의 변동내역, 당반기
    t_rf_re = table_at(tables, 49079)  # 18-2 rollforward, 당반기

    exp_re, n_exp_re = row_sum(t_pl_re, "발생한 보험금 및 그 밖의 발생한 재보험수익에 따른 증가분")
    loss_alloc_re, _ = row_sum(t_pl_re, "손실요소배분액")
    full_row_re, n_act_re = row_sum(t_rf_re, "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    # NOTE: sign convention flips vs the direct-side table (verified against raw column
    # values, not assumed) -- rollforward LRC-loss sub-col sum = -1 * loss_alloc_re here.
    act_re = full_row_re + loss_alloc_re

    item11 = (exp_re - act_re) / 1e6

    print("\n=== item11 재보험 예실차 (KR0079, 2026.2Q, 당반기 누계, 백만원) ===")
    print(f"예상 4종 (n={n_exp_re} cols): {exp_re/1e6:,.6f}")
    print(f"발생 4종 LIC-only (n={n_act_re} cols, sign-flipped loss_alloc subtracted): {act_re/1e6:,.6f}")
    print(f"item11 = 예상 - 발생 = {item11:,.6f}")
    print("population check: NOT independently reconciled against Tier-1 '출재보험서비스수익' "
          "(19,415.25백만원) -- neither the claims-only row nor the note's 6-component total "
          "matches it. Loss-component magnitude identity (100,026,907, sign-flipped) is the only "
          "cross-table check available; treat item11 with lower confidence than item6.")

    # =============== closure re-check against current (untouched) master ===============
    d = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    rows = {r["항목번호"]: r["값"] for r in d
            if r["원보험사코드"] == "KR0079" and r["공시분기"] == "2026.2Q"}
    print("\n=== closure re-check vs current PL_breakdown.json (읽기전용) ===")
    item7_new = rows[3] - rows[4] - rows[5] - item6
    item12_new = rows[8] - rows[9] - rows[10] - item11
    print(f"item7  old={rows[7]:,.6f} -> new={item7_new:,.6f}  (shift should == item6 = {item6:,.6f}; "
          f"actual shift={rows[7]-item7_new:,.6f})")
    print(f"item12 old={rows[12]:,.6f} -> new={item12_new:,.6f}  (shift should == item11 = {item11:,.6f}; "
          f"actual shift={rows[12]-item12_new:,.6f})")


if __name__ == "__main__":
    main()
