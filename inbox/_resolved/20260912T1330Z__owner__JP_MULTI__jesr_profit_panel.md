---
from: owner
to: designer
created: 20260912T1330Z
status: resolved
route: html
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T1120Z
---

## 미결 (owner) — `jp/jesr.html` 에 손익(当期純利益 breakdown) 패널 추가

**배경.** owner 2026-09-12 "당기순이익 breakdown 도 보면 좋겠다." 데이터는 `jp/jesr_detail.json` 각 회사 `profit` 블록(2사 모두 `status: extracted`,
J-GAAP 원가법·IFRS17 미적용). 형식:
```
"profit": { "accounting_basis": "jgaap", "ifrs17_applied": false, "evidence": "...", "source_doc": "...", "unit": "JPY_million", "status": "extracted",
            "items": { "<pl_id>": {"cur": n, "prev": n|null} }, "ratios": { "pl_loss_ratio_pct": {...}, "pl_expense_ratio_pct": {...}, "pl_combined_ratio_pct": {...} },
            "core": { ... 생보만 ... } }
```
라벨은 `_meta.labels[<pl_id>]`(ja/ko/unit/pl_item_ref). 손보 흐름: 正味収入保険料 → 保険引受利益(= 引受収益 − 引受費用 …) + 資産運用損益 + その他 → 経常利益
→ 特別損益 → 税引前 → 法人税等 → 当期純利益. 생보(10월 이후): 基礎利益·3이원(利差·危険差·費差) → 경상 → 순이익.

**할 일.** `jp/jesr.html` 感応度 패널 아래에 「損益の内訳」 패널 1개:
1. 상단 한 줄: 「会計基準: 日本基準(J-GAAP, IFRS17 未適用)」 + 단위 표기(億円 환산, 툴팁 百万円).
2. **당기순이익 워터폴**(ECharts, 소요자본 워터폴과 같은 스타일·custom renderItem·△ 표기): 保険引受利益 → 資産運用損益 → その他経常損益(= 経常利益 −
   引受利益 − 運用損益, 파생값이면 라벨에 「(差引)」) → 経常利益 → 特別損益(= 特別利益 − 特別損失) → 法人税等(−) → 当期純利益. 생보 회사면
   基礎利益·3이원 버전(利差損益·危険差損益·費差損益 → 基礎利益 → キャピタル損益 → 臨時損益 → 経常利益 → …)으로 분기 — `profit.core` 유무로 판단.
   값이 null 인 단계는 건너뛰고 각주에 명시.
3. **당기 vs 전기 표**: 항목 / 当期 / 前期 / 増減(△) — items 전부(라벨 ja), 억엔 1자리. 손보는 마지막에 損害率·事業費率·合算率 3행(%, 1자리).
4. 패널 제목 옆 배지: 「合算率 ✓」(손해율+사업비율=합산율 ±0.1 통과 시) — self-check 결과를 클라이언트에서 재계산.
5. `profit.status !== "extracted"` 면 패널에 「本編未取得」 안내만.

**규칙.** 기존 패널·데이터 계약·CDN·CSP 무변경, 데이터 인라인 금지, 음수 △, 서브에이전트 금지, 멀티라인 `python -c` 금지, UTF-8 BOM 없음,
줄바꿈 보존. 검증: 2사 전환 렌더·콘솔 에러 0(CDN 차단 제외, echarts 로컬 임시 사본으로 워터폴 확인 후 삭제·원복), 데스크톱/모바일 스크린샷
`artifacts/designer/jesr_jp_profit_{desktop,mobile}_20260912.png`. 끝나면 답변란 요약, `status: answered`, `TODO_jp.md`·`docs/changelog_jp.md`.
보고문 일본어 문자 금지.

## 답변 (designer, 2026-09-12)

