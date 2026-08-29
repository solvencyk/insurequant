# -*- coding: utf-8 -*-
"""Apply the two edits instructed by inbox/parser/20260830T0700Z:
1. data/_gold/user_csm_cells.json — KR0079 2025.2Q item4/item5 값+why (was untouched).
2. data/_gold/csm_amort_identity_ledger.json — remove the 미래에셋생명보험|2025.2Q entry,
   update _population.within_identity 340->341, ledgered 6->5.
Strong asserts on old values before mutating, so a stale-context mistake fails loud
rather than silently overwriting the wrong cell.
"""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = ROOT / "data" / "_gold" / "user_csm_cells.json"
LEDGER_PATH = ROOT / "data" / "_gold" / "csm_amort_identity_ledger.json"

NEW_WHY = (
    "validation 2026-08-30 판정(inbox/validation/20260830T0400Z): 원문 배분 채택. "
    "rcept 20250814003532 반기보고서 「보험계약부채(자산)의 보험계약 구성요소별 변동분에 대한 "
    "차이조정 공시」 당반기 표(5상품×[PV,RA,CSM×3] 25열)의 행 "
    "`보험계약마진을 조정하는 변동`(ACODE "
    "ifrs-full_IncreaseDecreaseThroughChangesInEstimatesThatAdjustContractualServiceMarginInsuranceContractsLiabilityAsset) "
    "5상품 CSM 소계 합 = -68,549,585,918원 = -685.50억, "
    "행 `보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진`(ACODE "
    "ifrs-full_InsuranceRevenueContractualServiceMarginRecognisedInProfitOrLossBecauseOfTransferOfServices) "
    "= -99,207,397,518원 = -992.07억. 연결(주석 18-1)·별도(주석 5) 두 사본 동일, "
    "같은 필링 「보험손익의 변동내역/보험수익」 표 15셀 합도 99,207,397,518원으로 동일, "
    "1년 뒤 2026.2Q 반기보고서(rcept 20260814004054) 전반기 비교열도 2상품군·5상품 두 표 모두 "
    "-685.50/-992.07 (소급재작성 없음). 종전 gold(-886.27/-791.3)는 원문 어디에서도 재현되지 "
    "않았고(부분합 전수 조합 확인), owner 답지 gold/CSM waterfall_미래에셋생명*.xlsx 는 "
    "2025.1Q·2025.4Q 만 있고 2025.2Q 는 없다 — 구코드 잔차흡수값 -1677.6 을 손으로 가른 plug 로 판단. "
    "재현: scripts/_probes/probe_20260830_val_kr0079_2025q2_adjudication_sim.py"
)

# ---------------------------------------------------------------------------
# 1) gold cells
# ---------------------------------------------------------------------------
gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
s = gold["set"]

targets = {4: {"old_val": -886.27, "new_val": -685.50, "old_was": -1677.6},
           5: {"old_val": -791.3, "new_val": -992.07, "old_was": None}}

matched = {}
for i, e in enumerate(s):
    if e.get("원보험사코드") == "KR0079" and e.get("공시분기") == "2025.2Q" and e.get("항목번호") in targets:
        item = e["항목번호"]
        if item in matched:
            raise SystemExit(f"FATAL: duplicate match for item{item} at index {i} (already matched {matched[item]})")
        matched[item] = i

assert set(matched) == {4, 5}, f"expected exactly item4+item5 matches, got {matched}"

for item, idx in matched.items():
    e = s[idx]
    exp = targets[item]
    assert e["값"] == exp["old_val"], f"item{item} 값 mismatch: expected {exp['old_val']}, found {e['값']}"
    assert e["was"] == exp["old_was"], f"item{item} was mismatch: expected {exp['old_was']}, found {e['was']}"
    print(f"[gold] index {idx} item{item}: 값 {e['값']} -> {exp['new_val']}  (was={e['was']} unchanged)")
    e["값"] = exp["new_val"]
    e["why"] = NEW_WHY

GOLD_PATH.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[gold] wrote {GOLD_PATH}")

# ---------------------------------------------------------------------------
# 2) ledger
# ---------------------------------------------------------------------------
ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
key = "미래에셋생명보험|2025.2Q"
assert key in ledger["entries"], f"FATAL: {key!r} not found in ledger entries"
removed = ledger["entries"].pop(key)
print(f"[ledger] removed entry {key!r}: residual_eok={removed.get('residual_eok')} cause={removed.get('cause')}")

pop = ledger["_population"]
assert pop["within_identity"] == 340, f"expected within_identity=340, found {pop['within_identity']}"
assert pop["ledgered"] == 6, f"expected ledgered=6, found {pop['ledgered']}"
pop["within_identity"] = 341
pop["ledgered"] = 5
print(f"[ledger] _population: within_identity 340->341, ledgered 6->5 "
      f"(compared_buckets unchanged {pop['compared_buckets']})")
assert pop["within_identity"] + pop["ledgered"] == pop["compared_buckets"], "population no longer sums"

LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[ledger] wrote {LEDGER_PATH}")
print(f"[ledger] remaining entries: {sorted(ledger['entries'].keys())}")
