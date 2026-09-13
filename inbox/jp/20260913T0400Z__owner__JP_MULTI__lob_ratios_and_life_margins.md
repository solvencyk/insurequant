---
from: owner
to: jp
created: 20260913T0400Z
status: open
route: investigate
company: JP_MULTI
period: FY2021-FY2025
track: J-ESR
supersedes: 20260913T0330Z
---

## 미결 (owner) — ① 손보 5사 종목별(LOB) 손해율·합산율 층 ② 생보 기초이익·3이원(利差·危険差·費差) 5개년 census+추출

**owner 2026-09-13.** "손해율·사업비율·합산율이 종목별(자동차·재물 등)로 찢어져 있지 않나? 생보는 이차·사차·비차 마진 통계가 있을 테니 조사해서 라이브에 추가하라."

**① 손보 종목별 층(`layer: "by_line"`).** 대상 5사(au·Meiji Yasuda Non-Life·東京海上日動·三井住友海上·損保ジャパン, PDF 는 `J-ESR/raw/fy2025_samples/` 및 `others/`).
「保険引受の状況」(種目別: 火災·海上·傷害·自動車·自賠責·その他·合計) 에서 종목×{正味収入保険料, 正味支払保険金, 正味損害率, (있으면) 正味事業費率·合算率}, cur/prev.
스키마 id 예: `lob_net_premiums_written{line}`, `lob_loss_ratio_pct{line}` — 종목 코드는 `fire|marine|pa|motor|cali|other|total` 로 통일하고 labels_ja 에 원문 종목명.
검산: 종목 합 = total(±1), total 손해율 = profit 층 損害率(±0.1). 회사별 종목 구성 차이(au 는 자동차 중심 등)는 문서에.

**② 생보 기초이익·3이원(`layer: "core_history"`).** 표본: NN Life(이미 확보, 3이원 표 없음 확인됨) + census `disclosure_url` 이 있는 생보 중 대형 상호회사·상장 4사
(日本生命·明治安田生命·住友生命·第一生命 또는 かんぽ生命·ライフネット 등 URL 있는 곳)의 FY2025 디스클로저지 본편을 curl(막히면 회사당 1회, 미확보 표기)로 받아
`others/` 에 저장. 각 사: 基礎利益 5개년 유무·연도 수, 三利源(利差損益·危険差損益·費差損益) 공시 유무·연도 수·라벨, 값(있는 만큼), 임의 공시 여부 메모.
스키마 id: `hist_core_profit`, `hist_interest_margin`, `hist_mortality_margin`, `hist_expense_margin` (`{FYxxxx: v}`), 검산 `基礎利益 ≈ Σ三利源`(회사 정의 차이 명시).
결과 표를 문서 §11 "생보 3이원 census" 로.

**③ builder.** `build_jesr_detail_json.py` 에 `by_line`(손보) / `core_history`(생보) 블록 + 라벨. 생보 회사는 ESR 층 없어도 companies 에 추가(직전 티켓 규칙과 동일).
재실행 → `jp/jesr_detail.json`. 화면은 오케스트레이터가.

**시간 규칙 45분.** python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 서브에이전트 금지, `jp/*.html` 수정 금지, 커밋 금지, 프로세스 종료, 회사 하나 끝날 때마다 저장.
끝나면 답변란에 ① 5사 종목별 표 요약 ② 생보 표본 census 표, `status: answered`, `TODO_jp.md`(5개 유지)·`docs/changelog_jp.md`. 보고문 일본어 문자 금지.
