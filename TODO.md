# Insurequant TODO

> Last updated: 2026-06-16 · Stage: cross-stage
> Index: CLAUDE.md (5-stage; parser 2-lane since 2026-06-13) · Stage TODOs: TODO_<stage>.md

Pipeline organized as **downloader / parser / validation / publishing / designer** — each stage has its own prompt (`docs/agents/claude-agent-<stage>.md`), TODO (`TODO_<stage>.md`), and changelog (`docs/changelog_<stage>.md`). See `CLAUDE.md` for the full index. This root file carries cross-stage items + project-wide policy only.

## Status

Cross-stage focus (2026-06-12): K-ICS gate RED=227 all documented exceptions (19_market 223 + KR0049 4) pending validation registration; cross-stage CSM-waterfall 신한EZ 제외 + K-ICS 금리민감도 feature have only publishing/designer tails left; owner backlog digest dispatched to all 5 stage inboxes. Mid-long-term: duration-gap (MLG-1) and K-ICS 시장위험 분해 (MLG-2) blocked on owner decisions.

**Stage files:**

- **Downloader** (Stage 1): `TODO_downloader.md` + `docs/changelog_downloader.md` + `docs/agents/claude-agent-downloader.md`
- **Parser** (Stage 2, **2-lane since 2026-06-13**): `TODO_parser_kics.md` · `TODO_parser_ifrs17.md` + `docs/changelog_parser_{kics,ifrs17}.md` (pre-split frozen: `docs/changelog_parser.md`) + shared `docs/agents/claude-agent-parser.md` + domain `docs/domains/claude-agent-{kics,ifrs17}.md`
- **Validation** (Stage 3): `TODO_validation.md` + `docs/changelog_validation.md` + `docs/agents/claude-agent-validation.md`
- **Publishing** (Stage 4, **merged gathering + pushing**): `TODO_publishing.md` + `docs/changelog_publishing.md` + `docs/agents/claude-agent-publishing.md` (skeleton — created 2026-05-31)
- **Designer** (Stage 5, **new — HTML/CSS/responsive**): `TODO_designer.md` + `docs/changelog_designer.md` + `docs/agents/claude-agent-designer.md` (skeleton — created 2026-05-31)

Items previously here that have moved out:

