# -*- coding: utf-8 -*-
from pathlib import Path
todo = Path("TODO_publishing.md"); arc = Path("docs/todo_archive_publishing.md"); chg = Path("docs/changelog_publishing.md")
t = todo.read_text(encoding="utf-8")
head, rest = t.split("## 열린 일", 1)
marker = "- **2026-10-19 밤 손해율 비교 단위"
i = head.index(marker)
oldest = head[i:].rstrip("\n") + "\n"
head = head[:i]
new = (
"- **2026-10-22 parser `acdb2fe9`(최신 비교열 19버킷 · 7사 KR0005 KR0032 KR0070 KR0082 KR0083 KR0087 KR0104) 파생 산출물 재생성(커밋 전)** — xlsx `손익분해PL` 1시트만 cherry-pick 386셀(값 171 + 값_당분기 215), 전부 7사, 나머지 18시트 값 동일(수식·피벗·차트 거부 없음).\n"
"  `panel_compare.json` 55값(보험손익 1 · 투자손익 19 · 당기순이익 18 · ROE 17 중 사별 51 + 그룹 중앙값 4), 사별 값은 전부 7사. `panel_csm_combo.json` 은 PL_breakdown 을 읽지 않아 `--check` 만(불변). 공개본 `손익분해PL` 386셀(7사) + manifest build_id `acdb2fe9`.\n"
"  `check_master_xlsx_drift` RED 1 -> 0 · `validate_data_contract` RED 1 -> 0 · YELLOW 169 불변 · `validate_master_tables --no-build` 요약 불변 · 골든 3종 · `test_rule_coverage_manifest` 104 · live_artifacts RED=0.\n"
"  남은 것: 재커밋 뒤 `export_public_sheets.py` 로 build_id 재생성(HEAD 가 바뀌므로). 증빙 `data/_derived/remaining_20261022/p3_resync/`.\n\n"
)
head = head.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + new, 1)
todo.write_text(head.rstrip("\n") + "\n\n## 열린 일" + rest, encoding="utf-8")
a = arc.read_text(encoding="utf-8")
k = a.index("\n", a.index("## 2026-10-22 밀린 Status")) + 1
a = a[:k] + "\n" + oldest.rstrip("\n") + "\n" + a[k:]
arc.write_text(a, encoding="utf-8")
c = chg.read_text(encoding="utf-8")
anchor = "## 2026-10-22 (오후) — 교보생명(KR0073) 기타포괄손익"
entry = (
"## 2026-10-22 (저녁) — parser `acdb2fe9`(7사 19버킷 최신 비교열 채택: 값 171셀 · 값_당분기 215셀) 파생 산출물 재생성 (커밋 전)\n\n"
"- 시작 진단: `check_master_xlsx_drift` RED 1 = `손익분해PL` 386셀(7사 KR0005 94 · KR0032 72 · KR0070 56 · KR0082 12 · KR0083 40 · KR0087 74 · KR0104 38; 분기 2023.3Q~2024.4Q). `validate_data_contract` RED 1 · YELLOW 169.\n"
"- xlsx: `sync_master_xlsx_sheet.py \"손익분해PL\" --dry-run` 후 실제 실행(행 추가·삭제 0, 13801행 불변). 전 시트 셀 대조(`xlsx_cell_diff.txt`): 변한 셀은 `손익분해PL` 386 뿐이고 전부 7사, 나머지 18시트 동일. 시작 전 xlsx 전체 백업은 세션 scratchpad.\n"
"- 빌더: PL_breakdown 을 읽는 viz 빌더를 grep 으로 확인 -> `viz_build_compare_panel.py` 뿐(`viz_build_csm_waterfall`·`viz_build_ifrs17_panels` 는 주석에만 이름이 나오고 DART 추출물을 읽음, `viz_build_csm_combo_panel`·`build_nb_csm_multiple` 은 안 읽음). compare `--check` 가 어긋남을 확인한 뒤 실행 -> 55값(보험손익 1 · 투자손익 19 · 당기순이익 18 · ROE 17 중 사별 51개는 전부 7사, 나머지 4개는 그룹 중앙값). 재빌드 뒤 `--check` 통과, csm_combo `--check` 도 통과(불변).\n"
"- 공개본: `export_public_sheets.py` 전체 실행 -> 바뀐 파일은 `손익분해PL.json`(386셀, 7사) · manifest(build_id `acdb2fe9`) 뿐(`public_export_diff.txt`). 오케스트레이터가 커밋한 뒤 한 번 더 내보내야 HEAD 와 맞는다.\n"
"- 게이트: drift RED 0 · data_contract RED=0 / YELLOW 169(불변) · validate_master_tables --no-build 요약이 직전 라운드(pv2)와 글자 단위로 동일 · golden fingerprint RED=0 · live_artifacts RED=0(기준선 25) · rule_coverage 104 · master_tables/viz 골든 2종/deploy_assets/push_gate_wiring/loss_unit 통과. 증빙 `data/_derived/remaining_20261022/p3_resync/`.\n\n"
)
i = c.index(anchor)
chg.write_text(c[:i] + entry + c[i:], encoding="utf-8")
