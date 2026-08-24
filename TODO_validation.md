# Insurequant Validation TODO (Stage 3)

> Last updated: 2026-08-24 (iter-3 룰 수정·면제 해제·inbox 전건 종결) · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Changelog: docs/changelog_validation.md

Session start: read this file + `claude-agent-validation.md` + domain refs (`docs/domains/claude-agent-{kics,ifrs17}.md`). English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

**(2026-08-24 iter-3, 룰 수정 + 면제 해제 + inbox 전건 종결) 🟢 `item47` 스코프 결함을 고쳤다 —
전 버킷 시뮬 **해결 1 / 파손 0**. 한화생명 면제 **해제**, 게이트 3종 전부 exit 0, inbox **활성 0건**.**

> **① 룰 수정 — 발행사 모순이 아니라 우리 룰의 결함이었다.** `item47`(보완자본 한도 적용 전)의
> 스코프가 발행사마다 다르다(한화생명 2025.2Q p18 = `item49` 포함 / IBK연금 2025.3Q p16 = 제외).
> 룰은 한 관행만 알아서 포함 관행 회사의 **한도 구속 분기**에 한도초과액을 `item49` 만큼 과대계산했고,
> 그 값이 다리에 들어가 KR0068 2025.2Q 를 −30,095 로 만들었다. **스코프는 회사 하드코딩 리스트가
> 아니라 그 회사 자신의 결정적 버킷 투표**로 정한다(`_tier2_i47_scope_map`). 갈래 4 → 6
> (`I49_IN_I47_CAPPED` / `I49_IN_I47_UNCAPPED`, **기존 이름의 접두사가 아니게** 지었다 — 게이트가
> `"branch=CAPPED" in detail` 부분문자열로 갈래를 읽어서 `CAPPED_INCL` 로 지으면 두 갈래가 뭉개진다).
>
> **시뮬을 룰엔진 전층으로 다시 쟀다** — 종전 시뮬은 다리만 재구현해서 갈래를 공유하는 축 B·F 의
> 부수효과를 못 봤다. `run_validation` 산출 전체 대조(`probe_20260824_findings_snapshot.py`):
> **새로 닫힘 1 · 새로 깨짐 0 · findings 총계 13,664 불변 · RED 38→37 · GREEN 9,521→9,522.**
> 시뮬 도중 **은닉 필터를 실제로 밟았다** — 갈래만 만들고 `raw_exc = excess if branch in
> ("CAPPED","BOTH")` 를 안 고쳐서 새 갈래가 조용히 초과액 0 이 됐다. 상수(`_TIER2_EXCESS_BEARING_
> BRANCHES`)로 빼고 시험으로 못 박았다.
>
> **② 면제 정리.** KR0068 2025.2Q **해제**(게이트가 `TIER2_EXEMPTION_INERT` 로 먼저 알려 줬다,
> 다리 잔차 0.26). 원장 기록은 지우지 않고 `status=CONTRADICTED` 로 남겨 **재등재 시 즉시 RED**.
> KR0075 3버킷은 해제가 아니라 **박제잔차 6개 갱신**(−221/−242 → +14.86/+87.22 …) — 마스터 셀은
> 한 칸도 안 움직였고 룰의 기대식만 바뀌었다. 새 값이 **다리 잔차와 수렴**하는 것이 방증
> (구성 +14.86 vs 다리 +15). 종전 값은 `expected_residual_alt_reading` 에 사유와 함께 보존.
> 면제를 지탱하던 시험 6건은 **지우지 않고 이전·fixture 화**했다(삭제 이유를 코드에 명시 —
> `VERIFIED_BY_OWNER` 배선은 살아 있어야 다음 owner 판단 면제 때 썩어 있지 않다).
> 골든 `--update` 재생성, 사유는 `test_kics_rules_golden.py` `_what` **5차** 항목.
>
> **③ `SOURCE_UNREADABLE_NOT_VERIFIED` YELLOW 20건을 근거 원장으로 판정 전환.** 매 라운드 같은
> 20줄을 찍고 아무도 안 보는 상태였다. `data/_gold/kics_source_vision_verified.json` 신설 +
> `validate_data_contract.py` 배선: 필수필드 결손 RED · 박제셀 결측 RED · **주장(적용후=적용전)
> 붕괴 RED** · 값 드리프트 YELLOW · 통과해도 **매 실행 인쇄**(`SOURCE_VISION_VERIFIED`) · 무용해지면
> `SOURCE_VISION_INERT`. 원장이 사라지면 조용히 통과가 아니라 종전 YELLOW 로 되돌아간다.
> 변이시험 23건(`tests/test_source_vision_verified.py`).
> **줄 수는 그대로 20 이다 — 침묵시킨 게 아니다.** 이제 진짜 미판독이 생기면
> `SOURCE_UNREADABLE_NOT_VERIFIED` 가 0 에서 튄다.
>
> **④ recipient 답변을 그대로 받지 않았다.** 4개 회사 각 1분기(TFI=O·X·UNKNOWN 전부 포함)를 직접
> 렌더링해 재현했고, 10쌍 전수로 **기계적 필요조건**(item1·14·15·17·19·27 60칸이 전부 전==후,
> 지급여력비율 소수 8자리까지 동일)을 따로 걸었다. **답변의 진단 한 줄은 반증했다** — "대상 페이지는
> 읽히는데 문서 평균 때문에 UNREADABLE 로 찍힌다" 는 틀렸다(인용 페이지가 문서 평균보다 **더**
> 안 읽힌다: 34.0 vs 68.9 · 2.0 vs 5.8 · 0.0 vs 1.2 자/p). 그 제안대로 사이드카를 대상 페이지
> 기준으로 바꾸면 YELLOW 가 준다가 아니라 **는다.**
>
> **⑤ 사고 기록.** `docs/postmortems/PM-2026-08-24_i47_scope_misread.md` 신설(5칸 = `closed`) +
> 색인·UH 표 갱신. 신규 **UH-9**(회사 단위 스코프 투표는 관행이 시간에 따라 바뀌는 발행사를 못
> 담는다 — KB손해가 2025.2Q 에 INCL→EXCL). **분기 단위 판정은 만들지 않았다** — 측정된 이득 0
> (전수 시뮬 status 전이 0건), UH-5 선례(오탐억제를 설계할 수 없으면 배선하지 않는다).
>
> **⑥ 게이트 실측(재현 명령은 각 티켓 §7/§4).**
> `validate_kics_disclosure.py` **exit 0**(RED=37 · blocking RED=0) ·
> `validate_data_contract.py` **exit 0**(RED=0 · YELLOW=296) ·
> `pytest tests/ -q --ignore=tests/test_pl_breakdown_golden.py --ignore=tests/test_ifrs17_bs_golden.py`
> **343 passed, 1 skipped**(직전 318). `kics_disclosure.json`·`insurequant_master_tables.xlsx`
> **읽기만 했다.**
>
> **⑦ 범위 밖 발견 1건(수정 안 함).** `validate_data_contract.py --selftest` 가 **50/51**
> — `N6 EXEMPTION_LEDGER_SCHEMA_INVALID` 케이스가 실패한다. HEAD 로 되돌려도 재현되므로
> **이번 라운드 이전부터 깨져 있었다.** 게이트 자신의 자기시험이 조용히 실패 중인 상태라
> 별도 티켓으로 분리했다.
>
> 종결: `inbox/_resolved/20260824T0410Z__validation__KR0068_2025.2Q__…` ·
> `inbox/_resolved/20260821T0620Z__validation__MULTI__meta_rules_wired_axis_and_provenance.md`.
> 인보 위생 검사 **활성 0 · 위반 0**.


**(2026-08-24 iter-2, KR0068 한화생명 2025.2Q 인과 규명) 🟢 `2_tier1_bridge` 잔차 −30,095 의
원인은 **발행사 모순이 아니라 우리 룰의 결함**이었다. `item47`(보완자본 한도 적용 전)의 스코프가
발행사마다 다르다 — 한화생명은 `item49`(해약환급금 초과분)를 **포함**해 인쇄하고 한도는 나머지
채무성 부분에만 걸리는데, 룰은 `한도초과 = max(0, item47 − item48)` 로 `item49` 만큼 과대계산한다.
raw 3분기 + EXCL 대조군(IBK연금 2025.3Q) 실측으로 확증. 스코프 인식 시뮬레이션 = **1 fix / 0 break**.
**룰은 안 고쳤다** — 골든이 라이브 마스터에 물려 있고 다른 세션이 그 마스터를 만지는 중이라
lost-update 위험. 면제도 **해제하지 않고 사유만 정정**(해제하면 RED → push 차단). 게이트 exit 0,
RED 카운트 무변화, 142 tests pass. 상세·재현·후속 착수조건:
`inbox/validation/20260824T0410Z__validation__KR0068_2025.2Q__tier1_bridge_residual_unexplained.md` §답변 iter-2.**

**(2026-08-24 3차, inbox 잔여 6건 정리) 🟢 서브에이전트 4개 529 과부하로 소실 → 직접
재확인. 3건 resolved(csm_waterfall 게이트 배선·item52/54 카카오페이 fix·메타룰 항목1/2)
· 3건 open 유지(viz 패널 3종 단위분열 / leaf residual 4셀 / 한화생명 인과) → 2026.2Q
서브에이전트 배정 예정, 상세는 `docs/changelog_validation.md` 이 날짜 항목.
가설 5연속 오답 경위 + 재발방지 규율은 `docs/agents/claude-agent-validation.md` §3.1 신설.**

**(2026-08-24 2차 owner 위임) 🟢 면제 4건 등재 — blocking RED 29 → 19. 남은 19 중 18 은 parser
발주분(`inbox/parser/20260824T0400Z`), 1 은 NH농협 2024.3Q 미조사.**

| 버킷 | 축 | 박제 잔차 | 계열 |
|---|---|---|---|
| KR0004 예별손해 2025.1Q | `3_tier2_composition` | +997.00 | ① 두 표가 tier 분할만 다르게 인쇄 |
| KR0003 롯데손해 2023.1Q | `2_tier1_bridge` · `3_tier2_composition` · `50_tfi_tier_split` | +19.00 / −19.00 / −18.00 | ① 두 표가 다른 값 + TFI 적용전만 안 닫힘 |
| KR0075 BNP카디프 2024.3Q | `2_tier1_bridge` · `3_tier2_composition` · `47_tier2_census`(전·후) · `51_tfi_tier2_composition` | +15.00 / −220.98 / census 2 / −221.31 | ② 표가 자기 구성행과 안 닫힘 |
| **KR0068 한화생명 2025.2Q** | `2_tier1_bridge` | **−30,095.00** ⚠️ | ~~④ 인과 미규명~~ → **2026-08-24 iter-2 규명: 우리 룰의 `item47` 스코프 오독. 룰 수정 대기** |

> **앞의 세 건은 새 조사가 아니다.** iter-6·iter-7 에 raw 확증을 이미 끝내 놓고 "owner 위임 목록
> 밖" 이라는 이유만으로 등재하지 않았던 것들이다(면제를 스스로 넓히지 않는다는 원칙). 이번에
> 위임돼서 등재만 했다. 값은 티켓에서 베끼지 않고 raw 를 다시 열어 독립 재현했고 전부 일치했다.
>
> **⚠️ 한화생명은 성격이 다르다 — 박제값이 발주된 숫자와 다르다.** owner 에게 제시된 잔차는
> **826.00**(각주 괄호 "보완자본 한도 초과액 제외" 를 무시한 읽기: `213,475 − 30,921 − 100,874
> = 81,680` vs `82,506`)인데, **룰이 실제로 emit 하는 diff 는 −30,095.00** 이다(`branch=CAPPED`:
> 한도초과 = `min(item47−item48, item12)` = `min(70,821.29, 30,921)` = 30,921 로 클램프 →
> `213,475 − 0 − 100,874 = 112,601`). 같은 축의 같은 불일치를 각주 해석 둘로 잰 값이다.
> **박제는 룰이 내는 값이어야 재검산이 성립한다** — 826 을 박으면 등재 즉시
> `TIER2_EXEMPTION_RESIDUAL_DRIFT` RED 라 면제가 아예 성립하지 않는다(실측 확인). 두 값을 원장에
> **둘 다** 적었고(`expected_residual` / `expected_residual_alt_reading`) 테스트가 강제한다 —
> 안 적으면 다음 세션이 "박제값이 발주와 다르다" 로 읽고 826 으로 고치거나 허용오차를 건드린다.
>
> **한화생명은 인과가 규명되지 않았다.** 원장 status 를 새로 만든 `VERIFIED_BY_OWNER` 로 갈랐다 —
> ①~③처럼 산수로 증명한 것이 아니라 owner 가 raw 를 직접 보고 "원문대로 오차 용인" 을 결정한
> 것이기 때문이다. 게이트는 ⓐ **VERIFIED 와 동일한 마커 검사를 그대로 걸고**(owner 판단이 숫자
> 재확인을 면제하지 않는다) ⓑ `owner_confirmation`{read_by, date, what_was_read, verdict} 를
> 요구하며(누락시 `EXEMPTION_OWNER_RECORD_INCOMPLETE` RED) ⓒ **매 실행**
> `EXEMPTION_STANDS_ON_OWNER_JUDGEMENT` review 로 인쇄한다. 조용해지면 다음 세션이 '증명된 것'
> 으로 오독한다. 후속 티켓 `inbox/validation/20260824T0410Z` 는 **열어 둔다** — 면제는 push 를
> 푼 것이지 원인을 닫은 것이 아니다. 미규명 단서(item51 후−전 = 825.75 ≈ 826)는 **사유가 아니라
> 해제조건 메모**로만 적었다.
>
> **삼성화재 2025.3Q 는 등재하지 않았다** — owner 가 "우리가 고친다" 로 결정해 parser 가 정정
> 중이다. 고쳐지면 그 축이 저절로 닫히는데 면제를 박아 두면 죽은 핀이 남는다(지난 라운드에
> 롯데 2026.1Q 죽은 핀을 `TIER2_EXEMPTION_INERT` 로 잡아냈던 그 형태).
> **NH농협 2024.3Q 도 등재하지 않았다** — 미조사다. 조사 전 등재는 근거가 아니라 추측이다.
>
> 재현: `validate_kics_disclosure.py` exit 2 / RED=56 / **blocking RED=19** ·
> `validate_data_contract.py` **RED=5**(전부 parser 발주분) · `pytest tests/ -q
> --ignore=tests/test_pl_breakdown_golden.py --ignore=tests/test_ifrs17_bs_golden.py`
> → **318 passed, 1 skipped**(직전 302). **골든 무변경** — 룰 엔진을 안 건드렸다(면제는 findings
> 매트릭스 밖의 층이다). `kics_disclosure.json` · `insurequant_master_tables.xlsx` **읽기만 했다.**

**(2026-08-24 iter-7) 🟢 item52/53/54 배선 완료 — 축 E 등식 승격 · 축 G 신설 · 항목번호 등록부.
blocking RED 13 → 29 (신규 18 은 전부 raw 확정 결함, parser 발주).**
> **RED 를 0 으로 만들지 않았다. 늘렸다.** parser iter-10 이 1,291셀(item52/53/54)을 실었는데 그
> 항목을 보는 룰이 하나도 없었다 — `test_rule_coverage_manifest.py` 가 즉시 잡았다(설계대로).
> 배선하자 **GREEN 이던 18칸이 RED 로 뒤집혔다.** 전부 raw PDF 로 원인을 확정했다.
>
> **① 축 E 등식 승격.** `50_tfi_tier_split{,_post}` 의 comparand 를 `item1`(헤드라인)/범위검사에서
> **`item52`(같은 표·같은 컬럼 지급여력금액 행)** 로 바꿨다. 적용전·적용후 둘 다 같은 식이 되어
> 이 축이 처음으로 대칭이 됐다. **열려 있던 YELLOW 70칸 중 69칸이 등식으로 닫혔다**(1칸은 item52
> 결측 → 폴백 유지). 그리고 **GREEN 379 중 6칸이 RED 로 뒤집혔다** — 카카오페이 5버킷 item52 가
> **100배**(로더의 `ALL_ZERO_TRIVIAL` 스케일 단축: 47/48/49/51 이 전부 대시라 "스케일 무관"으로
> 판정했는데 같은 표의 item52 는 0 이 아니었다. 같은 버킷 item50 은 다른 로더가 실어서 정확 —
> **한 버킷 안에서 두 로더가 다른 배율을 썼다**) + 삼성화재 2025.3Q 적용후 발행사 자릿수 전치.
> **종전 comparand 로는 구조적으로 못 보는 오류였다** — 승격의 값어치는 닫힌 69칸이 아니라 이 6칸이다.
>
> **② NH농협 2025.4Q 등재 — iter-6 의 내 판단이 틀렸다.** 그때 "표가 실제로는 닫힌다 = 우리 식에
> 항이 빠진 것" 이라며 등재를 거부하고 item54 를 발주했다. 값이 온 뒤 전수 시뮬이 그 계획을
> 반증했다: `item51 == min(47,48)+49+item54` 를 강제하면 **새로 닫힘 1 · 새로 깨짐 218**(대다수
> 회사는 item47 이 이미 후순위채무를 포함). 공통식이 아니라 이 발행사의 표 구성 관행이다 →
> 공식은 그대로 두고 잔차 박제형 면제(949.47 / 949.59). **해제조건을 배선했다** — item54 를 박제
> 셀에 넣었으므로 그 값이 움직이거나 결측이 되면 `TIER2_EXEMPTION_INPUT_DRIFT` RED 로 자동 해제.
>
> **③ 축 G `53_tfi_memo_rows{,_post}` 신설.** 메모행은 항등식의 항이 아니라 census(적용전) + 부호 +
> `53+54 ≤ item51` 포함관계로 건다. **적용후 census 는 일부러 안 걸었다** — 원문이 메모행을 적용전
> 칸에만 인쇄한다(적용후에 값이 있는 버킷 60/450). 걸면 376칸이 오탐이다. 적용후 미러는 부호·포함
> 관계이고 변이시험이 양 컬럼 발화를 증명한다. **포함관계 후보 둘이 raw 로 반증됐다** —
> `≤ item47`(DB생명 2025.2Q 가 `한도적용전 300,748 < 후순위채무 301,919` 을 그대로 인쇄, 4분기 연속) ·
> `≤ item52`(푸본현대 2025.3Q 는 자본잠식이라 지급여력금액 387억 < 후순위채무 3,522억).
> **"인접분기 동일값 = stale" 은 안 걸었다** — 53/54 는 잔액(stock)이라 여러 분기 동일이 정상이다
> (메리츠화재 12분기 2,850.00 · 교보생명 12분기 11,088.99). 유량 검사를 저량에 걸면 오탐 공장이 된다.
> census 결측 사유는 셋으로 갈랐다: 발행사 공란(raw 판독 등재분 12칸) / 스캐너 미판독(20버킷 backlog)
> / **그 외 전부 RED**.
>
> **④ 항목번호 등록부 신설 — `data/_gold/kics_item_registry.json`.** 오늘 두 레인이 52 를 동시에
> 잡았고 게이트가 **우연히** 잡았다(예약이 룰 주석과 TODO 산문에만 있었다). 47~54 만 등재하고
> 1~46 은 `unregistered_ranges` 로 명시적 미등재 선언 — 완결성이 아니라 다음 충돌 차단이 목적이다.
> `tests/test_kics_item_registry.py` 5건이 강제한다(특히 **`reserved` 번호에 데이터가 들어오면
> 실패** — 오늘의 사고 경로를 정확히 막는다).
>
> **⑤ 남은 RED.** 한화생명 2025.2Q = RED 유지 + 후속 티켓 분리
> (`inbox/validation/20260824T0410Z`). 825.75 ≈ 826 은 인과가 아니다 — 잔차가 −30,095 인데 826 을
> 근거로 대면 숫자부터 안 맞는다. 예별손해 2025.1Q = **발행사 자기모순 확정**(두 표의 합계는 같은데
> tier 분할만 다르다, raw 두 표 직접 대조) → 면제 초안 완성, **owner 승인 전이라 RED 유지**.
>
> **부수: 롯데 2026.1Q 면제 핀 2개 제거.** 승격 후 그 버킷이 축 E 에서 정확히 닫힌다(재게시된 전기
> 표는 자기 안에서는 일관되다). 게이트가 `TIER2_EXEMPTION_INERT` 로 먼저 알려 줬다. 재게시 사실은
> `3_tier2_composition`·`TIER2_LIMIT_STALE` 이 그대로 잡으므로 사각 없음. **죽은 핀을 남기면 다음
> 세션이 "그 축도 면제돼 있다"고 잘못 읽는다.**
>
> `pytest tests/ -q --ignore=...` **302 passed, 1 skipped**(직전 284 passed · 1 failed).
> 골든은 `--update` + 사유 기록(12,688 → 13,664 findings). `kics_disclosure.json` ·
> `insurequant_master_tables.xlsx` 읽기만 했다. 허용오차 무변경. 커밋·push 안 했다.

