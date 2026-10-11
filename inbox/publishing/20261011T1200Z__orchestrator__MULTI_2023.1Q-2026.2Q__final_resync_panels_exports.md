---
from: orchestrator
to: publishing
created: 20261011T1200Z
status: open
route: feature
company: MULTI
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11, 밤새 처리) 전체 스윕의 **마감 publishing 라운드**다. 이 시점의 마스터는 확정이며 이 티켓이 발사된 동안 마스터를 쓰는 다른 에이전트는 없다(오케스트레이터가 보장). 오늘 마스터가 바뀐 곳: `kics_disclosure.json`(재보사 +86행·AXA 2024.3Q +17행, 커밋 b80d16a·a81f401) · `kics_duration_gap.json`(+1행, 6행 변경) · `IFRS17_BS.json`(+약 1,747칸·정정 23칸, bd64513·c2d36f8) · `PL_breakdown.json`(+540칸) · `CSM_amortization.json` +180 · `CSM_sensitivity.json` +116 · `CSM_waterfall.json` +108 · `management_indicators.json` +1,259(e8ca3af) · `insurance_liability_portfolio.json`(+114행·12셀 정정, 86b055b) · 자본성증권·Forward(`kics_forward_capital.json`·`kics_tier1/2_utilization.json`, 60132a8) 등. 이 중 라이브 첫 노출이 되는 것이 많다. **가장 중요한 목표: IFRS17.html 에서 재보사 8곳(마이브라운 포함)이 목록에 뜨고 CSM·민감도·상각·BS·PL 패널이 비지 않는 것.**

