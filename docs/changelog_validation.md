# Validation Changelog (Stage 3)

Validation 전용 이력. Cross-stage 변경은 [`docs/claude-changelog.md`](claude-changelog.md)에도 1줄 cross-reference 유지.

Stage prompt: [`docs/agents/claude-agent-validation.md`](agents/claude-agent-validation.md). 권위 룰셋: [`docs/agents/kics-json-validation-rules.md`](agents/kics-json-validation-rules.md).

---

## 2026-06-07 (b) — CSM_waterfall closing 완전 해소 (parser 재추출 후 재검증)

parser가 CSM_waterfall 측정요소 변동표 재추출 → 재검증 (`scripts/validate_master_tables.py`):

- **CLOSING_IDENTITY: 40F → 0F** (299P / 0F / 6S). 23사 × 13분기 전부 `기초+신계약+이자+가정+상각 = 기말` 정합. 🎯
- **CSM_CROSSCHECK: 20F → 9F** (61P / 9F / 224S, common 243→294로 데이터 더 채워짐).

**CSM_CROSSCHECK 잔여 9건** → tol 3단계 정책 적용으로 정리 (아래 (c)):
- 진짜 의심 2건 (wf >> pl, 재보험분 혼입 의심): KB라이프 2023.4Q −51.7% (pl 283,905 / wf 430,670), 코리안리재보험 2025.4Q −78.3% (pl 41,154 / wf 73,360) → parser 전달됨.
- tol 경계 (사실상 pass): 미래에셋 2025.4Q +0.1%(211백만, floor 초과), 삼성생명 2024.4Q +1.7% / 2025.4Q +2.1%, 케이디비 −3.3%.
- 중간 4~7%: 에이비엘 +4.3%/+6.9%, 흥국화재 +6.4%.

## 2026-06-07 (g) — CSM_PLAUSIBILITY 룰 신설 (closing identity 사각지대)

사용자가 흥국화재 2025.4Q 기말 CSM이 **34.1억**(직전 26,693억)으로 비정상 폭락한 걸 지적. closing identity는 **내부 산술 합산만** 검증 → 가정조정(−28,929.9억, 다른 분기의 7배)이 폭락을 산술적으로 흡수해 closing이 우연히 닫혀 통과(0F). **절댓값 plausibility 검증 부재가 validation 갭**.

신규 룰 `CSM_PLAUSIBILITY` (`scripts/validate_master_tables.py` 1b):
- **복붙(dup)**: 같은 회사 내 서로 다른 분기의 기말 CSM이 소수점까지 동일 → 분기 데이터 복붙 의심 (CSM 잔액은 매분기 변하므로).
- **기말 QoQ 폭변(spike)**: 기말 CSM `|ΔQoQ| > 50%`.
- **연속성(cont)**: `FY[t] 각 분기 기초 CSM = FY[t-1].4Q 기말` (작년 기말=올해 기시; YTD 연초값 고정). tol max(0.5%·|전년말|, 2억). 2023은 2022 데이터 없어 SKIP. — 사용자 지적으로 추가, 가장 근본적인 sanity.

**연속성 검출 21건** (closing 0F·crosscheck pass였어도 잡힘):
- 🔴 진짜 오류: **메트라이프 2025.4Q 기초 48,134 = 2024말 24,067 ×2 (이중계상, KB라이프형 — 연속성만 검출)**, 케이디비생명 2025.1~4Q 기초 복붙(≠2024말), 흥국화재 2025.2Q·3Q 기초 복붙.
- 🟡 회색지대 (IFRS17 기초 재작성 가능, 무조건 오류 아님): 삼성생명 2024 Δ−1,452(일관, restatement 전형)·신한라이프·메리츠·에이비엘·푸본 작은 Δ; 교보(±2,905/+5,659)·KB라이프(+1,622)는 좀 커서 parser 확인.
- severity 권고: 배수/큰 Δ = RED, 작은 Δ = YELLOW(재작성 검토).

**검출 결과 (전 회사 스캔)**: 6 dup + 4 spike, 두 회사 집중:
- **케이디비생명**: 2025.1Q=2024.1Q / 2025.2Q=2024.2Q / 2025.3Q=2024.3Q (2025 1~3Q가 2024 복붙)
- **흥국화재**: 2025.2Q=2024.2Q / 2025.3Q=2024.3Q / 2025.1Q=2026.1Q 복붙 + **2025.4Q 기말 34.1억 폭락**(가정조정 −28,930 이상치)

→ **parser 전달 대상**: 케이디비생명·흥국화재 2025 분기 CSM_waterfall 재추출 (복붙·이상치) + **메트라이프 2025.4Q 기초 2배(이중계상)**. closing identity 0F였어도 절댓값이 틀린 케이스.

## 2026-06-07 (h) — 흥국 해소 (빌드 누락이 원인) + 빌드 체인 교훈

흥국화재 "고쳤다"는데 3번 재검증해도 루트 `CSM_waterfall.json`에 변화 0 → 추적 결과 **빌드 한 단계 누락**. 체인: `csm_waterfall_master_diag.json`(소스) → `build_root_masters.py` → 루트 `CSM_waterfall.json`. parser가 **diag는 22:13에 제대로 고쳤는데**(흥국 폭락·복붙 다 사라짐) **루트는 21:31 옛것** — `build_root_masters.py`를 안 돌려 미반영. validation이 `python scripts/build_root_masters.py` 실행 → 루트 갱신 → **흥국 완전 해소** (복붙 6→0 / spike 4→1 / cont 21→14).