- Downloader (F2 done, F7–F10, F14, MISC-BOND-*, MISC-IR-MERITZ, MISC-SEIBRO, decisions #5/#6) → `TODO_downloader.md`
- Parser (KICS-PARSER-SPLIT/REPARSE-Q4/KR0069/KR0097/RED-FIX2/RED-FIX3/SUB/POST/RATIO28/HIST/IMG + IFRS-A1~B5-KICS/B3-UNIFY/NORMALIZE/HIST/SEN-TABLE) → `TODO_parser_{kics,ifrs17}.md`
- Validation (KICS-VALIDATE, IFRS17-NB-RECONCILE) → `TODO_validation.md`
- Publishing (F4 v2, F13, INDEX-IFRS17-BUBBLE, INDEX-BUBBLE-V2, MISC-IR-PROTOTYPE, MISC-IR-NB-DENOM, IFRS17-CSM-BUBBLE, KICS-TIER1/2-UTIL, KICS-FORWARD-CAPITAL, KICS-HTML-SUB, IFRS17-HTML-DASH, F5/F6 data) → `TODO_publishing.md`
- Designer (MOB-KICS, MOB-IFRS17, VIS-DONUT, VIS-CHARTLEGEND, INDEX-C12, F1-HTML, F6-HTML, F17-PANEL3 HTML, M1/M2) → `TODO_designer.md`

**Reorg #2 (2026-05-30j)** — `data/assoc/` → `data/_derived/`; KIDI/DART → `FY####_Q#` 컨벤션 통일. **DART batch script refactor 잔여** → `TODO_downloader.md` REORG2-DART.

Session start: read this root file first, then the relevant stage's `TODO_<stage>.md`.

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## 🟠 data-contract gate (`validate_data_contract.py`) pending exceptions — 2026-06-20 (owner)

게이트 `python scripts/validate_data_contract.py` 라이브: **RED=4, 전부 tier2(보완자본 소진율) 동일 근본원인.** census 0(7분기 scope 적용)·as_of 0·cross_source 0·anomaly 0-RED. selftest 7/7.

**남은 4 RED = 단일 이슈("tier2 소진율 분자 정의 오류")가 4셀에 발현 — fix 불가, 발주됨:**
- `T2_UTIL_OVER_100_NO_EXEMPTION` × 3: 동양생명·KB손해·미래에셋생명 2026.1Q. proxy 경로가 item3(보완자본 총액)을 분자로 써서 **한도-제외 항목(다.(3) 해약환급금준비금 초과분/조정준비금)까지 포함** → >100% artifact (해설서 p102 마. 확인). 손fix 불가(한도-적용-전 보완자본이 표준 지급여력표에 없음).
- `T2_DENOM_NOT_SCR_HALF` × 1: 신한이지손해 2026.1Q. 분모 2.68억 = 정답 268억(SCR 536×50%)의 1/100 스케일 오파싱.
- **조치**: 분자를 DART "증권의 발행을 통한 자금조달"의 후순위채 발행 잔액으로 교체 → `inbox/parser/20260620T0238Z` (ifrs17 lane). 도넛 잠정 숨김 → `inbox/designer/20260620T0238Z`. ifrs17 데이터+wiring 완료 시 4건 일괄 해소 + CHECK4 전제 재검토. **push는 이 4건 해소 후.**
- 근거: 메모리 `reference_tier2_utilization_provenance`. 신규 글리치 아님 — 알려진 metric 결함의 정식 라우팅.
- 참고(eyeball 2026-06-20): tier2 외 신규 오류 없음. 저우선 확인거리 — 악사손해 2024.4Q 법인세 −1101(흑자인데 환입, 산수정합) 부호 소스확인 / forward_capital 2025.4Q 1분기 stale.

---

## 🔴 K-ICS gate documented exceptions — CURRENT (2026-06-14, parser)

> Supersedes the 2026-06-12 snapshot below. Since then: RED 227→**19** (대량 fitz 회수 + 코어/rule5
> 백필 + round3 K2/K3), AND validation **expanded the validator** (new `36_irr` IRR 41-46 rule + `19_market`
> cadence fix + `_market_tooling_fail` + `_parent_zero_child_nonzero`). The 2026-06-12 "19_market 223" list is
> mostly registered/recovered. Current gate state = **19 RED, ALL verified non-regression** (raw 페이지까지 검증). Characterization:

> **Update 2026-06-16 (round3 K1–K4, parser):** RED 21→**19**. K3 = 서울보증/카카오 orphan item35
> 제거(parent17=0인데 자식 비0 = 일반손해 대재해 오매핑, 3셀) + fill_subitems parent-gate 가드 추가 +
> validation 신설 `_parent_zero_child_nonzero` 게이트(parent-zero=0 확인). K2 = 예별손해(KR0004,
> 구MG) 2025.4Q docling+추출(코어28·하위29-35·시장36-40 적재; **자본잠식 -8.24%** 실값). 카카오
> 2023.3Q 19_market = 소스표 실재 → 36/38 적재로 **GREEN 해소**(cadence-SKIP 불필요, 아래 정정).
> K4(sensitivity 적용후)·K1(designer)은 게이트 무관.

> **Update 2026-07-03 (owner 워크스루 3건, parser/kics):** owner가 사이트에서 눈으로 발견한 kics 3건 처리.
> (1) **KR0083 푸본현대 2025.2Q** — FY2025_Q2 슬롯에 **엉뚱한 회사(KR0075 비엔피파리바카디프) PDF**가 적재돼
>   있었음(자기정합 데이터라 산술 게이트 GREEN 통과 = false-green). items 1-28을 진짜 푸본현대 값(25.3Q MD의
>   25.2Q 컬럼)으로 교정(지급여력비율 318.25%→**−10.13%**, 자본잠식 실값). sub-risk 29-46은 정본 PDF 부재로
>   삭제 → **downloader refetch 발주**(`inbox/downloader/20260703T1250Z...`). **잔여 RED = KR0083 2025.2Q
>   `19_market` 1건**(item19=8559 공시·36-40 결측, 정본 PDF 재취득 대기) = **documented exception, downloader
>   완료 시 해소**. (2) **KR0050 하나손보** 25.3Q #34 사업비 405.11·#35 대재해 44.81 backfill(docling 표뭉갬
>   복구) + 2024.2Q #35 대재해 0.04→40.86(콤마→마침표 오독). (3) **KR0076 아이엠라이프 26.1Q** sub 적용후
>   4개 채움(장수 68.37·해지 1249.87·사업비 433.16·대재해 36.95; 사망/장해질병=비대상, 장기재물=원천 N/A).
>   → 게이트 사각 2건(cross-quarter plausibility·parent-present-child-absent census) validation 발주.

