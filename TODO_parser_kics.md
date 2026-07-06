# Insurequant Parser TODO — K-ICS lane (Stage 2)

> Last updated: 2026-07-07 · Stage 2/5 — parser (kics lane)
> Prompt: docs/agents/claude-agent-parser.md · Changelog: docs/changelog_parser_kics.md (pre-split: docs/changelog_parser.md)

Stage 2 — **parser, K-ICS lane**: solvency disclosure extraction. Source = Docling MD; output = `kics_disclosure.json`; validators = `validate_kics_disclosure.py` / RS1–4 / market census. The IFRS17 lane (CSM/PL extraction off DART XML) lives in `TODO_parser_ifrs17.md` and runs as a separate session.

Session start: read this file + `docs/agents/claude-agent-parser.md` + `docs/domains/claude-agent-kics.md`. English where Korean encoding is fragile (see `CLAUDE.md`).

## Status

**2026-07-07 update (경과조치 적용후 — 정본 18사 확정 후 잔여 90셀, 상세는 P1 TRANS-18 항목):** owner가 FSS 2023-03-20
보도자료 붙임-1(`trend20230320_3.pdf` p6)을 정본으로 제공 — **선택 경과조치 실제 적용사 = 18개사**로 확정(이전
owner 22-seed와 이번 세션의 "코리안리·메리츠·한화생명·신한라이프 = 정당동일" 추정이 결과적으로 모두 옳았음, 정본과
교차일치). 게이트 `validate_kics_disclosure.py`의 `_TRANSITION_APPLIERS`가 18사로 정정되고 item28까지 검사 +
AMT_MISMATCH(비율만 패치·금액후 미수정) 룰 추가. 잔여 RED 139→**90**(라이브 재추출 반영 후). **케이디비생명·
하나생명 2개사(47셀) = 완전 미착수**, 나머지는 AMT_MISMATCH 잔재/일부 분기 결측. 상세는 P1.

K-ICS lane is **mature**: K-ICS disclosure + rate-sensitivity + market-risk-subitem masters all built (root `kics_disclosure.json` assembled, xlsx regenerated). 2026.1Q loaded for 36/39 companies (changelog (s)). Gate posture: `validate_kics_disclosure.py` reached RED=0 on 2026-06-11 (r); the 2026-06-12 (s) reload left RED=227 — almost all is `19_market` structural non-disclosure (EXEMPT registration requested via inbox) plus 악사 26.1Q image-only cells. Remaining work is residual coverage backfill (시장위험 하위, 경과조치 적용후, dedup) + a few escalated owner gold-scan decisions, not core extractor rewrites.

**2026-06-14 update (market 36-46 residual — fitz root-cause fix, changelog top entry):** owner live-QA "2025.4Q
36-40 전 손보 누락" = **stale 전제**(현 census 2025.4Q 36-40 최다 적재). round-1(localized+parsed MD)은 +10행에
RED 무변동이라 "파서 RED=0"으로 **오판**했으나, owner 지적으로 재조사 → **ROOT CAUSE = 시장위험 localizer의
pdfplumber 백엔드가 일부 PDF에서 EOF로 죽어 무음 스킵**(DB손해·NH는 손상 아님, fitz로 정상). **fitz 재localize
(find_tables 구조표)로 21셀 재추출 → +45행, RED 52→42, 8셀 clear**: DB손해 24.4Q·NH 25.4Q·한화 24.2Q [19_market],
하나·ABL·BNP×2·IBK [36_irr]. **잔여 42 RED**: KB손해 4분기·한화 23.4Q/25.2Q 금리위험액 = full-page 이미지(owner
OCR) · 신한라이프 4·교보 내부모형(validation INTERNAL_MODEL 면제) · 신한이지 micro 단위 · 흥국 image · 삼성 odd-Q
MD불일치 · rule5(13)·기타 비-시장. → **root-cause fix = LOCALIZER-FITZ(P1 위)** 적용하면 향후 분기 무음스킵 방지.

---

## 🔴 Open — P1

