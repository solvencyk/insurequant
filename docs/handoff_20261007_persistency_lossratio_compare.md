# 인수인계 — 유지율·손해율 신규 도메인 + 사별 비교 기능 (2026-10-07 10:10 기준)

owner 팀장 요청 3건. 홈페이지 표시는 아직 미정이고, 지금은 **추출 단계**다. 다음 세션은 이 파일 → 아래 티켓 3개 순서로 읽는다.

## 1. 요청

1. **회사별 유지율** — 정기경영공시 `7-6` 표의 판매채널별 13·25·37·61회차 유지율. 채널 구분은 회사 간 표준화.
2. **회사별 손해율 추이** — owner 지정 원천은 「위험보험료 대비 예상보험금」 표(DART 에도 있으나 열이 뭉쳐 있어 경영공시 PDF 로).
3. **사별 비교 기능** — 2~4개 회사를 어떻게 나란히 보여줄지(§5).

## 2. 작업 명세 = inbox 티켓 3개 (정본)

| 티켓 | 내용 | 산출 |
|---|---|---|
| `inbox/parser/20261007T0600Z__orchestrator__MULTI_2023.2Q-2026.2Q__persistency_by_channel.md` | 채널별 유지율 텍스트 추출 | `scripts/extract_persistency_channel.py` → `data/persistency/persistency_channel.json` + `census.csv` |
| `inbox/parser/20261007T0600Z__orchestrator__MULTI_2024.4Q-2025.4Q__claims_vs_risk_premium.md` | 손해율 표 A·B·C 텍스트 추출 | `scripts/extract_loss_ratio.py` → `data/loss_ratio/{claims_ae_ratio,risk_premium_vs_expected_claims,combined_ratio_nonlife}.json` + `census.csv` |
| `inbox/parser/20261007T0700Z__orchestrator__MULTI_2023.2Q-2026.2Q__persistency_lossratio_scanned_vision.md` | 스캔본 렌더 + 눈으로 판독(V1 생보 4사, V2 AIA·흥국화재·카카오페이·KB) | `data/persistency/vision_cells_v{1,2}.json`, `data/loss_ratio/vision_cells_v2.json`, `vision_census_v{1,2}.csv` |

발주 후 추가 지시(에이전트에 메시지로 보냄 — 티켓에는 없음):
- 추출기는 `vision_cells*.json` 을 **glob 으로** 전부 병합한다(V1·V2 파일 분리).
- 손해율: 본문(~p20~45)이 스캔이고 뒤쪽 사본에 텍스트가 있으면(KR0071 2024.4Q p214·385, KR0079 2024.4Q p315·316 / 2025.4Q p320·321, KR0097 2024.4Q p262·263) **뒤쪽 사본으로 추출 = FILLED(text)**.
- vision 행 스키마는 스캔 티켓 「산출」 절 그대로.

## 3-03. 진행 상태 (10-08 10:35 실측, 세션 `10fdb815…` — **이게 최신**)

**끝난 것 (다시 하지 말 것)**
- 유지율: `data/persistency/master_persistency.{json,csv}` 10,312행 37사. 추출·검증 지적·vision 티켓 전부 `inbox/_resolved/`.
- 손해율: `data/loss_ratio/master_loss_ratio.{json,csv}` 36,344행 37사(KR0079 `1~10년` 포함). 손해율 티켓 resolved. **Opus 검증(VL)은 owner 가 취소** — 다시 띄우지 말 것.
- 마스터 xlsx `insurequant_master_tables.xlsx` 의 `유지율`·`손해율` 시트(owner 가 손으로 추가) sync 완료·마스터와 완전 일치·요약 행 추가. `build_master_xlsx.MASTERS` 등재 + FLATTEN 이 출처·추출방식·플래그(손해율은 원문구분·원문포트폴리오도) 제외. Excel 이 숫자로 바꾼 티커는 문자로 복원. owner 원본 백업 = `…/10fdb815…/scratchpad/insurequant_master_tables.owner_20261008_0911.xlsx`.
- 사이트 설계 확정 = §5-2. **owner 라이브 배포 GO(10-08)**. **10분 전체 prepush 훅은 생략**(owner 결정, 메모리 `feedback_skip_full_hook_for_new_tables`).

**도는 것**: designer(Sonnet, `…/10fdb815…/subagents/agent-a06269af817d8ee2b.jsonl`, 10:33 살아 있음). 이미 디스크에 `scripts/viz_build_persistency_lossratio_panels.py`(09:55)·`IFRS17.html` 수정(10:03). 약속한 산출 = 패널 JSON 2개(경로는 designer 가 IFRS17 패널 관례로 정함)·섹션 8·9·`tests/test_push_gate_wiring.py` 의 PANEL_DERIVED_FROM 처리·스크린샷 `…/10fdb815…/scratchpad/designer/`·`TODO_designer.md` Status.
- 발주 프롬프트 전문 = `…/10fdb815…/scratchpad/designer_prompt_20261008.md`. **다른 세션에서는 이 에이전트를 SendMessage 로 못 깨운다** — 죽었으면 그 프롬프트에 "디스크 상태 먼저 확인하고 남은 것만" 을 붙여 designer 를 새로 띄운다.