**⚠️ 운영 교훈 (핸드오프 필수)**: parser가 소스(diag/viz)를 고쳐도 **`build_root_masters.py` 재실행 전엔 루트 마스터(검증 대상)에 반영 안 됨**. parser fix 후 빌드까지 확인할 것. mtime 비교(소스 > 루트)로 빌드 누락 탐지 가능.

**빌드가 드러낸 새 건**: 롯데손해 2025.4Q wf CSM상각 −980(거의 0, 이상치 — 빌드 로그 `1 unit-error c-q nulled`) → crosscheck +99.5% RED. 롯데 FY25 양식 이슈(V7)와 연관 의심 → parser. (케이디비 2025.4Q +12.8%는 기존.)

## 2026-06-07 (f) — DB손해·KB손해 별도/연결 fix → PL_BRIDGE 31F→16F

parser가 별도/연결 LOB 레그 fix를 DB손해·KB손해로 확장 → **2024+ 보험손익 fail 10건 완전 해소** (DB손해 5 + KB손해 5). 진단(DB=ΣLOB 결손 +7k~+47k / KB=ΣLOB 과대 −9k~−59k, LOB 내부는 정합)이 정확히 별도/연결 레그 오선택이었음.

**PL_BRIDGE 31F → 16F**. 잔여:
- **2023 분기 11건** — 사이트 비노출 → 넘어감 (DB생명 2·DB손해 3·메리츠 3·한화생명·한화손해·흥국화재).
- **2024+ 5건** — KB라이프 2024.1Q +1,136 / 악사손해 2024.4Q +3,483 / **흥국화재 2025.1Q −714·2025.4Q +1,684·2026.1Q +968** (소액이나 흥국화재 2026.1Q는 보험손익 대비 −4.9%로 비율은 작지 않음).

전체: closing 0F + crosscheck 0F(+2M) + pl_bridge 16F(2023 11 + 2024+ 5).

**dual-form의 정당성 (사용자 확인 2026-06-07)**: 보험손익은 통상 `종목별 보험손익 합 − 기타사업비`(adj)지만, **일부 회사·분기(흥국 2024.4Q, KB 등)는 종목별 합산에 기타사업비가 이미 녹아있어** bare(`= ΣLOB`)로 닫힘. dual-form은 **바로 이 케이스를 통과시키려는 의도된 설계**. → bare로만 통과하는 분기는 **정상이며 flag하지 않는다**. (앞서 흥국 2024.4Q를 "숨은 275억 LOB 결손/dual-form 허점"으로 본 진단은 오버 — 철회. "회사별 form 고정 flag" 제안도 철회.)
- **진단자(validation) 오진 경향 명시**: 한화손보→삼성화재는 보험손익 잔차를 "기타영업수익/기타사업비용"으로 오진했다가 실제 LOB 별도/연결이었음 — 이 교훈은 유효(§1.5). 단 흥국 2024.4Q처럼 bare로 닫히는 건 진짜 정상이니 과잉 진단 금지.

## 2026-06-07 (e) — 보험손익 잔차 = LOB 별도/연결 레그 오선택 (진단 가이드 정정)

삼성화재 2026.1Q +2,067, 한화손보 2025.2~4Q를 "기타영업수익 누락"으로 진단했으나 **2건 연속 오진**. parser FS-API 검증 결과 진짜 원인 = **ΣLOB 별도/연결 레그 오선택**:
- 별도(OFS) 기준 회사는 FS-API상 **기타영업수익 구조적 0** (`보험영업수익 = 보험수익 + 재보험수익`).
- parser component 노트 `pmin`(최소합계=별도) 휴리스틱이 **재보험 레그에서 뒤집힘**(연결이 그룹내부 재보험 상계 → 별도 재보험 > 연결) → 보험수익은 별도, 재보험회수는 연결로 기준 불일치 → ΣLOB 결손. 삼성화재 2026.1Q 일반손익 109,190 → 111,256(+2,066)로 닫힘.
- 분기마다 별도/연결 대소가 달라 같은 회사도 일부 분기만 fail (2025.4Q는 우연히 맞아 닫혔던 것).

parser fix(별도 보험수익 anchor + cost/재보험 레그 same-block `first_from`) → **삼성화재 2026.1Q + 한화손보 2025 둘 다 해소**. pl_bridge **36F → 31F**.

**진단 가이드 §1.5에 박음**: 보험손익 잔차는 "기타영업수익 누락"이 아니라 **LOB 별도/연결 기준 일관성부터 의심**.

**잔여 2024+ 보험손익 fail = 같은 패턴 강력 의심 → parser**: DB손해 5건(−25k~+39k 부호 섞임) + KB손해 5건(+9.5k~+59.6k). 분기별 부호 혼재가 별도/연결 휴리스틱 들쭉날쭉의 전형. + 소액(흥국화재 3·악사·KB라이프).

## 2026-06-07 (d) — CSM_CROSSCHECK 진짜 2건 해소 → 0F

진짜 의심 2건이 서로 다른 원인이었음 ("재보험 혼입" 가설은 둘 다 빗나감):