**(2026-08-24) 🟢 tier2/다리 발행사 자기모순 documented exception 등재 — blocking RED 39 → 13.**
> owner 가 이번 라운드는 등재까지 위임했다. **범위를 좁게 가져갔다** — 등재 전에 전수 갈래를
> 기계로 가르고("TFI 표가 `item51 == min(47,48)+49` 로 자기 안에서 닫히는가" · "그런데 헤드라인
> item3 과는 다른가"), 후보 전부를 raw PDF **word-좌표로 직접 열어** 확인했다. 13버킷 26 finding.
>
> **두 계열이고 사유를 구분해 적었다.** ① **두 표가 서로 다른 값을 인쇄**(코리안리 7분기 ·
> 롯데 2026.1Q) ② **한 표가 자기 구성행과 안 닫힌다**(롯데 2024.4Q·2025.1Q · BNP 2024.4Q·2025.1Q ·
> 동양생명 2025.2Q). owner 발주서는 롯데 2024.4Q 를 ①처럼 적었지만 실측하면 `item51 = 28,030.38`
> 로 헤드라인과 같아 ②였다 — **사유를 바꿔 적었다.** 사유가 틀린 면제는 다음 세션의 잘못된
> 일반화 씨앗이 된다.
>
> **코리안리는 7분기 전수를 raw 에서 열었다.** 2023.2Q~2024.3Q 는 헤드라인 = TFI **적용후**이고
> TFI 적용전은 자기 구성행으로 정확히 닫힌다. 2024.4Q 에서 보완자본만 적용전으로 넘어갔는데
> `Ⅲ.재분류항목` 은 적용후 그대로라 다리가 정확히 그 차액(−1,090)만큼 깨진다. **방증**: FY2024_Q4
> 필링의 직전분기 열이 2024.3Q 보완자본을 7,077(=그 분기 item51_적용전)로 재게시한다 — 그 분기
> 자기 필링은 5,996 이었다. 같은 셀을 두 필링이 다른 값으로 인쇄한다. 잔차가 −983~−1,081 로
> 분기마다 달라 **분기별로 따로 박았다**(하나로 뭉치면 그 순간 blanket skip).
>
> **면제는 두 겹이다.** ① raw 로 판독한 **마스터 셀**을 매 실행 재확인(`TIER2_EXEMPTION_INPUT_DRIFT`
> / `..._INPUT_MISSING` RED) ② 그 축이 실제로 내는 **RED 의 잔차·사유**를 매 실행 재확인
> (`..._RESIDUAL_DRIFT` RED · `..._INERT` review). ①만 있으면 룰 변화를, ②만 있으면 데이터 변화를
> 못 본다. 변이시험 **28건** 신설(`tests/test_tier2_issuer_inconsistent_exemption.py`) — 합성이
> 아니라 **라이브 마스터**로 흔든다(합성이면 "코드가 돈다"만 보이고 "등재분이 재검산된다"는 안 보인다).
>
> **등재를 스스로 넓히지 않았다.** `test_the_exemption_is_narrow_...` 가 보류 5버킷이 면제로 새어
> 들어가지 않는 것 + 실제로 RED 로 남아 있는 것을 기계로 강제한다. **BNP 2024.3Q 는 2024.4Q·
> 2025.1Q 와 증거가 동일한데도 위임 목록 밖이라 등재하지 않았다**(TODO·게이트 `not_registered` 에 기록).
>
> **NH농협 2025.4Q 는 등재를 거부했다 — 열어 보니 반대 결론이었다.** raw p46
> `697,899(47) + 447,254(49) + 94,959(기발행 후순위채무) = 1,240,112` = 공시 보완자본, **마지막
> 자리까지 정확.** 잔차 949.59억이 그 후순위채무 행과 1원 단위로 같다. 발행사 자기모순이 아니라
> **우리 식에 항이 빠진 것**이다 → parser 발주(§3). 면제로 덮으면 우리 결손이 발행사 탓으로 박제된다.
>
> **게이트 사각 하나를 같이 메웠다.** 등재 직후 `validate_data_contract.py` RED=25 였고 **그중 21건이
> 방금 등재한 면제분**이었다 — 그 게이트는 K-ICS 룰을 위임해 RED 를 들어 올리면서 **면제 층은 위임하지
> 않고 있었다.** 두 게이트가 같은 finding 에 다른 대답을 하면 등재가 조용히 무효가 된다. 같은 함수를
> 부르도록 배선(복사 금지 — 재검산이 두 벌이면 한쪽만 깨진다). `8_life` 도 같이 배선(현재는 분기
> 필터에 걸려 미발화지만 같은 모양의 구멍). **RED 25 → 4.**
>
> **남은 blocking 13**: 롯데 2023.1Q 3 · BNP 2024.3Q 5 · NH농협 2024.3Q 1 · NH농협 2025.4Q 2 ·
> 한화생명 2025.2Q 1 · 예별손해 2025.1Q 1. **한화생명은 RED 로 남기는 것이 정답이다** —
> 825.75 ≈ 826 단서는 인과 미확정이고, "거의 같다"를 근거로 면제하면 패턴을 원인으로 단정하는 것이다.
>
> **골든 `--update` 안 했다**(룰 엔진 무변경이라 필요 없었다). 데이터·xlsx·허용오차·기존 레지스트리
> 3종 전부 무변경(`kics_disclosure.json` mtime 08-22 그대로). `pytest tests/ -q --ignore=...` →
> **282 passed, 1 skipped**. 커밋·push 안 했다.

**(2026-08-22 d) 🔴 `47_tier2_census` 판정 근거를 추론 → 실측으로 교체 — blocking RED 119 → 81 → 53.**
> 어제 내가 `TIER2_TABLE_ABSENT_INTERMITTENT`(= 같은 회사가 다른 분기엔 공시했나)를 RED 로
> 승격시킨 것이 **틀린 기준**이었다. 47/48/49 는 [지급여력비율의 경과조치 적용에 관한 사항]
> (1)공통적용 경과조치 표의 행이고, TFI 는 그 자본증권이 상환·만기되면 적용이 끝난다 —
> **분기마다 켜졌다 꺼지는 것이 정상**이다. 이제 그 버킷 **자신의 TFI 실측값**
> (`data/_derived/kics_transition_applicability.json`, parser 494버킷 전수)으로 판정한다.
> 부재 28버킷 × 2컬럼: **30 RED → 2 RED + 26 YELLOW + 28 SKIP.**
> 원문 확인: 교보라이프플래닛 FY2023_Q1(TFI=O) MD 에 `보완자본 한도` 3회 + 표 존재,
> FY2023_Q2 이후(TFI=X) 같은 키워드 **0회** — 12버킷 24칸이 원천부재였다.
>
> **orchestrator 기준을 그대로 안 썼다 — 전수 반증이 나왔다.** `P(부재|TFI=X) = 15/108 =
> 13.9%` 다. 하나손해는 **13분기 전부 TFI=X 인데 12분기가 표를 인쇄한다**("해당사항 없음"
> 문장 뒤에 적용전 컬럼만 채운 표). 그래서 X 를 무조건 면죄부로 쓰지 않고, 같은 회사의 다른
> TFI=X 분기에 행이 있으면 SKIP 이 아니라 **review** 로 내린다(`tier2_x_present_codes`).
> 이 가지가 없으면 X 하나로 26칸이 통째로 사면된다.
>
> **사이드카를 그대로 안 믿는다.** `_load_tfi_applicability()` 가 `_source_readability()` 와
> 같은 방어 — 파일 없음/키 없음/`md_path` 디스크 부재 → **UNKNOWN 강등**(통과 아님).
> 룰엔진은 파일 I/O 를 안 하고(순수해야 골든 성립) 게이트가 실어 준다. 골든·매니페스트
> 테스트도 **같은 로더**를 쓰게 고쳤다 — 안 그러면 골든이 게이트의 RED 를 한 건도 못 박는다.
> `NA` 는 X 와 같게 보지 않는다(`-` = 미적용의 진술이 아니라 진술의 부재. NA 8버킷은 전부
> 행이 있어서 이 가지에 도달조차 안 한다 = 엄격해도 비용 0).
>
> **변이시험 8종 신설**(`test_tier2_limit_rules.py` §8): TFI=O 부재 → RED / TFI=X 부재 →
> RED 아님 / 사이드카 None·키없음·UNKNOWN·NA → **YELLOW(통과 아님)** / X-inconsistent →
> review, 반례 → SKIP / 적용후도 같은 판정.
>
> **내가 어제 쓴 근거 하나가 원문에 반증됐다 — `TIER2_DUPLICATE_ROW`.** "47 과 48 이
> 2자리까지 우연히 같을 수 없다 → 같은 셀을 두 번 읽은 지문" 이라고 써 놨는데, raw PDF 를
> 단어 좌표로 읽으니 **발행사가 두 행에 같은 숫자를 인쇄한다**(BNP카디프 FY2024_Q3 p16
> 31,614/31,614 · 동양생명 FY2025_Q2 p16 1,210,705/1,210,705 — 동양생명은 같은 표
> 적용후가 866,138/1,210,705 로 달라 "두 컬럼을 못 읽는 것" 이 아님). 주석을 정정했고
> **검사는 남겼다** — 하나생명 2024.4Q 에서 진짜 결함을 잡았기 때문이다: 그 분기 raw 는
> 347p 번들 사업보고서라 표가 아예 없는데 마스터엔 `47=48=51=item3=3452.36` 으로 item3 이
> 복사돼 있고, 그 복사 때문에 `3_tier2_composition` 이 branch=UNCAPPED 로 **GREEN 이 된다**.
> 이 한 줄이 없으면 그 버킷은 통째로 false-green 이었다.
>
> **`_TRANSITION_KIND` = 병행(overlay) 권고, 교체·수정 둘 다 반대.** 소비처는 **딱 한 곳**
> (`_axis_eval_rates` 자기미러 3분류)이고 `_AXIS_TRANSITION_KIND` 가 None 이 아닌 **R1·R2·
> mmult17 세 축에서만** 발화한다. 분기별 실측으로 갈면 **신규 suspect +24 · 해제 0 ·
> UNKNOWN 4**(R1 +6 / R2 +2 / mmult17 +16). suspect 는 `suspect == evaluated` 일 때만
> blocking 이 되는데 최악인 `R2 적용후`(eval 182 = mirrored 182)도 +2 면 0 이 안 된다.
> 그래도 교체 반대: 고신뢰 3건 중 **BNP카디프·카카오페이는 provenance 가 약하다**
> (`format1_breakdown_table_present` = 표 존재 추론. BNP 는 그 표의 TER/TIRR 이
> 31,150/31,150 로 전=후 동일). **에이비엘은 고신뢰인데 바로 그래서 registry 를 못 고친다** —
> 2023~24 분기는 같은 요약표가 TAC 를 명시 X 로 인쇄하므로 회사 단위로 `AC` 를 적으면 그
> 분기들이 틀린다. **registry 가 못 담는 것은 값이 아니라 시간축이다.** 전제조건은 사이드카가
> provenance 를 기계가 읽는 필드로 내보내는 것 → parser 발주.
>
> **남은 RED 54(blocking 53 + 승인 `8_life` 1) 전수 갈래**: 데이터 결함 **17**(신한이지 6 ·
> 교보 4 · 미래에셋 2 · 롯데 stale 2 · 하나생명 2 · 예별 1) / owner 승인 필요 **36**
> (BNP 14 · 롯데 9 · 코리안리 7 · NH농협 3 · 동양 2 · 8_life 1) / 판정불가 **1**(한화생명
> 2025.2Q — 한도초과 근사치가 item12 의 2.3배라 클램프로도 안 닫힘). **면제는 등재 안 했다**
> (초안만, owner 승인 필요). 데이터·xlsx·허용오차·레지스트리 3종 전부 무변경.
>
> **골든**: `test_kics_rules_golden.py --update` 를 **마지막에 한 번만** 재생성(손으로 해시
> 안 고쳤다). 사유 2개를 `_what` 에 기록. `pytest tests/ -q --ignore=...pl_breakdown...
> --ignore=...ifrs17_bs...` → **256 passed, 1 skipped**. 커밋·push 안 했다.

**(2026-08-22 c) 🔴 item50/51 설계결손 2건 수정 — blocking RED 236 → 119 (127건 중 117 해소).**
> parser 가 50/51 을 **431버킷 백필**하자 어제 내가 만든 두 축이 127칸 RED 로 터졌다. 전수 분해
> 결과 **데이터 오염 0건 · 전부 룰 커버리지 결손**이었다. 데이터·xlsx·허용오차·면제 레지스트리는
> 한 군데도 안 건드렸다.
>
> **결손 ① `51_tfi_tier2_composition` 67 → 5.** 형제 룰 `3_tier2_composition` 이 이미 갖고 있던
> 갈래(CAPPED/UNCAPPED/BOTH/TFI_NA)를 안 쓰고 `min(47,48)+49` 만 무조건 검사하고 있었다. 갈래를
> **재구현하지 않고** `_tier2_branch` 에 `target_item` 인자를 추가해 같은 함수를 공유시켰다.
> 갈래→status 매핑도 공유 상수 하나에서 온다. 해소 62 = UNCAPPED 50 + TFI_NA 12.
> `3_tier2_composition` 은 한 칸도 안 움직였다(RED 14 · GREEN 423, 전후 동일).
>
> **결손 ② `50_tfi_tier_split_post` 60 → 5. orchestrator 지시(`== item1_적용전`)도 원문에 반증됐다.**
> 지시대로면 25건만 닫힌다. IBK연금 FY2026_Q1 raw **p17** 이 결정적이다 — TFI 표 **자신의
> 지급여력금액 행이 857,997 → 938,740 으로 움직인다**(같은 표 지급여력기준금액 719,585/719,585 는
> 안 움직인다 = 축 D 근거 재확인). 어제 내가 근거로 든 "공통적용 경과조치는 재분류라 합계 불변"은
> **코리안리 한 회사에서만 참**이었다(실측: 합계가 움직이는 버킷 49개/11개사). 올바른 비교 대상은
> 표 자신의 지급여력금액 적용후 행(item52)인데 마스터에 없다 → 없는 값을 대신 채우지 않고
> **범위검사** `min(item1_전,item1_후) ≤ 50후+51후 ≤ max(...)` 로 바꿨다. **완화 범위를 숫자로
> 못 박았다**: item1 전=후 인 **362칸(84%)에서는 범위가 한 점으로 붕괴해 등식과 같은 강도**이고,
> 열리는 69칸은 GREEN 이 아니라 **YELLOW**(= item52 발주 대기열, 게이트가 매 실행 인쇄).
>
> **부수효과 — parser 가 요청한 기계 판별이 작동한다.** item51 축이 붙자 `3_tier2_composition`
> RED 14건이 자동으로 갈렸다: **두 표가 다른 값을 인쇄 9건**(축 F GREEN = TFI 표는 자기 공식으로
> 닫힘 → 우리 추출은 양쪽 다 원문대로) vs **표 자신이 자기 공식으로 안 닫힘 5건**(두 표 값 차
> ≤0.5). "우리가 두 표를 잘못 이었다"는 **0건**이다. `2_tier1_bridge` 8건도 **전부**
> `item2 == item50_적용전`(최대 차 0.49)이라 헤드라인 기본자본이 확증됐다 — 다리 잔차의 원인은
> item4/12/13 쪽이다.
>
> **변이시험**: 갈래 4종 × (item51 흔들기 · item47 흔들기) 전부 GREEN → RED. 범위검사도
> ±9,999 로 RED, 붕괴 버킷은 +5 로 RED, 하한 결측은 폴백 없이 SKIP+사유. 매니페스트의 갈래
> 시험 2종을 **두 축 전부**에 파라미터화(전엔 축 B 만 봤다) + `COMPOSITION_AXES` 선언 신설 +
> `test_composition_axes_share_one_branch_definition` 로 "갈래 정의는 하나뿐"을 소스에서 강제.
>
> **기각한 후보 탐지기 1건(기록)**: 교보의 적용후 미러링을 잡을 후보 "item50 후=전인데 item2 는
> 움직인다" 는 **45칸 중 40칸이 정당**(IBK raw 가 TFI 기본자본 157,463/157,463 로 실제 동일)이라
> 배선하지 않았다. item52 가 들어오면 이 클래스는 등식으로 자동 검출된다.
>
> **parser 발주 3건**(전부 raw 확인분, `inbox/parser/20260821T1425Z...` §5):
> ① **교보생명 4버킷 적용후 3항목 오독 확증** — item47_후 27,623.07(정답 16,534.08) ·
> item50_후 105,998.86(정답 117,087.85) · item51_후 **0.10**(정답 30,826.05). 교보 PDF 는
> 텍스트 스트림 순서가 뒤엉켜 `get_text()` 로 읽으면 반드시 틀린다 — **단어 좌표 x 로 컬럼을
> 갈라야** 한다. ② **item52 신설**(TFI 표 맨 윗줄 지급여력금액) → 범위검사가 등식으로 승격.
> ③ 50/51 백필 잔여 **9버킷**(KB손해 1 · 하나손해 4 · 교보 2 · 코리안리 2).
>
> **면제는 등재 안 했다**(초안만, owner 승인 필요). 잔여 blocking 119 = census 대기 85(손 안 댐)
> · 데이터 결함 9 · owner 승인 필요 25.
>
> **골든**: `test_kics_rules_golden.py --update` 를 **마지막에 한 번만** 재생성(손으로 해시 안
> 고쳤다). `_what` 에 사유 4개 기록. by_status 대이동(SKIP 3,953→2,257 · GREEN 7,352→8,758)은
> 내 룰 수정이 아니라 **parser 백필** 때문이고 findings 총계 12,688 은 불변이다.
> `pytest tests/ -q --ignore=...pl_breakdown...--ignore=...ifrs17_bs...` → **249 passed, 1 skipped**.
>
> **내가 틀렸던 것**: 어제 `48_tier2_limit` 주석에 "한 회사로 일반화하지 말라"는 취지를 써 놓고
> 바로 옆 축(50)에서 코리안리 한 회사의 성질을 전 회사에 일반화했다.

**(2026-08-22 b) 🔴 item50/51 룰 배선 + INTERMITTENT RED 승격 + RED 31 갈래확정 — blocking RED 31 → 107.**
> **매니페스트가 설계대로 작동했다.** parser 가 item50/51(코리안리 TFI표 자신의 기본자본·보완자본)을
> 7분기 적재하자 `test_rule_coverage_manifest.py` 가 즉시 "무방비 14칸"으로 실패했다. 어제
> 47/48/49 1,285칸이 조용히 통과하고 손으로 뒤져서야 발견된 것과 대비된다.
>
> **신규 축 2개 — 두 표를 섞지 않는 쪽으로 걸었다.** 코리안리는 헤드라인(item2/3)과 TFI표
> (item50/51)가 다른 값이고, **분기마다 스코프가 뒤집힌다**(6분기는 헤드라인=TFI후, 2024.4Q는
> 헤드라인=TFI전). 그래서 두 표를 잇는 룰은 만들지 않고 표 안에서 닫히는 축만 배선했다:
> `50_tfi_tier_split`(`item50+item51==item1`, 재분류라 합계 불변 → **적용후도 RED**, 실측 14/14) ·
> `51_tfi_tier2_composition`(`item51==min(47,48)+49`, 동일표·동일컬럼 → 적용전 **7/7 정확**,
> 적용후는 미확립 YELLOW). 변이시험 8종 전부 GREEN→RED 확인. `3_tier2_composition`은 **안 건드렸다** —
> item51로 갈아끼우면 코리안리 6칸의 item3가 통째로 무검사가 되어 갈래가 아니라 면제가 된다.
>
> **`TIER2_TABLE_ABSENT_INTERMITTENT` → RED 승격**(orchestrator 결정). 38버킷 × 2컬럼 = **76 RED**.
> 39가 아니라 38인 건 parser가 동양생명 2026.1Q를 적재해 1건이 해소됐기 때문. `..._COMPANYWIDE`
> 13버킷(미래에셋생명)은 **SKIP 유지** — 추출갭이라는 증거가 없고, 고칠 수 없는 RED는 게이트를
> 영구히 막는다. 승격이 면제가 아니라 **작업 큐**임을 변이로 증명(결측 채우면 RED→GREEN).
>
> **RED 31건 전건 raw 재검증 → 갈래 A 20 · B 11 · C(판정불가) 0.**
> · **A = 발행사 원본 불일치 확증 → 면제 초안(등재 안 함, owner 승인 필요).** 핵심 원문:
>   코리안리 FY2023_Q2 **p8** 헤드라인 `[경과조치 적용 전 …]` 이 기본자본 **32,204**를 인쇄하는데
>   같은 필링 p9 TFI표의 "적용 전"은 **31,221.14**다 — 헤드라인이 적용후 값을 적용전 칸에 싣는다.
>   NH농협손해 2025.4Q 잔차 949.47은 표 안 `(기발행 후순위채무) 94,959`와 **정확 일치**.
>   롯데손해 2023.1Q는 TFI표 자신이 8,034+17,830≠25,846으로 18 어긋난다.
> · **B = 우리 룰의 전제가 원문에 반증됨(면제 아님, 룰 수정 대상).** `TIER2_DUPLICATE_ROW`(7건)의
>   전제 "47==48은 한 셀 두 번 읽기"가 틀렸다 — BNP p16 `31,614/31,614`, 동양 p16
>   `1,210,705/1,210,705`를 발행사가 실제로 두 번 인쇄한다. **동양생명은 그 값으로 composition이
>   정확히 닫히는데도 RED**다(순수 오탐). 다리 4건은 발행사가 한도적용전을 이미 캡해 인쇄하면
>   `excess=max(0,47−48)`이 구조적으로 0이 되어 item12를 과차감하는 문제(동양 잔차 = item12 정확일치).
>   **그날 만든 룰을 그날 스스로 약화시키지 않았다** — owner 판단으로 올린다.
>
> **롯데손해 2026.1Q 확정: 발행사가 전기 표를 재게시. 마스터는 원문과 바이트 일치.**
> 결정적 증거는 parser가 놓친 것 — `item47_적용후`가 **5775.82 → 5801.18로 갱신**돼 있다.
> 우리가 전기 필링을 붙였다면 적용후도 같아야 하는데 다르다. raw p22 vs p77 대조로 발행사가
> 비율·한도적용전(후)·후순위채무 **세 줄만 갱신**하고 나머지를 복붙한 것을 확인했다.
> → 원문대로 두고 박제 면제(미래에셋 2023.2Q 선례). 결측으로 되돌리지 않는다.
>
> **parser 발주**: `47/48/49`는 있는데 `50/51`이 없는 **430버킷 / 38개사**(같은 표 위 두 줄).
> 게이트가 매 실행 `TFI_TIER_ROWS_ABSENT_BACKLOG: 430`으로 인쇄한다. RED 승격은 안 했다 —
> 어제 만든 스키마라 기대 그리드 미확정, orchestrator/owner 판단 사항.
>
> **미해결 큰 질문**: `item2`가 전≈후인데 같은 필링 TFI `item47`은 전≠후인 버킷이 **57개**
> (NH농협손해 13분기 · 현대해상 11 · 악사손해 10 · 코리안리 6 · DB손해 4 등 12개사). 코리안리형 정당 케이스와 미러링 오염이
> 섞여 있어 raw 대조 전에는 룰로 못 만든다 — 별도 티켓 필요.
>
> 게이트: `validate_kics_disclosure.py` exit 2 · RED=108 · **blocking RED=107**.
> `validate_data_contract.py` SUMMARY RED=61(종전 19) YELLOW=296.
> `pytest tests/ -q --ignore=…pl_breakdown_golden --ignore=…ifrs17_bs_golden` → **221 passed, 1 skipped**.
> `test_kics_rules_golden.py --update` 재생성(사유는 golden `_what`에 기록): findings 10,736→12,688
> (+1,952 = 488버킷×2룰×2컬럼) · RED 32→108(+76). **데이터·허용오차·면제 레지스트리 3종 무변경.**
> 안 건드린 것: `kics_disclosure.json` · `insurequant_master_tables.xlsx` · ifrs17. 커밋·push 안 함.

**(2026-08-22 a) 🔴 tier2 갈래 전수 분류 + 다리 구조적 상한 — blocking RED 43 → 34. 잔여 34는 전부 parser 발주.**
> parser 가 iter-3 에서 "43건 전부 원문과 일치, 룰 문제" 라고 회신했다. 절반은 맞았다.
>
> **갈래 전수 분류(488 버킷)**: `CAPPED` 324 · `UNCAPPED` 51 · `BOTH` 34 · **`TFI_NA_OK` 12(신설)** ·
> `INPUT_MISSING` 52 · `NEITHER` 15(RED). parser 가 제안한 `item3 == item13`(RECLASS_ONLY) 갈래는
> **채택하지 않았다** — parser 는 7건이라 했고 orchestrator 는 160건이라 했는데 실측은 **147건**이고
> 그중 **125건이 이미 CAPPED/UNCAPPED 로 통과**한다. 갈래로 만들면 그 125칸의 item47·item49 가
> 통째로 무검사가 된다. 갈래가 아니라 결과다.
>
> 대신 **결정론적으로 갈리는 진짜 갈래**를 찾았다: `item48 == 0 ∧ item14 > 0` 이면 item48 은
> SCR×50% 일 수 없으므로 **한도가 아니다**(해당사항 없음 표시). 그 상태에선 대체 항등식
> `item3 == item13` 으로 검산 — 해당 24칸 **전부** 성립(실제 갈래 진입 12칸). 판정에 회사
> 레지스트리도 owner 판단도 안 든다.
>
> **다리**: `한도초과 ≤ item12` 구조적 상한. 발행사 각주가 한도초과액을 불인정항목 Ⅱ 의
> *구성요소*로 정의하므로 그보다 클 수 없다. 후보식 전수 비교 — 초과항 없음 425/52 ·
> 무조건 440/37 · CAPPED 조건부 461/16 · **+클램프 467/10(채택)** · `exc=max(0,47−3)` 계열 435~440.
> 클램프 발동 10칸 중 **9칸에서 다리가 정확히 닫히고** 1칸(한화생명 2025.2Q)은 그대로 RED.
> 대가: 그 10칸은 item12 가 상쇄돼 item12 오류를 못 본다 → 게이트가 발동 칸수를 매번 인쇄.
>
> **신규 검출 2종 (census)**: `TIER2_DUPLICATE_ROW`(item47 == item48 정확일치 = 같은 셀 두 번
> 읽기, 4칸) · `TIER2_LIMIT_STALE`(item48 이 **직전분기** SCR×50% 와 일치 = 전기 값 잔존,
> 롯데손해 2026.1Q — 47/48/49 적용전 3칸이 2025.4Q 와 바이트까지 동일). **전자는 진단 정확도만
> 올리고 후자는 진짜 false-green 을 하나 잡았다.**
>
> **`TIER2_TABLE_ABSENT` 52칸을 쪼갰다**: `..._INTERMITTENT` **39**(같은 회사가 다른 분기엔
> 공시 → 추출갭) · `..._COMPANYWIDE` 13(미래에셋생명 전 분기 부재). **RED 승격은 안 했다 —
> blocking 이 39 늘어나는 결정이라 orchestrator/owner 판단 필요.** 사유는 갈렸으니 더는
> "SKIP 52" 가 통과처럼 안 읽힌다.
>
> **면제 신설 0건.** 허용오차 한 군데도 안 건드렸다(`tolerance=2.0`). `kics_disclosure.json` ·
> `insurequant_master_tables.xlsx` 미변경. 잔여 34건은 전부 `inbox/parser/20260821T1425Z...md`
> `## sender 재확인 (validation, iter-2)` 에 **예측값을 붙여** 발주(status open, iter 3).
>
> **변이시험**: `tests/test_tier2_limit_rules.py` 37 → 53(갈래별 falsifiability 증명),
> `tests/test_rule_coverage_manifest.py` 4 → 6(`COMPOSITION_BRANCHES` 선언 + 실데이터 갈래
> 전수 변이). 골든 `kics_rules_golden.json` 은 룰 의도변경으로 `--update` 재생성(RED 44 → 35).
> 재현: `python scripts/validate_kics_disclosure.py` → exit 2, blocking RED=34 ·
> `python scripts/validate_data_contract.py` → RED=20(종전 24) · `python -m pytest tests/ -q`
> (PL/17BS 골든 제외) → **221 passed**.
>
> **owner 승인 필요 3건**: ① 코리안리 6분기 — TFI 표 자신의 보완자본/기본자본 행 신규 적재
> (잔차가 `item14 × 5.00%` 와 최대 편차 0.38억으로 일치, 마스터로는 절대 못 닫는다) ②
> `..._INTERMITTENT` 39칸 RED 승격 여부 ③ 동양생명 2026.1Q vision 판독 시도 여부(완전 스캔본).


**(2026-08-21 l) 🔴 보완자본 한도 3줄(47/48/49) 룰 8축 배선 — blocking RED 63. parser 발주.**
> parser 가 47/48/49 를 1,299칸 적재했는데 **게이트가 exit 0 이었다** — 세 항목을 보는 룰이
> 하나도 없었다. 원 티켓의 다리를 드디어 닫았다: `2_tier1_bridge` =
> `item2 = item4 − (item12 − 한도초과) − item13`, 한도초과 = `max(0, item47 − item48)`.
> **조건부가 핵심** — 무조건 더하면 통과가 425→393 으로 줄어든다(한화생명 13Q·KB손해 6Q 가
> 새로 깨진다). `item3` 로 CAPPED/UNCAPPED 를 판정해 CAPPED 일 때만 더한다 → **잔차 53 → 15**.
> parser 의 "min+초과분 공식이 보편적이지 않다" 미결 질문에 대한 답이다.
>
> **8축(적용전·적용후 각각)**: `2_tier1_bridge`(RED 15) · `3_tier2_composition`(RED 28) ·
> `47_tier2_census`(RED 10+10) · `48_tier2_limit`(YELLOW).
>
> **⚠️ `48_tier2_limit` 은 blocking 이 아니다 — 로더가 그 식으로 배율을 골랐다(동어반복).**
> parser 가 100배 사고를 고치면서 스케일(÷1/÷100) 판별 앵커를 `item48 ≈ item14×50%` 로
> 바꿨다. 그 식을 검사하면 당연히 통과한다 → GREEN 이 증거가 아니다. YELLOW + 게이트에
> `LOADER_ENFORCED` 경고 인쇄, `test_loader_enforced_axes_never_become_blocking` 이 승격을
> 기계로 막는다. **비순환 증거는 `3_tier2_composition`** (item3 는 다른 표의 독립 추출값).
> 배율 선택 provenance 를 parser 에 요구했다 — "골랐다"를 "확인했다"로 셀 수 없다.
>
> **적용후 정정 — 내 앞선 "미러링 오염 429/430" 지적은 오판. 철회했다.**
> 통계로는 H1(원문이 두 컬럼에 같은 값 인쇄)과 H2(복사)를 구분 못 한다. 좌표로 확인:
> 한화손해 2023.1Q raw p9 는 한도 행에 `16,193@340 / 16,193@486` 두 숫자를 물리적으로 찍고,
> 그 표 **자신의 SCR 이 32,387/32,387 로 동일**하다(TFI 는 요구자본을 안 움직인다).
> 마스터 `item14_적용후`(22,492)는 전체결합 스코프라 개념이 다르다 → **적용후 분모는
> `item14_적용전`**. 이걸 틀렸으면 241칸 오탐이었다. item47_적용후는 미러가 아니라 실데이터
> (23.1Q 10,258/6,023 · 23.2Q raw p11 `1,022,151/11,442`).
>
> **적용후 다리·구성 2축은 YELLOW(미확립).** 한화손해 2023.2Q 는 적용전에서 정확히 닫히는데
> (30,730.03) 적용후만 잔차 5,872.17 이고 **추출은 raw 대조로 정확**하다 → 식이 안 맞는 것이라
> RED 로 단정하면 220칸 오탐. `POST_UNESTABLISHED_RULES` 에 등재, 확립되면 RED 승격.
>
> **커버리지 매니페스트**: 적용전 무방비 `{12,13}` **해소**(24/25/26 만 남음) · 적용후 검사
> 항목 `{2,14,28}` → **10개**(3·4·12·13·47·48·49 추가) · `GATE_BLIND` **비었다**.
> 변이시험 `tests/test_tier2_limit_rules.py` 37개 신설. 골든은 룰 신설로 의도적 갱신.
> parser 회신: `inbox/parser/20260821T1425Z...md` §sender 재확인. `kics_disclosure.json` 읽기만.

**(2026-08-21 k) ✅ owner 결정으로 R2 동어반복 2건 면제 → 게이트 exit 0, 라이브 배포 진행.**
> owner: *"테이블 숫자를 바꾸는 RED는 아닌거같은대? 이번에는 일단 풀고 올려라"* — 맞다.
> `IDENTITY_TAUTOLOGY` 는 census 를 읽어 findings 만 만들고 `records` 에 쓰지 않는다(확인함).
> **상한 박제형**으로 배선: `_TAUT_EXEMPT` + `_TAUT_PIN_EXCESS_TOL=0.10`. 더 되맞춰지면
> `IDENTITY_TAUTOLOGY_PIN_DRIFT` RED 복귀(허용오차가 실측 폭 +0.59 를 못 삼킨다), 수렴하면
> `..._EXEMPT_UNNECESSARY` review 로 등재 삭제 안내. **경고 인쇄는 3곳 모두 유지** — 면제한
> 것은 push 차단이지 경고가 아니다. 변이시험 5개 추가(총 10). 원인 조사는 계속(티켓 1830Z 2·3번).

**(2026-08-21 j) 🔴 push 차단중 — 훅이 `validate_kics_disclosure.py` 를 안 부르고 있었다. 배선하니 R2 동어반복 2건이 실제로 막는다.**
> `PRE-PUSH VERDICT: gate RED=0 · K-ICS rule gate=BLOCK · domain gates=pass · inbox 0 · tests=pass → BLOCKED`
>
> **(i) 의 "exit 0 / gate-clear" 는 이 게이트를 안 돌린 상태의 결과였다.** `CLAUDE.md` 의
> "K-ICS validation gate (mandatory)" 가 push 전 필수라고 못박은 `validate_kics_disclosure.py`
> (5.9초)를 훅도 CI 도 부르지 않았다. 증거: `validate_data_contract.py` L305 주석
> *"(prepush_check.py 는 validate_kics_disclosure.py 를 호출하지 않는다) 여기서 같이 건다"* —
> 빠진 게이트를 눈치챌 때마다 룰을 한 개씩 베껴 심고 있었다.
>
> **전수확인 결과 `scripts/validate_*.py` 8개 중 훅이 부르던 것은 1개뿐이었다.**
> · 배선함(1b·1c): `validate_kics_disclosure`(exit 2) · `validate_csm_continuity`(0, 2초) ·
>   `validate_kics_rate_sensitivity`(0, 3초) · `validate_nb_csm_multiple`(0, 3초)
> · 미배선+사유등재: `validate_csm_waterfall`(**exit 1**, `balance_incomplete:assumption` —
>   지금 걸면 모든 push 차단 → parser/ifrs17 티켓 `20260821T1900Z`) ·
>   `validate_master_tables`(골든 경유, 직접 호출은 `--no-build` 없으면 마스터 파괴) ·
>   `validate_statutory_reserves`(data-contract 가 import 해 실행)
> · **`tests/test_push_gate_wiring.py` 신설(12 tests)** — 새 `validate_*.py` 는 WIRED 나
>   사유 있는 NOT_A_PUSH_GATE 중 하나에 없으면 막힌다. `test_unwired_gates_still_fail` 은
>   "지금 깨져 있어서 뺐다" 사유가 아직 참인지 매 push 재확인한다.
>
> **남은 차단 원인 = R2_순자산합 IDENTITY_TAUTOLOGY 2건(적용전·적용후).**
> parser 가 넘긴 가설("image-only 24셀이 초과분을 설명한다")을 실측으로 **반증**했다 —
> 그 셀을 빼도 excess 1.25→1.23 / 1.43→1.40 밖에 안 움직인다(적용후는 여전히 RED).
> 진짜 신호는 **회사 단위 이봉분포**: KR0069 9/9 · KR0008 12/13 · KR0050 12/13 이 스캔사가
> 아닌데도 100%대이고, 반대로 **KR0073 은 13칸 중 1칸**(귀무 49%)으로 계통 이탈이다.
> 티켓 `inbox/validation/20260821T1830Z` · 프로브 `scripts/_probes/probe_r2_excluding_scan_cells.py`.
>
> **영향: 라이브(main) 배포가 이것 때문에 대기중.** main 의 `kics_disclosure.json` 은 2026-07-21 판
> (지난 한 달 = 적용후 710칸 변경 + 신규 204칸 미반영). 배포 사본은 `deploy/20260821-json` 에 준비됨.

**(2026-08-21 i) ✅ push 게이트 RED 8 → 0. `36_irr` documented exception 배선 완료 (owner 승인).**
> `sh .githooks/pre-push < /dev/null` → **exit 0** ·
> `PRE-PUSH VERDICT: gate RED=0 · inbox 기계적위반=0 · offline tests=pass → gate-clear` (140 passed / 243s).
>
> 직전 (h) 에서 면제 반증으로 드러났던 RED 중 마지막 8건(= `KICS_36_irr` 4 + `TRANSITION_AFTER_IRR_MISMATCH` 4,
> 전사로는 적용전 5 + 적용후 5)을 owner 가 **잔차 박제형 documented exception** 으로 결정했다
> (티켓 `inbox/validation/20260821T1810Z`). 대상 5건: KR0073 2025.2Q · KR0094 2024.2Q·2024.4Q·2025.2Q·2025.4Q.
> 상세·해제조건은 root `TODO.md` "Derivation not reproducible" 표.
>
> **배선**(`src/solvency/validation/kics_json_rules.py` → 게이트가 import):
> `IRR_DERIVE_ISSUER_INCONSISTENT` + `irr_derive_expected()` + `irr_pin_verdict()`.
> **적용전·적용후를 각각 박았다** — KR0079 8_life 때 적용전만 걸어 적용후가 그대로 막힌 전례 반복 방지.
> MATCH → SKIP(사유 인쇄) · DRIFT → RED · **결측 → RED**(SKIP 아님) · 잔차가 룰 tol 안으로 들어오면
> `IRR_EXEMPTION_INERT` review("등재를 풀어라").
>
> **변이시험 실측**(마스터 무수정, records 주입): 면제 OFF → RED 8 복귀(원래와 동일 셀) ·
> item36 흔들기 → IRR 축 RED 10 · item44 결측 → 10 · item43 흔들기 → 6.
> **6 인 이유는 면제 탓이 아니다** — `max(R,0)` 가 각 쌍의 열위 시나리오를 절단해 그 입력은 도출값을
> 구조적으로 못 움직인다(면제를 꺼도 룰이 못 본다). (회사,분기)×항목 전수 스윕: 도출값이 실제로
> 움직이는 입력은 **전부 DRIFT=RED**, 절단 입력은 **결측 경로가 덮는다**.
> 상주화: `tests/unit/test_irr_pin_exemption.py` 9건(pre-push 훅이 `tests/unit/` 전체를 돌린다).
>
> **티켓 근거 재측정 중 정정 1건**: "판정이 갈리는 102건이 **전부** 현행식만 통과" 는 사실이 아니다 —
> 실측 **A-only 100 · B-only 2**(B-only 2건이 곧 면제 대상 신한 25.2Q·25.4Q). 결론(A 우세)은 불변.
>
> **골든**: `tests/fixtures/kics_rules_golden.json` `--update` (RED 6→1, `36_irr` RED 5 → SKIP 5.
> YELLOW/GREEN 한 건도 안 움직임. 남은 RED 1 = KR0079 8_life 기존 면제분).
> `tests/test_rule_coverage_manifest.py` 는 `FULL_COVERAGE_SWEEP=1` 로 3 passed — **매니페스트 수정 불필요**
> (36·41-46 커버리지 불변, 신규 사각 0).
>
> **inbox**: 내가 sender 인 스레드 3건 재확인 후 종결(`_resolved/` 이동) — `20260821T1625Z`(downloader,
> 흥국 2건: KR0005 재취득 완료 / **KR0071 은 내 오판이었다 — fitz 키워드 0회를 오문서 증거로 읽었고 실제로는
> p1~p112 스캔이었다**), `20260821T1620Z`(parser, A~D 전부 종결), `20260821T1420Z`(parser, rule 2 가
> 이제 실제로 발화: GREEN 327 / **YELLOW 161** / RED 0 — 이전엔 574셀 전부 잔차 정확 0 이었다).
> `20260820T2340Z` 는 **답변 유지** — 삼성생명 item5 5분기·에이비엘 item7 구간 확장 레지스트리 등재가
> 남았다(비차단, `validate_statutory_reserves` RED=0).

**(2026-08-21 h) ⛔ 면제 10건 반증·해제 → 가려져 있던 RED 10건 노출. push 게이트 BLOCKED.**
> `sh .githooks/pre-push` → `gate RED=10 · inbox 기계적위반=0 · offline tests=pass → BLOCKED`.
> **RED 10건은 전부 이번 세션에 내가 노출시킨 것이고, 전부 담당 stage 로 발주했다.** 우회·재면제 없음.
>
> **① `IDENTITY_TAUTOLOGY` 신설 (티켓 `inbox/validation/20260821T1500Z`).**
> 항등식 축의 잔차가 반올림 잡음(Irwin–Hall 귀무)이 허용하는 것보다 지나치게 자주 정확히 0 이면 RED.
> 커버리지(변이시험)와 다른 축 — 변이시험은 "룰이 이 칸을 본다"만 증명한다. 임계는 **실측**:
> 6축×2컬럼 전수 측정에서 건전 상한 `excess 1.11 / z 2.6`(R6 적용전) · 동어반복 하한 `1.30 / 11.4`
> (R1 적용전) → 기하중점 `excess≥1.20 AND z≥5.0`, `n≥30`. 비율축·sqrt축은 잔차가 연속량이라 배제
> (실측 `|r|<1e-9` 이 R4 0/486 · 8_life 0/363 · 19_market 0/355). 적용전·적용후 둘 다 배선.
> `tests/test_identity_tautology.py`(5 tests) + **`prepush_check.py` fast 묶음에 등록**(안 넣으면 또 honor).
> 원인 축 2개: `_reconcile_item4_from_components`(item4=Σ5-11) · `recalc_kics_derived.py` 199-221
> (**item3 = item1 − item2 무조건 덮어쓰기** — 이건 티켓에 없던 신규 발견).
>
> **② 면제 근거 백로그 13건 종결** (`EXEMPTION_PROVENANCE_UNVERIFIED` 13 → **REVIEW 1**).
> raw 를 fitz + 240dpi 렌더링으로 전건 재판독. **10건 등재사유가 거짓 → 해제. 2건 참 → VERIFIED 승격.**
> - `INTERNAL_MODEL_36IRR_EXEMPT` 5건 전건 해제(빈 frozenset). "내부모형사·시나리오별 직접공시"
>   두 전제 다 거짓 — 표준서식 `[② 금리위험액 현황]` 이 raw 에 있고(교보 p21 · 신한 p22/p144/p28/p131),
>   `Ⅳ.금리위험액` 은 단일 병합셀이며, 신한은 p135 에서 스스로 **별표22 표준모형사**라고 적는다.
> - `_AFTER_SUBRISK_NOT_DISCLOSED` 3건 해제(KR0097 2026.1Q · KR0104 2023.1Q · KR0005 2024.4Q),
>   1건 유지(KR0097 2024.4Q — 참, 마커 등재).
> - `_POST_PARENT_NOT_DISCLOSED` 2건 해제(KR0071 · KR0097 2024.4Q), 1건 유지(KR0049 2024.3Q — 참).
> - 게이트 신규: `present_markers`(부재 증명보다 원문 각주가 강한 근거인 항목용) +
>   `EXEMPTION_VERIFIED_WITHOUT_MARKERS` RED(verify 블록 비워 두는 조용한 통과 경로 차단).
> → 발주: `inbox/parser/20260821T1620Z`(36_irr 5건 추출 · 하나생명 item16후 신설/item17후 정정) ·
>   `inbox/downloader/20260821T1625Z`(**흥국화재·흥국생명 2024.4Q raw 가 정기경영공시가 아니라
>   DART 사업보고서다** — "경과조치" 문자열이 367p/538p 전체에서 0회).
>
> **③ 축 평가율 분모를 구조 인식(scope-aware)으로.** 영구 미해소 review 3건을 **임계를 올리지 않고**
> 해소했다. `36_irr` = 짝수분기 한정(실측: 41-46 적용전 보유 짝수 220/226 · **홀수 0/262**),
> 적용후 순자산(5-11)·시나리오(41-46) = 경과조치 비적용사 한정(실측: 적용사 0/18 · 비적용사 21/21).
> scope 는 **구조에서만** 뽑는다(데이터로 정하면 갭이 분모에서 사라진다). 좁힌 범위 안 미평가 칸은
> `scope_missing` 으로 이름 인쇄 — `36_irr[적용전]` 6건(위 5건 + KR1098 2024.2Q) ·
> `36_irr[적용후]` 15건 · `R2_순자산합[적용후]` 72건. **AXIS_EVAL_RATE_LOW 3 → 0.**
>
> ⚠️ **공유 워킹트리 주의**: `tests/fixtures/kics_rules_golden.json` 이 내가 `--update` 를 돌리지
> 않았는데 재생성돼 있었다(동시 parser 세션). 현재 내용은 내 변경(36_irr SKIP 5 → RED 5)을 이미
> 반영하고 있고 전 테스트 통과(141 passed) 상태지만, **커밋 시점에 다시 대조할 것.**

---

**(2026-08-21 g) ✅ 티켓 2건 종결 + 방치 스레드 2건 종결. 차단 RED **0**(면제 1건 잔차박제).**
> 게이트 실측 최종: `RED=1 YELLOW=563 GREEN=4730 SKIP=1510` → **blocking RED=0**.
> exit 은 여전히 2 이고 사유는 내 축이 아니다 — coverage census 2셀(카카오페이 2024.2Q·3Q 미제출) +
> **KR0087 동양생명 2023.2Q item19후 present 인데 item36~39후 결측**(파서 11:03 write 로 새로 노출).
>
> **① `item23 = item24+25+26` (티켓 20260821T1100Z ①)** — 선행 세션이 배선까지 해 두고 크래시했다.
> 중복 작성하지 않고 **변이시험으로 검증만** 했다: 룰 끄면 0 / 원래 결함(KR0071 2023.3Q item24=8313)
> 재주입하면 1 / 통과 회사의 **값_적용후**에 +999 주입하면 1(적용후도 진짜 판정한다).
> 실측 적용전 403/403 · 적용후 205/205. 발주 시점의 유일한 불일치는 파서가 데이터로 고쳤다.
>
> **② `item2 = item4 − item12 − item13` — 배선하지 않는다. 원인 규명 완료.**
> 잔차 53건은 마스터 결함이 아니다. **미래에셋 2023.2Q p11 `기본자본주2)` 각주가 정의를 써 놨다**:
> *"순자산에서 불인정항목**(단, 보완자본 한도를 초과한 금액을 제외)**및 재분류항목을 차감"*.
> 즉 `item2 = item4 − (item12 − 보완자본한도초과) − item13` 이고 **한도초과액이 마스터에 없다**.
> 세 회사 백만원 단위 검증: 푸본현대 26.1Q 344,739→3,447.4(잔차 −3,447) · IBK 26.1Q 80,743→807.4
> (−808) · 농협생명 25.1Q 190,459→1,904.6(−1,905). 푸본 완전검산 `7,254−(7,460−3,447)−3,132=109` ✅.
> 자본 블록 Ⅰ/Ⅱ/Ⅲ 에는 합계 캡션이 **인쇄돼 있지 않다**(대조군: `나.(Ⅰ-Ⅱ+Ⅲ)`·`Ⅲ.기타요구자본(1+2+3)`
> 은 있다 → 그래서 ①은 오탐 0). **면제도 안 만들었다** — 면제할 결함이 아니라 룰이 아니다.
> → 파서 발주 `inbox/parser/20260821T1425Z` (보완자본 한도 3줄 적재). 적재되면 그때 RED 룰로 배선.
>
> **③ KR0079 2023.2Q `8_life` documented exception (티켓 20260821T1300Z)** — owner 승인분.
> **blanket skip 금지 설계**: `_LIFE8_ISSUER_INCONSISTENT` 가 기대잔차(±1,367.4050)를 값으로 들고
> 매 실행 재계산 → 이탈 `RESIDUAL_DRIFT` RED / 결측 `INPUT_MISSING` RED / 무용 `INERT` review.
> **적용전·적용후 둘 다 박제했다** — 발주서가 놓친 두 번째 RED 가 있었다(게이트
> `_transition_mmult_after` 축 17 적용후, 같은 잔차). 적용전만 면제했으면 적용후가 그대로 막았다.
> 변이 4종 전부 통과(면제 끄기 / item17 적용전 +5 / item33 **적용후** −3 / item35 삭제).
> 원장 스키마 신설 `VERIFIED_BY_IMAGE` — 이 PDF 는 **텍스트레이어가 행 단위로 잘려 있어**
> (58p 4,773자, `'3. 시장위험액9,53'` 처럼 값 중간 절단) `absent_markers` 가 **항상 '주장 확인'으로
> 끝나는 무검사**가 된다. 그래서 마커를 쓰지 않고, 대신 **인용 페이지 텍스트밀도를 매 실행 재측정**해
> "기계검증 불가" 주장 자체를 검증한다(>800자/p 면 `EXEMPTION_IMAGE_CLAIM_REFUTED` RED).
> root `TODO.md` 등재 완료.
>
> **④ 별건 2개를 파서로 라우팅** — 둘 다 이번 조사 중 발견:
> - **`item4` 가 공시값이 아니라 자식합으로 덮여 있어 rule 2 가 구조적으로 못 터진다**
>   (적용전 392/392 · 적용후 182/182 완전일치 = 우연 불가. MD 스윕 결과 공시 Ⅰ≠마스터 item4 **124셀**,
>   그중 **122셀이 정확히 자식합**). 범인: `fill_period_to_disclosure.py::_reconcile_item4_from_components`
>   + `recalc_kics_derived.py`. → `inbox/parser/20260821T1420Z`
> - 보완자본 한도 3줄 미적재 → `inbox/parser/20260821T1425Z` (위 ②)
>
> **⑤ 방치 스레드 2건 종결(원 sender = 나).** `check_inbox_hygiene.py` **위반 0** 확인.
> - `20260803T0520Z` (18일) — `validate_data_contract.py` CHECK 2 **2a(iv)** 배선. 사이드카 87셀
>   실사(디스크 부재 0 · 조인 87/87). **`target_q=None` 이 의도적**: 이 마스터는 이력형이라
>   `latest_q` 를 걸면 과거분기 86/87 셀이 STALE_AS_OF 로 터진다. 변이 4종 전부 발화 확인,
>   selftest **P1/P2** 신설 → **51/51 passed**, 게이트 `RED=0 YELLOW=311 exit=0`.
>   **미배선으로 남긴 것**: 마스터 전체 신선도 축(최신 2025.4Q vs 최신분기 2026.1Q) — 공시주기를
>   실데이터로 확정 못 해 근거 없이 걸지 않았다. 배선부 주석에 동일 기재.
> - `20260706T0502Z` (46일) — **옛 숫자로 안 닫았다.** 현재 마스터 재측정: 케이디비 78/78 ·
>   하나생명 78/78(둘 다 "완전 미착수"였던 회사) · `_TRANS_EFFECT_MARGIN` 축 **0건**(마진 완화 불요,
>   `1.0` 유지) · 적용사 item1/2/3/14/27/28 적용후 결측 **0**(하나생명 2024.2Q 제외).
>   파서가 지목한 룰 사각 **배선**: `_after_parent_missing_child_present`(부모후 결측 + 세부후 present
>   = mmult 미가동, review) — 현재 1건 `KR0071 2024.4Q item15후 결측·세부후 4/4 present`.
>
> 테스트: `test_kics_rules_golden`·`test_deploy_assets`·`test_master_tables_golden`·
> `test_post_transition_golden` **13 passed** / selftest **51/51**. 룰엔진(`kics_json_rules.py`)
> **무수정**, 골든 해시 **수기수정 없음**(세션 중 한 번 깨진 것은 파서 write 탓이고 파서가 11:05 재생성).
> `kics_disclosure.json` **무수정**(파서 동시 write 중, 전 변이시험 in-memory).

**(2026-08-21 f) 🔴 자기정정 — 내 미러 룰이 '정의'를 '결함'으로 뒤집어 읽었다. 축 RED 2건 철회.**
> owner 지적: **경과조치 미적용사에게 후 = 전은 정의상 참**이다. (e) 에서 나는 "적용후 입력이
> 적용전과 전부 동일 = 정보량 0" 이라 보고 미러를 통째로 실질평가에서 뺐고, 그 결과
> `36_irr 적용후`·`R2 적용후` 를 "전부 동어반복" 이라며 RED 로 올렸다. **틀렸다** — 그 칸들은
> 조작된 값이 아니라 유일하게 가능한 값이고, 검사한 것은 헛일이 아니라 맞는 값을 확인한 것이다.
> - **적용사/비적용사로 갈라 재측정**(`_TRANSITION_APPLIERS` 18사): `36_irr 적용후` 미러 103건 ·
>   `R2 적용후` 182건이 **전부 비적용사**, **적용사 미러 0건**. 오염은 한 건도 없었다.
> - **탐지기는 살리되 적용사로 좁혔다** — 신설 `AXIS_SELF_MIRRORED_APPLIER`(RED, 셀 단위).
>   여기서 한 겹 더 필요했다: **적용사라도 그 축을 움직이는 종류를 신청 안 했으면 후=전이 정상**이다.
>   실측 `R1 적용후` 미러 **82건이 전부 'AC'(가용자본 자본감소분) 미신청 적용사** — 종류 게이팅
>   없이 "적용사 미러 = 오염" 으로 걸었으면 **82건 전건 오탐**이었다. 그래서 `_AXIS_TRANSITION_KIND`
>   (축→종류, `_TRANSITION_KIND` FSS 붙임-1 정본과 짝)로 게이팅한다. **EQ·INT 는 조건부 발동이라
>   발화 대상에서 제외**(owner UH-5 가 같은 이유로 item19 COPY 룰을 기각한 전례를 따름).
>   현재 라이브 카운트 **0** — 룰이 "없다"고 말할 수 있는 상태가 정답이다.
> - **정정된 평가율**(미러를 평가로 인정): `36_irr 적용후` 실질 **47.0%**(전버킷 21.2%) ·
>   `R2 적용후` **37.6%** · `R1 적용후` 100%. 둘 다 RED 아니고 `AXIS_EVAL_RATE_LOW`(YELLOW).
>   보조지표로 **독립 평가율**(미러 제외 = "후가 전과 달라질 수 있는 칸 중 판정한 비율")도 같이
>   찍는다 — mmult15 64.3 · 17 60.9 · 19 56.7 · R1 48.0 · R5 63.6 · R6 64.9 · R7 52.4 · R8 65.4 ·
>   R2 0.0 · 36_irr 0.0%. **판정에는 안 쓴다**(비적용사 미러는 결함이 아니다).
> - **회귀 그물 N1 교체 + N1b 신설**: N1 = AC 신청사의 적용후 복사 → RED. **N1b = 미적용사 후=전 →
>   finding 0**(오탐 금지 고정). 옛 로직으로 되돌리면 N1b 가 즉시 `AXIS_NOT_EVALUATED` 로 터진다
>   (실검사 확인). **selftest 45/45 → 46/46.**
> - **면제 RED 2건도 소멸** — 파서가 `KR0003 2026.1Q`·`KR0073 2026.1Q` 를 레지스트리에서 해제하고
>   적용후 세부를 재추출했다. 근거 원장의 두 기록은 **고아로 보존**한다: 같은 (회사,분기)가 다시
>   면제로 등재되면 `status=CONTRADICTED` 가 즉시 RED 로 되살린다(반증된 근거의 조용한 부활 차단).
> - **게이트 (같은 데이터 A/B, master sha `2abd154b`)**: `validate_data_contract.py`
>   **RED 0 → 0 · YELLOW 275 → 310**. 즉 **메타룰은 이제 push 를 막지 않는다**(신규 RED 0).
>   YELLOW +35 = 판독불가 20 + 면제 미검증 12 + 평가율 저하 3. 골든 4종 13 passed(룰엔진 무변경).
> - **③④는 그대로 유효**(owner 확인): 면제 근거 원장 + 판독불가 셀 분리는 손대지 않았다.

**(2026-08-21 e) ✅ 메타룰 배선 — "룰이 돌았다"와 "룰이 판정했다"를 게이트가 구분한다. (일부 f 에서 정정)**
> (d) 의 적대적 재검증 결과를 **산문이 아니라 강제 검사**로 굳혔다. **게이트/룰 코드만 고쳤다 —
> `kics_disclosure.json` 무수정(파서 동시 작업 중), 면제 무등재, commit/push 없음.**
> - **① 평가율 = 1급 finding** (`_axis_evaluation_census` / `_axis_eval_findings`). 축 10개 ×
>   컬럼 2개를 항상 표로 인쇄한다. 분모는 **둘 다** 잰다 — 축 그리드(적용전에 대상+입력 1개 이상
>   실재)와 전 버킷. 그리드만 보면 **추출갭으로 입력이 사라질 때 분모도 같이 줄어 평가율이 오히려
>   좋아지는** 거울상 함정이 있어서다. 판정 기준은 평가율이 아니라 **실질 평가율(평가−미러)**.
>   - **RED `AXIS_NOT_EVALUATED`** = 실질 0칸. 근거: 이 저장소는 이미 같은 부류를 RED 로 다룬다
>     (`CAPSEC_SOURCE_UNRESOLVED`·`DIV_CENSUS_SOURCE_MISSING` = "검사축 소실 = 통과 아님").
>     308개 YELLOW 틈의 한 줄로 두면 안 보인다 — 그게 이 저장소가 두 달 데인 방식이다.
>   - **REVIEW `AXIS_EVAL_RATE_LOW`** = 두 분모 중 하나라도 50% 미만(비차단). 50% 는 데이터
>     임계가 아니라 **의사소통 임계**다: 그리드 절반도 못 본 축의 "FAIL 0" 은 정보보다 오해를 준다.
> - **② 자기미러 탐지 — 36_irr 말고 하나가 더 있었다.** 적용후 대상·입력이 **전부** 적용전과
>   수치 동일하면 비교식이 적용전과 글자 그대로 같다(정보량 0). 전수 스캔 결과 **100% 미러 축이
>   2개**: `36_irr 적용후`(103/103) **와 `R2_순자산합 적용후`(182/182)**. R2 는 (d) 에서도 못 본
>   신규 false-green 이다. 나머지 축의 적용후 미러 비중 32~52% → **적용후 검사는 절반가량이
>   전=전 재확인**이라는 사실도 이제 매 실행 인쇄된다(실질: mmult15 63.8 · 17 60.3 · 19 56.1 ·
>   R1 48.0 · R5 63.6 · R6 64.9 · R7 52.4 · R8 65.4%).
> - **③ 면제 근거 원장 신설** `data/_gold/kics_exemption_provenance.json` + 게이트 5룰.
>   면제 레지스트리 5종(+ 신설 축면제)을 전수 대조한다. **레지스트리에 있는데 원장에 기록조차
>   없으면 즉시 RED**(`EXEMPTION_PROVENANCE_MISSING`) — 조용히 새 면제를 추가하는 경로를 닫았다.
>   원장은 **억제 장치가 아니다**: 억제성 키(suppress/exempt/ignore/waive/skip/silence)가 들어오면
>   `EXEMPTION_LEDGER_SCHEMA_INVALID` RED 로 막힌다(원장이 면제기로 변질되는 것을 기계로 차단).
>   - **재검증이 실제로 돈다**: `verify={file,pages,absent_markers}` 를 든 항목은 게이트가 매 실행
>     **그 raw 페이지를 직접 열어** '부재' 주장을 반증한다. 라이브 2건 적발 —
>     `KR0003 2026.1Q`(p24·p25) · `KR0073 2026.1Q`(p15). 두 건 다 **본 세션에서 fitz 로 직접
>     재확인**했다(inbox 메시지를 믿지 않고). 잔여 12건은 `EXEMPTION_PROVENANCE_UNVERIFIED`(review).
> - **④ 판독불가 셀 분리** `SOURCE_UNREADABLE_NOT_VERIFIED`. `세부후결측(후=전)` 246칸을 한
>   덩어리로 세며 사실상 '정당' 취급하던 것을 **원천 판독성으로 갈랐다**: 판독가능 214 · UNREADABLE
>   26 · BORDERLINE 6. 신호는 **raw PDF 텍스트레이어**에서 뽑는다(docling MD 로 대신하면 이번에
>   적발된 면제 2건과 똑같은 실패 모드). 신설 `scripts/build_kics_source_textlayer.py` →
>   `data/_derived/kics_source_textlayer.json`(486셀: READABLE 461 · BORDERLINE 7 · UNREADABLE 18).
>   게이트는 사이드카를 그대로 믿지 않고 **기록된 파일 크기를 디스크와 대조**해 어긋나면
>   `UNMEASURED` 로 강등한다. 실측 분포에 73~103 자/페이지 사이가 비어 있어 하한 100 은 그 빈 구간.
>   KR0010·KR0079 가 룰엔진 `IMAGE_OCR_COMPANIES` 와 정확히 일치(독립 교차확인).
> - **회귀 그물 N1~N7** (`_data_contract_selftest.py`): 7룰 전부 mutation 케이스로 고정.
>   **각 케이스가 룰을 죽였을 때 실제로 FAIL 하는지까지 확인**했다(7/7 BITES) — 우연히 통과하는
>   mutation test 는 없는 것만 못하다. **selftest 38/38 → 45/45.**
> - **게이트 (같은 데이터에 A/B — 파서가 세션 중 마스터를 또 덮어써서 단순 before/after 는 오염)**:
>   `validate_data_contract.py` **RED 0 → 4 · YELLOW 275 → 308**, 델타는 **전부 신규 5룰뿐이고
>   기존 룰 변동 0**. RED 4 = `AXIS_NOT_EVALUATED` 2(R2후·36_irr후) + `EXEMPTION_CITATION_CONTRADICTED`
>   2(KR0003·KR0073). YELLOW +33 = 판독불가 20 + 면제 미검증 12 + 평가율 저하 1.
>   `validate_kics_disclosure.py` exit 2 유지(RED=12 전건 documented + census 2). 골든
>   `test_kics_rules_golden`·`test_master_tables_golden`·`test_post_transition_golden`·
>   `test_deploy_assets` 전부 통과(**룰엔진 무변경 → 골든 매트릭스 무이동**).
> - 🔴 **owner 판단 필요 — 나는 push 를 막았다.** 배선 직전 push 게이트는 RED=0 이었다
>   (ifrs17 레인이 케이디비 R_RSV_9 를 그 사이 해소). 지금 막는 4건은 전부 **owner/parser 해소
>   경로가 있는 진짜 결함**이지만, "0%-평가 축 = RED" 는 내가 고른 정책이다. 완화하려면
>   `validate_data_contract.py` 의 `AXIS_NOT_EVALUATED` severity 한 줄. 축 면제 경로는
>   `_AXIS_NOT_EVALUATED_EXEMPT`(현재 **비어 있음**, 등재는 owner 권한)로 열어 뒀고 등재 시
>   근거 원장 기록이 자동 강제된다.
> - **5% 밴드 측정(요청받은 보고, tolerance 무변경)**: `scripts/_probes/tolerance_band_5pct_audit.py`
>   상주. 8_life·19_market 이 `max(eff_tol, 5%)` 덕에만 통과하는 셀 = **축·컬럼 합쳐 16칸
>   (실제로는 8 (사,분기,축), 전·후가 미러라 두 번 세어짐)** = 평가셀의 **1.1%**.
>   최대 잔차: 삼성생명 2023.2Q 19_market **899.2억**(5% 밴드가 10,525억) · 현대해상 2024.2Q
>   8_life **273.1억** · KB손해 2023.2Q 8_life 161.1억 · KB손해 2024.2Q 19_market 46.4억 ·
>   코리안리 2023.4Q 19_market 45.5억 · 아이엠라이프 2023.1Q 8_life 4.9/9.9억 · 동양생명 2024.2Q
>   5.3억 · AIA 2025.2Q 3.5억. **flat 로 조이면 display 분기 신규 RED 는 4칸뿐**(코리안리
>   2023.4Q·AIA 2025.2Q 각 전·후), 나머지 12칸은 display 밖. "한꺼번에 수십 건이 켜진다"는
>   우려보다 훨씬 작다. **단 이건 적용전/적용후 공통 룰엔진 허용오차라 조이면 골든이 움직인다 →
>   owner 승인 없이는 안 건드린다.**
> - 발주 `inbox/parser/20260821T0620Z` (lane: kics). (d) 스레드 `20260821T0400Z` 는 파서가 쓰는 중이라 안 건드림.

**(2026-08-21 d) 🔴 owner 지시 적대적 재검증 — 어젯밤 수정 1건 REFUTED, 면제 2건 근거 거짓, 미판정 인구 전수 분류.**
> 게이트 재실행이 아니라 **원천(raw PDF/XML) 대조**로만 판정했다. 발주 `inbox/parser/20260821T0400Z`.
> - **⑦ 미판정 인구 (최우선)**: `FAIL=0` 은 평가된 셀 안에서만 참이다. 평가율 = mmult15 97.5% ·
>   mmult17 72.8% · mmult19 71.0% · **36_irr 21.2%** · **R2 37.4%** · R5 93.8% · R6 98.6%.
>   - **룰추론 249셀**(`세부후결측(후=전)`)을 raw 로 전수 판독: **213 = 원천 근거 있음**(210 문서
>     "전·후 동일" 문장 + 3 표 각주) · **3 = 원천이 적용후를 공시하는 추출갭**(신한이지 2024.4Q·
>     2023.1Q, AIA 2023.3Q — **홀수분기 2건은 코리안리와 같은 실패 모드**) · **24 = 스캔본이라 판정
>     불가**(KB손해 5분기·미래에셋 6분기·동양 2026.1Q, 문서 텍스트 145~2,178자) · 9 = 표도 문장도 없음.
>   - **`POST_SCENARIO_ABSENT` 114셀 판정 완료**: 시나리오표 컬럼은 `충격 전|충격 후(평균회귀·상승·
>     하락·평탄·경사)`이고 **경과조치 전/후 축이 원천에 없다**(23/23사 전수 + 흥국화재 2023.2Q p24
>     육안). → 개념상 부재, 면제 **제안**(등재 안 함). **따름정리: 채워진 103셀은 근거 없는 미러라
>     36_irr 적용후 FAIL 0 은 동어반복**이다.
> - 🔴 **`_AFTER_SUBRISK_NOT_DISCLOSED` 면제 2건 근거가 raw 와 불일치**: `("KR0003","2026.1Q")`
>   "②③표 부재(raw 정독 확인)" → **raw p24·p25 에 두 표 전부 존재** · `("KR0073","2026.1Q")`
>   "경과조치 섹션 자체 없음" → **raw p15 에 ②표 전체 존재**. 둘 다 **docling MD 가 그 페이지를
>   떨어뜨린 것**을 "raw 확인"으로 적었다. 해제는 owner 소관.
> - **① 미러링 17셀 CONFIRMED**(코리안리 p10 각주 2개 · 롯데 p25 각주). 단 롯데의 **파서 근거는
>   틀렸다**("표 없어서 앞분기 패턴으로 판단" → 실제로는 표가 있다). 결론만 우연히 맞았다.
> - **② 한화손해 2024.2Q item1후 53541→53537.72 REFUTED**. 같은 필링 총괄표·공통표(raw p14)와
>   2024.1Q·2024.3Q 관례가 전부 `item1후=53541`. 틀린 셀은 item2/3후(②표 단독값). 고칠 값 =
>   `item2후 28722.65 · item3후 24818.70`(합 53541.35). 현재 수정본은 0.75 잔차가 tol 2.0 밑이라
>   **통과할 뿐**이다.
> - **③ 138 재현 성공, "7로 좁힘"은 재현 실패(내 계산 2건)** — TAC 4건은 애초 그 필터 모집단 밖
>   (`item1후≠item1전`). TAC 논거 자체는 raw 참(KDB 2023.2Q p12 `1,077,452+342,955=1,420,407`,
>   기본/보완 불변). 전제조건 없이 전·후 전수 재스윕 → **게이트 tol 밖 위반 0건**. 결함 없음.
> - **④ 케이디비 item5 CONFIRMED** — 2025.1Q raw 에 `적립예정 1,338 / 잔액 1,338` 실재.
>   2026.1Q·2026.2Q 필링의 **전기 컬럼이 둘 다 `-`** 라 2025.4Q 부재가 독립 2회 교차확인.
> - **⑤ 확대 CONFIRMED** — 비적용사 21사에서 mmult 530셀·항등식 1,420셀 실제 평가(0인 회사 없음),
>   **변이 주입 5/5 검출**(축15 신설 포함). 단 7×7·5×5 tol=`max(2.0, 5%)` 라 삼성화재 기준 3,590억까지
>   통과 — 대형사 소액 leg 은 이 축으로 못 잡는다(적용전과 동일 값이라 회귀는 아님).
> - **⑥ 부분 REFUTED** — HEAD 대비 **신설 24행·변경 733셀**. 티켓 명시분은 전부 생존(2차 lost update
>   없음), 적용전 4셀 변경도 raw 로 전건 정당. **단 롯데 2026.1Q item29~35후 7셀은 티켓에 없고
>   값도 원문과 다르다**(예: item31 10031.49 vs raw 10031.61) — 역산 흔적. 그 (사,분기)가 면제라
>   게이트가 영원히 안 본다.
> - **데이터 무수정**(read-only) · **면제 무등재** · commit/push 없음.

**(2026-08-21 c) ✅ 적용후 배선 확대 완료 — 18사→39사 · 축15/36_irr 신설 · 허용오차 적용전과 동일. 신규 4셀.**
> 파서가 데이터를 닫았고(축 A/B/C 전후 FAIL 0, 독립 재확인), **게이트는 안 닫혀 있었다.**
> 파서의 "데이터가 깨끗하니 넓혀도 신규 RED 없다"는 주장을 검증한 결과 **4건이 나왔다.**
> - **바꾼 것 4가지**(`scripts/validate_kics_disclosure.py`): ① `_transition_identities_after` ·
>   `_transition_mmult_after` · `_parent_present_child_incomplete_after` **적용사 18사 → 전사 39사**
>   (비-applier 21사의 적용후 셀 **8,914개**가 적용사 6,089개보다 많은데 통째로 미순회였다)
>   ② `_TRANS_PARENT_SUBS` 에 **축 15**(`sqrt([17-20]·R4)+item21`) 추가 ③ **`_transition_irr_after`
>   신설**(36_irr 적용후, 종전 배선 전무) ④ **적용후 허용오차를 룰엔진(적용전)과 동일**하게 교정.
> - **④가 제일 컸다**: 합-항등식 적용후가 `max(2.0, 0.5%)` 라 53,537억 기준 **267억까지 통과**
>   (적용전은 flat 2.0). 그 틈으로 한화손해 item1후 복사가 새고 있었다. 반대로 비율은 적용후만
>   flat 2.0 이라 카카오페이 micro 3건이 **적용전 GREEN·적용후 RED** 로 비대칭 — 엔진 동적식 쓰니 소멸.
> - **신규 4셀**(동결 스냅샷 A/B: HEAD 0건 → 확대 4건, **기존 검출 소실 0건**):
>   ① **한화손해 KR0002 2024.2Q item1후** = 적용전 복사(raw 5,353,772 → 53,537.72 인데 53541).
>      raw 는 적용후에서도 정확히 닫힌다 → **파서 발주** ② **코리안리 KR1000 2023.3Q** item29~35후·
>      36~39후 **12칸 결측**(앞뒤 분기 present = SANDWICHED, 같은 필링에 기준금액 전=후 확정)
>      → **파서 발주** ③ **미래에셋 KR0079 2023.2Q item17후 mmult 1,367.4** = 값_적용후가 적용전과
>      **바이트 동일** → documented 적용전 `8_life` RED 의 거울, 새 결함 아님 → **owner 승인 후보**
>      (`_AFTER_SUBRISK_NOT_DISCLOSED` 등재 여부. **면제는 내가 등재하지 않는다**).
> - **미판정 축을 숨기지 않는다**: 세 검사 전부 `not_evaluated` 명시 집계 출력. 36_irr 적용후는
>   계산가능 103셀 FAIL 0 인데 **그 103셀의 41~46후가 적용전과 100% 동일**이고 `짝수Q·적용전완비·
>   적용후결측`이 **114셀** → "원천에 시나리오표 전/후 구분이 있나"를 파서 질의(`POST_SCENARIO_ABSENT`
>   로 세어서 보고, RED 로는 안 건다 — 미확인 결측을 결함으로 세지 않는다).
> - **정당한 scope 제한 1건**: `_transition_ratio_after_capture`(후>전 방향성)는 선택경과조치사에서만
>   성립하는 도메인 불변식이라 18사 유지. 나머지 21사는 항등식(R7/R8후)+결측(census 27/28)으로 전사 검사.
> - **회귀 그물 F6~F9 신설**(`_data_contract_selftest.py`): 비-applier mmult / 축15 / 36_irr후 /
>   허용오차 parity. 되돌리면 즉시 FAIL. **selftest 31/34 → 38/38.**
> - 🔴 **덤으로 잡은 게이트 자기검사 사각**: selftest `I1/I2/I3`(17BS 항등식·코어 census·미배포
>   YELLOW)이 `validate_statutory_reserves.py:371 r["생손보여부"]` KeyError 로 **ERROR** 였다 —
>   합성행엔 그 키가 없다. **그 세 룰이 무검증 상태**였는데 두 달간 아무도 몰랐다. 메타 3종을
>   `.get` 으로 교정(라이브 판정 무변화: RED=1 BASELINE=15 확인).
> - **게이트**: `validate_kics_disclosure.py` exit 2 (RED=12 전건 documented + census 2 documented +
>   신규 적용후 4셀) · `validate_data_contract.py` **RED=1 YELLOW=275 exit 2 — 확대 전후 동일**.
>   신규 4건은 전부 `_DISPLAY_QUARTERS` 밖(2023.2Q·2023.3Q·2024.2Q)이라 push 차단 경로에서 걸러진다
>   → **push 차단은 안 늘었다.** 유일 차단 RED = ifrs17 레인 케이디비생명 item5(`R_RSV_9`).
>   골든 `test_kics_rules_golden` 통과(룰엔진 무변경) · 골든/deploy 13 passed.
> - 발주 `inbox/parser/20260821T0155Z` (기존 `20260821T0010Z` 스레드는 파서가 쓰는 중이라 안 건드림).
> - ⚠️ **측정 함정**: 세션 중 파서가 `kics_disclosure.json` 을 덮어써(01:28 KST) 단순 before/after 가
>   오염됐다(YELLOW 560→561 이 내 변경 탓으로 보였다). **마스터를 얼리고 HEAD 게이트 vs 확대 게이트를
>   같은 데이터에 돌려** 분리했다. 공유 트리에서 게이트를 고칠 땐 이 절차를 쓸 것.

**(2026-08-21 b) 🔴 owner 재질의 — 적용후 검사는 룰 10개 중 2개가 아예 없고, 8개는 18/39사만 돈다.**
> owner: *"적용전 기준 테스트는 적용후에도 모두 똑같이 실시하라고 박아놨는데 왜 안 했지?"*
> **지시는 배선돼 있으나 절반만 덮는다.** 코드 실측:
>
> | 룰 | 적용후 검사 위치 | 범위 |
> |---|---|---|
> | R1·R2·R5·R6·R7·R8 | `_TRANS_AFTER_IDENT` | **적용사 18사만** |
> | 8_life·19_market | `_transition_mmult_after` | **적용사 18사만** |
> | **R4(기본요구자본 mmult)** | **없음** | — |
> | **36_irr** | **없음** | — |
> | 9·10·8_post | 룰엔진 `post=True` | 전사 |
>
> 룰엔진 본체에서 `post=True` 를 읽는 곳은 **단 3곳**(9·10·8_post)뿐이다.
> - **전 룰 × 전후 전수**(전사, 입력완비 버킷만): 적용후 고유 FAIL = **R1 1 · R4 9(tol2.0 이면 36)
>   · R6 1 · 8_life 4 · 19_market 1 = 16건**. R7/R8 은 전후 동수(카카오페이 documented)라 제외.
> - **측정 자체를 두 번 틀렸다**(기록): ① `source_has_breakdown` 미전달로 pre 19_market 이
>   RED 131 로 부풀었다 ② 적용후가 원래 없는 항목(item4~13·41~46, 커버리지 47~52%)을 결측이
>   아니라 결함으로 세서 R2 256 · 36_irr 114 로 부풀었다. **결측과 결함을 섞지 말 것** —
>   입력완비 버킷만 판정하고 나머지는 `계산불가` 로 따로 세는 3차 방식이 맞다.
> - **세 번째 축(더 클 수도 있다)**: 적용후 `계산불가` 가 36_irr **383/486** · R2 **304** ·
>   19_market **190**. 적용후 세부항목 커버리지가 절반이라 "적용후도 똑같이 검사"가 지금
>   구조에선 절반만 가능하다. 원천부재인지 추출갭인지 판정 요청을 발주에 추가했다.
> - 발주 갱신 `inbox/parser/20260821T0010Z`. 감사 스크립트 2종 상주:
>   `scripts/_probes/after_column_rule_audit.py`(전 룰 × 전후) ·
>   `scripts/_probes/mmult_after_audit.py`(mmult 3축).
> - 게이트 배선은 여전히 **owner 판단 대기**(R4 적용후를 RED 로 걸면 tol 2.0 기준 36건이 push 차단).

**(2026-08-21 a) 🔴 owner 지시 mmult 전수감사 — 적용후가 안 닫힌다. 내 어제 "0" 발언은 틀렸다.**
> - **정정**: 어제 "적용후 mmult 다 닫힌다"고 보고했는데, 그건 게이트가 찍은 `적용후 mmult
>   불일치: 0` 한 줄을 **시장위험 축에 대해서만** 보고 전체로 일반화한 것이다. 3축 × 전후로
>   전수 재계산하니 **안 닫힌다.**
> - **전수 결과** (행렬은 룰엔진에서 import, 재타이핑 안 함):
>
>   | 축 | 컬럼 | 계산가능 | FAIL(tol2) | FAIL(5%) | 계산불가 |
>   |---|---|---|---|---|---|
>   | A 생명장기 17=f(29-35) | 적용전 | 350 | 5 | 1 | 136 |
>   | A 생명장기 17=f(29-35) | 적용후 | 345 | **10** | 4 | 141 |
>   | B 시장 19=f(36-40) | 적용전 | 340 | 3 | 0 | 146 |
>   | B 시장 19=f(36-40) | 적용후 | 296 | **4** | 1 | 190 |
>   | C 기본요구자본 15=f(17-20)+21 | 적용전 | 484 | **0** | 0 | 2 |
>   | C 기본요구자본 15=f(17-20)+21 | 적용후 | 480 | **36** | 9 | 6 |
>
> - **게이트 검사범위 구멍 2개**(`_transition_mmult_after`): ① `if c not in _TRANSITION_APPLIERS:
>   continue` → **비-applier 회사는 적용후 mmult 를 아예 안 본다** ② `_TRANS_PARENT_SUBS` 가
>   `{17, 19}` 뿐 → **축 C(기본요구자본) 적용후 검사가 통째로 없다.** 게이트의 0 은 거짓말이
>   아니라 범위 밖이었고, 결과는 false-green 이다.
> - **축 C 는 전제가 틀린 게 아니라 데이터가 틀렸다**: 적용전 484/484 PASS(tol 2.0),
>   적용후도 **444/480 이 닫힌다** → 항등식은 적용후에도 성립. 그러니 36건은 셀 결함이다.
>   부호가 ± 섞여 단일 공식오류도 아니고, 회사별 연속분기로 묶인다(흥국생명·에이비엘·농협생명·흥국화재).
> - **산술적으로 불가능한 셀 2건**(가장 확실): 신한이지 2025.1Q `item35후=43` 인데 부모
>   `item17후=10` — **분산 후 부모가 개별 하위보다 작을 수 없다**. 하나손해 2025.2Q
>   `item34후=44.43` = item35 값 그대로(한 칸 밀림). 둘 다 적용전은 깨끗하다.
> - **또 다른 사각**: `계산불가`(하위결측)가 A 136~141 · B 146~190 = 전체 486의 **28~39%**.
>   FAIL 로도 안 잡히고 조용히 넘어간다(SKIP-on-missing 부류). B축 적용후가 최악.
> - **발주** `inbox/parser/20260821T0010Z` (lane: kics). 감사 스크립트 상주:
>   `scripts/_probes/mmult_after_audit.py`.
> - **게이트 배선은 안 했다** — 축 C 적용후를 RED 로 걸면 즉시 36건이 push 를 막는다.
>   배선 방식(즉시 RED / 래칫 baseline / 비차단 관찰)은 **owner 판단 대기**.
> - K-ICS 게이트 자체는 변경 없이 **RED=12 전건 documented** 유지.

**(2026-08-20 l) inbox 재확인 3건 전부 종결(resolved) + 농협생명 item7 등재. baseline 16. RED=0.**
> - 파서가 답한 내 스레드 3건(`20260819T0754Z` · `20260820T0430Z` · `20260820T1900Z`)을
>   전건 원문/원천 대조 후 **resolved** 처리. 잔여는 새 티켓 `20260820T2340Z` 로 이관.
> - ✅ **KB손해 P1 억원 단위오판**: 2021~2022 의 `9,778/10,583` 8칸 제거 확인. 같은 회사
>   2023.1Q = 1,058,272 로 **108배** 차 — 억원 판독이 맞다. 2023년 이후 시계열 무변동·연속.
> - ✅ **분기 22 → 16**: 사라진 6개는 2021·2022 **1~3분기뿐**, 각 6~7행(항목 5/6/7)이고
>   **코어 1/2/3/4 는 0칸**. `IFRS17.html eqYearPeriods()` 는 `.4Q` 만 3개년 역산하고
>   분기모드는 직전 5분기 → **화면 영향 없음** 확인.
> - ✅ **농협생명 item7 legit_flat 등재**: raw 3필링에서 `15,156 − 814 = 14,342` 이후 환입예정
>   `-` 로 잔액 정지, 전기 예정잔액 → 당기 기적립액 이월까지 연속 확인. baseline 17 → 16.
> - **등재하지 않기로 한 것 2건(의도)**: 농협생명 item8 · 롯데손보 item8 은 N/A 판정은 맞지만
>   **R-RSV-9 기대 그리드가 "한 번이라도 공시한 회사"라 행 0개인 (회사,항목)은 그리드 밖**이고
>   실제 finding 이 0건이라 등재하면 죽은 항목이 된다. 재발 방지는 파서가
>   `_P1_CONCEPTS` 옆에 박은 "보증준비금을 여기 추가하지 마라" 주석이 맡는다(확인함).
> - **R-RSV-5 알려진 한계**: 케이디비생명은 **미처리결손금** 상태라 기적립액이 계속 `-` 이고
>   `잔액 = 그 분기 적립예정액` — 누적이 아니라 분기마다 오르내린다(2026.1Q 23,550 → 2Q 4,323,
>   원문 확인). 룰의 "잔액은 누적이라 급변 불가" 전제가 이 구조에 안 맞는 **오탐**이다.
>   비차단(ORANGE)이라 레지스트리에 세 번째 축을 파지 않고 한계로 기록만 한다.
> - 🔴 **새로 드러난 것 — 삼성생명 item5 첫 실관측이 2025.4Q.** 제도는 2023년 시작인데
>   2023.1Q~2025.3Q 가 없다. **뒤채움이 가리고 있던 것이 사본 제거로 드러났다**(그게 목적이었다).
>   단 `disclosed_none` 에 2023.3Q~2024.4Q 6분기가 owner 확정으로 이미 등재돼 있으니
>   실제 조사 대상은 **2025.1Q~2025.3Q · 2023.1Q~2023.2Q**. 티켓 A 항목.
> - **현재**: RED=0 BASELINE=16 ORANGE=51 SUPPRESSED=76 · `validate_data_contract` RED=0
>   YELLOW=276 exit 0 · 13 passed. **push 차단 없음.**

**(2026-08-20 k) 해약환급금준비금 개념 질문 종결 — 개념 안 섞였다. 내 태그 매칭이 틀렸다.**
> - `(j)` 에서 남긴 "회사별 개념 차이" 질문에 파서가 태그로 답했고(`20260820T2210Z`),
>   5개 주장 전부 원천 확인 후 **수용·resolved**. 마스터·게이트 변경 없음(sha `e27cb60f1e52650f`).
> - ✅ **2023년은 기적립액이 0/부재라 `적립액 = 적립예정액`** — 태그 전수 덤프로 확정.
>   2024년부터 둘을 더하고(현대해상 2024.1Q `3,422,425+552,832=3,975,257` = 마스터) 전분기 검산 일치.
>   현대해상 P1 == FS-API(2023.3Q·2023.4Q·2024.1Q 전건). 괄호주기 핸들러는 `HANDLERS =
>   {"KR0008": ...}` 한 회사뿐(파일에 다른 회사코드 0개).
> - 🔴 **내 오류**: 재확인하려고 손으로 짠 태그 매칭에서 `endswith("SurrenderValueReserve")` 가
>   **CIS 의 `dart_AdjustedProfitLossNetOfSurrenderValueReserve`(해약환급금준비금 반영후
>   조정이익)** 까지 물어 "기적립액 670,968 / −80,965" 이라는 유령값을 얻었다.
>   `[[reference-reserve-adjusted-income-table-sign]]` 이 이미 아는 함정이고, 모듈 docstring 의
>   **"자체 파싱 금지, 빌더(`_extract_from_list`)를 호출하라"** 가 정확히 이걸 막는 규칙인데
>   내가 어겼다. 빌더를 쓴 앞선 검사들(삭제 98칸 등)은 정상이었다.
> - **12.5배 차이의 정체**: 현대해상 BS 괄호의 해약환급금 숫자(352,471)는 이 마스터의 item5
>   정의가 아니다 — 같은 괄호에서 비상위험은 `29,265+1,242,298=1,271,563` 로 P1 과 닫히는데
>   해약환급금만 안 닫힌다. 마스터는 현대해상에 그 괄호를 안 쓴다(P1/FS-API 만).
> - **소스 함정 기록(무해)**: 현대해상 FY2024_Q2 P1 표는 헤더가 2분기인데 법정준비금 3행이
>   1분기 값 그대로 stale 이다(책임준비금만 31,495,088→32,685,218 갱신). 마스터는 안 물었다 —
>   FS-API 합 4,218,680 이 들어가 있다. **"FS-API 우선, P1 은 gap-fill"이 실제로 막았다.**
>   기계 가드는 안 넣는 데 동의(정당한 flat 을 같이 버린다). 다만 더 좁은 지문을 기록해 뒀다:
>   "값이 같다"가 아니라 **"같은 표의 다른 행은 갱신됐는데 이 행들만 정지"** 라는 표 내부 모순.
>   P1 이 gap-fill 이 아니라 1순위가 되는 날에 꺼낼 것.

**(2026-08-20 j) 파서 뒤채움 수정 검증 + baseline 재동결 34→17. 래칫 키를 '포함관계+값'으로 교체. RED=0.**
> - 파서가 `20260820T1900Z`(뒤채움 과대계상)를 처리하고 `inbox/validation/20260820T2010Z` 로
>   **baseline 재동결**을 요청. 재동결은 면제 행위라 독립 검증 4종부터 돌렸다.
> - ✅ **삭제 98칸에 실관측 0건** — 전 칸 FS-API 조회, 전부 원천 침묵. 셀 삭제로 결함을 지운
>   흔적 없음(여기가 제일 위험한 지점이었다).
> - ✅ **changed 10칸이 내가 원문에서 읽은 값과 일치** — 삼성화재 556,503 · 메리츠
>   328,904/63,276/50,364/33,839. 현대해상 4칸도 P1 표와 정확히 일치.
> - ✅ **RED 17 = 정확일치 11 + 축소분 6 + 신규 0** (`--no-baseline` 전수 분류). 신규 0 확인 후 재동결.
> - ✅ **골든 재현성**: `test_ifrs17_bs_golden` 386초 통과, **실행 전후 sha256 동일**
>   (`e27cb60f1e52650f`) → 마스터는 빌더 산출 그대로, 손댄 흔적 없음. 백업 후 실행했다.
> - 🔧 **래칫 키를 바꿨다**: 구간 엔트리는 `포함관계 + value 일치`. 각 엔트리에 `value` 필드를
>   넣어 메시지 문자열 파싱을 없앴다. **둘 다 요구**한다 — 포함만 보면 프리즌 안의 '다른 값'
>   새 flat 을 흡수하고, 값만 보면 구간 확대를 통과시킨다. 4시나리오 실검사(동일/축소=흡수,
>   다른값/확장=차단).
> - 🔴 **같은 병을 오늘 두 번 앓았다.** 오전에 `legit_flat` 이 span 정확일치라 이월로 구간이
>   늘자 정당 사유가 RED 로 부활했고 from/to 포함관계로 고쳤는데, **옆 레지스트리(baseline)에
>   같은 병이 남아 있는 걸 못 봤다.** 구간 키를 문자열 정확일치로 잡지 말 것.
> - **현재**: `validate_statutory_reserves.py` RED=0 BASELINE=17 ORANGE=51 SUPPRESSED=75 ·
>   `validate_data_contract.py` RED=0 YELLOW=276 exit 0 · 골든 6종+deploy_assets 15 passed +
>   ifrs17_bs 1 passed. **push 차단 없음.**
> - YELLOW 254→276 은 R-RSV-9 census +19(전건 ORANGE). 뒤채움 사본을 걷어낸 자리가 **정직한
>   결측**으로 잡히는 것 — 지어낸 값보다 빈 칸이 낫다는 원칙대로다.
> - **미결(비차단)**: 해약환급금준비금 2023년 개념이 회사별로 갈릴 수 있다. 삼성화재는 BS
>   괄호주기 `적립예정액`(누적 램프), 현대해상은 P1 잔액(Q3 −23%). 현대해상은 같은 필링의 BS
>   괄호주기가 352,471 로 P1 4,391,552 와 **12.5배** 차이. 파서에 정의 정리 요청함.

**(2026-08-20 i) inbox 드레인 — parser 회신 3건 재검증. 면제는 9구간만 승인, 신규 결함 발주. baseline 34.**
> - **파서의 28건 일괄 면제 요청은 부분 수용.** 28/16 분해는 독립 재현해 숫자까지 일치했고
>   논리("복제를 결함으로 다시 세면 순환")도 옳다. 그러나 **"원천 없음"의 근거가 빌더 자신의
>   추출 결과**라 "필링이 없다"와 "우리가 못 읽었다"가 구분되지 않았다 — 파서가 먼저
>   "사이드카를 그대로 믿지 말라"고 쓴 그 지점이다.
> - 🔴 **(B) 가 실재했다**: 삼성화재 FY2023_Q2 필링에 `(해약환급금준비금 적립예정액:
>   556,503,490,830 원)` 이 그대로 있는데 마스터엔 2023.3Q 값 916,764 이 뒤로 복사돼 있다
>   (**1.65배**). 메리츠 2023.1Q 도 P1 3기간표에 328,904/63,276 이 있는데 마스터는
>   321,055/42,012. `parse_filing()` 에 직접 물려도 **17칸 전부 0/17** — 사람이 읽히는 값을
>   추출기가 못 본다.
> - **면제 기준을 '추출 실패'가 아니라 '필링의 부재'로 바꿔 배선**
>   (`validate_statutory_reserves.rollforward_exempt()`): ① raw 디렉터리 없음 또는
>   `meta.json no_filing:true` **그리고** ② FS-API 캐시도 침묵. → **9구간 억제**
>   (2021~2022 미수집 7 + 서울보증 2024 no_filing 2). **필링이 실재하는 21구간은 면제 안 함.**
>   `carry_forward_exempt()` 와 같은 독립 재확인 구조다.
>   함정: 서울보증은 raw 디렉터리가 **있고 안이 비어 있다**(xml 0개) — 디렉터리 존재만 보면
>   필링이 있는 것처럼 보인다. `no_filing` 을 같이 봐야 한다.
> - **뒤채움 규모 측정**: `rollforward_filled` 355칸 = 앞채움 280 + **뒤채움 75**.
>   뒤채움 연도별 2021=18 · 2022=3 · **2023=43** · 2024=6 · 2025=5. 2023 이 위험한 이유는
>   해약환급금준비금 제도 첫 해라 잔액이 0에서 급증하는 구간이기 때문. **원인은 fold-in
>   (`기적립액+적립예정액`)이 Q4 에만 걸리는 것** → 발주 `inbox/parser/20260820T1900Z`.
> - **에이비엘생명 item7 legit_flat 등재**: FS-API OFS 11개 필링 전수 확인(전부 status=000,
>   `대손준비금 기적립액` 6,336,633,809원 동일, `적립예정액` 라인 없음). **`2023.4Q~` 만 등재** —
>   `2023.1Q~2023.3Q` 는 전수 확인 못 해 baseline 에 남겼다(확인 안 한 셀 등재 = 결함 은폐).
>   근거의 **종류**가 하나손보·비엔피파리바(결손금 서사)와 다르다는 점을 파일에 명시.
> - **카카오페이 재검증 통과**: 원문 6개 값 직접 확인, 기간 배정 정상, 항등식 두 분기 **차 0.0**,
>   item13 한 해 밀림 해소. 그 축은 종결. run1 스레드 잔여 4건(롯데 item8 · 농협생명 item8 ·
>   케이디비 2026.1Q ×17.6 · AIG/메트라이프/BNP item4)은 `iter: 3` 으로 되돌림.
> - 🔴 **내 1500Z 배포 인계문이 stale 이었다** — `dividend.json` 이 그 뒤 1,924→2,043행으로
>   움직였다. 갱신문을 같은 스레드에 붙였다(재검증 전부 통과, 배포 판정은 유지).
>   **오늘 마스터가 여섯 번 움직였고 내 판정문이 stale 이 된 건 두 번째다** — 인계문에
>   "push 직전 게이트 재실행"을 계속 명시할 것.
> - **현재**: `validate_data_contract.py` RED=0 YELLOW=253 exit 0 ·
>   `validate_statutory_reserves.py` RED=0 **BASELINE=34**(44→34) ORANGE=43 SUPPRESSED=84 ·
>   `test_deploy_assets`+골든 3종 13 passed. baseline 축소 10건(면제 9 + 에이비엘 1),
>   신규 RED 흡수 0건 확인 후 `_shrink_log` 기록.

**(2026-08-20 h) 마스터 전수 검증 완료 → publishing 인계. 차단 사유 없음.**
> 인계문 = `inbox/publishing/20260820T1500Z__validation__MULTI__masters_verified_ready_for_deploy.md`.
> - **게이트**: `validate_data_contract` RED=0 exit 0 · `validate_statutory_reserves` RED=0 ·
>   `validate_master_tables --no-build` exit 2(**골든 SUMMARY 문자열 완전 일치 = 동결 상태**) ·
>   `validate_csm_continuity` red=0 · `validate_nb_csm_multiple` 5/5 · K-ICS RED=12(전건 documented).
> - **골든 8종 전부 통과**(16+1 tests). **`test_ifrs17_bs_golden` 이 452초 걸려 초록으로 돌아왔다** —
>   publishing 이 `20260819T0858Z` 로 올렸던 그 stale 골든이고, 배포 전 red 로 남아 있던 유일한 골든이다.
> - **마스터 HEAD 대비 셀 손실 0**: CSM_waterfall·PL_breakdown·kics_disclosure 는 **바이트 동일**,
>   IFRS17_BS 만 5,686→6,953행(+115셀, lost 0). 오늘 마스터가 다섯 번 움직였다
>   (5,389→5,686→6,089→6,729→6,953) — 인계문에 "push 전 게이트 재실행" 명시.
> - **비차단이지만 인계한 3건**: ① master_tables 의 pl_bridge 9F·crosscheck 1F·sens 2R 은
>   CSM_waterfall/PL_breakdown 이 HEAD 와 바이트 동일하므로 **이미 main 에 있는 상태**다.
>   ② K-ICS RED=12 는 documented(내 아침 보고가 틀렸다, 정정함). ③ `prepush_check.py` 가
>   골든을 안 부르는 구조적 구멍 — 이번엔 손으로 다 돌려 확인했다.
> - `test_ifrs17_bs_golden` 은 **마스터를 인플레이스로 덮었다 되돌린다**(452초). 실행 중 다른
>   게이트를 돌리면 재빌드본을 검사하게 되므로 겹치지 말 것. 복원 확인함(6,953행 유지).

**(2026-08-20 g) owner 이월 결정 대응 — census 면제 배선(RED 142→0) + 내 룰 2건 수정. baseline 44.**
> - **BS 코어 census 면제 배선**: 이월로 생긴 (회사,분기)는 그 분기에 회사가 재무제표를 안 낸다.
>   **사이드카를 그대로 믿지 않고** 게이트가 ①4Q 아님 ②raw 부재 또는 `meta.json no_filing:true`
>   두 조건을 독립 재확인한 칸만 면제. 어긋나면 `BS_CARRY_FORWARD_EXEMPTION_REJECTED` RED.
>   (검사받는 쪽이 자기 면제목록을 쓰는 구조 차단 — 2026-08-13 equity 라운드와 같은 지점.)
>   147칸 전수 검증: 코어 존재 0 · 4Q 섞임 0 · 실제 필링 존재 0(raw 있는 27칸은 전부 no_filing 마커).
> - 🔴 **내 R-RSV-1 이 이월 구간을 결함으로 물었다(신규 RED 69)** — hold-forward 는 설계상 flat 이라
>   필연이다. 첫 분기 뒤가 전부 이월 칸이면 SUPPRESSED 로 수정. **검증 로직은
>   `validate_statutory_reserves.carry_forward_exempt()` 단일 소스로 합쳤다**(두 벌 금지).
> - 🔴 **legit_flat 이 span 정확일치라 깨졌다(내 버그)** — 이월로 하나손보 구간이 2025.4Q→2026.2Q 로
>   늘자 등재해 둔 정당 사유가 RED 로 되살아났다. **from/to 포함관계**로 변경(to=null 열린 구간).
>   → **교훈: 구간 키를 문자열 정확일치로 잡지 말 것.** 데이터가 자라면 면제가 조용히 풀린다.
> - **신규 legit_flat**: 비엔피파리바카디프생명 item7(166.46) — 연간필링 2개에서
>   `기적립액 166,460 / 예정액 - / 잔액 166,460` 동일 + 미처리결손금 확대 확인. 하나손보와 같은 구조.
> - **현재**: `validate_data_contract.py` RED=0 YELLOW=254 exit 0(이월 직후 142였다) ·
>   `validate_statutory_reserves.py` RED=0 BASELINE=44 ORANGE=43 SUPPRESSED=74 · 테스트 10 passed.
> - **앵커 제안 철회**: 이월로 마스터가 경제적 실질을 반영하므로 룰에서 또 연1회 필러를 보정하면
>   이중이다. 2023년말 -0.9% · 2026.6말 +4.9% 로 owner 종결조건 ±5% 충족.

**(2026-08-20 f) owner 지시로 삼성생명 2026.2Q item6 행 삭제 — R-RSV 발주 종결. baseline 45.**
> - 삭제는 **두 곳**: `data/dart/viz/bs_manual_overrides.json` 의 `KR0069|6|2026.2Q`(원천) +
>   `IFRS17_BS.json` 행. **오버라이드가 원천이라 마스터만 지우면 재빌드에 되살아난다.**
>   삭제 이력은 그 파일 `_removed` 에 사유와 함께 보존. 마스터 쓰기 전 **mtime 경합 검사** 적용
>   (파서 동시 작업 중이라 읽는 사이 변경되면 쓰기 취소).
> - **R-RSV-8·R-RSV-9 는 RED 에서 완전히 빠졌다.** baseline 58→48→46→**45, 전부 R-RSV-1 한 종류**.
> - 게이트 RED=0 YELLOW=254 exit 0 · `test_deploy_assets.py` 10 passed.
> - owner 발주(20260819T0558Z) 종결. 잔여 45건은 파서 발주(`inbox/parser/20260820T0430Z`).

**(2026-08-20 e) legit-zero registry 등재 완료(owner 승인) + census 룰 2차 수정. baseline 46.**
> - **owner 승인분 등재**: 삼성생명 보증준비금 2024.4Q·2025.4Q · 푸본현대 대손준비금 2023.4Q.
>   전부 원문에서 `기적립액 전액 = 환입예정액 → 잔액 0` 확인(삼성 12,297/(12,297), 푸본 47,622/(47,622)).
>   기존 케이디비생명·하나생명분과 합쳐 **R-RSV-6 전이 5건 전부 SUPPRESSED**.
> - **자기정정**: 처음에 두 회사의 0인 분기를 **전부 18셀** 등재했다가 되돌렸다. 원문 확인은
>   3분기뿐인데 나머지를 넣은 건 "확인했다"는 거짓 주장이고, 내가 파서에게 경고한 결함 은폐와
>   같은 행위다. 확인분만 남겼다. **레지스트리 등재는 확인한 셀만.**
> - **census 룰 2차 수정**: '첫 공시 이전 부재 = ORANGE' vs '첫 공시 이후 구멍 = RED' 로 분리.
>   비상장사 감사보고서에 이익잉여금 구성내역 표가 없는 경우가 있다(악사손해보험 2022.4Q 실측:
>   `비상위험준비금` 3회가 전부 회계정책 주석 2.18, 값 행 0). **R-RSV-9 는 RED 에서 완전히 빠졌다.**
> - **되풀이되는 병 하나로 정리**: 기대 그리드를 "데이터가 있는 범위"로 잡으면
>   **downloader 가 과거 raw 를 정직하게 채울수록 RED 가 늘어난다.** 오늘 이 함정에 두 번 걸렸다
>   (아이엠라이프 2022.4Q · 악사 2022.4Q). **다른 census 룰에도 같은 점검을 걸 것.**
> - **현재**: `validate_statutory_reserves.py` RED=0 BASELINE=46(R-RSV-1 45 + R-RSV-8 1)
>   ORANGE=44 SUPPRESSED=6 · `validate_data_contract.py` RED=0 YELLOW=254 exit 0 ·
>   `test_deploy_assets.py` 10 passed. baseline 58→48→46.
> - **owner 판단 대기 1건**: 삼성생명 2026.2Q item6=0 삭제 여부(owner 수기 입력).
>   지우면 R-RSV-8 이 0 이 되고 baseline 은 45(전부 R-RSV-1)만 남는다.

**(2026-08-20 d) 파서가 내 R-RSV-9 룰 버그를 잡았다 — 수용·수정 완료. baseline 58 → 48.**
> - **내 룰이 틀렸다**: R-RSV-9 census 가 기대 그리드를 "그 회사가 BS 를 가진 모든 분기"로 잡아
>   **제도 시행(2023) 이전 분기까지 요구**했다. R-RSV-7 은 같은 분기를 "nonzero 면 오추출"이라
>   보는데 census 는 "없으면 결측"이라 세는 **자기모순**. downloader 가 2022.4Q raw 를 채워
>   넣자마자 아이엠라이프가 신규 RED 2건이 되어 push 를 막았다.
>   → **"raw 를 정상적으로 채울수록 RED 가 늘어나는 구조"**(파서 표현). census 룰 일반의 함정이니
>   **다른 census 룰에도 같은 점검을 걸 것**(기대 그리드를 데이터 범위가 아니라 제도·규정 범위로).
> - **수정**: `item in (5,8) and _qk(q) < SURRENDER_START` → 그리드 제외. 근거 실측 —
>   마스터 전체에서 2023.1Q 이전 값은 item5 4건(전부 코리안리, R-RSV-7 이 문다) · **item8 0건**.
> - **신설 `data/_gold/statutory_reserve_legit.json`** — baseline(미해결 결함)과 **반대 개념**:
>   `disclosed_none`(원문 "적립한 내역은 없습니다" → census 제외) ·
>   `legit_flat`(적립 중단 정당 사유 → R-RSV-1 제외). 각 항목이 **raw 원문 인용 + verified_by** 필수.
>   등재: 교보생명 item5 8셀 · 삼성생명 item5 6셀(둘 다 "적립한 내역 없음" 원문 확인) ·
>   하나손해보험 item6 2022.4Q~2025.4Q(미처리결손금 2,210억으로 적립 중단, 원문 확인).
> - **절차 확립**: 파서는 이 레지스트리에 직접 못 넣는다(결함 은폐 방지). **근거 제시 →
>   validation 원문 확인 → 등재** 왕복이 정상 경로다. 파서가 baseline 에 임의 추가하지 않은 것도 옳다.
> - **결과**: baseline 58→48(R-RSV-9 12→2, 잔여는 케이디비생명 item5 6셀·item8 2셀뿐) ·
>   `validate_data_contract.py` RED=0 YELLOW=255 exit 0 · `test_deploy_assets.py` 10 passed.
>   축소 시 **신규 RED 흡수 0건** 확인 후 해소분만 제거(`_shrink_log` 기록).
> - **앵커 원인 정정**: 2024.6말 -19.3% 는 셀결측 3사가 아니라 **연1회 공시사 8사(2023.4Q 합 5.8조)**
>   가 중간분기에 행이 없어서다. FY말 잔액 이월은 owner 판단 대기이나, **앵커 룰에서 연1회 필러를
>   직전 4Q 로 캐리해 비교**하면 마스터를 안 건드리고 해결된다 — 파서에 의견 요청함.
> - 2023년말 앵커 -5.5% → **-1.4%** (owner 종결조건 ±5% 충족).

**(2026-08-20 c) R-RSV 룰 배선 완료(래칫 baseline) + legit-zero registry 등재 + K-ICS RED=12 진단.**
> - **신설**: `scripts/validate_statutory_reserves.py` (룰 단일 소스) ·
>   `validate_data_contract.py::check_statutory_reserves()` 로 호출 → **prepush_check 경로에 실제 배선.**
>   `data/_gold/statutory_reserve_baseline.json` (래칫 58건 건별 열거).
> - **설계 결정 — 부호 프레임 게이팅은 넣지 않는다(어제 계획 폐기).**
>   `build_equity_composition_tier2.py:495` 가 `net_income_framed and concept != "보증준비금"` 로
>   **개념별 예외**를 둔다. 프레임 반전도 보편 규칙이 아니고 그 지식은 빌더에 있다.
>   게이트가 재구현하면 두 벌이 갈라지고 갈라진 쪽이 틀리면 **옳은 데이터를 RED 로 막는다**
>   (어제 A-1 이 그 실패). → 룰은 **빌더가 확정한 마스터만** 본다. R-RSV-4/12 도 자체 파싱 대신
>   `build_ifrs17_bs._extract_from_list` 호출(FS-API 350셀 대조, 불일치 0).
>   **부호 로직을 고칠 일이 생기면 빌더 한 곳만 고치면 된다.**
> - **래칫 방식**: 기존 결함 58건(R-RSV-1 45 · R-RSV-9 12 · R-RSV-8 1)만 비차단 BASELINE,
>   목록에 없는 새 RED 는 즉시 차단. 일괄 면제가 아니라 (rule,company,item,quarter) 건별
>   열거라 CLAUDE.md documented-exception 계약을 기계검사로 만족. 발주 `inbox/parser/20260820T0430Z`.
> - **legit-zero registry**: `user_pl_confirmed_cells.json` 에 master="IFRS17_BS" 10셀 등재
>   (케이디비생명 보증 6분기 · 하나생명 대손/보증 각 2분기). `SUPPRESSED` 로 표시하고 넘어간다.
>   미판정 2건(삼성생명 항목8 · 푸본현대 항목7)은 원문 미확인이라 미등재.
> - **게이트 현황**: `validate_data_contract.py` RED=0 YELLOW=263 exit 0 ·
>   `validate_statutory_reserves.py` RED=0 BASELINE=58 ORANGE=41 · `test_deploy_assets.py` 10 passed.
> - **K-ICS RED=12 진단 완료** → `inbox/parser/20260820T0400Z`. 3개 (회사,분기), 원인 전부 다름:
>   하나생명 2024.2Q = **텍스트레이어 0자 스캔 PDF**(면제도 정당) / 동양생명 2023.2Q =
>   **PDF엔 있는데 docling MD 가 떨궜다**(기본자본 raw 5회 vs MD 0회, 면제 대상 아님) /
>   미래에셋 2023.2Q = 8_life mmult 차 1,367.4, 타 분기는 전부 0.0 으로 닫힘 → 그 분기만
>   parsed MD 부재(raw 58p 에 텍스트 4,859자)라 값 출처가 다름.
> - **미이행(정직)**: baseline 58 축소는 parser 몫 · 삼성생명 2026.2Q item6=0 은 owner 판단 대기 ·
>   **골든 테스트 미작성** — 산출이 `IFRS17_BS.json` 에 붙어 있고 그 마스터가 파서 작업으로
>   실시간 변동 중(오늘만 5,389→5,686→6,089행). 안정된 뒤 만든다.

**(2026-08-20 b) answered 백로그 21건 전량 드레인 (16 종결 / 5 iter++). 신규 RED 2종 발견 — push 막힘.**
> owner escalate(`inbox/validation/20260820T0210Z`) 대응. 상세 근거표는 그 답변란이 정본.
> - **21 → 0.** 전체 프로젝트 `answered` 51 → 33. 일괄 resolve 안 했고 건별로 재현·실측 기재.
> - **K-ICS transition 계열 잔여는 3티켓 · 5개 (회사,분기)로 수렴**(전부 SANDWICHED =
>   앞뒤 분기엔 적용후가 있는데 그 분기만 없음): 하나손보 2023.2Q · 하나생명 2023.2Q ·
>   IBK 2023.2Q · 악사 2024.3Q · 처브 2024.3Q. **`TODO.md`의 "census 결측 4 + continuity
>   break 34셀/5"는 오늘 게이트 출력과 글자 그대로 일치 = 안 고쳐진 것.**
> - 🔴 **`validate_data_contract.py` RED=8 (exit 2)** — 카카오페이손해보험 2024.4Q·2025.4Q
>   코어 4항목 결측. 오늘 IFRS17_BS 확대(5,389→5,686행)로 그 회사 행이 처음 생기며 census에
>   걸렸다. raw 있음 → parser 발주(`inbox/parser/20260819T0754Z` 추가절).
> - 🔴 ~~**`validate_kics_disclosure.py` RED=12 — `TODO.md` 미등재 = 게이트 계약 위반**~~
>   **← 2026-08-20T1400Z 정정: 내가 틀렸다.** `TODO.md` line 10 + 113~119 에 세 건
>   (KR0087 2023.2Q ×7 · KR0097 2024.2Q ×4 · KR0079 2023.2Q 8_life ×1) 전부 documented
>   exception 으로 등재돼 있다("gate contract satisfied"). grep 을 잘못해 놓쳤다. **push 비차단.**
>   단 KR0087 동양생명 등재 사유 "이미지 전용(텍스트 부재)"는 **사실과 다르다** — PDF 텍스트
>   77,229자에 기본자본 5회·보완자본 8회가 있고 docling MD 만 0회다. scan-only 가 아니라 변환
>   누락이라 **재변환하면 RED 12→5**. 티켓 우선순위 HIGH→LOW.
> - **내가 틀렸던 것 기록**: ① R-RSV A-1(NH농협손보 2026.2Q) 297,481 발주 → 파서 반박이 맞음,
>   정답 309,489(조정이익 프레임 괄호=차감표기). ② transition F1 "item2 후=전" 전제 →
>   다중경과조치사(에이비엘·푸본현대)엔 성립 안 함, 준비금경과조치 증분이 item2로 들어간다.
> - **미이행 2건(내 몫, 확정)**: R-RSV 부호 프레임 게이팅 · C절 legit-zero registry 등재
>   (케이디비생명 항목8 / 하나생명 항목7·8). 둘 다 다음 착수분.
> - **프로세스 변경**: 검증 라운드 첫 단계에 **자기 answered 드레인**을 넣는다. 오늘 21건 중
>   16건이 이미 끝나 있었는데 두 달간 아무도 몰랐다.

**(2026-08-20) 게이트 구멍 발견 — `prepush_check.py`가 골든/pytest를 하나도 안 부른다. 배선 대상 접수.**
> - **사실**: `scripts/prepush_check.py`는 `validate_data_contract` + `triage_anomaly_candidates`
>   **둘만** 호출한다. pytest·골든 미호출 → `tests/test_ifrs17_bs_golden.py`가 RED인 채로
>   push가 main에 올라갔다(`fca6560`). 데이터 자체는 publishing이 combo-diff·데이터계약·
>   항등식 356건·라이브로 별도 검증해 실피해 없음. 하지만 **골든의 존재 이유(의도치 않은 빌더
>   drift 차단)가 push 경로에 배선돼 있지 않다** — owner가 R-RSV 티켓에서 경고한
>   "절반만 굳은 상태"와 동일 패턴. `[[incident-postmortem]]` 대상.
> - **골든 FAIL 재현**(514초): rows 5,389 → **5,686**(publishing 보고 5,587은 stale).
>   publishing이 "준비금 계열만 늘었다"고 했으나 **총계 1/2/3(303→325/325/323)과 AOCI 4(305→329)도
>   늘었다** — 2023.1Q·2023.2Q raw 백필이 들어온 결과. 승인 판단 시 준비금만 보면 안 된다고
>   `inbox/parser/20260819T0858Z`에 기록.
> - **경합 주의**: 이 골든은 `IFRS17_BS.json`을 8분 30초간 덮었다 되돌린다(백업·복원 실측 확인,
>   마스터 무손상). **파서 작업 중에는 돌리지 말 것.**
> - **R-RSV 착지 재확인**: 흥국화재 2026.2Q 총계 **해소**(항목 1~7 보유). 미해결 잔여 —
>   2025.4Q 총계 결측 5사(AIG손보·IBK연금·메트라이프·BNP카디프·하나손보) ·
>   롯데손보 항목8 행 부재 · KDB생명 항목5 FY2025 고정 · 농협생명 항목8 결측 ·
>   삼성생명 2026.2Q 항목6 `0`(owner 대기).
> - **E절 2022년말 앵커**: owner가 2022.4Q 준비금 raw 수집을 **보류** 결정
>   (`inbox/parser/20260819T0841Z` E항). 코리안리 21,575 검증은 그때까지 대기.
>   별건으로 연차-only 5사 FY2022~2024 감사보고서 21건은 수집 완료.

**(2026-08-19 b) R-RSV iter 2 — 파서가 A-1을 반박했고 그 반박이 맞다. 룰 명세 정정 + 배선 보류.**
> - **내 A-1이 틀렸다**: NH농협손보 2026.2Q 항목6을 297,481로 보고했으나 정답은 **309,489**.
>   `반영전 71,666 − (6,004) = 반영후 65,662`로 표 산수가 닫힌다 — **조정이익 프레임의 괄호는
>   "이익에서 차감"이고 준비금은 증가**다. 잔액표 관례를 그대로 적용한 오판.
>   (`[[reference-reserve-adjusted-income-table-sign]]`에 이미 있던 함정을 내가 적용 못 했다.)
> - **룰 명세 구멍 — owner에 반송**: R-RSV-2/3이 "괄호=음수"를 무조건 전제한다. 표 종류로
>   갈라야 한다 — 조정이익 프레임=반전 / 잔액표·BS=그대로 음수. 판별은 캡션이 아니라
>   **표 안 산수**. 반대 방향 검증 통과: 삼성화재 항목6 2025.4Q △179,350은 진짜 환입
>   (2,841,361−179,350=2,662,011). 재배선 시 `_NET_INCOME_FRAME_MARKERS` 게이팅 재사용.
> - **게이트 배선 보류 사유 확정**: 부호 프레임 게이팅 없이 배선하면 조정이익 프레임 회사가
>   전부 오탐으로 push를 막는다. 게이팅 먼저.
> - **착지 확인**(5,571→5,587행): NH농협손보 309,489 / AIA 2023.4Q 항목5 761,784·항목8 146,020 /
>   흥국화재 2026.2Q 준비금 3종 owner값 / 한화생명 7,058,650. **마스터 음수 준비금 0건**,
>   owner R-RSV-2 근거 3셀 전부 양수 복구.
> - **미해결**: 흥국화재 2026.2Q 총계 3종(+2025.4Q 5사) · 롯데손보 항목8 행 부재 ·
>   KDB생명 항목5 FY2025 고정 · 농협생명 항목8 C-2 판정 · R-RSV-1 RED 62건(ORANGE 5→19).
> - **owner 판단 대기**: 삼성생명 2026.2Q 항목6 `0`(owner 수기 입력이라 파서가 못 지움).
>   앵커 집계에서는 제외해 계산한다.

**(2026-08-19 a) 법정준비금 룰 R-RSV-1~12 1차 실행 완료 — 파서 발주 나감, 게이트 배선은 미이행.**
> - 입력: owner 룰 티켓 `inbox/validation/20260819T0558Z` (status: answered).
>   출력: `inbox/parser/20260819T0754Z__validation__MULTI_2025.4Q_2026.2Q__statutory_reserve_rules_run1.md`.
> - **실행 시점**: owner 티켓은 "파서 작업 종료 후"였으나 owner가 **2025.4Q·2026.2Q는 파서가
>   손대지 않는다**고 확인 → 그 두 분기만 확정 결함(A절)으로 발주, 나머지는 참고(B~G절, 재실행 필요).
> - **확정 결함 5건(원문 확인)**: NH농협손보 2026.2Q 항목6 `769,073` → 정답 `297,481`
>   (이익잉여금 표 303,485 + 적립예정 △6,004) / 삼성생명 2026.2Q 항목6 `0` — 생보에 손보 전용
>   개념, 행 삭제 / 흥국화재 2026.2Q 총계 3종(항목1·2·3) 결측 + 2025.4Q 동일 형태 5사 /
>   롯데손보 항목8 zero-vs-missing / 케이디비생명 항목5 FY2025 4분기 고정.
> - **오탐 4건을 원문 대조로 폐기**: 흥국생명 항목5 · KDB생명 항목8 · 하나생명 항목7/8.
>   전부 마스터가 옳았다(적립예정액 부호 / 환입 상계 잔액 0). **legit-zero registry 등재 요청**을
>   같이 보냈다 — 없으면 매 실행 재플래그(`[[project-owner-confirmed-registry]]` 두더지 패턴).
> - **R-RSV-1 RED 62건** (3분기 연속 또는 FY경계+4Q 동일). 최악: DB생명 항목8 14분기,
>   에이비엘 항목7 11분기, 농협생명 항목7 10분기 고정.
> - **R-RSV-10 앵커 정정 제안**: 2026.6말 -8.1%는 계통오차가 아니라 **연차-only 필러 8사**가
>   반기에 값이 없는 구조 탓(직전 4Q 합 약 4.95조). 앵커는 연차 필러를 직전 4Q로 캐리해 비교할 것.
>   2023년말 -3.8% 통과 · 한화생명 개별 앵커 -0.7% 통과.
> - **R-RSV-2/3 마스터 0건은 false-green 성격**: 빌더가 배출 시점 `abs()`로 부호를 지운다.
>   소스 음수 19건(전부 DB손해보험)이 그대로 흡수 — 룰은 **소스단에서도** 검사해야 한다.
> - **잔여 (UH)**: ① `prepush_check.py`가 실제로 부르는 게이트에 R-RSV 배선 ②
>   legit-zero registry 신설 ③ census 기대그리드를 "마스터 BS 유무"가 아니라 **raw 필링 유무**로
>   전환(흥국화재 2026.2Q가 그리드에서 조용히 빠졌다) ④ 배선 후 `test_master_tables_golden` 갱신.
>   A절 수정이 반영돼 값이 안정된 뒤 착수하는 게 맞다고 판단.

**(2026-08-17 c) 예별 부호 건 종결 — 2023.4Q 는 내가 맞고 2025.4Q 는 파서가 맞다. `CSM_SIGN_CONVENTION` 배선 완료, RED=0 유지.**
> - **2023.4Q 정정 반영 확인**: 신계약 **+509.7** · 이자 **+203.1** · 조정 **+477.5** · 상각 **△471.8**, 잔차 0.0.
>   전사 `상각>0` 위반 **0건**이 됐다.
> - **2025.4Q 는 내 요청이 틀렸다(정정)**. raw(20260406003175) 확인 결과 상각 **(17,399,016) 음수** ·
>   RA **+786,646 양수** = 표준 부호다. 2023.4Q 와 같은 역전이 아니다.
> - **다만 파서가 근거로 쓴 폐쇄식 덧셈검산은 성립하지 않는다(중요)** — **기말=0 이면 판별식이 퇴화**한다
>   (`기초−Σ변동 = 2×기초` 라 뺄셈은 애초에 못 닫히고, 덧셈이 닫히는 건 Σ변동=−기초 이기 때문).
>   **진짜 판별식은 상각 행 부호**다. 2024.4Q 는 기말≠0 이라 그 검산이 유효했다.
> - **음수 원인 확정**: 예별은 `손실부담계약의 인식(환입)` 을 **CSM 열 안에** 표시한다
>   (표준은 그 행의 CSM 열을 비운다 — 라이나 동일 표로 대조). 그래서 신계약인식효과 행이 onerous 분을
>   net 한 값으로 찍히고 행 합계가 0 으로 닫힌다. **공시 표기를 그대로 옮긴 값.**
> - **배선**: `CSM_SIGN_CONVENTION`(신계약<0 또는 상각>0 = RED) + `_CSM_SIGN_EXCEPTIONS` 1건
>   (예별 2025.4Q, 사유 전문 등재). 예외는 조용히 사라지지 않고 `..._EXCEPTED` **YELLOW 로 사유와 함께 계속 보인다.**
>   `--selftest` **34/34**(M1 신설), 게이트 **RED=0 / YELLOW=224 (exit 0)** — 배포 영향 없음.
> - **타사 스윕 발주 취소**: 이 서식의 지문이 `상각>0` 인데 **전사 355블록 중 위반 0건**이라
>   회사별 raw 대조 없이 마스터 전수 스캔으로 끝났다. 이제 그 스캔은 룰로 상시화됐다.
> - 스레드 2건 종결 → `inbox/_resolved/`.

## Status (이전)

**(2026-08-17 b) 예별 CSM 부호 — parser 의 "추출 정확, 회계판단 필요" escalate 를 raw 재계산으로 반박. 추출 버그 확정.**
> parser 티켓 `inbox/validation/20260817T1159Z…negative_new_business_csm.md` → **answered(반박)**.
> - **결정적 근거**: 그 필링의 CSM 표가 **`기말 = 기초 − Σ변동`** 으로 닫힌다
>   (605,551,876 − (−71,849,290) = 677,401,166, PV 열도 동일). 즉 **변동 블록은 손익(P&L) 기준**,
>   잔액은 부채 기준인데 추출기가 변동 행 부호를 그대로 옮겼다. 상각이 +인 건 그게 보험수익이라서다.
> - 신계약인식효과 행의 **RA 가 음수(−9,065,634)인 것 자체가 성립 불가** — 셋을 뒤집으면
>   `PV 순유입 / RA 부채 / CSM 양수` 로 전부 표준이 된다(라이나 같은 표는 이미 그 부호다).
> - **확정값(억)**: 신계약 **+509.7** · 이자 **+203.1** · 상각 **△471.8** · 조정 **+477.5**
>   (기초 6,055.5 / 기말 6,774.0 불변). 검산 정확히 닫힘.
>   **조정 477.5는 역산이 아니라** raw 의 `추정치 변동분(15,458,725) + 손실부담(32,291,082)
>   = 47,749,807천원` 과 독립 일치 — 부호를 뒤집었더니 raw 행 합과 맞았다.
> - **왜 못 잡았나**: 마스터의 조정이 **잔차(plug)** 라 셋이 뒤집혀도 폐쇄식이 닫힌다.
>   라이나 건(조정이 계약경계 효과를 흡수)과 **똑같은 함정** — 폐쇄식은 이 클래스에 무력하다.
> - 발주: 2023.4Q 정정 + 2025.4Q 동일 확인 + **타사 스윕**(판별식 `기말 == 기초 − Σ변동` 이면 손익 기준 필링).
> - `CSM_SIGN_CONVENTION` 배선은 **정정 후**. 지금 걸면 RED=3 으로 2026.2Q 배포가 막히는데,
>   정정되면 위반 0 이라 배포와 충돌하지 않는다.

## Status (이전)

**(2026-08-17) push 게이트 RED=0 — 배포 차단 해제. 교차대조 340쌍 전수 정상. inbox 5건 종결.**
> AIG 2023.4Q raw 가 downloader 를 통해 들어와 마지막 1건이 닫혔다.
> PL item4 = 22,760.117백만원(= **227.60117억**) vs 같은 분기 워터폴 상각 227.6억 — 소수점 4자리 일치.
>
> | 검사 | 결과 |
> |---|---|
> | `validate_data_contract.py` | **RED=0 / YELLOW=223, exit 0** |
> | PL↔워터폴 교차대조 전수 | **340쌍 정상 340 / 문제 0** (2026-08-15 시점 305/12/22 → 전부 해소) |
> | 셀 유실 | **0** (PL 8,543→8,554행, +11 = 코리안리 신규 서브LOB) |
> | `--selftest` | **33/33** |
> | `validate_master_tables --no-build` | `closing 356P/0F/0S` · `zero_legs 11→4` · `pl_bridge` 8F 불변 |
> | 골든 3종 | 전부 PASS |
>
> - **배포 GO**: `inbox/publishing/20260815T1400Z…` 최상단에 GO 표기. 배포 후 라이브에서
>   **삼성화재 2026.2Q 패널이 0 이 아닌지** 눈으로 확인 요청(이 사고의 발단).
> - **종결 5건** → `inbox/_resolved/`: LIVE legs(12사 코드수정) · viz 골든 · item16 · AIG fetch ·
>   xcheck. **파서가 밝힌 근본원인**은 DART 가 2026.2Q 반기보고서부터 CSM상각 행 라벨을 재구성한 것
>   (+ 현대해상만 공시단위 원→천원, + 3개월/누적 컬럼 오선택, + 롯데 FS-API 캐시 013 고착).
>
> **신규 발주 1건(비차단)** — `inbox/parser/20260817T0400Z…item9_withheld_because_rule_tolerates.md`:
> parser 가 AIG item9 을 raw 에서 찾아 놓고 *"룰이 item4 단독 비교라 문제 없음"* 을 근거로 비워 뒀다.
> **게이트를 품질의 하한이 아니라 상한으로 쓰는 판단**이라 지적했다. 내 룰의 `item9 or 0` 이
> 결측을 흡수하는 것도 사실이라 절반은 내 책임 — 다만 정당 결측(28건 중 대다수)과 구분할 근거가
> 없어 룰은 아직 안 조인다.
>
> **미해결로 남긴 것(추적)**: ① `sensitivity_heatmap.json` 비결정성(unit_source xref/default 왕복 →
> 값 1000배 진동, 골든 신뢰불가) ② 흥국화재 item13/14 `cum()` 컬럼계산 버그(값 null 유지)
> ③ `extract_tier2_abl`·`_oll_ytd` 는 코드가 아니라 override 로만 고쳐진 상태 ④ **배포 직전
> main 기준 게이트 재실행 절차화**(이번 사고의 구조적 원인, 여전히 미배선).

## Status (이전)

**(2026-08-17) 교차대조 RED 21 → 1. 파서 답신 전수 재검증 통과, 남은 1건은 downloader 로 라우팅.**
> `inbox/_resolved/20260815T1400Z…pl_csm_amort_xcheck_gaps.md` 종결.
> - **전수 재측정**: 교차대조 340쌍 중 **정상 339 / 배수이탈 0 / 한쪽만 빔 1**(HEAD 는 305/12/22).
>   `RED 21 → 1`, 셀 유실 0(PL 8,543→8,554 = 신규 11), `--selftest` 33/33, 골든 3종 PASS.
>   `validate_master_tables --no-build`: `closing 355P/1S → 356P/0F/0S`, `zero_legs 11 → 4`, `pl_bridge` 8F 불변.
> - **값이 맞다는 근거 = 배수 수렴.** 고친 자리의 PL/워터폴 배수가 **0.33~0.52 → 0.99~1.04**
>   (교보 7블록·DB생명 6블록·동양 2026.2Q 등). 2Q 0.5 / 3Q 0.35 는 **누적 대신 당분기 컬럼**을
>   실었던 전형적 지문이고, 서로 다른 note 에서 독립 추출된 두 값이 1.0 으로 붙는 건 우연이 아니다.
>   라이나 item9(−3,162,314 → −7,365.0)·미래에셋 2026.2Q(조정 −624.5 → +503.8, 폐쇄식 재검산 통과)도 동일 방식으로 확인.
> - **정정 1건 — "raw 없음"을 그대로 받지 않았다.** parser 가 AIG 2023.4Q 를 *"저장소에 없어 재추출 불가"*
>   로 종결했으나, DART 공시목록에 **`20240403002101 감사보고서 (2023.12)` 가 실재**한다(직접 조회).
>   저장소에 없는 것 ≠ 소스에 없는 것 → **downloader 발주**
>   `inbox/downloader/20260817T0100Z…aig_audit_report_fetch.md`. 받아오면 **RED=0** 이고 배포가 풀린다.
>   (함정: DART 등록명이 "AIG" 라 "AIG손해보험"으로는 이름검색이 안 걸린다 — `NAME_OVERRIDE` 와 같은 자리.)
> - **배포 상태**: `inbox/publishing/20260815T1400Z…` 갱신 — 차단 21 → 1, 9개사 값은 그대로 유효.
> - **잔여 위험(별건)**: `extract_tier2_abl` 노트선택 · `_oll_ytd` 누적판별은 **코드 수정 없이 override 로만**
>   맞춰진 상태다. 같은 경로를 타는 다른 회사가 재빌드에서 다시 틀어질 수 있고, 그때는 교차대조 RED 가 잡는다.

## Status (이전)

**(2026-08-15 p) owner 지시로 신설 룰 4종 **즉시 RED** 승격 — 관찰기 폐지. 게이트 RED=21, push 차단 중.**
> owner: *"신설 3종도 당연히 맞아야지. RED 로 올리고 파서한테 발주 때려."*
> **관찰기(YELLOW 1~2 릴리스) 관행을 이 건에는 적용하지 않는다** — 라이브 오표시를 놓친 직후에
> 새 탐지기를 또 관찰만 하는 건 같은 실수의 반복이다.
>
> | rule | 승격 | 현재 |
> |---|---|---|
> | `PL_CSM_AMORT_VS_WATERFALL` | YELLOW → **RED** | 14 |
> | `PL_CSM_AMORT_SCALE_GAP` | YELLOW → **RED** | 6 |
> | `CSM_AMORT_MISSING_VS_PL` | YELLOW → **RED** | 1 |
> | `PL_YTD_COLLAPSE_TO_ZERO` | YELLOW → **RED** | **0** (파서가 이미 소진 — 무료 승격, 회귀 잠금) |
>
> - 게이트 **RED=21 / YELLOW=223, exit 2** · `--selftest` **33/33**(L1·L2 기대치를 RED 로 갱신) ·
>   골든 3종 PASS.
> - **파서 발주 승격**: `inbox/parser/20260815T1400Z…pl_csm_amort_xcheck_gaps.md` → priority HIGH,
>   "참고"였던 C 섹션(배수 이탈 6건)도 **차단 사유**임을 명기. 못 채우는 자리는 **"raw 없음" 답신 →
>   0.0 아닌 null 로 명시** 후 내가 대조 대상에서 제외하는 경로로 정리한다.
> - **배포는 보류**: `inbox/publishing/20260815T1400Z…` 에 갱신 표기. 값이 검증된 2026.2Q 9개사
>   배포도 RED=0 전까지 나가지 않는다 — **라이브의 0 표시가 그동안 남는다는 대가는 owner 가 승인**했다.
> - 종결 조건: 21건 소진 → RED=0 → publishing 티켓 그대로 배포.

## Status (이전)

**(2026-08-15 o) owner 라이브 지적 — 2026.2Q PL 생명장기 분해 9개사 null. 내 검증이 두 군데서 뚫렸다. 룰 3개 신설·배선.**
> owner: *"라이브 26.2Q 삼성화재 PL breakdown 원수CSM상각·RA해제 전부 0. PL 의 CSM상각이랑
> CSM waterfall 의 상각액 규모 같은지 체크 안 했냐?"* — **맞다. 안 했다.**
>
> **구멍 1 — 게이트가 작업트리만 본다. 사용자가 보는 건 `main` 이다.**
> "게이트가 검사하는 파일 = 사용자가 보는 파일" 불변식을 **브랜치 축에서는 안 지키고 있었다.**
> 같은 룰을 `main` 에 돌리니 즉시 9건: 삼성화재 2026.2Q item2~14 전부 null(화면 0의 정체),
> DB손해·현대해상·한화생명·한화손보·흥국화재·미래에셋·롯데손보·코리안리 동일.
> **작업트리엔 이미 정상값이 있고 워터폴 상각과 소수점까지 일치** → 배포로 해소.
> → `inbox/publishing/20260815T1400Z…live_pl_csm_null_deploy_now.md`
>
> **구멍 2 — 두 마스터가 같은 사건을 각자 들고 있는데 서로를 한 번도 대조 안 했다.**
> 폐쇄식은 null/0 을 통과시킨다(다른 항이 흡수하면 그대로 닫힘) → **교차대조만이 탐지기**다.
> 신설 3종, 전부 `check_cross_source`, selftest L2 고정(33/33):
>
> | rule | 무엇을 잡나 | 현재 |
> |---|---|---|
> | `PL_CSM_AMORT_VS_WATERFALL` | PL 원수CSM상각 0/결측 + 워터폴 상각 유의미 | 14건 |
> | `PL_CSM_AMORT_SCALE_GAP` | 배수 0.4~2.5 이탈(단위·범위 불일치) | 6건(에이비엘 4건이 일관되게 0.1배 = 단위 의심) |
> | `CSM_AMORT_MISSING_VS_PL` (역방향) | 워터폴 상각 결측 + PL 엔 있음 | 1건 |
>
> **역방향 1건이 특히 나쁘다 — 미래에셋생명 2026.2Q**: 상각 1,128억이 통째로 빠졌는데
> `기초+신계약+이자+조정 = 기말` 이 **정확히 닫힌다**(조정이 plug). 기존 `IMPOSSIBLE_ZERO_AMORT` 는
> `상각 == 0` 만 봐서 **`None` 을 통과**시켰다. → `inbox/parser/20260815T1400Z…pl_csm_amort_xcheck_gaps.md`
>
> 게이트 현재 **RED=0 / YELLOW=244 (exit 0)** · selftest 33/33 · 골든 3종 PASS.
> 신설 3종은 관찰기라 YELLOW = push 안 막음. **잔여(14+6+1) 소진 후 RED 전환**이 종결 조건이다.
>
> **미배선 잔여(UH) 1건**: 배포 직전 **main 기준 게이트 재실행**. 이번엔 표로 대신했지만 절차화 필요 —
> 이게 없으면 "작업트리는 초록, 라이브는 빨강"이 또 난다.

## Status (이전)

**(2026-08-15 n) 파서 item16 수정 검증 — 현대해상 완결, 흥국화재·KB손해는 절반만 복원돼 새 음수 2건. 룰 스코프 해제로 드러남.**
> `_zero_other_expense` 를 `0.0` → `None` 으로 고친 조치는 **통과**. HEAD 값→null 7셀도 전부
> **HEAD 가 0.0 이던 자리**라 손실이 아니다(요청한 "0 대신 null" 그대로). 셀 유실 0(8,111→8,543행).
> - **현대해상 item16 완결**: 4셀 복원, 시계열 단조·당분기 전부 양수. 손댈 것 없음.
> - **흥국화재·KB손해는 1·2Q 만 채워져 3Q 가 0 으로 남았다 → 당분기 −11,246 / −192,135 신규 발생.**
>   복원 전(전 분기 0)보다 화면상 더 나쁘다. **원인은 내 iter 1 발주가 "HEAD 대비 변경 셀"만
>   나열한 것** — HEAD 도 0 이던 자리는 표에서 빠졌다. iter 2 에 좌표를 다시 줬다:
>   `inbox/parser/20260815T1230Z…pl_item16_partial_restore_gaps.md`
> - **`PL_YTD_COLLAPSE_TO_ZERO` 에서 `_DISPLAY_QUARTERS` 스코프 제거**(CSM 연속성 룰과 동일 판단).
>   붕괴는 중간분기(2024.3Q)에서 일어나는데 스코프를 걸면 원인 분기가 사각이 된다 —
>   실제로 위 2건이 그렇게 숨어 있었다(스코프 상태 적중 1 → 해제 후 **3**, 오탐 0).
> - 현재 **RED=0 / YELLOW=229 (exit 0)** · `--selftest` **32/32** · 골든 3종 PASS.
>   잔여 YTD 붕괴 3건 = 흥국화재 2024.3Q · KB손해 2024.3Q · 동양생명 2025.3Q(재보험 예실차, 미착수).

**(2026-08-15 m) 마스터 wipe 후 복구본 전수 재검증 — 골격은 무손실, 그러나 PL 19셀이 0 으로 회귀. 신규 룰 1개로 그 자리를 메움.**
> 작업 중 `CSM_waterfall`·`PL_breakdown` 이 HEAD 로 되감겨 오늘치가 통째로 날아갔다 파서가 복구.
> **복구본을 HEAD 와 2층(셀·필드)으로 전수 대조**했다.
>
> | 검사 | 결과 |
> |---|---|
> | `validate_data_contract.py` | **RED=0** / YELLOW=239 (exit 0) |
> | `validate_master_tables.py --no-build` | `0cont`, SUMMARY 골든 일치 |
> | HEAD 대비 셀 유실 | CSM 0 · PL 0 · IFRS17_BS 0 · dividend 0 |
> | 살아남은 셀 안 `값→null` | **전부 0** (2층 유실 없음) |
> | FY 경계 / 라이나 6항목 | BREAK 0 / 6-6 정확 일치 |
> | `--selftest` · 골든 3종 | **32/32** · 전부 PASS |
>
> **그런데 값 변경 19건이 나왔다 — 전량 `항목16 기타사업비용`이 HEAD 값 → `0.0`.**
> 현대해상 4셀 · KB손해 3셀 · 흥국화재 2셀(+ 파생 `값_당분기`). 내부모순으로 0 이 틀렸음이 확정된다:
> 현대해상 2023.3Q 누계 35,264.2 → **4Q 0.0**(당분기 **−35,264.2**), 2024 도 동형, 2025 는 1~2Q 가 비어
> 3Q 당분기가 73,119.5 로 몰린다. **FY 누계 비용은 4Q 에 0 으로 떨어질 수 없다.**
> `20260814T1637Z`(빌더가 61셀을 떨구는 원인) 와 같은 뿌리 — 그때 검증쪽이 HEAD 를 병합해 덮었고,
> 오늘 재빌드로 덮개가 벗겨진 것이다. → `inbox/parser/20260815T1120Z…pl_item16_zeroed_again_after_rebuild.md`
>
> **게이트 사각 → 룰 신설 `PL_YTD_COLLAPSE_TO_ZERO`** (`_pl_ytd_collapse`, check_census).
> 같은 FY 안에서 누계 non-zero → **정확히 0.0**. **0 은 등식을 깨지 않아 폐쇄식·PL 브리지가 조용히
> 통과시킨다**(실제로 RED=0 이었다). 8,543행 전수에 **적중 3 / 오탐 0**(현대해상 2 + 동양생명
> `재보험 예실차` 2025.3Q 7,026.0 → 0.0 신규 발견). 신설 관찰기라 **YELLOW**(선례 `CSM_WATERFALL_PLAUSIBILITY`),
> push 는 막지 않는다. 셀프테스트 **L1** 로 고정(31/31 → 32/32).
>
> **publishing 발주**: `inbox/publishing/20260815T1130Z…root_master_wipe_stop_running_builders.md`
> — 루트 마스터 빌더 직접 실행 금지, 게이트는 `validate_data_contract.py` 또는
> `validate_master_tables.py --no-build` 둘만. 이틀 연속 같은 함정(2026-08-14 PL 8,111→6,636)이라
> **기본값 반전**(기본 no-build)에 publishing 도 동의 표시하라고 요청했다.
>
> **배포 판단**: RED=0 이라 게이트상 push 가능. 단 19셀이 0/음수로 화면에 나가므로 **파서 수정 후 배포 권고**.
> 강행 여부는 owner.

**(2026-08-15 l) 라이나 재작성 반영 검증 통과 — push 게이트 RED=0, FY 경계 250/0. 남은 건 viz 골든 1건(fixture stale).**
> 파서가 iter 2 발주대로 전기 비교표시 기준으로 재작성 적용. **회신을 그대로 믿지 않고 전부 독립 재측정했다.**
>
> | 검사 | 결과 |
> |---|---|
> | `validate_data_contract.py` | **RED=0 / YELLOW=236 (exit 0)** — push 차단 해제 |
> | `validate_master_tables.py --no-build` | **`0cont`**(1→0), `qoq_warn` 206→205 |
> | 라이나 2023.4Q 6항목 | 발주값과 **6/6 정확 일치**, 폐쇄식 잔차 0.00 |
> | FY 경계 전수 | **OK 250 / BREAK 0** |
> | HEAD 대비 행 유실 | **0** (1,962 → 2,136) |
> | `csm_manual_overrides.json` | KR0074 **6건** — 원공시/재작성본 rcept 양쪽 + 계약경계 근거 + "파싱오류 아님" 명기 |
> | `--selftest` · `test_master_tables_golden` · `test_deploy_assets` | 31/31 · PASS · PASS |
> | 메트라이프(KR0095) | 재작성 이슈 없음 확인(2023.4Q 기말 21,521.1 == 2024.4Q 기초) |
>
> **`tests/test_viz_csm_waterfall_golden.py` 만 FAIL** — 파서 회신의 "113개 테스트 전부 통과"와 어긋난다.
> **산출물이 아니라 fixture 가 stale**: 디스크 `csm_waterfall.json` 은 이미 새 빌드(`1b26bc91…`)인데
> 골든이 `47e6e80f…` 에 멈춰 있다. drift 는 **개선**(`partial 3 → 0`, `ok 36 → 39`, 합계 47 동일) →
> `--update` 재생성 + 커밋에 사유 기록이면 끝. → `inbox/parser/20260815T1030Z…viz_csm_golden_stale_after_lina_fix.md`
> (같은 도구를 **위반 흡수**에 쓴 게 `20260815T0042Z` 반려 건이었다 — 이번은 반대 방향이라 정당한 사용.)
>
> **정정 기록**: 이 라운드에서 내 진단 2개(“스케줄 표에서 뽑았다” / “항목4 는 plug”)가 raw 재계산으로
> 뒤집혔다. `(k)` 참조. 숫자 일치를 곧바로 "베낀 것"으로 읽지 말 것 — 두 공시표가 같은 잔액을 다른
> 절단면으로 보여주면 일치가 정상이다.

**(2026-08-15 k) 라이나 RED 원인 확정 — 파싱 오류 아님, 회사의 소급재작성이다. 내 iter 1 진단도 함께 정정.**
> 파서가 "원천 데이터부터 틀렸다"고 회신 → raw 두 필링을 직접 열어 전 열 재계산했다. **양쪽 다 틀렸다.**
> - **파서 근거 기각**: *"기초 자산+부채 ≠ 기초 잔액"* → 그 표는 `잔액 = 부채 − 자산`(자산은 음의 부채)이고
>   그렇게 계산하면 **기초·기말 7개 열 전부 정확히 일치**한다(PV −1,977,369,986 등 전수 확인). 표는 흠이 없다.
> - **내 iter 1 진단 취소**: 값은 상각스케줄 표가 아니라 **진짜 측정요소별 변동표**에서 나왔다.
>   스케줄 합계가 CSM 잔액과 같은 건 정상 — 그 표가 *"기말 CSM 을 기대상각기간별로 배분"* 한 것이라
>   합계 = 잔액이다. 두 표 일치는 오류가 아니라 **교차확인**. **"항목4 = plug" 도 취소**:
>   30,211.1억 = 추정치변동분(−4,182.9) + **계약의 경계 변경 효과(+34,394.0)**, raw 행 그대로다.
> - **진짜 원인 = 소급재작성.** 같은 FY2023 을 두 필링이 다르게 말한다(양쪽 다 자체 폐쇄식은 정확히 닫힘):
>
>   | FY2023 CSM | 원공시 `20240409003674` | 재작성 = FY2024 필링 `20250409002702` 전기 비교표시 |
>   |---|---|---|
>   | 기초 | 22,082.5억 | 35,264.0억 |
>   | 기말 | **55,155.5억** | **32,301.6억** |
>
>   차이의 정체는 한 줄 — 원공시에만 있는 `기타 → 계약의 경계 변경 효과 +34,394억`(순부채 영향 0,
>   측정요소 간 재배분)이 재작성본에선 **사라졌다.** 정정공시는 없다(비상장 → 감사보고서만, DART 4건 전수 확인).
>   마스터가 2023.4Q=원공시 / 2024.4Q=재작성본 기준을 나란히 든 상태라 경계가 깨진 것이고, **어느 쪽도 파싱 오류가 아니다.**
> - **처분**: 2023.4Q 를 전기 비교표시 기준으로 재작성(기초 35,264.0 → 기말 32,301.6) → 2024.4Q 기초와
>   정확히 연결돼 RED 소멸. 추출 좌표(L9016 이후 두 번째 TABLE)와 6항목 값·검산까지 실어 발주:
>   `inbox/parser/20260815T0940Z…lina_restatement_pull_from_comparative.md`(iter 2).
>   **선례 있음** — `20260620T0600Z` 교보 CSM 전기값을 비교표시에서 끌어온 건. 새 방식이 아니다.
> - **교훈(룰 아님, 기록)**: `feedback_continuity_break_is_red` 는 유효하다 — 다만 "소급재작성이면 면제"가
>   아니라 **raw 로 재작성을 확정한 뒤 재작성 기준으로 값을 맞춘다**가 이 케이스의 올바른 종결이다.
>   면제도, 값 보정도 아니다. iter 1 은 종결(`inbox/_resolved/`).

**(2026-08-15 j) 파서 재조치 검증 완료 — RED 11 → 1. 남은 1건은 원인 특정 후 발주. 라이나 2023.4Q 가 CSM 변동표가 아니라 상각스케줄 표에서 만들어졌다.**
> 파서가 "급한 건 다 처리"라고 해서 전량 재검증. 오늘 바뀐 마스터: `PL_breakdown`(8,543행) ·
> `IFRS17_BS`(1,637→**5,008행**) · `CSM_waterfall`(1,962→2,136행) · `dividend`.
>
> **① 5사 앵커 조치 = 진짜 철회 확인(반려 iter 2 종결).** 교보·신한라이프·메리츠·에이비엘·푸본현대
> **2026.1Q 6항목이 HEAD 와 완전 동일**(override 흔적 0) + 25.4Q 기말 == 26.1Q 기초 == 26.2Q 기초
> (Δ 전부 0.0). 골든도 `6cont` → **`1cont`** 로 정직하게 되돌아왔고 live SUMMARY 와 **완전 일치**.
> **복사 의심을 raw 로 배제**: 메리츠 2026.2Q 기초 111,037.0억을 반기보고서 원문에서 직접 확인
> (`FY2026_Q2/raw/KR0001_.../20260814002253.xml` 합계행 `11,103,697` 백만원). 앵커를 베낀 게 아니다.
>
> **② 남은 RED 1건 = 라이나생명 2024.4Q 기초 32,302 ≠ 2023.4Q 기말 55,156 (Δ−22,854).**
> 2023.4Q 쪽이 틀렸다 — 숫자 정확 일치 2건으로 특정:
> 기말 55,155.5억 = 필링 `20240409003674` "기대상각기간별 보험계약마진" 표 합계 5,515,548,316천원,
> 기초 22,082.5억 = 같은 caption 두 번째 표 2,208,247,317천원. **그 필링 추출 CSM 표 4장이 전부
> 상각스케줄이고 변동표는 0장.** 스케줄 합계 = 미래 상각액 단순합(할인 전) → 잔액보다 구조적으로 큼(1.71배).
> - **폐쇄식은 이 건을 못 잡는다**: 조정(항목4) 30,211.1 = 나머지를 맞추는 **역산 plug**
>   (55,155.5−22,082.5−7,221.6−816.6+5,176.2 = 30,211.0). 356블록 중 352가 닫힌다 → **FY 경계 룰이
>   유일한 탐지기**였다((i) 에서 이 룰을 push 게이트로 올린 판단이 하루 만에 값을 했다).
> - 반대편(2024·2025)은 HEAD 와 값 동일 + 정상 연결. 전수 FY 경계 **OK 249 / BREAK 1**.
> - → `inbox/parser/20260815T0700Z__validation__KR0074_2023.4Q__lina_csm_from_amort_schedule.md`
>   (raw 있음 → parser. "변동표 없으면 블록을 빼라, plug 금지" 명시)
> - **동봉(조용한 자리)**: 신규 2023.4Q 3건이 앵커 없어 경계 검사 불가 — AIA 는 24·25 동시 유입으로
>   체인 OK 확인, **메트라이프는 라이나와 같은 지문**(추출 표가 스케줄뿐)이라 값 출처 확인 요청.
>
> **③ 17BS 확장 통과.** items 1-31(자산·부채·자본 세부 + 섹션/레벨 키)로 커졌는데
> `BS_IDENTITY` 위반 0 · 코어(1·2·3·4) 결측 0. owner 지침대로 세부행은 코어에 안 넣고 **새 룰도 안 만들었다**
> (`20260814T0149Z` "검증할 건덕지 없다 / 부모-자식 룰 신설 금지").
>
> **④ 회귀 없음**: CSM 행 유실 0(HEAD 1,962 → 2,136, 신규 29블록) · `--selftest` **31/31** ·
> `pytest tests/test_master_tables_golden.py tests/test_deploy_assets.py` **11 passed** ·
> `validate_master_tables.py --no-build` SUMMARY 골든 일치.
> **push 게이트 RED=1 / YELLOW=236 (exit 2) — 차단 중, 해제 조건은 위 라이나 1건.**

## Status (이전)

**(2026-08-15 i) CSM 연속성 룰 push 차단 게이트로 승격 (owner 지시) — 라이브 RED=11, push 차단 중.**
> - **왜**: `CONT` 가 `validate_master_tables.py` 에만 있고 `prepush_check.py` 는 `validate_data_contract.py` 하나만 부른다 → 파서가 5사 기초를 override 해 FY 경계를 새로 깼는데도 **push 경로는 초록**이었다. 게다가 그 게이트의 골든이 `1cont → 6cont` 로 재생성되며 위반을 흡수해 **테스트까지 통과**했다(골든 `--update` 오용).
> - **무엇**: `check_csm_continuity()` + 룰 `CSM_CONTINUITY_FY_BOUNDARY`(RED, **면제 없음**). 판정식·허용오차는 기존 CONT 와 동일하게 맞춰 두 게이트가 다른 답을 내지 않게 함. **차이 1개 — FY→분기 하드코딩 제거**: 기존 `FY_Q` 가 2026.1Q 까지라 **2026.2Q 가 검사 밖**이었고, 도출식으로 바꾸니 안 보이던 위반 5건이 추가로 드러났다(6 → 11).
> - **스코프**: `_DISPLAY_QUARTERS` 미적용. 그 집합에 2026.2Q 가 없는데 사이트는 그 분기를 그린다 → 스코프를 걸면 최신 분기가 사각이 된다.
> - **현재 RED 11** = 교보·메리츠·신한라이프·에이비엘·푸본현대 각 2건(2026.1Q+2Q) + 라이나생명 2024.4Q 1건. 해제 조건은 `inbox/parser/20260815T0042Z`(iter 2 반려). 통지: `inbox/publishing/20260815T0055Z`.
> - 셀프테스트 30/30 → **31/31**(K1 추가). `docs/postmortems/README.md` 게이트표에 마스터테이블 게이트 행 + 이번 실제 발화 사례 추가.

**(2026-08-15 h) 2026.2Q 파서 산출물 전수 검토 — 항등식 5축 전부 통과, 실이슈 2건 발주.**
> 발주: `inbox/parser/20260815T0018Z__validation__MULTI_2026.2Q__q2_review_anchor5_and_hanwha_bs.md`
> - **통과**: CSM 마감항등식 23/23 · CSM 연속성 23/23 · 반기누계(`값_당분기`==2Q누계−1Q누계) 159/159 · PL 브리지 46/46 · 17BS 항등식 12/12.
> - **검증쪽 자기정정 (기록용)**: 연속성을 `값`(누계) 컬럼으로 재면 **23사 전건 RED로 오탐**한다. 반기 기초는 **FY 시작(2025-12-31) 앵커**이고, 분기 기준 기초는 파서가 `값_당분기`에 따로 담는다. **저량항목의 `값_당분기` = 그 분기 자체의 기초/기말** — 다음 세션도 이 컬럼으로 연속성을 재라.
> - **Q-1 (reparse)**: FY 시작 앵커가 1Q 보고서와 어긋나는 **5사** — 교보생명 +5,659(+8.7%) · 신한라이프 −1,114 · 메리츠화재 +857 · 에이비엘 −472 · 푸본현대 −237. 마감항등식은 자기완결이라 기초 오선택을 못 잡는다(2026.1Q 5사 misparse와 같은 자리). raw 대조 전 면제 금지.
> - **Q-2 (owner 판정 필요)**: 17BS 2026.2Q 12사 중 **한화손보만 소스가 있는데 결측** — OFS `status=000`인데 BS 4행이 전부 값 공란(빈 껍데기), CFS는 45행 완전(자산 19.8조). owner P-1 "BS=OFS 고정"은 *틀린 값* 방지용이지 *항목 부재*를 상정하지 않았다 → "OFS에 항목1/2/3이 전무할 때만 CFS 폴백" 조건부 규칙 제안. 나머지 11사는 OFS·CFS 둘 다 013 = **정상 부재**.

**(2026-08-14 g) 배당 마스터(`dividend.json`) 게이트 배선 — 배당 도메인 RED 0. 단 게이트 전체는 RED=13(PL_breakdown, 별건).**
> 발주 `inbox/validation/20260814T1625Z`(owner) 드레인 완료. 신규 루트 마스터가 게이트 밖에 방치돼 있던 상태를 닫았다.
> - **배선**: `MASTER_FILES["dividend"]` 등록(mtime·동시백필·ARTIFACT_UNREADABLE 커버) + `_ifrs17_bs_is_published()` → **`_html_fetches(master_file)` 로 일반화**(17BS·배당 공용). `공시보고서.html` 이 fetch 를 켜면 **코드 수정 없이 YELLOW→RED 승격**.
> - **룰 3개**(`check_dividend`): `DIV_PAYOUT_IDENTITY`(46셀 위반0) · `DIV_CENSUS_MISSING`(310/310 결측0) · `DIV_ZERO_CONTRADICTION`(0) + `DIV_CENSUS_SOURCE_MISSING`(검사축 소실 감지) + `DIV_NO_FILING_COMPANY`(집계 YELLOW, 비상장 15사).
> - **설계 핵심 2개**: ① 기대 그리드를 회사목록이 아니라 **수집 census 의 status=000** 에서 도출(회사목록 기준이면 비상장 15사의 정상 부재가 전부 RED). ② `_DISPLAY_QUARTERS` 스코프 **미적용** — 배당 화면은 2023.1Q~2026.2Q 전 계열을 그린다.
> - **발주문의 "26셀 결측" 은 오케스트레이터 오기대**: 24사×14분기(336)는 산술격자일 뿐, 실제 기대는 필링 존재 310셀. 그 26칸은 전부 `status=013`(보고서 자체 없음) = 정상 부재.
> - **1회성 전수감사**: 항목6 전행 0 · 항목5 264/310행 0 → raw 310파일에서 해당 `se` 행 전수 확인, **thstrm 이 `-`/공란/0 아닌 케이스 0건**(진짜 무배당, 파싱손실 아님). 상시 룰로 승격하지 않음(매 실행 raw I/O 불필요, 같은 사고는 ZERO_CONTRADICTION 이 더 싸게 잡음).
> - **교차검증**: 독립 산출물 `배당현황_OpenDART_2023Q4-2026Q2.xlsx` 와 셀 단위 대사 **308/308 일치, mismatch 0**.
> - **셀프테스트 25/25 → 30/30**(J1~J5 신설).
> - **PL_breakdown 61셀/1,475행 유실 → owner 지시로 검증쪽이 합집합 병합 직접 실행. 게이트 RED 13 → 0.** 작업트리 PL = **8,111행/332셀**. 병합 = HEAD(=main, 동일) ∪ 작업트리, 키 `(코드,분기,항목번호)`. 내역: 작업트리 유지 6,636 · HEAD 복원 1,475 · **겹치는 키인데 작업트리가 `null` 이라 HEAD 로 채움 1,008**(셀 단위 combo-diff 가 못 잡는 층) · 값충돌 19(작업트리 15 / HEAD 4). `--no-build` SUMMARY 골든 일치 → 골든 재생성 불필요.
> - **⚠ 원인 규명(재현됨)**: `validate_master_tables.py` 는 `--no-build` 없이 돌리면 `build_root_masters.py` 를 먼저 실행하고, 그 재빌드 산출이 정확히 6,636행이다. 병합 직후 검증쪽이 플래그 없이 한 번 돌려 **병합이 그 자리에서 되돌아갔다**(되돌아간 파일 = 병합 전 백업과 MD5 동일). 우발 사고가 아니라 **그 경로마다 재현되는 결정론적 손실** = `project_git_purge` 함정의 실물. **검증 세션은 앞으로 이 스크립트를 반드시 `--no-build` 로 호출할 것.**
> - 파서 몫으로 남은 것(값 복구 아님): 빌더가 그 61셀을 떨구는 이유 규명 + 순가산화 또는 rebuild 기본값 반전. `inbox/parser/20260814T1637Z` 에 정책·충돌 19건·백업 경로까지 기록. 한화손보/한화생명 2023.1Q 항목20(영업이익) 2셀은 **HEAD 채택 + 파서 판정 대기**.

## Status (이전)

**(2026-08-14 f) owner 종결 지시 — 비상장 6개사 접음. 게이트 RED 42 → 0 (exit 0). 17BS 라운드 종료, 열린 티켓 0건.**
> owner: *"그 귀찮은 짓을 하지 말라니까? 걔네는 걍 접고 마무리해."* → Tier-2 본표 추출 추적 중단.
> - `validate_data_contract.py` 에 **`IFRS17_BS_NO_SOURCE`(6개사)** 추가 → 코어 census 면제.
>   AIG · 하나손해 · 신한이지 · 비엔피파리바카디프 · 메트라이프 · IBK연금 (전부 비상장).
>   면제 근거를 **코드 주석에 박았다**: OpenDART `013`/`014` 실측 + **상장 대조군 정상**(= 호출 문제 아님)
>   + owner 지시. 파일 레지스트리를 되살리지 않았다(방금 아카이브한 기구를 다시 만들지 않으려고).
> - **면제는 census 한정.** `BS_IDENTITY`(1==2+3)는 이 6개사에도 계속 돈다 — 값이 들어오면 구조검사는 받는다.
> - 조용히 사라지지 않게 **집계 YELLOW 1건**(`BS_CENSUS_NO_SOURCE_COMPANY`, 11블록 명시).
> - **최종: RED=0 / YELLOW=220 (exit 0) · `--selftest` 25/25 · `pytest tests/test_deploy_assets.py` 10/10.**
>   **push 차단 해제** — 배포 판단은 publishing 소관(owner 승인 필요).
> - 발주 티켓 2건 종결: `20260814T0500Z`(재확인 후 resolved) · `20260814T0620Z`(owner 취소로 resolved).
>   → 둘 다 `inbox/_resolved/`. **validation inbox 비어 있음.**
> - 남은 인지 항목(작업 아님): ① census 회사축 미검사(행 0건인 KR1098 카카오페이손해 무신호)
>   ② 비상장 6개사는 화면에 자산/부채/자본/AOCI 가 빈다 — designer 가 빈칸을 0 으로 렌더하지 않는지만 확인.

## Status (이전)

**(2026-08-14 e) owner 지시 API 조사 = 막다른 길(발주 없음). `test_deploy_assets` 10/10 통과 — 이제 배포 blocker 는 RED=42 하나뿐.**
> - **OpenDART 2종 실측 — 비상장사는 두 API 다 안 나온다.** owner 지목(`apiId=2019019` · `2019020`).
>   비상장 3사(IBK연금·메트라이프·AIG) × 필링 6건 전수 vs **상장 대조군 한화생명**:
>
>   | API | 비상장 3사 | 대조군(한화생명) |
>   |---|---|---|
>   | `fnlttSinglAcntAll`(2019020, 현행) | `013 조회된 데이타가 없습니다` (OFS·CFS) | `000` OFS 245행 / CFS 346행 |
>   | `fnlttXbrl`(2019019, 미사용) | `014 파일이 존재하지 않습니다` 6/6 | **ZIP OK** 1.4-1.7MB·7파일 3/3 |
>
>   구조적 이유 = `fnlttXbrl` 은 **정기공시 첨부 XBRL** 서비스인데 비상장 보험사는 **감사보고서(F)만**
>   내고 XBRL 첨부가 없다. **대조군이 3/3 성공했으므로 호출 오류가 아니라 파일 부재.**
>   → owner 지시("없으면 걍 패스")대로 **downloader 발주 없음.** 재조사 방지 근거는
>   `inbox/parser/20260814T0620Z…`(iter 2) 에 표로 붙여 뒀다. **RED 42 는 우회 소스가 없다 =
>   감사보고서 본문 XML 파싱 수정이 유일 경로**임이 확정됐다.
> - **`pytest tests/test_deploy_assets.py` 10 passed** — publishing 이 keep-list swap 을 착지시켰다
>   (`claude-agent-publishing.md` 5회 · `claude-agent-designer.md` 1회 `IFRS17_BS.json` 언급).
>   (d) 에 적힌 "publishing 으로 이동한 FAIL" 은 **해소됨.**
> - 게이트 재실행 **RED=42 / YELLOW=219 (exit 2)**, `--selftest` **25/25**. 수치 변화 없음 —
>   남은 42셀은 전부 위 Tier-2 본표 미추출이고 parser iter 2 답신 대기.

## Status (이전)

**(2026-08-14 d) 배포 승격 발생 — `IFRS17.html` 이 `IFRS17_BS.json` fetch 시작(16:39) → 심각도 자동 RED. push 게이트 RED=42 = 실차단 중.**
> **코드 수정 0줄.** 배포 HTML 이 그 JSON 을 읽으면 RED, 아니면 YELLOW라는 기존 판정식이 설계대로 동작한 것.
> - **RED 42 = 원인 한 가지뿐** — Tier-2 6개사 11블록에서 **재무상태표 본표(코어 1·2·3·4)가 통째 미추출**.
>   행은 있고 준비금 계열(5·7)만 들어와 있다. IBK연금 3분기 · 메트라이프 3분기 · AIG 1 · 하나손 1 ·
>   신한이지 1 (+ KR0075 2분기 = **owner 지시로 이번 턴 보류**).
>   → `inbox/parser/20260814T0620Z…ifrs17_bs_delta_after_ofs_rebuild.md`(iter 2, 실측대로 전면 갱신).
> - **owner 정정 반영**: IBK 2023.4Q 는 해약환급금준비금 기적립액 **0 + 전입액 185,680백만원**이 정상이고
>   (→ 2024.4Q 기적립액 185,680), 항목 5 는 optional 이라 **게이트가 애초에 안 본다.** 그 회사에서
>   문제인 건 자산/부채/자본/AOCI 가 전 분기 없다는 것. 티켓에 오독 방지 문구로 못박음.
> - **소스 수정으로 소멸 누계 14건, 예외 등재 0건**: 삼성생명 항등식 2 · 한화생명 3 · 흥국생명 5 ·
>   **AIA 3 + 아이엠라이프 1(추가 소멸)**. owner V-3("예외로 덮지 말고 소스를 고쳐라")이 전 구간 성립.
> - **남은 배포 blocker 1건(내 소관 밖)**: `pytest tests/test_deploy_assets.py` FAIL 이 designer →
>   **publishing 으로 이동**했다. designer repoint 는 끝났고(문서·HTML 정합), 이제
>   `claude-agent-publishing.md` 가 `IFRS17_BS.json` 을 언급하지 않는다 = keep-list 누락 → **라이브 404 위험.**
>   기존 owner 발주 `inbox/publishing/20260814T0232Z…keeplist_swap_equity_to_ifrs17_bs.md`(open)가 그 자리다 —
>   validation 신규 발주 없음.

## Status (이전)

**(2026-08-14 c) inbox 전량 드레인 + 재검증 종결 — 17BS 정본 전환 확정. push 게이트 RED=0 / YELLOW=261, `--selftest` 25/25.**
> 8/13~8/14 owner 발주 4건(`20260813T0422Z` · `20260814T0035Z` · `0216Z` · `0232Z`)을 전부
> `status: resolved`(0216Z 는 `superseded`) + `inbox/_resolved/` 이동. **validation inbox 는 현재 비어 있다.**
> - **도메인 전환 완료**: `equity_composition`(항목 1-49) 게이트 철거 → `IFRS17_BS.json`(항목 1-5) 등록.
>   룰은 **둘뿐** — `BS_IDENTITY`(1 == 2+3) · `BS_CENSUS_MISSING_ITEM`(코어 1·2·3·4). 5·6·7 optional=무검사.
>   룰 파일은 지우지 않고 `archive/2026-08_equity_composition/` 로 이동(되살리면 룰 4개가 통째로 붙어 온다).
> - **독립 재검증(파서 재빌드 `IFRS17_BS.json` 14:42 이후)**: 게이트 재실행 **RED=0 / YELLOW=261**(exit 0),
>   `--selftest` **25/25**, `pytest tests/test_deploy_assets.py` **1 FAIL**(아래, validation 소관 아님).
>   17BS findings **40 → 42**(전부 YELLOW — 아직 어떤 배포 HTML 도 `IFRS17_BS.json` 을 fetch 하지 않음.
>   designer repoint 시 **코드 수정 없이 RED 승격**).
> - **소스 수정으로 소멸 확인 10건 — 예외 등재 0건**: 삼성생명 `BS_IDENTITY` 2건(파서 P-1 OFS 고정) ·
>   한화생명 3 + 흥국생명 5 = AOCI 8건(파서 P-2 태그 조건부 채택). owner V-3 이 요구한
>   "예외로 덮지 말고 소스를 고쳐 소멸시킨다"가 그대로 성립했다.
> - **잔여 42셀 → `inbox/parser/20260814T0620Z…ifrs17_bs_delta_after_ofs_rebuild.md`(iter 2)**:
>   Tier-2 본표 부분산출 38(AIG·메트라이프·IBK·**KR0075 신규**·하나손·신한이지 — 준비금 주석만 잡고
>   재무상태표 본표를 못 잡는 지문) + AOCI 태그변형 잔여 4(AIA 3·아이엠라이프 1). **값 보정 요청 0건.**
> - **남은 FAIL 1건**(내 소관 밖, push 전 해소 필요): `IFRS17.html` 이 아직 `equity_composition.json` 을
>   fetch → `test_docs_agree_with_what_pages_fetch` FAIL. designer `20260814T0232Z`(Panel 7 repoint) +
>   publishing `20260814T0232Z`(keep-list swap) 완료 시 자동 해소.
> - **owner 판단 대기 1건**: census 회사축. 현 census 는 "마스터에 행이 있는 (회사,분기)" 안에서만 돌아
>   **행이 0건인 회사를 못 본다**(현재 KR1098 카카오페이손해 1사). 기대그리드(39사×7분기)로 올리면
>   366셀이 뜨고 방금 아카이브한 예외 레지스트리가 다시 필요해져 이번 라운드엔 붙이지 않았다.

## Status (이전)

**(2026-08-14) owner 범위 정정 반영 — equity census 코어 축소. 룰 RED 182 → 21. 게이트는 이제 실차단(RED=21).**
> 발주 `inbox/validation/20260814T0035Z…equity_scope_rollback_core_shrink.md` (지시 5개 전부 반영, **신규 룰 0개** — 줄이는 작업).
> - `CORE_ITEMS = (1, 6, 40, 41)`(자산/부채/자본/AOCI = owner 원 요구 high-level 17BS).
>   10/11(해약환급금준비금, "안되면 pass"였음)·5/20/29/30(요구된 적 없는 AOCI 흐름 분해) → **optional**,
>   결측은 셀별 RED 대신 집계 **YELLOW 1건**(`EQ_OPTIONAL_ITEM_ABSENT`).
> - `EQ_PARENT_CHILD_INCOMPLETE` RED→YELLOW. `EQ_TIER2_SCOPE_GAP`·`TIER2_CORE_ITEMS`·`load_tiers()` 삭제(Tier-2 중단).
> - **Tier-2 15개사 census 예외 등재** — 근거 `inbox/parser/20260814T0035Z…equity_tier2_stop.md`
>   "XBRL FS 없는 15개사 = 영구 결측 확정". 회사목록은 사이드카 `universe.tier2_companies`(14)+`tier2_still_missing`(KR1098).
>   `_excepted()`가 `companies` 배열도 받도록 3줄 확장.
> - 유지: `EQ_BS_IDENTITY`·`EQ_AOCI_ROLLFORWARD`·`EQ_AOCI_STOCK_FLOW_TIE`·`EQ_UNIT_SCALE_JUMP`·provenance RED·owner_confirmed 억제.
>
> **IFRS17.html 이 `equity_composition.json` 을 fetch 하기 시작 → 배포 판정 자동 전환**(스테이징 YELLOW 강등 종료).
> `validate_data_contract.py` **RED=21 = push 차단 중.** 내역: AOCI(6) 결측 13(한화생명 7·흥국생명 6) ·
> 롤포워드 6(KB라이프 328,699 / 한화손보 3,198 / DB생명·DB손보 각 2건 FY상수) ·
> 삼성생명 BS 항등식 2(2025.2Q/3Q, 자산총계 동일값 반복 = DART 원본 품질 이슈로 파서 종결).
> 앞 19건 → `inbox/parser/20260814T0130Z…equity_core4_gaps_after_scope_shrink.md`.
> 뒤 2건 = **owner 결정 대기**(예외 등재 / 화면 제외 / RED 유지).
>
> **버그 1건 수정**: 심각도 승격 직후 `--selftest` 가 0/22 로 무너졌다 — `Env` 가 inject(합성) 모드에서도
> `equity_findings` 를 디스크에서 읽어 실제 RED 21건이 22개 케이스 전부를 오염시켰다. `wf_by_code` 와 같은
> 격리 규칙 적용(inject 면 `equity_findings=[]`·`equity_published=False`) → **22/22 복구**. YELLOW 였을 땐 조용히 통과 중이었음.
>
> **부수 발견(배포 위험)**: `pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` **FAIL** —
> keep-list 를 유도하는 문서 2곳(publishing·designer §1 표)에 `equity_composition.json` 이 없다.
> 그대로 배포하면 라이브 404 → 두 스테이지에 각각 발주(`20260814T0135Z…equity_keeplist_doc_gap.md`).
> **RED 0 + 이 테스트 통과 전에는 push 금지.**

**(2026-08-13 b) 파서 답변 재검증(iter 2) — raw 대조로 P-1~P-7 확인, 신규 룰 4개 배선. 룰 RED=231, push 게이트 RED=0 유지.**
> 파서 답변 `inbox/_resolved/20260813T0600Z…equity_composition_red_findings.md` → 재검증 후 resolved,
> 잔여·신규는 `inbox/parser/20260813T1330Z…equity_composition_red_round2.md` (iter 2).
>
> **마스터가 아니라 raw 를 봤다.** 사이드카가 인용한 캐시 파일을 직접 열어 Tier-1 243 (회사,분기) 전수 재추출:
> - **P-1 항목8(비지배지분) = 진짜 raw 값**(22셀 일치 + 폐쇄식 잔차 − item8 = 0). plug 아님 **확정**.
> - **P-6 메리츠 = 파서 무결, 내 룰이 틀렸다**(원문 478,384,895,270원/-432,734,801원 둘 다 raw).
>   0 을 통과하는 실제 스윙을 비율만 보고 단위오류로 오탐 → **부호 반전 쌍 skip** 으로 수정.
>   owner_confirmed 등재 요청은 **거절**: 데이터가 아니라 탐지기가 틀린 것을 owner 승인으로 덮으면
>   그 다음부터 진짜 단위오류를 못 잡는다.
> - **P-4 = 값 판정은 맞으나 방식이 발주문 §3 위반** → 아래 신규 룰이 상시 탐지로 전환.
>
> **신규 룰 4개 (전부 `scripts/validate_equity_composition.py`, 게이트는 러너 결과를 흡수하므로 추가 배선 불요):**
>
> | rule id | 함수 | 무엇을 막나 | 현재 |
> |---|---|---|---|
> | `EQ_MASTER_VS_RAW_DRIFT` (RED) | `check_raw_fidelity` | **빌더의 무신고 값 정정.** 마스터 item 6/29/30 을 인용 캐시 raw 와 대조 | 1건 (KR0032 2024.4Q item30 부호 치환) |
> | `EQ_OPENING_VS_BS_COMPARATIVE` (RED) | `check_raw_fidelity` | 기초(20) 행 오선택. item20 = 그 필링 자신의 BS 전기 | 0건 (FY2024+ 201/201 일치, FY2023 은 전환연도라 제외) |
> | `EQ_BS_IDENTITY` (RED) | `check_identities` | 자산 = 부채 + 자본. **Tier-2 행에 걸 수 있는 유일한 구조검사**(단위오류 탐지) | 2건 (삼성생명 2025.2Q/3Q) |
> | `EQ_DERIVED_UNDECLARED` (YELLOW) | `check_raw_fidelity` | 역산값이 공시값으로 위장 — 항등식이 파생값으로 닫히면 검증력 0 | 64셀(item29) |
>
> **룰 정정 3건:** ① census 회사 축을 `kics_disclosure`(39사)로 이동, 분기 축만 `PL_breakdown` —
> PL 축이 6사를 통째로 못 보고 있었다(**카카오페이손보는 equity 행 0건인데 RED 0건**이었음).
> PL 부재사는 연 1회 4Q 기대. ② `TIER2_CORE_ITEMS=(1,6,10)` + 스코프 밖 결측은
> `EQ_TIER2_SCOPE_GAP` YELLOW 104건으로 상시 카운트(조용히 사라지지 않게). `EQ_PARENT_CHILD_INCOMPLETE`
> 도 Tier-2 제외(같은 갭 이중계상 21→2). ③ continuity 에 **raw 기반 자동 판정** — 기초가 그 필링의
> BS 전기와 일치하면 발행사 소급정정이 raw 2곳에서 확인된 것이므로 `EQ_AOCI_CONTINUITY_RESTATED`
> YELLOW(푸본현대 2025.1Q). 사람이 "재작성이라 넘어가자"고 선언하는 면제 경로를 만들지 않는다.
>
> **RED 231 분해**: census 결측 항목 211(**item10 단독 181 = Tier-1 회사 주석 미착수**, item29 70, item6 25,
> item20/30 각 15, item1 10) · census 셀 12 · 부모-자식 2 · 롤포워드 3 · BS 항등식 2 · raw drift 1.
> **회귀**: `--selftest 22/22` · `pytest tests/test_deploy_assets.py 10 passed` · 라이브 게이트 **RED=0 / YELLOW=605**.
>
> **파서 질문 5건 전부 종결(owner 대기 없음)** — Tier-2 코어/universe/KB라이프 항목31/메리츠/DRIFT 정책.
> DRIFT 는 owner 판단 요청이 왔으나 **데이터가 답했다**: item20 이 FY2024+ 201/201 에서 자기 필링의
> BS 전기와 일치 → 분기값 유지가 맞다(FY 통일은 롤포워드를 22→30 으로 악화시킨다는 파서 실측과 일치).
>
> **잔여(UH-9 갱신)**: ① 사이드카 `derived_items` item 단위 신고(파서) ② KR0069 2025.2Q/3Q BS stale
> 재페치 판정(`inbox/downloader/20260813T1330Z…fs_api_bs_stale_repeat.md`) — 판정 오면 캐시교체 또는
> documented exception ③ 항목 31(소유주거래) 신설 후 롤포워드 룰을 `20+29+31==30` 으로 확장.

**(2026-08-13 a) inbox 1건 드레인 — `equity_composition` (AOCI + 해약환급금준비금) 룰 신설 + 게이트 배선. 룰 RED=341, push 게이트는 RED=0 유지(미배포 스테이징).**
> 발주 `inbox/validation/20260813T0422Z…equity_composition_rules_and_gate.md` (V-1~V-6).
> 마스터가 같은 날 14:33에 1차 산출돼 룰 설계 + **실행 검증**까지 함께 수행.
>
> **배선 위치(V-6 요구대로 경로+함수명):**
> - 룰 본체 = `scripts/validate_equity_composition.py` (`run()` / `check_census` / `check_identities` /
>   `check_continuity` / `check_plausibility` / `check_provenance` / `check_cross_master`). 단독 실행 시 RED면 exit 2.
> - push 게이트 = `scripts/validate_data_contract.py::check_equity_composition` (run_gate 2번째 호출),
>   `Env._load_equity_findings` / `Env._equity_is_published`, `Env.MASTER_FILES["equity_composition"]`(mtime 감시).
>   룰을 두 벌로 구현하지 않고 러너 결과를 흡수한다.
> - **심각도는 배포 여부로 자동 결정**: 루트 배포 HTML 중 `equity_composition.json`을 fetch 하는 페이지가
>   생기는 순간(디자이너/퍼블리싱 작업) 코드 수정 없이 YELLOW→RED 승격(검증: published=True 주입 시 RED 341).
>   그전까지 무관한 배포를 막지 않으려는 스테이징 — 불변식 "게이트가 검사하는 파일 = 사용자가 보는 파일"의 적용.
>
> **발주문 1곳 정정(V-1 `AOCI_CONTINUITY`)**: "직전분기 30 == 당분기 20"이 아니라 **직전 FY 4Q의 30 == 당 FY의 20**.
> 한국 중간 자본변동표는 FY 누계라 기초자본 행이 FY 내내 고정(실측: 직전분기 기준 일치 0건 / 직전 FY 4Q 기준 150건).
> 인접분기로 짰으면 전 회사 false RED. 등급은 발주문대로 RED(CSM continuity 동급) 유지.
>
> **RED 328 분해** (파서 발주 `inbox/parser/20260813T0600Z…equity_composition_red_findings.md`):
> census 결측 231(코어 item29 148·item10 167 등) · 부모-자식 28 · 자본총계 폐쇄 22(=CFS 2사 비지배지분 미포착) ·
> AOCI 롤포워드 22(FY2023 기초 오선택, 회사별 상수 오차) · OCI 잔차 19 · stock-flow tie 2 ·
> continuity 2 · 단위 1 · provenance 사이드카 부재 1.
>
> **owner 결정 3건 즉시 반영(341 → 328)**: ① `EQ_RESERVE_WITHIN_RE` RED→YELLOW — 이익잉여금 =
> 준비금 3종 + **미처분이익잉여금**이고 잔여가 음수면 정당하게 초과하므로 항등식이 아니다
> (에이비엘 11·롯데 2건, 파서 재추출 대상에서 제외 통보) ② 케이디비생명 자본잠식 3분기 owner 확인 →
> `owner_confirmed` 등재(flag 성 룰만 억제, census/항등식 RED 는 불가) ③ AOCI↔K-ICS 가용자본 비교는
> 미구현 종결(AOCI 는 IFRS17 개념).
>
> **documented exception 등재(V-2 요건: reason+evidence 없으면 미인정)** — 기계 레지스트리
> `data/_gold/equity_census_exceptions.json`, 사람 사본은 아래 표. 근거는 downloader 답변.
>
> | 회사 | 분기 | rule id | 사유 |
> |---|---|---|---|
> | 전사(*) | 2023.1Q, 2023.2Q | `EQ_CENSUS_MISSING_CELL` | DART FS API status 013 영구공백(24개사 강제 재조회 24/24 일치). 근거: `inbox/parser/20260813T0530Z…equity_composition_raw_ready.md` §1 |
> | KR0150 서울보증 | 2023 전체·2024 전체 | `EQ_CENSUS_MISSING_CELL` | 같은 013이나 gap이 더 넓음(실데이터 2025.1Q~). 근거: 동일 문서 |
>
> **잔여(UH-9 신규)**: ① provenance 사이드카 미발행 → 발행 후 `validate_data_contract` CHECK 2(as_of)에도
> 정식 배선(UH-3에서 검증된 "발행 후 배선" 순서 준수) ② 기대그리드 universe를 형제 마스터 `PL_breakdown`(33사)에서
> 유도 중 — downloader가 말한 Tier-2 대상 15사와 수가 달라, 사이드카의 universe 선언이 오면 그 목록으로 교체.

**(2026-08-03 c) UH-3 종결 — provenance 사이드카 부재 = RED 전환. push 게이트 RED=13 (의도된 차단, 15→13).**
> **V23 `MISSING_PROVENANCE_SIDECAR` YELLOW → RED.** 2026-07-21부터 미완이던 UH-3 end-state.
> 선행조건(CHECK 2 대상 4종 전부 발행) 충족 확인 — publishing `faa34cd`+`emit_capsec_provenance.py`
> 3종 + parser `emit_sensitivity_provenance.py` 1종 → 라이브 YELLOW **1→0**. 이제 부재는
> "미발행(정상)"이 아니라 **발행 경로가 씻겨나간 신호**다. Phase-1 추론 블록은 **진단용으로 존치**
> (그 분기가 RED라 통과 경로 아님 — 작동하는 검사를 버리지 않는다).
> **전환 후 CHECK 2 RED=0 유지 = 오탐 0** · selftest **21 → 22/22**(신규 C3) · 이빨 검증
> (severity를 YELLOW로 강등하면 C3 미검출 FAIL) · pytest 10 passed.
> baseline fixture에 유효 사이드카 4종(`base_sidecars()`) 주입 + `f_stale_as_of`/`f_source_id_lineage_mismatch`
> 결함-1개 원칙 유지로 정정.
> **잔여 UH-8 신규**: `kics_rate_sensitivity`는 `MASTER_FILES`에 있으나 **CHECK 2 검사 대상이 아니다**
> (사이드카 없음 → 소스 신선도 미검증). 발행 선행 발주 `inbox/parser/20260803T0520Z…rate_sensitivity_provenance_sidecar`
> (lane: kics), **발행 후** CHECK 2 2a(iv) 배선(발행 전 배선 = 즉시 red-out, UH-3에서 검증된 순서).
> **RED 13 = 전부 `CAPSEC_COVERAGE_REGRESSION`**(15→13, parser가 KR0050·KR0076 레코드 적재 완료).
> 잔여 13사는 parser `20260803T0400Z` / downloader `20260803T0405Z` 처리 대기 = 의도된 push 차단.
> **부수**: `tests/test_master_tables_golden.py` `qoq_warn 198Y→197Y` 1축 재drift(마스터 미커밋 변경분,
> validation 무관) → 기존 스레드 `inbox/parser/20260803T0245Z…master_tables_golden_drift` 추가 기재.

## Status (이전)

**(2026-08-03 b) inbox 1건 드레인 — 자본성증권 커버리지 census 신설. push 게이트 RED=15 (의도된 차단).**
> **V22 (owner `20260803T0310Z`, blind_spot) `CAPSEC_COVERAGE_REGRESSION` 신설 = V21의 나머지 절반.**
> V21이 "틀린 소스라고 **말하는 것**"을 막은 직후에도 RED=0 — **소스가 통째로 비어도 통과**했다.
> DART 전환으로 annual raw 없는 회사의 채권이 사라져 KR0050 1,000억→0(2030 비율 124→146%),
> KR0076 2,700억→0(94→**152%**, 권고선 아래→위). 원인 = `bond_coverage`가 "스캔 후 무발행"과
> "소스에 아예 없음"을 **한 값으로 뭉갬**. 신규 룰의 축 = **선언된 per-bond 소스 안의 회사 존재 여부**
> (git diff는 보조축 YELLOW `CAPSEC_COVERAGE_DROP_VS_PRIOR`로만). **라벨을 믿지 않고**
> `index_bond_source()`가 소스를 직접 읽어 도출 + 3마스터 전부 + 축 소실 가드
> `CAPSEC_SOURCE_UNRESOLVED`(RED) + 금액 불일치 `CAPSEC_AMOUNT_MISMATCH`(관찰기 YELLOW).
> 배포 에셋 `bond_coverage`는 **추가만** 3-way(`absent_in_source` 신설, 수치 무변).
> **mutation: 배선 전 RED=0 → 배선 후 RED=15** · selftest **16 → 21/21** · pytest 9 passed.
> **RED 15건 exception 안 함** — parser `20260803T0400Z`(raw 있는 12사) + downloader
> `20260803T0405Z`(raw 없는 3사) 발주, raw→재추출→자연소멸이 정상 경로. PM-2026-08-03 **§6**.

## Status (이전)

**(2026-08-03) inbox 2건 드레인 완료 — 신규 게이트 룰 2종 배선, push 게이트 RED=0.**
> **V21 (owner `20260803T0056Z`, blind_spot) 자본성증권 provenance 라벨 거짓 = false-green 해소.**
> 게이트가 capital-securities 3마스터에 `source_id == "FSC_BONDS"`를 **하드코딩 요구** → 2026-06-20부터
> DART가 원천인 tier1/tier2 사이드카가 **DART 파일에 FSC 라벨**을 달아 통과 중이었다(게이트가 틀린 주장을
> "검증"). 신규 **`SOURCE_ID_LINEAGE_MISMATCH`**(RED, 경로 계보 ↔ 선언 라벨 일치) + effective 증거를
> **사이드카가 선언한 계보마다** 요구하도록 재조준(DART per-bond 2축 신설) + **`scripts/emit_capsec_provenance.py`**
> 신설(라벨을 게이트와 같은 함수로 **도출**, 손타이핑 제거) + `tests/test_deploy_assets.py` 기계검사.
> **mutation 증명: 배선 전 RED=0 → 배선 후(정정 전) RED=2 → 재발행 후 0.** as-of 정본 = 2026-03-31 확정,
> `baseline_2025_4Q` 키 misnomer는 **UH-7**로 publishing 발주(`20260803T0210Z`). PM-2026-08-03 작성.
> **V20 (parser `20260730T0040Z`, backlog) `CSM_WATERFALL_PLAUSIBILITY` 신설 = UH-6 해소.**
> `check_census` 1d 배선, YELLOW(관찰기 후 RED). 임계값 **parser 초안 ×20 → ×10 조정** — 초안 근거는
> 정정 전 값이고 정정 후 36사 분포 median 0.563/최대 1.530(×2.7)이라 ×20은 중간규모사 ×10 오류를 놓친다.
> 오탐 억제 (d) 지급여력금액≤0 skip 추가. **라이브 발화 0**(오탐 0). PM-2026-07-30 → closed.
> **게이트 self-test 14 → 16/16 PASS** (G1·G2 신규, 둘 다 이빨 검증 통과). `pytest tests/test_deploy_assets.py` 9 passed.
> **잔여 = 절반-경화 재확인**: `prepush_check.py`는 `validate_kics_disclosure.py`를 호출하지 않아 K-ICS
> 전용 룰은 push를 못 막는다. 체인 추가는 documented RED 8건으로 push를 즉시 차단 → **owner 결정 대기.**

## Status (그 이전)

**(2026-06-20 (b) 게이트 3종 전수 재검증 — owner JSON 직접수정 후)** owner가 root JSON 직접수정(`sync_owner_fills_to_json.py` 135셀 + `insert_kakao_missing_quarters.py` 89행 + MOLE 손정정) → validation은 owner 지시("덮어쓰지 마라")대로 **재적재 0, read-only 검증만**(`validate_master_tables.py --no-build`로 owner값 보존; 빌드 선행 시 diag 미반영분 소실 위험).
> **push 게이트(`prepush_check.py` = data-contract): RED=4, 전부 tier2** — 동양·KB·미래에셋 2026.1Q `T2_UTIL_OVER_100_NO_EXEMPTION`(proxy-gross artifact) + 신한이지 `T2_DENOM_NOT_SCR_HALF`(분모 1/100 스케일). 하나손·악사=YELLOW(면제표 파싱 legit "100%+"). **전부 owner `TODO.md`(6-20)+inbox 라우팅 완료**(downloader OCR `…0617Z…tier2_exemption_ocr` + parser ifrs17 `…0238Z`). push는 이 4건 해소 후 = 현 BLOCKED 정상. **validation 신규발주 0.**
> **K-ICS 게이트 RED=1**(KR0079 미래에셋 8_life 2023.2Q scan-only, SKIP 비차단) + census 4(동양/하나생명/카카오 이미지 PDF) = 전부 documented. **IFRS17 master: closing 321P/0F · crosscheck 0F**(owner PL 121셀+CSM 10셀 수정 무손상) · plausibility **cont 12→6 개선**(손정정 효과) · sens 1R(라이나 천원 미정규화=기존 0712Z/V12 audit-only 추적) · pl_bridge 14F(2023 known + 한화생명 이상치, 비차단).
> owner 룰7/8 dynamic tolerance 독립검증 **PASS**(`max(eff_tol, |exp|×0.5/d14 + 50/d14)` 분모 d14 반비례 → 정상분모 tol=2.0 불변, 카카오 20억만 124%p → 마스킹 0). **validation-actionable 신규 = 0** — 모든 잔여 RED는 owner 인지/라우팅/documented.

## 🔴 Open — P1

### V19 — 사고 포스트모템 관행 도입 + 기존 4건 소급 (owner `20260721T0233Z`, 2026-07-21)
"포스트모템이 게이트 룰로 종결되지 않으면 같은 부류가 재발한다" → 5칸(무엇이 통과/어떤 룰이면 잡았나/
지금 배선됐나/exception 근거·등재위치/미배선 잔여+후속티켓) 미충족 시 close 불가인 관행 신설.
- [x] **구현형태 = 로컬 스킬** (`.claude/skills/incident-postmortem/`). 외부 스킬 미채택 — 5칸이 이
  저장소의 게이트 파일·registry 변수명·display-scope를 직접 지목해야 강제력이 생기는데 범용 스킬은 불가.
  기존 로컬스킬(`kics-parser`·`ifrs17-parser`) 패턴 + 금융데이터.
- [x] 정본 `docs/postmortems/README.md` + `_TEMPLATE.md`, 스테이지 프롬프트 §5.1에서 링크.
- [x] **소급 4건 기록**: PM-2026-06-16(두 달 글리치, closed) · PM-2026-07-07(적용후 사각, **open**) ·
  PM-2026-07-08(V17 가짜복사, **open**) · PM-2026-07-15(부모 census, closed).
- [x] **소급의 실질 산출물 = 미배선(UH) 적발 → P1 2건 즉시 배선(owner 승인 2026-07-21)**:
  - [x] **UH-1 해소**: 적용후 검증 7종(`_transition_ratio_after_capture`/`_transition_mmult_after`/
    `_transition_identities_after`/`_parent_present_child_incomplete_after`/`_diversification_negative`/
    `_item12_equals_item1`/`_ratio_series_spikes`)을 `validate_data_contract.py` `check_census`
    **1b(iv)** 로 lift(display 7분기 scope). 6종 RED + spikes만 YELLOW(휴리스틱 단독차단 금지).
    **주입 테스트 검증**: scope를 2023.1~3Q 임시확장 시 baseline RED 0 → lifted RED 4건 방출 =
    함수→`_emit`→`res.add` 경로 작동. 배선 후 실 push 게이트 **RED=0 유지**(현 findings 전부 non-display).
  - [x] **UH-2 해소**: push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·
    `triage_anomaly_candidates.py`) **git 등재**. gitignore가 아니라 단순 미추가였고 나머지 의존성
    (`validate_kics_disclosure.py`·`validate_master_tables.py`·`kics_json_rules.py`)은 이미 tracked.
  - [x] **도메인 경계 명문화(owner)**: 경과조치=K-ICS 전용(적용전/후 이중공시). **IFRS17엔 대응 개념
    없음**(전환방법=도입시점 측정방법, 이중컬럼 아님) → 복사할 짝 자체가 없으므로 `TRANSITION_AFTER_*`
    IFRS17 유사룰 금지. 상위 패턴("presence만 검사→세탁")만 도메인 무관(IFRS17은 기존 plausibility/
    impossible-0가 담당). postmortems README·SKILL에 기록.
  - [x] **UH-4 해소 (2026-07-21)**: `scripts/_data_contract_selftest.py` 신설 — `Env(inject=)` 합성
    mutation suite **14/14 PASS**. 기존 spec §5 회귀 + **1b(iv) lift 5종(F1~F5) 회귀 보호**.
    **이빨 검증**: `_item12_equals_item1`·`_post_transition_parent_census`를 monkeypatch로 죽이면
    해당 케이스 미검출→FAIL 확인. 이후 신규 룰은 여기 케이스 추가 필수.
  - [x] **UH-3 부분강화 (2026-07-21)**: sidecar 부재가 `notes`(비집계)로 조용히 통과하던 것을 집계되는
    **YELLOW `MISSING_PROVENANCE_SIDECAR`**로 승격. **RED 전환은 발행 후** — 지금 RED면 미발행 마스터
    전부 red-out으로 push 영구차단. **진행: sidecar YELLOW 4→1** — publishing(`faa34cd`)이
    forward_capital·tier1·tier2 발행 → 3종 Phase-2 strict 전환. **sensitivity_heatmap만 잔여**
    (parser(ifrs17) `20260721T0530Z__…sensitivity_heatmap_provenance` 발주 대기). 4종 전부 발행 후
    no-sidecar=RED 보편룰 활성화.
  - [x] **UH-5 종결 (owner 승인 2026-07-21, premise-refined)**: 선행조건이던 FSS 2023-03-20 붙임-1
    (`trend20230320_3.pdf` p6, 회사별 경과조치 종류)을 좌표추출 전수 복원(총계 검증 4/19/12/8 일치)
    → `_TRANSITION_KIND` registry(`scripts/validate_kics_disclosure.py`) 등재. **전제 falsify**:
    "TAC형(가용자본만)" 회사 = **0사**(가용자본 신청 4사 전부 요구자본 보험리스크도 신청, elective
    18사 전원 요구자본 경과조치사). **실측 78 "부모후=전" 셀** = A(subrisk후≠전·부모후=전 모순) **0**
    [기존 `_transition_mmult_after`가 이미 강제] + C(item14후 다름·부모후=전) 52 **전부 item19(시장위험)**
    [주식/금리 미신청사 정당 + 신청 3사도 조건부 미발동 가능·내부정합] + D(subrisk후 부재) 26 [census
    소관]. **진짜 미검출 0** → 부모 COPY 룰은 item17=mmult 중복·item19=오탐 52 → **신설 불요.**
    owner Socratic 지적("subrisk 다르면 상위도 달라야")이 결론 핵심 — 참이며 이미 mmult가 강제(A=0).
    postmortem README 3차 종결 기록.