**✅ Structural non-disclosure — documented exceptions (parser-confirmed; image/scan/micro, 추출 불가):**
- **36_irr × 12** (item36 공시인데 순자산가치 6시나리오표 추출불가):
  - KR0010 KB손해 2023.4Q·2024.2Q·2025.4Q — 금리위험액 현황표가 **full-page 이미지**(p75-76 imgs=1,text=0; "금리는 내부모형" 주석). owner OCR.
  - KR0051 신한이지 2023.4Q·2024.2Q·2024.4Q — micro-insurer, 순자산가치 **억원-coarse 정수**라 derive ±99% 불안정(원천 한계).
  - **KR0004 예별손해(구MG) 2023.2Q·2023.4Q·2024.2Q·2024.4Q·2025.2Q·2025.4Q (짝수 6분기)** — item36(금리위험액) 공시이나 **충격시나리오별 순자산가치(41-46) 표 미공시**(소형 부실사; MD 전체에 평균회귀/금리상승 라벨 부재, fill_market_irr 회수 0). IRR detail 결측 = legit-absent.
- **19_market × 7** (item19 공시인데 36-40 분해 추출불가):
  - KR0005 흥국화재 2024.4Q·KR0071 흥국생명 2024.4Q — raw에 시장위험 분해표 NO-HEADER(이미지/미공시).
  - KR0010 KB손해 2024.4Q·2025.2Q — 금리위험액 이미지(주식/부동산/외환만 텍스트, 5종 reconcile 불가).
  - KR0068 한화생명 2023.4Q·2025.2Q — 금리위험액 현황 표 본문 이미지(헤더만 텍스트; 2025.2Q diff=60,815 = 금리 결측 탓).
  - KR0080 AIA 2025.4Q — scan-only(아래 documented).
  - **KR0083 푸본현대 2025.2Q (TEMPORARY, wrong-PDF)** — FY2025_Q2 PDF가 KR0075(BNP파리바카디프)와 sha256 동일(오파일). 코어 1-28은 25.3Q MD 직전분기컬럼서 교정(318%→−10.13), subs 36-40은 정본 PDF 대기 → downloader `20260703T1250Z`. **정본 재파싱 시 해소(구조적 미공시 아님).** 상세=위 2026-07-03 owner 워크스루 (1).
- **rule 2 × 1**: KR0080 AIA 2025.1Q (diff=−789) — scan-only(아래 documented).
- **rule 1 × 1**: KR0004 예별손해 2024.2Q (item1 3,572 ≠ item2 498 + item3 3,085 = 3,583, diff 11) — **소스 충실**(MD L268-270 그대로). 부실사 보완자본 한도초과/억원 반올림으로 지급여력금액이 단순합과 불일치 = 공시 자체 특성, 파싱오류 아님. 인접 분기는 diff<tol이라 미발화.
- **rule 8_life × 1**: KR0079 미래에셋 2023.2Q — scan-only. **8_life는 SKIP=게이트 비차단**.
- **2023.2Q 백필 잔여 (2026-06-15, docling 부활)**:
  - KR0087 동양생명 2023.2Q — 코어표 **이미지 전용**(텍스트 부재) → scan-only(KR0079/0080/0087 동류), census 갭.
  - KR1098 카카오 2023.2Q rule7 + 19_market — **micro-insurer**(item19=5억·item14=15억·천원 스케일): 비율 derive가
    초소형 분모 반올림으로 62%p 어긋남(공시 item27=2155.62 정확) + 36-40 nn=2 → micro artifact(신한이지류). documented.
- **census 결손 → owner OCR (2026-06-15, publishing `20260614T2313Z` 처리, docling 부활)**:
  - **KR0097 하나생명 2024.2Q** — 그 분기 공시본이 **이미지 PDF**(14.7MB; regex·pdfplumber·fitz 3중 확인 코어표
    텍스트 부재). 나머지 12분기 텍스트 정상. owner OCR/gold (downloader 텍스트본 재취득 가능성 확인).
  - **KR1098 카카오 2023.4Q·2024.2Q·2024.3Q·2024.4Q** — 이미지 PDF(동일 3중 확인). 2025.2Q/3Q는 텍스트로 적재됨
    = 비공시 아님, 이미지라 OCR뿐. **expected-absent 화이트리스트 아님.**
  - 카카오 2025.3Q rule6 = micro 반올림 artifact(documented).
  - ✅ **적재 완료**: 카카오 2025.2Q(28/28)·2025.3Q(27/28) 코어 + 2025.2Q 시장위험.