### TRANS-18 — 경과조치 적용후(item27/28) 정본 18사 확정, 잔여 90셀 (2026-07-07)

owner 20260703 systemic 발주 → 4라운드 검증 왕복(inbox `20260703T1138Z`→`20260705T1042Z`→`20260705T2150Z`
FAKE반려→`20260706T0434Z` 2차반려→`20260706T0502Z` **정본 확정**, 전부 `inbox/_resolved/` 또는 최신 open)
끝에 **정본 = FSS 2023-03-20 보도자료 붙임-1**로 선택(elective) 경과조치 실제 적용사 **18개사** 확정:
- 생보 12: 에이비엘(KR0070)·흥국생명(0071)·**케이디비생명(0072)**·교보생명(0073)·아이엠라이프구DGB(0076)·
  DB생명(0082)·푸본현대(0083)·**하나생명(0097)**·처브라이프(0100)·교보라이프플래닛(1010)·IBK연금(1011)·농협생명(0104)
- 손보 6: 악사손해(0049)·한화손해(0002)·롯데손해(0003)·예별손해구MG(0004)·흥국화재(0005)·NH농협손해(0032)
- **나머지 전 회사(코리안리·메리츠화재·삼성생명·한화생명·신한라이프·KB라이프·동양생명 등) = 공통(TFI)
  경과조치만 → 적용후=적용전이 정상, 건드리지 말 것.** (이번 세션 23개 raw-검증 에이전트가 이 결론에
  정본과 무관하게 독립적으로 도달 — 교차검증됨.)

**이번 세션 처리분**: 18사 중 raw 직접 재추출로 NH농협손해(9Q 전체)·에이비엘(8Q, 도중 100배 단위버그 발견/수정)·
예별손해(6Q)·DB생명(4Q, 100배 단위버그)·흥국화재(부분)·흥국생명(부분, 2024.4Q는 raw자체가 사업보고서라
downloader 이슈)·교보생명(7Q)·농협생명(1Q, 나머지 6Q는 병행 세션이 이미 커밋)·푸본현대/처브/교보라플(각1Q,
꼬리) 반영. **동시에 병행 진행 중이던 다른 세션이 커밋 `98deca2·2d5b6c3·789bc9f·01c7b4f·d449d91·69f16c4`로
흥국화재·교보생명·흥국생명·아이엠라이프·한화손해·롯데손해·농협생명·악사손해 총 54개분기 별도 수정** — 두
작업 합쳐 게이트 139→**90**.

**⚠️ 4번째 100배 단위버그 패턴 확인**: 서브에이전트가 raw 표(백만원)를 그대로 kics_disclosure.json(억원)에
넣는 실수 반복 발생(KR0032·KR0070·KR0082, 이번에 apply 스크립트에 자동 sanity-check 추가해 방지). **향후
에이전트 발주 시 "raw 백만원→/100 억원 변환, 결과가 적용전과 자릿수 비슷한지 확인" 문구 필수 포함.**

**잔여 90셀(완전 미해결)**:
- [ ] **케이디비생명(KR0072) 24셀 + 하나생명(KR0097) 23셀 = 완전 미착수**(정본 확정으로 신규 발견,
  아무도 raw를 본 적 없음). 최우선 착수 대상.
- [ ] **AMT_MISMATCH 잔재 9건** — item27은 이미 패치돼 margin은 넘겼는데 item1/item14 적용후와
  항등식이 안 맞음(비율만 손대고 금액 후속수정 누락): 한화손해(0002)·롯데손해(0003)·NH농협(0032 2025.4Q·
  2026.1Q)·흥국화재(0005 2026.1Q)·흥국생명(0071)·DB생명(0082). item1/14 후를 raw로 마저 채우면 자동 해소.
- [ ] **예별손해(KR0004) 11셀 잔존 RED** — 이번 세션이 raw로 검증한 값(예: 2024.4Q 3.45→4.13)이 실제로는
  맞는데, 게이트의 고정 마진(`_TRANS_EFFECT_MARGIN=1.0`)이 자본잠식/소형사의 **작지만 진짜인** 개선폭을
  COPY로 오탐. validation에 마진 로직 재검토 요청(파서가 임의로 게이트 완화 불가). 데이터 자체는 정확.
