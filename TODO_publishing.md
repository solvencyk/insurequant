# Insurequant Publishing TODO (Stage 4)

> Last updated: 2026-08-25 · Stage 4/5 — publishing
> Prompt: docs/agents/claude-agent-publishing.md · Changelog: docs/changelog_publishing.md

Stage 4 — **publishing**: validated per-source JSON → unified master JSONs read by HTML + recommended commit/push commands. Designer ([`TODO_designer.md`](TODO_designer.md)) owns HTML structure/styling; publishing only writes JSON masters. Created 2026-05-31 by splitting out of root `TODO.md` (merged former gathering + pushing stages).

Session start: read this file + `claude-agent-publishing.md` + relevant validation report.

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

## Status

**2026-08-25 (프롬프트 정합 — 이상치 분류 주기 확정)**: validation 티켓(`inbox/_resolved/20260825T0130Z`) 처리. 2026-08-25 커밋 `22697c2`로 일반 이상치 발견/트리아지가 push 게이트에서 분리(삭제 아님 → `scripts/scan_generic_anomalies.py`)되면서 stale해진 프롬프트 문장 4개를 코드 대조로 확인 후 정정. **핵심 결정: 이상치 발견+LLM-skeptic 은 push마다가 아니라 "분기 라운드 1회"로 돌린다** — 실행 주체(publishing)·4개 트리거(분기 라운드 첫 push 전 / 새 마스터 온보딩 / 빌더 대개편·±100행 뒤채움 / owner 요청)·기록 위치(라운드 리포트 + 이 TODO)를 `claude-agent-publishing.md` **§3.0b**에 명문화. 폐지도 "owner 요청 시에만"도 기각(근거: 산술 게이트는 내부적으로 닫히는 단위오류(BNP 1.77조)를 못 잡는다 / 문서에만 있고 아무도 안 부르는 단계가 이 저장소의 반복 실패형태). §3.0도 실제 체인(①·①b K-ICS·①c 도메인 4종·③ inbox·④ 오프라인 테스트)으로 갱신 — 종전 서술은 이상치 건 이전에 이미 2026-08-21 배선 4종이 통째로 빠져 있었다. 스캐너 실측(`--no-write`, 산출 JSON이 git 추적이라 트리 안 더럽힘): 후보 224(PEER_OUTLIER 147·COHORT_ZERO 77) → REAL=77 UNCERTAIN=6 NOISE=134 OWNER_CONFIRMED=8 → skeptic 입력 83건(2026-06 이후 **미분류 방치 중**, 다음 분기 라운드에서 소화). **부수 발견**: 무관한 stale 사실 `"prepush_check.py는 validate_kics_disclosure.py를 호출하지 않는다"`가 4곳에 복사돼 있었는데 2026-08-21 단계 1b 배선으로 이미 거짓(정반대를 퍼뜨리고 있었음) — `docs/launch_runbook.md`·`.claude/skills/launch-runbook/SKILL.md`·`.claude/skills/incident-postmortem/SKILL.md`(frontmatter+본문 함정표) 정정. `docs/postmortems/PM-2026-06-16` 배선표에는 후속 정정 각주 추가(이력은 보존). **단 SKILL 2건은 `.gitignore:86`이 `.claude/`를 통째로 무시해 git에 안 실린다 — 이 머신에만 반영됐고 다른 클론에는 stale 문장이 남는다**(스킬 = 머신-로컬 운영정본이라는 기존 계약대로이나, "고쳤다"를 "전파됐다"로 읽지 말 것). `docs/` 4건은 추적되므로 커밋 시 전파된다. 검증: 편집 5파일 UTF-8 BOM 없음, `pytest test_deploy_assets.py` 10 passed, inbox 위생 위반 0. **미착수 권고 1건**: `scan_generic_anomalies.py`가 화면에 후보 8건만 찍고 정작 조치 대상 83건(특히 skeptic 스코프인 UNCERTAIN 6건)은 JSON에만 남긴다 — 게이트 밖 수동 스크립트는 터미널이 곧 UI라 UNCERTAIN 전건 인쇄 권고(스크립트 소유자 = validation, 코드 미수정). 커밋/푸시 없음.

**2026-08-20 (배포 12차)**: 이전 턴에서 남겨뒀던 "2023년 준비금 뒤채움 과대계상" 건이 parser+validation 왕복으로 해소된 것을 확인 후 배포. `IFRS17_BS.json` 6,953→6,855행(뒤채움 사본 98칸 제거+원문대조 10칸 정정) — 삭제분은 validation이 FS-API 캐시 전수 조회로 실관측 0건 확인, 정정분은 원문 raw 대조로 이중검증됨(4중 독립검증 기록 확인 후 진행). combo-diff로 재확인(lost 98/gained 0/value-changed 10, 티켓 수치와 일치). 부수로 R-RSV-1 래칫 baseline 키 구조 버그도 같이 고쳐짐(구간축소를 오탐 RED로 잡던 것). 골든 fixture 재추적(이전 커밋에 stale 버전이 실려 있던 걸 최신화). xlsx 17BS 시트 재동기화. `55ef3ec..346e4da`. 라이브 확인: 6,855행, 삼성화재 2023.2Q 해약환급금준비금=556,503.49(정정값) 확인, 콘솔 에러 0.