- **서울보증(KR0150) 과거 interim = expected-absent (census 화이트리스트, 2026-06-15)**:
  2023.1Q/2Q/3Q · 2024.1Q/2Q/3Q · 2025.2Q/3Q **= refetch 불가 구조적 gap**. 서울보증 자체 공시실(sgic.co.kr)은
  **연간(Q4)+최근분기만** 노출, 과거 Q1-3 PDF 롤오프(서버 부재). 미상장이라 DART도 없음. downloader가
  2026-06-01 `SGI_QUARTERLY_STRUCTURAL`로 등록(audit_all_periods.py:39-43) + 2026-06-15 재확인 resolved.
  present = 2023.4Q·2024.4Q·2025.1Q·2025.4Q·2026.1Q(연간+최근) 정확. **K-ICS census도 이 8분기 결손은 무시.**

**✅ INTERNAL_MODEL_36IRR_EXEMPT — owner 승인 완료 (2026-06-14, "한화 선례 동형"):**
- **36_irr × 5**: KR0073 교보생명 2025.2Q · KR0094 신한라이프 2024.2Q·2024.4Q·2025.2Q·2025.4Q. **내부모형사** —
  순자산가치는 정확 추출되나 표준 derive식(R=충격전−시나리오)이 공시 금리위험액과 안 맞음. 회사가 **시나리오별
  금리위험액을 직접 공시**하고 그 값을 같은 식에 넣으면 공시총액과 **정확히 일치**(KR0094 2025.4Q=578,999 검증).
  한화생명 내부모형 선례 동형. **owner 승인** → documented 예외. validation이 `kics_json_rules.py`에
  `INTERNAL_MODEL_36IRR_EXEMPT` 등록(RED→SKIP) 요청 발송(`inbox/validation/`).

**✅ RESOLVED 2026-06-16 (카카오 2023.3Q 19_market — cadence-SKIP 아니었음):**
- 이전엔 "odd-Q NO-HEADER → validation cadence SKIP"으로 분류했으나 **틀렸다**(validation 0130Z 정정).
  `data/disclosure/FY2023_Q3/parsed/KR1098_…amended.md` L177-186에 시장위험 분해표 **실재**(시장 248/금리 15/
  부동산 244, 백만원). 파서가 item36(0.15)·item38(2.44) 적재 → 19_market **GREEN**. cadence-SKIP 불필요.
  (단 36_irr은 41-46 미공시라 별도 — 카카오 2023.3Q는 36_irr RED 아님: item36 near-0라 미발화.)

**요약 (2026-06-16, 예별 13분기 백필 후)**: **24 RED** = 구조적(documented: 36_irr 12·19_market 7·rule1 1·
rule2 1·8_life 1·rule6 1·rule7 1). +5 net = 예별 KR0004 36_irr×5(IRR 미공시) + rule1×1(예별 2024.2Q 한도/반올림),
−1 카카오 2023.3Q→2Q 19_market GREEN. 내부모형 0(KR0073·KR0094×4 = validation INTERNAL_MODEL_36IRR_EXEMPT
SKIP 등록). census MISSING 6(동양/하나/카카오 image cells, documented). **전부 documented → CLAUDE.md 게이트 rule
충족.** push는 owner 권한 — parser self-approve 안 함.

**✅ 항목4/12/13(Ⅰ.건전성감독기준 순자산·Ⅱ.불인정항목·Ⅲ.보완자본재분류) 값_적용후 결측 — documented exception (2026-07-21, owner+designer/parser)**

