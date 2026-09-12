---
from: owner
to: jp
created: 20260913T0025Z
status: resolved
route: investigate
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T1440Z
---

## 미결 (owner) — 원수(元受)·수재(受再)·출재(出再) 분해: 保険料·保険金 재보험 다리(bridge) 추출

**owner 2026-09-13.** "정미수입보험료·정미지급보험금 말고 원수(재보험 출재 전) 숫자를 따로 발라낼 수 없나?" → 디스클로저지 「保険引受の状況」(元受正味保険料·受再正味保険料·
支払再保険料·正味収入保険料 / 元受正味保険金·受再正味保険金·回収再保険金·正味支払保険金, 대개 종목별 표)에서 추출한다. 표본: `J-ESR/raw/fy2025_samples/`
au(4of5 분책 — 표가 다른 분책이면 census disclosure 페이지에서 특정, curl 1회, 막히면 미확보)·Meiji 본편 60p.

**할 일.**
1. 스키마 `layer: "profit"` 에 추가: `pl_gross_premiums_written`(元受正味保険料), `pl_assumed_premiums`(受再正味保険料), `pl_ceded_premiums`(支払再保険料),
   `pl_gross_claims_paid`(元受正味保険金), `pl_assumed_claims`(受再正味保険金), `pl_recovered_reinsurance_claims`(回収再保険金) — `{cur, prev}`, formula:
   `pl_net_premiums_written = gross + assumed − ceded`, `pl_net_claims_paid = gross_claims + assumed_claims − recovered`. 종목별(火災·海上·傷害·自動車·自賠責·その他)
   합계 표가 있으면 `pl_gross_premiums_by_line`(dict) 도 추가(선택).
2. `extract_esr_template_samples.py` 에 추출 + 검산(두 항등식 ±1 百万円, 연도 cur/prev 각각).
3. `build_jesr_detail_json.py` 는 **건드리지 않는다**(publishing 이 지금 편집 중) — `profit.items` 는 스키마 전 항목 non-null 을 자동 포함하므로 builder 재실행만으로
   화면에 전달된다(재실행은 오케스트레이터가). 단 `_meta.labels` 가 스키마에서 자동 생성되는지 확인해 답변란에 적어라.
4. 문서 §9 에 "재보험 다리" 항목·표 위치·검산 추가.

**시간 규칙.** 25분 안. python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 서브에이전트 금지, `jp/*`·builder 수정 금지, 커밋 금지, 프로세스 종료.
끝나면 답변란에 2사 다리 표(元受→受再→出再=正味, 保険料/保険金)와 검산, `status: answered`, `TODO_jp.md`(5개 유지)·`docs/changelog_jp.md`. 보고문 일본어 문자 금지.

## 답변 (jp, 2026-09-13)

원문은 두 회사 모두 이미 확보된 표본 PDF 안에 있었다(au 는 이미 쓰던 業績데이터 4of5 분책 p3~4, curl 불필요 — Meiji Yasuda 는 §9-6 에서
확보한 본편 60p p33~34). 種目별(火災/海上/傷害/自動車/自動車損害賠償責任/その他) 표의 合計 행만 읽는다.

### au損害保険 (au Non-Life) — 百万円, cur=2025年度 / prev=2024年度

| | 元受 | 受再 | 出再 | =正味(파생) | 원문 正味(실측) |
|---|---|---|---|---|---|
| 保険料 cur | 16,646 | 0(該当なし) | 8,509 | 8,137 | 8,137 |
| 保険料 prev | 17,165 | 0(該当なし) | 9,188 | 7,977 | 7,976 (±1) |
| 保険金 cur | 9,595 | 0(該当なし) | 7,655(回収) | 1,940 | 1,940 |
| 保険金 prev | 10,303 | 0(該当なし) | 8,434(回収) | 1,869 | 1,868 (±1) |

### 明治安田損害保険 (Meiji Yasuda Non-Life) — 百万円, cur=2025年度 / prev=2024年度

| | 元受 | 受再 | 出再 | =正味(파생) | 원문 正味(실측) |
|---|---|---|---|---|---|
| 保険料 cur | 16,363 | 811 | 1,482 | 15,692 | 15,692 |
| 保険料 prev | 16,086 | 688 | 1,447 | 15,327 | 15,327 |
| 保険金 cur | 4,733 | 552 | 176(回収) | 5,109 | 5,108 (±1) |
| 保険金 prev | 4,654 | 727 | 282(回収) | 5,099 | 5,098 (±1) |

**검산 P14_premium_bridge / P15_claims_bridge** (`extract_esr_template_samples.py`, ±1 百万円 tolerance, cur·prev 각각):
au 4/4 통과, Meiji Yasuda Non-Life 4/4 통과. 전체 게이트 exit 0(기존 checks 무회귀).

**스키마**: `J-ESR/esr_disclosure_schema.json` `layer:"profit"` `table:"profit:bridge"` 6항목 신설(`pl_gross_premiums_written`/
`pl_assumed_premiums`/`pl_ceded_premiums`/`pl_gross_claims_paid`/`pl_assumed_claims`/`pl_recovered_reinsurance_claims`) + 기존
`pl_net_premiums_written`/`pl_net_claims_paid` 에 formula 필드 추가. profit 층 항목 36→42.

**au 受再(수재) 표 없음**: 원문에 「③受再正味保険料 該当事項はありません」/「③受再正味保険金 該当事項はありません」 — au 는 수재계약이
없어 0 으로 채웠다(null 아님, 항등식이 0 으로 정확히 닫혀야 하므로).

**버그 1건 발견·즉시 수정**: 合計 행 탐색에 처음 `stop=heading_idx+80` 을 줬더니 `grab()` 이 라벨탐색과 값캡처 구간을 똑같이 잘라
au 保険料 두 항목이 빈 값(P14 0/0 실패)으로 나옴 — `stop` 제거로 해결(상세: 도메인 문서 §9-7).

**`_meta.labels` 자동생성 확인 (할 일 3)**: `build_jesr_detail_json.py` 는 이번 라운드에 건드리지 않았다. `build()` 함수(434~446행)가
`for it in schema["items"]: labels[it["id"]] = {...}` 로 스키마 전체를 순회해 `_meta.labels` 를 자동 채우므로, 새 6항목은 스키마에만
들어가면 **다음 빌더 재실행에서 라벨이 자동 추가**된다(수동 등재 불필요). 화면 `items`/`ratios`/`core` 뷰에 이 6개를 얹을지는 별도 판단.

산출: `J-ESR/esr_disclosure_schema.json`(42항목) · `J-ESR/extract_esr_template_samples.py`(`extract_bridge_block`/
`_bridge_row_value`/`BRIDGE_ORDER`, P14/P15) · `J-ESR/raw/fy2025_samples/extracted_sample_values.json`(재생성) ·
`docs/domains/jp_esr_disclosure_template.md` §9-7. `jp/*`·`build_jesr_detail_json.py`·서브에이전트·커밋 없음.

status: resolved

## 종결 재확인 (orchestrator 2026-09-13)

산출 확인·builder 재실행 SELF-CHECK OK. (트리: capital/risk 뿌리 재현 통과, profit_flow 검산 2건은 데이터 공백으로 false 로 정직 표기 — 스키마 밖 준비금 항목·특별이익 미공시. 다리: 2사 6항목 항등식 ±1 통과.) 같은 시각 owner 결정으로 자회사 dedup 을 껐다(SUBSIDIARY_DEDUP=False, 15사).

status: **resolved**