### V18 — 적용후 요구자본 **부모** census blind spot 정정 (owner `20260715T0801Z`, 2026-07-15)
07-12 V17 census(`_parent_present_child_incomplete_after`)는 **부모후가 present일 때** 자식후 결측만 봄 →
**부모(15~21) 자체가 통째 결측이면 census/identity/mmult 전부 skip = false-green.** 2026.1Q 5적용사
(한화생명·교보·하나·롯데손해·농협) 요구자본 부모후 결측인 채 push 게이트 통과사고.
- [x] **게이트 신설 `_post_transition_parent_census`** (scripts/validate_kics_disclosure.py): 적용후 공시
  회사의 부모 15~21(코어)·22/23(조정) 값_적용후 **continuity break**(직전분기 present인데 당분기 결측 +
  이후재출현=SANDWICHED/최신=TRAILING) = RED. onset·항구적중단 flag 안 함(오탐억제). 22/23 단독=review(비차단).
  **적용사 판정=continuity 자체**(18사 하드코딩 아님) → 공통경과조치사 한화생명(KR0068)·삼성생명(KR0069)도
  포착(기존 18사룰 사각). 면제 registry `_POST_PARENT_NOT_DISCLOSED`=비어있음(owner "오면제 금지").
- [x] **양쪽 배선**: K-ICS 게이트(전분기 exit2) + **push 게이트 `validate_data_contract.py check_census`
  (display 분기만 차단)** ← "push 게이트가 통과"의 정정 지점. 두 스크립트 compile OK, 기존검사 무회귀.