- **대상**: 가.지급여력금액(항목1)의 세부 3항목(항목4/12/13). 값_적용후가 raw 정기경영공시 PDF에 **애초에 별도 컬럼으로 존재하지 않음**(공통적용 경과조치 표에는 항목1·2·3·14만 있고 4/12/13 행 자체가 없음 — 4개사 raw 전문 grep으로 확인, `inbox/_resolved/20260712T0704Z__designer__MULTI_2026.1Q__capital_breakdown_after_missing.md`). 2026.1Q 기준 39개사 중 21개사(DB생명·IBK연금·NH농협손해·교보라이프플래닛·교보생명·농협생명·롯데손해·아이엠라이프·악사손해·에이비엘생명·예별손해·처브라이프·케이디비생명·푸본현대생명·하나생명·한화생명·한화손해·흥국생명·흥국화재 등)에서 3개 항목 전부 결측.
- **왜 backfill 불가**: 나머지 18개사는 `값=값_적용후`로 채워져 있으나, 이건 실제 공시가 아니라 `scripts/backfill_post_transition_when_not_applied.py`가 항목1/14/27(총액/기준금액/비율) 일치를 근거로 **미러링한 추정값**. 이 스크립트 자체 docstring에 **2026-07-16 KNOWN BUG**로 명시: 항목1/14/27이 일치해도 항목2/3(기본자본/보완자본) tier 배분은 공통 TFI 경과조치로 별도로 움직일 수 있어(**기본자본비율이 5~15%p까지 이동 가능**), 이 방식으로 **KB라이프생명 2024.2Q·동양생명 2024.1Q 항목12/13이 실제로 오염**됐다가 `fix_20260716_revert_wrong_item1213_mirror.py`로 되돌린 전례 있음.
- **owner 재확인 사례 (2026-07-21)**: **KR1000 코리안리재보험 2024.4Q** — 항목1(41,813→41,812.79)·14(21,812=21,812)·27(191.697%=191.697%)는 사실상 동일한데, **항목2 기본자본 32,860→33,950(+1,090)·항목3 보완자본 8,953→7,863(−1,090)·항목28 기본자본비율 150.65%→155.65%(+5.0%p)**로 정확히 위 KNOWN BUG 패턴 재현 확인. 이 분기는 실제로 항목1 diff(0.21)가 스크립트 tolerance(0.01)를 넘어 안전-미러링 대상에서 이미 제외돼 있었음(값_적용후 결측 상태 유지) — **정상 동작 확인**, 버그 아님.
- **결론**: 항목4/12/13 값_적용후는 raw에 근거가 없고, 안전한 backfill 방법도 없음(항목1/14/27만으로는 항목2/3/4/12/13의 tier 재배분을 보증 못함). **owner 승인 하에 fix 보류 — K-ICS.html은 이 결측을 "미공시"로 명시 표시**(`NO_POST_TRANSITION_DISCLOSURE = {4,12,13}`, designer 2026-07-12 배선). 18개사의 기존 미러링값(항목1/14/27만 근거)도 코리안리와 같은 패턴으로 오염됐을 가능성 있음 — **후속 감사 필요**(범위 밖, 별도 티켓 권장).

---

## 🔴 K-ICS gate documented exceptions (2026-06-12, parser) — SUPERSEDED, 이력용

Gate run 2026-06-12: RED=227 = **19_market 223 + KR0049 2026.1Q 4** (rules 2/4/5/6). All documented:

- **rule 19_market × 223 (28 companies)** — item19(시장위험액) disclosed but 36-40 breakdown absent
  **in the source PDFs themselves** (structural non-disclosure). Parser exhausted recovery:
  `fill_market_subs_from_pdf.py` (fitz + M-matrix reconcile<2%) full re-run = no-pdf 0, new rows 0.
  Full (company,quarter) list: `artifacts/kics_validation/market_breakdown_red_census_20260612.md`.
  → **validation**: register in `MARKET_BREAKDOWN_EXEMPT` (kics_json_rules.py) after cross-check —
  inbox `20260612T1100Z__parser__MULTI_ALL__2026q1_loaded_and_19market_exempt_request.md`.
  3 reconcile-fail cells kept OUT of exempt (table exists, gate rejected): KR0002 2024.2Q,
  KR0009 2023.3Q, KR0051 2023.1Q.
- **KR0049 악사손해 2026.1Q rules 2/4/5/6 (4)** — K-ICS detail page (p16) is a full-page image in
  the PDF; only core 5 items recoverable from text (총괄 + 공통적용 tables). Needs owner gold or OCR.
- **Scan-only PDFs (coverage census MISSING, not rule REDs)**: KR0079 미래에셋 (all quarters),
  KR0080 AIA (2024.4Q-2026.1Q; 2023.1Q-2024.3Q loaded), KR0087 동양 (2026.1Q). Both own-site and
  협회 copies are the same scans. → owner xlsx gold path (KB KR0010 precedent).

---

## 🚧 CROSS-STAGE — CSM waterfall 신한EZ 제외 후속 (owner xlsx 검토 2026-06-10, 보정 06-11)

