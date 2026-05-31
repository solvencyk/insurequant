# Insurequant Changelog — Downloader Stage

Stage 1 of 5 in the workflow split. See `CLAUDE.md` for the full 5-stage index.

**Scope:** data collection only — raw fetch from external sources (정기경영공시 / DART / FSC bonds / KIDI / IR factbooks).
**Cross-stage history:** `docs/claude-changelog.md` (parser/validation/gathering/pushing/refactor entries).
**This file:** entries scoped to downloader work only, extracted from the root changelog 2026-05-30.

Cross-stage entries that touch downloader as one phase but are primarily parser/gathering/viz (e.g. F11 foreign-affiliate viz integration, IR factsheet 전사 수집 + 손보 NB CSM 배수 파싱, F17 LOB parsing) remain in `docs/claude-changelog.md`. The compressed historical archive (pre-2026-05-25) also remains there.

## 2026-05-30 (N) -- DART batch script canonical-path refactor

User: "이건 지금 바로 실시하자 — DART batch script canonical path refactor".

Reorg #2 (2026-05-30j)에서 DART raw 폴더를 `data/dart/FY<year>_Q<q>/raw/<KR>_<name>[_<rcept>]/` 형태로 옮겼지만, 다운로더 3개 script는 여전히 OLD path로 write했음. 다음 분기 fetch 시 다시 OLD layout 생성 → 또 reorg 필요. 이번 refactor로 마감.

**신규 헬퍼**: `scripts/_dart_path_helpers.py`
- `_kics_name_to_kr()`: `kics_disclosure.json` 39개 원수사명 → KR code 매핑 (cached) + `_KICS_NAME_OVERRIDES` (AUDIT_REPORT_ANNUAL 5사 + 한화생명 표기변형)
- `kr_for_kics_name(kics_name)`: 원수사명으로 KR code 찾기 (보험 suffix 자동 시도)
- `period_label_to_dir('2023.1Q') → 'FY2023_Q1'`
- `annual_period_dir_for_rcept(rcept_no)`: rcept 첫 4자리 = filing year → FY{year-1}_Q4
- `quarterly_raw_dir(canonical_name, period_label, kr_code|kics_name|corp_code)`: 분기/반기용. Leaf = `<prefix>_<DART canonical_name>` (no rcept suffix)
- `annual_raw_dir(canonical_name, rcept_no, ...)`: 사업/감사용. Leaf = `<prefix>_<DART canonical_name>_<rcept_no>`. Year = filing_year - 1