**10:42 owner 지시로 designer 일시정지(TaskStop).** 멈춘 시점 디스크 상태:
- 됨: 빌더 `scripts/viz_build_persistency_lossratio_panels.py`(09:55) → 패널 `data/loss_ratio/panel_loss_ratio.json`(286KB)·`data/persistency/panel_persistency.json`(423KB)(09:56). `IFRS17.html` 섹션 8·9 추가(+286줄, 10:03, 두 패널을 fetch). 스크린샷 KR0009·KR0068·KR0150·KR1000 데스크톱/모바일(`…/scratchpad/designer/*.png`, 마지막 10:41).
- 멈출 때 하던 일: JS 블록을 Write 로 고치려던 참("Nothing was written") — 마지막 HTML 수정(10:03) 이후 스크린샷 검증 중이었다. 무엇을 고치려 했는지는 미상이니 스크린샷부터 직접 본다.
- 안 됨: `tests/test_push_gate_wiring.py` PANEL_DERIVED_FROM 처리(diff 없음) · `test_deploy_assets`/`test_push_gate_wiring` 실행 결과 · `TODO_designer.md` Status · KR0079 화면 확인.
- 재개 = designer 새로 띄우기: `scratchpad/designer_prompt_20261008.md` + "위 상태에서 이어서: 스크린샷 검토 → 남은 버그 수정 → PANEL_DERIVED_FROM → 테스트 2종 → TODO_designer Status".

