# Cross-stage Changelog

> Last updated: 2026-07-21 · Stage: cross-stage
> Index: CLAUDE.md (5-stage) · Stage histories: docs/changelog_<stage>.md

Cross-stage entries only (gathering / pushing / refactor / cross-stage viz / 폴더 정리). Stage-specific history lives in `docs/changelog_<stage>.md`. See `CLAUDE.md` for the 5-stage index.

Convention: latest few entries detailed; older compressed to 1-liners (git log has commit-level detail after first push 2026-05-25).

---

## 2026-07-21 — 리팩토링 2차: PL 빌더 분할 · K-ICS.html 인라인 JSON 외부화 · 품질게이트 복구

**A. `build_pl_breakdown.py` 4,885줄 → 패키지 분할 (`8ef3136`+`7b21bfb`)** — 먼저 **골든 게이트**(`tests/test_pl_breakdown_golden.py`, `RUN_PL_GOLDEN=1`)를 깔아 빌더가 결정론적·오프라인임을 확인(연속 2회 실행이 커밋된 마스터와 바이트 동일). 그다음 AST로 내부 참조 그래프를 떠서 이음매를 **측정**하고 그 선을 따라 잘랐다: tier1↔tier2 간선 0, companies는 바깥에서 11개 이름만 참조, companies를 참조하는 상류 0(단방향). 결과 `pl_breakdown/{common 34, tier1 355, tier2 488, companies 3493}` + 엔트리 567줄. **회사별 핸들러 구조는 우발적 복잡도가 아니라 회사마다 다른 DART 주석 레이아웃**이므로 그대로 보존했다. 산출물 바이트 동일(2,940행/117 company-quarter).

**B. K-ICS.html 인라인 JSON 147KB 외부화 (`a629e34`)** — `window.TIER1_DATA/TIER2_DATA/FORWARD_DATA`가 페이지의 **70%**(147,199/208,957자)를 차지했고 main도 동일. 근거였던 "file:// fetch 회피"는 이미 무효 — 페이지가 `kics_disclosure.json`·`kics_rate_sensitivity.json`을 fetch하므로 원래부터 file://로는 안 돌아갔다. 게다가 **FORWARD_DATA만 생성기가 있고 TIER1/TIER2는 손으로 붙인 값**이라 빌더 산출물과 조용히 어긋날 수 있었다. → 루트 JSON 3개로 분리(39/39/38행), 민감도 패널과 동일한 fetch-후-재렌더 패턴. `K-ICS.html 208,957 → 62,081자(-70.3%)`. `forward_capital_simulation.py`는 HTML 라인 치환 대신 JSON을 쓰므로 **`--no-html` 플래그 소멸**(publishing/designer 하드분리가 걸림돌이던 이유가 사라짐).
> ⚠️ **배포**: 3개 JSON은 신규 keep-list 항목. K-ICS.html만 올리면 자본도넛·forward 패널이 **에러 없이 빈칸**이 된다. `tests/test_deploy_assets.py`가 4개 페이지의 fetch/link 로컬 참조를 전부 뽑아 존재를 강제한다.

**C. MD 품질게이트가 아무것도 통과 못 시키던 버그 (`69e9648`)** — `score()`가 점수에 `numeric_normalisation_rate`를 곱한 뒤 0.7을 요구하는데, 그 rate가 **각 행 첫 셀(한글 항목명, 숫자일 수 없음)** 까지 세고 있었다. 라벨 있는 표는 rate가 0.6 근처가 상한이라 **완벽한 파일도 통과 불가** → 488개 중 485개 review. 라벨 컬럼 제외로 중앙값 0.595→0.699, review 485→306.

**D. 안 한 것 — `_num` 계열 30개 중복 (측정 후 기각)** — 30개 사이트에 **24개 서로 다른 구현**이었다. 복붙 부패가 아니라 두 계열(원시텍스트 파싱 vs 이미 정규화된 마스터 셀 읽기)이고, `"-"`를 `None`으로 볼지 `0.0`으로 볼지가 갈린다 — 후자를 통합하면 owner가 기록한 "0값 맹점"을 정면으로 건드린다(`dash_means_zero`는 호출부마다 명시적으로 끄고 있어 의도된 설계였음). 통합 가능한 군(3변형/약 10사이트)은 마스터 16.8만 값 + 엣지케이스로 **동치 증명(불일치 0)** 까지 했으나, 플랫한 scripts/ 구조에서는 공유 모듈 import 배관이 5줄 함수보다 비싸서 하지 않았다.

---

## 2026-07-21 — 리팩토링 1차: 죽은 kics_data.json 경로 제거 + 실행 불가 스크립트 복구

**삭제 (임포터 0 확인 후, `0543414`)** — `src/solvency/validation/rules.py`(967줄, xlsx 대상 a~g 룰; `kics_json_rules.py`가 대체) · `src/solvency/legacy/` 전체(~2.6k줄: camelot_parser·merge_xlsx·csv_to_json·회사별 다운로더 4종; 단일 다운로더 엔진 + docling_parser가 대체) · `transform/md_to_json.py` + `validation/schema.py` + `schemas/kics_data.schema.json`. `src/` 12,547 → **7,500줄 (-5,047)**, `run_harness.py` 517 → 296줄.