- **KB라이프 2023.4Q — wf 버그 (parser fix)**: 사업결합(KB생명+푸르덴셜) 으로 기초가 2줄(사업결합 전 2,373,817 / 복원 3,132,762). 전기 블록의 기말(2,373,818)이 사업결합 전 기초와 같아 값연속성 검사를 통과 → wf가 당기 블록(상각 −283,905=pl 일치)에 전기 블록(−146,769)을 합산해 **정확히 2배**(−430,674). closing identity는 전 stage 비례 2배라 **우연히 통과**, crosscheck(vs PL)만 잡아냄. parser가 period 구분을 caption이 아닌 header(`['구분','전기']`)에서 인식하도록 `_is_prior_header()` 추가 → KB라이프 13분기 closing OK, 상각 −2,839.1억(=pl 283,905 ✓).
- **코리안리 2025.4Q — validation 룰 스코프 버그 (validation fix)**: 파서 정확. 재보험사 PL은 발행계약을 `원수CSM상각(4) + 수재CSM상각(4-1)`로 분리(41,154 + 32,210 = 73,364 = wf 상각 일치). wf "발행한 보험계약" = 원수(direct)+수재(assumed)라 둘을 합쳐 잡는 게 맞는데, crosscheck 룰이 PL 쪽 수재(4-1)를 빼먹어 false-positive. → `scripts/validate_master_tables.py` crosscheck를 `p = 원수CSM상각 + (수재CSM상각 or 0)`로 수정 (출재 9-1은 보유자산이라 제외). §1.2 반영.

**결과**: CSM_CROSSCHECK **66P/2M/2F → 68P/2M/0F**. CSM_waterfall 도메인(closing 0F + crosscheck 0F) 완전 정합. 잔여 MINOR 2건(에이비엘 6.9%·흥국화재 6.4%)은 경고만.

## 2026-06-07 (c) — CSM_CROSSCHECK tol 3단계 정책

`CSM_CROSSCHECK`는 **서로 다른 DART 표**(PL 보험수익 구성 vs CSM 변동표) cross 비교라 표간 반올림·집계 차이로 수% 편차가 구조적. 단일표 검증(0.1%)보다 느슨한 **3단계 tol** 도입 ([§1.2](agents/claude-agent-validation.md)):
- **OK**: `|s| ≤ max(5%·|pl|, 300백만)`
- **MINOR** (경고, pass): `5% < |s| ≤ 10%`
- **RED**: `|s| > 10%` → parser loopback

결과: crosscheck **9F → 66P / 2M / 2F**. 진짜 불일치(KB라이프 51.7%·코리안리 78.3%)만 RED, 경계 7건은 OK 5(미래에셋·삼성생명·케이디비·에이비엘 4.3%) + MINOR 2(에이비엘 6.9%·흥국화재 6.4%)로 흡수. 진짜 2건과 경계(최대 6.9%) 사이 갭이 51%+로 매우 커서 10% 임계가 안전.

**PL_BRIDGE: 36F 변동 없음** (이번 parser 작업은 CSM_waterfall 한정). 잔여 = FY2023 상반기 HTML fallback + 한화손해 2025 보험손익 dual 미닫힘.

## 2026-06-07 — V8 마스터테이블 검증 소비자 코드 첫 실행 + 룰 정식화

사용자가 (거의) 전사·전분기 마스터테이블 구축 완료 → V8 소비자 코드 `scripts/validate_master_tables.py` 작성·실행. 입력: `data/dart/viz/pl_breakdown_master.json` (백만원, 32사×13분기) + `CSM_waterfall.json` (억원, 23사×13분기).

**3개 룰 실행 결과** (parser 1차 수정 + validation 룰 조정 후):
- CLOSING_IDENTITY: 218P / 40F / 41S (가정조정 독립추출이라 잔차 검증됨)
- PL_BRIDGE (8단 등식): 2023P / 36F / 469S
- CSM_CROSSCHECK: 33P / 20F / 190S

**룰 정식화 (오탐 제거)**:
- **보험손익 dual-form**: 회사마다 `보험손익 = ΣLOB`(손보 DB/현대/흥국/메리츠 — 기타영업수익·기타사업비용은 보험손익 라인 밖) 또는 `ΣLOB + 기타영업수익 − 기타사업비용`(삼성화재 등). 둘 중 하나 닫히면 PASS → 손보 bare-close 오탐 ~19건 해소.
- **영업이익 abs floor 200→600백만**: 영업이익 0근처 회사(KDB 등) 과민 방지. KDB 4건 해소.
- **CSM_CROSSCHECK 4Q-only**: pl 원수CSM상각·wf CSM상각 모두 YTD 누적 → 1~3Q는 분기배분 차이로 노이즈. 연말(4Q=연간 누계)에서만 비교. 136F→20F.

**parser 1차 수정 반영**: item16(기타사업비용) 음수 7건 abs 정규화(한화손해/농협생명/삼성생명), item19(보험금융손익) account_nm fallback로 277셀 포착(KB라이프 등 표준코드 미사용 회사), item17(투자손익) net 통일(gross-type 자동감지) → pl_bridge 영업이익 fail 일부 해소.

**남은 fail**:
- **CSM_waterfall 도메인 60건 (진짜 일)**: closing 40F (step 누락/오추출) + crosscheck 20F (두 마스터가 원수CSM상각 다르게 추출). parser 재추출 — `parser_handoff_master_validation.md` 그룹 C/D + `data/_derived/master_validation_fails.json`.
- **PL 잔여 36F (대부분 known)**: FY2023 상반기 HTML fallback (Tier-1 채우기 에이전트 대기) + 소수 진짜(한화손해 2025 보험손익 dual 미닫힘).