~~3사 제외~~ → **하나손해(KR0050)·하나생명(KR0097)은 복원**(자사 감사보고서 별도 변동표 실재 — 경영서술 수치와
정확 일치 검증, owner 재지시 2026-06-11). **신한이지(KR0051)만 제외 유지**: 감사보고서 변동표가 천원 단위인데
백만원 오인(×1000 인플레) + PAA 중심사로 일반모형 CSM ~2억 = 워터폴 무의미. override `data/dart/viz/csm_manual_overrides.json`.

- [ ] **designer**: CSM 워터폴/배수 HTML에서 **신한EZ손해**를 'CSM 분리공시 미제공(PAA 중심)' 표기 또는 목록 제외.
- [ ] **publishing**: override 적용은 build_root_masters.py 훅 자동 — 인지만.

---

## 🚧 CROSS-STAGE — K-ICS 금리민감도 신규 feature (2026-06-10 발주 → 06-12 publishing만 잔여)

경영공시 `6-8. 위험 민감도` → 금리민감도 표(경과조치 × measure × ±50/±100bp)를 신규 루트 마스터 `kics_rate_sensitivity.json`으로. 38사 서베이 완료, 스펙 정본 `docs/agents/kics-rate-sensitivity-spec.md`.

- [x] parser: 추출 스크립트 + 마스터(435행)/diag — RS1·RS2 자기검증 통과 (2026-06-10)
- [x] validation: RS1–RS4 룰 구현, 게이트 RED=0 (consolidate_inbox 핸들러 배선만 후속 잔여) (2026-06-10)
- [ ] **publishing: 커밋 번들 추천 + master xlsx 재생성** — inbox `20260612T0900Z__owner__ALL__backlog_digest.md` #1
- [x] designer: K-ICS.html 민감도 패널 (F-SENS-PANEL, 커버리지 29/30) (2026-06-11)

---

## 📬 2026-06-12 — 전 스테이지 backlog digest 발송 (owner 전수 점검)

5개 스테이지 inbox에 `20260612T0900Z__owner__ALL__backlog_digest.md` 발송 (publishing/designer inbox 신설,
`inbox/README.md` layout + route `backlog` 추가). 각 스테이지는 다음 호출 시 자기 다이제스트 드레인.

---

## 중장기 목표 (Mid-long-term goals) — 신규 마스터 테이블 (cross-stage)

(2026-06-06 owner 제안. 착수 전 단계 — 소스 위치만 슥 확인. 우선순위/일정 미정.)

### MLG-1. 듀레이션갭 (Duration Gap) 지표 마스터
- **목표**: 자산·부채 듀레이션 및 듀레이션갭(금리리스크 ALM) 전사·전분기 마스터 테이블.
- **소스 확인 결과**: 정기경영공시 MD(`data/disclosure/FY*/parsed/*.md`)에 "듀레이션" 단어 **0회**(삼성화재/삼성생명/DB 확인) → 표준 경영공시엔 없음. **소스 추가 조사 필요**:
  - 1순위 후보: DART 사업보고서 주석의 **금리위험 민감도 / 자산·부채 듀레이션** 표 (사별 상이, K-ICS 금리위험액 산출 부속).
  - 2순위: 사별 IR 자료 / K-ICS 공시 부속서.
- **다음 스텝(대략)**: (a) DART 사업보고서 1~2개사(삼성화재·한화생명) 금리위험 주석에서 듀레이션 표 존재 확인 → (b) 있으면 parser 시그니처 추가, 없으면 IR 소스로 전환. PL/CSM 마스터와 동일 8-field 스키마 재사용.
- **[조사완료 2026-06-07 야간]** DART 본문(한화생명/삼성생명 주석 50)에 **듀레이션갭 서술 + 만기사다리(16버킷) + 100bp 금리민감도(손익/OCI)** 존재하나 **자산/부채 듀레이션 숫자·갭 자체는 없음**(만기+할인곡선 유도 필요). 손보(삼성화재/DB)는 sparse. → **owner 결정 필요**: (i) 100bp 민감도만 추출(직접 가능), (ii) 듀레이션 유도식 정의(만기가중/할인). 다세션 작업. 상세 → `changelog_parser.md` (j).

