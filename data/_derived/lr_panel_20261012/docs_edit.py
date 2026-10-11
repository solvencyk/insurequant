from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
todo_p = R/"TODO_publishing.md"; arc_p = R/"docs/todo_archive_publishing.md"; cl_p = R/"docs/changelog_publishing.md"
todo = todo_p.read_bytes().decode("utf-8")
start = todo.index("- **2026-10-11 보험계약부채 시트 신설**")
end = todo.index("## 열린 일")
block = todo[start:end].rstrip("\n") + "\n\n"
new_status = (
"- **2026-10-12 재보사 손해율 패널·xlsx 동기화(커밋만 · push 보류)** — `panel_loss_ratio.json` 37→44사(재보사 7곳 추가·기존 37사 바이트 동일)+최상위 `ae` 블록(예실차 162행·44사), xlsx `손해율` +1,904행(변경 셀 0).\n"
"  남은 것: ① designer 가 `ae` 를 화면에 표시(`meta.note` 참조) ② 예실차(`claims_ae_ratio.json`)·긴 형식 표(`risk_premium_vs_expected_claims.json`)는 xlsx 시트가 없다 → 신설은 owner 승인(`build_master_xlsx.py` 스키마) ③ `public_exports/` 는 다른 마스터가 끝난 뒤 마감 라운드에서.\n\n")
marker = "## Status (최신 3개)\n\n"
todo2 = todo[:start] + todo[end:]
todo2 = todo2.replace(marker, marker + new_status, 1)
todo2 = todo2.replace("> 갱신 2026-10-11 ·", "> 갱신 2026-10-12 ·", 1)
todo_p.write_bytes(todo2.encode("utf-8"))
arc = arc_p.read_bytes().decode("utf-8")
head = "# TODO archive — `TODO_publishing.md` (Status 이력, 읽기 지연)\n\n"
assert arc.startswith(head.replace("
","
"))
arc_p.write_bytes((head + block + arc[len(head):]).encode("utf-8"))
cl = cl_p.read_bytes().decode("utf-8")
m = "---\n\n## 2026-10-11 — 미니 재동기화"
assert m in cl
entry = ("---\n\n## 2026-10-12 — 재보사 손해율 패널 확장 + 예실차 블록 + xlsx `손해율` 동기화 (커밋만, push·배포 보류)\n\n"
"- `scripts/viz_build_persistency_lossratio_panels.py`: `build_ae()` 추가(읽기 `data/loss_ratio/claims_ae_ratio.json`). 패널 최상위에 `ae` 블록: "
"`ae[회사코드]={n, q:{공시분기:[[기준연도, 사업구분, 예상손해율%, 실제손해율%, 예실차비율%p, [플래그]]]}}` — 값은 마스터 그대로, 공시값 '-'는 null, "
"플래그는 마스터 `플래그` + `identity_break`/`dash`. `companies` 처리 코드는 바꾸지 않았다(재보사는 마스터에 행이 들어와 자동 편입).\n"
"- 패널 전후: 37사→44사(+KR1101~1107), 크기 180,325→206,065 바이트, `meta.quarters` 불변. 기존 37사 `companies` 항목 37/37 바이트 동일, `panel_persistency.json` 바이트 동일, `ae` 162행이 마스터와 불일치 0. `--check` OK.\n"
"- xlsx `손해율` 시트: 36,344→38,248행(+1,904, 변경 셀 0, 삭제 0), 나머지 시트 값 동일(sync 사후검증 OK). 백업 `insurequant_master_tables.xlsx.bak_20261012_lossratio`. "
"예실차·긴 형식 표용 시트는 `MASTERS` 에 없다(신설은 owner 승인 사항, 이번엔 안 만듦).\n"
"- 검증: `test_push_gate_wiring` 65 passed·`test_deploy_assets` 12 passed. `check_master_xlsx_drift`/`validate_data_contract` 의 RED 는 전부 다른 레인이 쓰는 중인 마스터"
"(PL_breakdown 3종 112건·MASTER_XLSX_ROW_MISSING 6시트=17BS·가정민감도·CSM워터폴·CSM상각·손익분해PL·보험계약부채)이고 손해율·유지율은 0. `public_exports/` 는 이번에 재생성하지 않았다.\n"
"- 원자료·스크립트: `data/_derived/lr_panel_20261012/`.\n\n")
cl_p.write_bytes(cl.replace(m, entry + m[4:], 1).encode("utf-8"))
