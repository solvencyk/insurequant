# Insurequant Publishing TODO (Stage 4)

Last updated: 2026-05-31 (split out of root `TODO.md`; merged former gathering + pushing stages).

Stage 4 — **publishing**: validated per-source JSON → unified master JSONs read by HTML + recommended commit/push commands. Designer ([`TODO_designer.md`](TODO_designer.md)) owns HTML structure/styling; publishing only writes JSON masters.

**Stage files**
- Prompt: [`docs/agents/claude-agent-publishing.md`](docs/agents/claude-agent-publishing.md) (skeleton)
- Changelog: [`docs/changelog_publishing.md`](docs/changelog_publishing.md)
- This file: open publishing work + done archive

Session start: read this file + `claude-agent-publishing.md` + relevant validation report.

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

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

### INDEX-IFRS17-BUBBLE — CSM bubble below K-ICS treemap

In-progress. size=CSM, color=NB CSM mult; `csm_bubble.json` + `viz_build_csm_bubble.py`; K-ICS treemap unchanged.

- [ ] data pipeline 완성도 확인 (현재 27/28, 코리안리 N/A)
- [ ] index.html embed → designer 핸드오프 (구조 변경 시)

### INDEX-BUBBLE-V2 — Bubble chart 4축 재설계 (2026-05-30, 사용자 요청)

현 size·color 2축 → 4축 재구성:
- **X축 = 당기순이익** (단기 수익: 최근 얼마 벌었나)
- **Y축 = CSM 잔액** (미래 이익 재원: 앞으로 얼마 남았나)
- **bubble 크기 = 신계약 CSM** (재원 성장: 매해 얼마나 키우나)
- **bubble 색 = 신계약 CSM 배수** (sales 수익성 건강도)

Data:
- 당기순이익 = F17 `net_income_breakdown.json` (Tier1, 28사)
- CSM 잔액 / 신계약 CSM / 배수 = 기존 `csm_bubble.json`

- [ ] `viz_build_csm_bubble.py` 확장 또는 신규 빌더 (join 로직)
- [ ] 4축 chart spec (ECharts) → designer 핸드오프

### MISC-IR-NB-DENOM — NB CSM ratio assembly (validation V2는 separate)

In-progress. **Waterfall:** `validate_csm_waterfall.py` 23/23 pass. **NB mult:** 5/6 IR cohort pass. Loop: `run_ifrs17_csm_reconcile_loop.py`. Validation 측 잔여 → `TODO_validation.md` V2.

Publishing 측면: validation pass 후 nb_csm_multiple.json + bubble JSON 갱신.

### MISC-IR-PROTOTYPE — viz prototype assembly

In-progress. CSM Waterfall 23/23 ok. NB CSM ratio IR 6-co. index.html bubble: `viz_build_csm_bubble.py`.

- [ ] 6-co IR cohort 외 cohort 확장 (`build_ir_disclosed_multiples.py` 9사 도착)

### IFRS17-CSM-BUBBLE — long-term roadmap

In-progress. Pipeline: crawl (downloader) → validators → `viz_build_csm_bubble.py`. Waterfall validation 23/23.

- INDEX-IFRS17-BUBBLE 과 같은 pipeline 일부. INDEX-BUBBLE-V2 완성 시 자연 흡수.

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