### MLG-2. K-ICS 요구자본 세부 도해 (시장위험액→금리위험 / 해지위험액 세부)
- **목표**: 지급여력기준금액 중 **시장위험액 하위(금리/주식/부동산/외환/자산집중)**, **해지위험액 세부**를 분해한 마스터/도해.
- **소스 확인 결과**: `kics_disclosure.json`은 top-level만 캡처(`3. 시장위험액`, `1-5. 해지위험액` 등). **하위 분해 미캡처**. 단 경영공시 MD(`data/disclosure`)에 **"금리위험"·"주식위험" 텍스트 존재**(삼성화재·DB·삼성생명 확인) → **기존 데이터에서 parser 확장으로 추출 가능 (답지 불요)**.
- **다음 스텝(대략)**: (a) K-ICS 요구자본 detail 섹션 표 확인(시장위험액 하위행: 금리/주식/부동산/외환/자산집중) → (b) 기존 K-ICS parser에 하위 항목번호(예 `3-1` 금리위험…) 추가 — 코리안리 `2-1` 시리즈처럼 문자 항목번호 패턴 재사용 → (c) validation gate에 합산검증(Σ하위 = 시장위험액) 추가.
- **[조사완료 2026-06-07 야간]** `fill_subitems_to_disclosure.py`(생명장기 1-1~1-7 파서)가 템플릿이나, 시장위험은 **통합 ①시장위험액 현황 표 부재** + 하위가 사별·위험별 **이질 표**(금리=충격전후 shock표 → 위험액 *유도* 필요·모호, 주식=헤더 embed, 부동산=합계행). clean disclosed 총액 사별 불일치(삼성화재 금리·주식만, 삼성생명 금리만, DB손해 전무). → **PL-Tier2급 사별 핸들러 다수 + 금리위험액 유도규칙 owner 결정 필요.** R11(Σ=시장위험액)은 금리 확정 후. 다세션. 상세 → `changelog_parser.md` (j).

---

## 🔀 Cross-stage follow-ups (multi-stage; detail in stage files)

| # | Task | Stages involved | Detail location |
|---|------|-----------------|-----------------|
| F12 | K-ICS 시장위험 하위위험액 전체 파싱 + 분산효과 validation | parser + validation | `TODO_parser.md` F12 + `TODO_validation.md` V3 |
| F17 | 당기순이익 분해 (Tier1 전사 + Tier2 손보 LOB) | parser + publishing (+ designer for Tier2 panel) | `TODO_parser.md` F17 (body) + `TODO_publishing.md` F17 viz + `TODO_designer.md` F17 Tier2 |
| F18 | IR factsheet 정형화 + DART↔IR cross-validation | parser + validation + publishing | `TODO_parser.md` F18 + `TODO_validation.md` V1 + `TODO_publishing.md` F18 viz |
| F13 | 재보험 영업 지표 세트 | downloader (F8) + parser + publishing | `TODO_downloader.md` F8 + `TODO_publishing.md` F13 |

## 📋 Policy / User decisions (cross-stage)

| # | Decision | Date |
|---|----------|------|
| 1 | K-ICS skip cohort: KR0029 AIG, KR0150 SGI permanent skip. KR0051 / KR0074 partial-coverage by design | 2026-05-24 |
| 2 | Meritz IR source: Meritz Financial Group factsheet xlsx (replaces Meritz Hwajae standalone). AIG IR: skip low-priority | 2026-05-24 |
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료**. IR PDF for 6 cos; assoc crawl (KIDI/KLIA/KNIA) for 23-co computed multiple | 2026-05-24 |
| 4 | First HTML viz: CSM Movement Waterfall (IFRS17 A1 23-co) | 2026-05-24 |
| 5 | API keys: repo root `.env` only (gitignored). Never commit/log key values | 2026-05-24 → `TODO_downloader.md` D5 |
| 6 | Bond Call rule: issue + 5y for ALL bonds. Past 5y = assume `called` | 2026-05-24 → `TODO_downloader.md` D6 |
| 7 | Pushing: subagent **reports + recommends only**. Human runs `git push` | 2026-05-30 |
| 8 | DART attachments (별첨/감사보고서 zip): **don't fetch**. Body XML has all IFRS17 disclosures | 2026-05-30 → `TODO_downloader.md` DL-NOATTACH |

## 🌐 Universe (cross-stage)

- **K-ICS**: 38 insurers (`kics_disclosure.json` `원수사명`); skip cohort KR0029/KR0150
- **IFRS17**: 28 insurers (`src/ifrs17/universe.py`) — 23 listed + 5 foreign-affiliate life via audit reports (F11, `AUDIT_REPORT_ANNUAL`, annual-only). Historical 13Q cohort = 23 listed.
- **K-ICS↔IFRS17 mismatch**: AIA (에이아이에이생명보험) is in IFRS17 universe but NOT in `kics_disclosure.json`. Cohort joins must handle this.

