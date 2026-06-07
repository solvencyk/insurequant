# Cross-stage Changelog

Cross-stage entries only (gathering / pushing / refactor / cross-stage viz / 폴더 정리). Stage-specific history lives in `docs/changelog_<stage>.md`. See `CLAUDE.md` for the 5-stage index.

Convention: latest few entries detailed; older compressed to 1-liners (git log has commit-level detail after first push 2026-05-25).

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