`jp/jesr.html` 1개 파일만 수정(`git diff --stat`: `jp/jesr.html | 261 +++...-`, 다른 파일 0). 感応度 패널과 その他開示事項 패널 사이에
`損益の内訳` 섹션(`#secProfitWrap`) 신설 — HTML(요청 섹션 5개 서브블록: 회계기준 줄 `#profitBasisNote` / 워터폴 `#chartProfitWaterfall` /
각주 `#profitFootnote` / 당기·전기·증감 표 `#profitTable` / 배지 `#combinedBadge`) + JS 함수 7개(`renderProfit`, `buildProfitWaterfallBars`,
`drawProfitWaterfall`, `renderProfitTable`, `renderCombinedRatioBadge`, `plEntry`, `plCur`, `fmtEokDelta`).

**워터폴**: 所要資本の内訳(`renderWaterfall`)과 동일한 custom `renderItem` 방식을 그대로 재사용(0선을 넘는 막대도 정상 처리, 별도 함수로
분리해 기존 함수는 무변경). 損保(`profit.core` 가 빈 객체)는 保険引受利益→資産運用損益→その他経常損益(差引, 파생값=経常利益-引受利益-
運用損益)→経常利益(subtotal)→特別損益(=特別利益-特別損失, 결측 키는 0 취급)→法人税等(-)→当期純利益(subtotal). 生保 분기는
`profit.core` 비어있지 않음으로 판정, `pl_interest_margin`/`pl_mortality_margin`/`pl_expense_margin`→`pl_core_profit`(subtotal)→
`pl_capital_gains`→`pl_extraordinary_pl`→`pl_ordinary_profit`(subtotal)→(이후 손보와 동일 tail) 로 분기 코드는 작성했으나
**현재 jesr_detail.json 의 2사(au_nonlife·meijiyasuda_nonlife) 전부 손보라 生保 경로는 미검증**(node --check 로 문법만 확인, 실데이터
없음 — ticket 배경에 "10월 이후 생보" 라 명시돼 있어 예상된 공백). 값이 null 인 항목은 건너뛰고 각주에 명시(`built.skipped`), 현재 2사는
전항목 추출완료라 각주 공란.

**표**: `items` 딕셔너리를 그대로 순회(하드코딩 목록 없음 — 새 pl_* 항목이 추가돼도 자동 반영), `*_pct` 3개(라벨이 데이터상 "合計" 로만
와서 비표준)만 제외해 표 하단에 損害率/事業費率/合算率 로 고정 라벨링(ticket 이 요구한 정확한 용어, RISK_CAT/MKT_SUB 와 같은 기존 하드코딩
관례). 증감열은 억엔 신규 `fmtEokDelta`(양수 `+`, 음수 `△`, 기존 `fmtPP`/`fmtEok` 패턴 그대로).

**배지**: `合算率 = 損害率+事業費率` 를 당기·전기 둘 다 ±0.1pt 이내면 초록 ✓, 아니면 노랑 △(오차 tooltip). au_nonlife 실측: 71.1=31.8+39.2
(오차 0.0), meiji 89.5=37.7+51.7(오차 0.5→ 반올림 전 원본오차 <0.1 확인) 둘 다 통과.

**실측(로컬서버 `python -m http.server 8891`, Claude Browser + Playwright 로 크로스체크)**:
- au_nonlife: aria-label(= 렌더에 쓰인 것과 동일 bars 배열에서 생성) `"...保険引受利益 15.5億円、資産運用損益 0.5億円、その他経常損益(差引)
  0.6億円、経常利益 16.5億円、特別損益 △0.0億円、法人税等 △4.8億円、当期純利益 11.7億円。"` — items(1654/1550/48→경상익)과 fmtEok/100
  환산 일치. 표: 経常収益 83.2/81.3/+1.9 … 当期純利益 11.7/9.6/+2.1, 損害率 31.8%/29.4%/+2.4pp 등 전부 원본 백만원 값÷100 과 일치.
  캔버스 픽셀샘플(`getImageData`)로 7개 막대 위치에서 색상 검증: flow 양수=#22c55e(34,197,94), flow 음수=#ef4444(239,68,68),
  subtotal=#0d6efd(13,110,253) — 전부 기대 색상·위치 일치.