**`run_harness.py` 함정 제거** — `--stage perf|data|all` 삭제. 기본값이 `all`이라 인자 없이 실행하면 2026-05-30 폐기된 `kics_data.json`을 루트에 다시 만들어냈다. 이제 `--stage` 필수, 선택지 `quality|pdf|parse`. `--stage data`의 부수효과로만 돌던 MD 품질게이트+리뷰큐는 `--stage quality`로 독립.

**실행 불가 스크립트 복구 (`4bcb188`)** — `scripts/export_red_all_cases.py`가 **UTF-16 LE**로 저장돼 있어 "source code string cannot contain null bytes"로 매 실행 즉사. publishing 프롬프트가 post-validation 리포팅 도구로 지목한 스크립트였다. UTF-8 재인코딩 후 정상 동작 확인. BOM 2건(`ingest_fsc_bonds.py`·`recalc_basic_capital_ratio_post.py`)도 정리 → scripts 212개 전부 파싱 가능(이전 3개 실패).

**컨텍스트 트리밍** — TODO.md Status가 RED=227(2026-06-12) 주장(실제 12), 같은 파일 안에 24라는 세 번째 숫자까지 공존 → 검증된 현재값으로 교체 + SUPERSEDED 이력 블록 제거. 종결(resolved/done/superseded) 상태로 open 레인에 남아있던 inbox 12건 `_resolved/` 이관. 죽은 모듈을 가리키던 flow 문서 정정, `claude-json-build.md` 폐기.

**검증** — pytest 113 passed(이전 111 passed/2 failed; e2e 2건은 엔진이 status를 downloaded/downloaded_basic으로 쪼갠 뒤 방치된 stale assert였음). `validate_kics_disclosure.py` RED=12 YELLOW=561 GREEN=4701 SKIP=1530 — 리팩토링 전과 완전 동일.

---

## 2026-05-31 — Stage changelogs split out

Per-stage history moved to dedicated files:

