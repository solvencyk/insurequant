# Insurequant Parser TODO — IFRS17 lane (Stage 2)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-ifrs17.md` · 이력 `docs/changelog_parser_ifrs17.md`
> 2026-10-07 정리 전 전문(88~92차 Status 포함)은 `docs/todo_archive_parser_ifrs17.md` 맨 위에 있다. K-ICS 레인은 `TODO_parser_kics.md`.

## Status (최신 3개)

- **2026-10-11 BS·PL 후속(티켓 20261011T0900Z)** — `IFRS17_BS.json` 10,651 → 10,777행(추가 126 · 값 변경 23 = KR1098 자본금 2026.2Q 2,000 → 3,000억 1 + 코리안리 KR1000 2023.1Q·2Q 22[2Q 복사·잘못된 표 선택 정정], 그 밖 변경 0) · `PL_breakdown.json` 변경 0. 보류 BS 500 → 378(적재 121: 0 증명 69 · 프라이어-연말 브리지 33 · 같은 표·비교열 사슬·규칙 T·줄 합 탐색 19, 사유 등재부 `hold_reasons_5c.md`) · 연속 동일값 전수(BS 복사 오류 KR1000 1묶음) · 처브 항목 20 정의표(권고 D2) · PL 항목 1 보류 17칸 원인 3부류. 커밋 안 함.
  남은 것: data-contract RED 34 → 37(내 몫 1 = `MASTER_XLSX_DRIFT 17BS` 23칸 · `ROW_MISSING 17BS` 1,747행, publishing 이 `sync_master_xlsx_sheet.py "17BS"`) · BS 골든(고정 9,030행) 재생성은 validation · owner 결정(처브 항목 20 D1/D2 · IBK연금 항목 13 정의 · 메트라이프·처브 특별계정 포함 정의) · 마스터 정정 후보 미적용(PL KR0008 항목 14 2023.2Q 일반손익 · PL KR0072 항목 10 4칸 · BS 항목 10 예치금 혼입 KR1000/KR0001/KR0071 30칸 · 한화생명 BS 항목 10 2023.2Q · 상장 2023.1Q·2Q 연결(CFS) 값 KR0070·KR0079 총계).
  근거·재현·되돌리기 `data/disclosure/_meta/bspl_granularity_runlog.md` 맨 위 「중간 결과 — 후속 티켓」 · 도구 `scripts/bspl_followup_*.py` · 산출·증거·백업 `data/_derived/bspl_followup_20261011/`·`bspl_followup_backup_20261011/`.
- **2026-10-11 BS·PL 세부(granularity) 경영공시 백필(티켓 20261011T0310Z)** — 비상장 15사 + 재보사 8곳(+상장 구멍): `IFRS17_BS.json` 9,030 → 10,651행(+1,621) · `PL_breakdown.json` 12,941 → 13,458행(+517 신규·23 null 채움, 항목 1·16·22·23·24 만 — §3d), 기존 행 값·바이트 변경 0. 대상 23사 BS 2,198 → 3,761칸 · PL 1,035 → 1,548칸, 항등식·코어 census 시뮬 실패 0. 커밋 안 함.
  남은 것: data-contract RED 0 → 34(이 적재 몫 `PL_YTD_COLLAPSE_TO_ZERO` 3[법인세 정당 0.0, owner 등재 후보 파일] + `MASTER_HOLE` 하노버 2025.3Q PL[원천 not_posted]; 17 `PL_CSM_AMORT_VS_WATERFALL` 은 CSM 레인이 올린 17 RED 와 같은 칸[룰 이름만 바뀜]; xlsx 12 는 publishing·K-ICS, K-ICS 레인 신규 1) · `test_master_tables_golden` 예상 실패(`--update` 안 함)·BS 골든 미실행 · 충돌 BS 10(KR1098 자본금 2026.2Q 마스터 2,000 이상치 포함)·PL 135 · 보류 BS 500(규칙 불일치 312·앵커 없음 182) · PL 항목 1 보류 17 · PL 17·20·21 855칸 대기 · downloader 별첨(하나손보 9분기·악사 3·BNP 11 등).
  근거·재현·되돌리기 `data/disclosure/_meta/bspl_granularity_runlog.md` · 도구 `scripts/bspl_granularity*.py`.
