# Insurequant Validation TODO (Stage 3)

Last updated: 2026-06-01.

Stage 3 — **validation**: 파싱된 숫자의 정합성 + QoQ anomaly + 도메인 간 교차검증.

**Stage files**
- Prompt: [`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md)
- Changelog: [`docs/changelog_validation.md`](docs/changelog_validation.md)
- This file: open validation work

Session start: read this file + claude-agent-validation.md + 관련 도메인 ref(`docs/domains/claude-agent-{kics,ifrs17}.md`).

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## 🚧 Open validation work

### V1 — DART↔IR cross-source 2개 룰 활성화 (2026-06-01: segment 폐기로 3→2)

룰은 [`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md) §1.2 + §1.4. RED → DART parser loopback. **현재 IR-side 정형 JSON 부재로 전사 SKIP 상태.** (segment 룰은 폐기 → V8로 대체)

- [ ] **IR parser delivery 대기**: `data/ir/<period>/parsed/<KR>.json` (root TODO F18). 도착 cohort 9사: 메리츠·삼성화재·현대·KB·DB·한화생명·삼성생명·미래에셋·동양. 도착 즉시 룰 자동 ON.
- **IR factsheet NB CSM multiple 가용성** (V2 cohort 영향):
  - 부재 (multiple 룰 제외): 현대해상 · KB손해
  - 부재이나 간접 산출 가능: DB손해 (IR factsheet 신계약 CSM + 월납보험료 → multiple derive)
- [ ] **Threshold v1 튜닝**: 활성화 후 실제 diff 분포 보고 조정. 현재 v1:
  - `CSM_WATERFALL_DART_VS_IR` — max(5%·|IR|, 100억) per step
  - `CSM_BREAKDOWN_DART_VS_IR` — max(5%·|IR|, 100억) per item. **메리츠는 보종 비교 영구 SKIP** (측정요소별 표만 공시, 보종 축 부재) → total만.

### V8 — DART 자기완결 정합성 룰 (PL_BRIDGE + CSM_CROSSCHECK, 소비자코드 구현 완료 2026-06-07; CSM_waterfall 도메인 잔여)

cross-source 억지 매칭 대신 **DART 단일 소스 내부 정합성**으로 검증. IR factsheet 불필요.

**(a) `PL_BRIDGE_DART_INTERNAL`** ([§1.5](docs/agents/claude-agent-validation.md)) — 부문별 IFRS17 보험손익 주석 → 연결 포괄손익계산서 당기순이익까지 10개 등식(B1–B10). 삼성화재 2025.4Q `보험손익 breakdown.xlsx`에서 도출, 검증 전부 PASS.

**(b) `CSM_CROSSCHECK_WATERFALL_VS_PL`** ([§1.2](docs/agents/claude-agent-validation.md)) — 두 마스터(`PL_breakdown` ↔ `CSM_waterfall`) 항목명 공백 정규화 후: CSM상각(부호반대 동규모) + 신계약 CSM(동값, PL에 없으면 SKIP). 메리츠/삼성 수기 모델에서 도출.

**입력 마스터테이블** (사용자 구축 중, long-format, §1.5.1):
- `PL_breakdown.xlsx` — P&L 17항목 (삼성화재 2025.4Q만 값, 나머지 템플릿)
- `CSM_waterfall.xlsx` — 6-step (값 None 템플릿)
- `CSM_amortization.xlsx` — 경과연차별 상각 스케줄 (별도, 현재 cross-check 미사용)
- 회사별 원본: CSM waterfall {KB/메리츠/삼성/삼성생명/한화생명/한화손보}, 보험손익 breakdown {삼성화재/메리츠/삼성생명/한화생명}

