---
from: orchestrator
to: publishing
created: 20261011T2100Z
status: resolved
route: feature
company: MULTI
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
이전 마감 publishing 라운드(`8848cb8`…`f218170`, NB `1412aaf`…) 뒤에 마스터가 더 바뀌었다. **미니 재동기화**(시트·공개본·패널·NB). 마스터는 이 티켓 발사 시점에 모두 커밋 완료(오케스트레이터 보장)이고 다른 에이전트가 마스터를 쓰지 않는다. 바뀐 것(HEAD 기준 `git log -- <마스터>` 로 직접 세고 보고할 것):

- `PL_breakdown.json`: 재보사 항목 16 +7칸(`69c8962`), 항목 4(CSM 상각) 재보사 17버킷 + 라이나 9버킷 = +26행(`0a7632e`·`59dc684`, 출처 사이드카 `PL_breakdown_provenance.json` 포함). (xlsx 손익분해PL 누락 행이 정확히 +33 이어야 맞다.)
- `CSM_waterfall.json`(+`CSM_waterfall_provenance.json`): 라이나 KR0074 CSM 항목 1~6 을 2025.3Q·2026.1Q·2026.2Q(`6081de1`) + 2023.3Q·2024.1Q~3Q·2025.1Q~2Q(`28b9e23`) 채움, 그리고 기존 라이나 4개 분기(2023.4Q·2024.4Q·2025.3Q·2025.4Q)의 `값_당분기` None 칸 채움(가장 최근 커밋 확인).
- `CSM_amortization.json`: 라이나 상각 스케줄 추가(분기별 행, `6081de1` + 최신 커밋) + 18사 2025.4Q 172칸 값 정정(`cf66dce`, 전기말 표를 잘못 뽑았던 것을 당기말로).
- 그 결과 달라지는 파생물: NB 배수 마스터(`NB_CSM_multiple.json`; 라이나는 이제 실제 CSM 으로 연누계·당분기 배수 계산) · `data/dart/viz/csm_amort_schedule.json`(이미 빌더 수정과 함께 한 번 재빌드됨, 라이나 추가분 반영하려면 다시) · `data/dart/viz/csm_waterfall.json` · `data/csm_combo/panel_csm_combo.json` · `data/compare/panel_compare.json`.
- 빌더 `scripts/viz_build_ifrs17_panels.py` 는 `cf66dce` 로 수정됨(`_current_period_twin`). 건드리지 말 것(불일치 발견 시 보고).

### 해 줄 것 (단계마다 디스크 저장, 런로그 `data/disclosure/_meta/mini_resync_runlog_20261011.md` 맨 위 갱신)
1. **사전 확인**: `git status` 에서 마스터 JSON 이 HEAD 와 같은지(커밋 안 된 마스터 변경이 있으면 시작하지 말고 보고), `validate_data_contract.py` 의 `MASTER_XLSX_*` 목록과 `scripts/check_master_xlsx_drift.py` 로 시트별 누락·드리프트 행수를 기록.
2. **xlsx 시트 동기화** (전체 재생성·openpyxl 재저장 금지, 바뀐 시트만 `scripts/sync_master_xlsx_sheet.py "<시트>"`, 시작 전 백업, 끝난 뒤 기존 행·값 불변 증명): `손익분해PL` · `CSM워터폴` · `CSM상각` · `NB 신계약CSM배수` 시트(이름은 기존 sync 목록에서 확인). 시트마다 「추가 행 / 바뀐 칸」을 마스터 diff 와 대조(`CSM상각` 의 바뀐 칸은 172 + 라이나 값 정정; `손익분해PL` 은 +33 행 예상, `CSM워터폴` 은 라이나 추가 + `값_당분기` 채움 칸). 의도 밖 변경이 있으면 멈추고 보고.
3. **NB 배수 마스터 재빌드**: `scripts/build_nb_csm_multiple.py` (먼저 스크립트 인자·동작을 읽고 확인, `--help` 로 실행하지 말 것). 라이나 KR0074 가 실제 배수를 가지는지, 다른 회사 행은 전후 변경 0인지(재보사 18행 null 포함) 확인. `NB_CENSUS_MISSING` 이 0으로 유지되는지 확인.
4. **패널 재빌드**(마스터 확정이니 한 번씩): `viz_build_ifrs17_panels.py`(`csm_amort_schedule`·민감도 등 — 빌더가 4패널을 함께 만든다. 다른 3패널은 전후 바이트 동일해야 함; 인플레이스 덮어쓰기라 실행 전 백업), `viz_build_csm_waterfall.py`(전후 diff, 달라지는 건 라이나 추가분뿐이어야 함), `viz_build_csm_combo_panel.py`(+`--check`), `viz_build_compare_panel.py`. 전후로 달라진 회사·분기를 보고. 골든(`test_viz_ifrs17_panels_golden`·`test_viz_csm_waterfall_golden`)은 `--update` 하지 말고 실패 사유만 보고(validation 이 한다).
5. **`public_exports/` 재생성**: `scripts/export_public_sheets.py`(커밋된 HEAD 를 읽는다 — 2·3·4 단계 산출물을 **먼저 커밋**한 뒤 실행하고 재커밋). `manifest.json` `build_id`·`generated_at_utc` 갱신, 공개 게이트(`check_public_exports`) 발견 0 확인.
6. **게이트·테스트**: `validate_data_contract.py` 의 `MASTER_XLSX_*` RED 0, `scripts/validate_live_artifacts.py`(`NB_CENSUS_MISSING`·신규 RED 여부; `INSPL_CENSUS_MISSING` 8 은 알려진 보고 사항), `tests/test_deploy_assets.py` · `tests/test_push_gate_wiring.py` · `tests/test_prepush_scope.py` · `tests/test_rule_coverage_manifest.py`. 풀 훅(`prepush_check.py`)은 돌리지 않는다.

