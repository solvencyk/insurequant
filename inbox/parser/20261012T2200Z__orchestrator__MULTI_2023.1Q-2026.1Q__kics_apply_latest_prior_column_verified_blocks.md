---
from: orchestrator
to: parser
lane: kics
created: 20261012T2200Z
status: open
route: fix
company: MULTI
period: 2023.1Q-2026.1Q
iter: 1
---

## 미결 (sender 작성)
### owner 결정 기록 (2026-10-12 채팅)
드라이런(`20261012T1900Z`, 커밋 `ae7a54b7`, `data/_derived/kics_latest_prior_precedence_dryrun_20261012/summary.md`)을 보고 owner: 「생각보다 바꿀 값이 많지는 않네? 최신 공시 직전 값이 검산이 다 닫히는 게 확실한 애들만 덮어써라」.
→ **적용 범위 = 드라이런이 「채택 후보」(`block_verdicts.csv` 의 `ticket_category` = 채택 후보, 26블록 87칸) 로 판정한 블록 중, 아래 「확실」 기준을 통과한 것만.** 나머지(완전성 부족 45 · 룰 사각 8 · gold 충돌 1 · 현행 유지 7 · 현행 유지+목록 1 · 둘 다 실패 5) 는 **건드리지 않는다**(보류 목록으로 남김).

### 「확실」 기준 (모두 만족해야 덮어쓴다)
1. 최신 열을 넣은 후보 마스터에서 그 블록의 RED 가 없고, 이웃 분기·다른 게이트 축(data-contract CHECK 1·3·4·7 포함)에 **새 RED 가 없다**(드라이런이 이미 평가; 적용 직전 실제 마스터로 한 번 더 확인).
2. 완전성 문제가 없다(적용후 열 독립 값 없음 · 핵심표 판독 실패 · 짝수분기 세부표 미확인 없음).
3. 주의 표시(`flags`: `GAPFILL_ROW_IN_DIFF`·`NO_OWN_CONTROL`·`LATER_PRINTINGS_DIFFER`·`EXTRACTION_SUSPECT`)가 붙은 블록은 **바뀌는 셀마다 원본 PDF 를 직접 열어 쪽 번호·인쇄값을 기록**하고 일치할 때만 적용한다(스캔/이미지 쪽이면 240dpi 렌더링으로 읽기 — 키워드 0회로 부재 단정 금지). 직접 확인이 안 되면 보류.
4. 후속 공시 둘의 인쇄가 서로 다르면 더 늦은 공시를 택하되, 그 칸이 그 둘 사이에서 어긋나면(최신 열도 흔들림) 보류하고 목록에 올린다.

### 해 줄 것
1. 위 기준으로 적용 블록 목록을 확정해 `data/_derived/` 새 폴더(예: `kics_latest_prior_apply_20261012/`)에 `applied_blocks.csv`(회사·분기·셀·옛값·새값·출처 쪽·직접 확인 쪽) 와 `held_blocks.csv`(보류 사유) 로 저장. 드라이런의 `plans/<회사>_<분기>.json` 덮어쓰기 계획을 그대로 쓰되 적용 직전에 마스터 현재 값이 계획의 옛값과 같은지 **셀 단위 guard** 로 확인(다르면 그 셀 중단·보고).
2. **셀 단위로만 쓴다**(마스터 JSON 통째 read-modify-write 금지, `build_root_masters.py main()` 금지, 쓰기는 임시 파일 후 교체로 원자적으로 — 지금 다른 에이전트가 이 파일을 읽고 있다). 전(값) 칸 + 적용후 미러(전=후인 회사만; 적용사 18사 적용후 열은 독립 값 없으면 건드리지 않음) + 파생 27·28(기존 산출 공식 그대로) 을 계획대로 갱신.
3. **예외 해소 2건**(롯데손해 2025.1Q 항목 13: 19,202 → 17,997 · NH농협손해 2024.3Q 항목 13: 8,867 → 9,390): 값이 룰을 닫으므로 박제 예외(`_TIER2_ISSUER_INCONSISTENT` 해당 2건)를 **해제**한다 — 이 티켓이 owner 해제 승인 기록이다. 예외 해제 때문에 나는 RED·핀 이탈 신호는 위 계획과 맞는지 확인하고 `docs/kics_gate_exceptions.md` 를 코드와 맞춘다. 다른 예외는 건드리지 않는다.
4. **영속화**: 루트 JSON 만 고치면 빌드에서 사라진다. 앞선 같은 종류 적용(악사 2024.3Q `acd351a`, 교보 2026.1Q owner 2026-09-01, 재보사 owner 2026-10-09 규칙 적용분)이 쓴 방식과 같은 방식으로 영속화하고(등재 위치를 그 선례에서 찾아 따른다), **소급재작성/as-filed 정책**과 충돌하지 않게 이 블록들이 「최신 공시 직전 열 채택(owner 2026-10-12)」으로 확정된 것임을 그 장부에 기록한다. 재빌드 시 덮어써지지 않는지 선례처럼 확인(전체 빌드 실행 금지, combo-diff 방식).
5. 게이트: `validate_kics_disclosure.py`(RED 56 → 예외 2건 해제로 줄거나 같아야 하고 **늘면 안 됨**; 늘면 원인 보고), `validate_data_contract.py`, `validate_master_tables.py --no-build`, `scripts/check_master_xlsx_drift.py` — 한 번에 하나씩 끝까지. master xlsx K-ICS 시트는 `scripts/sync_master_xlsx_sheet.py` 로 바뀐 칸만 반영. 골든(`test_kics_rules_golden`·`test_post_transition_golden`) 은 **고치지 말고** 결과만 보고(필요하면 validation 이 `--update`).
6. `TODO_parser_kics.md` Status + `docs/changelog_parser_kics.md`(적용·보류 건수, 되돌리는 방법 = 계획 JSON 의 옛값).

### 규칙
- 이 티켓의 결정은 위 범위가 전부다. 보류 목록의 블록, 정책 전환(소급재작성 as-filed 기본값 변경), 새 예외 등재는 하지 않는다. 마스터 외 `public_exports/`·HTML 수정 금지(재공개는 publishing 이 별도). 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`·스크립트 파일만(멀티라인 `-c`·stdin heredoc 금지), 고아 프로세스 즉시 종료, docling 불필요. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 적용 블록·칸 수, 보류 블록 수와 사유, 직접 PDF 확인한 칸, 예외 해제 2건 결과, 게이트 전후(RED 수), 영속화 방식, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