**Leaf 명명**: DART의 `corp_name`을 사용 (Reorg #2 dir 명명과 일치). kics 원수사명과 다른 케이스 6 (삼성생명 ↔ 삼성생명보험, 코리안리 ↔ 코리안리재보험, IBK ↔ 아이비케이연금보험, KB라이프 ↔ 케이비라이프생명보험 등) 모두 DART 표기를 따름.

**Prefix 우선순위**: 명시적 `kr_code` > `kics_name` 룩업으로 얻은 KR > `corp_code` (group holdings 폴백) > 없음.

**3 script 갱신**:
1. `ifrs17_batch_all.py` (line 119): `out_dir = settings.raw_dir / f"{canonical}_{rcept_no}"` → `out_dir = annual_raw_dir(...)` (kics_name=name, canonical_name=canonical, rcept_no, corp_code 전달). extracted_dir 경로는 무변경 (parser stage 영역).
2. `ifrs17_batch_historical.py`: `HIST_RAW = ...` 제거. `process_one_period`을 annual / quarterly 분기 처리:
   - **Annual (A001)**: rcept_no를 dir 이름에 박아야 하니 `fetch_rcept_no`를 out_dir 결정 *전*에 호출. cache는 안 씀 (out_dir 자체가 rcept-dependent라 같은 rcept면 같은 dir).
   - **Quarterly (A002/A003)**: 기존처럼 out_dir/meta.json에 rcept_no 캐시.
3. `ifrs17_ingest_audit_annual.py` (line 97): `out_dir = settings.raw_dir / f"{canonical}_{rcept_no}"` → `out_dir = annual_raw_dir(...)`. AUDIT_REPORT_ANNUAL 5사는 _KICS_NAME_OVERRIDES로 KR 매핑 보장.

**Smoke 검증**: `scripts/_dart_path_helpers_smoke.py` 신규. 9개 케이스 모두 Reorg #2 기존 leaf와 정확히 일치 (메리츠/삼성생명/IBK/KB라이프/코리안리/AIA annual + quarterly + 그룹 holding fallback).

**호환성**: kics_disclosure.json에 없는 회사 (group holdings 등) → `corp_code` prefix로 fallback. AUDIT_REPORT_ANNUAL (kics 제외 5사) → overrides로 직접 KR 매핑. 39사 모두 매핑 검증.

**미터치**:
- `settings.extracted_dir` (parser stage output): 그대로 둠. 사용자 요청 "데이터 수집만 집중".
- `HIST_EXTRACTED = data/dart/extracted_history/`: 그대로 둠.
- `settings.raw_dir`은 ensure_dirs로 빈 폴더 생성될 수 있음 (무해).
- xml/ 추출 컨벤션: historical = `out_dir/xml/`, batch_all/audit = flat `out_dir/`. 기존 데이터의 추출 layout과 일관성 유지 위해 그대로 둠.

**다음 분기 fetch 동작**:
- `ifrs17_batch_all.py --year 2025` → `data/dart/FY2025_Q4/raw/KR####_<name>_<rcept>/`
- `ifrs17_batch_historical.py --all --periods 2026.2Q` → `data/dart/FY2026_Q2/raw/KR####_<name>/`
- `ifrs17_ingest_audit_annual.py --year 2025` → `data/dart/FY2025_Q4/raw/KR####_<name>_<rcept>/` (AUDIT_REPORT_ANNUAL 5사)

## 2026-05-30 (M) -- File-integrity audit + 현대해상 IR 재다운로드

User: "현대해상 2025.4Q IR공시자료 엑셀파일 열어보니까 안열리는데? 뭔가 파일 깨진거같아 ... 데이터 열었을때 안열리는 건들 있는지 조사해보고 오류난 건들은 다시 다운받아".

**Findings**:
- IR/disclosure/DART/KIDI 4 source × FY2023_Q1~FY2026_Q1 13 분기 = 1,965 파일 magic-byte + container 검증
- 초기 broken=8 → PDF tail padding이 -128B 검사 범위 밖에 있는 정상 PDF 6건이 false positive. 검사기를 `body[-16384:]` 윈도우 + `startxref` 존재 확인으로 완화
- 진짜 broken = 2건:
  1. **KR0009 현대해상 FY2025_Q4 Factsheet xlsx** (2.75MB) magic=`4372323403000000` 정체불명. hi.co.kr selenium goMenu('101641') click pattern으로 재다운로드 OK (225KB PK zip 정상). 깨진 원본은 `.xlsx.bad`로 백업
  2. **KR0071 흥국생명 FY2023_Q1 amended PDF** (487KB) magic=`9b 20 44 52 4d 4f 4e 45` = "DRMONE — This Document is encrypted and protected by Fasoo DRM". 흥국생명 다른 12 분기 PDF는 모두 정상 (%PDF-1.4/1.6). 이 한 amended(정정공시) 파일만 사이트가 Fasoo DRM 처리해서 호스팅 — 재다운로드해도 동일. DART 사업보고서로 대체하거나 SKIP 결정 필요(사용자 보고)

**Files**:
- `scripts/check_data_file_integrity.py` — 4 source 통합 file-integrity 검사기 (xlsx zip container, xls OLE, pdf %%EOF+startxref, zip testzip, json/xml 디코드)
- `scripts/check_ir_file_integrity.py` — IR-only 검사기 (개발용 prototype)
- `scripts/redownload_hyundai_ir_2025q4.py` — 현대해상 FY2025_Q4 한 분기만 재다운로드 (one-off)
- `scripts/redownload_shinhanez_disclosure.py` — 신한이지 6개 분기 disclosure 재다운로드 시도 (결과: 사이트 PDF가 -128B 외 padding 형식이라 다 정상이었음 — false positive 확인용으로만 사용)
- `data/_integrity_report.json` — 전 source × 전 분기 검사 결과

**Result**: 1,964/1,965 OK (99.95%). 남은 1건 = 흥국 amended DRM은 사용자 결정 대기.

**Follow-up (사용자 수동 교체)**: 흥국생명 FY2023_Q1 amended PDF를 사용자가 직접 받아서 교체 (Fasoo DRM 우회). 새 파일: `%PDF-1.4`, 483KB, EOF/startxref 모두 정상 위치. 재검증 결과 **1,965/1,965 OK (100%)**.

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
