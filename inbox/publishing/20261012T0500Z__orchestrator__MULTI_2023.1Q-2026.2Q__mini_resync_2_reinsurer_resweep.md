---
from: orchestrator
to: publishing
created: 20261012T0500Z
status: open
route: feature
company: MULTI
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
재보사 재스윕(owner 2026-10-12)으로 마스터가 더 바뀌었다. **미니 재동기화 2차** — xlsx 시트·NB·패널·`public_exports/`. 마스터는 모두 커밋 완료(HEAD `3727438` 이후, 작업 트리 마스터 = HEAD; 시작 때 직접 확인하고 아니면 멈추고 보고)이고 다른 에이전트는 마스터를 쓰지 않는다. 직전 라운드(`손해율` 시트 +1,904행·`panel_loss_ratio.json` 재보사+`ae` 블록, 커밋 `66e6156`)는 끝났으니 다시 하지 않는다. 바뀐 것(`git log -- <마스터>` 로 직접 세고 보고):

- `PL_breakdown.json` +303행(재보사 8곳 투자손익·영업이익·영업외손익 등 + 항목 4 3칸) · 기존 15행 정정(재보사 최신 공시 전기 칸 채택 규칙: `값` 11행·파생 `값_당분기` 4행) + `PL_breakdown_provenance.json`. (이전 PL 항목 4 라운드 `0a7632e`·`59dc684` 이후분 포함: xlsx `손익분해PL` 은 직전 미니 라운드에서 맞춰졌으니 이번엔 그 뒤 변화분만.)
- `IFRS17_BS.json` +49칸 + 오버레이 `data/dart/viz/bs_manual_overrides.json`(4,300→4,349).
- `CSM_waterfall.json` +18(RGA·하노버 2025.4Q, 퍼시픽 2023.4Q; `57b7d78`) · `CSM_amortization.json` +15 · `CSM_sensitivity.json` +6 · `insurance_liability_portfolio.json` +110(+사이드카).
- 화면 파생물: IFRS17.html 은 롱포맷 마스터를 직접 읽지만 viz 패널(`data/dart/viz/csm_waterfall.json`·`csm_amort_schedule.json`·`sensitivity_heatmap.json` 등)에는 새 재보사 행이 안 들어간다(CSM 계열 에이전트 보고: csm_waterfall 패널 재보사 0곳). `data/csm_combo/panel_csm_combo.json`·`data/compare/panel_compare.json` 도 ILP·CSM 변화 반영 필요. 빌더 `viz_build_ifrs17_panels.py`(`cf66dce` 에서 수정됨, `append_master_only_companies`)는 건드리지 않고 산출만 확인.

### 해 줄 것 (단계마다 디스크 저장, 런로그 `data/disclosure/_meta/mini_resync_2_runlog_20261012.md` 맨 위 갱신)
1. **사전 확인**: `git status` 마스터 JSON 이 HEAD 와 같은지, `scripts/check_master_xlsx_drift.py`·`validate_data_contract.py` 의 `MASTER_XLSX_*` 시트별 누락·드리프트 행수를 기록.
2. **xlsx 시트 동기화**(전체 재생성·openpyxl 재저장 금지, 바뀐 시트만 `scripts/sync_master_xlsx_sheet.py "<시트>"`, 시작 전 백업, 끝난 뒤 기존 행·값 불변 증명): `손익분해PL` · `17BS` · `CSM워터폴` · `CSM상각` · `가정민감도` · `보험계약부채`. 시트마다 「추가 행 / 바뀐 칸」을 마스터 diff 와 대조(`손익분해PL` 의 바뀐 칸 = 정정 11 + 파생 4 = 값 변경 15행 분량, 나머지는 추가). 의도 밖 변경이 있으면 멈추고 보고. 시트 신설·열 변경 금지(필요하면 보고).
3. **NB 배수 마스터**: `scripts/build_nb_csm_multiple.py`(스크립트를 먼저 읽고 동작 확인, `--help` 금지). 새 CSM 워터폴 재보사 행으로 NB 재보사 census 가 달라지는지 확인(재보사는 월납월초 분모 없음 → null 배수 행). 다른 회사 행 변경 0, `NB_CENSUS_MISSING` 0 유지. 바뀌면 NB 시트도 동기화.
4. **패널 재빌드**(마스터 확정이니 한 번씩, 인플레이스 덮어쓰기라 실행 전 백업·예외 시 복구): `viz_build_ifrs17_panels.py` 4패널 · `viz_build_csm_waterfall.py` · `viz_build_csm_combo_panel.py`(+`--check`) · `viz_build_compare_panel.py`. 전후 변화(회사·분기)를 보고하고, 달라지는 건 재보사 추가분·라이나(이미 반영)뿐이어야 한다. 골든(`test_viz_ifrs17_panels_golden`·`test_viz_csm_waterfall_golden`)은 `--update` 금지, 실패 사유만 보고(validation 몫).
5. **`public_exports/` 재생성**: `scripts/export_public_sheets.py` 는 커밋된 HEAD 를 읽는다 → 2·3·4 단계 산출물을 **먼저 커밋**한 뒤 실행하고 재커밋. `manifest.json` `build_id`·`generated_at_utc` 갱신, 공개 게이트(`check_public_exports`) 발견 0.
6. **게이트·테스트(한 번에 하나씩, PC 부하가 높다)**: `validate_data_contract.py`(예상: `MASTER_XLSX_*` 0 · 다른 RED 는 검증 단계 몫이니 **종류별로만 보고**: `CONCEPT_MIXED_DISCLOSURE_INTO_DART` 계열은 validation 이 이어서 처리), `validate_live_artifacts.py`, `tests/test_deploy_assets.py` · `tests/test_push_gate_wiring.py` · `tests/test_prepush_scope.py`. 풀 훅·전체 pytest 금지.

### 규칙
- 마스터 JSON 셀 수정 금지(읽기만). 예외 등재 금지. 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json` 제외; `.gitignore` 경로를 `git add` 에 넣으면 add 가 오류를 낸다 — 경로를 확인), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push·배포 금지**. 서브에이전트 금지, docling 금지. HTML 금지.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), 맨 `python`·`python -`(stdin heredoc) 금지, 인자를 모르는 스크립트를 `--help` 로 실행하지 말 것, `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고 (2~5줄 존댓말 + 파일 경로)
- 시트별 추가 행·변경 칸 대 마스터 diff·기존 불변 증명, NB 전후, 패널 전후 변화(회사·분기), `public_exports` 변경 목록·게이트, 골든 실패 사유, 게이트 RED 종류별 수, `TODO_publishing.md` Status + `docs/changelog_publishing.md`.

## 답변 (recipient 작성 — 처리 후)
