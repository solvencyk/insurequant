# Insurequant Parser TODO — IFRS17 lane (Stage 2)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-ifrs17.md` · 이력 `docs/changelog_parser_ifrs17.md`
> 2026-10-07 정리 전 전문(88~92차 Status 포함)은 `docs/todo_archive_parser_ifrs17.md` 맨 위에 있다. K-ICS 레인은 `TODO_parser_kics.md`.

## Status (최신 3개)

- **2026-10-11 6차: 라이나 KR0074 CSM 분기 백필 + 상각 스케줄(티켓 20261011T1700Z)** — `CSM_waterfall.json` 2,286 → 2,304행(+18 = 2025.3Q·2026.1Q·2026.2Q × 항목 1~6, YTD 억원 5자리) · `CSM_waterfall_provenance.json` +3셀(DISCLOSURE) · `CSM_amortization.json` 570 → 600행(+30, 세 분기 상각 스케줄 1~10년), 기존 행 변경 0(HEAD 접두 동일 · 키 diff 0). 원천 = 정기경영공시 PDF 검토 주석(p91+93 · p66+68 · p63, 천원): 모든 쪽 가로·세로 항등식 + 천원 0 잔차 + 별도 = 연결 + 기초 = 마스터 직전 연말 + 같은 코드로 연말 행 재현(2025.4Q·2024.4Q·2023.4Q 6항목 1자리 일치) + 독립 ILP 마스터 일치. 커밋 안 함.
  남은 것: data-contract RED 23 → 28(신규 5 = `PL_CSM_AMORT_VS_WATERFALL` 라이나 3[등재 후보 `proposed_registry_entries.json`, owner] + xlsx `MASTER_XLSX_ROW_MISSING` 2[publishing]) · live_artifacts `NB_CENSUS_MISSING` 3(NB 재빌드, 모의 라이나 연누계 배수 11.22 · 9.02 · 10.33) · **범위 밖 발견: 연간 CSM 상각 스케줄이 15사에서 직전 연도 표**(`s34_amort_panel_year_census.json`, 새 티켓) · 라이나 기존 2025.4Q 상각 10행·값_당분기 5칸은 미수정(`proposed_fixes_existing_cells.json`) · 7번째 분기를 더하면 active_min=7 이라 MASTER_HOLE.
  근거·재현 `data/disclosure/_meta/csm_backfill_annual_filers_runlog_20261011.md` · 도구 `scripts/extract_lina_csm_rows_20261011.py` · `load_lina_csm_backfill_20261011.py`(되돌리기 `--revert --apply`) · 백업 `data/_derived/csm_backfill_backup_20261011/`.
- **2026-10-11 5차: 재보사 PL 항목 16 기타사업비용 7칸(티켓 20261011T1730Z)** — `PL_breakdown.json` 13,458 → 13,465행(추가 7 = 뮌헨 KR1101 2023.1Q -200 · 2Q -2,000 · 3Q +4,100 · 2024.1Q -2,300 / 제네럴 KR1103 2023.3Q +2,500 · 2024.1Q +100 · 2025.4Q +1,200, 백만원 누계), 기존 행 값 변경 0 · 삭제 0, 다음 분기 파생 값_당분기 2행만 None → 값(뮌헨 2024.2Q 1,500 · 제네럴 2024.2Q 382). 7칸 모두 2-1 요약 쪽을 열어 인쇄값 재현 + 보험손익 다리(수익−서비스비용+재보험수익−재보험서비스비용−기타사업비용)가 인쇄 보험손익에 ±1억 이내로 닫힘. 재보사 KR1102~1108 센서스: 같은 패턴 0(미공시 버킷만 비어 있음). 제네럴 2023.1Q 는 원문이 `( )` 라 빈 칸이 맞다.
  게이트(--no-build) data_contract RED 21 → 23: 신규 2 = `MASTER_XLSX_ROW_MISSING`(7행)·`MASTER_XLSX_DRIFT`(2셀) `손익분해PL` 시트 — 내가 xlsx 를 안 만졌으므로 publishing 이 `sync_master_xlsx_sheet.py "손익분해PL"` 로 닫을 몫. master_tables SUMMARY 불변(pl_bridge 29F/0NEW). 커밋 안 함.
  근거·재현 `data/disclosure/_meta/bspl_granularity_runlog.md` 「5차」 · 명세 `data/_derived/bspl_apply_20261011/item16/spec_item16.json` · 도구 `scripts/bspl_apply_item16_reinsurers.py` · 백업 `data/_derived/bspl_apply_backup_20261011/item16/`.
