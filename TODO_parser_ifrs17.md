# Insurequant Parser TODO — IFRS17 lane (Stage 2)

> 갱신 2026-10-22 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-ifrs17.md` · 이력 `docs/changelog_parser_ifrs17.md`
> 2026-10-07 정리 전 전문(88~92차 Status 포함)은 `docs/todo_archive_parser_ifrs17.md` 맨 위에 있다. K-ICS 레인은 `TODO_parser_kics.md`.

## Status (최신 3개)

- **2026-10-22 16차: 교보생명 KR0073 OCI 13칸 최신 비교열 적재(티켓 20261021T1556Z, owner 「남은 일 진행」)** — 2024.4Q(25·26·31·32) · 2025.1Q(같은 4) · 2025.2Q(25·26·29·31·32)를 후속 공시 별도 전기 누적 열로 교체, 세 분기 모두 블록이 닫혀(25 = 26+27+28+29+30+32, 31 = 24+25 잔차 0.000) 보류 없음. 필링 XML 줄 번호로 13/13 재확인(FS-API 와 1e-6 일치), 전부 주석 소급재작성(26 · 재평가잉여금 제거)이고 2025.2Q 의 29 +28,365 만 태그 이동(원 공시도 같은 줄 인쇄). 항목 6·7 · 비 OCI 불변.
  gold set 482→495(마스크 29 불변, 새 박제 없음) · 실제 `build_pl()` 사본 산출로 KR0073 18행만 반영 · 출처표 3블록 · 이음매 단일분기 8칸(2024.4Q·2025.3Q 의 25·26·31·32)은 `null_dangi` 로 공란(다른 필링 기준 누계의 차분이라 「빈 칸이 틀린 값보다 낫다」). 화면: 2025.2Q 기타포괄손익 누계 −9,119.64 → −9,253.29억 · 단일분기 262.95 → 176.71억(후속 공시 3개월 열 인쇄값과 일치).
  게이트 전→후: 데이터계약 RED 0→1(xlsx `손익분해PL` 31셀 = 동기화 지연) · master_tables SUMMARY 2필드(pl_bridge 3696→3697P · oci_vs_bs_aoci 22→23Y; 골든 `--update`) · 연속성/워터폴/NB/live_artifacts 불변 · PL 골든 통과 · rule_coverage 103/104(실패 1 = 같은 xlsx RED). 남은 것: publishing xlsx 시트 동기화(전엔 push 불가) · 2025.4Q 25·26·31·32 단일분기 이음매는 이전부터(후보) · FY2026 3분기 보고서 제출 시 2025.3Q 재갱신.
  근거·재현 `data/_derived/remaining_20261022/a_oci/`(`INDEX.txt` · `verify_xml.txt` · `apply_kr0073_oci.py --verify` / `--revert --apply`) · `docs/changelog_parser_ifrs17.md` 16차. 커밋 안 함.
- **2026-10-22 15차: 교보생명 KR0073 2023.3Q PL 단일분기 = FY2024 Q3 보고서 3개월 열 인쇄값(검증 티켓 20261021T1655Z, 코디네이터 「옵션 B-lite」)** — 3e53aef8 이 만든 2023.3Q 값_당분기(재작성 전 상반기 누계와 재작성 후 9개월 누계의 차; 보험손익 190,929 대 공시 3개월 열 89,282 · CSM상각 252,287 대 150,548)를 보고서(`20241114003039.xml` 별도 기준 전기 3개월 열)가 인쇄한 값으로 바꿨다: 인쇄되고 항등식 10개가 닫히는 29칸(항목 1~12 · 16~32)은 인쇄값(SET), 인쇄 안 된 항목 15 는 공란(NULL), 0.0 인 13·14 와 2023.2Q·4Q·2024.3Q·값(누계)은 불변. 독립 두 판독(원문 XML 줄 ↔ FS-API+생산 Tier-2 핸들러) 29/29 일치.
  장치: gold `user_pl_cells.json` 의 선택 키 `set_dangi.cells`([코드,분기,항목,값,출처 줄])·`null_dangi.cells`(항목 15)를 `build_root_masters.build_pl()` 이 읽는다(기존 억제 장치가 없어 최소 확장, 게이트 예외·등재부 없음, 겹치면 거부, 테스트 4개). 네 분기 단일분기 합은 연 누계와 어긋난다 = 공시된 적 없는 재작성 상반기 보정(원수 CSM상각 525,962 대 627,701, 차 101,739). CSM 2023.3Q 단일분기 +960.03억(적재 전 −589.16)은 그대로.
  게이트 전→후: 데이터계약 RED 0→1(xlsx `손익분해PL` 19셀 = 시트가 옛 파생값을 들고 있음) · YELLOW 169 · master_tables SUMMARY 전 필드 불변 · 연속성 red 0 · 워터폴/NB/live_artifacts 불변 · 실제 `build_pl()` 재실행 KR0073 448행 차이 0(다른 회사 기존 드리프트 495셀 같은 집합) · 테스트: survive-rebuild 7/7(신규 4) · gold 10 · identity 14 · viz 골든 2종 · 지문 6 spec ok · PL 골든(266초) 통과, manifest 103/104(실패 1 = xlsx 드리프트 19셀), master_tables 골든 SUMMARY 전 필드 일치(--update 불요).
  남은 것: publishing = xlsx `손익분해PL` 2023.3Q 값_당분기 HEAD 대비 19셀(항목 1~7 · 11 · 12 · 15 · 17 · 19 · 20 · 22~25 · 28 · 31)·`public_exports` / validation = 게이트·골든 재실행(마스터 SUMMARY 는 불변). 커밋 안 함.
  근거·재현 `data/_derived/kyobo_seam_blank_20261022/`(`INDEX.txt` · `seam_3m_extract.txt` · `apply_seam_set.py --verify` / `--revert --apply`) · `docs/changelog_parser_ifrs17.md` 15차.
- **2026-10-22 14차: 교보생명 KR0073 PL 최신 비교열 갱신 + CSM 재작성 기준(R) 적재(티켓 20261021T1310Z E1~E4 완결 · owner 「박제 거부, PL 마스터가 낡았다」)** — PL 2023.1Q~2024.2Q 6분기 122셀(변경 68 · 신규 채움 54; 예: 2023.4Q 항목 4 원수 CSM상각 437,009→627,701, 연간 순이익 489,082→632,201백만)을 후속 공시 별도 전기(누적) 열로 `user_pl_cells.json` 에 +122 등재(마스터 KR0073 152셀, 출처표 12블록 = emitter 산출)하고 CSM R 패키지(6분기 41셀 · gold +14/갱신 27[E5 포함] · 박제 없음)를 E5 위에 적재. 항등식 10개 · PL↔CSM 상각 짝 6/6 정확히 닫힘, 빌더 재실행이 CSM 2,358행 · PL KR0073 448행을 그대로 재현.
  게이트 전→후: 데이터계약 RED 1→2(xlsx `손익분해PL` 추가, `CSM워터폴`은 기존) · YELLOW 169 불변 · master_tables csm_amort 387P/1PIN/0F/5S 불변(박제안의 신규 RED 5 소멸) · pl_bridge 3676→3696P · qoq 266→262 · **tax22_src 282P/0F→278P/4F**(2023.3Q~2024.2Q; 룰이 원 공시 법인세와 대조 → validation `9f69ffcf` 가 룰을 고쳐 282P/0F 로 복귀) · 연속성 red 0 · 워터폴/NB/커버리지/live_artifacts 불변 · 테스트: gold 10 · identity 14 · viz 골든 2종 · PL 골든(364초) 통과, manifest 101/102(실패 1 = xlsx 드리프트), master_tables 골든은 SUMMARY 4필드 이동(validation `--update` 대기).
  범위 밖(별도 open 티켓 `20261021T1556Z`): 2024.4Q·2025.1Q·2025.2Q OCI 13칸이 후속 공시 전기 열과 다르다. 이월: `IFRS17_BS` 2023.4Q·ILP LIC 는 원 공시 기준 그대로(PL 순이익과 어긋남, 별도 갱신 필요); 2023.3Q 당분기 이음매는 15차에서 공시 3개월 열 인쇄값으로 교체했다.
  처리됨: publishing `eea3f61c`(xlsx 두 시트 · NB · 비교/콤보 패널) · `011e0bfc`(public_exports) / validation `9f69ffcf`(`tax22_src` 룰 · 골든 · 지문). 커밋은 메인이 했다.
  근거·재현 `data/_derived/kyobo_pl_restate_dryrun_20261021/`(`INDEX.txt` · `pl_cell_changes.csv` · `apply_kr0073_pl_refresh.py --verify` / `--revert --apply`) · `data/_derived/kyobo_csm_basis_fix_20261021/`(`apply_kr0073_fix.py --scenario R`) · `docs/changelog_parser_ifrs17.md` 14차.

## 열린 일

- [ ] **교보생명 KR0073 PL·CSM 최신 비교열 후속(14차 이월)** — ① (16차에서 적재 완료: OCI 13칸, 티켓 `20261021T1556Z` answered; 남은 것 = publishing xlsx `손익분해PL` 동기화, 2025.4Q 단일분기 이음매 후보, FY2026 3분기 보고서 제출 뒤 2025.3Q 재갱신) ② `IFRS17_BS` 2023.4Q 와 ILP LIC(BS20↔ILP15 짝)는 아직 원 공시 기준 — FY2024 연차 비교 재무상태표(기초 보험계약부채 960억 과대 정정 반영)로 갱신하는 별도 작업이 필요하고 PL 연간 순이익(489,082 → 632,201백만)과 어긋나 있다.
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