### 알려진 사항 (이 티켓 범위 밖)
- 골든 `--update`·예외 등재는 validation 몫. 디자인 변경(HTML)은 designer 몫(재보사 표기 건 진행 중이니 HTML 은 건드리지 말 것).
- `INSPL_CENSUS_MISSING` 8 은 보고만.

### 규칙
- 마스터 JSON 셀 수정 금지(읽기만). 예외 등재 금지. 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서 제외; `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`), **push·배포 금지**. 서브에이전트 금지, docling 금지.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), 맨 `python`·`python -` 절대 금지, 인자를 모르는 스크립트를 `--help` 로 실행하지 말 것(빌더가 그냥 돌아 산출을 덮어쓴 전례), `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 단계별 결과(시트별 추가 행·변경 칸 대 마스터 diff, 기존 시트 불변 증명), NB 전후, 패널 전후 변화(회사·분기), `public_exports` 변경 목록과 게이트, 골든 실패 사유, 게이트·테스트 결과. `TODO_publishing.md` Status + `docs/changelog_publishing.md`.

## 답변 (recipient 작성 — 처리 후)
(publishing 5d320c9·812b007·65272db, orchestrator 검증·종결 2026-10-11) 시작 시 xlsx 드리프트 189칸→종료 0. 시트: 손익분해PL +33행(재보사 24·라이나 9)/2칸, CSM워터폴 +54(라이나)/15칸(빈칸→값), CSM상각 +50(라이나)/172칸, 신계약CSM배수 +9(라이나)/6칸, 삭제 0·나머지 시트 불변. NB 마스터 381→390행(라이나만 변경, 연누계 9.0~14.6배·당분기 9.0~15.2배, 2023.3Q 당분기만 공란=2023.2Q CSM 보류), 재보사 18행 null 유지, NB_CENSUS_MISSING 0. IFRS17 viz 4패널·csm_waterfall 재빌드 바이트 동일, csm_combo 라이나 신계약CSM 11칸 채움, compare 53칸 변경. public_exports 4시트+manifest(build_id 5d320c9), 공개 게이트 0. data_contract RED 0, live_artifacts RED 8(INSPL_CENSUS_MISSING 기존). 남은 것: viz 골든 csm_amort_schedule 해시(validation). 참고(owner 판단): csm_amort_schedule 패널의 라이나 행은 DART FY2025 분할표 부분합이고, 마스터에서 읽는 규칙은 재보사에만 적용되어 라이나 상각 스케줄 마스터값이 패널에 안 간다.
