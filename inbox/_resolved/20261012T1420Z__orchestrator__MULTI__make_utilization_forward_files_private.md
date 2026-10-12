---
from: orchestrator
to: publishing
created: 20261012T1420Z
status: resolved
route: fix
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): 「내린 시트들은 비공개로 돌리고」. 앞서 다운로드 목록에서만 내린 3시트(기본자본소진율·보완자본소진율·자본비율전망)를 **공개 사이트에서 접근 불가**로 만든다(분류 판단이 들어가는 숫자라서; 재공개·유료화는 owner 가 나중에 정한다 — 되돌릴 수 있게 둘 것). 작업 브랜치 push·폰 배포 **전에** 끝내야 한 번의 배포로 반영된다 — 빨리.

### 해 줄 것
1. **비공개 대상**: ⓐ `public_exports/기본자본소진율.json`·`보완자본소진율.json`·`자본비율전망.json` 3개 ⓑ 공개 `public_exports/manifest.json` 의 이 3시트 항목 ⓒ 루트 `kics_tier2_utilization.json`·`kics_forward_capital.json`(HTML 이 더 이상 fetch 하지 않음) ⓓ **designer 티켓 `20261012T1425Z` 가 K-ICS 큼직한 셀을 타임라인 JSON 계산으로 바꾼 뒤** `kics_tier1_utilization.json` 도(그 커밋이 `git log -- K-ICS.html` 에 올라오면). 저장소의 마스터 JSON·xlsx 시트·`output/`·내부 산출은 **지우지 않는다**(내부 보관). 즉 「저장소에는 남기고 라이브(`main`)에서는 안 보이게」.
2. **메커니즘**(`scripts/android_push_and_deploy.sh` 는 main 에서 파일을 지우지 못한다 — jp 비공개 폴더만 `git rm`): 배포 스크립트에 **명시적 `PRIVATE_PATHS`(main 에서 `git rm` 할 경로) 단계**를 넣고, 배포 시 신규/갱신 파일 목록(`NEW_FILES`·기존 파일 갱신 루프)에서 제외한다. `scripts/export_public_sheets.py` 는 이 3시트를 공개 스냅샷에 만들지 않게(또는 만들되 배포 대상에서 제외 — 어느 쪽이든 `manifest.json` 에는 안 나온다) 한다. `download-survey.js` 의 주석 처리·`report-widget.js` 제외는 designer 가 이미 했다 — 목록과 일관되는지만 확인. 스크립트가 바뀌면 폰에서 **2회 실행**이 필요할 수 있으니(메모리 `project_termux_deploy_procedure`) 첫 실행이 새 스크립트를 가져오는 구조인지 확인하고 owner 안내 문구를 보고에 적는다.
3. **게이트·시험**: 이 변경으로 깨지는 검사(`validate_live_artifacts`·`validate_data_contract` 의 공개본 대조, `check_master_xlsx_drift`, `tests/test_deploy_assets.py`·`test_push_gate_wiring.py`·`test_prepush_scope.py`·`test_rule_coverage_manifest.py`)는 **느슨하게 풀지 말고** 「비공개 3시트 제외」 규칙을 코드로 명시해 좁힌다(예: `PRIVATE_SHEETS` 상수 하나를 공유). 변이시험 추가(비공개 목록에서 한 경로를 빼면 배포 시험이 실패). 새 RED 는 덮지 말고 종류별 보고.
4. 로컬 검증: 배포 스크립트의 건조 실행/단위 로직으로 「main 에서 이 경로들이 사라지고 다른 파일은 그대로」를 증명(실제 push·배포 금지). 증빙을 `data/_derived/` 새 폴더에 저장.
5. 완료 후 `TODO_publishing.md` Status + `docs/changelog_publishing.md`(되돌리는 방법 한 줄: `PRIVATE_PATHS` 에서 경로 제거 + `download-survey.js` 주석 해제 + exporter 복구).

### 규칙
- 마스터 JSON·xlsx 수정 금지, HTML 금지(designer 몫), 예외 등재 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push·배포 금지.** 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만(고아 프로세스 즉시 종료). 시험·게이트는 한 번에 하나씩 끝까지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 비공개로 만든 경로 목록, 메커니즘, 변경한 검사(좁힌 규칙), 폰 실행 안내(1회/2회), 되돌리는 방법, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 3c83f58·fda6752). 비공개: 기본자본소진율·보완자본소진율·자본비율전망 공개본 3개 삭제·manifest 제외, 배포 스크립트 PRIVATE_PATHS 가 main 에서 이 3개와 루트 JSON 3개(kics_tier1/tier2_utilization·kics_forward_capital)를 git rm(저장소 보관), 새 게이트 규칙·tests/test_private_deploy.py 13건·변이시험 2. 자본성증권발행현황 공개본에서 한도·인정액 계산 열 7개 제외(123행 유지). 재동기화: 뮌헨 K-ICS공시 +3행·스위스리 보험계약부채 +8행(기준표시 「계산값(전 행 합)」)·csm_combo 패널 KR1102 노드·공개본 4개. 게이트 data-contract RED 0·live_artifacts RED 0(등재 25)·드리프트 0. 폰: 작업 브랜치를 먼저 체크아웃해 새 스크립트를 받은 뒤 1회 실행. 주의: 사전 push 훅의 배포 건조 실행 시험이 시험당 5~10분(PC 의 git 호출 느림).
