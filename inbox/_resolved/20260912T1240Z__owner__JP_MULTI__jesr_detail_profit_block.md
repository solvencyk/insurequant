---
from: owner
to: publishing
created: 20260912T1240Z
status: resolved
route: assemble
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T1120Z
---

## 미결 (owner) — `jp/jesr_detail.json` 에 `profit` 블록(손익 층) 추가

**배경.** owner 2026-09-12 "당기순이익 breakdown 도 보고 싶다". jp-collector 가 스키마 `layer: "profit"` 36항목과 표본 추출을 끝냈다
(`inbox/_resolved/20260912T1150Z__owner__JP_MULTI__profit_layer_schema.md`, 블록 형식 제안은 `docs/domains/jp_esr_disclosure_template.md` §9-5).
표본값은 `J-ESR/raw/fy2025_samples/extracted_sample_values.json` 의 각 회사 `profit` 층.

**할 일.** `J-ESR/build_jesr_detail_json.py` 확장 → 각 company 에 `"profit"` 블록:
```json
"profit": {
  "accounting_basis": "jgaap|ifrs|unstated", "ifrs17_applied": true|false|"unstated", "evidence": "...", "source_doc": "...",
  "unit": "JPY_million", "items": { "<pl_id>": {"cur": 1234, "prev": 1100} , ... },   // non-null 만, prev 없으면 null
  "ratios": { "pl_loss_ratio_pct": {...}, "pl_expense_ratio_pct": {...}, "pl_combined_ratio_pct": {...} },   // 손보만
  "core": { "pl_core_profit": {...}, "pl_interest_margin": {...}, "pl_mortality_margin": {...}, "pl_expense_margin": {...} },  // 생보만
  "status": "extracted|not_obtained"    // Meiji Yasuda 본편 미확보면 not_obtained + items 빈 객체
}
```
`_meta.labels` 에 profit 층 id 라벨(ja/ko/unit/pl_item_ref) 추가. self-check: au 는 `pl_ordinary_profit`·`pl_net_income` 존재, 손보 `合算率 =
損害率 + 事業費率`(±0.1), Meiji 는 status 만. 다른 블록·키는 무변경(designer 계약). `J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260729_main.pdf`
가 생겨 있으면(오케스트레이터 백그라운드 재시도) 먼저 `extract_esr_template_samples.py` 를 다시 돌려 Meiji profit 을 채운다.

**규칙.** python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 서브에이전트 금지. `jp/*.html`·`J-ESR/esr_disclosure_schema.json`·루트
마스터 수정 금지(designer 가 jp HTML 작업 중). 끝나면 답변란에 au profit 요약(経常利益·当期純利益·合算率)과 self-check 로그, `status: answered`,
`TODO_jp.md`·`docs/changelog_jp.md` 갱신. 보고문 일본어 문자 금지.

## 답변 (publishing)

`meijiyasuda_nonlife_20260729_main.pdf` 는 이번에도 로컬에 없어서(`J-ESR/raw/fy2025_samples/` 확인) 추출기 재실행은 생략하고
기존 `extracted_sample_values.json`(Meiji profit 전부 null, 사유 텍스트 그대로)을 그대로 사용했습니다.

`J-ESR/build_jesr_detail_json.py` 에 `build_profit_block()` 을 추가해 스키마 그대로(값 변경 없음) 조립했습니다. 티켓 예시의
`core` 는 4개 id 만 나열돼 있었지만, 그 4개가 스키마 `table` 태그 `profit:core`(基礎利益)·`profit:three`(三利源) 두 테이블의
교집합 절반과 정확히 겹쳐서, 태그 기준으로 일반화했습니다(`profit:core` 의 나머지 2개 `pl_capital_gains`/`pl_extraordinary_pl`
도 같은 그룹으로 포함). 10월 62사가 三利源 표기를 다르게 공시해도 코드 수정 없이 맞물리도록 하려는 판단이며, 값이 늘어난 것뿐
다른 필드는 티켓 그대로입니다. 이 판단이 의도와 다르면 알려주시면 바로 좁히겠습니다.

