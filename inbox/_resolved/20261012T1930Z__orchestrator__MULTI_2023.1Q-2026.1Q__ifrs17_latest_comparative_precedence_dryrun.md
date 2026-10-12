---
from: orchestrator
to: parser
lane: ifrs17
created: 20261012T1930Z
status: resolved
route: feature
company: MULTI
period: 2023.1Q-2026.1Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): K-ICS 에 정한 원칙을 **PL·CSM 도 같은 로직**으로 검증한다. 원칙의 핵심은 「최신 공시가 그 분기를 다시 보여 준 컬럼(DART 정기보고서의 전기·전년동기 비교 컬럼)을 우선하되, **검증 단위까지 산술이 닫히지 않으면 이전 공시 값을 쓴다**」이다(owner: 「내 논점은 '최신 우선'이 아니라 '검증단위까지 닫히지 않으면 이전값 사용'」). K-ICS 드라이런은 `inbox/parser/20261012T1900Z…` 로 K-ICS 파서가 하고 있다. 이 티켓은 **IFRS17 레인(PL_breakdown·CSM_waterfall·CSM_amortization·ILP·IFRS17_BS)의 읽기 전용 드라이런**이다 — 마스터·등재부·골든·xlsx·HTML 을 쓰지 않는다. 적용은 owner 가 결과 표를 본 뒤 별도 티켓.

### 판정표(오케스트레이터 제안; 드라이런 설계에 그대로 쓴다)
각 (회사 × 분기 × 도메인) **블록**마다 후보 둘 — 현행(마스터 값)과 최신 공시 비교 컬럼 값 — 을 같은 검증 묶음으로 평가한다.
| 최신 비교 컬럼 | 현행 | 판정 |
|---|---|---|
| 닫힘 | 닫힘 | 값이 다르면 **최신 채택**(진짜 재작성; 「†」 재작성 표기 후보) / 같으면 변화 없음 |
| 닫힘 | 안 닫힘(RED·예외 등재) | **최신 채택**(예외 해소 후보) |
| 안 닫힘 | 닫힘 | **현행(이전값) 유지** — owner 원칙 |
| 안 닫힘 | 안 닫힘 | 현행 유지 + 목록(둘 다 못 닫음) |
| 검증 룰이 없는 칸 | — | 반증이 없으므로 최신 우선, 「룰 사각」 표시 |
**닫힘의 범위에 기간 간 연속성을 포함한다**(이것이 PL·CSM 의 핵심): CSM 은 roll-forward 항등식·기시=직전 기말(`WITHIN_FY_OPENING_DRIFT`·경계 단절은 RED)·상각 스케줄 합=CSM 잔액·NB CSM 정합, PL 은 누계(YTD) 관계·분기=누계 차분·보험손익/투자손익/영업이익/세전/순이익 항등식·원수/재보험 부분합, ILP·BS 는 해당 합계 항등식과 CSM·준비금 대조. 소급재작성(IFRS17 전환 비교 재작성 등)은 각 기간 안에서는 둘 다 닫히지만 **다음 기간 기시와의 연속성**은 새 값만 닫으므로 이 판정표로 자연히 채택된다.
- 덮어쓰기 단위는 셀이 아니라 **블록 전체**(관련 항목 한꺼번에); 일부만 덮지 않는다. owner 확정 gold(`data/_gold/user_pl_confirmed_cells.json` 등)·`PL_BREAKDOWN` owner-confirmed 이상치와 겹치면 「gold 충돌」로 제외. 어느 비교 컬럼이 출처인지(공시·DART 문서·쪽/표) 적는다.

