# -*- coding: utf-8 -*-
"""Step 80: TODO_parser_ifrs17.md Status (newest first, keep 3) + open items; the displaced oldest Status entry is cut and pasted
VERBATIM to the top of docs/todo_archive_parser_ifrs17.md (below its title).  Plain string operations, LF, no BOM."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")
TODO = ROOT / "TODO_parser_ifrs17.md"
ARCH = ROOT / "docs" / "todo_archive_parser_ifrs17.md"

todo = TODO.read_text(encoding="utf-8")
arch = ARCH.read_text(encoding="utf-8")
assert "\r" not in todo and "\r" not in arch and not todo.startswith("﻿")
assert "6차: 라이나 KR0074 CSM" not in todo, "already applied"

START = "- **2026-10-11 BS·PL 정정 제안 적용 + 별첨·이미지 원천 적재(티켓 20261011T1130Z)**"
i = todo.index(START)
j = todo.index("## 열린 일", i)
block = todo[i:j]                         # the 3 lines of the oldest Status entry (+ trailing newline(s) before the next heading)
assert block.count("\n- **") == 0, "block contains another bullet"
core = block.rstrip("\n") + "\n"

NEW_STATUS = (
    "- **2026-10-11 6차: 라이나 KR0074 CSM 분기 백필 + 상각 스케줄(티켓 20261011T1700Z)** — `CSM_waterfall.json` 2,286 → 2,304행(+18 = 2025.3Q·2026.1Q·2026.2Q × 항목 1~6, YTD 억원 5자리) · `CSM_waterfall_provenance.json` +3셀(DISCLOSURE) · `CSM_amortization.json` 570 → 600행(+30, 세 분기 상각 스케줄 1~10년), 기존 행 변경 0(HEAD 접두 동일 · 키 diff 0). 원천 = 정기경영공시 PDF 검토 주석(p91+93 · p66+68 · p63, 천원): 모든 쪽 가로·세로 항등식 + 천원 0 잔차 + 별도 = 연결 + 기초 = 마스터 직전 연말 + 같은 코드로 연말 행 재현(2025.4Q·2024.4Q·2023.4Q 6항목 1자리 일치) + 독립 ILP 마스터 일치. 커밋 안 함.\n"
    "  남은 것: data-contract RED 23 → 28(신규 5 = `PL_CSM_AMORT_VS_WATERFALL` 라이나 3[등재 후보 `proposed_registry_entries.json`, owner] + xlsx `MASTER_XLSX_ROW_MISSING` 2[publishing]) · live_artifacts `NB_CENSUS_MISSING` 3(NB 재빌드, 모의 라이나 연누계 배수 11.22 · 9.02 · 10.33) · **범위 밖 발견: 연간 CSM 상각 스케줄이 15사에서 직전 연도 표**(`s34_amort_panel_year_census.json`, 새 티켓) · 라이나 기존 2025.4Q 상각 10행·값_당분기 5칸은 미수정(`proposed_fixes_existing_cells.json`) · 7번째 분기를 더하면 active_min=7 이라 MASTER_HOLE.\n"
    "  근거·재현 `data/disclosure/_meta/csm_backfill_annual_filers_runlog_20261011.md` · 도구 `scripts/extract_lina_csm_rows_20261011.py` · `load_lina_csm_backfill_20261011.py`(되돌리기 `--revert --apply`) · 백업 `data/_derived/csm_backfill_backup_20261011/`.\n"
)

NEW_OPEN = (
    "- [ ] **연간 CSM 상각 스케줄이 직전 연도 표인 15사 — 새 티켓(뷰 빌더·골든 영향)** — `viz_build_ifrs17_panels._pick_amort_block` 이 같은 `<당기말>` 캡션을 물려받은 두 후보(당기말 · 전기말 표)를 동점으로 보고 `line_no` 가 큰 전기말 표를 고른다(재현 `data/_derived/csm_backfill_lina_20261011/s33_dart_amort_blocks.py`). `csm_amort_schedule.json` FY2025 `buckets.total` 이 직전 연도 기말 CSM 과 0.05% 이내로 같은 회사 14곳(DB손보 · NH농협손보 · 동양 · 메리츠화재 · 삼성생명 · 삼성화재 · 아이엠라이프 · ABL · KDB생명 · 코리안리 · 푸본현대 · 한화손보 · 흥국생명 · 흥국화재) + 라이나, 마스터 `CSM_amortization.json` 2025.4Q 가 그 값을 물려받았다. 고친 뒤 패널·마스터 재생성 + `test_viz_ifrs17_panels_golden --update` 사유 기록. 후보 정정값(라이나) `proposed_fixes_existing_cells.json`.\n"
    "- [ ] **라이나 CSM 분기 백필 후속(owner·publishing)** — ① 새 RED 3(`PL_CSM_AMORT_VS_WATERFALL` 라이나 2025.3Q·2026.1Q·2026.2Q): 건별 등재(`proposed_registry_entries.json`) 또는 재보사 17건과 같이 게이트 설계 변경(경영공시 계보 워터폴 셀은 PL 대조 제외) ② publishing: xlsx `CSM워터폴`(+18행)·`CSM상각`(+30행) 시트 동기화, NB 마스터 재빌드(`build_nb_csm_multiple.py` → 라이나 3행 추가 → live_artifacts `NB_CENSUS_MISSING` 3 해소) ③ 결정: 분기 확장 여부 — 2025.1Q(p57)·2025.2Q(p83)는 지금 읽기 코드로 바로 닫히고 2024.1Q~3Q(p51·p76·p52)는 「분기말 잔액」 라벨 보강만 필요하지만, 라이나는 지금 6분기라 7번째 분기를 더하는 순간 active_min=7 로 MASTER_HOLE RED(2024.1Q~3Q)가 되므로 2024.1Q 부터 한 번에 · 2025.4Q `값_당분기` 5칸(기존 칸)은 다음 `build_csm()` 이 채우거나 승인 후 셀 단위로 ④ `bspl_apply_findpage.py` · `bspl_apply_render.py` 가 `raw/` 를 직접 glob 해 `tests/test_disclosure_raw_pdf_wiring.py` 2건 실패(BS·PL 담당 에이전트 스크립트, `disclosure_pdfs()` 로 교체).\n"
    "\n"
)

todo2 = todo.replace(core, "", 1)
assert core not in todo2
todo2 = todo2.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + NEW_STATUS, 1)
todo2 = todo2.replace("## 열린 일\n\n", "## 열린 일\n\n" + NEW_OPEN, 1)
assert todo2.count("6차: 라이나 KR0074 CSM") == 1 and todo2.count("라이나 CSM 분기 백필 후속") == 1

title = "# TODO archive — `TODO_parser_ifrs17.md` (Status 이력, 읽기 지연)\n\n"
assert arch.startswith(title)
arch2 = title + core + arch[len(title):]

TODO.write_text(todo2, encoding="utf-8", newline="\n")
ARCH.write_text(arch2, encoding="utf-8", newline="\n")
print("TODO bytes", len(todo.encode("utf-8")), "->", len(todo2.encode("utf-8")), "| archive bytes", len(arch.encode("utf-8")), "->", len(arch2.encode("utf-8")))
print("moved block lines:", core.count("\n"))
