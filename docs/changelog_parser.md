# Parser Changelog (Stage 2)

Parser-specific history. Cross-stage entries keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).

Stage prompt: [`docs/agents/claude-agent-parser.md`](agents/claude-agent-parser.md). Domain refs: [`docs/domains/claude-agent-{kics,ifrs17,misc}.md`](domains/).

Convention: latest few entries detailed; older ones compressed to 1-liners (git log has commit-level detail).

---

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

## 2026-06-07 (h) — 흥국화재 _single 핸들러: 재보험 PAA 장기 누락 수정

validator가 흥국화재 PL을 "별도/연결 레그 오선택 + 2024.4Q 숨은 275억"으로 진단했으나 둘 다 오진:
2024.4Q 275억 = 기타사업비용(_old 핸들러 net basis, bare 닫힘 — 무시 대상). 진짜 버그는 `_single`
핸들러(2025.4Q/2026.1Q)가 **재보험 leg(rerev/recost)의 PAA 장기 컬럼을 드롭**한 것.
- `_jang_rerev/_jang_recost = totrow[0]`(non-PAA 장기)만 읽어, 흥국이 PAA로 출재한 장기재보험 부분
  누락 → 재보험 장기 과소 → 장기손익 과대 → ΣLOB가 adj목표(item1+item16)보다 과대(2025.4Q +1,684,
  2026.1Q +968).
- **수정**: `jang_tot()` — 장기 = non-PAA 장기(ns[0]) + **PAA 장기(PAA합계−PAA일반−PAA자동차 =
  ns[-1]−ns[-3]−ns[-2])**. 0-컬럼 드롭으로 칼럼수가 분기마다 달라지는 문제에 robust(합계 항등식 사용).
  검증: 2025.4Q recost PAA장기 74689−71732−385=2,572·rerev 56900−57617+1605=888 → 순 −1,684 복원;
  2026.1Q recost 20639−19563−108=968. 둘 다 ΣLOB=item1+item16 **diff +0**.
- **결과**: pl_bridge 16F→14F. 흥국 gold 2025.2Q 0 DIRECT, closing/crosscheck 무회귀. blast 반경 =
  흥국 2025.4Q/2026.1Q만(_single은 KR0005 전용).
- **잔여**: 흥국 2023.1Q(−345, 0.4%)·2025.1Q(−714, 1.2%)은 레거시 `_old` 핸들러(combined-table 구조,
  PAA-장기 드롭 아님). 2023-2024는 정상 bare-닫힘이라 _old 수술은 회귀 위험 — 별도 판단.

## 2026-06-07 (g) — 신계약CSM배수 루트 마스터 빌드 (연누계 + 당분기)

deferred됐던 월납월초→CSM배수 마스터 빌드. 루트 `NB_CSM_multiple.json` (305행, 35사), 스키마 =
`NB_CSM_multiple.xlsx` 헤더 정확 일치 (원보험사코드·원수사명·티커·생손보여부·공시분기 + 신계약CSM/
월납월초/배수 각 연누계·당분기). 빌더 `scripts/build_nb_csm_multiple.py`(신규).
- **신계약CSM**: `CSM_waterfall.json` 항목2 (값=연누계, 값_당분기=당분기). 정정된 CSM waterfall 반영.
- **월납월초**: **`data/kidi/premium_summary.json`** (사용자가 2026-06-06 KIDI INCOS ML01/MN07 재크롤,
  2026.1Q 포함). `denominator_eok` = 월납 초회 + 기타 초회 (일시납 제외 = 저축성 월납 포함, 사용자 기준).
  **KR_code로 조인**(이름매칭 불필요), YTD 누적 직접값 → 연누계 = denominator_eok, 당분기 = YTD 차분.
  (초기엔 stale `_derived/nb_premium_wolnap.json` 2025.3Q까지·월평균을 잘못 사용 → 사용자 지적으로 정정.)
- **배수** = 신계약CSM ÷ 월납월초. 비현실 배수(>40 또는 분자≤0)는 null + flag(원시 CSM·월납은 보존).
- **커버리지: 월납 305/305(100%, 35/35사), 2026.1Q 19개사.** 배수_연누계 294 / 당분기 270.
  IR 공시배수 대조: DB손해 0.7%·메리츠 4.6% 정밀; 삼성화재 6.4%·한화생명 10.8%는 **스코프차**(IR=보장성 /
  내것=저축성포함 total = 사용자 기준)로 의도된 차이.
- **flag 6건 (전부 CSM_waterfall 데이터 의심, NB_CSM 빌드 문제 아님 → CSM 스테이지 점검 대상)**:
  신한이지(CSM 4,946억/월납 1억=4908배)·카카오페이(20,187억/6.8억)는 디지털 PAA-only인데 신계약CSM이
  비현실적으로 큼(GMM CSM 잘못 추출 의심); BNP(101·83배) 소형 생보; 한화손해 2025.4Q CSM_연누계 −710
  (4Q 재서술). 모두 배수 null·원시값 surfaced.

## 2026-06-07 (f) — FY2023 H1 Tier-1 item17(투자손익) net 보정: 생보 영업이익 닫힘

FY2023 상반기는 FS-API 부재(status 013)→Tier-1이 HTML `extract_tier1`로 fallback. 생보 요약
손익계산서는 영업이익 = 보험손익 + 투자손익(+기타)인데, `L("투자손익")`이 GROSS 하위행을 매칭해
영업이익 항등식 위반(동양 2023.1Q +305k가 대표): 동양=순투자손익(보험금융 차감前) → "순보험금융손익"
별도행, 신한=Ⅱ.투자손익 + 별도 Ⅲ.기타손익.
- **수정(`extract_tier1`):** (1) item19 fallback에 `"순보험금융손익"` 추가(동양 item19=−305,234 채움);
  (2) **영업이익 항등식 net 보정** — gross 투자손익이 `보험손익+투자손익=영업이익`을 깨면, 순보험금융손익
  있으면 `item17=투자+보험금융`(동양, item19도 채움), 없고 별도 기타사업비용 행 없으면(생보 요약)
  `item17=영업이익−보험손익`(신한·DB생명, 기타손익 흡수). FS-API 경로/손보는 항등식 이미 성립→no-op.
- **결과:** 동양 2023.1Q item17 440,261→135,028, DB생명 2023.1Q 156,135→59,768·2023.2Q→84,432,
  신한 2023.1Q 72,835→53,930 — 영업이익 전부 닫힘. 2023.2Q/4Q·2024.4Q(FS-API) 무회귀.
  **pl_bridge 20F→16F (영업이익 4건 해소).** closing 299P/0F·crosscheck 68P/2M/0F 무회귀. 골드는
  전부 2024+(FS-API 경로)라 무영향(신규 DIRECT fail 0). blast 반경 = FY2023 H1 등 HTML-fallback 35 q-c.
- **남은 16F:** FY2023 basis 잔차(②, DB생명·DB손해·메리츠 2023 보험손익(dual) — Tier-2 별도 vs Tier-1
  연결/CFS, FY2023 H1 별도 Tier-1 확보 시 해소) + 소액(흥국·악사·KB라이프 sub-1%).

## 2026-06-07 (e) — DB손해·KB손해 PL: 별도/연결 노트 오선택 (병렬 진단 → 통합)

validator가 DB손해(ΣLOB 결손)·KB손해(ΣLOB 과대)를 보고. 읽기전용 에이전트 2개 병렬 진단 → 메인이 통합.
둘 다 삼성화재/한화 계열 별도/연결 문제지만 메커니즘이 달랐음.
- **DB손해 (`_old_db`, 2023–2024 fallback 경로):** 후보 필터가 `"생명" in hb`를 요구해 **연결 블록(DB생명
  자회사 생명컬럼 포함)에 잠김** + `<수재>` 탈락. 둘 다 item14(일반)에 집중(DB 수재는 일반에만 존재).
  수정: **별도 블록(생명 無) 선택** + LOB 합계행(원수+수재) 읽기. 골드 2024.4Q 일반 70,497→117,480, 자동차
  192,061 정확; 2024.2Q 일반 100,374 정확. **2024.1Q–2025.1Q ΣLOB=item1+item16 닫힘** (2025.2Q+ 는
  `extract_tier2_db` 신규 핸들러 우선 → 무영향). 블래스트 반경 DB 전용(_old_db 도달은 KR0011만; KR0008은
  _old_samsung 우선).
  · **잔여: DB손해 2023.1Q/2Q/3Q (FY2023).** 2023 H1은 FS-API 부재→item1=연결(HTML, 생명 포함)인데
    Tier-2는 장기/자동차/일반만(생명 구조적 제외)이라 basis 불일치 → 정본 별도 유지하고 FY2023 H1 Tier-1
    (별도 확보) 작업 때 해소 예정. KB식 item1-aware로 못 푸는 이유=생명컬럼 구조차.
- **KB손해 (`_kb_note`):** 노트가 2벌(연결 큰 합계 먼저, 별도 뒤). 기존 `<당기>` 필터가 **별도 Q4 노트(평문
  caption)를 배제**해 연결 강제 → ΣLOB 과대(=연결−별도). 수정: `<당기>` 게이트 제거 + **총보험서비스결과
  합계가 Tier-1 item1과 일치하는 노트 선택**(item1을 `parse_filing`→핸들러로 스레딩). **2024+ 는 별도
  item1, FY2023은 연결-HTML item1을 추종**(자동 robust). 전 분기 ΣLOB=item1 diff=0 검증(2023.1Q 연결
  258,881 / 2024.4Q 별도 977,999 등). KB손해 8F→0F.
- **결과: pl_bridge 31F→20F** (DB손해 8→3, KB손해 8→0). closing 299P/0F·crosscheck 68P/2M/0F 무회귀.
  골드: DB 2024.2Q item13/14 정확(DIRECT 2→1, 잔여 item11=재보험 예실차 기존잔차), KB 2025.2Q 0 DIRECT.
  남은 20F는 대부분 **FY2023(H1 Tier-1 갭)** + 소수 sub-1% 잔차(흥국·악사).
- **배관 변경:** `parse_filing(…, name, quarter)` 추가(main 호출 1곳), 손보 디스패치에서 KB일 때 FS-API
  우선 item1 계산해 전달. 비-KB 코드 경로 불변.

## 2026-06-07 (d) — 삼성화재 2026.1Q PL: component 노트 레그별 별도/연결 기준 불일치

validator가 삼성화재 2026.1Q 보험손익 등식 +2,067(20.67억) 미닫힘 보고("기타영업수익 누락" 가설).
FS-API로 검증: 삼성화재 별도 보험영업수익 = 보험수익 + 재보험수익 정확(기타영업수익=0), 보험손익(ISR)
514,384 = 보험서비스결과 − 기타사업비용 → **진짜 보험서비스결과 = 보험손익 + 기타사업비용 = 573,635**.
그런데 Tier-2 ΣLOB = 571,568 → **LOB가 2,067 부족**(기타영업수익 아님, 한화와 같은 LOB 추출 문제).
- **근본원인:** `extract_tier2_sonbo_component`의 `pmin`(레그별 최소합계=별도)이 4개 레그를 **독립적으로**
  선택 → 기준 혼선. 연결 주석이 그룹내부 재보험을 상계하므로 **별도 재보험회수(80,446) > 연결(78,380)**
  이라, 보험수익은 별도(작은쪽)인데 재보험회수는 연결(작은쪽)을 집음. 일반 재보험회수가 21,886(연결)로
  들어가 23,952(별도)보다 2,066 부족 → ΣLOB 2,067 부족. (2025.4Q는 별도 재보험 < 연결이라 pmin이
  우연히 맞아 닫혔음.)
- **수정:** 별도 rev(min 합계)를 anchor로 잡고 cost/재보험 레그를 **같은 문서 블록**(rev 인덱스 이후 첫
  후보, `first_from`)에서 선택 → 4레그 동일 기준. 한화 (c)와 동형 별도/연결 패턴.
- **결과:** 2026.1Q 일반 109,190→111,256(+2,066), ΣLOB 571,568→573,634 = 진짜 보험서비스결과 ✓ 닫힘.
  2025.2Q/3Q/4Q 불변(별도 재보험<연결이라 pmin·first_from 동일결과). **pl_bridge 32F→31F**(삼성화재
  2026.1Q 해소). 삼성화재 골드 2025.2Q·2024.2Q 0 DIRECT 회귀. (이 함수는 타 손보 fallback이기도 —
  별도-only 신고는 단일블록이라 no-op, 별도<연결 전사는 동일결과 → 무회귀.)

## 2026-06-07 (c) — 한화손보 2025 PL 13/14: 연결 표 오선택 → 별도 표 (deferred 버그 해소)

validator가 한화손보 2025.2Q/3Q/4Q 보험손익 등식 미닫힘(역산상 기타영업수익 21,215/48,896/48,895
필요)을 "기타영업수익 누락"으로 진단. **골드(`보험손익 breakdown_한화손보.xlsx`, 메타 오타 "2025.4Q"
지만 실제 당반기=2025.2Q)로 확인 결과 가설 오진:** 골드 item15 기타영업수익=공란(0), 진짜 오차는
item13 자동차(내 −21,864 vs 골드 −5,650)·item14 일반(13,663 vs 18,665). LOB 오차합 −21,215.6 = gap.
- **근본원인:** `extract_tier2_hanwha`가 발행보험 컴포넌트 표를 first-occurrence로 집었는데, 한화손보
  NEW 신고서는 **연결 주석 먼저·별도(개별) 주석 뒤**로 2벌 수록. 연결엔 **캐롯손보(자동차/일반 자회사)**
  가 합쳐져 PAA LOB(13/14)이 과대. 장기(GMM)는 자회사 없어 별도=연결 → items 4/5/6은 이미 정확해
  버그가 안 보였음(이전 세션 "한화 NEW 13/14 deferred"의 정체).
