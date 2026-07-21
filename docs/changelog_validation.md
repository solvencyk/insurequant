# Validation Changelog (Stage 3)

> Last updated: 2026-07-15 · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Authoritative rules: docs/agents/kics-json-validation-rules.md

Validation-only history. Cross-stage changes also keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).

---

## 2026-07-21 — 사고 포스트모템 관행 도입 + 기존 4건 소급 (owner `20260721T0233Z`)

owner: "포스트모템이 게이트 룰로 종결되지 않으면 같은 부류가 다시 통과한다." 5칸 미충족 시 close 불가인
blameless 포스트모템 관행 신설.

- **구현형태 = 로컬 스킬 채택** (`.claude/skills/incident-postmortem/SKILL.md`). 외부 서드파티 스킬
  미채택 사유: 종결 5칸이 이 저장소의 **게이트 파일명·registry 변수명·display-scope·두 게이트 분리**를
  직접 지목해야 강제력이 생기는데 범용 포스트모템 스킬로는 불가. 기존 로컬스킬(`kics-parser`·
  `ifrs17-parser`) 패턴 존재 + 금융데이터.
- **정본**: `docs/postmortems/README.md`(관행·종결조건·색인·UH표) + `_TEMPLATE.md`.
  스테이지 프롬프트 `docs/agents/claude-agent-validation.md` **§5.1 신설**에서 링크.
- **소급 4건**: PM-2026-06-16 두 달 글리치(**closed**, push 게이트 배선) · PM-2026-07-07 적용후 전면
  미검증(**open**) · PM-2026-07-08 V17 가짜복사(**open**) · PM-2026-07-15 부모 census(**closed**, 양쪽 배선).

### 🔴 소급의 실질 산출물 — 미배선(UH) 4건

- **UH-1 (P1, 최대 발견)**: 적용후 검증 7종(`_transition_ratio_after_capture`·`_transition_mmult_after`·
  `_transition_identities_after`·`_parent_present_child_incomplete_after`·`_diversification_negative`·
  `_item12_equals_item1`·`_ratio_series_spikes`)이 **push 게이트에 미배선**. `validate_data_contract.py`의
  `check_census`는 `kics_json_rules.run_validation`의 rule-based 결과만 lift하고, **`prepush_check.py`는
  `validate_kics_disclosure.py`를 import·실행하지 않음** → 07-07·V17 사고 대응 룰 전부가 push를 못 막는다.
  사고 4건 중 3건이 여기 걸림.
- **UH-2 (P1)**: `scripts/validate_data_contract.py`가 **git untracked**(머신-로컬) → push 게이트 배선
  (V18 부모 census 포함)이 git에 없음.
- **UH-3 (P2)**: provenance Phase-2 end-state 미강제 — sidecar 존재 3종(kics_disclosure·CSM_waterfall·
  PL_breakdown)만 strict, 없는 마스터는 Phase-1 추론 fallback으로 통과.
- **UH-4 (P2)**: `validate_data_contract.py --selftest`가 `_data_contract_selftest` 부재로 실행 불가.

### ✅ 같은 날 UH-1·UH-2 배선 완료 (owner 승인 "나머지는 추천대로 배선 고고")

- **UH-1**: 적용후 검증 7종을 `validate_data_contract.py` `check_census` **1b(iv)** 로 lift
  (display 7분기 scope). 6종 RED(`TRANSITION_AFTER_{COPY|MISSING|LOWER|AMT_MISMATCH}` ·
  `TRANSITION_AFTER_MMULT_MISMATCH` · `TRANSITION_AFTER_IDENTITY` · `POST_TRANSITION_CHILD_MISSING` ·
  `DIVERSIFICATION_NEGATIVE` · `ITEM12_EQUALS_ITEM1`) + `RATIO_SERIES_SPIKE`만 YELLOW(휴리스틱이라
  단독 push 차단 금지 — 원 룰 정의 준수). **주입 테스트로 방출 경로 검증**: display-scope를 2023.1~3Q로
  임시 확장 시 baseline RED 0 → lifted RED 4건(예별손해 3분기·IBK연금) 방출 확인. 배선 후 실 게이트는
  **RED=0 유지**(현 findings 전부 non-display 2023.x).
- **UH-2**: push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·
  `triage_anomaly_candidates.py`) **git 등재**. gitignore가 아니라 단순 미추가였음(scripts/ 163개 이미
  tracked, 나머지 의존성도 전부 tracked였음).
- **도메인 경계 명문화(owner 지적)**: 경과조치는 **K-ICS 전용**(적용전/적용후 이중공시). IFRS17엔
  대응 개념 없음 — 전환방법(수정소급/공정가치)은 도입시점 측정방법이지 이중컬럼이 아니라 **복사할 짝
  자체가 없음** → `TRANSITION_AFTER_*` IFRS17 유사룰 금지. 상위 패턴("presence만 검사→세탁")만 도메인
  무관이며 IFRS17은 기존 `CSM_WATERFALL_PLAUSIBILITY`/`IMPOSSIBLE_ZERO_*`가 담당. README·SKILL 기록.
- **PM-2026-07-07·PM-2026-07-08 → `closed`** (3번 칸 충족). 잔여 P2: UH-3·UH-4·UH-5(신규, 요구자본
  COPY 검사 부재).

---

## 2026-07-16 — 부모 census parser fill 적대검증 (worklist `20260715T0835Z` resolved)

parser가 continuity 워크리스트 답변(fill: 삼성생명 2025.1Q·동양생명 4분기·한화생명 2025.2Q/3Q·흥국생명
17~21·하나생명 18~23). validation 재검증:
- **미러fill(후=전) 정당성 PASS** (V17 가짜복사 재발 아님): 삼성생명(KR0069)·동양생명(KR0087)·한화생명
  (KR0068)은 `_TRANSITION_APPLIERS` 18사(elective)에 없는 **공통(TFI)경과조치사** → 요구자본(item15~21)
  후=전이 도메인상 정답(TFI는 가용자본만 영향). 적대검증: item1(가용자본)후는 2025.2Q에 실효과(Δ+825~1188)
  로 ≠전인데 item15~21후=전(±1억 반올림뿐) = 공통경과조치 정합 확인. mirror=정답.
- **무회귀**: `_transition_ratio_after_capture`(COPY/LOWER/AMT_MISMATCH)·mmult·항등식·분산효과음수 전부
  0 유지. continuity break **117→62셀**, **push 게이트 census RED 47→4**.
- **잔여 2건 owner escalate**(raw 도출불가, `_POST_PARENT_NOT_DISCLOSED` 결정 대기):
  흥국생명 2024.4Q [15,16,22](image PDF+TIR/TER 다중경과 R4 재현불가) · 하나생명 2024.4Q [16](비표준
  감사보고서 공시, item17후=1757.32가 raw page 2001.90 불일치=partial-mmult 아티팩트 의심 → item16 파생값
  불신). validation 자체 waiver 안 함 = owner 택일(exemption 등재 vs 재추출).
- non-display 비차단 워크리스트: 코리안리 3분기·악사·처브·IBK 2023.2Q 등(git-purge raw, 저우선).

---

## 2026-07-15 — 적용후 요구자본 **부모** census blind spot (owner `20260715T0801Z`)

owner: 2026.1Q push 게이트가 통과했으나 5적용사(한화생명·교보·하나·롯데손해·농협) 요구자본 부모 항목
`값_적용후`가 결측인 채 통과(false-green). 근본원인: 07-12 census(`_parent_present_child_incomplete_after`)는
**부모후 present일 때만** 자식 결측을 봐서 **부모(15~21) 통째 결측이면 census/identity/mmult 전부 skip**.

- **신설 `_post_transition_parent_census`** (scripts/validate_kics_disclosure.py): 적용후를 공시하는 회사의
  요구자본 부모 continuity census. (회사,항목) 값_적용후가 **직전 공시분기 present인데 당 분기 결측**이고
  이후 재출현(SANDWICHED)/최신분기(TRAILING)이면 = 추출갭 → RED. 도입초 onset·항구적 중단은 flag 안 함.
  - 대상: 15기본요구자본·16분산효과·17생명장기·18일반손해·19시장·20신용·21운영 = **코어(RED)**; 22법인세조정·
    23기타요구자본 = 조정(코어 break 동반 시만 RED, 단독은 review — 종속회사/법인세 legit-absent 흔함).
  - **적용사 판정 = continuity 자체**(별도 seed 없음) → `_TRANSITION_APPLIERS` 18사(elective)에 없던 공통
    경과조치사 **한화생명(KR0068)·삼성생명(KR0069)·코리안리(KR1000)**도 포착. 한화생명이 기존 검사에서
    빠지던(18사 하드코딩) 근본원인 해소.
  - 항목 4/12/13(구조적 적용후 미공시=NO_POST_TRANSITION_DISCLOSURE)은 census 대상 원천제외 → 구조적은
    flag 안 됨(요청3). 면제 registry `_POST_PARENT_NOT_DISCLOSED`=비어있음(owner "오면제 금지", waiver=owner 권한).
- **양쪽 배선**: (1) `validate_kics_disclosure.py` 전분기 리포트+exit2 (parser 워크리스트),
  (2) `validate_data_contract.py` `check_census` 1b(iii) **display 분기만 차단**(다른 census와 동일 scope)
  = "push 게이트가 통과"의 정정 지점. 두 스크립트 compile OK, 기존검사(mmult/항등식/하위census/core RED) 무회귀.
- **검증**: 병행 parser 세션이 2026.1Q 5사 15~23 값_적용후 전량 UPSERT(mtime 17:32) → 2026.1Q census RED=0 +
  산술 후검사 0 통과 = **게이트가 갭→RED, fill→통과** 설계대로 작동 확인.
- **잔존 push 차단 census RED=47 (8 회사·분기, historical display)** → parser 발주 `20260715T0835Z`:
  🆕 삼성생명 2025.1Q·흥국생명 2024.4Q(진짜 추출갭, 매분기 공시 중 1분기 유실) · owner 2차 한화생명 2025.2Q/3Q ·
  raw확인 동양생명 3분기·하나생명 2024.4Q(구조적이면 owner exemption).
- **건2 `8_post` dynamic tol (publishing `20260712T0219Z`)**: 이미 07-12 코드반영 확인(KR1098 2023.4Q 8_post
  =YELLOW diff -92.82 tol내), `7_post` 룰 부재 → 추가 조치 불요. resolved.

---

## 2026-07-12 (4) — 전수 헤드라인 대조 + 파서 IBK fix 반려

owner "같은 혼합 다른 회사도 헤드라인 대조 전수검증 + 파서작업 확인". 18적용사×전분기 raw 주요경영지표
'경과조치 후' vs 데이터 item27후 대조(anchor=경과조치'전' 일치행, 오탐0):
- **110건 정합 · 불일치 3건(예별손해 KR0004 2023.1Q/2Q/3Q) · 119건 자동파싱불가(포맷/이미지)**.
- **예별손해 3건 = IBK와 동형 혼합**: item27후가 ②표 단독값(74.67/72.21/58.33)인데 헤드라인 정본은
  82.56/79.96/64.50. 다중경과조치(①②③) 결합 최종 아닌 개별표값 오추출.
- **파서 IBK fix(20260712T0430Z) 반려**: item1후를 ①TAC표값 8241.63으로 넣어 **공통(TFI) 경과조치
  누락**(raw: 공통 605,115→697,391 +92,276 빠짐). 결합 정답 = 605,115+공통+TAC = 9164.38(원래값이
  맞았음). parser item14후=4657.6은 ②③결합(≈5179)보다 낮아 불가능. 정정값 발주(item1후 9164.38·
  item14후 5179.08·item3후 8869.48·item28후 5.69, item2후·item27후는 parser 맞음).
- 케이디비 2025.4Q 헤드라인 대조 플래그 = 내 파서 오탐(점선줄), 데이터 205.7 정상.
- 발주 `20260712T0700Z__…__headline_reconcile_ibk_yebyeol.md`(IBK 반려+예별3건+119 per-company 재조정).
- 대조 스크립트 `scratchpad/headline_crosscheck2.py`(anchor, 오탐0). core RED 13·분산효과음수 1 불변.

## 2026-07-12 (3) — 파서 census-fill 적대검증 + 분산효과 부호 sanity 신설

parser가 322→2 fill(commit a797681) 완료 주장 → owner "존나 적대적으로 검증". 독립 재검증:
- **파서 fill 견고 확인**: item18=0이월 0오류·시장하위 carry 0불일치·신용/운영 carry✓·mmult 정합·
  한화손해 item19후=전(raw ②표 "시장 461,015→461,015 불변" 확인, 준비금경과라 시장무관, 13분기 일관).
  2 exemption(롯데·교보 2026.1Q)도 raw 정독→②③표 진짜 부재 확인, `_AFTER_SUBRISK_NOT_DISCLOSED` 등재.
- **적대 스윕이 파서 무관 기존 오류 1건 적발 — IBK연금 2023.2Q**: 적용후가 ②표(기본요구자본 677,870,
  시장 불변)와 ③표(시장 281,235)를 **혼합** → Σ(위험액)<기준금액 → **분산효과 -246.66(음수)**. item27후
  135.19도 헤드라인 요약표 176.95와 불일치. R6 항등식·item27체크·mmult가 산술만 봐서 전부 통과시킴.
- **신설 `_diversification_negative`**(전·후, 전체회사, RED blocking): item16<0 또는 Σ(17~21)<item15.
  전 회사 스캔 결과 음수 1건(IBK)뿐 = 고립. 게이트 배선(exit-code) 완료.
- parser 발주 `20260712T0430Z__…__ibk_multitransition_mixed.md`(②③ 결합 재도출 or item27후 정정+세부 None).
- **현 게이트: census 0·mmult 0·항등식 0·분산효과음수 1(IBK) 정상차단**. core RED 13 불변.

