# Insurequant Changelog — Downloader Stage

Stage 1 of 5 in the workflow split. See `CLAUDE.md` for the full 5-stage index.

**Scope:** data collection only — raw fetch from external sources (정기경영공시 / DART / FSC bonds / KIDI / IR factbooks).
**Cross-stage history:** `docs/claude-changelog.md` (parser/validation/gathering/pushing/refactor entries).
**This file:** entries scoped to downloader work only, extracted from the root changelog 2026-05-30.

Cross-stage entries that touch downloader as one phase but are primarily parser/gathering/viz (e.g. F11 foreign-affiliate viz integration, IR factsheet 전사 수집 + 손보 NB CSM 배수 파싱, F17 LOB parsing) remain in `docs/claude-changelog.md`. The compressed historical archive (pre-2026-05-25) also remains there.

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

## 2026-05-31 (O~S) -- 데이터 수집 완결: 전수 audit + disclosure 28셀 backfill

세션 arc: "데이터 수집 다 끝났나?" 검증 → gap 발견 → 외부제약 우회 → backfill. 최종 **무결성 1,994/1,994 OK**, disclosure 73→34 gap (잔여 34 = 손보 6사 분기, TODO `NONLIFE-Q123`).

신규 스크립트: `audit_all_periods.py`(13기간×39사×5source 전수, structural vs real-gap 분류), `backfill_life_disclosure_gaps.py`(pub.insure.or.kr 생보), `backfill_nonlife_disclosure_kpub.py`(kpub 손보), `download_dongyang_disclosure_q4.py`.

핵심 사실/결정:
- **KIDI N04 = MG/예별** (cbCmp 라벨 "MG" 유지). MAPPING에 `KR0004` 추가, 13분기 fetch (일부 분기 분모0 = 장기손보 미보고, 구조적).
- **생보 통합공시 pub.insure.or.kr**: 표 = [회사명,1분기,2분기,3분기,결산], `?search_stdYear=YYYY`. 분기·결산 모두 제공. → 동양 결산 2셀 + 삼성/교보/DB생명/흥국/ABL 7셀 + IBK연금 11셀 + AIA 2셀 = 22셀 backfill.
- **손보 통합공시 kpub.knia.or.kr**: 컬럼 = **연도(2025~2021), 연간 결산만** (분기 없음). 다운로드는 ZIP(본문+감사보고서) → 본문 PDF만 추출(감사/별첨/재무제표/Reporting/지급여력 제외). → 손보 결산 8셀(KB손보·농협·AIG·악사·신한EZ·서울보증).
- **audit false-negative 정정**: AIA(코드 `AIA` vs 파일 `KR0080`)·MG(`KR0004_MG` vs `KR0004_예별`) → `FILE_PREFIX_ALIAS`. KIDI 카카오/코리안리=구조적 zero, FY2026_Q1=미발표. DART는 사용자 "비상장 감사보고서 불필요" → NONLISTED 구조적 제외, 실질 gap=서울보증만.
- **동양 IR(myangel) 401 차단**: downloadFile 엔드포인트 anti-bot 차단(보유 FY2026_Q1조차 401). IR factbook 자체는 미해결이나 생보 disclosure로 검증데이터 확보. crawler `raw/` 경로버그 fix.
- **삼성생명 IR FY23 Q1-Q3**: samsunglife.com ~2년치만 보존(롤오프). 단 데이터는 `4QFY23FactsheetKOR.xlsx`의 분기 컬럼에 내장 → parser stage 구판 레이아웃 핸들링으로 복구 가능.
- **integrity 검사기**: Excel 임시락(`~$*.xlsx`) read 실패 → `~$` prefix 스킵 추가.

잔여 (다음 세션): 손보 6사 분기 Q1-Q3 34셀(회사 자체사이트, 일부 구조적) · 서울보증 DART 8셀(IPO 시점). 상세 TODO `NONLIFE-Q123`/`SEOULBO-DART`.

## 2026-05-30 (N) -- DART batch script canonical-path refactor