- **2026-10-11 4차: 사이트 신판 대조 + 별첨 감사보고서로 빈 칸 채움(티켓 20261011T1215Z)** — `IFRS17_BS.json` 10,962 → 10,967행(추가 5 = 0 증명: 농협생명 2025.4Q 항목 14·22 · 흥국화재 2024.4Q 항목 22 · AIG 2023.4Q 항목 22·23; 줄 없음 + 자산·부채 줄 합이 총계로 원 단위 폐합), HEAD 대비 값 변경 0 · 삭제 0 · `PL_breakdown.json` 변경 0. 참고 칸 7개(현대해상 3 · 한화생명 2 · 하나생명 1 · KB라이프 1)의 바뀐 쪽은 전부 BS/PL 원천이 아님(쪽번호·운용자산이익률·손해사정 표·유동성갭) → 정정 0.
  남은 것: 보류 6군(흥국화재 항목 23 = 사채 BondsIssued 정의 · 흥국화재 PL 29 줄 없음 · AIG 2023.4Q PL 항목 2·3·5~14·25~32 원천 없음[새 첨부는 지급여력 BS 감사보고서 이미지] · 농협생명 항목 6·8 · 한화손보 항목 8 · 연결 `x-1` 항목) · data-contract RED 38 → 39(신규 1 = K-ICS 레인 `MASTER_XLSX_DRIFT 금리민감도`, 내 몫 아님).
  근거·재현 `data/disclosure/_meta/bspl_granularity_runlog.md` 맨 위 「중간 결과 — 4차」 · 명세 `data/_derived/bspl_apply_20261011/spec_C4_zero_proofs.json` · 도구 `scripts/bspl_apply_make_spec_c4_zero.py` + `bspl_apply_bs_fix.py --round C4_zero` · 백업 `data/_derived/bspl_apply_backup_20261011/C4_zero/`.
## 열린 일

- [ ] **연간 CSM 상각 스케줄이 직전 연도 표인 15사 — 새 티켓(뷰 빌더·골든 영향)** — `viz_build_ifrs17_panels._pick_amort_block` 이 같은 `<당기말>` 캡션을 물려받은 두 후보(당기말 · 전기말 표)를 동점으로 보고 `line_no` 가 큰 전기말 표를 고른다(재현 `data/_derived/csm_backfill_lina_20261011/s33_dart_amort_blocks.py`). `csm_amort_schedule.json` FY2025 `buckets.total` 이 직전 연도 기말 CSM 과 0.05% 이내로 같은 회사 14곳(DB손보 · NH농협손보 · 동양 · 메리츠화재 · 삼성생명 · 삼성화재 · 아이엠라이프 · ABL · KDB생명 · 코리안리 · 푸본현대 · 한화손보 · 흥국생명 · 흥국화재) + 라이나, 마스터 `CSM_amortization.json` 2025.4Q 가 그 값을 물려받았다. 고친 뒤 패널·마스터 재생성 + `test_viz_ifrs17_panels_golden --update` 사유 기록. 후보 정정값(라이나) `proposed_fixes_existing_cells.json`.
- [ ] **라이나 CSM 분기 백필 후속(owner·publishing)** — ① 새 RED 3(`PL_CSM_AMORT_VS_WATERFALL` 라이나 2025.3Q·2026.1Q·2026.2Q): 건별 등재(`proposed_registry_entries.json`) 또는 재보사 17건과 같이 게이트 설계 변경(경영공시 계보 워터폴 셀은 PL 대조 제외) ② publishing: xlsx `CSM워터폴`(+18행)·`CSM상각`(+30행) 시트 동기화, NB 마스터 재빌드(`build_nb_csm_multiple.py` → 라이나 3행 추가 → live_artifacts `NB_CENSUS_MISSING` 3 해소) ③ 결정: 분기 확장 여부 — 2025.1Q(p57)·2025.2Q(p83)는 지금 읽기 코드로 바로 닫히고 2024.1Q~3Q(p51·p76·p52)는 「분기말 잔액」 라벨 보강만 필요하지만, 라이나는 지금 6분기라 7번째 분기를 더하는 순간 active_min=7 로 MASTER_HOLE RED(2024.1Q~3Q)가 되므로 2024.1Q 부터 한 번에 · 2025.4Q `값_당분기` 5칸(기존 칸)은 다음 `build_csm()` 이 채우거나 승인 후 셀 단위로 ④ `bspl_apply_findpage.py` · `bspl_apply_render.py` 가 `raw/` 를 직접 glob 해 `tests/test_disclosure_raw_pdf_wiring.py` 2건 실패(BS·PL 담당 에이전트 스크립트, `disclosure_pdfs()` 로 교체) ⑤ validation: `test_master_tables_golden` SUMMARY 3필드가 이 적재로 움직인다(closing 381P → 384P · csm_amort_identity 22S → 25S · qoq_warn 252Y → 254Y) — 의도된 변화라 `--update` + 사유 기록(나는 안 했다).

