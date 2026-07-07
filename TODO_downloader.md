# Insurequant TODO — Downloader Stage

> Last updated: 2026-07-07 · Stage 1/5 — downloader
> Prompt: docs/agents/claude-agent-downloader.md (+ docs/agents/source-catalog.yaml) · Changelog: docs/changelog_downloader.md

**Cross-stage TODO:** `TODO.md` (root). **This file:** active + done items scoped to data collection only.

## Status

5-source 전수 수집 완료 (as of 2026-06-01). 무결성 **2,041/2,041 OK**. **전 source 실질 gap 0** (NONLIFE-Q123 26셀 자체사이트 backfill + 서울보증 분기/DART는 미상장·롤오프 구조적 drop). 상세 history는 `docs/changelog_downloader.md`.

**Parser 핸드오프 주의 (Q2=반기):** AIG손해(KR0029)는 별도 2분기 공시가 없고 **상반기(반기) 누적** 공시로 FY{Y}_Q2를 채움(1.1~6.30 누적, 독립 분기 아님). 신한EZ(KR0051)·카카오페이(KR1098)의 Q2도 "상반기" 라벨. parser/validation에서 이들 Q2를 standalone-quarter가 아닌 cumulative-반기로 해석할 것.

검증 도구: `scripts/audit_all_periods.py`(전수 gap audit) + `scripts/check_data_file_integrity.py`(파일 무결성). 신규 다운로드 후 이 둘을 게이트로 실행.

---