Reorg #2 layout(`data/dart/FY<y>_Q<q>/raw/<KR>_<name>[_<rcept>]/`)로 옮겼지만 다운로더 3 script가 OLD path로 write하던 것 → 다음 분기 fetch 시 layout 깨짐. 신규 헬퍼 `scripts/_dart_path_helpers.py`로 통일:
- `kr_for_kics_name()`(kics 원수사명→KR, +`_KICS_NAME_OVERRIDES` AUDIT_REPORT_ANNUAL 5사+한화생명), `period_label_to_dir`, `annual_period_dir_for_rcept`(rcept 앞4자리=filing year→FY{y-1}_Q4), `quarterly_raw_dir`/`annual_raw_dir`.
- Leaf = DART `corp_name` 사용(Reorg #2 명명과 일치). Prefix 우선순위: `kr_code` > kics 룩업 > `corp_code`(group holding 폴백).
- 갱신: `ifrs17_batch_all.py`·`ifrs17_batch_historical.py`(annual은 rcept-dependent라 fetch를 out_dir 결정 전 호출, quarterly는 meta 캐시)·`ifrs17_ingest_audit_annual.py`. path 결정만 변경, extract/parse 무변경.
- `_dart_path_helpers_smoke.py` 9/9 케이스 통과(메리츠/삼성생명/IBK/KB라이프/코리안리/AIA + quarterly + group fallback).
- 미터치: `settings.extracted_dir`/`extracted_history`(parser stage 영역), xml/ 추출 컨벤션.

## 2026-05-30 (M) -- File-integrity 검사기 + 현대해상 IR 재다운로드

User: 현대해상 2025.4Q IR 엑셀이 안 열림 → 깨진 파일 전수 조사 요청. `scripts/check_data_file_integrity.py` 신규(4 source magic-byte + container: xlsx zip/xls OLE/pdf %%EOF+startxref/zip testzip). 초기 broken=8 → PDF tail padding 6건 false positive(검사 윈도우 `body[-16384:]`+startxref로 완화). 진짜 broken 2건:
- 현대해상 FY2025_Q4 Factsheet xlsx (magic `43723234` 불명) → hi.co.kr 재다운로드 OK(`redownload_hyundai_ir_2025q4.py`), 원본 `.bad` 백업.
- 흥국 FY2023_Q1 amended PDF = Fasoo DRM("DRMONE") → 재다운로드 불가, **사용자가 직접 교체**(정상 %PDF-1.4). 최종 1,965/1,965 OK.

## 2026-05-30 (L) -- Collection-Status Report step + 양식 추가

User: "데이터 수집 다하고 나면 수집 결과를 나한테 아래 양식으로 '이 세션의 채팅에서' 보고하는 것까지 프로세스에 박아놓자". `구분/사코드/사명/정기경영공시/자본성증권 발행/DART 공시/보험개발원 통계/IR공시/비고` 9-column 표 + 39사 universe + 비고 conventions 정의.

**Files**:
- `scripts/report_collection_status.py` (신규, 250 line) — universe 39사 자동 enumerate, 5 source checker (disclosure / bonds / dart / kidi / ir), 비고 phrasing helper, "전체자료 입수 완료" criterion (acceptable X = structural / honest source gap).
- `docs/collection-status-FY2026_Q1.md` (생성) — FY2026.1Q 첫 보고.
- `docs/agents/claude-agent-downloader.md` Step 7 추가 (mandatory chat-side reporting + 양식 + 비고 convention table + universe list + bottom summary spec).

**Universe lock (39사)**:
- 손보 17: KR0001~KR1098 + KR0004_MG (MG손해=구 예별, KIDI N04). KR1059 캐롯 → 한화손보 합병으로 영구 제외.
- 생보 22: KR0068~KR1011 + AIA(non-KR).

**DART 분기보고서 cohort 확정**: spot check (FY2025_Q1 raw)에서 actual document.zip 보유 = 24사 (이전 가정 23 → 24 정정. 서울보증 KR0150 포함). 나머지 15사 (NON_LISTED 8 + audit-only 5 + AIG + MG)는 분기보고서 미공시 = 구조적 X (수용 가능). DART_LISTED_SET / DART_NONLISTED 두 set으로 분류.

**비고 conventions**:
- 전체완료: "전체자료 입수 완료" (모든 X가 acceptable)
- 자본성증권 X: "<period> 중 별도 자본성증권 발행 내역 없음" (예: 1Q 발행 없음) / "자본성증권 미발행 회사" (FSC 등록 자체 없음)
- DART X: "DART 정기보고서 미공시 (비상장/외국계, 감사보고서만)" (구조적) / "DART 다운로드 실패 (재시도 필요)" (actionable) / "DART 미상장 회사"
- KIDI X: "KIDI <period> 데이터 미공시 (대기 중)" (latest 분기 미공시) / "KIDI 구조적 N/A (재보험·자동차전문)" / "KIDI 미커버 회사" (MAPPING 누락, actionable)
- IR X: "IR 공시자료 미제공사" (구조적) / "그룹 IR(KR#### <그룹사명>)에 합산" (O row의 positive note)

**FY2026_Q1 보고 결과**:
- 총 39사, 전체자료 입수 완료 **37사 (95%)**.
- Source별: 정기경영공시 39/39 / 자본성증권 발행 2/39 (흥국화재 1.0천억 + DB손해 4.4천억 신규발행) / DART 24/39 / 보험개발원 0/39 (FY2026.1Q=202603 KIDI 미공시) / IR 17/39 (그룹IR 4사 합산 포함).
- Actionable gap **2건**:
  - KR0004_MG: KIDI cbCmp 매핑 누락 (`scripts/ingest_kidi_monthly_premium.py` MAPPING에 N04 추가 필요)
  - KR0150 서울보증: KIDI 미커버 회사 + IR 미제공사 + 자본성증권 미발행 (대부분 구조적이라 새 mapping만 추가하면 acceptable)

**다음 세션 우선순위**:
1. DART batch scripts refactor (canonical path write)
2. Parser subagent prompt 작성 (`docs/agents/claude-agent-parser.md` skeleton 채우기)

---

## 2026-05-30 (j) -- Reorg #2: DART/KIDI/assoc 마저 정리 (canonical 일관 적용)

사용자 push back: "폴더정리 제대로 한거 맞아? IR 폴더는 분기별>회사별 정리돼 있는데, DART랑 KIDI 폴더는 정리가 하나도 안돼있어. assoc 폴더는 대체 정체가 뭐야?". Reorg #1(workflow phase 2)이 DART/KIDI는 "자체 컨벤션이라 그대로" 라고 판단한 게 잘못. 일관된 멘탈모델 = 모든 source가 `<source>/<period>/raw/KR####_<name>`.

**Script** `scripts/one_off_reorg2_canonical.py` (DRY_RUN 검증 후 실행):

**Step 1**: `data/assoc/` → `data/_derived/` rename. assoc 안에는 derived/computed/manual override 파일들 (`nb_premium_wolnap.json`, `nb_csm_multiple.json`, `nb_csm_validation.json`, `ir_wolnap_benchmarks.json`, `nb_premium_overrides.yaml`, legacy `kidi_life_premium.json`+`kidi_longterm_premium.json`)로 raw data 아님. 이름 misleading.

**Step 2**: KIDI `data/kidi/raw/<batch_stamp>/<KR>_<YYYYMM>.json` (494 files mixed) → `data/kidi/FY<year>_Q<q>/raw/<KR>_<YYYYMM>.json`. yyyymm 마지막 두자리 03/06/09/12 → Q1/Q2/Q3/Q4. **38사 × 13Q = 494 file 분기별 균등 분배** (각 period 38).

**Step 3**: DART raw_history `<name>/<2025.4Q>/document.zip` → `data/dart/FY2025_Q4/raw/KR####_<name>/document.zip`. 회사>분기 → 분기>회사 reverse + KR 코드 prefix.

**Step 4**: DART raw `<name>_<rcept>/` (77 annual rcepts) → `data/dart/FY<rcept_year-1>_Q4/raw/KR####_<name>[__cons]_<rcept>/`. rcept_no YYYYMMDDxxxxxx 앞 4자리가 filing year, FY = filing_year-1. consolidated suffix는 `__cons`로 보존.

**Step 5 (dedup)**: 같은 period 내 `KR####_<name>` (raw_history 출신, zip만) vs `KR####_<name>_<rcept>` (raw annual 출신, zip+unpacked XML) 중복 발견. 55개 simple dir → `data/_archive/20260530T120000Z_reorg2/dart_dups/` archive. rcept-suffixed 버전이 superset이라 keep.

**Script path constant 갱신** (`data/assoc` → `data/_derived`): 8 file (`build_nb_csm_multiple.py`, `crawl_assoc_nb_premium.py`, `crawl_kidi_life_premium.py`, `crawl_kidi_longterm_premium.py`, `extract_ir_wolnap_benchmarks.py`, `run_ifrs17_csm_reconcile_loop.py`, `validate_nb_csm_multiple.py`, `viz_build_csm_bubble.py`) 총 24 line.

**KIDI ingest 신규 fetch도 canonical로**: `ingest_kidi_monthly_premium.py`의 raw write path를 `OUT_DIR / "raw" / stamp` → `period_dir_for(ym)` (FY<year>_Q<q>/raw)로 refactor. 신규 분기 다운로드도 즉시 분기별 위치에 저장.

**`templates/data/assoc/` archive**: 2026-05-28 "HTML single-source refactor" 이후 stale duplicates (`nb_csm_validation.json`+`nb_premium_wolnap.json`) → `data/_archive/.../templates_data_assoc/`로 archive.

**docs/agents/* 갱신**: `claude-agent-downloader.md` + `source-catalog.yaml`에서 `data/dart/raw`/`raw_history`/`data/kidi/raw/<stamp>` 경로 표기를 새 canonical로 7+4 line 변경.

**최종 layout 확인**:
```
data/
├── disclosure/FY####_Q#/raw/KR####_<name>.<ext>
├── ir/FY####_Q#/raw/KR####_<name>/<filename>
├── dart/FY####_Q#/raw/KR####_<name>[__cons]_<rcept>/document.zip + xml
├── kidi/FY####_Q#/raw/KR####_<YYYYMM>.json (+ premium_summary.json)
├── bonds/  (snapshot-based, 자체 컨벤션 유지)
├── _derived/  (former assoc/, derived/computed/override 파일들)
└── _archive/<UTC-stamp>/ (recoverable)
```

DART FY2024_Q4=41/FY2025_Q4=44 (사업+감사+연결 audit 합산). FY2022_Q4=2 (AIG 4년 cohort 시작). KIDI 각 period 38 균등.

**남은 후속 작업 (다음 세션)** — `TODO_downloader.md` REORG2-DART:
- DART batch scripts (`ifrs17_batch_historical.py`, `ifrs17_batch_all.py`, `ifrs17_ingest_audit_annual.py`)가 아직 OLD path로 write. 신규 분기 fetch 시 canonical에서 벗어남.
- `src/assoc/nb_premium_common.py` Python 모듈 이름은 그대로 (모듈명 vs 폴더명 별개).
- `data/bonds/` snapshot 컨벤션은 source 특성상 분기 라벨이 부자연스러움 (issue+5y mortality 등 cumulative ledger). 유지.

---

## 2026-05-30 (i) -- Downloader workflow 정리 완료 (5 source audit + canonical reorg + master prompt)

User: "이 세션에서 나눈 대화는 나중에도 다시 써먹도록, workflow를 확실하게 정리해놔. Downloader subagent한테 시킬 프롬프트 md 형태, 디테일 빼먹지 말고. 완료되면 다음 parser subagent한테 작업 넘길거야." + 폴더 정리 + obsolete 아카이브.

**Workflow `wf_f8b5a806-a78`** (3 phases, 7 agents, 427k subagent tokens, 16.7분):

**Phase 1 — Audit (5 parallel `Explore` agents)**: data/disclosure / data/ir / data/dart / data/kidi+bonds / 기타 data/ subdirs. 비파괴 read-only inventory, 각 path의 purpose(raw/parsed/manifest/extracted/viz/meta/archive_candidate/obsolete/other) + recommendation(keep/move/archive/delete) + target_path 분류. 5/5 통과.

**Phase 2 — Reorg (1 agent)**: inventory 결과 기반 canonical layout 적용.
- `data/disclosure/FY{2023..2026}_Q*/pdf/` → `raw/` 리네임 (13 periods)
- `data/ir/FY*/KR####_<name>/` → `data/ir/FY*/raw/KR####_<name>/` (group IR은 parent KR로)
- 15 obsolete tree → `data/_archive/20260530T120000Z/<original-relative-path>` (recoverable, 445MB)
- `_reorg.log` 168-line from-to 기록
- **159 moves / 0 errors / 0 skip**. manifests(_meta/_inventory_manifest.json/nb_premium_wolnap.json 등) 전부 보존.

**Phase 3 — Document (1 agent)**: 두 파일 작성:
- `docs/agents/claude-agent-downloader.md` (21,721 bytes UTF-8 no BOM) — 미래 세션이 임의 분기 다운로드 재실행 가능한 self-contained master prompt. Mission / Reading order / 5 source full catalog (URL+XPath+mode+notes per insurer) / Canonical folder layout / Workflow for new quarter / Validation rules / Self-heal / What NOT to do / DART core 4 metrics / Future sources F7-F14 / Parser hand-off.
- `docs/agents/source-catalog.yaml` (17,312 bytes UTF-8) — machine-readable companion. 6 sources structured (disclosure_nonlife 17 entries, disclosure_life_bulk row_index map, bonds 4 API IDs, dart scripts+universe, kidi endpoint+column map, ir 13 entries with group `covers`).

**검증**:
- `data/disclosure/FY2026_Q1/raw/` 39 PDF (17 손보 + 22 생보)
- `data/ir/FY2026_Q1/raw/` 16 dirs (13 IR + 일부 manifest 부산물)
- `data/_archive/20260530T120000Z/` archive root + _reorg.log 정상
- YAML parses cleanly via `yaml.safe_load`

**기술 finding**:
- Workflow 첫 launch는 33분간 stall (3 agent started 후 silent halt) → TaskStop으로 중단 후 `resumeFromRunId` 옵션으로 재기동, 캐시된 phase 결과 즉시 통과 + 진짜 새로 돌릴 부분만 실행. 안전한 재실행 패턴 확인.
- Workflow validator 'Date.now/Math.random/new Date' 정적 검사가 prompt string 내 'Date.now is not available' 문자열까지 reject → 회피 (하드코딩 stamp string 사용).

**Next session 핸드오프**:
- Parser subagent 작업 시작 (사용자 명시)
- `docs/agents/claude-agent-parser.md` 작성 필요 (이번 session 미완성, downloader prompt와 sibling)
- 우선 작업: F17 Tier2 LOB 파서 라벨 변형 매트릭스 (현대 vs KB 보험료배분접근법 vs 삼성화재 보장성/물보험/저축성), NON_LISTED 8사 + AIG audit ingest

---

## 2026-05-30 (h) -- DART raw 100% audit + gap fill (KPI "전부 다 성실하게" 달성)

User 의심 정확함: "연결재무제표 주석 제대로 안 다운받아뒀을거같은데?". 정직한 audit 후 5건 진짜 누락 + 8 NON_LISTED 감사보고서 미수신 발견.

**누락 진단 (LISTED 23사 × 13Q = 299 expected)**:
1. 메리츠화재 2025.4Q: `data/dart/raw/` 에 있었으나 `raw_history/` 동기화 누락 → 복사
2. 삼성화재 2025.4Q: 위와 동일 → 복사
3. 동양생명 2023.3Q: 진짜 누락 → `ifrs17_batch_historical.py` 로 받음 ✓
4. 농협생명 2023.4Q: `batch_historical`이 status=014 (정정 rcept 잘못 picking) → 직접 list.json 검색 후 진짜 rcept (20240401002122) fetch ✓
5. 에이비엘 2025.4Q: 위와 동일 (20260331003080) ✓

→ **LISTED 23 × 13Q = 299/299 (100%)** raw 보유

**NON_LISTED 8사 + AIG + audit-only FY2025 추가** (KPI "전부 다"):
- IBK연금보험 / 교보라이프플래닛 / BNP파리바카디프 / 신한이지손해 / 아이엠라이프 / 악사손해 / 카카오페이손해 / 하나손해 — **각사 FY2024 + FY2025 감사보고서 (개별 + 일부 연결)** 받음
- AIG손해보험 (corp_code 미발견 → "에이아이지손해보험"으로 재검색해 00983606 발견) — **FY2022 + FY2023 + FY2024 + FY2025 × (개별/연결) = 8 rcept** 받음
- audit-only 5사 (라이나/메트라이프/AIA/하나생명/처브) — **FY2025 audit (개별/연결)** 추가 9 rcept
- 서울보증보험 — 2023~2024.3Q는 미공시(상장 전), 2024.4Q부터 분기보고서 시작, 4 분기 받음 (중복 정리)

**최종 인벤토리** (`data/dart/_inventory_manifest.json` 신규):
- `data/dart/raw/` annual rcepts: **76**
- `data/dart/raw_history/` period zips: **303**
- 총 380 raw rcept zip 보유

**본문 IFRS17 주석 키워드 sanity check** (사용자의 핵심 의심 해소):

| 회사/기간 | 보험계약마진 | 신계약 | 보험료배분접근법 | 보험손익 |
|---|---|---|---|---|
| 한화생명 2025.4Q | 647 | 38 | 272 | 15 |
| KB손해 2025.4Q | 259 | 64 | 124 | 17 |
| 농협생명 2023.4Q | 176 | 6 | 56 | 48 |
| 라이나 FY2025 audit | 55 | 7 | 1 | 2 |
| AIG FY2025 audit | 55 | 3 | 19 | 2 |

→ 모든 본문에 IFRS17 연결재무제표 주석 풍부. 별첨 fetch 불필요라는 결론 재확인.

**기술적 발견**:
- `scripts/ifrs17_batch_historical.py` 가 `list_filings` 결과의 첫 rcept_no를 그대로 사용하는데, DART는 정정([기재정정], [첨부정정]) 공시가 원본보다 먼저 나올 수 있음 → 잘못된 rcept picking → status=014 'file not found' 에러. **고침 방향**: 정정 prefix 제외하고 가장 늦은 rcept (또는 원본 사업보고서)를 picking 해야. (다음 세션 fix → `TODO_downloader.md` BATCH-HISTORICAL-FIX)
- `list_filings`는 `list[dict]` 직접 반환 (이전 audit script가 `.get("list")` 시도해서 오류).
- 외국계/non-K-ICS 회사 corp_code: 한글 통상 이름이 아닌 정식 한글 표기 사용 ("AIG손해보험" → "에이아이지손해보험").

**남은 honest gap** (DART에 진짜 없는 것):
- 서울보증 2023.1Q ~ 2024.3Q (당시 정기공시 미공시)
- audit-only 5사 분기/반기 (의도된 gap, 감사보고서만)
- NON_LISTED 8사 분기/반기 (의도된 gap)

---

## 2026-05-30 (g) -- DART 별첨 fetch 진단 철회 (본문에 다 있음, 회사별 라벨 변형 처리 필요)

> Cross-stage entry — downloader diagnostic part kept here; parser follow-up (LOB label variations) tracked in root `TODO.md` F17.

사용자 정정: 별첨 감사보고서 다운로드 시도 잘못됨. KB손보 FY2025 사업보고서 본문(`data/dart/raw/KB손해보험_20260313001064/20260313001064.xml` 5.6MB) grep 결과:
- "보험료배분접근법을 적용하지 않" 20회 / "...적용하는" 6회
- "보험손익의 상세내역" 2회
- "보험계약마진" 131회 / "신계약" 34회
- "장기보험" 29 / "자동차보험" 27 / "일반보험" 18

내가 F17 changelog에 "main XML 2~6MB thin, '계약의 유형'=0" 적은 진단 **잘못**. 본문에 모든 IFRS17 주석(CSM 변동, 신계약 CSM, 보험손익 LOB 분해) 풍부하게 있음. `_iter_tables_with_context`가 헤더 "계약의 유형"만 식별 시그니처로 써서 다른 라벨을 찾지 못한 게 진짜 원인.

**XBRL DART API (`fnlttSinglAcntAll.json`) 평가** — 사용자: "주석에 있는데 그건 xbrl 파싱이 잘 표준화돼있지 않아". Tier1 P&L 정도만 가능. IFRS17 깊은 주석(CSM/sensitivity/LOB)은 XBRL 태깅 없음 → HTML 표 파싱 유지.

**메모리 [[feedback-dart-no-attachment-fetch]] 저장**: DART 본문에 다 있음, 별첨 fetch 시도 금지, 회사별 헤더/컬럼 변형 처리로 해결.

---

## 2026-05-30 (f) -- FY2026.1Q 생보 22사 경영공시 일괄 다운로드 완료 (세션 file ingest A-Z 마무리)

User: 생보 일괄 다운로드 + DART 관련 가이드 필요사항 명시 요청.

**Script** `scripts/download_disclosure_2026q1_life.py` — 사용자 제공 URL+XPath (`https://pub.insure.or.kr/mngtDis/mngtDis/list.do` + `//*[@id="scroll_cont"]/table/tbody/tr[23]/td[2]/a`)로 일괄 zip(22.4MB) 다운로드. Playwright `expect_download` 사용, 매직바이트 검증.

**Zip 압축해제 + 분류** — `정기공시_2026년 1분기_첨부파일.zip` 22 PDFs → KR####_<name>.pdf로 표준 위치 저장. 21건은 파일명에서 회사 식별, 1건(`2026년 1분기 정기경영공시.pdf` 250KB)은 pdfminer로 첫 페이지 추출해 **신한라이프생명보험 (KR0094)** 확인.

**생보 22사 분류 결과**: 22 PDFs, total 29.0MB (자세한 회사·바이트 매핑은 root `docs/claude-changelog.md` 동일 entry 참조).

**세션 누적 file ingest (FY2026.1Q + KIDI 시계열)**:
- KIDI 38사×13Q = 494 fetch (premium denominator)
- 손보 경영공시 17사 (22.5MB)
- 생보 경영공시 22사 (29.0MB)
- IR 13 source 17 file (20.8MB)
- 한화손보 IR mis-classified 12분기 + decks/hanwha_gi/ 삭제

**남은 다운로드 작업 (DART)** — 후속 결정:
1. 별첨(attachment) API endpoint — 본문에 다 있으므로 fetch 불필요로 결정 (2026-05-30g)
2. XBRL fnlttSinglAcntAll.json — Tier1 P&L만 가능, 깊은 주석 미태깅
3. 외국계 5사 ingest — pblntf_ty=F (감사보고서) 외 source 없음

---

## 2026-05-30 (e) -- FY2026.1Q IR 자료 13 source 다운로드 완료 + 한화손보 IR mis-classified 정리

User: 손보 12사 + 생보 4사 IR factsheet/factbook URL+XPath 제공. 그룹 IR 3개(KB금융/신한금융/농협금융)는 멀티 KR 커버. 사용자 추가 정보: 하나금융지주(CSM 배수 없음 skip), DB금융네트워크(별도 없음, DB생명은 DB손보 IR에 포함 가능성), 교보생명(IR 없음), **한화손해보험 IR 폴더는 경영공시 mis-classified 였음 — 삭제 지시**.

**Script** `scripts/download_ir_2026q1.py` — disclosure downloader 패턴 재활용 + 신규 모드:
- `onclick_url`: `<a onclick="fileDownload('/path/to/file.xlsx')">` 패턴 — onclick 정규식으로 path 추출 후 `page.request.get()`
- 매직바이트 확장자 자동탐지: OLE compound는 IR 맥락 default `.xls` (롯데), `PK\\x03\\x04 + xl/workbook.xml` = `.xlsx`, `+ ppt/presentation.xml` = `.pptx` 등.
- `suggested_filename` 우선 (xlsx 파일 다운로드 시 원본 이름 보존 — `MFG_202603(k).xlsx` / `(KOR) SFMI 26.1Q_f.xlsx` 등).

**한화손보 IR 정리** — `data/ir/FY{2023..2026}_Q*/KR0002_한화손해보험/` (12분기) + `data/ir/decks/hanwha_gi/` (10 분기 PDF 별칭) 모두 삭제. 파일명이 `FY2026-1_4.pdf` 등 경영공시 패턴 정확 일치. `_kr_map.json`의 KR0002 엔트리도 prune.

**1차 batch 11/13 → 보정 후 13/13** 100% 성공 (회사별 다운로드 결과는 root changelog 참조).

**보정 사례 (1차 → 보정 후)**:
- 미래에셋생명: `<a onclick="fileDownload(...)">` no href → direct_href → click_dl 전환
- 롯데손보: OLE compound 파일 `.xls`로 확장자 매직바이트 보정 (.ole → .xls IR-default)
- 현대해상: 사용자가 삼성화재와 동일 XPath 잘못 제공 → onclick_url 시도 (path /data/... 추출했으나 404, server측 fileDownload는 별도 endpoint 사용 추정) → 사용자가 정정 XPath 제공 → click_dl 성공

**사용자 명시 결정**: "이번에 2026.1Q만 내가 URL이랑 xpath 다 구해준거다. 2026.2Q부턴 너가 직접 찾아." → 메모리 `feedback_find_urls_yourself.md` 저장. 다음 분기부터는 기존 config 재활용하되 신규 분기 라벨만 swap, 사이트 구조가 완전 변경된 경우만 사용자 도움 요청.

---

## 2026-05-30 (d) -- FY2026.1Q 손보 17사 경영공시 PDF 다운로드 완료

User: 손보사별 정기경영공시 URL+XPath 16개 + MG손보(예별) URL 제공. 캐롯 합병으로 skip. 사용자 지시 "재무제표 별도/연결/감사보고서는 거들떠보지 마" 준수.

**Script** `scripts/download_disclosure_2026q1_nonlife.py` — Playwright 기반 per-insurer config-driven downloader. 4 modes:
- `direct_href`: XPath → `<a href>` → requests.get + page cookies
- `click_dl`: XPath → button/img/JS-onclick → Playwright `expect_download`
- `two_step`: navigate URL → click step1 → (optional `js_eval_first`로 SPA in-page route 트리거) → step2 download
- `two_step_direct_url`: URL1 → URL2 direct → step2

추가 옵션: `wait_selector`, `wait_networkidle`, `wait_ms` per-site, `fallback_xpaths`. 매직바이트(`%PDF`/`PK\\x03\\x04`/`\\xd0\\xcf\\x11\\xe0`)로 확장자 자동탐지 → 잘못된 `.pdf` 확장자 자동 `.zip`/`.hwp`로 보정.

**진단 인프라**: 실패 시 `data/disclosure/_meta/FY2026_Q1/<KR>_failure.png` + `<KR>_failure.html` 자동 저장. 1차 batch 11/17 → HTML dump 분석 후 사이트별 보정:
- 메리츠: AngularJS, ng-scope 렌더 대기 + `<a class="btn_file i_pdf">` 명시
- 한화손보: devtools 막힘이었지만 HTML에 직접 PDF href 발견 → direct_href로 단순화
- 롯데: 사용자 의도(2-step) 정확 — list `<a title>` 클릭 → detail `<a href="javascript:downLoadFile(...)">` click_dl
- 현대해상: `serviceAction.do`는 homepage, JS `goMenu('100911')` eval 후 disclosure list가 in-place 렌더 → 2026.1Q 클릭 → fileList li[3] (li[1,2]=재무제표 skip)
- 서울보증: SPA, networkidle wait 5초 후 `#test1` 가시
- 삼성/롯데는 zip 파일(분기자료 묶음)

**결과**: 17/17 OK, 총 22.5MB. PDF 15 + ZIP 2 (삼성 1.8MB / 롯데 1.12MB).

---

## 2026-05-30 (c) -- F2 v3 KIDI ML01/MN07 crawler DONE — NB CSM 분모 6→328 entries, computed multiple 6→27/28

User triage: 데이터 수집 부족이 시행착오의 근원, 사용자가 source/keyword/URL 직접 짚어주는 방식으로 전환. **사용자 제공 3건**: (1) 정기경영공시는 `data/disclosure/{FY_Q}/pdf/`이며 DART fallback 금지(지급여력은 disclosure-only) (2) KIDI sample 2장 + URL `incos.kidi.or.kr:5443/insMonth/detail/ML01.do|MN07.do` + cbCmp selector dump (3) 생보 일괄 `pub.insure.or.kr/mngtDis/mngtDis/list.do` + 2026.1Q td XPath.

**Endpoint probe.** Detail page 200으로 열리는 핵심 = `?stattbl_id=ML01` 쿼리 필수(`/` GET → JSESSIONID 후 POST). 페이지 내 `fnSelect()` 본문에서 실제 ajax 호출 = `POST /insMonth/getQueryResult.do` payload `queryId=getML01List|getMN07List`, `comp_type=<L## | N##>`, `data_year=YYYYMM`. F2 v3 가설 정확 일치.

**컬럼 매핑 lock.** Top row(ML01 LINE=47 LVL=1 '합계' / MN07 LINE=99111 LVL=2 '원리금보장형장기손해보험 합계'). `ITEM_VAL2`=일시납 초회(천원, **제외**=저축성 일시납 위주, 사용자 의견), `ITEM_VAL4`=월납 초회(천원, 포함), `ITEM_VAL8`=기타 초회(천원, 포함). 분모(억)=(V4+V8)/1e5. **smoke test**: KR0008 N08 2025-12 V4=215,799,013 V8=4,286,738 → 분모 2200.86억 / KR0069 L03 2025-12 V4=278,913,166 V8=33,858,094 → 분모 3127.71억, 사용자 제공 sample 정확 재현(소수점까지).

**신규 ingest script** `scripts/ingest_kidi_monthly_premium.py`: 기존 `KidiClient`(`crawl_assoc_nb_premium.py`) 재사용. MAPPING 38사 × 13 quarter-ends(202303~202603). 라이 `data/kidi/raw/<stamp>/<KR>_<YYYYMM>.json` + 집계 `data/kidi/premium_summary.json`. **batch 494 fetch, 0 errors, ~6분**. 0-denom: 38건(2026.1Q 전체 — KIDI 미공개 202602까지만 / 코리안리=재보험사 구조적 N/A / 캐롯=장기손보 미운영).

**다운스트림 연결** — `crawl_assoc_nb_premium.py`에 `KIDI_SUMMARY_PATH` + `_parse_kidi_summary` + `KR_TO_WATERFALL`(28사 하드코딩, K-ICS 원수사명 ≠ waterfall name 미스매치 보정) + `_PERIOD_BY_MONTHS` 추가. 결과: companies **6→328**(KIDI 322 + IR 6 우선순위 보존).

**검증** — `validate_nb_csm_multiple` 6/6 pass(이전 5/6). `viz_build_csm_bubble` 재빌드 → premium=27/28 computed=27/28(코리안리 N/A). 검증 sample: 삼성화재 KIDI 15.68x vs IR disclosed 15.4 ✓, DB손해 16.3x vs F17 derived 15-17 ✓, 메리츠 11.5x ✓. **outlier flag** — 푸본현대 0.24x, 한화손보 16.8x(별도 한화손보 분자 ~2x 과대 spawn 진행).

**메모리 갱신**: `reference_data_sources.md` 신규 — DART/KIRI 가설 금지, disclosure 위치, KIDI endpoint·컬럼매핑, 생보 일괄/손보 사별 URL, DART KB·메리츠 별첨 함정.

---

## 2026-05-25 -- IFRS17 historical 13Q ingest + CSM 시계열 panel (push #2)

User asked to expand IFRS17 from FY2024 annual only to all quarters 2023.1Q ~ 2026.1Q. Built 3-stage pipeline + new IFRS17.html panel + deployed. **Downloader portion only** (stage 1):

**Stage 1 — Historical fetch (`scripts/ifrs17_batch_historical.py`):**
- Period targets: 13Q (사업 4 + 반기 3 + 분기 6). pblntf_detail_ty {A001/A002/A003} + report_keyword filter, skip 기재정정.
- Cache by canonical/period dir. Reuse `resolve_corp` + `OpenDARTClient`.
- 442 (insurer, period) targets attempted: 226 ok (CSM extracted) + 143 no_filing (비상장 분기 미공시 정상) + 68 no_csm_table_found + 5 errors.
- raw zip cached under `data/dart/raw_history/<canonical>/<period>/`. extracted_history per-period `_csm.json` (raw csm_extractor output).

(Stage 2/3 — promote-to-measurement + waterfall builder — are gathering work; see root `docs/claude-changelog.md`.)

---

## 2026-05-25 -- Bond tier `(신종)` fix + FSC bond normalize refresh

**Bond normalize (`scripts/normalize_bond_schedule.py`):**
- `_classify_tier` now maps FSC `(신종)`, `신종자본증권`, `하이브리드` → `tier1_hybrid` (was only literal `신종자본`).
- Re-normalize `20260525T061945Z`: tier1_hybrid **63** (was 48). KR0032 bond T1 outstanding **4500** = BS 신종 4500; KR0104 T1 **5000** ≈ BS 4999.
- Registry aliases: KR0032/KR0072/KR0104 주식회사 variants.

(Downstream forward sim v3 refresh tracked in `docs/claude-changelog.md`.)

---

## Compressed historical archive (pre-2026-05-25)

The compressed one-liner archive in root `docs/claude-changelog.md` ("## Historical archive (compressed)") contains a few downloader-relevant lines, kept inline there for compactness:

- FSC bond ingest client `src/bonds/` + `scripts/ingest_fsc_bonds.py` (MISC-BOND-INGEST)
- FSC schedule API per-insurer full pull: 1720 rows / 19 insurers
- Bond calendar v3: 5y Call rule for ALL bonds, 3-status outstanding/called/matured
- FSC schedule API 15059611 [승인] confirmed

These remain in the root changelog rather than being re-extracted, since they're already condensed.
