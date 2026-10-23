**2026-10-24 parser/ifrs17 답변 (티켓 20261023T1215Z 건 2, 롯데손해보험 KR0003 2023.4Q CSM 단일분기 항목 3·4·5 + CSM `null_dangi` 장치; 오케스트레이터 지시 작업 5)** — 장치 신설 + 3칸 비움 완료, 미커밋·미푸시. 증거 `data/_derived/remaining_20261022/e25_followups/kr0003_lotte_csm_blank/`(색인 `../INDEX.txt`).

**건 1 (KB라이프 PL 14칸)**: 오케스트레이터 메모(2026-10-23 밤)대로 결함 아님으로 판정돼 **비우지 않았다**.

**건 2 — 장치**: `scripts/build_root_masters.py` 에 `_csm_null_dangi_keys(CSM_OVR)` 를 신설했다(PL `_pl_null_dangi_keys` 의 쌍둥이). `data/_gold/user_csm_cells.json` 의 `null_dangi.cells = [코드, 분기, 항목번호]` 칸은 `build_csm()` 이 값(누계)을 두고 `값_당분기` 만 None 으로 만든다. 파일·키가 없으면 구 동작 그대로(라이브 gold 로 새 빌드한 결과가 라이브 마스터 전 행 2,358행과 같음을 적용 전에 확인했다 = 코드 변경만으로는 동작 불변). 삼키지 않는 오류: 형식 오류, 중복 칸, 마스터에 행이 없는 칸, 그리고 `set_dangi` 섹션 하나라도(CSM 에는 읽는 쪽이 없어 조용히 무시되므로 거부; null_dangi 와 같은 칸이 겹치면 더더욱) → `ValueError`.

**건 2 — 칸**: KR0003 2023.4Q 항목 3(이자 부리) · 4(가정 및 경험 조정) · 5(CSM 상각)의 `값_당분기` 223.0 / 813.7 / -542.8 → 빈칸. 값(누계) 777.0 / 2,795.0 / -1,859.0 은 그대로. `CSM_waterfall.json` 에 같은 3칸만 셀 단위로 반영했다(새 코드의 `build_csm()` 실행에서 기존 gold 대비 달라지는 칸이 정확히 이 3칸임을 확인하고 그 칸만 씀).

**어느 칸이 섞였나 (`c03_vintage_evidence.txt`, 원문 재독 포함)**: 4Q 누계는 최신 비교열(기초 16,669.0)이고 3Q 누계는 옛 판이다(FY2024 3Q 보고서의 전기 9개월 CSM 표 L15912: 기초 1,677,438 · 신계약 409,211 · 이자 55,402 · 추정치 198,132 · 상각 (131,623) · 기말 2,208,560백만원 = 마스터 2023.3Q 와 같다). 연간 값이 두 판 사이에서 바뀐 항목만 단일분기(4Q − 3Q)가 섞인다.

| 항목 | 연간 옛 → 새 | 단일분기 옛 → 새 | 판정 |
|---|---|---|---|
| 2 신계약 | 5,478.9 → 5,478.9 | 1,386.8 → 1,386.8 | 두 판 동일 — **비우지 않음** |
| 3 이자 부리 | 780.5 → 777.0 | 226.5 → 223.0 (-3.5) | 섞임 — 비움 |
| 4 가정 및 경험 조정 | 2,801.0 → 2,795.0 | 819.7 → 813.7 (-6.0) | 섞임 — 비움 |
| 5 CSM 상각 | -1,868.5 → -1,859.0 | -552.3 → -542.8 (+9.5) | 섞임 — 비움 |
| 1 기초 / 6 기말 | 저량 | 22,085.6 (= 3Q 기말 as filed) / 23,860.8 (= 최신 연간 기말) | 차분이 아니라 시점 잔액 — **비우지 않음** |