### 해 줄 것
1. **예외·보류 전수 목록**: IFRS17 레인에서 예외·등재·보류로 남아 있는 것을 모아 (회사, 분기, 도메인, 룰, 사유)로 한 표에 모은다 — 예: `WITHIN_FY_OPENING_DRIFT`/라이나 CSM 2023.1Q·2Q 보류(`data/_derived/csm_backfill_lina_20261011/held_rows_waterfall.json`), 경계 단절·재작성 3사(라이나·미래에셋·KB라이프) 사이드카, `_PL_SOURCE_ABSENT`, `PL_YTD_COLLAPSE_*`, `INSPL_CENSUS_MISSING`, ILP R2/R3/R4, 하노버 2023.4Q ILP 재작성 충돌·뮌헨 2023.4Q ILP 부호 반전·제네럴 민감도·퍼시픽 2023.4Q CSM 항목 4(`3bf1690` 계열), CSM 워터폴 대 ILP 기준 차이(`data/_derived/validation_registrations_20261012/csm_wf_vs_ilp_basis_diff_cells.md`), 예별 2025.4Q 등. 유형 분류: ⓐ 공시 간·재작성 충돌(이 원칙의 대상) ⓑ 발행사 자체 불일치 ⓒ 원문 부재 ⓓ 파서 오류/오탐 ⓔ 기타.
2. **ⓐ 건마다 드라이런**: 후속 공시(DART 사업·반기·분기보고서, `data/dart/**` 원문 XML)의 전기·전년동기 비교 컬럼을 추출해 위 판정표로 평가(임시 사본 위에서 게이트·검증기를 돌림). 특히 **라이나 CSM 2023.1Q·2Q**: 2024.1Q·2Q 보고서의 전년동기 비교 컬럼이 재작성 기준으로 2023.1Q·2Q 값을 담고 있다면 보류 건이 이 원칙으로 풀리는지 확인(이전 라운드 owner 결정은 「보류 유지」 — 새 근거가 나오면 보고만 하고 적재하지 않는다).
3. 산출: `data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/`(분류표 csv, 건별 판정 csv — 현행 값·최신 비교 컬럼 값·두 후보의 새 RED/닫힘 결과·판정·출처, 요약 md, 재현 스크립트). 요약: 유형별 건수, 판정별 건수(최신 채택/현행 유지/둘 다 불가/룰 사각/gold 충돌) + 영향 셀 수, 라이나 2023.1Q·2Q 가능 여부, **새로 드러난 문제**, 이 판정표를 PL·CSM 에 적용할 때 룰(닫힘 판정)이 부족한 곳(검증 룰 사각 목록).
4. 이전 라운드 사례(`docs/changelog_parser_ifrs17.md` 의 재작성·R1 15행·`3bf1690` 등)를 먼저 읽어 중복 판정하지 않는다.

### 규칙
- 마스터 JSON·xlsx·`public_exports`·HTML·골든·등재부 수정 금지(드라이런). 임시 사본은 `data/_derived/` 아래에서만. docling 불필요(DART XML). `validate_master_tables.py` 는 `--no-build`, `build_root_masters.py main()` 금지. 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`·스크립트 파일만(멀티라인 `-c`·stdin heredoc 금지, 고아 프로세스 즉시 종료). 게이트·시험은 한 번에 하나씩 끝까지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 예외 전수 건수·유형 분포, 판정별 건수와 영향 셀 수, 라이나 2023.1Q·2Q 가능 여부, 룰 사각, 산출 경로·커밋 해시. `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.

## 답변 (recipient 작성 — 처리 후)
드라이런 완료(parser-ifrs17, 커밋 580ae0e, 읽기 전용; 마스터·등재부·골든·xlsx 무변경). 산출: data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/ (classification.csv · case_verdicts.csv · census_blocks.csv · dryrun_stats.json). summary.md 는 하니스 쓰기 제한으로 못 만들었고 같은 내용이 docs/changelog_parser_ifrs17.md 11차 항목에 있다.
예외·보류 254건 분류(ⓐ 30 · ⓑ 11 · ⓒ 90 · ⓓ 77 · ⓔ 46 · 신규 발견 9). 529블록 판정: 최신 채택 39(진짜 재작성 32 · 예외 해소 7, 마스터 셀 약 240) · gold 충돌 59 · 현행 유지 24 · 둘 다 불가 1 · 조건부 2 · 후보 미검증 107(PL Tier-2 전기 컬럼 리더 부재) · 이전 라운드 재판정 안 함 7 · 변화 없음 206 · 비교 컬럼 추출 불가 84.
라이나 CSM 2023.1Q·2Q 보류 유지(최신 비교열이 보류 행과 숫자까지 같음). 적용은 마스터만 고치면 빌더가 되돌리므로 gold-overlay 등재 또는 전기 컬럼 리더가 필요 — owner 결정 후 별도 티켓.
orchestrator 종결: 2026-10-12.
