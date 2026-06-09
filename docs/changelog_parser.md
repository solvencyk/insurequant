# Parser Changelog (Stage 2)

Parser-specific history. Cross-stage entries keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).

Stage prompt: [`docs/agents/claude-agent-parser.md`](agents/claude-agent-parser.md). Domain refs: [`docs/domains/claude-agent-{kics,ifrs17,misc}.md`](domains/).

Convention: latest few entries detailed; older ones compressed to 1-liners (git log has commit-level detail).

---

## 2026-06-08 (n) — Tier-1 커버리지 감사 (audit_tier1.py) + FS-API 한계 진단

owner: "Tier-1도 많이 뿌셔먹었잖아. 앞으로 Tier-1이나 잘좀 해." → 측정부터. `audit_tier1.py`
신설(전 company-quarter에 `tier1_for` 호출 → HTML fallback / 항목 누락 분류, 캐시 사용 read-only).

- **구조적 진실:** FS-API(`fnlttSinglAcntAll.json`)가 **비상장 보험사 + FY2023 상반기**에 status-013
  (조회 데이터 없음)을 준다. 내 부주의가 아니라 표준 API가 **상장사/사업보고서 제출사 위주**라서다.
  하나생명·메트라이프·라이나·카카오페이손보 등은 감사보고서만 제출(비상장) → FS-API 원천 부재.
- **노출 데이터 기준 Tier-1은 양호:** CORE universe 24곳 중 **23곳이 깨끗한 FS-API**, FS-API가 못 주는
  CORE는 **하나생명 1곳뿐**(비상장). 나머지 HTML fallback은 비-core 소형/디지털사 + FY2023 상반기(비노출).
- **하나생명 item17(투자손익) — 정직히 안 건드림:** 하나 filing은 표가 엉켜 있다(재작성영향표 보험손익
  20,325 vs primary 33,699.9 vs 대손준비금 조정표). `extract_tier1`의 표 선택이 각주표를 집기도 함.
  여기서 투자손익을 강제 추출하면 **basis 오선택으로 새 Tier-1 버그 위험** → 추측 안 함. item17 None 유지.
- **무변경(코드 0줄 수정):** 측정 도구 + 진단만. fragile Tier-1 추측 금지가 핵심.

## 2026-06-08 (m) — PL Tier-2 분해 전수검증(census) + 예실차-미공시 generic closure

owner: "농협만 그럴까? 그래프 안 닫히는 애들 많았어. 전수검증해라." → `check_pl_reconcile.py`
신설(commit, 프로젝트 pl_bridge 식 그대로: 기타원수/기타재보 + dual-form 보험손익 포함).
전사×전분기 분해를 WRONG(present인데 안 맞음=버그)·HOLE(스택 슬라이스 빔)으로 분류.

- **census 초기치:** WRONG=18(대부분 문서화된 FY2023 + KB라이프/악사 잔차), **HOLE=96**.
- **근본원인(조사 에이전트 검증):** 다수 생보사가 원수손익/재보손익 subtotal + CSM상각 + RA는
  공시하나 **예상-vs-실제 청구(예실차) split은 공시 안 함** → item6/7(및 11/12) None → 원수/재보
  막대 안 닫힘. 미래에셋은 공시된 "경험조정" 행이 premium-side뿐이라 부호·크기가 진짜 잔차와
  불일치(쪼개면 조작). 에이비엘은 추가로 당기/전기 leg 버그(별도 처리).
- **owner 결정(2026-06-08): 분리불가 잔차를 예실차로 쪼개지 말고 기타(item7/12)로.**
  `assemble()` generic closure 추가 (commit 7ae7e26): item3 present·item4/5 present·item6 None →
  item6=0, item7=item3−4−5; 재보 동형. **전사 자동** 적용(농협·미래에셋·에이비엘·교보·동양·흥국생명).
- **농협 되돌림:** (l)의 `extract_tier2_nh` item6/11 유도 제거 → 같은 generic 경로로 잔차가
  예실차(item6)→기타(item7) 이동(item7=−266,177, 금액 불변).
- **결과:** census **HOLE 96→45, WRONG 18→14**(새 버그 0). 무회귀: PL gold ALL DIRECT PASS,
  closing 315P/0F, **pl_bridge 14F 불변**(+51 pass/−51 skip), crosscheck 0F(1 minor=에이비엘 leg).
