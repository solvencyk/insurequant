# Insurequant Changelog — Downloader Stage

> Last updated: 2026-06-14 · Stage 1/5 — downloader
> Prompt: docs/agents/claude-agent-downloader.md · TODO: TODO_downloader.md

**Scope:** data collection only — raw fetch from external sources (정기경영공시 / DART / FSC bonds / KIDI / IR factbooks).
**Cross-stage history:** `docs/claude-changelog.md` (parser/validation/gathering/pushing/refactor entries).
**This file:** entries scoped to downloader work only, extracted from the root changelog 2026-05-30.

Cross-stage entries that touch downloader as one phase but are primarily parser/gathering/viz (e.g. F11 foreign-affiliate viz integration, IR factsheet 전사 수집 + 손보 NB CSM 배수 파싱, F17 LOB parsing) remain in `docs/claude-changelog.md`. The compressed historical archive (pre-2026-05-25) also remains there.

## 2026-06-14 -- G8: NB CSM배수 25.4Q 누락 3사 — FY2025 감사보고서 raw 복원 (추출은 parser로 라우팅)

owner QA(G8, `inbox/downloader/20260614T0712Z`): index.html CSM배수가 AIG(KR0029)·카카오페이손해
(KR1098)·하나생명(KR0097)에서 2025.4Q 누락 → 24.4Q fallback. inbox 프레이밍은 "DART refetch 3건"이었으나
**진단 결과 단순 refetch 건이 아니었음.**

- **원인 분리**: NB CSM배수 분자(신계약 CSM)는 `CSM_waterfall.json` 항목2(=파서 마스터) → 다운로더 산출물
  아님. 3사 FY2025 감사보고서 raw가 working tree에서 사라져 있었음(추출 후 정리/purge 추정; data/dart raw는
  gitignored). 인벤토리 `_inventory_manifest.json`(raw_annual)이 rcept를 기록 중이라 라이브 DART 재취득 가능.
- **복원(downloader 액션)**: 라이브 `/api/list.json`(회사명 검색, 영구매핑 없음) → FY2025 감사/연결보고서
  rcept 확정 → `/api/document.xml` fetch + extract, canonical `data/dart/FY2025_Q4/raw/<KR>_<name>_<rcept>/`:
  - KR0029 AIG: `20260407002104`(별도) + `20260407002109`(연결). annual_raw_dir가 kics명 "AIG손해보험" ↔
    DART명 "에이아이지손해보험" 불일치로 corp_code prefix(`00983606_`)로 떨궈서 → **빌더 글롭 `KR0029_*`에
    걸리도록 `KR0029_` prefix로 리네임 정정.**
  - KR1098 카카오페이: `20260323001537`(별도). KR0097 하나생명: `20260325000201`(별도)+`000202`(연결).
  - 검증: 보험계약마진 26~55회/신계약 3~12회 (IFRS17 본문 OK).
- **추출 스모크(read-only, 마스터 미변경)로 진짜 원인 확정** → 파서 이슈:
  - AIG: 신계약CSM=986,825.6억(≈2000배 과대, 롤포워드는 닫힘) magnitude/table misparse. (과거 FY2024=443.8)
  - 카카오페이: 신계약CSM=20,187.6억(현 마스터 stale값과 동일 → 이전 빌드도 같은 표를 같은 방식으로 읽음).
    배수는 build_nb_csm_multiple `_MULT_CAP=40`이 정상 null 처리 중.
  - 하나생명: build-waterfall 경로 no blocks → AUDIT_REPORT_ANNUAL이라 `ifrs17_ingest_audit_annual.py`
    (extract_csm_tables) 경로 필요(2024.4Q=3240.3이 그 산물).
- **핸드오프**: parser/ifrs17 inbox에 route:reparse 작성
  (`inbox/parser/20260614T1330Z__downloader__MULTI_2025.4Q__nb_csm_fy2025_raw_ready.md`).
  파서가 magnitude 교정 + 하나생명 audit-annual ingest → CSM_waterfall 재빌드 → build_nb_csm_multiple 재실행.
- G8 원 스레드 → `_resolved/` 이동(status: resolved). downloader 잔여 액션 없음.
- **미결(별개)**: `20260614T1232Z` qa_residual item(2) — KB/한화손해 2023.4Q 금리위험·카카오 2025.4Q
  시장위험 스캔-only(텍스트레이어 없음) OCR. downloader OCR 경로 부재 → owner 결정 대기, 메시지 open 유지.

## 2026-06-09 -- AIA 식별자 마이그레이션: 리터럴 "AIA" → KR0080 (코드+데이터 코디네이션)

