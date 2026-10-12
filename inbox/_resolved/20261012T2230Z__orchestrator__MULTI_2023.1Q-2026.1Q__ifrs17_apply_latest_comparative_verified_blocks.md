---
from: orchestrator
to: parser
lane: ifrs17
created: 20261012T2230Z
status: resolved
route: fix
company: MULTI
period: 2023.1Q-2026.1Q
iter: 1
---

## 미결 (sender 작성)
### owner 결정 기록 (2026-10-12 채팅)
드라이런(`20261012T1930Z`, 커밋 `580ae0e`, `data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/`)을 보고 owner: 「확실히 검산 닫히는 것만 최신 공시로 덮어쓰기 하고, 라이브 push 까지 쭉 밀어붙여라」(K-ICS 와 같은 기준). 적용 경로(마스터만 고치면 빌더가 되돌리는 문제)는 owner 가 방식을 정하지 않았으므로 **기존 선례와 같은 영속화 방식**을 택한다(아래 4).

### 「확실」 기준 (모두 만족해야 덮어쓴다)
1. 드라이런 판정이 「최신 채택」(진짜 재작성 32 + 예외 해소 7 = 39블록, 마스터 셀 약 240)이고, 최신 비교열을 넣은 임시 사본에서 해당 블록의 모든 게이트(PL 브리지·CSM 상각·연속성·ILP·NB·워터폴·`validate_data_contract`)가 닫히며 **이웃 분기·다른 게이트 축에 새 RED 가 없다**(적용 직전 실제 마스터로 한 번 더 확인).
2. gold 충돌(owner 확정 셀과 겹침, 59블록)·현행 유지 24·둘 다 불가 1·조건부 2·후보 미검증 107·비교 컬럼 추출 불가 84·이전 라운드 재판정 안 함 7 은 **건드리지 않는다**(보류 목록으로 남김). 라이나 CSM 2023.1Q·2Q 보류 유지.
3. 주의 표시가 있는 블록·셀은 바뀌는 칸마다 원본 공시 표(쪽 번호·인쇄값)를 직접 열어 기록하고 일치할 때만 적용(스캔/이미지 쪽은 240dpi 렌더링). 직접 확인 불가면 보류.
4. 적용은 같은 종류의 앞선 적용(예: 재보사 owner 2026-10-09 규칙 적용분·gold 장부 영속화)이 쓴 방식으로 한다 — 마스터 셀 단위 guard(현재 값 == 계획 옛값) + 빌더가 되돌리지 못하게 하는 영속화(선례를 `git log`·changelog 에서 찾아 따름; 새 룰·새 메커니즘 신설 금지). 전체 빌드 실행 금지, 재빌드 안전은 combo-diff 방식으로 확인.

### 해 줄 것
1. 적용·보류 목록을 `data/_derived/` 새 폴더(예: `ifrs17_latest_comparative_apply_20261012/`)에 `applied_cells.csv`(마스터·회사·분기·항목·옛값·새값·출처 쪽·직접 확인 쪽)·`held_blocks.csv`(사유) 로 저장하고 위 기준대로 적용.
2. 예외 해소 7건(박제 예외가 최신 열로 풀리는 블록): 해당 예외 등재를 **해제**한다 — 이 티켓이 owner 해제 승인 기록이다. 다른 예외는 건드리지 않는다. 문서(`docs/` 예외 설명)가 코드와 어긋나면 맞춘다.
3. **신규 발견 중 이미 원 공시 표로 확인된 건**: 2023.2Q Tier-1 에서 3개월 열이 누적으로 적재된 오류(흥국화재 5셀·한화생명 4셀) 는 원 공시 대조가 끝났으므로 같은 방식으로 고친다(고친 셀·근거 쪽 기록). 나머지 신규 발견은 보류 목록에 올리고 고치지 않는다.
4. 쓰기는 전부 셀 단위·임시 파일 후 교체로 원자적으로(다른 에이전트가 마스터를 읽고 있다). `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 `--no-build`. 드라이런이 짚은 `validate_data_contract` RED 3건(xlsx 시트 동기화 필요: `17BS`·`CSM워터폴`·`손익분해PL`)은 `scripts/sync_master_xlsx_sheet.py` 로 **바뀐 칸만** 반영해 해소(전체 재생성 금지). 게이트(`validate_data_contract`·`validate_master_tables.py --no-build`·연속성·ILP·NB·워터폴·`check_master_xlsx_drift.py`)는 한 번에 하나씩 끝까지, 새 RED 는 덮지 말고 종류별 보고. 골든 테스트는 고치지 말고 **결과만 보고**(validation 이 `--update`).
5. `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`(적용·보류 건수, 되돌리는 방법 = 계획의 옛값).

### 규칙
- 위 범위가 전부다. 정책 전환·새 예외 등재·보류 블록 수정 금지. `public_exports/`·HTML 수정 금지(재공개는 publishing). 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`·스크립트 파일만(멀티라인 `-c`·stdin heredoc 금지), 고아 프로세스 즉시 종료. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·K-ICS 레인 에이전트의 미커밋 파일 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 적용 블록·칸 수(마스터별), 보류와 사유, 직접 확인한 칸, 예외 해제 7건 결과, 신규 발견 9셀 정정, 게이트 전후(RED·핀), 영속화 방식, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
처리 완료: 249셀(CSM 27 · PL 157 · BS 65) 적용 + 3개월/누적 정정 14셀 + 한화손보 2셀 + 예외 해제 10줄 (parser-ifrs17 b8c37fff), validation 독립 재독 249/249 일치·PDF 계보 116/116 일치·골든 갱신 (validation 5414c81e), 파생 산출물 재생성 (publishing 99c7ead7, 638ebabb). 라이브 배포 main 970259b8 (2026-10-13). 적용 칸 옆 별건 결함 4건은 inbox/parser/20261012T1820Z... 로 이관. orchestrator 종결 2026-10-13.