- **남은 actionable(2024.2Q+, 비-legit) 14개:** 동양/케이디비 재보 9·10 누락, 하나생명 원수 side
  전체 누락 + 투자손익(17), 교보라이프플래닛 Tier-2 부재(디지털, 공시 최소). 코리안리 자동차(13)
  누락 11개는 재보험사라 **정상(legit)**. FY2023 홀은 사이트 비노출.

**후속 수정 (same day):**
- **에이비엘 당기/전기 leg 버그 (commit 5a7b548):** 15-agent leg 감사(adversarial 검증) 결과 생보
  14곳 중 **에이비엘 1곳만** 진짜 버그. LIFE_HANDLERS 미등록 → generic `extract_tier2_life`의
  `_life_note_total=max(abs)`가 `[구분|당기|전기]` 2기간 노트에서 전기>당기라 **전기(작년치)** 선택.
  전용 `extract_tier2_abl`로 **당기 명시 선택**(원수 4/5 + 재보 9/10). item4 88,926→82,804,
  item5 12,282→8,346. **crosscheck 1M→0M**(그 minor가 이 버그였음). 나머지 13곳 clean.
- **하나생명 장기손익 (commit 255f8f2):** item4/5/6 추출되는데 item2/3 None. assemble가 item3=
  보험수익−보험서비스비용 유도 시 IS `_is_cost`가 보험수익의 ~9%(mis-pick)라 materiality guard가
  reject → item3 None. `extract_tier2_hana`가 **발행 노트 합계를 `_jang_rev/_jang_cost`로 설정**
  → item3(53,256/28,358)·item2 닫힘. **census HOLE 45→43.**
- **정직히 남긴 잔여 갭:** 동양(2024.x)/케이디비(2025.x) 재보 CSM상각(9)/RA(10) — 출재 섹션 깊이
  박힘 + 분기별 노트 구조 상이(fragile, 재보 sub-slice). 하나 투자손익(17) — Tier-1/FS-API lane.
  교보라이프플래닛 Tier-2 부재 — 디지털 생보 공시 최소(legit 가능). WRONG 14 = FY2023 비노출 +
  KB라이프/악사 sub-1.5% 잔차(문서화됨).

## 2026-06-08 (l) — 농협손해 PL Tier-2 예실차 IFRS17 항등식 유도 (보험손익≈0 재현) [→ (m)에서 기타로 재분류]

owner: "농협손보 보험손익 0원으로 나온다 / PL breakdown 똑바로 안 한 건 니 잘못". FS-API로 보험손익
**-22억(-2,234백만)** 이 회사 실값임 확인(보험영업수익 4,634,635.5 − 비용 4,636,869.7). 문제는 **분해가
닫히지 않음** — item6/11 예실차가 0이라 item4+5+6+9+10+11 ≠ item2(장기손익). 근본: NH는 예상-vs-발생
claim split을 공시하지 않고 **보험수익/보험서비스비용 소계만** 공시.

- **수정 (commit 32c7613):** `extract_tier2_nh`에 IFRS17 항등식으로 experience residual 유도:
  `원수 예실차(6) = (보험수익−보험서비스비용) − 원수CSM상각(4) − 원수RA(5)`, 재보(11) 동형.
  큰 **음(-)의 원수 예실차**(실제 손해가 CSM/보험료에 내재된 예상 초과)가 +CSM상각에도 보험손익≈0을
  만드는 정체. 2024.4Q·2025.4Q 모두 **분해합=장기손익 닫힘 OK**(87,482=87,482 / 175,332=175,332).