### 해 줄 것 (순서대로, 단계마다 디스크에 저장·런로그 `data/disclosure/_meta/final_resync_runlog_20261011.md` 맨 위 「중간 결과」 갱신)
1. **사전 확인**: `git status` 에서 마스터 JSON 이 커밋된 상태(HEAD 와 같음)인지, `scripts/check_master_xlsx_drift.py`·`scripts/validate_data_contract.py` 의 `MASTER_XLSX_*` RED 12+ 목록을 먼저 뽑아 시트별 누락·드리프트 행수를 기록.
2. **xlsx 시트 동기화** — 전체 재생성 금지, 바뀐 시트만 `scripts/sync_master_xlsx_sheet.py "<시트>"` 로(시트마다 시작 전 백업, 끝난 뒤 기존 시트 행수·값 SHA 불변 증명은 이전 라운드 `ilp_master_sheet_runlog.md` 방식): `17BS` · `손익분해PL` · `가정민감도` · `CSM워터폴` · `CSM상각` · 경영지표 시트(있으면) · `K-ICS공시` · `금리듀레이션갭` · `기본자본소진율` · `보완자본소진율` · `자본비율전망` · `보험계약부채`(+114행·12셀 변경). 시트마다 「추가 행 / 바뀐 칸」 수를 마스터 diff 와 대조해 의도하지 않은 변경이 없음을 확인. 시트 이름·열 구성 변경이 필요하면 하지 말고 보고.
3. **`public_exports/` 재생성**: `scripts/export_public_sheets.py` (커밋된 HEAD 를 읽으니 마스터가 모두 커밋된 상태임을 확인하고 실행). `manifest.json` `build_id`·`generated_at_utc` 갱신, 공개 게이트(`check_public_exports` 의 회사코드·내부 용어·드리프트) 발견 0 확인. 새 공개 시트(`보험계약부채`·`자본성증권발행현황`·`금리듀레이션갭`)가 `scripts/android_push_and_deploy.sh` 의 `NEW_FILES` 에 모두 들어 있는지 확인(designer 가 다운로드 목록에 3개를 넣었다 — 라이브에 파일이 없으면 404).
4. **IFRS17 viz 패널 재빌드**: IFRS17.html 은 `CSM_waterfall.json`·`PL_breakdown.json`·`IFRS17_BS.json` 롱포맷 마스터는 직접 읽어 재보사가 자동으로 드롭다운에 뜨지만, 상각(`data/dart/viz/csm_amort_schedule.json`)·가정민감도(`sensitivity_heatmap.json`)·CSM 워터폴(`csm_waterfall.json`)·보험손익(`insurance_pl_breakdown.json`) 등 viz 패널에는 재보사가 없다(현재 KR1101/뮌헨 0건 확인). 해당 빌더(`scripts/viz_build_ifrs17_panels.py`·`viz_build_csm_waterfall.py`·`viz_build_nb_csm_ratio.py` 등; 어느 패널이 어느 빌더 산출인지 `IFRS17.html` 의 fetch 목록(`dataPaths`)과 `tests/test_push_gate_wiring.py` 의 `PANEL_DERIVED_FROM` 으로 확인)가 재보사 8곳을 처리하는지 본다. 빌더는 산출을 **인플레이스로 덮어쓰니 실행 전 백업, 예외 시 복구**. 빌더가 재보사를 못 처리하면(회사 목록 하드코딩·티커 의존 등) 빌더를 최소 수정해 재보사를 넣는다(무엇을 바꿨는지 기록; 기존 39사 산출은 바이트 동일해야 함 — 실행 전후 diff 로 증명, 달라지는 건 재보사 추가분뿐). **골든 테스트가 달라지면(`test_viz_ifrs17_panels_golden`·`test_viz_csm_waterfall_golden`) `--update` 하지 말고** 실패 사유(재보사 추가분인지)만 보고 — validation 이 `--update` 한다.
5. **패널 재빌드**: `scripts/viz_build_csm_combo_panel.py`(+ `--check` 통과) → `data/csm_combo/panel_csm_combo.json`, `scripts/viz_build_compare_panel.py` → `data/compare/panel_compare.json`. 마스터가 확정이니 최종 한 번만. 재빌드 전후 달라진 회사·분기를 보고(ILP +114행·12셀, BS/PL 정정이 반영되는 칸).
6. **자본성증권 정리**: ① `compute_tier1_utilization.py`·`compute_tier2_utilization.py` 가 입력 MD 파일명에서 회사명을 얻어 KB라이프가 `케이비라이프생명보험` 으로 되살아나는 문제 — 코드→`원수사명` 매핑을 쓰도록 근본 수정(수정 후 재실행 결과가 현재 배포본과 KB라이프 1칸 외 같아야 함) ② `kics_forward_capital.json` 에 서울보증(PAA 보증보험) 제외 행과 사유를 추가해 화면 문구가 데이터에서 나오게(designer 가 K-ICS.html 에서 `forward_capital_simulation.py::EXCLUDE_PAA` 이유를 문구로 쓰고 있다 — designer 요청: 「데이터가 사유를 말하게」). 다른 회사 행 변경 0.
7. **게이트·테스트**: `validate_data_contract.py` 의 `MASTER_XLSX_*` RED 0 확인(다른 RED 는 아래 「알려진 RED」 외 새로 생기면 보고), `scripts/validate_live_artifacts.py`(`TIER_*` 발견), `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py`·`tests/test_rule_coverage_manifest.py`(xlsx/public_export 관련), `tests/test_share_screenshot.py`. 풀 훅(`prepush_check.py`)은 돌리지 않는다(오케스트레이터가 별도 실행).

### 알려진 RED / 이 티켓 범위 밖 (건드리지 말 것)
- `PL_CSM_AMORT_VS_WATERFALL` 17 · `PL_YTD_COLLAPSE_TO_ZERO` 3 · 하노버 2025.3Q PL `MASTER_HOLE` 1 — owner 등재 사항. `KICS_CENSUS_EXEMPTION_INERT` KR1102 2023.2Q 등재 해제·골든 `--update` — validation 몫.

### 규칙
- 마스터 JSON 셀 수정 금지(읽기만, 6번 ② 의 `kics_forward_capital.json` 은 예외 — 제외 행 추가 한정). xlsx 전체 재생성·openpyxl 재저장 금지. 골든 `--update` 금지. 예외 등재 금지. 커밋은 자기 파일만(`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`), push·배포 금지. 서브에이전트 금지, docling 금지.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python3`·`python -`(stdin heredoc) 절대 금지**, 인자를 모르는 스크립트를 `--help` 로 실행하지 말 것(빌더가 그냥 실행돼 산출을 덮어쓴 전례), `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 단계별 결과(시트별 추가 행·변경 칸 대 마스터 diff, 기존 시트 불변 증명), `public_exports` 변경 목록·게이트, viz 패널에 재보사가 들어갔는지(패널별 회사 수 전후), 빌더 수정 내용과 기존 39사 불변 증명, 골든 실패 사유, 패널 재빌드 변화 요약, 자본성증권 수정, 테스트·게이트 결과, `TODO_publishing.md` Status + `docs/changelog_publishing.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
