# Insurequant Parser TODO — IFRS17 lane (Stage 2)

> Last updated: 2026-07-30 · Stage 2/5 — parser (ifrs17 lane)
> Prompt: docs/agents/claude-agent-parser.md · Changelog: docs/changelog_parser_ifrs17.md

Stage 2 — **parser, IFRS17 lane**: CSM/PL extraction. Source = DART body XML; output = `CSM_waterfall` / `PL_breakdown` masters; validators = CSM golds / PL golds / `csm_waterfall` / `pl_bridge`. The K-ICS lane (solvency disclosure off Docling MD) lives in `TODO_parser_kics.md` and runs as a separate session.

Session start: read this file + `docs/agents/claude-agent-parser.md` + `docs/domains/claude-agent-ifrs17.md`. English where Korean encoding is fragile (see `CLAUDE.md`).

## Status

IFRS17 lane is **mature**: CSM waterfall + PL breakdown masters all built (root JSONs assembled, xlsx regenerated). 2026.1Q loaded (changelog (s)). CSM golds 8/8 and PL golds pass; `check_pl_reconcile.py` closed the large systematic gaps (예실차-미공시 generic closure + 에이비엘 leg + 하나 장기). Remaining work is residual Tier-2 coverage backfill + a few escalated owner decisions (코리안리 FY2025 basis), not core extractor rewrites.