- [x] **소비자 코드 구현** (2026-06-07) — `scripts/validate_master_tables.py`. PL_BRIDGE 8단 등식(보험손익 dual-form) + CLOSING_IDENTITY + CSM_CROSSCHECK(4Q-only). 첫 실행: closing 218P/40F, pl_bridge 2023P/36F, crosscheck 33P/20F.
- [x] **룰 정식화** (2026-06-07) — 보험손익 dual-form(bare ΣLOB / adj +기타영업수익-기타사업비용), 영업이익 abs floor 600백만, CSM_CROSSCHECK 4Q-only (YTD 분기배분 노이즈 제거).
- [x] **CSM_waterfall closing 해소** (2026-06-07b) — parser 재추출 후 CLOSING_IDENTITY 40F → **0F** (299P/0F/6S). 23사×13분기 전부 정합.
- [x] **CSM_PLAUSIBILITY 룰 신설** (2026-06-07g) — closing identity 사각지대(산술만 봄) 보강 3종: 복붙(기말 동일) + 기말 QoQ |Δ|>50% 폭변 + **연속성(기초=전년말, 사용자 지적)**. 검출 6 dup / 4 spike / 21 cont.
- [→] **CSM 재추출 (parser)**: 케이디비 2025·흥국 2025 복붙 / 흥국 2025.4Q 기말 34억 폭락 / **메트라이프 2025.4Q 기초 2배(이중계상, KB라이프형 — 연속성만 검출)**. closing 0F였어도 절댓값 틀림.
- [참고] 연속성 21건 중 회색지대(삼성생명 −1,452 등 작은 Δ)는 IFRS17 기초 재작성 가능 → 무조건 오류 아님. 배수/큰Δ만 RED, 작은Δ는 YELLOW(재작성 검토). 교보·KB라이프는 좀 커서 parser 확인.
- [x] **흥국화재 해소** (2026-06-07h) — parser는 diag 소스를 제대로 고쳤으나 `build_root_masters.py` 누락으로 루트 마스터 미반영이었음.
- [x] **빌드→검증 통합** (2026-06-08) — `validate_master_tables.py`가 검증 전 `build_root_masters.py`를 자동 선행(idempotent). 빌드 누락으로 "고쳤는데 검증에 안 보임" 문제 구조적 차단. `--no-build`로 끌 수 있음. **회귀 명령: `python scripts/validate_master_tables.py` (빌드+검증 한 방)**.
- [x] **메트라이프 2배·케이디비 복붙·흥국·롯데 해소** (2026-06-08) — parser fix + 빌드 반영. 진짜 데이터 오류(이중계상/복붙/폭락/롯데 crosscheck) 전부 소진. 현재 dup:0 spike:1 cont:12 crosscheck:0F closing:0F.
- [→] **잔여 확인 대상 (소수)**: 교보생명 cont(2024.3Q/4Q −2,905·2026.1Q +5,659), 케이디비 spike(2024.1Q→2Q +58%). 그 외 cont 회색지대(삼성생명 −1,452 등 작은 Δ)는 IFRS17 기초 재작성 가능 → 무조건 오류 아님, YELLOW로 둠.
- [x] **CSM_CROSSCHECK tol 3단계** (2026-06-07c) — cross-table 표간 편차 구조적 → OK≤max(5%,300mn) / MINOR≤10%(경고) / RED>10%. 결과 66P/2M/2F. 경계 7건 흡수.
- [x] **CSM_CROSSCHECK 진짜 2F 해소** (2026-06-07d) → **0F**. KB라이프 2023.4Q: wf 당기+전기 이중합산(사업결합 기초 2줄) → parser `_is_prior_header()` fix. 코리안리 2025.4Q: validation 룰 스코프 버그(재보험사 발행계약=원수+수재인데 수재 누락) → crosscheck `p=원수+수재CSM상각`으로 수정. **CSM_waterfall 도메인 완전 정합** (closing 0F + crosscheck 0F).
- [참고] crosscheck MINOR 2건 (에이비엘 6.9%·흥국화재 6.4%) — 경고만, pass.
- [x] **DB손해·KB손해 별도/연결 fix** (2026-06-07f) — 2024+ 보험손익 10건 완전 해소. PL_BRIDGE 31F→16F.
- [→] **PL 잔여 14F**: (1) **2023 분기** — 사이트 비노출 → 넘어감. (2) **소액 잔차** (흥국 2025.1Q +714·KB라이프 +1,136·악사 +3,483) — 종목합산 기타비 내재 케이스거나 미세, 지나감. (3) bare로 닫히는 분기(흥국 2024.4Q 등)는 **정상**(종목별 합산에 기타사업비 내재) — flag 안 함.
- [참고] **dual-form은 의도된 설계** (사용자 확인): 종목별 보험손익 합산에 기타사업비가 녹은 회사·분기를 bare로 통과시킴. 앞선 "흥국 2024.4Q 숨은 275억/허점/form 고정 flag" 진단은 오버 → 철회. 한화손보·삼성화재 LOB 별도/연결 교훈(§1.5)은 유효하나 과잉진단 금지.
- [참고] **보험손익 잔차 진단 가이드 (2026-06-07e, §1.5)**: 별도 기준 회사 기타영업수익 구조적 0 → 잔차는 "기타영업수익 누락"이 아니라 **LOB 별도/연결 기준 오선택** 의심. 삼성화재·한화손보 2건 오진 후 정정. parser fix로 둘 다 해소.
- [참고] 신계약 CSM은 `pl_breakdown_master`에 구조상 없음 → cross 짝 없음, V7 `NB_CSM_DART_VS_IR`(IR) + closing identity가 검증 담당. 단위: pl 백만원 / waterfall 억원 (cross-check 시 ×100 정렬).

