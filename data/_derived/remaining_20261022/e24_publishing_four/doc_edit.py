# -*- coding: utf-8 -*-
from pathlib import Path


def rd(p):
    return Path(p).read_text(encoding="utf-8")


def wr(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


todo = "TODO_publishing.md"
arc = "docs/todo_archive_publishing.md"
chg = "docs/changelog_publishing.md"
t = rd(todo)
head, rest = t.split("## 열린 일", 1)
marker = "- **2026-10-22 parser `acdb2fe9`"
i = head.index(marker)
oldest = head[i:].rstrip("\n") + "\n"
head = head[:i]
new = (
"- **2026-10-23 parser `b1187788`+`90be97e7`(최신 비교열 4사 KR0099 KR0003 KR0070 KR0009 · PL 209 + CSM 58셀, 단분기 포함 마스터 PL 466 · CSM 124셀) 파생 산출물 재생성(커밋 전)** — xlsx 3시트만 cherry-pick: `CSM워터폴` 124셀(KR0003 9 · KR0009 38 · KR0070 43 · KR0099 34) · `손익분해PL` 466셀(30 · 135 · 158 · 143) · `신계약CSM배수` 24셀(KR0009 10 · KR0070 14), 나머지 16시트 값 동일(백업 `insurequant_master_tables.xlsx.bak_20261023_four_d1d3`).\n"
"  NB_CSM_multiple.json 24셀만 셀 단위(가드)로 갱신: ABL 2023.1Q~4Q · 현대해상 2023.1Q~3Q, KB라이프·롯데손보는 신계약 CSM(항목 2)이 안 바뀌어 0셀. `panel_compare.json` 사별 52값(기말 CSM 10 · 배수 5 · 신계약CSM 5 · 보험손익 10 · 투자손익 11 · 당기순이익 11, 큰 이동 현대해상 기말 CSM 2023.2Q 91,361 -> 85,984억 · 2023.1Q 89,209 -> 84,533억, ABL 2023.3Q 9,731 -> 8,439억), `panel_csm_combo.json` 7값(신계약 CSM, 메타 불변).\n"
"  `check_master_xlsx_drift` RED 2 -> 0 · `validate_live_artifacts` RED 7 -> 2(NB_VS_WATERFALL 5 해소, 남은 2 = PUBLIC_EXPORT_DRIFT 124·466셀, 커밋 뒤 `export_public_sheets.py`) · `validate_data_contract` RED=0 · `validate_master_tables --no-build` · 골든 3종 · 지문 RED=0 · `test_rule_coverage_manifest` 104 통과 + 1 실패(같은 PUBLIC_EXPORT_DRIFT, 재내보내기 뒤 해소 예정) · deploy_assets 12 · push_gate_wiring 66.\n"
"  화면 노출: compare.html 0값(지표마다 마지막 값만 그림, 꺾은선은 손해율 곡선뿐) · index.html 버블맵 0값(최신 분기만) · IFRS17.html 연도모드 2023.4Q 만 보임 = CSM 워터폴 11셀(롯데 5 · 현대 4 · ABL 2) + PL 3번 패널 40셀(롯데 18 · 현대 11 · ABL 11), KB라이프 0. 분기모드·NB 패널·콤보 0값. 증빙 `data/_derived/remaining_20261022/e24_publishing_four/`.\n"
"\n"
)
head = head.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + new, 1)
wr(todo, head.rstrip("\n") + "\n\n## 열린 일" + rest)

a = rd(arc)
k = a.index("\n", a.index("## 2026-10-22 밀린 Status")) + 1
a = a[:k] + "\n" + oldest.rstrip("\n") + "\n" + a[k:]
wr(arc, a)

