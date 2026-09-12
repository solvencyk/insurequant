---
from: owner
to: jp
created: 20260912T1440Z
status: resolved
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

---

## 답변 (jp, 2026-09-12)

**두 회사 모두 이미 확보된 표본 PDF 안에 5개년표가 있어 curl 이 필요 없었다** — au 는 4of5 분책(`au_nonlife_disclo_260730_4of5.pdf`) 자체의 p2 가
그 표였고, Meiji 는 `20260729_main.pdf`(60p, §9-6 에서 이미 확보) p9 가 그 표였다. profit 층이 이미 읽던 `profit_pages["summary5"]` 페이지를
재사용했을 뿐, 새 문서를 열지 않았다.

### au Non-Life (FY2021 -> FY2025, 백만엔·%)

| 항목 | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|
| 正味収入保険料 | 5,582 | 6,470 | 7,358 | 7,976 | 8,137 |
| 経常利益 | 1,334 | 1,128 | 1,637 | 1,451 | 1,654 |
| 当期純利益 | 1,273 | 728 | 1,111 | 961 | 1,171 |
| 損害率 | 30.9 | 36.4 | 26.9 | 29.4 | 31.8 |
| 事業費率 | 46.7 | 38.9 | 49.5 | 42.7 | 39.2 |
| 合算率(파생) | 77.6 | 75.3 | 76.4 | 72.1 | 71.0 |
| 総資産額 | 15,060 | 16,357 | 17,629 | 19,390 | 21,524 |
| 純資産額 | 5,805 | 6,533 | 7,644 | 8,605 | 9,776 |
| 旧基準SMR | - | - | - | - | - |
| 新基準ESR | - | - | - | - | 791.7 |

검산: H01(FY2025==profit.cur, FY2024==profit.prev) + H02(合算率 항등식) **17/17 통과**.

### Meiji Yasuda Non-Life (FY2021 -> FY2025, 백만엔·%)

| 항목 | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|
| 正味収入保険料 | 14,822 | 14,724 | 14,862 | 15,327 | 15,692 |
| 経常利益 | 1,947 | 866 | 1,078 | 1,216 | 1,594 |
| 当期純利益 | 1,147 | 450 | 709 | 777 | 1,003 |
| 損害率 | (미공시) | (미공시) | 40.2 | 38.3 | 37.7 |
| 事業費率 | (미공시) | (미공시) | 52.6 | 51.5 | 51.7 |
| 合算率 | (미공시) | (미공시) | 92.8 | 89.8 | 89.5 |
| 総資産額 | 67,732 | 66,368 | 67,909 | 62,769 | 63,763 |
| 純資産額 | 26,060 | 25,104 | 26,445 | 21,895 | 23,367 |
| 旧基準SMR | 2,847.6 | 2,940.4 | 2,814.7 | 2,642.5 | - |
| 新基準ESR | - | - | - | - | 743.2 |

손해율/사업비율/합산율은 5개년표 자체엔 없어 profit 층이 읽는 3개년표(p35)에서 FY2023~2025 만 백필, FY2021~2022 는 결측을 억지로 채우지 않고 null 로
남겼다(`raw_tokens` 에 "BACKFILL" 표시로 소스 구분 가능). 검산 **15/15 통과**.

### 구현

- 스키마: `J-ESR/esr_disclosure_schema.json` `layer:"history"` 13항목(값 10 + 생보 id 3개는 정의만) — 값은 `{"FY2021":v,...,"FY2025":v}`.
- 추출: `J-ESR/extract_esr_template_samples.py::extract_history/run_history_checks` — 새 헬퍼 `strip_paren`(괄호 안 실제 값 vs 괄호 안 대시 구분)이
  두 회사의 서로 다른 함정을 하나로 처리: Meiji 正味収入保険料 행의 괄호 대전기증감률 스킵, Meiji 단체SMR 라벨 안의 장음부호가 대시 문자와 같은
  코드포인트라 `merge_vertical` 이 라벨을 쪼개는 문제는 느슨한 부분일치 정규식으로 우회(au 무회귀 확인). 旧基準SMR/新基準ESR 은 같은 행을
  괄호 유무로 나눈다(괄호=旧基準, 없으면=新基準). exit 0.
- publishing 블록: `J-ESR/build_jesr_detail_json.py::build_history_block()` 신설, `{"fiscal_years":[...],"unit":"JPY_million","series":{"<hist_id>":[v,...]}}`
  형태로 `jp/jesr_detail.json` `companies[].history` 에 노출, `_meta.labels` 자동 포함, `self_check()` 에 같은 검산 추가 — exit 0, SELF-CHECK OK.
- 기존 esr/article_axes/profit 블록·키는 바이트 무변경(스키마 diff = 신규 항목·설명문 추가뿐). `aggregation.checks_pass/checks_total` 은 (11) 항목과
  같은 이유로 자연 증가(신규 H01/H02 가 같은 summary gate 에 합류) — 별도 조치 불필요.
- 문서 `docs/domains/jp_esr_disclosure_template.md` §0·§10 신설(표 위치·라벨 렌더링 특이점·SMR/ESR 괄호 분리·검산·회사별 편차·중간기(中間期)
  공시 메모: 일본은 연차+9월말 中間期만 법정 공시, 분기는 상장 지주 決算短信 헤드라인뿐이라 이 층은 연 1회만 갱신).
- `jp/*.html`·서브에이전트·커밋 없음. `TODO_jp.md` (14) 갱신, (10) 항목은 `docs/todo_archive_jp.md` 로 이동, `docs/changelog_jp.md` 기록 완료.

## 종결 재확인 (orchestrator 2026-09-12)

history 13항목·2사 5개년 확인(au 전 항목 5년, Meiji 손해율·사업비율·합산율은 FY2023~25만 — 원문 표에 FY2021~22 없음), builder self-check OK, 기존 블록 무변경. 다른 손보사 표 존재 여부는 별도 확인 라운드(owner 질문).

status: **resolved**
