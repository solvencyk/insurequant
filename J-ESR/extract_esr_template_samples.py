# -*- coding: utf-8 -*-
"""
J-ESR regulatory-template extractor prototype (FY2025 samples) — three layers.

  layer "esr"          : the 令和7年金融庁告示第74号/75号 regulatory tables (headline, eligible-capital composition,
                         required-capital composition, EBS, insurance-liability bridge, sensitivity, method flags)
  layer "article_axes" : the three FSA-monitoring-report axes (docs/domains/claude-agent-jp.md §4b) that live in
                         OTHER sections of the same disclosure PDF — 異常危険準備金 / 再保険(AIR) / 基礎利益·逆ざや —
                         plus the ESR placeholder skeleton for companies that print 後日公表予定.
  layer "profit"       : J-GAAP statutory P&L (損益計算書 spine, 損保 保険引受利益·資産運用損益·損害率/事業費率/合算率,
                         生保 基礎利益·キャピタル/臨時損益·三利源) with 前年度/当年度 pairs + accounting-basis meta
                         (accounting_basis / ifrs17_applied, evidence sentences only). Ticket 20260912T1150Z.

Reads the local sample PDFs with fitz and emits:
  (B) J-ESR/esr_disclosure_schema.json
  (C) J-ESR/raw/fy2025_samples/extracted_sample_values.json   (values + self-check)
  (scratch) J-ESR/raw/fy2025_samples/_item_table_fragment.md   (markdown table rows for the domain doc)

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/extract_esr_template_samples.py

No network. Amounts are stored as disclosed (百万円 unless the item says otherwise); ratios in %.
Dashes ("－"/"ー") are stored as null (= not applicable / zero); checks treat null as 0.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "J-ESR" / "raw" / "fy2025_samples"
SCHEMA_OUT = ROOT / "J-ESR" / "esr_disclosure_schema.json"
VALUES_OUT = SAMPLES / "extracted_sample_values.json"
CENSUS = ROOT / "J-ESR" / "fy2025_esr_census_20260912.csv"
RULES = ROOT / "J-ESR" / "esr_aggregation_rules.json"  # 告示74/75 aggregation matrices (hand-transcribed, see sources[] inside)
MD_FRAGMENT_OUT = SAMPLES / "_item_table_fragment.md"

DASHES = {"-", "ー", "−", "―", "‐", "－"}
NUM_RE = re.compile(r"^[△▲]?\d{1,3}(,\d{3})*(\.\d+)?%?$")
M = "JPY_million"
P = "pct"


def norm(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip()


def is_dash(tok: str) -> bool:
    return tok.rstrip("%") in DASHES


def is_num(tok: str) -> bool:
    return bool(NUM_RE.match(tok))


def is_val(tok: str) -> bool:
    return is_dash(tok) or is_num(tok)


def to_val(tok):
    if tok is None or is_dash(tok):
        return None
    neg = tok.startswith("△") or tok.startswith("▲")
    t = tok.lstrip("△▲").replace(",", "").rstrip("%")
    v = float(t) if "." in t else int(t)
    return -v if neg else v


# layer "history" helpers — 主要な経営指標等の推移 5개년표 rows sometimes wrap a value in full/half-width
# parens (Meiji Yasuda: 対前期増減率 % next to each amount, and the pre-FY2025 旧基準 SMR figures) while
# au's version of the same table never uses parens. strip_paren() lets one row-walker handle both.
PAREN_NUM_RE = re.compile(r"^[（(]([△▲]?[\d,]+\.?\d*%?)[）)]$")
PAREN_DASH_RE = re.compile(r"^[（(](?:" + "|".join(re.escape(d) for d in DASHES) + r")[）)]$")


def strip_paren(tok: str):
    """(bare_token, was_paren_wrapped). Only unwraps a NUMBER inside parens (not a dash — those are
    handled separately by PAREN_DASH_RE as pure noise to skip, since 決算 tables use them for a
    zeroed-out sub-item like 積立勘定 rather than a real prior-year figure)."""
    m = PAREN_NUM_RE.match(tok)
    return (m.group(1), True) if m else (tok, False)


# --------------------------------------------------------------------------------------
# layer "esr" item spec.  One list drives the schema (B), the extraction (C) and the doc table (A).
#   col: "cur" = 2nd token (当年度; 1st token is 前年度 '－' in FY2025), "ev" = last token (EBS 経済価値ベースの額),
#        "first" = 1st token when the row has all 4 EBS columns (財務会計ベースの額)
#   kics: K-ICS master item number (docs/agents/kics-json-validation-rules.md) or None when the concept does not map.
# --------------------------------------------------------------------------------------
ITEMS = [
    # ---- T1 headline summary (要約) ----
    dict(id="eligible_capital", table="T1", labels=[r"^適格資本の額\s*\(A\)$"], ko="적격자본 총액(A)", unit=M, parent=None,
         formula="= tier1_eligible + tier2_eligible", required=True, kics=1),
    dict(id="required_capital", table="T1", labels=[r"^所要資本の額\s*\(B\)$"], ko="소요자본 총액(B, 세효과 고려후)", unit=M, parent=None,
         formula="= rc_post_tax", required=True, kics=14),
    dict(id="esr_pct", table="T1", labels=[r"^ソルベンシー・マージン比率\s*\(\s*\(A\)\s*/\s*\(B\)\s*\)$"],
         ko="ESR(경제가치기준 지급여력비율, 신기준 SMR)", unit=P, parent=None,
         formula="= eligible_capital / required_capital * 100 (truncation interval)", required=True, kics=27),

    # ---- T2 eligible capital composition (適格資本の額の構成) ----
    dict(id="tier1_eligible", table="T2", labels=[r"^Tier1適格資本の額"], ko="Tier1 적격자본(A)", unit=M, parent="eligible_capital",
         formula="= tier1_basic - tier1_adjustments", required=True, kics=2),
    dict(id="tier1_basic", table="T2", labels=[r"^Tier1適格資本に係る基礎項目の額"], ko="Tier1 기초항목(B) = EBS 순자산", unit=M, parent="tier1_eligible",
         formula="= tier1_instr_unrestricted + tier1_instr_restricted + tier1_non_instrument; == ebs_net_assets", required=True, kics=4),
    dict(id="tier1_instr_unrestricted", table="T2", labels=[r"^算入制限のないTier1資本調達手段の額"], ko="산입제한 없는 Tier1 자본조달수단(자본금·기금)", unit=M, parent="tier1_basic", formula=None, required=False, kics=5),
    dict(id="tier1_instr_restricted", table="T2", labels=[r"^算入制限のあるTier1資本調達手段の額"], ko="산입제한 있는 Tier1 자본조달수단(신종자본증권 등)", unit=M, parent="tier1_basic", formula=None, required=False, kics=6),
    dict(id="tier1_non_instrument", table="T2", labels=[r"^資本調達手段以外のTier1適格資本の額"], ko="자본조달수단 이외 Tier1 적격자본", unit=M, parent="tier1_basic",
         formula="= tier1_ni_retained_earnings + tier1_ni_capital_surplus + tier1_ni_aoci + tier1_ni_other_contrib + tier1_ni_ev_adjustment", required=False, kics=None),
    dict(id="tier1_ni_retained_earnings", table="T2", labels=[r"^剰余金等の額又は利益剰余金等の額"], ko="잉여금등(이익잉여금+규제상 준비금)", unit=M, parent="tier1_non_instrument",
         formula="= ebs_retained_earnings + ebs_regulatory_reserve_equity", required=False, kics=7),
    dict(id="tier1_ni_capital_surplus", table="T2", labels=[r"^資本剰余金\(Tier2適格資本に算入されるものを除く\)の額"], ko="자본잉여금(Tier2 산입분 제외)", unit=M, parent="tier1_non_instrument", formula="== ebs_capital_surplus", required=False, kics=None),
    dict(id="tier1_ni_aoci", table="T2", labels=[r"^その他の包括利益累計額又は評価・換算差額等の額"], ko="기타포괄손익누계액(평가·환산차액)", unit=M, parent="tier1_non_instrument", formula="== ebs_aoci", required=False, kics=9),
    dict(id="tier1_ni_other_contrib", table="T2", labels=[r"^その他の拠出金等の額"], ko="기타 출자금등", unit=M, parent="tier1_non_instrument", formula=None, required=False, kics=None),
    dict(id="tier1_ni_ev_adjustment", table="T2", labels=[r"^経済価値ベースの調整額"], ko="경제가치기준 조정액(EBS 순자산 − 회계 순자산 − 규제상 준비금)", unit=M, parent="tier1_non_instrument", formula="== ebs_ev_adjustment", required=False, kics=11),
    dict(id="tier1_adjustments", table="T2", labels=[r"^Tier1適格資本に係る調整項目の額"], ko="Tier1 조정항목(C, 공제)", unit=M, parent="tier1_eligible",
         formula="= Σ tier1_adj_* (7 subs)", required=True, kics=12),
    dict(id="tier1_adj_intangibles", table="T2", labels=[r"^無形固定資産\(繰延税金負債相殺後\)の額"], ko="무형고정자산(DTL 상계후)", unit=M, parent="tier1_adjustments", formula="== ebs_intangibles", required=False, kics=None),
    dict(id="tier1_adj_dta", table="T2", labels=[r"^繰延税金資産の額"], ko="이연법인세자산", unit=M, parent="tier1_adjustments", formula=None, required=False, kics=None),
    dict(id="tier1_adj_pension_asset", table="T2", labels=[r"^前払年金費用又は退職給付に係る資産"], ko="선급연금비용/퇴직급여 관련 자산", unit=M, parent="tier1_adjustments", formula=None, required=False, kics=None),
    dict(id="tier1_adj_holdings_other_fi", table="T2", labels=[r"^他の金融機関等が意図的に保有しているTier1資本調達手段の額"], ko="타 금융기관 의도적 보유 Tier1 조달수단", unit=M, parent="tier1_adjustments", formula=None, required=False, kics=None),
    dict(id="tier1_adj_own_instruments", table="T2", labels=[r"^自己のTier1資本調達手段への投資の額"], ko="자기 Tier1 조달수단 투자", unit=M, parent="tier1_adjustments", formula=None, required=False, kics=None),
    dict(id="tier1_adj_ineligible_reinsurance", table="T2", labels=[r"^不適格再保険資産の額"], ko="부적격 재보험자산", unit=M, parent="tier1_adjustments", formula=None, required=False, kics=None),
    dict(id="tier1_adj_encumbered_excess", table="T2", labels=[r"^処分制約のある資産のうち関連する負債と所要資本を上回る額"], ko="처분제약 자산 중 관련부채+소요자본 초과분", unit=M, parent="tier1_adjustments", formula=None, required=False, kics=None),
    dict(id="tier2_eligible", table="T2", labels=[r"^Tier2適格資本の額"], ko="Tier2 적격자본(D)", unit=M, parent="eligible_capital",
         formula="= tier2_basic - tier2_adjustments - tier2_cap_deduction", required=True, kics=3),
    dict(id="tier2_basic", table="T2", labels=[r"^Tier2適格資本に係る基礎項目の額"], ko="Tier2 기초항목(E)", unit=M, parent="tier2_eligible",
         formula="= tier2_instruments + tier2_non_instrument", required=False, kics=None),
    dict(id="tier2_instruments", table="T2", labels=[r"^Tier2資本調達手段の額$"], ko="Tier2 자본조달수단(후순위채 등)", unit=M, parent="tier2_basic",
         formula="= tier2_instr_t1_excess + tier2_instr_paid + tier2_instr_unpaid", required=False, kics=None),
    dict(id="tier2_instr_t1_excess", table="T2", labels=[r"^算入制限のあるTier1資本調達手段の制限を超過した額"], ko="제한초과 Tier1 조달수단(Tier2 재분류)", unit=M, parent="tier2_instruments", formula=None, required=False, kics=13),
    dict(id="tier2_instr_paid", table="T2", labels=[r"^払込済みTier2資本調達手段の額"], ko="납입완료 Tier2 조달수단", unit=M, parent="tier2_instruments", formula=None, required=False, kics=None),
    dict(id="tier2_instr_unpaid", table="T2", labels=[r"^払込未済のTier2資本調達手段の額"], ko="미납입 Tier2 조달수단(약정자본)", unit=M, parent="tier2_instruments", formula=None, required=False, kics=None),
    dict(id="tier2_non_instrument", table="T2", labels=[r"^資本調達手段以外のTier2適格資本の額"], ko="자본조달수단 이외 Tier2 적격자본", unit=M, parent="tier2_basic",
         formula="= tier2_ni_surplus_from_instr + tier2_ni_encumbered_t1_deducted + tier2_ni_basket", required=False, kics=None),
    dict(id="tier2_ni_surplus_from_instr", table="T2", labels=[r"^Tier2資本調達手段の額に含まれる資本調達手段を"], ko="Tier2 조달수단 발행 자본잉여금", unit=M, parent="tier2_non_instrument", formula=None, required=False, kics=None),
    dict(id="tier2_ni_encumbered_t1_deducted", table="T2", labels=[r"^処分制約のある資産のうちTier1適格資本から控除される額"], ko="처분제약 자산 중 Tier1 공제분", unit=M, parent="tier2_non_instrument", formula=None, required=False, kics=None),
    dict(id="tier2_ni_basket", table="T2", labels=[r"^Tier2バスケット\(上限適用後\)の額"], ko="Tier2 바스켓(상한 적용후)", unit=M, parent="tier2_non_instrument", formula=None, required=False, kics=None),
    dict(id="tier2_adjustments", table="T2", labels=[r"^Tier2適格資本に係る調整項目の額"], ko="Tier2 조정항목(F)", unit=M, parent="tier2_eligible",
         formula="= tier2_adj_holdings_other_fi + tier2_adj_own_instruments", required=False, kics=None),
    dict(id="tier2_adj_holdings_other_fi", table="T2", labels=[r"^他の金融機関等が意図的に保有しているTier2資本調達手段の額"], ko="타 금융기관 의도적 보유 Tier2 조달수단", unit=M, parent="tier2_adjustments", formula=None, required=False, kics=None),
    dict(id="tier2_adj_own_instruments", table="T2", labels=[r"^自己のTier2資本調達手段への投資の額"], ko="자기 Tier2 조달수단 투자", unit=M, parent="tier2_adjustments", formula=None, required=False, kics=None),
    dict(id="tier2_cap_deduction", table="T2", labels=[r"^Tier2適格資本への上限適用による控除の額"], ko="Tier2 상한 적용 공제(G)", unit=M, parent="tier2_eligible", formula=None, required=False, kics=None),
    dict(id="eligible_capital_total", table="T2", labels=[r"^適格資本の額\s*\(\(A\)\+\(D\)\)$", r"^適格資本の額\(A\)\+\(D\)$"], ko="적격자본 합계(A+D) — T2 표 합계행", unit=M, parent=None,
         formula="== eligible_capital", required=True, kics=1),

    # ---- T3 required capital composition (所要資本の額の構成) ----
    dict(id="rc_life", table="T3", labels=[r"^生命保険リスクの額"], ko="생명보험리스크(A)", unit=M, parent="rc_pre_tax",
         formula="= sqrt(x^T R x) of rc_life_* subs (告示74 第八十一条 matrix, esr_aggregation_rules.json levels.life)", required=True, kics=17),
    # life sub-rows (告示75 別紙様式第三号; 損保 may omit when immaterial — 注 2(7) — hence optional). Searched only up to 損害保険リスクの額
    # so that the life マネジメント・アクション row does not swallow the 巨大災害 one when the block is omitted.
    dict(id="rc_life_mortality", table="T3", labels=[r"^死亡リスクの額"], ko="사망리스크", unit=M, parent="rc_life", formula=None, required=False, optional=True, stop_before=r"^損害保険リスクの額", kics=29),
    dict(id="rc_life_longevity", table="T3", labels=[r"^長寿リスクの額"], ko="장수리스크", unit=M, parent="rc_life", formula=None, required=False, optional=True, stop_before=r"^損害保険リスクの額", kics=30),
    dict(id="rc_life_morbidity", table="T3", labels=[r"^罹患及び障害リスクの額"], ko="이환·장해리스크(질병·상해)", unit=M, parent="rc_life", formula=None, required=False, optional=True, stop_before=r"^損害保険リスクの額", kics=31),
    dict(id="rc_life_lapse", table="T3", labels=[r"^解約及び失効リスクの額"], ko="해지·실효리스크", unit=M, parent="rc_life", formula=None, required=False, optional=True, stop_before=r"^損害保険リスクの額", kics=33),
    dict(id="rc_life_expense", table="T3", labels=[r"^経費リスクの額"], ko="사업비리스크", unit=M, parent="rc_life", formula=None, required=False, optional=True, stop_before=r"^損害保険リスクの額", kics=34),
    dict(id="rc_life_mgmt_action", table="T3", labels=[r"^マネジメント・アクションの効果の額"], ko="경영조치 효과(생보, 정보행 — 하위액에 이미 반영)", unit=M, parent="rc_life", formula=None, required=False, optional=True, stop_before=r"^損害保険リスクの額", kics=None),
    dict(id="rc_nonlife", table="T3", labels=[r"^損害保険リスクの額"], ko="손해보험리스크(B)", unit=M, parent="rc_pre_tax",
         formula="<= rc_nl_liability + rc_nl_motor + rc_nl_property + rc_nl_other (correlation aggregation)", required=True, kics=18),
    dict(id="rc_nl_liability", table="T3", labels=[r"^賠償責任保険類似の商品に係るリスクの額"], ko="배상책임보험 유사 상품 리스크", unit=M, parent="rc_nonlife", formula=None, required=False, kics=None),
    dict(id="rc_nl_motor", table="T3", labels=[r"^自動車保険類似の商品に係るリスクの額"], ko="자동차보험 유사 상품 리스크", unit=M, parent="rc_nonlife", formula=None, required=False, kics=None),
    dict(id="rc_nl_property", table="T3", labels=[r"^財物保険類似の商品に係るリスクの額"], ko="재물보험 유사 상품 리스크", unit=M, parent="rc_nonlife", formula=None, required=False, kics=None),
    dict(id="rc_nl_other", table="T3", labels=[r"^その他保険に係るリスクの額"], ko="기타보험 리스크", unit=M, parent="rc_nonlife", formula=None, required=False, kics=None),
    dict(id="rc_catastrophe", table="T3", labels=[r"^巨大災害リスクの額"], ko="거대재해리스크(C)", unit=M, parent="rc_pre_tax",
         formula="<= rc_cat_natural + rc_cat_other - rc_cat_mgmt_action", required=True, kics=None),
    dict(id="rc_cat_natural", table="T3", labels=[r"^巨大自然災害リスクの額"], ko="거대자연재해리스크", unit=M, parent="rc_catastrophe",
         formula="<= rc_cat_nat_jp_earthquake + rc_cat_nat_jp_windflood + rc_cat_nat_jp_snow + rc_cat_nat_foreign + rc_cat_nat_other", required=False, kics=None),
    dict(id="rc_cat_nat_jp_earthquake", table="T3", labels=[r"^日本における地震に係るリスクの額"], ko="일본 지진", unit=M, parent="rc_cat_natural", formula=None, required=False, kics=None),
    dict(id="rc_cat_nat_jp_windflood", table="T3", labels=[r"^日本における風水災に係るリスクの額"], ko="일본 풍수해", unit=M, parent="rc_cat_natural", formula=None, required=False, kics=None),
    dict(id="rc_cat_nat_jp_snow", table="T3", labels=[r"^日本における雪災に係るリスクの額"], ko="일본 설해", unit=M, parent="rc_cat_natural", formula=None, required=False, kics=None),
    dict(id="rc_cat_nat_foreign", table="T3", labels=[r"^外国における巨大自然災害リスクの額"], ko="해외 거대자연재해", unit=M, parent="rc_cat_natural", formula=None, required=False, kics=None),
    dict(id="rc_cat_nat_other", table="T3", labels=[r"^その他の額$"], ko="기타(거대자연재해 내)", unit=M, parent="rc_cat_natural", formula=None, required=False, kics=None),
    dict(id="rc_cat_other", table="T3", labels=[r"^その他の巨大災害に係るリスクの額"], ko="기타 거대재해(팬데믹·테러 등)", unit=M, parent="rc_catastrophe", formula=None, required=False, kics=None),
    dict(id="rc_cat_mgmt_action", table="T3", labels=[r"^マネジメント・アクションの効果の額"], ko="경영조치 효과(거대재해)", unit=M, parent="rc_catastrophe", formula=None, required=False, kics=None),
    dict(id="rc_market", table="T3", labels=[r"^市場リスクの額"], ko="시장리스크(D)", unit=M, parent="rc_pre_tax",
         formula="<= rc_mkt_interest + rc_mkt_spread + rc_mkt_equity + rc_mkt_property + rc_mkt_fx + rc_mkt_concentration - rc_mkt_mgmt_action", required=True, kics=19),
    dict(id="rc_mkt_interest", table="T3", labels=[r"^金利リスクの額"], ko="금리리스크", unit=M, parent="rc_market", formula=None, required=False, kics=36),
    dict(id="rc_mkt_spread", table="T3", labels=[r"^スプレッドリスクの額"], ko="스프레드리스크", unit=M, parent="rc_market", formula=None, required=False, kics=None),
    dict(id="rc_mkt_equity", table="T3", labels=[r"^株式リスクの額"], ko="주식리스크", unit=M, parent="rc_market", formula=None, required=False, kics=37),
    dict(id="rc_mkt_property", table="T3", labels=[r"^不動産リスクの額"], ko="부동산리스크", unit=M, parent="rc_market", formula=None, required=False, kics=38),
    dict(id="rc_mkt_fx", table="T3", labels=[r"^為替リスクの額"], ko="환리스크", unit=M, parent="rc_market", formula=None, required=False, kics=39),
    dict(id="rc_mkt_concentration", table="T3", labels=[r"^資産集中リスクの額"], ko="자산집중리스크", unit=M, parent="rc_market", formula=None, required=False, kics=40),
    dict(id="rc_mkt_mgmt_action", table="T3", labels=[r"^マネジメント・アクションの効果の額"], ko="경영조치 효과(시장)", unit=M, parent="rc_market", formula=None, required=False, kics=None),
    dict(id="rc_credit", table="T3", labels=[r"^信用リスクの額"], ko="신용리스크(E)", unit=M, parent="rc_pre_tax", formula=None, required=True, kics=20),
    dict(id="rc_operational", table="T3", labels=[r"^オペレーショナル・リスクの額"], ko="운영리스크(F)", unit=M, parent="rc_pre_tax", formula=None, required=True, kics=21),
    dict(id="rc_mgmt_action_excess", table="T3", labels=[r"^マネジメント・アクションの効果の上限超過額"], ko="경영조치 효과 상한초과액(G, 가산)", unit=M, parent="rc_pre_tax", formula=None, required=False, kics=None),
    dict(id="rc_diversification", table="T3", labels=[r"^分散効果の額"], ko="분산효과(H, 차감)", unit=M, parent="rc_pre_tax", formula=None, required=True, kics=16),
    dict(id="rc_pre_tax", table="T3", labels=[r"^所要資本の額\(税効果考慮前\)"], ko="소요자본(세효과 고려전, I/J)", unit=M, parent="required_capital",
         formula="= rc_life + rc_nonlife + rc_catastrophe + rc_market + rc_credit + rc_operational + rc_mgmt_action_excess - rc_diversification + rc_non_insurance_business", required=True, kics=15),
    dict(id="rc_tax_effect", table="T3", labels=[r"^所要資本の税効果の額"], ko="소요자본 세효과(J/K, 차감)", unit=M, parent="required_capital", formula=None, required=True, kics=22),
    dict(id="rc_post_tax", table="T3", labels=[r"^所要資本の額\(税効果考慮後\)"], ko="소요자본(세효과 고려후) — T3 합계행", unit=M, parent=None,
         formula="= rc_pre_tax - rc_tax_effect; == required_capital", required=True, kics=14),

    # ---- T4 EBS (経済価値ベースのバランスシート) — value column = 経済価値ベースの額 (last) unless col='first' ----
    dict(id="ebs_total_assets", table="T4", labels=[r"^総資産$"], ko="EBS 총자산", unit=M, parent=None, formula="= statutory + reclass + revaluation (row-wise)", required=False, col="ev", kics=None),
    dict(id="ebs_intangibles", table="T4", labels=[r"^無形固定資産$"], ko="EBS 무형고정자산", unit=M, parent="ebs_total_assets", formula="== tier1_adj_intangibles", required=False, col="ev", kics=None),
    dict(id="ebs_reinsurance_recoverables", table="T4", labels=[r"^再保険回収額$"], ko="EBS 재보험회수액", unit=M, parent="ebs_total_assets", formula=None, required=False, col="ev", kics=None),
    dict(id="ebs_total_liabilities", table="T4", labels=[r"^総負債$"], ko="EBS 총부채", unit=M, parent=None, formula="= ebs_insurance_liabilities + ebs_non_insurance_liabilities", required=False, col="ev", kics=None),
    dict(id="ebs_insurance_liabilities", table="T4", labels=[r"^保険負債\(保険契約準備金\)合計$"], ko="EBS 보험부채 합계", unit=M, parent="ebs_total_liabilities", formula="= ebs_current_estimate + ebs_moce", required=False, col="ev", kics=None),
    dict(id="ebs_current_estimate", table="T4", labels=[r"^現在推計の額"], ko="현재추계(최선추정부채, BEL)", unit=M, parent="ebs_insurance_liabilities", formula=None, required=False, col="ev", kics=None),
    dict(id="ebs_moce", table="T4", labels=[r"^現在推計を超えるマージン"], ko="MOCE(현재추계 초과 마진, 위험마진)", unit=M, parent="ebs_insurance_liabilities", formula=None, required=False, col="ev", kics=None),
    dict(id="ebs_reg_reserve_in_liabilities", table="T4", labels=[r"^規制上の準備金に属するもの"], ko="규제상 준비금(위험준비금·이상위험준비금 등, 회계기준 보험부채 내) — イ열", unit=M, parent="ebs_insurance_liabilities", formula="reclassified to equity (ロ열 △)", required=False, col="first", kics=None),
    dict(id="ebs_non_insurance_liabilities", table="T4", labels=[r"^非保険負債合計$"], ko="EBS 비보험부채 합계", unit=M, parent="ebs_total_liabilities", formula=None, required=False, col="ev", kics=None),
    dict(id="ebs_other_reserves_reclass", table="T4", labels=[r"^その他の準備金$"], ko="기타 준비금(부채로 재분류된 규제상 준비금 일부) — ニ열", unit=M, parent="ebs_non_insurance_liabilities", formula=None, required=False, col="ev", optional=True, kics=None),
    dict(id="ebs_price_fluctuation_reserve", table="T4", labels=[r"^価格変動準備金$"], ko="가격변동준비금(회계기준, 자본으로 재분류) — イ열", unit=M, parent="ebs_non_insurance_liabilities", formula=None, required=False, col="first", optional=True, kics=None),
    dict(id="ebs_net_assets", table="T4", labels=[r"^純資産$"], ko="EBS 순자산", unit=M, parent=None,
         formula="= ebs_total_assets - ebs_total_liabilities; == tier1_basic; = ebs_net_assets_statutory + ebs_regulatory_reserve_equity + ebs_ev_adjustment", required=False, col="ev", kics=4),
    dict(id="ebs_net_assets_statutory", table="T4", labels=[r"^純資産$"], ko="회계기준 순자산(EBS 표 イ열)", unit=M, parent="ebs_net_assets", formula=None, required=False, col="first", reuse=True, kics=None),
    dict(id="ebs_capital_stock", table="T4", labels=[r"^基金又は資本金$", r"^資本金$"], ko="자본금/기금", unit=M, parent="ebs_net_assets", formula=None, required=False, col="ev", kics=None),
    dict(id="ebs_capital_surplus", table="T4", labels=[r"^資本剰余金$"], ko="자본잉여금", unit=M, parent="ebs_net_assets", formula=None, required=False, col="ev", kics=None),
    dict(id="ebs_retained_earnings", table="T4", labels=[r"^剰余金又は利益剰余金$", r"^利益剰余金$"], ko="이익잉여금", unit=M, parent="ebs_net_assets", formula=None, required=False, col="ev", kics=None),
    dict(id="ebs_regulatory_reserve_equity", table="T4", labels=[r"^規制上の準備金$"], ko="규제상 준비금(자본으로 재분류된 합계) — ニ열", unit=M, parent="ebs_net_assets",
         formula="≈ ebs_reg_reserve_in_liabilities + ebs_price_fluctuation_reserve - ebs_other_reserves_reclass (observed bridge)", required=False, col="ev", kics=None),
    dict(id="ebs_aoci", table="T4", labels=[r"^その他の包括利益累計額合計", r"^その他の包括利益累計額$"], ko="기타포괄손익누계액", unit=M, parent="ebs_net_assets", formula=None, required=False, col="ev", optional=True, kics=None),
    dict(id="ebs_ev_adjustment", table="T4", labels=[r"^経済価値ベースの調整額$"], ko="경제가치기준 조정액", unit=M, parent="ebs_net_assets", formula=None, required=False, col="ev", kics=11),

    # ---- T6 insurance liabilities by product (保険負債の商品別差異調整) — value = 経済価値ベースの額(MOCE除く) ----
    dict(id="il_total_ex_moce", table="T6", labels=[r"^保険負債$"], ko="보험부채(MOCE 제외) 경제가치", unit=M, parent=None, formula="== ebs_current_estimate", required=False, col="ev", kics=None),
    dict(id="il_unexpired", table="T6", labels=[r"^未経過責任に係る保険負債$"], ko="미경과책임 보험부채(LRC 상당)", unit=M, parent="il_total_ex_moce", formula=None, required=False, col="ev", kics=None),
    dict(id="il_incurred", table="T6", labels=[r"^既経過責任に係る保険負債$"], ko="기경과책임 보험부채(LIC 상당)", unit=M, parent="il_total_ex_moce", formula=None, required=False, col="ev", kics=None),
]

# extra esr-layer items not produced by the table walker (derived / variant-table / sensitivity / method)
EXTRA_ESR_ITEMS = [
    dict(id="rc_non_insurance_business", table="T1_combined", labels_ja=["非保険事業に係る所要資本の額"], ko="비보험사업 소요자본(i) — au 결합표에만 있는 행", unit=M, parent="rc_pre_tax", formula=None, required=False, column="cur", kics=23),
    dict(id="tier1_ratio_pct", table="derived", labels_ja=[], ko="기본자본비율 상당 = tier1_eligible / required_capital × 100 (일본 미공시, 파생)", unit=P, parent="esr_pct", formula="= tier1_eligible / required_capital * 100", required=False, column="derived", kics=28),
    dict(id="esr_pct_5yr_summary", table="summary_5yr", labels_ja=["単体ベースのソルベンシー・マージン比率", "ソルベンシー・マージン比率 新基準"], ko="5개년 주요지표 표의 헤드라인(교차확인용)", unit=P, parent="esr_pct", formula="== esr_pct", required=False, column="last", kics=None),
]

SENS_SCENARIOS = [
    ("base", "当期末の数値", "기준(당기말)"),
    ("jpy_rate_up50", "円金利50ベーシス・ポイント上昇", "엔 금리 +50bp"),
    ("jpy_rate_down50", "円金利50ベーシス・ポイント下降", "엔 금리 -50bp"),
    ("usd_rate_up50", "米ドル金利50ベーシス・ポイント上昇", "달러 금리 +50bp"),
    ("usd_rate_down50", "米ドル金利50ベーシス・ポイント下降", "달러 금리 -50bp"),
    ("jpy_ufr_down50", "円金利UFR50ベーシス・ポイント下降", "엔 UFR -50bp"),
    ("equity_property_down10", "株式・不動産10%下落", "주식·부동산 -10%"),
    ("fx_yen_up10", "為替10%円高", "환율 10% 엔고"),
]
SENS_ROWS = [
    ("esr_pct", r"^ソルベンシー・マージン比率$", "ESR", P, None),
    ("eligible_capital", r"^適格資本の額$", "적격자본", M, None),
    ("ebs_total_assets", r"^総資産$", "총자산", M, None),
    ("il_total_ex_moce", r"^保険負債の額", "보험부채(MOCE 제외)", M, None),
    ("ebs_moce", r"^現在推計を超える", "MOCE", M, None),
    ("ebs_non_insurance_liabilities", r"^非保険負債の額$", "비보험부채", M, None),
    ("ebs_net_assets", r"^純資産の額$", "순자산", M, "41 (base) / 43 (jpy_rate_up50) / 44 (jpy_rate_down50) — 충격폭 다름(K-ICS 규정 시나리오 vs 50bp), 근사"),
    ("required_capital", r"^所要資本の額$", "소요자본", M, None),
    ("rc_life", r"^生命保険リスクの額$", "생명보험리스크", M, None),
    ("rc_market", r"^市場リスクの額$", "시장리스크", M, None),
]

METHOD_ITEMS = [
    dict(id="internal_model_applied", ko="내부모형 적용 여부", labels=["内部モデル手法の適用"], type="tri"),
    dict(id="usp_applied", ko="회사고유 스트레스계수(USP) 적용 여부", labels=["会社固有のストレス係数手法の適用"], type="tri"),
    dict(id="internal_discount_rate_applied", ko="내부할인율 적용 여부", labels=["内部割引率手法の適用"], type="tri"),
    dict(id="mgmt_action_applied", ko="경영조치(management action) 반영 여부", labels=["マネジメント・アクション"], type="tri"),
    dict(id="risk_mitigation_reinsurance", ko="재보험 리스크경감 반영 여부", labels=["リスク削減手法", "リスク削減効果"], type="bool"),
    dict(id="transitional_measures", ko="경과조치(激変緩和措置) 적용 여부", labels=["経過措置", "激変緩和"], type="bool"),
    dict(id="sensitivity_omitted", ko="민감도 표 생략 여부(차이 1%p 미만 사유)", labels=["記載を省略"], type="bool"),
    dict(id="first_year_no_movement_analysis", ko="변동요인분석 미기재(초년도)", labels=["変動要因分析"], type="bool"),
]

# --------------------------------------------------------------------------------------
# layer "article_axes" — schema entries (values come from extract_axes)
# --------------------------------------------------------------------------------------
AXES_ITEMS = [
    # ESR placeholder skeleton (companies still at 後日公表予定)
    dict(id="esr_status", axis="esr_placeholder", applies="both", labels_ja=["後日公表予定", "別途公表予定", "2026年10月末に公表予定"], ko="posted / not_yet / not_found", unit="enum", kics=None),
    dict(id="esr_placeholder_locations", axis="esr_placeholder", applies="both", labels_ja=["ソルベンシー・マージン比率 新基準", "保険金等の支払能力の充実の状況（ソルベンシー・マージン比率）"], ko="'後日公表予定' 문구가 놓인 표/절 위치 목록(10월에 채워질 자리)", unit="list", kics=None),
    dict(id="smr_old_basis_fy2024_pct", axis="esr_placeholder", applies="both", labels_ja=["ソルベンシー・マージン比率 旧基準"], ko="구기준 SMR FY2024 (비교 참고, ESR 아님)", unit=P, kics=None),
    # 손보 축: 이상위험준비금
    dict(id="cat_reserve_total", axis="catastrophe_reserve_adequacy", applies="nonlife", labels_ja=["異常危険準備金", "責任準備金の内訳"], ko="이상위험준비금 잔액 합계(전 종목)", unit=M, kics=None),
    dict(id="cat_reserve_fire", axis="catastrophe_reserve_adequacy", applies="nonlife", labels_ja=["火災 行 × 異常危険準備金 列"], ko="화재 종목 이상위험준비금 잔액(금융청 부족 지적 대상)", unit=M, kics=None),
    dict(id="cat_reserve_by_line", axis="catastrophe_reserve_adequacy", applies="nonlife", labels_ja=["火災/海上/傷害/自動車/自動車損害賠償責任/その他"], ko="종목별 이상위험준비금 잔액", unit="dict", kics=None),
    dict(id="ordinary_reserve_total", axis="catastrophe_reserve_adequacy", applies="nonlife", labels_ja=["普通責任準備金"], ko="보통책임준비금 합계(같은 표)", unit=M, kics=None),
    dict(id="cat_reserve_adequacy_note", axis="catastrophe_reserve_adequacy", applies="nonlife", labels_ja=["積立不足", "積立率", "異常危険準備金の取崩"], ko="적립 부족/적립률 서술 유무 (없으면 null)", unit="text", kics=None),
    # 재보험 / AIR 축
    dict(id="air_used", axis="air_used", applies="both", labels_ja=["アセット・インテンシブ", "資産集約型再保険", "再保険"], ko="not_mentioned / mentioned / mentioned_esr_purpose", unit="enum", kics=None),
    dict(id="air_evidence", axis="air_used", applies="both", labels_ja=["既契約の出再に伴う損益", "共同保険式再保険", "最低保証再保険"], ko="AIR 정황 근거(기계약 출재 손익·관계사 재보험 각주 등)", unit="text", kics=None),
    dict(id="inforce_cession_pl", axis="air_used", applies="life", labels_ja=["既契約の出再に伴う損益に相当する額"], ko="기계약 출재 관련 손익(기초이익에서 제외된 액)", unit=M, kics=None),
    dict(id="reins_counterparties_n", axis="air_used", applies="both", labels_ja=["出再先保険会社の数", "再保険を引き受けた主要な保険会社等の数"], ko="출재 상대 재보험사 수", unit="count", kics=None),
    dict(id="reins_top5_share_pct", axis="air_used", applies="both", labels_ja=["出再保険料のうち上位5社の出再先に集中している割合", "支払再保険料の金額が大きい上位5社に対する支払再保険料の割合"], ko="상위 5사 출재보험료 집중도", unit=P, kics=None),
    dict(id="reins_rating_a_or_above_pct", axis="air_used", applies="both", labels_ja=["出再保険料の格付ごとの割合", "格付機関による格付に基づく区分ごとの支払再保険料の割合"], ko="A등급 이상 재보험사 출재보험료 비중", unit=P, kics=None),
    dict(id="reins_unreceived_claims", axis="air_used", applies="life", labels_ja=["未だ収受していない再保険金の金額"], ko="미수 재보험금", unit=M, kics=None),
    # 생보 축: 기초이익 / 이차손익
    dict(id="core_profit", axis="interest_margin_sign", applies="life", labels_ja=["基礎利益"], ko="기초이익(당기)", unit=M, kics=None),
    dict(id="core_profit_prev", axis="interest_margin_sign", applies="life", labels_ja=["基礎利益"], ko="기초이익(전기)", unit=M, kics=None),
    dict(id="negative_spread_100m", axis="interest_margin_sign", applies="life", labels_ja=["逆ざや", "逆鞘"], ko="역마진(逆ざや) 금액 — 단위 億円(표본 원문 단위) — 양수=역마진 존재", unit="JPY_100million", kics=None),
    dict(id="negative_spread_prev_100m", axis="interest_margin_sign", applies="life", labels_ja=["逆ざや"], ko="역마진 전기(億円)", unit="JPY_100million", kics=None),
    dict(id="interest_margin", axis="interest_margin_sign", applies="life", labels_ja=["利差損益", "利差益", "利差損", "順ざや"], ko="이차손익(三利源 공시사에서만)", unit=M, kics=None),
    dict(id="interest_margin_sign", axis="interest_margin_sign", applies="life", labels_ja=["利差損益", "逆ざや", "順ざや"], ko="positive / negative / unstated (역마진이면 negative)", unit="enum", kics=None),
    dict(id="three_source_disclosed", axis="interest_margin_sign", applies="life", labels_ja=["利差損益", "危険差損益", "費差損益"], ko="三利源(利差·危険差·費差) 분해 공시 여부", unit="bool", kics=None),
]

# --------------------------------------------------------------------------------------
# layer "profit" — J-GAAP statutory P&L layer (ticket 20260912T1150Z). Values are stored as {"cur": 当年度, "prev": 前年度}
# (百万円 as disclosed; ratios %). `scope`: life / nonlife / both. `pl`: Korean PL_breakdown item number
# (root PL_breakdown.json 항목번호 1~32) — strict counterpart only, null when the concept has no IFRS17 analogue.
# `src`: which table the row comes from — "pl" 損益計算書 / "uw" 保険引受利益明細表 / "ratio" 正味損害率·事業費率·合算率 표 /
#        "inv" 資産運用利回り(実現利回り) 표 / "core" 経常利益等の明細(基礎利益) 표 / "three" 三利源 표 / "meta" 회계방침 절.
# --------------------------------------------------------------------------------------
PROFIT_ITEMS = [
    # ---- common P&L spine (損益計算書) ----
    dict(id="pl_ordinary_revenue", scope="both", src="pl", labels=[r"^経常収益$"], ko="경상수익(총수익)", unit=M, formula=None, pl=None),
    dict(id="pl_ordinary_expenses", scope="both", src="pl", labels=[r"^経常費用$"], ko="경상비용(총비용)", unit=M, formula=None, pl=None),
    dict(id="pl_ordinary_profit", scope="both", src="pl", labels=[r"^経常利益$", r"^経常利益\s*A\+B\+C$"], ko="경상이익", unit=M,
         formula="= pl_ordinary_revenue - pl_ordinary_expenses; life: = pl_core_profit + pl_capital_gains + pl_extraordinary_pl; nonlife: = pl_underwriting_profit + pl_investment_pl + other (P07)", pl=20),
    dict(id="pl_extraordinary_gains", scope="both", src="pl", labels=[r"^特別利益$"], ko="특별이익", unit=M, formula=None, pl=None),
    dict(id="pl_extraordinary_losses", scope="both", src="pl", labels=[r"^特別損失$"], ko="특별손실", unit=M, formula=None, pl=None),
    dict(id="pl_pretax_profit", scope="both", src="pl", labels=[r"^税引前当期純利益$", r"^税引前当期純剰余$"], ko="법인세차감전 당기순이익", unit=M,
         formula="= pl_ordinary_profit + pl_extraordinary_gains - pl_extraordinary_losses", pl=22),
    dict(id="pl_income_taxes", scope="both", src="pl", labels=[r"^法人税等合計$"], ko="법인세등 합계", unit=M, formula=None, pl=23),
    dict(id="pl_net_income", scope="both", src="pl", labels=[r"^当期純利益$", r"^当期純剰余$"], ko="당기순이익(상호회사: 당기순잉여)", unit=M,
         formula="= pl_pretax_profit - pl_income_taxes", pl=24),
    dict(id="pl_interest_dividend_income", scope="both", src="pl", labels=[r"^利息及び配当金収入$", r"^利息及び配当金等収入$"], ko="이자 및 배당금 수입", unit=M, formula=None, pl=None),
    # ---- nonlife ----
    dict(id="pl_net_premiums_written", scope="nonlife", src="pl", labels=[r"^正味収入保険料$"], ko="정미수입보험료(원수+수재-출재)", unit=M,
         formula="= pl_gross_premiums_written + pl_assumed_premiums - pl_ceded_premiums", pl=None),
    dict(id="pl_net_claims_paid", scope="nonlife", src="pl", labels=[r"^正味支払保険金$"], ko="정미지급보험금", unit=M,
         formula="= pl_gross_claims_paid + pl_assumed_claims - pl_recovered_reinsurance_claims", pl=None),
    # ---- nonlife: 保険引受の状況 재보험 다리(bridge) — ticket 20260913T0025Z. table="bridge" is handled
    # specially in extract_profit() (via extract_bridge_block()/BRIDGE_ORDER), not by the generic
    # grab()-then-pick_pc() path other src values use, because each sub-table's own 合計 row sits
    # several lines below a heading that repeats elsewhere on the page (a per-employee footnote for
    # au, a footnote sentence for Meiji) — a plain label-regex grab would land on the wrong row.
    dict(id="pl_gross_premiums_written", scope="nonlife", src="bridge", labels=[r"元受正味保険料", r"元受正味保険料\(除く収入積立保険料\)", r"元受正味保険料\(含む収入積立保険料\)"], ko="원수정미보험료(출재 전, 元受正味保険料; 含む収入積立保険料 표만 있는 회사는 P14 에서 収入積立保険料 차감)", unit=M, formula=None, pl=None),
    dict(id="pl_assumed_premiums", scope="nonlife", src="bridge", labels=[r"受再正味保険料"], ko="수재정미보험료(受再正味保険料, 해당없으면 0)", unit=M, formula=None, pl=None),
    dict(id="pl_ceded_premiums", scope="nonlife", src="bridge", labels=[r"支払再保険料", r"出再正味保険料"], ko="출재보험료(支払再保険料; 損保ジャパン 표기 出再正味保険料)", unit=M, formula=None, pl=None),
    dict(id="pl_gross_claims_paid", scope="nonlife", src="bridge", labels=[r"元受正味保険金"], ko="원수정미보험금(元受正味保険金)", unit=M, formula=None, pl=None),
    dict(id="pl_assumed_claims", scope="nonlife", src="bridge", labels=[r"受再正味保険金"], ko="수재정미보험금(受再正味保険金, 해당없으면 0)", unit=M, formula=None, pl=None),
    dict(id="pl_recovered_reinsurance_claims", scope="nonlife", src="bridge", labels=[r"回収再保険金", r"出再正味保険金"], ko="회수재보험금(出再分 회수, 回収再保険金; 損保ジャパン 표기 出再正味保険金)", unit=M, formula=None, pl=None),
    dict(id="pl_loss_adjustment_expenses", scope="nonlife", src="pl", labels=[r"^損害調査費$"], ko="손해조사비", unit=M, formula=None, pl=None),
    dict(id="pl_commissions_collection", scope="nonlife", src="pl", labels=[r"^諸手数料及び集金費$"], ko="제수수료 및 집금비", unit=M, formula=None, pl=None),
    # 損益計算書の注記 「諸手数料及び集金費の内訳」: 支払諸手数料及び集金費 − 出再保険手数料 = 諸手数料及び集金費(P&L 순액).
    # 注記는 당기 단년이라 prev 없음. owner 2026-09-13: 출재보험수수료(재보험자가 출재사에 지급)는 재보험 수지에 넣는다.
    dict(id="pl_commissions_gross", scope="nonlife", src="note", labels=[r"支払諸手数料及び集金費"], ko="지급제수수료 및 집금비(총액, 注記; 당기만)", unit=M, formula="= pl_commissions_collection + pl_ceded_commission", pl=None),
    dict(id="pl_ceded_commission", scope="nonlife", src="note", labels=[r"出再保険手数料"], ko="출재보험수수료(재보험자→출재사 수취, 注記; 당기만) — 재보험 수지 구성항목", unit=M, formula=None, pl=None),
    dict(id="pl_operating_general_admin", scope="nonlife", src="pl", labels=[r"^営業費及び一般管理費$"], ko="영업비 및 일반관리비(전체)", unit=M, formula=None, pl=None),
    dict(id="pl_other_ordinary_revenue", scope="nonlife", src="pl", labels=[r"^その他経常収益$"], ko="기타경상수익", unit=M, formula=None, pl=None),
    dict(id="pl_other_ordinary_expenses", scope="nonlife", src="pl", labels=[r"^その他経常費用$"], ko="기타경상비용", unit=M, formula=None, pl=None),
    dict(id="pl_underwriting_revenue", scope="nonlife", src="uw", labels=[r"^保険引受収益$"], ko="보험인수수익", unit=M, formula=None, pl=None),
    dict(id="pl_underwriting_expenses", scope="nonlife", src="uw", labels=[r"^保険引受費用$"], ko="보험인수비용", unit=M, formula=None, pl=None),
    dict(id="pl_uw_operating_general_admin", scope="nonlife", src="uw", labels=[r"^保険引受に係る営業費及び一般管理費$"], ko="보험인수 관련 영업비·일반관리비", unit=M, formula=None, pl=None),
    dict(id="pl_underwriting_other", scope="nonlife", src="uw", labels=[r"^その他収支$"], ko="기타수지(자배책 법인세상당액 등)", unit=M, formula=None, pl=None),
    dict(id="pl_underwriting_profit", scope="nonlife", src="uw", labels=[r"^保険引受利益$"], ko="보험인수이익", unit=M,
         formula="= pl_underwriting_revenue - pl_underwriting_expenses - pl_uw_operating_general_admin + pl_underwriting_other", pl=1),
    dict(id="pl_investment_pl", scope="nonlife", src="inv", labels=[r"^合計$"], ko="자산운용손익(실현기준 = 資産運用収益+積立保険料等運用益-資産運用費用)", unit=M, formula=None, pl=17),
    dict(id="pl_loss_ratio_pct", scope="nonlife", src="ratio", labels=[r"^合計$"], ko="정미손해율 %", unit=P,
         formula="= (pl_net_claims_paid + pl_loss_adjustment_expenses) / pl_net_premiums_written * 100", pl=None),
    dict(id="pl_expense_ratio_pct", scope="nonlife", src="ratio", labels=[r"^合計$"], ko="정미사업비율 %", unit=P,
         formula="= (pl_commissions_collection + pl_uw_operating_general_admin) / pl_net_premiums_written * 100", pl=None),
    dict(id="pl_combined_ratio_pct", scope="nonlife", src="ratio", labels=[r"^合計$"], ko="합산비율 %", unit=P, formula="= pl_loss_ratio_pct + pl_expense_ratio_pct", pl=None),
    # ---- life ----
    dict(id="pl_premium_income", scope="life", src="pl", labels=[r"^保険料等収入$"], ko="보험료등수입(보험료+재보험수입)", unit=M, formula=None, pl=None),
    # 생보 損益計算書: 特別損益 다음, 税引前 앞에 契約者配当準備金繰入額(상호회사 社員配当準備金繰入額)이 온다 — 第一生命 FY2025 107,500 (2026-09-13 P04 실패로 발견)
    dict(id="pl_policyholder_dividend_provision", scope="life", src="pl", labels=[r"^契約者配当準備金繰入額$", r"^社員配当準備金繰入額$"], ko="계약자(사원)배당준비금 전입액(세전이익 차감 항목)", unit=M, formula=None, pl=None),
    dict(id="pl_core_profit", scope="life", src="core", labels=[r"^基礎利益$", r"^基礎利益\s*A$"], ko="기초이익(생보 핵심이익, 経常利益 - キャピタル損益 - 臨時損益)", unit=M,
         formula="= pl_ordinary_profit - pl_capital_gains - pl_extraordinary_pl; (三利源 공시사) ≈ pl_interest_margin + pl_mortality_margin + pl_expense_margin", pl=None),
    dict(id="pl_capital_gains", scope="life", src="core", labels=[r"^キャピタル損益$", r"^キャピタル損益\s*B$"], ko="캐피털손익(유가증권매각손익·파생·환차 등)", unit=M, formula=None, pl=None),
    dict(id="pl_extraordinary_pl", scope="life", src="core", labels=[r"^臨時損益$", r"^臨時損益\s*C$"], ko="임시손익(위험준비금·대손충당 등)", unit=M, formula=None, pl=None),
    dict(id="pl_interest_margin", scope="life", src="three", labels=[r"^利差損益$", r"^利差益$", r"^利差損$"], ko="이차손익(三利源)", unit=M, formula=None, pl=None),
    dict(id="pl_mortality_margin", scope="life", src="three", labels=[r"^危険差損益$", r"^危険差益$"], ko="위험차손익(三利源)", unit=M, formula=None, pl=None),
    dict(id="pl_expense_margin", scope="life", src="three", labels=[r"^費差損益$", r"^費差益$", r"^費差損$"], ko="비차손익(三利源)", unit=M, formula=None, pl=None),
]
PROFIT_META_ITEMS = [
    dict(id="accounting_basis", ko="회계기준 jgaap / ifrs / unstated — 회계방침 절·감사 문구·P&L 양식에서 판정(추정 금지)", unit="enum",
         labels=["企業会計基準", "標準責任準備金", "大蔵省告示第48号", "責任準備金繰入額", "保険業法第111条", "国際財務報告基準", "IFRS"]),
    dict(id="ifrs17_applied", ko="IFRS17 적용 true / false / unstated — false 는 accounting_basis=jgaap 가 확인된 単体 법정재무제표에서만(IFRS 는 上場社 連結 임의적용뿐)", unit="tri",
         labels=["IFRS第17号", "IFRS 17", "保険契約に関する国際財務報告基準"]),
    dict(id="accounting_basis_evidence", ko="판정 근거 문장(원문, 페이지) — A: 회계방침 절 명시 / B: 법정 P&L 양식(責任準備金繰入額 등)+会社法·保険業法 감사 문구", unit="text", labels=[]),
    dict(id="profit_source_doc", ko="손익 표가 있는 문서(별책만 있는 회사는 본편 URL) / NOT_ACQUIRED 사유", unit="text", labels=[]),
]

# 保険引受の状況 bridge (ticket 20260913T0025Z) — document order of the 6 sub-tables differs per
# company, so each item's heading is located by walking forward from the previous item's row
# (see extract_bridge_block()) rather than by a company-wide fixed page offset.
BRIDGE_ORDER = {
    "au_nonlife": ["pl_ceded_premiums", "pl_gross_premiums_written", "pl_assumed_premiums",
                   "pl_gross_claims_paid", "pl_recovered_reinsurance_claims", "pl_assumed_claims"],
    "meijiyasuda_nonlife": ["pl_gross_premiums_written", "pl_assumed_claims", "pl_recovered_reinsurance_claims",
                            "pl_assumed_premiums", "pl_ceded_premiums", "pl_gross_claims_paid"],
}

# --------------------------------------------------------------------------------------
# layer "by_line" (2026-09-13, ticket 20260913T0400Z) — 損保 保険引受の状況 種目別 표 3개
# (正味収入保険料 / 正味支払保険金(+正味損害率) / 正味損害率·正味事業費率·合算率). Each table is
# 種目 × 3 fiscal years; a row's value tokens are `3 × g` where g = tokens per year
# (au/TMNF/MSI/Sompo g=3, Meiji g=2). Amount = first token of each year group; the claims table's
# 3rd token is the 正味損害率 column; the ratio table's group is (損害率, 事業費率, 合算率).
# Values are stored as {line_code: {"prev": FY2024, "cur": FY2025}}. Sub-rows "(うち賠償責任)" are
# never matched (exact 7 labels only).
# --------------------------------------------------------------------------------------
LOB_LINES = [("fire", r"^火災$", "火災"), ("marine", r"^海上$", "海上"), ("pa", r"^傷害$", "傷害"), ("motor", r"^自動車$", "自動車"),
             ("cali", r"^自動車損害賠償責任$", "自動車損害賠償責任"), ("other", r"^その他$", "その他"), ("total", r"^合計$", "合計")]
BYLINE_ITEMS = [
    dict(id="lob_net_premiums_written", src="premiums", pos=0, labels=[r"正味収入保険料"], ko="종목별 정미수입보험료", unit=M, pl="pl_net_premiums_written"),
    dict(id="lob_net_claims_paid", src="claims", pos=0, labels=[r"正味支払保険金"], ko="종목별 정미지급보험금", unit=M, pl="pl_net_claims_paid"),
    dict(id="lob_loss_ratio_pct", src="ratio", pos=0, labels=[r"正味損害率", r"正味事業費率"], ko="종목별 정미손해율 %", unit=P, pl="pl_loss_ratio_pct"),
    dict(id="lob_expense_ratio_pct", src="ratio", pos=1, labels=[r"正味損害率", r"正味事業費率"], ko="종목별 정미사업비율 %", unit=P, pl="pl_expense_ratio_pct"),
    dict(id="lob_combined_ratio_pct", src="ratio", pos=2, labels=[r"正味損害率", r"正味事業費率"], ko="종목별 합산율 %", unit=P, pl="pl_combined_ratio_pct"),
]
# table headings per source (first line, from the top of the page list, that matches ALL regexes and is not a footnote)
BYLINE_HEADINGS = {
    "premiums": [r"^[\(（]?\d*[\)）]?\s*正味収入保険料"],
    "claims": [r"^[\(（]?\d*[\)）]?\s*正味支払保険金"],
    "ratio": [r"正味損害率", r"正味事業費率", r"合算率"],
}

# --------------------------------------------------------------------------------------
# layer "history" (2026-09-12, ticket 20260912T1440Z) — 「主要な経営指標等の推移」 5개년표.
# Both au and Meiji Yasuda Non-Life print this table with the same 5 fiscal-year columns
# (oldest -> newest); position in the row = fiscal year, regardless of company.
HIST_FISCAL_YEARS = ["FY2021", "FY2022", "FY2023", "FY2024", "FY2025"]

HISTORY_ITEMS = [
    dict(id="hist_net_premiums_written", scope="nonlife", labels=[r"^正味収入保険料$"], ko="정미수입보험료 5개년", unit=M,
         skip=[r"対前期増減率"], drop_paren=True, pl="pl_net_premiums_written"),
    dict(id="hist_ordinary_profit", scope="both", labels=[r"^経常利益$"], ko="경상이익 5개년", unit=M, skip=[], drop_paren=False, pl="pl_ordinary_profit"),
    dict(id="hist_net_income", scope="both", labels=[r"^当期純利益$", r"^当期純剰余$"], ko="당기순이익 5개년", unit=M, skip=[], drop_paren=False, pl="pl_net_income"),
    dict(id="hist_loss_ratio_pct", scope="nonlife", labels=[r"^正味損害率$"], ko="정미손해율 5개년 %", unit=P, skip=[], drop_paren=False, pl="pl_loss_ratio_pct"),
    dict(id="hist_expense_ratio_pct", scope="nonlife", labels=[r"^正味事業費率$"], ko="정미사업비율 5개년 %", unit=P, skip=[], drop_paren=False, pl="pl_expense_ratio_pct"),
    dict(id="hist_combined_ratio_pct", scope="nonlife", labels=None, ko="합산비율 5개년 % (파생 = 손해율+사업비율, 있으면 표 직접값 우선)", unit=P, skip=[], drop_paren=False, pl="pl_combined_ratio_pct"),
    dict(id="hist_total_assets", scope="both", labels=[r"^総資産額$"], ko="총자산 5개년", unit=M, skip=[r"うち積立勘定"], drop_paren=False, pl=None),
    dict(id="hist_net_assets", scope="both", labels=[r"^純資産額$"], ko="순자산 5개년", unit=M, skip=[], drop_paren=False, pl=None),
    dict(id="hist_smr_old_pct", scope="both", labels="smr", ko="구기준 단체 SMR 5개년 %(신제도 시행 전, 괄호로 병기된 회사만)", unit=P, skip=[], drop_paren=False, pl=None),
    dict(id="hist_esr_pct", scope="both", labels="smr", ko="신기준 ESR(경제가치기준 지급여력비율) 5개년 % — FY2025 부터 공표", unit=P, skip=[], drop_paren=False, pl=None),
    # 생보용 — 표본 2사(손보)엔 적용 없음. id·라벨만 정의(owner 지시).
    dict(id="hist_core_profit", scope="life", labels=[r"^基礎利益$", r"^基礎利益\s*A$"], ko="기초이익 5개년(생보)", unit=M, skip=[], drop_paren=False, pl=None),
    dict(id="hist_premium_income", scope="life", labels=[r"^保険料等収入$"], ko="보험료등수입 5개년(생보)", unit=M, skip=[], drop_paren=False, pl=None),
    dict(id="hist_policy_reserves", scope="life", labels=[r"^責任準備金残高$"], ko="책임준비금잔고 5개년(생보)", unit=M, skip=[], drop_paren=False, pl=None),
]
HIST_SMR_LABEL_RE = r"ソルベンシー.{0,3}マージン比率"

# Meiji Yasuda Non-Life main volume (別冊 has no P&L) — 損益計算書 p42 renders EVERY row label
# vertically (one glyph per line) AND groups ALL labels of a section before ALL its values
# (12-item 経常収益 block → 36 values in 3 year-major chunks; 15-item 経常費用 block → 45 values;
# then 経常利益(3) / 特別利益(9) / 特別損失(12) / 税引前~当期純利益(15) blocks) — grab()'s per-label
# regex + small skip_limit cannot anchor this shape at all, so item positions are read out of one
# flat run of value-tokens (labels are skipped regardless of rendering) at fixed offsets, verified
# 2026-09-12 against the real page (see docs/domains/jp_esr_disclosure_template.md §9-6).
# tuple = (idx at 2023년도, idx at 2024년도=prev, idx at 2025년도=cur) into that 120-token flat run.
MEIJI_PL_FLAT_MAP = {
    "pl_ordinary_revenue": (0, 12, 24), "pl_net_premiums_written": (2, 14, 26), "pl_other_ordinary_revenue": (11, 23, 35),
    "pl_interest_dividend_income": (7, 19, 31), "_inv_rev": (6, 18, 30),
    "pl_ordinary_expenses": (36, 51, 66), "pl_net_claims_paid": (38, 53, 68), "pl_loss_adjustment_expenses": (39, 54, 69),
    "pl_commissions_collection": (40, 55, 70), "pl_operating_general_admin": (46, 61, 76), "pl_other_ordinary_expenses": (47, 62, 77),
    "_inv_exp": (44, 59, 74),
    "pl_ordinary_profit": (81, 82, 83), "pl_extraordinary_gains": (84, 87, 90), "pl_extraordinary_losses": (93, 97, 101),
    "pl_pretax_profit": (105, 110, 115), "pl_income_taxes": (108, 113, 118), "pl_net_income": (109, 114, 119),
}

# --------------------------------------------------------------------------------------
# Big-3 non-life main volumes (ticket 20260913T0330Z) — ESR layer absent (all three print
# "2026年10月末までに開示" placeholders), every other layer extracted from the 292/272/292-page
# 現状2026 books under J-ESR/raw/fy2025_samples/others/. Per-company layout switches below are
# documented in docs/domains/jp_esr_disclosure_template.md §9-8 / §10-8.
OTHERS = "others"

# 保険引受の状況 bridge for the big-3: sub-table HEADINGS differ per company (Sompo Japan calls
# 支払再保険料 "出再正味保険料" and 回収再保険金 "出再正味保険金"; Tokio Marine prints 受再/支払 and
# 受再/回収 as PAIRED two-column tables) so each entry is (heading regex, id | (id_left, id_right)).
# Walked in document order with a shared cursor, values = the 合計 row's AMOUNT tokens (integers —
# 構成比/増減率 carry a decimal point) so the 6/7/9-token row shapes all reduce to [y1, y2, y3].
BRIDGE_SPEC = {
    "tokiomarine_nichido": [
        (r"^元受正味保険料\(含む収入積立保険料\)", "pl_gross_premiums_written"),
        (r"^受再正味保険料及び支払再保険料$", ("pl_assumed_premiums", "pl_ceded_premiums")),
        (r"^元受正味保険金$", "pl_gross_claims_paid"),
        (r"^受再正味保険金及び回収再保険金$", ("pl_assumed_claims", "pl_recovered_reinsurance_claims")),
    ],
    "mitsui_sumitomo": [
        (r"^2\s*元受正味保険料\(除く収入積立保険料\)", "pl_gross_premiums_written"),
        (r"^3\s*受再正味保険料の種目別推移", "pl_assumed_premiums"),
        (r"^4\s*支払再保険料の種目別推移", "pl_ceded_premiums"),
        (r"^1\s*元受正味保険金の種目別推移", "pl_gross_claims_paid"),
        (r"^2\s*受再正味保険金の種目別推移", "pl_assumed_claims"),
        (r"^3\s*回収再保険金の種目別推移", "pl_recovered_reinsurance_claims"),
    ],
    "sompo_japan": [
        (r"^1\s*元受正味保険料\(含む収入積立保険料\)", "pl_gross_premiums_written"),
        (r"^2\s*受再正味保険料$", "pl_assumed_premiums"),
        (r"^3\s*出再正味保険料$", "pl_ceded_premiums"),
        (r"^5\s*元受正味保険金$", "pl_gross_claims_paid"),
        (r"^6\s*受再正味保険金$", "pl_assumed_claims"),
        (r"^7\s*出再正味保険金$", "pl_recovered_reinsurance_claims"),
    ],
}

# 責任準備金の内訳 (by line × 普通責任/異常危険/危険/払戻/契約者配当/合計, FY2024 and FY2025 side by side
# = 12 numbers per row, or two stacked one-year tables = 6 per row). NB: norm() is NFKC, so the
# circled numerals MSI uses as table numbers ("②") arrive as plain digits ("2") — regexes below match those. Tokens are pulled with a regex
# from the text between one 種目 label and the next, because the 3 books glue cells together
# ("－1,109,472", "2,074,170 1,027,463", "自動車損害賠償責任 417,739 |").
RESERVE_SPEC = {
    "tokiomarine_nichido": dict(heading=r"^責任準備金の残高内訳$", year_marker=None),
    "mitsui_sumitomo": dict(heading=r"^3\s*責任準備金の種目別残高の内訳", year_marker=r"^2025年度末$"),
    "sompo_japan": dict(heading=r"^3\.\s*責任準備金の内訳$", year_marker=None),
}
RESERVE_LOBS = ["火災", "海上", "傷害", "自動車", "自動車損害賠償責任", "その他", "合計"]

COMPANIES = [
    dict(key="au_nonlife", company_jp="au損害保険", company_en="au Non-Life", sector="nonlife", pdf="au_nonlife_disclo_260730_4of5.pdf",
         byline_pages=dict(premiums=[2], claims=[4], ratio=[5]), layers=["esr", "article_axes", "profit", "history", "by_line"],
         pages=dict(T1=[22], T1_combined=[22], T2=[23], T3=[24], T4=[25], T6=[28], T7=[29], T8=[26, 27, 29]),
         headline_5yr_page=2, axes_pages=dict(reins=[6], reserves=[8]),
         profit_pages=dict(pl=[17], uw=[5], ratio=[5], inv=[11], summary5=[2], basis=[15, 17, 31], bridge=[3, 4]), pl_layout="prev_cur_diff"),
    dict(key="meijiyasuda_nonlife", company_jp="明治安田損害保険", company_en="Meiji Yasuda Non-Life", sector="nonlife", pdf="meijiyasuda_nonlife_20260904_performance_data.pdf",
         byline_pages=dict(premiums=[33], claims=[34], ratio=[35]), layers=["esr", "article_axes", "profit", "history", "by_line"],
         pages=dict(T1=[2], T2=[3], T3=[4], T4=[5, 6, 7], T6=[11], T7=[12], T8=[8, 13]),
         headline_5yr_page=None, axes_pages=dict(),
         # 別冊 業績データ has no P&L. Profit layer reads the MAIN VOLUME (separate PDF, owner-supplied
         # 2026-09-12 2nd round): J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260729_main.pdf (60p).
         # main() opens profit_pdf defensively — if it is absent this run, profit falls back to
         # NOT_ACQUIRED (below) rather than crashing the whole script.
         profit_pdf="meijiyasuda_nonlife_20260729_main.pdf",
         # The main volume disappeared from local disk partway through the 2026-09-12 session that
         # wired this (confirmed absent by exhaustive filesystem search + git history — never
         # tracked; cause unknown). main() prefers the live PDF when present; this fixture is a JSON
         # snapshot of doc[p-1].get_text('text') for pages 9/35/36/42/45, captured from the real file
         # BEFORE it vanished, so a re-run still fills the profit layer instead of going NOT_ACQUIRED.
         profit_pdf_fixture="meijiyasuda_nonlife_main_pages_fixture.json",
         profit_main_volume_url="https://www.meijiyasuda-sonpo.co.jp/profile/disclosure/pdf/20260729.pdf",
         profit_not_acquired="NOT_ACQUIRED: main volume 20260729.pdf is not on disk and no fixture was found either.",
         profit_pages=dict(pl=[42], uw=[36], ratio=[35], summary5=[9], basis=[42, 45], bridge=[33, 34]),
         pl_layout="label_block_3yr", vertical_labels=True,
         pl_flat_bounds=(r"損益計算書$", r"^損益計算書の注記"), pl_flat_len=120, pl_flat_map=MEIJI_PL_FLAT_MAP,
         pl_investment_override="pl_stmt",
         # 保険引受利益明細表 labels this row "営業費及び一般管理費" (bare), not the schema's canonical
         # "保険引受に係る営業費及び一般管理費" (that fuller phrase is only in the table's footnote).
         label_overrides={"pl_uw_operating_general_admin": [r"^営業費及び一般管理費$"]}),
    dict(key="nnlife", company_jp="エヌエヌ生命保険", company_en="NN Life", sector="life", pdf="nnlife_2025disclosure_202607.pdf",
         layers=["article_axes", "profit"], pages=dict(), headline_5yr_page=11,
         axes_pages=dict(summary5=[11], soundness=[15], core_profit=[60], reins=[64], esr_section=[54]),
         profit_pages=dict(pl=[44], core=[60], three=[60], basis=[47, 48, 49]), pl_layout="prev_pct_cur_pct"),
    # ---- Dai-ichi Life (2026-09-13 owner upload): アニュアルレポート2026 분책 index_004 「業績に関する諸資料」(86p). 책 페이지 = 분책 + 50.
    #      損益計算書 p25~26(2열 百万円) / 経常利益等の明細(基礎利益 A·B·C) p30 / 三利源 은 p31 이 億円 단위라 profit 층에서는 제외(core_history 에서 億円으로 수록) /
    #      再保険 p21 / 5개년 主要指標 p7(億円) / 会計方針 p32~33. ESR 층 없음(規制様式 미공표).
    dict(key="dai_ichi_life", company_jp="第一生命保険", company_en="Dai-ichi Life", sector="life", subdir=OTHERS, pdf="daiichi_2026_index_004.pdf",
         layers=["article_axes", "profit"], pages=dict(), headline_5yr_page=7,
         source_url="https://www.dai-ichi-life.co.jp/company/results/disclosure/2026/pdf/index_004.pdf", source_doc_type="アニュアルレポート2026 業績に関する諸資料(分冊, 86p)",
         axes_pages=dict(summary5=[7], core_profit=[30], reins=[21]),
         profit_pages=dict(pl=[25, 26], core=[30], three=[], basis=[32, 33]), pl_layout="prev_cur_diff"),
    # ---- big-3 non-life main volumes (ticket 20260913T0330Z): no ESR layer (not_yet), everything else ----
    dict(key="tokiomarine_nichido", company_jp="東京海上日動火災保険", company_en="Tokio Marine & Nichido Fire", sector="nonlife",
         subdir=OTHERS, pdf="tmnf_2026_full.pdf", byline_pages=dict(premiums=[89], claims=[91], ratio=[91]), layers=["article_axes", "profit", "history", "by_line"], pages=dict(), headline_5yr_page=None,
         source_url="https://www.tokiomarine-nichido.co.jp/company/pdf/TMNF_2026_d.pdf", source_doc_type="ディスクロージャー誌(東京海上日動の現状2026 本編, 292p)",
         axes_pages=dict(reins=[92], reserves=[118]), reins_style="tmnf",
         # 損益計算書 p102 = 2 columns (2024年度/2025年度, no 比較増減) → prev_cur_diff still reads toks[0]/[1].
         # 資産運用利回り(実現利回り) 合計 (p95) is 2-year × 3 and its numerator double-counts 積立保険料等運用益
         # (26,259) → pl_investment_pl comes from the P&L 資産運用収益−資産運用費用 instead (same rule as Meiji).
         profit_pages=dict(pl=[102], uw=[90], ratio=[91], summary5=[88], basis=[102, 109], bridge=[89, 90, 91]),
         pl_layout="prev_cur_diff", pl_investment_override="pl_stmt", summary5_skip_p10=True,
         label_overrides={"pl_uw_operating_general_admin": [r"^営業費及び一般管理費$"]},
         # 元受正味保険料 table is "(含む収入積立保険料)" only → P14 subtracts the P&L 収入積立保険料 line.
         bridge_gross_incl_deposit=True,
         # 主要な経営指標等の推移 p88: every amount row is followed by a (対前期増減(△)率) sub-label and each
         # value by its (x.x%) growth in parens → skip the sub-label, drop every paren token.
         hist_skip=[r"対前期増減"], hist_drop_paren_all=True),
    dict(key="mitsui_sumitomo", company_jp="三井住友海上火災保険", company_en="Mitsui Sumitomo Insurance", sector="nonlife",
         subdir=OTHERS, pdf="msi_2026_full.pdf", byline_pages=dict(premiums=[95], claims=[97], ratio=[99]), layers=["article_axes", "profit", "history", "by_line"], pages=dict(), headline_5yr_page=None,
         source_url="https://www.ms-ins.com/company/aboutus/disclosure/data/a01.pdf", source_doc_type="ディスクロージャー誌(Mitsui Sumitomo Insurance Disclosure 2026 本編, 272p)",
         axes_pages=dict(reins=[55], reserves=[123]), reins_style="msi",
         # 業績データ pages render row labels one glyph per line ("経|常|利|益") and P&L sub-items in ASCII
         # parens "(1,679,248)" → merge_vertical on every table incl. the P&L, unwrap paren values.
         profit_pages=dict(pl=[109], uw=[100], ratio=[99], summary5=[31], basis=[107, 109, 114], bridge=[94, 95, 96, 97]),
         pl_layout="prev_cur_diff", vertical_labels=True, vertical_pl=True, unwrap_parens=True,
         pl_investment_override="pl_stmt", summary5_skip_p10=True,
         label_overrides={"pl_uw_operating_general_admin": [r"^営業費及び一般管理費$"]},
         # p31 5개년표: label+"（対前期増減率）" merge into one line, growth % tokens sit as "（|1.27% ）" pairs;
         # 損害率/事業費率 carry TWO decimals here (62.85%) vs one in the 3-year table (62.8) → H01 tol 0.1 ok.
         # SMR row = 新基準/旧基準 pairs per year (旧基準 FY2021-24 722.5/684.3/691.1/706.3, 新基準 all "－"/(注1)).
         # growth cells arrive as "(" / "1.27% )" / "- )(" fragments (a backspace glyph after the paren) → skip all three shapes
         hist_skip=[r"^[（(]\W*$", r"%\s*[）)]", r"^-\s*[）)]", r"^[）)]$"], hist_drop_paren_all=True,
         hist_label_overrides={"hist_net_premiums_written": [r"^正味収入保険料"], "hist_ordinary_profit": [r"^経常利益"],
                               "hist_net_income": [r"^当期純利益"]},
         hist_smr_layout="new_old_pairs", smr_from_history=True),
    dict(key="sompo_japan", company_jp="損害保険ジャパン", company_en="Sompo Japan Insurance", sector="nonlife",
         subdir=OTHERS, pdf="sompojapan_2026_full.pdf", byline_pages=dict(premiums=[118], claims=[119], ratio=[120]), layers=["article_axes", "profit", "history", "by_line"], pages=dict(), headline_5yr_page=None,
         source_url="https://www.sompo-japan.co.jp/-/media/SJNK/files/company/disclosure/2026/sj_disc2026.pdf?la=ja-JP", source_doc_type="ディスクロージャー誌(損保ジャパンの現状2026 本編, 292p)",
         # 業績データ section (p116+) is set in subset MS-PGothic/YuGothic fonts WITHOUT a ToUnicode map: fitz
         # returns raw glyph ids (digits at +16044, kana at +5776/+5774, kanji = MS Gothic glyph order) →
         # GidDoc decodes span-by-span using the local msgothic.ttc cmap (see decode_gid_text()).
         gid_decode=True,
         axes_pages=dict(reins=[121, 122], reserves=[151]), reins_style="sompo",
         profit_pages=dict(pl=[136], uw=[122], ratio=[120], summary5=[116], basis=[136, 142], bridge=[117, 118, 119]),
         pl_layout="prev_cur_diff", pl_investment_override="pl_stmt", summary5_skip_p10=True,
         label_overrides={"pl_uw_operating_general_admin": [r"^営業費及び一般管理費$"]},
         bridge_gross_incl_deposit=True,
         hist_skip=[r"対前年度増減率"], hist_drop_paren_all=True),
]

# extract_axes() placeholder phrases — the big-3 print three new variants (§10-7).
ESR_PLACEHOLDER_PHRASES = ["後日公表予定", "別途公表予定", "10月末に公表予定", "後日公表",
                           "別時期での開示", "2026年10月末までに開示", "2026年10月末の予定"]


# --------------------------------------------------------------------------------------
# Sompo Japan glyph-id decoding (ticket 20260913T0330Z). The 業績データ pages embed subset
# MS-PGothic / YuGothic TrueType fonts with Identity-H and no ToUnicode CMap, so fitz emits the
# glyph index as the code point. Empirically (verified against p116 主要な財務指標 / p121-122
# 再保険 tables): ASCII glyphs sit at gid = cp + 16044, hiragana at cp + 5776, katakana at
# cp + 5774, a handful of full-width punctuation at fixed gids, and kanji glyph ids are exactly
# MS Gothic's glyph order (msgothic.ttc index 0 — has_glyph(cp) returns the gid, so the map is
# built by inverting it over the BMP). Properly-encoded spans (Iwata CID fonts) are left alone.
GID_FONT = Path(r"C:/Windows/Fonts/msgothic.ttc")
GID_BROKEN_FONTS = ("PGothic", "YuGothic", "MS-Mincho")
GID_PUNCT = {0x4804: "（", 0x4805: "）", 0x4802: "％", 0x4567: "△", 0x4809: "－", 0x4807: "＋", 0x3F82: "÷",
             0x4816: "：", 0x46B8: "、", 0x46B9: "。", 0x4819: "＝"}
_GID_MAP = None


def gid_map():
    global _GID_MAP
    if _GID_MAP is None:
        m = {}
        if GID_FONT.exists():
            f = fitz.Font(fontfile=str(GID_FONT))
            for cp in range(0x20, 0x10000):
                g = f.has_glyph(cp)
                if g and g not in m:
                    m[g] = cp
        _GID_MAP = m
    return _GID_MAP


def decode_gid_text(text):
    m = gid_map()
    out = []
    for c in text:
        o = ord(c)
        if o < 0x80:
            out.append(c)
        elif 32 <= o - 16044 <= 126:
            out.append(chr(o - 16044))
        elif 0x3041 + 5776 <= o <= 0x3096 + 5776:
            out.append(chr(o - 5776))
        elif 0x30A1 + 5774 <= o <= 0x30FC + 5774:
            out.append(chr(o - 5774))
        elif o in GID_PUNCT:
            out.append(GID_PUNCT[o])
        else:
            cp = m.get(o)
            out.append(chr(cp) if cp else c)
    return "".join(out)


class GidPage:
    def __init__(self, page):
        self._page = page
        self._text = None

    def get_text(self, kind="text"):
        if self._text is None:
            lines = []
            for b in self._page.get_text("dict")["blocks"]:
                for l in b.get("lines", []):
                    parts = []
                    for s in l["spans"]:
                        t = s["text"]
                        if any(k in s["font"] for k in GID_BROKEN_FONTS):
                            t = decode_gid_text(t)
                        parts.append(t)
                    lines.append("".join(parts))
            self._text = "\n".join(lines) + "\n"
        return self._text

    def get_fonts(self, *a, **k):
        return self._page.get_fonts(*a, **k)


class GidDoc:
    """fitz.Document stand-in whose pages decode glyph-id text (Sompo Japan)."""

    def __init__(self, doc):
        self._doc = doc
        self._pages = {}

    def __getitem__(self, idx):
        if idx not in self._pages:
            self._pages[idx] = GidPage(self._doc[idx])
        return self._pages[idx]

    def __iter__(self):
        return iter(self[i] for i in range(len(self._doc)))

    def __len__(self):
        return len(self._doc)


def open_company_pdf(comp):
    path = SAMPLES / comp.get("subdir", "") / comp["pdf"]
    doc = fitz.open(str(path))
    if comp.get("gid_decode"):
        if not GID_FONT.exists():
            print(f"WARN {comp['key']}: {GID_FONT} missing — glyph-id pages cannot be decoded on this machine")
        doc = GidDoc(doc)
    return doc, path


# --------------------------------------------------------------------------------------
class FixturePage:
    """Stand-in for a fitz Page backed by pre-captured get_text('text') output."""

    def __init__(self, text):
        self._text = text

    def get_text(self, kind="text"):
        return self._text


class FixtureDoc:
    """Stand-in for a fitz Document when the live PDF is absent — replays extraction against a
    JSON snapshot of {page_number: raw get_text('text')} captured while the PDF was on disk (see
    comp["profit_pdf_fixture"]). Only pages the fixture recorded are addressable."""

    def __init__(self, pages_by_number):
        self._pages = {int(k): FixturePage(v) for k, v in pages_by_number.items()}

    def __getitem__(self, idx):
        return self._pages[idx + 1]  # callers use doc[p - 1]

    def __iter__(self):
        return iter(self._pages[p] for p in sorted(self._pages))

    def __len__(self):
        return max(self._pages) if self._pages else 0


def page_lines(doc, pages):
    out = []
    for p in pages:
        for ln in doc[p - 1].get_text("text").splitlines():
            n = norm(ln)
            if n:
                out.append((p, n))
    return out


def grab(lines, start, label_res, skip_limit=6, stop=None):
    """First line >= start matching any regex -> (value_tokens, page, next_index) or None."""
    end = len(lines) if stop is None else stop
    for i in range(start, end):
        p, ln = lines[i]
        if any(re.search(r, ln) for r in label_res):
            j = i + 1
            skipped = 0
            while j < end and not is_val(lines[j][1]) and skipped < skip_limit:
                j += 1
                skipped += 1
            toks = []
            while j < end and is_val(lines[j][1]):
                toks.append(lines[j][1])
                j += 1
            return toks, p, j
    return None


def pick(toks, col):
    if not toks:
        return None
    if col == "ev":
        return to_val(toks[-1])
    if col == "first":
        return to_val(toks[0]) if len(toks) >= 4 else None
    if len(toks) >= 2:
        return to_val(toks[1])
    return to_val(toks[0])


def extract_esr(comp, doc):
    values, pages, raw = {}, {}, {}
    cursors = {}
    table_lines = {t: page_lines(doc, pg) for t, pg in comp["pages"].items()}
    for it in ITEMS:
        t = it["table"]
        lines = table_lines[t]
        start = cursors.get(t + "_prev", 0) if it.get("reuse") else cursors.get(t, 0)
        stop = None
        if it.get("stop_before"):
            stop = next((i for i in range(start, len(lines)) if re.search(it["stop_before"], lines[i][1])), None)
        res = grab(lines, start, it["labels"], stop=stop)
        if res is None:
            values[it["id"]], pages[it["id"]] = None, None
            raw[it["id"]] = "ROW_OMITTED" if it.get("optional") else "NOT_FOUND"
            continue
        toks, p, nxt = res
        values[it["id"]] = pick(toks, it.get("col", "cur"))
        pages[it["id"]] = p
        raw[it["id"]] = toks
        if not it.get("reuse"):
            cursors[t + "_prev"] = start
            cursors[t] = nxt

    lines = table_lines.get("T1_combined")
    if lines:
        res = grab(lines, 0, [r"^非保険事業に係る所要資本の額"])
        values["rc_non_insurance_business"] = pick(res[0], "cur") if res else None
        pages["rc_non_insurance_business"] = res[1] if res else None
        raw["rc_non_insurance_business"] = res[0] if res else "NOT_FOUND"
    else:
        values["rc_non_insurance_business"], pages["rc_non_insurance_business"], raw["rc_non_insurance_business"] = None, None, "NOT_IN_TEMPLATE"

    # derived: tier1 ratio (K-ICS 기본자본비율 상당)
    t1, rq = values.get("tier1_eligible"), values.get("required_capital")
    values["tier1_ratio_pct"] = round(t1 / rq * 100, 1) if t1 and rq else None
    pages["tier1_ratio_pct"], raw["tier1_ratio_pct"] = None, "DERIVED"

    hl5 = None
    if comp.get("headline_5yr_page"):
        for p, ln in page_lines(doc, [comp["headline_5yr_page"]]):
            m = re.match(r"^(\d{2,4}\.\d)%$", ln)
            if m:
                hl5 = float(m.group(1))  # last % token on the page = latest FY (columns run oldest -> newest)
    values["esr_pct_5yr_summary"] = hl5
    pages["esr_pct_5yr_summary"], raw["esr_pct_5yr_summary"] = comp.get("headline_5yr_page"), "REGEX"

    # sensitivity
    sens_lines = table_lines["T7"]
    split_idx = next((i for i, (_, ln) in enumerate(sens_lines) if "当期末の数値との差額" in ln), None)
    blocks = [("levels", sens_lines[:split_idx] if split_idx else sens_lines)]
    if split_idx:
        blocks.append(("diffs", sens_lines[split_idx:]))
    sens = {"scenarios": [s[0] for s in SENS_SCENARIOS], "levels": {}, "diffs": {}, "pages": comp["pages"]["T7"]}
    for bname, blines in blocks:
        cur = 0
        for rid, rre, _, _, _ in SENS_ROWS:
            res = grab(blines, cur, [rre])
            if res is None:
                sens[bname][rid] = None
                continue
            toks, p, nxt = res
            cur = nxt
            vals = [to_val(t) for t in toks[:8]]
            vals += [None] * (8 - len(vals))
            sens[bname][rid] = dict(zip(sens["scenarios"], vals))

    # method flags — searched only in the qualitative pages (T8) + sensitivity page (T7), so that T3 row labels
    # such as マネジメント・アクションの効果の額 do not masquerade as "applied"
    doc_text = norm("\n".join(pg.get_text("text") for pg in doc))
    qual_text = norm("\n".join(doc[p - 1].get_text("text") for p in sorted(set(comp["pages"]["T8"] + comp["pages"]["T7"]))))
    method = {}
    for mi in METHOD_ITEMS:
        found = None
        for lab in mi["labels"]:
            idx = qual_text.find(lab)
            if idx >= 0:
                found = qual_text[idx: idx + 80]
                break
        if mi["type"] == "tri":
            method[mi["id"]] = "unstated" if found is None else (False if ("該当ありません" in found or "該当なし" in found) else True)
        else:
            method[mi["id"]] = found is not None
    ima = method["internal_model_applied"]
    method["calc_method"] = "standard" if ima is False else ("standard_implied" if ima == "unstated" else "internal_model")
    m = re.search(r"(一般バケット|ミドルバケット|トップバケット)\s*((?:\d+\.\d+%\s*)+)", doc_text)
    tenors = re.findall(r"(\d+)年", doc_text[max(0, m.start() - 60): m.start()]) if m else []
    method["discount_bucket_jpy"] = m.group(1) if m else None
    method["discount_rates_jpy"] = dict(zip([t + "y" for t in tenors[-4:]], [float(x.rstrip("%")) for x in m.group(2).split()])) if m else None
    spread_label = next((ln for _, ln in table_lines["T3"] if ln.startswith("スプレッドリスク")), None)
    return dict(values=values, pages=pages, raw_tokens=raw, sensitivity=sens, method=method, spread_label=spread_label)


# --------------------------------------------------------------------------------------
def extract_axes(comp, doc):
    """layer article_axes — company-type specific sections outside the ESR tables."""
    v = {k: None for k in [a["id"] for a in AXES_ITEMS]}
    pg = {}
    doc_text = norm("\n".join(p.get_text("text") for p in doc))
    ap = comp["axes_pages"]

    # --- ESR placeholder / status ---
    locs = []
    for i, page in enumerate(doc):
        t = norm(page.get_text("text"))
        for phrase in ESR_PLACEHOLDER_PHRASES:
            if phrase in t:
                ctx_i = t.find(phrase)
                locs.append(dict(page=i + 1, phrase=phrase, context=t[max(0, ctx_i - 60): ctx_i + 20].replace("\n", " ")))
                break
    v["esr_placeholder_locations"] = locs
    v["esr_status"] = "not_yet" if locs and "esr" not in comp["layers"] else ("posted" if "esr" in comp["layers"] else "not_found")
    # FY2025 column is often a dash — ASCII "-" or full-width "ー"/"―" (第一生命 p7: 907.3％ 865.4％ 865.0％ 852.9％ ー) — capture it so FY2024 stays second-to-last
    m = re.search(r"旧基準\s*\n((?:[\d.]+%?\s*\n|[-ー―]\s*\n){1,5})", doc_text)
    if m:
        toks = [x for x in m.group(1).split() if x]
        # columns run oldest -> newest; FY2024 = second-to-last
        v["smr_old_basis_fy2024_pct"] = to_val(toks[-2]) if len(toks) >= 2 and is_num(toks[-2]) else None
    pg["esr_placeholder"] = [l["page"] for l in locs]

    # --- AIR / reinsurance ---
    if "アセット・インテンシブ" in doc_text or "資産集約型" in doc_text:
        v["air_used"] = "mentioned_esr_purpose" if re.search(r"(アセット・インテンシブ|資産集約型).{0,200}(ESR|ソルベンシー)", doc_text, re.S) else "mentioned"
    else:
        v["air_used"] = "not_mentioned"
    ev = []
    if "既契約の出再に伴う損益" in doc_text:
        ev.append("基礎利益 note: 既契約の出再に伴う損益を除外 (in-force block cession P&L excluded from core profit)")
    if "共同保険式再保険" in doc_text:
        ev.append("関連当事者取引 note: 共同保険式再保険・最低保証再保険 (coinsurance-type / guarantee reinsurance with group company)")
    v["air_evidence"] = "; ".join(ev) if ev else None

    if ap.get("reins") and comp.get("reins_style"):
        # big-3 forms (ticket 20260913T0330Z) — same two tables as au but different cell decorations.
        lines = page_lines(doc, ap["reins"])
        pg["reins"] = ap["reins"]
        txt = "\n".join(ln for _, ln in lines)
        st = comp["reins_style"]
        if st == "tmnf":
            # 2025年度 / 154社(－) / 61.7%(－)   |   格付区分 … 2025年度 / 99.3(－) / 99.3(－) / 0.7(－)   (BBB以上 is cumulative)
            m = re.search(r"2025年度\s*\n(\d+)社[^\n]*\n([\d.]+)%", txt)
            if m:
                v["reins_counterparties_n"], v["reins_top5_share_pct"] = int(m.group(1)), float(m.group(2))
            m = re.search(r"格付区分\s*\n.*?2025年度\s*\n([\d.]+)\([^\n]*\n([\d.]+)\([^\n]*\n([\d.]+)\(", txt, re.S)
            if m:
                v["reins_rating_a_or_above_pct"] = float(m.group(1))
                v["_reins_rating_buckets"] = {"S&P社 A格以上": float(m.group(1)), "その他(格付なし・不明・BB格以下)": float(m.group(3))}
                v["_reins_rating_note"] = f"S&P社 BBB格以上 column ({m.group(2)}) is cumulative (includes A格以上) — excluded from the bucket sum"
        elif st == "msi":
            # 2025年度 / 209 （0） / 40.0% （0.0%）   |   格付区分 A以上 … 2026年4月末 / 99.6%（0.0%） / 0.0%（0.0%） / 0.4%（0.0%） / 100.0%
            m = re.search(r"2025年度\s*\n(\d+)\s*\([^\n]*\n([\d.]+)%", txt)
            if m:
                v["reins_counterparties_n"], v["reins_top5_share_pct"] = int(m.group(1)), float(m.group(2))
            m = re.search(r"2026年4月末\s*\n([\d.]+)%[^\n]*\n([\d.]+)%[^\n]*\n([\d.]+)%", txt)
            if m:
                v["reins_rating_a_or_above_pct"] = float(m.group(1))
                v["_reins_rating_buckets"] = {"A以上": float(m.group(1)), "BBB以上A未満": float(m.group(2)), "その他": float(m.group(3)), }
                v["_reins_rating_note"] = "rating table dated 2026年4月末 (as of 2026-04-30), counterparties/top5 are 2025年度"
        elif st == "sompo":
            # 出再先保険会社の数 / 100 / 102 (2024, 2025)  …  出再先に集中している割合(%) / 48.6 / 47.5   |   格付区分 A以上 98.3 98.9 / BBB格 1.7 1.1 / その他 0.0 0.0
            m = re.search(r"出再先保険会社の数\s*\n(\d+)\s*\n(\d+)\s*\n", txt)
            if m:
                v["reins_counterparties_n"] = int(m.group(2))
            m = re.search(r"集中している割合[^\n]*\n([\d.]+)\s*\n([\d.]+)\s*\n", txt)
            if m:
                v["reins_top5_share_pct"] = float(m.group(2))
            m = re.search(r"A以上\s*\n([\d.]+)\s*\n([\d.]+)\s*\n.*?BBB格\s*\n([\d.]+)\s*\n([\d.]+)\s*\n.*?その他[^\n]*\n([\d.]+)\s*\n([\d.]+)\s*\n", txt, re.S)
            if m:
                v["reins_rating_a_or_above_pct"] = float(m.group(2))
                v["_reins_rating_buckets"] = {"A以上": float(m.group(2)), "BBB格": float(m.group(4)), "その他": float(m.group(6))}
    elif ap.get("reins"):
        lines = page_lines(doc, ap["reins"])
        pg["reins"] = ap["reins"]
        if comp["sector"] == "nonlife":
            # au form: (10) 出再先保険会社の数 / 上位5社 ... 2025年度 5社 100.0%
            txt = "\n".join(ln for _, ln in lines)
            m = re.search(r"2025年度\s*\n(\d+)社\s*\n([\d.]+)%", txt)
            if m:
                v["reins_counterparties_n"], v["reins_top5_share_pct"] = int(m.group(1)), float(m.group(2))
            # (11) 格付区分 A以上 BBB以上 その他 合計 ... 2025年度 80.0% ー% 20.0% 100.0%
            m = re.search(r"格付区分\s*\n(.+?)合計\s*\n", txt, re.S)
            if m:
                buckets = [b for b in m.group(1).split("\n") if b and not b.startswith("(")]
                m2 = re.search(r"2025年度\s*\n((?:[\d.]+%|ー%|-%)\s*\n?){" + str(len(buckets) + 1) + ",}", txt)
                if m2:
                    toks = re.findall(r"([\d.]+%|ー%|-%)", m2.group(0))
                    share = dict(zip(buckets, [to_val(t) for t in toks]))
                    v["reins_rating_a_or_above_pct"] = sum((share.get(b) or 0) for b in buckets if b.startswith("A"))
                    v["_reins_rating_buckets"] = share
        else:
            # life form: (4) 主要な保険会社等の数 / (5) 上位5社 / (6) 格付区分 / (7) 未収再保険金
            res = grab(lines, 0, [r"再保険を引き受けた主要な保険会社等の数"])
            v["reins_counterparties_n"] = pick(res[0], "cur") if res else None
            res = grab(lines, 0, [r"上位5社に対する支払"])
            v["reins_top5_share_pct"] = pick(res[0], "cur") if res else None
            i0 = next((i for i, (_, ln) in enumerate(lines) if ln.startswith("格付区分")), None)
            if i0 is not None:
                share = {}
                j = i0 + 1
                while j < len(lines) and not lines[j][1].startswith("(注"):
                    ln = lines[j][1]
                    if re.match(r"^(AAA|AA|A|BBB|BB|B)[+-]?$|^A以上$|^BBB以上$|^その他$", ln):
                        res = grab(lines, j, [re.escape(ln) + "$"])
                        if res:
                            share[ln] = pick(res[0], "cur")
                            j = res[2]
                            continue
                    j += 1
                v["_reins_rating_buckets"] = share
                v["reins_rating_a_or_above_pct"] = round(sum((x or 0) for k, x in share.items() if k.startswith("A")), 1)
            res = grab(lines, 0, [r"未だ収受していない再保険金の金額"])
            v["reins_unreceived_claims"] = pick(res[0], "cur") if res else None

    # --- nonlife: 異常危険準備金 (責任準備金の内訳 table, 2025年度) ---
    if comp["sector"] == "nonlife" and ap.get("reserves") and comp["key"] in RESERVE_SPEC:
        lines = merge_vertical(page_lines(doc, ap["reserves"]))
        pg["reserves"] = ap["reserves"]
        spec = RESERVE_SPEC[comp["key"]]
        i0 = next((i for i, (_, ln) in enumerate(lines) if re.search(spec["heading"], ln)), None)
        if i0 is not None and spec.get("year_marker"):
            i0 = next((i for i in range(i0, len(lines)) if re.search(spec["year_marker"], lines[i][1])), i0)
        if i0 is not None:
            by_line, cur = {}, i0 + 1
            num_re = re.compile(r"[△▲]?\d{1,3}(?:,\d{3})+|[△▲]?\d+|[-－ー−]")  # norm() NFKC turns "－" into "-"
            for k, lob in enumerate(RESERVE_LOBS):
                j = next((i for i in range(cur, len(lines)) if lines[i][1] == lob or lines[i][1].startswith(lob + " ")), None)
                if j is None:
                    continue
                nxt = next((i for i in range(j + 1, len(lines)) if any(lines[i][1] == l2 or lines[i][1].startswith(l2 + " ") for l2 in RESERVE_LOBS[k + 1:] + ["(うち賠償責任)", "うち賠償責任"])
                            or lines[i][1].startswith("(注") or lines[i][1].startswith("注")), min(len(lines), j + 20))
                blob = " ".join([lines[j][1][len(lob):]] + [ln for _, ln in lines[j + 1:nxt]])
                toks = [t for t in num_re.findall(blob)]
                if len(toks) >= 12:
                    toks = toks[6:12]     # FY2024 | FY2025 side by side → keep the FY2025 half (row order, from the row start)
                elif len(toks) < 6:
                    continue
                by_line[lob] = dict(ordinary=to_val(toks[0]), catastrophe=to_val(toks[1]), total=to_val(toks[5]), raw=toks[:6])
                cur = nxt
            if by_line:
                v["cat_reserve_by_line"] = {k2: x["catastrophe"] for k2, x in by_line.items() if k2 != "合計"}
                v["cat_reserve_total"] = by_line.get("合計", {}).get("catastrophe")
                v["cat_reserve_fire"] = by_line.get("火災", {}).get("catastrophe")
                v["ordinary_reserve_total"] = by_line.get("合計", {}).get("ordinary")
                v["_reserve_rows_raw"] = {k2: x["raw"] for k2, x in by_line.items()}
                v["_reserve_total_all"] = by_line.get("合計", {}).get("total")
        m = re.search(r"異常危険準備金[^\n]{0,60}(不足|積立率)[^\n]{0,60}|積立不足[^\n]{0,80}", doc_text)
        v["cat_reserve_adequacy_note"] = m.group(0) if m else None
    elif comp["sector"] == "nonlife" and ap.get("reserves"):
        lines = page_lines(doc, ap["reserves"])
        pg["reserves"] = ap["reserves"]
        i0 = next((i for i, (_, ln) in enumerate(lines) if "責任準備金の内訳" in ln and "2025年度" in ln), None)
        if i0 is not None:
            by_line, cur = {}, i0
            for lob in ["火災", "海上", "傷害", "自動車", "自動車損害賠償責任", "その他", "合計"]:
                res = grab(lines, cur, [r"^" + lob + r"$"])
                if res:
                    toks, _, cur = res
                    # columns: 普通責任準備金 / 異常危険準備金 / 危険準備金 / 払戻積立金 / 契約者配当準備金等 / 合計
                    by_line[lob] = dict(ordinary=to_val(toks[0]) if len(toks) > 0 else None, catastrophe=to_val(toks[1]) if len(toks) > 1 else None)
            v["cat_reserve_by_line"] = {k: x["catastrophe"] for k, x in by_line.items() if k != "合計"}
            v["cat_reserve_total"] = by_line.get("合計", {}).get("catastrophe")
            v["cat_reserve_fire"] = by_line.get("火災", {}).get("catastrophe")
            v["ordinary_reserve_total"] = by_line.get("合計", {}).get("ordinary")
        # only an explicit statement about 異常危険準備金 counts; 責任準備金積立水準 '積立率 100%' is the policy reserve, not this
        m = re.search(r"異常危険準備金[^\n]{0,60}(不足|積立率)[^\n]{0,60}|積立不足[^\n]{0,80}", doc_text)
        v["cat_reserve_adequacy_note"] = m.group(0) if m else None
    elif comp["sector"] == "nonlife":
        v["cat_reserve_adequacy_note"] = "NOT_IN_SAMPLE_DOC (別冊 業績データ has no 責任準備金の内訳 table — main disclosure volume needed)"

    # --- life: 基礎利益 / 逆ざや ---
    if comp["sector"] == "life":
        if ap.get("core_profit"):
            lines = page_lines(doc, ap["core_profit"])
            pg["core_profit"] = ap["core_profit"]
            res = grab(lines, 0, [r"^基礎利益$"])
            if res:
                v["core_profit_prev"], v["core_profit"] = to_val(res[0][0]), to_val(res[0][1])
            res = grab(lines, 0, [r"^既契約の出再に伴う損益に相当する額$"])
            v["inforce_cession_pl"] = pick(res[0], "cur") if res else None
        if ap.get("soundness"):
            lines = page_lines(doc, ap["soundness"])
            pg["soundness"] = ap["soundness"]
            res = grab(lines, 0, [r"^逆ざや$"])
            if res and len(res[0]) >= 2:
                v["negative_spread_prev_100m"], v["negative_spread_100m"] = to_val(res[0][0]), to_val(res[0][1])
        v["three_source_disclosed"] = bool(re.search(r"利差損益|危険差損益|費差損益", doc_text))
        if v["three_source_disclosed"]:
            v["interest_margin_sign"] = "see interest_margin"
        elif v["negative_spread_100m"] is not None:
            v["interest_margin_sign"] = "negative" if v["negative_spread_100m"] > 0 else "positive"
        elif "順ざや" in doc_text:
            v["interest_margin_sign"] = "positive"
        else:
            v["interest_margin_sign"] = "unstated"
    return dict(values=v, pages=pg)


# --------------------------------------------------------------------------------------
def merge_vertical(lines):
    """au 5개년 표는 행 라벨이 세로쓰기(한 글자 한 줄)로 추출된다 → 연속 1글자 줄을 하나로 합친다."""
    out, buf, bufp = [], [], None
    for p, ln in lines:
        if len(ln) == 1 and not is_val(ln) and not ln.isdigit():
            buf.append(ln)
            bufp = p
            continue
        if buf:
            out.append((bufp, "".join(buf)))
            buf = []
        out.append((p, ln))
    if buf:
        out.append((bufp, "".join(buf)))
    return out


def pl_flat_tokens(lines, start_rx, end_rx):
    """All value tokens between the first line matching start_rx and the first line matching
    end_rx after it (labels dropped regardless of how they render — see MEIJI_PL_FLAT_MAP)."""
    start_i = next((i for i, (_, ln) in enumerate(lines) if re.search(start_rx, ln)), None)
    if start_i is None:
        return None
    end_i = next((i for i, (_, ln) in enumerate(lines) if i > start_i and re.search(end_rx, ln)), len(lines))
    return [ln for _, ln in lines[start_i:end_i] if is_val(ln)]


def _bridge_row_value(lines, heading_idx):
    """From a 保険引受の状況 bridge sub-table heading line, find its own 合計 row and read (prev, cur)
    amounts (百万円). Two row shapes are in the sample: 9-token 金額/構成比/増減率 × 3年 (au premium
    tables) and 6-token 金額/構成比 × 3年 (au claim tables + every Meiji table, growth-rate column
    absent). N/A tables (au 受再正味保険料/保険金 when au writes no assumed business) print
    「該当事項はありません」 instead of a 合計 row — read as 0, not missing."""
    for j in range(heading_idx + 1, min(len(lines), heading_idx + 12)):
        if "該当事項はありません" in lines[j][1]:
            return 0, 0, lines[j][0], "N/A (該当事項はありません)"
    # no `stop` here: grab()'s capture loop is itself bounded by `stop`, so a tight bound aimed at
    # just reaching the 合計 label leaves no room to read the values that follow it.
    res = grab(lines, heading_idx + 1, [r"^合計$"])
    if res is None:
        return None, None, None, "NOT_FOUND"
    toks, p, _ = res
    n = len(toks)
    if n >= 9:
        return to_val(toks[3]), to_val(toks[6]), p, toks
    if n >= 6:
        return to_val(toks[2]), to_val(toks[4]), p, toks
    if n >= 3:
        return to_val(toks[1]), to_val(toks[2]), p, toks
    return None, None, p, toks


def extract_bridge_block(comp, tl, profit_items_by_id):
    """layer profit, table profit:bridge — 元受/受再/出再 재보험 다리. Sub-table document order
    differs per company (BRIDGE_ORDER), so items are walked in that order sharing one cursor —
    a plain per-item label search would otherwise land on a footnote reusing the same phrase
    (e.g. au's 従業員1人当たり元受正味保険料) instead of the table's own heading."""
    out = {}
    lines = tl.get("bridge")
    order = BRIDGE_ORDER.get(comp["key"])
    if lines is None or not order:
        return out
    cur = 0
    for iid in order:
        it = profit_items_by_id[iid]
        h = next((i for i in range(cur, len(lines)) if any(re.search(r, lines[i][1]) for r in it["labels"])), None)
        if h is None:
            out[iid] = (None, None, None, "NOT_FOUND")
            continue
        out[iid] = _bridge_row_value(lines, h)
        nxt = next((i for i in range(h + 1, min(len(lines), h + 200))
                    if lines[i][1] == "合計" or "該当事項はありません" in lines[i][1]), None)
        cur = (nxt + 1) if nxt is not None else h + 1
    return out


def _amount_tokens(toks):
    """Amount columns of a 保険引受の状況 合計 row: integers (百万円) — 構成比/増減率/損害率 columns
    always carry a decimal point, dashes are dropped."""
    return [t for t in toks if "." not in t and not is_dash(t)]


def extract_bridge_spec(comp, tl):
    """profit:bridge for companies in BRIDGE_SPEC (big-3): headings differ per company and Tokio
    Marine pairs two items in one table (受再/支払, 受再/回収 → amounts [a1,b1,a2,b2,a3,b3])."""
    out = {}
    lines = tl.get("bridge")
    spec = BRIDGE_SPEC.get(comp["key"])
    if lines is None or not spec:
        return out
    cur = 0
    for heading_rx, ids in spec:
        h = next((i for i in range(cur, len(lines)) if re.search(heading_rx, lines[i][1])), None)
        if h is None:
            for iid in (ids if isinstance(ids, tuple) else (ids,)):
                out[iid] = (None, None, None, "NOT_FOUND heading " + heading_rx)
            continue
        res = grab(lines, h + 1, [r"^合計$"])
        if res is None:
            for iid in (ids if isinstance(ids, tuple) else (ids,)):
                out[iid] = (None, None, None, "NOT_FOUND 合計 after " + heading_rx)
            cur = h + 1
            continue
        toks, p, nxt = res
        amts = _amount_tokens(toks)
        if isinstance(ids, tuple):
            if len(amts) >= 6:
                a, b = amts[-6:], None
                out[ids[0]] = (to_val(a[2]), to_val(a[4]), p, toks)
                out[ids[1]] = (to_val(a[3]), to_val(a[5]), p, toks)
            else:
                out[ids[0]] = out[ids[1]] = (None, None, p, toks)
        else:
            if len(amts) >= 2:
                out[ids] = (to_val(amts[-2]), to_val(amts[-1]), p, toks)
            else:
                out[ids] = (None, None, p, toks)
        cur = nxt
    return out


def unwrap_paren_lines(lines):
    """MSI 損益計算書 prints sub-items as "(1,679,248)" / "(－)" / "(△24,594)" and one broken "(64,842" →
    strip the parens so is_val()/grab() see plain value tokens. Double parens "((4,312))" are left alone."""
    out = []
    for p, ln in lines:
        m = re.match(r"^\(([△▲]?[\d,]+(?:\.\d+)?%?)\)?$", ln) or re.match(r"^\(([-－ー−])\)$", ln)
        out.append((p, m.group(1)) if m else (p, ln))
    return out


def pick_pc(toks, layout):
    """(prev, cur) from a row's value tokens.
    prev_cur_diff     : 前年度 / 当年度 / 比較増減                     (au 損益計算書)
    prev_pct_cur_pct  : 前年度 金額 / 百分比 / 当年度 金額 / 百分比 — 소계행만 4토큰, 내역행은 2토큰 (NN 損益計算書)
    three_years       : 2023 / 2024 / 2025                             (au 明細表·比率表)
    three_years_x3    : (損益·平均運用額·利回り) × 3개년 = 9토큰       (au 資産運用利回り 합계행)
    ratio_x3          : (損害率·事業費率·合算率) × 3개년 = 9토큰       (au 比率표 합계행) → returns the last-3 / prev-3 triples
    five_years        : 2021..2025                                     (au 主要な経営指標)"""
    n = len(toks)
    if layout == "prev_cur_diff" and n >= 2:
        return to_val(toks[0]), to_val(toks[1])
    if layout == "prev_pct_cur_pct":
        if n >= 4:
            return to_val(toks[0]), to_val(toks[2])
        if n >= 2:
            return to_val(toks[0]), to_val(toks[1])
    if layout == "three_years" and n >= 3:
        return to_val(toks[1]), to_val(toks[2])
    if layout == "three_years_x3" and n >= 9:
        return to_val(toks[3]), to_val(toks[6])
    if layout == "five_years" and n >= 2:
        return to_val(toks[-2]), to_val(toks[-1])
    return None, None


def extract_profit(comp, doc):
    """layer profit — 損益計算書 / 保険引受利益明細表 / 比率표 / 資産運用利回り / 基礎利益(三利源) + accounting-basis meta."""
    ids = [it["id"] for it in PROFIT_ITEMS]
    v, pg, raw = {i: None for i in ids}, {}, {}
    meta = dict(accounting_basis="unstated", ifrs17_applied="unstated", accounting_basis_evidence=None, profit_source_doc=None)
    pp = comp.get("profit_pages")
    if not pp:
        for i in ids:
            raw[i] = "NOT_ACQUIRED"
        meta["profit_source_doc"] = comp.get("profit_not_acquired") or "NOT_ACQUIRED"
        meta["profit_main_volume_url"] = comp.get("profit_main_volume_url")
        # accounting basis from the 別冊 alone: EBS 財務会計ベース column carries 価格変動準備金 / 危険準備金 (保険業法 reserves) but the
        # 회계방침 절 is in the main volume → stays unstated (no estimation).
        meta["accounting_basis_evidence"] = "別冊 has no 会計方針 section (EBS 財務会計ベース column shows 価格変動準備金·危険準備金等 — consistent with jgaap, unconfirmed)"
        return dict(values=v, pages=pg, raw_tokens=raw, meta=meta, summary5=None)
    meta["profit_source_doc"] = comp.get("profit_pdf") or comp["pdf"]
    if comp.get("profit_pdf_used_fixture"):
        meta["profit_source_doc"] += " (read via profit_pdf_fixture — live PDF absent this run, see COMPANIES comment)"
    layout = comp["pl_layout"]
    tl = {k: page_lines(doc, pages) for k, pages in pp.items()}
    if comp.get("unwrap_parens"):
        tl = {k: unwrap_paren_lines(ls) for k, ls in tl.items()}
    if comp.get("vertical_labels"):
        # Meiji Yasuda main volume renders 保険引受利益明細表/比率표 row labels one glyph per line
        # (unlike au/NN's horizontal labels) — merge them so grab()'s regex can anchor on them.
        # "pl" and "summary5" are handled separately below (pl via pl_flat_tokens; summary5 already
        # merge_vertical'd further down) so they are left untouched here — unless vertical_pl (MSI:
        # the P&L itself is glyph-per-line but row-wise, so merging is exactly what grab() needs).
        keep = ("summary5",) if comp.get("vertical_pl") else ("pl", "summary5")
        tl = {k: (merge_vertical(ls) if k not in keep else ls) for k, ls in tl.items()}
    pl_flat = None
    if layout == "label_block_3yr":
        pl_flat = pl_flat_tokens(tl["pl"], *comp["pl_flat_bounds"])
        if pl_flat is not None and comp.get("pl_flat_len") and len(pl_flat) != comp["pl_flat_len"]:
            pl_flat = None  # layout drifted from the verified page — don't trust positional offsets
    profit_items_by_id = {it["id"]: it for it in PROFIT_ITEMS}
    bridge_vals = extract_bridge_spec(comp, tl) if comp["key"] in BRIDGE_SPEC else extract_bridge_block(comp, tl, profit_items_by_id)
    cursors = {}
    for it in PROFIT_ITEMS:
        if it["scope"] not in ("both", comp["sector"]):
            raw[it["id"]] = "N/A_SECTOR"
            continue
        src = it["src"]
        if src == "bridge":
            res = bridge_vals.get(it["id"])
            if res is None or (res[0] is None and res[1] is None):
                raw[it["id"]] = res[3] if res else "NOT_FOUND"
                continue
            prevv, curv, p, tok = res
            v[it["id"]] = dict(prev=prevv, cur=curv)
            pg[it["id"]], raw[it["id"]] = p, tok
            continue
        if src == "pl" and layout == "label_block_3yr":
            idxs = comp["pl_flat_map"].get(it["id"])
            if pl_flat is None or idxs is None:
                raw[it["id"]] = "NOT_FOUND"
                continue
            i23, i24, i25 = idxs
            v[it["id"]] = dict(prev=to_val(pl_flat[i24]), cur=to_val(pl_flat[i25]))
            pg[it["id"]] = pp["pl"][0]
            raw[it["id"]] = [pl_flat[i23], pl_flat[i24], pl_flat[i25]]
            continue
        if src == "note":
            found = None
            for pno in range(len(doc)):
                # au prints a backspace control char between label and amount -- strip controls before matching
                txt = norm(" ".join(re.sub(r"[\x00-\x1f]", " ", doc[pno].get_text("text")).split()))
                for lab in it["labels"]:
                    m = re.search(lab + r"[\s　]*(△?)\s*([\d,]+)\s*百万円", txt)
                    if m:
                        found = (pno + 1, m.group(0), (-1 if m.group(1) else 1) * int(m.group(2).replace(",", "")))
                        break
                if found:
                    break
            if found is None:
                raw[it["id"]] = "NOT_FOUND"
                continue
            v[it["id"]] = dict(prev=None, cur=found[2])
            pg[it["id"]], raw[it["id"]] = found[0], found[1]
            continue
        lines = tl.get(src)
        if lines is None:
            raw[it["id"]] = "NO_PAGE"
            continue
        start = cursors.get(src, 0)
        if src == "ratio":
            # heading varies (au "(6)正味損害率…" / Meiji "6. 正味損害率…") → match on the two labels together
            h = next((i for i, (_, ln) in enumerate(lines) if "正味損害率" in ln and "正味事業費率" in ln), 0)
            res = grab(lines, h, [r"^合計$"])
            if res and len(res[0]) >= 9:
                k = {"pl_loss_ratio_pct": 0, "pl_expense_ratio_pct": 1, "pl_combined_ratio_pct": 2}[it["id"]]
                v[it["id"]] = dict(prev=to_val(res[0][3 + k]), cur=to_val(res[0][6 + k]))
                pg[it["id"]], raw[it["id"]] = res[1], res[0]
            else:
                raw[it["id"]] = "NOT_FOUND"
            continue
        if src == "inv":
            h = next((i for i, (_, ln) in enumerate(lines) if ln.startswith("(3)資産運用利回り")), 0)
            res = grab(lines, h, [r"^合計$"])
            lay = "three_years_x3"
        else:
            # per-company label alias (schema's canonical `labels` stays untouched) — e.g. Meiji
            # Yasuda's 保険引受利益明細表 prints the underwriting-share G&A row as the bare label
            # "営業費及び一般管理費" (the fuller "保険引受に係る…" phrase only appears in a footnote).
            labels = comp.get("label_overrides", {}).get(it["id"], it["labels"])
            res = grab(lines, start, labels)
            lay = layout if src == "pl" else ("three_years" if src == "uw" else "prev_cur_diff")
        if res is None:
            raw[it["id"]] = "NOT_FOUND" if src != "three" else "TABLE_ABSENT"
            continue
        toks, p, nxt = res
        prev, cur = pick_pc(toks, lay)
        v[it["id"]] = dict(prev=prev, cur=cur)
        pg[it["id"]], raw[it["id"]] = p, toks
        if src == "uw":  # 明細表 rows are in form order; P&L labels are anchored (^…$) and unique, so no cursor there
            cursors[src] = nxt
    if comp.get("pl_investment_override") == "pl_stmt" and pl_flat is not None:
        # 資産運用利回り(実現利回り)합계행의 분자는 資産運用収益+積立保険料等運用益-資産運用費用인데, 積立保険料等運用益은
        # 이미 保険引受収益(→保険引受利益) 안에 들어 있어 그대로 pl_investment_pl 로 쓰면 P07 이 이중계상으로 깨진다
        # (Meiji Yasuda 2026-09-12 발견, ±15 어긋남). 損益計算書의 資産運用収益-資産運用費用 으로 대체한다.
        ir, ie = comp["pl_flat_map"]["_inv_rev"], comp["pl_flat_map"]["_inv_exp"]
        prev = z(to_val(pl_flat[ir[1]])) - z(to_val(pl_flat[ie[1]]))
        cur = z(to_val(pl_flat[ir[2]])) - z(to_val(pl_flat[ie[2]]))
        v["pl_investment_pl"] = dict(prev=prev, cur=cur)
        pg["pl_investment_pl"] = pp["pl"][0]
        raw["pl_investment_pl"] = "override=pl_stmt: 資産運用収益-資産運用費用 (not the yield-table 合計, which double-counts 積立保険料等運用益 already inside 保険引受収益 for this company)"
    elif comp.get("pl_investment_override") == "pl_stmt" and tl.get("pl") is not None:
        # same rule for label-anchored P&Ls (big-3): 資産運用収益 / 資産運用費用 rows of the 損益計算書.
        r1 = grab(tl["pl"], 0, [r"^資産運用収益$"])
        r2 = grab(tl["pl"], 0, [r"^資産運用費用$"])
        if r1 and r2:
            rp, rc = pick_pc(r1[0], layout)
            ep, ec = pick_pc(r2[0], layout)
            v["pl_investment_pl"] = dict(prev=z(rp) - z(ep), cur=z(rc) - z(ec))
            pg["pl_investment_pl"] = pp["pl"][0]
            raw["pl_investment_pl"] = f"override=pl_stmt: 資産運用収益{r1[0]} - 資産運用費用{r2[0]} (yield-table 合計 double-counts 積立保険料等運用益 inside 保険引受収益)"
    adjustments = {}
    if comp.get("bridge_gross_incl_deposit") and tl.get("pl") is not None:
        # 元受正味保険料 table is "(含む収入積立保険料)" only → the bridge identity needs the deposit premium
        # (収入積立保険料, a 損益計算書 row inside 保険引受収益) taken back out. Stored as disclosed; P14 subtracts it.
        r3 = grab(tl["pl"], 0, [r"^収入積立保険料$"])
        if r3:
            dp, dc = pick_pc(r3[0], layout)
            adjustments["deposit_premium_in_gross"] = dict(prev=dp, cur=dc, source="損益計算書 収入積立保険料",
                                                           note="pl_gross_premiums_written includes 収入積立保険料 (table heading 含む収入積立保険料); P14 = gross + assumed - ceded - this")
    # 5개년 主要な経営指標 표 (au) — cross-check source for P10
    s5 = None
    if pp.get("summary5") and not comp.get("summary5_skip_p10"):
        ml = merge_vertical(tl["summary5"])
        s5 = {}
        for sid, rx in [("pl_net_premiums_written", r"^正味収入保険料$"), ("pl_ordinary_revenue", r"^経常収益$"), ("pl_ordinary_profit", r"^経常利益$"),
                        ("pl_underwriting_profit", r"^保険引受利益$"), ("pl_net_income", r"^当期純利益$"), ("pl_loss_ratio_pct", r"^正味損害率$"),
                        ("pl_expense_ratio_pct", r"^正味事業費率$"), ("pl_interest_dividend_income", r"^利息及び配当金収入$")]:
            res = grab(ml, 0, [rx])
            if res:
                prev, cur = pick_pc(res[0], "five_years")
                s5[sid] = dict(prev=prev, cur=cur)
    # --- accounting basis (evidence sentences only; no inference beyond the two documented tiers) ---
    basis_text = norm("\n".join(doc[p - 1].get_text("text") for p in pp.get("basis", []))).replace("\n", " ")
    doc_text = norm("\n".join(p.get_text("text") for p in doc)).replace("\n", " ")
    # Vertical-rendered labels (Meiji main volume) turn into "責 任 準 備 金 …" once "\n" -> " " above,
    # which breaks every substring check below — match against a space-stripped copy instead (CJK
    # phrases carry no real spaces, so this only ever ADDS matches, never removes one that already
    # worked for au/NN's horizontally-rendered text).
    basis_ns = basis_text.replace(" ", "")
    doc_ns = doc_text.replace(" ", "")
    ev = []

    def ctx(txt, ph, w=70):
        i = txt.find(ph)
        return None if i < 0 else re.sub(r"\s+", " ", txt[max(0, i - w): i + len(ph) + w])

    # IFRS test is scoped to the basis pages (単体 statements): the big-3 main volumes also carry the
    # group's CONSOLIDATED IFRS statements further back, which must not relabel the solo P&L.
    ifrs_scope = basis_ns if comp.get("ifrs_scope_basis_pages", comp["key"] in BRIDGE_SPEC) else doc_ns
    ifrs_hit = next((ph for ph in ["国際財務報告基準", "IFRS"] if ph in ifrs_scope), None)
    tier_a = next((ph for ph in ["標準責任準備金", "大蔵省告示第48号", "企業会計基準"] if ph in basis_ns), None)
    tier_b_pl = "責任準備金繰入額" in basis_ns or "責任準備金戻入額" in basis_ns
    tier_b_audit = ("会社法第436条" in basis_ns or "保険業法第111条" in basis_ns)
    if ifrs_hit and ("作成基準" in ifrs_scope or "連結財務諸表" in ifrs_scope):
        meta["accounting_basis"] = "ifrs"
        ev.append(f"IFRS: {ctx(doc_ns, ifrs_hit)}")
    elif tier_a:
        meta["accounting_basis"] = "jgaap"
        ev.append(f"A(会計方針 p{pp['basis']}): {ctx(basis_ns, tier_a)}")
    elif tier_b_pl and tier_b_audit:
        meta["accounting_basis"] = "jgaap"
        ev.append(f"B(法定P&L 様式 p{pp['basis']}): {ctx(basis_ns, '責任準備金繰入額' if '責任準備金繰入額' in basis_ns else '責任準備金戻入額', 40)}")
        ev.append(f"B(監査 文구): {ctx(basis_ns, '会社法第436条' if '会社法第436条' in basis_ns else '保険業法第111条')}")
    ifrs17_scope = basis_text if ifrs_scope is basis_ns else doc_text
    if any(ph in ifrs17_scope for ph in ["IFRS第17号", "IFRS 17", "保険契約に関する国際財務報告基準"]):
        meta["ifrs17_applied"] = True
    elif meta["accounting_basis"] == "jgaap":
        meta["ifrs17_applied"] = False  # 単体 statutory accounts under 保険業法/会社計算規則 are J-GAAP by law; IFRS is a consolidated-only option
        if ifrs_scope is basis_ns and any(ph in doc_ns for ph in ["IFRS第17号", "国際財務報告基準"]):
            ev.append("ifrs17_applied=false for the 単体 statements (basis pages have no IFRS mention); the same volume's 連結 section is IFRS/IFRS17 at group level — not this layer")
        else:
            ev.append("ifrs17_applied=false: derived from accounting_basis=jgaap on 単体 statutory statements (no IFRS/IFRS17 mention in the document)")
    meta["accounting_basis_evidence"] = " | ".join(ev) if ev else None
    return dict(values=v, pages=pg, raw_tokens=raw, meta=meta, summary5=s5, adjustments=adjustments)


def run_profit_checks(comp, pf):
    """P01..P12 — 손익 층 검산. 금액 百万円 절사(항 수만큼 ±1), 비율 소수1자리 반올림(±0.15)."""
    checks = []
    if not comp.get("profit_pages"):
        checks.append(dict(id="P00_not_acquired", formula="profit tables acquired", lhs=None, rhs=None, tol="", **{"pass": True}, gate=False,
                           note=pf["meta"]["profit_source_doc"]))
        return checks
    v = pf["values"]

    def g(i, col):
        x = v.get(i)
        return None if not x else x.get(col)

    def add(cid, formula, lhs, rhs, tol, note="", gate=True):
        ok = lhs is not None and rhs is not None and abs(lhs - rhs) <= tol
        checks.append(dict(id=cid, formula=formula, lhs=lhs, rhs=None if rhs is None else round(rhs, 2), tol=tol, **{"pass": ok}, gate=gate, note=note))

    for col in ("cur", "prev"):
        sfx = "" if col == "cur" else "_prev"
        add(f"P03_ordinary{sfx}", "pl_ordinary_profit = pl_ordinary_revenue - pl_ordinary_expenses", g("pl_ordinary_profit", col), z(g("pl_ordinary_revenue", col)) - z(g("pl_ordinary_expenses", col)), 1)
        add(f"P04_pretax{sfx}", "pl_pretax_profit = pl_ordinary_profit + pl_extraordinary_gains - pl_extraordinary_losses - 契約者配当準備金繰入額(생보, 없으면 0)", g("pl_pretax_profit", col),
            z(g("pl_ordinary_profit", col)) + z(g("pl_extraordinary_gains", col)) - z(g("pl_extraordinary_losses", col)) - z(g("pl_policyholder_dividend_provision", col)), 1)
        add(f"P05_net_income{sfx}", "pl_net_income = pl_pretax_profit - pl_income_taxes", g("pl_net_income", col), z(g("pl_pretax_profit", col)) - z(g("pl_income_taxes", col)), 1)
        if comp["sector"] == "life":
            add(f"P01_core_bridge{sfx}", "pl_ordinary_profit = pl_core_profit + pl_capital_gains + pl_extraordinary_pl", g("pl_ordinary_profit", col),
                z(g("pl_core_profit", col)) + z(g("pl_capital_gains", col)) + z(g("pl_extraordinary_pl", col)), 2)
            three = [g("pl_interest_margin", col), g("pl_mortality_margin", col), g("pl_expense_margin", col)]
            if any(x is not None for x in three):
                add(f"P02_three_sources{sfx}", "pl_core_profit ≈ 利差 + 危険差 + 費差 (company definitions differ — informational)", g("pl_core_profit", col), sum(z(x) for x in three), 5, gate=False)
            else:
                checks.append(dict(id=f"P02_three_sources{sfx}", formula="三利源 table present", lhs=None, rhs=None, tol="", **{"pass": True}, gate=False, note="TABLE_ABSENT — 三利源 not disclosed (NN Life prints キャピタル/臨時 split only)"))
        else:
            add(f"P06_combined{sfx}", "pl_combined_ratio_pct = pl_loss_ratio_pct + pl_expense_ratio_pct (±0.15, each rounded to 0.1)", g("pl_combined_ratio_pct", col),
                z(g("pl_loss_ratio_pct", col)) + z(g("pl_expense_ratio_pct", col)), 0.15)
            # その他収支 (自賠責 法人税相当額 etc.) sits inside 保険引受利益 but NOT in the P&L's 経常利益 → back it
            # out (au: null, Meiji: -1/-2 — invisible under tol 3; Tokio Marine: -3,152 — visible, exact once removed).
            other = z(g("pl_other_ordinary_revenue", col)) - z(g("pl_other_ordinary_expenses", col)) - (z(g("pl_operating_general_admin", col)) - z(g("pl_uw_operating_general_admin", col))) - z(g("pl_underwriting_other", col))
            add(f"P07_ordinary_bridge{sfx}", "pl_ordinary_profit = pl_underwriting_profit − その他収支 + pl_investment_pl + (その他経常収益 − その他経常費用 − (営業費及び一般管理費 − 保険引受に係る営業費及び一般管理費)) (±3)",
                g("pl_ordinary_profit", col), z(g("pl_underwriting_profit", col)) + z(g("pl_investment_pl", col)) + other, 3)
            npw = g("pl_net_premiums_written", col)
            if npw:
                add(f"P08_loss_ratio{sfx}", "pl_loss_ratio_pct = (正味支払保険金 + 損害調査費) / 正味収入保険料 × 100 (±0.1)", g("pl_loss_ratio_pct", col),
                    (z(g("pl_net_claims_paid", col)) + z(g("pl_loss_adjustment_expenses", col))) / npw * 100, 0.1)
                add(f"P09_expense_ratio{sfx}", "pl_expense_ratio_pct = (諸手数料及び集金費 + 保険引受に係る営業費及び一般管理費) / 正味収入保険料 × 100 (±0.1)", g("pl_expense_ratio_pct", col),
                    (z(g("pl_commissions_collection", col)) + z(g("pl_uw_operating_general_admin", col))) / npw * 100, 0.1)
            # tol 3: four 百万円-truncated terms (Sompo Japan FY2025 reproduces to 48,253 vs disclosed 48,251; au/Meiji within 1)
            add(f"P11_underwriting{sfx}", "pl_underwriting_profit = 保険引受収益 − 保険引受費用 − 保険引受に係る営業費及び一般管理費 + その他収支 (±3, 4 truncated terms)", g("pl_underwriting_profit", col),
                z(g("pl_underwriting_revenue", col)) - z(g("pl_underwriting_expenses", col)) - z(g("pl_uw_operating_general_admin", col)) + z(g("pl_underwriting_other", col)), 3)
            add(f"P13_interest_vs_investment{sfx}", "pl_interest_dividend_income ≈ pl_investment_pl (등식은 운용비용·매각손익 0 인 회사만 — informational)", g("pl_interest_dividend_income", col), z(g("pl_investment_pl", col)), 1, gate=False)
            dep = ((pf.get("adjustments") or {}).get("deposit_premium_in_gross") or {}).get(col)
            add(f"P14_premium_bridge{sfx}", "pl_net_premiums_written = pl_gross_premiums_written + pl_assumed_premiums - pl_ceded_premiums (元受+受再-出再)" + (" - 収入積立保険料 (gross table is 含む収入積立保険料)" if dep is not None else ""),
                g("pl_net_premiums_written", col),
                z(g("pl_gross_premiums_written", col)) + z(g("pl_assumed_premiums", col)) - z(g("pl_ceded_premiums", col)) - z(dep), 1)
            add(f"P15_claims_bridge{sfx}", "pl_net_claims_paid = pl_gross_claims_paid + pl_assumed_claims - pl_recovered_reinsurance_claims (元受+受再-回収)", g("pl_net_claims_paid", col),
                z(g("pl_gross_claims_paid", col)) + z(g("pl_assumed_claims", col)) - z(g("pl_recovered_reinsurance_claims", col)), 1)
            if col == "cur" and g("pl_ceded_commission", col) is not None:
                add("P16_commission_note", "pl_commissions_collection = pl_commissions_gross - pl_ceded_commission (注記 差引; 당기만)", g("pl_commissions_collection", col),
                    z(g("pl_commissions_gross", col)) - z(g("pl_ceded_commission", col)), 1)
    if pf.get("summary5"):
        n = nbad = 0
        for sid, row in pf["summary5"].items():
            for col in ("cur", "prev"):
                if row.get(col) is not None and g(sid, col) is not None:
                    n += 1
                    if abs(row[col] - g(sid, col)) > 0:
                        nbad += 1
        checks.append(dict(id="P10_summary5_xref", formula="主要な経営指標 5개년표 == P&L/明細表 (cur & prev, exact)", lhs=n - nbad, rhs=n, tol="count", **{"pass": nbad == 0 and n > 0}, gate=True, note=f"{n} cells compared"))
    return checks


def run_profit_axes_xref(comp, pf, ax):
    """P12 — profit layer ↔ article_axes cross: pl_core_profit == core_profit (same table, two layers)."""
    out = []
    if comp["sector"] == "life" and comp.get("profit_pages"):
        for col, aid in (("cur", "core_profit"), ("prev", "core_profit_prev")):
            lhs = (pf["values"].get("pl_core_profit") or {}).get(col)
            rhs = ax["values"].get(aid)
            out.append(dict(id=f"P12_core_profit_xref_{col}", formula=f"profit.pl_core_profit.{col} == article_axes.{aid}", lhs=lhs, rhs=rhs, tol=0, **{"pass": lhs is not None and lhs == rhs}, gate=True, note=""))
    return out


# --------------------------------------------------------------------------------------
def extract_byline(comp, doc):
    """layer by_line — 種目別 3표. Rows are grabbed sequentially (cursor) from the table heading so a
    later table on the same page with the same 種目 labels (e.g. 出再 tables) cannot be picked up."""
    ids = [it["id"] for it in BYLINE_ITEMS]
    v, pg, raw, notes = {i: None for i in ids}, {}, {}, []
    bp = comp.get("byline_pages")
    if not bp:
        for i in ids:
            raw[i] = "NO_PAGE"
        return dict(values=v, pages=pg, raw_tokens=raw, notes=notes)
    src_rows = {}
    for src, pages in bp.items():
        lines = page_lines(doc, pages)
        if comp.get("vertical_labels"):
            lines = merge_vertical(lines)
        hres = BYLINE_HEADINGS[src]
        h = next((i for i, (_, ln) in enumerate(lines) if all(re.search(r, ln) for r in hres) and "注" not in ln and "÷" not in ln), None)
        if h is None:
            src_rows[src] = None
            continue
        rows, cur = {}, h + 1
        for code, rx, _ja in LOB_LINES:
            res = grab(lines, cur, [rx])
            if not res or len(res[0]) < 6 or len(res[0]) % 3 != 0:
                rows[code] = None
                continue
            rows[code] = res[0]
            cur = res[2]
        src_rows[src] = (rows, lines[h][0])
    for it in BYLINE_ITEMS:
        got = src_rows.get(it["src"])
        if not got:
            raw[it["id"]] = "NOT_FOUND"
            continue
        rows, page = got
        vals, rt = {}, {}
        for code, _rx, _ja in LOB_LINES:
            toks = rows.get(code)
            if toks is None:
                vals[code] = None
                rt[code] = "NOT_FOUND"
                continue
            g = len(toks) // 3
            if it["pos"] >= g:
                vals[code] = None
                rt[code] = "COL_ABSENT"
                continue
            vals[code] = dict(prev=to_val(toks[g + it["pos"]]), cur=to_val(toks[2 * g + it["pos"]]))
            rt[code] = toks
        v[it["id"]], pg[it["id"]], raw[it["id"]] = vals, page, rt
    # claims table's own 正味損害率 column (3rd token when g == 3) — kept as an informational cross-ref
    got = src_rows.get("claims")
    if got:
        rows, page = got
        xr = {}
        for code, _rx, _ja in LOB_LINES:
            toks = rows.get(code)
            if toks and len(toks) // 3 >= 3:
                g = len(toks) // 3
                xr[code] = dict(prev=to_val(toks[g + 2]), cur=to_val(toks[2 * g + 2]))
        if xr:
            v["_loss_ratio_from_claims_table"] = xr
    return dict(values=v, pages=pg, raw_tokens=raw, notes=notes)


def run_byline_checks(comp, byl, pf):
    """B01 Σ종목 == 合計 (±1 per amount item) · B02 合計 손해율/사업비율/합산율 == profit 층 (±0.1) ·
    B03 종목별 合算率 == 손해율+사업비율 (±0.15, each rounded) · B04 claims 표 損害率 열 == ratio 표 (informational)."""
    checks = []
    if not comp.get("byline_pages"):
        return checks
    v = byl["values"]
    for col in ("cur", "prev"):
        for iid in ("lob_net_premiums_written", "lob_net_claims_paid"):
            d = v.get(iid)
            if not d or not d.get("total"):
                continue
            parts = [z((d.get(c) or {}).get(col)) for c in ("fire", "marine", "pa", "motor", "cali", "other")]
            tot = d["total"][col]
            # each 種目 is truncated to 百万円 separately (切り捨て), so Σ of 6 terms runs up to 5 short of the
            # disclosed 合計 (TMNF/MSI/Sompo/Meiji: 2~3) → tol = number of terms (same rule as the risk_tree root check)
            checks.append(dict(id=f"B01_sum_{iid}_{col}", formula=f"Σ(fire..other) == total (±6, 6 truncated terms) [{iid}]", lhs=sum(parts), rhs=tot, tol=6,
                               **{"pass": tot is not None and abs(sum(parts) - tot) <= 6}, note=""))
        for lid, pid in (("lob_loss_ratio_pct", "pl_loss_ratio_pct"), ("lob_expense_ratio_pct", "pl_expense_ratio_pct"), ("lob_combined_ratio_pct", "pl_combined_ratio_pct")):
            d = v.get(lid)
            pv = (pf["values"].get(pid) or {}).get(col) if pf else None
            if not d or not d.get("total") or pv is None:
                continue
            lv = d["total"][col]
            checks.append(dict(id=f"B02_total_{lid}_{col}", formula=f"{lid}[total] == profit.{pid} (±0.1)", lhs=lv, rhs=pv, tol=0.1,
                               **{"pass": lv is not None and abs(lv - pv) <= 0.1 + 1e-9}, note=""))
        lr, er, cr = v.get("lob_loss_ratio_pct"), v.get("lob_expense_ratio_pct"), v.get("lob_combined_ratio_pct")
        if lr and er and cr:
            for code, _rx, _ja in LOB_LINES:
                c = (cr.get(code) or {}).get(col)
                l, e = (lr.get(code) or {}).get(col), (er.get(code) or {}).get(col)
                if c is None or (l is None and e is None):
                    continue
                checks.append(dict(id=f"B03_combined_{code}_{col}", formula="lob_combined == lob_loss + lob_expense (±0.15)", lhs=c, rhs=round(z(l) + z(e), 1), tol=0.15,
                                   **{"pass": abs(c - (z(l) + z(e))) <= 0.15 + 1e-9}, note=""))
        xr = v.get("_loss_ratio_from_claims_table")
        if xr and lr:
            for code, d in xr.items():
                a, b = d.get(col), (lr.get(code) or {}).get(col)
                if a is None or b is None:
                    continue
                checks.append(dict(id=f"B04_claims_vs_ratio_{code}_{col}", formula="claims-table 正味損害率 == ratio-table 正味損害率 (±0.1, informational)", lhs=a, rhs=b, tol=0.1,
                                   **{"pass": abs(a - b) <= 0.1 + 1e-9}, gate=False, note="same PDF, two tables"))
    return checks

def extract_history(comp, doc, ratio_raw_tokens=None):
    """layer history (ticket 20260912T1440Z) — 主要な経営指標等の推移 5개년표. Reads the same
    profit_pages["summary5"] page already used by extract_profit's P10 cross-check, but keeps
    all 5 fiscal-year columns instead of just {prev,cur}.
    ratio_raw_tokens: pf["raw_tokens"]["pl_loss_ratio_pct"] etc from extract_profit — the 3-fiscal-year
    正味損害率/事業費率/合算率 table's raw 9-token row, used to backfill FY2023-2025 for companies
    (Meiji Yasuda) whose 5개년표 has no ratio rows at all."""
    ids = [it["id"] for it in HISTORY_ITEMS]
    v, pg, raw = {i: None for i in ids}, {}, {}
    pp = comp.get("profit_pages") or {}
    sp = pp.get("summary5")
    if not sp:
        for i in ids:
            raw[i] = "NO_PAGE"
        return dict(values=v, pages=pg, raw_tokens=raw, fiscal_years=HIST_FISCAL_YEARS)
    lines = merge_vertical(page_lines(doc, sp))
    comp_skip = comp.get("hist_skip", [])
    drop_all = comp.get("hist_drop_paren_all", False)
    label_ovr = comp.get("hist_label_overrides", {})

    def row(label_res, skip_res=(), drop_paren=False):
        drop_paren = drop_paren or drop_all
        skip_res = list(skip_res) + list(comp_skip)
        idx = next((i for i in range(len(lines)) if any(re.search(r, lines[i][1]) for r in label_res)), None)
        if idx is None:
            return None, None
        j = idx + 1
        vals, parens = [], []
        while j < len(lines) and len(vals) < 5:
            ln = lines[j][1]
            if PAREN_DASH_RE.match(ln) or any(re.search(r, ln) for r in skip_res):
                j += 1
                continue
            raw_t, is_p = strip_paren(ln)
            if is_p and drop_paren:
                j += 1
                continue
            if is_val(raw_t):
                vals.append(to_val(raw_t))
                parens.append(is_p)
                j += 1
                continue
            break
        return vals, parens

    smr_cache = None
    for it in HISTORY_ITEMS:
        iid = it["id"]
        if it["scope"] not in ("both", comp["sector"]):
            raw[iid] = "N/A_SECTOR"
            continue
        if iid == "hist_combined_ratio_pct":
            continue  # derived below (table rarely prints 合算率 in the 5개년표 itself)
        if it["labels"] is None:
            raw[iid] = "NOT_IMPLEMENTED_id_only"  # life-only ids, no sample company to extract from
            continue
        if it["labels"] == "smr":
            if smr_cache is None:
                if comp.get("hist_smr_layout") == "new_old_pairs":
                    # MSI p31: 単体SMR row = "新基準 | 旧基準 | (new, old) × 5 years" — 旧基準 values are NOT in parens,
                    # so re-express as the common convention: old → parens=True, new → parens=False.
                    idx = next((i for i in range(len(lines)) if re.search(HIST_SMR_LABEL_RE, lines[i][1])), None)
                    toks = []
                    j = (idx + 1) if idx is not None else len(lines)
                    while j < len(lines) and len(toks) < 10:
                        ln = lines[j][1]
                        if ln in ("新基準", "旧基準"):
                            j += 1
                            continue
                        if is_val(ln):
                            toks.append(ln)
                        elif re.match(r"^[（(]注\d*[）)]$", ln):
                            toks.append("－")  # (注1) in the 新基準 cell = not yet disclosed
                        else:
                            break
                        j += 1
                    pairs = [(toks[i], toks[i + 1]) for i in range(0, len(toks) - 1, 2)]
                    vals = [to_val(o) if to_val(n) is None else to_val(n) for n, o in pairs]
                    parens = [to_val(n) is None for n, o in pairs]
                    smr_cache = (vals, parens) if idx is not None else (None, None)
                else:
                    smr_cache = row([HIST_SMR_LABEL_RE])
            vals, parens = smr_cache
        else:
            vals, parens = row(label_ovr.get(iid, it["labels"]), it.get("skip", []), it.get("drop_paren", False))
        if vals is None:
            raw[iid] = "NOT_FOUND"
            continue
        if len(vals) < 5:
            vals = vals + [None] * (5 - len(vals))
            parens = parens + [False] * (5 - len(parens))
        if iid == "hist_smr_old_pct":
            series = {y: (vals[i] if parens[i] else None) for i, y in enumerate(HIST_FISCAL_YEARS)}
        elif iid == "hist_esr_pct":
            series = {y: (vals[i] if not parens[i] else None) for i, y in enumerate(HIST_FISCAL_YEARS)}
        else:
            series = {y: vals[i] for i, y in enumerate(HIST_FISCAL_YEARS)}
        v[iid] = series
        pg[iid] = sp[0]
        raw[iid] = vals

    if comp["sector"] == "nonlife":
        loss, exp = v.get("hist_loss_ratio_pct"), v.get("hist_expense_ratio_pct")
        # backfill FY2023-2025 from the profit:ratio 3-year table when the 5개년표 itself has no
        # 損害率/事業費率 rows (Meiji Yasuda) — same 合計 row P08/P09 already anchor on.
        if (not loss or all(x is None for x in loss.values())) and ratio_raw_tokens and isinstance(ratio_raw_tokens, list) and len(ratio_raw_tokens) >= 9:
            rl = ratio_raw_tokens
            loss = {"FY2021": None, "FY2022": None, "FY2023": to_val(rl[0]), "FY2024": to_val(rl[3]), "FY2025": to_val(rl[6])}
            exp = {"FY2021": None, "FY2022": None, "FY2023": to_val(rl[1]), "FY2024": to_val(rl[4]), "FY2025": to_val(rl[7])}
            v["hist_loss_ratio_pct"], v["hist_expense_ratio_pct"] = loss, exp
            comb_direct = {"FY2021": None, "FY2022": None, "FY2023": to_val(rl[2]), "FY2024": to_val(rl[5]), "FY2025": to_val(rl[8])}
            v["hist_combined_ratio_pct"] = comb_direct
            for iid in ("hist_loss_ratio_pct", "hist_expense_ratio_pct", "hist_combined_ratio_pct"):
                raw[iid] = "BACKFILL from profit:ratio 3yr table (5개년표 has no ratio rows for this company)"
                pg[iid] = pp.get("ratio", [None])[0]
        elif loss and exp:
            comb = {y: (round(loss[y] + exp[y], 1) if loss.get(y) is not None and exp.get(y) is not None else None) for y in HIST_FISCAL_YEARS}
            if any(x is not None for x in comb.values()):
                v["hist_combined_ratio_pct"] = comb
                raw["hist_combined_ratio_pct"] = "DERIVED = hist_loss_ratio_pct + hist_expense_ratio_pct"
    return dict(values=v, pages=pg, raw_tokens=raw, fiscal_years=HIST_FISCAL_YEARS)


def run_history_checks(comp, pf, hist):
    """H01 — FY2025 == profit.cur / FY2024 == profit.prev (5개년표 vs 손익 층, 같은 회사 두 표).
    H02 — 合算率 = 損害率+事業費率 항등식, 연도별."""
    checks = []
    v, pfv = hist["values"], pf["values"]
    for it in HISTORY_ITEMS:
        iid, pid = it["id"], it.get("pl")
        if pid is None or it["scope"] not in ("both", comp["sector"]):
            continue
        hs, pv = v.get(iid), pfv.get(pid)
        if not hs or not pv:
            continue
        tol = 0.1 if it["unit"] == P else 1
        for fy, col in (("FY2025", "cur"), ("FY2024", "prev")):
            lhs, rhs = hs.get(fy), pv.get(col)
            if lhs is None or rhs is None:
                continue  # not disclosed on one side — informational absence, not a mismatch
            ok = abs(lhs - rhs) <= tol + 1e-9
            checks.append(dict(id=f"H01_{iid}_{fy}", formula=f"history.{iid}.{fy} == profit.{pid}.{col} (±{tol})",
                               lhs=lhs, rhs=rhs, tol=tol, **{"pass": ok}, gate=True, note=""))
    if comp["sector"] == "nonlife":
        loss, exp, comb = v.get("hist_loss_ratio_pct"), v.get("hist_expense_ratio_pct"), v.get("hist_combined_ratio_pct")
        if loss and exp and comb:
            for fy in HIST_FISCAL_YEARS:
                l, e, c = loss.get(fy), exp.get(fy), comb.get(fy)
                if l is None or e is None or c is None:
                    continue
                ok = abs(c - (l + e)) <= 0.1
                checks.append(dict(id=f"H02_combined_identity_{fy}", formula="hist_combined_ratio_pct == hist_loss_ratio_pct + hist_expense_ratio_pct (±0.1)",
                                   lhs=c, rhs=round(l + e, 1), tol=0.1, **{"pass": ok}, gate=True, note=""))
    return checks


# --------------------------------------------------------------------------------------
def write_lf(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def z(x):
    return 0 if x is None else x


def run_checks(c):
    v, s, checks = c["values"], c["sensitivity"], []

    def add(cid, formula, lhs, rhs, tol, note=""):
        ok = lhs is not None and rhs is not None and abs(lhs - rhs) <= tol
        checks.append(dict(id=cid, formula=formula, lhs=lhs, rhs=rhs, tol=tol, **{"pass": ok}, note=note))

    def add_le(cid, formula, lhs, rhs, note=""):
        checks.append(dict(id=cid, formula=formula, lhs=lhs, rhs=rhs, tol="lhs<=rhs+1", **{"pass": z(lhs) <= z(rhs) + 1}, note=note))

    e, r, esr = v["eligible_capital"], v["required_capital"], v["esr_pct"]
    if e and r:
        lo, hi = e / (r + 1) * 100, (e + 1) / r * 100
        ok = esr is not None and (lo - 0.05) <= esr <= (hi + 0.05)
        checks.append(dict(id="C01_esr_ratio", formula="esr_pct in [eligible/(required+1), (eligible+1)/required]*100 (±0.05; amounts truncated to 百万円)",
                           lhs=esr, rhs=[round(lo, 2), round(hi, 2)], tol="interval", **{"pass": ok}, note=f"point estimate {e / r * 100:.2f}"))
    add("C02_eligible_eq_total", "eligible_capital == eligible_capital_total", v["eligible_capital"], v["eligible_capital_total"], 0)
    add("C03_required_eq_post_tax", "required_capital == rc_post_tax", v["required_capital"], v["rc_post_tax"], 0)
    add("C04_eligible_tiers", "eligible_capital = tier1_eligible + tier2_eligible", v["eligible_capital"], z(v["tier1_eligible"]) + z(v["tier2_eligible"]), 1)
    add("C05_tier1", "tier1_eligible = tier1_basic - tier1_adjustments", v["tier1_eligible"], z(v["tier1_basic"]) - z(v["tier1_adjustments"]), 1)
    add("C06_tier1_basic", "tier1_basic = instr_unrestricted + instr_restricted + non_instrument", v["tier1_basic"],
        z(v["tier1_instr_unrestricted"]) + z(v["tier1_instr_restricted"]) + z(v["tier1_non_instrument"]), 1)
    add("C07_tier1_non_instr", "tier1_non_instrument = retained + capital_surplus + aoci + other_contrib + ev_adjustment", v["tier1_non_instrument"],
        z(v["tier1_ni_retained_earnings"]) + z(v["tier1_ni_capital_surplus"]) + z(v["tier1_ni_aoci"]) + z(v["tier1_ni_other_contrib"]) + z(v["tier1_ni_ev_adjustment"]), 2)
    add("C08_tier1_adj", "tier1_adjustments = Σ 7 subs", v["tier1_adjustments"],
        sum(z(v[k]) for k in ["tier1_adj_intangibles", "tier1_adj_dta", "tier1_adj_pension_asset", "tier1_adj_holdings_other_fi", "tier1_adj_own_instruments", "tier1_adj_ineligible_reinsurance", "tier1_adj_encumbered_excess"]), 2)
    add("C09_tier2", "tier2_eligible = tier2_basic - tier2_adjustments - tier2_cap_deduction", v["tier2_eligible"], z(v["tier2_basic"]) - z(v["tier2_adjustments"]) - z(v["tier2_cap_deduction"]), 1)
    add("C10_tier2_basic", "tier2_basic = tier2_instruments + tier2_non_instrument", v["tier2_basic"], z(v["tier2_instruments"]) + z(v["tier2_non_instrument"]), 1)
    add("C11_tier2_non_instr", "tier2_non_instrument = surplus_from_instr + encumbered_t1_deducted + basket", v["tier2_non_instrument"],
        z(v["tier2_ni_surplus_from_instr"]) + z(v["tier2_ni_encumbered_t1_deducted"]) + z(v["tier2_ni_basket"]), 1)
    terms = ["rc_life", "rc_nonlife", "rc_catastrophe", "rc_market", "rc_credit", "rc_operational", "rc_mgmt_action_excess"]
    add("C12_rc_pre_tax", "rc_pre_tax = A+B+C+D+E+F+G - H + non_insurance_business (tol = n terms; each term truncated)", v["rc_pre_tax"],
        sum(z(v[k]) for k in terms) - z(v["rc_diversification"]) + z(v["rc_non_insurance_business"]), len(terms) + 2)
    add("C13_rc_post_tax", "rc_post_tax = rc_pre_tax - rc_tax_effect", v["rc_post_tax"], z(v["rc_pre_tax"]) - z(v["rc_tax_effect"]), 1)
    add_le("C14_nonlife_le_sum", "rc_nonlife <= Σ nonlife subs (correlation aggregation)", v["rc_nonlife"], sum(z(v[k]) for k in ["rc_nl_liability", "rc_nl_motor", "rc_nl_property", "rc_nl_other"]))
    add_le("C15_cat_le_sum", "rc_catastrophe <= rc_cat_natural + rc_cat_other", v["rc_catastrophe"], z(v["rc_cat_natural"]) + z(v["rc_cat_other"]))
    add_le("C16_catnat_le_sum", "rc_cat_natural <= Σ nat-cat subs", v["rc_cat_natural"], sum(z(v[k]) for k in ["rc_cat_nat_jp_earthquake", "rc_cat_nat_jp_windflood", "rc_cat_nat_jp_snow", "rc_cat_nat_foreign", "rc_cat_nat_other"]))
    add_le("C17_market_le_sum", "rc_market <= Σ market subs", v["rc_market"], sum(z(v[k]) for k in ["rc_mkt_interest", "rc_mkt_spread", "rc_mkt_equity", "rc_mkt_property", "rc_mkt_fx", "rc_mkt_concentration"]))
    add("C18_tier1_basic_eq_ebs_net", "tier1_basic == ebs_net_assets", v["tier1_basic"], v["ebs_net_assets"], 0)
    add("C19_ebs_net", "ebs_net_assets = ebs_total_assets - ebs_total_liabilities", v["ebs_net_assets"], z(v["ebs_total_assets"]) - z(v["ebs_total_liabilities"]), 1)
    add("C20_ebs_liab", "ebs_total_liabilities = insurance + non_insurance", v["ebs_total_liabilities"], z(v["ebs_insurance_liabilities"]) + z(v["ebs_non_insurance_liabilities"]), 1)
    add("C21_ebs_ins_liab", "ebs_insurance_liabilities = current_estimate + moce", v["ebs_insurance_liabilities"], z(v["ebs_current_estimate"]) + z(v["ebs_moce"]), 1)
    add("C22_ebs_net_bridge", "ebs_net_assets = statutory net assets + regulatory_reserve_equity + ev_adjustment", v["ebs_net_assets"],
        z(v["ebs_net_assets_statutory"]) + z(v["ebs_regulatory_reserve_equity"]) + z(v["ebs_ev_adjustment"]), 1)
    add("C23_ev_adj_xref", "tier1_ni_ev_adjustment == ebs_ev_adjustment", v["tier1_ni_ev_adjustment"], v["ebs_ev_adjustment"], 0)
    add("C24_intangibles_xref", "tier1_adj_intangibles == ebs_intangibles", v["tier1_adj_intangibles"], v["ebs_intangibles"], 0)
    add("C25_capital_surplus_xref", "tier1_ni_capital_surplus == ebs_capital_surplus", v["tier1_ni_capital_surplus"], v["ebs_capital_surplus"], 0)
    add("C26_retained_xref", "tier1_ni_retained_earnings = ebs_retained_earnings + ebs_regulatory_reserve_equity", v["tier1_ni_retained_earnings"],
        z(v["ebs_retained_earnings"]) + z(v["ebs_regulatory_reserve_equity"]), 1)
    add("C27_aoci_xref", "tier1_ni_aoci == ebs_aoci", z(v["tier1_ni_aoci"]), z(v["ebs_aoci"]), 0)
    add("C28_il_eq_current_estimate", "il_total_ex_moce == ebs_current_estimate", v["il_total_ex_moce"], v["ebs_current_estimate"], 0)
    add("C29_il_split", "il_total_ex_moce = il_unexpired + il_incurred", v["il_total_ex_moce"], z(v["il_unexpired"]) + z(v["il_incurred"]), 1)
    if v.get("esr_pct_5yr_summary") is not None:
        add("C30_headline_5yr", "esr_pct == 5-year-summary headline", v["esr_pct"], v["esr_pct_5yr_summary"], 0)
    add("C34_reg_reserve_bridge", "ebs_regulatory_reserve_equity = reg_reserve_in_liabilities + price_fluctuation_reserve - other_reserves_reclass (observed, 2 samples)",
        v["ebs_regulatory_reserve_equity"], z(v["ebs_reg_reserve_in_liabilities"]) + z(v["ebs_price_fluctuation_reserve"]) - z(v["ebs_other_reserves_reclass"]), 2)
    lv = s["levels"]
    if lv.get("esr_pct") and lv["esr_pct"].get("base") is not None:
        for rid in ["esr_pct", "eligible_capital", "required_capital", "ebs_net_assets", "ebs_total_assets", "rc_market", "ebs_moce", "il_total_ex_moce", "ebs_non_insurance_liabilities"]:
            add(f"C31_sens_base_{rid}", f"sensitivity.levels.{rid}.base == {rid}", lv[rid]["base"] if lv.get(rid) else None, v.get(rid), 0)
        if s["diffs"]:
            nbad = n = 0
            for rid, row in s["diffs"].items():
                if not row or not lv.get(rid):
                    continue
                tol = 0.15 if rid == "esr_pct" else 1
                for sc in s["scenarios"][1:]:
                    if row.get(sc) is None or lv[rid].get(sc) is None:
                        continue
                    n += 1
                    if abs((lv[rid][sc] - lv[rid]["base"]) - row[sc]) > tol:
                        nbad += 1
            checks.append(dict(id="C32_sens_diff_table", formula="diffs[row][sc] == levels[row][sc] - levels[row].base (pct ±0.15, amounts ±1)", lhs=n - nbad, rhs=n, tol="count", **{"pass": nbad == 0}, note=f"{nbad} mismatches"))
        nb = n = 0
        for sc in s["scenarios"][1:]:
            ee, rr, xx = lv["eligible_capital"].get(sc), lv["required_capital"].get(sc), lv["esr_pct"].get(sc)
            if ee and rr and xx is not None:
                n += 1
                lo, hi = ee / (rr + 1) * 100, (ee + 1) / rr * 100
                if not (lo - 0.05 <= xx <= hi + 0.05):
                    nb += 1
        checks.append(dict(id="C33_sens_ratio", formula="each scenario esr == eligible/required (truncation interval)", lhs=n - nb, rhs=n, tol="count", **{"pass": nb == 0}, note=""))
    else:
        checks.append(dict(id="C31_sens_base", formula="sensitivity table present or omission note present", lhs=None, rhs=None, tol="",
                           **{"pass": c["method"].get("sensitivity_omitted") is True}, note="issuer omitted values (all |Δ| < 1pp) — pass only if the omission note is present"))
    return checks


def sqrt_agg(x, R):
    """sqrt(x^T R x); x already null->0."""
    n = len(x)
    return math.sqrt(max(0.0, sum(x[i] * x[j] * R[i][j] for i in range(n) for j in range(n))))


def run_aggregation_checks(comp, c, rules):
    """Recompute 所要資本の額の構成 (form 3) from the disclosed sub-amounts with the 告示74 correlation matrices
    (J-ESR/esr_aggregation_rules.json) — the J-ESR analogue of the K-ICS mmult check. Every check carries
    `gate`: False = informational (structurally not reproducible from disclosed inputs, or a registered known deviation)."""
    v, L, checks = c["values"], rules["levels"], {}
    known = {(d["company_key"], d["check"]) for d in rules.get("known_deviations", [])}
    calc = {}

    def add(cid, formula, lhs, rhs, tol, gate=True, note=""):
        ok = lhs is not None and rhs is not None and abs(lhs - rhs) <= tol
        if not ok and (comp["key"], cid) in known:
            gate, note = False, (note + " | registered in esr_aggregation_rules.json known_deviations").strip(" |")
        checks[cid] = dict(id=cid, formula=formula, lhs=lhs, rhs=None if rhs is None else round(rhs, 1), tol=tol, **{"pass": ok}, gate=gate, note=note)

    # --- top level (第百五十五条) ---
    top = L["top"]
    x = [z(v.get(i)) for i in top["ids"]]
    top_sqrt = sqrt_agg(x, top["matrix"])
    simple = sum(x)
    F, G, I = z(v.get("rc_operational")), z(v.get("rc_mgmt_action_excess")), z(v.get("rc_non_insurance_business"))
    calc.update(top_sqrt=round(top_sqrt, 1), simple_sum_ABCDE=simple, diversification=round(simple - top_sqrt, 1))
    add("G01_top_diversification", "rc_diversification == Σ(A..E) − sqrt(x^T R_top x)", v.get("rc_diversification"), simple - top_sqrt, 1)
    add("G02_pre_tax_chain", "rc_pre_tax == top_sqrt + F + G + I (tol = 7 truncated inputs)", v.get("rc_pre_tax"), top_sqrt + F + G + I, 7)
    # --- operational cap (第百五十四条) ---
    op = L["operational"]
    cap = op["cap_factor"] * (top_sqrt + G)
    at_cap = abs(F - cap) <= 1
    calc.update(op_cap=round(cap, 1), op_at_cap=at_cap)
    checks["G03_op_cap"] = dict(id="G03_op_cap", formula="rc_operational <= 0.20 × (top_sqrt + G) + 1", lhs=F, rhs=round(cap, 1), tol=1,
                                **{"pass": F <= cap + 1}, gate=True, note="AT CAP (binding)" if at_cap else "below cap")
    # --- tax effect (第百五十六条第一号 branch 1) ---
    tx = L["tax_effect"]
    t = tx["statutory_effective_tax_rate"]["assumed_for_check"]
    K, J = v.get("rc_tax_effect"), v.get("rc_pre_tax")
    base = top_sqrt + F + G
    implied_t = (K / (J - I) / tx["branch1_factor"]) if (K is not None and J) else None
    tax_calc = tx["branch1_factor"] * t * base
    calc.update(tax_branch1=round(tax_calc, 1), implied_statutory_tax_rate=None if implied_t is None else round(implied_t, 4))
    checks["G04_tax_branch1"] = dict(id="G04_tax_branch1", formula=f"rc_tax_effect <= 0.80 × t × (top_sqrt+F+G) + 1, t={t}; implied t reported", lhs=K, rhs=round(tax_calc, 1), tol=1,
                                     **{"pass": K is not None and K <= tax_calc + 1}, gate=True,
                                     note=("branch 1 binds (|K − 0.8·t·base| <= 1)" if K is not None and abs(K - tax_calc) <= 1 else "K off branch 1 → branch 2 (DTA/profit) binds or different t")
                                     + (f"; implied t = {implied_t:.4f}" if implied_t is not None else ""))
    # --- market (第百二十七条) ---
    mk = L["market"]
    xm = [z(v.get(i)) for i in mk["ids"]]
    # 告示75 注5(3): the row is relabelled スプレッドリスク（上昇）/（下降）の額 according to which stress binds → selects the matrix
    case = "matrix_case_down" if "下降" in (c.get("spread_label") or "") else "matrix_case_up"
    mkt_sqrt = sqrt_agg(xm, mk[case])
    calc.update(market_sqrt=round(mkt_sqrt, 1), market_case=case)
    add("G05_market", f"rc_market == sqrt(x^T R_mkt x) [{case}] (tol 6)", v.get("rc_market"), mkt_sqrt, 6)
    # --- nonlife (第八十九条; disclosed subs per 告示75 注3(2)) ---
    nl = L["nonlife"]
    xn = [z(v.get(i)) for i in nl["ids"]]
    nl_sqrt = sqrt_agg(xn, nl["matrix_for_disclosed_subs"])
    multi_geo = z(v.get("rc_cat_nat_foreign")) > 0
    calc.update(nonlife_sqrt=round(nl_sqrt, 1), multi_geography=multi_geo)
    if any(xn):
        add("G06_nonlife", "rc_nonlife == sqrt(x^T R_nl x), ρ=0.50 (exact only for single-geography companies)", v.get("rc_nonlife"), nl_sqrt, 4,
            gate=not multi_geo, note="multi-geography (rc_cat_nat_foreign > 0): regulation aggregates 大区分 within geography first → informational" if multi_geo else "single-geography")
    # --- catastrophe (第百条) ---
    ct = L["catastrophe"]
    xc = [z(v.get(i)) for i in ct["ids"]]
    cat_sqrt = sqrt_agg(xc, ct["matrix"])
    calc.update(cat_sqrt=round(cat_sqrt, 1))
    if any(xc):
        add("G07_catastrophe", "rc_catastrophe == sqrt(nat² + other²) (ρ=0.00, 告示75 注4(4))", v.get("rc_catastrophe"), cat_sqrt, 2)
    jp = [z(v.get(i)) for i in ["rc_cat_nat_jp_earthquake", "rc_cat_nat_jp_windflood", "rc_cat_nat_jp_snow"]]
    if any(jp):
        nat_calc = math.sqrt(sum(a * a for a in jp)) + z(v.get("rc_cat_nat_foreign")) + z(v.get("rc_cat_nat_other"))
        calc.update(natcat_japan_sqrt=round(math.sqrt(sum(a * a for a in jp)), 1), natcat_calc=round(nat_calc, 1))
        add("G08_natcat_japan", "rc_cat_natural == sqrt(Σ jp perils²) + foreign + other (observed simple sum across geographies; 第九十二条 unspecified)", v.get("rc_cat_natural"), nat_calc, 5, gate=False)
    # --- life (第八十一条) ---
    lf = L["life"]
    xl = [z(v.get(i)) for i in lf["ids"]]
    if any(xl):
        add("G10_life", "rc_life == sqrt(x^T R_life x)", v.get("rc_life"), sqrt_agg(xl, lf["matrix"]), 5)
    # --- full chain to headline ---
    post_calc = top_sqrt + F + G + I - tax_calc
    e = v.get("eligible_capital")
    esr_calc = e / post_calc * 100 if e and post_calc else None
    calc.update(post_tax_calc=round(post_calc, 1), esr_calc=None if esr_calc is None else round(esr_calc, 2))
    add("G09_post_tax_chain", "rc_post_tax vs top_sqrt + F + G + I − 0.8·t·(top_sqrt+F+G) (tol 8)", v.get("rc_post_tax"), post_calc, 8)
    # ratio tolerance follows the amount tolerance of G09: ±8 百万円 on the denominator → ±(esr × 8 / R) pp (au: 792% / 1,171 → 1 百万円 = 0.68pp)
    tol_pp = round(max(0.5, (esr_calc or 0) * 8 / post_calc), 2) if post_calc else 0.5
    add("G09b_esr_chain", f"esr_pct vs eligible / rc_post_tax_calc × 100 (tol {tol_pp}pp = 8 百万円 on the denominator)", v.get("esr_pct"), esr_calc, tol_pp)
    return list(checks.values()), calc


def run_axes_checks(comp, ax, esr):
    checks = []
    v = ax["values"]
    if comp["sector"] == "nonlife" and esr and v.get("cat_reserve_total") is not None:
        # au: 規制上の準備金 reclassified to equity == 異常危険準備金 total (no 価格変動準備金 / 危険準備金 at au)
        lhs, rhs = esr["values"].get("ebs_regulatory_reserve_equity"), z(v["cat_reserve_total"]) + z(esr["values"].get("ebs_price_fluctuation_reserve"))
        checks.append(dict(id="A01_cat_reserve_vs_ebs_reg_reserve", formula="ebs_regulatory_reserve_equity == cat_reserve_total + price_fluctuation_reserve (when no other regulatory reserves)", lhs=lhs, rhs=rhs, tol=1, **{"pass": lhs is not None and abs(lhs - rhs) <= 1}, note="au: 異常危険準備金 2,222 is the only regulatory reserve"))
    if v.get("_reins_rating_buckets"):
        tot = sum((x or 0) for x in v["_reins_rating_buckets"].values())
        checks.append(dict(id="A02_reins_rating_sum", formula="Σ rating buckets == 100", lhs=round(tot, 1), rhs=100.0, tol=0.2, **{"pass": abs(tot - 100) <= 0.2}, note=""))
    if comp["sector"] == "life" and v.get("core_profit") is not None:
        checks.append(dict(id="A03_core_profit_positive_int", formula="core_profit parsed as int (百万円)", lhs=v["core_profit"], rhs=None, tol="", **{"pass": isinstance(v["core_profit"], int)}, note=""))
        checks.append(dict(id="A04_negative_spread_sign", formula="interest_margin_sign == negative iff negative_spread_100m > 0", lhs=v["interest_margin_sign"], rhs=v["negative_spread_100m"], tol="",
                           **{"pass": (v["interest_margin_sign"] == "negative") == (z(v["negative_spread_100m"]) > 0)}, note=""))
    if v.get("esr_status") == "not_yet":
        checks.append(dict(id="A05_placeholder_found", formula="esr_status not_yet requires >=1 placeholder location", lhs=len(v["esr_placeholder_locations"]), rhs=">=1", tol="", **{"pass": len(v["esr_placeholder_locations"]) >= 1}, note=""))
    return checks


def census_headline(company_jp):
    with open(CENSUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["company_jp"] == company_jp:
                return dict(esr_pct=float(row["esr_pct"]) if row["esr_pct"] else None, status=row["fy2025_esr_status"], scope=row["esr_scope"], as_of=row["as_of"])
    return dict(esr_pct=None, status=None, scope=None, as_of=None)


def clean_label(rx):
    return re.sub(r"\\s\*|\\\(|\\\)|\\\+|[\^\$]", lambda m: {"\\(": "(", "\\)": ")", "\\+": "+"}.get(m.group(0), ""), rx).replace("\\s*", "")


def build_schema():
    items = []
    for it in ITEMS:
        items.append(dict(id=it["id"], layer="esr", table=it["table"], labels_ja=[clean_label(l) for l in it["labels"]], ko=it["ko"], unit=it["unit"],
                          parent=it["parent"], formula=it["formula"], required=it["required"], column=it.get("col", "cur"), kics_item_ref=it["kics"]))
    for it in EXTRA_ESR_ITEMS:
        items.append(dict(id=it["id"], layer="esr", table=it["table"], labels_ja=it["labels_ja"], ko=it["ko"], unit=it["unit"], parent=it["parent"], formula=it["formula"],
                          required=it["required"], column=it["column"], kics_item_ref=it["kics"]))
    for sc, ja, ko in SENS_SCENARIOS[1:]:
        items.append(dict(id=f"sens_{sc}_esr_pct", layer="esr", table="T7", labels_ja=[ja], ko=f"민감도 ESR: {ko}", unit=P, parent="esr_pct",
                          formula="levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음)", required=False, column="sens", kics_item_ref=None))
    for mi in METHOD_ITEMS:
        items.append(dict(id=mi["id"], layer="esr", table="T8", labels_ja=mi["labels"], ko=mi["ko"], unit="flag", parent=None, formula=None, required=False, column="text", kics_item_ref=None))
    items.append(dict(id="calc_method", layer="esr", table="T8", labels_ja=["内部モデル手法の適用", "標準的手法"], ko="산정방식 standard / standard_implied / internal_model", unit="enum", parent=None, formula="derived from internal_model_applied", required=True, column="text", kics_item_ref=None))
    items.append(dict(id="discount_bucket_jpy", layer="esr", table="T8", labels_ja=["適用バケット", "一般バケット", "ミドルバケット", "トップバケット"], ko="엔화 할인율 버킷", unit="enum", parent=None, formula=None, required=False, column="text", kics_item_ref=None))
    items.append(dict(id="discount_rates_jpy", layer="esr", table="T8", labels_ja=["主な通貨", "主要な年限ごとの割引率"], ko="엔화 할인율(연한별 %)", unit="pct_by_tenor", parent=None, formula=None, required=False, column="text", kics_item_ref=None))
    for a in AXES_ITEMS:
        items.append(dict(id=a["id"], layer="article_axes", table="axes:" + a["axis"], labels_ja=a["labels_ja"], ko=a["ko"], unit=a["unit"], parent=None, formula=None,
                          required=(a["id"] in ("esr_status", "air_used", "interest_margin_sign", "cat_reserve_total")), column="section", applies_to=a["applies"], kics_item_ref=a["kics"]))
    for it in PROFIT_ITEMS:
        items.append(dict(id=it["id"], layer="profit", table="profit:" + it["src"], labels_ja=[clean_label(l) for l in it["labels"]], ko=it["ko"], unit=it["unit"], parent=None,
                          formula=it["formula"], required=(it["id"] in ("pl_ordinary_profit", "pl_net_income")), column="prev+cur", sector_scope=it["scope"],
                          kics_item_ref=None, pl_item_ref=it["pl"]))
    for mi in PROFIT_META_ITEMS:
        items.append(dict(id=mi["id"], layer="profit", table="profit:meta", labels_ja=mi["labels"], ko=mi["ko"], unit=mi["unit"], parent=None, formula=None,
                          required=(mi["id"] in ("accounting_basis", "ifrs17_applied")), column="text", sector_scope="both", kics_item_ref=None, pl_item_ref=None))
    for it in BYLINE_ITEMS:
        items.append(dict(id=it["id"], layer="by_line", table="by_line:" + it["src"], labels_ja=[clean_label(l) for l in it["labels"]] + [ja for _c, _r, ja in LOB_LINES],
                          ko=it["ko"], unit=it["unit"], parent=None, formula=("= lob_loss_ratio_pct + lob_expense_ratio_pct" if it["id"] == "lob_combined_ratio_pct" else None),
                          required=False, column="line×prev+cur", sector_scope="nonlife", line_codes=[c for c, _r, _j in LOB_LINES], kics_item_ref=None, pl_item_ref=it["pl"]))
    for it in HISTORY_ITEMS:
        if it["labels"] is None:
            labels_ja = []
        elif it["labels"] == "smr":
            labels_ja = ["単体ベースのソルベンシー・マージン比率"]
        else:
            labels_ja = [clean_label(l) for l in it["labels"]]
        formula = "= hist_loss_ratio_pct + hist_expense_ratio_pct (표 직접값이 있으면 그 값 우선, 없으면 파생)" if it["id"] == "hist_combined_ratio_pct" else (
            "괄호(旧基準) 값만 — 신제도 시행 전 연도" if it["id"] == "hist_smr_old_pct" else (
            "괄호 없는(新基準) 값만 — FY2025 부터" if it["id"] == "hist_esr_pct" else None))
        items.append(dict(id=it["id"], layer="history", table="history:summary5", labels_ja=labels_ja, ko=it["ko"], unit=it["unit"], parent=None,
                          formula=formula, required=(it["id"] in ("hist_ordinary_profit", "hist_net_income")), column="fiscal_years", sector_scope=it["scope"],
                          kics_item_ref=None, pl_item_ref=None))
    return dict(
        schema_version="2026-09-12",
        regulation="保険業法施行規則 59条の2 / 令和7年金融庁告示第74号(SMR告示)·第75号(EBS) — FY2025 첫 적용",
        layers={"esr": "regulatory ESR tables (T1~T8)", "article_axes": "FSA monitoring-report axes from other sections (docs/domains/claude-agent-jp.md §4b): catastrophe_reserve_adequacy / air_used / interest_margin_sign + ESR placeholder skeleton",
                "profit": "J-GAAP statutory P&L layer (ticket 20260912T1150Z): 損益計算書 spine + 損保 保険引受利益·資産運用損益·損害率/事業費率/合算率 + 生保 基礎利益·キャピタル/臨時·三利源 + accounting-basis meta. Values are {prev, cur} pairs.",
                "history": "5개년 시계열 층 (ticket 20260912T1440Z): 「主要な経営指標等の推移」 표에서 정미수입보険料/経常利益/当期純利益/損害率/事業費率/合算率/総資産/純資産/(旧基準SMR·新基準ESR) 를 FY2021~FY2025 5개 사업연도로 뽑는다. 生保 id 3개(hist_core_profit/hist_premium_income/hist_policy_reserves)는 id만 정의, 표본 손보 2사엔 미적용.",
                "by_line": "종목별 층 (ticket 20260913T0400Z): 損保 保険引受の状況 種目別 3표(正味収入保険料 / 正味支払保険金 / 正味損害率·正味事業費率·合算率)에서 火災·海上·傷害·自動車·自賠責·その他·合計 × {prev,cur}. 종목 코드 fire|marine|pa|motor|cali|other|total."},
        unit_note="amounts as disclosed (JPY_million = 百万円) unless the item unit says otherwise (negative_spread_* are 億円 in the life summary box). census/master converts to 億円 (÷100). Record unit_disclosed per row — large life insurers may print 億円.",
        null_note="dash (－ / ー) = not applicable; stored as null, treated as 0 in formulas.",
        column_note="FY2025 tables carry two value columns (イ=前年度 '－', ロ=当年度); column='cur' takes the 2nd token. EBS tables: 'ev' = last token (経済価値ベースの額), 'first' = 財務会計ベースの額 (only when all 4 columns are printed). profit layer: column='prev+cur' = both fiscal years of the 損益計算書 (前年度 / 当年度), stored as {\"prev\":…, \"cur\":…}. history layer: column='fiscal_years' = {\"FY2021\":…,…,\"FY2025\":…}, position in the disclosed row = fiscal year (oldest -> newest) regardless of company; hist_smr_old_pct/hist_esr_pct 는 같은 SMR/ESR 행을 괄호 유무로 나눈 것(괄호=旧基準, 없으면=新基準・FY2025 부터).",
        kics_ref_note="kics_item_ref = docs/agents/kics-json-validation-rules.md item number. Approximate mappings (different aggregation/scope) are documented in docs/domains/jp_esr_disclosure_template.md §6; null = no K-ICS counterpart (e.g. 巨大災害 C, スプレッド, MOCE, EBS rows).",
        pl_ref_note="pl_item_ref (profit layer only) = root PL_breakdown.json 항목번호 1~32 (docs/domains/claude-agent-ifrs17.md). Strict counterparts only: 24 당기순이익 / 22 세전이익 / 23 법인세 exact; 20 영업이익 ≈ 経常利益 (J 特別損益 ≈ K 영업외 — approximate); 1 보험손익 ≈ 損保 保険引受利益 and 17 투자손익 ≈ 資産運用損益 are J-GAAP-cost vs IFRS17 concepts (approximate, sign/scope differ). 基礎利益·三利源·正味収入保険料·損害率 등은 null (no IFRS17 analogue).",
        accounting_basis_note="accounting_basis: jgaap when (A) 会計方針 절이 企業会計基準/標準責任準備金(大蔵省告示第48号) 을 인용하거나 (B) 법정 損益計算書 양식(責任準備金繰入額 등) + 会社法第436条/保険業法第111条 감사 문구가 같이 있고 IFRS 언급이 없을 때; ifrs when 連結財務諸表の作成基準 이 国際財務報告基準/IFRS 를 명시. ifrs17_applied: true 는 IFRS第17号 명시, false 는 accounting_basis=jgaap 인 単体 법정재무제표(保険業法 상 J-GAAP 강제)에서만, 그 외 unstated. 추정 금지.",
        tables={
            "T1": "要約: ソルベンシー・マージン比率並びに適格資本の額及び所要資本の額 (headline)",
            "T1_combined": "au variant: (1) 単体SMR 결합표 — Tier1/2 + 리스크(a)~(k) 한 표, 非保険事業 (i) 포함",
            "T2": "適格資本の額の構成に関する事項",
            "T3": "所要資本の額の構成に関する事項",
            "T4": "経済価値ベースのバランスシート (4열: 財務会計/組替え/評価替え/経済価値)",
            "T5": "外国証券の種類別差異調整 (look-through; not extracted)",
            "T6": "保険負債の商品別差異調整 (6열; 経済価値ベースの額(MOCE除く) 만 추출)",
            "T7": "感応度分析 (8 scenarios × 10 rows; 差額表 optional)",
            "T8": "定性: 計算に用いられた前提及び手法 (내부모형/USP/내부할인율/경영조치/재보험/할인율 버킷)",
            "axes:catastrophe_reserve_adequacy": "손보 본편 責任準備金の内訳 표(종목 × 普通/異常危険/危険/払戻/配当/合計)",
            "axes:air_used": "リスク管理·再保険 절 + 出再先 수/上位5社/格付 표 + 関連当事者 각주",
            "axes:interest_margin_sign": "생보 経常利益等の明細(基礎利益) 표 + 健全性 box 逆ざや (+ 三利源 표가 있는 회사는 利差損益)",
            "axes:esr_placeholder": "後日公表予定 문구가 놓인 5개년 표·健全性 box·業績データ 7절",
            "profit:pl": "損益計算書 (前年度/当年度 2열 ± 比較増減·百分比 열)",
            "profit:uw": "損保 保険引受利益明細表 (3개년: 保険引受収益/費用/営業費及び一般管理費/その他収支/保険引受利益)",
            "profit:ratio": "損保 正味損害率、正味事業費率及びその合算率 표 (종목 × 3개년, 合計행)",
            "profit:inv": "損保 資産運用利回り(実現利回り) 표 合計행 = 資産運用損益(実現ベース)",
            "profit:core": "生保 経常利益等の明細(基礎利益) 표 (基礎利益 A / キャピタル損益 B / 臨時損益 C / 経常利益 A+B+C)",
            "profit:three": "生保 三利源 표 (利差損益/危険差損益/費差損益) — 대형사만, NN Life 는 없음",
            "profit:meta": "회계방침 절(会計方針に関する事項)·감사 문구·損益計算書 양식에서 회계기준 판정",
            "profit:bridge": "損保 保険引受の状況 — 元受/受再/出再 재보험 다리 6표(각 표 종목별+合計행, ticket 20260913T0025Z). pl_net_premiums_written = gross+assumed-ceded, pl_net_claims_paid = gross_claims+assumed_claims-recovered",
            "by_line:premiums": "損保 正味収入保険料 種目別 표 (3개년 × (金額,構成比[,増減率]))",
            "by_line:claims": "損保 正味支払保険金 種目別 표 (3개년 × (金額,構成比[,正味損害率]))",
            "by_line:ratio": "損保 正味損害率、正味事業費率及びその合算率 種目別 표 (3개년 × (損害率,事業費率,合算率))",
            "history:summary5": "主要な経営指標等の推移 5개년표 (au 業績データ 편 p2 / Meiji Yasuda 본편 p9) — 정미수입보험료·経常利益·当期純利益·(손보만)損害率·事業費率·総資産額·純資産額·単体ベースのソルベンシー・マージン比率(旧基準 괄호/신기준 ESR 비괄호)",
        },
        sensitivity=dict(scenarios=[dict(id=a, label_ja=b, ko=c) for a, b, c in SENS_SCENARIOS],
                         rows=[dict(id=a, label_ja=re.sub(r"[\^\$]", "", b), ko=c, unit=d, kics_item_ref=e) for a, b, c, d, e in SENS_ROWS]),
        items=items,
        checks="C01..C34 (esr) + A01..A05 (article_axes) + G01..G10 (aggregation recompute, sqrt(x^T R x)) + P01..P15 (profit, cur & prev; P14/P15 = 元受/受再/出再 bridge) + H01..H02 (history: FY2025==profit.cur, FY2024==profit.prev, 合算率 항등식) implemented in J-ESR/extract_esr_template_samples.py::run_checks / run_axes_checks / run_aggregation_checks / run_profit_checks / run_profit_axes_xref / run_history_checks",
        aggregation_rules_ref="J-ESR/esr_aggregation_rules.json (告示74 第八十一条·第八十九条·第百条·第百二十七条·第百五十四条~第百五十六条 + 告示75 別紙様式第三号 注; matrices in id order)",
    )


def md_fragment(results, schema):
    keys = [c["key"] for c in COMPANIES]
    rows = ["| id | layer | table | label (ja) | meaning (ko) | unit | parent | kics | " + " | ".join(keys) + " | page | formula |",
            "|---|---|---|---|---|---|---|---|" + "---|" * len(keys) + "---|---|"]
    for it in schema["items"]:
        vals, pg = [], []
        for k in keys:
            r = results[k]
            val, page = "", ""
            if it["layer"] == "esr" and r.get("esr"):
                e = r["esr"]
                if it["table"] == "T7":
                    sc = it["id"][len("sens_"):-len("_esr_pct")]
                    lv = e["sensitivity"]["levels"].get("esr_pct")
                    val = "" if not lv or lv.get(sc) is None else str(lv[sc])
                    page = str(e["sensitivity"]["pages"][0])
                elif it["table"] == "T8":
                    val = str(e["method"].get(it["id"]))
                else:
                    x = e["values"].get(it["id"])
                    val = "－" if x is None else (f"{x:,}" if isinstance(x, int) else str(x))
                    page = "" if e["pages"].get(it["id"]) is None else str(e["pages"][it["id"]])
            elif it["layer"] == "article_axes" and r.get("axes"):
                x = r["axes"]["values"].get(it["id"])
                if isinstance(x, list):
                    val = f"{len(x)} loc" if x else "－"
                elif isinstance(x, dict):
                    val = json.dumps(x, ensure_ascii=False)
                else:
                    val = "－" if x is None else (f"{x:,}" if isinstance(x, int) and not isinstance(x, bool) else str(x))
            elif it["layer"] == "esr":
                val = "n/a(not_yet)"
            elif it["layer"] == "profit" and r.get("profit"):
                pf = r["profit"]
                if it["table"] == "profit:meta":
                    x = pf["meta"].get(it["id"])
                    val = "－" if x is None else str(x)
                else:
                    x = pf["values"].get(it["id"])
                    rt = pf["raw_tokens"].get(it["id"])
                    if x is None:
                        val = "n/a" if rt == "N/A_SECTOR" else ("NOT_ACQUIRED" if rt == "NOT_ACQUIRED" else "－")
                    else:
                        fmt = lambda y: "－" if y is None else (f"{y:,}" if isinstance(y, int) else str(y))
                        val = f"{fmt(x['cur'])} (prev {fmt(x['prev'])})"
                    page = "" if pf["pages"].get(it["id"]) is None else str(pf["pages"][it["id"]])
            vals.append(val.replace("|", "/"))
            pg.append(page)
        ref = it["kics_item_ref"] if it["kics_item_ref"] is not None else (f"pl{it['pl_item_ref']}" if it.get("pl_item_ref") is not None else "")
        rows.append(f"| `{it['id']}` | {it['layer']} | {it['table']} | {' / '.join(it['labels_ja'])} | {it['ko']} | {it['unit']} | {it['parent'] or ''} | {ref} | "
                    + " | ".join(vals) + f" | {'/'.join(p for p in pg if p)} | {it['formula'] or ''} |")
    return "\n".join(rows)


def main():
    results, summary = {}, {}
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    for comp in COMPANIES:
        doc, pdf_path = open_company_pdf(comp)
        r = dict(company_jp=comp["company_jp"], company_en=comp["company_en"], sector=comp["sector"], layers=comp["layers"],
                 source_pdf=str(pdf_path.relative_to(ROOT)).replace("\\", "/"), n_pages=len(doc), as_of="2026-03-31", scope="solo", unit_disclosed="JPY_million",
                 source_url=comp.get("source_url"), source_doc_type=comp.get("source_doc_type"))
        esr = None
        if "esr" in comp["layers"]:
            esr = extract_esr(comp, doc)
            esr["checks"] = run_checks(esr)
            agg_checks, esr["aggregation_recompute"] = run_aggregation_checks(comp, esr, rules)
            esr["checks"] += agg_checks
            r["esr"] = esr
        ax = extract_axes(comp, doc)
        ax["checks"] = run_axes_checks(comp, ax, esr)
        r["axes"] = ax
        # profit layer may live in a SEPARATE pdf (comp["profit_pdf"], e.g. Meiji Yasuda's main volume).
        # Prefer the live PDF; fall back to a captured-text fixture (profit_pdf_fixture) when the PDF
        # is absent; only go NOT_ACQUIRED (profit_pages=None) if neither is available.
        pf_doc, pf_comp = doc, comp
        if comp.get("profit_pdf"):
            pf_path = SAMPLES / comp["profit_pdf"]
            fixture_path = SAMPLES / comp["profit_pdf_fixture"] if comp.get("profit_pdf_fixture") else None
            if pf_path.exists():
                pf_doc = fitz.open(str(pf_path))
            elif fixture_path and fixture_path.exists():
                with open(fixture_path, encoding="utf-8") as f:
                    pf_doc = FixtureDoc(json.load(f))
                pf_comp = {**comp, "profit_pdf_used_fixture": True}
            else:
                pf_comp = {**comp, "profit_pages": None}
        pf = extract_profit(pf_comp, pf_doc)
        pf["checks"] = run_profit_checks(pf_comp, pf) + run_profit_axes_xref(pf_comp, pf, ax)
        r["profit"] = pf
        # history layer (ticket 20260912T1440Z) — same summary5 page profit already reads for its
        # P10 cross-check, and the same doc (au: single pdf; Meiji: main-volume pf_doc/pf_comp) since
        # the 5개년표 lives next to 損益計算書, not in the 別冊.
        hist = None
        if "history" in comp["layers"]:
            hist = extract_history(pf_comp, pf_doc, ratio_raw_tokens=pf["raw_tokens"].get("pl_loss_ratio_pct"))
            hist["checks"] = run_history_checks(pf_comp, pf, hist)
            r["history"] = hist
            if comp.get("smr_from_history"):
                # MSI: the generic 旧基準 regex in extract_axes reads the wrong column of the 新基準/旧基準 pair row →
                # take FY2024 旧基準 from the history layer's per-year parse instead.
                old = (hist["values"].get("hist_smr_old_pct") or {}).get("FY2024")
                if old is not None:
                    ax["values"]["smr_old_basis_fy2024_pct"] = old
        byl = None
        if "by_line" in comp["layers"]:
            byl = extract_byline(pf_comp, pf_doc)
            byl["checks"] = run_byline_checks(pf_comp, byl, pf)
            r["by_line"] = byl
        cz = census_headline(comp["company_jp"])
        r["census"] = dict(**cz, match=(cz["esr_pct"] == esr["values"]["esr_pct"]) if esr else (cz["status"] == ax["values"]["esr_status"]))
        results[comp["key"]] = r
        all_checks = (esr["checks"] if esr else []) + ax["checks"] + pf["checks"] + (hist["checks"] if hist else []) + (byl["checks"] if byl else [])
        summary[comp["key"]] = dict(
            company_en=comp["company_en"], sector=comp["sector"], layers=comp["layers"],
            esr_pct=esr["values"]["esr_pct"] if esr else None, eligible=esr["values"]["eligible_capital"] if esr else None, required=esr["values"]["required_capital"] if esr else None,
            esr_items_matched=sum(1 for x in esr["raw_tokens"].values() if x not in ("NOT_FOUND", "NOT_IN_TEMPLATE", "ROW_OMITTED")) if esr else 0,
            esr_items_nonnull=sum(1 for x in esr["values"].values() if x is not None) if esr else 0,
            esr_items_total=len(esr["values"]) if esr else 0,
            axes_items_nonnull=sum(1 for k, x in ax["values"].items() if x is not None and not k.startswith("_")),
            profit_items_nonnull=sum(1 for x in pf["values"].values() if x is not None),
            profit_items_applicable=sum(1 for x in pf["raw_tokens"].values() if x != "N/A_SECTOR"),
            profit_items_total=len(pf["values"]),
            profit_checks_pass=sum(1 for c in pf["checks"] if c["pass"]), profit_checks_total=len(pf["checks"]),
            accounting_basis=pf["meta"]["accounting_basis"], ifrs17_applied=pf["meta"]["ifrs17_applied"],
            history_items_nonnull=(sum(1 for x in hist["values"].values() if x is not None) if hist else 0),
            history_checks_pass=(sum(1 for c in hist["checks"] if c["pass"]) if hist else 0), history_checks_total=(len(hist["checks"]) if hist else 0),
            byline_checks_pass=(sum(1 for c in byl["checks"] if c["pass"]) if byl else 0), byline_checks_total=(len(byl["checks"]) if byl else 0),
            checks_pass=sum(1 for c in all_checks if c["pass"]), checks_total=len(all_checks),
            checks_failed=[c["id"] for c in all_checks if not c["pass"] and c.get("gate", True)],
            checks_info_failed=[c["id"] for c in all_checks if not c["pass"] and not c.get("gate", True)],
            aggregation=esr["aggregation_recompute"] if esr else None,
            census_match=r["census"]["match"], calc_method=esr["method"]["calc_method"] if esr else None, esr_status=ax["values"]["esr_status"],
            air_used=ax["values"]["air_used"], interest_margin_sign=ax["values"].get("interest_margin_sign"), cat_reserve_total=ax["values"].get("cat_reserve_total"))

    schema = build_schema()
    write_lf(SCHEMA_OUT, json.dumps(schema, ensure_ascii=False, indent=2) + "\n")
    out = dict(schema_ref="J-ESR/esr_disclosure_schema.json", generated_at=str(date.today()), generator="J-ESR/extract_esr_template_samples.py",
               n_schema_items=dict(esr=sum(1 for i in schema["items"] if i["layer"] == "esr"), article_axes=sum(1 for i in schema["items"] if i["layer"] == "article_axes"),
                                   profit=sum(1 for i in schema["items"] if i["layer"] == "profit"), history=sum(1 for i in schema["items"] if i["layer"] == "history"),
                                   by_line=sum(1 for i in schema["items"] if i["layer"] == "by_line")),
               summary=summary, companies=results)
    write_lf(VALUES_OUT, json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    write_lf(MD_FRAGMENT_OUT, md_fragment(results, schema) + "\n")
    print(json.dumps(dict(n_schema_items=out["n_schema_items"], summary=summary), ensure_ascii=False, indent=2))
    for k, r in results.items():
        for c in (r.get("esr", {}).get("checks", []) + r["axes"]["checks"] + r["profit"]["checks"] + r.get("history", {}).get("checks", []) + r.get("by_line", {}).get("checks", [])):
            if not c["pass"]:
                print("FAIL" if c.get("gate", True) else "INFO", k, c)
        for iid, tk in r.get("esr", {}).get("raw_tokens", {}).items():
            if tk == "NOT_FOUND":
                print("NOT_FOUND", k, iid)
        for iid, tk in r["profit"]["raw_tokens"].items():
            if tk in ("NOT_FOUND", "NO_PAGE"):
                print("PROFIT_NOT_FOUND", k, iid, tk)
        for iid, tk in r.get("history", {}).get("raw_tokens", {}).items():
            if tk in ("NOT_FOUND", "NO_PAGE"):
                print("HISTORY_NOT_FOUND", k, iid, tk)
    ok = all(s["checks_failed"] == [] and s["census_match"] for s in summary.values())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
