# Insurequant Publishing TODO (Stage 4)

> Last updated: 2026-05-31 · Stage 4/5 — publishing
> Prompt: docs/agents/claude-agent-publishing.md (skeleton) · Changelog: docs/changelog_publishing.md

Stage 4 — **publishing**: validated per-source JSON → unified master JSONs read by HTML + recommended commit/push commands. Designer ([`TODO_designer.md`](TODO_designer.md)) owns HTML structure/styling; publishing only writes JSON masters. Created 2026-05-31 by splitting out of root `TODO.md` (merged former gathering + pushing stages).

Session start: read this file + `claude-agent-publishing.md` + relevant validation report.

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

## Status

Open viz-assembly work, all gated on upstream stages: F4 v2 (forward-outlook confidence research), F13 (재보험 지표, waits on downloader F8), F17/F18 viz (waits on parser Tier2/IR JSON). CSM bubble map **완결됨** (라이브, 2026-06-14 — 4축 V2 폐기). No master JSON push pending here standalone.

---

## 🚧 Open publishing work

### F4 v2 — Forward Outlook confidence: Cat C/D research + 외국계 분류 helper

Scope 좁힘 (cat E 정상 제외 / cat F 코드 fix 완료).

- F4 v2 report: `output/kics_forward_capital/confidence_low_rootcause_v2_20260525T145147Z.md`
- **Cat B drill-down**: 11사 (10 아님) — KR0069 삼성생명 BS T2 66,289억 (FSC alias 최대 gap), KR0008 삼성화재 4,097억, KR1000 코리안리 4,431억 = alias 해결 시 75,000억 격차 해소
- **Cat C/D 리서치 필요**: BS 자본성증권 carrying value 정의 (FV vs amortized) + Call exercise 시 차감 메커니즘. 답 나오면 over/under_deduct 의미 재정의
- **외국계 분류 helper** 코드 추가 권고: `bond_coverage="no_self_issued, parent_capital"` 등

### F13 — 재보험 영업 지표 세트

Cross-source assembly: GA 채널비중 (downloader F8 → `TODO_downloader.md`) · 위험손해율 (⚠️ 공시-실무 왜곡 명시) · **재보험 현황** (출재보험료 비중 · 출재 CSM 규모 · 원수vs출재 마진갭) · 해지율 13·25·37회차 (F2/F8 → downloader). → 역선택 조기경보 스코어 + 이중관점(원수사 vs 재보험사) 카드.

- [ ] downloader F8 (consumer.knia.or.kr) 도착 후 assembly start
- [ ] 출재율 metric derive — DART reinsurance rollforward (parser side OK) → ratio compute
- [ ] 카드 viz JSON contract 정의 → designer 핸드오프

### F17 viz — Panel 3 net income breakdown (gathering side; parser body in `TODO_parser.md` F17)

Parser는 데이터 추출 + reconciliation gate. Publishing은 그 결과를 panel JSON으로 어셈블 + HTML가 읽도록.

- [x] Tier1 (전사) JSON 어셈블 — 10/10 손보 — `data/dart/viz/net_income_breakdown.json` exists, Panel 3 swapped
- [ ] Tier2 (LOB) — parser 9/11 확장 결과 어셈블 (F17 in-flight decision pending in parser TODO)
- [ ] Tier2 stacked-bar / waterfall viz contract 결정 → designer 핸드오프

### F18 viz — IR factsheet integration (gathering side; parser body in `TODO_parser.md` F18)

- [ ] `data/ir/<period>/parsed/<KR>.json` 도착 후 disclosed_csm_multiple.json + nb_premium_wolnap.json + segment_insurance_income 통합
- [ ] DART↔IR cross-source 룰 validation pass 확인 → 통합 어셈블 진행

### ~~INDEX-IFRS17-BUBBLE / INDEX-BUBBLE-V2~~ — 완결됨 (2026-06-14)

CSM bubble map은 main에 라이브로 **완결**. 실제 축 매핑(index.html ECharts): **X=신계약 CSM 규모(로그), Y=NB CSM 배수, 크기=기말 CSM 잔액**. 4축 V2 재설계는 **폐기(불필요)** — 3개 인코딩이 최종 디자인. (빌더 주석은 JSON 필드 설명일 뿐 축≠필드.) Done 표 참조.

