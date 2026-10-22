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
marker = "- **2026-10-22 교보생명(KR0073) 마스터 재교정 2건"
i = head.index(marker)
oldest = head[i:].rstrip("\n") + "\n"
head = head[:i]
new = (
"- **2026-10-23 parser `afea4342`(READY-25 최신 비교열 · 9사 KR0001 KR0003 KR0010 KR0068 KR0070 KR0079 KR0083 KR0099 KR0104 · PL 440 + CSM 55셀) 파생 산출물 재생성(커밋 전)** — xlsx 3시트만 cherry-pick: `CSM워터폴` 132셀 · `손익분해PL` 1,045셀 · `신계약CSM배수` 20셀(NB_CSM_multiple.json 20셀을 셀 단위로 갱신, 메리츠 KR0001·한화생명 KR0068 2023.1Q~3Q뿐), 나머지 16시트 값 동일(수식·피벗·차트 거부 없음, 백업 `insurequant_master_tables.xlsx.bak_20261023_ready25`).\n"
"  `panel_compare.json` 사별 91값 + 손보 ROE 중앙값 1(기말 CSM 11 · 보험손익 20 · 투자손익 22 · 당기순이익 22 · ROE 8 · 신계약CSM 4 · 배수 4, 큰 이동 한화생명 신계약CSM 2023.2Q 13,592 -> 11,643억, 메리츠 기말 CSM 2023.2Q 100,684 -> 97,015억), `panel_csm_combo.json` 20값(신계약 CSM 6 + 대조 메타 `csm_mismatch` 4 -> 3). 공개본 `손익분해PL` 1,045 · `CSM워터폴` 132 · manifest build_id `afea4342`.\n"
"  `check_master_xlsx_drift` RED 2 -> 0 · `validate_live_artifacts` RED 6 -> 0(NB_VS_WATERFALL 4 + PUBLIC_EXPORT_DRIFT 2) · `validate_data_contract` RED=0 · YELLOW 169 불변 · `validate_master_tables --no-build` 요약이 parser 골든과 동일 · 골든 3종 · `test_rule_coverage_manifest` 104 · deploy_assets 12 · push_gate_wiring 66.\n"
"  화면 노출: compare.html 0값 · CSM 워터폴/NB/콤보 0값 · IFRS17.html 3번 패널(PL 연도모드 4Q) 39셀만(KB손보 2023.4Q 15 · 미래에셋 2023.4Q 11 · 푸본현대 2024.4Q 10 · ABL 2024.4Q 3). 남은 것: 커밋 뒤 `export_public_sheets.py` 재실행(신계약CSM배수 20셀 + build_id). 증빙 `data/_derived/remaining_20261022/e21_ready25/p5_resync/`.\n\n"
)
head = head.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + new, 1)
wr(todo, head.rstrip("\n") + "\n\n## 열린 일" + rest)
a = rd(arc)
k = a.index("\n", a.index("## 2026-10-22 밀린 Status")) + 1
a = a[:k] + "\n" + oldest.rstrip("\n") + "\n" + a[k:]
wr(arc, a)

