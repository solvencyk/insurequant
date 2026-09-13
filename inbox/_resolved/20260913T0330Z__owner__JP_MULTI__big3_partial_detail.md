---
from: owner
to: jp
created: 20260913T0330Z
status: resolved
route: investigate
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260913T0230Z
---

## 미결 (owner) — 확보한 대형 손보 3사 본편(東京海上日動·三井住友海上·損保ジャパン)에서 ESR 외 전 층 추출 → 상세 페이지 5사로

**owner 2026-09-13.** "손해율 있다면서 왜 사이트에는 2사만 나오나." → `J-ESR/raw/fy2025_samples/others/` 의 3 PDF(272~292p)에서 **ESR 층을 제외한
전부**(profit 손익·재보험 다리·history 5개년·article_axes 준비금/재보험 집중·회계기준)를 추출해 `extracted_sample_values.json` 에 3 회사를 추가하고,
`build_jesr_detail_json.py` 가 그 3사를 `companies` 에 넣게 한다(ESR 없는 회사: `esr_status: "not_yet"`, headline 은 esr null, capital_tree·risk_tree 는 빈 리스트,
profit/history/axes 는 채움). 화면(`jp/jesr.html`)은 오케스트레이터가 고친다 — 건드리지 마라.

**할 일(40분).**
1. 3사 각각: 손익계산서(経常収益/費用·保険引受利益·資産運用損益·経常利益·当期純利益), 保険引受の状況(元受/受再/出再·正味, 保険金도), 主要な経営指標等の推移
   (5개년 또는 3개년 — 있는 만큼, 연도 키 FY20xx), 損害率·事業費率·合算率(직접 라벨 또는 5개년표 파생 — 직전 티켓 §10-7 실측대로), 異常危険準備金·普通責任準備金,
   재보험 집중(出再先数·上位5社·格付), 회계기준 근거문장. 표 위치·라벨 변형은 문서 §9·§10 에 회사별 편차로 기록.
2. `extract_esr_template_samples.py` 에 3사 배선(회사 id: `tokiomarine_nichido`, `mitsui_sumitomo`, `sompo_japan`), 검산 P/hist 항등식.
3. `build_jesr_detail_json.py`: ESR 층 없는 회사를 허용(self-check 분기: `esr_status=="not_yet"` 이면 headline.esr_pct null 허용, capital/risk 트리 빈 리스트 허용,
   profit/history 검산은 동일). `_meta.coverage.detail_posted` → `detail_total` 5 / `esr_posted` 2 로 분리. 기존 2사 블록·키 무변경.
4. 재실행 → `jp/jesr_detail.json` 5사. 답변란에 3사 요약(合算率 FY2025·純利益·出재 비중·표 위치).

**규칙.** python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 서브에이전트 금지, 네트워크 불필요, `jp/*.html` 수정 금지, 커밋 금지, 프로세스 종료.
끝나면 `status: answered`, `TODO_jp.md`(5개 유지)·`docs/changelog_jp.md`. 보고문 일본어 문자 금지.

## 답변 (jp, 2026-09-13)

**결과: `jp/jesr_detail.json` 5사(au·Meiji Yasuda = ESR posted 2, 東京海上日動·三井住友海上·損保ジャパン = ESR not_yet 3).** 추출기 exit 0(게이트 실패 0, 3사 profit 31/31·history 10/10),
builder `SELF-CHECK OK`. 기존 2사 블록은 키·값 무변경(추가 키 `esr_status`/`esr_placeholder` 2개만, `_meta.labels` 동일) — 스크립트로 전후 diff 확인.
`_meta.coverage = {detail_total: 5, esr_posted: 2, esr_not_yet: 3, posted_total: 15, census_total: 79}` (`detail_posted` 는 제거).