회귀 명령: `python scripts/validate_master_tables.py`.

## 2026-06-01 (밤 c) — 통합 마스터테이블 입력 계약 + CSM_CROSSCHECK 확장

사용자가 회사별 수기 모델을 **long-format JSON 마스터테이블 3종**으로 정형화 중: `PL_breakdown` (P&L 17항목) / `CSM_waterfall` (6-step) / `CSM_amortization` (경과연차별 상각 스케줄, 별도). §1.5.1에 입력 계약 codify (공통 스키마 `{원보험사코드, 원수사명, 티커, 생손보여부, 항목번호, 항목명, 공시분기, 값}`, 백만원).

- **`CSM_AMORT_WATERFALL_VS_PL` → `CSM_CROSSCHECK_WATERFALL_VS_PL` 확장** ([§1.2](agents/claude-agent-validation.md)): `(원보험사코드, 공시분기)` 매칭 + **항목명 공백 정규화**(`"CSM상각"`=`"CSM 상각"`) 후 — (1) **CSM상각**: PL(양수) + waterfall(음수) ≈ 0 (부호반대 동규모), (2) **신계약 CSM**: 두 마스터 동값 일치. 한쪽 부재 시 항목별 graceful SKIP. tol `max(0.1%·|expected|, 200mn)`.
- **데이터 확인** (마스터 항목 추출): 신계약 CSM은 `CSM_waterfall`에만 존재, `PL_breakdown`엔 **구조상 없음**(미래서비스 → 당기손익 무관). → 신계약 CSM cross 짝 없음 → 현재 SKIP, V7 `NB_CSM_DART_VS_IR`(IR 비교) + waterfall closing identity가 신계약 CSM 검증 담당. CSM상각만 양쪽 존재 → 즉시 cross-check 가능.
- **현재 상태**: `PL_breakdown` 삼성화재 2025.4Q만 값, `CSM_waterfall`/`CSM_amortization`은 분기 템플릿(값 None) → 채워지면 자동 활성. 회사별 파일: CSM waterfall {KB/메리츠/삼성/삼성생명/한화생명/한화손보}, 보험손익 breakdown {삼성화재/메리츠/삼성생명/한화생명}.

## 2026-06-01 (밤 b) — 메리츠 CSM waterfall: breakdown 영구 SKIP + CSM_AMORT cross-table 신설

사용자가 `CSM waterfall_메리츠.xlsx` 공유. 메리츠 CSM waterfall 출처 = DART **"(4) 측정요소별 변동내역"** 표 (배당있는 행9–39 + 배당없는 행46–76 두 블록 합). step별: 기초/신계약/이자/상각/기말은 직접 추출, **가정·경험조정은 잔차**(closing identity로 닫음). CSM = **D/E/F 3칼럼**(수정소급/공정가치/그 외 = 전환방법), B(미래CF현가)/C(RA) 제외 — V7 `csm_leaf_cols=[2,3,4]`와 동일.

- **보종 breakdown 불가 확정**: D/E/F는 **전환방법별**이지 보종(보장성/물보험/저축성)이 아님. 신계약 CSM 1,588,172는 전부 F칼럼(그 외)에 있고 D=E=0. 메리츠 측정요소별 표엔 보종 축 자체가 없음 → `CSM_BREAKDOWN_DART_VS_IR` 메리츠 보종 비교 **영구 SKIP** (total만).
- **`CSM_AMORT_WATERFALL_VS_PL` 신설** ([§1.2](agents/claude-agent-validation.md)): DART 자기완결 cross-table. waterfall CSM상각(음수) + P&L 보험수익 CSM상각(양수) ≈ 0 (동규모·부호반대, 발행계약 기준, 재보험 제외). tol `max(0.1%·|amort|, 200mn)`, RED → parser loopback. 선행: waterfall + P&L(보험손익 주석) 둘 다 추출.
- closing identity 확인: `11,187,889(기초) + 1,588,172(신계약) + 361,544(이자) − 866,645(가정) − 1,167,264(상각) = 11,103,696(기말)` ✓.

## 2026-06-01 (밤) — SEGMENT cross-source 폐기 + PL_BRIDGE_DART_INTERNAL 신설

사용자가 삼성화재 2025.4Q `보험손익 breakdown.xlsx` 수기 모델 공유 → **부문별 보험손익 DART↔IR 비교는 원천 불가** 확정. 근거: IR 부문 손익 = `DART 부문 서비스손익` + `기타영업수익/기타사업비용을 IR 고유 키로 부문 배분`. DART는 기타항목을 **전사 단일값**으로만 공시 → 배분 역산 불가.

- **`SEGMENT_INSURANCE_INCOME_DART_VS_IR` 폐기** ([§1.2](agents/claude-agent-validation.md)). §1.4 `segment_insurance_income` 입력 DEPRECATED.
- **`PL_BRIDGE_DART_INTERNAL` 신설** ([§1.5](agents/claude-agent-validation.md)) — DART 자기완결 정합성 (cross-source 아님, IR 불필요). 부문 IFRS17 주석 → 연결 포괄손익계산서 당기순이익까지 10개 등식(B1–B10). 엑셀 검증 셀 5개를 그대로 codify. tol `max(0.1%·|expected|, 200mn)`, RED → parser loopback (B1–B4 부문추출=`DART`, B5–B10 P&L매핑=`internal`).
- 삼성화재 2025.4Q 검증례: 보험손익 `1,672,913(부문합)+16,728−206,607=1,483,034` ✓ → 영업이익 → 세전 → 당기순이익 2,020,287 ✓ 전부 PASS.
- **선행조건**: parser가 부문별 보험손익 주석 + 연결 포괄손익계산서를 정형 추출해야 활성화 (현재 미추출 → SKIP). 행 순서 회사별 상이 → 항목명 기반 매핑 필수.

