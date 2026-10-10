# Insurequant Parser TODO — IFRS17 lane (Stage 2)

> 갱신 2026-10-10 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-ifrs17.md` · 이력 `docs/changelog_parser_ifrs17.md`
> 2026-10-07 정리 전 전문(88~92차 Status 포함)은 `docs/todo_archive_parser_ifrs17.md` 맨 위에 있다. K-ICS 레인은 `TODO_parser_kics.md`.

## Status (최신 3개)

- **2026-10-10 발생사고요소(LIC) BEL·RA 1단계 적재** — `insurance_liability_portfolio.json` 항목 10~15 +832행(158셀: A1 53·A2 47·T 58, 억원, owner 정정으로 신규 마스터 아님) + 현대해상 2-4 2025.1Q~3Q 12칸 정정(PAA 합이 VFA 열로·PDF 쪽번호가 VFA CSM 으로 읽혀 있었다). 커밋 안 함.
  검산 `scripts/validate_insurance_liability_lic.py` RED 0(R-LIC1 부채 146셀 최대 2.7ppm + 순액 7셀, R-LIC2 155/156, R-LIC3 158/158) · 미적재 1(예별 4Q, 계약이전 범위 단절) · 원천 부재 75 · 사이드카 `data/_derived/ilp_includes_lic.json`(ABL·KDB생명·푸본현대).
  남은 것: IBK연금 2-4 6분기 오류 정정 허가 · 2단계 간접값 16·17(사전시험 28셀 통과) · 3단계(라이나·처브 PDF·하나손보 별첨·예별) · 재현·근거 `data/disclosure/_meta/lic_load_runlog_stage1.md`.
- **2026-10-09 전사 BS/PL 공란 백필(owner 10-08)** — BS 공란 25+부분 5 → 0(184칸, 경영공시 요약표·4-1표·별도BS, 10사), PL 공란 29 → 1(126칸, 12사·28(회사,분기)).
  후속 10-09: KR0004 2025.3Q 채움(법인세 0 → `PL_YTD_COLLAPSE_TO_ZERO` RED, 등재는 validation/owner) · 보험손익 15칸 보류(pl_bridge 0NEW 복귀) · 당분기 17칸 차분 · xlsx 2시트 동기화. 커밋 안 함.
  재현 `scripts/fix_pl_backfill_followup_20261009.py`·`merge_pl_backfill_disclosure_20261008.py` · 기록 `data/disclosure/_meta/bspl_backfill_runlog_merge.md`(후속 절에 미해결 D2·D4·D5·D8·D9).
- **2026-09-22 라이나생명 2023.4Q PL 20칸 신규 충전** — FY2024 사업보고서 전기 비교컬럼 + 주석23(2024.4Q·2025.4Q 와 같은 재작성 기준).
  FY2023 은 소급재작성됐다(자기 보고서 순이익 463,997 vs 채택값 511,309). PL 골든·입력지문 재생성 `a0f0607`.

## 열린 일

- [ ] **ILP 항목 1~9 — IBK연금(KR1011) 경영공시 2-4 6분기 정정(허가 대기, 2026-10-10 발견)** — 마스터는 항목 1~6=0·항목 7=항목 8(72,887 등)인데 2025.4Q PDF p21 합계 행은 일반모형 72,887.3/480.8/4,694.9 + 변동수수료접근법 319.1/47.7/508.8(합 78,938.6 = DART LRC 78,938.7).
  6분기 모두 같은 오류이고 정정안(PDF 합계 행)을 런로그 §10 에 확정해 뒀다. 티켓이 항목 1~9 수정을 P3 외에 금지해 고치지 않았다.
- [ ] **LIC 2단계(단일열 간접 도출 항목 16·17)·3단계(비상장 잔여: 라이나·처브 PDF, 하나손보 별첨, 예별 4Q 결정)** — 판정 기준·사전시험·선결 사항은 런로그 §8·§9. 발주 대기(오케스트레이터).

- [ ] **PL 골든 실패** — `RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py` 에서 `sha256_coverage` 만 어긋난다(master 바이트는 같음).
  KR0074 라이나 2023.4Q 1행: 디스크 coverage 는 `no_income_statement`·missing 21·tier2 `partial`, 빌더 재실행은 missing `[4]`·tier2 `ok`.
  `a0f0607` 이후 디스크 coverage 와 빌더 산출이 어긋난 것으로 보인다. 2026-10-06 K-ICS 정정과는 무관함을 확인했다.
- [ ] **PL 부모 #2 결측 26버킷(display 7)** — `inbox/parser/20260918T0710Z`. 칸마다 `FILLED`/`ABSENT_IN_SOURCE`/`UNREADABLE` 로 회신.
- [ ] **KR0004 2025.4Q 비교 단절 주의** — 예별 = 구 MG = DART 명의 엠지, 한 계열이다. 2025-09-03 계약·자산부채 이전 때문에 DART(총자산 728억)와
  경영공시(38,191억)가 52배 다르다. 마스터 PL 2025.4Q 가 이전 전후 범위를 어떻게 담는지, 경영공시 `2025년` 열이 이전 후 기간만인지는 확인 안 함. 근거 `inbox/_resolved/20260918T0705Z`.
- [ ] **ZERO_LEGS DART 4Q 9건** — 아이엠라이프·AIA·예별·카카오페이·하나손보 4Q. sub-leg 추출 갭 가능성(validation 2026-09-20 12차). 원문 확정.
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