- [ ] **BS·PL 세부 백필 후속(owner·validation·downloader·publishing)** — ① RED(불변): `PL_CSM_AMORT_VS_WATERFALL` 17(재보사 PL 항목 4 계보 한계 — `pl_csm_amort_missing_ledger.json` 건별 등재 또는 게이트 설계 변경, 후보는 CSM 레인 `proposed_registry_entries.json`) · `PL_YTD_COLLAPSE_TO_ZERO` 3(등재 후보 `data/_derived/bspl_granularity_20261011/proposed_owner_confirmed_cells_ytd_collapse.json`, 아니면 항목 23 3칸 철회) · `MASTER_HOLE` 하노버 2025.3Q PL(통째 결손 면제 경로 없음, 원천 not_posted) ② 보류 BS 346칸(후속 378 − 이번에 채운 32; 사유 `data/_derived/bspl_followup_20261011/hold_reasons_5c.md`) + (B) 보류 목록 `data/_derived/bspl_apply_20261011/hold_list_B_20261011.json`: RGA 2025.1Q·2Q·2026.1Q·2Q 항목 13/14/15(8-1 자산 줄 합이 인쇄 총계에 안 닫힘) · RGA 2023.2Q·3Q(재작성 판, `hold_evidence_B_rga.json`) · BNP 항목 10/11/13/20/24(8-1 줄 = 일반계정, 마스터 = 특별계정 포함 DART, `hold_evidence_B_bnp_kr0075.json`) · 악사 10/13/20/21/24(감독서식) · 하노버 2023.3Q 10/13/15/24(AI801 서식 정의) · IBK연금 항목 13 의 2023.4Q→2024.4Q 정의 단절 · 처브 항목 20(D1/D2, `kr0100_item20_table.json`, 권고 D2) · 메트라이프·처브 특별계정 포함 여부 ③ owner: 삼성화재 KR0008 2023.2Q 항목 1·15·16 을 DART 별도 기준으로 맞추는 제안(`proposed_pl_kr0008_2023.2Q_dart_basis.json`; 적용하면 2023.2Q 항목 1 빈 칸이 닫힘) · 이번에 PL 마스터에 직접 고친 37칸은 gold overlay(`data/_gold/user_pl_cells.json`)에 없어 `build_pl` 재실행 시 되돌아간다(등재 후보 `proposed_gold_overlay_pl_20261011.json`, 근본 수정은 KR0072 핸들러의 3개월/누적 쌍 표 열 선택·KR0008 보험종목별 표 합산) · ABL 2023.1Q·2Q AOCI(DART 별도 3,722·3,680억)가 K-ICS 마스터(3,165·3,135억)와 15% 어긋난 새 YELLOW 2건(K-ICS 레인이 어느 기준인지 확인) ④ 골든 `--update`(validation, 사유 기록; BS 골든 고정 9,030행 → 현재 10,962행) ⑤ xlsx 동기화(publishing): 17BS 행 누락 1,932 + 값 드리프트 93 · 손익분해PL 드리프트 121칸 ⑥ PL 항목 1 보류 17칸: A 9칸(생명 항목 2 레그 — Tier-2 생명 핸들러 확장 또는 owner 가 게이트 면제 조건 변경) · B 5칸(항목 15 기타영업수익 = 0.0 승인 시 잔차 −79~+77로 닫힘) · C 3칸(삼성화재 2023.2Q 는 ③ 의 제안으로) ⑦ 빌더 결함(마스터만 고쳤고 코드는 안 고침; 되살아남 방지로 오버레이·사이드카·파트에 같이 기록): `build_ifrs17_bs.py` 항목 10 이 알파벳 순 첫 행(`dart_CashAndDuefromBanks`/`dart_DueFromBanksAtAmortisedCost`)을 집어 `ifrs-full_CashAndCashEquivalents` 를 이김 · FS-API status 013 분기의 XML 폴백(`_pick_bs_table`)이 연결표·엉뚱한 표를 고름 · PL 369행 `값_당분기` None 잔존(항목 1·16·22·23·24) ⑧ 관찰: 라이나 KR0074 FY2024 감사보고서가 2023.12.31 비교열을 소급 재작성(마스터 2023.4Q 는 원 보고서 값 유지) · 마스터가 억원 반올림으로 둔 연말 칸 중 정확값이 있는 것(신한이지·처브 항목 31 등) · 하나생명 2026.1Q 8-1 은 150dpi 화면 캡처 이미지라 재작성본 수령 시 부채 4칸 재독. downloader 별첨 목록은 런로그 「첨부·원천이 필요한 칸」.

