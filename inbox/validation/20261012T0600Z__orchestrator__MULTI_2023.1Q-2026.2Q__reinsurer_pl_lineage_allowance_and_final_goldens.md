---
from: orchestrator
to: validation
created: 20261012T0600Z
status: open
route: gate-change
company: KR1101-KR1108
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
재보사 재스윕 마감 라운드(owner 2026-10-12 취침 중, 오케스트레이터 자율 진행). 마스터·xlsx·패널·공개본이 모두 커밋됐다(HEAD `bf0b30a` 이후: parser PL/BS `3727438`·CSM `57b7d78`·손해율 `46f74f2`, publishing `66e6156`·`b4b6a71`·`5079688`, validation 속도 `c7f676b`). 이 티켓은 **작업 브랜치 push 직전의 마지막 검증**이다. 풀 훅(`.githooks/pre-push`)은 `c7f676b` 이후 약 11분으로 추정되고 오케스트레이터가 push 때 돌린다 — 사전에 같은 항목을 개별 실행해 통과하게 만든다.

### 현재 상태(오케스트레이터 실측)
- `validate_data_contract.py`: **RED 102 = 전부 `CONCEPT_MIXED_DISCLOSURE_INTO_DART`**. 새 PL 셀들(재보사 8곳 투자손익·영업이익·영업외손익 등, parser `3727438`)의 계보가 경영공시 요약 포괄손익계산서(`data/disclosure/…`)인데 §3d 가 DISCLOSURE 계보 PL 셀을 항목 1·16·22·23·24(+ 항목 4 는 `fs_note_csm_amort` 허용, `1db7c2d`)로만 제한한다. 사이드카 `PL_breakdown_provenance.json` 에는 `how=disclosure_summary_pl_reinsurer`(+쪽·인쇄값)가 달려 있다. 순수 재보사(KR1101~KR1107)·마이브라운(KR1108)은 DART 사업보고서가 없어 원천이 경영공시 하나뿐이고 한 회사 시계열 안에서 개념이 섞이지 않는다 — 항목 4 때와 같은 구조다.
- `MASTER_XLSX_*` 0, `validate_live_artifacts` RED 0, 공개 게이트 0, 빠른 시험 142 통과.