## 2026-06-01 (저녁) — 🚨 history 재빌드 off-by-one-year 회귀 발견 + check 도구 cohort 가드

**parser가 19:33에 `csm_waterfall_history.json` 재빌드 (P2 진행)** → 검증 결과 분기↔연도 정렬이 1년 어긋남. 삼성화재 IR singleQ(ground truth)로 완벽 증명:

| period | IR singleQ (정답) | 재빌드 hist delta | hist[+1년 시프트] |
|---|---|---|---|
| 2023.1Q | 6782.7 | 5005.1 ❌ | **6782.7** ✓ |
| 2024.1Q | 8855.5 | 6782.7 ❌ | **8855.5** ✓ |
| 2024.3Q | 8385.2 | 11641.9 ❌ | 7669.2 |

즉 재빌드 history에서 "2024.1Q"로 라벨된 값이 실제로는 2023.1Q 데이터. 재빌드 전 baseline(삼성화재 9/12 OK)은 정렬이 맞았으므로 **재빌드가 회귀를 도입**. → parser P2 재빌드 로직에 off-by-one-year 버그, 수정 후 재빌드 필요. (systemic 이슈 3건 재확인은 회귀 수정 후로 보류 — 현재 데이터로는 의미 없음.)

**check 도구 cohort 가드** (`scripts/check_nb_csm_history.py`): IR 측 유효 NB CSM 값이 0인 회사를 cohort에서 제외 + skip 사유 로깅. 제외 2사:
- 코리안리 — IR series 빈 스텁 (series 0개)
- 한화손해 — 특수 스키마 (`nb_csm_eok_ir`/`nb_csm_eok_dart`, multiple-flag 용도, `nb_csm_eok` 부재)

**부수 검증**: 한화손해 KR0002 파일에 기록된 IR 7,410 vs DART 14,819.8 (2024.4Q) — 정확히 2배. parser 소계 이중계상 ÷2 fix 후 DART=7,409.9 ≈ IR 7,410 → **한화손해도 ÷2 fix 정확히 먹혔다는 독립 검증**. (단 한화손해 2025.1Q DART는 2024.1Q stale carryover — parser staleness 별도 버그, 한화손해 IR note에 기록됨.)

## 2026-06-01 — V7 history-wide check 도구 + systemic 이슈 3건 발견 (baseline)

기존 `scripts/check_nb_csm_widespread.py`는 FY2024 단일 스냅샷(`csm_waterfall.json`) 기준이라 사용자 의도("전 분기 × 전 회사")와 맞지 않음 — parser 세션이 지적. 신규 도구 `scripts/check_nb_csm_history.py` 도입.

- **입력**: `csm_waterfall_history.json` (13Q × 23사) + `data/ir/series/*.json`
- **DART 변환**: 분기별 NB 값이 YTD cumulative라 가정 (sample 3사 확인) → per-Q delta로 변환 (`NB[Y.nQ] − NB[Y.(n-1)Q]`, Q1은 raw)
- **IR 변환**: convention-aware 일반화 — singleQ field 완비 시 그대로, YTD marker(`YTD/누계/cumulative`) 시 동일 변환, 그 외 raw per-Q
- **Tolerance**: rel ≤ 5% **또는** abs ≤ 100억 → OK; rel ≤ 10% → MINOR; else OVER/UNDER
- **Output**: 분기 × 회사 ratio matrix + per-quarter cohort summary + per-company flag count → `data/_derived/nb_csm_history_check.json`

**Baseline 결과 (parser fix 미반영 상태, 9사 cohort × 13Q)**:

Per-company sanity rank — 삼성화재(9 OK / 1 MINOR, IR singleQ anchor) · 삼성생명(9 OK / 1 OVER) · DB손해(9 OK / 1 OVER / 2 UNDER, 단 폭주값) · 한화생명(7 OK / 4 OVER / 2 UNDER) · 메리츠(4 OK + 2 MINOR / 5 OVER / 1 UNDER) · 미래에셋(4 OK / 2 OVER / 2 UNDER) · 롯데(0 OK / 5 OVER, 8 MISSING).

**Systemic 이슈 3건** (parser 두 fix와 직교):

1. **2025.2Q cohort-wide 이상치 분기** — 9사 중 OK 1 / OVER 3 / UNDER 2. 삼성화재 +30% · 삼성생명 +29% · 한화생명 +104% 동시 발생 → 그 분기 history 빌더가 블록 선택 룰을 다르게 적용한 패턴.
2. **DB손해 2025.2-4Q 부호 반전 + 폭주** — −23,589억 / −7,976억 / +55,162억. 분기 간 블록 비일관 (전기/당기/연결/별도 + 누적/당기 mix). closing→opening continuity 깨졌을 가능성.
3. **미래에셋 2024.3Q-2025.2Q ↑↓ 교대** — +19% / −16% / +16% / −22%. 두 다른 블록 alternating, continuity tiebreak가 분기마다 다른 블록 선택.