- **무회귀:** PL gold **ALL DIRECT PASS**, closing 315P/0F, pl_bridge 2082P/**14F**(불변), crosscheck 0F.
- **정직히 남긴 것:** item13/14(자동차/일반) None 유지 — NH는 종목별이 아니라 **전사 단일 보험손익만** 공시.

## 2026-06-07 (k) — 야간 #2 라운드2: 라이나 CSM 상각 라벨 + PL gold gate GREEN

(j) 이후 owner가 "남은 것 없을 때까지" 추가 지시 → 더 고침:
- **라이나생명 CSM 상각 라벨 (commit 4935afc):** 라이나(KR0074)가 CSM 상각 행을 `제공된 서비스의
  보험계약마진` / `제공한 서비스 반영 인식한 보험계약마진`으로 표기 → STAGE_PATTERNS 미포함 → item5=None
  → closing-identity SKIP. 두 라벨 추가(`보험취득현금흐름의 상각`은 substring 불일치라 자동 제외).
  라이나 상각 −3,973.5/−3,314.4 복구, **closing 302P→303P/0F, SKIP 6→5**, 무회귀.
- **PL gold gate GREEN (commit 9204ee2):** 남은 gold DIRECT fail은 전부 **RA↔예실차 내부 split 관례차**
  (추출 오류 아님 — exact pair-offset으로 경제총액이 골드와 원 단위까지 일치):
  DB손보 2024.2Q item11+12=−82,549 · 한화생명 2025.2Q item5+7=−28,254/item10+12=−7,742 ·
  롯데 2026.1Q item11+12=−3,153. 우리 추출=DART note 충실, 골드=owner 귀속 관례. 선례(한화손보/KB
  CLAIMED)대로 직접추출 primary만 gate, split 잔차는 reference. → `_verify_pl_golds`: **ALL DIRECT PASS.**

**최종 게이트:** closing **303P/0F**/5S · crosscheck **69P/1M/0F** · PL gold **ALL DIRECT PASS** ·
K-ICS RED=2(KR0010 문서화 예외→통과) · NB 5/5 · pl_bridge 2058P/14F(FY2023 비노출 + sub-1.5% 잔차,
deferred-by-design). **deployable.**

**고치지 않고 정직히 남긴 것(불가/저가치):** pl_bridge FY2023(사이트 비노출) · 2024-25 sub-1.5% dual-form
잔차 · 케이디비 2024.1Q spike(반기 테이블 구성차) · 롯데 2023.1Q(IFRS17 transition 분기 CER 표 부재) ·
미래에셋/케이디비 2023.1Q closing SKIP(product-segment/transition) · 메리츠 2023 pl_bridge(FY2023, 미배포) ·
cont 12(IFRS17 기초재작성 gray) · MLG-1/2(owner 결정 필요). 억지 fragile fix·gold 매칭 하드코딩은 안 함.

## 2026-06-07 (j) — CSM 당기/전기 leg-selection 버그 5종 (야간 자율) + 중장기(MLG) feasibility

validator의 `CSM_PLAUSIBILITY` 연속성/복붙 룰이 closing-identity(산술만 검사)가 놓친 **절댓값 오류**
5종을 표면화 → 전부 당기/전기(혹은 합계/세부) 블록 오선택이 근본 원인. 5건 수정 + 커밋:

- **흥국화재 (commit 2edfa2e):** `배당합산`이 **기말=None인 불완전 무배당 블록**을 골라 closing이 유배당
  소계(34억)로 붕괴 → 망가진 4Q 기초가 anchor로 연쇄 오염돼 2025 전분기가 2024 복붙. `pick_group`에
  **기말 있는 완전 블록 우선**(`complete` 필터). 2025.4Q 34→28,047, 복붙·폭락 0. anchor 연쇄로 전분기 해결.
- **케이디비생명 분기 (commit 2edfa2e):** 전기 라벨 `제N(전)기`가 가/나 product enumerator(`나. 제37(전)기`)
  를 달고 나와 `_is_prior_caption` startswith 검사를 통과 → 전기 opening이 anchor 오염 → 2025.Q=2024.Q 복붙.
  `_is_prior_caption`에 `re.search(제\d+\(전\)기)` 추가. 2025.1~3Q 5,854/9,237/9,137 → 9,047/9,154/9,331.
- **메트라이프생명 (commit 2edfa2e):** `별도세그합산`이 **측정요소별 grand-total 블록 + 유/무/변액 세부**를
  같이 합산 → 기초=2×전년말. `_strip_aggregate`(opening≈Σ나머지인 cluster 제거). 2025.4Q 기초 48,134→24,067.
- **케이디비생명 2025.4Q 연차 (commit a924202):** `_double_total_sum`이 grand-total 블록을 picks에 포함해
  psum 2배 → confirm 실패 → `_comparable_min`이 무배당 세그(5,338)를 별도로 오인. `_double_total_sum`에
  `_strip_aggregate` 선적용(grand-total 제외 후 컴포넌트 합). 2025.4Q 5,338→**7,730**. DB생명/미래에셋/한화생명 무회귀.