### 해 줄 것 (단계마다 디스크 저장, 런로그 `data/disclosure/_meta/final_round2_validation_runlog_20261012.md` 맨 위 갱신)
1. **§3d 계보 허용 규칙(좁게)**: `how=disclosure_summary_pl_reinsurer` 이고 쪽수·인쇄값이 있는 `contract_notes`/요약 PL 블록의 셀만, **그 `how` 로 실제 적재된 항목 번호 집합**으로 한정해 제한에서 뺀다(집합은 사이드카에서 도출해 코드에 박제하지 말고 상수로 검증). 대상 회사는 **DART 사업보고서가 없는 회사**(재보사 7곳 + 마이브라운, 코드가 아니라 「DART 계보 PL 셀이 하나도 없는 회사」 같은 데이터 조건으로 판정할 수 있으면 그 방식, 아니면 코드 집합 + 사유)로 한정. 다른 `how`·다른 항목·DART 가 있는 회사의 DISCLOSURE 셀은 계속 RED. 항목 4 허용(`1db7c2d`)과 같은 모양으로 구현하고, **수정 전 양방향 시뮬레이션**(102건이 닫히고 새로 깨지는 것 0)과 **변이시험**(허용 범위를 넓히거나 근거·집합 조건을 빼면 잡히는지)을 만들고 `tests/test_rule_coverage_manifest.py`·selftest·`prepush_check` 배선을 같이 확인. 이 허용은 새 예외 등재가 아니라 계보 규칙의 정당한 확장이다(owner 지시: 재보사 투자손익·영업외 공란 채우기). 사유를 `TODO_validation.md`·changelog 에 남긴다.
2. **`PL_YTD_COLLAPSE_TO_ZERO`**: 지금 RED 0 이어야 한다(parser 가 인쇄된 0 7칸을 마스터에서 보류 — owner 승인 전 등재 금지). 만약 RED 로 다시 나오면 **등재하지 말고** 어느 셀인지 보고.
3. **골든 `--update`(이유를 커밋 메시지에 명시, 의도하지 않은 이동은 하지 말고 보고)**: 기대 이동 — `tests/test_master_tables_golden.py`(SUMMARY: `pl_bridge`·closing·`csm_amort_identity`·`qoq_warn`·coverage 등 재보사 적재 반영; 이유 칸 수와 함께), `tests/test_ifrs17_bs_golden.py`(**BS 마스터 +49칸·오버레이 4,300→4,349 → 빌더 산출이 달라지는지** — 지금 마스터 sha 로 골든 sha 와 비교해 정말 움직일 때만 `--update`; ~8분, 부하가 높으니 마지막에 한 번), `RUN_PL_GOLDEN=1` PL 골든(~5분: 빌더 산출 대 골든 지문이 PL 적재로 움직이는지 먼저 확인, 마스터 직접 적재분은 빌더 산출에 안 들어가면 불변), viz 골든 2종(publishing 확인: 4패널·csm_waterfall 바이트 불변 → 통과 예상), `validate_golden_input_fingerprints.py --update`(전체 골든을 먼저 돌려 산출이 정말 안 움직였는지 확인 후). `tests/test_pl_ytd_collapse_owner_confirmed.py` 등 기존 PL 시험이 새 행에서 깨지지 않는지.
4. **훅 항목 개별 실행(풀 훅 대체)**: `scripts/prepush_check.py` 구성 그대로 — data-contract 하드게이트·K-ICS 룰 게이트(`validate_kics_disclosure.py`, 캐시로 빨라짐)·도메인 게이트(csm_continuity·kics_rate_sensitivity·nb_csm_multiple·csm_waterfall·live_artifacts·disclosure_freshness·stale_quarter_tables)·DART raw 유실·골든 입력지문·배포 JS 런타임·inbox 위생·오프라인 테스트 전수(`FULL_COVERAGE_SWEEP=1`, 약 4분 예상). 가능하면 `prepush_check.py` 를 **직접 한 번 돌려도 된다**(push 는 하지 않는다) — 단 PC 부하가 높으니 다른 무거운 일과 겹치지 않게. 결과를 항목별로 표로.
5. **보고만(등재 금지)**: 새로 보이는 owner 결정 사항(예: 인쇄된 0 7칸 등재 여부, R1 정정 15행의 적용 확인 요청, 서울보증 PL 통째 구멍 2건, 스위스리 자본증권 「발행 없음」 표시 방안, 포트폴리오 이름 매핑, 퍼시픽 2023.4Q 항목 4 영업양수분, 뮌헨 2023.4Q ILP 부호 반전)을 한 표로 현재 영향·권고안과 함께.

### 규칙
- 마스터 JSON·등재부 셀 수정 금지(오류 발견 시 inbox 발주), `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 반드시 `--no-build`. 신규 예외·등재 금지(owner 승인 사항은 보고만). xlsx·`public_exports`·HTML 금지. 골든 `--update` 는 위 3번 범위만. 서브에이전트 금지, docling 금지. viz 골든 2종은 산출을 인플레이스로 덮어쓰는 빌더라 실행 전 백업·예외 시 복구.
- 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json` 제외; `.gitignore` 경로를 `git add` 에 넣으면 add 가 오류를 낸다), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push 금지**(오케스트레이터 몫). 파이썬은 풀패스·스크립트 파일만(멀티라인 `-c`·맨 `python`·stdin heredoc 금지), `encoding` 명시. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고 (2~5줄 존댓말 + 파일 경로)
- 허용 규칙 전후(RED 102→0)·시뮬레이션·변이시험 결과, 골든별 `--update` 여부·이동 칸 수·이유, 훅 항목별 결과표(「이 상태로 push 하면 훅이 통과하는가」 한 줄 결론), 보고만 항목 표, 커밋 해시. `TODO_validation.md` Status + `docs/changelog_validation.md`.

## 답변 (recipient 작성 — 처리 후)
