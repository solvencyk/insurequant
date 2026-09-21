# Insurequant Publishing TODO (Stage 4)

> Last updated: 2026-09-21(6차 배포 라이브) · Stage 4/5 — publishing
> Prompt: docs/agents/claude-agent-publishing.md · Changelog: docs/changelog_publishing.md

Stage 4 — **publishing**: validated per-source JSON → unified master JSONs read by HTML + recommended commit/push commands. Designer ([`TODO_designer.md`](TODO_designer.md)) owns HTML structure/styling; publishing only writes JSON masters. Created 2026-05-31 by splitting out of root `TODO.md` (merged former gathering + pushing stages).

Session start: read this file + `claude-agent-publishing.md` + relevant validation report.

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

## Status

**🚀 2026-09-21 6차 배포 라이브 — IFRS17·기타공시 헤더셀렉트+토글 4파일 + K-ICS item14 후 30칸.** main 커밋 `a5118f3`(`6741dea..a5118f3`), owner GO 후 push.
1차 시도(같은 날 앞 세션)는 `validate_kics_rate_sensitivity.py` RS2_BASE_ANCHOR RED=2(흥국생명 2025.2Q/4Q
item14 후 역산치)로 BLOCKED. parser-kics 에이전트가 `inbox/parser/20260921T1400Z` §B 를 처리하다 중단됐고
오케스트레이터가 마무리(`32ebfb0`, 상세는 `TODO_parser_kics.md` 18회차): item14 후 30칸 원문 정수 교체(30/30
MD 대조) + 흥국생명 item23 후 5분기 R5 재폐쇄 + 등재부 pin 갱신 + xlsx sync. `deb21e6` public_exports 재생성
(build_id `32ebfb0`). `21594e6` 골든 입력지문 갱신(kics_disclosure.json 을 입력으로 쓰는 4빌더 — 골든 4종 전부
pass, 산출 불변 확인 후 `--update`).
- 작업 트리 `prepush_check.py --full` 2회: 1차 `골든 입력지문=FAIL → BLOCKED`(예상, 위 갱신으로 해소) → 2차
  **gate-clear**(gate RED=0 · K-ICS 룰게이트 clear · 도메인게이트 pass · 골든 입력지문 pass · 배포 JS 런타임 RED=0 ·
  inbox 위반 0 · 605 passed).
- 격리 워크트리 cherry-push 7파일: `common.css` · `K-ICS.html` · `IFRS17.html` · `공시보고서.html` ·
  `kics_disclosure.json` · `public_exports/K-ICS공시.json` · `public_exports/manifest.json`.
- **라이브 확인**: `manifest.json` build_id `32ebfb0` · 라이브 바이트 ↔ HEAD 블롭 **5/5 일치**(한글 파일명은 curl 에
  URL-encoded 경로로 — 안 그러면 GitHub Pages 404 페이지를 받아 오탐) · `kics_disclosure.json` 흥국생명 2025.2Q
  item14 후 18,412 확인.
- 화면 숫자 변경: K-ICS 세부항목 표 적용후 컬럼 item14 30칸(8사, 대부분 ±1억) · 흥국생명 item23 후 5칸(±3~6억).
  item27 후(비율)는 헤드라인 소스라 불변.
- 워크트리 제거, 로컬 `main` = origin/main `a5118f3`. 남은 티켓: `inbox/parser/20260921T1400Z` §A(RS6 31칸) open.

**🟢 2026-09-21 자본비율전망 비고 내부 진단 문구 분리 (owner 티켓 처리, 배포 안 함).**
`inbox/publishing/20260921T0320Z` 처리 완료(status: answered). owner가 라이브 QA로 지적:
`public_exports/자본비율전망.json` 비고 660행(추정 610행)에 `compute_confidence()`
(`forward_capital_simulation.py`) 내부 게이트 진단 문자열(`subordinated_eok` 등 필드명,
`advisory, not in overall` 게이트 용어)이 그대로 노출.
- **원천 재확인**: 실제 조립 지점은 forward_capital_simulation.py가 아니라
  `build_master_xlsx.py::_flatten_forward_capital()` — `kics_forward_capital.json`
  루트 마스터에는 `비고` 필드 자체가 없다(flatten 시점 파생값). 그래서 **루트 마스터·
  provenance는 전혀 안 건드렸다**(diff 0, 숫자 이동 여지 자체가 없음).