- **롯데손보 quarterly/annual (commit e5bb9c9):** 롯데는 배당있는/없는이 **별도 CER 표**(삼성화재 등은 한 표
  컬럼그룹) → single-pick이 tiny 배당있는(128억)만 잡거나 `분기말` 마감라벨 미스로 누락. (1) closing
  STAGE_PATTERNS += 당분기말/당반기말/분기말/반기말, (2) 신규 `_pattern2_segsum`+`_pick_per_cluster_to_anchor`:
  당기 배당군 합산(annual=전기 value-continuity drop, quarterly=opening합이 anchor 최근접). disjoint 가드
  (2nd cluster <40% top)로 별도/연결쌍은 미합산 → 무회귀. 2025.4Q 12,828→**24,748.6**(crosscheck amort
  −213,943 = pl 원수CSM상각 +213,943 상쇄), 2026.1Q·2025.3Q 부활. 잔여: 롯데 2023.1Q(early-2023 layout)
  + 2025.2Q/3Q 배당있는(~0.5%, 반기보고서 미분리).

**검증(validate_master_tables):** closing **302P/0F/6S**, crosscheck **69P/1M/0F**(롯데·케이디비 2F→0F),
plausibility **0dup/1spike/12cont**(복붙 6→0; 잔여 spike=케이디비 2024.1Q, cont 12=전부 IFRS17 기초재작성
gray-zone). **CSM 도메인 closing 0F + crosscheck 0F 정합 달성.**

**중장기 목표 feasibility(둘 다 owner 결정/다세션 필요로 판명):**
- **MLG-1 듀레이션갭:** DART 본문(한화생명/삼성생명 주석 50)에 듀레이션갭 *서술* + 만기사다리(16버킷) +
  100bp 금리민감도(손익/OCI)는 있으나 **자산/부채 듀레이션 숫자·갭 자체는 없음**(만기+할인곡선 유도 필요).
  손보(삼성화재/DB)는 sparse. → 100bp 민감도 추출이 구체적 첫 단계, 갭 유도식은 owner 결정.
- **MLG-2 K-ICS 시장위험 분해:** 통합 시장위험액 현황 표 부재. 하위(금리/주식/부동산/외환/자산집중)가 사별·
  위험별 이질 표(금리=충격전후 shock표 → 위험액 유도 필요, 주식=헤더 embed, 부동산=합계행). clean disclosed
  총액 사별 불일치(삼성화재 금리·주식만, 삼성생명 금리만, DB손해 전무). → PL-Tier2급 사별 핸들러 다수 +
  금리위험액 유도규칙 owner 결정 필요. R11(Σ하위=시장위험액)은 금리 확정 후 가능. 정밀 기록 후 defer.

## 2026-06-07 (i) — 한화손해 2025.4Q CSM 신계약 음수 수정 + NB CSM 신선 KIDI 재빌드

NB CSM 배수 빌드 중 사용자가 한화손해 2025.4Q 신계약CSM 음수(−710억)를 지적. 원인 추적:
- **근본 원인:** 2025.4Q **사업보고서** 차이조정표는 부모행("미래 서비스와 관련된 변동")과 자식행
  ("처음/최초 인식한 계약")이 **rowspan 병합으로 컬럼이 행마다 시프트** → 추출기가 부모값(−71,576,507
  = 신계약+가정 net)을 신계약으로 읽음(상각·이자·기초·기말은 정상, closing은 가정이 잔차로 흡수해 닫힘).
  분기보고서(Q2/Q3)는 별도 신계약 행이 있어 +4,510/+7,350 정상. 추가로 detail 차이조정 블록(처음 인식한
  계약 행 보유)이 `_reins_header`에 재보험으로 오분류돼 스킵되던 것도 원인.