- [ ] **재보사(KR1101~KR1108) CSM 계열 마스터 — owner 결정 대기** — ① 새 RED 17(`PL_BUCKET_ABSENT_VS_WATERFALL`): 건별 등재(후보 `data/_derived/reinsurer_ifrs17_csm_20261011/proposed_registry_entries.json`) 또는 게이트 설계 변경 ② 퍼시픽 2024 민감도(FY2025 전기 열이 한 행 밀려 인쇄, 규칙대로 FY2025 채택 중) ③ 스코리 당기손익 부호 반전 적재 확인 ④ 스위스리 신계약 CSM(감사보고서 1,098/1,743억 대 4-6-3 ① 622/1,328억) ⑤ 재빌드 소실 대비 gold-overlay 등재 여부.
  downloader: 하노버·RGA FY2025 IFRS17 감사보고서 별첨(2025.4Q 워터폴 행 부재). 전체 목록 런로그 끝절 `data/disclosure/_meta/reinsurer_ifrs17_csm_runlog.md`.

- [ ] **재보사 ILP 잔여(owner·downloader)** — ① 스위스리 KR1102 2026.1Q: 인쇄 합계가 Indirect-Par 행을 뺀 값(생명 (2,664) 313 197 · 손해 (2,801) 411 487)이라 적재 안 함 — 전체 행 합(생명 (7,506) 363 1,403 · 손해 (4,715) 431 797)을 파생값으로 쓸지 결정.
  ② 하노버 KR1104 2026.2Q: 2-4 합계 BEL −292 대 같은 공시 BS 순 LRC BEL −440.95(RA·CSM 은 같음) — 어느 쪽이 맞는지 발행사 확인 또는 결정(항목 1~8 미적재, LIC 항목 10~15 는 적재). ③ 하노버 2025.3Q PDF 수집(downloader; 2024.3Q 비교 칸도 그 안에 있다).
  ④ 스위스리·제네럴·RGA·스코리·마이브라운과 하노버·퍼시픽 연말은 LIC(10~15)가 비어 있다(경영공시에 재무상태표 상세 없음; RGA·스코리·마이브라운은 연말 감사보고서 주석에 다른 표기로 있어 읽기 구현이 필요). 근거 런로그 §14.