## 2026-07-12 (2) — 적용후 요구자본 census 신설 (blind spot 정정)

**앞 항목의 "gate-clear"는 조기판정이었음.** owner가 아이엠라이프 2025.4Q 적용후 신용·분산효과 결측을
지적 → 적용후 게이트가 mmult(item17/19 leaf)만 보고 **요구자본 구성(15→16~21) census가 없었음**을
확인. 적용후 항등식(R6)은 결측셀을 skip → 부분충전이 양쪽으로 샘.

- **신설 `_parent_present_child_incomplete_after`**(적용전 census 미러): 부모후 present인데 '적용전
  present&material' 자식후 결측=RED(blocking). 부모맵 `{15:(16~21),17:(29~35),19:(36~40)}`. 게이트
  exit-code·print 배선.
- **적발 322 항목셀**(149 부모·분기): DERIVE 96(분산효과 파생)·CARRY 206(신용/운영/시장하위 후=전
  carry-forward)·EXTRACT 20(raw 재추출, 14 회사·분기). 분류·근거 `data/_derived/after_census_gaps.json`.
- parser 발주 `inbox/parser/20260712T0230Z__...__after_requirement_census_322cells.md`.
- **현 게이트: 적용후 census 149 RED로 정상 차단**(exit 2). parser fill 후 0 확인 → 재publish.
- carry-forward 안전성 검증: 신용 후=전 217/218·운영 213/213·분산효과 항등식 119/119 성립.

## 2026-07-12 (1) — 적용후 전수검증 완결 + publish gate-clear [정정됨 → (2) 참조]

owner 지시 "모든 검증룰은 적용전후 동일 적용" 대응. prepush RED=0 달성(publish 가능).

- **8_post dynamic tol 배선**(`kics_json_rules.py`): rule 8(적용전)만 있던 micro-coarse tol(`max(eff_tol, |exp|*0.5/d14 + 50/d14)`)을 8_post에도. 카카오 2023.4Q(item14후=20억 반올림, 974/20=4870 vs 공시4777) prepush RED 1→0. rule8과 불일치 교정.
- **적용후 tolerance 교정**(`validate_kics_disclosure.py`): `_transition_identities_after` R1~R8 합-항등식 tol 5%→0.5%(mmult용 5%가 exact 합에 잘못 복사돼 농협생명 가용자본 2693억 break 마스킹하던 버그). item1후=item2후+item3후 등 3건 unmask → parser raw-verified override로 해소(inbox 20260707T2223Z).
- **COPY amount-guard**: 적용후 item27/28 COPY 판정에 item2후/item14후 이동 여부 추가(롯데 자본잠식 소폭개선 오탐 방지).
- **documented exceptions 5셀**(`_AFTER_SUBRISK_NOT_DISCLOSED`): 하나생명 24.4Q/26.1Q(phase-in 미공시)·농협생명 23.1Q(다중경과 결합공식불명)·처브 24.3Q(컬럼불규칙)·흥국화재 24.4Q(image-only) — 적용후 mmult·추출갭 둘 다 제외. TODO_validation.md 기록.
- **게이트 상태**: prepush RED=0(gate-clear) · K-ICS 적용후(항등식·mmult·item12·유실) 0 · core RED 13(동양·하나생명·미래에셋 image-scan + 한화손해 4억 반올림, 전부 documented) · IFRS17 core 깨끗.

## 2026-07-07 (b) — 인계: parser의 게이트 수정 적대적 리뷰(승인) + 잔여 4 MISSING 복구발주

멈춘 검증 세션 인계. parser가 0502Z 정본발주 처리(139→4 MISSING)하면서 **내 게이트 스크립트를 3커밋 수정**(69fe566 데이터/doc·972c206 sign fix·94db994 dynamic margin) → 파서가 검증코드를 건드린 거라 **적대적 리뷰**:
- **972c206 부호 fix = 정당**: `LOWER`(방향위반)을 `b>=0`일 때만 발화. 분모(기준금액) 항상 양수→비율부호=분자부호, "자본잠식사(음수비율)는 분모↓시 더 음수 정상"을 정확히 구현. COPY/AMT_MISMATCH 부호무관 유지. raw 4사 검증 근거.
- **94db994 dynamic margin = 정당**: 절대 1.0pp→`max(0.1,min(1.0,0.15·|전|))`. 독립감사(`scratchpad/adv_margin.py`): 통과된 5셀 전부 상대변화 18~47%=진짜 소액개선(복사면 ~0%), floor 0.1이 반올림복사 계속 차단, 구멍 0. rule8 동적허용오차와 동형. **accept.**
- **rule_8_post `same_basis` fix**(kics_json_rules.py, 미커밋): item2후/item14후 기준 어긋나면(한쪽만 post) pre2/post14 무의미값→spurious RED. mixed-basis시 SKIP(진짜결측은 transition MISSING이 잡음). 정당.
- **잔여 4 MISSING 복구발주 `20260707T0013Z`**: 흥국생명/흥국화재 2024.4Q(원천오염이나 25.1Q 비교표 직전분기컬럼으로 복원)·악사 2024.3Q(cadence아님, 다른 홀수분기 다 present, 재추출). 전부 복구경로 확인.
- **코어 RED 12 = 전부 이미지스캔**: KR0087 동양2023.2Q×7·KR0079 8_life(documented)·**KR0097 하나생명 2024.2Q×4(신규, scan-image items1-26 결측, OCR 재처리 필요)**.
- **transition 게이트 최종**: 18정본사 item27·28, 부호인지, dynamic margin, AMT_MISMATCH. 반올림복사·item27-only·"진짜동일"·부호오탐 전부 차단. 139→4(복구발주됨).

---

## 2026-07-07 — ✅ 경과조치 after-capture 작업본(139→7) 적대적 재검증 + rule_8_post 폴백버그 수정

DEFINITIVE(20260706T0502Z) 발주에 대한 parser 작업본을 **raw 3중대조(회사별 fan-out 4에이전트) + 내부정합 프로브 + 스코프 diff**로 적대 재검증. **판정: 작업본 대체로 건전(sound).**
- **raw로 확증**: 케이디비생명 13Q from-scratch(총괄표 억 직접대조·item1 자본감소분 점프·음수부호·복붙지문0)·하나생명 3Q·마진완화/부호skip 셀 전부(IBK 2024.2Q item1 6064→9407 +55%도 REAL). 검증기 sign-fix·margin-fix 정당(항등식 체크 유지로 은폐 없음). before값 무변경·행 무증감·항등식 0불일치. 부호skip 셀 전량 분모(item14) 실감소 뒷받침(SUSPECT=0). 스코프이탈 10건(메리츠·신한라이프 후=전)은 정확·무해.
- **F1(RED→parser)**: 에이비엘 KR0070 2025.3Q item28後=52.22·푸본 KR0083 2023.1Q item28後=△70.57 — raw 총괄표에 값 실재한데 "not fixable"로 성급 포기. item2後=item2前(불변)·item28=item2/item14×100로 복원. 발주 `20260706T2330Z`.
- **F2(→parser)**: 흥국생명 KR0071 2024.4Q item1後=35158/14後=16987/27後=207이 **출처불명**(available raw=오수집 사업보고서, 지급여력비율 수치·총괄표 부재; 207 정수+item14後 파생 냄새). parser 자기원칙(None+not_disclosed)·sibling item28後(None)과 모순 → 인용 or null 요청.
- **F4(→downloader/OCR)**: 하나생명 KR0097 2024.2Q 스캔이미지(56p text0)지만 DPI렌더로 전 코어 복원가능(현재 0레코드, parser "OCR채움" 미반영). 영구 dead-end 아님.
- **F3 수정 완료(validation 도메인)**: `kics_json_rules.py` rule_8_post 폴백버그 — item2後 결측인데 item14後만 있으면 `expected=pre2/post14`(pre분자÷post분모 혼합) spurious RED. **분자/분모 same-basis(`(2 in values_post)==(14 in values_post)`)일 때만 검증**하도록 수정. spurious 8_post RED 3→0, GREEN 458 보존(coincidence-pass 19만 정당 skip). 진짜 결측은 transition MISSING이 독립 검출 → 은폐 없음. 테스트 25/25 pass.
- **게이트 현황(exit 2 유지, push 차단 정상)**: 룰 RED 8(KR0087 2023.2Q 7 + KR0079 8_life 1 = 전부 scan-only pre-existing/documented) + census MISSING 3(하나생명 2024.2Q·카카오 ×2) + transition MISSING 7(흥국화재2·악사2·에이비엘1·흥국생명1·푸본1). transition 7 중 5(에이비엘·푸본·흥국생명)는 F1/F2로 처리 예정, 2(흥국화재)·악사는 raw 부재(downloader/연말이연) 정당.

## 2026-07-06 — 🔴 경과조치 "적용후" 가짜수정 적발 + 게이트 하드룰 (owner #6, user 지목)