**2026-08-20 (배포 11차)**: 2026.2Q 배당 갭 해소 배포 — `dividend.json` 1,924→2,043행(+119, DART alotMatter negative-cache 해제로 19개사 신규 유입) + xlsx '배당' 시트 동기화(공식 xlsx skill, 다른 8개 시트 무변경 확인, 수식 0개라 캐시 위험 없음). `a0979b9..55ef3ec`. 게이트 RED=0, combo-diff 손실0, `test_dividend_golden.py` 재생성 확인. 라이브: 2,043행·2026.2Q 24개사 fetch 확인, 콘솔 에러 0. `inbox/publishing/20260820T1815Z`(parser)·`20260820T1500Z`(validation, "masters ready" 통지) 둘 다 답변·`_resolved/` 이동 — publishing inbox 전부 drain됨.

**2026-08-20 (배포 10차)**: 8/19~20 parser 작업분 전수 확인 후 배포(`5c27538..a0979b9`). 사전 확인: `IFRS17_BS.json` combo-diff에서 8셀 LOST 발견 — TODO_parser_ifrs17.md 24th pass 기록 대조해 OFS/CFS 표선택 버그 정정으로 인한 의도된 삭제임을 확인(DB손해·한화생명 2023.1Q 연결오염 제거, 문서화됨). `CSM_waterfall.json`은 키 동일(0 lost/gained)인데 diff 39,590줄이라 값 단위로 재대조 — 실제 값변경 6셀뿐(예별손해 부호수정, 미래에셋생명 2026.2Q CSM상각 결측해소, 둘 다 기존 티켓과 일치). `kics_forward_capital.json`은 순수 추가(quarter-agnostic baseline 키, 기존값과 동일). 게이트 RED=0, BS항등식 356P/0F, `pytest test_deploy_assets.py` 10 passed. 라이브 확인: BS 6,953·CSM 2,136행, 미래에셋생명 CSM상각=-1128.3(결측 해소) fetch 확인, 콘솔 에러 0.

**2026-08-20 (gold-overlay 착수)**: owner 승인 받아 `20260620T0859Z` 착수·완료(`71914c3`, 로컬 커밋 — scripts/tests라 main 미배포). PL/CSM 오버레이 파일(`data/dart/viz/{pl,csm}_manual_overrides.json`)을 K-ICS 관례에 맞춰 `data/_gold/user_{pl,csm}_cells.json`로 이전, `build_root_masters.py`/`emit_ifrs17_provenance.py` 경로 갱신. 진짜 구멍이던 `sync_owner_fills_to_json.py`(xlsx H열 동기화가 루트 JSON에 직접 써서 리빌드에 클로버되던 경로)를 gold 오버레이 경유로 리라우팅(즉시반영은 유지). 회귀 테스트 신설(`tests/test_gold_overlay_survives_rebuild.py`, tmp_path 격리, 2번 연속 리빌드에도 gold 셀 생존 확인, 3/3 pass) — `build_root_masters.py` 실행 금지 원칙은 유지(직접 실행 안 함). `user_pl_confirmed_cells.json`(skeptic suppress)은 스키마가 달라 병행 유지. 부수 발견: 커밋 직전 IFRS17_BS.json이 다른 세션 작업으로 5,686→6,209행 되며 RED=12 — 내 스코프 아니라 커밋에서 제외. 부수 사고(경미): 세션 시작 전부터 staged였던 무관 archive rename 8건이 커밋에 같이 딸려감(순수 rename, 데이터 위험 없음) — `git commit`이 add한 것만이 아니라 index 전체를 커밋한다는 걸 또 놓침.

**2026-08-20 (배포 9차 + 정리)**: owner 상태점검 티켓(`inbox/publishing/20260820T0033Z`) 대응. 워킹트리에 미커밋 상태로 쌓여있던 루트 마스터 3종(CSM/PL/BS) 발견 — combo-diff로 안전 확인 후 WIP 체크포인트 커밋(`4592f1e`), IFRS17.html 증분(원천테이블 연도모드 4개년 캡 수정, 2021년까지 늘어지던 버그)도 검증(`eqYearPeriods()` 실데이터 실행 확인) 후 커밋(`a6acee6`). main 배포(`fca6560..5c27538`): IFRS17_BS.json(5,587→5,686) · PL_breakdown.json(8,554→8,650) · IFRS17.html. 라이브 확인 완료. 골든 stale 건은 parser에 리마인드만(기존 발주 유지). gold-overlay 통일 건(`20260620T0859Z`)은 여전히 미착수 — owner 확인 필요하다고 답변에 명시. 나머지 68건 미커밋 파일은 타 stage 소관이라 미손댐.

