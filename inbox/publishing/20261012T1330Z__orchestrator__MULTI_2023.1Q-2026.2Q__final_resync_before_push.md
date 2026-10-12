---
from: orchestrator
to: publishing
created: 20261012T1330Z
status: open
route: feature
company: MULTI
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
오늘 마스터가 여러 번 바뀌었다 — 재보사 손해율 세그먼트 표준화(`268002b`), 재보사 PL 7칸 복원·처브 BS 20/ILP 14·15·분할표 상각 18칸(`3bf1690`), 그리고 K-ICS 칸 보정(퍼시픽 경과조치 16칸·악사 4칸·뮌헨 50·52(·51)) — 마지막 것은 parser-kics 가 곧 커밋한다(`git log -- kics_disclosure.json` 으로 확인; 아직 `kics_disclosure.json` 이 미커밋 수정 상태일 수 있다). 지금 xlsx·공개본·패널이 마스터보다 뒤처져 있다(게이트: `validate_data_contract` RED 7=XLSX 드리프트, `validate_live_artifacts` RED 5 — 시트 17BS·CSM상각·손익분해PL·보험계약부채). owner 가 push·배포 직전 최종 정합을 요청했다. **직전 라운드 절차(`data/_derived/mini_resync_20261012/runlog.md`, `docs/changelog_publishing.md` 의 `b4b6a71`/`5079688` 항목)를 그대로 따른다.**

### 해 줄 것 (순서대로; 마스터 JSON 은 읽기만)
1. **패널·파생 JSON 재빌드**(바뀐 마스터에 의존하는 것만; 기존 빌더를 개별 호출, 통짜 `build_root_masters.py main()` 금지): `viz_build_ifrs17_panels.py`·`viz_build_csm_waterfall.py`·`viz_build_csm_combo_panel.py`·`viz_build_compare_panel.py`·`viz_build_nb_csm_ratio.py`·`viz_build_ifrs17_kpis.py`·csm_amort_schedule 패널·`data/loss_ratio/panel_loss_ratio.json`(손해율 패널 — **재보사 세그먼트 표준화(생명보험/장기손해보험)가 반영돼야 한다**; 빌더는 `scripts/viz_build_persistency_lossratio_panels.py` 등 기존 경로, `risk_premium_vs_expected_claims.json.gz` 를 읽도록 바뀐 점 확인). 각 빌드의 전후 해시·변경 목록을 증빙으로 저장하고, 의도한 칸 외 변경이 없는지 확인. 골든 시험(`tests/test_viz_*_golden.py` 등)이 해시 어긋남을 내면 **`--update` 하지 말고** 어떤 골든이 무엇 때문에 어긋났는지 보고(validation 이 한다).
2. **xlsx 시트 동기화**: 변경된 시트만 `scripts/sync_master_xlsx_sheet.py "<시트>"` 로(전체 재생성·openpyxl 재저장 금지, 시작 전 백업, 행·칸 변경 목록·타 시트 바이트 불변 증명): `17BS`·`CSM상각`·`손익분해PL`·`보험계약부채`·`손해율`(해당 시)·`CSM워터폴`(해당 시)·그리고 **`K-ICS공시`(parser-kics 커밋이 들어온 뒤 마지막에)**. `scripts/check_master_xlsx_drift.py` 로 드리프트 0 확인. 시트 이름·열 구성 변경 금지.
3. 마스터·xlsx·패널을 커밋한 뒤 **`scripts/export_public_sheets.py`**(커밋된 HEAD 를 읽는다)로 `public_exports/` 재생성·`manifest.json`(`build_id`) 갱신·재커밋. 이번에 **다운로드 목록에서 임시로 내린 3시트**(기본자본소진율·보완자본소진율·자본비율전망)의 `public_exports` 파일은 지우지 않는다(목록에서만 내렸다).
4. 게이트: `validate_data_contract.py`(RED 0 목표; XLSX_*/PUBLIC_EXPORT_* 0), `validate_live_artifacts.py`(알려진 `INSPL_CENSUS_MISSING` 8 은 등재됨 — 새 RED 만 보고), `validate_master_tables.py --no-build`, `check_master_xlsx_drift.py`. 시험·게이트는 **한 번에 하나씩 끝까지**. 새 RED 는 덮지 말고 종류별 보고.
5. `TODO_publishing.md` Status + `docs/changelog_publishing.md` 갱신. 이것이 끝나면 오케스트레이터가 validation(최종 골든/게이트)을 부르고 작업 브랜치 push(전체 훅)·폰 배포 안내로 넘어간다 — **빨리** 끝내는 것이 우선이다.

### 규칙
- 마스터 JSON 수정 금지(읽기만), HTML 금지, 예외 등재 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외, `.gitignore` 경로를 `git add` 에 넣지 말 것), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지, docling 금지. 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`·스크립트 파일만(멀티라인 `-c`·stdin heredoc 금지, 고아 python 프로세스 즉시 종료). 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 빌드한 패널·동기화한 시트 목록, 게이트 결과(RED 종류별), 골든 어긋남 목록, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