### MISC-IR-NB-DENOM — NB CSM ratio assembly (validation V2는 separate)

In-progress. **Waterfall:** `validate_csm_waterfall.py` 23/23 pass. **NB mult:** 5/6 IR cohort pass. Loop: `run_ifrs17_csm_reconcile_loop.py`. Validation 측 잔여 → `TODO_validation.md` V2.

Publishing 측면: validation pass 후 nb_csm_multiple.json + bubble JSON 갱신.

### MISC-IR-PROTOTYPE — viz prototype assembly

In-progress. CSM Waterfall 23/23 ok. NB CSM ratio IR 6-co. index.html bubble: `viz_build_csm_bubble.py`.

- [ ] 6-co IR cohort 외 cohort 확장 (`build_ir_disclosed_multiples.py` 9사 도착)

### ~~IFRS17-CSM-BUBBLE~~ — 완결됨 (2026-06-14)

INDEX-IFRS17-BUBBLE 과 동일 pipeline. Waterfall validation 23/23. 버블맵 라이브 완결로 흡수됨. Done 표 참조.

---

## 📦 Done — recent (publishing-scoped)

| ID | Task | Done | Notes |
|----|------|------|-------|
| ~~KICS-TIER1-UTIL~~ | tier1 hybrid utilization 2025.4Q assembly | done | SCR×15% strict 10%; 35/38 valid; `output/tier1_utilization/`; `templates/tier1_utilization_latest.json` |
| ~~KICS-TIER2-UTIL~~ | tier2 utilization 2025.4Q assembly | done | KIRI PDF reconcile; 34/38 in 0-100%; `output/tier2_utilization/`; `templates/tier2_utilization_latest.json` |
| ~~KICS-FORWARD-CAPITAL~~ | Forward solvency simulation in K-ICS.html | done v3 | v3 confidence uses `subordinated_eok`. Latest `20260525T061947Z/forward_simulation_v3.json` + inline `window.FORWARD_DATA` |
| ~~IFRS17-HTML-DASH~~ | IFRS17.html 6-panel dashboard data wiring | done | Per-panel JSON contract finalized; designer owns HTML structure |
| ~~F17-T1-PANEL3~~ | Panel 3 클린 4-bar 당기순이익 분해 (data side) | 2026-05-30 | `data/dart/viz/net_income_breakdown.json`; designer swapped Panel 3 layout |
| ~~F5~~ | No-bond insurer forward sim 추가 | done | 24 → 37 cohort. KR0008 삼성화재 263%→263% flat. 13 no_bond insurer 추가 |
| ~~F6~~ | CSM 상각 schedule yearly granularity (data side) | 2026-05-28 | `extract_amort_schedule` emits yearly y1..y10 + y10plus + granularity. 16 yearly / 6 coarse / 2 no-data |
| ~~F1~~ | index.html → IFRS17 cross-nav data hook | done | `fcdd544`. ECharts on('click') → URL param |
| ~~INDEX-BUBBLE~~ | index.html CSM bubble map | 2026-06-14 | Live on main. 축: X=신계약CSM(로그)·Y=NB배수·크기=기말CSM. `viz_build_csm_bubble.py`+`csm_bubble.json`. 코리안리 배수 N/A=회색. 4축 V2 재설계 폐기(불필요) |

---

## Reading order for publishing subagent

1. This file (`TODO_publishing.md`) — current state
2. [`docs/changelog_publishing.md`](docs/changelog_publishing.md) — history
3. [`docs/agents/claude-agent-publishing.md`](docs/agents/claude-agent-publishing.md) — master prompt
4. Validation report (from validation stage) — must be `next_action: pass` before assembling
5. Root [`TODO.md`](TODO.md) for cross-stage dependencies

---

## Hand-off

- **From validation**: validation report with `next_action: pass`. RED=0 across all relevant domains.
- **To designer**: master JSON paths that changed + schema delta if any new fields. Designer decides HTML changes.
- **To human**: suggested `git add` + `git commit -m "..."` + `git push origin main` commands. Human runs them.