### V7 — NB CSM cross-source 룰 + 시계열 전수 검증 (2026-06-01, history baseline 확보)

룰 `NB_CSM_DART_VS_IR_ANNUAL_SUM` 정식 codify ([§1.2](docs/agents/claude-agent-validation.md)). Severity RED, tol `max(5%·|IR|, 100억)`.

**검증 도구 2종**:
- `scripts/check_nb_csm_widespread.py` — FY2024 단일 스냅샷 (`csm_waterfall.json`). 7사 cohort. **6/7 OK** (롯데 1건 잔여, FY25 의존)
- `scripts/check_nb_csm_history.py` (2026-06-01 신규) — 13Q × 23사 시계열 (`csm_waterfall_history.json`). DART YTD→per-Q delta 변환 + IR convention-aware. **9사 cohort baseline 확보**

**FY24 widespread 상태**: 6/7 OK, 1/7 OVER (롯데)

| Company | Ratio | Flag |
|---|---|---|
| 미래에셋·삼성생명·삼성화재·DB손해·메리츠·한화생명 | ~1.00 | ✅ OK |
| 롯데손해 | 1.233 | 🟡 +23% (FY25 의존) |

**History baseline 발견 (parser fix 미반영 + 시계열 추가 이슈)**:

Per-company OK rate: 삼성화재 9/12 · 삼성생명 9/10 · DB손해 9/12 · 한화생명 7/13 · 메리츠 4/12 · 미래에셋 4/8 · 롯데 0/5. 한화손해·코리안리는 KR null 매핑 누락으로 전사 MISSING.

**Systemic 이슈 3건** (parser P2와 함께 처리):
1. **2025.2Q cohort-wide 이상치** — 9사 중 OK 1 / OVER 3 / UNDER 2. 그 분기 history 빌더가 블록 선택 룰을 다르게 적용한 패턴
2. **DB손해 2025.2-4Q 부호 반전** — −23,589억 / −7,976억 / +55,162억. 분기 간 블록 비일관 (continuity 깨짐)
3. **미래에셋 2024.3Q-2025.2Q ↑↓ 교대** — 두 다른 블록 alternating, continuity tiebreak 결함 시그널

**잔여 작업**

- [→] Gate enforcement는 **publishing stage 측** (사용자가 publisher에 전달)
- [→] **Parser P1**: 롯데 FY2025 구성요소별 차이조정 표 capture + NB override (412,168 = IR FY25 일치)
  - Raw 위치: `data/dart/FY2025_Q4/raw/KR0003_롯데손해보험_20260319001293/_00760.xml:27375`
- [→] **🚨 Parser P2 회귀**: 19:33 history 재빌드가 분기↔연도 정렬을 1년 밀어버림 (off-by-one-year). 삼성화재 IR singleQ로 증명 — "2024.1Q" 라벨 = 실제 2023.1Q 데이터. 재빌드 로직 수정 후 다시 빌드 필요. systemic 이슈 3건 재확인은 회귀 수정 후로 보류.
- [x] ~~한화손해/코리안리 매칭 누락~~ — 오진 정정 완료. 매칭은 정상; 실제는 코리안리 빈 스텁 + 한화손해 특수 스키마. `check_nb_csm_history.py` cohort 가드로 처리 (skip 사유 로깅).
- [→] **한화손해 stale carryover** (별도 parser 버그): 2025.1Q DART NB가 2024.1Q 값 그대로 복제됨. 한화손해 IR note에 기록.
- [ ] (passive) V1 활성화 시 `CSM_WATERFALL_DART_VS_IR` new_business step과 overlap → retire 검토

