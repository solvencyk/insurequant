# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/docs/changelog_parser_ifrs17.md")
s = p.read_bytes().decode("utf-8")
assert "\r\n" not in s
assert s.count("> Last updated: 2026-10-23") == 1
s = s.replace("> Last updated: 2026-10-23", "> Last updated: 2026-10-24")
anchor = "## 2026-10-23 (21차:"
assert s.count(anchor) == 1
NEW = """## 2026-10-24 (22차: 후속 티켓 4건 + CSM 단일분기 빈칸 장치 — PL 값 32칸 · CSM 값_당분기 3칸, 박제·핀·잔차·예외 0 — 티켓 20261023T1130Z · 20261023T1210Z · 20261023T0600Z · 20261024T0100Z · 20261023T1215Z 건 2)

커밋 안 함, push 안 함. 서브에이전트·docling 안 씀. `build_root_masters.main()`·`build_ifrs17_bs`·xlsx 동기화·panel·public_exports·NB·원장(박제)·핸들러 미접촉. 증거 `data/_derived/remaining_20261022/e25_followups/`(`INDEX.txt` · 답변 원문 `answers/` · 게이트/테스트 `gates/`).

- **범위(오케스트레이터 지시 한 번에 4건 + 작업 5, 한 회사씩 순서대로)**: ① KB라이프 KR0099 2023.1Q 항목 9·11·12 ② ABL KR0070 FY2023 항목 5·6·7·9·10 ③ 농협생명 KR0104 2024.1Q·2Q 항목 17·20·21 ④ KB손해보험 KR0010 항목 16 ⑤ CSM 에도 PL `null_dangi` 같은 칸 단위 단일분기 빈칸 장치를 두고 롯데 KR0003 2023.4Q CSM 항목 3·4·5 를 비움(`1215Z` 건 2; 건 1 KB라이프 PL 14칸은 오케스트레이터가 결함 아님으로 판정해 비우지 않음).
- **방법**: 읽기 스크립트(`k01`/`a01`/`n01`)가 필링 XML 물리 줄에서 최신 비교열을 읽고 `p01_build_plan.py` 가 적용 계약 `e25_plan.json` 을 만든다. 적재는 ABL 적용기에서 `make_apply_e25.py` 로 생성한 `e25_apply.py`(치환 1회 일치 단언; `--snapshot-drift` · `--check` · `--out-dir` 모의 · `--apply` · `--verify`)가 실제 `build_pl()` 을 임시 사본에 돌려 달라지는 칸만 셀 단위로 쓴다(진짜 빌드 == 라이브 마스터 `--verify` 로 증명, 출처표는 샌드박스 emitter 로 재계산). 적용 전 독립 재독 `x01_verify_e25.py`(표준 라이브러리만, 계획기 코드 공유 0, 227 checks, 변이 line/value/column 3종 모두 검출; 적재 뒤에도 `E25_BASE=backup_before_apply` 로 같은 결과 재현). 적재 전 30개 파일 백업을 sha256 으로 바이트 동일 확인.
- **결과**: PL 값 32칸 = gold set 신규 29(KB라이프 3 · 농협생명 8 · ABL 18) + 제자리 교체 1(ABL 2023.1Q 항목 7: 낡은 gold -1,767 → -1,328.36347) + KB손보 손입력 2칸 제거(60,900 · 33,300 → 빈칸); 파생 단일분기 34칸; 출처표 13블록. 모두 빌더 소스와 달라 마스크 칸이 아니다(PL 센서스 (1379, 22) → (1408, 22), 박제 0). 단일분기: KB라이프 2023.2Q = -1,118 / -27 / 763 = 인쇄 3개월 열, 농협생명 2024.3Q 17 / 20 / 21 = 인쇄 3개월 열(소수 6자리), ABL 2Q·3Q 5개 항목 10칸 인쇄 3개월 열과 차이 0.
- **판정 메모**: ABL 2023.1Q 항목 5 = 272 는 재보험 표 값의 오추출(최신 비교열 원수 값 3,593); 앞선 적재 답변의 「최신 3,524」는 같은 표 기타사업비용 전분기 열이라 맞지 않았다. ABL 항목 7 은 같은 주석의 나머지 행 합과 ±1 이내로 독립 검산했다(`3 = 4+5+6+7` 이 주석 안에서 닫힌다). 농협생명은 티켓에 없던 항목 18 도 함께 옮겼다(17 = 18+19 유지; 게이트 허용오차 200백만원이라 게이트는 못 잡는 칸). KB손보 60,900 · 33,300 은 2026-10-11 경영공시 세부 백필 1차 적재가 요약 PL 「기타사업비용」 행(DART 행의 약 1/5, 다른 개념)을 `_zero_other_expense` 로 비워진 칸에 넣은 것이다; 같은 로더의 다른 128칸 중 DART 소스와 비교 가능한 5칸은 0.03~0.95% 차이뿐이라 다른 회사는 해당 없다.
- **싣지 않은 것(결정 요청)**: KB손보 항목 16 원문 6칸(2024.3Q 284,474 · 2024.4Q 380,949 · 2025.1Q 91,927 · 2025.2Q 190,741 · 2025.3Q 283,832 · 2025.4Q 388,289)은 빌더 소스와 같아 gold 로 실으면 마스크 칸 → 새 박제 6건이 필요하다(이번 지시는 새 박제 금지). ABL 범위 밖 발견: 2024.1Q~3Q 항목 5 = 196/369/578 은 재보험 RA 오추출(원수 3,275/6,556/9,661), 2024.4Q 항목 5·10 이 주석·롤포워드와 다르고, 2024.1Q~3Q 항목 9·10 빈칸, 항목 7 gold 는 오추출 5 로 계산됨, FY2023 항목 11·12 미적재.
- **작업 5**: `_csm_null_dangi_keys()` 31줄 추가(`build_csm()` 이 gold `null_dangi.cells` 를 읽음; 형식 오류 · 중복 · 마스터에 없는 칸 · `set_dangi` 섹션은 ValueError). 칸 3개는 연간 값이 두 판 사이에서 바뀐 흐름 항목만(이자 -3.5 · 가정 -6.0 · 상각 +9.5, 롤포워드 잔차 +105.5 = 기초 재작성 105.4), 신계약(두 판 동일)·기초·기말(저량)은 유지. 시험: `test_gold_overlay_survives_rebuild.py` +3, `test_rule_coverage_manifest.py::test_csm_null_dangi_is_declared_read_and_enforced`(등재를 빼면 정확히 이 3칸이 되살아나야 한다 — 롯데 WFY 시험을 본뜸), 변이 M1~M3 모두 검출. `user_csm_cells.json` 읽는 곳 전수 확인(최상위 키에 둔감).
- **게이트·테스트(적재 전 → 후)**: master_tables pl_bridge 3783P → 3787P/18F/0NEW(ABL 항목 6 채움으로 `3 = 4+5+6+7` 4버킷이 검사받기 시작) 외 SUMMARY 전 필드 동일 · data_contract RED 0 → 2(MASTER_XLSX_DRIFT `손익분해PL` 66칸 · `CSM워터폴` 3칸 = 바뀐 칸 수와 정확히 같음), YELLOW 168 동일 · 연속성 flagged 1/RED 0 · 워터폴 41 pass · nb_csm 5/5 · live_artifacts RED 0 불변 · 골든 `--update` 2줄(master_tables SUMMARY 한 줄, 입력 지문 viz_ifrs17_panels 한 줄: CSM_waterfall.json 51,368,530 → 51,368,526 바이트) · PL 골든 1 passed(276초) · 규칙 커버리지 105 passed + 1 failed(xlsx 드리프트와 같은 원인) · viz 골든 2종 · deploy_assets 12 · push_gate_wiring 66 통과.
- **남은 것**: publishing = xlsx `손익분해PL` 66칸 · `CSM워터폴` 3칸 동기화, panel/public_exports / 결정 = KB손보 항목 16 박제 6건 / parser = ABL 2024 항목 5·9·10·7 정정 · FY2023 항목 11·12 · KDB `1255Z`.
- **프로세스 기록**: 한 줄 `python3 -c`/`python -c` 호출 3회와 python 표준입력 heredoc 1회를 실행했다(모두 즉시 종료, 고아 프로세스 없음 확인). `git push`/`git add -A` 없음.

"""
s = s.replace(anchor, NEW + anchor)
p.write_bytes(s.encode("utf-8"))
print("ok")
