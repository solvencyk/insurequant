---
from: owner
to: jp
created: 20260912T1440Z
status: open
route: investigate
company: JP_MULTI
period: FY2021-FY2025
track: J-ESR
supersedes: 20260912T1150Z
---

## 미결 (owner) — 손보 「主要な経営指標等の推移」 5개년 시계열(손해율·사업비율·합산율·正味収入保険料·当期純利益 등) 추출 → 상세 JSON `history`

**owner 2026-09-12.** "손해율·사업비율·합산비율 시계열을 쭉 보여줘도 좋겠다. 당기/전기만 있어 허전하다." 디스클로저지 본편의 「主要な経営指標等の推移」
표(보통 5사업연도)를 쓴다. 표본: `J-ESR/raw/fy2025_samples/au_nonlife_disclo_260730_4of5.pdf`(별책이면 본편 필요 여부 확인 — au 는 4of5 분책이라 지표 표가
다른 분책에 있을 수 있음: 그 경우 census 의 au disclosure 페이지에서 해당 분책 URL 을 특정해 curl(막히면 미확보)), `meijiyasuda_nonlife_20260729_main.pdf`(본편 60p).

**할 일.**
1. 스키마 `J-ESR/esr_disclosure_schema.json` 에 `layer: "history"` 항목: `hist_net_premiums_written`, `hist_net_income`, `hist_ordinary_profit`,
   `hist_loss_ratio_pct`, `hist_expense_ratio_pct`, `hist_combined_ratio_pct`, `hist_total_assets`, `hist_net_assets`, `hist_smr_old_pct`(구기준 SMR, 있으면),
   `hist_esr_pct`(신기준, FY2025 부터) — 각 항목은 `{"FY2021": v, ..., "FY2025": v}` 형태(사업연도 키). 생보용(`hist_core_profit`, `hist_premium_income`,
   `hist_policy_reserves`)은 id 만 정의.
2. `J-ESR/extract_esr_template_samples.py` 에 history 추출 추가(2사), 검산: FY2025 값 == profit 층 cur, FY2024 == prev, 合算率 = 損害率+事業費率(각 연도 ±0.1).
3. `J-ESR/build_jesr_detail_json.py` 에 `history` 블록 추가: `{"unit":"JPY_million","fiscal_years":["FY2021",...,"FY2025"],"series":{"<hist_id>":[v,...]}}`
   + `_meta.labels` 에 hist 라벨. self-check 에 위 검산. 기존 블록·키 무변경.
4. 문서 `docs/domains/jp_esr_disclosure_template.md` §10 "시계열 층"(표 위치·연도 수·회사별 편차·중간기 공시 존재 여부 메모: 일본은 연차+中間期(9월말)만 법정,
   분기는 상장 지주 결산단신 헤드라인만).

**시간 규칙.** 30분 안. 네트워크는 curl 1회 시도, 막히면 미확보로 표기하고 있는 표본으로 끝낸다. python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음,
서브에이전트 금지, `jp/*.html` 수정 금지(designer 가 작업 중), 커밋 금지. 끝나면 답변란에 2사 5년 표(합산율 등) 요약, `status: answered`, `TODO_jp.md`
(Status 5개 유지)·`docs/changelog_jp.md`. 보고문 일본어 문자 금지.