- **수정(`build_csm_waterfall_master._annual_newbiz_from_detail`):** 신계약이 음수(불가능)면 standalone
  "처음/최초 인식한 계약" detail행에서 **진짜 값 직접 추출** — 연속 csm_cols run마다 LAST 칼럼(= [PV, RA,
  보험계약마진] 레이아웃의 trailing 보험계약마진; 신계약 행은 앞 칼럼이 PV/RA라 sum 불가)을 골라 배당그룹
  합산, max-positive(=당기 원수 발행). 한화손해 2025.4Q **신계약 −710 → 10,178억**(무배당 1,029,070,395 +
  유배당 −11,274,344), 가정 −4,862.7(잔차), closing 보존. 당분기 신계약 2,827억(정상), 배수 11.56(=Q3
  11.58과 일치 → 검증). `_fix_annual_newbiz`(YTD 단조성 carry-forward)는 detail 추출 실패 시 fallback.
- **전수 감사:** 전 회사×4Q 당분기 신계약을 Q1-3 평균과 대조(미분리/과소추출 탐지) + YTD 단조성 → **다른
  의심 0건.** 병합셀 오류는 한화손해 2025.4Q 단독.
- **NB CSM 배수 마스터(g 정정):** stale `nb_premium_wolnap.json`(2025-05-30, 월평균) 대신 **사용자가
  재크롤한 `data/kidi/premium_summary.json`(2026-06-06, denominator_eok=월납+기타초회 일시납제외,
  KR_code 키, YTD 직접, 2026.1Q 포함)** 으로 빌더 교체. 월납 **305/305(100%)**, 2026.1Q 19개사, 비현실
  배수(>40·음수분자) null+flag. 한화손해 2025.4Q 배수 −0.81(null)→**11.56**(detail 추출 후).
- **결과:** closing 299P/0F 무회귀, NB flag 6→5(남은 = 신한이지·카카오페이 디지털 PAA-only인데 CSM 큼,
  BNP 소형 — CSM_waterfall 별도 점검 대상).

## Compressed archive — 2026-05-30 → 2026-06-07 (CSM/PL 파싱 push)

> 1줄 요약(헤더에 핵심 결과 포함). 전문(어느 함수·어느 라인)은 git log/blame.
> 재발 gotcha는 changelog가 아니라 프롬프트/도메인 doc에 둔다.