c = rd(chg)
anchor = "## 2026-10-23 — parser `5419a817`"
entry = (
"## 2026-10-23 (오전) — parser `afea4342`(READY-25: 9사 최신 비교열 채택, PL 440셀 + CSM 55셀) 파생 산출물 재생성 (커밋 전)\n\n"
"- 시작 진단: `check_master_xlsx_drift` RED 2 = `CSM워터폴` 132셀(KR0001 29 · KR0003 40 · KR0068 36 · KR0079 27; 값 55 + 값_당분기 77) · `손익분해PL` 1,045셀(KR0001 145 · KR0003 266 · KR0010 249 · KR0068 115 · KR0070 6 · KR0079 119 · KR0083 20 · KR0099 9 · KR0104 116; 값 440 + 값_당분기 605). `validate_live_artifacts` RED 6 = NB_VS_WATERFALL 4(KR0001·KR0068 2023.1Q/2Q) + PUBLIC_EXPORT_DRIFT 2. HEAD = `afea4342`, 마스터는 커밋 상태(`csm_pl_item_diff.txt`).\n"
"- NB_CSM_multiple.json: `build_nb_csm_multiple.py` 는 통째 덮어쓰는 빌더라 임시 경로로만 돌려(`nb_rebuild.py --check`, 마스터 미접촉) 커밋본과 비교했다 -> 바뀐 칸 20 = KR0001 10 · KR0068 10(2023.1Q 8 · 2023.2Q 8 · 2023.3Q 4; 신계약CSM_연누계 4 · 당분기 6 · 배수 연누계 4 · 당분기 6), 키·행수 393 동일. 그 20칸만 셀 단위로 썼다(`--apply`, 현재 값 == HEAD 값 가드, 디스크 직렬화 == 재직렬화 확인). 나머지 7사(KR0003 KR0010 KR0070 KR0079 KR0083 KR0099 KR0104)는 CSM 항목 2 가 안 바뀌어 NB 불변. 예: 한화생명 2023.2Q 연누계 13,592.2 -> 11,643.1억(배수 9.89 -> 8.47), 메리츠 2023.1Q 4,282.7 -> 4,171.8억(14.82 -> 14.44).\n"
"- xlsx: 시작 전 `insurequant_master_tables.xlsx.bak_20261023_ready25` 백업 -> `CSM워터폴` · `손익분해PL` · `신계약CSM배수` 순으로 `--dry-run` 뒤 실행(변경 셀 132 / 1,045 / 20, 행 추가·삭제 0, 스크립트 사후 검증 OK). 전 시트 셀 대조(`xlsx_cell_diff.txt`): 바뀐 시트는 이 3개뿐이고 전부 대상 9사, 나머지 16시트 동일.\n"
"- 빌더: compare `--check` · csm_combo `--check` 둘 다 어긋남 확인(rc 1) 뒤 실행, 재빌드 뒤 `--check` 통과. `panel_compare.json` 91값 + ROE 손보 중앙값 1(2024.1Q 12.7 -> 12.2); meta·companies·loss_curve 불변(`diff_compare_labeled.txt`). 회사는 KR0001 KR0003 KR0010 KR0068 KR0079 KR0083 KR0104(KR0070·KR0099 는 compare 지표가 아니거나 반올림 안에서 같음). 큰 이동(억원): 메리츠 기말 CSM 2023.1Q 100,034 -> 96,454 · 2023.2Q 100,684 -> 97,015, 한화생명 신계약CSM 2023.2Q 13,592 -> 11,643 · 당기순이익 2023.1Q 3,569 -> 4,709 · 투자손익 2023.1Q/2Q 빈칸 -> 4,304/3,491, KB손보 투자손익 2023.4Q 2,105 -> 1,577, 농협생명 보험손익 2023.1Q/2Q 빈칸 -> 986/1,917, 미래에셋 투자손익 2023.4Q △22 -> △226. `panel_csm_combo.json` 20값 = KR0001 3 · KR0068 3 신계약 CSM + `meta.csm_mismatch` 4 -> 3건(롯데 2024.3Q 대조 불일치 해소) + 대조 문구(`diff_csm_combo.txt`). `viz_build_ifrs17_panels`·`viz_build_csm_waterfall` 은 DART 추출물을 읽어 재생성 없음(골든 통과, `data/dart/viz` 변경 0).\n"
"- 공개본: `export_public_sheets.py` 전체 실행(HEAD `afea4342`) -> 바뀐 파일은 `손익분해PL.json`(1,045셀 = 값 440 + 값_당분기 605, 9사) · `CSM워터폴.json`(132셀 = 값 55 + 값_당분기 77, 4사) · manifest(build_id `5419a817` -> `afea4342`) 뿐(`public_export_diff.txt`). `신계약CSM배수.json` 은 NB 마스터가 아직 미커밋이라 불변(0셀) -> 커밋 뒤 재실행해야 20셀과 build_id 가 맞는다.\n"
"- 노출 확인(`exposure_check.txt`): compare.html 은 지표마다 마지막 비null 값만 쓰는데 바뀐 91값 중 그에 해당하는 것 0. IFRS17.html CSM 워터폴(연도모드=최신+직전 3개 연말 `값`, 분기모드=최근 5분기 `값_당분기`) 0셀: 4Q 에서 바뀐 11셀(KR0003 2024.4Q · KR0068 2023.4Q · KR0079 2024.4Q)은 전부 `값_당분기`. NB 배수 패널·콤보 신계약 CSM(2023.1Q~3Q) 0셀. PL 3번 패널(연도모드=각 4Q+최신 `값`)에는 39셀이 표에 든다 = KB손보 2023.4Q 15 · 미래에셋 2023.4Q 11 · 푸본현대 2024.4Q 10 · ABL 2024.4Q 3. 나머지 2023.1Q~2024.3Q 값은 공개 다운로드(엑셀·공개 JSON)와 패널 JSON 안에만 있다.\n"
"- 게이트(`run_gates.log`·`*_after.txt`): drift RED 2 -> 0(드리프트 셀 1,177 -> 0) · live_artifacts RED 6 -> 0(기준선 YELLOW 25 불변) · data_contract RED=0 / YELLOW 169 · validate_master_tables --no-build SUMMARY 가 parser 골든(pl_bridge 3755P/18F · csm_amort_identity 388P/4S · qoq_warn 263Y · oci_vs_bs_aoci 26Y)과 동일 · golden fingerprint RED=0 · master_tables/viz 골든 2종 통과 · rule_coverage 104 · deploy_assets 12 · push_gate_wiring 66(1 skip) · loss_unit 15. 게이트 실행 뒤 추적 파일 추가 변경 없음(`qoq_warn.json`·`pl_oci_vs_bs_aoci_warn.json` 불변). 증빙 `data/_derived/remaining_20261022/e21_ready25/p5_resync/`.\n\n"
)
i = c.index(anchor)
wr(chg, c[:i] + entry + c[i:])
