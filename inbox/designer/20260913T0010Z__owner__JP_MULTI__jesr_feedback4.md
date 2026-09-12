---
from: owner
to: designer
created: 20260913T0010Z
status: open
route: html
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T1520Z
---

## 미결 (owner) — `jp/jesr.html` 를 K-ICS.html 방식으로: 適格資本·所要資本 **한 표 + [+] 펼침**, 손익 선별 흐름 + 재보험 다리, 収益性指標 별도 패널(5개년 SVG)

**owner 2026-09-12~13 피드백(정정 포함).** ① 자본표는 하위 합 ≠ 상위라 부호·계층이 필요 ② 보험/대재해 하위 분해가 화면에 없음 → **별도 패널이 아니라** 한국
K-ICS.html 처럼 **한 표 안에서 [+] 버튼으로 하위 리스크가 펼쳐지는 방식** ③ 손익 항목 선별이 나쁨(총계 행 남발) ④ 손해율은 별도 패널 ⑤ 원수(元受)·수재·출재 분해.

**데이터(`jp/jesr_detail.json`).** `capital_tree`·`risk_tree`(publishing 20260913T0005Z): `[{"id","label_ja","depth","sign":"="|"+"|"-","value","is_total","check"?,
"aggregation"?}]` 전위 순회. `profit_flow`(선별 흐름 `[{"id","label_ja","sign","cur","prev","derived"}]` + `checks`), `profit.items`(전 항목; jp-collector 20260913T0025Z 가
`pl_gross_premiums_written`·`pl_assumed_premiums`·`pl_ceded_premiums`·`pl_gross_claims_paid`·`pl_assumed_claims`·`pl_recovered_reinsurance_claims` 를 추가 — 있으면 사용),
`ratios`·`core`·`history`. 라벨 `_meta.labels`. **산식 해석 금지 — 트리를 그대로 그린다.**

**할 일.**
1. **「適格資本・所要資本」 단일 표**(기존 適格資本の構成 표·所要資本 워터폴·市場リスク 패널을 **이 표로 대체**; 워터폴은 표 아래에 작게 유지해도 됨):
   - 루트 `K-ICS.html` 430~470행 렌더 방식·`common.css` `.subtoggle`·`.subitem`·`tr.subrow-<group>` 그대로. 열 = 項目 | 符号 | 金額(億円) | 備考.
   - 상단 블록 適格資本(`capital_tree`), 하단 블록 所要資本(`risk_tree`) — 블록 헤더 행(굵게) 2개. 자식이 있는 행마다 [+]/[−] 토글, **기본은 depth 1 까지만 펼침**
     (Tier1/Tier2, 生保·損保·巨大災害·市場·信用·運営·分散·税効果), 그 아래는 접힘. 부모를 접으면 모든 자손 숨김(다단 그룹: `subrow-<parentId>` 를 조상 전부에 부여).
   - 符号 열: total 「＝」, 더하기 「＋」, 빼기 「－」(값 앞 △). 備考: total 행은 `check` ok → 「✓」, 아니면 「差 n」; 상관 통합 노드는 「相関統合（単純合計 n）」.
     구성비는 適格資本 블록 depth ≤1 만.
2. **損益の内訳**: 표를 `profit_flow` 행만(符号 열, 当期·前期·増減, 파생 행 「(差引)」). `正味収入保険料` 행과 `正味支払保険金` 행에 [+] 토글 → 재보험 다리 하위 행
   (元受 → ＋受再 → －出再 = 正味 / 元受保険金 → ＋受再 → －回収 = 正味, `profit.items` 의 위 6개 id 가 있을 때만). 손해율 3행 제거. 워터폴은 `=` 행 마디로 재구성.
   `<details>` 「全項目を表示」 로 items 전체 표.
3. **「収益性指標」 패널 신설**(損益 아래): 손보 = 損害率·事業費率·合算率 당기 카드 3개 + `history` 5개년 인라인 SVG 꺾은선(3선, null 끊김, 100% 점선, 값 라벨, `role="img"`
   +aria-label) + 正味収入保険料·当期純利益 5개년 CSS 가로막대 + 연도×지표 표(SMR旧·ESR新 포함, 「—」). 생보 = 3이원 카드 + 基礎利益(코드 경로만). **이 패널은 ECharts 금지.**
4. 상세 없는 회사의 기본 페이지·드롭다운·행 클릭·hreflang·GA·팝업 그대로.

**시간·검증 규칙(30분).** 로컬 서버(빈 포트)에서 au·Meiji: 표 행 수 = capital_tree+risk_tree 길이(+헤더 2), 기본 접힘 상태에서 depth≥2 행 hidden, [+] 클릭 후 표시,
profit 표 행 수 = profit_flow 길이(+다리 행), SVG polyline 3개, pageerror 0 — **DOM 으로만**. ECharts 시각 검증 생략. 스크린샷 1장(`artifacts/designer/jesr_jp_feedback4_desktop_20260913.png`,
CDN 차단이면 차트 빈 채로 OK). 띄운 서버 kill. 서브에이전트 금지, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 줄바꿈 보존, 커밋 금지, JSON·common.css 무변경.
끝나면 답변란 요약, `status: answered`, `TODO_jp.md`(5개 유지)·`docs/changelog_jp.md`. 보고문 일본어 문자 금지.