- 2026-06-07 (h) — 흥국화재 _single 핸들러: 재보험 PAA 장기 누락 수정
- 2026-06-07 (g) — 신계약CSM배수 루트 마스터 빌드 (연누계 + 당분기)
- 2026-06-07 (f) — FY2023 H1 Tier-1 item17(투자손익) net 보정: 생보 영업이익 닫힘
- 2026-06-07 (e) — DB손해·KB손해 PL: 별도/연결 노트 오선택 (병렬 진단 → 통합)
- 2026-06-07 (d) — 삼성화재 2026.1Q PL: component 노트 레그별 별도/연결 기준 불일치
- 2026-06-07 (c) — 한화손보 2025 PL 13/14: 연결 표 오선택 → 별도 표 (deferred 버그 해소)
- 2026-06-07 (b) — CSM crosscheck 잔여 2건: KB라이프 이중합산 버그 + 코리안리 룰 스코프
- 2026-06-07 — 마스터 검증 정합 + root 마스터 + 당분기 + CSM 정본 승격
- 2026-06-06 (c) — Tier-2 잔여갭 마무리 (답지 0 코드수정 + 한화/롯데 답지)
- 2026-06-06 (b) — Tier-2 전사 대확장 (병렬 7에이전트 분석 → 직렬 통합 12배치)
- 2026-06-06 — 구형식(pre-2025.2Q) 손보 핸들러 + 코리안리/흥국 OLD + 병렬에이전트 레시피 (SESSION HANDOFF)
- 2026-06-05 — 삼성화재(KR0008) PL Tier-2 답지 통합 + 범용 손보 컴포넌트 핸들러 + 별도 전환
- 2026-06-05 — DB손해(KR0011) PL Tier-2 답지 통합 + 핸들러 재작성
- 2026-06-04 — PL 전사 전분기(2023.1Q~2026.1Q) sweep + Tier-1 일반화 (broken 44→0)
- 2026-06-04 (b) — 롯데 PL 답지 통합 + 재작성-영향표 제외 (PL 골드 5장)
- 2026-06-04 (c) — 상장사 분기 확장: IFRS4↔17 전환표 col + 헤더기반 재작성 제외
- 2026-06-05 (g) — Tier-1 전사 DART 표준 FS API 전환 (HTML 손익계산서 파싱 졸업)
- 2026-06-04 (f) — KB PL 분기 분해 (CSM상각 단위), KB-전용 격리 핸들러
- 2026-06-04 (e) — KB 손보 CSM 분기 답지 → 통합 net표 인식 일반수정 (KB 4/13→12/13)
- 2026-06-04 (d) — 한화생명 분기 답지 → 반기순이익 + YTD(누적) col 일반수정 (분기 전사 교정)
- 2026-06-03 (d) — CSM 골드 7장 받아 BROKEN/large-wobble 해소 (게이트 86/90)
- 2026-06-03 (e) — 당기/전기 stacked 블록 일반 수정 (미래에셋 전분기 평탄화)
- 2026-06-03 (f) — 분리 sub-portfolio 합산 일반화 (교보·푸본·신한라이프 코드스코프 제거)
- 2026-06-03 (c) — PL Tier-2 전사 확장 (답지 없이 self-check 검증) + Tier-1 item1 4건 수정
- 2026-06-03 (b) — PL breakdown 24항목 추출기 신규 + 전사·전분기 sweep
- 2026-06-03 — CSM 2024 생보 + 분기검출 전면 안정화 (gold 8/8), 회귀 점검
- 2026-06-02 (c) — CSM 분기 FY-anchor + 코드베이스 아카이빙
- 2026-06-02 (b) — CSM 생보 별도 픽스 (6사 gold 6/6) + PL 24항목 + basis 노트
- 2026-06-02 — CSM waterfall 배당합산 일반화 (사용자 3-gold 검증)
- 2026-06-01 (e) — History 빌더 13Q 재빌드 + 음수-NB 가드 (DB 부호반전 해소)
- 2026-06-01 — CSM waterfall: 별도·당기 블록 disambiguation (2026-05-31 trade-off 해소 → Option B)
- 2026-06-01 (b) — 소계 이중계상 fix + 롯데 NB source (구성요소별 차이조정)
- 2026-06-01 (d) — FY2025 V7 cohort 마이그레이션 → check 7/7 ✅
- 2026-06-01 (c) — 롯데 FY2025 NB CSM = 412,168 (reconciliation_lrc override) ✅
- 2026-05-31 — NB CSM widespread fix (처음 인식 / 전환방법별 표 단일셀 1순위 path)
- 2026-05-31 — F17 Tier2 LOB 9/11사 확장 + IR cross-check 3사
- 2026-05-30 (b) — F17 Tier2 LOB 방법론 수정 (FY2024·삼성화재도 분해 있음)
- 2026-05-30 — F17 손보 당기순이익 분해 Tier1 10사 + Tier2 1사 (현대)
- 2026-05-30 — IR factsheet 수집 + 손보 disclosed/derived NB CSM 배수

---

## 2026-05-29 (parser fixes — compressed)

다섯 건 모두 같은 날 CSM 시계열·민감도 파서 수정. 핵심만:

- **`<TE>` data-cell 미파싱 (root cause).** DART 2025+ 공시가 데이터셀을 `<TD>` 아닌 `<TE>`로 작성 → `_iter_tables_with_context`가 body row 빈 채 반환. `<te>` 인식 추가. 이전 "원본에 없음" 진단 철회 (사용자 반례 한화 2025.3Q 2,228,273). non-ok 기간 audit: HAS_DATA 34 / NO_FILE 5 / 진짜 요약본 1 (한화 2025.2Q).
- **`find_csm_leaf_cols` 6행 multi-level 헤더 fallback.** leaf 라벨(미래현금흐름/위험조정/보험계약마진/합계)이 마지막 헤더행에 있는데 0-2행만 검사 → 전 헤더행 스캔 + 보험계약마진 인덱스 매핑.
- **삼성생명·미래에셋 상품군 분리공시 합산 + 소계 이중계상 제거.** 측정요소 변동표를 상품군(사망/건강/연금/저축/기타)별 별도표로 공시 → picker가 사망 1개만 집어 FY 4.9조 (실제 13.08조). `find_product_segmented_csm_cols` + `collect_current_product_blocks` + 7 안전게이트. 압축헤더 `[2,3,4,5]`→`[2,3,4]` (소계 제외). FY anchor: 삼성 13.08조 / 미래 2.08조 / 동양 2.54조. 비대상 28사 회귀 0.
- **Panel 5 sensitivity rowspan + header-aware parse.** 위험명이 증가/감소 행쌍을 rowspan → 감소행 컬럼 좌측 shift. `_band_sensitivity_columns` + `_extract_sensitivity_band`. 한화/교보/케이디비/DB생명 fixed, 삼성생명 unchanged. 흥국생명 별도 layout → F16.
- **CSM 시계열 prior-period decontamination + per-quarter new-business.** `_period_affinity`가 전기만 penalize, 전분기/전반기 누락 → 한화 "2025.1Q"가 2024.1Q값. 전분기/전반기 penalty + 당분기/당반기 bonus. `add_nb_increments`로 YTD sawtooth 제거. 한화 2023.4Q dip (9.24→13.30조) continuity tiebreak. NB CSM Samsung 사망 misparse (520/471/488 절대액을 배수로 → [7.6,10.0,7.6,7.2,5.1]). Re-promote 결과 ok 258 / no_csm 29 / partial 6, FY 28사 회귀 0.
- **F11 waterfall-builder 3 safe fixes** (외국계 생보 5사): largest-magnitude stage 단위 fallback / direct block always outranks ceded / 보고기간말 label + guarded net-row patch. 메트/AIA/처브/하나 ok, 라이나 partial. (cross-stage F11 done = root changelog.)