단일분기 롤포워드 잔차는 옛 연간 +0.1 → 새 연간 +105.5(= 기초 재작성 16,774.4 − 16,669.0)였고, 흐름 3개가 비어 이제 보이는 칸으로는 롤포워드가 조립되지 않는다. 「기초(1)도 필요하면」은 필요 없다고 판단했다(근거: 위 표 마지막 줄). 연간 보고서에 4분기 3개월 열이 없어 직접 대조는 못 한다. 3Q 누계가 최신 비교열로 재작성되는 공시가 생기면 칸을 풀고 다시 유도한다(owner 규칙 2026-10-22: 빈칸이 틀린 값보다 낫다).

**읽는 쪽 점검(`user_csm_cells.json` 새 최상위 키 `null_dangi`)**: `build_root_masters`(`exclude_companies` · `set` 만 읽음) · `emit_ifrs17_provenance`(`obj.get("set")`) · `validate_data_contract` GOLD_OVERLAY_SPECS(`set`) · `sync_owner_fills_to_json`(다른 키 보존한다고 명시) · `apply_latest_comparative_20261012`(일회성) · `tests/test_gold_overlay_survives_rebuild` 모두 최상위 키에 둔감하다. 게이트 전부 새 발견 없이 돌았다.

**시험·센서스**: `tests/test_gold_overlay_survives_rebuild.py` +3(지정 칸만 비움·이웃 불변·2차 재빌드에도 유지 / 키 없으면 구 동작 / 형식 오류·중복·없는 행·set_dangi 5종 거부). `tests/test_rule_coverage_manifest.py` +1 `test_csm_null_dangi_is_declared_read_and_enforced` — 롯데 FY2023 WFY 시험을 본떠 실데이터로: 선언 `CSM_NULL_DANGI_CELLS`(3칸) = gold 파일 칸 목록, 커밋된 마스터의 3칸이 값을 가진 채 단일분기 빈칸, **등재를 빼고 같은 빌드를 돌리면 정확히 이 3칸만 숫자 단일분기로 되살아난다(= 등재가 읽힌다; 안 살아나면 죽은 등재라 철거)**, 이웃(항목 1·2·6) 불변, set_dangi 주입은 빌드가 거부. `GOLD_OVERLAY_CENSUS` CSM (417, 77)은 `set` 센서스라 불변이고 주석으로 못박았다(PL 은 이번 적재로 (1408, 22)). 민감도: 빌더가 등재를 무시(M1) · 엉뚱한 항목을 읽음(M2) · set_dangi 를 조용히 무시(M3)하게 바꿔 보면 새 시험이 셋 다 실패한다(`c05_test_mutation.txt`).

**xlsx**: `scripts/check_master_xlsx_drift.py` 는 `CSM워터폴` 3칸(위 3칸, `값_당분기: 시트='223.0' vs 마스터=None` 등)과 `손익분해PL` 66칸(작업 1~4)만 보고하고 다른 시트 드리프트 0이다. xlsx 는 동기화하지 않았다(publishing 몫). 화면: IFRS17.html 분기 모드 창(최신 5분기)에 2023.4Q 는 안 나온다. 공개 다운로드 `CSM워터폴` 시트 값_당분기 열에서 이 3칸이 빈칸이 된다.

**게이트·테스트**: 결과는 같은 배치의 다른 티켓 답변과 같다: master_tables SUMMARY 는 pl_bridge 한 필드만(3783P → 3787P) 움직이고 CSM 쪽 필드(closing · csm_amort_identity · qoq_warn)는 전부 불변, data_contract 새 RED 는 MASTER_XLSX_DRIFT 2건뿐, 연속성 flagged 1/RED 0, 워터폴 41 pass, nb_csm 5/5, viz 골든 2종·master_tables 골든·PL 골든 통과, 입력 지문 viz_ifrs17_panels 한 줄 `--update`(CSM_waterfall.json 3칸의 `null` 치환으로 51,368,530 → 51,368,526 바이트). 되돌리기: `kr0003_lotte_csm_blank/c02_apply_csm.py --revert --apply`(CSM 두 파일) + 코드·시험은 `backup_before_apply/` 사본 복사(INDEX.txt 6절).