AIA생명(에이아이에이생명보험)은 kics_disclosure 로스터에 없는 audit-only 외국계라 일부 스크립트가 코드 대신 리터럴 `"AIA"`를 식별자로 써왔고 → `AIA_*` 파일/폴더가 KR####_ 컨벤션을 깨고 있었음. KR0080은 이미 registry/_dart_path_helpers/_kr_map 등에서 AIA 정본 코드라, 누락분을 KR0080으로 통일.

- **코드 4스팟**(식별자로 쓰던 곳만): `ingest_kidi_monthly_premium.py:71` 키, `crawl_assoc_nb_premium.py:66` 키, `report_collection_status.py:68/123/142` 로스터 → `"AIA"`→`"KR0080"`.
- **유지(건드리면 안 됨)**: `ifrs17_find_missing.py`(=DART corp-name 검색 쿼리), `extract_dart_zips.py` INSURER_PREFIXES(백워드-compat), `audit_all_periods.py` alias, `one_off_reorg2_canonical.py`(1회성).
- **데이터 17경로 리네임** `AIA_`→`KR0080_`: KIDI 13(`data/kidi/FY*/raw/AIA_<yyyymm>.json`) + DART raw 3폴더(FY2024_Q4·FY2025_Q4) + disclosure 1(FY2026_Q1). `_archive`는 제외.
- **파생 JSON 코드필드** `"AIA"`→`"KR0080"` (JSON-aware, 이름 보존): premium_summary 13 + kidi_life_premium 13 + nb_csm_multiple 1.
- **검증**: `report_collection_status.py` exit 0, AIA→KR0080 "전체자료 입수 완료"; `_archive` 외 AIA_ 잔여 0; 파생 JSON bare "AIA" 0. 네트워크 크롤 미실행.
- **주의**: 데이터만 리네임하면 ingest가 "AIA" 키로 읽어/써서 깨짐 → 코드+데이터 동시 변경이 필수였음.

## 2026-06-04 -- KIDI 신계약 월납초회보험료 FY2026_Q1(202603) 재수집

사용자 재확인 요청 → 라이브 KIDI INCOS 엔드포인트 probe 결과 **2026.1Q(202603)이 그새
발표됨** (5/31 fetch 시점엔 항목 라벨만 있고 ITEM_VAL 비어있던 게, 이제 값 채워짐).
3개 크롤러 풀 리빌드(전 기간, 202603 포함):
- `crawl_kidi_life_premium.py` → `kidi_life_premium.json`: 264 → **286 records** (생보 22사 × 202603 추가)
- `crawl_kidi_longterm_premium.py` → `kidi_longterm_premium.json`: 184 → **200 records** (손보장기 16사)
- `ingest_kidi_monthly_premium.py` → raw per-company + `premium_summary.json`: **507 entries** (39사×13), errors 0

검증(202603 월납초회 실측): 삼성생 739.63억 / 한화생 621.18억 / 교보생 390.7억 /
삼성화재 455.89억 / DB손 417.66억 / 메리츠손 348.33억 / 현대손 298.75억. 전부 1Q 누계로 정합.

`audit_all_periods.py`: `KIDI_NOT_RELEASED`에서 FY2026_Q1 제거(빈 set) — 이제 실제 체크해도
KIDI REAL GAPS **0**. → KIDI 13분기 전수 수집 완료(구조적 0: 코리안리(재보험)·서울보증(보증, 미매핑)).

## 2026-06-04 -- 한화생명(KR0068) 분기 IFRS17 본문/별첨 확인 (parser 질의)

