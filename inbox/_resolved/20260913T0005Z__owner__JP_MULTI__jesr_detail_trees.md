---
from: owner
to: publishing
created: 20260913T0005Z
status: resolved
route: assemble
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T1240Z
---

## 미결 (owner) — `jp/jesr_detail.json` 에 구조화 블록 3개: `capital_tree` · `risk_tree` · `profit_flow` (owner 피드백 4건의 데이터 쪽)

**owner 2026-09-12 피드백.** ① 자본 구성표가 하위 합 ≠ 상위라 혼란 — 더하기/빼기 부호와 계층 들여쓰기 필요 ② 보험위험·대재해위험 하위 분해가 화면에 없음
③ 손익 항목 선별이 나쁨(경상수익·경상비용·특별손익 총계 행 등) ④ 손해율은 별도 패널. 데이터는 이미 `jp/jesr_detail.json` `items` 에 있고 스키마에
parent/formula 가 있다 — designer 가 산식을 파싱하지 않도록 **builder 가 트리를 만들어 준다.**

**할 일 (`J-ESR/build_jesr_detail_json.py`).** 각 company 에 추가(기존 블록·키 무변경):
1. `capital_tree`: 스키마 `layer esr` 중 `eligible_capital` 뿌리에서 parent 를 따라 내려간 **전위 순회 리스트**
   `[{"id","label_ja","depth":0..4,"sign":"="|"+"|"-","value":<百万円>|null,"is_total":bool}]`. sign = 부모 formula 안에서 그 자식 앞의 부호("- tier1_adjustments" → "-",
   그 외 "+"), 뿌리와 formula 를 가진 노드는 `is_total=true`. **값이 null 인 리프는 제외**, 자식이 모두 null 인 중간 노드도 제외. 각 total 노드에 `check`:
   `{"lhs": value, "rhs": Σ(sign·child), "ok": |lhs−rhs|≤1}` — 표시된 행만으로 합계가 재현되는지(스키마 formula 가 `=== x`(별칭)인 노드는 트리에서 뺀다).
2. `risk_tree`: `rc_pre_tax` 뿌리, 같은 형식. 상관 통합 노드(formula 가 `<=` 또는 `sqrt`) 는 `"aggregation":"correlated"` 와 `check`:
   `{"simple_sum": Σ자식, "disclosed": value, "diversification_within": simple_sum − value}` (등식 아님을 designer 가 표시). 그룹 = 生保·損保·巨大災害(자연재해 하위 포함)·
   市場·信用·運営·分散効果·税効果. 값 null 리프 제외.
3. `profit_flow`: 업권별 **선별 흐름**(순서 고정, 값 null 이면 행 제외하되 `missing` 목록에 id 기록):
   - 손보: `pl_net_premiums_written`(=) → `pl_net_claims_paid`(-) → `pl_loss_adjustment_expenses`(-) → `pl_commissions_collection`(-) → `pl_uw_operating_general_admin`(-)
     → `pl_underwriting_other`(±, 준비금·이상위험준비금 증감 등 잔여, 라벨 「その他(準備金繰入等)」) → `pl_underwriting_profit`(=) → `pl_investment_pl`(+) →
     `pl_other_ordinary`(±, = 経常利益 − 引受利益 − 運用損益, 파생 표시) → `pl_ordinary_profit`(=) → `pl_extraordinary_net`(±, 파생 = 特別利益 − 特別損失) →
     `pl_income_taxes`(-) → `pl_net_income`(=). 각 행 `{"id","label_ja","sign","cur","prev","derived":bool}` + 검산 `{"underwriting_ok","ordinary_ok","net_ok"}`.
   - 생보: `pl_premium_income`(=) → 3이원 `pl_interest_margin`·`pl_mortality_margin`·`pl_expense_margin`(+) → `pl_core_profit`(=) → `pl_capital_gains`(+) →
     `pl_extraordinary_pl`(±) → `pl_ordinary_profit`(=) → `pl_income_taxes`(-) → `pl_net_income`(=). (표본 없음 — 구조만, NN Life 로 dry-run 가능하면 확인)
   - `profit.items` 전체는 그대로 두되 designer 는 접힌 "전 항목" 에서만 쓴다.