**2026-08-19 (배포 8차)**: IFRS17_BS.json 준비금 세부확대(22분기, 5,028→5,587행) + IFRS17.html 원천 테이블 패널 배포(`5e0af59..fca6560`). 배포 전 combo-diff 손실0·RED=0·BS항등식 356P/0F·`node --check`·실제 렌더함수 라이브데이터 실행(항등식 gap=0) 전부 확인. **특이사항**: `tests/test_ifrs17_bs_golden.py` FAIL(픽스처 stale, 5,389→5,587행 drift) — 데이터 자체는 안전 확인됐으나 골든 재생성은 빌더 소유자 판단이 필요해 parser에 발주(`inbox/parser/20260819T0858Z`), owner 지시대로 배포 먼저 하고 골든은 별도 트랙으로 진행. 라이브 확인: 원천 테이블 18행 렌더, 콘솔 에러 0.

**2026-08-18 (배포 7차)**: index.html CSM 버블맵 로그축 자동범위 수정 — `9619297..5db2610`. ECharts 로그축이 데이터 최댓값(~1.7조)을 다음 10의 거듭제곱(10조)으로 반올림해 버블이 왼쪽에 몰리던 문제, 매 렌더마다 현재 표시 데이터의 실제 min/max+로그패딩(×1.58)으로 축 범위 재계산하도록 수정(하드코딩 없음, 업권 필터에도 반응). 전체 [1,10조]→[4억,2.7조]·손보필터 [6억,2조] 압축 확인, 콘솔 에러 0, `pytest test_deploy_assets.py` 10 passed. JSON 마스터 변경 없음. 라이브 hard-reload로 배포 반영 확인.

**2026-08-18 (배포 6차)**: index.html CSM 버블맵 X축(신계약CSM)을 Y축(배수) 고정타깃(2026.1Q)에서 분리(D-2 후속, owner 20260818T0210Z) — `996e5ba..9619297`. X축을 회사별 최신(CSM_waterfall 항목2)으로, "직전값 이월" 오표기 제거, 스케일 ÷4→÷2 수정. 이번엔 로직이 복잡해서(추정/비추정 분기 처리) `node --check` 문법검사에 더해 **실제 `buildBubbleData()` 함수를 파일에서 그대로 추출**해 라이브 데이터로 브라우저에서 직접 실행 — 37개사 NaN 0건, 삼성화재(최신) raw값 그대로, AIG손보(연1회공시) 986.8→493.4(÷2) 정확히 확인. 배포 후 라이브 hard-reload로 새 캡션 텍스트 반영 확인, 콘솔 404 1건은 제 검증스크립트 자체의 fallback fetch였음(실제 페이지 리소스 전부 200).

**2026-08-18 (배포 5차)**: designer HTML 4개 배포(`d225383..996e5ba`, `inbox/_resolved/20260818T0104Z`) — owner D-1~D-5 지시 반영. K-ICS.html(baseline 키 폴백, UH-7 후속) · index.html(CSM버블 캡션 정확화 + 하드코딩 "2026.1Q" 동적화) · IFRS17.html(PL기간 피커가 최신이 반기여도 직전FY로 고정되던 버그 수정 + 법정준비금 재배치 + CSS 토글 버그) · 공시보고서.html(분기/연도 토글 추가 + 항목1 제거). JSON 마스터 변경 없어(순수 HTML/JS) combo-diff는 불필요, 대신 4개 파일 인라인 스크립트 전부 `node --check`로 문법 검증(로컬 브라우저 preview가 이번에도 compositing 안 돼 대체) + `pytest test_deploy_assets.py` 10 passed. 라이브 검증: 공시보고서 분기/연도 토글 동작, IFRS17 `histRange`가 "2023.1Q~2026.2Q"로 동적 갱신 확인, 콘솔 에러 0.

**2026-08-17 (배포 4차)**: 라이브 버그 수정 — 2026.2Q PL 생명장기 분해 9개사(삼성화재·DB손보·현대해상·한화생명·한화손보·흥국화재·미래에셋생명·롯데손보·코리안리)가 main에 item2-14 통째 null로 올라가 있던 걸 owner가 화면에서 발견(`inbox/_resolved/20260815T1400Z`). owner가 신설 PL↔CSM워터폴 교차대조 룰 3종을 즉시 RED로 승격시켜 배포가 며칠 보류됐다가, parser(20건)+downloader(AIG 2023.4Q raw 1건) 해소로 RED=0 전환. 독립 재확인(gate RED=0 + combo-diff 4마스터 전부 손실0) 후 `PL_breakdown.json`(8,543→8,554행)+`IFRS17_BS.json`(5,008→5,028행) 배포(`1902bd7..d225383`) — CSM/dividend는 main과 이미 동일해 제외, HTML 4개도 diff 0 확인 후 배포에서 뺌. 라이브 검증: 삼성화재 2026.2Q 24행 전부 채움 확인, 원수CSM상각=802,950백만원(8,029.5억) 표값과 일치.

