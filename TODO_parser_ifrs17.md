# Insurequant Parser TODO — IFRS17 lane (Stage 2)

> 갱신 2026-10-24 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-ifrs17.md` · 이력 `docs/changelog_parser_ifrs17.md`
> 2026-10-07 정리 전 전문(88~92차 Status 포함)은 `docs/todo_archive_parser_ifrs17.md` 맨 위에 있다. K-ICS 레인은 `TODO_parser_kics.md`.

## Status (최신 3개)

- **2026-10-24 22차: 후속 티켓 4건 + CSM 단일분기 빈칸 장치 — PL 값 32칸(신규 29 · 제자리 교체 1[ABL 2023.1Q 항목 7] · KB손보 손입력 2칸 제거) + CSM `값_당분기` 3칸 (티켓 `1130Z` · `1210Z` · `0600Z` · `20261024T0100Z` · `1215Z` 건 2, 미커밋)** — 박제·핀·잔차·예외 0, 칸마다 필링 줄 번호 독립 재독 227 checks 문제 0.
  KB라이프 2023.1Q 항목 9·11·12(2Q 단일분기 -1,118/-27/763) · ABL FY2023 항목 5·6·7·9·10(2023.1Q 항목 5 = 272 는 재보험 표 오추출 → 3,593; 항목 7 gold 낡음 → -1,328.36) · 농협생명 2024.1Q·2Q 항목 17·18·20·21(2024.3Q 이음매 닫힘) · KB손보 항목 16 의 60,900/33,300 = 경영공시 요약 PL 행(다른 개념)을 1차 세부 백필이 손입력한 값 → 빈칸.
  CSM `null_dangi` 장치(`build_root_masters._csm_null_dangi_keys`) 신설 + 롯데 2023.4Q 항목 3·4·5 단일분기 빈칸(항목 2·1·6 은 안 섞여 유지). 게이트: pl_bridge 3783P → 3787P/18F/0NEW 외 SUMMARY 불변 · data_contract RED 0 → 2(xlsx 드리프트 `손익분해PL` 66 + `CSM워터폴` 3 = 바뀐 칸 수) · 골든 `--update` 2줄(SUMMARY · 입력 지문) · PL 골든 · viz 2종 통과.
  남은 것: KB손보 항목 16 원문 6칸(2024.3Q~2025.4Q) 복원 = 새 박제 6건 필요 → 결정 / ABL 2024.1Q~3Q 항목 5 오추출 · FY2023 항목 11·12 / publishing = xlsx 2시트 · panel. 근거·재현 `data/_derived/remaining_20261022/e25_followups/`(`INDEX.txt` · `x01_verify_e25.py`) · changelog 22차.
- **2026-10-23 21차: owner 결정 D1~D3 4사 적재, PL 209칸 + CSM 58칸 최신 비교열(KB라이프 2023.1Q~3Q · 롯데 2023.4Q · ABL · 현대해상 FY2023), owner gold 7칸 교체·제거; KDB생명은 owner 결정으로 보류(HEAD 유지)(티켓 20261023T0900Z, 열림)** — 칸마다 필링 줄 번호 독립 재독 문제 0, 회사별 게이트 새 RED/FAIL 0, 롯데 WFY 면제는 validation 이 등재했다.
  gold: 교체·제거 7 = ABL 3(PL 교체 1 · CSM 제거 2) · 현대해상 4(CSM 제거 3 · 교체 1); 제거 5칸은 승인 교체값이 빌더 소스 값과 같아서(남기면 마스크 칸). 현대해상 IR 팩트시트 레그 6칸은 계보와 함께 gold. 이음매 `null_dangi` +23(롯데 12 · 현대해상 11), 새 박제 0, 원장 99줄 불변. 단일분기 파생 변경 PL 257 + CSM 66칸.
  게이트 HEAD→적재 후: 데이터계약 RED 0→2(xlsx 드리프트 CSM워터폴 124 · 손익분해PL 466 = 바뀐 칸 수) · live_artifacts RED 0→5(NB_VS_WATERFALL ABL 3 · 현대해상 2) · pl_bridge 3755P→3783P/18F/0NEW · 연속성 flagged 1/RED 0 · 골든·gold_overlay·identity 통과 · rule_coverage 104/105(실패 1 = xlsx RED, `[23]` 통과).
  **KDB 보류(owner 2026-10-23)**: 2023.3Q·4Q 의 17·18·20·22·24·31(누계 12 + 단일분기 12칸)이 연결 값이라(단일분기 합 = 연간 + 7.27억, validation 티켓 `20261023T1320Z`) 적재를 바이트 그대로 되돌렸다(KDB 변경 칸 0). validation 의 항목 23 선언도 원복됐고 롯데 WFY 등재는 유지. A 별도 복원 / B 연결 통일 / C 비움은 재적재 때 택일하고 항목 23 BLIND 재선언을 같은 커밋에 묶는다.
  남은 것: 롯데 CSM 4Q 단일분기 +105.5억(CSM 빈칸 장치 없음, `1215Z` 건 2; 건 1 KB라이프 4Q 14칸은 결함 아님 판정) · 옛 판 하위항목 `1130Z` KB라이프 · `1210Z` ABL(2023.1Q 항목 5 = 272 오추출 포함) · `1255Z` KDB(보류) · 큰 이동 사유 확인 · 현대해상 레그 가교 +98.12백만원 / publishing = xlsx 2시트 · NB_CSM_multiple · panel · public_exports. 커밋 안 함. 근거·재현 `data/_derived/remaining_20261022/e23_d1_d3/` · changelog 21차.
- **2026-10-23 20차: READY-25 적재 — 9사 25버킷 PL 440칸 + 4사 12버킷 CSM 55칸 최신 비교열, owner gold PL 7 + CSM 2칸 교체, KB라이프 `abs()` 결함 수정(티켓 20261023T0300Z, owner 「쭉 진행」)** — 농협생명 2023.1Q·2Q · 푸본현대·ABL 2024.4Q · 미래에셋 2023.4Q~2024.3Q · KB손보 2023.1Q~2024.3Q · KB라이프 2024.1Q · 롯데 2023.1Q~2024.3Q · 메리츠 2023.1Q·2Q · 한화생명 2023.1Q~3Q. 후보 PL 471 중 31칸은 안 실음(반올림·마스터와 같음 30 + 마스크가 돼 박제가 필요한 KB손보 2024.3Q 항목 16 1). 필링 줄 번호 독립 재독(`e21_verify.py`) 문제 0.
  gold 규칙: 교체 PL 7 = ⓐ 3(롯데 2023.2Q 항목 19 · 한화생명 2023.1Q 항목 20 · 2023.2Q 항목 21) + 해석 확장 4(KB손보·메리츠 2023.1Q·2Q 항목 16: gold 가 연결 기준 원 인쇄값 → 별도 값, `A_basis`); CSM 롯데 2023.1Q 항목 4·6 은 원 공시에 CSM 표가 없어 같은 전기 표의 다른 줄이던 gold 를 최신 기말순보험계약부채로 교체(`class C`; 되돌림 `e21_apply.py --revert`). ⓑ 0. null_dangi +30 −8(푸본현대 2024.4Q 8칸 복원) · set_dangi +1 −4 · 박제 −3 · 새 박제 0. `extract_tier2_kblife` `abs(jrr)`→`jrr`: 바뀐 셀이 2024.1Q 항목 2·8·12 3칸뿐이라 PL 골든 `--update`(`sha256_master`만), 그 3칸 gold 는 마스크가 돼 제거.
  게이트 전→후: 데이터계약 RED 0→2(MASTER_XLSX_DRIFT 손익분해PL·CSM워터폴, 예상) · live_artifacts RED 0→4(NB_VS_WATERFALL 메리츠·한화생명 2023.1Q·2Q, 예상) · master_tables SUMMARY pl_bridge 3697P/23F→3755P/18F/0NEW · csm_amort 387P/5S→388P/4S · qoq 262→263Y · oci_vs_bs_aoci 21→26Y(골든 `--update`) · 연속성 flagged 2→1 · 워터폴/NB 불변 · PL 골든·gold_overlay 7·identity 14·viz 골든 2종 통과 · 지문 `--update` 뒤 RED 0 · rule_coverage 103/104(실패 1 = xlsx RED).
  남은 것: publishing = xlsx 손익분해PL·CSM워터폴 · NB_CSM_multiple 4행 · panel/public_exports(PUBLIC_EXPORT_DRIFT 는 마스터 커밋 뒤에 나온다) / validation = pl_bridge_baseline 5줄 · WFY_EXCEPTIONS · 롯데 2023.1Q LEDGER_INERT 줄 / 읽기 코드 변경 미반영(`e20_held_and_remaining/measure/PLAN.md` §6 1~4·6~10, 프로토타입 `p_*.py`) / NEEDS_OWNER 21행(D1~D3) / 푸본현대·ABL 2024.4Q 항목 26·31 단일분기 공란 / KB손보 2024.4Q 항목 16 낡은 60,900. 커밋 안 함.
  근거·재현 `data/_derived/remaining_20261022/e21_ready25/`(`INDEX.txt` · `e21_apply.py --verify`/`--revert --apply` · `e21_diff_vs_head.txt`) · `docs/changelog_parser_ifrs17.md` 20차.

## 열린 일

- [ ] **21차 후속(D1~D3 4사 적재 뒤): KDB 보류 · owner 확인 · parser 후속 · 제안 · publishing** — 적재 4사는 미커밋, KDB생명은 보류(HEAD 값 유지), 증거 `data/_derived/remaining_20261022/e23_d1_d3/`, 답변은 티켓 `20261023T0900Z`(열림).
  - ① **KDB 보류(owner 2026-10-23: HEAD 유지)**: 2023.3Q·4Q 의 17·18·20·22·24·31 이 연결 값이다(validation 티켓 `20261023T1320Z`, 단일분기 합 = 연간 + 7.27억). 재적재 때 owner 가 택일한다: A 3Q·4Q 12칸은 HEAD 별도 값 그대로 + 3Q 단일분기 6칸 `null_dangi` / B FY2023 6항목을 연결로 통일(1Q·2Q 는 같은 필링의 2-2 연결 표) / C 칸 단위로 비움. parser 의견 A.
  - ①의 재적재 선행조건: 같은 커밋에 항목 23 BLIND 재선언(`PL_CONSTRUCTIVE_BLIND[23]` · `PL_ITEMS_UNCHECKABLE_BY_EQUATION`, 판 `gate_cleanup/post_copies/`)을 묶고, 티켓 `1255Z`(항목 5·6·9·10·11)를 같은 라운드에 옮긴다. 적재 직후 사본과 절차는 `kr0072_kdb_load2/post_load_copies/README.txt`.
  - ② (22차 해소) 롯데 CSM 2023.4Q 단일분기 항목 3·4·5 +105.5억: CSM `null_dangi` 장치를 신설해 3칸을 비웠다(`1215Z` 건 2, answered). KB라이프 2023.4Q 단일분기 14칸은 같은 판끼리의 차이라 `null_dangi` 가 필요 없다(`1215Z` 건 1, validation 판정).
  - ③ 옛 판 하위항목(헤드라인 불변, 단일분기만 이상): KB라이프 `1130Z` · ABL `1210Z`(FY2023 항목 5·6·7·9·10) 는 22차에서 적재(answered). 남은 것 = KDB 항목 5·6·9·10·11(`1255Z`, ① 과 같은 라운드).
  - ④ (제안) 후속 공시가 4-1·4-2 자리에 연결 값만 싣는 회사가 더 있는지 전수 점검한다(KDB 는 표 제목으로 별도를 판별한 읽기에서 샜고 FS-API 대조도 못 잡았다; 18~21차 적재분의 2023~2024 분기 포함).
  - ⑤ owner 확인: 큰 이동의 사유(ABL 보험손익 2023.1Q~3Q · ABL 3Q OCI +605억 · 현대해상 2Q 보험손익 −839억 · 롯데 4Q 투자손익 −139억 · CSM 기말 ABL 3Q −1,292억 · 현대해상 1Q·2Q −4,675억·−5,377억)는 공시 안 근거를 티켓 답변 2절 N3 에 적었다. 선택: 현대해상 2023.4Q 레그 가교 잔차 +98.12백만원은 IR 팩트시트 연간 레그(L26 248,926.412 · L30 201,237.589 · L11 76,425.619)로 닫을 수 있으나 owner gold 13·14 와 빌더 리터럴 2 를 건드린다(항목 3·7 plug 잔차 +2.224 · FY2023→FY2024 CSM 경계 1.0억 동반).
  - ⑥ publishing: (22차 몫 추가 = xlsx `손익분해PL` 66칸 · `CSM워터폴` 3칸, 농협생명·KB라이프·ABL·KB손보·롯데 CSM) · xlsx `CSM워터폴` 124 · `손익분해PL` 466칸 · `NB_CSM_multiple`(ABL 2023.1Q~3Q 연누계·당분기와 4Q 당분기 · 현대해상 2023.1Q·2Q) · `panel_compare.json` · `panel_csm_combo.json` · public_exports(PUBLIC_EXPORT_DRIFT 는 마스터 커밋 뒤에 나온다).
  - ⑦ **결정(owner/오케스트레이터): KB손보 KR0010 항목 16 원문 6칸 복원** — 2024.3Q 284,474 · 2024.4Q 380,949 · 2025.1Q 91,927 · 2025.2Q 190,741 · 2025.3Q 283,832 · 2025.4Q 388,289(DART 별도 행 재독, 줄 번호 `kr0010_kbsonbo/k01_item16_series.txt`). `_zero_other_expense` 가 이 회사 항목 16 을 매 분기 지우고 gold 가 2023.1Q~2024.2Q · 2026.1Q·2Q 에만 있다. 값이 빌더 소스와 같아 gold 로 실으면 마스크 칸 → 새 박제 6건(선례: 같은 항목 박제 6건 2026-08-30) 필요해 이번엔 싣지 않았다(티켓 `20261024T0100Z`). 대안 = `_zero_other_expense` 변경(PL 골든·전 회사 영향).
  - ⑧ (발견, 범위 밖) ABL 2024.1Q~3Q 항목 5 = 196/369/578 은 재보험 RA 오추출(원수 3,275/6,556/9,661), 2024.4Q 항목 5 12,282 ≠ 주석·롤포워드 13,655 · 항목 10 -785 ≠ -793, 2024.1Q~3Q 항목 9·10 빈칸(-2,249/-4,437/-6,746 · -196/-373/-583), 2024.1Q~3Q 항목 7 gold 는 오추출 5 로 계산, FY2023 항목 11(874/1,793/3,129/2,993)·12 미적재. 같은 읽기로 닫히는 값이 `kr0070_abl/a01_read_abl_fy2023.txt` · `a02_control_current_cols.txt` 에 있다.
- [ ] **교보생명 KR0073 PL·CSM 최신 비교열 후속(14차 이월)** — ① OCI 13칸(16차, 티켓 `20261021T1556Z` resolved) 적재 완료, 남은 것 = 2025.4Q 단일분기 이음매 후보 4칸(`null_dangi`) · FY2026 3분기 보고서 제출 뒤 2025.3Q 재갱신 ② `IFRS17_BS` 2023.4Q 5칸 + 2024.4Q 항목 1 + ILP 2023.4Q 3칸(17차) 적재 완료, 보류 그대로 = 티어 B AOCI 5칸(2023.1Q~3Q·2025.1Q~2Q, 2025.1Q·2Q 는 OCI 칸과 같이 움직여야 함) · 티어 C 중간분기 자본·ILP 2023.1Q~3Q 14/15 · ALT(FY2025 정책변경 기초) = owner 결정. 측정 근거 `data/_derived/remaining_20261022/b_bs_ilp/`.
- [ ] **다른 회사 같은 유형(최신 비교열 미반영) — 닫히는 버킷은 전부 적재 완료(18차 19 · 19차 21 · 20차 READY 25행 · 21차 owner 결정 D1~D3 4사 FY2023(KDB생명은 보류); 21차 후속은 아래 첫 항목), 남은 것 = 안 닫히는·확인불가 버킷(아래 55버킷은 20차 이전 수치라 재측정 필요; 원인·읽기 수정안은 티켓 `20261022T1800Z` 단계 2 · PLAN.md §6 읽기 변경 1~4·6~10)**
  측정 `data/_derived/remaining_20261022/d_census/`(`d_census_table.csv` 51 · `d_census_addl.csv` 53) 대비 남은 것: A51 STAY 22(블록 불닫힘·미확인) + 부속 33(FY 형제 20 · CSM-only 10 · OCI만 3; CSM-only 는 PL4 읽기 없이 CSM 만 바꾸면 `CSM_AMORT_IDENTITY` 가 깨진다)이고, 적재할 게 없는 A51 9는 그대로다(`data/_derived/remaining_20261022/e20_held_and_remaining/apply/s19_scope_check.txt`).
  같은 뿌리의 단일분기 어긋남 4곳(메리츠 2023.1Q~2Q · 한화생명 2023.1Q~2Q · KB라이프 2023.1Q~3Q · 롯데손보 2024.1Q~3Q)은 CSM·PL 을 같은 판으로 함께 갱신하면 닫히는 것을 원문으로 확인(`c_singleq/` 의 `per_bucket`); 롯데·ABL·KB라이프는 두 번 재작성돼 연속성 RED 3 이 남는다. → 메리츠 2023.1Q~2Q(PL+CSM) · 한화생명 2023.1Q~2Q(PL+CSM)·2023.3Q(CSM) · 롯데손보 2024.1Q~3Q(PL+CSM)·2023.1Q(PL+CSM)·2023.2Q(PL)는 20차에서 같은 판으로 적재했다(한화생명 LOB 노트 항목 5·6·9·10·11 은 옛 판 유지, 프로토타입 `measure/p_hanwha.py`); KB라이프 2023.1Q~3Q 는 21차에서 옵션 B 로 적재했다(2023.4Q 는 옛 판 그대로).
  19차가 남긴 공란: 푸본현대 2024.4Q 단일분기 8칸은 20차에서 복원(2024.4Q 누계 채택; 대신 항목 26·31 은 연간 비교열만 새 판이라 ABL 2024.4Q 26·31 과 함께 새 공란 4칸) · 2025.3Q 26칸(FY2026 3분기 보고서 제출 뒤 재계산) · KDB생명 2024.4Q 항목 17·18(표시 분리, 마스터에 기타영업손익 칸이 없다).
- [ ] **`null_dangi` 미등재 430칸** — 출처를 섞지 않으려 의도적으로 비운 단일분기 칸(경영공시→DART 181 · 경영공시→경영공시 175 · 경영공시→owner 43 · DART 낡은 공란 24 · 흥국생명 4 · 기타 3)이 `build_pl` 재실행 시 조용히 채워진다. `null_dangi` 에 사유와 함께 등재하거나 파생값으로 닫을지 정한다(`c_singleq/` 의 표). 한화생명 2025.4Q 공정가치법 70% 는 오류 아님(별도·원수 10.7%, 70% 는 출재 행) — 종결.
- [ ] **연간 CSM 상각 스케줄이 직전 연도 표인 15사 — 새 티켓(뷰 빌더·골든 영향)** — `viz_build_ifrs17_panels._pick_amort_block` 이 같은 `<당기말>` 캡션을 물려받은 두 후보(당기말 · 전기말 표)를 동점으로 보고 `line_no` 가 큰 전기말 표를 고른다(재현 `data/_derived/csm_backfill_lina_20261011/s33_dart_amort_blocks.py`). `csm_amort_schedule.json` FY2025 `buckets.total` 이 직전 연도 기말 CSM 과 0.05% 이내로 같은 회사 14곳(DB손보 · NH농협손보 · 동양 · 메리츠화재 · 삼성생명 · 삼성화재 · 아이엠라이프 · ABL · KDB생명 · 코리안리 · 푸본현대 · 한화손보 · 흥국생명 · 흥국화재) + 라이나, 마스터 `CSM_amortization.json` 2025.4Q 가 그 값을 물려받았다. 고친 뒤 패널·마스터 재생성 + `test_viz_ifrs17_panels_golden --update` 사유 기록. 후보 정정값(라이나) `proposed_fixes_existing_cells.json`.
- [ ] **라이나 CSM 분기 백필 후속(owner·publishing)** —
  - ① 새 RED 3(`PL_CSM_AMORT_VS_WATERFALL` 라이나 2025.3Q·2026.1Q·2026.2Q): 건별 등재(`proposed_registry_entries.json`) 또는 재보사 17건과 같이 게이트 설계 변경(경영공시 계보 워터폴 셀은 PL 대조 제외)
  - ② publishing: xlsx `CSM워터폴`(+18행)·`CSM상각`(+30행) 시트 동기화, NB 마스터 재빌드(`build_nb_csm_multiple.py` → 라이나 3행 추가 → live_artifacts `NB_CENSUS_MISSING` 3 해소)
  - ③ 결정: 분기 확장 여부 — 2025.1Q(p57)·2025.2Q(p83)는 지금 읽기 코드로 바로 닫히고 2024.1Q~3Q(p51·p76·p52)는 「분기말 잔액」 라벨 보강만 필요하지만, 라이나는 지금 6분기라 7번째 분기를 더하는 순간 active_min=7 로 MASTER_HOLE RED(2024.1Q~3Q)가 되므로 2024.1Q 부터 한 번에 · 2025.4Q `값_당분기` 5칸(기존 칸)은 다음 `build_csm()` 이 채우거나 승인 후 셀 단위로
  - ④ `bspl_apply_findpage.py` · `bspl_apply_render.py` 가 `raw/` 를 직접 glob 해 `tests/test_disclosure_raw_pdf_wiring.py` 2건 실패(BS·PL 담당 에이전트 스크립트, `disclosure_pdfs()` 로 교체)
  - ⑤ validation: `test_master_tables_golden` SUMMARY 3필드가 이 적재로 움직인다(closing 381P → 384P · csm_amort_identity 22S → 25S · qoq_warn 252Y → 254Y) — 의도된 변화라 `--update` + 사유 기록(나는 안 했다).

- [ ] **BS·PL 세부 백필 후속(owner·validation·downloader·publishing)** —
  - ① RED(불변): `PL_CSM_AMORT_VS_WATERFALL` 17(재보사 PL 항목 4 계보 한계 — `pl_csm_amort_missing_ledger.json` 건별 등재 또는 게이트 설계 변경, 후보는 CSM 레인 `proposed_registry_entries.json`) · `PL_YTD_COLLAPSE_TO_ZERO` 3(등재 후보 `data/_derived/bspl_granularity_20261011/proposed_owner_confirmed_cells_ytd_collapse.json`, 아니면 항목 23 3칸 철회) · `MASTER_HOLE` 하노버 2025.3Q PL(통째 결손 면제 경로 없음, 원천 not_posted)
  - ② 보류 BS 346칸(후속 378 − 이번에 채운 32; 사유 `data/_derived/bspl_followup_20261011/hold_reasons_5c.md`) + (B) 보류 목록 `data/_derived/bspl_apply_20261011/hold_list_B_20261011.json`: RGA 2025.1Q·2Q·2026.1Q·2Q 항목 13/14/15(8-1 자산 줄 합이 인쇄 총계에 안 닫힘) · RGA 2023.2Q·3Q(재작성 판, `hold_evidence_B_rga.json`) · BNP 항목 10/11/13/20/24(8-1 줄 = 일반계정, 마스터 = 특별계정 포함 DART, `hold_evidence_B_bnp_kr0075.json`) · 악사 10/13/20/21/24(감독서식) · 하노버 2023.3Q 10/13/15/24(AI801 서식 정의) · IBK연금 항목 13 의 2023.4Q→2024.4Q 정의 단절 · (처브·메트라이프 항목 20 의 특별계정 포함 정의는 2026-10-12 9차에서 처브 6칸을 D2 로 통일해 닫힘)
  - ③ owner: 삼성화재 KR0008 2023.2Q 항목 1·15·16 을 DART 별도 기준으로 맞추는 제안(`proposed_pl_kr0008_2023.2Q_dart_basis.json`; 적용하면 2023.2Q 항목 1 빈 칸이 닫힘) · 이번에 PL 마스터에 직접 고친 37칸은 gold overlay(`data/_gold/user_pl_cells.json`)에 없어 `build_pl` 재실행 시 되돌아간다(등재 후보 `proposed_gold_overlay_pl_20261011.json`, 근본 수정은 KR0072 핸들러의 3개월/누적 쌍 표 열 선택·KR0008 보험종목별 표 합산) · ABL 2023.1Q·2Q AOCI(DART 별도 3,722·3,680억)가 K-ICS 마스터(3,165·3,135억)와 15% 어긋난 새 YELLOW 2건(K-ICS 레인이 어느 기준인지 확인)
  - ④ 골든 `--update`(validation, 사유 기록; BS 골든 고정 9,030행 → 현재 10,962행)
  - ⑤ xlsx 동기화(publishing): 17BS 행 누락 1,932 + 값 드리프트 93 · 손익분해PL 드리프트 121칸
  - ⑥ PL 항목 1 보류 17칸: A 9칸(생명 항목 2 레그 — Tier-2 생명 핸들러 확장 또는 owner 가 게이트 면제 조건 변경) · B 5칸(항목 15 기타영업수익 = 0.0 승인 시 잔차 −79~+77로 닫힘) · C 3칸(삼성화재 2023.2Q 는 ③ 의 제안으로)
  - ⑦ 빌더 결함(마스터만 고쳤고 코드는 안 고침; 되살아남 방지로 오버레이·사이드카·파트에 같이 기록): `build_ifrs17_bs.py` 항목 10 이 알파벳 순 첫 행(`dart_CashAndDuefromBanks`/`dart_DueFromBanksAtAmortisedCost`)을 집어 `ifrs-full_CashAndCashEquivalents` 를 이김 · FS-API status 013 분기의 XML 폴백(`_pick_bs_table`)이 연결표·엉뚱한 표를 고름 · PL 369행 `값_당분기` None 잔존(항목 1·16·22·23·24)
  - ⑧ 관찰: 라이나 KR0074 FY2024 감사보고서가 2023.12.31 비교열을 소급 재작성(마스터 2023.4Q 는 원 보고서 값 유지) · 마스터가 억원 반올림으로 둔 연말 칸 중 정확값이 있는 것(신한이지·처브 항목 31 등) · 하나생명 2026.1Q 8-1 은 150dpi 화면 캡처 이미지라 재작성본 수령 시 부채 4칸 재독. downloader 별첨 목록은 런로그 「첨부·원천이 필요한 칸」.

- [ ] **재보사(KR1101~KR1108) CSM 계열 마스터 — owner 결정 대기** — ① 새 RED 17(`PL_BUCKET_ABSENT_VS_WATERFALL`): 건별 등재(후보 `data/_derived/reinsurer_ifrs17_csm_20261011/proposed_registry_entries.json`) 또는 게이트 설계 변경 ② 퍼시픽 2024 민감도(FY2025 전기 열이 한 행 밀려 인쇄, 규칙대로 FY2025 채택 중) ③ 스코리 당기손익 부호 반전 적재 확인 ④ 스위스리 신계약 CSM(감사보고서 1,098/1,743억 대 4-6-3 ① 622/1,328억) ⑤ 재빌드 소실 대비 gold-overlay 등재 여부.
  downloader: 하노버·RGA FY2025 IFRS17 감사보고서 별첨(2025.4Q 워터폴 행 부재). 전체 목록 런로그 끝절 `data/disclosure/_meta/reinsurer_ifrs17_csm_runlog.md`.

- [ ] **재보사 ILP 잔여(owner·downloader)** — (스위스리 KR1102 2026.1Q 합계는 2026-10-12 10차에서 owner 지시로 전체 행 합을 적재해 닫힘 — `data/_derived/ilp_kr1102_derived_load_20261012/evidence.md`.)
  ① 하노버 KR1104 2026.2Q: 2-4 합계 BEL −292 대 같은 공시 BS 순 LRC BEL −440.95(RA·CSM 은 같음) — 어느 쪽이 맞는지 발행사 확인 또는 결정(항목 1~8 미적재, LIC 항목 10~15 는 적재). ② 하노버 2025.3Q PDF 수집(downloader; 2024.3Q 비교 칸도 그 안에 있다).
  ③ 스위스리·제네럴·RGA·스코리·마이브라운과 하노버·퍼시픽 연말은 LIC(10~15)가 비어 있다(경영공시에 재무상태표 상세 없음; RGA·스코리·마이브라운은 연말 감사보고서 주석에 다른 표기로 있어 읽기 구현이 필요). 근거 런로그 §14.
- [ ] **분할표 읽기·xlsx 동기화 후속(publishing·별도 티켓)** — 마스터 `CSM_amortization.json` 2025.4Q 18칸(분할표 4사 y9·y10 + 한화생명 별도 표)은 고쳤지만 패널 `csm_amort_schedule.json` 과 `viz_build_ifrs17_panels.extract_amort_schedule` 은 분할표 앞 반쪽만 읽고(`buckets.total` 부분합 — 라이나·AIA·처브·메트라이프·BNP) 한화생명은 연결 표를 고른다: 고치려면 패널 재생성 + `test_viz_ifrs17_panels_golden --update` 가 따르고, 그 전에 `build_tidy_exports.py --only amort` 로 마스터를 다시 만들면 18칸이 되돌아가니 `scripts/load_amort_split_tables_20261012.py --apply` 를 다시 돌린다. 데이터 계약 RED 5(전부 xlsx: `17BS`·`CSM상각`·`보험계약부채`·`손익분해PL` 시트 `sync_master_xlsx_sheet.py`)는 publishing 몫. 증빙 `data/_derived/ifrs17_owner_followups_20261012/amort_split_evidence.md`.
- [ ] **ILP 라이나 기준(owner)** — ① 라이나 2023.1Q·2Q(항목 10·13·14·15)는 옛 기준(FY2024 공시 비교열이 재작성 전), 2023.3Q·2023.4Q·2024.1Q~ 는 재작성 기준이라 LRC·합계 계열이 2023.2Q → 3Q 에서 끊긴다(LIC 는 매끈) — 두 칸 유지 여부. (처브 항목 14·15 9셀은 2026-10-12 9차에서 특별계정 포함(D2)으로 통일해 닫힘 — `data/_derived/ifrs17_owner_followups_20261012/chubb_d2_evidence.md`.) 근거 런로그 §2.3.
- [ ] **항목 9 가 빈 국내 55칸** — PDF 대조: 「해당사항 없음/원칙모형」 39(→ 0 후보)·텍스트층에서 못 찾음 16, 「사용」은 롯데(수정 완료) 외 없음. 채울지 owner 결정. 근거 `data/disclosure/_meta/ilp_round3_20261011/t100_item9_blank_census.txt`, 런로그 §15.2.
- [ ] **designer 패널 재빌드 374셀(348 + 이번 26)** — `data/disclosure/_meta/ilp_round3_20261011/t120_rebuild_list.txt`(분기별·항목군별 회사 목록) + `data/disclosure/_meta/ilp_leftovers_20261011/r_rebuild_list.txt`(하나손보 11 · 라이나 3 · 처브 6 신규, 메트라이프 6 값 변경; 하나손보 2026.1Q·2Q 는 부채 기준 LIC 가 급감 — 자산측 LIC −495/−512억이라 항목 8 + 항목 10 ≠ BS 순액, 「추정」(BS20 − 항목 8)이 틀림, provenance `asset_side_eok`). 재보사 8곳 신규, 재작성 사이드카 5셀, 재보사는 항목 8(순액)과 10~15(부채측)의 합이 안 맞음, 재보사 BS 항목 20 이 BS 마스터에 들어와(다른 레인) 빌더의 LIC 「추정」(BS20 − 항목 8)이 재보사에도 걸린다 — 자산측 LRC 가 큰 회사는 추정이 틀리고(뮌헨은 실공시 대조로 제외) 실공시가 없는 스위스리·제네럴·RGA·스코리는 검증 불가, 「미분리 음수」 21건 진단. 런로그 §16. + 2026-10-12 9차: 처브 ILP 항목 14·15 9셀 값 변경(`data/_derived/ifrs17_owner_followups_20261012/chubb_d2_spec_ilp.json`; 처브가 LIC 「추정」 불신 목록에서 빠질 수 있다).

- [ ] **예별(KR0004) 2025.3Q `PL_YTD_COLLAPSE_TO_ZERO` RED = validation r2 V2-1(기준 혼합) — owner/validation 결정 대기** — 원문이 `제1(당)3분기 2025-06-16~09-30`(신설 예별손해보험(주) 제1기)이고 법인세는 `-` 라 0.0 이 인쇄값이다. 2Q(구 MG 제13기 8,079.7)와 보고주체가 다른 단절이라 값을 바꿔도 다른 RED 가 된다.
  결정지 ① 되돌리기(10-09 에 만든 4행 + 사이드카 1셀 삭제, `MASTER_HOLE(통째)` 복귀) ② 유지 + 근거를 단 셀 단위 등재. 증거 4줄·절차는 런로그 1b §3.3. V2-4(골든 `--update` 보류)가 이 결정에 걸려 있다.
- [ ] **예별 `extract_tier2_yebyeol` 핸들러 후속(PL 골든 재생성 동반)** — 항목 13·14 를 `(수익−비용)+(재보험수익−재보험비용)` 손익 부호로, 장기 열 4합계를 `_jang_*` 로 내면 항목 2/3/8 이 빌더에서 나온다(임시: `_GOLD_CELL_OVERRIDE`, 값은 런로그 1b §3.2).
  지금은 루트 마스터 10칸만 정정돼 있어 `build_pl()` 이 13·14 를 되돌린다. 2023.4Q·항목 5~7·9~12 도 같이.
- [ ] **PL 골든 실패** — `RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py` 에서 `sha256_coverage` 만 어긋난다(master 바이트는 같음). **2026-10-22 재측정(14차 적용 뒤): `1 passed`(364초) — 재현되지 않는다(원인 미확인; 다음 실행도 통과하면 이 항목을 닫을 것).**
  KR0074 라이나 2023.4Q 1행: 디스크 coverage 는 `no_income_statement`·missing 21·tier2 `partial`, 빌더 재실행은 missing `[4]`·tier2 `ok`.
  `a0f0607` 이후 디스크 coverage 와 빌더 산출이 어긋난 것으로 보인다. 2026-10-06 K-ICS 정정과는 무관함을 확인했다.
- [ ] **PL 부모 #2 결측 26버킷(display 7)** — `inbox/parser/20260918T0710Z`. 칸마다 `FILLED`/`ABSENT_IN_SOURCE`/`UNREADABLE` 로 회신.
- [ ] **KR0004 2025.4Q 비교 단절 주의** — 예별 = 구 MG = DART 명의 엠지, 한 계열로 다룬다(owner). 2025-09-03 계약·자산부채 이전 때문에 DART(총자산 728억)와 경영공시(38,191억)가 52배 다르다. 근거 `inbox/_resolved/20260918T0705Z`.
  2026-10-10 확인: 경영공시 `2025년` 열은 **2025-06-16 설립(발기) 이후**(예별손해보험(주), 예금보험공사 100%) 기간이고 마스터 PL 2025.4Q 는 DART 엠지 제13기 연간이다 — 2025.2Q(구 MG)·2025.3Q(신설 제1기)·2025.4Q(DART 엠지) 세 칸이 보고주체가 다르다(런로그 1b §3.3).
- [ ] **ZERO_LEGS DART 4Q 9건** — 아이엠라이프·AIA·예별·카카오페이·하나손보 4Q. sub-leg 추출 갭 가능성(validation 2026-09-20 12차). 원문 확정. (예별은 2026-10-10 에 항목 2·3·8 이 채워졌고 5·6·7·9~12 가 남았다.)
- [ ] **KR0075 카디프 2023.4Q 자산·부채총계 0.08% 차이 원인** — FY2024 감사보고서 2023.12.31 비교열과 대조(네트워크 불요).
  마스터(FS-API)는 바꾸지 말고 원인만 도메인 문서 quirk 에 한 줄.

## 휴면 (2026-06~07 개설, 재개 전에 `scripts/check_pl_reconcile.py`·게이트로 다시 잰다)

XLSX-FOLLOWUP(NB 분모 '기타' 혼입 · PL 0값 감사 · 0의 의미론) · PL-T2(동양·KDB 재보 item9/10 · 하나생명 item17 · 교보라플 Tier2 · KDB 2023.2Q) ·
CSM-FOLLOWUP(closing 5 SKIP · 메트라이프 2025.4Q 점프 · pl_bridge/crosscheck 잔존) · TIER2-NEXT(미래에셋·한화손해·흥국·롯데 등) ·
F15 CSM 시계열 결측 · F17 Tier2 LOB(9/11 손보, 결정 대기) · 코리안리 FY2025 CSM basis(owner A/B 결정 대기) · F18 IR(보류).

2026-10-07 실측으로 닫은 것: KR0004 PL 전무 → 96행 · MLG-1 듀레이션갭 → K-ICS 경로로 2026-09-22 신설 · F16 흥국생명 민감도.

## 규칙 — LOB 축을 섞지 말 것

- 손보 CSM 분해 = 보장성 / 물보험 / 저축성(전부 장기보험 안, 삼성화재가 이 축을 쓴다).
- 손보 손익 분해(보험손익) = 장기 / 자동차 / 일반(Tier2). 자동차·일반은 PAA 라 CSM 롤포워드가 없다.
- 보종별 신계약 CSM 배수는 일부 회사만 IR 로 공시한다 — DART 에서 합성하지 않는다.