- **수정:** `_hanwha_sep_rev_idx`(보험수익 후보를 문서위치로 클러스터 → 후속=별도 블록의 당기 선택) +
  `_hanwha_section_from`(별도 인덱스부터 forward anchor로 비용/재보험 레그 고정). 합계크기론 구분 불가
  (2025.4Q 연결전기<별도당기) → 문서순서 기반. 1Q는 OLD포맷(후보 0)이라 무영향.
- **결과:** 2025.2Q 골드 13/14 정확 일치(−5,650.034 / 18,664.691), items4/5/6 불변(별도=연결). 2025.3Q/
  4Q/2026.1Q 보험손익 등식 전부 닫힘. **pl_bridge 36F→32F (한화손보 4건 보험손익 dual 해소).**
  `_verify_pl_golds`에 한화손보 2025.2Q 등록(CLAIMED {1,4,5,6,9,10,13,14,16}; item11 ~0.3% 가정·경험
  잔차는 reference). 타사 골드 0 DIRECT 회귀.

## 2026-06-07 (b) — CSM crosscheck 잔여 2건: KB라이프 이중합산 버그 + 코리안리 룰 스코프

validator가 crosscheck 잔여 9건 중 "진짜 의심 2건"(KB라이프 2023.4Q, 코리안리 2025.4Q, wf>pl)을
"재보험분 혼입" 가설로 넘김. 디버그 결과 **두 가설 모두 빗나갔고** 원인은 서로 달랐음.
- **KB라이프 2023.4Q = 진짜 wf 버그(당기+전기 이중합산).** `pick_combined_agnostic`/`_caption_segment_sum`이
  당기 블록(상각 −283,905백만=pl과 정확일치)에 **전기 블록(−146,769)을 더해** 정확히 2배(−430,674)로 만듦.
  근본원인: KB라이프 **사업결합(KB생명+푸르덴셜)** 으로 기초가 2줄("기초(사업결합 전)" 2,373,817 vs 복원
  "기초" 3,132,762). 전기.기말(2,373,818)이 *사업결합 전* 기초와 같아 `_is_prior_stage` 값연속성이 빗나가
  전기블록 미탈락. **이중합산은 모든 stage를 비례 2배 → closing identity는 우연히 닫혀 closing 검증 통과,
  crosscheck(vs PL)만 잡아냄.** 수정: period 구분이 caption이 아니라 header(`['구분','전기']`)에 있으므로
  `_is_prior_header()` 추가 — 전기-family 헤더만 있고 당기-family 없는 블록 탈락. `pick_combined_agnostic`
  + `_seg_cands` 양쪽 가드. pattern2(코리안리류)는 값연속성이 이미 잡으므로 미변경(surgical).
  → KB라이프 13분기 전부 closing OK, 상각 −2,839.1억(×100=pl 283,905 ✓).
- **코리안리 2025.4Q = 버그 아님(파서 정확).** 재보험사 PL은 string-item 구조(4 원수CSM상각=41,154 +
  **4-1 수재CSM상각=32,210 = 73,364 = wf 상각**). 발행한 보험계약 = 원수(direct)+수재(assumed) 이므로
  wf·pl 둘 다 정답. crosscheck 룰이 pl 쪽 **수재(4-1) 누락**한 false-positive. `validate_master_tables.py`
  crosscheck를 `p = 원수CSM상각 + (수재CSM상각 or 0)`로 수정(출재 9-1은 보유자산이라 미포함).
- **결과: crosscheck 9F→0F (68P/2M/0F/224S), closing 299P/0F 무회귀, 35개사·1825 filled 유지.**
  MINOR 2건(에이비엘 6.9%, 흥국화재 6.4%)은 표간 반올림 구조편차(경고, pass).

## 2026-06-07 — 마스터 검증 정합 + root 마스터 + 당분기 + CSM 정본 승격

마스터테이블 자기완결 검증(`validate_master_tables.py`) fail 대응. 진짜버그 vs 검증룰 오탐 분류 후 수정.
- **item16 부호**: FS-API 기타사업비용 음수반환 → assemble에서 abs 정규화. bridge fail 7건 + 한화 골드 해소.
- **item19 보험금융손익**: KB라이프 등이 `-표준계정코드 미사용-`이라 account_id 매핑 실패 → fetch_dart_fs에
  account_nm fallback(보험금융수익−비용). **item17 투자손익 net 통일**(gross-type 자동감지해 +19,
  gross는 item18 투자이익) → 영업이익=1+17 전사 성립(FS-API 셀).
- **root 마스터**: `PL_breakdown.json`(7727행)·`CSM_waterfall.json`(1830행) = 값(연누계)+값_당분기.
  빌더 `scripts/build_root_masters.py`. 유량=YTD차분, 저량(CSM 기초/기말)=시점잔액(기말 그대로, 기초=직전분기 기말).
- **CSM 정본 승격**: 정본 = `build_csm_waterfall_master.py`(item4=잔차) → diag → build_root_masters가
  읽어 root 출력. 옛 history-chain(item4=literal+전분기 오블록, NULL코드) 대체. **closing 40F→0F,
  crosscheck 136F→9F, CSM 23→35개사, NULL코드 0.** AIG 2025.4Q 단위오류(~1000×) CSM_ABS_CAP 가드.
  build_tidy_exports `meta()`에 DART_NAME_TO_KICS 역alias도 추가(history-chain 다른 출력용).
- **빌드순서**: (PL) build_pl_breakdown → (CSM) build_csm_waterfall_master → build_root_masters(마지막).

## 2026-06-06 (c) — Tier-2 잔여갭 마무리 (답지 0 코드수정 + 한화/롯데 답지)

(b) 이후 사용자가 "아직 안 채워진 곳 답지 요청해" → 정직 분류(코드수정 가능 vs 답지필요 vs 스킵).
대부분 답지 아닌 코드문제로 판명, 추가 6에이전트 분석 → 통합. **주요사 Tier-2 262→287/302, self-check v 205→218.**

### 답지 없이 코드로 (소스에 데이터 존재)
- **미래에셋(KR0079)** 전담 핸들러 `extract_tier2_miraeasset` — 백만원 per-product note(Era-1) + 원-wide
  rollforward(Era-2, /1e6). 4→13/13. (구 _life_product_split 무수정, code-keyed.)
- **흥국화재(KR0005)** `extract_tier2_heungkuk_single` — 2025.4Q/2026.1Q 단일기간(3개월/누적 split 제거 +
  非PAA LOB컬럼 collapse) 버그(4/5=0, item6 implausible) 수정. dispatch single→wide→old. 11→12/13.
- **KB손해(KR0010)** Q3 누적-half — 3개월/누적 split note에서 누적 읽도록 `_pick`. 10→13/13.
- **현대해상(KR0009)** 2023.3Q `_hyundai_old_split` — 구형 split layout([보험계약부채,재보험계약자산]×[3개월,누적]).
- **하나생명(KR0097)** `extract_tier2_hana` + Tier-1 수정(item1=순보험서비스손익 exclude 재보험,
  item16←기타보험비용 alias). 0→2/2.
- **한화손해 OLD(KR0002)** `extract_tier2_hanwha_old` + `_hanwha_dispatch` — 3 단일기간 sibling표
  [장기,일반,자동차], RAW셀 인덱싱(누적=idx5/paired, idx1/single), 천원/1e3, 별도=최소 grand total.
  1→11/13(2023.1Q/2Q만 FS-API Tier-1 부재). **게이트 adj2(+item16) form 추가** — pre-FY2025 손보
  컨벤션 item1=ΣLOB+item16(item16 음수저장) 수용(min에 추가→통과만 늘림, 무회귀).
- **롯데(KR0003)** `_extract_tier2_lotte_combined_bycontent`(2024.2Q/3Q caption-stripped combined) +
  `_extract_tier2_lotte_split`(2025.3Q/2026.1Q per-segment split) + dispatcher. 6→10/12. 2026.1Q 답지 일치.

### 인프라
- **단위오류 sanity cap** (assemble): Tier-2 |값|>1e7 백만원이면 orphan breakdown null (미래에셋 원-unit garbage 차단).

### 답지 검증
- **한화손해 2024.2Q 답지: 12/14 일치** (4/5/6/9/11/13/14/2 정확; **별도엔 퇴직연금 없음=전부 장기/자동차/일반** owner 확인).
  잔여: item10↔12 split(재보 RA 260백만 분배차, item8 소계는 정확), item16 부호(FS-API 한화 기타사업비용 음수반환=Tier-1 이슈).
- **롯데 2026.1Q 답지: 정확 일치** (item11 split만 hand-allocation이라 RC 무관).

### 동양생명 2023.2Q — owner 셀-오버라이드 (FS-API 부재 예외)
FS-API에 FY2023-H1 데이터 없음(status 013) + 노트가 비표준 초기양식(총보험서비스결과 88,324·기타보험비용
40,444 ≠ 스키마 item1 116,208·item16 12,560)이라 표준 파이프라인으로 산출 불가. owner가 포괄손익계산서
까지 제공 → `_GOLD_CELL_OVERRIDE[(KR0087,2023.2Q)]`로 답지값 주입(documented 예외, 학습규칙 아님).
9/10/11/12는 재보 미공시로 None 유지. → 동양 13/13. **주요사 Tier-2 287→288/302, v 218→219.**

### 남은 갭 (구조적 — 수정불가, 합의됨)
- 데이터부재: 롯데 2023.2Q/3Q(반기·3분기 컴포넌트노트 원천부재).
- FS-API Tier-1 부재(item1 앵커 없음): 한화손해 2023.1Q/2Q, 흥국화재 2023.2Q.
- 스킵 합의: AIG(외국계), 서울보증(보증보험=LOB 부적합).
- **신한이지손해(KR0051): PASS(owner 결정)** — PAA 전용 디지털손보, 별도공시 없고 신한지주서 손보분
  발라내기 어려움. Tier-2 비워둠(Tier-1만).
- 한화손해 NEW(2025.2Q+) 13/14: T451 재보 summary가 PAA 과대계상(~21k). OLD는 답지로 정확 확인,
  NEW만 wobble. 후속 정밀화 대상.
- 한화손해 OLD item10↔12 split(재보RA 260백만 분배차, item8 소계 정확) + item16 부호(FS-API 한화
  기타사업비용 음수반환=Tier-1 이슈, 퍼블리싱서 abs 정규화 권장).

## 2026-06-06 (b) — Tier-2 전사 대확장 (병렬 7에이전트 분석 → 직렬 통합 12배치)

사용자 지시: "한화손보만 하지 말고 나머지사들도 병렬로". CLAUDE.md 룰대로 **분석=서브에이전트 7개
병렬(read-only), 통합=메인 직렬(단일 파일 충돌 방지)**. 매 배치 모듈 스모크 + 게이트 무회귀 확인.

### 통합 핸들러/패치 (전부 RC/gold 검증)
1. **한화손해(KR0002) NEW 재작성** — `_hanwha_section` caption 버그('관계기업의 재무정보금액' →
   실제 '(단위:천원)' 불일치로 항상 None) 수정 + `n[0]`(3개월)→`n[JC]`(누적) + LOB순서 [장기,일반,
   자동차]. 단위 천원/1e3. 2025.2Q gold items 4/5/6/9/10 정확 일치, 2/3/8 정확(252,200/250,697/1,503).
   **13/14는 퇴직연금 LOB(3-LOB 컴포넌트표 밖, gold가 수동 배분)로 gold와 상이 → 순수 PAA값 emit**
   (자동차 -21,864 vs gold -5,650). item11 +594 잔차(레시피 acceptable). 1/13→4/13(2025.2Q+).
