---
from: orchestrator
to: parser
created: 20261023T0900Z
status: open
route: reparse
lane: ifrs17
company: MULTI (KR0099 KR0003 KR0070 KR0072 KR0009)
period: 2023.1Q-2023.4Q
iter: 1
---

## 미결 (sender 작성)

owner 가 2026-10-23 에 NEEDS_OWNER 결정 4건을 모두 내렸다(채팅 선택, 권장안 그대로): ① **KB라이프 KR0099 = 옵션 B**: FY2023 2023.1Q~3Q 만 최신(V1 기초 31,327.6)으로 적재, 2023.4Q·2024 는 지금 그대로(시나리오 `N2_KBlife_B`, PL 61 + CSM 15칸). ② **롯데손보 KR0003 2023.4Q = 채택 + WFY 면제 등재**(시나리오 `N7_Lotte_FY2023Q4`, PL 19 + CSM 5칸; 면제 등재는 validation 몫이니 너는 등재하지 않는다). ③ **ABL KR0070 · KDB생명 KR0072 · 현대해상 KR0009 FY2023 = 셋 다 진행**: 연쇄용 owner CSM gold 교체를 승인했고(분류 ⓑ 포함: 원 인쇄값도 최신값도 아닌 Q1~Q3 원 기초를 Q4 에 강제한 칸), 현대해상은 LOB 레그 원천으로 IR 팩트시트 `(3) UW Income` 전년동기 누계 허용(시나리오 `N4_ABL_FY2023` PL 75 + CSM 20 · `N5_KDB_FY2023` 70 + 20 · `N6c_HD_FY2023_IRlegs` 58 + 18).

근거·칸 목록·줄 번호·게이트 모의는 `data/_derived/remaining_20261022/e20_held_and_remaining/measure/PLAN.md`(4절 결정표, 1절 계획표 순위 11~15, `plan_table.csv`, `gold_cells_replaced.csv`, `csm_vector_sources.csv`, `ready_cells_ALL.csv` 의 NEEDS_OWNER 후보)에 있다. 모의에서 기대한 결과: 연속성·워터폴 RED 0, `NB_VS_WATERFALL` RED(ABL 2023.1Q~3Q · 현대해상 2023.1Q·2Q: publishing 이 NB 재빌드), master_tables WFY 롯데 1건(validation 이 면제 등재 후 WFYEX), pl_bridge 현대해상 N6c 3707P/FAIL 23/NEW 0.

### 원칙 (앞 두 티켓과 같다)
- 최신 비교열 우선 · 별도(OFS) 기준 · 박제·잔차 끼워 맞추기·게이트 예외 등재 없음(예외 등재는 validation). owner gold 교체는 이번에 승인된 칸에 한해: `gold_cells_replaced.csv` 의 해당 시나리오 칸 · 롯데 2023.1Q 는 이미 앞 단계 처리. 교체 시 `was`·`note`(필링 줄 번호와 「owner 2026-10-23 승인, 연쇄용 gold」)를 남기고 목록(옛→새)을 답변에 표로 적는다.
- 적재 직전에 후보 칸의 `old` 값이 라이브 마스터(HEAD `d8899bd9`)와 같은지 다시 확인하고, **전 칸을 필링 XML 줄 번호로 독립 재독**(값·단위·부호·행 라벨·열; IR 팩트시트 레그는 시트 셀 좌표까지). 계획서의 인용을 믿고 넘어가지 말고 별도 코드로 읽는다. 새 마스크 칸·새 박제는 만들지 않는다(반올림만 다른 칸은 제외하고 사유 기록).
- 적재 도구는 직전 라운드 것을 재사용한다: `data/_derived/remaining_20261022/e21_ready25/INDEX.txt`(적재 · 재독 · diff · 게이트 스크립트 지도) 와 `e20_held_and_remaining/apply/`. 영속 경로는 `data/_gold/user_pl_cells.json`·`user_csm_cells.json` 셀 단위 set(이음매는 `set_dangi`/`null_dangi`), 달라진 칸만 마스터에 셀 단위 반영, 출처표는 `scripts/emit_pl_provenance.py` 샌드박스 사본, `GOLD_OVERLAY_CENSUS` 갱신. 현대해상 IR 레그는 시트 값을 gold 로 영속화하고 출처 계보(IR 팩트시트)를 provenance 에 표시해야 `data_contract` 가 통과한다 — 2023.4Q 레그가 이미 IR 유래 owner gold 라 선례가 있으니 같은 방식으로.
- 한 회사씩 게이트를 돌려 새 RED/FAIL 이 생기면 그 회사는 적재하지 말고 원인을 적는다(예상된 것: xlsx 동기화 RED, `NB_VS_WATERFALL`, 롯데 WFY 1). KB손보 2024.4Q 항목 16(마스터 60,900 대 FY2025 전기 380,949)과 농협생명 2.9백만원 건은 이번 범위가 아니다.
- **커밋·push 금지.** python 풀패스 + 스크립트 파일 + stdin `/dev/null`. 무거운 게이트는 한 번에 하나(RAM 여유 약 3GB). 증거는 `data/_derived/remaining_20261022/e23_d1_d3/` 에 새로 만든다. 끝나면 `TODO_parser_ifrs17.md` 맨 위(항목당 5줄)와 changelog 를 갱신하고 이 티켓 `## 답변` 을 채운다.

## 답변 (recipient 작성 — 처리 후)

(처리 전)