- [x] **2026.1Q 라이브 해소 확인**: 병행 parser 세션이 5사 15~23 값_적용후 UPSERT(mtime 17:32) →
  2026.1Q census RED=0 + mmult/항등식/분산효과후 0 통과(fill 정합). **게이트가 갭→RED, fill→통과 검증.**
- [x] **parser 발주 `20260715T0835Z` 처리+적대검증 완료 (2026-07-16, resolved)**: push 게이트 census
  RED **47→4**. parser fill(삼성생명 2025.1Q·동양생명 4분기·한화생명 2025.2Q/3Q·흥국생명 17~21) 검증:
  - **미러fill(후=전) 정당성 PASS** — 삼성/동양/한화는 공통경과조치사(요구자본 후=전, 가용자본 item1만
    2025.2Q Δ실효과). V17 가짜복사 아님. 무회귀(mmult/항등식/ratio COPY/분산효과 전부 0).
- [🔴→👤] **잔여 push-block 2건 = owner escalate (raw 도출불가, `_POST_PARENT_NOT_DISCLOSED` 결정 필요)**:
  - **흥국생명(KR0071) 2024.4Q [15,16,22]**: image PDF + TIR+TER 다중경과조치 R4 재현불가(역산 item15
    14,747 vs 헤드라인 16,987, Δ2,240 비반올림). parser 비전판독 17~21은 채움, 15/16/22 결합불명.
  - **하나생명(KR0097) 2024.4Q [16]**: 비표준 공시(감사보고서 재무상태표, 이미 `_AFTER_SUBRISK_NOT_DISCLOSED`).
    item16후 산술파생 가능(=1369.09)이나 입력 item17후=1757.32가 raw page(2001.90) 불일치(partial-mmult
    아티팩트 의심) → 파생값 불신. owner 택일: item16 파생채움 vs 부모후 exemption.
  - **owner 결정 대기** — 둘 다 `_POST_PARENT_NOT_DISCLOSED`(scripts/validate_kics_disclosure.py) 등재
    또는 parser 재추출 지시. validation 자체 waiver 안 함.