## ✅ Done — cross-stage anchors

| ID | Task | Notes |
|----|------|-------|
| ~~F1~~ | index.html → IFRS17 cross-nav | `fcdd544`. ECharts on('click') → URL param + auto-select. Data hook = publishing; HTML = designer |
| ~~F3~~ | CSM 상각 schedule 전수 조사 | `4b06492`. 19/24 → 22/24 ok |
| ~~F5~~ | No-bond insurer forward sim 추가 | `b02e24d`. 24 → 37 cohort |
| ~~F6~~ | CSM 상각 schedule yearly granularity | 2026-05-28. 16 yearly / 6 coarse / 2 no-data |
| ~~F11~~ | 외국계 생보 5사 IFRS17 추가 | DONE 2026-05-29. 23→28 (생보 13→18). corp_codes: 라이나 00504232 / 메트라이프 00171104 / AIA 01295517 / 하나생명 00187123 / 처브 00203102. universe.py `AUDIT_REPORT_ANNUAL`. NOTE: AIA not in kics_disclosure.json |
| ~~IFRS-Q~~ | Open Q1-Q9 | done. All 9 confirmed |

## 📚 Long-term / roadmap

> 📈 **중장기 제품·수익화·전략 로드맵 → `docs/roadmap.md`** (2026-05-26 신설)

Active long-term tracks now live in their respective stage TODOs:

- **IFRS17 bubble + market map evolution** → `TODO_publishing.md` (data) + `TODO_designer.md` (HTML)
- **Forward solvency simulation** → `TODO_publishing.md` (KICS-FORWARD-CAPITAL done v3 archive)
- **Roadmap §1A-2 priority 6 추가지표** (요구자본 위험액 분해 / RA / P&L 보험·투자 분해 / 출재율 / 유지율 / 운용자산이익률) → distributed across parser + publishing
- **Roadmap §1E 규제 뉴스 피드** → `TODO_downloader.md` F14

## 🧾 Meta

- Encoding rule: `CLAUDE.md` "Document/TODO Encoding Rule" added 2026-05-24
- .gitignore: `data/dart/raw/`, `data/dart/reports/` excluded
- 2026-05-25 doc trim: changelog 124KB→11KB (latest 5 entries detailed + historical archive 1-liners)
- git: initialized + pushed to github.com/solvencyk/insurequant (main). GitHub Pages → solvencyk.github.io/insurequant
- 2026-05-26: `docs/roadmap.md` 신설
- 2026-05-28 HTML single-source refactor (P1+P4): templates/*.html 4개 삭제. ⚠️ 데이터 JSON 중복 남음 (P2)
- 2026-05-28 모바일 반응형 M1/M2 적용
- 2026-05-28 IFRS17 패널 정리: 파생 KPI 카드 + BS 스냅샷 제거 → `docs/archived_metrics.md`
- 2026-05-30j Reorg #2: `data/assoc` → `data/_derived`, KIDI/DART → `FY####_Q#`. DART batch script refactor 잔여 → `TODO_downloader.md`
- 2026-05-30k 5-stage workflow split (downloader/parser/validation/gathering/pushing 초안)
- 2026-05-31 Stage 2/3/4/5 split fully populated: parser/validation TODO+changelog (오전), publishing(=gathering+pushing 머지)+designer(MOB/VIS HTML 별도 stage) TODO+changelog (오후). Root TODO is now genuinely cross-stage only

## ✓ MVP checklist (IFRS17)

- [x] A1 A2 A3 A4 B1 B5 all 23/23 MVP (B5 K-ICS primary ingest done FY2025_Q4)

## 🎯 Next priorities (cross-stage)

1. **KICS-IMG manual OCR** (user-owned): KR0010 KB Sonhae rule 2 ×2 — only remaining RED. Parser policy → `TODO_parser.md`; validation gate exception → `TODO_validation.md` V6
2. **F17 decision**: 9/11 손보 Tier2 LOB commit vs debug 삼성·DB vs IR-clean only. Parser detail → `TODO_parser.md`. Tier2 panel rendering → `TODO_designer.md` after decision
3. **F18 activation**: parser delivers IR JSON → V1 validation rules activate → publishing assembles cross-source viz
4. **REORG2-DART**: 3 batch scripts canonical-layout refactor → `TODO_downloader.md`
5. **Stage prompts 마무리**: parser / publishing / designer prompts still skeleton (TBD bodies); validation + downloader prompts are owner-authored complete