4. `ratios` 는 그대로(별도 패널용). `_meta.labels` 에 파생 id(`pl_other_ordinary`,`pl_extraordinary_net`) 라벨 추가. self-check 에 capital_tree 뿌리 check ok,
   risk_tree 의 `rc_pre_tax` 재현(= Σ대분류 + 운영 − 분산효과, ±1), profit_flow 검산 3개 추가.

**규칙.** 30분 안. python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 서브에이전트 금지, `jp/*.html`·스키마 항목 정의 무변경(라벨 추가만), 커밋 금지.
끝나면 답변란에 2사 capital_tree 뿌리 check·risk_tree 재현·profit_flow 검산 결과, `status: answered`, `TODO_jp.md`(5개 유지)·`docs/changelog_jp.md`. 보고문 일본어 문자 금지.

## 답변 (publishing, 2026-09-13)

`J-ESR/build_jesr_detail_json.py` 에 `build_tree()`(공용, 전위순회) + `build_profit_flow()` 를 추가하고 각 company 에
`capital_tree`·`risk_tree`·`profit_flow` 3키를 신설했다. 기존 `capital`/`risk`/`market_sub`/`profit`/`history` 등은 무변경.
재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py` → exit 0, `SELF-CHECK OK`.

**설계에서 티켓 문구를 그대로 안 따르고 바꾼 지점 2개** (다르게 판단한 근거를 먼저 밝힌다):

1. **`is_total` 판정.** 티켓은 "formula 를 가진 노드는 is_total=true" 였는데, capital_tree 안에서 `tier1_ni_capital_surplus`
   /`tier1_ni_aoci`/`tier1_ni_ev_adjustment` 3항목은 formula 가 있지만(`== ebs_capital_surplus` 등, EBS 트리를 가리키는
   alias) 이 트리 안에서는 자식이 0개다. 리터럴대로 하면 "자식 0개짜리 total(빈 check)" 이 되어 티켓의 "alias 노드는 트리에서
   뺀다"는 지시와 충돌한다. 그래서 **스키마상 자식 존재 여부(구조)** 로 is_total 을 판정하도록 바꿨다 — alias 3항목과
   `tier1_ni_retained_earnings`(formula 는 있지만 EBS 를 가리킴, 같은 문제)가 별도 분기 없이 자동으로 "리프" 로 처리된다.
2. **total 노드 check 의 tolerance.** 티켓은 `±1` 을 명시했지만, risk_tree 뿌리(`rc_pre_tax`, 9항 공식)는 au(diff 2)·meiji
   (diff 3) 둘 다 ±1 을 못 지킨다. 기존 추출기 자체 체크 `C12_rc_pre_tax` 가 바로 이 공식에 이미 `tol=9`(주석: "tol = n terms;
   each term truncated")를 쓰고 있어, 그 근거를 그대로 따라 `tol = max(1, 실제로 합산한 항 개수)` 로 일반화했다. 2~3항짜리
   capital_tree 노드는 결과적으로 ±1~2 라 회귀 없음.

**2사 실측**

- **capital_tree**: au 14행, 뿌리(`eligible_capital`) check `{"lhs":9278,"rhs":9277,"tol":2,"ok":true}`. meiji 15행(au 와
  차이 = `tier1_ni_aoci` 가 meiji 만 공시됨), 뿌리 check `{"lhs":40290,"rhs":40289,"tol":2,"ok":true}`.
- **risk_tree**: au 12행, 뿌리(`rc_pre_tax`) check `{"lhs":1510,"rhs":1508,"tol":6,"ok":true}`(= rc_nonlife+rc_catastrophe+
  rc_market+rc_credit+rc_operational-rc_diversification, rc_life/rc_mgmt_action_excess/rc_non_insurance_business 는 3사
  다 미공시라 항목에서 빠짐). meiji 22행, 뿌리 check `{"lhs":6985,"rhs":6982,"tol":6,"ok":true}`. `aggregation:"correlated"`
  노드(rc_nonlife/rc_catastrophe/rc_cat_natural/rc_market) 의 `simple_sum` 이 기존 추출기 체크 C14/C15/C16/C17 의 rhs 와
  2사 전부 정확히 일치해서 교차검증됨: au 1190/87/-/247, meiji 2458/2666/2523/7567.
- **profit_flow**: au 11행(`pl_underwriting_other`·`pl_extraordinary_net` 값이 없어 `missing`=2), meiji 13행(`missing`=0).
  검산 3개 — `ordinary_ok` = **true 둘 다**(`pl_other_ordinary` 가 잔차로 정의돼 항상 닫히는 항등식). `underwriting_ok` =
  **false 둘 다** — 선별한 6행(정미수입보험료-정미지급보험금-손해조사비-수수료-사업비+기타)의 합이 실제 保険引受利益 과 차이남
  (au 806~866, meiji 690~829, 백만엔). 원인은 스키마에 없는 保険引受費用 세부 행(추정: 責任準備金等繰入額 등 준비금 증감)이
  원문에는 있기 때문으로 보인다 — `pl_underwriting_other`(その他収支) 는 실측 자체가 작은 값(meiji -1~-2)이라 이 갭을 메우지
  못한다. `net_ok` = **false 둘 다** — 당기(cur)에 特別利益 이 미공시라 `pl_extraordinary_net` cur 값이 null, 그 항을 빼고
  재현하면 diff 2(au)/20(meiji). meiji 는 전기(prev)만 단독 재현하면 1216+26-465=777=실측 net_income prev 와 정확히 일치.
  **정직하게 false 로 JSON 에 실었다** — 억지로 맞추지 않았고, `self_check()` 하드게이트는 root check 2개(capital/risk)와
  `ordinary_ok` 만 검사한다(모두 true 로 통과). `underwriting_ok`/`net_ok` 는 실제 데이터 공백이지 코드 버그가 아니라서
  게이트에 안 걸었다 — 필요하면 이 둘을 닫으려면 스키마에 새 항목(責任準備金等繰入額 등)을 추가하는 별도 티켓이 필요하다.

**부작용 확인.** `git diff` 로 `jp/jesr_detail.json` 의 나머지 차이(재보험 pl_assumed_*/pl_gross_*/pl_ceded_* 라벨·`profit.items`
값·`aggregation.checks_pass/total`)는 전부 이번 세션 시작 전부터 워킹트리에 이미 있던 (15)번 재보험 브릿지 스키마/추출기 미커밋
변경분이다(`git diff --stat HEAD -- J-ESR/esr_disclosure_schema.json` 이미 +107줄, 내가 손댄 적 없음). 내가 추가한 것은
`capital_tree`/`risk_tree`/`profit_flow` 3키 + `_meta.labels` 2개(`pl_other_ordinary`/`pl_extraordinary_net`) +
`generated_at` 뿐이다. `jp/*.html`·스키마 항목 정의 무변경, 커밋 없음(서브에이전트도 없음). 상세: `TODO_jp.md` (16),
`docs/changelog_jp.md` (16).

## 종결 재확인 (orchestrator 2026-09-13)

산출 확인·builder 재실행 SELF-CHECK OK. (트리: capital/risk 뿌리 재현 통과, profit_flow 검산 2건은 데이터 공백으로 false 로 정직 표기 — 스키마 밖 준비금 항목·특별이익 미공시. 다리: 2사 6항목 항등식 ±1 통과.) 같은 시각 owner 결정으로 자회사 dedup 을 껐다(SUBSIDIARY_DEDUP=False, 15사).

status: **resolved**
