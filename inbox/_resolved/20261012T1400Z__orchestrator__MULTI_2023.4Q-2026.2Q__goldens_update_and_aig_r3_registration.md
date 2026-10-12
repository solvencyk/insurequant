---
from: orchestrator
to: validation
created: 20261012T1400Z
status: resolved
route: fix
company: MULTI
period: 2023.4Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
오늘 마스터 변경이 모두 커밋됐다(`268002b`·`3bf1690`·`acd351a`·`538cbe7`…). push 전 마지막 정리를 한다. **빨리** 끝내는 것이 우선이다(owner 가 배포를 기다린다). 풀 훅(≈10분)은 오케스트레이터가 이 티켓 뒤에 push 로 돌리니 풀 훅 리허설은 하지 않는다.

### 해 줄 것
1. **골든 `--update`(이유 기록)**: parser-kics 커밋 `acd351a` 가 `kics_disclosure.json` 을 바꿨다(퍼시픽 KR1107 2025.3Q·2026.2Q 항목 47~54 +16행, 악사 KR0049 2024.3Q 4칸). 해당 보고(`git show acd351a`)에 따르면 `tests/test_kics_rules_golden.py`(룰 엔진 findings 매트릭스)와 `validate_golden_input_fingerprints` 의 INPUTS_MOVED ×4(ifrs17_bs·pl_breakdown·dividend·post_transition — 네 빌더가 `kics_disclosure.json` 에서 회사 메타만 읽는다고 보고됨)가 어긋난다. **먼저 그 이동이 정말 이 변경 때문인지(그 외 이동 없음) 확인**한 뒤 `--update` 하고 커밋에 이유를 적는다. 그 밖의 골든(`CLAUDE.md` §7 표: PL `RUN_PL_GOLDEN=1`·post_transition·master_tables·viz 2종·ifrs17_bs(≈8분)·dividend·deploy_assets)도 오늘 변경(`3bf1690` 처브 BS/ILP·분할표·재보사 PL 7칸·`268002b` 손해율·`538cbe7` 재동기화) 뒤에 한 번씩 돌려 어긋남이 있으면 같은 방식(원인 확인 → `--update` → 이유)으로 처리. 이미 통과 중인 것은 재실행 불필요(runlog 로 판단).
2. **AIG(KR0029) 2024.4Q 포트폴리오 검증기 R3 「10배 규칙」 등재**: parser-ifrs17 가 원문을 확인해 값이 맞고 구조적 사유임을 확인했다(`data/disclosure/_meta/ifrs17_owner_followups_runlog_20261012.md` 「등재 필요」). owner 가 「확인된 것만 등재」로 승인했다(2026-10-12 「나머지는 다 승인」). R3 에는 등재부를 읽는 쪽이 없어 **읽는 쪽 분기 + 등재 + 변이시험**을 한다(등재만 하고 룰이 안 읽으면 다음 라운드에 샌다). KR1102(스위스리) 2026.1Q `R2_CENSUS` 는 owner 결정 대기(파생 적재 vs 등재)이니 **등재하지 않는다**.
3. 끝나면 전체 시험 중 빠른 것(`tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py`)과 방금 건드린 골든 시험을 한 번씩. 새 RED 는 덮지 말고 종류별 보고. `TODO_validation.md` Status + `docs/changelog_validation.md`.
4. **보고에 별도 한 줄**: `CSM_WATERFALL_VS_ILP_CSM_STOCK`(워터폴 대 ILP 기준 차이) 룰 설계가 선행돼야 한다는 이전 보고의 내용을 이 라운드 말미 TODO 「열린 일」에 남길 수 있게 필요한 최소 설계 범위(입력·허용오차·예외 형태)를 3~5줄로 적는다(설계 자체는 하지 않는다 — Opus 몫).

### 규칙
- 마스터 JSON·xlsx·HTML 수정 금지. 예외 등재는 위 2번만. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만(멀티라인 `-c`·stdin heredoc 금지, 고아 프로세스 즉시 종료). 시험·게이트는 한 번에 하나씩 끝까지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 업데이트한 골든(이유), 등재 결과, 새 RED(있으면), CSM 룰 설계 범위 메모, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 470e146·b8b949a). 골든 --update: K-ICS 룰 골든·입력지문 4종(17BS·PL·배당·적용후) — 이동 원인은 parser-kics acd351a(퍼시픽 +16행·악사 4칸)와 33635d1(뮌헨 +3행)뿐(직전 마스터로는 골든과 일치 확인), K-ICS 게이트 RED 56 불변. 2차 갱신(뮌헨) 뒤에는 17BS·PL 골든 재실행 생략(두 빌더가 이 파일에서 회사 메타만 읽음). AIG KR0029 2024.4Q R3 10배 규칙: 포트폴리오 검증기에 값 박제 등재부 R3_PINNED_EXEMPTIONS + 읽는 쪽 check_r3 + 변이시험 11건(tests/test_ilp_r3_pinned_exemption.py), 검증기 RED 2->1(남은 1건 KR1102 2026.1Q R2_CENSUS 는 owner 결정 -> 계산값 적재 지시로 parser-ifrs17 에 발주). CSM 워터폴 대 ILP 룰 설계 범위: 입력 CSM_waterfall.json 기말 CSM·insurance_liability_portfolio.json 항목 3+6, 허용오차 후보 max(1억, 0.5%), 재작성 칸 기준 명시 YELLOW·계약이전 칸 값 박제, 롯데 군집은 칸별 분류(TODO_validation 열린 일).
