# -*- coding: utf-8 -*-
from pathlib import Path
todo = Path("TODO_publishing.md"); arc = Path("docs/todo_archive_publishing.md"); chg = Path("docs/changelog_publishing.md")
t = todo.read_text(encoding="utf-8")
head, rest = t.split("## 열린 일", 1)
marker = "- **2026-10-19 IFRS17 8절"
i = head.index(marker)
oldest = head[i:].rstrip("\n") + "\n"
head = head[:i]
new = (
"- **2026-10-22 교보생명(KR0073) 마스터 재교정 2건(parser `e01f1395` 기타포괄손익 13셀 · `59e6e459` 17BS 6셀 · 보험계약부채 3셀) 파생 산출물 재생성(커밋 전)** — xlsx 시트 3개만 cherry-pick(`손익분해PL` 31셀 · `17BS` 6셀 · `보험계약부채` 4행 교체=값 3셀+기준표시/비고), 전부 KR0073, 나머지 16시트 값 동일.\n"
"  `panel_csm_combo.json` 3값 + `meta.restated` 1(2023.4Q 소급재작성 표지) · `panel_compare.json` 7값(ROE 4 · 자본 1 · 자산 2), 전부 KR0073. 공개본 3시트(교보 28행) + manifest build_id `9dfd28f9`. `check_master_xlsx_drift` RED 4 -> 0, `validate_data_contract` RED=0 · YELLOW 169 불변,\n"
"  `validate_master_tables --no-build` 불변 · 골든 3종 · `test_rule_coverage_manifest` 104 통과. 남은 것: 재커밋 뒤 `export_public_sheets.py` 로 build_id 재생성(HEAD 가 바뀌므로). 증빙 `data/_derived/remaining_20261022/p2_resync/`.\n\n"
)
j = head.index("- **2026-10-22 교보생명")
head = head[:j] + new + head[j:]
todo.write_text(head.rstrip("\n") + "\n\n## 열린 일" + rest, encoding="utf-8")
a = arc.read_text(encoding="utf-8")
k = a.index("\n", a.index("## 2026-10-22 밀린 Status")) + 1
a = a[:k] + "\n" + oldest.rstrip("\n") + "\n" + a[k:]
arc.write_text(a, encoding="utf-8")
c = chg.read_text(encoding="utf-8")
anchor = "## 2026-10-22 — 교보생명(KR0073) CSM·PL 교정"
entry = (
"## 2026-10-22 (오후) — 교보생명(KR0073) 기타포괄손익 13셀 · 17BS 6셀 · 보험계약부채 3셀(parser `e01f1395` · `59e6e459`) 파생 산출물 재생성 (커밋 전)\n\n"
"- 시작 진단: `check_master_xlsx_drift` RED 4건 = `17BS` 6셀 · `손익분해PL` 31셀(`값_당분기` 비움 8셀 포함) · `보험계약부채` ROW_MISSING/ROW_EXTRA 4행(키에 `기준표시`=`부채 기준` -> `부채 기준(소급재작성)` 이 들어 있어 값이 아니라 행 교체로 나온다). `validate_data_contract` RED 4 · YELLOW 169.\n"
"- xlsx: `sync_master_xlsx_sheet.py` 로 세 시트만(`--dry-run` 먼저). `보험계약부채` 는 스크립트가 delete 4 + insert 4 로 처리(행수 6343 불변), 다른 행은 손대지 않았다. 전 시트 셀 대조(`xlsx_cell_diff.txt`): 변한 셀은 `17BS` 6 · `손익분해PL` 31 · `보험계약부채` 11(값 3 + 기준표시 4 + 비고 4)뿐이고 전부 KR0073, 나머지 16시트 동일. 수식·피벗·차트 거부 사유 없음.\n"
"- 빌더(`--check` 가 둘 다 어긋남을 확인한 뒤 실행): `viz_build_csm_combo_panel.py` -> 3값(KR0073 2023.4Q: 보험계약부채 875333.4 -> 872428.79, 합 848405.9 -> 845501.32, 반올림 26927.46 -> .47) + `meta.restated.KR0073.2023.4Q`; `viz_build_compare_panel.py` -> 7값(ROE 4 · 자산 2 · 자본 1), 전부 KR0073. `viz_build_ifrs17_panels`·`viz_build_csm_waterfall` 은 두 마스터를 읽지 않아 재생성하지 않았다. 재빌드 뒤 `--check` 둘 다 통과.\n"
"- 공개본: `export_public_sheets.py` 전체 실행 -> 바뀐 파일은 `손익분해PL`(18행) · `17BS`(6행) · `보험계약부채`(4행) · manifest 뿐(전부 교보생명보험, `public_export_diff.txt`). build_id 는 실행 시점 HEAD(`9dfd28f9`)라 오케스트레이터가 커밋한 뒤 한 번 더 내보내야 HEAD 와 맞는다.\n"
"- 게이트: drift RED 0 · data_contract RED=0 / YELLOW 169(불변) · validate_master_tables --no-build 요약 불변 · live_artifacts RED=0(기준선 25) · rule_coverage 104 통과 · master_tables/viz 골든 2종/deploy_assets/push_gate_wiring/loss_unit 통과. 증빙 `data/_derived/remaining_20261022/p2_resync/`.\n\n"
)
i = c.index(anchor)
chg.write_text(c[:i] + entry + c[i:], encoding="utf-8")
