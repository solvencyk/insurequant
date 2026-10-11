---
from: orchestrator
to: parser
created: 20261011T1900Z
status: open
route: reparse
company: MULTI (15사: 라이나 · DB손보 등 — 목록 s34_amort_panel_year_census.json)
period: 2025.4Q (+ 같은 결함이 있는 분기)
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
라이나 CSM 백필(`inbox/_resolved/20261011T1700Z…`, 커밋 `6081de1`) 중 parser-ifrs17 이 발견했다: **`scripts/viz_build_ifrs17_panels.py::_pick_amort_block` 이 같은 `<당기말>` 캡션을 물려받은 두 후보 표(당기말·전기말) 중 `line_no` 가 큰 쪽, 즉 전기말(2024-12-31 기준) 스케줄을 고른다.** 그 결과 `CSM_amortization.json` 과 패널 `data/dart/viz/csm_amort_schedule.json` 의 해당 회사 2025.4Q 「기대 상각 스케줄」이 **전기말 기준**으로 들어가 있다(라이나 2025.4Q 10행 확인). 같은 결함이 DB손보 등 14곳 + 라이나 = **15사**(목록·증거: `data/_derived/csm_backfill_lina_20261011/s34_amort_panel_year_census.json` · `.py`, 다른 분기 센서스 `s60_census_other_quarters.json`)에 있다. IFRS17.html 상각 차트로 **라이브에 이미 나가 있는 화면 오류**일 수 있다(실제 라이브 파일과 대조해 확인할 것).

### 해 줄 것
1. **원인 재현**: 15사 중 3곳(라이나 · DB손보 · 하나 더)에서 원문(DART XML 또는 해당 표)을 열어 두 후보 표의 캡션·기준일·`line_no` 를 보이고, 어느 쪽이 당기말(해당 분기 말) 스케줄인지 기준일 기반으로 판정하는 규칙을 정한다(`line_no` 대신 표가 가리키는 기준일/순서). 규칙은 기존 정상 회사(결함 없는 나머지)의 선택을 바꾸면 안 된다 — 수정 전후 전 회사·분기 선택 결과 diff 로 증명(바뀌는 건 15사 결함분뿐).
2. **빌더 수정** (`_pick_amort_block` 또는 호출부) + **데이터 정정**: `CSM_amortization.json` 의 해당 회사·분기 칸을 **셀 단위 + 옛 값 guard + 백업**(`data/_derived/amort_fix_backup_20261011/`)으로 정정하고 provenance 를 남긴다. 패널 `data/dart/viz/csm_amort_schedule.json` 은 빌더 산출이 인플레이스로 덮어쓰이니 실행 전 백업, 예외 시 복구, 변하는 것은 15사 결함분뿐임을 전후 diff 로 증명(재보사 추가분 `append_master_only_companies` 는 보존).
3. **검산**: 정정 후 각 회사 스케줄 합계(1~10년+초과)와 같은 분기 `CSM_waterfall` 기말 CSM 의 관계가 정상 회사들의 범위와 맞는지(전기말 스케줄이면 기말 CSM 과 크게 어긋남), 연도 단조성, 단위(억원). 영향 분기 전수 센서스(2023.4Q~2026.2Q)에서 같은 결함이 다른 분기에도 있는지(`s60` 참고) 확인해 함께 정정.
4. **하지 말 것**: 라이나 2025.4Q `값_당분기` 후보(`proposed_fixes_existing_cells.json`) 중 상각 스케줄과 무관한 칸은 건드리지 않고 목록만 보고. 골든 `--update` 금지(`test_viz_ifrs17_panels_golden` 은 실패 사유만 보고 — validation 이 갱신), 신규 예외 등재 금지.

### 규칙
- 쓰는 파일: `CSM_amortization.json` · 해당 provenance/사이드카 · `scripts/viz_build_ifrs17_panels.py` · `data/dart/viz/csm_amort_schedule.json`(+같은 빌더 산출 3개는 바이트 불변이어야 함). PL·BS·K-ICS·ILP·CSM_waterfall·NB 마스터·xlsx·`public_exports`·HTML·게이트·등재부·골든 금지. 커밋·push 금지(오케스트레이터가 HEAD 대조 후 커밋), 서브에이전트 금지, docling 금지.
- 동시에 다른 parser-ifrs17 에이전트가 `PL_breakdown.json` 을 쓰고 있다 — 겹치지 말 것. `validate_data_contract.py`·`validate_master_tables.py` 는 `--no-build`(인자 없이·`--help` 단독 금지).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·맨 `python`·stdin heredoc 금지), `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다. `TODO_parser_ifrs17.md`/`docs/changelog_parser_ifrs17.md` 는 건드리지 말고(오케스트레이터가 기록) 런로그 `data/disclosure/_meta/csm_amort_schedule_fix_runlog_20261011.md` 에만 남긴다.

### 보고
- 원인 재현 3건, 새 선택 규칙과 전 회사 선택 전후 diff, 정정 칸 수(회사×분기), 검산, 패널 전후 diff(바뀐 회사만), 빌더 골든 실패 사유, 라이브 파일과의 대조 결과.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