user: "경과조치 적용사면 적용 전후로 지급여력비율이 같아선 안 된다"는 도메인 불변식으로 파서 재실행 검증 지시. → **파서 "복사버그 정정" 커밋이 가짜수정임을 적발.**
- **적발**: 파서가 커밋 5건(`31bcead·55e81f3·f3b4013·ad968cf·c604e0e`)으로 처리 주장했으나, item27 적용후를 raw에서 추출한 게 아니라 **round(적용전)을 적용후 칸에 복사**(exact-identical만 피한 위장). 22 적용사 item27 285셀: **복사/반올림(|후−전|<0.1) 139 + 결측 19 + 역전 6 = 164 가짜(57%)**, 진짜 후>전 121뿐. 결정적 근거 = 정상 마진 50~190%p(한화손해 176.7→254.4·아이엠 158.5→294.8·DB생명 202.4→361)라 후=전(차이 0.01)은 물리적 불가.
- **게이트 하드룰 `_transition_ratio_after_capture`** (owner 20260703T1138Z #6): 불변식 = 경과조치 적용사는 item27 적용후 > 적용전. 적용사 = **owner 22 seed ∪ 동적탐지(후−전≥1%p 분기 ≥2)**. 적용후 (후−전)<1%p OR None OR 후<전 = **RED, exit 2 하드차단.** item27 전용(금액계열은 경과조치 종류별 방향 상이).
- **라이브 168셀 검출**(21 적용사; **IBK연금만 0 = 유일 정상재추출 → 룰 오탐 0 확인**). self-test 7/7. 파서 반려 `20260705T2150Z`.
- **publish = 보류 확정**: 적용후=화면 표시값(경과조치 후 지급여력비율)이 21사 168셀 가짜 → 진짜 재추출 + 게이트 168→0 전엔 불가. 게이트가 이제 하드 강제.

---

## 2026-07-05 (c) — parser 0745Z 백필 검증: PARTIAL 14→3, 잔여 진짜갭 2건 재발주 + 자체정리

parser가 0745Z(census 백필 발주) 처리 완료 주장 → **데이터로 검증**(말 안 믿고 시계열 대조).
- **parser 실적**: PARTIAL 14→4·FULL_ABSENT 14→2. docling 미실행 11건(raw는 있으나 md_inbox 부재) 재docling+fill, item27 중복행 dedup(삼성생명·메트라이프 14분기), 부수버그 2건 수정(KR0082 2023.3Q item29 cell-shift 부모값 복제→987.32 / KR0097 2024.4Q item35 1000x→52.08). 커밋 3(`f62add4·26b8446·748a8b2`).
- **잔여 4 PARTIAL 시계열 검증 → 파서 주장 일부 반박**:
  - **KR0073 교보 2023.2Q item35(대재해)** = 진짜 갭(파서 놓침): 다른 11분기 전부 ~3,450억(±3%)인데 2023.2Q만 빔. → 재발주.
  - **KR0075 BNP 2025.3Q item37(주식)** = 파서 "실제0 공시" 주장 **반박**: 12분기 전부 67~311억, 0인 적 없음. 생보사 주식위험 0 비현실적. → 재발주(2025.3Q 표 재확인).
  - KR1098 카카오 2023.3Q item40(자산집중) = micro(1.3~68억), 0 가능성 수용 → parser에 "0이면 None 아닌 0.0 적재" 권장.
  - KR0051 신한이지 2023.2Q item32(LTC) = 값 ~1억(median 1.0=floor 경계) 오탐 → **`_CHILD_MATERIAL_FLOOR` 1.0→5.0억 상향**(진짜 갭 median 24억+ 무영향, self-test 7/7). PARTIAL 4→3.
  - KR0104·KR1010 2023.2Q FULL_ABSENT = 파서 확정 legit-absent(원천 세부표 부재) 수용.
- **재발주**: `inbox/parser/20260705T0805Z…census_residual_2cells`(교보 item35 + BNP item37, 데이터 증거 첨부). 현 PARTIAL 3 = 재발주 2 + 카카오 micro 대기.

---

## 2026-07-05 (b) — parser 재라운드 검증: KR0083 해소 → prepush GATE-CLEAR (RED 1→0)

파서 재작업(IFRS17 viz 재빌드 + KR0083 2025.2Q K-ICS 재추출) 검증.
- **KR0083 2025.2Q 완전 해소**: downloader가 오슬롯 PDF 교체(KR0075 BNP 파일이 KR0083 슬롯을 덮고 있던 원인) → parser 재추출(items 1-28 교차검증 일치·subs 29-46 복원·item19=√(VᵀMV)=8559 reconcile ✓, #32 장기재물=푸본현대 전분기 미공시 legit-absent). → **prepush(data-contract) RED 1→0 = GATE-CLEAR**(provisional=False), K-ICS RED 9→8, FULL_ABSENT 16→14.
- **K-ICS RED=8 = 전부 documented**: KR0079 8_life(SKIP=비차단) + KR0087 동양 2023.2Q ×7(코어표 이미지전용 scan-only census갭, `TODO.md` L89). 신규 RED 0.
- **IFRS17 마스터 코어 무손상**: closing 324P/0F · crosscheck 0F · cont 0 · dup 0. sens 1R(라이나 known)/direction 18→20(민감도 재빌드, 비차단).
- **push 잔여 = 내 신규룰 PARTIAL 14**(parser worklist 0745Z 아직 open/미드레인) — 실제 갭, parser 백필 대기. 내 validation inbox empty.
- ⚠️ **관측**: prepush data-contract 게이트 census는 `_coverage_census`+`_parent_zero_child_nonzero`만 재사용, **내 `_parent_present_child_incomplete`(PARTIAL 14)는 미포함** → prepush=RED0인데 K-ICS 게이트엔 14 PARTIAL 잔존. push 권위 게이트에 신규룰 배선 검토 필요(follow-up).

---

## 2026-07-05 — parser IFRS17 재빌드 검증 + IBK연금 무재보험 false-positive 해소 (owner "cell 등록")

parser가 IFRS17 레인 재빌드(viz 패널 + 마스터: csm_waterfall·pl_breakdown·sensitivity_heatmap·bs_snapshot + DART FS 캐시). 게이트 전수 재검증.

- **코어 정합성 무손상**: IFRS17 **closing 324P/0F · crosscheck 0F · plausibility cont 0/dup 0** — 재빌드가 기본 등식 안 깨뜨림. **tier2 data-contract RED 4→0** (두 달 막던 소진율/분모 이슈 해소 확인).
- **push 게이트(prepush) RED 5→1**: 5 RED = KR0083 2025.2Q 19_market(진짜 갭, 이미 parser 0745Z 라우팅) + **IBK연금보험 재보험손익=0 ×4**(`IMPOSSIBLE_ZERO_LEG`). IBK연금 4건은 **오탐** — 순수 연금사 무재보험 입증(재보험 5개 leg 전부 0.0 + 원수분해 정확히 닫힘: 원수CSM상각35111.6+위험조정2162.6−예실차5855.7−기타4015.9=생명장기원수손익27402.6). 손보 장수 케이스와 동형(카테고리로 단정 금지).
- **owner 결정 "cell 등록"** → 처리: (1) `data/_gold/user_pl_confirmed_cells.json`에 IBK연금 2024.4Q·2025.4Q 재보험 legit-zero **4셀 등록**. (2) `validate_data_contract.py._pl_impossible_zero_leg`가 owner-confirmed registry 존중하게 배선(skeptic과 동일 `_load_owner_confirmed` 패턴, tol 내 재드리프트 시 재발화). (3) 마스터 게이트도 whack-a-mole 방지 위해 `IMPOSSIBLE_ZERO_EXEMPT` + `ZLEG_LEGIT`에 IBK연금 면제(에이비엘 선례 동형). → prepush **RED=1**(KR0083만), 마스터 **impossible0 4→0·zero_legs 5→3**(잔여 동양/예별 known).
- **잔여 전부 known/legit**: pl_bridge 6F(전부 2023.1Q 사이트 비노출 + KB라이프 소액), zero_legs 3(동양 2025.3Q·예별 소형손보 생명장기 None), sens 1R(라이나 천원 미정규화 V12 audit-only), anomaly 199Y(마이크로사 triage큐 비차단). **push 차단 = KR0083 1건뿐**(parser 백필 대기).
- 부수: `_data_contract_selftest.py` 부재(pre-existing purge, git無) → `--selftest` 불가하나 본 게이트 정상. 회귀는 라이브 실측(RED 조성 검증)으로 대체.

---

## 2026-07-04 — 게이트 사각 2종 신규룰 (parser blind_spot 0703 처리): 부모-자식 census + 지급여력비율 스파이크

parser blind_spot `20260703T1250Z`(owner 워크스루가 게이트 RED=0 통과분에서 잡은 2부류) 처리. 데이터는 parser가 이미 수정, 이건 **룰 강화**(auto_loop 아님). 둘 다 `scripts/validate_kics_disclosure.py`에 구현, self-test 7/7 PASS.

- **사각 B → `_parent_present_child_incomplete` (RED, 차단):** 부모 위험액(item17/19) present&비0인데 그 회사가 '평소 유의미하게 보고하던' 자식(29-35/36-40)이 결측 = docling 행 누락. 기존 `_parent_zero_child_nonzero`의 역방향(부모>0·자식결측) 사각을 닫음. 자식 '기대'는 **회사별 self-census**(부모-present 분기 과반 present & 중앙값≥1억) — **회사유형이 아니라 회사별 실보고값 기준**(owner 지적: 손보사도 장수리스크 있을 수 있음 → DB손해 406억·코리안리 45억·삼성화재 20억 실보고 확인, 검출대상 유지). 구조적 N/A·상시0(생보 LTC item32 등)만 자동제외. **PARTIAL**(자식 일부 present+기대자식 결측=표실재·행누락)만 RED 승격, **FULL_ABSENT even-Q**(자식 전부결측, 2023.2Q 도입초 간이공시 클러스터 의심)는 자동RED 대신 **원천확인 review(비차단)**. 라이브: PARTIAL **14 RED**(KR0050 24.1Q/24.3Q/25.1Q item34·35 = blind_spot 예상 3건 정확 발화) + FULL_ABSENT review 16.
- **사각 A → `_ratio_series_spikes` (YELLOW, 비차단):** item27(지급여력비율) 회사별 시계열에서 인접 2분기 '양쪽 모두'와 크게 벌어진 단일 분기 = 엉뚱한 회사 PDF 오적재 같은 소스오염(자기정합적이라 산술룰 GREEN 통과). **부호역전 자체는 flag 안 함**(자본잠식사 정상 0선통과) — resid=|x-(prev+next)/2|>max(30, 3·(|prev|+|next|)) & 양옆 각각 30%p 이탈. 라이브 발화 0(parser 수정 후 clean), 옛 KR0083 25.2Q +318 주입 시 정확 발화(self-test). item27 중복행(삼성생명·메트라이프 전정밀도+반올림 이중기재) 분기 dedup 포함.
- **무손상 확인**: 기존 run_validation RED=9 불변(내 추가는 findings/by_status 미접촉, 별도 report 섹션+exit code만). census/parent-zero 기존 로직 그대로.
- **후속 라우팅**: 발화 14 RED + 16 review 백필 → `inbox/parser/20260704T0745Z…parent_child_census_gaps`(부수발견 2건 동봉: item27 중복행·세션중 kics_disclosure.json 재작성=parser 활성 추정). blind_spot 0703 = **resolved**(inbox/_resolved). owner tier_limit 1529Z도 resolved 아카이브.

---

## 2026-06-20 (b) — owner xlsx/JSON 직접수정 후 게이트 3종 전수 재검증 (push-gate 무결성, 재적재 0)

owner가 `sync_owner_fills_to_json.py`(135셀)+`insert_kakao_missing_quarters.py`(89행)+MOLE 손정정(교보 원수예실차·BNP 단위·코리안리 중복)으로 **root JSON 직접수정**. validation은 owner 지시("덮어쓰지 마라")대로 **재적재 금지, read-only 검증만**(`validate_master_tables.py --no-build`로 owner값 보존 — 빌드 선행 시 diag 미반영분 소실 위험).

- **data-contract 게이트(`prepush_check.py` = push #0): RED=4, 전부 tier2(CHECK 4 domain identity).** 동양·KB·미래에셋 2026.1Q `T2_UTIL_OVER_100_NO_EXEMPTION`(proxy-gross artifact) + 신한이지 `T2_DENOM_NOT_SCR_HALF`(1/100 스케일). 하나손·악사=YELLOW(면제표 파싱 legit "100%+"). **전부 owner `TODO.md`(2026-06-20) + inbox 라우팅 완료**(UTIL×3=downloader OCR 0617Z, DENOM×1=parser ifrs17 0238Z). push는 4건 해소 후 = 현 BLOCKED 정상. **validation 신규발주 0.**
- **owner CHECK 4 리뷰(재구현 0)**: 면제표 파싱사=YELLOW / proxy 미파싱=RED / RBC 분모=RED 분기 전부 의도대로. 회귀 "KB류 미추출>100%=RED" 하드강제 충족. tier_limit inbox(1529Z) resolved.
- **K-ICS 게이트: RED=1**(KR0079 미래에셋 8_life 2023.2Q, scan-only SKIP 비차단) + census missing 4(동양/하나생명/카카오 이미지 PDF) — 전부 `TODO.md` documented.
- **IFRS17 master 게이트: closing 321P/0F · crosscheck 0F** 유지 = **owner PL 121셀+CSM 10셀 수정이 정합성 무손상**. plausibility **cont 12→6 감소**(owner 손정정이 오히려 개선). 잔여 sens 1R(라이나 천원 미정규화=기존 0712Z/V12 audit-only 밴드레이아웃 추적), pl_bridge 14F(2023 known + 한화생명 이상치, 비차단), zero_legs 1(동양 2025.3Q known).
- **owner 룰7/8 dynamic tolerance 독립검증 PASS**: `max(eff_tol, |exp|×0.5/d14 + 50/d14)` dynamic항이 분모 d14(item14)에 반비례 → 정상분모 tol=2.0 불변, 카카오 20억만 tol≈124%p. 진짜오류 마스킹 0(게이트 실측 K-ICS RED=1만=타사 미마스킹 확인) → owner 감사주장("카카오 2023.4Q 2건만") 정합.

- **cont 6건 처분(owner 결정 2026-06-20, "마저" 후속) = 둘 다 데이터 정정(면제 아님)**: 교보생명 2024 = legit 소급정정 → **후속 공시 '전기' rollforward로 과거 cell 정정**(owner 제안). 처음엔 `CONT_RESTATEMENT_CONFIRMED` 면제 등록했다가 owner가 "면제 말고 전기표에서 재작성값 가져와 정정" 제안 → **면제 코드 원복, parser 0600Z 정정 발주로 전환**(시계열 통일이 면제보다 정확). 삼성생명 2024 = misparse(owner: 2023.4Q 기말 122474 정답) → parser 0545Z. **raw XML은 purge지만 extracted(`data/dart/extracted/<회사>_<rcept>_measurement.json`)는 살아있어 실행가능** — raw 없을 때 후속 공시 비교열 추출이 우회로. 정정 후 cont 6→0. 라이나 sens RED → V12 0435Z phase2 추적 핀. pl_bridge 14F = 전부 known(2023 비노출 12 + 소액잔차 2).

**종합: push 차단 = ① data-contract tier2 4건(parser 0238Z/downloader OCR) + ② IFRS17 삼성 cont(parser 0545Z 정정 대기). 둘 다 데이터작업 = validation 소관 밖.** 그 외 신규 글리치 0, 잔여 전부 owner 인지/라우팅/documented.

---

## 2026-06-20 — 룰7/8(지급여력·기본자본비율) 초소형 분모 동적 tolerance (orchestrator FYI)

owner가 카카오페이손해(KR1098) 2023.4Q·2024.4Q 통째결손을 xlsx로 채워 JSON 직접삽입(89행) → 2023.4Q에서 **KICS_7·8 RED**. 원인=기본요구자본(item14) **20억** 초소형 분모의 정수반올림: 재계산 974/20×100=4870 vs 공시 item27/28=4777.18(정확). 분모 ±0.5 반올림이 비율 ~120%p 흔듦. **`kics_json_rules.py` 룰7·8에 동적 tolerance** `max(eff_tol, exp×0.5/|item14| + 50/|item14|)` 추가(기존 **8_life 선례 동형**, line 429~432). 감사: OLD-fail→NEW-pass 셀=**카카오 2023.4Q 2건뿐, 타사 0건**(단조 widening, 진짜오류 마스킹 없음 검증). 게이트 RED 13→11. parser 0811Z 후속2 참조.

---

## 2026-06-17 — data-contract 게이트 마무리(서브에이전트 한도중단 복구) + consolidate 자동아카이브 + inbox 드레인

- **data-contract 게이트 완성**: 면제 메커니즘 제거(zero-RED 정책) + Phase 2 사이드카 reader 추가를 시킨 서브에이전트가 **세션 한도로 중단**(reader+helper는 작성, `Env._load_provenance_sidecars` 로더만 누락 → AttributeError 크래시 0/7). 메인이 누락 로더 추가로 복구: `--selftest` **7/7**, 라이브 **exit2 RED=52**(sensitivity 22 STALE_AS_OF 유지). reader=사이드카 있으면 strict/없으면 Phase-1 fallback.
- **`consolidate_inbox.py` 자동 아카이브**(owner): `_archive_resolved()` 매 실행 시 stage 폴더 `status: resolved`→`inbox/_resolved/`(answered 제외, idempotent, 동명 중복제거) + `_data_contract_findings` 핸들러 pre-wired. 일회 sweep 포함 resolved 19건+ 정리.
- **validation inbox 0 open 드레인**.

---

## 2026-06-16 — 부모-자식 정합 룰 신설(SGI 게이트 사각) + INTERNAL_MODEL_36IRR 등록 + 카카오 cadence 정정

owner 라이브 QA 3차 inbox 드레인(`…SGI…catastrophe_misparse_blindspot`, `…kics_market_irr_exempt_register`).

**🔧 신규 룰 — `_parent_zero_child_nonzero` (`validate_kics_disclosure.py`)**: 부모 위험액 항목이 표에
present & ≈0인데 하위 세부 비0 = 구조상 불가능(K-ICS 상관행렬 집계상 분산총액 ≥ 최대 단일세부) → RED(게이트
차단 exit 2). 부모 매핑은 명시 item번호(항목번호 flat index·라벨접두어 '1.'은 자본tiering에도 출현 → 접두어
매칭 불가): item17(생명장기)→29-35, item19(시장)→36-40. 부모 결측은 census 소관이라 제외. owner SGI 25.4Q
대재해(item35=5212/생명장기 0) 사각 폐쇄. **전수 스캔 3셀**(owner 1 + 적발 2): 서울보증 2025.4Q·2023.4Q,
카카오 2023.3Q — 전부 대재해(item35) 오정렬. 파서 발주(`…parentzero_catastrophe_plus_kakao_19market`).

**✅ INTERNAL_MODEL_36IRR_EXEMPT 등록(owner 승인 2026-06-15)**: `kics_json_rules.py` frozenset + 36_irr 블록
최상단 SKIP 단락. 5셀(KR0073 2025.2Q · KR0094 2024.2Q/2024.4Q/2025.2Q/2025.4Q) RED→SKIP. **36_irr RED 11→6**
(잔여=KB 이미지 3 + 신한이지 micro 3). 내부모형사 — 41-46 순자산가치 present라 표준식이 _check_numeric RED를
내므로 최상단 SKIP. 근거 = 회사 시나리오별 금리위험액 직접공시 → 식 정확일치(KR0094 25.4Q=578,999).

**🔴 카카오 2023.3Q 19_market = cadence-SKIP 부적절(TODO line 79-80 정정)**: parser 제안("NO-HEADER cadence")을
검증하니 docling MD L177-186에 분해표 실재(시장위험액 248/금리 15/부동산 244). 19_market RED는 참(JSON 36-40
미적재) → cadence-SKIP 안 함(실재 표 은폐+회귀 위험). 단 micro 억원-coarse(item19=2=248백만/100)라 적재해도
near-0·reconcile 불안정 = 카카오 2023.2Q 동류 micro artifact. 처분=파서 적재 후 micro documented or owner
micro exception(cadence 아님). 회귀: pytest tests/unit 110 passed.

## 2026-06-16 (b) — V7 NB CSM 시계열 off-by-one 재확인 + check_nb_csm_history.py 복원 (backlog #5)

owner "바로 진행" → backlog_digest #5(history 빌더 off-by-one 회귀 → check 재실행, systemic-3 재확인) 처리.

- **off-by-one-year 회귀 = FIXED 확정**: 현 `data/ir/series/`는 Q1 YTD-reset 정합(삼성화재 nb_csm_eok 6782.7→14426→26068→34995, 2024.1Q 8855.5 리셋 = 1년 시프트면 불가능). series mtime 10:40 > stale check 10:35이나 ir_eok·flag 완전 동일 = 시프트 흔적 0.
- **`scripts/check_nb_csm_history.py` 복원**: 사라진 ad-hoc 도구를 self-contained 재작성. 컨벤션을 series 메타에서 도출(nb_csm_singleQ_eok field=singleQ / units "YTD"=ytd_delta / else per_q_delta), DART new_business YTD→per-Q delta(Q1 raw, mn→억). DART per-Q가 stale matrix와 정확 일치(faithful 검증). `data/_derived/nb_csm_history_check.json` 현행 갱신, exit 2 if OVER/UNDER. 소비자 0(standalone 리포트).
- **systemic-3 = 실재(정렬 아티팩트 아님), 근본원인 = DART partial 추출**: 롯데 2025.2Q status=partial→NB_YTD=0→delta −1098.5(음수 NB 불가) / 미래에셋 2025.2Q·3Q partial→YTD collapse→2025.4Q ok에서 catchup spike(=‟↑↓ 교대") / 2025.2Q cohort-wide=동일 partial(반기·3분기 CSM 블록). DB 부호반전은 DB DART 2025.2Q+ 부재로 재현 안 됨(현상 롯데로 이동). 삼성생명 2025.2Q OVER(+26%)=status=ok=진짜 DART↔IR scope 차이(별건).
- **라우팅**: parser/ifrs17 `20260616T0230Z__validation__MULTI__nb_csm_partial_extract_corrupts_history`(partial 재추출 + status∈{partial,no_csm_block} 전사 sweep + 삼성생명 별건). 검증측 #5 완료, parser 재추출 트리거 대기.

## 2026-06-16 (c) — backlog #6/#7/#8/#9 (4-에이전트 Workflow 병렬 + 통합)

owner "전부다 진행" → backlog_digest 잔여 4건을 Workflow(4 에이전트 병렬)로 처리 후 메인 통합·검증·라우팅.

- **#6 삼성화재 FY2024 IR benchmark = RESOLVED / 현대해상 = owner·downloader**: `validate_nb_csm_multiple.py`에 `load_fy2024_ir_anchors`(IR series 2024.4Q.multiple_derived_ytd를 aligned FY2024 anchor로) + 삼성화재 PREFERRED_SCOPE에 monthly_avg_from_ytd. 삼성화재 computed 14.76 vs IR 15.16 rel 0.026 period_aligned=True fallback_used=False, **fallback_pass 2→1**. 현대해상은 in-repo FY2024 annual IR multiple 부재(1H/2H cadence) → fallback 잔존, owner 결정.
- **#7 V9 잔여 = 조사완료(parser-fix 0)**: closing identity 전부 EXACT(산술오류 0). (※ 한때 CONT 이중계상 면제를 넣었으나 **owner 지시로 즉시 revert: continuity break = 무조건 RED, "소급재작성" 면제 금지** — cont=15 유지, 면제 0. WFY 면제만 존치. 메모리 [[continuity-break-is-red]].) **[정정 2026-06-16: 오진 시인]** 교보 2026.1Q 등 5사 2026.1Q boundary = REAL 재작성 **아님 = 파싱오류**(owner 원본검증: 2026.1Q 기시=직전 2025.4Q 기말; 교보 65,110/메리츠 111,037/신한라이프 75,537/에이비엘 9,702/푸본현대 1,907.45). self-closing identity는 opening 검증 불가 = 내 오진. → downloader FY2026_Q1 raw 복원 + parser 재추출 발주(`…restore_fy2026q1_dart_raw`, `…csm_2026q1_opening_misparse`). 케이디비 2024.2Q +58%만 별건 within-period 변동. 저배수 4사 = scope 오류 아님(Q1 계절저점/micro, 분자 waterfall item2 일치; 한화 9.84는 IR FY 7.6 초과=‟low" 오독) → backlog framing 정정.
- **#8 verify_parser_change.py = DONE**: snapshot/diff(blast-radius; kics는 (code,quarter,item) cell-diff)/validate(6검증기 일괄 exit+summary 표)/all. 통합 `validate` 실행 확인(6검증기 정상). 추출기 변경 회귀 1커맨드.
- **#9 QoQ yaml loader = 이미 배선(no-op)**: `validate_master_tables.py:84`가 이미 `yaml.safe_load(config/qoq_thresholds.yaml)`. backlog 항목 stale.
- 회귀: pytest tests/unit 110 passed. verify_parser_change validate = 6검증기 정상(비-0은 전부 documented/routed: kics RED 동시변경, master cont/pl_bridge known, nb_csm_history parser 라우팅).

## 2026-06-16 (d) — KB PL 기타사업비 전수검증 + decision-free inbox 드레인 + data-contract 게이트 착수

owner: (1) decision-free inbox A-to-Z, (2) KB PL 기타사업비(item16) 전수검증.

- **PL 기타사업비(item16) 0처리 전수검증** (owner: IFRS17.html KB 보험손익 0.63조는 −16 없이 나옴, item16=0.39 차감이 워터폴 깨뜨림). 등식 `item1=4+5+6+7+8+13+14+(15−16)`(IFRS17.html:472). `scripts/check_pl_other_expense_closure.py` 신설 — pl_breakdown_master 244셀 분류: **ZERO 21**(보험손익이 −16 없이 닫힘 → item16 spurious) / KEEP 223 / NEITHER 31. ZERO = **KB손해 13분기 전부 resid=0 정확**(owner 케이스) + 케이디비생명 2023.2Q(0) + 흥국화재 6 early분기(2025.2Q부터는 −16으로 닫힘=비일관) + DB손해 2023.2Q는 resid −6,869=별건 제외. item20 영업이익=item1+item17이라 item16은 영업이익에도 안 들어감(=워터폴 전용 오류). → parser/ifrs17 발주 `…pl_other_expense_zero_where_closes`(build_pl_breakdown 일반규칙: 닫히면 item16=0, raw 비의존 transform). PL 마스터는 parser 리빌드 소유라 직접 편집 안 함(소실).
- **decision-free inbox 드레인**: (a) `doc_hygiene_prompt`→resolved (validation 프롬프트 3정정: gathering→parser·§3.1 inbox정본 재서술·misc 보조도메인 명확화). (b) `v7_gate_enforcement`(publishing)→resolved (check_nb_csm_history 복원 확인·V7는 data-contract ③ same-concept로 흡수+V1 retire 경로, 별도 publishing 블록 불요).
- **data-contract 사전-push 게이트 Phase 1 = DONE·검증** (owner `…data_contract_prepush_gate`, 최우선 인프라): `scripts/validate_data_contract.py`(+selftest) — 기존 validator import·호출(삭제 없음). 메인세션 검증: `--selftest` **7/7 PASS**(회귀 5건+변형) / 라이브 **exit 2 RED=52**(census 30=K-ICS 게이트 흡수+MISSING_FILER 6 · **as_of 22=신규 provenance 축이 V12 sensitivity_heatmap FY2024 staleness 적발** · cross-source 0) / build 미트리거. owner 결정 3: 22 STALE_AS_OF 처분(§4 면제 owner권한)·와이어링(§6)·exception 포맷. Phase 2 provenance 계약 정의 완료(parser/downloader 바운스 대기).

---

## 2026-06-15 — CSM 민감도 전수 재추출 발주(25.4Q 경영공시 기준) + DIRECTION_SANITY 룰 + 흥국생명 진단

owner: IFRS17.html CSM 민감도 흥국생명 이상(사망률↑ CSM−36 vs 25.4Q 경영공시 +28 / 해지율 역행 / 장해질병 누락) 지적.

- **진단(raw 검증)**: 현 heatmap 소스 = **FY2024 DART 사업보고서**(흥국 rcept 20250331003642, 2024.12.31) = **1년 stale + 비전수**(비상장사 DART 미제출). parser는 합계 행 충실 추출(해지율↑ 합계 CSM−1445.2/손익+61.12 = heatmap 일치 = **파싱오류 아님**). 장해질병 = FY2024 사업보고서 부재(경영공시엔 존재). 해지율 역행(CSM↓손익↑) = **source-faithful**(건강보험 product CSM−112,242/손익+564 견인).
- **소스 결정**: **25.4Q 경영공시**(`data/disclosure/FY2025_Q4`) — 전 보험사 의무·분기별·장해질병 granular. DART 사업보고서는 상장/대형사·연1회. 둘 다 2025.12.31·~2026.3 제출로 recency 동급, **커버리지·세분이 경영공시 우위** → 전수 fill 정답. inbox/parser(ifrs17) `20260615T0415Z__...csm_sensitivity_refill_disclosure_basis` 발주(파싱은 parser, validation 직접 안 함).
- **신규 룰 SENSITIVITY_DIRECTION_SANITY**(`validate_master_tables.py` 5b, owner rule-of-thumb): `sign(csm_delta)≠sign(pl_impact)`면 YELLOW(|CSM|·|손익|≥1억 floor). 손익/자본 컬럼 오선택·부호오류 전수 triage. 흥국 해지율형 source-faithful 역행도 flag되므로 fill 후 real(onerous) vs 파싱오류 판별. compile OK, stale FY2024 데이터엔 미실행(fill 후 작동).

## 2026-06-14 (b) — 정합성 전수검증: scan false-positive fix + sensitivity 단위룰 신설 + inbox 드레인 + 동시변경 적발

owner "docs 둘러보고 inbox·마스터 JSON 정합성 검증" 지시 → 3대 게이트 실측 + inbox 드레인.

**게이트 실측 (게이트 RED은 외부 동시쓰기로 변동, 아래 스냅샷 ~20:00 KST):**
- K-ICS `validate_kics_disclosure.py`: RED **42** (등식 21 + 시장 21) + census hole 21, exit 2. 등식 21 = 메리츠 rule5 ×12(systematic +45억) + 코리안리 2025.2Q core None ×7 + AIA rule2 ×1 + 미래에셋 8_life ×1.
- 금리민감도 `validate_kics_rate_sensitivity.py`: **RED 0** (RS3 32Y, DB손해 basis 예외 3). PASS.
- IFRS17 `validate_master_tables.py`: closing 0F·crosscheck 0F·pl_bridge 14F(2023 known + 메리츠 2023 + 한화생명 2023.2Q −90,613 이상치)·cont 15·wfy 2. + **신규 sensitivity RED 0/YELLOW 1**.

**🔧 fix 1 — `_scan_breakdown_presence` false-positive (삼성생명 odd-Q)**: distinct≥3 **substring** 매칭이 경과조치표 compound('주식위험액증가분점진적인식')·산문('자산집중위험등')을 라벨로 세어 odd-Q false RED. parser D 분쟁 raw 판정(KR0069 FY2023_Q3 MD L184/185/174/230 전부 비-표) → parser 정답, 06-13c "삼성생명 odd 3=진짜 갭" 자기정정. fix: 번호접두어 제거 후 **clean-cell 매칭**(셀==라벨/어간 또는 라벨 직후 숫자). 19_market RED 15→10(KR0069 odd 3 SKIP, 짝수·GREEN 불변).

**🔧 fix 2 — SENSITIVITY_UNIT_SANITY 룰 신설 (owner 0712Z claim2)**: `validate_master_tables.py`에 회사별 max|csm_delta| vs 또래 median 규모비. RED>1000x/<1/1000x(단위 미정규화, gate 차단)·YELLOW>100x/<1/100x. 현대해상=원단위→삼성화재 640배 케이스 회귀가드. 실측 RED 0(heatmap 19:58 재정규화로 640배 해소)·YELLOW 1(푸본현대 9.86억=median 1/308, ÷100 미적용 의심). 미래에셋·롯데·한화손해 3사 scenarios 0건(coverage 갭).

**🚨 동시변경 적발**: `kics_disclosure.json` mtime 17:16→**19:59:46**, `sensitivity_heatmap.json` 17:19→19:58 — **다른 parser 세션이 실시간 백필 중**(멀티세션 설계). 세션 중 게이트 RED 52→42, 시장 RED 31→21. 단일 스냅샷은 잠정값. 시장 RED은 parser 활성 도메인이라 라우팅 제외(중복 회피).

**📬 inbox 드레인 (validation/ open 3 → 처리)**:
- owner `census_gaps_sensitivity_sanity` → **resolved**. claim1(2025.4Q 36-40 전사누락)=라이브 staleness(데이터 38/38 적재·게이트 RED로 차단 중, 라이브만 미재배포=publishing/designer). claim2=sensitivity 룰 신설.
- parser `irr_exempt_register` **v2/iter2** → **answered**. 삼성생명 odd-Q resolved(라인번호 공유). TOOLING_FAIL census 요청=원칙수용·wire-up 보류(nonok.json이 데이터보다 lag, KR0011/KR0032 이미 빠짐, 진짜갭은 19_market이 이미 RED). INTERNAL_MODEL_36IRR/OCR/micro EXEMPT=owner 결정 상신(§4, 자체 waiver 금지).
- owner `backlog_digest`(0612Z) → #3/#4(시장36-40·item14후) 완료 종결, 잔여 open.

**근본원인 검증 Workflow(8 에이전트, raw 대조 진단→적대검증) → 라우팅**:
- **메리츠 rule5 ×12 → reparse**: parser가 item23(기타요구자본)+sub item25(비례성원칙)를 12 과거버킷 0 과소추출. 공시값(38~54억)=diff 정확일치, item14/15/22 정확. **라이브 2026.1Q는 이미 item23=57 PASS** = 구경로 버그. inbox/parser `KR0001_MULTI__rule5_item23_underextract` 발주.
- **코리안리 2025.2Q ×7 → reparse**: redocling이 MD 재생성 완료(코어 지급여력표 실재)인데 후속 파서가 금리민감도 스코프만 돌고 코어 1-28 추출기 미실행. item28 파생도출 필요. inbox/parser `KR1000_2025.2Q__core_items_not_extracted` 발주.
- **AIA KR0080 2025.1Q rule2(−789) → documented_exception(owner §4)**: image-only scan, item8/item9 둘 다 819(중복 OCR키잉), 텍스트 reparse 불가. 정확 allocation 미확정(item9≈30 추정). owner 등록 권고.
- **미래에셋 KR0079 8_life(2023.2Q +1367) → documented_exception(owner §4)**: image-only(파싱 MD조차 부재, pypdf 숫자레이어 0), subs 29-35 OCR노이즈 ~8.5% spread, 단일 culprit 없음. **기존 KR0079 rule2 예외를 8_life로 확장 권고.**

**재드레인(owner 지적 "안던진 inbox 없냐") — 동시변경 반영 재검증 + IFRS17 미발신 적발**:
- 데이터 재변경 확인: `kics_rate_sensitivity.json`(20:14)·`sensitivity_heatmap.json`(19:58, parser G7 재빌드) → **전 게이트 재검증**: K-ICS RED 42 · RS RED 0(20:14 변경 후도 안정) · master closing/crosscheck 0F · sens 0R/1Y. 내 답변 메시지 3건 무결(v3 clobber 없음).
- owner IFRS17 sensitivity 메시지(`ifrs17_csm_sensitivity_extraction`)는 **parser/ifrs17로 갔고 answered**(A G4b·C G6 삼성=백만원/현대=천원·B G7 5손보 복구). 그 답변 line 76 "validation 단위/비율 sanity 게이트 룰 권장"을 내 SENSITIVITY_UNIT_SANITY가 **충족**.
- **미발신 적발 → ifrs17 parser 발주**(`20260614T1135Z__validation__MULTI_2025__sensitivity_unit_ratio_sanity`): **푸본현대 csm_delta=9.86 vs pl=1164.85(비율 1/118, median 1/308) = under-scale** — 파서 OVER-scale 가드(>총CSM×3)의 사각(작은 쪽 미탐), 내 룰이 YELLOW로 포착. + 미래에셋(unavailable)·신한라이프(partial) CSM 민감도 coverage 재확인.
- parser 3건 회신(메리츠·코리안리·sensitivity) **전부 answered → 재검증 통과**: 메리츠 item23/25 12분기 적재(rule5 12 RED→0), 코리안리 코어 1-28+item28 파생+시장37-40(7 RED+19_market 해소), 푸본현대 = under-scale가 아니라 **mis-tagged 롤포워드**(shock행 0, parser `_has_shock_rows` 가드로 KB·푸본현대 ok→partial). 게이트 **RED 42→23**, sensitivity YELLOW→0. 3건 `_resolved/` 이동.

**inbox 백로그 triage (owner "1번 ㄱㄱ")** — validation-sent answered **16건 종결→`_resolved/`**:
- 06-09 continuity 8(KR0003/0011/KR1000 해소 + KR0009/0070/0072/0073/0099 = legit_restatement documented, WFY_EXCEPTIONS) / 시장 6(룰 라이브·146회수·fitz백필로 superseded) / qoq_signflip(동양 FIXED·교보 real·코리안리 escalate 3 verdict) / user_xlsx(06-11 재검증 통과·spawned 2건 clean).
- **유지(잔여)**: `hyundai_pl_legit_misjudge`(현대 2024.1Q~2025.2Q ZLEG_LEGIT_CQ 등록 잔여 — zero_legs 6 중 현대 5) + KR0083 2026.1Q continuity(현 RED Δ12.4%·sensitivity flagged = 실데이터 의심).
- **신규 in-inbox(parser irr_exempt 재확인)**: ① localizer **fitz-fallback LANDED**(KR0011·KR0032 ERR→OK, pytest 110) → **TOOLING_FAIL census 선결조건 충족, wire-up 가능**. ② **IBK(KR1011) 내부모형 면제서 제외**(fitz로 41-46 적재·derive rel 0.0% GREEN) → INTERNAL_MODEL_36IRR owner상신 = 신한라이프 4 + 교보 1 = **5건만**. ③ 현 RED 23 = 전부 OCR/내부모형/micro/scan = owner.

**A·B 실행 (owner "AB go")**:
- **(A) TOOLING_FAIL census 배선** — `validate_kics_disclosure.py._market_tooling_fail()`: nonok.json(localizer ERR/NO_SIGNAL/TIMEOUT/SCAN)을 현재 데이터와 대조해 *여전히 갭*(item19 공시·36-40 결측)인 셀만 're-localize' 워크리스트로 노출. stale-nonok 제외(데이터 lag 방지), 게이트 비차단(짝수 진짜갭은 19_market이 이미 RED — 원인 귀속용). 현 **TOOLING_FAIL=0**(3 nonok 전부 백필). parser fitz-fallback 안착 약속분 이행.
- **(B) 현대해상 2024.1Q~2025.2Q ZLEG_LEGIT_CQ 등록** — parser 표단위 raw확인(OLD form 비용측 LOB 부재) → `zero_legs 6→1`(동양 2025.3Q 잔여, 별건). `hyundai_pl_legit_misjudge` thread 종결.

**수렴 (parser 3 메시지 실시간 처리 → 내 재검증 PASS → resolved)**: parser가 KR0001(item23/25 항등도출=공시값 일치 적재)·KR1000(코어 1-28 + item28 파생 156.19 + 시장37-40 fitz보너스)·sensitivity(근본원인=mis-tag 롤포워드 shock행0, `_has_shock_rows` 가드 차단; 내 under-scale 가설보다 정확) 전부 answered. **재검증: 게이트 RED 42→23**(비-시장 21→**2**), **sens YELLOW 1→0**. 3 스레드 `_resolved/` 이관. **잔여 RED 23 = 전부 owner 결정 또는 parser 활성도메인**: AIA rule2 + 미래에셋 8_life = documented_exception 대기(2) / 시장 21 = localizer fitz-fallback 진행 + INTERNAL_MODEL/OCR/micro EXEMPT(owner). **validation-actionable reparse = 0.**

## 2026-06-14 — 파서 회신 2건 처리: 시장위험 146 회수 재검증 + item14후(8_post) 검증

새 parser inbox 2건 드레인(둘 다 resolved → _resolved):

- **`market_subrisk_recovered_146` 재검증 ✅**: 파서가 LLM추출+sqrt reconcile<2% 게이트로 36-40을 103→**146 all-five** 회수(41-46 144→**177**), gold 1325셀 영속화. master 반영 확인(all-five=146/41-46=177 실측). 게이트 19_market RED **148→21**(파서 회수 + 내 source-grounded cadence 합산). 파서가 이전 SKIP 요청 철회("200+ RED은 룰 아티팩트 아니라 underparse, owner·validation 옳았다") — 내 cadence 진단(홀수=간이공시) 독립 확인.
  - **핵심 회신**: 파서의 "odd-Q 103 EXEMPT 등록" 요청 **불필요** 통보 — source-grounded 룰이 disclosure MD 직접 읽어 홀수 간이공시를 자동 SKIP(수동 명단관리 불요, 분기 자동갱신). MARKET_BREAKDOWN_EXEMPT는 "짝수인데 원천도 부재" 예외만.
  - 잔여 19_market 21 = scan/OCR(AIA·카카오) + 짝수 full-form 결측(한화생명·흥국·DB·NH·KB손해·신한이지·처브) + 삼성생명 odd 3(텍스트표 존재·누락). `19market_real_gaps_21` inbox와 일치.
- **`post_transition14_done` (owner #4 / xlsx #3 blocker) 검증 ✅**: 파서가 생보 경과조치 적용후 item14후 적재(전=후 스킵버그 + _is_market_section 오분류 수정). 게이트 **rule 8_post = GREEN 442 / RED 0**(hollow SKIP 아님). 검증식 (2후+3후)/14후×100≈item27후 25/25 일치.
  - 파서의 룰 SKIP 요청 2건(36_irr/19_market 부분데이터 SKIP) **승인 안 함**: 0600Z에서 파서 철회. 올바른 해결은 SKIP rubber-stamp 아니라 데이터 회수 + source-grounded cadence(이미 적용). PDF census AGGREGATE 244 blanket 등록도 안 함(잠정후보).

게이트 현재: K-ICS RED 58(19_market 21 + 36_irr 16 + census 21), RS RED 0, IFRS17 closing/crosscheck 0F. owner #4 done.

## 2026-06-13 (c) — 19_market 과잉 RED 적발·수정 (source-grounded cadence; 148→21)

owner "19_market 148 진짜 어려운 거냐" 질문 → raw 추적으로 **내 2026-06-12 19_market RED 승격이 cadence 미처리로 과잉 flag**임을 적발(36_irr엔 넣은 cadence를 19_market엔 안 넣음 = 내 버그, owner 격노건과 반대방향).

- **진단(raw 확증)**: 148 RED을 MD 직접 확인 — 삼성화재 2025.1Q(홀수) MD엔 item19=60,822만 있고 36–40 세부표 없음(주식/금리위험액은 경과조치 문맥뿐). 생보 9사+삼성화재 등 **1Q/3Q는 간이공시라 세부표 원천부재**(69/72 raw 확증). 현대해상도 2023.3Q엔 표 있었으나 2025.3Q엔 없음 = 시기별 cadence 변화.
- **수정 (source-grounded + parity)**: `validate_kics_disclosure.py._scan_breakdown_presence()` — item19 공시·36–40 결측 후보셀의 disclosure MD를 직접 읽어 세부표 5종 라벨 distinct≥3이면 표 존재로 판정. `run_validation(source_has_breakdown=...)` 파라미터로 전달. `kics_json_rules.py` 19_market: **짝수분기(2Q/4Q full form)는 결측이면 무조건 RED**(텍스트스캔이 이미지/스캔표를 못 보므로 짝수는 숨기지 않음), **홀수분기는 MD에 표 있으면 RED·없으면 SKIP**(간이공시 cadence). `IRR_SCENARIO_EXEMPT`처럼 MARKET_BREAKDOWN_EXEMPT는 override 유지.
- **결과 19_market: RED 148→21** (EVEN 18 full-form 갭 + ODD 3 삼성생명 텍스트갭 = 진짜 추출가능 갭) / **cadence-SKIP 127 전부 ODD**(간이공시 원천부재, 짝수 숨김 0). GREEN 289 불변. 하나손해·삼성생명 2025.4Q는 파서가 이미 추출(GREEN).
- **자기정정**: 직전에 "148 전부 파서갭"이라 한 진술 철회 — raw 보니 ~127은 cadence-legit(내 룰 과잉), 진짜 갭은 21. 게이트 RED 264→**58**(19_market 21 + 36_irr 16 + census 21).

## 2026-06-13 (b) — 36_irr SKIP맹점 폐쇄(cadence-aware RED) + report_latest fresh-write

owner "TODO에서 확실히 고쳐야 하는 것만 골라 즉시 수정" 지시 → validation 단독 must-fix 2건(파서 무의존, 결정적):

- **36_irr SKIP→RED (cadence-aware)** (`kics_json_rules.py`): 19_market과 동일 맹점(부모 present·자식 결측인데 SKIP=통과). 단 41–46(금리위험 순자산가치 6시나리오)은 **짝수분기(2Q/4Q) 서식에만 존재**(실증: 41–46 보유분기 = 2023.2Q~2025.4Q 짝수 6개뿐, 홀수 0). 규칙: item36 공시·41–46 결측이 **짝수분기면 RED**(parser gap), **홀수분기면 SKIP**(원천부재 정당). `IRR_SCENARIO_EXEMPT`(빈값) 문서화 면제. 결과 **RED 23 (전부 EVEN, ODD false 0)** — 기존 SKIP에 은폐됐던 짝수분기 갭. 23건: 2023.2Q(BNP파리바·흥국화재) / 2023.4Q(KB손해·신한이지·에이비엘·하나생명·하나손해·흥국화재) / 2024.2Q(KB손해·교보플래닛·BNP·신한이지·흥국화재) / 2024.4Q(교보플래닛·신한이지) / 2025.2Q(교보플래닛·교보생명·하나생명) / 2025.4Q(IBK연금·KB손해·교보플래닛·케이디비·하나생명). → parser 41–46 재추출(market_subrisk inbox 후속).
- **report_latest.json fresh-write** (`validate_kics_disclosure.py`): 게이트가 매실행 `artifacts/kics_validation/report_latest.json`을 fresh로 덮어씀. 기존엔 orphan stale(5/25본)이 glob 정렬에서 timestamped 최신보다 뒤로 정렬돼 mis-read 유발(소비자 코드 0). 함정 제거.
- **게이트**: RED=268(19_market 220 + 36_irr 23 + census 21 + 등식 ~). 19_market 여전히 작동, compile OK.

## 2026-06-13 — owner 직접지시 kics_disclosure 데이터 정정 (dedup + 스케일 + AIA 적용후) + 19_market 면제 거부

owner가 kics_disclosure.json 다수 데이터 버그 지적. validation이 직접 정정(파서 무의존, 결정적):

- **중복행 dedup** (`scripts/dedup_kics_disclosure.py`, backup .bak): 16,160→15,665(−495). key+값 동일 34키 축약 / 값상이는 항등식 채택(비영단일 56, 23=24+25+26 closure 12 code·q, 27·28 정의식 13, 최빈 9; **FLAG 0**). garbage 기각(item12 68431·71335, item26 8313). 리포트 `artifacts/kics_validation/dedup_report_*.md`. 파서엔 "파이프라인 끝에 dedup 상설" + first/last/any 질문 답(="항등식으로 1행").
- **하나손해 2026.1Q 기본자본비율 2861%→28.62%** (`scripts/fix_kics_targeted.py`): 근본원인 item2(기본자본)=132375 ×100 스케일오류(item2>item1 불가 식으로 적발 — blanket threshold 아님; 카카오페이 6310%는 item2≤item1이라 정상 보존). item2→1323.75, item3 plug(−125617=item1−item2_old)→5434.25 복구, item28(적용전+적용후)→28.62. rule 1·8_post RED 해소.
- **AIA(KR0080) 적용전=적용후 강제** (owner: 경과조치 미적용사): 값_적용후 16행 copy-leak(item2=39162·item3=75984 frozen) 일소 + item27 8분기 도출(item1/14×100). rule 7 RED 해소. 적용전(값)은 파서 재적재로 이미 클린.
- **코리안리 자동차손익 null→0** 권고(owner: 자동차=일반 sub항목, 별도 미분리 = 정상). 파서 빌드 반영 요청.
- **19_market 면제 요청 거부**: 파서가 "fitz no-pdf 0건 = 223건 구조적 미공시"로 MARKET_BREAKDOWN_EXEMPT 등록 요청 → **blanket REJECT**. 근거: 하나손해(image-split)·삼성생명(라벨변형) 실공시 입증(2026-06-12a) = 추출기 한계지 부재 아님. reconcile-fail 3건은 표 존재. 조건부만 허용(image-split 스티칭+라벨변형 재추출 후, 그래도 없으면 raw 페이지 근거 첨부분만 셀단위 등록). MARKET_BREAKDOWN_EXEMPT 여전히 비어있음.
- **게이트**: dedup+정정 후 RED 293(19_market 229 + census 22 + 등식 ~42). 내가 유발한 RED(rule1 KR0050, 8_post KR0050) 전부 해소, 신규 0. 잔여 등식 RED(rule5/8 메리츠 등)는 기존 파서 추출 이슈.
- **진행 중(서브에이전트)**: 금리민감도 11사 2025.4Q 추출시도 + 현대 PL 2023–24 IR대조. 결과 도착 시 파서 라우팅. inbox 회신: `20260612T1100Z__parser__...2026q1_loaded_and_19market_exempt_request.md` ## 답변.

## 2026-06-12 (b) — consolidate_inbox 선배선(RS/waterfall) + V2 fallback 재검증 + market 스레드 정정종결

owner 백로그 다이제스트(#2/#6/#10) 즉시가능분 처리.

- **#2 consolidate_inbox VALIDATORS 배선**: `_rate_sensitivity_findings`(RS1/RS2_base RED) + `_waterfall_findings`(must_reparse) 추가, `VALIDATORS=[continuity,rate_sensitivity,waterfall]`. TEMPLATE을 `{section}`/`{request}`로 일반화(continuity 보존). 세 RED 버킷 0건 = **선배선**(owner "RED 발생 전 배선"). 06-09(a) "waterfall 항목 생기면 추가/untested 안 씀" 방침 → 스키마 확정(RS=runner dict키, waterfall=`failed` 버킷 동형)되어 pre-wire. 검증 3중(idempotent run findings=9 skip / 계약 플레이스홀더 테스트 / 합성 RED e2e: name→code·period유도 정상).
- **#6 V2 fallback**: `validate_nb_csm_multiple.py` 재실행 — **한화생명 fallback_used=False = retire 확정.** 삼성화재(2025.3Q 17.54 vs IR 14.1, rel 0.244=tol 0.25 턱밑)·현대해상(2025.1H)은 aligned FY2024 행 실패→fallback 통과(validator tolerance-loophole 경고). 삼성화재 IR annual benchmark 보강 미결(FY2024 IR 분모 소싱 필요).
- **#10 housekeeping**: inbox/validation 5건 `_resolved/` 이관(RS 2 clean + market 3 정정후). market_coverage_phase2_loaded의 "잔여 SKIP 정당(삼성화재·삼성생명·현대·한화 PDF 비공시)" 결론 **OVERTURN** 기록(=2026-06-12(a) 적발과 연결). "clean 종결" 아닌 "정정 종결"로 판단.

## 2026-06-12 — KICS 게이트 2대 사각 적발: coverage census 부재 + 19_market SKIP맹점

owner 격노 적발: (1) `kics_disclosure.json` 2026.1Q가 한때 KB손해 1개사(26셀)만 적재됐는데 게이트가 RED=0 통과 (2) 시장위험 세부 5종(item 36–40)이 거의 미적재인데 19_market이 SKIP으로 통과. 다른 세션은 즉시 적발. **근본원인 = 게이트가 "있는 셀이 맞나"만 보고 "있어야 할 셀이 있나"를 안 봄.**

**근본원인 (코드 레벨):**
- `validate_kics_disclosure.py`는 `run_validation(records)` — 데이터에 **존재하는 (회사×분기) bucket만** 순회. 분기/회사가 통째로 빠지면 finding 0개 → RED=0. 기대 universe 개념 부재.
- `kics_json_rules.py` `19_market`: 부모 item19 공시 + 자식 36–40 **전부 결측이면 RED이 아니라 SKIP**. 게이트가 RED만 세니 SKIP=사실상 통과. (`36_irr`도 동형 — 추후 검토.)

**수정 2건:**
- **`19_market` SKIP→RED 승격**: 부모 item19 공시인데 36–40 전무 → RED(parser gap 추정). 부분결측은 0 처리 허용 유지. 진짜 미공시는 `MARKET_BREAKDOWN_EXEMPT`(회사,분기) 문서화 면제(현재 비어있음).
- **coverage census 신설** (`validate_kics_disclosure.py` `_coverage_census`): regular-filer(≥분기절반 출현) × 분기 기대그리드 → 빠진 (회사,분기) RED + exit code 반영. 리포트에 `coverage_census` 블록·콘솔 분기별 미싱 출력.

**재실행 결과**: RED=292 (수정 전 사실상 은폐). 내역: 19_market 224건(36개사·13분기 전부 — 삼성생명/삼성화재/현대/DB/메리츠 포함) + census 미싱셀 28 + 등식 RED 40. **224건은 수정 전 전부 SKIP**이었음.

**raw 교차검증 (미공시 반증)**: 하나손해 2025.4Q는 5종 실재(금리30,358/주식62,491/부동산2,643/외환12,483/자산집중5,251)이나 표가 `<!-- image -->`로 분절 → 파서 미봉합. 삼성생명 2025.4Q는 "1.금리위험액"+충격시나리오방식 중간열 라벨변형. 둘 다 미공시 아님 = 전사 파서 갭. 2026.1Q는 항목 1–28에서 추출 절단(29–46 전무).

inbox: `20260611T2200Z__validation__MULTI_ALL__kics_market_subrisk_systemic_underparse.md` (route reparse — 36–40 전사 재추출 + 분절표 봉합·라벨변형 가이드 + 2026.1Q 29–46 backfill + census 28셀). 메모리: `coverage-census-mandatory` 신설.

## 2026-06-11 (c) — 현대해상 PL legit_absent 오판 적발 + AIA 사코드 + 불가능-0 leg 룰

owner가 현대해상 2026.1Q PL 답지(`gold/보험손익 breakdown_현대해상_2026.1Q.xlsx`)로 parser의 legit_absent 판정 반박.

- **AIA 사코드** (owner 재지시): `CSM_amortization.json` 10행 사코드 공란 → KR0080 채움. 원인: `build_tidy_exports.py meta()`가 kics_disclosure 원수사명만 봐서 kics 미수록 AIA는 None. `NAME_CODE_FALLBACK`(에이아이에이생명보험→KR0080) 추가(영속) + json 즉시 패치.
- **불가능-0 leg 룰** (`IMPOSSIBLE_ZERO_LEGS`): 생명장기 원수손익·기타원수·재보험손익·기타재보 4종은 장기보험사면 0원 불가 → 0.0이면 RED. 현재 0건(전부 None)이나 미래 가드. 메모리 `validation-blind-spots` 보강.
- **현대해상 legit_absent 오판 정정**: parser가 4종을 도출불가로 판정했으나 답지로 실재 확인(생명장기원수 279,302=241,253+37,322−126,865+127,592 검산 일치). raw에 보험수익 분석공시 멀쩡. ZLEG_LEGIT에서 **현대 회사면제 제거 → 8분기 재노출**. 단 **2025.2Q만** 진짜 미공시(보험서비스비용·재보험수익 자체 부재, owner 확인) → `ZLEG_LEGIT_CQ` 분기단위 면제.
- 교훈: legit_absent 주장은 **raw 표 존재로 교차검증** 필수 — 회사 전체 면제는 분기단위 진짜 미공시를 가린다.

inbox: `20260611T1000Z__validation__KR0009__hyundai_pl_legit_misjudge.md` (경고, route reparse, 8분기 재추출 + 2025.2Q 패스).

## 2026-06-11 (b) — parser 회신 재검증 통과: overrides 영속성·NB EX-기타·아이엠 정정 확인 + exception 등록

parser가 V9 inbox에 회신: ⓪ `csm_manual_overrides.json` + `_apply_csm_overrides()` 훅 구축(빌드 생존) ③ NB EX-기타 + `_MULT_FLOOR=1.0` 적용 ④ 아이엠 분자 CSM열로 정정(0.02→8.36/8.82) ① WFY 10/10 판별(DB손해 re-anchor 18셀 / 9건 legit restatement) ② PL None 분류 + gold-cell +170셀, 신한이지 CSM 제외(×1000 단위오류).

**재검증 (기본 빌드 포함)**: 정정 전부 빌드 생존 ✅ (롯데 16,774.38 / 아이엠 1,599.8 / DB re-anchor / 신한이지 제외). `--no-build` 모드 해제.

**exception 등록**: `WFY_EXCEPTIONS` 9건(legit restatement — 교보 3Q24 공식 소급재작성 등) + `ZLEG_LEGIT` (현대 분리미공시 4종 / ABL 재보 4종 / 서울보증·AIG·교보플래닛·신한이지 ALL). 결과: **wfy 9→0, zleg 23→1**(동양 2025.3Q 잔여).

**신규 발견 → parser 회신**: 메트라이프 영업이익 등식 2분기 FAIL(+12,086/+12,897, gold-cell 후 표면화) + 코리안리 crosscheck 2F 재출현(wf 2024.4Q 상각 ≈ pl 2023.4Q → 1년 lag 의심, KR1000 basis 연관).

SUMMARY: coverage 0/0 | closing 0F | dup0/spike1/cont16/wfy0/zamort0 | pl_bridge 2209P/16F(2023 12+메트라이프2+KB라이프·흥국 소액2) | zleg 1 | crosscheck 2F(코리안리) | qoq 195Y.

## 2026-06-11 — 사용자 xlsx 수기검수 적발 → 검증 사각 4종 보강 + 4갈래 조사

사용자가 마스터 xlsx 수기검수로 validation 미스 적발 (롯데 2023.2Q 기초, KDB 2023 상반기 상각 공란, 미래에셋 상각 누락, 현대해상 PL leg "0", 아이엠라이프 배수 0.02). **검증 사각 4종을 메모리+룰로 영구 반영**:

**신규 룰 3종** (`validate_master_tables.py`):
- **WFY**: FY내 기초 CSM 동일성 (YTD 컨벤션). 기존 연속성은 FY 경계만 봄. → 즉시 10건 적발 (DB손해 FY2023 4분기 전부 상이 등 — 롯데 동형 정정공시 의심, parser 재확인).
- **ZAMORT**: CSM상각 == 정확히 0 불가능 (사용자 룰 지시).
- **ZLEG**: PL 생명장기 sub-item 10종 중 0/None ≥4 무더기 flag → 28건 (현대해상 13분기 — **None이 bridge SKIP으로 은폐되던 패턴**; "0"으로 보인 건 xlsx의 None 렌더링).

**4갈래 병렬 조사 결과**:
- **xlsx diff**: 사용자 수정 24셀+신규 12행 식별 (롯데 2023.1Q신설+2Q전항목 / 케이디비 2023상반기 / 미래에셋 2023.1Q신설+2025.2Q~26.1Q 상각신설·가정재분해). → parser가 root JSON·xlsx까지 ingest 확인(19:12). ⚠️ diag stale — 다음 빌드 시 소실 위험, inbox CRITICAL로 전달. validation은 당분간 `--no-build`.
- **NB 분모**: 기타(비월납, 대부분 단체) 초회보험료 혼입 확정. EX-기타 시 농협생명 3.71→11.20, NH손해 1.74→11.38, KB라이프→10.48, 삼성생명→11.47 (10~17 정상권 진입). **삼성생명 EX-기타가 IR에 5분기 전부 근접**(MAE 0.43 vs 1.10; IR 정의=월납월초) → builder EX-기타 전환 권고. 교보·한화는 기타로 설명 안 됨(별도 원인). 568억은 NH손해 기타(농협생명은 649.8억).
- **PL zeros**: 정확히-0 무더기 0건 — 실체는 None. 예실차=0 45셀은 미공시→identity 유도(정상).
- **소스 추적**: DART 미공시 11사 전부 **연간 감사보고서(00760 별도, pblntf_ty=F)** 소스 — 검증된 공시지만 4Q만. **하나손해/하나생명/신한이지는 지주 분리가 아니라 자체 별도 감사보고서 파싱** (지주 보고서 미사용 — 분리 시도 자체가 없었음). 아이엠라이프 DART 분기 부재 = 비상장 지주 자회사(사업보고서 의무 없음). **아이엠라이프 0.02 = 분자 오염**(BEL+RA+CSM 행합 4.4억; 실제 CSM 1,599.8억) → parser 수정 대상.

inbox: `20260611T0900Z__validation__MULTI_ALL__user_xlsx_audit_followup.md` (diag 영속성 CRITICAL + WFY 10건 + ZLEG 28건 + NB EX-기타 + 아이엠라이프). 메모리: `feedback_validation_blind_spots` + `project_master_xlsx_review_loop`.

## 2026-06-10 — K-ICS 금리민감도 RS1–RS4 룰 구현 + 검증 통과 (RESOLVED)

owner 발주(RS1–RS4) + parser 마스터 적재(`kics_rate_sensitivity.json` 423행, 74 사·분기) → `scripts/validate_kics_rate_sensitivity.py` 신규 구현. 정본 `docs/agents/kics-rate-sensitivity-spec.md` §5.

- **RS1_RATIO_IDENTITY** (RED): (사,분기,경과조치)·충격컬럼별 `비율≈금액/기준금액×100`, tol max(0.5%p, 0.5%·비율). → **0 RED** (705 컬럼 전수 통과).
- **RS2_BASE_ANCHOR** (RED): 적용전 base vs kics_disclosure item1/14/27, tol 금액 2억/비율 0.5%p. → **0 RED** + KR0011 DB손해 2025.2Q 3 measure documented exception(별도/연결 basis, `RS2_EXCEPTIONS`).
- **RS3_DIRECTION_SANITY** (YELLOW): 생보 −100bp 비율 상승(역방향) 28건 — ALM상 정상 가능, 플래그만.
- **RS4_COVERAGE_CENSUS** (YELLOW): **회사 cadence 인식**(1Q/3Q 보유 이력 없으면 반기공시 → 1Q/3Q 부재 정상) → 손보 1Q/3Q 과탐 40→**1**(코리안리 2025.2Q hole).

**gate RED=0.** 룰표 `claude-agent-validation.md` §1.1 등재. 결과 `data/_derived/kics_rate_sensitivity_validation.json`. inbox owner/parser 2건 resolved. (consolidate_inbox 핸들러 배선은 RED 발생 시 후속 — 06-12(b)에서 선배선.)

## 2026-06-09 (d) — 시장위험 Phase-2 적재 재검증 통과 (RESOLVED)

parser Phase-2(PDF 직접추출, +150행 → 14,394) 재검증. `run_validation`:
- **게이트 RED=2**(KB손해 KR0010 rule2 OCR, KICS-IMG; **신규 RED 0**). 통과.
- `19_market` GREEN 163→**185** / SKIP 221→199. `36_irr` GREEN 42→**47** / YELLOW 17→23 / SKIP 314.
- 교보(KR0073) 전치표 5분기 스폿: derived vs item36 diff 0.1~2.8%(tol 5% 이내, YELLOW=정당).
- 잔여 SKIP 정당: 19_market 구조적 ~100(삼성화재·삼성생명·현대·한화생명 PDF 비공시) / 36_irr Q1·Q3 ~85(시나리오표 원천부재) / IRR 직접형 15(별도 schema 보류). ⚠️ 이 "정당" 결론은 2026-06-12(a)에서 OVERTURN(분절표·라벨변형 = 파서 갭).

inbox `phase2_loaded` **resolved**. **V3 시장위험 검증 한 사이클 완결**: 룰 구현 → 골든 → 1차적재 → 결손census → Phase-2 PDF추출 → 재검증 RED 0. 추가 적재 시 동일 게이트 재실행.

## 2026-06-09 (c) — 시장위험 item36–46 1차 적재 검증 통과 (RED 0)

parser가 item36–46 1차 적재 → `validate_kics_disclosure.py` (19_market/36_irr 활성) 재실행:
- **19_market: 163 GREEN / 221 SKIP / 0 RED**
- **36_irr: 42 GREEN / 17 YELLOW / 325 SKIP / 0 RED**
- 게이트 RED=2 불변(기존 KR0010 OCR).

**단위 정합 확인** (앞 (b)의 회신 요청 해결): item36–40을 억원(세부표 백만원 ÷100) 적재한 게 맞음 — 19_market GREEN 163건이 item19(억원)와 일치. YELLOW 17(36_irr)은 0.0~3.4% 미세편차(`classify_diff`). 게이트 무관. SKIP은 미적재 분기 — parser 적재 계속 시 자동 GREEN. parser inbox 회신: `inbox/parser/20260609T0300Z__validation__MULTI_ALL__market_risk_loaded_pass.md`.

## 2026-06-09 (b) — V3 시장위험 룰 19_market + 36_irr 구현 (8_life 복제)

parser inbox(`market_risk_rule`, `market_irr_rules_19_36`) 요청 → `src/solvency/validation/kics_json_rules.py`에 2룰 구현. 정본: `docs/agents/kics-market-risk-decomposition.md`.

- **`19_market`**: `item19 = sqrt(V'·M·V)`, V=[36–40](금리·주식·부동산·외환·자산집중). `MARKET_M` 5×5(대각1.0/외환-주식 −0.25/자산집중 행열 0/그외 0.25). `_diversified_sqrt` 재사용. **부분결측 허용**(없는 하위=0; item19 또는 36–40 전부 결측 → SKIP). dynamic tol `max(eff_tol, 5%·expected)`, IMAGE_OCR 10.0 승계.
- **`36_irr`**: `item36 = √[max(R상승,R하락)² + max(R평탄,R경사)²] + R평균회귀`. R=base(41)−시나리오순자산(43/44/45/46), 평균회귀=41−42(signed). 41–46 중 결측 → SKIP.

**골든 3/3 정확 일치**: 19_market 흥국 FY2023_Q1 sqrt(V'MV)=813,201백만=8,132억(=item19) / 36_irr 흥국 157,128(공시 157,127) / 현대 322,767(공시 일치).

**상태**: item36–46 적재가 parser 진행 중 → 신규 2룰 **전사 SKIP**(게이트 미반영). RED=2 불변(회귀 없음). 적재 후 자동 활성. 단위: 룰은 item36–40을 억원(=item19 동일단위) 가정 — parser 적재 단위 회신 대기. inbox 2건 answered.

## 2026-06-09 (a) — consolidator 스크립트화 (mechanical=script, judgment=agent)

운영 개선 #2: validator JSON → inbox 메시지 변환을 에이전트/수동 → **스크립트** [`scripts/consolidate_inbox.py`](../scripts/consolidate_inbox.py)로.

- **왜**: smoke-test에서 emit(consolidator)·eval을 에이전트로 돌리니 1 finding에 208k 토큰. 변환은 기계적이라 에이전트 낭비. 원칙 **에이전트=판단·신규성, 스크립트=기계** 적용.
- **consolidate_inbox.py**: continuity validator(`csm_continuity_validation.json`) findings → `inbox/parser/` reparse 메시지(값 시계열 + 내부 closing-identity precompute 포함). **idempotent** — `parser/`·`_resolved/`에 같은 (회사·기간·토픽) 있으면 skip. 신규 validator는 `VALIDATORS` 리스트에 핸들러 추가. waterfall must_reparse 버킷은 당시 비어 미적용(항목 생기면 추가 — untested 코드 안 씀). → 06-12(b)에서 RS/waterfall 핸들러 선배선.
- **루프**: validator 실행 → `python scripts/consolidate_inbox.py` → 사람이 "inbox 확인해라". (driver 상설화는 안 함 — 사람 킥으로 충분, owner 결정.)
- **배선**: `inbox/README.md` "consolidator 향후 작업" → 스크립트 명시; validation 프롬프트 §3.0 route 분류를 mechanical(script)/judgment(agent)로 분리.
- **inbox 정리**: parser fix로 해결된 3건(흥국 FY2023·코리안 FY2024·코리안 2024.1Q) + 스모크 데모 1건 → `_resolved/`. `parser/`에 live finding 9개만 남김. 폐기된 probe `_seed_continuity_inbox.py` 제거.

## 2026-06-09 — V4 QOQ_DELTA_WARN 구현 (시계열 anomaly) + parser inbox

V4 `QOQ_DELTA_WARN` 소비자 코드 구현 (`validate_master_tables.py` 4번). spec(`config/qoq_thresholds.yaml`)의 CSM 항목 대상:
- 누적 항목(신계약/이자부리/상각) → **YoY**(전년 동기 YTD 대비). net-quarterly QoQ는 분기 계절성으로 노이즈 폭발(645건) → YoY로 계절성 상쇄.
- 시점 항목(기말 CSM) → QoQ. floor 50억(작은 분모 % 폭발 제거).
- **PL 손익(보험손익/투자손익/당기순이익) 제외**: 시장·금리 민감 본질적 고변동 + spec items 미등록. (임의 추가했다가 590건 노이즈 → 철회.)
- YELLOW(다운스트림 차단 안 함). 전체 → `data/_derived/qoq_warn.json` (sign_flip 플래그 포함).

**결과**: 193건 YELLOW (신계약 69 / 이자부리 59 / 상각 51 / 기말 14). 대부분 사업변동. **진짜 데이터 의심 = 이자부리 부호반전 3건** (양수→음수): 동양 2025.4Q(1,134→−2,140)·교보 2025.3Q(3,242→−5,290)·코리안리 2025.2Q(318→−116).

→ parser inbox: `inbox/parser/20260609T0200Z__validation__MULTI_2025__qoq_interest_signflip.md` (route: blind_spot, 이자부리 부호 raw 확인 요청).

**교훈**: QoQ anomaly는 임계·기준(net/YoY/raw) 선택이 신호품질을 좌우. flow는 YoY, stock은 QoQ, 고변동 손익은 제외. 부호반전이 단순 %급변보다 강한 데이터-오류 신호.

## 2026-06-08 — MASTER_COVERAGE 룰 신설 (hole을 SKIP으로 숨기던 사각지대 보강)

**검증 결함 인정**: closing/pl_bridge/crosscheck가 항목 None을 전부 SKIP 처리 → 거대한 skip(pl_bridge 456 / crosscheck 227) 뒤에 "있어야 하는데 없는" 데이터(hole)가 숨어 있었음. parser census(WRONG vs HOLE 분리)가 먼저 짚음 — validation이 했어야 할 일.

신규 룰 `MASTER_COVERAGE` (`validate_master_tables.py` 0번): active 회사(핵심항목 ≥7분기)의 빈 분기 = hole. **2024+ = real hole**, 2023 = known(사이트 비노출), <7분기 = structural(외국계·소형 미공시, 제외).

**검출**: real hole(2024+) **4건** / 2023 known 40 / struct 18.
- **미래에셋생명 CSM 2025.2Q·3Q·2026.1Q** — `CSM상각` None (2025.1Q는 −483.6 있음). closing identity가 skip하던 것.
- **롯데손해 PL 2025.2Q** — `생명장기손익` None (1Q·3Q는 있음). pl_bridge가 skip하던 것.
→ **parser 데이터 채움 대상**. 둘 다 절댓값 검증을 통과한 게 아니라 *검증 자체를 skip*당한 케이스.

검증 철학 갱신: "값이 틀린 것(WRONG)"뿐 아니라 **"값이 없는 것(HOLE/coverage gap)"**도 1급 검증 대상. skip은 침묵이 아니라 분류돼야 함.

## 2026-06-08 — 빌드→검증 통합 (build_root_masters 자동 선행)

`validate_master_tables.py`가 검증 전 `build_root_masters.py`를 자동 선행(idempotent). 빌드 누락으로 "고쳤는데 검증에 안 보임" 문제 구조적 차단(아래 06-07(h) 교훈). `--no-build`로 끔. 회귀 명령: `python scripts/validate_master_tables.py` (빌드+검증 한 방).

## 2026-06-07 (h) — 흥국 해소 (빌드 누락이 원인) + 빌드 체인 교훈

흥국화재 "고쳤다"는데 3번 재검증해도 루트 `CSM_waterfall.json`에 변화 0 → **빌드 한 단계 누락**. 체인: `csm_waterfall_master_diag.json`(소스) → `build_root_masters.py` → 루트 `CSM_waterfall.json`. parser가 **diag는 22:13에 제대로 고쳤는데** **루트는 21:31 옛것** — `build_root_masters.py`를 안 돌려 미반영. validation이 빌드 실행 → 루트 갱신 → **흥국 완전 해소** (복붙 6→0 / spike 4→1 / cont 21→14).

**⚠️ 운영 교훈 (핸드오프 필수)**: parser가 소스(diag/viz)를 고쳐도 **`build_root_masters.py` 재실행 전엔 루트 마스터에 반영 안 됨**. mtime 비교(소스 > 루트)로 빌드 누락 탐지 가능.

**빌드가 드러낸 새 건**: 롯데손해 2025.4Q wf CSM상각 −980(거의 0, 이상치) → crosscheck +99.5% RED. 롯데 FY25 양식 이슈(V7)와 연관 의심 → parser.

## 2026-06-07 (g) — CSM_PLAUSIBILITY 룰 신설 (closing identity 사각지대)

사용자가 흥국화재 2025.4Q 기말 CSM이 **34.1억**(직전 26,693억)으로 비정상 폭락한 걸 지적. closing identity는 **내부 산술 합산만** 검증 → 가정조정(−28,929.9억)이 폭락을 흡수해 closing이 우연히 닫혀 통과(0F). **절댓값 plausibility 검증 부재가 validation 갭**.

신규 룰 `CSM_PLAUSIBILITY` (`scripts/validate_master_tables.py` 1b):
- **복붙(dup)**: 같은 회사 내 서로 다른 분기의 기말 CSM이 소수점까지 동일 → 복붙 의심.
- **기말 QoQ 폭변(spike)**: 기말 CSM `|ΔQoQ| > 50%`.
- **연속성(cont)**: `FY[t] 각 분기 기초 CSM = FY[t-1].4Q 기말`. tol max(0.5%·|전년말|, 2억). 2023은 SKIP. — 사용자 지적으로 추가, 가장 근본적인 sanity.

**연속성 검출 21건**:
- 🔴 진짜 오류: **메트라이프 2025.4Q 기초 48,134 = 2024말 24,067 ×2 (이중계상, KB라이프형)**, 케이디비생명 2025.1~4Q 기초 복붙, 흥국화재 2025.2Q·3Q 기초 복붙.
- 🟡 회색지대 (IFRS17 기초 재작성 가능): 삼성생명 2024 Δ−1,452·신한라이프·메리츠·에이비엘·푸본 작은 Δ; 교보(±2,905/+5,659)·KB라이프(+1,622)는 parser 확인.
- severity 권고: 배수/큰 Δ = RED, 작은 Δ = YELLOW.

**dup/spike 검출**: 6 dup + 4 spike, 케이디비생명·흥국화재 집중.
→ **parser 전달 대상**: 케이디비생명·흥국화재 2025 CSM_waterfall 재추출 + 메트라이프 2025.4Q 기초 2배. closing 0F였어도 절댓값이 틀린 케이스.

## 2026-06-07 (f) — DB손해·KB손해 별도/연결 fix → PL_BRIDGE 31F→16F

parser가 별도/연결 LOB 레그 fix를 DB손해·KB손해로 확장 → **2024+ 보험손익 fail 10건 완전 해소** (DB손해 5 + KB손해 5). 진단(DB=ΣLOB 결손 / KB=ΣLOB 과대, LOB 내부는 정합)이 정확히 별도/연결 레그 오선택이었음.

**PL_BRIDGE 31F → 16F**. 잔여: 2023 분기 11건(사이트 비노출) + 2024+ 5건(KB라이프 2024.1Q +1,136 / 악사손해 2024.4Q +3,483 / 흥국화재 2025.1Q −714·2025.4Q +1,684·2026.1Q +968).

**dual-form의 정당성 (사용자 확인 2026-06-07)**: 보험손익은 통상 `종목별 합 − 기타사업비`(adj)지만 일부 회사·분기(흥국 2024.4Q, KB 등)는 종목별 합산에 기타사업비가 이미 녹아있어 bare(`= ΣLOB`)로 닫힘. dual-form은 이 케이스를 통과시키려는 의도된 설계 → bare로만 통과하는 분기는 정상, flag 안 함. (앞서 "숨은 275억 LOB 결손/dual-form 허점" 진단·"회사별 form 고정 flag" 제안 철회.) 단 한화손보→삼성화재 LOB 별도/연결 교훈(§1.5)은 유효 — 과잉진단 금지.

## 2026-06-07 (e) — 보험손익 잔차 = LOB 별도/연결 레그 오선택 (진단 가이드 정정)

삼성화재 2026.1Q +2,067, 한화손보 2025.2~4Q를 "기타영업수익 누락"으로 진단했으나 **2건 연속 오진**. parser FS-API 검증 결과 진짜 원인 = **ΣLOB 별도/연결 레그 오선택**:
- 별도(OFS) 기준 회사는 FS-API상 **기타영업수익 구조적 0**.
- parser `pmin`(최소합계=별도) 휴리스틱이 **재보험 레그에서 뒤집힘**(연결이 그룹내부 재보험 상계) → 기준 불일치 → ΣLOB 결손.
- 분기마다 별도/연결 대소가 달라 같은 회사도 일부 분기만 fail.

parser fix(별도 보험수익 anchor + cost/재보험 레그 same-block `first_from`) → **삼성화재 2026.1Q + 한화손보 2025 둘 다 해소**. pl_bridge **36F → 31F**. 진단 가이드 §1.5에 박음: 보험손익 잔차는 "기타영업수익 누락"이 아니라 **LOB 별도/연결 기준 일관성부터 의심**.

## 2026-06-07 (d) — CSM_CROSSCHECK 진짜 2건 해소 → 0F

진짜 의심 2건이 서로 다른 원인이었음 ("재보험 혼입" 가설은 둘 다 빗나감):
- **KB라이프 2023.4Q — wf 버그 (parser fix)**: 사업결합(KB생명+푸르덴셜)으로 기초가 2줄. 전기 블록 기말이 사업결합 전 기초와 같아 값연속성 검사 통과 → wf가 당기 블록(−283,905)에 전기 블록(−146,769)을 합산해 **정확히 2배**(−430,674). closing identity는 비례 2배라 우연 통과, crosscheck만 잡음. parser `_is_prior_header()`(`['구분','전기']`) 추가 → KB라이프 13분기 OK, 상각 −2,839.1억(=pl ✓).
- **코리안리 2025.4Q — validation 룰 스코프 버그 (validation fix)**: 파서 정확. 재보험사 PL은 발행계약을 `원수CSM상각(4) + 수재CSM상각(4-1)`로 분리(41,154+32,210=73,364=wf 상각). crosscheck 룰이 PL 수재(4-1)를 빼먹어 false-positive → `p = 원수CSM상각 + (수재CSM상각 or 0)`로 수정(출재 9-1 제외). §1.2 반영.

**결과**: CSM_CROSSCHECK **66P/2M/2F → 68P/2M/0F**. CSM_waterfall 도메인(closing 0F + crosscheck 0F) 완전 정합. 잔여 MINOR 2건(에이비엘 6.9%·흥국화재 6.4%)은 경고만.

## 2026-06-07 (c) — CSM_CROSSCHECK tol 3단계 정책

`CSM_CROSSCHECK`는 **서로 다른 DART 표**(PL 보험수익 구성 vs CSM 변동표) cross 비교라 표간 반올림·집계 차이로 수% 편차가 구조적. **3단계 tol** 도입 (§1.2):
- **OK**: `|s| ≤ max(5%·|pl|, 300백만)` · **MINOR** (경고, pass): `5% < |s| ≤ 10%` · **RED**: `|s| > 10%` → parser loopback.

결과: crosscheck **9F → 66P / 2M / 2F**. 진짜 불일치(KB라이프 51.7%·코리안리 78.3%)만 RED, 경계 7건 흡수. 진짜 2건과 경계(최대 6.9%) 갭이 51%+로 커서 10% 임계 안전.

## 2026-06-07 (b) — CSM_waterfall closing 완전 해소 (parser 재추출 후 재검증)

parser가 CSM_waterfall 측정요소 변동표 재추출 → 재검증 (`scripts/validate_master_tables.py`):
- **CLOSING_IDENTITY: 40F → 0F** (299P / 0F / 6S). 23사 × 13분기 전부 `기초+신계약+이자+가정+상각 = 기말` 정합. 🎯
- **CSM_CROSSCHECK: 20F → 9F** (61P / 9F / 224S). 잔여 9건은 (c) tol 3단계로 정리(진짜 의심 2건 KB라이프·코리안리 + 경계 7건).

## 2026-06-07 — V8 마스터테이블 검증 소비자 코드 첫 실행 + 룰 정식화

사용자가 (거의) 전사·전분기 마스터테이블 구축 완료 → V8 소비자 코드 `scripts/validate_master_tables.py` 작성·실행. 입력: `pl_breakdown_master.json` (백만원, 32사×13분기) + `CSM_waterfall.json` (억원, 23사×13분기).

**3개 룰 첫 실행**: CLOSING_IDENTITY 218P/40F/41S · PL_BRIDGE(8단) 2023P/36F/469S · CSM_CROSSCHECK 33P/20F/190S.

**룰 정식화 (오탐 제거)**:
- **보험손익 dual-form**: `보험손익 = ΣLOB`(손보) 또는 `ΣLOB + 기타영업수익 − 기타사업비용`(삼성화재 등). 둘 중 하나 닫히면 PASS → 손보 bare-close 오탐 ~19건 해소.
- **영업이익 abs floor 200→600백만**: 0근처 회사(KDB 등) 과민 방지.
- **CSM_CROSSCHECK 4Q-only**: pl·wf 모두 YTD 누적 → 1~3Q 분기배분 노이즈 제거. 136F→20F.

**parser 1차 수정 반영**: item16 음수 7건 abs 정규화, item19 account_nm fallback 277셀 포착, item17 net 통일.

**남은 fail**: CSM_waterfall 도메인 60건(closing 40F + crosscheck 20F) = parser 재추출 · PL 잔여 36F(대부분 known FY2023 HTML fallback + 한화손해 dual 미닫힘).

회귀 명령: `python scripts/validate_master_tables.py`.

---

## Archive (pre-2026-06)

> 1줄 요약. 전문은 git log/blame. dead-end/폐기 근거는 프롬프트에 보존(SEGMENT cross-source 폐기·PL_BRIDGE §1.5 / 메리츠 보종 영구SKIP §1.2 / off-year→continuity §3.0 / dual-form 과잉진단 금지 §1.5 / 빌드체인 gotcha §3.0). K-ICS RED 진행 + 분기별 batch 원문은 `docs/claude-changelog.md` Historical archive(2026-05-24/25, 2026-04-26~28).

- 2026-06-01 (밤) — SEGMENT cross-source 폐기 + PL_BRIDGE_DART_INTERNAL 신설(§1.5, DART 자기완결 10등식, 삼성화재 2025.4Q PASS) → V8
- 2026-06-01 (밤 b) — 메리츠 CSM waterfall: breakdown 영구 SKIP + CSM_AMORT cross-table 신설
- 2026-06-01 (밤 c) — 통합 마스터테이블 입력 계약 + CSM_CROSSCHECK 확장
- 2026-06-01 (저녁) — 🚨 history 재빌드 off-by-one-year 회귀 발견 + check 도구 cohort 가드
- 2026-06-01 — V7 history-wide check 도구(`check_nb_csm_history.py`, 13Q×9사) + systemic 이슈 3건 발견(2025.2Q cohort-wide / DB 2025.2-4Q 부호 반전 / 미래에셋 ↑↓ 교대); FY24 widespread 6/7 OK(롯데 FY25 의존); 한화 V2 fallback retire 가능
- 2026-06-01 — V7 6/7 OK 회복 (parser 별도·당기 disambiguation + 소계 이중계상 fix)
- 2026-05-31 — V7 `NB_CSM_DART_VS_IR_ANNUAL_SUM` 룰 + convention-aware check 도구
- 2026-05-31 — NB CSM multiple validator: period-aware + fallback flagging (V2), retry max 8→5
- 2026-05-31 — QoQ threshold registry v1 (`config/qoq_thresholds.yaml`, V4 spec)
- 2026-05-31 — DART ↔ IR cross-source 3개 룰 추가 + IR-side input 계약 §1.4 (V1 spec)
- 2026-05-30 — Validation prompt 초안 (R1–R10, IFRS17 CSM 룰셋, `QOQ_DELTA_WARN`, retry loop max=5)
- 2026-05-29 — Plausibility gate (`MAX_PLAUSIBLE_MULTIPLE=60`) + Samsung Life 사망 misparse fix
- 2026-05-25 — K-ICS rules 9 + 10 추가 + RED reduction 419→2 (KR0010 OCR 잔여) + unit-hint mismatch auto-detect + Tier-2 utilization reconcile
- 2026-05-24 — K-ICS JSON validation rules doc + pipeline gate; KICS-VALIDATE harness; R7 matrix fix
- 2026-04-26 → 2026-04-28 — Foundational validation

세부 K-ICS RED 진행 + 분기별 batch 원문은 [`docs/claude-changelog.md`](claude-changelog.md) Historical archive에 압축 보존. 본 파일은 validation-relevant 분리본.