- non-display 비차단 워크리스트(push 무관): 코리안리 KR1000 3분기·악사 2024.3Q·처브 2024.3Q·IBK연금
  2023.2Q(다중경과 결합불가 기지)·하나손/하나생 2023.2Q. git-purge raw, 저우선.
- 완료기준: 게이트 `post_transition_parent_census.red` display분 = 0 (현 4, owner 2셀 처리 시 0).
- [x] **건2 `8_post` dynamic tol (publishing `20260712T0219Z`)**: 이미 코드반영(07-12) 확인 —
  KR1098 2023.4Q 8_post=YELLOW(diff -92.82 tol내), `7_post` 룰 부재(누락 없음). resolved.

### V17 — 🚨 경과조치 "적용후" 전수 재추출 (owner 전수건 21/22 미처리, 2026-07-05 재발주)
owner `20260703T1138Z`(경과조치 적용후 컬럼 구조적 유실, 22 적용사) = **여전히 open, IBK연금 1개만 처리.** 이번 라운드 최대 미완건. validation 라이브 실측 후 최우선 재발주.
- [🔴] **parser "복사버그 정정" = 가짜수정 적발·반려 `20260705T2150Z`**: 파서가 커밋 5건(31bcead 등)으로 처리 주장했으나 검증 결과 **적용후 = round(적용전) 복사**(exact-identical만 피한 위장). item27 22적용사 285셀 중 **164 가짜/결측**(복사139+결측19+역전6), 진짜 후>전 121뿐(정상마진 50~190%p). → 진짜 raw 재추출 강력 반려.
- [x] **게이트 하드룰 신설 `_transition_ratio_after_capture`** (owner #6): 적용사(owner 22 seed ∪ 동적) item27 적용후 ≤ 적용전+1%p(복사/반올림) OR 결측 OR 역전 = **RED, exit 2 차단**. IBK연금만 0=정상재추출 통과(오탐0). self-test 7/7. 재검툴 `scratchpad/verify_item27.py`·`adversarial.py`.
- [🔴] **2차 적대적 검증 → 파서 회피 재적발 `20260706T0434Z`**: 파서 재수정(168→112) 후 적대검증 = 두 회피. **(A) "진짜동일 재확인" 5사(한화생명·코리안리·신한라이프·KB라이프·동양) 거짓** — 동양 2025.2Q 후>전 실재(172→177)로 반증, 나머지 유실. 게이트 seed로 63셀 RED 유지=재분류 거부. **(B) item27만 패치·금액(item1/14)후 미수정 정합붕괴 9건**(한화손해 item27후283≠도출190). → **게이트 AMT_MISMATCH 검사 추가**(item27후≠item1후/item14후×100 >2%p=RED). 현 **121 RED**(COPY50·MISSING19·LOWER43·AMT_MISMATCH9). iter3, 다음 회피 owner escalate.
- [x] **선택 경과조치 적용사 정본 확정(2026-07-06) = 18사**: owner가 **FSS 2023-03-20 보도자료 붙임-1**(`trend20230320_3.pdf` p6, 원수사별 신청현황) 제공 → 22-seed·그간 추정 전부 폐기. **생보 12**(ABL·흥국생명·케이디비·교보생명·아이엠라이프[=구DGB]·DB생명·푸본현대·하나생명·처브·교보라플·IBK·농협생명) **+ 손보 6**(AXA·한화손보·롯데손보·예별손보[=구MG]·흥국화재·NH손해). SCOR재보험=데이터부재. 나머지=공통(TFI) 후=전 정상. 코리안리·메리츠·한화생명·신한라이프=미적용 확정(오탐 해소).
- [x] **게이트 item27+item28 이중검사 + AMT_MISMATCH**: 18사 하드코딩, 두 비율 후≤전+1%p OR 결측 OR 항등식붕괴=RED exit2. 현 **139셀**(item27 68·item28 71; 케이디비·하나생명 최다=전량유실). self-test 7/7. 정본 발주 `20260706T0502Z`(2150Z·0434Z supersede).
- ⚠️ **publish = 보류 확정**: 적용후=화면 표시값. 18사 item27·28 적용후 진짜 재추출(item1·2·14 정합) + 게이트 139→0 전엔 불가.
- [x] **(2026-07-12 c) 전수 헤드라인 대조 + 파서 IBK fix 반려**: 18적용사×전분기 raw '경과조치 후' vs item27후(anchor 오탐0) → 110정합·**예별손해 KR0004 2023.1Q/2Q/3Q 불일치**(item27후=②표단독 74.67 vs 헤드라인 82.56, IBK동형 혼합)·119 자동파싱불가. **파서 IBK fix(0430Z) 반려**: item1후를 TAC단독 8241.63으로=**공통TFI 누락**(정답 9164.38=원래값, item14후 5179.08). 발주 `20260712T0700Z`(IBK반려+예별3+per-company 재조정). 케이디비 2025.4Q=내 오탐(데이터 205.7 정상).
- [x] **(2026-07-12 b) 파서 census-fill 적대검증 + 분산효과 부호 sanity**: parser 322→2 fill(a797681) 독립검증 = **견고**(item18=0이월·carry·mmult·한화손해 item19후=전 raw확인·롯데/교보 2026.1Q exemption raw정당). **단 적대스윕이 파서무관 기존오류 1건 적발**: IBK연금 2023.2Q 적용후가 ②표(시장불변)·③표(시장감소) 혼합→분산효과 -246.66(음수)+item27후 135.19≠헤드라인 176.95. **`_diversification_negative` 신설**(전·후 전체회사 item16<0/Σ(17~21)<15, RED blocking). parser 발주 `20260712T0430Z`. 현 게이트 분산효과음수 1(IBK) 차단.
- [x] **(2026-07-12) 적용후 요구자본 census 신설 = blind spot 정정**: owner가 아이엠라이프 2025.4Q 적용후 신용·분산효과 결측 지적 → 적용후 게이트가 mmult(item17/19 leaf)만 보고 **요구자본 구성(15→16~21) census 부재** 확인(항등식 R6은 결측셀 skip → 양쪽 샘). **`_parent_present_child_incomplete_after` 신설**(적용전 census 미러, 부모맵 15/17/19, RED blocking, exit-code 배선). **적발 322 항목셀(149 부모·분기)**: DERIVE 96(분산효과=Σ(17~21후)−15후)·CARRY 206(신용/운영/시장하위 후=전)·EXTRACT 20(raw재추출 14 회사·분기). 분류 `data/_derived/after_census_gaps.json`. parser 발주 `20260712T0230Z__…__after_requirement_census_322cells.md`. **현 게이트 census 149 RED 정상차단, parser fill 후 0 확인→재publish.** (owner가 앞서 현버전 라이브 push함 — 이 부분충전은 요구자본 detail, headline 지급여력비율후는 정상.)

### V16 — parser IFRS17 재빌드 검증 + IBK연금 무재보험 false-positive 해소 (2026-07-05, owner "cell 등록")
parser IFRS17 레인 재빌드(viz+마스터) 후 게이트 전수 검증. 코어 무손상 확인 + push RED 오탐 1종 해소.
- [x] **코어 정합성 검증**: closing 324P/0F · crosscheck 0F · cont 0 · dup 0 유지. tier2 data-contract RED **4→0**(소진율/분모 이슈 해소).
- [x] **IBK연금 재보험손익=0 ×4 = 오탐 확정**: 순수 연금사 무재보험(재보험 5 leg 전부 0 + 원수분해 정확히 닫힘). owner "cell 등록" → `user_pl_confirmed_cells.json` 4셀 + `validate_data_contract._pl_impossible_zero_leg` registry 존중 배선 + 마스터게이트 `IMPOSSIBLE_ZERO_EXEMPT`/`ZLEG_LEGIT` 면제. **prepush RED=1, 마스터 impossible0 0/zero_legs 3**.
- [x] **KR0083 2025.2Q 19_market 해소 (2026-07-05 b)**: downloader 오슬롯 PDF 교체(KR0075 BNP가 덮던 것) → parser 재추출(subs 29-46 복원, 19_market reconcile ✓). **prepush RED 1→0 = GATE-CLEAR**, K-ICS RED 9→8(전부 documented: KR0079 8_life SKIP + KR0087 동양 2023.2Q 이미지전용).
- [x] **parser 0745Z 처리 완료(2026-07-05 c)**: PARTIAL 14→3·FULL_ABSENT 14→2. 시계열 검증으로 잔여 판정 — 진짜갭 2건(교보 item35·BNP item37) 재발주 `0805Z`, 카카오 micro-0 수용, 신한이지 LTC는 floor 1.0→5.0 자체정리, KR0104·KR1010 legit-absent 수용.
- [x] **전건 해소 (2026-07-05 d): PARTIAL 14→0.** 교보 item35 백필·BNP item37/38 genuinely-0 적재(파서 MD근거 "변액주식 139억 감소"=내 통계추론 오판 인정)·카카오 item40 0.0 적재·신한이지 floor 자체정리. `0805Z` resolved. 잔여 = FULL_ABSENT 2(KR0104·KR1010 legit-absent 비차단) + census-missing 3(documented).
- [→] **follow-up: prepush에 `_parent_present_child_incomplete` 배선** — 지금은 PARTIAL 0이라 무영향이나, 향후 push 권위 게이트가 이 축을 정직하게 강제하도록 배선 권장.
- 참고: `_data_contract_selftest.py` 부재(pre-existing purge) — 게이트 정상, 회귀는 라이브 실측 대체. 메모리 [[owner-confirmed-registry]].

### V15 — 게이트 사각 2종 신규룰 (parser blind_spot 0703): 부모-자식 census + 지급여력비율 스파이크
owner 워크스루가 게이트 RED=0 통과분에서 잡은 2부류를 parser가 blind_spot으로 이관 → 룰 강화(데이터는 parser 수정 완료). 둘 다 `scripts/validate_kics_disclosure.py` 구현, self-test 7/7.
- [x] **`_parent_present_child_incomplete` (RED)**: 부모(item17/19)>0인데 회사별 self-census상 '평소 유의미 보고' 자식(29-35/36-40) 결측=행누락. 기대=과반present&중앙값≥1억(회사유형 아님 — 손보 장수리스크 실보고사 DB손해/코리안리/삼성화재 검출유지; 구조적0 LTC 제외). **PARTIAL만 RED(14)**, FULL_ABSENT even-Q(16, 2023.2Q 도입초 클러스터)는 원천확인 review 비차단. 역방향(`_parent_zero_child_nonzero`는 부모0·자식≠0만) 사각 닫음.
- [x] **`_ratio_series_spikes` (YELLOW)**: item27 인접 2분기 양방 이탈 단일분기=소스오염(부호역전 자체는 자본잠식사 정상이라 flag 안 함). 라이브 0, 옛 KR0083 25.2Q +318 주입 발화 확인. item27 중복행 dedup.
- [→] **parser 백필 발주**: PARTIAL 14 RED(KR0050 34·35 등) + FULL_ABSENT 16 review → `inbox/parser/20260704T0745Z…parent_child_census_gaps`. 재파싱 후 게이트 재확인.
- 부수발견(동봉): item27 중복행(삼성생명·메트라이프 이중정밀도), 세션중 kics_disclosure.json 재작성(parser 활성). blind_spot 0703 + owner 1529Z → `_resolved/`. 메모리 [[coverage-census-mandatory]]·[[validation-blind-spots]].

### V10 — KICS gate coverage census + 19_market SKIP blind spot (2026-06-12 owner 적발)
Root cause: gate didn't census "cells that should exist" + treated SKIP as pass. RED=292 after fix.
- [x] **19_market 과잉 RED 수정** (2026-06-13c, source-grounded cadence): 내 06-12 RED 승격이 cadence 미처리로 홀수 간이공시를 과잉flag. `_scan_breakdown_presence()`(disclosure MD 직접확인) + 짝수=항상RED·홀수=MD표유무로 판정. **RED 148→21**(EVEN 18 + 삼성생명 odd 3 = 진짜갭), cadence-SKIP 127(전부 홀수 간이공시). raw 확증(삼성화재/현대 홀수 MD에 세부표 부재).
- [→] **parser 재추출 (19_market 진짜갭 21건만)**: 짝수 full-form 결측 18(KB손해2024.4Q/2025.2Q·한화생명2023.4Q/2024.2Q·흥국생명/흥국화재2024.4Q·DB생명2025.2Q·DB손해2024.4Q·NH2025.4Q·신한이지3·처브3·AIA2025.4Q·카카오2025.4Q) + 삼성생명 odd 3(2023.3Q/2024.1Q/2024.3Q, MD에 표 있음). gold: 하나손해·삼성생명 2025.4Q(이미 GREEN). 148→21로 정정 inbox 발송.
- [→] **2026.1Q 항목 절단 (parser)**: 30사 적재됐으나 전 회사 항목 1–28까지만, 29–46 전무 → backfill.
- [→] **census 미싱셀 28건 (parser)**: 미래에셋(7분기)·코리안리(6분기)·동양·하나생명 등 MD는 parsed인데 JSON 추출 누락.
- [x] **`36_irr` SKIP맹점 폐쇄** (2026-06-13): cadence-aware RED 승격 — item36 공시·41–46 결측이 **짝수분기(2Q/4Q)면 RED**(시나리오표는 2Q/4Q 서식에만 존재, 실증: 41–46 전 분기 짝수에만 적재), **홀수분기는 SKIP**(원천부재 정당). `IRR_SCENARIO_EXEMPT` 면제셋(빈값). 결과: RED 23(전부 짝수, 홀수 false 0). 19_market 동형. → parser 41–46 재추출(아래 23건, market_subrisk inbox 후속).
- [x] **`report_latest.json` fresh-write** (2026-06-13): 게이트가 매실행 `artifacts/kics_validation/report_latest.json` 덮어쓰게 함 → stale glob 함정 제거(소비자 코드 0, orphan 5/25본이 문제였음).
- inbox: `20260611T2200Z__validation__MULTI_ALL__kics_market_subrisk_systemic_underparse.md`. 메모리: `coverage-census-mandatory`.

### V12 — CSM 민감도 전수 재추출(25.4Q 경영공시 기준) + direction sanity (2026-06-15, parser 대기)
owner: IFRS17.html 흥국생명 CSM 민감도 이상 지적. 진단 = 현 소스가 FY2024 DART 사업보고서(1년 stale·비전수), parser 추출 자체는 정확.
- [→] **parser(ifrs17) 전수 재추출 발주**: `sensitivity_heatmap.json`을 25.4Q 경영공시(`data/disclosure/FY2025_Q4`) 기준으로. inbox `20260615T0415Z__validation__MULTI_2025.4Q__csm_sensitivity_refill_disclosure_basis`. risk 전수(사망/해지/사업비/장해질병 정액·실손/…), 당기말만, csm_delta=CSM·pl_impact=손익효과, 억원 정규화, unavailable 정직표기. 미다운로드면 downloader bounce.
- [x] **SENSITIVITY_DIRECTION_SANITY 룰 신설**(`validate_master_tables.py` 5b): sign(csm_delta)≠sign(pl_impact) YELLOW. fill 후 재검증 시 sign-opposition 전수 triage(real vs 파싱오류).
- 참고: 흥국 해지율 역행=source-faithful(건강보험 견인), 장해질병 누락=FY2024 사업보고서 부재 → 경영공시로 해결. recency는 사업보고서≈경영공시(둘다 2025.12.31), 전수·granular가 경영공시 우위.

### V13 — 부모-자식 정합 룰 + INTERNAL_MODEL_36IRR 등록 + 카카오 cadence 정정 (2026-06-16, owner 라이브 QA 3차)
owner SGI 게이트 사각 + parser INTERNAL_MODEL 승인 inbox 드레인.
- [x] **`_parent_zero_child_nonzero` 룰 신설**(`validate_kics_disclosure.py`): 부모 위험액 present&≈0인데 하위 비0 = 구조상 불가능 RED(게이트 차단). item17→29-35, item19→36-40 명시매핑. 전수 3셀: 서울보증 2025.4Q(item35=5212)·2023.4Q(5264)·카카오 2023.3Q(4.72) 전부 대재해 오정렬.
- [x] **parser 발주(3셀 재파싱) → ✅ RESOLVED (2026-06-20 게이트 재확인)**: `Parent-zero / nonzero-child: 0` 실측. parser round3 K3가 서울보증/카카오 orphan item35 제거(parent17=0 가드) → 게이트 parent-zero 0 수렴. (`inbox/parser/20260616T0130Z__validation__MULTI__parentzero_catastrophe_plus_kakao_19market`.)
- [x] **INTERNAL_MODEL_36IRR_EXEMPT 등록**(owner 승인 2026-06-15): `kics_json_rules.py` frozenset 5셀(KR0073 2025.2Q·KR0094 ×4) RED→SKIP. **36_irr RED 11→6**. pytest 110 passed.
- [→] **카카오 2023.3Q 19_market 재특성화**: parser "cadence SKIP" 제안 = 부적절(MD L177-186에 분해표 실재 = 19_market RED 참). micro 억원-coarse라 카카오 2023.2Q 동류 artifact. 처분(파서 적재 후 micro / owner micro exception) = owner 결정. TODO.md(root) line 79-80 카카오 cadence 분류 정정 필요(owner 갱신).

### V14 — backlog #6/#7/#8/#9 (2026-06-16, owner "전부다 진행", 4-에이전트 Workflow)
- [x] **#6 삼성화재 FY2024 IR benchmark RESOLVED**: `validate_nb_csm_multiple.py` `load_fy2024_ir_anchors`(IR series 2024.4Q.multiple_derived_ytd) + 삼성화재 PREFERRED_SCOPE monthly_avg_from_ytd → computed 14.76/IR 15.16 rel 0.026 fallback_used=False. **fallback_pass 2→1**.
- [x] **#6 현대해상 = 영구 fallback 확정 (owner 2026-06-16: "현대해상 IR은 CSM배수 없어 패스")**: 현대 IR이 신계약 CSM 배수를 아예 미공시 → benchmark 불가, fallback(2025.2Q=18.9)이 정상·영구. fetch 불요. V2 line 87 "현대 IR multiple 부재→영구 fallback"과 일치. fallback_pass=1은 이 1건(현대)으로 고정.
- [x] **#7 CONT 면제 → REVERT (owner 2026-06-16)**: 한때 CONT에 documented-재작성 면제를 넣었으나 owner 지시로 즉시 되돌림 — **continuity break(기시≠직전기말)는 무조건 RED, "소급재작성"이라 면제 금지**. cont=15 유지(면제 0), WFY 면제만 존치. pytest 110. 메모리 [[continuity-break-is-red]] + [[route-by-raw-availability]] 저장.
- [→] **#7 2026.1Q boundary = 파싱오류 (정정 2026-06-16, owner 원본검증; 내 #7 오진 시인)**: 5사 2026.1Q 기시 CSM이 misparse — 정답은 직전 2025.4Q 기말(교보 65,110·메리츠 111,037·신한라이프 75,537·에이비엘 9,702·푸본현대 1,907.45). self-closing identity는 opening 검증 못 함(오진 원인). **재작성 아님 = RESTATEMENT_EXCEPTIONS 등록 금지, CONT RED 유지.** `data/dart/FY2026_Q1/` 부재(purge) → downloader raw 복원(`inbox/downloader/…restore_fy2026q1_dart_raw`) → parser/ifrs17 재추출(`inbox/parser/…csm_2026q1_opening_misparse`). 복원 후 재검증.
- [i] **#7 저배수 4사 = scope 오류 아님**(framing 정정): 교보 6.61/한화 9.84=2026.1Q Q1 계절저점 YTD(한화는 IR FY 7.6 초과), 교보플래닛 2.0·처브 2.4=micro 실제 저배수. 분자 전부 waterfall item2 일치. **조사 종결, 액션 없음.**
- [x] **#8 verify_parser_change.py 신설**: snapshot/diff(blast-radius, kics cell-diff)/validate(6검증기 일괄)/all. 추출기 변경 회귀 1커맨드. 통합 validate 검증 완료.
- [x] **#9 QoQ yaml loader = 이미 배선**: `validate_master_tables.py:84` 이미 `yaml.safe_load(config/qoq_thresholds.yaml)`. backlog 항목 stale, no-op.

### V11 — 2026-06-14 (b) 정합성 전수검증 후속 (라우팅 발주 + owner 예외 결정 대기)
근본원인 검증 Workflow(8 에이전트 raw 대조) 후 비-시장 등식 RED 4종 disposition:
- [x] **메리츠 KR0001 rule5 reparse → ✅ RESOLVED**: parser가 item23+item25 12분기 적재(항등도출=공시값 일치). 재검증 **rule5 12 RED→0**. `_resolved/` 이관.
- [x] **코리안리 KR1000 2025.2Q reparse → ✅ RESOLVED**: parser가 코어 1-28 + item28 파생(156.19) + 시장37-40 fitz 적재. 재검증 **7 RED + 19_market→0**. `_resolved/` 이관.
- [x] **푸본현대 sensitivity (ifrs17 발주) → ✅ RESOLVED**: parser 근본원인=mis-tag 롤포워드(shock행0), `_has_shock_rows` 가드로 KB·푸본현대 ok→partial 정직화. 재검증 **SENSITIVITY YELLOW 1→0**. `_resolved/` 이관.
- [x] **(종결 2026-08-20) AIA KR0080 2025.1Q rule2** — owner 예외 등재 **이미 완료**: `TODO.md` L115 *"rule 2 × 1: KR0080 AIA 2025.1Q (diff=−789) — scan-only(아래 documented)"*. 게이트 계약 충족.
- [x] **(종결 2026-08-20) 미래에셋 KR0079 8_life** — owner 예외 등재 **이미 완료**: `TODO.md` L117 *"rule 8_life × 1: KR0079 미래에셋 2023.2Q — scan-only. 8_life는 SKIP=게이트 비차단"*. 게이트 계약 충족.
- [ ] **(owner 결정) parser irr_exempt v2 잔여**: INTERNAL_MODEL_36IRR = **신한라이프 KR0094×4 + 교보 KR0073 2025.2Q = 5건만**(IBK KR1011은 parser fitz로 41-46 적재·derive rel 0.0% GREEN → 면제 불요, 2026-06-14 정정) + OCR(KB/한화생명/흥국×2) + micro(신한이지 KR0051×3) EXEMPT — 전부 owner 권한. inbox/validation answered 참조.
- [x] **scan false-positive fix**: `_scan_breakdown_presence` clean-cell화 → 삼성생명 odd-Q 3 false RED 제거(19_market 15→10). parser D 종결.
- [x] **SENSITIVITY_UNIT_SANITY 룰 신설**(owner 0712Z claim2): `validate_master_tables.py` RED>1000x/YEL>100x. 640배 회귀가드. 푸본현대 YEL 1(÷100 미정규화 의심) + 미래에셋·롯데·한화손해 sensitivity 0건 → parser/ifrs17.
- [x] **TOOLING_FAIL census 배선 완료**(2026-06-14, owner "AB go"): `validate_kics_disclosure.py._market_tooling_fail()` — nonok.json을 현 데이터와 대조해 여전히-갭 셀만 're-localize' 노출(stale 제외, 비차단). 현 0건. parser fitz-fallback 안착분 이행.
- [x] **hyundai_pl ZLEG 등록 완료**(KR0009): 현대 2024.1Q~2025.2Q `ZLEG_LEGIT_CQ` 등록 → zero_legs 6→1. thread 종결.
- [→] **KR0083 푸본현대 2026.1Q continuity**: FY_BOUNDARY 2025.4Q기말 1906≠2026.1Q기초 1669(Δ12.4%) 현 RED + sensitivity flagged = 실데이터 의심, 잔여 유지.

### V7 — NB CSM cross-source + 시계열 전수 (parser P1/P2 회귀 잔여)
Rule `NB_CSM_DART_VS_IR_ANNUAL_SUM` codified (§1.2, RED, tol max(5%·|IR|, 100억)). Tools: `check_nb_csm_widespread.py` (FY24 snapshot, 6/7 OK) + `check_nb_csm_history.py` (13Q×9사 baseline). FY24 widespread: 롯데 1.233 (+23%, FY25 의존), 나머지 ~1.00 OK.
- [→] **Parser P1**: 롯데 FY2025 구성요소별 차이조정 표 capture + NB override (412,168 = IR FY25 일치). Raw: `data/dart/FY2025_Q4/raw/KR0003_롯데손해보험_20260319001293/_00760.xml:27375`.
- [x] **🚨 Parser P2 회귀 = 재확인 완료 (2026-06-16)**: off-by-one-year **해소 확정**(현 `data/ir/series/` Q1 YTD-reset 정합, 삼성화재 6782.7→14426→...→2024.1Q 8855.5 리셋). `check_nb_csm_history.py` **복원**(self-contained, 컨벤션 series 메타 도출) + `nb_csm_history_check.json` 갱신. **systemic-3 = 실재(정렬 아티팩트 아님), 근본원인 = DART CSM_waterfall partial/no_csm_block 추출**: 롯데 2025.2Q partial→NB_YTD=0→delta −1098.5(음수 불가) / 미래에셋 2025.2Q·3Q partial→collapse-then-catchup spike(=↑↓ 교대) / 2025.2Q cohort-wide 동일. DB 부호반전은 DB DART 2025.2Q+ 부재로 재현 안 됨. 삼성생명 2025.2Q OVER(+26%)=status ok=진짜 scope 차이(별건). → parser/ifrs17 `20260616T0230Z__...nb_csm_partial_extract_corrupts_history` 발주.
- [→] **한화손해 stale carryover** (별도 parser 버그): 2025.1Q DART NB가 2024.1Q 값 그대로 복제됨. 한화손해 IR note에 기록.
- [ ] (passive) V1 활성화 시 `CSM_WATERFALL_DART_VS_IR` new_business step과 overlap → retire 검토.
- Regression cmds (parser P1+P2 후): `check_nb_csm_widespread.py` → ok=7/7; `check_nb_csm_history.py` → OVER/UNDER 0 수렴.
- Gate enforcement는 publishing stage 측(사용자가 publisher에 전달).

## 🟠 Open — P2

### V8 — DART 자기완결 정합성 (CSM_waterfall 도메인 잔여)
PL_BRIDGE + CSM_CROSSCHECK 소비자 코드 구현 완료(2026-06-07). 빌드→검증 통합(`validate_master_tables.py`가 `build_root_masters.py` 자동 선행, idempotent; `--no-build`로 끔). 회귀 명령: `python scripts/validate_master_tables.py`. 현재 dup:0 spike:1 cont:12 crosscheck:0F closing:0F.
- [→] **데이터 채움 (parser/수집)**: 미래에셋 CSM상각 2025.2Q·3Q·2026.1Q 누락(2025.1Q는 있음), 롯데 생명장기손익 2025.2Q 누락(1Q·3Q는 있음). closing/pl_bridge가 skip하던 진짜 hole.
- [x] **cont 6건 = 둘 다 데이터 정정 → ✅ RESOLVED·검증완료 (2026-06-20)**: boundary break 2종 모두 후속 공시 '전기(비교)' rollforward로 과거 cell 정정 → cont 자연 해소. **parser 처리 완료, validation 재검증 `cont 6→0` 확인**.
  - **교보생명 2024(cont 2 + wfy 1) = legit 소급정정**. owner: "24.3Q부터 회사가 기초 58249로 소급정정 → 2024.4Q+ 보고서 '전기'열에 재작성 2023말값". **처음엔 면제(`CONT_RESTATEMENT_CONFIRMED`) 등록했으나 owner가 데이터정정 방식 제안 → 면제 코드 원복, 정정 발주로 전환**(더 정확, 시계열 통일). parser `inbox/parser/20260620T0600Z__validation__KR0073__kyobo_csm_priorperiod_pull`. raw XML purge지만 **extracted 살아있음**(`data/dart/extracted/교보생명보험_<rcept>_measurement.json`).
  - **삼성생명 2024(cont 4) = misparse**. owner: "2023.4Q 기말 122474 정답, 현 123926 오류". parser `0545Z`(owner-gold + 동일 extracted-전기 기법 교차검증).
  - 둘 다 정정 후 **cont 6→0**. 케이디비 spike(2024.1Q→2Q +58%)는 별건 잔여.
- [→] **PL 잔여 14F**: (1) 2023 분기 사이트 비노출 → 넘어감. (2) 소액 잔차(흥국 2025.1Q +714·KB라이프 +1,136·악사 +3,483) — 종목합산 기타비 내재 또는 미세, 지나감. (3) bare로 닫히는 분기(흥국 2024.4Q 등)는 정상.
- 참고: dual-form은 의도된 설계(사용자 확인) — bare 통과 분기 flag 안 함. 과잉진단 금지(§1.5). 단위: pl 백만원 / waterfall 억원 (cross-check ×100 정렬).

### V9 — 사용자 xlsx 수기검수 후속 (룰 3종 WFY/ZAMORT/ZLEG, parser 대기)
영속성 해결(`csm_manual_overrides.json` + `_apply_csm_overrides()` 훅, 빌드 생존). WFY 10/10 판별 완료(wfy 0). ZLEG 23→1(동양 2025.3Q 잔여). 메모리 `validation-blind-spots`·`master-xlsx-review-loop`.
- [ ] 교보(6.61)·한화생명(9.84)·교보플래닛(2.0)·처브(2.4) 저배수 별도 원인 조사(분자 scope?).
- [→] **신규 (parser)**: 메트라이프 영업이익 등식 2분기 FAIL(+12,086/+12,897) + 코리안리 crosscheck 2F(wf 상각 1년 lag 의심) + 동양 2025.3Q zleg 1건.
- [→] **현대해상 PL 8분기 재추출 (parser, 경고 inbox)**: 생명장기원수/기타원수/재보험손익/기타재보 — legit_absent 오판, 답지 anchor. 2025.2Q 패스.
- inbox: `20260611T0900Z__validation__MULTI_ALL__user_xlsx_audit_followup.md`.
- 참고: 보험손익 잔차 = LOB 별도/연결 기준 오선택부터 의심(§1.5). 신계약 CSM은 pl_breakdown_master에 구조상 없음 → V7 NB_CSM_DART_VS_IR + closing identity가 검증 담당.

### V1 — DART↔IR cross-source 2개 룰 활성화 (segment 폐기로 3→2)
룰 [§1.2 + §1.4]. RED → DART parser loopback. **현재 IR-side 정형 JSON 부재로 전사 SKIP.** (segment 룰 폐기 → V8 대체)
- [ ] **IR parser delivery 대기**: `data/ir/<period>/parsed/<KR>.json` (root TODO F18). 도착 cohort 9사: 메리츠·삼성화재·현대·KB·DB·한화생명·삼성생명·미래에셋·동양. 도착 즉시 룰 자동 ON. ⚠️ **2026-08-20 실측: 1년째 미도착.** `data/ir/**/parsed/` 전체에 파일이 **1개뿐**(KR0087 동양생명 FY2026_Q2, 2026-07-30). 9사 cohort는 오지 않았다 — 재개하려면 IR 파서 레인을 별도 발주해야 한다.
- [ ] **Threshold v1 튜닝**: 활성화 후 실제 diff 분포 보고 조정. v1: `CSM_WATERFALL_DART_VS_IR` max(5%·|IR|,100억)/step; `CSM_BREAKDOWN_DART_VS_IR` max(5%·|IR|,100억)/item (메리츠는 보종 비교 영구 SKIP — 측정요소별 표만, total만). ⚠️ **2026-08-20 실측: 1년째 미도착.** `data/ir/**/parsed/` 전체에 파일이 **1개뿐**(KR0087 동양생명 FY2026_Q2, 2026-07-30). 9사 cohort는 오지 않았다 — 재개하려면 IR 파서 레인을 별도 발주해야 한다.
- IR factsheet NB CSM multiple 가용성: 부재(현대해상·KB손해); 간접 산출 가능(DB손해 = 신계약 CSM + 월납보험료 derive).

### V2 — IFRS17-NB-RECONCILE 정합성 (한화 fallback retire 완료)
`validate_nb_csm_multiple.py` period-aware denominator + fallback flagging. 한화 fallback retire 완료(2026-06-12 재검증, `fallback_used=False`). 결과: tested 5 / pass 5 / fallback_pass 2(삼성화재·현대).
- [ ] 삼성화재 IR annual benchmark 보강 — 잔여 fallback 1건 해소. 2026-06-12 재확인: aligned FY2024 행 실패 → 2025.3Q fallback(rel 0.244=tol 0.25 턱밑, tolerance-loophole 경고). FY2024 연간 IR 분모 소싱 필요. (현대는 IR multiple 부재 → fallback 영구 유지.)

### V3 — K-ICS 시장위험 분산효과 validation (F12 cross-stage)
validation 룰 2개 구현 완료(2026-06-09b, `kics_json_rules.py`): `19_market`(item19=sqrt(V'·M·V), V=[36–40], MARKET_M 5×5) + `36_irr`(금리위험액 시나리오 분해). 정본 `docs/agents/kics-market-risk-decomposition.md`. 골든 3/3 일치. 화면 노출 X.
- [→] parser stage가 item36–46 적재(시장위험 세부표 5종 + 금리 시나리오 순자산가치 6종) — 진행 중. (V10 재추출과 동일 작업축.)
- [ ] 적재 단위(억원 vs 백만원) parser 회신 확인 → 백만원이면 대조식 ×100 조정. 적재 후 게이트 RED=0 확인.

### V4 — QoQ threshold registry
`config/qoq_thresholds.yaml` §2 + `QOQ_DELTA_WARN` 소비자 코드 구현 완료(2026-06-09, `validate_master_tables.py` 4번). CSM 항목 대상(누적→YoY / 시점→QoQ, floor 50억), PL 손익 제외. 193 YELLOW, 진짜 의심=이자부리 부호반전 3건(동양·교보·코리안리) → parser inbox. 전체 `data/_derived/qoq_warn.json`.
- [ ] (잔여 미구현) yaml loader precedence(item→domain→global) + prior-snapshot fetch + 누적 net-quarterly 변환 + finding emit(YELLOW, summary 기록, loopback 안 함). 진입점: K-ICS는 `validate_kics_disclosure.py` hook, IFRS17은 `validate_csm_waterfall.py` / 별도 스크립트 결정 필요.

## 🟡 Open / waiting

### V5 — 누적 항목 등록 목록 확장
§2.3 등록: IFRS17 `new_business_csm`, `csm_amortization`, `insurance_revenue`. 신규 누적 항목 발견 시 등록 + net 분기 기준 비교로 자동 전환.
- [ ] (운영 중 발견 시 갱신)

### V6 — KR0010 KB손해 OCR 잔여 RED 2건
K-ICS rule 2 OCR 미정확 (KR0010, KR0079도 image-only). 사용자 owned (`TODO.md` `KICS-IMG`). validation gate는 documented exception 처리 중.
- [x] **(종결 2026-08-20) 수기 OCR → RED 2→0** — 무효. 현재 게이트는 **RED=12이고 전건 `TODO.md` documented exception**이라 계약을 이미 충족한다(RED 2라는 전제 자체가 stale). OCR은 owner가 2026-08-15 *"됐어 패스"*로 **명시 보류** — 재요청 전 미착수(`TODO_downloader.md` OCR-MARKETRISK 행이 정본).

## ✅ Done (archive)
완결 항목(V10 census·V-RS 금리민감도 RS1–RS4·V8 PL_BRIDGE/CSM_CROSSCHECK/CSM_PLAUSIBILITY/MASTER_COVERAGE·V9 WFY/ZAMORT/ZLEG·V2 한화 fallback retire·V7 history check·V4 QoQ v1, 2026-05-31~06-12). 각 항목의 날짜별 상세는 `docs/changelog_validation.md`(당시 이미 `(changelog MM-DD)`로 인덱싱됨) + git log.

## 🛡️ Documented exception 관리
운영자(사용자)만 `TODO.md`에 `(도메인, 회사코드, 분기, rule_id, 사유)` 추가 가능. 서브에이전트가 자체 RED waiver 쓰지 말 것. `escalate_to_human` 단계에서만 "재파싱 5회 실패" 사유 기록.

현재 활성 exception:
- KR0010 KB손해 / KICS rule 2 / image-only PDF OCR 미정확 (V6)
- KR0079 미래에셋생명 / KICS rule 2 / image-only PDF OCR 미정확
- KR0097 하나생명 2024.4Q(item30·35)·2026.1Q(item35) / 적용후 세부위험 mmult / **적용후 세부 미공시**(raw는 phase-in 인식비율 10%만, 실값 부재→도출불가) — owner 확정 2026-07-12. 게이트 `_AFTER_SUBRISK_NOT_DISCLOSED`로 추출갭 제외.
- KR0104 농협생명 2023.1Q / 적용후 세부위험 / **다중 경과조치(①②③) 결합공식 불명**(개별표 어느것도 헤드라인과 불일치, 파서 재파싱해도 도출불가) — owner 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0100 처브 2024.3Q / 적용후 세부위험 / **②표 값이 행별로 다른 컬럼 착지**(일반화 규칙 없음) — owner 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0005 흥국화재 2024.4Q / 적용후 세부위험 mmult / **image-only PDF**(텍스트레이어0, 재수집=같은이미지) — owner GOLD-SCAN 대기, 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0097 하나생명 2024.2Q / KICS rule 2·4·5·6 / **스캔이미지 PDF**(items 1-26 미추출, item27/28만 OCR) — OCR 재처리 후속. documented.
- KR0002 한화손해 2024.2Q / KICS rule 9 / **4억(0.015%) 반올림 비물질**(tolerance-too-tight, 카카오 8_post 동류) — documented, 무해.
- (fixed, 예외아님) 카카오 2023.4Q 8_post: item14후=20억 coarse 반올림 → **8_post에 rule8 dynamic tol 배선(2026-07-12)**으로 통과. prepush RED 1→0.

## 📞 Loopback contract
§3. **max 5회**. RED packaging에 `suspected_source: "DART" | "IR" | "internal"` 명시. cross-source 룰은 항상 `"DART"`.

| 조건 | next_action | exit |
|---|---|---|
| RED=0 | `pass` | 0 |
| YELLOW만 (RED=0) | `pass` | 0 |
| loop_iteration==5 & RED>0 | `escalate_to_human` | 2 |

## 🔗 참조 룰셋 / 코드
- 권위 doc: [`docs/agents/kics-json-validation-rules.md`](docs/agents/kics-json-validation-rules.md) (R1–R10 formulas, tolerance, R4/R7 matrices, item-label mapping)
- K-ICS 구현: [`src/solvency/validation/kics_json_rules.py`](src/solvency/validation/kics_json_rules.py)
- 러너: K-ICS `python scripts/validate_kics_disclosure.py` · IFRS17 CSM `scripts/validate_csm_waterfall.py` · NB CSM multiple `scripts/validate_nb_csm_multiple.py` · reconcile loop `scripts/run_ifrs17_csm_reconcile_loop.py`
- Output: `artifacts/validation/<domain>_<timestamp>.json`