**Parser P1+P2 후 회귀 명령**:
- `python scripts/check_nb_csm_widespread.py` → `ok=7/7`
- `python scripts/check_nb_csm_history.py` → per-quarter cohort summary에서 OVER/UNDER 0 수렴, per-company OK 비율 향상

### V2 — IFRS17-NB-RECONCILE 정합성 정정 (2026-06-01: 한화 fallback retire 가능)

`scripts/validate_nb_csm_multiple.py` period-aware denominator + fallback flagging.

- [x] PREFERRED_SCOPE 한화 → `monthly_avg_from_ytd` + `pick_premium_records`에 `prefer_period` 파라미터 (scope 우선순위 유지, 같은 scope 내 period 매칭 row 우선)
- [x] `nb_csm_ratio.json` hanwha_life에 `single_point.2024_total=7.609` (IR series 분기 weighted avg)
- [x] `period_aligned` / `fallback_used` / `cohort_fallback_pass` 정직성 플래그 — aligned-period 실패 후 tolerance 우연 통과 case 표면화
- [x] retry loop max-iter 8→5
- [ ] **한화 fallback flag retire** (2026-06-01) — V7 parser fix 후 한화 분자가 32,346억 → 21,230억으로 정정. 이제 aligned-period FY24 annual benchmark 21,230.85억과 직접 매치하므로 `fallback_used=true` 떨어져야 정상. 재검증: `python scripts/validate_nb_csm_multiple.py` → 한화 `period_aligned=true`, `fallback_used=false` 확인.
- [ ] 삼성화재 IR annual benchmark 보강 — 잔여 fallback 1건 해소 (현대는 IR factsheet에 NB CSM multiple 자체가 부재 → fallback 영구 유지)

**결과**: tested 5 / pass 5 / fallback_pass 3 (한화·삼성화재·현대). V7 parser fix 반영 후 한화 1건 retire 예정.

### V3 — K-ICS 시장위험 분산효과 validation (F12 cross-stage, parser+validation)

`parser+validation` cross-stage. 시장위험 하위위험액 전체(금리·주식·부동산·외환·자산집중) 파싱 후 분산효과 sqrt 정합성 룰 신설. 생명·장기 보험위험 R4 분산효과 sqrt validation과 동형. **화면 노출 X** (데이터 신뢰용). 금리위험액(+5쇼크 순자산 민감도=듀레이션갭)만 추후 display 후보.

- [ ] parser stage가 하위위험액 5개 + 분산효과 행 추출 (parser TODO 측)
- [ ] validation 룰 R11 추가: `시장위험총액 = sqrt(V·R·V) + 분산효과 보정` (R4 패턴 차용)
- [ ] tolerance: 보험위험 R4와 동일하게 `max(2.0, 0.05·|expected|)`

### V4 — QoQ threshold registry

[`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md) §2.

- [x] **2026-05-31**: `config/qoq_thresholds.yaml` v1 생성. global/kics/ifrs17/misc default + item-level override (`new_business_csm` 30%, `csm_amortization` 10%, `insurance_revenue` 20%, `csm_closing` 10%, `csm_interest_accretion` 20%, `item27/28_ratio` 10%) + `cumulative_items` registry mirror.
- [ ] **QOQ_DELTA_WARN 소비자 코드 구현** — 현재 룰은 prompt에 spec만 있고 validator 측 구현 부재(`src/solvency/validation/`에 QoQ 코드 없음, `scripts/validate_*.py` 어디서도 yaml load 안 함). 필요한 것:
  - yaml loader (precedence: item → domain default → global default)
  - prior-snapshot fetch + 누적 항목 net-quarterly 변환
  - finding emit (YELLOW severity, summary에 기록, loopback 안 돌림)
  - 진입점: K-ICS는 `validate_kics_disclosure.py`에 hook, IFRS17은 `validate_csm_waterfall.py` / 별도 스크립트 결정 필요

### V5 — 누적 항목 등록 목록 확장

§2.3 등록된 누적 항목: IFRS17 `new_business_csm`, `csm_amortization`, `insurance_revenue`. 신규 누적 항목 발견 시 등록 + net 분기 기준 비교로 자동 전환.

- [ ] (운영 중 발견 시 갱신)

### V6 — KR0010 KB손해 OCR 잔여 RED 2건

K-ICS rule 2 OCR 미정확 (KR0010, KR0079도 image-only). 사용자 owned ([`TODO.md`](TODO.md) `KICS-IMG`). validation gate는 documented exception으로 처리 중.

- [ ] 수기 OCR 완료 → KICS-VALIDATE RED 2 → 0 회복

---

## 🛡️ Documented exception 관리

운영자(사용자)만 [`TODO.md`](TODO.md)에 `(도메인, 회사코드, 분기, rule_id, 사유)` 추가 가능. 서브에이전트가 자체 판단으로 RED waiver 쓰지 말 것. `escalate_to_human` 단계에서만 "재파싱 5회 실패" 사유 기록.

**현재 활성 exception**
- KR0010 KB손해 / KICS rule 2 / image-only PDF OCR 미정확 (V6)
- KR0079 미래에셋생명 / KICS rule 2 / image-only PDF OCR 미정확

---

## 📞 Loopback contract

[`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md) §3. **max 5회**. RED packaging에 `suspected_source: "DART" | "IR" | "internal"` 명시. cross-source 룰은 항상 `"DART"`.