파서가 한화생명 분기 Tier-1 NO 보고 ("분기/반기보고서가 요약재무정보만 노출, 보험손익 분해
IFRS17 표 미수록(포맷 상이)") → downloader에 본문 vs 별첨 확인 요청.

**확인 결과: 전부 본문(body XML)에 있음. 별첨 아님. 재다운로드 불필요.**
- 분기 dir 구조: 단일 main XML(`<rcept>.xml`), document.zip 멤버도 1개뿐 (연간과 달리
  `_00760`/`_00761` 별첨 없음). 즉 받을 추가 문서 자체가 없음.
- 본문 term-scan (FY2025_Q1 분기, 4.9MB/913 tables): 보험수익=80, 보험서비스비용=68,
  보험금융=86, 보험계약마진=117, 보험서비스=112, 포괄손익계산서=11회, 영업부문=7.
  반기(Q2)·연간은 더 풍부. → IFRS17 보험손익 분해 데이터는 본문에 물리적으로 존재.
- 파서가 "요약만"으로 본 이유: 본문 **헤드라인 포괄손익계산서가 레거시 요약 워터폴**
  (매출액/영업이익/법인세차감전순이익/당기순이익/기타포괄손익) 포맷이라 first-match가 이걸 잡음.
  실제 IFRS17 보험손익 분해는 본문 뒤쪽 상세표/주석에 있고, 표준 `<TABLE>/<TD>`가 아닌
  비표준 markup(`<TE>` wide-table 또는 서술형 추정)이라 추출이 어려운 것 → **파서측 매칭 이슈**,
  다운로드 갭 아님. (한화생명 1사 한정, 파서 세션이 보류 중인 항목과 일치.)

## 2026-06-03 -- DART document.zip 미추출 수정 (parser raw_not_extracted unblock)

파서 세션이 `status=raw_not_extracted`(document.zip만 있고 본문 XML 없음)을 보고.
원인 + 수정:

**원인 (2가지 결합):**
1. 해당 dir들은 fetch-only 단계에 남아 있었음 — `document.zip`는 받았으나 unzip(extractall)이
   실행 안 됨. (batch 스크립트의 추출 로직 자체는 정상 `extractall`; --skip-extract 실행분이거나
   Reorg #2가 미추출 dir을 그대로 옮긴 케이스로 추정.)
2. 비상장·외국계 보험사의 공시는 standalone 감사보고서라 zip 내부에 main `<rcept>.xml`이 없고
   `<rcept>_00760.xml`(연결)/`_00761.xml`(별도)만 들어있음 → main xml만 찾는 점검은 "빈 dir"로 오판.
   IFRS17 공시(보험계약마진/포괄손익/부문)는 이 _0076x 멤버 안에 그대로 존재.

**수정:** 신규 `scripts/extract_dart_zips.py` — idempotent. `data/dart/FY*_Q*/raw/*/document.zip`를
스캔, 본문 xml(`*.xml`/`xml/*.xml`/`extracted*/*.xml`)이 없는 dir만 in-place로 extractall (메리츠 등
정상 dir과 동일 레이아웃). 보험사 prefix(KR / AIA)만 대상; 지주(corp_code) dir은 제외(--include-all로 포함).
네트워크 재다운로드 없음 — 이미 받아둔 zip을 풀기만.

**결과:** 보험사 dir 42개 추출(46 xml members), idempotent 재실행 0건. parser 좌표 기준
bucket A(zip有/xml無) 40 → **0**. spot-check: AIG `_00760` 보험계약마진=55, AIA=49, 메트라이프=124.
기존 파서가 `*.xml` glob으로 자동 인식 → raw_not_extracted 해소 예상(파서 측 코드 변경 불필요).

**부수 발견 (별개 이슈, bucket C = 빈 dir/zip無 121건):** 110건은 비상장사 Q1-3 = DART 분기보고서
구조적 미제출(정상, gap 아님). 11건은 비상장 11사의 **FY2023_Q4 연간 감사보고서 미다운로드**(이들의
FY2024_Q4·FY2025_Q4는 위에서 추출 완료). 비상장 감사보고서 fetch 여부는 사용자 결정 사항(과거
"비상장사 감사보고서 불필요" 결정 ↔ parser의 PL/CSM 요청 충돌) → 사용자에게 질의.

## 2026-06-02 -- Housekeeping: archived early IR auto-discovery probes

Archived `scripts/_probes/` (45 files, ~2,600 lines) to
`data/_archive/20260602T150745Z_downloader_ir_probes/_probes/` (git rename, not
deleted; README in that dir maps each probe family to its canonical replacement).

These were exploratory DOM-inspection / URL-discovery scripts from the early
"find and download everything yourself" IR phase (iterative `_*_probe`,
`_*_probe2` ... `_hi_ir_probe11`). They learned each insurer's IR board / click /
download mechanism but never wrote into the data tree; the working recipes were
folded into the config-driven `scripts/crawl_ir_*.py` crawlers (kept). Verified
nothing imports `_probes` and no doc references it; `report_collection_status`
still imports clean after the move. Kept (not deleted) as reference for onboarding
foreign insurers later.

Not touched: `scripts/dl_lotte_ir.py` — a clean but superseded one-off (Lotte
only, replaced by `crawl_ir_lotte_koreanre.py`). Flagged for the user to decide;
left in place.

## 2026-06-01 -- NONLIFE-Q123 종료: 손보 6사 분기공시 26셀 backfill (자체사이트)

손보 6사 분기(Q1-Q3) 정기경영공시를 각 사 자체사이트에서 사별 병렬 에이전트로 수집. 34셀 중 **26셀 수집, 8셀(서울보증) 구조적 미발행** → disclosure 실질 gap **0**. 무결성 2,041/2,041 OK, audit disclosure REAL GAPS 0.

신규 스크립트(사별): `scripts/backfill_q123_{aig,axa,shinhanez,sgi,koreanre,kakaopay}.py`. 저장: `data/disclosure/FY{Y}_Q{N}/raw/KR####_<name>.pdf` (기존 네이밍 일치).

사별 결과·사이트 구조:
- **AIG손해(KR0029)** 9/9: 사이트 cadence = `1분기/상반기/3분기/결산` (**별도 2분기 없음** → 상반기 누적으로 Q2 채움). list page `dpwom012.html?curPage=N`에 제목 anchor 옆 직접 다운로드 href(`downLoadFiles.do?fileId=`) — detail page 불필요.
- **악사(KR0049)** 4/4 (FY2023 Q1·Q3, FY2025 Q1·Q3): 표가 **FY행 1개 + 분기별 td 셀** 구조 → 셀별 `N/4분기` 라벨로 매핑(naive "행첫 a"는 Q1만 잡힘). 전체(결산)셀은 ZIP.
- **신한EZ(KR0051)** 4/4 (FY2023 Q1-Q3, FY2024 Q1): 카디프→신한EZ 개명에도 FY2023 풀 보존(페이지네이션 목록). Q2 라벨 = "상반기".
- **서울보증(KR0150)** 0/8 = **구조적 미발행**: SPA(`CCGIRI010101F01_listTmpl`)가 **연간 경영공시 + 최신 1분기만** 노출(과거 분기 롤오프), DART 미상장 → 양쪽 모두 미수집 불가. audit에 `SGI_QUARTERLY_STRUCTURAL` 예외 등록.
- **코리안리(KR1000)** 6/6 (FY2024·FY2025 Q1-Q3): `ir_03_1.asp` 단일 표에 전 연도 행, 셀 href가 직접 PDF(`/pdf/gyungyoung/<year>_<q>.pdf`). 파일 stem `KR1000_코리안리.pdf` 사용.
- **카카오페이(KR1098)** 3/3 (FY2024 Q2, FY2025 Q2·Q3): 정적 SPA 표 직접 href. 정정/KICS포함본 우선(FY2024_Q2는 5.1MB KICS본). Q2=상반기.

**Parser 핸드오프**: AIG/신한EZ/카카오 FY{Y}_Q2 = 반기(상반기) 누적(1.1~6.30), standalone 분기 아님 — validation에서 누적-반기로 해석 필요. (TODO_downloader Status에도 기재.)

서울보증 DART 8셀(`SEOULBO-DART`): 사용자 결정("걍 버려")으로 **drop (won't-fix)**. 미상장(IPO 철회) → DART 미공시 = 구조적. audit `DART_DROP` 등록 → **전 source REAL GAPS 0** 달성.

## Archive (pre-2026-06) — 2026-05-25 → 2026-05-31 (FY2026.1Q 수집 + Reorg)

> 1줄 요약. 전문은 git log/blame. 회사별 URL/XPath 정본은 source-catalog.yaml.

- 2026-05-31 (O~S) -- 데이터 수집 완결: 전수 audit + disclosure 28셀 backfill
- 2026-05-30 (N) -- DART batch script canonical-path refactor
- 2026-05-30 (M) -- File-integrity 검사기 + 현대해상 IR 재다운로드
- 2026-05-30 (L) -- Collection-Status Report step + 양식 추가
- 2026-05-30 (j) -- Reorg #2: DART/KIDI/assoc 마저 정리 (canonical 일관 적용)
- 2026-05-30 (i) -- Downloader workflow 정리 완료 (5 source audit + canonical reorg + master prompt)
- 2026-05-30 (h) -- DART raw 100% audit + gap fill (KPI "전부 다 성실하게" 달성)
- 2026-05-30 (g) -- DART 별첨 fetch 진단 철회 (본문에 다 있음, 회사별 라벨 변형 처리 필요)
- 2026-05-30 (f) -- FY2026.1Q 생보 22사 경영공시 일괄 다운로드 완료 (세션 file ingest A-Z 마무리)
- 2026-05-30 (e) -- FY2026.1Q IR 자료 13 source 다운로드 완료 + 한화손보 IR mis-classified 정리
- 2026-05-30 (d) -- FY2026.1Q 손보 17사 경영공시 PDF 다운로드 완료
- 2026-05-30 (c) -- F2 v3 KIDI ML01/MN07 crawler DONE — NB CSM 분모 6→328 entries, computed multiple 6→27/28
- 2026-05-25 -- IFRS17 historical 13Q ingest + CSM 시계열 panel (push #2)
- 2026-05-25 -- Bond tier `(신종)` fix + FSC bond normalize refresh

---

## Compressed historical archive (pre-2026-05-25)

The compressed one-liner archive in root `docs/claude-changelog.md` ("## Historical archive (compressed)") contains a few downloader-relevant lines, kept inline there for compactness:

- FSC bond ingest client `src/bonds/` + `scripts/ingest_fsc_bonds.py` (MISC-BOND-INGEST)
- FSC schedule API per-insurer full pull: 1720 rows / 19 insurers
- Bond calendar v3: 5y Call rule for ALL bonds, 3-status outstanding/called/matured
- FSC schedule API 15059611 [승인] confirmed

These remain in the root changelog rather than being re-extracted, since they're already condensed.