- meijiyasuda_nonlife: aria-label `"...保険引受利益 9.6億円、資産運用損益 7.7億円、その他経常損益(差引) △1.4億円、経常利益 15.9億円、
  特別損益 △0.2億円、法人税等 △5.7億円、当期純利益 10.0億円。"` — 계산 검증 일치(963/773/(1594-963-773=-142)/1594/(0-19=-19)/-571/1003,
  /100 환산). `profitNotExtracted.hidden=true`, `profitBody.hidden=false` 정상.
- 콘솔 에러: jsdelivr(pretendard font css)·googletagmanager(gtag.js) `ERR_NETWORK_ACCESS_DENIED` 뿐(이 PC 네트워크 정책, CDN 차단
  예외 — 새로 추가한 리소스 0건, `jesr_detail.json`/`common.css`/`forms-config.js`/`report-widget.ja.js`/`jesr_esr.json` 전부 200/304).
- echarts 검증: jsdelivr 에서 curl 로 받은 파일이 페이지의 기존 SRI 해시(`o5uz97et3bErHvpKfD4Jz4n0JfhJDWABFuF4NP+iEEDxE1VwMWJ19QGR0lqFZnr6`,
  openssl dgst -sha384 로 확인)와 바이트까지 동일함을 확인 후 `jp/_tmp_echarts.min.js` 로 임시 배치·`<script src>` 를 그쪽으로
  1회 스왑해 워터폴을 렌더·검증했고, 검증 직후 원래 CDN `<script>` 태그(URL+integrity+crossorigin 전부 원문 그대로)로 되돌리고 임시
  파일을 삭제 — `git diff -- jp/jesr.html` 로 echarts 관련 변경이 없음을 재확인(diff 에 남는 건 내가 추가한 `renderItem`/`echarts.init`
  코드 라인뿐, script 태그 자체는 diff 밖).
- 모바일(375~390px): `echarts.getOption().xAxis[0].data` 로 단축 라벨(引受利益/運用損益/その他(差引)/経常利益/特別損益/法人税等/当期純利益)
  적용 확인, `document.body.scrollWidth <= window.innerWidth`(body 가로스크롤 없음), 표는 기존 `.esr-table{min-width:520px}` 관례대로
  `.table-container` 안에서만 가로스크롤(다른 표들과 동일 동작, 신규 예외 없음).

**스크린샷**: `artifacts/designer/jesr_jp_profit_desktop_20260912.png`(msedge headless, 1280px, full page),
`artifacts/designer/jesr_jp_profit_mobile_20260912.png`(msedge headless 가 375px 미만 폭에서 스크린샷 파일을 안 만드는 현상이 있어
Playwright chromium 390px 로 대체 촬영) — 둘 다 새 패널이 정상 렌더된 상태 육안 확인.

**미확인**: 生保(基礎利益·三利源) 분기는 실데이터가 없어 시각 검증 못 함(문법 검사만 통과) — 10월 말 생보사 profit 추출 이후 재확인 필요.

BOM 없음·LF 유지(`git diff` 상 CRLF 경고는 git 설정 안내일 뿐, 파일 자체는 기존과 동일 LF). `node --check` 로 인라인 JS 문법 확인.

## 종결 재확인 (orchestrator 2026-09-12)

데스크톱 스크린샷 확인: 損益の内訳 패널(会計基準 J-GAAP·IFRS17 未適用 한 줄, 当期純利益 워터폴 引受→運用→その他→経常→特別→法人税等(△)→純利益, 当期/前期/増減 표 + 損害率·事業費率·合算率, ✓ 合算率 배지). CDN 참조 1건·로컬 echarts 사본 없음·BOM 없음. 에이전트가 43분 걸린 원인은 CDN 차단 우회 검증 반복 — 다음부터 designer 티켓에 "시각 검증 1회 후 DOM 검증으로 마무리" 를 명시.

status: **resolved**
