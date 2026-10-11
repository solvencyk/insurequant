---
from: orchestrator
to: validation
created: 20261011T1510Z
status: resolved
route: verify
company: MULTI
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
밤샘 스윕(owner 2026-10-11)의 **최종 검증 라운드**다. 이 시점 마스터는 확정(커밋 완료)이고 publishing 마감 라운드(`inbox/publishing/20261011T1200Z…`, xlsx·public_exports·viz 패널)가 끝난 뒤에 발사된다. 오늘 바뀐 것: 재보사 8곳 적재(K-ICS · CSM 계열 · PL · BS · ILP · Forward/자본성증권), BS +약 1,900칸·정정 70칸, PL +540·정정 53칸, ILP +2,390행 · 정정 12칸, K-ICS 신판 정정 98필드(예별 2025.4Q · 농협손보 2025.1Q · 교보 3개 분기), AXA 2024.3Q 완성본 +17행, KR1102 2023.2Q +86행 등. **push·배포는 owner 지시로 보류 중**이므로 이 티켓은 커밋까지만(풀 훅·push 는 오케스트레이터).

### 해 줄 것 (단계마다 디스크 저장, 런로그 `data/disclosure/_meta/final_validation_runlog_20261011.md` 맨 위 갱신)
1. **전체 게이트 현황**: `validate_data_contract.py` · `validate_kics_disclosure.py` · `validate_master_tables.py --no-build`(인자 없이·`--help` 단독 실행 금지) · 도메인 게이트 · LIC(발생사고요소) 검산기 · `validate_live_artifacts.py` 를 돌려 RED/YELLOW 를 분류: ① 고쳐야 하는 것(어느 stage 몫인지, 필요하면 inbox 발주) ② owner 결정 대기(보고만) ③ 증거로 등재 해제할 수 있는 것.
   - **publishing 마감 라운드(`8848cb8`…`f218170`) 후 상태**: `validate_data_contract` RED 22(알려진 것만) · `validate_live_artifacts` RED 26 = `NB_CENSUS_MISSING` 18(publishing 이 NB 배수 마스터 재보사 18행 추가로 해소 중, 완료 알림 뒤 발사) + **`INSPL_CENSUS_MISSING` 8**(보험손익 원표 viz `insurance_pl_breakdown.json` 은 DART 표 담는 파일이라 재보사 원표가 없고 만들 수 없다 — 화면은 이 파일을 쓰지 않음; 게이트 baseline/면제 필요 여부를 판단해 **후보로 보고만**, 등재 금지) · `test_viz_ifrs17_panels_golden` 실패(csm_amort_schedule 39→46사·sensitivity_heatmap 32→39사, 재보사 추가분뿐 — 확인 후 `--update`) · `validate_golden_input_fingerprints.py` RED 10(골든 `--update` 뒤 지문 갱신).
2. **등재 해제(증거 기반만)**: `KICS_CENSUS_EXEMPTION_INERT` KR1102 2023.2Q(`_CENSUS_SOURCE_ABSENT` 등재 — 이번에 +86행 적재로 소멸) · AXA 2024.3Q 부재 등재 · 교보 2026.1Q 재작성 연쇄 등재 해제(`data/_gold/kics_restatement_ledger.json` `_adoption_cascades` 19_market, 데이터계약 YELLOW `KICS_RESTATEMENT_CASCADE_INERT`) + 후 박제 `AFTER_IDENT_ISSUER_INCONSISTENT[("KR0073","2026.1Q","R5_기준금액")]` 정리 + KB손보 2025.4Q·2026.2Q 텍스트층 사이드카/비전 원장/KICS-IMG 허용오차(KR0010 tol 10) 갱신 여부 판단. 등재 해제는 해제해도 새 RED 가 생기지 않음을 시뮬레이션으로 먼저 보이고 적용(양방향 시뮬레이션 규칙). **새 예외 등재는 하지 않는다**(후보는 보고만).
3. **골든 갱신(`--update`, 이유를 커밋 메시지에 명시, 의도하지 않은 이동은 하지 말고 보고)**: `tests/test_kics_rules_golden.py`(룰 finding 이동 — 사이트 신판 5칸 정정·재보사·AXA) · `test_post_transition_golden`(추출 지문 이동) · `validate_golden_input_fingerprints.py --update`(전체 골든을 돌려 산출이 정말 안 움직였는지 확인한 뒤) · `test_master_tables_golden` · `test_ifrs17_bs_golden`(~8분) · PL 골든(`RUN_PL_GOLDEN=1`) · viz 골든 2종(`test_viz_ifrs17_panels_golden`·`test_viz_csm_waterfall_golden`; publishing 이 패널을 재빌드한 결과가 재보사 추가분뿐인지 먼저 확인, 빌더 산출은 인플레이스 덮어쓰기라 실행 전 백업) · 그 밖에 실패하는 골든. 17 failed(앞 K-ICS 티켓 기준 `test_rule_coverage_manifest` · xlsx 드리프트 묶음)가 publishing 동기화 후 해소됐는지 확인.
   - **추가(parser-kics `c391c1e` 후속)**: 신판 MD 5개가 옛 MD 옆에 병존해 `tests/test_post_transition_golden.py` 가 `*.md` 를 직접 글롭하며 이중 집계한다(셀 7,144 → 7,269). 테스트가 `scripts/_disclosure_pdf_paths.py::md_files_latest()` 를 쓰게 고친 뒤(테스트 코드 수정은 허용) 골든을 `--update` 한다. `*.md` 를 직접 글롭하는 다른 도구 목록은 `data/disclosure/_meta/kics_newer_editions_apply_runlog_20261011.md` §13.6 — 영향이 있으면 해당 stage 에 inbox 발주. `fill_period --refresh` 는 항목 48을 잘못 덮는 기존 결함이 있어 전 기간 `--refresh` 금지(보고만).