**다음 순서 (이어받는 세션)**
1. designer 완료 확인: 보고의 파일 목록·테스트 결과·스크린샷을 직접 본다(`test_deploy_assets.py`·`test_push_gate_wiring.py` 를 내가 한 번 더 돌림).
2. publishing(Sonnet) 발주 — 커밋·배포:
   - 작업 브랜치 `fix/csm-product-segmented-columns` 에 **이 도메인 파일만** 커밋: `scripts/{extract_persistency_channel,build_persistency_master,triage_persistency_company_sum,extract_loss_ratio,build_loss_ratio_master,viz_build_persistency_lossratio_panels,build_master_xlsx,sync_master_xlsx_sheet}.py`·`scripts/_probes/probe_20261007_new_tables_census.py`·`data/persistency/`·`data/loss_ratio/`(**`risk_premium_vs_expected_claims.json` 80MB 는 제외** — GitHub 50MB 경고/100MB 한도)·패널 JSON 2개·`IFRS17.html`·`insurequant_master_tables.xlsx`·바뀐 tests·`docs/handoff_20261007_*`·`data/_derived/{validation_20261007_persistency.md,new_tables_census_20261007.csv}`·`inbox/_resolved/2026100*`·열린 inbox 티켓 3개.
   - **커밋 금지**: `TODO.md`·`TODO_validation.md`·`docs/changelog_validation.md`·`docs/todo_archive_validation.md`(세션 시작 전부터 있던 다른 세션의 미커밋분), 루트의 owner 개인 파일(pptx·docx·`*.md` 발표 자료).
   - 검사: 빠른 테스트 3종(`tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`scripts/check_master_xlsx_drift.py`)만. 작업 브랜치 push 는 `--no-verify` + 커밋 메시지에 "신규 테이블, RED 룰 미합의 — owner 지시로 전체 훅 생략".
   - main: 격리 워크트리(origin/main)에 `IFRS17.html` + 패널 JSON 2개(신규 파일 — android 스크립트는 신규 파일을 빠뜨리니 PC 에서 push) cherry → push → `public_exports/manifest.json` build_id 로 라이브 확인. 절차 = `.claude/skills/launch-runbook`.
3. 라이브 확인 후 owner 에게 2~5줄 보고(존댓말).

**안 급한 열린 것**: MI 열밀림 티켓 2개(`inbox/parser/20261007T1300Z…`·`…T1001Z…mi_persistency_shift_addendum.md`) · KR0075 2024.2Q 재다운로드(`inbox/downloader/20261007T1400Z…`) · 사별 비교 기능(owner 지표 목록 대기) · 이 도메인 TODO·changelog 기록(cross-stage = 루트 `TODO.md` + `docs/claude-changelog.md`). **KR0150 서울보증 결측은 찾지 말 것**(메모리).

## 3-02. 진행 상태 (17:55 실측, 세션 `10fdb815…`)

- run `wf_ccc4f5ad-b34` 는 16:33 사용 한도로 다시 죽었다(그 세션은 20시 리셋). 끝난 것: **V5 완료**(`vision_cells_v5.json`·`data/persistency/vision_census_v5.csv`, KB 2026.2Q 표 C FILLED, 나머지 9칸 ABSENT, AIA 2024.4Q <2023> 블록은 원문에 "전년 수치 생략" → 공시분기 2023.4Q 원천 없음).
- **유지율 끝**: P3 의 마지막 전체 실행(16:39)을 기준으로 오케스트레이터가 `build_persistency_master.py`·`triage_persistency_company_sum.py` 재실행 → 마스터 10,312행 1:1 검산 통과, triage 87칸(SOURCE 53·DEFINITION 26·MI_COLUMN_SHIFT 8). 유지율 티켓 `status: answered`(「P3 최종」 블록).
- L4 는 패치 10개(16:32, 저장소 스크립트 직접 수정)까지 했고 산출 JSON 은 15:21 그대로다. 회귀(`0224558f…/scratchpad/l4/tB.py`) 표 B 블록: 2024.4Q PDF OK 29·FAIL 13, 2025.4Q PDF OK 54·FAIL 11(시작 때 26/14·45/18).
  남은 FAIL 24블록: KR0002<2024> · KR0003<2023>·<2024> · KR0032<2025> · KR0050 3블록 · KR0051 3블록 · KR0068<2024>(2024.4Q) · KR0069<2024> · KR0070 2블록 · KR0087<2023>·<2025> · KR0094 2블록 · KR1000 3블록(+가짜 `2019` 블록) · KR1098 2블록(비율 단위 소수).
  V5 가 남긴 추출기 버그: `assemble()` 2023.4Q 분기가 vision census 를 안 읽어 KR0079 2023.4Q 표 A·B 가 SCAN_PENDING 으로 남는다.
- 17:55 이 세션에서 재발주(Agent 백그라운드): **L5**(Sonnet, L4 이어받기 → 손해율 티켓 answered) ∥ **VP**(Opus, 유지율 검증 → `data/_derived/validation_20261007_persistency.md`). L5 가 끝나면 LM(Sonnet) → VL(Opus). 프롬프트 원문은 위 `…finish-wf_67046f3c-5f5.js` 의 L4·VP·LM·VL 에 "이어받기" 단락만 붙인 것.
  생존 판정 = `~/.claude/projects/…/10fdb815-4dd2-4690-8424-bc804fb0ff06/subagents/agent-a9a3414981b9f4949.jsonl`(L5)·`agent-a98a9f75f09e07692.jsonl`(VP) mtime + L5 스크래치 `10fdb815…/scratchpad/l5/` + 손해율 티켓 「L5 최종」·`data/_derived/validation_20261007_persistency.md`.
- 19:10 **VP 완료 = RED 1 · YELLOW 8**(보고서 `data/_derived/validation_20261007_persistency.md`). 유지율 숫자 오독·열 밀림 0, 마스터 1:1. RED-1 = KR0004 예별 2026.2Q 금액 44행이 원문 머리 "백만원"인데 1/1000 규모(무플래그).
  티켓: parser `20261007T1001Z__validation__…persistency_validation_findings.md`(RED-1·YELLOW-2·4·6·8) · parser `…mi_persistency_shift_addendum.md`(루트 management_indicators 오적재 2칸, T1300Z 와 함께 처리) · downloader `20261007T1001Z__validation__KR0150_…missing_halfyear_disclosure.md`.
  → 19:12 **P4**(Sonnet, `agent-ac36fced2d5e1c648.jsonl`, 스크래치 `10fdb815…/scratchpad/p4/`) 발주 = findings 티켓 처리(인쇄값 유지 + 단위오기 플래그·규모 검사 selfcheck) → 전체 재실행 → 티켓 answered. L5 는 18:35 기준 표 B FAIL 10블록까지 줄임(진행 중).
- 19:1x L5·P4 가 사용 한도로 죽음(22:40 리셋). 22:42 **SendMessage 로 같은 에이전트를 맥락째 재개**(새로 띄우지 않음 — 다시 읽는 비용 절약). L5 엔 "블록당 30분 넘기면 인쇄 그대로 + 플래그로 닫고 마무리" 지시.
  22:45 **LM**(Sonnet, `agent-a1a5cc075244e4b9b.jsonl`, 스크래치 `scratchpad/lm/`)을 L5 와 병렬로 발주 — 추출기는 안 건드리고 현재 산출로 변환기 `scripts/build_loss_ratio_master.py` 를 만든다. **L5 가 끝나면 오케스트레이터가 변환기를 다시 돌려야 한다.** 그다음 VL(Opus).
  KR0150 서울보증 재수집 티켓(검증이 발행)은 owner 지시로 즉시 resolved — 지난 분기공시는 회사 사이트에서 내림, NO_RAW_PDF 최종.
- 23:2x **P4 완료·검증·종결**: 유지율 마스터 10,312행 1:1 통과, 플래그 실측(단위오기추정 44·금액기준상이 108·대상신계약액=0 760·오기 추정 64)이 보고와 일치 → findings 티켓 + 유지율 추출 티켓 둘 다 `_resolved/` 로 이동. **유지율 도메인은 끝.**
  L5·LM 은 23:28 에도 jsonl 갱신 중(살아 있음). LM 이 1차 마스터(`master_loss_ratio.*`·`portfolio_taxonomy.csv`·`period_adoption.csv`·`master_census.csv`, 23:22)를 이미 냈다. 남은 순서: L5 최종 → 변환기 재실행(+ `--verify-only` 같은 기계 검산만) → vision 티켓(0700Z)·손해율 티켓 종결 → owner 에게 결과물 전달.
  10-08 03:40 이전에 L5·LM 이 또 사용 한도로 죽음(L5 = 표 B 회귀 FAIL 0 달성 뒤 diffs 패치 중, LM = 1차 마스터 23:47 산출 뒤). 08:5x 둘 다 SendMessage 로 재개 — L5 는 남은 3건 각 20분 상한 후 전체 실행·「L5 최종」, LM 은 `--verify-only` 마무리·「LM 마스터 변환」.
  09:0x **L5 최종**(표 A/B/C census PARSE_FAILED 0, 블록 회귀 42/42·66/66, 원문오기 4칸 등재)·**LM 완료**(마스터 36,092행 36사, `--verify-only` 통과 — 오케스트레이터 재확인, CSV utf-8-sig). vision 티켓 0700Z resolved.
  남은 1건: KR0079 미래에셋생명 표 B 가 뒤쪽 텍스트 사본(2024.4Q p316-317·2025.4Q p321, `당기` 캡션·`1~10년` 합산열)에 있는데 ABSENT → 09:1x L5 재개(30분 상한, `1~10년` 인쇄 그대로). 끝나면 변환기 재실행 → 손해율 티켓 resolved → 결과물 재전달.
  09:1x **owner 가 `insurequant_master_tables.xlsx` 에 `유지율`·`손해율` 시트를 손으로 추가**(출처·추출방식·플래그 열 삭제) → "작업 끝나면 이걸 업데이트". 조치: `build_master_xlsx.MASTERS` 에 두 시트 등재 + FLATTEN `_drop_provenance`(시트에서만 세 열 제외, JSON 엔 남음) + NUMERIC/TEXT_COLS 추가, `sync_master_xlsx_sheet.py` 가 요약에 행 없는 손수 시트도 저장하게 1줄 보정. Excel 이 숫자로 바꾼 티커(000060→60) 12,596칸을 문자로 복원(일회성 스크래치 스크립트, 원본 백업 `scratchpad/insurequant_master_tables.owner_20261008_0911.xlsx`). **유지율 시트 sync 완료**(10,312행 완전 일치·요약 행 추가). 손해율 시트는 KR0079 반영 + 변환기 재실행 후 `sync_master_xlsx_sheet.py "손해율"`.
  10:0x **KR0079 반영 완료 → 손해율 마스터 36,344행 37사, 손해율 티켓 resolved. xlsx `손해율` 시트 sync 완료**(owner 지시로 `원문구분`·`원문포트폴리오` 열도 시트에서 뺌 — 빼도 행 키 중복 0, JSON 엔 남음). **유지율·손해율 추출·마스터·xlsx 전부 끝.** 남은 건 사이트 게시(아래 §5-2).
  **23:3x owner 결정: VL(Opus 손해율 검증) 발주 취소.** 제대로 된 검증은 owner 가 나중에 따로 한다 — 지금은 시간·토큰만 먹는다. 추출기·변환기의 기계 검산(항등식·census·1:1)만 돌리고 넘긴다.

## 3-01. 진행 상태 (15:10 실측, 세션 `0224558f…`)

- 세션 `10fdb815…` 의 L3·P2 는 13:57 사용 한도로 둘 다 죽었다(15:00 새 5시간 창 시작, 6% 사용). 디스크에 남은 것:
  - L3: `data/loss_ratio/` 산출 4종 + `census.csv`·`diffs.csv`·`pdf_survey.csv`(13:51). 스크립트는 13:53 패치 2 반영(그 뒤 재실행 안 됨). 스크래치 도구 = `10fdb815…/scratchpad/l3/`(dbgB·dbgB2·tB·core 조립).
    13:51 census 표 B(2024.4Q·2025.4Q): FILLED 65 · vision 7 · **FILLED_CHECK_FLAGS 37 · PARSE_FAILED 10**(KR0099·KR1011 전 블록, KR0082·KR0087 <2023>, KR0003 2025) · SCAN_PENDING 1(KR0080 2024.4Q <2023>).
    실패 유형: 현재가치·합계 열 숫자 붙음(`11,381,05411,975,726`), 라벨 붙음(`무배당재물Non`), 합계≠Σ. 표 C 는 KR1059 2025.1Q PARSE_FAILED, KB 홀수분기 스캔 SCAN_PENDING.
  - P2: 추출기 패치(RAW_TRUNCATED·V1 identity 어휘 정규화·오기 등재부 읽기) + `data/persistency/source_errata.csv` 16행(13:57). 전체 재실행·`company_sum_triage.csv`·KR0074 2023.2Q·티켓 답변은 안 됨.
- 15:15 재발주(Workflow, 작업 = Sonnet · 검증 = Opus): P3(유지율 마무리 + 마스터 변환기) · L4(표 B 실패 블록) · V5(손해율 스캔 잔여) → LM(손해율 공시분기 채택 + 표준 분류 + 마스터 변환기) → VP·VL(검증 opus).
  첫 run `wf_67046f3c-5f5` 는 15:26 세션 종료로 P3·L4·V5 가 아무것도 끝내지 못하고 죽었다(P3 는 15:17 전체 실행, L4 는 15:26 스크립트 패치까지 진행). → 15:33 같은 스크립트로 재실행 **run `wf_ccc4f5ad-b34`**(프롬프트에 "두 번째 시도, 스크래치·15:11 이후 변경분부터 이어서" 추가). 프롬프트 7개 원문 = `~/.claude/projects/C--Users-sangwook-cho-Desktop-insurequant/0224558f-086a-48cb-ae61-34c5d14d4e91/workflows/scripts/persistency-lossratio-finish-wf_67046f3c-5f5.js`,
  에이전트 기록 = 같은 세션 `subagents/workflows/wf_67046f3c-5f5/`. 흐름: P3 → VP / (L4 ∥ V5) → LM → VL.
  죽으면 판정 기준(산출 파일 존재 + 티켓 status):
  - P3 = `data/persistency/company_sum_triage.csv` + `master_persistency.{json,csv}` + 유지율 티켓 answered.
  - L4 = 손해율 티켓 answered + census 표 B 의 PARSE_FAILED·FILLED_CHECK_FLAGS 감소.
  - V5 = `data/loss_ratio/vision_cells_v5.json` + `data/persistency/vision_census_v5.csv`.
  - LM = `data/loss_ratio/{portfolio_taxonomy,period_adoption,master_census}.csv` + `master_loss_ratio.{json,csv}`.
  - VP·VL = `data/_derived/validation_20261007_{persistency,loss_ratio}.md`.
  같은 세션이면 스크립트를 고쳐 `resumeFromRunId` 로, 다른 세션이면 스크립트를 복사해 끝난 job 을 빼고 새로 돌린다.

## 3-00. 진행 상태 (13:05 실측, 세션 `10fdb815…`)

- 세션 `0224558f…` Workflow 는 11:25 **5시간 사용 한도**로 P·L·V2a·F 가 죽었다(V1·V2b 만 완료). 이 세션이 이어받았다.
- **끝난 것**: V2a 마지막 빌드(오케스트레이터 실행, KR0080 2025.4Q 표 A·B FILLED, 불일치 0) → 스캔 티켓 V2a 블록 + `status: answered`.
  유지율 추출기 버그 1줄 수정(`load_vision_rows` 의 dict 형 identity → 문자열 라벨) 후 전체 실행 → `data/persistency/persistency_channel.json` 10,192행 · `census.csv` 277칸(FILLED 235 · vision 16 · ABSENT 19 · NO_RAW_PDF 3 · SCAN_PENDING 4) · `selfcheck.csv`.
- **V4 완료(13:35)**: KR0010 2024.4Q(p98)·2026.2Q(p56-57) FILLED(vision), 불일치 0 → `vision_cells_v4.json`·`vision_census_v4.csv`, 스캔 티켓 V4 블록.
  KR0075 2024.2Q 는 원문 부재가 아니라 **raw 가 잘린 사본**(33쪽, 6-5 중간 끊김) → `inbox/downloader/20261007T1400Z__…truncated_disclosure_pdf.md`. census 상태는 `RAW_TRUNCATED` 로 내보내라고 P2 에 지시.
- **도는 중(14:00, 이 세션 백그라운드, Sonnet)** — 죽었으면 아래 범위대로 재발주(산출 파일·티켓 status 로 판정):
  - L3 = 손해율 추출기 완성. 시작 시 `scripts/extract_loss_ratio.py` 는 표 B 파서만 있고 표 A·C·main·census·출력이 없었다. 지시: end-to-end 먼저 닫고(출력 4개 파일 존재) 표 B 실패 회사를 줄인 뒤 티켓 answered.
    추가 지시: vision 경과기간 라벨을 canon_period 로 통일(최종 표기 `30년 이후`·`현재가치`), KR0010 2025.4Q <2024년> 블록 576칸(숫자출처=text-layer)은 vision 으로만 병합, "다른 기준연도인데 값 전부 같은 블록" 플래그.
    완료 판정 = `data/loss_ratio/{claims_ae_ratio,risk_premium_vs_expected_claims,combined_ratio_nonlife}.json` + `census.csv` + 손해율 티켓 answered.
  - P2 = 유지율 텍스트 마무리: KR0074 2023.2Q 옛 통합서식(p37~38, 대시 `ㅡ`, 열 「방카」) 파싱, 텍스트 항등식 break 16건 판정·수정, 회사합 |차|>0.5 87건 분류 → `data/persistency/company_sum_triage.csv`,
    KR0075 2024.2Q → `RAW_TRUNCATED`, V1 identity 라벨 `ok_precision`→`round`·`n/a`→`na` 정규화, 마지막 인자 없는 전체 실행, 유지율 티켓 answered.
- KB 2025.4Q 표 B 당기 블록: p45 이미지를 오케스트레이터가 직접 열어 42,472/44,676 인쇄를 확인했다(판독 오류 아님). owner: "가정을 안 바꿨거나 오류일 것" → 인쇄 그대로 + 플래그.
- **새로 발견**: 루트 `management_indicators.json` 의 KR0076 2024.4Q · KR0051 2025.2Q · KR1000 2023.4Q 1-2 표 행 전체가 밀려 있다(유지율 음수 등, `main` 에 없어 라이브 무관) → `inbox/parser/20261007T1300Z__…management_indicators_column_shift.md`.
- 원문 특이점: KB손해 2025.4Q 공시의 **당기 <2025년> 블록**(p45, 이미지)이 같은 공시 전기 <2024년> 블록(p46, 텍스트)·2024.4Q 공시 <2024년>(p38)과 숫자가 같다(합계 1년 42,472/44,676 등). 전기 블록끼리 같은 건 정상(§5-1). 이상한 건 당기 블록이다 — 같은 쪽 표 A 는 2025 94.50/96.90 · 2024 94.60/88.30 으로 다르다.
  기본 처리 = 인쇄 그대로 + 플래그. DART 2025 사업보고서 같은 표로 대조 예정.
- 그다음: 세 에이전트 끝나면 유지율 추출기 재실행(v4 병합) → 티켓 3개 검증·resolved → validation(opus) → §5-1 양식 변환.

## 3-0. 진행 상태 (11:15 실측, 세션 `0224558f…`)

- 10:13 `/clear` 로 세션 `10fdb815…` 의 에이전트 4개가 전부 죽었다 → 세션 `0224558f…` 가 Workflow `wf_ec1fff1f-c4b`(전부 Sonnet, 동시 ≤4)로 재발주.
  - 프롬프트 6개(P·L·V1·V2a·V2b·F) 원문 = `~/.claude/projects/C--Users-sangwook-cho-Desktop-insurequant/0224558f-086a-48cb-ae61-34c5d14d4e91/workflows/scripts/persistency-lossratio-resume-wf_ec1fff1f-c4b.js`.
    세션이 또 죽으면 이 파일을 복사해 `JOBS` 에서 끝난 것만 빼고 새 Workflow 로 돌린다(resume 은 같은 세션에서만 됨).
  - 에이전트 jsonl: `…/0224558f…/subagents/workflows/wf_ec1fff1f-c4b/agent-*.jsonl`, 결과는 같은 폴더 `journal.jsonl`. 스크래치 = `%TEMP%/claude/…/0224558f…/scratchpad/{p,l,v1,v2a,v2b,f}`.
- **V2 를 둘로 나눴다**: V2a = KR0080(+끝난 KR1098) → `vision_*_v2`, V2b = KR0005·KR0010 → `vision_cells_v3.json`(유지율·손해율 각각)·`vision_census_v3.csv`. 추출기는 `vision_cells*.json`·`vision_census_v*.csv` 를 glob 병합.
- 11:15 상태:
  - V1 **완료**: 11칸 전부 FILLED(`vision_census_v1.csv`).
  - V2b: 대상 칸 전부 FILLED(KR0005 표 B 전년블록 2023 은 ABSENT_IN_SOURCE). 에이전트가 답변 쓰는 중일 수 있음.
  - V2a: KR0080 유지율 3개 분기 FILLED, KR1098 끝. **KR0080 2024.4Q·2025.4Q 표 A·B 진행 중**.
  - L: `scripts/extract_loss_ratio.py` 생김(11:13), 산출 JSON·census 아직. P: `scripts/extract_persistency_channel.py` 아직 없음(scratchpad/p 에서 시험 실행 중, run4.txt).
  - F(정리: 추출기 재실행 병합·티켓 status·TODO/changelog): 아직 시작 전. 티켓 3개 모두 `status: open`.
- 완료 판정은 아래 3. 과 같다 + `vision_census_v3.csv` 포함. 그다음은 §5-1 양식 변환 → §6.

## 3. 진행 상태 (10:06 실측)

- parser-kics 에이전트 4개가 이 세션(`10fdb815…`) 백그라운드에서 돌고 있었다: 유지율 텍스트 · 손해율 텍스트 · V1 · V2.
  **세션이 끊기면 같이 죽는다.** 살아 있는지는 `~/.claude/projects/C--Users-sangwook-cho-Desktop-insurequant/<세션>/subagents/agent-*.jsonl` mtime(10분 넘게 정지 = 죽음) + 아래 산출 파일로 판정.
- 디스크에 있던 것: `data/persistency/vision_cells_v1.json`·`vision_census_v1.csv`(흥국생명 2024.4Q·미래에셋 2023.2Q FILLED), `data/loss_ratio/` 폴더 생성.
  추출기 스크립트 2개는 아직 없었다(에이전트 프로토타입은 세션 scratchpad `lr_*.py`·`p0*.py` 에 있음 — 다른 세션에서도 경로로 읽을 수는 있다).
- **완료 판정**: 티켓 3개 `status: answered` + `## 답변` 작성 + 위 산출 파일 전부 존재. 하나라도 빠졌으면 그 티켓만 같은 프롬프트로 재발주
  (vision 은 회사·분기 단위로 디스크에 저장하므로 `vision_census_v*.csv` 의 FILLED 칸은 건너뛰라고 지시).
- 커밋은 아직 안 했다. 새 파일은 전부 미추적(`data/persistency/`, `data/loss_ratio/`, 티켓 3개, 이 파일, census 사본).

## 4. 오케스트레이터 census 결과 (재조사 불필요)

원본: `data/_derived/new_tables_census_20261007.csv` (스크립트 `scripts/_probes/probe_20261007_new_tables_census.py`, 549개 PDF, 출력은 스크립트 옆에 생김).

- **유지율 채널표(7-6)·손보 합산비율 표는 2Q·4Q 공시에만 있다.** 1Q·3Q 분기공시는 축약본이라 없다. 7개 분기 × 약 39사.
- **손해율 표 A(보험금 예실차비율: 예상·실제 손해율 2개년)·B(위험보험료 대비 예상보험금: 포트폴리오 × 경과 1~30년+)는 2024.4Q·2025.4Q 결산본에만 있다.**
  B 는 과거 실적이 아니라 **미래 전망**이다. 실적 추이에 가까운 건 A(2개년)와 손보 표 C.
- 회사 단위 13~85회차 유지율(1-2 표)은 이미 루트 `management_indicators.json`(`계약유지율_13회차` 등, 약 228행)에 있다 — 채널 합 대조용.
- 채널 11개(협회 표준): 설계사 · 개인대리점 · 법인대리점{금융기관 · TM · 홈쇼핑 · 기타} · 직영{임직원 · 복합 · 다이렉트} · 중개사 · 기타.
  옛 서식 예외: 미래에셋 2023.2Q 는 8열(임직원·중개사·기타 없음) + 유지율 정수 인쇄(항등식 정밀도 미달은 정상).
- 스캔본(2Q·4Q): KR0079 7개 분기 전부, KR0097 2024.2Q·4Q, KR1098 2024.2Q·4Q, KR0005 2024.4Q, KR0071 2024.4Q(일부), KR0080 2024.4Q·2025.2Q·2025.4Q, KR0010 2025.4Q, KR0087 2026.2Q.
  KR0010 2026.2Q 는 raw 가 Print-To-PDF 0글자 사본이지만 docling MD 에 텍스트가 있다.
- 텍스트는 있는데 채널표가 안 잡힌 곳(ABSENT 후보, 근거 확인 필요): 코리안리 KR1000(재보험) · 서울보증 KR0150 · 캐롯 KR1059 · 카카오페이 KR1098 · BNP카디프 KR0075 2024.2Q.
- 같은 (회사, 분기) 중복 파일: KR0011 2025.3Q(`_amended2`) 1건뿐.

## 5. 사별 비교 기능 — 논의 상태 (결정 대기)

FnGuide 경쟁사비교(`wcomp.fnguide.com/CompanyInfo/Comparison`) 실측: 대상 회사 + FnGuide 가 고른 경쟁사 3곳 = **4곳 고정**(사용자 변경 불가).
위쪽에 지표 하나당 차트 하나(2×2, 회사는 색으로 구분), 아래쪽에 행 = 지표 · 열 = 회사 표. 1920 에서도 가운데 ~1,000px 만 쓴다.

오케스트레이터 추천(owner 에게 제시함, **답 대기**):
- 회사별 화면을 나란히 놓지 말고 **지표 하나 = 차트 하나, 회사 = 색 구분 겹침**. 같은 축이어야 비교가 정확하다.
- 화면 크기는 회사 수가 아니라 **차트 카드 열 수**로 흡수(와이드 3열 · 1080 2열 · 모바일 1열, CSS grid). 비교 회사는 최대 4곳.
- 회사 선택 칩 최대 4개(기본 = 보던 회사 + 같은 생/손보 규모 비슷한 3사), 회사별 색 고정, 회사 목록을 URL 에 넣어 공유.
  맨 위 요약표(행 = 지표, 열 = 회사, 모바일은 첫 열 고정 가로 스크롤) + 아래 추이 차트. 업계 중앙값 점선 추가 권장.
- **다음 행동**: owner 가 비교할 핵심 지표 목록을 주면 목업부터(designer). 후보: 지급여력비율·기본자본비율·CSM·보험손익·ROE·13회차 유지율·손해율.

## 5-1. owner 결정 — 마스터 양식 (2026-10-07 11시경, 채팅)

- **팀장 요청의 「손해율」 = 표 B(위험보험료 대비 예상보험금, 미래 손해율 가정) 그 자체**가 맞다. 마스터 본체는 표 B. 표 A·C 는 추출 원본(`data/loss_ratio/`)으로만 둔다.
- **추출 원본 JSON(long, 출처 포함)은 그대로 두고, 마스터는 아래 양식으로 변환해 넣는다**(xlsx 시트 + 루트 마스터).
- 유지율 마스터 열: `원보험사코드 · 원수사명 · 티커 · 생손보여부 · 공시분기 · 회차구분("13회차") · 채널대분류 · 채널소분류 · 대상신계약액 · 유지계약액 · 유지율`.
  채널 표준코드 `법인대리점_금융기관` → 대분류 `법인대리점` / 소분류 `금융기관보험대리점`. 소분류 없는 채널(설계사·개인대리점·중개사·기타)은 소분류 공란.
- 손해율 마스터 열(owner 안 + 보강): `원보험사코드 · 원수사명 · 티커 · 생손보여부 · 공시분기 · 경과차년 · 구분 · 상품구분 · 포트폴리오 · 위험보험료 · 예상보험금 · 손해율`.
  - 포트폴리오 분류는 오케스트레이터 재량으로 세분화하되 **39사 전체에 같은 기준**(원문 라벨 census → 표준 3단: 구분 Non-Par/Direct-Par/Indirect-Par/합계 · 상품구분 유배당/무배당/변액 등 · 포트폴리오 사망/건강/상해/질병/재물/연금저축… , 원문 라벨은 별도 보관).
  - 경과차년은 글자: `1년`~`10년`, `11~15년`, `16~20년`, `21~25년`, `26~30년`, `30년 이후`, `현재가치`.
  - 손해율 = 예상보험금 ÷ 위험보험료 × 100 재계산(원문 비율은 정수 반올림 인쇄).
  - 사이트 표시는 포트폴리오 합산 기준 = 원문 **합계 행** 사용(직접 합산 시 Σ예상보험금 ÷ Σ위험보험료, 비율 평균 금지).
- **시점 = `공시분기` 하나로 구분(기준연도 열 없음).** 결산 PDF 하나에 당기·전기 두 블록이 있다:
  - 공시분기 Y.4Q = Y.4Q PDF 의 `<Y년>` 블록(당기).
  - 단 (Y+1).4Q PDF 의 `<Y년>` 블록(전기)과 값이 다르면 정정공시로 보고 **(Y+1).4Q PDF 전기 블록을 채택**(채택 출처·사유는 원본 JSON/플래그에 남김).
  - (오케스트레이터 해석) Y.4Q PDF 에 표 자체가 없으면(2023.4Q 결산본) (Y+1).4Q PDF 전기 블록으로 채운다 → 2023.4Q·2024.4Q·2025.4Q 3개 시점.

## 5-2. 사이트 게시안 (2026-10-08 **owner 확정 + 라이브 배포 GO**)

- 10:1x designer(Sonnet, `agent-a06269af817d8ee2b.jsonl`, 스크래치 `scratchpad/designer/`) 발주: 패널 빌더 `scripts/viz_build_persistency_lossratio_panels.py` + 패널 JSON 2개 + IFRS17.html 섹션 8·9 + PANEL_DERIVED_FROM. 끝나면 publishing 에 커밋·main cherry-push·라이브 build_id 확인 발주 — **owner 결정(10:2x): 10분 전체 prepush 훅은 생략**(새 테이블, RED 룰 미합의). 빠른 테스트(`test_deploy_assets`·`test_push_gate_wiring`·xlsx drift)만 돌리고 작업 브랜치 push 는 `--no-verify` + 커밋 메시지에 사유(80MB `risk_premium_vs_expected_claims.json` 은 커밋 금지, owner 개인 파일 pptx·docx·md 와 다른 세션의 TODO·changelog 미커밋분은 제외).

- 위치: IFRS17.html 에 섹션 추가(8 손해율 가정, 9 유지율). 회사 선택은 페이지 공통 셀렉트.
- **손해율(확정)**: 공시시점 드롭다운 → 경과차년별 꺾은선(1~10년 + 5년 구간, 현재가치는 선에서 빼고 숫자 하나로) → **합계 선 + 전년 공시 합계 점선만**. 상품군별 선은 owner 가 "난잡" 이라 **넣지 않는다**. 아래 세부 테이블(행 = 구분·상품구분·포트폴리오, 열 = 경과차년 16칸, 첫 열 고정).
- **유지율(제안, owner 확인 대기)**: x = 13·25·37·61회차(실제 개월 간격, 49회차는 공시표에 없음) 감소 곡선, 선 = 채널 그룹 4개, 아래 채널 × 회차 히트맵 표(대상신계약액 0 → '-'). 섹션 제목에 "해지율 가정의 근거가 되는 실적".
  채널 그룹안(업계 통상 구분 = 전속·GA·방카·비대면, 그룹 유지율 = Σ유지계약액 ÷ Σ대상신계약액):
  전속설계사 ← 설계사 / GA(대리점) ← 개인대리점 + 법인대리점·기타 / 방카슈랑스 ← 법인대리점·금융기관보험대리점 /
  비대면 ← 법인대리점·TM + 법인대리점·홈쇼핑 + 직영·다이렉트 / 기타(표에만) ← 직영·임직원 + 직영·복합 + 중개사 + 기타.
  2025.4Q 13회차 대상신계약액 비중: GA 52.6% · 전속 27.7% · 방카 13.8% · 비대면 5.2% · 기타 0.7%.

## 6. 추출 이후 순서

1. validation(opus): 항등식(유지율 = 유지계약액 ÷ 대상신계약액, A−B, A÷B, 합산 = 손해율 + 사업비율) 전수 + 채널 합 ↔ `management_indicators.json` 대조 + vision 칸 표본 재판독.
2. owner 와 표시 방식 확정 — 마스터 양식·B 채택·시점 규칙은 §5-1 로 확정됨. 남은 결정은 §5 비교 기능 지표 목록.
   그 전에 parser: 표 B 구분·포트폴리오 원문 라벨 census → 39사 공통 표준 분류 + §5-1 공시분기 채택 로직 + 마스터 양식 변환기.
3. publishing: 루트 마스터 신설 + `public_exports` · keep-list. designer: 패널. push 는 owner GO.
