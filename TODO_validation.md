# Insurequant Validation TODO (Stage 3)

Last updated: 2026-05-31.

Stage 3 — **validation**: 파싱된 숫자의 정합성 + QoQ anomaly + 도메인 간 교차검증.

**Stage files**
- Prompt: [`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md)
- Changelog: [`docs/changelog_validation.md`](docs/changelog_validation.md)
- This file: open validation work

Session start: read this file + claude-agent-validation.md + 관련 도메인 ref(`docs/domains/claude-agent-{kics,ifrs17}.md`).

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## 🚧 Open validation work

### V1 — DART↔IR cross-source 3개 룰 활성화 (2026-05-31 신규)

룰은 [`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md) §1.2 + §1.4에 박혀 있음. 전부 RED → DART parser loopback. **현재 IR-side 정형 JSON 부재로 전사 SKIP 상태.**

- [ ] **IR parser delivery 대기**: `data/ir/<period>/parsed/<KR>.json` (root TODO F18). 도착 cohort 9사: 메리츠·삼성화재·현대·KB·DB·한화생명·삼성생명·미래에셋·동양. 도착 즉시 룰 자동 ON.
- [ ] **Threshold v1 튜닝**: 활성화 후 실제 diff 분포 보고 조정. 현재 v1:
  - `CSM_WATERFALL_DART_VS_IR` — max(5%·|IR|, 100억) per step
  - `SEGMENT_INSURANCE_INCOME_DART_VS_IR` — max(10%·|IR|, 50억) per segment
  - `CSM_BREAKDOWN_DART_VS_IR` — max(5%·|IR|, 100억) per item
- [ ] **생보 `segment_insurance_income` 키 셋 확정** (보장성/저축성/연금/변액 등 후보). 결정 후 §1.4 schema + 룰 활성화 조건 갱신.

### V2 — IFRS17-NB-RECONCILE 잔여 (한화생명 period mismatch)

`scripts/run_ifrs17_csm_reconcile_loop.py`. 현재 5/6 cohort PASS. 한화생명만 **FY24 numerator vs IR 1Q25 denominator 시점 불일치**로 fail. severity는 YELLOW (loopback 없음).

- [x] **2026-05-31**: retry loop max-iter 8→5 동기화 (`scripts/run_ifrs17_csm_reconcile_loop.py` `--max-iter` default 갱신)
- [ ] 한화 period mismatch 해소 방침 결정:
  - (a) numerator를 IR 시점 매칭 quarter로 재산정 / (b) denominator를 FY24 retroactive 추정 / (c) documented exception으로 YELLOW 영구 인정

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
- 한화생명 / IFRS17 NB_CSM_MULTIPLE_RECONCILIATION / period mismatch (V2 결정 전까지 YELLOW)

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

- 2026-05-31: DART↔IR cross-source 3개 룰 + IR-side input 계약 §1.4 신설
- 2026-05-30: validation prompt 초안 (R1–R10 codify, IFRS17 CSM 룰셋, `QOQ_DELTA_WARN`, retry loop max=5)
- 2026-05-29: Plausibility gate (`MAX_PLAUSIBLE_MULTIPLE=60`, NB CSM multiple Panel 4)
- 2026-05-25: K-ICS rules 9 + 10 추가 (item2 post≥pre, item14 pre≥post transitional consistency)
- 2026-05-25: K-ICS RED reduction cumulative (419→311→217→99→77→48→10→2; KR0010 OCR 1건만 잔여)
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
