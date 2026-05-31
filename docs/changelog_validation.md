# Validation Changelog (Stage 3)

Validation 전용 이력. Cross-stage 변경은 [`docs/claude-changelog.md`](claude-changelog.md)에도 1줄 cross-reference 유지.

Stage prompt: [`docs/agents/claude-agent-validation.md`](agents/claude-agent-validation.md). 권위 룰셋: [`docs/agents/kics-json-validation-rules.md`](agents/kics-json-validation-rules.md).

---

## 2026-05-31 — QoQ threshold registry v1 + reconcile loop max-iter 8→5

**V4 (스펙 절반).** `config/qoq_thresholds.yaml` v1 생성. global/kics/ifrs17/misc default 15% + item-level override 등록 — `new_business_csm` 30% (분기 변동성 高), `csm_amortization` 10% (안정), `insurance_revenue` 20% (계절성), `csm_closing` 10% (stock 평탄), `csm_interest_accretion` 20% (금리 sensitive), KICS `item27/28_ratio` 10%. `cumulative_items` registry mirror (§2.3와 동일 — `new_business_csm` / `csm_amortization` / `insurance_revenue`).

Lookup precedence는 item → domain default → global. Cumulative 항목은 net 분기 increment 비교로 자동 전환.

**소비자 코드 미구현 명시**. yaml 자체는 canonical spec으로 박혔지만 `src/solvency/validation/`에 QoQ 코드 없음, `scripts/validate_*.py` 어디서도 load 안 함. wiring task 별도 — TODO_validation V4 sub.

**V2 sub.** `scripts/run_ifrs17_csm_reconcile_loop.py` `--max-iter` default 8 → 5 (prompt §3 동기화). docstring 참조 코멘트 추가.

## 2026-05-31 — DART ↔ IR cross-source 3개 룰 추가

[`docs/agents/claude-agent-validation.md`](agents/claude-agent-validation.md)에 IFRS17 도메인 cross-source 룰 3개 추가 — 전부 RED → DART parser loopback (5회 retry):

- **CSM_WATERFALL_DART_VS_IR** — DART CSM waterfall vs IR factsheet, step별 (opening / new_business / interest / assumption / amortization / closing) 개별 비교. tol = `max(5%·|IR|, 100억)` per step.
- **SEGMENT_INSURANCE_INCOME_DART_VS_IR** — 손보 부문별 보험손익 vs IR (장기 / 자동차 / 일반). tol = `max(10%·|IR|, 50억)` per segment. 생보는 스키마 확정 전까지 SKIP.
- **CSM_BREAKDOWN_DART_VS_IR** — 손보 CSM 도해 vs IR (보장성 / 물보험 / 저축성 or total). tol = `max(5%·|IR|, 100억)`. IR이 segment 미분해 → total만 비교.

§1.4 신설: IR-side input 계약 `data/ir/<period>/parsed/<KR>.json` (모든 값 억원, 누락 키 null → 해당 항목 SKIP, 회사 전체 부재 → 회사 SKIP). 알려진 IR 미공시 회사(교보·KDB·외국계·카카오페이손해 등) 자동 SKIP 명시.

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