**별도 발견 (별개 작업)**: 한화손해(KR0002) / 코리안리 IR series ↔ history 회사명 매칭 누락 (load 시 `kr=None`) — alias mapping 점검 필요 (parser 또는 publishing owner).

**Parser fix(P2) 이후 회귀 명령**: `python scripts/check_nb_csm_history.py` → per-quarter cohort summary에서 OVER/UNDER 0 수렴 확인 + per-company OK 비율 향상.

## 2026-06-01 — V7 6/7 OK 회복 (parser 별도·당기 disambiguation + 소계 이중계상 fix)

Parser 세션이 `viz_build_csm_waterfall.py`에 두 가지 fix 반영:

1. **별도·당기 block disambiguation** — 생보 측정요소별 4표(연결/별도 × 당기/전기) 동일 캡션. 기존 picker가 마지막 tiebreak에서 NB 절대값 큰 쪽(전기·연결, 기초 13.59조)을 골랐던 것 → 전기 copy 제거 + 기초 작은 쪽(별도) 우선. 한화·메리츠·에이비엘·케이비라이프·DB생명·교보 6사 교정.
2. **소계 칼럼 이중계상 fix** — `find_csm_leaf_cols`가 `[수정소급, 공정가치, 이외, 소계]` 헤더에서 소계까지 leaf에 포함해 ×2 inflate. 소계 칼럼 drop → `[2,3,4]`. 롯데·한화손보·교보·NH 등 7사 일괄 ÷2.

**검증 결과** (`python scripts/check_nb_csm_widespread.py`): **ok=6/7**, 잔여 1건 롯데(+23%):

| Company | Before | After | Δ |
|---|---|---|---|
| 한화생명 | ×1.524 (32,346억) | **×1.000 (21,230.9억)** | IR 21,230.8억과 0.0억 차이 |
| 메리츠화재 | ×1.160 (16,006억) | **×1.000 (13,795.7억)** | IR 13,795.7억과 0.0억 차이 |
| 롯데손해 | ×2.466 (9,705억) | ×1.233 (4,852.5억) | 이중계상은 풀림; FY24 측정요소별 양식 자체 +23% gap |

**롯데 잔여 1건 — FY25 추출 의존**: 롯데는 FY25부터 공시 양식을 "구성요소별 차이조정"으로 바꿈. 사용자 확인 raw 위치: `data/dart/FY2025_Q4/raw/KR0003_롯데손해보험_20260319001293/_00760.xml:27375` "보험계약 구성요소별 변동분에 대한 차이조정 / 배당요소가 없는 보험계약, 소계 / 미래서비스 관련 변동 / 최초인식계약" = **412,168 (= IR FY25 일치)**. 현재 measurement extractor는 측정요소별만 잡음 → FY2025 추출 시 구성요소별 차이조정 표 capture + 롯데 NB override가 parser 측 다음 작업.

**Downstream 재빌드 대기** (publishing/parser owner): `csm_bubble.json`, `nb_csm_multiple.json`, 13Q `csm_waterfall_history.json` 셋 다 한화 별도 shift + 7사 ÷2 영향 — history builder continuity tiebreak 13Q×23사 별도 검증 필요.

**V2 부수 효과**: `validate_nb_csm_multiple.py` 한화 분자가 32,346억 → 21,230억으로 정정됐으므로 `fallback_used=true` 플래그 retire 가능 (이제 aligned-period FY24 annual benchmark 21,230.85억과 직접 매치). 별도 작업으로 진행.

## 2026-05-31 — V7 NB CSM cross-source 룰 + convention-aware check 도구

신규 룰 `NB_CSM_DART_VS_IR_ANNUAL_SUM` ([§1.2](agents/claude-agent-validation.md)): DART `csm_waterfall.json` `new_business` vs IR series FY total. Cohort 7사 (메리츠/롯데/삼성화재/DB/한화생명/삼성생명/미래에셋), severity RED, tol `max(5%·|IR|, 100억)`, DART parser loopback.

신규 도구 `scripts/check_nb_csm_widespread.py`. IR FY derivation은 **convention-aware**: (1) 모든 분기에 `nb_csm_singleQ_eok` 있으면 sum singleQ, (2) metric에 `YTD`/`누계`/`cumulative` marker 있으면 Q4 값(YTD 누적), (3) 그 외 sum quarters (per-Q delta 가정). 초기 단순 sum convention이 cumulative series(삼성화재 singleQ field 별도 / DB metric "누계")를 ~3x 부풀려 fake UNDER를 만들던 도구 버그 patch — parser 세션 피드백으로 발견.

**검증 결과**: 4/7 OK (삼성화재 / DB / 삼성생명 / 미래에셋) + 3/7 OVER (한화 +52% / 메리츠 +16% / 롯데 +147%) — parser layout 인식 결함 (`csm_leaf_cols=[2]` BEL 오인 / `[2,3,4]` BEL+RA+CSM 합산). Parser 세션이 3사 한정 fix 진행 중.

사용자 결정: 정식 게이트 룰로 박음, gate enforcement는 publishing stage 측 (publisher에 사용자가 직접 전달). Cohort 확장 없음 (21사 IR factsheet 부재).

## 2026-05-31 — NB CSM multiple validator: period-aware + fallback flagging (V2)