**2026-08-15 (배포 3차)**: CSM continuity 수정(5사 override 철회+2026.2Q raw 재확정) + PL 기타사업비용 9셀 복원 main 배포(`6e5634f..1902bd7`). xlsx는 parser가 이미 재생성해둬서(mtime 확인) 재작업 불요, 시트 행수(CSM 2,136·PL 8,543)도 대조 확인. 격리 워크트리 cherry-push, `CSM_waterfall.json`/`PL_breakdown.json` 2개 파일만. 라이브 검증: 브라우저에서 직접 fetch해 행수 + 교보생명보험 2026.2Q 기초CSM=65,109.6 확인(WebFetch는 대용량 파일 앞부분만 봐서 신뢰 불가 — 이후 큰 JSON 검증은 브라우저 직접 fetch 우선).

**2026-08-15 (사고)**: publishing 과실로 데이터 유실 발생 — `scripts/build_tidy_exports.py`를 내용 확인 없이 실행, 루트 `CSM_waterfall.json`/`PL_breakdown.json`/`CSM_amortization.json`을 이 스크립트의 자체(훨씬 좁은) 계산으로 덮어씀(CSM 2,136→1,794행, **PL 8,543→187행**). 유실분은 parser가 방금 완료한 CSM continuity 수정(`inbox/parser/20260815T0042Z`, override 철회 + 2026.2Q raw 재확정)이었는데 git에 커밋된 적이 없어 복구 불가 — git 이력·타 세션 scratchpad 확인했으나 백업 없음. **즉시 조치**: 두 파일 다 마지막 커밋(`08321db`/`79b1f7d`, CSM 1,962행·PL 8,111행)으로 롤백, 게이트 RED=0 재확인 — **main/라이브는 무관**(유실분이 애초에 미배포 상태였음). 재작업 발주: `inbox/parser/20260815T0739Z`(HIGH). **교훈**: 처음 보는 스크립트는 반드시 내용부터 읽고, 루트 마스터에 손댈 가능성 있으면 사전 백업 후 실행.

**후속 (같은 날)**: 유실분은 parser가 별건 작업 중 `build_csm()`/`build_pl()`을 재실행하며 override 파일 덕에 우연히 복구(재작업 불필요, `inbox/_resolved/20260815T0739Z`). 같은 날 validation이 **별도의 두 번째 마스터 되감김**을 지적(`inbox/_resolved/20260815T1130Z`, `validate_master_tables.py`를 `--no-build` 없이 돌리는 함정 재발) — publishing도 `validate_master_tables.py` rebuild 기본값 반전(기본 no-build)에 동의 표명, parser 쪽 요구와 합쳐 2-스테이지 조건 충족. **앞으로 publishing은 게이트를 `validate_data_contract.py` + `validate_master_tables.py --no-build` 두 개로만 돌리고, 루트 마스터 빌더는 직접 실행하지 않는다.** 최종 검증: CSM 2,136행·PL 8,543행·IFRS17_BS 5,008행·dividend 1,924행, RED=0, `--no-build` cont=0. 잔여 1건(동양생명 2025.3Q 재보험예실차 0-회귀, YELLOW·비차단)은 parser 미착수 — 배포 전 owner 인지 필요.

**2026-08-15 (배포 2차)**: IFRS17 재무상태표 패널 T자 재구성 main 배포(`4f1d344..6e5634f`) — Panel 7(타일형)을 Panel 1(최상단)로 이동해 T자(좌 자산/우상 부채/우하 자본, 실값 비율) + 2단계 드릴다운으로 전면 개편(`inbox/_resolved/20260814T1250Z`, designer). `IFRS17_BS.json`도 같이 갱신: `섹션`/`레벨` 컬럼 추가, 항목 1-7→1-31, 1,637→5,008행. **`scripts/build_ifrs17_bs.py`가 여태 git 미추적이었던 것을 이번에 발견해 같이 커밋** — 앞으로는 이 파일도 정상 추적됨. 게이트 RED=0 YELLOW=236, `pytest test_deploy_assets.py` 10 passed 확인 후 owner GO 받고 push. GitHub Actions Pages 배포(legacy `pages/builds` API는 새 커밋을 안 잡아줘서 `gh run list`로 확인 — 다음부터는 이쪽을 우선 사용) 확인 후 라이브 검증: `IFRS17_BS.json`에서 `섹션`/`레벨` 필드 WebFetch 확인 + 브라우저에서 삼성화재해상보험 선택해 T자 패널 실데이터 렌더 확인(자산 112조4,436억=부채 77조981억+자본 35조3,455억, 항등식 성립).