| 조건 | next_action | exit |
|---|---|---|
| RED=0 | `pass` | 0 |
| YELLOW만 (RED=0) | `pass` | 0 |
| loop_iteration==5 & RED>0 | `escalate_to_human` | 2 |

---

## 📦 최근 시즌 done (요약)

상세 이력은 [`docs/changelog_validation.md`](docs/changelog_validation.md) 참고.

- 2026-06-01 (밤): SEGMENT cross-source 룰 폐기 (IR 부문손익=DART 부문 서비스손익+기타항목 배분, DART는 전사 단일값만 → 재현 불가) + `PL_BRIDGE_DART_INTERNAL` 신설 (§1.5, DART 자기완결 10등식, 삼성화재 2025.4Q 검증 PASS) → V8
- 2026-06-01: V7 history check 도구 신설 (`scripts/check_nb_csm_history.py`, 13Q × 9사 baseline) + systemic 이슈 3건 발견 (2025.2Q cohort-wide / DB 2025.2-4Q 부호 반전 / 미래에셋 ↑↓ 교대); FY24 widespread 6/7 OK (롯데 1건 FY25 의존); 한화 V2 fallback retire 가능
- 2026-05-31: V7 `NB_CSM_DART_VS_IR_ANNUAL_SUM` 룰 + convention-aware check 도구; V2 NB CSM multiple period-aware + fallback flag; V4 `config/qoq_thresholds.yaml` v1 spec; V2 sub max-iter 8→5; DART↔IR cross-source 3개 룰 + IR-side input 계약 §1.4
- 2026-05-30: validation prompt 초안 (R1–R10, IFRS17 CSM 룰셋, `QOQ_DELTA_WARN`, retry loop max=5)
- 2026-05-29: Plausibility gate (`MAX_PLAUSIBLE_MULTIPLE=60`)
- 2026-05-25: K-ICS rules 9 + 10 + RED reduction 419→2 (KR0010 OCR 1건만 잔여)
- 2026-05-24: K-ICS JSON validation rules doc + pipeline gate; KICS-VALIDATE harness; R7 matrix fix

---

## 🔗 참조 룰셋 / 코드

- 권위 doc: [`docs/agents/kics-json-validation-rules.md`](docs/agents/kics-json-validation-rules.md) (R1–R10 formulas, tolerance, R4/R7 matrices, item-label mapping)
- K-ICS 구현: [`src/solvency/validation/kics_json_rules.py`](src/solvency/validation/kics_json_rules.py)
- 러너:
  - K-ICS: `python scripts/validate_kics_disclosure.py`
  - IFRS17 CSM: [`scripts/validate_csm_waterfall.py`](scripts/validate_csm_waterfall.py)
  - IFRS17 NB CSM multiple: [`scripts/validate_nb_csm_multiple.py`](scripts/validate_nb_csm_multiple.py)
  - IFRS17 reconcile loop: [`scripts/run_ifrs17_csm_reconcile_loop.py`](scripts/run_ifrs17_csm_reconcile_loop.py)
- Output 위치: `artifacts/validation/<domain>_<timestamp>.json`