## Active follow-ups (next sessions)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| ~~HKF-WAF-BLOCK~~ | ~~흥국화재(KR0005) FY2024_Q4 정기경영공시 재취득~~ | ✅ **2026-07-07 완료(재취득 불필요로 정정)** | WAF 때문에 재다운로드는 결국 못했지만 **필요 없었음** — 원인 재조사 결과 **기존 raw가 이미 맞는 파일**이었음(폰트인코딩 깨짐으로 fitz 텍스트추출만 실패, 렌더링+비전으로 읽으면 정상 정기경영공시). 흥국생명(KR0071)도 동일 패턴(스캔이미지+뒤에 감사보고서 합본). 양사 item1-28(전/후)·item36 등을 raw에서 직접 판독해 `kics_disclosure.json` 반영, 게이트 RED 0. 상세: `docs/changelog_downloader.md` 2026-07-07, `TODO_parser_kics.md` 8차 |
| F7 | **KOSIS 손보사별 손해율 시계열 ingest** | 🔴 P1 | 출처: 국가통계포털 KOSIS `orgId=382, tblId=TX_38202_A1561`. JSON API 공개 → 자동화 쉬움. 손해보험사별 원수보험료/보유보험료/경과손해율 (개별사 × 분기/연간). 현재 손해율은 PDF/HTML 파싱 기반 → KOSIS 교차검증으로 품질 보완. **액션**: `scripts/ingest_kosis_loss_ratio.py` 신규 + `data/kosis/<stamp>/` |
| F8 | **손보협회 비교공시 (consumer.knia.or.kr) — GA 인사이트** | 🔴 P1 | 핵심 항목: (a) **채널별 불완전판매비율** (GA/직판/방카 구분) (b) **설계사정착률** (c) **민원발생현황** (d) **보험금 부지급률** (e) **보험금 지급지연율**. **액션**: 사이트 구조 probe (JS-rendered 가능성 점검) → API 또는 scrape 결정 → `data/knia_consumer/` |
| F9 | **data.go.kr 금융통계 API 추가 연동** | 🟠 P2 | 이미 자본성증권 (15059611) 연동 패턴 있음. 추가: (a) `15061307` 금융통계손해보험정보 (b) `15061306` 금융통계생명보험정보 (c) `15094797` 실손보험정보. **액션**: `src/bonds/fsc_client.py` 패턴 재활용해서 `src/finstat/` 신규 모듈 작성 |
| F10 | **GA 통합공시 (gapub.insure.or.kr)** | 🟠 P3 | GA별 불완전판매비율/계약건수/모집실적. **액션**: 사이트 구조 probe |
| F14 | **규제 뉴스 피드** (roadmap §1E) | 🟠 P3 | 최근 1주 규제뉴스 스크래핑 + 키워드 피드백 학습 랭킹. 큐레이션 피드(자동발행 X) |
| DART-RAW-PROVENANCE | DART raw 23사×13분기 source_file+as_of 사이드카 (`emit_dart_raw_provenance.py`) | 🟠 P2 | Phase 2 gate: CSM_waterfall/PL_breakdown 마스터 provenance 필요. bonds 완료, DART raw 잔여 |
| CAPSEC-SAMO-GAP | 삼성생명·악사·하나손해·AIA·삼성화재 사모채 per-bond 데이터 없음 | 🟠 P2 | FSC 0건, DART 0건 확인. 공개소스 없음. forward-sim에서 BS 총계 기반 단순가정 처리 불가피 — publishing 결정 필요 |
| OCR-MARKETRISK | 시장위험 스캔-only PDF OCR 경로 | 🟠 P2 | KB손해·한화손해 2023.4Q 금리위험 = full-page 이미지(텍스트레이어 없음); 카카오페이 2025.4Q 시장위험 = 스캔. 파서가 fitz/pdfplumber로 텍스트 못 뜸 → OCR 필요. **결정 대기**: downloader OCR 스택 도입 vs owner 수동 OCR. 확보되면 parser/kics가 시장위험 36-40 추출. 출처 `inbox/downloader/20260614T1232Z` item(2) |
| MISC-SEIBRO | Seibro HTML fallback | 🟢 low | m.seibro.or.kr smoke ok; lower priority since FSC works |
| ~~REORG2-DART~~ | ~~DART batch script 3개 canonical-layout refactor~~ | ✅ **2026-05-30N 완료** | `scripts/_dart_path_helpers.py` 신규 + 3 script 갱신 + smoke 9/9. 다음 분기 fetch는 `data/dart/FY<year>_Q<q>/raw/` canonical 위치에 쌓임 |
| BATCH-HISTORICAL-FIX | `ifrs17_batch_historical.py` 정정 rcept picking 버그 | 🟠 P2 | DART는 정정([기재정정], [첨부정정]) 공시가 원본보다 먼저 나올 수 있음 → 잘못된 rcept picking → status=014 'file not found' 에러. **고침 방향**: 정정 prefix 제외하고 가장 늦은 rcept (또는 원본 사업/반기/분기보고서)를 picking. REORG2-DART와 같은 PR에서 같이 처리 권장 |
| F15-DL | 동양생명 2025.2Q~2026.1Q 재다운로드 검토 | 🟠 P2 | (F15 본체는 parser 버그 — `TODO.md`) 추출단계에서 wide `<TE>` 표의 잔액(기초/기말)행이 전부 0으로 들어옴 → 원본 다시 받아야 할 수도 있음. 재다운로드 후 재파싱이 효과적인지 먼저 확인 |
| FUTURE-DL | DART 별첨 fetch endpoint 조사 (KB/메리츠/NH FY2025 LOB) | 🟠 P2 | KB/메리츠/NH FY2025 사업보고서는 LOB 표를 별첨 감사보고서로 분리. 결정 2026-05-30: **fetch 안 함** (본문에 다 있음, 회사별 라벨 변형 처리로 해결). 단 별첨 endpoint 위치는 future reference로 기록 — 새 이슈에 필요 시 조사 |
| IR-SAMSUNGLIFE-23 | 삼성생명 IR FY2023 Q1/Q2/Q3 standalone factsheet 부재 | 🟢 low | samsunglife.com IR은 ~2년치만 보존 → FY23 Q1-Q3 standalone factsheet 롤오프됨 (2026-05-30P 확인). **단 데이터는 살아있음**: 보유 중인 `★ 4QFY23FactsheetKOR.xlsx`에 1Q~4Q 분기 컬럼 물리적 존재 → parser stage에서 구판 시트 레이아웃(`parse_factsheet`가 "월초대비 신계약CSM 배수" 라벨 못 찾음) 핸들링하면 복구 가능. **다운로더 액션 없음** — parser stage 이슈로 이관 |
| ~~NONLIFE-Q123~~ | ~~손보 6사 분기(Q1-Q3) 경영공시 — 회사 자체사이트 스크래퍼~~ | ✅ **2026-06-01 완료** | 34셀 중 **26셀 backfill 수집**(AIG 9 / 악사 4 / 신한EZ 4 / 코리안리 6 / 카카오 3), **8셀(서울보증)은 구조적 미발행** 판정. 사별 스크립트 `scripts/backfill_q123_<token>.py` (aig/axa/shinhanez/sgi/koreanre/kakaopay). 검증: 무결성 2,041/2,041 OK + audit disclosure REAL GAPS 0. ⚠️ AIG/신한EZ/카카오 Q2 = 반기 누적(위 핸드오프 주의 참조). 서울보증 = 자체사이트 연간+최신분기만 보존(audit `SGI_QUARTERLY_STRUCTURAL` 예외 등록) |
| ~~HEUNGKUK-CALL-FIX~~ | ~~흥국화재 신종자본증권1 콜 미행사 override~~ | ✅ **2026-06-17 완료** | normalize.py `_CALL_NOT_EXERCISED={"KR60005416C3"}` 추가 → 재실행 → KR0005 신종 3,200→**4,120억** (FS appendix 일치). normalize `20260616T153258Z`. provenance 재발행 |
| ~~CAPSEC-DART-FETCH~~ | ~~자본성증권 in-force per-bond DART fetch (KDB생명·농협생명)~~ | ✅ **2026-06-16 완료** | FSC 0→DART B-type 조사→KDB 2건(2,410억)+농협 2건(5,000억). 교보=미발행. 현대해상=FSC 정확(parser오류). `data/bonds/disclosure/2026q1_capital_securities.json`. `inbox/publishing/20260616T1300Z` |
| ~~PROVENANCE-BONDS~~ | ~~bonds provenance 사이드카 emission (Phase 2)~~ | ✅ **2026-06-16 완료** | `bonds_provenance.json`(24사) + `disclosure_bonds_provenance.json`(2사). as_of=2026-03-31, effective_filtered=true. `scripts/emit_bonds_provenance.py` |
| ~~CSM-CONTINUITY~~ | ~~CSM 워터폴 연속성(기말≠기시) 복구 raw~~ | ✅ **2026-06-16 완료** | owner: 2026.1Q 기시 전사 misparse(`FY2026_Q1` git-purge로 0 dirs). **우선 5사 2026.1Q**(교보·메리츠·신한라이프·에이비엘·푸본) + `validate_csm_continuity` break(코리안리 23.4Q→24.1Q 경계 + FY2023 드리프트 현대·에이비엘·KDB·교보 + FY2024 KB라이프·코리안리)→ **FY2023/FY2024 Q1-Q4 동반 = 33/33 fetched**, CSM블록 결손 0. break는 24.4Q/25.1Q 아니었음. parser raw-ready `inbox/parser/20260616T0640Z`. ⚠️rebuild은 복원분+기존 raw 범위 |
| ~~CAPSEC-VERIFY~~ | ~~자본성증권 발행현황 검증·수정 (owner 0506Z #2)~~ | ✅ **2026-06-16 완료** | registry **bare-stem alias 오수집** 발견·수정(메리츠/아이엠/미래에셋/카카오 → 계열사 채권 오태깅, 메리츠 1.77→19.6조 폭증). 4 alias 제거(`{nonlife,life}_insurer_registry.yaml`). 재크롤 clean(normalized `20260616T060817Z`): 22/24 live 동일, 🔴KR1098 카카오페이 3,202억→0(가짜), 🟢KR0099 KB라이프 0→1,200억(누락분), KR0011 −890(정상). big-3 Face 정확→owner T2 BS −11.6%는 parser BS시가측 추정. parser-kics `inbox/parser/20260616T0615Z`. ⚠️tier 재빌드는 publishing/parser gate |
| ~~NBCSM-INTERIM~~ | ~~NB CSM 시계열 오염 복구용 interim DART raw~~ | ✅ **2026-06-16 완료** | parser/ifrs17 발주(validation partial-extract 오염). git-purge로 부재한 반기/분기보고서 raw를 `ifrs17_batch_historical.py --skip-extract`로 **10사×{2025.2Q,2025.3Q,2023.1Q}=30셀 fetch-only 재취득**(30/30). CSM 블록 29/30 존재(우선 7셀 OK, 롯데 2025.2Q NB=0 최악건 포함). 🔴 honest gap: 롯데 2023.1Q CSM표 부재(도입초 축약, census whitelist). parser raw-ready `inbox/parser/20260616T0420Z`. ⚠️마스터 rebuild은 raw 전체복원 세션에서 |
| ~~KR0004-MG-DART~~ | ~~예별손해(구 MG=엠지) DART 감사보고서~~ | ✅ **2026-06-16 완료** | KR0004는 비상장 → DART 정기보고서 0 = universe 부재(통째로 0이었음). 외부감사 감사보고서(F)는 존재 = DART entity '엠지손해보험'(corp `00962861`). **별도·FY2023~ 3건 적재**(owner 스코프; FY2022 IFRS4·연결 제외). `data/dart/FY{Y}_Q4/raw/KR0004_엠지손해보험_<rcept>/`(00760 별도). IFRS17 주석 확인(보험계약마진 36~59). `scripts/fetch_kr0004_mg_dart_audit.py`. parser/ifrs17 raw-ready `inbox/parser/20260616T0210Z` |
| ~~KR0004-MG-HISTORY~~ | ~~예별손해(구 MG) 과거 11분기 K-ICS 공시~~ | ✅ **2026-06-16 완료** | parser bounce(round3 K2): KR0004가 26.1Q만 적재, 그 이전=구 MG 명의. 2023.1Q~2025.3Q **11분기 전수 fetch(11/11 OK)** from `yebyeol.co.kr`(예별=구 MG 동일 법인, 2013~ 전 분기 아카이브). 결산 ZIP 본문="엠지손해보험" 확인. text-layer OK(OCR 불필요). `scripts/backfill_kr0004_mg_quarters.py`. KR0004=2023.1Q~2026.1Q 13분기 연속 확보. parser raw-ready `inbox/parser/20260616T0145Z` |
| ~~SEOULBO-DART~~ | ~~서울보증 DART 8셀~~ | ✅ **2026-06-01 drop (won't-fix)** | 사용자 결정("서울보증 걍 버려"). 미상장(IPO 철회) → DART 분기/반기/사업보고서 미공시 = 구조적. audit `DART_DROP`에 등록 → 전 source REAL GAPS 0 |
| ~~IR-DONGYANG-401~~ | 동양생명 IR factbook (myangel) 401 — disclosure로 부분 해결 | 🟢 low | **2026-05-30R: 사용자 지적으로 생보협회 경영공시(pub.insure.or.kr)로 대체 → disclosure 13/13 완성** (`download_dongyang_disclosure_q4.py`로 FY2023_Q4·FY2024_Q4 결산 2개 받아 채움). 동양생명 검증 데이터는 disclosure(IFRS17 주석 포함)로 확보됨. IR factbook(myangel) 자체는 여전히 401 차단 — **IR factbook 전용 지표(CSM배수 등)가 disclosure에 없어 별도로 필요할 때만** 재시도: (a) non-headless+다른IP로 raon ozvid auth header 캡처 (b) DART 본문 fallback. 현재는 low priority |

**전략적 시너지 (코리안리 리포트 인과 체인 재현):**
- F8 (설계사정착률) + F8 (채널별 불완전판매비율) + 37회차 해지율 (별도 source)
- = "GA 채널 → 해지율 → 손해율" 인과 체인을 공시 데이터만으로 재현
- → insurequant 프리미엄 기능 후보

---

## User decisions (downloader-scoped)

| # | Decision | Date |
|---|----------|------|
| D5 | API keys: repo root `.env` only (gitignored). `OPENDART_API_KEY` / `DATA_GO_KR_BOND_ISSUANCE_KEY` / `DATA_GO_KR_BOND_REDE_KEY`. Never commit/log key values | 2026-05-24 |
| D6 | Bond Call rule: issue + 5y for ALL bonds (Korean market convention; ignore "콜" keyword gate). Past 5y = assume `called` (de facto mandatory per thebell/흥국 cases) | 2026-05-24 |
| DL-FYR | **Next quarter onwards (2026.2Q+)**: find URLs / XPaths yourself. 2026.1Q only was user-provided. Reuse existing configs, swap only period-specific labels. Escalate to user only if site structure fully changed | 2026-05-30 |
| DL-NOATTACH | **Don't fetch DART attachments (별첨/감사보고서 zip).** Body XML has all IFRS17 disclosures. Verified 2026-05-30 (한화 647 / KB 259 / 농협생명 176 / 라이나 audit 55 / AIG audit 55 occurrences of `보험계약마진` in body) | 2026-05-30 |
| DL-NOTSKIP | KR0029 AIG + KR0150 SGI **K-ICS skip** (no PDF on their own sites), BUT **DART**에서는 받을 수 있는 만큼 받음 (AIG = "에이아이지손해보험" corp_code 00983606 / SGI = 2024.4Q 이후 분기보고서 시작) | 2026-05-30 |
| DL-DART-C-FY23 | bucket C 빈 dir 121건 분류: 110 = 비상장 11사 Q1-3 (DART 분기보고서 구조적 미제출, gap 아님) + 11 = 비상장 11사 **FY2023_Q4 감사보고서 = 받지 않음** (사용자 결정 2026-06-03, "비상장사 감사보고서 불필요" 유지). → 비상장사 DART PL/CSM 시계열 = **FY2024_Q4 + FY2025_Q4 2포인트로 확정** (extract_dart_zips로 추출 완료). 다음 세션 재제기 금지 | 2026-06-03 |

---

## Done — recent (one-liners; detail in changelog / data manifests)

| ID | Task | Done |
|----|------|------|
| SENS-FY25 | IFRS17 CSM 민감도 FY2025 사업/감사보고서 raw 28사 전수 적재 (FY2024 고정 해소) — DART 회사명검색, `data/dart/FY2025_Q4/raw/`, 28/28 공시·실패0, KR prefix 통일. 추출(sensitivity)은 parser/ifrs17로 라우팅(`inbox/parser/20260615T0520Z`) | 2026-06-15 |
| G8 | NB CSM배수 25.4Q 누락 3사 FY2025 감사보고서 raw 복원 (AIG/카카오페이손해/하나생명) — 라이브 DART 재취득 + `KR0029_` prefix 정정 + IFRS17 키워드 검증. 추출 교정(magnitude misparse + 하나생명 audit-annual)은 parser/ifrs17로 라우팅(`inbox/parser/20260614T1330Z`). 단순 refetch 아님 = 파서 추출 이슈로 확정 | 2026-06-14 |
| F2 | KIDI ML01/MN07 NB CSM crawler (38사×13Q=494, premium_summary.json) | 2026-05-30 |
| DL-FY26Q1 | FY2026.1Q full ingest (손보17+생보22+IR13+DART) | 2026-05-30 |
| DL-DART-AUDIT | DART raw 100% audit + gap fill (`_inventory_manifest.json`) | 2026-05-30 |
| MISC-BOND | FSC bond issuance+Call ingest → per-ISIN calendar (tier1 63 + tier2 261) | 2026-05-25 |
| IFRS-HIST | Historical 13Q ingest 2023.1Q~2026.1Q (`ifrs17_batch_historical.py`) | done |
| DL-COMPLETE | 5-source 완결: 전수 audit + disclosure 28셀 backfill (gap 73→34) | 2026-05-31 |
| DL-ARCHIVE-PROBES | Archived 45 early IR auto-discovery probes (`scripts/_probes/`) → `data/_archive/20260602T150745Z_downloader_ir_probes/` (git rename, kept for foreign-insurer ref). Canonical `crawl_ir_*.py` untouched | 2026-06-02 |
| DL-DART-EXTRACT | Fixed parser `raw_not_extracted`: 42 insurer DART dirs had `document.zip` but no body XML (fetch-only + foreign filings have only `_00760`/`_00761` members, no main xml). New idempotent `scripts/extract_dart_zips.py` extracted them in-place; bucket A 40→0. Parser auto-picks via `*.xml` glob | 2026-06-03 |

---

## Reading order for downloader subagent

When invoked, read in this order:

1. This file (`TODO_downloader.md`) — current state and documented exceptions
2. `docs/changelog_downloader.md` — history (what previous sessions did)
3. `docs/agents/claude-agent-downloader.md` — master prompt (mission + 5 sources catalog + canonical layout)
4. `docs/agents/source-catalog.yaml` — machine-readable URL/XPath catalog
5. `data/dart/_inventory_manifest.json` — DART coverage; avoid re-fetching
6. `data/disclosure/_meta/FY*/_manifest.json` — per-period manifests
7. `data/ir/_*.json` — IR manifests (`_db_manifest.json`, `_db_decks_manifest.json`, `_hyundai_manifest.json`, `_kr_map.json`)

For cross-stage context (other 4 stages), see root `TODO.md`.

---

NOTE: English only where Korean encoding is fragile. Korean content preserved here is read-only history; new entries prefer English. See `CLAUDE.md` "Document/TODO Encoding Rule".