- [ ] **포트폴리오 검증기 RED 7 — owner 예외·정의 결정** — KR0100 R3 5칸(IFRS17_BS 항목 20 의 중간분기 값은 일반계정, 연말·2026 은 특별계정 변액 포함 → IFRS17 레인 정의 통일 또는 R3 예외), KR0029 2024.4Q(구조, 값 맞음), KR1102 2026.1Q(위 ①). 건별 사실표·선택지 `data/disclosure/_meta/ilp_leftovers_runlog_20261011.md` §5(2026-10-11 재확인, 새로 풀린 건 없음).
- [ ] **ILP 라이나·처브 기준(owner)** — ① 라이나 2023.1Q·2Q(항목 10·13·14·15)는 옛 기준(FY2024 공시 비교열이 재작성 전), 2023.3Q·2023.4Q·2024.1Q~ 는 재작성 기준이라 LRC·합계 계열이 2023.2Q → 3Q 에서 끊긴다(LIC 는 매끈) — 두 칸 유지 여부. ② 처브 항목 15·14 는 중간분기 일반계정(9셀: 2023.1Q~2025.3Q) 대 연말 DART(특별계정 포함) 계단 — BS 레인이 항목 20 정의(D1/D2)를 정하면 9셀 항목 14·15 재계산(LIC 불변). 근거 런로그 §2.3.
- [ ] **항목 9 가 빈 국내 55칸** — PDF 대조: 「해당사항 없음/원칙모형」 39(→ 0 후보)·텍스트층에서 못 찾음 16, 「사용」은 롯데(수정 완료) 외 없음. 채울지 owner 결정. 근거 `ilp_round3_20261011/t100_item9_blank_census.txt`, 런로그 §15.2.
- [ ] **designer 패널 재빌드 374셀(348 + 이번 26)** — `ilp_round3_20261011/t120_rebuild_list.txt`(분기별·항목군별 회사 목록) + `ilp_leftovers_20261011/r_rebuild_list.txt`(하나손보 11 · 라이나 3 · 처브 6 신규, 메트라이프 6 값 변경; 하나손보 2026.1Q·2Q 는 부채 기준 LIC 가 급감 — 자산측 LIC −495/−512억이라 항목 8 + 항목 10 ≠ BS 순액, 「추정」(BS20 − 항목 8)이 틀림, provenance `asset_side_eok`). 재보사 8곳 신규, 재작성 사이드카 5셀, 재보사는 항목 8(순액)과 10~15(부채측)의 합이 안 맞음, 재보사 BS 항목 20 이 BS 마스터에 들어와(다른 레인) 빌더의 LIC 「추정」(BS20 − 항목 8)이 재보사에도 걸린다 — 자산측 LRC 가 큰 회사는 추정이 틀리고(뮌헨은 실공시 대조로 제외) 실공시가 없는 스위스리·제네럴·RGA·스코리는 검증 불가, 「미분리 음수」 21건 진단. 런로그 §16.

- [ ] **예별(KR0004) 2025.3Q `PL_YTD_COLLAPSE_TO_ZERO` RED = validation r2 V2-1(기준 혼합) — owner/validation 결정 대기** — 원문이 `제1(당)3분기 2025-06-16~09-30`(신설 예별손해보험(주) 제1기)이고 법인세는 `-` 라 0.0 이 인쇄값이다. 2Q(구 MG 제13기 8,079.7)와 보고주체가 다른 단절이라 값을 바꿔도 다른 RED 가 된다.
  결정지 ① 되돌리기(10-09 에 만든 4행 + 사이드카 1셀 삭제, `MASTER_HOLE(통째)` 복귀) ② 유지 + 근거를 단 셀 단위 등재. 증거 4줄·절차는 런로그 1b §3.3. V2-4(골든 `--update` 보류)가 이 결정에 걸려 있다.
- [ ] **예별 `extract_tier2_yebyeol` 핸들러 후속(PL 골든 재생성 동반)** — 항목 13·14 를 `(수익−비용)+(재보험수익−재보험비용)` 손익 부호로, 장기 열 4합계를 `_jang_*` 로 내면 항목 2/3/8 이 빌더에서 나온다(임시: `_GOLD_CELL_OVERRIDE`, 값은 런로그 1b §3.2).
  지금은 루트 마스터 10칸만 정정돼 있어 `build_pl()` 이 13·14 를 되돌린다. 2023.4Q·항목 5~7·9~12 도 같이.
- [ ] **PL 골든 실패** — `RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py` 에서 `sha256_coverage` 만 어긋난다(master 바이트는 같음).
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