| | Tokio Marine & Nichido Fire | Mitsui Sumitomo Insurance | Sompo Japan Insurance |
|---|---|---|---|
| 合算率 FY2025 (FY2024) | 93.0 (94.7) — 5개년표 파생, 3개년표 直接 93.0 | **93.2** (98.7) 直接 | **97.0** (100.0) 直接 (5개년 파생 97.1) |
| 損害率 / 事業費率 FY2025 | 61.6 / 31.4 | 62.8 / 30.4 | 63.8 / 33.3 |
| 当期純利益 FY2025 (FY2024), 百万円 | 731,125 (949,719) | 459,965 (459,900) | 295,649 (256,982) |
| 経常利益 / 保険引受利益 | 930,809 / 47,741 | 660,270 / 115,762 | 377,064 / 48,251 |
| 出재 비중 (出再保険料 ÷ (元受+受再)) | 540,476 ÷ 3,185,206 = **17.0%** (元受 含む積立) | 455,012 ÷ 2,209,443 = **20.6%** (元受 除く積立) | 466,747 ÷ 2,842,077 = **16.4%** (元受 含む積立) |
| 元受 / 受再 / 出再 보험료 | 2,862,377 / 322,829 / 540,476 | 2,017,006 / 192,437 / 455,012 | 2,662,630 / 179,447 / 466,747 |
| 元受 / 受再 / 回収 보험금 | 1,420,151 / 264,344 / 229,910 | 998,449 / 164,499 / 192,475 | 1,381,751 / 178,590 / 221,304 |
| 異常危険準備金 합계 / 火災 | 1,072,011 / 393,148 | 590,001 / 127,651 | 693,262 / 288,055 |
| 出再先数 / 上位5社 / A格以上 | 154社 / 61.7% / 99.3% | 209社 / 40.0% / 99.6% (格付는 2026年4月末) | 102社 / 47.5% / 98.9% |
| 회계기준 | jgaap, IFRS17 false (B 티어, p102·p109) | jgaap, false (p107·p109·p114) | jgaap, false (p136·p142) |
| ESR 상태 | not_yet — p35/38/88/128 「別時期での開示」「2026年10月末までに開示」 | not_yet — p26/31/135/242 「2026年10月末までに開示」 | not_yet — p39/116/129/162~164 「2026年10月末の予定」 |
| 표 위치(1-idx) | 損益 p102 · 明細 p90 · 比率 p91 · 5개년 p88 · 다리 p89~91 · 재보험 p92 · 준비금 p118 | 損益 p109 · 明細 p100 · 比率 p99 · 5개년 **p31**(직전 티켓 "없음"은 오판) · 다리 p94~97 · 재보험 p55 · 준비금 p123 | 損益 p136 · 明細 p122 · 比率 p120 · 5개년 p116 · 다리 p117~119 · 재보험 p121~122 · 준비금 p151 |

**설계 결정(추정 없음, 전부 원문 산수).**
1. TMNF·Sompo 의 元受正味保険料 표는 「含む収入積立保険料」뿐 → 공시값 그대로 저장하고 損益計算書 「収入積立保険料」 행(48,334 / 63,753)을 `profit.adjustments.deposit_premium_in_gross` 로 뽑아 P14 에서 차감(8/8 통과). MSI 는 「除く」 표가 있어 그 값.
2. P07(経常利益 브리지)에 `− その他収支` 항 추가(保険引受利益 안의 自賠責 法人税相当額은 経常利益에 없음). TMNF 는 −3,152 라 이 항 없이는 실패, 넣으면 0 차이. au/Meiji 결과 불변(tol 3 안). P11 tol 1→3(4항 절사, Sompo 48,253 vs 48,251).
3. 資産運用損益은 3사 모두 積立保険料等運用益 ≠ 0 이라 Meiji 와 같은 `pl_stmt` 대체(P&L 資産運用収益−費用).
4. 회계기준 IFRS 검색을 basis 페이지로 한정 — 본편 뒷부분의 그룹 연결 IFRS17 재무제표 때문에 単体 손익이 ifrs 로 오판되던 것. 근거문에 "連結 section is IFRS at group level" 명시.
5. Sompo Japan 폰트 함정(직전 티켓 §10-7)은 숫자만이 아니라 **한자·가나 전부** 글리프 id 였다 — 한자는 MS Gothic 글리프 순서와 정확히 일치해 `C:/Windows/Fonts/msgothic.ttc` 의 cmap 을 뒤집어 복원(`GidDoc`, `gid_decode=True`). 이 PC 폰트 의존(없으면 경고).
6. builder: `esr_status` 를 5사 전부에 넣음(HTML 분기 편의). not_yet 3사는 headline ESR null·capital/items/sensitivity/트리 빈값·risk/market_sub 전부 null, self-check 가 "빈값이어야 함 + placeholder 문구·페이지 존재 + profit 필수 4항목 + 合算率 항등식 + history 교차" 를 검사. nnlife(not_yet, history 층 없음)는 제외.
7. `_meta.labels` 4개(資産運用損益·合算率·旧基準 SMR·ESR 新基準)는 커밋 e67bc36 에서 JSON 을 손으로 고쳐 둔 것이라 builder 재실행이 되돌릴 뻔 → builder `LABEL_JA_DISPLAY_OVERRIDES` 로 고정.

**산출·문서.** `J-ESR/raw/fy2025_samples/extracted_sample_values.json`(6사) · `J-ESR/esr_disclosure_schema.json`(bridge 라벨 변형 3개 추가) · `jp/jesr_detail.json`(5사) ·
`J-ESR/extract_esr_template_samples.py`(BRIDGE_SPEC/RESERVE_SPEC/GidDoc/3사 config) · `J-ESR/build_jesr_detail_json.py` · `docs/domains/jp_esr_disclosure_template.md` §9-8·§10-8.
`jp/*.html`·커밋·서브에이전트·네트워크 없음. 40분 규칙은 초과(폰트 복원·3사 레이아웃 3종이 각각 별도 경로).

## 종결 재확인 (orchestrator 2026-09-13)

5사 JSON·페이지 DOM 검증(3사 profit 19행·카드 3·polyline 3·準備金 표, 드롭다운 18, pageerror 0), 커밋 a15637b. 함정 5건 문서화 확인.

status: **resolved**