4. **오늘 적재분 거짓 녹색 사냥(검증 5대 사각)**: 재보사 8곳의 BS/PL/CSM/ILP/K-ICS 칸에서 항등식(자산=부채+자본, 보험손익 소계, 기초+변동=기말, ILP 합계, 연속성)·0값 맹점·하한 plausibility·누계/당분기 관계를 **셀 단위 전수**로 점검하고, 각 레인에서 무작위 표본 칸(회사·분기·항목 20개)을 원천 PDF/XML 과 대조. 틀린 칸은 고치지 말고 근거와 함께 해당 stage 에 inbox 발주.
5. **owner 결정 항목 정리(보고만, 등재 금지)**: `PL_CSM_AMORT_VS_WATERFALL` 17(`proposed_registry_entries.json`) · `PL_YTD_COLLAPSE_TO_ZERO` 3 · 하노버 2025.3Q PL `MASTER_HOLE` 1 · 스위스리 2023.4Q·하노버 2023.4Q/2024.1Q·RGA 2023.2Q·스위스리아시아 2023.3Q 직전 열 적재 RED · 퍼시픽 2025.3Q·2026.2Q 경과조치 0 대 공란 16칸 · 마이브라운 2025.3Q `TIER2_LIMIT_STALE` 오탐 · 뮌헨 2026.2Q 50·52 보류 · AXA 2024.3Q 4칸 상이 · KR0100 항목 20 정의와 ILP RED 5 · KR0029 2024.4Q 「10배 규칙」 · KR1102 2026.1Q ILP 합계 · 라이나 2023.1Q·2Q 옛 기준 등. 각각 현재 상태·권고안·영향 칸 수를 한 표로.

### 규칙
- 마스터 JSON 셀 수정 금지(오류 발견 시 inbox 발주), `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 반드시 `--no-build`. 예외·등재부에는 **해제만**(위 2번) 가능, 신규 등재 금지. 골든 `--update` 는 위 3번 목록만. xlsx·`public_exports`·HTML 금지. 서브에이전트 금지, docling 금지.
- 풀 훅(`prepush_check.py`)과 push·배포는 하지 않는다. 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서 제외), 메시지 끝 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. 모델은 Sonnet(검증 2회 불발 시에만 오케스트레이터가 Opus 지시).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·맨 `python`·stdin heredoc 금지), `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 게이트별 전후 RED/YELLOW 표, 분류 결과(고칠 것·owner 대기·해제), 등재 해제 내역과 시뮬레이션 결과, 골든별 `--update` 여부와 이유(이동 칸 수), 거짓 녹색 사냥 결과(표본 대조 불일치 목록), owner 결정 표, `TODO_validation.md` Status + `docs/changelog_validation.md`.

## 답변 (recipient 작성 — 처리 후)
(validation 7bd05b2, orchestrator 검증·종결 2026-10-11) 마스터 0칸 수정·신규 등재 0. 증거 기반 해제 5묶음(KR1102 2023.2Q census 원천부재·악사 2024.3Q 15~23후 부재 박제·교보 2026.1Q 후 박제 938.25와 19_market 재작성 연쇄·pl_amort_coverage_baseline 5줄; 해제 전후 K-ICS finding 변화 0). 골든 `--update` 6종(kics 룰 634버킷·post_transition·master_tables·ifrs17_bs 47사·viz 패널 재보사 추가분·입력지문 RED 10→0), kics 룰 골든 지문 키 사각(`company_code`/`quarter` 필드가 엔진에 없어 모든 행 None) 수정. 게이트: data_contract RED 22→21, K-ICS exit 2→0(RED 56 blocking 0), live_artifacts RED 8(INSPL) 불변. 거짓 녹색 사냥: 표본 레인별 20칸 불일치 8건 전부 설명(오류 0), 재보사 PL 항목16 인쇄·마스터 공란 7칸을 parser 에 발주(`20261011T1730Z`), CSM 워터폴 대 ILP 273칸 중 267 일치(차이는 예별 계약이전·교보/KB라이프/하나생명/롯데 재작성·현대 정밀도). owner 결정표 15항목은 `data/disclosure/_meta/final_validation_runlog_20261011.md` 및 오케스트레이터 owner 보고.