- [ ] **KR0005/KR0071 2024.4Q raw 자체 오염** — 정기경영공시서가 아닌 사업보고서/감사보고서 첨부가 잘못
  수집됨(경과조치 섹션 부재). downloader 재수집 발주 필요.
- [ ] **rule_8_post RED 4건 신규 노출**(기존 1→4) — item2_적용후=None으로 정직하게 남긴 셀(에이비엘
  2025.3Q·흥국생명 2024.4Q·푸본현대 2023.1Q)에서 검증기의 기존 폴백버그(None→적용전값 조용 대체)가
  더 많이 발화. validation 로직 수정 필요(파서 소관 아님, 이미 inbox에 flagged).

### LOCALIZER-FITZ — 시장위험 localizer pdfplumber 무음실패 → fitz fallback (root-cause, 2026-06-14)

`extract_market_section_pages.py`(+ `recover_market_subs_parallel.py`)가 **pdfplumber**로 PDF를 여는데, 일부
파일에서 `PdfminerException: Unexpected EOF`로 **열기 자체가 실패** → `market_pages_nonok.json` ERR로 빠지고
localized page 미생성 → 추출 워크플로우가 그 (사,분기)를 통째로 건너뜀 = **무음 커버리지 사각**. 확인된 피해:
DB손해 2024.4Q·NH농협손해 2025.4Q(둘 다 fitz로는 정상, 표 텍스트 존재) — owner의 NH 36-40 누락 신고 진짜 원인.
- [x] **DONE 2026-06-14**: `extract_market_section_pages.py` `localize_and_dump`에 try(pdfplumber)→except→
  `_localize_fitz`(fitz get_text + find_tables) fallback 추가. EOF-PDF(DB손해 24.4Q·NH 25.4Q)가 ERR→OK 전환
  확인, pdfplumber 정상경로 회귀 OK, `pytest tests/unit/` 110 passed. `_keep_table_rows`/`_emit_localized` 공통화.
- [ ] (validation 측) ERR/NO_SIGNAL을 'TOOLING_FAIL' census 버킷으로 분리 — validation이 localizer 안착 후
  wire-up 예정(inbox/validation `..._exempt_register.md` 합의). parser는 fitz-fallback 완료로 선결조건 해소.

### GOLD-CHAIN — review-loop 영속화 정합 + backfill 스크립트 체인 편입 (2026-06-20, inbox 0811Z)

owner xlsx fill·내 backfill이 rebuild에서 살아남는지 점검 → 2대 사각 (메모리 [[reference_kics_gold_reviewloop]]).
- [x] **DONE 2026-06-20**: owner image-OCR fill(카카오 KR1098 2023.4Q/2024.4Q·AIA KR0080·한화 KR0068 it37)을
  durable gold(`data/_gold/user_kics_cells.json`)에 영속화(+90셀, `append_owner_image_fills_to_gold.py`) +
  stale-gold 1건(한화 it37 45096.51→58590.96, owner 수정 클로버 차단) `reconcile_gold_to_xlsx.py`로 정합.
- [ ] **backfill 스크립트 rebuild 체인 편입**: `backfill_life_subrisk_positional.py`·`_from_pdf.py`·시장하위
  backfill이 `fill_*→apply_user_kics_gold→recalc` 체인 밖 → from-scratch 재빌드 시 미재현(+155 life-subrisk 등 소실).
  체인 러너(or 문서)에 `fill_market_*` 다음·`apply_user_kics_gold` 앞 단계로 편입. 현재는 커밋에만 존재.
- [ ] **gold git 추적 결정**: `user_kics_cells.json`은 현재 untracked(머신-로컬) — 다른 세션/머신 rebuild 시
  owner fill 소실. 추적 여부 owner 확인(민감정보 아님, 추적 권장).

### DEDUP — kics_disclosure 중복 행 slice (발견 2026-06-12, changelog (s))