- **2026-10-11 재보사 8곳(KR1101~KR1108) CSM 계열·경영지표 마스터 적재(티켓 20261011T0430Z)** — `CSM_amortization` +180행(390 → 570) · `CSM_sensitivity` +116행(195 → 311) · `CSM_waterfall` +108행(2,178 → 2,286, 사이드카 +18셀) · `management_indicators` +1,259행(7,665 → 8,924, 티켓 ④), 기존 행 바이트 동일(git HEAD 접두 일치·기존 회사 변경 0). 상각표 18건 합 = 4-6-2 CSM 전건 허용 안 · 민감도 116행과 상각표 6공시 PDF 렌더링 대조 불일치 0 · MI 는 kpi_summary 652/657 · IFRS17_BS 304/306 · kics 171/171 일치, MI 검증기 커버리지 구멍 121 → 23. 커밋 안 함.
  남은 것: data-contract 새 RED 17(`PL_BUCKET_ABSENT_VS_WATERFALL`, 재보사 PL 항목 4 계보 한계 — owner 등재 후보 `proposed_registry_entries.json` 또는 게이트 설계 변경) · `MASTER_XLSX_ROW_MISSING` 3(가정민감도·CSM워터폴·CSM상각 시트 동기화, publishing) · 하노버·RGA FY2025 IFRS17 감사보고서 별첨(downloader) · owner 질문(퍼시픽 2024 민감도 행 밀림 · 스코리 당기손익 부호 반전 · 스위스리 신계약 CSM 두 표 불일치 등 런로그 끝절) · `build_csm_sensitivity.py`·`build_tidy_exports.py --only amort` 재실행 시 행이 사라지니 `load_reinsurer_csm_masters_20261011.py --apply` 로 재적재.
  근거·재현 `data/disclosure/_meta/reinsurer_ifrs17_csm_runlog.md` · 적재기 `scripts/load_reinsurer_csm_masters_20261011.py`·`load_reinsurer_mi_20261011.py`(되돌리기 `--revert --apply`).
## 열린 일

- [ ] **BS·PL 세부 백필 후속(owner·validation·downloader·publishing)** — ① RED: `PL_CSM_AMORT_VS_WATERFALL` 17(재보사 PL 항목 4 계보 한계 — `pl_csm_amort_missing_ledger.json` 건별 등재 또는 게이트 설계 변경, 후보는 CSM 레인 `proposed_registry_entries.json`) · `PL_YTD_COLLAPSE_TO_ZERO` 3(등재 후보 `data/_derived/bspl_granularity_20261011/proposed_owner_confirmed_cells_ytd_collapse.json`, 아니면 항목 23 3칸 철회) · `MASTER_HOLE` 하노버 2025.3Q PL(통째 결손 면제 경로 없음) ② (해소 2026-10-11 후속) KR1098 자본금 2026.2Q 2,000 → 3,000억 정정 ③ 마스터 정의가 연도별로 바뀐 회사의 정의 확정 후 보류 378칸 재평가(사유 등재부 `data/_derived/bspl_followup_20261011/hold_reasons_5c.md`): IBK연금 항목 13 의 2023.4Q→2024.4Q 정의 단절(증권만 → 두 줄 합; 2025.1Q~2026.1Q 4칸은 두 줄 합으로 적재 완료, 2023·2024 중간분기가 남음) · 처브 항목 20(D1/D2, 표 `kr0100_item20_table.json`, 권고 D2 = K-IFRS 라인) · 메트라이프·처브 특별계정 포함 여부 ④ 골든 `--update`(validation, 사유 기록; BS 골든 고정 9,030행 → 현재 10,777행) ⑤ xlsx 동기화 17BS(행 누락 1,747 + 값 드리프트 23)·손익분해PL 517행 + 드리프트 37칸(publishing) ⑥ PL 항목 1 보류 17칸: A 9칸(생명 항목 2 레그 — Tier-2 생명 핸들러 확장 또는 owner 가 게이트 면제 조건 변경) · B 5칸(항목 15 기타영업수익 = 0.0 승인 시 잔차 −79~+77로 닫힘) · C 3칸(**삼성화재 PL KR0008|14|2023.2Q 일반손익 354,530 대 DART 표 재계산 161,674 = 마스터 오류**, 제안 `proposed_pl_correction_kr0008_item14_2023.2Q.json`) ⑦ 마스터 정정 후보(이 티켓은 기존 칸 변경 금지라 미적용): PL KR0072 항목 10 4칸 3개월 열 혼입(`proposed_pl_corrections_kr0072_item10.json`) · BS 항목 10 이 현금및예치금(DART `CashAndDuefromBanks`)으로 들어간 KR1000 7·KR0001 12·KR0071 11칸(`item10_tag_scan.json`; FS-API 행 선택이 알파벳 순서로 `dart_CashAndDuefromBanks` 가 `ifrs-full_CashAndCashEquivalents` 를 이김) · 한화생명 KR0068 항목 10 2023.2Q 마스터 1,143,319.9 는 오류(DART 반기 XML 별도 요약 BS 와 8-1 K 가 모두 1,081,513) · 상장 2023.1Q·2Q 마스터 총계가 연결(CFS) 표 값인 ABL생명 KR0070·미래에셋생명 KR0079(`proposed_bs_corrections_cfs_to_ofs_kr0070_kr0079.json`, 별도 값은 DART 요약별도재무상태표) · DART 별도 요약 BS 로 채울 수 있는 빈 칸 9(런로그 부수 발견 ⑤). downloader 별첨 목록은 런로그 「첨부·원천이 필요한 칸」.