- 커밋 3개: `44ae5fb`(비고에서 reasons 분리, 신설 `_diagnostics` 컬럼 + export
  `_DROP_COLS` 추가) · `a61c8b2`(xlsx "자본비율전망" 시트 sync — sync 도구에 "기존
  시트 컬럼 신설" 케이스 지원 추가) · `c130062`(public_exports 재생성).
- 셀 diff 증명: 총 2090행 불변, jargon 660→0행, `_diagnostics` 비고 제외 키로 재매칭한
  '값' 컬럼 불일치 0건, `check_master_xlsx_drift.py` 드리프트 셀 0.
  `validate_live_artifacts.py` RED=0(YELLOW 17 전부 기존 baseline) ·
  `validate_data_contract.py` RED=0(YELLOW 123 전부 기존 baseline).
- validation에 재발방지 검사 제안 티켓 신설(구현 안 함):
  `inbox/validation/20260921T0335Z__publishing__ALL__public_export_jargon_check_proposal.md`
  (정규식 후보 4개 + false-positive 2건 직접 검증 포함).
- push 안 함 — main 반영 여부는 오케스트레이터/owner 판단. 대상 파일: `scripts/build_master_xlsx.py`·
  `scripts/export_public_sheets.py`·`scripts/sync_master_xlsx_sheet.py`·
  `insurequant_master_tables.xlsx`·`public_exports/자본비율전망.json`·`public_exports/manifest.json`.

**🔴 2026-09-21 5차 배포 — 라이브 K-ICS 금리민감도·세부항목 표 ReferenceError 복구 + 데이터 3건.** main 커밋 `92159dd`(`8ba15d9..92159dd`).
**owner 가 라이브에서 잡았다** — 라이나생명 2026.2Q 금리민감도가 "아직 없습니다"로, 세부항목 표가 "JSON 파일을
불러오는 중 오류 발생: ReferenceError: IQP is not defined" 로 나왔다. 2차 배포(`2dbc4ca`)가 `function IQP()` 정의만
지우고 호출 2곳을 남긴 것. `renderRateSensitivity()` 의 예외가 부팅 `.then` 을 통째로 죽여 `.catch` 가
`table-container` 를 오류 문구로 덮었다(패널 하나가 아니라 페이지 부팅 전체가 죽는 구조). 데이터는 수정 0건.
- 파일 5: `K-ICS.html`(IQP 복구 + renderSensDetail try/catch) · `kics_rate_sensitivity.json`(하나손해·삼성생명·
  카카오페이 2026.2Q 적용후 9칸, 789→798) · `data/dart/viz/sensitivity_heatmap.json`(가정민감도 caption 18사
  메타발언 제거, `354b0f2`) · `public_exports/금리민감도.json` · `manifest.json`(build_id `3633b21`).
- 작업 트리 `prepush_check.py --full` **gate-clear · 593 passed** 후 push. 신설 §1f 배포 JS 런타임 게이트가
  origin/main(구) 을 RED=2 로 재현하고 복구본을 RED=0 으로 통과 — 이번 사고형은 이제 훅이 막는다.
- 라이브 바이트 ↔ HEAD 블롭 **5/5 일치**. 라이브 헤드리스 렌더 4사(라이나·삼성생명·하나손해·카카오페이) 세부항목
  표 41행 · 금리민감도 표 7행 · 미공시 칩 0 · pageerror 0.
- **뒷정리 3겹을 같은 라운드에서 닫았다**: `MASTER_XLSX_ROW_MISSING`(금리민감도 시트 sync 9행) ·
  `viz_ifrs17_panels` 골든 입력지문(`354b0f2` 가 안 올린 것) · `PUBLIC_EXPORT_MISSING_CELL`(재생성). 1차 FULL
  게이트는 이 셋으로 BLOCKED 였고 2차에서 clear.
- 남은 publishing 티켓: `inbox/publishing/20260921T0320Z`(자본비율전망 비고 610행 내부 진단 용어 분리, open).


**🚀 2026-09-21 4차 배포 — 데이터 2묶음(HTML/CSS/JS 변경 0).** main 커밋 `3e9af35`(K-ICS 12+55칸) → `8ba15d9`(PL 백필 775칸).
- `3e9af35`: `kics_disclosure.json` NH농협손보 12칸(6행 표를 7행 슬롯에 맞추던 슬롯 시프트 정정) + item13 적용후
  55칸 삭제(미러 오염, 55/55 과대·과소 0 을 `item13_후 = item4_전 − item12_전 − item2_후` 로 독립 검산).
- `8ba15d9`: `PL_breakdown.json` 12,122→12,897행 · (회사,분기) 374→529 — 비상장 15사 1~3분기 요약 PL 을 정기경영공시
  §2-1 에서 백필(항목 1·16·22·23·24, 계보 DISCLOSURE 155셀 사이드카). 기존 행 덮어씀 0·삭제 0. `public_exports/
  손익분해PL.json` · `manifest.json` 동반. 라이브 12,897행 · 529조합 · 라이나 2026.1Q 보험손익 62,200 확인.
- 둘 다 작업 트리 `prepush_check.py` gate-clear 후 격리 워크트리 cherry-push. 이 기록은 5차 라운드에서 소급 작성.

**🔴 2026-09-20 3차 배포 — 내가 2차에 심은 라이브 버그 정정.** main 커밋 `5aa296f`(`2dbc4ca..5aa296f`).
**owner 가 라이브에서 잡았다** — K-ICS 에서 삼성생명을 고르면 값이 멀쩡한데 네비 칩 3개가 계속 "미공시".
- **기전**: 페이지 부팅 시점엔 보험사 미선택이라 세 패널에 "상단의 보험사를 선택하면…" 안내가 떠 있고
  판정기가 그걸 보고 미공시로 찍는다. 그런데 **렌더 후 재동기화 호출을 IFRS17 에만 넣고 K-ICS 에는
  안 넣어서** 한 번 찍힌 칩이 영영 남았다. 2차 배포 당시 내 검증은 IFRS17 만 회사 선택 후로 확인했고
  K-ICS 는 부팅 직후 상태만 봤다 — **검증 경로가 배선 누락과 같은 모양으로 비어 있었다.**
- **수정**: 페이지마다 배선하지 않는다. `theme.js` 가 `.container` 를 MutationObserver 로 보고 본문이
  바뀌면 다시 잰다(디바운스 180ms). 어느 페이지든 자동으로 맞는다.
- 같이: `index.html` 버블 축 설명(284자 한 줄)을 `?` 뒤로 — 본문엔 축 이름만.
- 라이브 바이트 대조 2/2, 작업 트리 gate-clear · 567 passed. 데이터 미배포.

(밀린 항목은 `docs/todo_archive_publishing.md` 참조 — 2026-09-20 팔레트 B 배포 항목 이번 라운드에 archive됨)

## 🚧 Open publishing work

### F4 v2 — Forward Outlook confidence: Cat C/D research + 외국계 분류 helper

Scope 좁힘 (cat E 정상 제외 / cat F 코드 fix 완료).

- F4 v2 report: `output/kics_forward_capital/confidence_low_rootcause_v2_20260525T145147Z.md`
- **Cat B drill-down**: 11사 (10 아님) — KR0069 삼성생명 BS T2 66,289억 (FSC alias 최대 gap), KR0008 삼성화재 4,097억, KR1000 코리안리 4,431억 = alias 해결 시 75,000억 격차 해소
- **Cat C/D 리서치 필요**: BS 자본성증권 carrying value 정의 (FV vs amortized) + Call exercise 시 차감 메커니즘. 답 나오면 over/under_deduct 의미 재정의
- **외국계 분류 helper** 코드 추가 권고: `bond_coverage="no_self_issued, parent_capital"` 등

### F13 — 재보험 영업 지표 세트

Cross-source assembly: GA 채널비중 (downloader F8 → `TODO_downloader.md`) · 위험손해율 (⚠️ 공시-실무 왜곡 명시) · **재보험 현황** (출재보험료 비중 · 출재 CSM 규모 · 원수vs출재 마진갭) · 해지율 13·25·37회차 (F2/F8 → downloader). → 역선택 조기경보 스코어 + 이중관점(원수사 vs 재보험사) 카드.

- [ ] downloader F8 (consumer.knia.or.kr) 도착 후 assembly start ⚠️ **2026-08-20 실측: 미착수** — `source-catalog.yaml` L392에 URL만 등재돼 있고 `data/knia_consumer/` 없음. downloader TODO F8은 여전히 🔴 P1(사이트 구조 probe 단계).
- [ ] 출재율 metric derive — DART reinsurance rollforward (parser side OK) → ratio compute
- [ ] 카드 viz JSON contract 정의 → designer 핸드오프

### F17 viz — Panel 3 net income breakdown (gathering side; parser body in `TODO_parser.md` F17)

Parser는 데이터 추출 + reconciliation gate. Publishing은 그 결과를 panel JSON으로 어셈블 + HTML가 읽도록.

- [x] Tier1 (전사) JSON 어셈블 — 10/10 손보 — `data/dart/viz/net_income_breakdown.json` exists, Panel 3 swapped
- [ ] Tier2 (LOB) — parser 9/11 확장 결과 어셈블 (F17 in-flight decision pending in parser TODO)
- [ ] Tier2 stacked-bar / waterfall viz contract 결정 → designer 핸드오프

### F18 viz — IR factsheet integration (gathering side; parser body in `TODO_parser.md` F18)

- [ ] `data/ir/<period>/parsed/<KR>.json` 도착 후 disclosed_csm_multiple.json + nb_premium_wolnap.json + segment_insurance_income 통합 ⚠️ **2026-08-20 실측: 1년째 미도착** — `data/ir/**/parsed/`에 파일 1개뿐(KR0087 동양생명 FY2026_Q2). 9사 cohort 미도착. 재개하려면 IR 파서 레인 별도 발주 필요.

> **⚠ 2026-08-30 실측 정정 — "미도착"이 아니라 "미파싱"이다.** `data/ir/` 에 raw IR
> 자료가 **130개 파일** 있다: 현대해상 13분기 · 한화생명 13분기 · 미래에셋생명 13분기 ·
> DB손해 11분기 · KB금융(_groups) 14분기 + 삼성화재·삼성생명·롯데손해·코리안리·동양생명
> 각 1분기. 없는 것은 **`parsed/<KR>.json` 산출물**뿐이고(2개 분기 6개 파일만 존재),
> 즉 수집이 안 된 게 아니라 파싱 단계를 아무도 돌리지 않았다. owner 2026-08-30: IR 은
> 파싱 검증용 보조 소스이니 **꼭 필요할 때만** 착수할 것.
- [ ] DART↔IR cross-source 룰 validation pass 확인 → 통합 어셈블 진행

### ~~INDEX-IFRS17-BUBBLE / INDEX-BUBBLE-V2~~ — 완결됨 (2026-06-14)

CSM bubble map은 main에 라이브로 **완결**. 실제 축 매핑(index.html ECharts): **X=신계약 CSM 규모(로그), Y=NB CSM 배수, 크기=기말 CSM 잔액**. 4축 V2 재설계는 **폐기(불필요)** — 3개 인코딩이 최종 디자인. (빌더 주석은 JSON 필드 설명일 뿐 축≠필드.) Done 표 참조.

### MISC-IR-NB-DENOM — NB CSM ratio assembly (validation V2는 separate)

In-progress. **Waterfall:** `validate_csm_waterfall.py` 23/23 pass. **NB mult:** 5/6 IR cohort pass. Loop: `run_ifrs17_csm_reconcile_loop.py`. Validation 측 잔여 → `TODO_validation.md` V2.

Publishing 측면: validation pass 후 nb_csm_multiple.json + bubble JSON 갱신.

### MISC-IR-PROTOTYPE — viz prototype assembly

In-progress. CSM Waterfall 23/23 ok. NB CSM ratio IR 6-co. index.html bubble: `viz_build_csm_bubble.py`.

- [ ] 6-co IR cohort 외 cohort 확장 (`build_ir_disclosed_multiples.py` 9사 도착) ⚠️ **2026-08-20 실측: 1년째 미도착** — `data/ir/**/parsed/`에 파일 1개뿐(KR0087 동양생명 FY2026_Q2). 9사 cohort 미도착. 재개하려면 IR 파서 레인 별도 발주 필요.

### ~~IFRS17-CSM-BUBBLE~~ — 완결됨 (2026-06-14)

INDEX-IFRS17-BUBBLE 과 동일 pipeline. Waterfall validation 23/23. 버블맵 라이브 완결로 흡수됨. Done 표 참조.

---

## 📦 Done — recent (publishing-scoped)

| ID | Task | Done | Notes |
|----|------|------|-------|
| ~~KICS-TIER1-UTIL~~ | tier1 hybrid utilization 2025.4Q assembly | done | SCR×15% strict 10%; 35/38 valid; `output/tier1_utilization/`; `templates/tier1_utilization_latest.json` |
| ~~KICS-TIER2-UTIL~~ | tier2 utilization 2025.4Q assembly | done | KIRI PDF reconcile; 34/38 in 0-100%; `output/tier2_utilization/`; `templates/tier2_utilization_latest.json` |
| ~~KICS-FORWARD-CAPITAL~~ | Forward solvency simulation in K-ICS.html | done v3 | v3 confidence uses `subordinated_eok`. Latest `20260525T061947Z/forward_simulation_v3.json` + inline `window.FORWARD_DATA` |

> ⚠️ **위 3행의 경로 표기는 2026-07-22 이후 옛것이다** (완료 기록이라 행 자체는 보존).
> 현재 배포본은 루트 `kics_tier1_utilization.json` · `kics_tier2_utilization.json` ·
> `kics_forward_capital.json`이고, K-ICS.html은 이걸 **fetch**한다 — `window.FORWARD_DATA`
> 인라인도, `templates/*_latest.json`도 더는 배포 경로가 아니다(후자 2개는 삭제됨).
> 정본 표 = `docs/agents/claude-agent-publishing.md` §1(재도출 명령 포함).
| ~~IFRS17-HTML-DASH~~ | IFRS17.html 6-panel dashboard data wiring | done | Per-panel JSON contract finalized; designer owns HTML structure |
| ~~F17-T1-PANEL3~~ | Panel 3 클린 4-bar 당기순이익 분해 (data side) | 2026-05-30 | `data/dart/viz/net_income_breakdown.json`; designer swapped Panel 3 layout |
| ~~F5~~ | No-bond insurer forward sim 추가 | done | 24 → 37 cohort. KR0008 삼성화재 263%→263% flat. 13 no_bond insurer 추가 |
| ~~F6~~ | CSM 상각 schedule yearly granularity (data side) | 2026-05-28 | `extract_amort_schedule` emits yearly y1..y10 + y10plus + granularity. 16 yearly / 6 coarse / 2 no-data |
| ~~F1~~ | index.html → IFRS17 cross-nav data hook | done | `fcdd544`. ECharts on('click') → URL param |
| ~~INDEX-BUBBLE~~ | index.html CSM bubble map | 2026-06-14 | Live on main. 축: X=신계약CSM(로그)·Y=NB배수·크기=기말CSM. `viz_build_csm_bubble.py`+`csm_bubble.json`. 코리안리 배수 N/A=회색. 4축 V2 재설계 폐기(불필요) |

---

## Reading order for publishing subagent

1. This file (`TODO_publishing.md`) — current state
2. [`docs/agents/claude-agent-publishing.md`](docs/agents/claude-agent-publishing.md) — master prompt
3. Validation report (from validation stage) — must be `next_action: pass` before assembling
4. Root [`TODO.md`](TODO.md) for cross-stage dependencies

Deferred (2026-07-27): [`docs/changelog_publishing.md`](docs/changelog_publishing.md) is history — open it only when you need the background of a past decision; most sessions don't (현황은 위 1번, 상세는 git log).

---

## Hand-off

- **From validation**: validation report with `next_action: pass`. RED=0 across all relevant domains.
- **To designer**: master JSON paths that changed + schema delta if any new fields. Designer decides HTML changes.
- **To human**: suggested `git add` + `git commit -m "..."` + `git push origin main` commands. Human runs them.