`(원보험사코드, 공시분기, 항목번호, 항목명)` 중복 **94키 (값 상이 65키)** — 예: KR0001 2023.1Q item26 ×13, item12 값 {257, 32, 68431}. 과거 fill 누적 잔재. fill의 (code,item,name) index와 validator 입력이 어느 행을 읽느냐에 따라 흔들리는 잠복 리스크.
- [ ] dedup 스크립트: 같은 키 그룹 → 정답 판별(MD 재추출 대조 우선, 불능 시 최빈/최신) → 1행만 유지.
- [ ] fill_period에 신규-행 삽입 전 동일키 존재 가드 추가(이름 변형이 아닌 진짜 중복 차단).
- [ ] validation에 룰 입력의 중복 반응(first/last/any) 질의함 — inbox 20260612T1100Z 4).
- NOTE: FY2023_Q1 `--refresh` dry-run에서 메리츠 item12 257→68431 오매칭 신호도 관찰 — dedup 후 해당 라벨 매칭 재점검 (refresh는 그 전까지 금지).

### NEW-1 — 시장위험 하위(item36-40) 추가 backfill (inbox 20260612T0900Z 신규-1 + 20260611T2200Z systemic)

소스 MD에 5종 세부표(자산집중위험 행) 있는데 JSON 미적재인 (사,분기). validator는 "전사적 미파싱"으로 승격(19_market SKIP→RED). 분절표(`<!-- image -->`) 봉합 + 라벨변형(`(\d\.)?\s*(금리|주식|부동산|외환|자산집중)\s*위험(액)?`) + 값셀 탐색(방법 텍스트 다음 숫자).
- [ ] **224건, 36개사, 전 13분기** 36-40 재추출. gold anchor: 하나손해 2025.4Q(시장 76,839 / 금리 30,358 / 주식 62,491 / 부동산 2,643 / 외환 12,483 / 자산집중 5,251 백만원) + 삼성생명 2025.4Q. 도구 `fill_market_subs_from_pdf.py`(words-coordinate 전략) 또는 MD 분단표 합치기. **게이트: 19_market 행렬합 rel<2%** 통과분만 적재. 생보도 동일 스캔 후 일괄.
- [ ] 진짜 미공시 (사,분기)는 raw 표 부재 명시 회신 → validation `MARKET_BREAKDOWN_EXEMPT` 등록.
- [ ] **2026.1Q 항목 절단 backfill**: 30개사가 1-28만, 29-46 전무(8_life 29-35 + 시장위험 36-46) → 29-46 backfill.
- [ ] **census 미싱셀 28건**(MD parsed인데 JSON 추출 누락): 미래에셋 7분기·코리안리 6분기·동양·하나생명 등 + 2026.1Q 6사(한화손해·롯데손해·삼성화재·하나손해·미래에셋·동양). 명단 inbox 20260611T2200Z.

### NEW-2 — 생보 경과조치 적용후 요구자본(item14후/15후) 적재 20건 (inbox 20260612T0900Z 신규-2, owner xlsx #3 블로커)

경과조치 적용사인데 item14후 미적재 + item15후 유도값이 공시 비율과 불일치하는 생보 20건. 원천 MD [경과조치 전|후] 표에서 item14후(나.지급여력기준금액 후) 직접 적재. 검증식: `(2후+3후)/14후×100 ≈ item27후` ±0.6%p.
- [ ] ABL(KR0070) 2025.1Q/2Q/4Q · 푸본현대(KR0083) 2023.3Q~2025.3Q 9분기 · iM라이프(KR0076) 2024.4Q~2025.4Q 4분기 · IBK연금(KR1011) 2025.4Q · 농협생명(KR0104) 2024.4Q/2025.2Q/2025.3Q.
- [ ] 추가 확인 6건(적용사인데 14후·15후 둘 다 없음): 한화생명 2025.2Q / 삼성생명 2025.1Q / 동양 2025.2Q / iM 2023.1Q / 처브 2024.3Q.

### GOLD-SCAN — owner gold 필요 (이미지 스캔 PDF, 2026-06-12 확정)