- **Parser** → [`docs/changelog_parser.md`](changelog_parser.md): 2026-05-31 NB CSM widespread fix + F17 9/11 / 2026-05-30 Tier2 방법론 + Tier1 PoC + IR disclosed/derived / 2026-05-29 product-segmented + `<TE>` + rowspan + de-contam / 2026-05-25 B5 appendix + historical promote.
- **Validation** → [`docs/changelog_validation.md`](changelog_validation.md): 2026-05-31 DART↔IR cross-source 3 rules (`CSM_WATERFALL_DART_VS_IR` / `SEGMENT_INSURANCE_INCOME_DART_VS_IR` / `CSM_BREAKDOWN_DART_VS_IR`, F18-gated) / 2026-05-29 plausibility gate / 2026-05-25 rules 9+10 + RED 99→2 + Tier-2 reconcile / 2026-05-24 KICS-VALIDATE harness.
- **Downloader** → [`docs/changelog_downloader.md`](changelog_downloader.md): all 2026-05-30 downloader work (Reorg #2 ~ F2 v3 KIDI crawler).

## 2026-05-30 — data/ifrs17 → data/dart 리네임 + Panel 3 viz 교체

**리네임:** dup `data/dart` 삭제 후 `data/ifrs17` → `data/dart` 실제 리네임. 코드 repoint 35파일 (경로형만; `src/ifrs17` 모듈·`IFRS17.html`·`from src.ifrs17` 불변). 잔여 참조 0, viz 재빌드 정상 (28사, 회귀 0). **Panel 3 viz:** IFRS17.html Panel 3을 원시표 덤프 → 클린 4-bar 당기순이익 분해 (보험손익/투자손익/영업외 → 당기순이익) 교체. 브라우저 검증 OK. (F17 parser 절반 = changelog_parser.md.)

## 2026-05-29 — F11 DONE: 외국계 생보 5사 IFRS17 대시보드 편입

IFRS17 cohort 23→28 (생보 13→18), 5사 모두 대시보드 + index bubble 렌더. 브라우저 검증, 회귀 0. **Viz는 glob-driven** — builder가 `data/dart/extracted/*.json` enumerate + IFRS17.html이 `wf.companies`에서 selector 생성 → 표준 artifact 생산만으로 selector(28) + bubble 자동 확장, HTML 구조 변경 거의 없음. 5사는 정기보고서 없고 standalone 감사보고서 (2024.12, pblntf_ty=F)에 IFRS17 주석 — 기존 `csm_extractor` 무수정 파싱. `ifrs17_ingest_audit_annual.py` 확장 (meas/pl/sens 추출). corp_codes는 root TODO.md F11 행 참조. AIA는 kics_disclosure.json에 없음 (universe-only). 라이나 partial (amort row 없음), 나머지 4사 ok. parser-side waterfall 3 fixes = changelog_parser.md.

## 2026-05-28 — IFRS17 yearly CSM amort (F6) + KPI/BS panel pruning + 모바일 M1/M2 + HTML single-source

여러 gathering/designer 작업 (commit-level은 git):

- **F6 yearly amort (panel 2):** `viz_build_ifrs17_panels.py` `extract_amort_schedule`가 `yearly`(y1..y10+y10plus+total)+`granularity` 추가 (4-bucket `buckets` 유지). 16 yearly / 6 coarse / 2 no-data. IFRS17.html 데스크톱 10년/모바일 5년 (`matchMedia` 640px), coarse는 4-bucket fallback. `Chart.getChart` 검증.
- **Panel pruning:** Downstream KPI 카드 4개 + BS 스냅샷 표 제거 (파생 proxy 비공식 / BS는 DART 중복). 생성 스크립트는 유지 (bubble closing CSM). 정의는 `docs/archived_metrics.md`. 패널 1–6 재번호.
- **모바일 M1 (공통 토대):** 4페이지에 `@media (max-width:640px)` — 헤더/탭 가로스크롤, 여백·차트높이 축소, 표 가로스크롤. 데스크톱 무영향. Preview 375/1280 검증.
- **모바일 M2 (treemap→list):** index.html ≤640px에서 treemap 숨기고 세로 리스트 (`renderList`, 지급여력기준금액 desc). render()와 데이터·색상·토글·클릭 공유. 콘솔 에러 0.
- **HTML single-source (P1+P4):** `templates/{index,K-ICS,IFRS17,공시보고서}.html` 4개 삭제, 루트가 유일 원본 (templates/K-ICS.html이 stale forward 데이터 서빙하던 버그 해소). index.html 미사용 xlsx CDN 제거. 로컬 미리보기 = 루트 `python -m http.server`. ⚠️ 데이터 JSON 중복 남음 (P2).

## 2026-05-25 — IFRS17 historical 13Q + CSM 시계열 panel (push #2) + bond tier + forward sim

- **Historical 13Q + Panel 8:** 3-stage 파이프라인 (fetch=downloader / promote=parser / viz aggregate=gathering). `csm_waterfall_history.json` (23사 × 13Q). IFRS17.html Panel 8 "CSM 시계열" Chart.js dual-axis (기말 + 신계약, 22 배경라인). 한화 2023.4Q opening mismatch + 분기보고서 text-only gap = 이후 parser fix. **Push:** commit `e846e5a`, https://solvencyk.github.io/insurequant/IFRS17.html deployed.
- **Bond tier `(신종)` fix:** `normalize_bond_schedule._classify_tier`가 `(신종)`/`신종자본증권`/`하이브리드` → `tier1_hybrid`. tier1 48→63. KR0032 T1 4500=BS, KR0104 T1 5000≈BS.
- **Forward sim v3:** confidence high 5 (+1). KR0032 `fsc_missing_t1` cleared; KR0072 remains (FSC has only called tier1). KR0003 Lotte basic_cap −3875억 / KR0072 KDB −3311억 (user-confirmed real stress).

---

## Historical archive (compressed)

Commit-level detail in git log (first push 2026-05-25).

### 2026-05-25 mid-session (gathering/pushing/cross-stage)
- Forward sim v2: confidence per-row, `capacity_exhausted` cap, auto-sync `window.FORWARD_DATA`
- K-ICS.html Phase 4: 자본성증권 도넛 + Forward Outlook 라인 (dual-axis, 130%/50% 기준선)
- KICS-FORWARD-CAPITAL Phase 3 v1: yearly × 5y, 19사. 롯데 2030 94.67%, 한화 158→134%
- Bond calendar v3: 5y Call rule 전 종목, 3-status. 19.60조 outstanding. FSC API per-insurer 1720 rows / 19사
- Meritz xlsx (K-ICS 240.74%, CSM 112.9조, NB mult 12.61x, Group RoE 25.37%)
- K-ICS gate RED=0 ex OCR (report 20260524T180329Z, 12795 rows, 25 tests)
- User-facing Tier1/Tier2 utilization report 2025.4Q (Korean prose); full RED export 99 cases
- Tier-2 utilization numerator fix (KIRI reconcile): in-range 9→34. FSC bond ingest `src/bonds/`

### 2026-05-24 dashboard + HTML viz
- IFRS17 CSM waterfall panel + 7-panel dashboard · index.html treemap fetch/layout fix · `viz_build_ifrs17_panels.py` rewrite (ASCII source, UTF-8 no BOM) · index C-1/C-2 (no transition toggle) · item28 basic-capital ratio post-transition · K-ICS.html 보조지표(29-35) + 경과조치 토글 · CSM Waterfall HTML proto · NB CSM Ratio HTML proto · IR visual aid 카탈로그 6사

### 2026-05-23 initial setup
- IFRS17 키지표·스크래핑 우선순위 (`docs/claude-agent-ifrs17.md`) · 생명장기손해보험위험액 보조지표 → kics_disclosure.json · IFRS17 도메인 부트스트랩

### 2026-04-25 ~ 04-28 pipeline foundation
- 코드 통폐합 + Docling 파이프라인 · 디렉토리 quarter-first 마이그레이션 · NONLIFE/LIFE 협회 다운로더 · PDF 검증/ACL 모듈 · FY2025_Q4 하네스 일괄 실행