> **2026-07-30 inbox drain (17 lane:ifrs17 items processed)** — full detail in `docs/changelog_parser_ifrs17.md`
> 2026-07-30 entry. Highlights: **KR0075(BNP파리바카디프) 100x + KR1098(카카오페이) 1000x CSM unit bugs
> fixed** (raw-confirmed where raw exists, override-based where it doesn't — see overrides' `why` fields);
> **KR0029(AIG)'s identical bug already resolved by an untracked prior session**; **KR0004(예별손해=구MG)
> onboarded 3 years** via safe per-dir extraction (not the destructive full raw-glob); **KR1011(IBK) protected**
> from a latent data-loss bug in the diag-rebuild path; **`sensitivity_heatmap_provenance.json` sidecar
> shipped** (validation's UH-3 ask, gate RED=0); **FY2025 sensitivity mass-refresh confirmed already done**
> (32/32사, TODO below was stale saying only 흥국 — corrected). **⚠️ Found + avoided a near-miss**: this
> branch's `build_root_masters.py::main()` is unsafe as a whole — not just the CSM half (already known) but
> **the PL half too** (`pl_breakdown_master.json` diag is equally stale from the git-purge; a bare `main()`
> run silently collapsed the committed `PL_breakdown.json` from 319 to 117 (company,quarter) combos before
> being caught by diffing and reverted). **Always call `build_csm()`/`build_pl()` individually and diff full
> combo-sets against `git show HEAD:<file>` before trusting output on this branch** — see
> `[[project_git_purge]]` memory. New open items from this session are filed under P1/P2 below and in the
> relevant `inbox/{downloader,validation}/` tickets (KR1098 FY2024 raw refetch, KR0051 FY2025 raw refetch,
> `CSM_WATERFALL_PLAUSIBILITY` rule request, postmortem `docs/postmortems/PM-2026-07-30_kr0075_csm_100x_unit.md`).
> **Master xlsx needs regeneration** (publishing, official `xlsx` skill) — CSM_waterfall.json/NB_CSM_multiple.json
> changed.

> **Disposition pass 2026-06-14** (committed-master read-only, 5-agent; inbox `20260612T0900Z` 답변): V9/V7/PL-T2 잔여 14건 판정 → **legit 10 종결** (코리안리 상각 "1y lag" = 부호규약 artifact·워터폴 close / history off-by-one = year-shift 없음 / 메트라이프 영업이익 등식 OK / 한화손해 NB non-stale / 동양 재보 = net-only legit-absent, phantom item9/10 백필 금지 / 케이디비·롯데·교보플래닛 정상 또는 legit-absent), **real_gap 2 (raw-blocked)**: 현대해상 예실차(item6/11) pre-2025.3Q 결측 + 악사 interim 분기 부재 — fix는 purge된 분기 raw 필요, **designer handoff 1**: csm_delta=null→0 렌더(동양/NH, `inbox/designer/20260614T1300Z`), **out_of_scope 1**: 하나생명 item17 투자손익=FS-API 레인. fixable-now bug 0.

> **round3 IFRS17 QA 2026-06-16** (inbox `20260616T0007Z__…ifrs17_pl_sensitivity_round3` → commit 5b9b0eb):
> **P1 흥국 해지율** = staleness fix(heatmap FY2024→FY2025 흥국 1社 교체, 부호버그 아님). **P2 푸본현대 투자손익
> −1,487.7억 = REAL**(별도 소스 24항목 대사, 연간순손실 실재). **P3 하나생명 item17 = parse_miss**(2-line
> II.투자수익/III.투자비용 공시 → 단일 룩업 미스; 정확값 item18=317,891.06·item17=+821.41백만; `_GOLD_CELL_OVERRIDE
> [(KR0097,2025.4Q)]` 추가) — ↑ disposition-pass의 "하나 item17=FS-API out_of_scope" **해소(파서측 정정)**. 단 라이브
> master 반영=raw-enabled rebuild 필요(이 브랜치 파괴적). · **IFRS17 도메인 SKILL** `.claude/skills/ifrs17-parser/`
> 결정화(skill-creator, machine-local; inbox `20260616T0043Z`).
>
> **phase-2 잔존** (FY2025 sensitivity 전사 refresh): band/generic 경로 product/sub-row 일반화(농협/케이디비
> 가비지) + 동양/메트라이프/에이비엘/처브 SA=0 분류 — 다세션. 현 heatmap은 흥국만 FY2025, 나머지 FY2024 유지.

---

## 🟡 Completed (2026-07-04) — IBK연금보험 KR1011 온보딩

- [x] CSM_waterfall.json IBK 3개년 적재 (closure/continuity 검증 완료)
- [x] PL_breakdown.json IBK 72레코드 적재 (tier1+tier2 gold override, closure 5종 Δ=0)
- [x] viz 전파 (sensitivity_heatmap/csm_amort/insurance_pl/csm_waterfall/csm_bubble/kpis/quadrant)
- [x] publishing inbox 발송
- [x] **IBK CSM waterfall newbiz 스테이지 누락 — 완료 (2026-07-30 세션 이어받음).** 라벨 미스매치 2건(`당기에 최초로 인식한 계약`/`제공된 서비스에 대해 인식한 보험계약마진`, STAGE_PATTERNS에 정확 리터럴 추가) 수정 중 **더 심각한 사전 버그 2건 추가 발견**: ① `_disambiguate_basis_period`가 IBK의 "2)유배당 외"(무배당) 세그먼트를 whole-book으로 오선택(5.5% 과소— 캡션 `^\d\)\s*유배당` 정규식으로 스왑대상에서 제외, 처브라이프도 같은 캡션 패턴이나 값 무변경 확인됨), ② FY2023 filing이 전기(FY2022) 컬럼을 선택(`len(full)<2` 조기return이 prior 판정 결과를 버림 — `len(current)==1`일 때 승격하도록 수정). 3개년 15값 전부 CSM_waterfall.json 마스터와 정확 일치 검증, 47개사 전체 diff로 IBK 외 회귀 0 확인(첫 시도 때 한화생명 등 12사 회귀 유발했던 버전은 폐기하고 재수정). `csm_bubble.json`/`downstream_kpis.json`은 별도의 사전 staleness(17개사, 무관)+kpis 자체 버그(closing null)까지 얽혀있어 미반영·원복 — 후속 필요.
- [ ] **master xlsx 재생성** — xlsx skill 사용 (publishing 세션).

---

## 🔴 Open — P1

### XLSX-FOLLOWUP — owner xlsx 수동검토 후속 (2026-06-10, CSM 정정은 changelog (c) 반영 완료)

- [ ] **NB배수 분모 '기타' 초회보험료 혼입** — 농협생명/NH손보 568억(26.1Q) 등. 기타 제외 재계산(KB라이프/교보/한화/삼성생명 포함), 삼성 IR 대조, 10~17 range 확인 → 분모 정의 수정 여부 결정. (분모=월납초회 VAL4만 적용은 06-11에 했으나 IR 대조·range 확인 잔여.)
- [ ] **PL 0값 sanity 감사** — 현대해상(생명장기 원수/재보험 6항목 전부 0)·롯데 25.2Q·NH손보·악사·ABL·KDB·라이나·미래에셋·동양·메트라이프. 분류: extraction_miss/legit_absent(→null)/true_zero. (10/10 감사는 06-11 (o) 완료; 잔여는 designer null 렌더링.)
- [ ] **0의 의미론**: 미공시 항목이 0으로 적재되는 설계 교정 검토 — 미공시=null, 공시된 0만 0.
- [ ] (validation 발주됨) **AMORT_ZERO** 룰 — 상각=0 불가. inbox `20260610T1700Z__parser__MULTI__csm_owner_review_fixes.md`.
- [ ] (validation 발주됨) **NB배수 <1.0 하한** (분자붕괴 표면화).
- 미래에셋 '기타' 테이블 CSM: owner — 식별비용 크면 패스 가능 (보류).

---

## 🟠 Open — P2

### PL-T2 — PL Tier-2 residual gaps (after 2026-06-08 census, changelog (m))

Track with `python scripts/check_pl_reconcile.py`. 큰 systematic 갭은 닫힘(예실차-미공시 generic closure + 에이비엘 leg + 하나 장기). Remaining actionable (non-legit, 2024.2Q+):
- [ ] **동양(2024.x) / 케이디비(2025.x) 재보 CSM상각(item9) / RA(item10)** — 출재 섹션 깊이 박힘, 분기별 노트 구조 상이. Small (재보 sub-slice), per-company/quarter handler. fragile fix 강제 안 함.
- [ ] **하나생명 투자손익(item17)** 2024.4Q/2025.4Q — Tier-1/FS-API lane (parser scope 밖일 수 있음).
- [ ] **교보라이프플래닛 Tier-2 absent** — 디지털 생보, 공시 최소 (likely legit-absent; confirm).
- [ ] **KDB 2023.2Q items 15/17/18** (OLD 양식 매핑 모호 — owner gold 대기) + **KDB 2025.2Q item6 오염 의심** (보정값 미확보, 미래에셋 2025.2Q diff).
- legit (not bugs): 코리안리 자동차(item13) — 재보험사 무자동차(11 c-q). FY2023 holes/WRONG = 사이트 비노출.

### CSM-FOLLOWUP — CSM closing / 마스터 통합 잔여 (2026-06-07 야간, changelog 2026-06-07)

- [ ] **closing 5 SKIP**: 라벨변형(KDB 2023.1Q·미래에셋 2025.2Q/3Q·하나손해 2024.4Q — 상각/이자 변동요인별 라벨) + AIG 2025.4Q(단위오류 null). `viz_build_csm_waterfall.py` STAGE_PATTERNS amortization에 라벨 append.
- [ ] **메트라이프 2025.4Q ~2.2× 점프**(세그 중복 의심) + **KDB 2025.4Q 기초 불연속**(closing 통과, 시퀀스만) — 발행 전 review.
- [ ] **pl_bridge 36F 잔존** = bare-closes 오탐(룰 dual-form 권고) + DB생명/동양 2023(FY2023 상반기 Tier-1 부재) + DB OLD 재보.
- [ ] **crosscheck 9F 잔존** = 코리안리 재보험 item4 scope(상각 1y lag 의심) + 소수.
- [ ] CSM diag → canonical 통합 확인 / 분기 시계열 연속성 재검증(별도 min-opening 적용 후) / KDB·ABL 생명 CSM 미커버 구조 확인.

### TIER2-NEXT — Tier-2 대확장 후속 (2026-06-06 (b), changelog 2026-06-06 (b))

- [ ] **미래에셋 분기 4/12** — rollforward 원-unit → 백만원 emit 핸들러(현재 sanity cap으로 garbage만 차단).
- [ ] **한화손해 13/14 퇴직연금** — owner 배분판단 필요(현재 순수 PAA값). + pre-2025.2Q OLD 핸들러(8분기 blank). + 2025.1Q NB stale carryover.
- [ ] **흥국화재 NEW 2025.4Q/2026.1Q** — 연차 단일표 오작동(4/5=0). 별도 수정.
- [ ] **흥국생명 2026.1Q 더블링** — `_life_comprehensive` dedup이 caption 공백차 중복노트 누적.
- [ ] **롯데 6/12** — 2024.2Q/3Q·2025.3Q/2026.1Q 컴포넌트노트 미발견(deeper probe).
- [ ] 교보 반기/분기 3개월 basis(누적 아님) / 한화생명 2023.2Q(x=1, FY2023 outlier).
- [ ] 아이엠라이프 빌더 핸들러 정식화 (현 override 정상 — KR0076 구성요소별 변동표 CSM열 전용).

검증: `PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/build_pl_breakdown.py` → `scripts/_verify_pl_golds.py` → `scripts/_pl_selfcheck.py`.

### Cross-stage parser features (full detail here; root TODO.md keeps 1-line refs)

#### F15 — CSM 시계열 분기 결측 (after 2026-05-29 fixes). 잔여 honest gaps:
- [ ] **삼성생명 2023.1Q** — early-2023 layout, parser miss
- [ ] **미래에셋 2023.1Q / 2023.3Q / 2026.1Q** — early-2023 layouts + 2026.1Q anomaly
- [ ] **동양생명 2025.2Q ~ 2026.1Q** — 잔액(기초/기말) row 0 추출; 재다운로드 검토 `TODO_downloader.md` F15-DL
- [ ] **손보 일부 전사-vs-세그먼트 pick** — reject guard 후 gap 처리; 회사별 disambiguation matrix 필요

#### F16 — Panel 5 흥국생명 민감도 (product-as-rows layout) ✅ DONE 2026-06-14 (changelog 2026-06-14 sensitivity follow-up)
흥국생명 sensitivity 표 별도 양식: 상품(사망/건강/연금)=행, 당기말/전기말 × CSM/손익효과/자본효과=컬럼. 영문 'CSM'+'손익 효과' 라벨. 기존 3-path band parser 미적용 → 행 어긋남.
- [x] product-row × period-band-column 4번째 path 신설 — `_extract_heungkuk_product_rows` + `_is_heungkuk_csm_pl_capital_layout` guard (`viz_build_ifrs17_panels.py`). 흥국 6 시나리오(위험×상승/하락) 정상.
- [x] 다른 회사 회귀 zero check — status {ok:25,unavailable:1,partial:2} 불변, 타 패널 byte-identical, pytest 110
- [ ] Panel 5 caption 갱신 (가능한 회사 명시) — designer 소관

#### F17 — Tier1 + Tier2 LOB 당기순이익 분해 (parser body). 남은 parser gap:
- [ ] **KB / 메리츠 / NH농협** — FY2025 사업보고서가 FS를 별첨 감사보고서로 분리, body XML에 LOB 없음. (별첨 fetch 안 함; 회사별 label 매트릭스 + 본문 내 다른 표 찾기)
- [ ] **DB / 한화 / 흥국** — 회사별 disambiguation (다중후보표 중 picker 오선택)
- [ ] **삼성화재 Tier2** — taxonomy 보장성/물보험/저축성 → 현 파서가 장기/자동차/일반만 기대해 미스 (Taxonomy 참조)
- [ ] **코리안리** — 재보험사 LOB N/A, 영구 SKIP
- [ ] FY2024 LOB — 사업보고서에 존재(감사보고서 X). 필요 시 fetch 대상 분리
- [ ] **In-flight decision (2026-05-31):** Tier2 LOB 9/11 손보 OK. (1) 9/11 commit + 2 gap을 documented exception, (2) 삼성·DB debug, (3) IR-clean 회사만 — 중 하나 결정 대기.

#### F18 — IR factsheet 정형화 (DART↔IR cross-validation 활성화)
Validation 룰 3개 추가됨 (V1 in `TODO_validation.md`); 활성화 대기.
- [ ] **Delivery 계약**: `data/ir/<period>/parsed/<KR>.json` 정형 JSON. Schema: `docs/agents/claude-agent-validation.md` §1.4. 모든 값 억원
- [ ] **출발 cohort 9사**: 메리츠·삼성화재·현대·KB·DB·한화생명·삼성생명·미래에셋·동양
- [ ] IR 미공시 회사 (교보·KDB·외국계·카카오페이손해 등) auto-SKIP 명시
- [ ] 생보 `segment_insurance_income` 키 셋 (보장성/저축성/연금/변액 후보) 확정 — validation V1 참조

---

## 🟡 Open / waiting

- [ ] **코리안리(KR1000) FY2025 CSM basis 결정 (escalated 2026-06-09 (b), inbox `20260609T0200Z`)** — CSM이 두 노트에서 상이(일반모형 FY2024말 8031.5 vs CER/배당칼럼 9046.7). FY2024→2025 경계 +1015억 점프 + 2025.2Q 이자부리 FX 혼입(−147.2억). 단순 re-anchor 불가. **owner/2nd소스 결정:** Option A — 전년 일반모형노트로 통일(2025+ 재추출, 기초 8031.5, 내부일관) / Option B — 2025+ CER basis 수용, 경계를 documented basis-switch exception(파서 무변경). ⚠️ pattern2/배당칼럼 = 삼성화재/현대/한화손보/삼성생명 공유 → 재추출 시 per-company 가드 + full diff. 함께: 2025.2Q FX를 item3 대신 item4 residual로(삼성생명 회귀확인).
- [ ] **validation 회신 대기**: WFY documented exception 9건 등록 + KR0011 해소 확인 + NB<1.0·AMORT_ZERO 룰 구현 확인.
- [ ] **designer 핸드오프**: PL legit-absent null '—' 렌더. 메트라이프 2025.4Q CSM 점프(~2.2x) 재확인. 3사 중 신한이지 '분리공시 미제공' HTML 처리(root TODO).
- [ ] **MLG-1 듀레이션갭** (owner 결정): 100bp 민감도 추출이 첫 단계, 유도식 owner 결정. DART 본문에 갭 서술+만기사다리+100bp 민감도 있으나 듀레이션 숫자·갭 자체 없음. [xref: parser-kics] (듀레이션갭은 K-ICS 금리위험과도 연결되나 CSM/민감도 컨텍스트가 1차라 IFRS17 lane 소관 — default rule per split.)
- [xref: parser-kics] **IFRS-NORMALIZE** — `row_aliases.yaml` 확장이 IFRS17 lane과 공유됨(현 PoC 930/2956 tagged). Full substance + owner = K-ICS lane (`TODO_parser_kics.md`). IFRS17 lane은 row_aliases.yaml 변경 시 동기화만 확인.

---

## Taxonomy note (do not conflate in parser)

LOB axis differs between 손보 CSM decomposition and 손보 P&L decomposition:
- **손보 CSM decomposition** = 보장성 / 물보험 / 저축성 (all within 장기보험; 삼성화재 uses this)
- **손보 P&L decomposition (보험손익)** = 장기 / 자동차 / 일반 (Tier2 in F17)
- 자동차 / 일반 = PAA contracts → no CSM rollforward; P&L only
- 보종별 신계약 CSM multiple은 일부 보험사만 IR 공시 — DART에서 합성 금지

Remove once F17 lands and prompt §2.2 captures it.

---

## ✅ Done (archive)

완결 항목 40+개(IFRS17 lane, 2026-05-24~06-11) — CSM waterfall 블록선택·basis disambiguation, PL breakdown 24항목 전사 sweep, sensitivity heatmap, NB CSM 배수, root 마스터 빌드, `<TE>` parser fix, 외국계 5사 등. 한 줄 상세는 `docs/changelog_parser.md`(당시 `(changelog XX)`로 인덱싱) + git log. (K-ICS-lane done items → `TODO_parser_kics.md`.)


---

## Reading order for parser subagent (IFRS17 lane)

1. This file (`TODO_parser_ifrs17.md`) — open work + done archive + taxonomy note
2. `docs/agents/claude-agent-parser.md` — master prompt + per-domain contract
3. Domain ref: `docs/domains/claude-agent-ifrs17.md` for label variants and company quirks
4. Root `TODO.md` only for cross-stage items (F15/F16/F17/F18) — full detail lives here
5. Sibling lane: `TODO_parser_kics.md` (solvency disclosure) — for [xref] items

Deferred (2026-07-27): `docs/changelog_parser_ifrs17.md` (+ pre-split `changelog_parser.md`) is history — open only when you need a past decision's background; most sessions don't.

## Hand-off to validation

After parser produces normalized CSM/PL masters, validation is invoked per `docs/agents/claude-agent-validation.md` §3 (retry loop, max 5). On RED, validation calls back the parser with the failing rule + suspected source.
