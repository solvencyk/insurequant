# -*- coding: utf-8 -*-
from pathlib import Path
def rd(p): return Path(p).read_text(encoding="utf-8")
def wr(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f: f.write(s)
todo = "TODO_publishing.md"; arc = "docs/todo_archive_publishing.md"; chg = "docs/changelog_publishing.md"
t = rd(todo)
head, rest = t.split("## 열린 일", 1)
marker = "- **2026-10-22 교보생명(KR0073) 마스터 교정(parser `3e53aef8`)"
i = head.index(marker)
oldest = head[i:].rstrip("\n") + "\n"
head = head[:i]
new = (
"- **2026-10-23 parser `5419a817`(최신 비교열 21버킷 · 11사 KR0032 KR0068 KR0069 KR0070 KR0071 KR0072 KR0082 KR0083 KR0087 KR0094 KR0104 · 값 84 + 값_당분기 110셀) 파생 산출물 재생성(커밋 전)** — xlsx `손익분해PL` 1시트만 cherry-pick 194셀(전부 11사, 13801행 불변), 나머지 18시트 값 동일(수식·피벗·차트 거부 없음, 백업 `insurequant_master_tables.xlsx.bak_20261023_pl_e20`).\n"
"  `panel_compare.json` 9값뿐(보험손익 3 · 투자손익 4 · 당기순이익 1 · ROE 1 = NH농협손보 2023.1Q · DB생명 2023.1Q/2Q · 푸본현대 2024.3Q), 중앙값·메타 불변. `panel_csm_combo.json` 은 `--check` 만(불변). 공개본 `손익분해PL` 194셀(11사) + manifest build_id `5419a817`.\n"
"  `check_master_xlsx_drift` RED 1 -> 0 · `validate_data_contract` RED=0 · YELLOW 169 불변 · `validate_master_tables --no-build` 요약은 직전과 같고 `oci_vs_bs_aoci` 23Y -> 21Y 만 달라짐(parser 쪽 실측과 동일) · 골든 3종 · `test_rule_coverage_manifest` 104 · live_artifacts RED=0.\n"
"  2023.1Q/2Q 바뀐 값은 화면에 안 나온다(compare.html 은 최신 분기만 · IFRS17.html 표는 4Q+최신 / 최근 5분기 창). 남은 것: 재커밋 뒤 `export_public_sheets.py` 로 build_id 재생성. 증빙 `data/_derived/remaining_20261022/e20_held_and_remaining/p4_resync/`.\n\n"
)
head = head.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + new, 1)
head = head.replace("> 갱신 2026-10-22 ·", "> 갱신 2026-10-23 ·", 1)
wr(todo, head.rstrip("\n") + "\n\n## 열린 일" + rest)
a = rd(arc)
k = a.index("\n", a.index("## 2026-10-22 밀린 Status")) + 1
a = a[:k] + "\n" + oldest.rstrip("\n") + "\n" + a[k:]
wr(arc, a)
c = rd(chg)
anchor = "## 2026-10-22 (저녁) — parser `acdb2fe9`"
entry = (
"## 2026-10-23 — parser `5419a817`(11사 21버킷 최신 비교열 채택: 값 84셀 · 값_당분기 110셀) 파생 산출물 재생성 (커밋 전)\n\n"
"- 시작 진단: `check_master_xlsx_drift` RED 1 = `손익분해PL` 194셀(11사 KR0032 8 · KR0068 30 · KR0069 20 · KR0070 15 · KR0071 25 · KR0072 6 · KR0082 16 · KR0083 16 · KR0087 28 · KR0094 9 · KR0104 21; 분기 2023.1Q 16 · 2023.2Q 8 · 2024.3Q 8 · 2024.4Q 38 · 2025.1Q 46 · 2025.2Q 52 · 2025.3Q 26). HEAD = `5419a817`, 마스터는 커밋 상태.\n"
"- xlsx: 시작 전 `insurequant_master_tables.xlsx.bak_20261023_pl_e20` 백업 -> `sync_master_xlsx_sheet.py \"손익분해PL\" --dry-run` 후 실행(행 추가·삭제 0, 13801행 불변, 스크립트 사후 검증 OK). 전 시트 셀 대조(`xlsx_cell_diff.txt`): 변한 셀은 `손익분해PL` 194 뿐이고 전부 11사, 나머지 18시트 동일.\n"
"- 빌더: `viz_build_compare_panel.py` `--check` 가 어긋남을 확인한 뒤 실행 -> 9값(보험손익 3 · 투자손익 4 · 당기순이익 1 · ROE 1; NH농협손보 2023.1Q, DB생명 2023.1Q/2Q, 푸본현대 2024.3Q). meta·companies·loss_curve·중앙값 불변(`diff_compare_labeled.txt`). 나머지 194셀 중 대부분은 compare 지표(항목 1·17·24)가 아니거나 억원 반올림 안에서 같아 패널이 안 바뀐다. `viz_build_csm_combo_panel` `--check` 불변, `viz_build_ifrs17_panels`·`viz_build_csm_waterfall` 은 PL 마스터를 안 읽어(DART 추출물) 재생성 없음, 골든 통과.\n"
"- 공개본: `export_public_sheets.py` 전체 실행(HEAD `5419a817`) -> 바뀐 파일은 `손익분해PL.json`(194셀, 11사) · manifest(build_id `5419a817`) 뿐(`public_export_diff.txt`). 커밋하면 HEAD 가 바뀌므로 한 번 더 내보내야 build_id 가 맞는다.\n"
"- 노출 확인(`exposure_check.txt`): compare.html 은 사별 최신 분기 값만 쓰고(분기 선택기 없음, 세 회사 모두 2026.2Q 값 있음) IFRS17.html 3번 패널은 `PL_breakdown.json` 을 직접 읽어 연도모드=각 4Q+최신 `값`, 분기모드=최근 5분기 `값_당분기` 를 그린다. 바뀐 194셀 중 표 창에 드는 것은 67셀(2024.4Q `값` 15 · 최근 5분기 `값_당분기` 52), 2023.1Q/2Q 3개 회사분기(NH농협손보 2023.1Q, DB생명 2023.1Q/2Q)는 표·차트에 안 나오고 공개 다운로드(엑셀·`손익분해PL.json`)와 패널 JSON 안에만 있다.\n"
"- 게이트: drift RED 0 · data_contract RED=0 / YELLOW 169(불변) · validate_master_tables --no-build 요약이 p3 와 같고 `oci_vs_bs_aoci` 23Y -> 21Y 만 다름(parser e20 `gates_after` 와 동일) · golden fingerprint RED=0 · live_artifacts RED=0(기준선 25) · rule_coverage 104 · master_tables/viz 골든 2종/deploy_assets/push_gate_wiring/loss_unit 통과. 게이트 실행 뒤 추적 파일 변경 없음. 증빙 `data/_derived/remaining_20261022/e20_held_and_remaining/p4_resync/`.\n\n"
)
i = c.index(anchor)
wr(chg, c[:i] + entry + c[i:])
