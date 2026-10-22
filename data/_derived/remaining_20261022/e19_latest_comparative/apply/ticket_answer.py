from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/inbox/parser/20261022T0900Z__orchestrator__MULTI_2023.3Q-2024.3Q__latest_comparative_19_buckets.md")
raw = p.read_bytes(); crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
assert s.count("status: open") == 1
s = s.replace("status: open", "status: answered", 1)
ANS = """
**결과: 19버킷 전부 적재(parser/ifrs17, 2026-10-22). 보류 버킷 0, 보류 1칸(농협생명 2023.3Q 항목 32).** 커밋·push 안 함. 증거·재현 `data/_derived/remaining_20261022/e19_latest_comparative/apply/`(`INDEX.txt`).

**owner 질문(「재공시 vs 현행 공시 충돌 RED 는 없다고 했는데 왜 또 고치나」)**: RED 가 있어서 고친 것이 아니다. 게이트는 한 판(원 공시 한 벌) 안의 산술만 보므로 옛 값과 새 값이 각자 닫혀 RED 가 없었고 지금도 없다(적재 전후 RED 변화는 xlsx 동기화 지연 1건뿐). 이번 일은 owner 결정(2026-10-22 「교보처럼 최신 비교열로」)에 따른 갱신이다. 되돌리고 싶으면 `e19_apply.py --revert --apply`.

1. **재독**: 계획서 7개의 172칸을 필링 XML 줄에서 독립 코드(`e19_verify_plans.py`)로 다시 읽어 값·단위·행 라벨·열(ACONTEXT 또는 행 위치)·옛 값=라이브 마스터·gold 비겹침을 확인했다 172/172 일치. 이음매 3개월 열 20/20(`e19_verify_seams.py`).
2. **적재**: gold `user_pl_cells.json` set +171(495→666; 마스크 29 불변·새 박제 없음; 기존 항목 수정 0) · `null_dangi` +17(NH농협손보 2023.4Q 8, 동양 2023.4Q 9) · `set_dangi` +20(흥국 2023.3Q 4, DB생명 2023.3Q 4, 푸본현대 2024.3Q 8, 농협생명 2023.3Q 4). 마스터는 실제 `build_pl()` 을 옛 gold/새 gold 로 두 번 돌려 달라진 235칸(값 171 + 값_당분기 215, 중복 포함)만 반영했다. 계획서가 적은 단일분기 244개와 빌드가 0건 다르다. 출처표 19블록 + 병합 노트 키, `GOLD_OVERLAY_CENSUS` PL (666, 29).
3. **독립 diff(git HEAD 대비, `e19_diff_vs_head.txt`) ALL PASS**: 7사 밖 변경 0, 값·값_당분기 외 필드 0, gold 기존 항목 불변, 출처표는 7사 19블록만.
4. **제외 1칸**: 농협생명 2023.3Q 항목 32(−3,080.0 → −3,080.034). 반올림 차이뿐인데 gold 값이 빌더 소스와 0.05 이내면 「마스크 칸」이 되어 등재부 박제가 있어야 `test_gold_overlay_every_masked_cell_is_pinned` 가 통과한다. 박제는 하지 않고 원 인쇄값을 뒀다(항목 25 − 부분합 잔차 0.034 백만원; 나머지 17칸은 정확히 닫힘).
5. **동양생명 2024.3Q**: 후속 공시가 백만원 반올림으로만 인쇄해 항등식 잔차가 최대 0.50 백만원(20=1+17 0.17 · 22=20+21 0.50 · 17=18+19 0.44)이다. 더 정밀한 원천이 없다. 게이트 허용오차(200) 안.
6. **인접 분기**: 계획서 제안대로 이음매는 3개월 열 인쇄값(`set_dangi`), 없으면 공란(`null_dangi`). 푸본현대 2024.3Q 8칸의 `set_dangi` 는 값_당분기만 건드리고 owner gold(항목 27·28·30 값)는 그대로다; gold 인접 칸을 보호 대상으로 보면 항목 27 한 칸을 `null_dangi` 로 바꾸면 된다. 푸본현대 2024.4Q·DB생명 2023.1Q·2Q·농협생명 2023.1Q·2Q 는 승인 범위 밖이라 옛 판 그대로다.
7. **화면(누계, 억원, 19버킷)**: 투자손익 −417.2~+585.8 · 당기순이익 −320.8~+450.5 · 기타포괄손익 −33.5~+320.8 · 보험손익은 DB생명 2023.3Q +18.9(투자손익 −18.9 재분류)만 변동. 총포괄손익은 보험금융 배분 변경 5사 불변, 오류 정정인 흥국화재(+43.2/+78.6/−11.6/−24.5)와 농협생명 2023.3Q(순이익 +450.5)만 이동. 버킷별 전후 표 `onscreen_eok.txt`.
8. **게이트 전→후**(`gates_compare.txt`): 데이터계약 RED 0→1(MASTER_XLSX_DRIFT 손익분해PL, publishing 동기화로 해소) · master_tables SUMMARY 동일(pl_bridge 3697P/23F 불변, oci_vs_bs_aoci 23건 집합만 교체, tax22 「최신 비교열로만 통과」 4→22, 골든 `--update` 불필요) · 연속성·워터폴·NB·live_artifacts 불변 · 지문 RED 0. 테스트: gold_overlay 7 · identity 14 · master_tables 골든 · PL 골든(167초) 통과, rule_coverage 104 중 실패는 xlsx 청결 1건만(전에는 104 통과). 이 과정에서 `test_tax22_latest_comparative_vintage_branch_is_read_and_enforced` 가 교보 4칸만 박아 둬서 실패 → 실측 22칸으로 확장(`_TAX22_LATEST_COMPARATIVE_ONLY`; 게이트 예외 아님).
9. **남은 것**: publishing = xlsx `손익분해PL` 386셀 동기화 · panel_csm_combo/panel_compare/public_exports 재생성 / 이번 범위 밖 유지 32버킷·부속 53버킷 / 변경 파일: `PL_breakdown.json` · `PL_breakdown_provenance.json` · `data/_gold/user_pl_cells.json` · `tests/test_rule_coverage_manifest.py` · `data/_derived/pl_oci_vs_bs_aoci_warn.json`(테스트가 재생성) · `TODO_parser_ifrs17.md` · `docs/todo_archive_parser_ifrs17.md` · `docs/changelog_parser_ifrs17.md`.
재현: `e19_apply.py --verify` · `e19_diff_vs_head.py` · `e19_verify_plans.py`(모두 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, stdin `/dev/null`).
"""
marker = "## 답변 (recipient 작성 — 처리 후)\n"
assert s.count(marker) == 1
s = s.replace(marker, marker + ANS, 1)
p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