`scripts/validate_nb_csm_multiple.py` 정합성 정정. 기존 "한화 period mismatch" 진단 철회 — 실제로는 parser 분자(V7) + denominator scope + IR benchmark 시점, 3개 버그 stacked. Validation 측 2개 fix:

- `PREFERRED_SCOPE["한화생명"]` → `monthly_avg_from_ytd` 우선 (FY2024 KIDI row 매칭) + `pick_premium_records`에 `prefer_period` 파라미터 (scope 우선순위 유지하면서 같은 scope 내에서 period 매칭 row 먼저 시도). `waterfall_period_to_premium_period()` helper로 csm_waterfall global period → wolnap period 매핑.
- `nb_csm_ratio.json` hanwha_life에 `single_point.2024_total=7.609` (IR series 분기 weighted avg — ΣNB_CSM 21,230.85억 / Σwolnap_implied 2,790.06억). `latest_ir_ratio()`가 4번째 우선순위로 자동 채택.
- `period_aligned` / `fallback_used` / `cohort_fallback_pass` 정직성 플래그 — aligned-period 실패 후 tolerance 우연 통과 case 표면화.
- `run_ifrs17_csm_reconcile_loop.py` `--max-iter` 8→5 (prompt §3 동기화).

**결과** (`data/_derived/nb_csm_validation.json`): tested 5 / pass 5 / fallback_pass 3 — ALIGNED: DB(rel 5.6%) / 삼성생명(3.9%); FALLBACK: 한화 / 삼성화재 / 현대. Parser V7 fix + 삼성화재·현대 IR annual benchmark 보강 시 fallback 점진 해소.

## 2026-05-31 — QoQ threshold registry v1 (V4 spec)

`config/qoq_thresholds.yaml` v1 spec 생성. global default 15% + item-level override (`new_business_csm` 30% / `csm_amortization` 10% / `insurance_revenue` 20% / `csm_closing` 10% / `csm_interest_accretion` 20% / KICS `item27/28_ratio` 10%) + `cumulative_items` registry (mirrors §2.3). Lookup precedence: item → domain → global. Cumulative 항목은 net 분기 increment 자동 전환.

**소비자 코드 미구현** — yaml은 canonical spec, validator loader/diff calculator 부재. wiring → TODO_validation V4 sub.

## 2026-05-31 — DART ↔ IR cross-source 3개 룰 추가 (V1 spec)

[`docs/agents/claude-agent-validation.md`](agents/claude-agent-validation.md) §1.2에 IFRS17 cross-source 룰 3개 — 전부 RED → DART parser loopback:

- `CSM_WATERFALL_DART_VS_IR` — step별 (opening / new_business / interest / assumption / amortization / closing), tol `max(5%·|IR|, 100억)` per step
- `SEGMENT_INSURANCE_INCOME_DART_VS_IR` — 손보 장기/자동차/일반, tol `max(10%·|IR|, 50억)` per segment; 생보 SKIP (스키마 확정 전)
- `CSM_BREAKDOWN_DART_VS_IR` — 손보 보장성/물보험/저축성 or total, tol `max(5%·|IR|, 100억)` per item

§1.4 신설: IR-side input 계약 `data/ir/<period>/parsed/<KR>.json` (모든 값 억원, 누락 시 graceful SKIP). RED packaging에 `suspected_source: "DART" | "IR" | "internal"` 필드. IR 정형 JSON delivery 대기 중 (root F18) — 도착 시 자동 ON. 알려진 IR 미공시 회사(교보·KDB·외국계·카카오페이손해 등) 자동 SKIP.

RED packaging에 `suspected_source: "DART" | "IR" | "internal"` 필드 추가 — cross-source 룰은 항상 `"DART"` 의심.

**Cross-stage 의존**: parser/gathering 단계가 분기별 IR factsheet에서 위 schema를 추출해야 룰 활성화. 현재 `data/ir/series/<KR>.json`은 NB CSM multiple 전용. **Parser stage TODO 발생** — root [`TODO.md`](../TODO.md) `F18` 참조.

---

## 2026-05-30 — Validation prompt 초안 작성

[`docs/agents/claude-agent-validation.md`](agents/claude-agent-validation.md) 신설. 작업 계약(input/output/exit code), 도메인별 룰, retry loop, exception 처리, 게이트 동작, 호출 예시 codify.

- **K-ICS** R1–R10 codify (기존 [kics-json-validation-rules.md](agents/kics-json-validation-rules.md) + [kics_json_rules.py](../src/solvency/validation/kics_json_rules.py))
- **IFRS17 CSM 룰셋**: `CSM_WATERFALL_NEW_BUSINESS` / `CSM_WATERFALL_CLOSING_IDENTITY` (tol `max(500mn, 0.5%·|closing|)`) / `MINIMUM_STAGE_COVERAGE` / `NB_CSM_MULTIPLE_RECONCILIATION` (YELLOW, loopback 없음)
- **Misc IR / 정기경영공시**: K-ICS R1–R10 재사용 + quality_check score < 0.7 → YELLOW
- **공통 `QOQ_DELTA_WARN`**: threshold 15% 기본, 누적 항목(`new_business_csm`, `csm_amortization`, `insurance_revenue`)은 net 분기 기준 비교. floor below 1억원 → SKIP (rounding noise). 항상 YELLOW (loop 안 돔)
- **Retry loop max=5** (IFRS17 reconcile 8→5 코드 갱신 별도 PR로 발행 예정). 5회 초과 시 escalate_to_human → root TODO에 1줄 기록
- **게이트**: K-ICS RED → 전 다운스트림 차단; IFRS17 RED → templates/data/assoc/ sync만 차단 (HTML deploy 자체는 panel-level stub 허용); Misc는 K-ICS와 동일