c = rd(chg)
anchor = "## 2026-10-23 (오전) — parser `afea4342`"
entry = (
"## 2026-10-23 (밤) — parser `b1187788`·`90be97e7`(4사 KB라이프 KR0099 · 롯데손보 KR0003 · ABL KR0070 · 현대해상 KR0009 최신 비교열 채택) 파생 산출물 재생성 (커밋 전)\n\n"
"- 시작 진단: `check_master_xlsx_drift` RED 2 = `CSM워터폴` 124셀(KR0003 9 · KR0009 38 · KR0070 43 · KR0099 34) · `손익분해PL` 466셀(KR0003 30 · KR0009 135 · KR0070 158 · KR0099 143), 분기 2023.1Q~4Q(`csm_pl_item_diff.txt`, 기준 `d5077c7b`). `validate_live_artifacts` RED 7 = NB_VS_WATERFALL 5(KR0070 2023.1Q~3Q · KR0009 2023.1Q/2Q) + PUBLIC_EXPORT_DRIFT 2. KDB생명은 보류라 손대지 않았다.\n"
"- NB_CSM_multiple.json: `build_nb_csm_multiple.py` 는 통째 덮어쓰는 빌더라 임시 경로로만 돌려(`nb_rebuild.py --check`, 마스터 미접촉) 커밋본과 비교했다 -> 바뀐 칸 24 = KR0009 10(2023.1Q~3Q) · KR0070 14(2023.1Q~4Q); KR0099·KR0003 은 신계약 CSM(항목 2)이 안 바뀌어 0칸(`nb_four_company_report.txt`). 24칸만 가드(현재 칸 == 커밋 값)를 걸어 셀 단위로 썼고 사후 임시 빌드와 전체 일치(`nb_apply.txt`).\n"
"- xlsx: 시작 전 `insurequant_master_tables.xlsx.bak_20261023_four_d1d3` 백업 -> `CSM워터폴` · `손익분해PL` · `신계약CSM배수` 순으로 `--dry-run` 뒤 실행(변경 셀 124 / 466 / 24, 행 추가·삭제 0, 사후 검증 OK). 전 시트 셀 대조(`xlsx_cell_diff.txt`): 바뀐 시트는 이 3개뿐이고 전부 4사(신계약CSM배수는 2사), 나머지 16시트 동일.\n"
"- 빌더: compare `--check` · csm_combo `--check` 둘 다 어긋남(rc 1) 확인 뒤 실행, 재빌드 뒤 `--check` 통과. `panel_compare.json` 52값(기말 CSM 10 · 배수 5 · 신계약CSM 5 · 보험손익 10 · 투자손익 11 · 당기순이익 11; 이 중 None -> 값 8 = KB라이프·ABL·현대해상 2023.1Q/2Q 보험·투자손익), meta·companies·loss_curve·중앙값 불변(`diff_compare_labeled.txt`). `panel_csm_combo.json` 7값(현대해상 2023.1Q~3Q · ABL 2023.1Q~4Q 신계약 CSM), 메타 불변(`diff_csm_combo.txt`). 큰 이동(억원): 현대해상 기말 CSM 2023.2Q 91,361 -> 85,984 · 2023.1Q 89,209 -> 84,533, ABL 2023.3Q 9,731 -> 8,439, 현대해상 보험손익 2023.2Q 4,995 -> 4,157, 당기순이익 2023.2Q 5,780 -> 4,970, 투자손익 2023.4Q 4,999 -> 4,550, 롯데손보 투자손익 2023.4Q -722 -> -861. `viz_build_ifrs17_panels`·`viz_build_csm_waterfall` 은 골든이 입력 지문 일치 + 산출 해시 통과라 재빌드하지 않았다.\n"
"- 공개본: `export_public_sheets.py` 는 실행하지 않았다(HEAD 를 읽고 NB 마스터가 미커밋). 커밋 뒤 재실행하면 `CSM워터폴` 124 · `손익분해PL` 466 · `신계약CSM배수` 24셀 + build_id 가 바뀐다.\n"
"- 노출 확인(`exposure_check.txt`, `latest_q_check.txt`): 4사 모두 최신 분기 2026.2Q. compare.html 은 지표마다 마지막 값만 막대로 그리고 꺾은선은 손해율 경과차년 곡선뿐이라 바뀐 52값 중 노출 0(작업 지시문의 14분기 추세선 가정은 HTML 을 읽어 정정). index.html 버블맵은 회사별 최신 분기만 써 0. IFRS17.html 은 연도모드(최신 + 직전 3개 연말 `값`)에서 2023.4Q 가 보여 CSM 워터폴 11셀(롯데 5 · 현대 4 · ABL 2)과 PL 3번 패널 40셀(롯데 18 · 현대 11 · ABL 11)이 바뀐다. KB라이프는 2023.4Q `값` 이 안 바뀌어 0. 분기모드(최근 5분기)·NB 패널(연도모드는 4Q `연누계`, 불변)·콤보는 0.\n"
"- 게이트(`run_gates.log`·`*_after.txt`): drift RED 2 -> 0(드리프트 셀 590 -> 0) · live_artifacts RED 7 -> 2(PUBLIC_EXPORT_DRIFT 만, NB_VS_WATERFALL 사라짐) · data_contract RED=0 / YELLOW 168 · validate_master_tables --no-build 요약 coverage_hole 0 · closing 393P · pl_bridge 3783P/18F · 골든 지문 RED=0 · master_tables/viz_ifrs17/viz_csm_waterfall 골든 통과 · `test_rule_coverage_manifest` 104 통과 + 1 실패(`test_public_export_clean_state_has_no_findings`, 같은 PUBLIC_EXPORT_DRIFT) · deploy_assets 12 · push_gate_wiring 66 · loss_unit_panels 15. `check_csm_coverage` KR1098 2023.4Q 는 기존 건이라 건드리지 않았다.\n"
"- 남은 것: 오케스트레이터가 마스터·패널·xlsx 를 커밋 -> `export_public_sheets.py`(PYTHONUTF8=1) -> 재커밋 -> `test_rule_coverage_manifest` 재확인. 증빙 `data/_derived/remaining_20261022/e24_publishing_four/`.\n\n"
)
c = c.replace(anchor, entry + anchor, 1)
c = c.replace("> Last updated: 2026-10-22", "> Last updated: 2026-10-23", 1)
wr(chg, c)
print("ok")