**2026-08-15 (배포)**: `dividend.json`(신규, DART alotMatter 배당현황, 24개사, 1,924행) + `공시보고서.html`(배당현황 대시보드 오픈, designer 작업물) + `PL_breakdown.json`(61셀/1,475행 유실분 복구, 7,799→8,111행) main 배포 완료(`de0aef9..4f1d344`, 격리 워크트리 cherry-push). Pre-flight `validate_data_contract.py` RED=0 YELLOW=220, `pytest test_deploy_assets.py` 10 passed 확인 후 owner GO 받고 push. 라이브 검증: `dividend.json`/`PL_breakdown.json` WebFetch 스키마 확인 + 브라우저에서 삼성화재해상보험 선택해 배당 Panel 실데이터 렌더 확인(현금배당금총액 8,289억원 등) + 콘솔 에러 0. `inbox/publishing/20260814T2230Z`(dividend keep-list) `_resolved/`로 이동. **PL_breakdown 근본원인(`validate_master_tables.py`가 `--no-build` 없이 돌면 `build_root_masters.py` 재실행으로 같은 61셀을 결정론적으로 다시 떨굼)은 미수정** — `inbox/parser/20260814T1637Z`에 열어둠, parser가 빌더를 순가산으로 바꾸거나 rebuild 기본값을 반전해야 재발 방지.

**2026-08-15**: `dividend.json`(신규 마스터, DART alotMatter 배당현황, 24/39사 Tier-1, 1,924행) keep-list 등록 처리(`inbox/publishing/20260814T2230Z`, 이후 배포로 종결 — 위 항목 참조).

**2026-08-14 (배포)**: `IFRS17_BS.json`(신규, 1,637행) + `IFRS17.html`(Panel 7 "재무상태표·자본의 질") main 배포 완료 (`255e445..de0aef9`, 격리 워크트리 cherry-push). Pre-flight `validate_data_contract.py` RED=0 YELLOW=220 확인 후 owner GO 받고 push. 라이브 검증: `IFRS17_BS.json` WebFetch로 스키마·내용 확인, `IFRS17.html`은 브라우저에서 삼성생명(KR0069) 선택 후 Panel 7 렌더 확인(자산총계 309조 9,483억원, 2025.4Q) + 콘솔 에러 0. `common.css` 등 나머지 keep-list는 main과 동일해 미포함. 워크트리 정리 완료.

**2026-08-14**: HIGH 티켓(`inbox/publishing/20260814T0232Z`, owner) 처리 완료 — `equity_composition.json`(항목1-49, 아카이브됨) → `IFRS17_BS.json`(항목1-7) keep-list 교체. `claude-agent-publishing.md` §1 fetch표·§9 keep-list 스냅샷·§0 게이트 라이브 수치 갱신, `build_master_xlsx.py:18` 소스 스왑(`17BS` 시트, owner 수기 피벗은 백업 후 소실 — 보정 로직은 `build_ifrs17_bs.py`에 이식 확인됨), xlsx 재생성(8열·1,637행). `pytest tests/test_deploy_assets.py` 10 passed. 이 티켓 `_resolved/`로 이동.
- **당시엔 RED=42로 push 보류 보고**(6개사 Tier-2 본표 부분추출, `[IFRS17_BS] BS_CENSUS_MISSING_ITEM`) — **재확인 결과 다른 세션(validation)이 이미 RED=0으로 종결**해 있었음: owner가 "DART API 013/014 실측 결과 비상장 6개사는 XBRL 자체가 없다"를 확인하고 "걔네는 걍 접고 마무리해" 지시 → `validate_data_contract.py`에 `IFRS17_BS_NO_SOURCE` census 면제 추가(`BS_IDENTITY`는 계속 검사), YELLOW 1건(`BS_CENSUS_NO_SOURCE_COMPANY`)으로 집계만 남김(`inbox/_resolved/20260814T0620Z`). `claude-agent-publishing.md`의 RED=42 서술 3곳 정정 완료. **기술 게이트는 RED=0으로 통과 — 실제 main push는 여전히 owner 명시적 GO 별도 필요**(publishing은 권고만).

