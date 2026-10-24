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
marker = "- **2026-10-23 parser `5419a817`"
i = head.index(marker)
oldest = head[i:].rstrip("\n") + "\n"
head = head[:i]
new = (
"- **2026-10-24 parser `fc41f505`·`a20976cf`·`fb3960f9`·`f25ed8b8`(이웃 낡은 셀 4차례: KB라이프·ABL·농협생명·KB손보·동양·현대해상·한화생명·NH농협손보·DB생명 PL, 롯데 CSM 2023.4Q 항 3·4·5 단분기 비움) 파생 산출물 재생성(커밋 전)** — xlsx 2시트만 cherry-pick: `CSM워터폴` 3셀(롯데 2023.4Q 값_당분기 3 -> 빈칸) · `손익분해PL` 389셀(ABL 144 · NH농협손보 85 · 한화생명 43 · DB생명 40 · 동양 35 · 농협생명 16 · 현대 15 · KB라이프 9 · KB손보 2), 나머지 17시트 값 동일(백업 `insurequant_master_tables.xlsx.bak_20261024_e25`).\n"
"  NB_CSM_multiple.json 0셀(신계약 CSM 항목 2 불변) · `panel_csm_combo.json` 불변 · `panel_compare.json` 2값뿐(NH농협손보 2023.2Q 보험손익 None -> 1,133 · 투자손익 None -> 785억, 최신 분기 아님).\n"
"  `check_master_xlsx_drift` RED 2 -> 0 · `validate_live_artifacts` RED 2(PUBLIC_EXPORT_DRIFT 손익분해PL·CSM워터폴만, 커밋 뒤 `export_public_sheets.py`) · `validate_data_contract` RED=0 · YELLOW 168 · 지문 RED=0 · 골든 3종 · deploy_assets 12 · push_gate_wiring 66 · `test_rule_coverage_manifest` 105 통과 + 1 실패(같은 PUBLIC_EXPORT_DRIFT).\n"
"  화면 노출: compare.html 0값 · index.html 0값 · IFRS17.html 3번 패널(PL 브리지)만 44셀 = ABL 40 · 한화생명 3(2023.4Q) · KB손보 1(2024.4Q 기타사업비용 60,900 -> 빈칸), 1% 넘는 이동 24셀(ABL 2025.4Q 원수 위험조정 단분기 -480 -> 2,316 등). CSM 워터폴·NB·콤보 0값. 증빙 `data/_derived/remaining_20261022/e25_publishing_parser4/`.\n"
"\n"
)
head = head.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + new, 1)
head = head.replace("> 갱신 2026-10-23", "> 갱신 2026-10-24", 1)
wr(todo, head.rstrip("\n") + "\n\n## 열린 일" + rest)

a = rd(arc)
k = a.index("\n", a.index("## 2026-10-22 밀린 Status")) + 1
a = a[:k] + "\n" + oldest.rstrip("\n") + "\n" + a[k:]
wr(arc, a)

c = rd(chg)
anchor = "## 2026-10-23 (밤)"
entry = (
"## 2026-10-24 — parser `fc41f505`·`a20976cf`·`fb3960f9`·`f25ed8b8`(이웃 낡은 셀 정리 1~4차) 파생 산출물 재생성 (커밋 전)\n\n"
"- 시작 진단: `check_master_xlsx_drift` RED 2 = `CSM워터폴` 3셀(롯데 2023.4Q 값_당분기 항 3·4·5, 새 `null_dangi` 로 비움) · `손익분해PL` 389셀(KR0070 144 · KR0032 85 · KR0068 43 · KR0082 40 · KR0087 35 · KR0104 16 · KR0009 15 · KR0099 9 · KR0010 2). 마스터 변경 기준 `77bcc10d..HEAD`: PL 값 174 + 값_당분기 215셀, CSM 3셀.\n"
"- xlsx: 백업 `insurequant_master_tables.xlsx.bak_20261024_e25` -> `--dry-run` 뒤 `CSM워터폴`(3셀) · `손익분해PL`(389셀) 순서로 `sync_master_xlsx_sheet.py`(행 추가·삭제 0, 사후 검증 OK). 전 시트 셀 대조(`xlsx_cell_diff.txt`): 바뀐 시트는 이 둘뿐, 나머지 17시트 동일. drift RED 2 -> 0.\n"
"- NB: `nb_rebuild.py --check`(임시 경로 빌드, 마스터 미접촉) 바뀐 칸 0 -> 갱신 없음. `viz_build_csm_combo_panel --check` 일치(불변). `viz_build_compare_panel` 은 어긋나 재빌드: 2값(NH농협손보 2023.2Q 보험손익·투자손익 None -> 1,133 · 785억), meta·companies·loss_curve 불변(`diff_compare_labeled.txt`). ifrs17 panels·csm_waterfall 빌더는 골든 통과라 재빌드하지 않았다.\n"
"- 노출(`exposure_check.txt`, `exposure_detail.txt`): compare.html 0 · index.html 0 · IFRS17.html 3번 패널 44셀(ABL 40 · 한화생명 2023.4Q 3 · KB손보 2024.4Q 1), 1% 넘는 이동 24셀. 큰 이동: ABL 2025.4Q 원수 위험조정 단분기 -480 -> 2,316 · 2025.2Q -32.3% · 2024.4Q 연도 +11.2%, 한화생명 2023.4Q 원수 예실차 -39,299 -> -24,518(+37.6%) · 기타 생명장기 원수손익 -171,661 -> -186,527(-8.7%), ABL 2025.3Q 기타 생명장기 원수손익 단분기 -5,500 -> 빈칸. 합계가 같은 쌍(위험조정 <-> 기타)의 재배분이 많다.\n"
"- 게이트(`*_after.txt`, `pytest_*.txt`): data_contract RED=0 / YELLOW 168 · validate_master_tables --no-build 요약 pl_bridge 3783P -> 3807P · oci_vs_bs_aoci 101blank -> 95blank(parser 골든과 같음) · 지문 RED=0 · 골든 3종 · deploy_assets 12 · push_gate_wiring 66 · loss_unit_panels 15 · live_artifacts RED 2(PUBLIC_EXPORT_DRIFT 손익분해PL · CSM워터폴) · `test_rule_coverage_manifest` 105 통과 + 1 실패(`test_public_export_clean_state_has_no_findings`, 같은 건).\n"
"- 남은 것: 오케스트레이터 커밋 -> `export_public_sheets.py` -> 재커밋 -> `test_rule_coverage_manifest` 재확인. 증빙 `data/_derived/remaining_20261022/e25_publishing_parser4/`.\n\n"
)
c = c.replace(anchor, entry + anchor, 1)
c = c.replace("> Last updated: 2026-10-23", "> Last updated: 2026-10-24", 1)
wr(chg, c)
print("ok")
