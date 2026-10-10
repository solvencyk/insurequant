---
from: orchestrator
to: parser
created: 20261011T0900Z
status: open
route: rework
company: MULTI
period: 2023.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
티켓 `20261011T0310Z`(BS/PL 세부 경영공시 백필, 종결·커밋 bd64513)의 후속이다. owner 지시(2026-10-11, 밤새 처리): 「경영공시로 지금 수준 granularity 는 충분히 다 채울 수 있다 — 전부 다시 채워와라.」 1차에서 **마스터 이상 3건**과 **보류(HOLD) 칸 약 500개**가 남았다. 런로그 `data/disclosure/_meta/bspl_granularity_runlog.md` 「충돌」「보류」 절과 `data/_derived/bspl_granularity_20261011/`(후보·manifest)가 출발점. 같은 런로그에 이어서 쓴다.

### 작업 (우선순위 순, 단계마다 디스크 저장·런로그 맨 위 「중간 결과」 갱신)
1. **카카오페이손보 KR1098 항목 30(자본금) 2026.2Q**: 마스터 200,000백만원(2,000억), 경영공시 자기자본 표는 2025.4Q~2026.2Q 내내 3,000억이고 2026.2Q 자본총계 1,089.6억 = 3,000 − 1,876.6 − 29 − 5 로 닫힌다(마스터 2,000이면 안 닫힘). 원문 PDF 쪽을 렌더링으로 확인하고, 마스터 값이 이상치로 확정되면 **셀 단위 + 옛 값 guard + 백업**으로 정정(정정 근거를 오버레이 `bs_manual_overrides.json` 근거 칸에). 같은 회사 다른 분기·같은 종류(자기자본 표 전분기 열 vs 마스터) 불일치도 훑는다.
2. **코리안리 KR1000 2023.1Q = 2023.2Q 복사 의심**: 항목 1(자산) 11,017,223 · 2(부채) 8,301,593 · 3(자본) 2,715,630 · 20(보험계약부채) 7,661,996 백만원이 두 분기에서 **소수점까지 똑같고** 정수다(다른 분기는 소수 6자리). 원천(DART `data/dart` 2023 1Q·2Q 보고서 또는 경영공시 별도 K 재무제표 — 경영공시 2023.1Q 별도 자산 110,058.0 · 부채 79,114.05 · 보험계약부채 72,829.35억으로 마스터와 다름)을 찾아 각 분기의 정확한 값을 확정하고 **셀 단위 + guard + 백업**으로 정정. 어느 경로(오버레이/빌더)로 들어온 값인지 provenance 도 밝혀 같은 오류가 되살아나지 않게 한다. 정정 후 BS 항등식·BS golden 영향(어느 셀이 바뀌는지)을 보고.
3. **복사 의심 전수 탐지**: `IFRS17_BS.json`·`PL_breakdown.json` 전체에서 (회사, 항목) 별로 **연속 두 분기의 값이 소수점까지 완전히 같은 칸**(0·결측 제외, 단 법정준비금 R_RSV_1 이 이미 잡는 항목 5~8 은 제외)을 열거한다. 대부분 정당(예: 변동 없는 자본금)일 수 있으니 항목 성격별로 분류하고, 의심 칸은 원천 대조 후 정정하거나 정당 근거를 적는다. 목록은 `data/_derived/bspl_granularity_20261011/consecutive_duplicates_20261011.json` 로.
4. **처브라이프 KR0100 항목 20(보험계약부채)** 2024.2Q~2025.3Q 정의 혼재(일반계정 vs 특별계정 포함): **마스터는 건드리지 말고** 전 분기 두 정의의 값을 나란히 놓은 표와 「일관된 계열로 만들려면 어느 정의가 맞는지」 근거(연말 감사 앵커·DART 라인 정의)를 보고서에 낸다(owner 결정용).
5. **1차 보류 칸 재검토**: `HOLD_UNTESTED` 182(재보사 156·비상장 26; 그중 125칸은 값이 0 인 라인 — K 재무제표 자산 합 폐합으로 0 을 증명하는 규칙이 없어 보류)와 `HOLD_REJECTED_RULE` 312(라인은 있으나 마스터 DART 정의를 재현 못 함). (a) 0 증명 규칙(해당 재무제표의 자산 합이 라인 0 을 넣어도 닫히고, 같은 항목이 다른 분기에서 0 이 아니라는 이유만으로 거르지 않음)을 구현해 닫히는 0 칸은 적재, (b) 비영 57칸은 표 항등식 + 연말 앵커 근거를 다시 찾아 적재 가능한 것은 적재, (c) `HOLD_REJECTED_RULE` 는 「마스터 정의를 재현하는 연도별 규칙」이 정말 없는지 회사·항목별로 확인하고, 규칙이 있으면 적재, 없으면 사유(정의 단절 연도, 재현 실패 값)를 목록으로. **혼합 정의 적재 금지는 유지**(owner 규칙).
6. PL 항목 1 보류 17칸(`KR0003|1|2023.1Q`·`KR0008|1|2023.2Q` 등 pl_bridge 새 실패로 철회된 칸 포함)도 원인을 정리: DART 레그 부분이라 bridge 가 안 닫히는 구조이면 어떤 보강(어느 DART 레그가 비었는지)이 필요한지 적는다.

### 규칙
- 마스터 쓰기는 **셀 단위 + guard + 백업**, 통짜 read-modify-write 금지, `build_root_masters.py main()`·`build_ifrs17_bs.py` 통째 실행 금지, `validate_master_tables.py` 는 `--no-build`. 1차와 같은 방식(원자적 교체, 마스터는 마지막에 씀). 2번·1번 정정 외 **기존 칸 변경 0** 을 적재 전후 diff 로 증명.
- 이 티켓은 `IFRS17_BS.json`·`PL_breakdown*.json`·`data/dart/viz/bs_manual_overrides.json`·`data/_derived/bs_from_disclosure*`·`data/_derived/bspl_*` 만 쓴다. K-ICS 파일·ILP·CSM_*·게이트·예외 등재부·골든(`--update` 금지)·HTML·xlsx·`public_exports` 금지. 커밋·push 금지. 서브에이전트 금지, docling 은 꼭 필요할 때만 1개. 동시 에이전트 3개(RAM 15.5GB).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python -`(stdin heredoc) 절대 금지**, `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 단계별 결과(정정 셀 전후, 새로 적재한 칸 수, 남은 보류와 사유), 복사 의심 목록, KR0100 정의표, 게이트 전후(`validate_data_contract`·`validate_master_tables --no-build`), 기존 칸 변경 0 증명, `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