**2026-08-14 (inbox 정리)**: 2~8주 방치된 backlog 티켓 다수가 실제로는 이미 처리 완료됐는데 frontmatter `status`가 `open`으로 남아 있거나(`## 답변`엔 "status: answered"라 적어놓고 YAML은 안 고침) 후속 아키텍처 전환으로 obsolete가 된 채 방치돼 있었음 — 재확인 후 정리:
- `resolved`+archive: `20260803T0743Z`(xlsx 재생성, 기존 답변 확인만) · `20260814T0135Z`(equity keep-list gap, superseded 확인) · `20260620T0859Z_skeptic_hardening`(§3 하드닝 규칙 4개 전부 이미 프롬프트에 반영 확인) · `20260616T0700Z`(K-ICS FORWARD_DATA 인라인 재임베드 — 이후 "인라인 금지" 리팩토링으로 아예 다른 방식으로 대체돼 obsolete) · `20260813T0422Z`(equity_composition 배포준비 — 파일 자체가 archive돼 superseded)
- frontmatter만 `open`→`answered` 동기화(내용은 이미 종결, 재확인 대기 상태로 존치): `20260619T0412Z`(prepush_check 체인+skeptic 배선, 현재 §0에 라이브) · `20260620T0834Z`(코리안리·삼성화재·신한이지 5셀 owner-확정 레지스트리, `data/_gold/user_pl_confirmed_cells.json` 존재 확인)
- **진짜 미착수로 남은 것**: `20260620T0859Z__gold_overlay_durable_ownerfix` (open) — PL/CSM 마스터에도 K-ICS식 gold-overlay를 build 마지막 단계로 통일하자는 owner 아키텍처 요청, `## 답변` 공란. 착수 안 함(범위가 커서 owner 확인 후 진행 권고).

**2026-08-06**: `inbox/publishing/20260806T0027Z` (owner) — `claude-agent-publishing.md`가 viz path migration 상태를 두 곳에서 모순되게 서술(§1 "still reads data/ifrs17/viz" vs §9 "LANDED"). `git ls-tree -r main` + `git show main:IFRS17.html`로 실측 확인: 라이브는 전부 `data/dart/viz/*`에서 fetch, `data/ifrs17/viz`는 main·로컬 어디에도 없음 → §9가 맞음. §1 stale Path note 삭제, §9 문구를 실측근거로 교체, §9 delete-list 예시에서 존재하지 않는 `data/ifrs17/viz` 제거(`data/ir`는 유효해 유지). Resolved, `inbox/_resolved/`로 이동.

Open viz-assembly work, all gated on upstream stages: F4 v2 (forward-outlook confidence research), F13 (재보험 지표, waits on downloader F8), F17/F18 viz (waits on parser Tier2/IR JSON). CSM bubble map **완결됨** (라이브, 2026-06-14 — 4축 V2 폐기). No master JSON push pending here standalone.

**2026-08-03**: 2026-08-03 capsec 체인의 마스터 JSON 4종을 `main`에 배포 완료 (`a4e8a7c..255e445`) — `CSM_waterfall.json`(1944→1962행, KR0004 3개년 온보딩)·`NB_CSM_multiple.json`(321→327)·`PL_breakdown.json`(KR0051 2025.4Q 투자이익/보험금융손익 분리)·`kics_forward_capital.json`(FSC→DART 리베이스). HTML 4종+`common.css`는 main과 이미 동일해 미포함. Pre-flight `validate_data_contract.py` RED=0, 행 손실 가드 dropped=0, 배포 후 라이브 4파일 브라우저 fetch 검증 완료.

**2026-08-03 (2차)**: inbox 2건 처리.
1. `insurequant_master_tables.xlsx` 재생성 완료 (`inbox/publishing/20260803T0743Z`, resolved) — 재생성 전 수식 셀 0건 스캔 확인 후 `.bak` 백업 → `build_master_xlsx.py` 실행. KR0004 3개년·KR0051 PL 분리값 눈으로 확인. xlsx는 untracked/push 비대상.
2. `kics_forward_capital.json`의 `baseline_2025_4Q` 키 오기(UH-7, `inbox/publishing/20260803T0210Z`, answered) — `scripts/forward_capital_simulation.py`에서 quarter-agnostic `baseline` + `baseline_quarter` 형제 필드로 교체, 하위호환 위해 이번 릴리스만 `baseline_2025_4Q` alias 병기. 재생성 후 `validate_data_contract.py` RED=0, `pytest tests/test_deploy_assets.py` 9 passed. HTML 소비처(`K-ICS.html:1090`, 1곳)는 publishing이 못 건드리므로 designer inbox로 라우팅(`inbox/designer/20260803T0900Z`) — alias 제거는 designer 스왑 확인 후.

**2026-07-22**: designer의 A11y 색상/대비 2차분(owner-review queue 5건, `docs/changelog_designer.md` 2026-07-21d) + 트리맵 red→blue 원복(finviz 정체성, 07-22) — `launch_runbook.md` 절차로 격리 워크트리 cherry-push, owner GO 받고 `main`에 push 완료(`a5d0ffa`, index/K-ICS/IFRS17.html + common.css). Pre-flight `validate_data_contract.py` RED=0 확인. 배포 후 라이브 4개 값 curl 검증 완료.