---

## 2026-05-29 — Plausibility gate + Samsung Life 사망 misparse fix

User flagged 삼성생명 종신/사망 NB CSM multiple >400x (impossible; realistic max ~30-50x).

**400x = regex misparse [fixed].** `viz_build_nb_csm_ratio.extract_samsung_life`가 death row를 positional 5-number regex로 읽어 IR PDF의 사망 배수(single digits)와 절대 CSM 금액(십억원: 459/435/520/471/488)을 혼동. **Fix**: 건강 row와 마지막 사망 라벨 사이를 스캔, `\d+\.\d+` cap 이하만 채택. 결과: [7.6, 10.0, 7.6, 7.2, 5.1].

**Plausibility gate [신규 validation rule].** `MAX_PLAUSIBLE_MULTIPLE = 60.0` + `validate_plausible(payload)`를 `build_payload`에서 호출. chart series 중 `<=0` 또는 `> 60`이면 build fail (절대금액을 ratio로 오독). Negative test: 520x catch, 7.6x pass. Browser-verified: Panel 4 death line ~5–10x, y-axis 0–18x, 콘솔 에러 0. `validate_nb_csm_multiple` (computed vs IR) 5/6 pass (한화 period-mismatch 잔존).

---

## 2026-05-25 — Validation rules 9 + 10 추가

K-ICS transitional consistency 룰 신설:
- **R9**: `item2_post ≥ item2_pre - tol` (grandfather)
- **R10**: `item14_pre ≥ item14_post - tol` (SCR phase-in)

Tolerance: 2.0 (R1/R2 동일).

---

## 2026-05-25 — Unit-hint mismatch auto-detect

23 insurer-quarter latent bugs (3× ×100, 20× ÷100), 56 post values corrected. Rule 8_post pre/post bug fixed → RED=2 (KR0010 OCR only).

---

## 2026-05-25 — K-ICS RED reduction (cumulative session)

KICS-VALIDATE harness re-runs: **RED 99 → 77 → 48 → 10 → 2** (KR0010 OCR 1건만 잔여).

- **Rule 2** (KR1098/KR0051/KR1010/KR0095): KakaoPay/MetLife reversed capital labels, item4 reconcile, item10 baseline; `_canonicalize_table_label`, MetLife alias, `labels_compatible` guard
- **8_life item35** parser fix (KR0009/KR0095/KR1098/KR0051/KR0049): multi-line unit hint, life-only 총계, default 백만원 for life catastrophe tables
- **Shinhan Life (KR0094) 2024.4Q rule 6 fix**: drop bare `분산효과` alias; only top-level item16 labels
- **Rule 5 missing item22** (KR1010/KR1098/KR0051): recalc infers item22=0; OCR-spaced label match; rule5 RED 19→0
- **Samsung Life (KR0069)** 2023.1Q/3Q parse: bullet section start patterns; 0 RED all 12 quarters
- **DB손해 (KR0011) 8_life**: keep first 위험액 block (sub-item overwrite fix); 8_life RED 4 (was 33)
- **Rule 3 always SKIP** (item1 authority is rule 1); 384 buckets

---

## 2026-05-25 — Tier-2 utilization reconcile

Tier-2 utilization numerator fix (KIRI PDF reconcile, no double-subtract): in-range 9 → 34, outliers 29 → 4. Outlier report `output/tier2_utilization/outlier_report_20254Q.md`.

**8_life dynamic tolerance** 적용 (RED 177→99). Cat (a)+(b)+(d) `max(2.0, 5%·|expected|)`.

---

## 2026-05-24 — KICS-VALIDATE harness initial + RED reduction pass

Session handoff Cursor → Claude. K-ICS validation 본격 시작.

- K-ICS RED per-rule samples @177
- KR0097 Hana Life parse fix (RED 18→2)
- K-ICS missing-data reparse + item27/28 recalc fix (RED 311→217)
- K-ICS validation RED fix pass 2 (user ground truth, RED 419→311)
- KICS-REPARSE-Q4 FY2025_Q4 refresh: parse 30/38 ok, fill_period upd=30
- K-ICS JSON validation rules doc [`docs/agents/kics-json-validation-rules.md`](agents/kics-json-validation-rules.md) + pipeline gate
- K-ICS validation re-run (R7 matrix fix)
- KICS-VALIDATE JSON rules harness (rules 1–8) initial
- K-ICS full reparse, validate, JSON swap (all periods)
- K-ICS parser: split-table continuation + row scope (KR0005 FY2025_Q4 golden test)

---

## 2026-04-26 → 2026-04-28 — Foundational validation

- PDF 검증 / ACL 정상화 모듈 (2026-04-26)
- 과거 분기 PDF 배치 검증 + 누락 비율(27/28) 자동 산출 (2026-04-28)

---

## 참조

세부 K-ICS RED 진행 + 분기별 batch 작업의 원문은 [`docs/claude-changelog.md`](claude-changelog.md) Historical archive 2026-05-24/25 / 2026-04-26~28 섹션에 압축 보존. 본 파일은 validation-relevant 분리본.
