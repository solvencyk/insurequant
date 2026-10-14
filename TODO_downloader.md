# Insurequant TODO — Downloader Stage (Stage 1)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-downloader.md` (+ `docs/agents/source-catalog.yaml`) · 이력 `docs/changelog_downloader.md`
> 2026-10-07 정리 전 전문(완료 행 포함)은 `docs/todo_archive_downloader.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-11 사이트 현행판 vs raw 전수 대조(48코드 x 14분기, raw 645칸)** — 605칸을 사이트·협회 현행 게시본과 대조(전 약 80칸): 동일 558 · **신판 23**(raw `_v` 16 + attachments 7) · 바이트만 다름 16 · 서식만 6 · raw 가 더 완전 2. **K-ICS 수치가 바뀐 새 판 7칸**(예별 2025.4Q 비율 △8.24→△13.53 · NH손보 2025.1Q · KDB 2025.3Q · 교보 4칸), KB 스캔 raw→텍스트판 2칸, 모두 새 판 PDF 생성일이 raw 보다 뒤.
  parser 티켓 2건(`inbox/parser/20261011T1210Z…`·`…T1215Z…`), 칸별 결과 `data/disclosure/_meta/site_edition_census_result_20261011.json`, 런로그 `…/site_edition_census_runlog_20261011.md`. 못 한 것: 코리안리 11칸(443 TLS 재설정) · 퍼시픽·마이브라운 · **생보 회사 사이트 137칸은 협회만 대조**. 공유 티켓 `20261011T1100Z` 는 오케스트레이터가 종결.
- **2026-10-11 경영공시 BS·PL 별첨 수집(70칸)** — 별첨 60건(90MB, `FY*/attachments/`; 하나손보 14분기 별도·연결 FS, 신한이지 결산공고·감사보고서, 카카오페이 Q4 감사보고서) 수령. **25칸은 8-1/8-2 가 이미지 쪽으로 raw 에 이미 있음**(BNP 9·하나생명 9·RGA 4·AXA 3), 원천 부재 7·정책 4·해당없음 9.
  새 판 3건 raw/`_v`(AXA 2024.3Q K-ICS 완성본 등), parser 티켓 2건(`inbox/parser/20261010T2350Z…`·`…2351Z…`), KR0075 2024.2Q 는 회사 파일 자체가 잘림(honest gap). 런로그 `data/disclosure/_meta/attachments_fetch_runlog_20261011.md`. 공유 티켓 `20261011T0830Z` 는 오케스트레이터가 종결.
- **2026-10-10 재보사 헤드라인 전용 12칸 재확인** — 2칸 해소(KR1102 2023.4Q K-ICS 완성본 `_v20240510` · KR1107 2024.3Q 원문), 원천 부재 6 · 수집 정책 4(KR1107 2023.x).
  parser(kics) 티켓 2건, 런로그 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_9d.md`. 남은 것: KR1107 www 호스트 Incapsula 확인창(우회 안 함) · 다른 호스트 사용 여부는 owner 판단.

## 열린 일

- [ ] **전수 대조 잔여 (2026-10-11 census 후속)** — ① 코리안리 KR1000 사이트 11칸(Q4 3칸은 협회로 확인): www.koreanre.co.kr 443 이 TLS 재설정으로 접속 불가, 다른 시간대·망에서 재시도. ② 생보 회사 사이트 137칸 미대조(협회 현행본만 대조: 한화생명·푸본현대·동양·신한라이프·KB라이프·플래닛·IBK 전부, 삼성·흥국·DB생명·교보·메트라이프·ABL 일부). 방법·스크립트 `data/disclosure/_meta/site_edition_census_20261011/` (`life_site_run2.py` 가 쪽 이동·select 지원). ③ 새 판 저장분 처리는 parser 티켓(`20261011T1210Z`·`T1215Z`)으로 넘김.
- [ ] **2026.3Q 정기경영공시 수집** — 루트 `TODO.md` 라운드. 생보는 분기 다운로더를 복제해 기간 라벨만 올리고, 수집분은 내용검증(신선도·기간·문서형) 3종을 통과해야 수집으로 친다.

## 백로그

| # | Task | Priority | Notes |
|---|------|----------|-------|
| F7 | KOSIS 손보사별 손해율 시계열 ingest | P1 | `orgId=382, tblId=TX_38202_A1561`, JSON API. 미착수(`data/kosis/` 없음) |
| F8 | 손보협회 비교공시 (consumer.knia.or.kr) — 채널별 불완전판매·정착률·민원·부지급률·지급지연 | P1 | 사이트 구조 probe 단계. F13(publishing) 선행조건. 미착수 |
| F9 | data.go.kr 금융통계 API 추가 연동 (`15061307`·`15061306`·`15094797`) | P2 | `data/_archive/20260803T063432Z/src/bonds/fsc_client.py`(보관본; `src/bonds/` 는 없음) 패턴 재활용 |
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