**2026-07-21**: provenance sidecar 3종 발행 완료(forward_capital/tier1/tier2_utilization) + 게이트 로더 키-불일치 버그 수정, launch runbook 신설(`docs/launch_runbook.md` + `launch-runbook` skill). `inbox/publishing/20260716T0330Z`(2026.1Q 5개사 적용후 요구자본 fill 배포 여부) — owner 승인 받고 착수했으나 `git fetch origin main` 대조 결과 **이미 다른 세션이 배포 완료**(kics_disclosure.json diff 0) — 중복 push 스킵, resolved. **미착수 잔여 backlog** (2026-06-16~20, owner/designer 발주, 이번 세션 범위 밖): reembed-done trigger(0616T0700Z) · skeptic gate-chain 문서화(0619T0412Z) · owner-confirmed registry 분쟁 3건(0620T0834Z) · gold-overlay 통일 요청(0620T0859Z) · skeptic 하드닝 명문화(0620T0859Z) — `inbox/publishing/`에 `status: open`으로 남아 있음, 다음 세션에서 트리아지 필요.

---

## 🚧 Open publishing work

### F4 v2 — Forward Outlook confidence: Cat C/D research + 외국계 분류 helper

Scope 좁힘 (cat E 정상 제외 / cat F 코드 fix 완료).

- F4 v2 report: `output/kics_forward_capital/confidence_low_rootcause_v2_20260525T145147Z.md`
- **Cat B drill-down**: 11사 (10 아님) — KR0069 삼성생명 BS T2 66,289억 (FSC alias 최대 gap), KR0008 삼성화재 4,097억, KR1000 코리안리 4,431억 = alias 해결 시 75,000억 격차 해소
- **Cat C/D 리서치 필요**: BS 자본성증권 carrying value 정의 (FV vs amortized) + Call exercise 시 차감 메커니즘. 답 나오면 over/under_deduct 의미 재정의
- **외국계 분류 helper** 코드 추가 권고: `bond_coverage="no_self_issued, parent_capital"` 등

### F13 — 재보험 영업 지표 세트

Cross-source assembly: GA 채널비중 (downloader F8 → `TODO_downloader.md`) · 위험손해율 (⚠️ 공시-실무 왜곡 명시) · **재보험 현황** (출재보험료 비중 · 출재 CSM 규모 · 원수vs출재 마진갭) · 해지율 13·25·37회차 (F2/F8 → downloader). → 역선택 조기경보 스코어 + 이중관점(원수사 vs 재보험사) 카드.

- [ ] downloader F8 (consumer.knia.or.kr) 도착 후 assembly start ⚠️ **2026-08-20 실측: 미착수** — `source-catalog.yaml` L392에 URL만 등재돼 있고 `data/knia_consumer/` 없음. downloader TODO F8은 여전히 🔴 P1(사이트 구조 probe 단계).
- [ ] 출재율 metric derive — DART reinsurance rollforward (parser side OK) → ratio compute
- [ ] 카드 viz JSON contract 정의 → designer 핸드오프

### F17 viz — Panel 3 net income breakdown (gathering side; parser body in `TODO_parser.md` F17)

Parser는 데이터 추출 + reconciliation gate. Publishing은 그 결과를 panel JSON으로 어셈블 + HTML가 읽도록.

- [x] Tier1 (전사) JSON 어셈블 — 10/10 손보 — `data/dart/viz/net_income_breakdown.json` exists, Panel 3 swapped
- [ ] Tier2 (LOB) — parser 9/11 확장 결과 어셈블 (F17 in-flight decision pending in parser TODO)
- [ ] Tier2 stacked-bar / waterfall viz contract 결정 → designer 핸드오프

### F18 viz — IR factsheet integration (gathering side; parser body in `TODO_parser.md` F18)

- [ ] `data/ir/<period>/parsed/<KR>.json` 도착 후 disclosed_csm_multiple.json + nb_premium_wolnap.json + segment_insurance_income 통합 ⚠️ **2026-08-20 실측: 1년째 미도착** — `data/ir/**/parsed/`에 파일 1개뿐(KR0087 동양생명 FY2026_Q2). 9사 cohort 미도착. 재개하려면 IR 파서 레인 별도 발주 필요.
- [ ] DART↔IR cross-source 룰 validation pass 확인 → 통합 어셈블 진행

### ~~INDEX-IFRS17-BUBBLE / INDEX-BUBBLE-V2~~ — 완결됨 (2026-06-14)

CSM bubble map은 main에 라이브로 **완결**. 실제 축 매핑(index.html ECharts): **X=신계약 CSM 규모(로그), Y=NB CSM 배수, 크기=기말 CSM 잔액**. 4축 V2 재설계는 **폐기(불필요)** — 3개 인코딩이 최종 디자인. (빌더 주석은 JSON 필드 설명일 뿐 축≠필드.) Done 표 참조.

### MISC-IR-NB-DENOM — NB CSM ratio assembly (validation V2는 separate)

