# changelog_validation.md 보관 — 미분류(옛 압축 보관 절)

> `docs/changelog_validation.md` 에서 무수정으로 옮긴 항목(최신이 위). 현행 항목은 원 파일에 있다. 관리: `scripts/doc_rotate.py changelog`.

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