자사+협회 모두 이미지 스캔 — 텍스트 추출 불가, KB(KR0010) xlsx-gold 전례 경로 권고:
- [ ] KR0079 미래에셋생명 — 전 구간 (기존 KICS-IMG 항목과 동일 코호트).
- [ ] KR0080 에이아이에이생명 — 2024.4Q~2026.1Q (2023.1Q~2024.3Q는 텍스트 있어 적재 완료, 신규 편입).
- [ ] KR0087 동양생명 — 2026.1Q만.
- [ ] KR0049 악사손해 — 2026.1Q 세부표 페이지(p16)만 이미지 → 코어 5행 외 잔여 항목 (게이트 잔여 RED 4건).

---

## 🟠 Open — P2

### MARKET-P2 — 시장위험 Phase-2 잔여 (after 2026-06-09 (e), 정당/후속)

- [ ] **19_market 구조적 SKIP ~100** (삼성화재 전분기·삼성생명·현대해상·한화생명): PDF에도 하위5종 비공시 = 정당 SKIP, RED 아님 (NEW-1과 분류 확정 필요).
- [ ] **36_irr Q1/Q3 ~85**: 분기보고서에 시나리오표 원천부재 = 구조적 SKIP.
- [ ] **IRR 직접형/granular 15** (KR0097 하나생명·KR1010 교보라이프·KR0051 신한이지): derived≠item36 → 직접공시 시나리오위험액 별도 schema 필요(저장 보류, SKIP 유지).
- [ ] **PDF 레이아웃 미스** (하나손해 2024.x 등): interleaved/grouped/concat fallback에 words-coordinate 전략 추가.
- [ ] **KB손해 image-only 4분기**: 스캔본 → OCR 경로.

### FY2026Q1 — K-ICS PDF→MD docling 잔여 (inbox 20260612T0900Z)

- [ ] **FY2026_Q1 K-ICS PDF→MD docling** (`data/disclosure/FY2026_Q1/raw/` → md_inbox; 일부 대형 PDF std::bad_alloc) → 금리민감도·시장하위 추출기 재실행으로 흡수.

### F12 — K-ICS 시장위험 하위위험액 전체 파싱 (parser side)

Cross-stage feature (root `TODO.md` keeps a 1-line ref; full detail here). Parser + validation cross-stage. 화면 노출 X, 데이터 신뢰용. Validation half = V3 in `TODO_validation.md`.
- [ ] 시장위험 하위 5개 + 분산효과 row 추출 추가
- [ ] 금리위험액 (+5쇼크 순자산 민감도 = 듀레이션갭) display-ready 필드 분리
- [ ] 출력 schema에 `market_risk_breakdown` 신설 → validation R11 sqrt 정합성 룰의 입력

---

## 🟡 Open / waiting

- [ ] **validation: RS1–4 룰 발주 대기** (스펙 §5). 마스터 ready 회신 = `inbox/validation/20260610T0830Z__parser__ALL__rate_sensitivity_master.md`. (RS1-4는 통과했으나 정식 룰 구현 확인 잔여.)
- [ ] **MLG-2 시장위험 분해** (owner 결정): PL-Tier2급 사별 핸들러 + 금리 유도규칙 owner 결정 필요. R11은 금리 확정 후. [xref: parser-ifrs17] (PL-Tier2급 핸들러 패턴은 IFRS17 lane이 owner; 본 항목은 시장위험액이 1차 데이터라 K-ICS lane 소관.)
- [ ] **IFRS-NORMALIZE** — 23-co full normalization: `row_aliases.yaml` 확장(현 PoC 930/2956 tagged) + K-ICS sensitivity 잔여 empty FY2025_Q4 생보사 normalize. (K-ICS sensitivity normalization이 1차; IFRS17 lane도 row_aliases.yaml 공유하므로 [xref: parser-ifrs17].)
- [ ] **KICS-IMG** — image-only PDF manual OCR: KR0010 KB손해(rule 2 ×2)·KR0079 미래에셋생명·KR0080. 정책: parser는 image-only 만나면 escalate, OCR 즉흥 금지 (`claude-agent-parser.md` §2.1). (KR0010은 2026-06-11 (r)에 owner gold로 RED=0 달성.)
- [ ] **REFACTOR-3 slice2 — PARKED (owner-gated, 2026-06-14)**: `make_quarter_column_picker` / `_canonicalize_table_label` 등 파라미터화 로직을 `company_handlers.REGISTRY[code]` dict-dispatch로 흡수. **착수 조건 = 진짜 KR-keyed 노브(column-picker quirk·값 reconcile 등)가 실제 발생할 때.** 현재 `src/`에 `if code==KR` 분기 0개(확인) → 지금 추출은 over-engineering(정적 config 아닌 predicate 로직). slice1(레지스트리)+DEDUP-1/2+GOLDEN-E2E(csm)는 완료 → changelog_parser_kics 2026-06-14. 원 스레드 inbox `_resolved/20260613T0200Z__owner__ALL__parser_refactor.md` (resolved).

