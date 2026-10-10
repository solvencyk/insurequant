# Insurequant Parser TODO — IFRS17 lane (Stage 2)

> 갱신 2026-10-10 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-ifrs17.md` · 이력 `docs/changelog_parser_ifrs17.md`
> 2026-10-07 정리 전 전문(88~92차 Status 포함)은 `docs/todo_archive_parser_ifrs17.md` 맨 위에 있다. K-ICS 레인은 `TODO_parser_kics.md`.

## Status (최신 3개)

- **2026-10-10 후속(1b) IBK연금 2-4 6분기 48칸 정정 · KR0011 중복 9행 제거 · 예별 PL 다리 10칸 정정** — ILP 2,883행·중복 키 0, LIC 검산기 R-LIC2 YELLOW 해소(RED 0·YELLOW 7). 예별 2024.4Q·2025.4Q 항목 2·3·8 채움 + 13·14 부호·범위 정정(폐쇄식이 손익계산서 보험손익과 ±0.001 백만원으로 닫힘) → `MASTER_HOLE` 2건 해소, `coverage_hole 5→3PL`·pl_bridge 31F→29F.
  남은 것: `PL_YTD_COLLAPSE_TO_ZERO` 예별 2025.3Q(= validation r2 V2-1, 신설법인 제1기 기준 혼합, owner/validation 결정) · xlsx `손익분해PL`·public_exports 10칸 재동기화(publishing) · designer `panel_csm_combo.json` 재빌드(KR1011 6분기) · `test_master_tables_golden --update`(validation).
  커밋 안 함. 근거·재현·전후 수치 `data/disclosure/_meta/lic_load_runlog_stage1b.md` · 스크립트 `scripts/fix_20261010_{ilp_kr1011_ibk_total_row,ilp_kr0011_dedup_2025_3q,pl_kr0004_lob_legs}.py`.
- **2026-10-10 발생사고요소(LIC) BEL·RA 1단계 적재** — `insurance_liability_portfolio.json` 항목 10~15 +832행(158셀: A1 53·A2 47·T 58, 억원, owner 정정으로 신규 마스터 아님) + 현대해상 2-4 2025.1Q~3Q 12칸 정정(PAA 합이 VFA 열로·PDF 쪽번호가 VFA CSM 으로 읽혀 있었다). 커밋 안 함.
  검산 `scripts/validate_insurance_liability_lic.py` RED 0(R-LIC1 부채 146셀 최대 2.7ppm + 순액 7셀, R-LIC2 155/156, R-LIC3 158/158) · 미적재 1(예별 4Q, 계약이전 범위 단절) · 원천 부재 75 · 사이드카 `data/_derived/ilp_includes_lic.json`(ABL·KDB생명·푸본현대).
  남은 것: 2단계 간접값 16·17(사전시험 28셀 통과) · 3단계(라이나·처브 PDF·하나손보 별첨·예별) · 재현·근거 `data/disclosure/_meta/lic_load_runlog_stage1.md`(IBK 정정은 1b 에서 끝남).
- **2026-10-09 전사 BS/PL 공란 백필(owner 10-08)** — BS 공란 25+부분 5 → 0(184칸, 경영공시 요약표·4-1표·별도BS, 10사), PL 공란 29 → 1(126칸, 12사·28(회사,분기)).
  후속 10-09: KR0004 2025.3Q 채움(법인세 0 → `PL_YTD_COLLAPSE_TO_ZERO` RED, 등재는 validation/owner) · 보험손익 15칸 보류(pl_bridge 0NEW 복귀) · 당분기 17칸 차분 · xlsx 2시트 동기화. 커밋 안 함.
  재현 `scripts/fix_pl_backfill_followup_20261009.py`·`merge_pl_backfill_disclosure_20261008.py` · 기록 `data/disclosure/_meta/bspl_backfill_runlog_merge.md`(후속 절에 미해결 D2·D4·D5·D8·D9).

## 열린 일

- [ ] **예별(KR0004) 2025.3Q `PL_YTD_COLLAPSE_TO_ZERO` RED = validation r2 V2-1(기준 혼합) — owner/validation 결정 대기** — 원문이 `제1(당)3분기 2025-06-16~09-30`(신설 예별손해보험(주) 제1기)이고 법인세는 `-` 라 0.0 이 인쇄값이다. 2Q(구 MG 제13기 8,079.7)와 보고주체가 다른 단절이라 값을 바꿔도 다른 RED 가 된다.
  결정지 ① 되돌리기(10-09 에 만든 4행 + 사이드카 1셀 삭제, `MASTER_HOLE(통째)` 복귀) ② 유지 + 근거를 단 셀 단위 등재. 증거 4줄·절차는 런로그 1b §3.3. V2-4(골든 `--update` 보류)가 이 결정에 걸려 있다.
- [ ] **예별 `extract_tier2_yebyeol` 핸들러 후속(PL 골든 재생성 동반)** — 항목 13·14 를 `(수익−비용)+(재보험수익−재보험비용)` 손익 부호로, 장기 열 4합계를 `_jang_*` 로 내면 항목 2/3/8 이 빌더에서 나온다(임시: `_GOLD_CELL_OVERRIDE`, 값은 런로그 1b §3.2).
  지금은 루트 마스터 10칸만 정정돼 있어 `build_pl()` 이 13·14 를 되돌린다. 2023.4Q·항목 5~7·9~12 도 같이.
- [ ] **LIC 2단계(단일열 간접 도출 항목 16·17)·3단계(비상장 잔여: 라이나·처브 PDF, 하나손보 별첨, 예별 4Q 결정)** — 판정 기준·사전시험·선결 사항은 런로그 §8·§9. 발주 대기(오케스트레이터).

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