2. **KB라이프생명(KR0099) 신규** `extract_tier2_kblife` — KB 고유 라벨('서비스제공에 따른 보험계약
   마진의 변동' 등) + 당기/누적 블록선택. code-keyed. RC 정확 closure. 0/13→13/13.
3. **NH농협손해(KR0032) 재작성** — `_ytd_col`(누적) + 섹션라벨 drift(재보험서비스비용↔재보험비용) +
   `_jang_recost`. 4/5/9/10 전12분기 누적정합. 6/11/13/14=data-absent(NH 단일 전사노트, LOB/예실차
   미공시) → item2=전사 보험손익(RC closure용).
4. **코리안리(KR1000)** — `cum`/`comp` stride drift 수정(분기 [3개월,누적] step=2 / FY2025연차+
   2026.1Q 단일 step=1). 2025.4Q·2026.1Q 복구. 11/13→13/13.
5. **현대해상(KR0009) OLD** `_hyundai_old_components` — 결합표 [구분,장기,자동차,일반,합계] 섹션분리,
   천원/1e3, item4/5/9/10 merge-when-None(NEW 2/13/14 무수정). 6/11=미공시. 4/13→10/13.
6. **DB·삼성화재 구형식 single-col (Patch A)** — `_old_lobcum`/`_old_assemble_jang`/`_old_samsung`/
   `_old_db`에 `st`(LOB당 셀폭) 파라미터. 반기/3Q=2(누적 idx1), Q1/연차=1(단일 idx0). 헤더로 감지.
   DB +5분기, 삼성화재 +4분기. 삼성 2024.4Q RC 정확. st=2 byte-identical(무회귀).
7. **KB손해 Q1 (Patch B)** — `_kb_note` 캡션 `<당분기>` 추가. Q1 3분기 복구.
8. **메리츠 Format-B 누적 (Patch C)** — `extract_tier2_sonbo_structured` st-aware(분기 누적 idx).
   결과행 LOB [장기,일반-1,자동차,일반-2] × st. 2024.2Q/3Q·2025.2Q/3Q 복구(8→13/13), 2025.4Q
   gold 보존. 2025.2Q RC 정확 closure(일반=29,590−1,137).
9. **생보 신형식 재보 라벨변형 (afd2-A)** — `_V_RE_REV_ACT`/`_V_RE_COST_EXP`에 신한/KDB/흥국생명
   출재 발생/예상 라벨 추가. item11 채움(검증 무회귀).
10. **교보 item6 (afd2-B)** — `발생한보험서비스수익`→`비용` 라벨오타 수정.
11. **삼성생명(KR0069) OLD 신규** `extract_tier2_samsung_life` — 결합 보험서비스수익/비용 노트의
    출재 섹션에서 9/10/11 추출(누적). NEW(2025.2Q+)는 {} 반환→generic. 9분기 9/10/11 채움.
12. **생보 구형식(a941) Layout 1/2** `extract_tier2_life_old` — L1(한화생명 LOB-컬럼) + L2(농협/
    푸본/KDB/흥국생명 구분-행). 누적/합계 정합. comprehensive 최상단 + parse_filing generic에 배선,
    **NEW CSM 라벨 감지 가드**(rollforward 제외)로 골드 무회귀. 한화생명 4→13/13, 농협/푸본/흥국생명/
    KDB old 채움. (L3 미래에셋은 comprehensive 기존 경로 침범해 제외.)

### 인프라 수정
- **`_reconcile_tier2_unit`를 손보 전용핸들러(SONBO_HANDLERS) 코드엔 스킵** — Tier-1이 FS-API로
  전환된 뒤 HTML `_is_rev`가 신뢰불가(한화손해 2025.2Q HTML 보험수익 1000× 과소 → ratio 670 →
  잘못된 1e-3 리스케일로 정상 breakdown 억제). 전용핸들러는 이미 백만원 emit. 악사 Format-A/
  미래에셋 원-unit은 유지.
- **단위오류 sanity cap (assemble)** — Tier-2 컴포넌트 |값|>1e7 백만원(10조; 실제 최대 ~1.5M)이면
  orphan breakdown 전체 null. 미래에셋 분기 rollforward(원-unit, _jang_rev 부재로 reconcile 미작동)
  494B~585조 garbage 차단. master 전체 0 garbage cells.

### 결과
- master **7703 rows / 315 c-q**. self-check **v 160→205** (+45 reconciled c-q), i 101→50, x=1.
- 골드 게이트 **무회귀** (메리츠/삼성생명/한화생명·롯데·KB·DB·삼성화재·흥국·코리안리·삼성화재24 전부
  0 DIRECT fail; 한화생명 2025.2Q item5/10·DB 2024.2Q item11/14는 기존 documented).
- 주요사 Tier-2 분기 **262/301**.

### 남은 follow-up (이번 미통합/미해결 — 후속)
- **한화손해 13/14 퇴직연금 배분**: 3-LOB 컴포넌트표 밖. 순수 PAA값 emit 중(gold와 상이). owner 판단 필요.
- **한화손해 pre-2025.2Q OLD**: 별도 과목표 핸들러 미작성(8분기 blank).
- **미래에셋 분기(2025.2Q/3Q/2026.1Q)**: rollforward 원-unit → 백만원 emit 핸들러 필요(afd2 Patch D
  미통합, sanity cap으로 garbage만 차단). 현재 4/12.
- **흥국화재 NEW 2025.4Q/2026.1Q**: `extract_tier2_heungkuk`가 연차/최근 단일표 오작동(4/5=0,
  item6 implausible) — 별도 이슈(a104 플래그).
- **롯데 2024.2Q/3Q·2025.3Q/2026.1Q**: 컴포넌트노트 미발견(a5b2 'NEEDS DEEPER PROBE'). 6/12.
- **흥국생명 2026.1Q item6/11 더블링**: `_life_comprehensive` dedup이 caption 공백차로 중복노트 누적
  (item6 −49,068 vs 실제 ≈−24,534) — afd2 플래그, dedup fingerprint 수정 필요.
- **교보 반기/분기 3개월 basis**: `_life_first_num`이 누적 아닌 3개월 컬럼 read(item4-11) — afd2 플래그.
- **한화생명 2023.2Q (x=1)**: FY2023 1차연도 노트 outlier, L1 미포착(기존 broken).

## 2026-06-06 — 구형식(pre-2025.2Q) 손보 핸들러 + 코리안리/흥국 OLD + 병렬에이전트 레시피 (SESSION HANDOFF)

세션 중단(식사). 재개 시 이 항목 + `TODO_parser.md` 먼저 읽기.

### 이번 세션 완료 (전부 RC/gold 검증, master 재빌드됨 — 311 c-q, 7585 rows)
- **DB손해(KR0011)**: 신형식 2025.2Q 핸들러(`extract_tier2_db`) 재작성(caption "연결회사" 버그 + YTD 버그 + 연결/별도 fix) — gold 13/13. 구형식 2024.2Q는 아래 `_old_db`.
- **삼성화재(KR0008)**: 신형식 `extract_tier2_sonbo_component`(범용 손보, 헤더 LOB-인지) — gold 2025.2Q 13/13. **basis 연결→별도 전환**(owner 결정; `fetch_dart_fs.BASIS_CFS`에서 KR0008 제거, 이제 {삼성생명·메리츠}만 연결). 구형식 2024.2Q는 `_old_samsung`.
- **흥국화재(KR0005)**: 신형식 `extract_tier2_heungkuk`(nonPAA/PAA 단일표, 총계행 라벨탐색) — gold 2025.2Q 13/13. 예실차 중복(owner가 답지 수정) 정정.
- **코리안리(KR1000)**: `extract_tier2_coreanre`(재보험사 dual-schema: 생명→item2-12, 장기→**item2-1~12-1 문자항목** via `_extra_items`, 일반→14) — gold 2025.2Q 전항목 일치. **master 스키마 확장**(문자 항목번호) + assemble RC에 `_extra_lob` 추가 + main()에서 `_extra_items` emit + 게이트(`_verify_pl_golds`) 문자항목 지원. **OLD 분기는 `_coreanre_old`**(단일 병합표, 2023.3Q~2025.1Q RC≤1) — 통합 완료, 2/11→11/13.
- **구형식 핸들러 `extract_tier2_old`**(삼성·DB·현대 공용, fallback 체인): `_old_samsung`(섹션-라벨 병합표, 합산 예상, 생명컬럼 없음) + `_old_db`(caption별 분리표, 4분할 예상, 생명컬럼 제외, 원수소계). **robust LOB reader**(`_old_present`/`_old_lobcum`: 재보 합계행의 0-LOB 컬럼 누락을 상대임계값+양끝정렬로 복원). gold: 삼성 2024.2Q 13/13, DB 2024.2Q 10/13(item11/12/14만 DB 재보표 불규칙으로 어긋남).
- **메리츠 회귀 수정**: `extract_tier2_old`가 메리츠 국내/해외·배당 중첩헤더를 잘못 잡아 CSM=0 뱉던 것 → 헤더 가드(`국내&해외`/`배당요소` 스킵) + `abs(item4)>1` 거름. 메리츠 8/13 복원.
- 게이트 `_verify_pl_golds.py`: 경로 `gold/`로 수정, None-gold(Tier-1 blank) skip, 문자항목(2-1) 지원, golds 추가(DB·삼성·흥국·코리안리 2025.2Q + 삼성/DB 2024.2Q). 삼성화재 2025.4Q **연결** gold는 별도전환으로 게이트에서 내림(파일 보존).

### 주요사 Tier-2 현황 (item4 채워진 분기/총분기)
NH 12/12, 코리안리 11/13, KB 9/13, 메리츠 8/13, 삼성화재 8/12, DB 8/13, 롯데 6/12, 현대 4/13, 흥국 3/13, 한화손해 1/13. **Tier-1(item1·17-24)은 전사 100%(FS-API).** self-check: G=4 v=160 i=101 ~=26 x=1.

### ⏭ 미통합 — 병렬 서브에이전트가 역설계+RC검증한 레시피 3개 (재분석 불요, 바로 코딩)
1. **한화손해(KR0002)** — 기존 `extract_tier2_hanwha`가 BROKEN(연차표 읽어 2× — 실제 gold는 **2025.2Q 반기**). 2025.2Q+ 표준노트(`보험수익,예상보험금` row0), **단위 천원→/1e3**, 별도=FS-API `_is_rev` 매칭(min-grand 아님), 누적컬럼(헤더 3개월&누적→off=1 st=2), **예실차에 투자관리비 포함**(흥국/코리안리와 달리), 재보 LOB는 `재보험자에게서 회수` 요약표(cost-row 라벨 2종: `총 재보험비용,잔여보장…` 분기 / `재보험자에게 지급…` 연차). gold 13/15 일치(item11/12 split만 ±594 — residual). 2025.2Q/3Q/4Q/2026.1Q RC=0. pre-2025.2Q는 별도 OLD 과목표(`보험계약마진상각수익`/`위험조정변동수익`/`예상보험금수익`, LOB `합계`행) — 후속.
2. **흥국 OLD(KR0005, pre-2025.2Q)** — 보험종류별 leg-분리표(장기/일반/자동차, 백만원 1.0). REV/RECOST=단일 결합표, COST·REREV=일반모형(장기)+PAA(일반/자동차) 분리. 장기=nums[0]. 구조적 predicate(caption 불신). item6 예실차=예상발생-(발생보험금+직접유지비+손해조사비, **투자관리비 제외**). **RC 컨벤션 주의: FY2023/2024는 item1=item2+13+14 (−16 안 함!), FY2025부터 −16.** 9분기 전부 RC closes(2023.1Q/2Q는 FS-API Tier-1 없음). 신형식은 2025.2Q부터라 quarter-gate로 분기.
3. **현대 OLD(KR0009, 2023.4Q~2025.1Q)** — 요약표(item2/13/14, `_jang_net`)는 기존 핸들러로 이미 RC-close. 컴포넌트(item4/5/9/10)만 추가: row0=`보험수익` + 섹션 `재보험서비스비용` 결합표, **단위 천원→/1e3**, col0=장기, needles `보험계약마진상각`/`위험조정변동`. **item6/11은 추출 불가**(현대 OLD는 보험비용/재보수익 leg 미공시). 2023.3Q=데이터 없음. 2025.2Q=공시누락 예외(Tier-1만).

### 알려진 이슈 / 결정사항
- DB 구형식 item11(재보예실차)·14(일반): DB 재보표 셀 불규칙(장기누적<3개월)으로 ±, RC<25%라 통과하나 ~로 표기. 정밀화 후속.
- self-check ~ 17→26: 삼성/DB 구분기 신규충원분 일부 RC 미세오차(주로 DB 재보).
- 결정: 삼성화재=별도, item19=재보풀네팅(API표준), 예실차 정의 사별 상이(흥국/코리안리=투자관리비 제외, 한화=포함), 코리안리 문자항목 `2-1`, DB 답지 시트 공시분기 "2024.4Q"는 오타(실제 2024.2Q).

## 2026-06-05 — 삼성화재(KR0008) PL Tier-2 답지 통합 + 범용 손보 컴포넌트 핸들러 + 별도 전환

답지 `gold/보험손익 breakdown_삼성화재_2025.2Q.xlsx` (분기, Tier-2 only). 기존 삼성화재 분기 Tier-2는
거의 비어있고(3/11) 채워진 2025.3Q는 자동차손익=1,293,510 같은 쓰레기값(self-check wobble)이었음.

신규 **`extract_tier2_sonbo_component`** (삼성화재 gold-validated, 범용): 표준 IFRS17 컴포넌트
노트가 **단일 표**(행0=LOB 총계, 아래 CSM상각·위험조정·보고기간발생(기초예상) 행). DB와 다른 점 —
컬럼순서 **장기/자동차/일반**(DB는 장기/일반/자동차)이라 **헤더에서 LOB 순서 읽음**, **예실차=단일
합산행**(보고기간발생 기초예상 − 발생보험금 및 그밖), 재보 **PAA 블록 없음**, 재보 총계행이 **첫 행**.
별도 선택은 DB와 동일 'grand total 최소'. 라벨 변형 상수(`_S2_CSM` 등) 재사용, 예실차는 합산행/4분할
둘 다 지원. SONBO_HANDLERS에 KR0008 연결 + **fallback 체인 1순위**로 배선(타 손보 신형식 자동 포착,
RC-gate가 오추출 억제). fleet 빌드 중 빈 `보험수익` 행0로 인한 IndexError → pmin 가드 추가.

검증: **2025.2Q gold Tier-2 13개 전부 일치**. 신형식 4분기(2025.2Q~2026.1Q) 전부 RC≈0 → 'v'
(2025.3Q 쓰레기값 교정). 구형식 7분기(2023.3Q~2025.1Q)는 DB와 동일하게 컴포넌트 노트 부재.

**basis 결정 (owner 2026-06-05): 삼성화재 연결→별도(OFS).** 두 답지가 basis 불일치였음 —
2025.2Q=별도(item1 935,731=FS-API 별도), 기존 2025.4Q=연결(1,483,034=FS-API 연결). 연결은 해외
일반/자동차 자회사를 끌어와 LOB 분해를 왜곡(자동차손익조차 연결 −121,722 vs 별도 −111,241로 갈림).
owner가 별도 통일 선택 → `fetch_dart_fs.BASIS_CFS`에서 KR0008 제거(이제 {삼성생명, 메리츠}만 연결).
기존 4Q 연결 답지는 게이트에서 내림(파일 보존); 삼성화재 기준 = 2025.2Q 별도 답지. self-check
v 152→154, ~ 17→15. 회귀 없음.

## 2026-06-05 — DB손해(KR0011) PL Tier-2 답지 통합 + 핸들러 재작성

답지 `gold/보험손익 breakdown_DB.xlsx` (2025.2Q, Tier-2 only — Tier-1은 FS-API라 포괄손익계산서 미제공).
기존 `extract_tier2_db`는 3중 버그로 전 분기 `{}` 반환 중이었음:
1. **caption "연결회사" 요구** — 실제 DB 표 caption은 `(단위:백만원)`/`발행보험의 보험수익 분석 공시`. 매칭 0.
2. **YTD 버그** — `_firstlab`가 `ns[0]`(장기 3개월)을 읽음. 누적이 아니라 3개월치 추출.
3. **연결/별도 미구분** — 노트가 당기/전기 × 연결/별도 4벌. LOB(13/14)·총계가 basis로 갈림.

답지 레시피를 역설계해 핸들러 재작성 (장기 원수/재보 컬럼, 누적):
- 당기 선택: 직전이 `전기/전반기` 1행 마커인 표는 비교용 → 제외.
- 별도 선택: 별도 ⊆ 연결 → 당기 후보 중 **grand total 최소** = 별도(연결은 DB생명 자회사 포함).
- 누적 컬럼: 반기/3Q는 `[3개월,누적]` 쌍(off=1,st=2), Q1/연차는 단일컬럼(off=0,st=1) — 헤더로 자동.
- item9/10 재보 CSM/RA = **−(원시값)** (−abs() 아님; 재보비용 CSM 원시 음수 → item9 양수).
- LOB 13/14 = (보험수익−보험비용)+(재보수익−재보비용) per LOB; 재보비용은 non-PAA+PAA 블록 합산.
- item6 예실차 = (예상 보험금/유지비/손조비/투자관리비) − (발생 동일 4종), 장기 원수 누적.
- `_jang_*` 4종 emit → `assemble`이 item 2/3/7/8/12 파생.

검증: **2025.2Q gold 0 DIRECT fail (13개 Tier-2 항목 전부 일치).** LOB 요약표 임계값 `>=6→>=4`로
낮춰 Q1/연차 단일컬럼도 포착 → **신형식 4분기(2025.2Q·3Q·4Q·2026.1Q) 전부 RC_miss≈0** (self-check 'v').
**구형식 9분기(2023.1Q~2025.1Q)는 데이터 부재**: DART에 "발행보험의 보험수익 분석 공시" 컴포넌트
표가 2025.2Q부터 도입 — 그 이전은 rollforward만 있어 CSM상각-단위 분해 불가(답지로도 메울 수 없음).

gold gate 정비: 경로 `gold/` 접두 해석(파일이 루트→gold/로 이동했었음), 빈 gold 셀(Tier-1) skip,
KB 같은 partial gold는 `CLAIMED`로 선언 항목만 검증. **DB·KB 0 DIRECT fail.** 남은 RED는 무관한
기존 이슈 1건뿐: 한화생명 2025.2Q item5/10 RA 미세차(0.74%/24%, KR0068 핸들러, 미수정).

## 2026-06-04 — PL 전사 전분기(2023.1Q~2026.1Q) sweep + Tier-1 일반화 (broken 44→0)

사용자 지시: "전분기 PL을 이번 lesson으로 다 추출. 답지-specify 하드코딩 말고 rule을 학습해
다른 회사/분기에 응용. 최대한 맞추고 진짜 답지 필요한 것만 몇개 요청." → 무답지 self-check 도입 후
일반 규칙 6종으로 broken 44→0.

신규 keeper: **`scripts/_pl_selfcheck.py`** → `docs/pl_selfcheck_matrix.md` (G/v/i/~/x).
보편 항등식만 신뢰: **22=20+21**(세전=영업+영업외), 24=22-23. `20=1+17`은 비보편(기타영업
구조사는 깨짐)이라 정보성 struct-note로만. Tier-2↔보험손익 RC는 **컨벤션 무관 dual-form**
(item1 ≈ ΣLOB 또는 ΣLOB+15-16).

일반 규칙(회사코드 하드코딩 0, 신규 per-company 분기캡션 0):
- **FIX A 우선순위 NI** (`_pick_priority`): 당기순이익 > 계속영업이익(손실). 중단영업=0이라
  계속영업이익==영업이익이 당기순이익보다 위에 찍히는 포맷(ABL 등)에서 NI를 영업이익으로 오추출 → 해결(8셀).
- **FIX B 법인세 잔차**: item22·item24 둘 다 있으면 item23=item22-item24. DART 법인세 부호
  컨벤션 차이/오추출(현대·DB손해·롯데·악사…) 일괄 해결(12셀). 골드 무영향(이미 정합).
- **FIX C 항등식-우선 basis 선택**: 정렬키를 (hint, ident_ok, prio, |ni|)로 격상 — 영업이익=
  보험손익+투자손익 성립을 basis 선호(+5)보다 우선. 연결(비보험 자회사 fold)→별도 자동전환(AIG 등). 골드 4사 무회귀.
- **각주-ref 가드** (`_drop_footnote`): numbered 손익계산서(I~X)의 주석번호(주29 등)가 첫 컬럼
  데이터로 섞이는 것 제거. 하나생명 영업외/법인세 오추출 → broken 해소.
- **Tier-2 단위정합** (`_reconcile_tier2_unit`): Tier-2 _jang_rev를 Tier-1 _is_rev와 대조,
  장기보험수익은 총보험수익의 부분이어야 하므로 ratio ~1e3/~1e6면 천원/원으로 판정해 ×1e-3/1e-6. 악사 LOB note(천원) 보정.
- **abs-cost fallback**: 생보 income-statement fallback에서 비용 legs(보험비용/재보험비용)에 abs()
  — 미래에셋 FY2023 보험비용=(659,299) 음수표기로 item3 덧셈돼 6× 과대 → 해결. (양수회사 무영향)
- **롯데 Tier-2 일반화**: 기수(`<제81(당)기>`)·주석번호(30./31.) 하드코딩 제거 → 섹션-워커.
  통합표(FY2023/24 `보험손익 및 재보험손익` 1표)·분리표(FY2025 2표) 양형태 처리. FY2023.4Q/FY2024.4Q 신규 추출, FY2025 무회귀.
- **RC-게이트**: ΣLOB가 보험손익과 25%↑ 어긋나면 breakdown(2-14) 억제, Tier-1 유지. garbage 미배출.
  억제셀 = 골드후보 자동집계(coverage.tier2="suppressed").

**결과:** broken(x) **44→0**, self-check **G4/v88/i81/~11**, .206(미상장 Q1-Q3 설계상 공란).
Tier-2: reconcile 103 / 억제 19 / 없음 240 / partial 91. 골드게이트 무회귀
(삼성화재24·메리츠24·삼성생명22[기존 item19 split]·한화생명23).
잔여 wobble 11 = 중간갭<25%(2023첫해·메리츠 Q1·롯데 Q1·악사 2024 — 방향성 OK).
**골드후보(Q4 연차 6셀/5사) → [`docs/pl_gold_needed.md`](pl_gold_needed.md):** 롯데손해 2024.4Q(중요·item1 모호),
한화손해 2025.4Q(기존 NB-rowspan), 하나생명 2024/2025.4Q·악사 2025.4Q·교보라이프 2024.4Q(소형).
분기(Q1-Q3) 억제 13셀=메리츠·현대·삼성화재 — 분기 주석/통계 불안정, Tier-1은 유지(저우선).

## 2026-06-04 (b) — 롯데 PL 답지 통합 + 재작성-영향표 제외 (PL 골드 5장)

사용자 `보험손익 breakdown_롯데_2024.xlsx` 제공. 답지가 롯데 2024.4Q 원인을 정확히 짚어줌:
- **근본원인 = 재작성-영향표 오추출.** 추출기가 고른 item1=468,499는 "**재무제표의 소급재작성이
  포괄손익계산서에 미치는 영향**" 표의 `[재작성후, 영향, 재작성전]` col0 = **2023년 재작성치**였음.
  진짜 statement는 "요약손익계산서" col0 = **177,845**(=답지). 둘 다 20=1+17 성립이라 FIX C로 구분
  안 됐고 |ni| 타이브레이크가 더 큰(틀린) 쪽 선택.
- **일반 규칙(하드코딩 0):** `_is_income_statement`에서 캡션에 **"미치는 영향"** 포함 표 제외. 단,
  "재작성"·"소급재작성" 단독은 정상 statement 각주(한화생명 "…소급재작성 하지 아니하였으며…")에도
  나오므로 **"미치는영향" 문구로만 한정**(처음 광범위 매칭이 한화생명 23→11 회귀시켜 정밀화).
- **_is-fallback 가드:** 생보 item2/3/8 fallback에서 보험비용이 보험수익의 10% 미만(near-zero
  오추출)이면 생략 → item2/3/8=None, **note 기반 items 4-11은 보존**(교보 2025.4Q: FIX C가
  보험비용≈0 statement로 바꿔 게이트가 정상 note까지 억제하던 부작용 차단).
- **결과:** 롯데 2024.4Q **답지 23/24 정확 일치**(item1=177,845·item2=222,982·item4=225,448
  …item24=24,221; 유일 불일치 item15 None-vs-0). 골드 **5장**: 삼성화재24·메리츠24·삼성생명22
  (item19 split)·한화생명23·롯데2024 23. **무회귀.** self-check **G4/v89/i74/~11/x0**.
- 재작성-영향표만 있던 분기셀 4개(impact-prior garbage) 제외 → 260→256 cq(정합 개선). 골드후보
  Q4 6→**3셀**(교보라이프·악사·한화손해NB = 소형/기존defect). `docs/pl_gold_needed.md` 갱신.

## 2026-06-04 (c) — 상장사 분기 확장: IFRS4↔17 전환표 col + 헤더기반 재작성 제외

사용자 지적("미상장사 빼면 상장사 분기/연차 구조 비슷할 것, 시도해봐"). 맞았다 — 분기 미추출은
구조 차이가 아니라 **고칠 수 있는 버그**였다.
- **근본원인:** 삼성화재 등은 분기 포괄손익계산서를 **IFRS4↔17 전환비교표**로만 노출(헤더
  `기준서1104호(A) / 기준서1117호(B) / 증감(B-A)`). 추출기가 col0(=구 1104호, 보험손익 −493,436)을
  읽어 음수 garbage → 자동 제외돼 분기 전체가 "."였음. **진짜 IFRS17 값은 col1(1,538,847)**.
- **일반 규칙 2건:** ① `_is_transition_table`(헤더에 1117호) 감지 → extract_tier1이 그 표를
  **col=1(1117호)로 읽음**(`_pick_line/_pick_priority`에 `col` 인자 추가). ② 재작성-영향표 제외를
  **캡션→헤더 기반**으로 전환(`_is_income_statement`): 헤더에 `소급/재작성/수정전/수정후` → 제외.
  (캡션은 분기보고서에서 긴 회계정책 문단이라 "미치는 영향"이 우연히 섞여 정상 statement까지
  오제외하던 문제 해결 — 삼성화재 분기 statement가 캡션필터에 걸리던 것 복구.) 롯데 impact표는
  헤더 `소급 전/재작성효과/소급 후`로 여전히 제외, 한화생명 정상 statement(헤더=기수)는 유지.
- **결과:** **삼성화재 분기 2024.1Q~2025.3Q 복구**(item1=IFRS17, 20=1+17 성립). 골드 5장
  무회귀(삼성화재 24/24 — 연차는 실제 statement 유지, 전환표 안 씀). cq 256→**260**, `.` 212→**207**.
  self-check **G4/v90/i76/~13/x0**. 상장사 대부분 분기 Tier-1 보유(삼성화재·메리츠·현대·KB·DB·
  롯데·삼성생명·코리안리·동양·미래에셋).
- **남은 갭:** **한화생명 분기** = 반기/분기보고서가 요약재무정보(영업수익/영업이익/세전/당기순)만
  노출, 보험손익 분해 IFRS17 포괄손익계산서를 parseable하게 안 담음(포맷 상이, 완화 시 false-match
  위험 커서 보류). **Tier-2(분해 4-14) 분기**는 여전히 noisy(분기 LOB 주석 미정합 → RC 게이트 억제).

## 2026-06-05 (g) — Tier-1 전사 DART 표준 FS API 전환 (HTML 손익계산서 파싱 졸업)

사용자 지시(2026-06-04): "FS API로 Tier-1 전사 다 맞춰라, HTML Tier-1 코드는 archive." + 스모크
테스트로 검증 요구. → FS API가 **표준화돼 있음 확인**(account_id 일관): 보험손익=
`ifrs-full_InsuranceServiceResult`, 투자손익=`dart_InvestmentIncomeExpenses`, 영업이익/세전/
법인세/당기순=`ifrs-full_ProfitLossFromOperatingActivities/BeforeTax/IncomeTaxExpenseContinuing/
ProfitLoss`. account_nm은 회사마다(보험손익/보험서비스결과, 당기순/반기순/연결반기순) 달라도 id로 매핑.
- **신규 `scripts/fetch_dart_fs.py`**: corp_code를 회사명으로 런타임 검색(영구매핑 금지 룰 준수,
  KB라이프/IBK연금만 별칭), fnlttSinglAcntAll OFS/CFS fetch+캐시(`data/dart/_fs_api_cache/`),
  account_id→24항목 매핑. **반기/분기는 `thstrm_add_amount`(누적/YTD)**, 연차는 `thstrm_amount`.
  HTML이 겪던 3개월/누적·전환표·재작성표·반기순이익 문제가 API에선 원천 소멸.
- **basis(별도/연결)**: 기본 OFS(별도=방법론), 연결-headline 그룹만 CFS = {삼성화재·삼성생명·메리츠}
  (골드 item24가 연결값). item19(보험금융손익)=**재보험 풀-네팅**(보험금융수익−비용+재보험금융수익−비용)
  으로 통일 — 답지가 회사별로 재보험 반영을 들쭉날쭉했어서 **API 기준으로 통일**(사용자 지시). item21=
  세전−영업이익 잔차(22=20+21 보장), item15=0(API에 기타영업수익 단독계정 없음).
- **통합**: `build_pl_breakdown`가 Tier-1=FS-API(실패시 HTML fallback), Tier-2=HTML 유지.
  구 `extract_tier1`(+전환표/재작성표/누적 휴리스틱)은 **DEPRECATED, fallback-only**(배너 표시;
  감독 하에 scripts/archive/ 이전 예정).
- **결과(골드-게이트, 무회귀)**: Tier-1 전 골드 0 DIRECT fail(삼성화재·메리츠 24/24·삼성생명·한화생명·
  롯데). **company-quarters 292→308**(FS-API 257 / HTML-fallback 35; API가 HTML 못 잡던 16셀 채움).
  self-check **G4/v147/i121/~19/x1**. item15/19는 게이트 DIRECT에서 제외(API 표준, 답지 불일치 OK).
- 잔여 wobble/fail = Tier-2 영역(KB 부분추출·한화 2025.2Q 위험조정·2023 첫해) — Tier-1 아님.

## 2026-06-04 (f) — KB PL 분기 분해 (CSM상각 단위), KB-전용 격리 핸들러

사용자 `보험손익 breakdown_KB.xlsx`(2025.2Q) + 지적 2건: ① **Tier-1(보험손익/투자손익/영업이익/
당기순)은 DART 표준 FS API로 받는 게 맞다** — HTML 표 파싱(반기순이익·누적·전환표·재작성표 삽질)은
잘못된 레이어. 분해(Tier-2)만 주석이라 손파싱 불가피. ② **공유코드 만져 푸본 깨먹지 마라** — 사별 격리.
- **KB-전용 분기 핸들러**(`_kb_quarterly_note`+`extract_tier2_kb_quarterly`, extract_tier2_kb의
  None-분기에서만 호출 → **KR0010 외 무영향, 공유코드 무수정**). KB 분기 `(4) 보험손익 상세내역`은
  `[3개월, 누적]` 다열이라 **누적(YTD) half**를 읽음.
- **답지-clean 추출(검증):** 원수 CSM상각(4)=423,962·위험조정(5)=100,970, 재보험 CSM상각(9)=
  −1,538·위험조정(10)=−4,377, 자동차(13)=8,562 — **전부 답지 일치.** KB 분기 9개(23.2Q~25.4Q)에 적용.
- **미배출(오값 방지):** 장기손익(2)/일반(14)/보험손익(1)은 **KB가 기타사업비용을 부문별로 차감**한
  값이라(주석 총 보험서비스결과는 차감 전 491,164/29,205) 별도 부문별 기타사업비용 표가 필요 → 추후.
  예실차(6/11)는 발생사고 ICF 변동 포함이라 단순 예상−실제와 불일치 → 보류.
- 골드게이트: 기존 6장 전원 무회귀(삼성화재24·메리츠24·삼성생명22·한화생명23·롯데23·한화 2025.2Q 20).
  KB 2025.2Q는 partial(분해 5 + Tier-1 일부).
- **TODO(다음):** (a) Tier-1 → **DART 표준 FS API**로 전환(income-statement 파싱 졸업), (b) KB 부문별
  기타사업비용 표 연결로 item1/2/14 완성.

## 2026-06-04 (e) — KB 손보 CSM 분기 답지 → 통합 net표 인식 일반수정 (KB 4/13→12/13)

사용자 `CSM waterfall_KB손보.xlsx`(2025.2Q) + 원칙 지시(만능 파서 강요 X, 사별 핸들러 OK, 단
**타사 로직 먼저 적용 + 검증 후 답지는 마지막** — `docs/agents/claude-agent-parser.md` ⭐에 영구기록).
- **진단(타사 대조):** KB 연차(2025.4Q)는 PASS인데 분기만 0/6. `block_stages`는 KB 분기 블록에서
  **기초=8,820,482(=답지) 정확히 추출** — 즉 추출 OK, **선택만 실패**. 원인: KB 분기 CSM rollforward
  가 `(3)순보험계약부채 및 순재보험계약자산` **통합표**라 캡션·행에 "재보험"이 있어 `pick_combined_agnostic`
  의 출재-배제 필터에 통째로 걸림(타 손보는 배당/측정요소 캡션이라 안 걸림).
- **일반수정:** 통합 net표 = 캡션에 **`보험계약부채` AND `재보험계약자산` 둘 다** 있을 때만 출재-배제를
  건너뛰고 keep(block_stages가 원수 보험계약마진을 읽음). 그 외(푸본 generic `기말보험계약부채`, 농협
  출재 sub-note 등)는 **원본 로직 그대로** → 무회귀. anchor(전년 Q4 기말)로 당기/전기 구분.
- **결과:** KB 2025.2Q 답지 PASS(기초 88,204.8·신계약 8,142.3·이자 1,623.5·조정 −1,554.8·상각
  −4,239.6·기말 92,176.1 억, 전부 일치). **KB CSM 4/13 → 12/13.** 게이트 104/108 → **110/114(19장)**,
  푸본현대 회귀 적발 후 좁혀서 복원. 상태표 **G19/c251/~34/?1**. 잔여 wobble=대부분 2023 첫해(무관).

## 2026-06-04 (d) — 한화생명 분기 답지 → 반기순이익 + YTD(누적) col 일반수정 (분기 전사 교정)

사용자 `보험손익 breakdown_한화생명_2025.2Q.xlsx`(별도) 제공. 다운로더가 "본문에 다 있음, 파서
매칭" 확인해줌. 본문 해부 → **두 가지 일반 버그**가 분기 추출을 광범위하게 막고 있었다:
- **(1) 반기/분기순이익 라벨:** 분기·반기보고서 포괄손익계산서는 당기순이익이 아니라 **"반기순이익/
  분기순이익"**으로 찍힘. `_is_income_statement`의 has_ni와 NI picker가 "당기순이익"만 봐서 분기
  statement 자체를 통째로 놓침(한화생명 분기 0개의 진짜 원인). → `NI_LABELS`에 반기/분기순이익 추가.
- **(2) 3개월 vs 누적(YTD) 컬럼:** 분기 statement는 `[당3개월, 당누적, 전3개월, 전누적]` 4컬럼.
  스키마는 YTD인데 추출기가 col0(3개월)을 읽어, 잡혀도 **분기-only 값**(누적 아님)이 됐음.
  `_ytd_col`(헤더에 3개월+누적이면 누적 col=1) 추가 → extract_tier1이 누적 컬럼을 읽음.
- 한화생명 별도 statement(표986: 보험손익 175,999/투자손익 14,893/영업이익 190,892/반기순이익
  179,701, col1=누적)를 정확히 잡음. 답지 **20/24**(Tier-1 전부 정확; item5/10 위험조정만 0.7%/소액).
- **파급(검증됨, 회귀 아님 — YTD가 올바른 스키마):** 삼성생명 분기 677/794/761(3개월)→677<1471<
  2232<2452(YTD), 현대 203/248/183→203<451<634, **삼성화재 1627/1627/1627(전환표 상수
  garbage)→609<1247<1786<2020**. 분기 당기순이익 시계열이 비로소 단조 누적.
- **결과:** company-quarters 260→**292**, `no_income_statement` 149→**60**, self-check
  **G4/v125/i125/~17/x1/.118**(was .207). 한화생명 분기 10개 복구, 상장사 대부분 분기 8-10개 보유.
  **연차 골드 6장 무회귀**(annual 헤더는 제X기라 _ytd_col=0, 무영향). Q4 골드후보 3→**1**(교보라이프뿐).
- 잔여: **x=1 한화생명 2023.2Q**(첫해 statement 영업외 행 컬럼수 불균일→col1 정렬 어긋남, 1/292
  셀, self-check 플래그). 분기 Tier-2(분해) 일부 noisy(RC게이트 억제 24셀). 둘 다 저영향.

## 2026-06-03 (d) — CSM 골드 7장 받아 BROKEN/large-wobble 해소 (게이트 86/90)

사용자가 CSM waterfall 답지 7장 제공(농협·롯데·DB손보·동양 2025.2Q·삼성생명 2025.1Q·교보·미래에셋).
신규 게이트 **`scripts/_verify_csm_golds.py`** — repo의 "CSM waterfall_*.xlsx" 자동 발견, 6단계 대조.
골드 시트가 사망/건강/연금저축 **컬럼 분할**인 경우 합산이 총계(삼성·미래) → 게이트가 컬럼 합산.

- **삼성생명 2025.1Q (70,969→129,020):** `_anchor_segment_sum` 추가 — 분기는 anchor(=Q4 기초=연초)가
  있으므로, 단일블록이 anchor와 안 맞고 **major opening-cluster 합이 anchor와 일치하면** 그 합을 사용.
  출재 잡블록(최대 클러스터의 10% 미만) 배제. anchor 검증이라 over-sum/타사 오작동 불가. 5/6(6번째 조정=이자 반올림 0.03%).
- **교보 2025.4Q (53,397→64,381) / 미래에셋 2025.4Q (19,956→20,782) / 푸본현대 2025.4Q (1,494.5→1,423.5):**
  연간(anchor 없음) 교차-세그먼트. 회사 스코프로 한정(타사 무영향): 교보·푸본(KR0073·KR0083)=무배당+유배당+변액
  캡션 교차 합산(`_opening_clusters`+`_drop_prior`로 전기 제거); 미래에셋(KR0079)=배당·상품별 두 분해 공존 →
  상품별 분해만 합산(중복 방지). `pick_combined_agnostic(blocks, anchor, code)`로 code 전달.
- **롯데·DB손보·동양 2025.2Q:** 마스터가 이미 정답(직전 다운로더 재sweep 반영분)이었음 — 골드로 확정.
- **결과:** 사용자 골드 **9사**(+푸본현대) 전원 통과, 기존 8 기초-골드 무회귀(`_verify_csm_all` OK), 게이트 **92/96**.
  잔여 4셀: 삼성생명 2024.4Q 이자(1.5% 반올림), 삼성생명 2025.1Q 조정(이자 반올림 residual), 한화손보 신계약/조정(기존 NB rowspan).
- **3색 상태표 → [`docs/csm_status_matrix.md`](csm_status_matrix.md)** (생성기 `scripts/_csm_status_matrix.py`):
  27사×13분기를 G/c/~/?로 분류. 2025.4Q 연간 컬럼은 주요사 전부 G/c.

## 2026-06-03 (e) — 당기/전기 stacked 블록 일반 수정 (미래에셋 전분기 평탄화)

미래에셋 2025.1Q 답지로 확인: wobble이 restatement가 아니라 **추출기 버그**였다. 미래에셋 상품군
테이블은 **한 블록에 당분기 THEN 전분기가 쌓여**(두 개의 "기초 잔액" 행), `extract_stages`가 전분기
기초(사망 9,691억)를 당분기(7,859억) 대신 읽었다. **`block_stages`가 extract_stages 호출 전에
"전분기/전반기/전기" 경계에서 행을 잘라 당기 구간만** 보게 수정 — 회사코드 무관 일반 규칙(단일기간 블록엔 no-op).
- **결과:** 미래에셋 거의 전 분기 `~`→`c`, 2025.1Q+2025.4Q 골드 통과. **게이트 98/102(17장), 기존 8 무회귀, wobble 44→38.**
- 답지가 "버그 vs restatement"를 갈라준 케이스 — 사용자 지적이 정확했다.

## 2026-06-03 (f) — 분리 sub-portfolio 합산 일반화 (교보·푸본·신한라이프 코드스코프 제거)

신한라이프 답지로 확인: 신한 총계 = 무배당(69,696) + 변액(1,359) + 유배당(1,185) = 72,241 — 교보·푸본과 동일
"무배당+유배당+변액 합산" 패턴. 교보/푸본은 코드스코프(KR0073/KR0083) 하드코딩이었고 신한(KR0094)만 빠졌던 것.
**크기 기반 일반 규칙으로 교체(코드스코프 제거):** 클러스터(전기 drop, 별도/연결 collapse) 중 **2번째 큰
클러스터가 최대의 40% 미만이면 분리 sub-portfolio → 합산**; 40% 이상이면 별도/연결 쌍 → MIN(별도).
캡션 무관 → 교보·신한(명시 캡션) + 푸본(제네릭 캡션) 다 처리, 한화생명(별도 9.24M/연결 13.30M=69%) 안전,
미래에셋·삼성(상품마커, 40%↑)은 기존 seg 경로.
- **결과:** 교보/푸본/신한 전부 골드 통과, **신한라이프 전 분기 평탄화**, 기존 8 + 9 user 골드 무회귀.
  **게이트 104/108(18장), wobble 38→34.** 잔여 4셀=삼성 2024.4Q 이자·2025.1Q 조정 반올림 + 한화손보 NB(기존).
- 잔여 wobble 34 = 대부분 2023 과거연도(gold 없음, 표구조 상이). 회사코드 하드코딩 **0** 달성.
- **PL:** 농협생명 PL 답지도 24/24 통과(self-check가 실제 골드로 확증). goldmap → `docs/csm_coverage_goldmap.md`.
- ⚠️ 교보 골드시트 내부 셀이 "삼성생명 2025.1Q"로 복붙오기 — 게이트는 FILE_OVERRIDE로 우회. 시트 셀 교정 권장.

---

## 2026-06-03 (c) — PL Tier-2 전사 확장 (답지 없이 self-check 검증) + Tier-1 item1 4건 수정

사용자 지적 반영("답지 달라 하지 말고 내가 준 데이터로 시도부터 해라"). LOB note 미매칭사 12곳을
회사별 원문 표 구조를 규명해 핸들러로 흡수. 답지가 없는 회사는 **Tier-1 보험손익(item1) reconciliation**
(`item2+15−16` 생보 / `장기+자동차+일반+15−16` 손보)으로 self-check. **16사 전원 gap ≤0.04% PASS.**

**병렬 조사(서브에이전트 4):** 손보 KB(KR0010)/현대(KR0009)/한화손해(KR0002), DB손해(KR0011)/NH농협손해(KR0032)/
롯데손해(KR0003)/코리안리(KR1000); 생보 교보(KR0073)/DB생명(KR0082)/동양(KR0087), 신한라이프(KR0094)/농협(KR0104)/
흥국생명(KR0071)/케이디비(KR0072)/미래에셋(KR0079)/푸본현대(KR0083). 회사마다 단위(원/천원/백만)·컬럼순서·
라벨변형·단일통합표 vs 분리표·계약유형별 vs component-decomposition이 달라 `extract_tier2_*` 핸들러 12개 추가,
parse_filing에 code-keyed 라우팅. 생보 일부는 별도 basis + IS sub-line으로 item3/8 도출.

**Tier-1 item1 4건 수정(회사 스코프, 골드 불변):** 현대 809K→396,111(별도), 한화손해 206→206,270(천원 단위버그),
코리안리 226K→223,754(해외포함 statement 제거), 교보 371K→391,590(별도). TIER1_HINTS dict로 해당 코드만
selection bonus, 타사·골드는 byte 불변.

**골드 게이트(독립 재검증):** 삼성화재 24/24·메리츠 24/24·삼성생명 22/24 불변, **한화생명 19→23/24 개선**
(파생 2/3/8/12 도출). 무회귀. **커버리지 2025.4Q ok 4→13.** 맵 → [`docs/pl_breakdown_coverage.md`](pl_breakdown_coverage.md)
(생성기 `scripts/_pl_coverage_map.py`).

**남은 갭(답지 불요):** raw_not_extracted(다운로더 갭=document.zip만), no_income_statement(파서확장),
구조적 N/A(NH 6/11·코리안리 13/14·미래에셋 6 — note에 분해 없음). 회사별 구조 메모는 `scripts/_plprobe_*.py`.

**다운로더 수정 후 재sweep (같은 날):** downloader가 13사 본문 XML(`_00760` 연결/`_00761` 별도) 추출 완료
→ PL/CSM 재실행. 파서 코드 변경 불필요(`*.xml` glob). **raw_not_extracted 2025.4Q 13→0, 전체 151→121**;
PL 194→260 cq, 2025.4Q ok 13. 골드 무회귀(PL 24/24·24/24·22/24·23/24, CSM 8/8) 독립 재검증.
잔여: no_income_statement 소형·외국계 7사(라이나·IM라이프·메트라이프·처브·IBK연금·카카오페이·KB라이프 —
포괄손익계산서 본문에 있으나 보험손익 소계 없는 번호식 포맷, Tier-1 확장 필요, **사용자 보류 결정**);
downloader 재확인 2건(하나손해 XML 테이블 0개; BNP파리바 IS 미검출). 비상장사 = Q4만/FY24·25만(구조적).

---

## 2026-06-03 (b) — PL breakdown 24항목 추출기 신규 + 전사·전분기 sweep

야간 자율작업(서브에이전트). 사용자 요청: PL breakdown 전사·전분기 파싱 + 안 되는 사/시점 gold 요청.

**신규 `scripts/build_pl_breakdown.py`** (기존 `build_net_income_breakdown.py` 무손상) →
`data/dart/viz/pl_breakdown_master.json` (4,656행 = 194 company-quarter × 24항목, 단위 백만원).
- 2-tier: **Tier-1** 포괄손익계산서(항목 1,15-24; 손보 "보험손익"/생보 "보험서비스결과", 연결·별도 basis-aware),
  **Tier-2** 발행/재보험 note(원수 4,5,6 / 재보험 9,10,11 / 손보 자동차·일반 13,14). 파생 2,3,7,8,12=스키마 항등식.
- note 3종 포맷 대응: 컬럼형 장기/자동차/일반(삼성화재류), 메리츠 "(재)보험손익 상세내역", 생보 계약유형별.

**gold 4사 (2025.4Q, 허용 max(0.5%,±1백만)):** 삼성화재 24/24·메리츠 24/24·한화생명 19/24(직접추출 전부 통과,
잔차 2/3/7/8/12 null)·삼성생명 22/24(항목18/19만 0.67% — gold의 투자/금융손익 분리가 스키마 외 조정, 파싱오류 아님).
검증 = `scripts/_verify_pl_golds.py`.

**커버리지(453 company-quarter 탐색):** ok 9 / partial 161 / no_income_statement 132 / raw_not_extracted 151.
Tier-1은 포괄손익 있는 거의 모든 공시 커버; LOB note(4-14)는 대개 FY2025+에만 존재. 맵 → [`docs/pl_breakdown_coverage.md`](pl_breakdown_coverage.md).

**gold-needed(2025.4Q, Tier-1 정상·LOB note 미매칭):** 손보 한화손해·롯데손해·현대해상·KB손해·DB손해·NH농협손해·코리안리,
생보 교보·DB생명·동양·신한라이프·농협생명. **파서밖:** no_income_statement(하나손해·KB라이프=파서확장),
raw_not_extracted(2025.4Q 13사=document.zip만 존재 → downloader 갭, 에스컬레이트).

---

## 2026-06-03 — CSM 2024 생보 + 분기검출 전면 안정화 (gold 8/8), 회귀 점검

야간 자율작업. 사용자 요청: CSM 전사·전분기 끝까지 + 안 되는 사/시점 gold 요청 목록.

**삼성생명 이자효과 환율 가산 (2024/2025 통일):** `pattern2_stages.find_interest()` 추가 —
이자 = "보험계약의 순 금융손익" + "환율변동효과 등"(있으면). 2024 사망 190,497+7,003=197,500(gold✓),
2025는 환율행 없어 불변. (사용자 IR 공시 기준 수정 요청)

**2024.4Q 생보 별도 검출 (gold 신규 2건 통과):**
- 한화생명 2024.4Q: 본문에 별도(9,238,488)·연결(13,296,823) full-book 둘 다 → 별도 선택 필요.
- 삼성생명 2024.4Q: "보험계약 상품라인" 사망/건강/연금 별도 세그 테이블 → 합산 필요.
- `pick_combined_agnostic` 재작성: 캡션 "상품라인" → `_segment_min_sum`(근접쌍 클러스터별 MIN=별도 합).
  4,812,932+5,583,557+1,850,883=12,247,372=gold ✓. full-book는 `_comparable_min`(max의 50%이상 후보 중 MIN
  → garbage partial 제거 + 별도/연결 쌍에서 별도). **결과 한화생명 92,384.9·삼성생명 122,473.7 = gold ✓✓.**

**회귀 점검 (A/B min vs max):** 직전 세션의 blanket MIN fallback이 ~125 company-quarter 파괴
(DB손보 -570/삼성화재 -83 등 garbage 선택)였음을 A/B로 적발 → `_comparable_min`(50% 게이트)으로 복원.
MAX대비 차이 125→40(전부 개선: 한화생명 별도, 삼성생명 2024 Q1-3 상수화 등).

**is_prior 분기 버그 수정:** `_is_prior_stage`가 자기 자신 opening을 비교에서 제외. 분기는 기초≈기말
(1분기 소폭변동)이라 close≈자기opening으로 당분기 블록을 prior로 오판·제거하던 버그 → 한화생명 2024.1Q
연결(132,968)→별도(92,384.9) 정상화. + 분기 "2)전분기/전반기" prior 블록 캡션 제외(`_is_prior_caption`).

**결과:** 골드 8/8(2025.4Q 6 + 2024.4Q 생보 2). 6 gold사 + 2024 생보 전분기 일관.
gold-map → [`docs/csm_coverage_goldmap.md`](csm_coverage_goldmap.md). 잔여 BROKEN(gold 필요):
DB손보 2025(122K→17K 붕괴)·롯데손보 2025·동양생명 2025.2Q·**삼성생명 2025.1Q**(추출기 캡션잘림으로
상품라인/출재 마커 소실→세그합산 미발동, 단일세그 70,969 선택; 추출기 캡션보존 수정 필요).
large-wobble(별도/연결 추정, 검증불가): 교보·농협생명·미래에셋·푸본현대.

---

## 2026-06-02 (c) — CSM 분기 FY-anchor + 코드베이스 아카이빙

**분기 정합성 (FY-anchor 2-pass):** 분기공시는 YTD(연초 누적)라 한 해 안 기초가 일정해야 함.
- `pick_combined_agnostic`의 중복 기초/기말/신계약 라벨 게이트 제거 → block_stages가 이미 STAGE_PATTERNS로
  open+close+movement 검증하므로, 분기보고서 축약 단순표(삼성화재 Q1/Q3 "제76(당)기 1분기" 형식)도 잡힘.
  삼성화재 Q1/Q3 none→커버.
- `_select(cands, anchor, fallback)`: anchor(억) 있으면 opening이 anchor에 최근접한 후보 선택 →
  전기(작음)·연결(큼) 동시 배제. anchor 없으면 min(별도, pattern2)/max(combined-agn) fallback.
- main 2-pass: Q4는 anchor 없이 min→별도(gold검증), Q1~3은 같은해 Q4 기초(=연초 별도)를 anchor.
- 결과: **6사 gold 2025.4Q 6/6 유지, 연도경계 연속성 57/59, 삼성화재 13분기 일관**(2025 전분기 기초 140,739).
  잔여: 생보 일부 연도(한화생명/삼성생명 2024.4Q가 연결/partial 오선택 → 그 해 분기 anchor 오염), 미래에셋·교보 다년. → gold 필요.

**아카이빙 (`archive/2026-06_csm_nb_reverse_engineering/`):** gold 이전 "혼자 찾기" 스캐폴딩 10개 이동
(viz_build_csm_waterfall_history·build_fy2025_waterfall·build_nb_csm_multiple·build_ir_disclosed_multiples·
check_nb_csm_{history,widespread}·build_lotte_series·analyze_transitional_measures{,_v2}·extract_ir_wolnap_benchmarks).
keeper(build_csm_waterfall_master/build_net_income_breakdown/build_tidy_exports + viz_build_csm_waterfall + src/ifrs17)에서
import 0건 확인, 4 키퍼 컴파일 OK. 삭제 아님(해외사 참고용). 상세 → `archive/.../notes.md`. ⚠️ build_tidy_exports가
csm_waterfall_history.json(history 빌더 산출)을 읽음 — JSON은 남아 동작하나 재생성하려면 부활 필요(향후 master diag로 재배선).

---

## 2026-06-02 (b) — CSM 생보 별도 픽스 (6사 gold 6/6) + PL 24항목 + basis 노트

사용자가 생보 gold(삼성생명·한화생명 CSM + 4사 PL 원수/재보험 분리판) 추가 제공.

**📌 기준 방법론 영구기록:** [`docs/domains/csm-pl-basis-methodology.md`](domains/csm-pl-basis-methodology.md) 신설 — 별도/연결, 원수/재보험 불일치 발견·해소 히스토리 + PL 24항목 스키마. (사용자 "꼭 명기" 요청)

**CSM 차이조정표 일반화 + 별도 픽스:**
- `_csm_cols_pattern2` G(그룹 수) = "구성요소별 보험계약 합계" 칼럼 수 → 단일발행(한화생명 G=1)·상품라인(삼성생명 G=3 사망/건강/연금)·배당(G=2) 통합. CSM = 그룹당 idx 2~(stride-2) 합산(전환방법 3-split 포함).
- `pattern2_stages`: 라벨이 col0(부모)+col1(자식) 2칼럼 걸칠 때 둘 다 검사(한화생명/삼성생명); opening/closing은 자산인/부채인 sub-row 제외 + 기초/기말 startswith; all-zero 행 skip.
- **별도/연결:** 본문 XML에 별도·연결 CER 둘 다 존재(연결≥별도). `pick_pattern2`가 현재기간 후보 중 **min-opening = 별도** 선택. 손보는 후보 1개라 영향 0. → **한화생명 130,657(연결)→91,091(별도), 삼성생명 130,807→129,020. 6사 gold 6/6 항목 정확.**
- `__main__` 가드 추가(import 테스트 가능), `waterfall_for_dir` 헬퍼 추출.

**PL breakdown 24항목 (원수/재보험 분리):** 불일치(삼성생명만 net, 3사 원수) 해소 위해 measure 확장 — CSM상각/RA/예실차/기타를 원수(4-7)·재보험(9-12) 둘 다 별도 항목으로. 공식·검산 → basis 노트 §3. 구현 대기.

---

## 2026-06-02 — CSM waterfall 배당합산 일반화 (사용자 3-gold 검증)

사용자가 손수 만든 gold 시트 3개(메리츠/KB/삼성 2025.4Q)로 CSM waterfall 공식 확정·일반화.

**확정 공식:** 각 단계 = 배당있는 보험계약 CSM + 배당없는 보험계약 CSM (보험계약마진 칼럼). 항목4(가정·경험)=residual(기말−기초−신계약−이자−상각). 3사 모두 6/6 1원단위 일치.

**구조 3패턴 (이질성):**
1. `배당합산` — 배당있는/없는이 **별도 sub-table 2개** (메리츠·KB·롯데·흥국). caption 마커 `배당요소가있는/없는` + STAGE_PATTERNS NB게이트. dang·mu **둘 다** 있어야 발사(롯데: 유배당만 있으면 partial→fallthrough).
2. `배당칼럼합산` — **한 표 안 CSM 칼럼 2그룹** (삼성: `배당요소가 있는/없는`, 현대: `유배당/무배당`). leaf헤더 보험계약마진 위치 → CSM cols, 행내 합산. 현대는 **원 단위**→magnitude 스케일링.
3. `combined`/`combined-agn` — 캡션무관 단일 원수 블록 (DB·농협·코리안리: 측정모형 split, junk 캡션). 재보험/출재/관계기업 제외, max-opening.

**가드:** pattern2·combined-agn은 open+close + (신계약 or 상각) 있어야 채택(DB 배당×전환방법 6칼럼 garbage 199,613억 reject). 배당합산 신계약<−10,000백만이면 reject(한화).

**검증 결과 (2025.4Q, 억) — 총 20사 커버 (손보 10 + 생보 10):**
- GOLD 4사: 메리츠 6/6 / KB 6/6 / 삼성화재 6/6 / **한화손보 5/6**
- 한화손보: 기초 38,032·기말 40,694·이자·상각 gold 정확, **NB만 −716(손상)**. measurement_extractor가 한화 중첩 rowspan 차이조정표를 오파싱해 assumption행 값이 NB행에 섞임(추출기 레벨 버그). 코어 추출기 수정 = 오버엔지니어링 → 보류. NB는 residual로 흡수, 헤드라인 정확.
- cross-validated: 롯데 신계약 4,121.7 = 사용자 gold 412,168백만 일치
- 손보 continuity-sane: 흥국 28,047 / 현대 89,778 / DB 121,869 / 농협 15,949 / 코리안리 9,381
- **생보 10사 확장**(배당합산/배당칼럼/combined 동일 메커니즘, 전부 balanced·신계약 양수): 한화생명 129,446 / 신한라이프 72,008 / 교보 57,311 / 농협생명 31,374 / KB라이프 32,289 / 동양 23,861 / 흥국생명 22,774 / 미래에셋 19,722 / DB생명 19,813 / 푸본현대 1,669

**미커버 (정직):**
- 소형 손보 6사(AIG·악사·하나손해·신한이지·서울보증·카카오페이): measurement 블록 0 = **PAA-only, GMM CSM 없음 → none이 정답**(파싱실패 아님).
- 소형 외국계 생보 8사(라이나·메트라이프·처브·BNP카디프·IBK연금·교보라플·IM라이프·하나생명): history도 미커버, CSM 미미 추정.
- **의미있는 누락 3사: 삼성생명(거인 ~30조, 207블록 중첩표)·KDB생명·ABL생명** — 한화류 중첩 배당×방법 + col1 라벨 구조 추정, 깊은 작업 필요.

**scope 정정:** SONBO 하드코딩 8개 → **동적스캔 전 보험사**(손보 16 + 생보, DART raw 보유). 기존 8개는 임의 "상장 손보" subset이었음.

**산출물:** `data/dart/viz/csm_waterfall_master_diag.json` (진단용, 858행, canonical 아님). 캐노니컬 `CSM_waterfall.json`은 아직 broad history판. 통합(build_tidy_exports) 미실시.

**분기 시계열 (사용자 교정):** "분기 표도 결산과 똑같이 생겼다" → 구조 문제 아님. 데이터 보면 기초가 한 회계연도 분기마다 동일=YTD 정상. 불안정 원인은 (1) 연도경계 별도/연결 basis 불일치, (2) 일부 분기 블록 오선택(삼성 25.3Q 150,077 과대 vs Q4 gold 141,677). basis 고정(_00760)+블록선택 정합으로 해결가능. 이전 "분기 구조적 불안정" 주장 과장 → 정정.

shared `viz_build_csm_waterfall.py` STAGE_PATTERNS["interest"]에 `보험금융수익(비용)` 추가(현대·한화 라벨, additive).

**PL breakdown 17항목 (동 세션):** Tier2 부문손익 **공식 확정** — 부문손익 = 보험수익 − 보험서비스비용 + 재보험수익 − 재보험비용 (부문별 component 합산). 삼성 일반 검산 3,050,283−2,458,622+690,662−1,102,759 = 179,564 = gold 정확(천원). 현 `extract_tier2_lob`는 재보험 미포함 → 일반 5,917억 오류. **구현 대기** (재보험 부문 component 합산 추가, 삼성·메리츠 gold 게이트, 나머지 손보 gold 필요). Tier1 전사 11항목은 10/10 OK 유지. 상세 → `TODO_parser.md` 🎯 섹션 B.

---

## 2026-06-01 (e) — History 빌더 13Q 재빌드 + 음수-NB 가드 (DB 부호반전 해소)

`check_nb_csm_history.py` (전 분기 × 9사 IR cohort)로 노출된 systemic 이슈 진단·부분해소.

**상속 확인:** history 빌더(`viz_build_csm_waterfall_history.py`)는 이미 `rank_main_blocks`(disambiguation) / `find_csm_leaf_cols`(소계 fix) / `collect_current_product_blocks`(product-aggregate 가드)를 import — **재빌드만으로 shared fix 반영**됨 (별도 주입 불필요).

**근본 원인 (DB손해 2025.2Q):** 반기/3분기 보고서의 measurement 표는 **깊은 다층 헤더 + CSM 전환방법별 3-split + 빈 라벨 셀** 구조. `find_csm_leaf_cols` fallback이 `reversed(hrows)`로 CSM-split 행을 먼저 만나, 그 앞이 빈 셀이라 `val_before=0` → **`csm_leaf_cols=[0]`=BEL 칼럼** 반환 → 신계약 NB가 BEL 변동(음수) **−16,414**로 읽힘 (부호반전·폭주의 정체).

**Stopgap (구현):** `build_one_period`에 **음수-NB 후보 거부 가드** (누적 NB CSM은 <0 불가). DB 부호반전(−23,589 / −7,976 / +53,714) → 정직한 gap. **DB손해 history OVER/UNDER 3→0, OK 6.** 빌더 ok 260→258 (garbage 2건만 gap화), 정상 분기 무영향.

**남은 것 (진짜 fix, 고위험 → 별도 세션):**
- `find_csm_leaf_cols`가 **반기 다층헤더 전환방법별-split 양식에서 CSM 칼럼([2,3,4])을 식별**하도록 보강 → 음수가 OK로 회복. ⚠️ 함수가 전 곳에서 쓰여 FY2024/FY2025/history **전체 재검증 필수.**
- 미래에셋 교대(continuity tiebreak 세그먼트↔총계 오감), 삼성화재/메리츠 분기 OVER/UNDER — 같은 반기-format + continuity 뿌리.
- 한화손해: IR `nb_csm_eok_ir` 비표준 필드 → check IR N/A(전부 MISSING). 코리안리: empty series. (둘 다 (d) 진단 참조.)

**Files:** `viz_build_csm_waterfall_history.py` (음수-NB 가드). **Rebuilt:** csm_waterfall_history.json.

## 2026-06-01 — CSM waterfall: 별도·당기 블록 disambiguation (2026-05-31 trade-off 해소 → Option B)

Root cause of the unbalanced waterfall (한화 residual +1.11조) AND several NB CSM "OVER" flags was **block SELECTION**, not the basis flag. 생보 file the 측정요소별 rollforward up to 4× (연결/별도 × 당기/전기) under an IDENTICAL caption ("(5) 당기와 전기 중 … 측정 요소별 변동내역 … 1) 당기"), so `_period_affinity` can't separate them and `rank_main_blocks`' last tiebreak (largest `new_business_abs`) picked the WORST copy — 한화 landed on 연결·전기 (기초 13.59조), 메리츠 on 전기 (FY2023).

**Fix:** `_disambiguate_basis_period()` in `viz_build_csm_waterfall.py`, applied at the end of `rank_main_blocks` (waterfall + 13Q history builder both inherit it). Mirrors the proven `transition_new_business` heuristic: drop prior-period copies (closing CSM ≈ another candidate's opening), then among current candidates in the main magnitude band (≥20% of largest opening — drops small PAA/재보험 tables) pick the smallest opening CSM (= 별도). Self-limiting: single-table filings + product-segmented filings (collect_current_product_blocks path) untouched.

**Result — 6/28 corrected, all residual 0; 22 unchanged:**

| Company | open before→after | NB before→after | balance |
|---|---|---|---|
| 한화생명 | 13,591,377 → 9,238,488 (연결·전기→별도·당기) | 2,123,086 (=별도, unchanged) | resid +1,111,274 → **0** |
| 메리츠화재 | 9,637,639 → 10,468,726 (전기 FY23→당기 FY24) | 1,600,648 → **1,379,571** | = IR FY24 13,795.7억 exactly → check 1.160 OVER → **1.000** |
| 에이비엘생명 | 전기→당기 | 245,843 | resid 101,744 → **0** |
| 케이비라이프 | 전기→당기 | 501,304 | resid 133,364 → **0** |
| DB생명 | 1,552,357 → 1,654,891 (전기→당기) | 524,734 → 469,446 | 0 → 0 |
| 교보생명 | 10,993,354 → 11,649,847 (연결·전기→별도·당기) | — | 0 → 0 |

**메리츠 정정 (이전 entry 보완):** the 16% OVER was NOT a CSM-column read error — leaf-col extraction always read CSM(그 외) correctly, not the horizontal-sum 합계. It was a 전기/당기 mis-pick (16,006억 = FY2023). Now 당기 = 13,795.7억 = IR exactly. No 손보-specific transition pattern needed for Meritz.

**Still OVER (separate root cause, NOT this fix):** 롯데손해 2.466 (`find_csm_leaf_cols` 소계 double-count + no 부문별 table). Pre-existing imbalances unrelated to block selection: NH농협손해 (regulatory basis), 메트라이프 +150,053, 처브 −54,917.

**⚠️ Pipeline still on FY2024 extracts** (`data/dart/extracted` = rcept 2025…); FY2025_Q4 raw downloaded but NOT yet parsed to `_measurement.json`. Meritz FY2025 당기 (별도 CSM그외 1,588,172 = IR 15,882억) appears only after FY2025 extraction runs.

**Downstream needing re-run for consistency:** `viz_build_csm_waterfall_history.py` (13Q — inherits fix but not yet re-run), `csm_bubble.json`/`nb_csm_multiple.json` (한화·메리츠 closing CSM shifted to 별도). **Files:** `viz_build_csm_waterfall.py`. **Rebuilt:** `csm_waterfall.json`.

## 2026-06-01 (b) — 소계 이중계상 fix + 롯데 NB source (구성요소별 차이조정)

**소계 double-count fix:** `find_csm_leaf_cols` Case-1 branch returned `range(start, start+len(sub))`, blindly including a trailing 소계 sub-column → CSM summed with its own subtotal = **2×**. Now drops `_is_subtotal_label` columns (수정소급/공정가치/이 외/**소 계** → keep [2,3,4]). Corrected **7/28 손보** (all uniformly ÷2, balance preserved): 롯데손해 NB 970,504→485,252, 한화손보 (known ~2× flag) 1,481,978→740,989, 교보 closing 11.6→5.8조, NH/+others. 22 untouched. 교보(생보)도 ÷2 된 건 measurement 표에 literal 소계 칼럼이 있어서 — 정상 교정.

**롯데 NB source 정정 (user-supplied):** ÷2 후에도 측정요소별 "최초 인식 계약" CSM (485,252, FY24) ≠ IR. IR-aligned NB = **"보험계약 구성요소별 변동분에 대한 차이조정" 표, 무배당/배당없는 보험계약 소계, 미래서비스 관련 변동 → 최초인식계약** = **412,168 (FY2025 = IR 확인)**. FY2025 raw 확인: `KR0003…20260319001293.xml` 메인 = 구성요소별 차이조정 caption (line 28080/28872), `_00760.xml:27375` 신계약 BEL(454,714)/RA 59,104/**CSM 412,168**. ⚠️ 이 표는 현재 measurement extractor가 안 잡음 (측정요소별만); FY2024 filing은 측정요소별 양식이라 구성요소별 차이조정 최초인식계약 행 없음 (양식이 연도별로 다름). **Pending:** extractor에 구성요소별 차이조정 capture 추가 + NB override → 아래 (c)에서 구현.

## 2026-06-01 (d) — FY2025 V7 cohort 마이그레이션 → check 7/7 ✅

`python scripts/check_nb_csm_widespread.py 2025` = **ok=7/7** (메리츠 1.008 / 롯데 1.000 / 삼성화재 1.000 / DB 1.049 / 한화생명 1.000 / 삼성생명 1.000 / 미래에셋 1.000). IR FY2025 = sum(2025.1Q–4Q).

**FY2025 filing 구조 변화:** FY2025 사업보고서는 IFRS17 measurement 주석을 **본문(main XML) + 별도주석(_00760) 양쪽에 중복** 수록 → 합치면 picker 혼란 (메리츠 전기 13,796 / 삼성생명 172표에 파묻혀 0 / DB 3.6). **해법: FY2025는 _00760(별도 주석)만 추출** → 6/7 즉시 OK.

**미래에셋 2× fix:** _00760 안에 coarse(사망/기타) + fine(상품별 5개) 두 분류 공존, 집계행 "기타"(NB=fine 전체합)와 fine을 둘 다 합산 → 2×. `collect_current_product_blocks`에 **집계행 드롭 가드** (|NB| ≈ 나머지 전체 합, 2% tol) 추가. 미래에셋 10,798→5,399 ✅. **FY2024 regression 0** (가드는 집계행 존재 시에만 발동).

**신규 인프라:**
- `scripts/build_fy2025_waterfall.py` — FY2025_Q4/raw → `data/dart/extracted_fy2025/` (_00760 추출) → `data/dart/viz/csm_waterfall_2025.json` (23사, `build_for_file` 재사용).
- `check_nb_csm_widespread.py <FY>` — CLI 연도 인자 (기본 2024; `2025`면 csm_waterfall_2025.json + 2025 분기). FY2024 동작 불변.

**범위:** cohort 7사만 IR 대조·검증. 비-cohort 16사는 best-effort (_00760-only, IR 미대조; 농협생명 0 등 일부 미해결). FY2024 check 여전히 6/7 (롯데 OVER — FY2024엔 차이조정 표 없음, 측정요소별 485,252, 예상된 동작).

**Files:** `viz_build_csm_waterfall.py` (product-aggregate 가드), `check_nb_csm_widespread.py` (FY arg), `build_fy2025_waterfall.py` (new).

## 2026-06-01 (c) — 롯데 FY2025 NB CSM = 412,168 (reconciliation_lrc override) ✅

FY2025 롯데손해 raw (rcept 20260319001293) 파싱. 기존 extractor가 구성요소별/잔여보장 변동 표를 **이미 capture함** (caption keyword "구성요소별"이 `measurement_extractor._CAPTION_PRIMARY`에 이미 존재) — FY2024엔 그 양식이 없어서 안 잡혔을 뿐.

**발견:** FY2025 filing은 measurement 표 33개. 측정요소별 표는 NB 과대(485,252), IR-aligned NB는 **당기 원수 잔여보장 구성요소별 변동** 표(제81당기, 원수, 신계약 행, CSM 칼럼) = **412,168**. extractor가 구성요소별 표 caption을 "관계기업 요약재무정보"로 오귀속 + 무배당 표가 둘(412,168 당기 / 485,252 전기) → generic picker가 작은 배당있는 블록(NB 0)을 골라 실패.

**Fix:** `reconciliation_new_business()` (viz_build_csm_waterfall.py) — NB override (우선순위 transition_new_business **다음**, 그래서 전환방법별 생보 무영향). 당기·원수(잔여보장+구성요소, 재보험/전기 제외) 표의 신계약/최초인식계약 CSM 읽음. **롯데 FY25 NB = 412,168 ✅ (= IR).** **FY2024 full build: NB 변경 0 (zero regression)** — FY2024 filing엔 이 표 양식 없음.

**Still open:** FY2025 롯데 full waterfall의 opening/closing은 여전히 오선택 (generic picker가 33-table FY2025 구조에서 배당있는 작은 블록 골라 opening 6,047). NB(=CSM 배수 입력값)는 정확; 나머지는 FY2025 picker 작업 필요. FY2025 measurement JSON은 extracted_dir에 미저장 (파이프라인 아직 FY2024, dup 회사 entry 방지). **Files:** viz_build_csm_waterfall.py.

## 2026-05-31 — NB CSM widespread fix (처음 인식 / 전환방법별 표 단일셀 1순위 path)

New-business CSM was over-stated for several life insurers: the parser read it from the 측정요소별 변동 table's "최초 인식한 계약의 효과" CSM column (연결, larger) instead of the company's "전환방법별 보험계약마진 변동" table "신계약 인식효과 / 합계" cell (별도) — which is what IR discloses.

**Fix:** priority NB path in `scripts/viz_build_csm_waterfall.py` (`transition_new_business` + `_transition_table_blocks` + `_transition_row_value`). Scans the *direct-business* 전환방법별 table (excludes 재보험 ceded sibling), drops 전기 copies + tiny per-product segments (기초 < 20% max), picks smallest-기초 (별도) current-period 신계약 인식효과 합계. Falls back to `find_csm_leaf_cols` when absent. Same override wired into `viz_build_csm_waterfall_history.py`.

| Company | KR | before | after | IR FY24 | result |
|---|---|---|---|---|---|
| 한화생명 | KR0068 | 32,361 | **21,231** | 21,230.8 | OK (1.000) — fixed |
| 메리츠화재 | KR0001 | 16,006 | 16,006 | 13,795.7 | OVER — no transition table; fallback kept |
| 롯데손해 | KR0003 | 9,705 | 9,705 | 3,936.1 | OVER — no transition table; fallback kept |

메리츠·롯데 (손보) file 측정요소별 일반모형/장기/자동차, not 전환방법별 — need a separate 손보 pattern (out of scope, user to supply raw). Lotte also has a 소계 double-count in `find_csm_leaf_cols` (`[2,3,4,5]` sums 이외+소계) — flagged, not fixed.

Hanwha quarterly increments now reconcile with IR exactly (Q1 5,154 / Q2 4,811 / Q3 5,420 / Q4 5,846억). Collateral 전기→당기 corrections on NO_IR cos (에이비엘 3,476→2,458 / 케이비라이프 6,347→5,013 / 메트라이프 5,044→3,742). 미래에셋 (1.000) / 삼성생명 (1.012) untouched — zero regression. 삼성화재/DB parser 정상 — earlier check-tool 4Q-SUM-on-cumulative bug already fixed in `check_nb_csm_widespread.py` (validation session owns).

**⚠️ Trade-off pending user:** override changes ONLY new_business; opening/closing stay on 측정요소별 (연결) basis → waterfall balance no longer closes for 한화·에이비엘·케이비라이프·메트라이프 (`validate_csm_waterfall.py` balance_fail, `nb_fail=0`, 한화 residual ≈ +1.11조 = 연결/별도 NB delta). (A, current) NB matches IR for bubble/multiple, waterfall unbalanced. (B) switch whole Hanwha waterfall to 별도 측정요소별 block — balance closes but opening/closing change.

**Files:** `viz_build_csm_waterfall.py`, `viz_build_csm_waterfall_history.py`. **Rebuilt:** csm_waterfall.json (+history), csm_bubble.json (Hanwha multiple 26.5x→17.4x), downstream_kpis.json, nb_csm_multiple.json, csm_waterfall_validation.json.

## 2026-05-31 — F17 Tier2 LOB 9/11사 확장 + IR cross-check 3사

Tier2 LOB (장기/자동차/일반 보험손익) extended 4사 → **9/11 손보사** OK against reconciliation gate. `scripts/build_net_income_breakdown.py` +210 lines: 5 per-company extractors (`_kb_lob`/`_hana_lob`/`_meritz_lob`/`_nh_lob`/`_koreanre_lob`) + `PERCO_LOB` dispatch + basis-aware gate. Report: `output/lob_underwriting_income_cross_check_20260531T103915Z.md`. Decision pending (`TODO_parser.md` in-flight box).

**Per-company DART source** (key finding — table layout varies, not missing):
- *Note 발행보험 by 계약유형*: 삼성화재 / 현대 / DB / 한화 — **재보험 미포함** (발행보험만)
- *보험손익 상세내역 (IFRS17 행 직접, 재보험 포함)*: KB (별첨 `_00760.xml` line 20001 — already fetched, not main XML) / 하나 (천원 단위 ⚠️)
- *보종별 사업실적표 (regulatory, 사업비 배분차)*: 메리츠 / NH / 코리안리(재보험 taxonomy)
- 롯데 = single-segment 공시, DART에 부문별 손익 표 없음 (구조적, IR factsheet 필요); 흥국 = unreliable parse

**IR cross-check (3사 — IR LOB 있는 회사만):** 메리츠 장기 +10.0% / 자동차 -7.0% / 일반 +5.0% (사업비 미차감 구조적 +10%, 비율 일관 = clean). 삼성화재 장기 +10.4% but 자동차 +23% / 일반 **+246%** (DART note=발행보험, IR=재보험 포함). DB 자동차 **부호 뒤집힘** (DART +6,810 vs IR -547, 출재손실 ~7,400억 추정). 재보험 누락 가설 확정 — but DART note에 부문별 수재/출재 분해표 없음 (구조적 한계).

**Taxonomy correction:** 손보 CSM 분해 = 보장성/물보험/저축성 (장기 내); 손보 P&L 분해 = 장기/자동차/일반. 자동차·일반 = PAA → CSM 없음. 보종별 신계약 CSM 배수는 IR 공시 회사 한정.

---

## 2026-05-30 (b) — F17 Tier2 LOB 방법론 수정 (FY2024·삼성화재도 분해 있음)

사용자 반례로 'FY2024 LOB 없음 / 삼성화재 taxonomy 다름' 진단 철회 (성급한 source-limited 오판, `<TE>` 때와 동일 교훈). **수정 (`build_net_income_breakdown.py`):** ① 컬럼 식별 position-based (병합 super-header 탓 헤더-인덱스 어긋남 → numeric cell 위치 0/1/2=장기/자동차/일반); ② rollforward 표(BS 규모) 제외, flow 분석표만; ③ 보험수익 = max(합계행, 컴포넌트 합); ④ 단위 factor = Tier1 보험손익 anchor; ⑤ Tier1 연결 우선 (현대 별도 3,961 → 연결 10,431). **결과 4사** (억): 삼성화재 장기 16,651/자동차 −1,220/일반 5,917 · 현대 4,097/−677/6,613 · DB 12,257/6,811/−26 · 한화손보 4,171/−966/−735. 이후 2026-05-31 에 9/11 확장.

## 2026-05-30 — F17 손보 당기순이익 분해 Tier1 10사 + Tier2 1사 (현대)

신규 `build_net_income_breakdown.py` → `data/dart/viz/net_income_breakdown.json`. **Tier1 (포괄손익계산서, 10/10):** 보험손익/투자손익/보험금융수익·비용/영업이익/영업외/당기순이익. 단위 매그니튜드 자동추론 (당기순이익 5~120,000억 들도록) + 일관성(보험손익+투자손익≈영업이익) + 자릿수 guard. 예: 삼성화재 14,830/11,761/순이익 20,203, DB 11,454/12,386/17,906, 메리츠 14,270/8,595/16,929. **Tier2 현대 검증완료** (장기 보험수익 80,684/비용 76,397/손익 4,097/CSM상각 9,639억). 나머지 reconciliation gate로 제외.

## 2026-05-30 — IR factsheet 수집 + 손보 disclosed/derived NB CSM 배수

삼성화재 (KR0008) 13Q disclosed — factsheet `CSM` 시트가 배수 직접 공시 (단분기 월납환산x3), cumsum이 DART/KIDI 분자와 정확 일치. `parse_ir_samsung_fire.py`. DB (KR0011) 13Q derived (component-based, 분자·분모 모두 KIDI와 근접 → 손보 ~16x 두 소스 동시검증). `parse_ir_db_derived.py`. 한화손보 (KR0002) — DART/KIDI 분자 ~2배 과대 (FY24 14,820 vs IR 7,410) flagged, 배수 미산출. 현대 single-point. 집계 `build_ir_disclosed_multiples.py` → `disclosed_csm_multiple.json` 9사. 회사마다 배수 공시기준 제각각 (삼성생명 월평균월초 / 메리츠 월납환산 / 한화생명 APE / 삼성화재 단분기x3) → 단일기준 KIDI computed가 버블 비교에 적합.

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