- [ ] **재보사(KR1101~KR1108) CSM 계열 마스터 — owner 결정 대기** — ① 새 RED 17(`PL_BUCKET_ABSENT_VS_WATERFALL`): 건별 등재(후보 `data/_derived/reinsurer_ifrs17_csm_20261011/proposed_registry_entries.json`) 또는 게이트 설계 변경 ② 퍼시픽 2024 민감도(FY2025 전기 열이 한 행 밀려 인쇄, 규칙대로 FY2025 채택 중) ③ 스코리 당기손익 부호 반전 적재 확인 ④ 스위스리 신계약 CSM(감사보고서 1,098/1,743억 대 4-6-3 ① 622/1,328억) ⑤ 재빌드 소실 대비 gold-overlay 등재 여부.
  downloader: 하노버·RGA FY2025 IFRS17 감사보고서 별첨(2025.4Q 워터폴 행 부재). 전체 목록 런로그 끝절 `data/disclosure/_meta/reinsurer_ifrs17_csm_runlog.md`.

- [ ] **재보사 ILP 잔여(owner·downloader)** — ① 스위스리 KR1102 2026.1Q: 인쇄 합계가 Indirect-Par 행을 뺀 값(생명 (2,664) 313 197 · 손해 (2,801) 411 487)이라 적재 안 함 — 전체 행 합(생명 (7,506) 363 1,403 · 손해 (4,715) 431 797)을 파생값으로 쓸지 결정.
  ② 하노버 KR1104 2026.2Q: 2-4 합계 BEL −292 대 같은 공시 BS 순 LRC BEL −440.95(RA·CSM 은 같음) — 어느 쪽이 맞는지 발행사 확인 또는 결정(항목 1~8 미적재, LIC 항목 10~15 는 적재). ③ 하노버 2025.3Q PDF 수집(downloader; 2024.3Q 비교 칸도 그 안에 있다).
  ④ 스위스리·제네럴·RGA·스코리·마이브라운과 하노버·퍼시픽 연말은 LIC(10~15)가 비어 있다(경영공시에 재무상태표 상세 없음; RGA·스코리·마이브라운은 연말 감사보고서 주석에 다른 표기로 있어 읽기 구현이 필요). 근거 런로그 §14.
- [ ] **하나손해보험(KR0050) 분기 별첨 11회차 수집(downloader)** — 2023.1Q~3Q·2024.1Q~3Q·2025.1Q~3Q·2026.1Q~2Q: 분기 경영공시 PDF 가 재무제표·주석(Ⅷ)을 「첨부 파일 참조」로만 둬 LIC 가 비어 있다. 근거 런로그 §13.
- [ ] **포트폴리오 검증기 RED 7 — owner 예외·정의 결정** — KR0100 R3 5칸(IFRS17_BS 항목 20 의 중간분기 값은 일반계정, 연말·2026 은 특별계정 변액 포함 → IFRS17 레인 정의 통일 또는 R3 예외), KR0029 2024.4Q(구조, 값 맞음), KR1102 2026.1Q(위 ①). 근거 런로그 §15.3.
- [ ] **항목 9 가 빈 국내 55칸** — PDF 대조: 「해당사항 없음/원칙모형」 39(→ 0 후보)·텍스트층에서 못 찾음 16, 「사용」은 롯데(수정 완료) 외 없음. 채울지 owner 결정. 근거 `ilp_round3_20261011/t100_item9_blank_census.txt`, 런로그 §15.2.
- [ ] **메트라이프(KR0095) 항목 7·8 6칸(2025.1Q~2026.2Q)** — 합계 행 PAA 가 0.4~0.5억으로 인쇄돼 있는데 마스터는 0.0(옛 추출기가 소수점 아래를 자름). 고칠지 owner 결정. 런로그 §15.5.
- [ ] **designer 패널 재빌드 348셀** — `ilp_round3_20261011/t120_rebuild_list.txt`(분기별·항목군별 회사 목록). 재보사 8곳 신규, 재작성 사이드카 5셀, 재보사는 항목 8(순액)과 10~15(부채측)의 합이 안 맞음, 재보사 BS 항목 20 이 BS 마스터에 들어와(다른 레인) 빌더의 LIC 「추정」(BS20 − 항목 8)이 재보사에도 걸린다 — 자산측 LRC 가 큰 회사는 추정이 틀리고(뮌헨은 실공시 대조로 제외) 실공시가 없는 스위스리·제네럴·RGA·스코리는 검증 불가, 「미분리 음수」 21건 진단. 런로그 §16.

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
