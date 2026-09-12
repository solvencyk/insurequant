---
from: owner
to: designer
created: 20260912T1520Z
status: resolved
route: html
company: JP_MULTI
period: FY2021-FY2025
track: J-ESR
supersedes: 20260912T1420Z
---

## 미결 (owner) — `jp/jesr.html` 「主要指標の推移」 패널: 5개년 시계열(손해율·사업비율·합산율 + 정미수입보험료·당기순이익), **ECharts 금지·순수 SVG/CSS**

**owner 2026-09-12.** "손해율·사업비율·합산비율 시계열을 쭉 보여줘라. 당기/전기만 있어 허전하다." + "일본판은 가벼워야 한다, 왜 이렇게 오래 걸리나"
→ 이 패널은 **ECharts 를 쓰지 않는다**(CDN 차단 검증 루프 원인 제거). 데이터: `jp/jesr_detail.json` 각 회사 `history` 블록
`{"unit":"JPY_million","fiscal_years":[...5],"series":{"hist_loss_ratio_pct":[...], "hist_expense_ratio_pct":[...], "hist_combined_ratio_pct":[...],
"hist_net_premiums_written":[...], "hist_net_income":[...], ...}}` (null 가능: Meiji 비율 FY2021~22 없음), 라벨 `_meta.labels[hist_*]`.

**구성(損益の内訳 패널 바로 아래, 상세 있는 회사만).**
1. 제목 「主要指標の推移（5事業年度）」 + 단위 줄(比率 %·金額 億円).
2. **비율 꺾은선 1개(인라인 SVG, viewBox 기반 반응형)**: 損害率·事業費率·合算率 3선(색 3개, 범례 텍스트), x축 FY2021…FY2025, y축 0~100% 눈금 4개,
   각 점에 값 라벨(소수 1자리), null 구간은 선 끊김. 합산율 100% 기준선(점선). `role="img"` + 데이터 기반 `aria-label`.
3. **금액 막대 2열(순수 CSS `.li-bar` 계열 재사용)**: 正味収入保険料·当期純利益 연도별 가로막대(같은 섹션 최대값 기준 폭), 억엔 1자리, 음수 △.
4. 표: 연도 × (正味収入保険料·経常利益·当期純利益·総資産·純資産·損害率·事業費率·合算率·SMR(旧)·ESR(新)) — 값 없는 칸 「—」.

**시간·검증 규칙(25분).** 순수 HTML/CSS/SVG 라 CDN 무관 — 로컬 서버에서 au·Meiji 두 회사 전환해 SVG 점 개수·표 행 수·pageerror 0 을 DOM 으로 확인하고
스크린샷 1장(`artifacts/designer/jesr_jp_history_desktop_20260912.png`). 띄운 http.server 는 끝나기 전에 kill. 다른 패널·JSON·CSS 공유 파일 무변경.
서브에이전트 금지, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 줄바꿈 보존, 커밋 금지. 끝나면 답변란 요약, `status: answered`, `TODO_jp.md`(5개 유지)·
`docs/changelog_jp.md`. 보고문 일본어 문자 금지.

## 종결 (orchestrator 2026-09-13)

owner 피드백 4건(자본표 부호/들여쓰기·보험/대재해 하위·손익 항목 선별·손해율 별도 패널)과 합쳐 한 라운드로 재발주 — 시계열은 「収益性指標」 패널로 흡수. 에이전트는 마지막 단계에서 종료했고 부분 편집은 되돌렸다(다음 라운드에서 재구현). supersedes → 20260913T0010Z.

status: **resolved**