---

## ✅ Done (archive)

One line per finished item. Full story in `docs/changelog_parser.md` + git. (Pre-split combined archive; K-ICS-lane items only — IFRS17-lane done items moved to `TODO_parser_ifrs17.md`.)

- K-ICS 금리민감도 추출 — `extract_kics_rate_sensitivity.py` → `kics_rate_sensitivity.json` 423행, RS1/RS2 pass — 2026-06-10 (changelog 2026-06-10)
- BNP(KR0075)/코리안리(KR1000) FY2025 재파싱 — docling v4 페이지선택 수정, +12행, RS4 hole=0 — 2026-06-10 (changelog (b))
- KB손해(KR0010) owner gold cell 적재 — `apply_kr0010_gold.py`, RED=0 최초 달성 — 2026-06-11 (changelog (r))
- 값_적용후 정합 2건 + recalc 분모버그 — 농협생명·삼성화재 + den14=post14 — 2026-06-11 (changelog (p))
- 2026.1Q 36/39사 적재 + MG/AIA 신규 편입 + 파서 버그 2건 — `append_kics_detail_from_pdf.py`·`seed_new_companies.py` — 2026-06-12 (changelog (s))
- 시장위험 하위분해 적재 (items 36–46) — `fill_market_subitems_to_disclosure.py`, +1,449행 — 2026-06-09 (changelog (c))
- 시장위험 커버리지 census + Phase-2 PDF 추출 — 36-46 복구 +150행, RED 0 — 2026-06-09 (changelog (d)·(e))
- K-ICS parser: split-table + row scope + Q4 reparse + KR0069/KR0097 fixes — 2026-05-24 (changelog archive)
- K-ICS RED reduction passes (419→311→217) + sub-items 29-35 + 값_적용후 historical — 2026-05-24/25 (changelog archive)
- Unit-hint mismatch auto-detect — 23 insurer-quarter latent bugs, 56 post 보정 — done (UNIT-HINT)
- B5-APPENDIX K-ICS sensitivity appendix headings + multi-period batch — 2026-05-25 (B5-APPENDIX)
- Pipeline foundation (Docling PDF→MD, 협회 파서 1차, kics_disclosure.json) — 2026-04-25~28 (changelog archive)

---

## Reading order for parser subagent (K-ICS lane)

1. This file (`TODO_parser_kics.md`) — open work + done archive
2. `docs/changelog_parser.md` — history (pre-split combined)
3. `docs/agents/claude-agent-parser.md` — master prompt + per-domain contract
4. Domain ref: `docs/domains/claude-agent-kics.md` for label variants and company quirks
5. Root `TODO.md` only for cross-stage items (F12) — full detail lives here
6. Sibling lane: `TODO_parser_ifrs17.md` (CSM/PL extraction) — for [xref] items

## Hand-off to validation

After parser produces normalized `kics_disclosure.json`, validation is invoked per `docs/agents/claude-agent-validation.md` §3 (retry loop, max 5). On RED, validation calls back the parser with the failing rule + suspected source.