In-progress. **Waterfall:** `validate_csm_waterfall.py` 23/23 pass. **NB mult:** 5/6 IR cohort pass. Loop: `run_ifrs17_csm_reconcile_loop.py`. Validation 측 잔여 → `TODO_validation.md` V2.

Publishing 측면: validation pass 후 nb_csm_multiple.json + bubble JSON 갱신.

### MISC-IR-PROTOTYPE — viz prototype assembly

In-progress. CSM Waterfall 23/23 ok. NB CSM ratio IR 6-co. index.html bubble: `viz_build_csm_bubble.py`.

- [ ] 6-co IR cohort 외 cohort 확장 (`build_ir_disclosed_multiples.py` 9사 도착) ⚠️ **2026-08-20 실측: 1년째 미도착** — `data/ir/**/parsed/`에 파일 1개뿐(KR0087 동양생명 FY2026_Q2). 9사 cohort 미도착. 재개하려면 IR 파서 레인 별도 발주 필요.

### ~~IFRS17-CSM-BUBBLE~~ — 완결됨 (2026-06-14)

INDEX-IFRS17-BUBBLE 과 동일 pipeline. Waterfall validation 23/23. 버블맵 라이브 완결로 흡수됨. Done 표 참조.

---

## 📦 Done — recent (publishing-scoped)

| ID | Task | Done | Notes |
|----|------|------|-------|
| ~~KICS-TIER1-UTIL~~ | tier1 hybrid utilization 2025.4Q assembly | done | SCR×15% strict 10%; 35/38 valid; `output/tier1_utilization/`; `templates/tier1_utilization_latest.json` |
| ~~KICS-TIER2-UTIL~~ | tier2 utilization 2025.4Q assembly | done | KIRI PDF reconcile; 34/38 in 0-100%; `output/tier2_utilization/`; `templates/tier2_utilization_latest.json` |
| ~~KICS-FORWARD-CAPITAL~~ | Forward solvency simulation in K-ICS.html | done v3 | v3 confidence uses `subordinated_eok`. Latest `20260525T061947Z/forward_simulation_v3.json` + inline `window.FORWARD_DATA` |

> ⚠️ **위 3행의 경로 표기는 2026-07-22 이후 옛것이다** (완료 기록이라 행 자체는 보존).
> 현재 배포본은 루트 `kics_tier1_utilization.json` · `kics_tier2_utilization.json` ·
> `kics_forward_capital.json`이고, K-ICS.html은 이걸 **fetch**한다 — `window.FORWARD_DATA`
> 인라인도, `templates/*_latest.json`도 더는 배포 경로가 아니다(후자 2개는 삭제됨).
> 정본 표 = `docs/agents/claude-agent-publishing.md` §1(재도출 명령 포함).
| ~~IFRS17-HTML-DASH~~ | IFRS17.html 6-panel dashboard data wiring | done | Per-panel JSON contract finalized; designer owns HTML structure |
| ~~F17-T1-PANEL3~~ | Panel 3 클린 4-bar 당기순이익 분해 (data side) | 2026-05-30 | `data/dart/viz/net_income_breakdown.json`; designer swapped Panel 3 layout |
| ~~F5~~ | No-bond insurer forward sim 추가 | done | 24 → 37 cohort. KR0008 삼성화재 263%→263% flat. 13 no_bond insurer 추가 |
| ~~F6~~ | CSM 상각 schedule yearly granularity (data side) | 2026-05-28 | `extract_amort_schedule` emits yearly y1..y10 + y10plus + granularity. 16 yearly / 6 coarse / 2 no-data |
| ~~F1~~ | index.html → IFRS17 cross-nav data hook | done | `fcdd544`. ECharts on('click') → URL param |
| ~~INDEX-BUBBLE~~ | index.html CSM bubble map | 2026-06-14 | Live on main. 축: X=신계약CSM(로그)·Y=NB배수·크기=기말CSM. `viz_build_csm_bubble.py`+`csm_bubble.json`. 코리안리 배수 N/A=회색. 4축 V2 재설계 폐기(불필요) |

---

## Reading order for publishing subagent

1. This file (`TODO_publishing.md`) — current state
2. [`docs/agents/claude-agent-publishing.md`](docs/agents/claude-agent-publishing.md) — master prompt
3. Validation report (from validation stage) — must be `next_action: pass` before assembling
4. Root [`TODO.md`](TODO.md) for cross-stage dependencies

Deferred (2026-07-27): [`docs/changelog_publishing.md`](docs/changelog_publishing.md) is history — open it only when you need the background of a past decision; most sessions don't (현황은 위 1번, 상세는 git log).

---

## Hand-off

- **From validation**: validation report with `next_action: pass`. RED=0 across all relevant domains.
- **To designer**: master JSON paths that changed + schema delta if any new fields. Designer decides HTML changes.
- **To human**: suggested `git add` + `git commit -m "..."` + `git push origin main` commands. Human runs them.
