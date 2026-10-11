---
from: orchestrator
to: validation
created: 20261011T2200Z
status: resolved
route: verify
company: MULTI
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
마스터·패널·xlsx·공개본이 모두 커밋되어 **작업 브랜치 push 직전**이다(HEAD `65272db`). 이후 오케스트레이터가 `git push origin fix/csm-product-segmented-columns` 를 돌리면 `.githooks/pre-push`(≈18분, `--no-verify` 금지, 마스터 변경이 있어 전체 게이트)가 돈다. 이 티켓은 **훅이 한 번에 통과하도록 사전 정리**하는 마지막 라운드다. 마스터에 쓰는 에이전트는 이 시점에 없다.

오늘 지금까지 바뀐 것(최근 순): publishing `5d320c9`/`812b007`/`65272db`(xlsx 4시트·NB 배수 마스터 390행·csm_combo·compare 패널·public_exports 4시트), designer `dcac354`(IFRS17.html 재보사 PL 라벨), validation `1db7c2d`(§3d 항목 4 계보 허용·ZERO_LEGS·승인 등재 4건), Lina CSM `6081de1`/`28b9e23`/`396faff`(워터폴 54칸+값_당분기 20칸·상각 스케줄 +20행), PL 항목 4 `0a7632e`(재보사 17+라이나 3)·`59dc684`(라이나 6), 상각 스케줄 수정 `cf66dce`(18사 2025.4Q 172칸·`viz_build_ifrs17_panels.py` `_current_period_twin`), PL 항목 16 `69c8962`.

### 해 줄 것 (단계마다 디스크 저장, 런로그 `data/disclosure/_meta/pre_push_final_runlog_20261011.md` 맨 위 갱신)
1. **훅이 실제로 도는 항목을 그대로 사전 실행**: `scripts/prepush_check.py` 의 전체 게이트 구성(data-contract 하드게이트·K-ICS 룰 게이트·도메인 게이트·DART raw·골든 지문·inbox 위생·오프라인 테스트 전수)을 읽고, 풀 훅을 직접 돌리지 말고(오케스트레이터가 push 때 돌린다) **같은 항목을 개별 실행**해 어디서 RED/실패가 나는지 모은다. (직접 `prepush_check.py` 전체를 돌릴 수 있으면 돌려도 된다. 단 push 는 하지 않는다.)
2. **골든 `--update`(이유를 커밋 메시지에 명시, 의도하지 않은 이동은 하지 말고 보고)**: 기대 대상 = `tests/test_viz_ifrs17_panels_golden.py`(`csm_amort_schedule` 해시: `cf66dce` 가 18사 2025.4Q 를 당기말 표로 바꾼 의도된 이동 — publishing 이 같은 빌더로 재빌드한 결과는 바이트 동일했다. 다른 3 패널 해시는 불변이어야 함) · `tests/test_master_tables_golden.py`(SUMMARY: coverage_hole 3→2PL·`pl_src_absent` 토큰·라이나 CSM 적재로 closing·csm_amort_identity·qoq_warn 이동) · `validate_golden_input_fingerprints.py --update`(전체 골든을 먼저 돌려 산출이 정말 안 움직였는지 확인한 뒤) · 그 밖에 실패하는 골든. `RUN_PL_GOLDEN=1` PL 골든은 PL 항목 4/16 추가 후 지문이 움직이는지 확인(빌더 산출 대 마스터 비교 방식이면 이동 없음을 증명). `test_ifrs17_bs_golden`(~8분)은 BS 마스터가 오늘 오후 이후 불변이면 생략 가능(불변 근거를 해시로 적을 것).
3. **오프라인 테스트 실패 처리**: 알려진 실패 `tests/test_disclosure_raw_pdf_wiring.py` 2건(`scripts/bspl_apply_findpage.py`·`bspl_apply_render.py` 의 raw 글롭 배선 — 일회성 스크립트라 훅 묶음에 포함되는지 먼저 확인). 훅에 포함되면 테스트 기대에 맞게 **스크립트 쪽 글롭을 최소 수정**(`scripts/_disclosure_pdf_paths.py` 헬퍼 사용)하거나, 일회성 스크립트임을 근거로 테스트 허용 목록에 사유와 함께 등재(후자는 새 예외 등재이므로 owner 승인 사항 — 먼저 전자를 시도하고 안 되면 보고만). 그 밖의 실패(`test_rule_coverage_manifest` · xlsx/public_exports 관련)는 publishing 동기화 후 해소됐는지 확인.
4. **알려진 사항 보고만(등재 금지)**: `validate_live_artifacts` `INSPL_CENSUS_MISSING` 8, 서울보증 2024.2Q·3Q PL 통째 구멍 2건(마스터테이블 게이트), 라이나 2023.1Q·2Q CSM 보류, `test_viz_ifrs17_panels_golden`·차트 쪽의 분할표 5사 부분합(라이나·AIA·처브·메트라이프·BNP카디프)과 한화생명 연결 표 선택(`cf66dce` 보고) — 각각 현재 영향·권고안을 한 표로.
5. **훅 통과 예상 보고**: 위 1~3 후 「이 상태로 push 하면 훅이 통과하는가」를 항목별 근거와 함께 한 줄 결론(통과 예상 / 막히는 항목과 해결안).

### 규칙
- 마스터 JSON 셀 수정 금지(오류 발견 시 inbox 발주), `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 반드시 `--no-build`. 신규 예외·등재 금지(owner 승인 사항은 보고만). xlsx·`public_exports`·HTML 금지. 골든 `--update` 는 위 2번 범위만. 서브에이전트 금지, docling 금지. viz 골든 2종은 산출을 인플레이스로 덮어쓰는 빌더라 실행 전 백업·예외 시 복구.
- 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json` 같은 게이트가 재생성하는 부수 파일 제외), 메시지 끝 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push 금지**(오케스트레이터 몫).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·맨 `python`·stdin heredoc 금지), `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 게이트·테스트별 전후 결과, 골든별 `--update` 여부와 이동 칸 수·이유, 훅 통과 예상 결론, 보고만 항목 표. `TODO_validation.md` Status + `docs/changelog_validation.md`.

## 답변 (recipient 작성 — 처리 후)
(validation 2033a52·d01cd69·5499de0, orchestrator 검증·종결 2026-10-11) 풀 훅 사전 실행(약 28분, pytest 1491초): data_contract RED 0 · K-ICS 게이트 exit 0 · 지문 RED 0(--update 후) · 오프라인 테스트 772 통과, 막는 항목은 live_artifacts INSPL_CENSUS_MISSING 8 하나(재보사 7곳+마이브라운이 DART 표 기반 보험손익 원표 패널에 구조상 없음). 골든 --update 3종(viz_ifrs17_panels csm_amort_schedule 해시=cf66dce 의도 이동, master_tables SUMMARY, 입력지문 viz 항목); kics 룰·post_transition·dividend·csm_waterfall·PL(RUN_PL_GOLDEN)·BS 불변. test_disclosure_raw_pdf_wiring 2건은 훅 묶음 밖이지만 스크립트 글롭 최소 수정으로 해소. 보고만 항목: 서울보증 2024.2Q·3Q PL 통째 구멍 2건, 라이나 CSM 2023.1Q·2Q 보류, 분할표 5사 부분합, 한화생명 연결 표 선택. 등재 8줄은 owner 채팅 승인 후 티켓 20261011T2300Z 로 처리.