**au_nonlife profit 요약** (au_nonlife_disclo_260730_4of5.pdf, jgaap / IFRS17 미적용):
- 経常利益(pl_ordinary_profit): 당기 1,654 / 전기 1,451 (百万円)
- 当期純利益(pl_net_income): 당기 1,171 / 전기 961
- 合算率(pl_combined_ratio_pct): 당기 71.1(=손해율 31.8+사업비율 39.2) / 전기 72.1(=29.4+42.7) — 둘 다 오차 0.1 이내
- meijiyasuda_nonlife: status="not_obtained", items/ratios/core 전부 `{}`, source_doc 에 NOT_ACQUIRED 사유 그대로 유지.

**self-check 로그** (재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`):
```
wrote .../jp/jesr_detail.json -- companies=2
  au_nonlife: esr_pct=791.7 eligible=9278 required=1171 reproduced=True checks=62/62
    profit: status=extracted accounting_basis=jgaap ifrs17_applied=False pl_ordinary_profit={'cur': 1654, 'prev': 1451} pl_net_income={'cur': 1171, 'prev': 961} combined_ratio={'cur': 71.1, 'prev': 72.1}
  meijiyasuda_nonlife: esr_pct=743.2 eligible=40290 required=5420 reproduced=True checks=50/52
    profit: status=not_obtained accounting_basis=unstated ifrs17_applied=unstated pl_ordinary_profit=None pl_net_income=None combined_ratio=None
SELF-CHECK OK
EXIT=0
```
self-check 는 au `pl_ordinary_profit`/`pl_net_income` 존재, 손보 合算率=損害率+事業費率(±0.1, cur·prev 각각), meiji
status=="not_obtained"+items=={}, profit 하위 모든 id 가 `_meta.labels` 존재 여부(라벨 137→173)를 전부 통과했습니다.

`git diff jp/jesr_detail.json` 로 부작용 확인: `generated_at` 갱신과 신규 `profit`/`pl_item_ref` 필드 외 유일한 변화는
`aggregation.checks_pass/checks_total` 이 43/43→62/62(au)·49/51→50/52(meiji) 로 늘어난 것인데, 이번 코드 변경이 아니라
입력 `extracted_sample_values.json` 이 이전 (10) 라운드에서 이미 profit 검산을 포함하도록 갱신돼 있었고 `aggregation`
필드가 원래 회사 전체 검산 요약을 읽는 로직이었기 때문입니다. headline/risk/market_sub/capital/axes/sensitivity 등
다른 블록은 바이트 무변경입니다. BOM 없음·`ast.parse` 통과 확인했습니다. `jp/*.html`·`esr_disclosure_schema.json`·루트
마스터는 미접촉이며, 같은 워크트리에서 designer 세션이 `jp/index.html`·`jp/jesr.html` 을 동시 수정 중인 것을 `git status`
로 확인하고 손대지 않았습니다.

`TODO_jp.md`(11) · `docs/changelog_jp.md`(11) 갱신했습니다. 커밋은 하지 않았습니다(오케스트레이터가 묶어서 처리).

## 종결 재확인 (orchestrator 2026-09-12)

검수 완료: terms.html 핵심 조항(有料サービス留保·編集著作物/DB 권리·準拠法·運営者·内部トラフィック·誤り報告) 확인, CSP connect-src 에 script.google.com/googleusercontent 포함, NEW_FILES 7개, 팝업 모바일 스크린샷 정상, BOM 없음. profit 블록은 au 확정(経常利益 1,654·当期純利益 1,171·合算率 71.1), Meiji 는 본편 확보 후 재빌드 예정(별도 jp-collector 진행 중). owner 확인 항목(運営者 표기·準拠法·GA 보유기간·施行日)은 owner 에게 전달.

status: **resolved**
