---
from: orchestrator
to: parser
lane: ifrs17
created: 20261012T1020Z
status: open
route: fix
company: MULTI
period: 2023.4Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
### owner 승인 기록
owner 는 2026-10-12 채팅에서 `TODO.md` 「owner 결정 대기」 ①~㉕ 의 오케스트레이터 제안안을 「나머지는 다 승인」으로 승인했다. 아래는 승인된 제안 중 **ifrs17 레인 몫**이다(항목 번호는 TODO.md 기준). 승인 범위 밖의 값은 만들지 않는다. 원문 확인이 안 되면 칸을 비워 두고 보고.

### 해 줄 것 (셀 단위, old-value guard + 백업, HEAD 키 대조 증빙)
1. **⑯ 재보사 「인쇄된 0」 7칸 복원**: validation 이 같은 날 `data/_gold/user_pl_confirmed_cells.json` 에 7칸 등재를 마친 뒤에 `scripts/reinsurer_resweep_pl_followup.py --restore7 --apply`(상태 `data/_derived/reinsurer_resweep_20261012/collapse7_state.json`). **등재 전이면 이 항목만 뒤로 미루고** 나머지를 먼저 한다(등재 여부는 그 JSON 에 7칸이 있는지로 확인). 복원 뒤 `PL_YTD_COLLAPSE_TO_ZERO` 가 안 나는지 게이트 출력으로 확인.
2. **⑳ 퍼시픽(KR1107) 2023.4Q CSM 항목 4**: 영업양수 1,069억 포함 인쇄값을 그대로 유지하고, 비고(provenance sidecar 의 `note`/`how` 규약)에 「영업양수 1,069억 포함, 인쇄값」을 남긴다.
3. **㉑ 뮌헨 2023.4Q ILP 부호 반전**·**㉒ 하노버 2023.4Q ILP 충돌·제네럴 민감도**: 변경 없음(현 적재 유지 / 공란 유지). 건드리지 않는다.
4. **⑦ 처브(KR0100) 항목 20 정의·ILP RED 5**, **⑧ KR0029(AIG) 2024.4Q 「10배 규칙」**, **⑨ KR1102(스위스리) 2026.1Q ILP 합계**: 각각 원문을 직접 읽어 정의·값이 맞는지 확인하고, 틀리면 고친다. **확정된 것만** 고치고, 면제 등재가 필요하면 하지 말고 「등재 필요 목록(회사·분기·룰·사유)」으로 보고(등재는 validation).
5. **⑩ 예별(KR0004) 2025.4Q CSM 0.0 대 ILP 6,227**: 원문(경영공시 PDF·DART)으로 재확인. 교보·KB라이프·하나생명·롯데의 재작성 기준 차이는 validation 이 등재하니 건드리지 않는다.
6. **⑮ 분할표 5사(라이나·AIA·처브·메트라이프·BNP카디프) 상각 스케줄 부분합 + 한화생명 연결 표 선택**: 한 표가 쪽/표로 갈라져 인쇄돼 부분합만 적재된 경우 뒷부분을 합쳐 전체로 맞추고(별도 표가 있으면 별도 표 우선), 한화생명은 연결 표 대신 별도 표를 택한다. 대상 칸 전수 목록·전후 값·합계 항등식 확인표를 증빙으로 저장. `csm_amort_schedule` 패널의 라이나 행을 마스터값으로 바꿀지는 이번 범위가 아니다(보고만).

### 규칙
- 마스터 통째 read-modify-write 금지(`build_root_masters.py main()` 통짜 실행 금지, `validate_master_tables.py` 는 `--no-build`). docling 은 필요한 쪽만 동시 ≤2. 예외 등재 금지. xlsx·`public_exports`·패널·HTML 은 publishing/designer 몫(건드리지 않는다). 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·stdin heredoc 금지), `encoding` 명시, UTF-8(BOM 없음). 시험·게이트는 한 번에 하나씩 끝까지. 커밋은 자기 파일만 명시 경로(루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 항목별 결과(고친 칸 수·보류 사유), 등재 필요 목록, HEAD 키 대조 증빙 경로, 게이트 전후 비교, 커밋 해시. `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.

## 답변 (recipient 작성 — 처리 후)
