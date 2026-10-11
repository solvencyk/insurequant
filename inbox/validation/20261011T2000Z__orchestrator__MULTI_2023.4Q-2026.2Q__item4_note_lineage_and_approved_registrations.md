---
from: orchestrator
to: validation
created: 20261011T2000Z
status: open
route: gate-change
company: MULTI
period: 2023.4Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 가 2026-10-11 채팅에서 두 가지를 확정했다. 둘 다 이 티켓에서 처리한다. **골든 `--update` 는 하지 않는다**(Lina CSM 백필·상각 스케줄 수정이 아직 적재 중이라 마지막 라운드에서 한 번에 한다).

### A. PL 항목 4(`원수CSM상각`) 재무제표 주석 계보 허용 (게이트 코드 변경)
owner 지시: 재보사 17건 `PL_CSM_AMORT_VS_WATERFALL` 은 예외 등재가 아니라 **PL 항목 4 를 채워서** 닫는다. parser-ifrs17 이 `0a7632e` 로 20칸(재보사 17버킷 + 라이나 KR0074 3버킷)을 적재했고 그 결과 `PL_CSM_AMORT_VS_WATERFALL` 20→0, `csm_amort_identity` 20버킷 잔차 0.00억이 되었다. 그러나 두 게이트가 새로 아프다:
1. `validate_data_contract.py` §3d `CONCEPT_MIXED_DISCLOSURE_INTO_DART` RED 20건. 이 20칸의 원천은 경영공시 PDF 에 **붙은 감사보고서 주석**(경로상 `data/disclosure/`)인데 §3d 는 DISCLOSURE 계보 PL 셀을 항목 1·16·22·23·24 로만 제한한다. 사이드카에는 `source_id=DISCLOSURE`, `how`·`resolution=fs_note_csm_amort` 가 달려 있다.
2. `validate_master_tables.py` ZERO_LEGS 가 9→23(`src_na zleg` 195→181). 다리 10종이 전부 None 이면 「원천 미수록」 면제인데 항목 4 가 생겨 면제가 풀렸다.

해 줄 것 (parser-ifrs17 제안 반영, 둘 다 **좁게**):
- (a) `validate_data_contract.py` L1964 `_disc &= _pub` 직전에, 사이드카 `resolution=="fs_note_csm_amort"`(또는 how)인 셀의 **항목 4 만** §3d 제한에서 빼는 예외를 둔다. 항목·계보·키가 다른 셀은 계속 걸려야 한다.
- (b) `validate_master_tables.py` L1225–1226 「다리 전부 None」 판정에서 `원수CSM상각`(항목 4) 은 다리로 세지 않는다. 항목 4 외에 값이 있는 버킷은 그대로 ZERO_LEGS 로 잡힌다.
- 수정 전 **양방향 시뮬레이션**(닫히는 것·새로 깨지는 것)을 먼저 보인다: 기대 결과 = §3d 20건 소멸, ZERO_LEGS 9·src_na zleg 195 로 복귀, 그 밖의 RED/YELLOW 이동 0. 변이시험으로 「항목 4 이외 셀·다른 resolution 은 여전히 걸린다」를 증명한다. `tests/test_rule_coverage_manifest.py`·관련 테스트를 같이 고친다(룰 추가·개명 시 매니페스트 동기화).
- 이 변경은 새 예외 등재가 아니라 계보 규칙의 정당한 확장이다. 그래도 사유를 `TODO_validation.md`·changelog 에 남긴다.

### B. owner 승인 등재 2건 (등재 허용 — 채팅 승인)
owner 승인 문구: 「하노버 25.3q만 예외 승인」 · 「법인세는 네 제안대로 승인」(법인세 0 은 원문에 0 으로 인쇄된 것으로 처리).
1. **`PL_YTD_COLLAPSE_TO_ZERO` 3건**: 스위스리아시아 2023.2Q 법인세(-900→0.0, 원문이 0 인쇄), 퍼시픽 2024.4Q(500→0)·2025.4Q(200→0)(감사보고서 당기법인세 `-`, 3Q 경영공시는 발생 표시). 기존 owner 확정 경로 `data/_gold/user_pl_confirmed_cells.json`(룰 `PL_YTD_COLLAPSE_TO_ZERO`, 값+원문 마커를 매 실행 재검증, 예별 2025.3Q 와 같은 방식)에 등재한다. 값·마커는 원문을 열어 다시 확인한 뒤 적는다.
2. **하노버 2025.3Q PL `MASTER_HOLE` 1버킷(5 PL 셀)**: 사이트가 그 분기를 게시하지 않았다(K-ICS 쪽은 이미 `NOT_POSTED` 면제). PL 쪽에 같은 종류의 「원천 부재」 기록을 만들어 RED 를 닫는다(K-ICS 장치는 PL 을 덮지 않는다). 새 장치를 만들 때 게이트에 **읽는 쪽(lookup 분기)** 이 실제로 있는지 같이 확인한다(등재부만 쓰면 샌다).
- 위 2건 외 신규 등재 금지.

### 규칙
- 마스터 JSON 셀 수정 금지, `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 반드시 `--no-build`. 골든 `--update` 금지(아래 보고에 「이 변경으로 움직이는 골든 목록」만 적는다). xlsx·`public_exports`·HTML 금지. 서브에이전트 금지, docling 금지.
- 지금 다른 에이전트가 `CSM_waterfall.json`·`CSM_amortization.json` 과 라이나 적재를 진행 중이다. 이 티켓의 게이트 실행은 **PL·PL 사이드카·등재부 기준**의 전후 비교로 한정하고, CSM 계열 RED 의 변동은 해석하지 않는다.
- 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·타 에이전트 미커밋 파일 제외), 메시지 끝 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. push·풀 훅은 오케스트레이터 몫.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·맨 `python` 금지), `encoding` 명시, UTF-8(BOM 없음).

### 보고
- A: 변경 전후 RED/YELLOW 표(§3d·ZERO_LEGS), 시뮬레이션·변이시험 결과, 움직이는 골든 목록. B: 등재 3+1건과 lookup 분기 위치, 등재 후 해당 RED 소멸 확인. `TODO_validation.md` Status + `docs/changelog_validation.md`. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

## 답변 (recipient 작성 — 처리 후)