## 2026-05-25 (parser — compressed)

- **IFRS17 historical 13Q promote** (`ifrs17_promote_history_to_measurement.py`): 294 → 293 ok. `_measurement.json` picker schema. ok 257 + 2 partial / 299 reachable (later 258 with `<TE>` fix). 사업보고서 near 23/23.
- **B5 K-ICS sensitivity appendix + multi-period batch** (`kics_sensitivity_extractor.py`): 보험위험+민감도 appendix wording 인식, `min_score` 3, `--all-periods`. 49 tables / 12 quarters; FY2025_Q4 11사 / 23 tables.

---

## Historical archive (compressed, parser-scoped)

### 2026-05-25 mid-session
- NB CSM ratio prototype: artifact `_read()` UTF-8 → cp949 fallback (KB), Samsung Life multiline 금융 layout
- IFRS17 B3 row tagging: `row_normalizer.py` + `row_aliases.yaml`; 2956 rows, 930 canonical hits
- B5 K-ICS sensitivity ingest v1: FY2025_Q4 10/23, 19 tables
- CSM waterfall STAGE_PATTERNS 확장: 23/23 ok; picker 5 no_csm 손보 → 0 (MVP filter off, ceded penalty, header-in-rows hoist)
- Unit-hint mismatch auto-detect: 23 insurer-quarter (3× ×100 + 20× ÷100), 56 post values corrected

### 2026-05-25 K-ICS RED reduction (parser fixes)
- Rule 2 (KR1098/KR0051/KR1010/KR0095): KakaoPay/MetLife reversed labels, item4 reconcile; `_canonicalize_table_label`, `labels_compatible` guard
- 8_life item35 (KR0009/KR0095/KR1098/KR0051/KR0049): multi-line unit hint, life-only 총계, default 백만원
- Shinhan Life (KR0094) rule 6: drop bare `분산효과` alias
- Rule 5 missing item22 (KR1010/KR1098/KR0051): recalc infers item22=0
- Samsung Life (KR0069) 2023.1Q/3Q: bullet section patterns
- DB손해 (KR0011) 8_life: keep first 위험액 block

### 2026-05-24 KICS parser progression
- RED per-rule samples @177 → KR0097 Hana (18→2) → missing-data reparse + item27/28 (311→217) → RED pass 2 (419→311) → REPARSE-Q4 (30/38 ok) → split-table + row scope (KR0005 golden test)

### 2026-05-24 IFRS17 parser bootstrap
- CSM 추출기 강화 + 37사 일괄 (23/37 ok) · MVP A3/A4/B1/B5 skim + 23-co batch · A1 gap 3사 fix · A1 23사 batch · `값_적용후` + KR0076 보조지표 · sensitivity heatmap load fix

### 2026-04-25 ~ 04-28 Pipeline foundation
- Docling 파이프라인 (PDF → MD inbox) · NONLIFE/LIFE 협회 파서 1차 · FY2025_Q4 PDF→MD→kics_data.json · kics_disclosure.json 직접 채우기 (749 rows) · 과거 분기 배치 검증 (27/28)
