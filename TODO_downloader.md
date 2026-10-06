# Insurequant TODO — Downloader Stage (Stage 1)

> 갱신 2026-10-07 · 프롬프트 `docs/agents/claude-agent-downloader.md` (+ `docs/agents/source-catalog.yaml`) · 이력 `docs/changelog_downloader.md`
> 2026-10-07 정리 전 전문(완료 행 포함)은 `docs/todo_archive_downloader.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-09-18 서울보증 8분기 PDF 재확인** — 신규 결측이 아니라 `audit_all_periods.py` `SGI_QUARTERLY_STRUCTURAL` 그대로. SGIC 공시 페이지는
  "연간 + 최신 1분기" 만 노출하고 지난 분기는 롤오프한다. 원천 부재 재확인, 재수집 대상 없음.
- **2026-09-12 J-ESR 킥오프 census 79사** — posted 15 / not_yet 62 / not_found 2, `J-ESR/fy2025_esr_census_20260912.csv`. 손보 11건이 "10월 말 공표 예정".
- **2026-09-12 정정본 병존 저장(`save_versioned_pdf`)** + KR0075 2023.4Q 0.08% 차이 조사 — 정정공시 없음 확정.

## 열린 일

- [ ] **2026.3Q 정기경영공시 수집** — 루트 `TODO.md` 라운드. 생보는 분기 다운로더를 복제해 기간 라벨만 올리고, 수집분은 내용검증(신선도·기간·문서형) 3종을 통과해야 수집으로 친다.

## 백로그

| # | Task | Priority | Notes |
|---|------|----------|-------|
| F7 | KOSIS 손보사별 손해율 시계열 ingest | P1 | `orgId=382, tblId=TX_38202_A1561`, JSON API. 미착수(`data/kosis/` 없음) |
| F8 | 손보협회 비교공시 (consumer.knia.or.kr) — 채널별 불완전판매·정착률·민원·부지급률·지급지연 | P1 | 사이트 구조 probe 단계. F13(publishing) 선행조건. 미착수 |
| F9 | data.go.kr 금융통계 API 추가 연동 (`15061307`·`15061306`·`15094797`) | P2 | `src/bonds/fsc_client.py` 패턴 재활용 |
| F10 | GA 통합공시 (gapub.insure.or.kr) | P3 | 사이트 구조 probe |
| F14 | 규제 뉴스 피드 (roadmap §1E) | P3 | 큐레이션 피드, 자동발행 X |
| DART-RAW-PROVENANCE | DART raw source_file+as_of 사이드카 | P2 | bonds 완료, DART raw 잔여 |
| CAPSEC-SAMO-GAP | 삼성생명·악사·하나손해·AIA·삼성화재 사모채 per-bond 데이터 없음 | P2 | 공개소스 없음 — publishing 처리 방식 결정 필요 |
| BATCH-HISTORICAL-FIX | `ifrs17_batch_historical.py` 정정 rcept picking 버그 소급감사 | P2 | 코드 fix 2026-08-13 완료, 소급 전수 재검사 미실시 |
| F15-DL | 동양생명 2025.2Q~2026.1Q 재다운로드 검토 | P2 | 본체는 parser 버그(잔액행 0). 재다운로드 효과부터 확인 |
| OCR-MARKETRISK | 시장위험 스캔-only PDF OCR 경로 | 보류 | owner 2026-08-15 "됐어 패스" — 재요청 전 미착수 |
| MISC-SEIBRO | Seibro HTML fallback | low | FSC 가 동작하므로 후순위 |
| IR-DONGYANG-401 | 동양생명 IR factbook 401 | low | disclosure 로 대체 완료, IR 전용 지표가 필요할 때만 |

## 결정 (downloader 범위)

| # | Decision | Date |
|---|----------|------|
| D5 | API keys: repo root `.env` only (gitignored). `OPENDART_API_KEY` / `DATA_GO_KR_BOND_ISSUANCE_KEY` / `DATA_GO_KR_BOND_REDE_KEY`. Never commit/log key values. `bonds` source 는 2026-08-03 retire, 키는 F9 재사용 대비 유지 | 2026-05-24 |
| D6 | Bond Call rule: issue + 5y for ALL bonds. Past 5y = assume `called` | 2026-05-24 |
| DL-FYR | 2026.2Q 부터 URL/XPath 는 스스로 찾는다. 기존 설정 재사용, 기간 라벨만 교체. 사이트 구조가 통째로 바뀐 경우만 사람에게 | 2026-05-30 |
| DL-NOATTACH | DART 별첨(감사보고서 zip) 받지 않는다 — 본문 XML 에 IFRS17 주석 전부 있음 | 2026-05-30 |
| DL-NOTSKIP | KR0029 AIG · KR0150 SGI 는 DART 에서 받을 수 있는 만큼 받는다 | 2026-05-30 |
| DL-DART-C-FY23 | 비상장 11사 Q1-3 DART 분기보고서 = 구조적 미제출(gap 아님), FY2023_Q4 감사보고서 = 받지 않음. 재제기 금지 | 2026-06-03 |
| DL-2022Q4-HOLD | 법정준비금 항목5-8용 2022.4Q 본문 XML 24사 = 보류 | 2026-08-19 |
