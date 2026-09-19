# Insurequant Designer TODO (Stage 5)

> Last updated: 2026-09-15c · Stage 5/5 — designer
> Prompt: docs/agents/claude-agent-designer.md (§5 design system formalized 2026-06-16) · Changelog: docs/changelog_designer.md

Session start: read this file + `claude-agent-designer.md` + the page(s) in scope (root HTML files). Publishing ([`TODO_publishing.md`](TODO_publishing.md)) owns master JSONs; designer only reads them and decides how they render. English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

Stage 5 = HTML structure / styling / responsive breakpoints / A11y / chart layout. Desktop pages are in production; KEYCOLOR-V1 K-ICS cancelled by owner (IFRS17 구현 불만족). Mobile scope confirmed; M1 foundation done; full mobile pass open.

**Recent (2026-09-15c, 손해율 버블차트 폐지 → 적층막대 일원화 — owner 질의("비용 대비 효용"), 커밋만·라이브 미배포):**
- **owner 질문: 손해율×사업비율 버블이 난잡함에 비해 값어치를 하냐, ESR 랭킹만 남기고 치울까.
  재서 답했다 — ① 버블은 빼고 ② 패널 자체는 남긴다.**
- **①-a 2D 자체는 정보가 있었다.** 손해율-사업비율 상관 **r = −0.096**(대각선이 아님). 합산율이
  1.0pt 이내인 쌍 56개에서 손해율 차이 평균 **10.3pt**·최대 **35.6pt**(明治安田 37.7 vs SBI 73.3).
  즉 "합산율 하나로 뭉개면 안 된다"는 맞다.
- **①-b 그런데 적층막대가 그 정보를 안 잃는다.** 손해율·사업비율 두 값이 구간으로 그대로 보이고,
  **합산율은 막대 길이 + 숫자**(버블에선 색 농도 하나뿐이었다 — 헤드라인 지표에 가장 약한 채널을
  주고 있었다). 버블만의 추가 정보는 "원 크기=보험료" 하나인데 그건 이미 정렬 순서가 담당한다
  (10만배 차이라 범례에 「面積比≠保険料比」 변명을 달고 있던 채널이다).
- **①-c 실측 비교(1280px)**: 회사명 표시 버블 30사 중 일부만(라벨 충돌) → 막대 **31사 전건**.
  겹친 쌍 버블 10조(최악 −20.4px) → 막대 **0조**. JS 에러 0, 가로 넘침 0.
  **ECharts CDN(1,029,203 bytes)이 이 페이지에서 통째로 빠졌다** — 유일한 사용처가 버블이었다.
  HTML −19,292 bytes.
- **② "ESR 랭킹만 남긴다"는 안 된다 — 재보니 손보 ESR 은 5사뿐이고 그중 3개가 지주사다**
  (au損保·明治安田損保 + SOMPO HD·東京海上 HD·MS&AD HD). 東京海上日動·三井住友海上·損保ジャパン·
  あいおい 같은 **대형 사업회사는 ESR 랭킹에 아예 없다.** 손해율 패널을 치우면 손보 31사 중 26사가
  화면에서 사라진다(마크업 주석에도 "이 회사들의 유일한 입구"라고 적혀 있다).
- **③ 막대 척도에 버블과 같은 병이 남아 있어 같이 고쳤다.** 꼬리 2사(ヤマップ 230.0%·全管協
  237.4%, 둘 다 事業費率>100%)가 트랙의 **49%**를 먹어 29사가 왼쪽에 뭉쳤다. 버블이 쓰던 것과
  **같은 선·같은 이유**(事業費率>100% = 보험료보다 비용이 큰 구조적 이상)로 눈금에서 빼고 오른쪽
  끝에서 打ち切り(사선 해치, 실수치는 우측 숫자·title 로 상시 개시). 실측 89.3%~98.4% 폭차
  **27px → 52px**, 대형4사 12px → 23px.
- **③-b 눈금 기준을 `list`(접힌 5사) → `full`(31사)로.** 종전엔 「もっと見る」로 척도가 바뀌고,
  접힌 상태에선 maxV=97.1 이라 **100% 기준선이 오른쪽 끝에 붙어 있었다**(실측). 이제 양쪽 82% 고정.
- **④ 칩: 정직하게 재니 내가 또 늘렸길래 도로 줄였다.** 버블 뷰 4칩/잔글씨 4줄 → 일람 뷰가
  5칩/**5줄**이 됐다(버튼 뒤에 있던 6칩 범례가 상시 노출로 바뀌어서). 색 칩 2→1 병합 + caveat 칩
  3줄을 **1줄**로 접어(印＝値に注記あり：Δ／OCR／Σ) **3칩/4줄**. 배지 자체는 각 행에 그대로고
  긴 설명은 이미 배지 `title`·행 `aria-label` 에 있다 — 범례에서 중복이던 부분만 뺐다.
  caveat 칩은 `data-caveat-cat` 으로 **실제로 그 印이 붙은 행이 있을 때만** 나온다.
- **다음**: ESRランキング 범례 8개는 그대로다(2026-09-15b 에서 넘긴 건, owner 판단 대기).
  일본 손보의 진짜 핵심축은 「引受으로 버느냐 運用으로 버느냐」인데(東京海上 引受利益은 経常利益의
  **5%**, 三井住友 17%, 損保ジャパン 13% — 실측) `pl_underwriting_profit`/`pl_investment_pl` 이
  5~6사뿐이라 아직 화면에 못 올린다. jp 레인 수집 타깃으로 넘긴다.

**Recent (2026-09-15b, 버블 하단 잔글씨 7줄→4줄 — owner 반려("칩 남발"), 커밋만·라이브 미배포):**
- **owner 지적이 맞다. 이번 세션에 내가 늘렸다.** 이 세션 전 범례는 5줄이었고(`1499f9f`), 버블
  라운드에서 7줄이 됐다 — 마지막 3문장짜리 확대 조작 안내는 2026-09-14c 에 내가 얹은 것이다.
  `d70be8a` 에서 이미 "랭킹 칩 3개→1개"로 한 번 쳐냈던 축인데 도로 늘렸다.
- **원칙 2개로 정리했다.** ① **화면에 없는 것은 설명하지 않는다** — 「点線の円＝保険料未収録」은
  실제 未収録이 **0사**인데도 상시 출력되고 있었다(있지도 않은 상태를 설명). ② **조작법은 범례가
  아니다** — 확대 3문장을 meta 한 줄 끝으로 옮겼다.
- **구현**: 고정 범례는 2개만 HTML 에 남기고(`data-fixed`), ▲·破線·点線은 `renderLossRatioBubble()`
  이 실데이터를 보고 붙인다. 색 2줄(緑/赤)은 swatch 2개를 한 줄에 합쳐 1줄로. 사이즈 줄의 긴
  면적 caveat 은 `title`(호버)로 내리고 본문은 「非線形・面積比≠保険料比」로 압축.
  MS&AD 주석 3줄도 1줄 + `title` 로.
- **실측**: 차트 하단 6행 → **3행**(meta 1 + 범례 1 + MS&AD 1), 범례 항목 7 → 4.
  未収録 0사라 点線 줄은 실제로 안 나온다. **재렌더 2회 후에도 4개 유지**(조건부 항목이 중복
  누적되지 않는지 확인 — `span:not([data-fixed])` 를 매번 비우고 다시 붙인다). 가로스크롤 없음, 에러 0.
- **다음**: ESRランキング 범례는 아직 8개다(이번 지적 범위 밖 — "아랫부분"이라 했고 랭킹은 상단).
  줄일지는 owner 판단.

**Recent (2026-09-15, 손보 決算 상세에 BS/損益 패널 개방 — owner 발주(직접 지시), 커밋만·라이브 미배포):**
- **배경: 패널은 원래 다 만들어져 있었고 데이터가 없어 숨어 있었을 뿐이다.** jp 레인이 법정 BS/PL 을
  실으면서(21사/23사) `jesr_app.js` 의 두 군데 전제가 사실과 어긋나게 됐다.
- **① `setHidden('secProfitWrap', ratioOnly)` → PL 유무로 판정.** "ratio_only 면 損益 패널 무조건 숨김"은
  ratio_only 에 PL 이 아예 없던 시절 규칙이다. 이제 `profit.items` 에 보험료 말고 다른 항목이 실제로
  있는지로 판정한다 — 아직 없는 회사(출처 교체 대기·스캔 PDF)는 종전대로 숨고 scopeNoteWrap 한 줄이 이유를 남긴다.
- **② `if(ratioOnly){dispose} else {renderProfit}` → 같은 조건으로.** 위만 고치면 패널만 열리고
  본문이 안 그려져 **빈 패널**이 된다(실측). renderProfit 을 실제로 호출해야 워터폴+표가 붙는다.
- **③ 단계표(profit_flow)가 없는 회사는 빈 표 대신 전 항목표를 본문으로.** `profit_flow`(元受収支→
  再保険収支→…)는 本編까지 읽은 회사에만 있어, 법정 PL 만 실은 19사는 요약표가 「データがありません。」
  한 줄로 남았다(실측). 그 표를 접고 `<details>` 의 전 항목표를 펼치며 summary 문구를
  「全項目を表示」→「損益計算書（全項目）」로 바꾼다. **HTML 3벌(jesr/jgaap/disclosure)을 고치지 않고**
  `closest('details')` 로 DOM 에서 찾아 처리했다(§5.2 파일별 복사 관례를 늘리지 않으려고).
- **실렌더 확인**: AIG損保 상세에서 워터폴(経常利益 282.6 → 特別損益 △95.3 → 法人税等 △52.2 →
  当期純利益 135.0)과 16행 損益計算書 표, 16행 BS 표, `✓ 資産 = 負債 + 純資産` 배지까지 눈으로 확인. 콘솔 에러 0.
- **회귀 확인**: 기존 full 회사(東京海上日動·損保ジャパン·au損保)는 단계표 19~21행 그대로 보이고 전 항목표는
  접힌 채다. 회사 셀렉트로 신규→기존 전환해도 토글이 따라온다(aig→東京海上日動 실측).
- **다음**: 아직 PL/BS 가 없는 10사는 jp 레인 몫(`TODO_jp.md` (33)). 라이브 배포는 폰 Termux 번들.

**Recent (2026-09-14c, 손해율 버블차트 실렌더 검증 + 3건 수정 — owner 발주(직접 지시), 커밋만·라이브 미배포):**
- **배경: (2026-09-14b)의 버블차트는 코드가 들어갔을 뿐 "그려지는 걸 본 적이 없었다"**(담당
  에이전트가 세션 한도로 최종검증 직전에 끊김). 이 라운드는 그 검증을 끝내고, 검증에서 나온 결함
  3건을 고친 것. **이 샌드박스의 Chromium 은 외부망을 못 뚫어 CDN 의 ECharts 가 안 온다**(curl 은
  프록시로 됨) — 그래서 `echarts=undefined`·canvas 0 이 나왔던 것이지 페이지 결함이 아니었다.
  받아둔 `echarts@5.5.0` 의 sha384 가 페이지 `integrity` 속성과 **바이트 단위로 일치**함을 먼저
  확인한 뒤(=페이지가 가리키는 파일이 맞다), Playwright `route()` 로 그 사본을 물려 실렌더했다.
  **저장소에는 사본을 넣지 않았다**(하네스 전용, `jp/index.html` 은 CDN 그대로).
- **결함① 라벨이 글자죽이 됐다 — `labelLayout` 에서 `moveOverlap:'shiftY'` 제거.** 실측: 현행
  `{hideOverlap:true, moveOverlap:'shiftY'}` 는 30장 전부 그려서 **겹침 35쌍**(밀집대에서 판독
  불가). `moveOverlap` 이 `hideOverlap` 을 무효화한다(`hideOverlap` 단독 = 16장/겹침 0쌍).
- **결함② 대형 4사 라벨이 1장만 남았다 — 라벨 방향 4방향 회전(上→右→下→左).** `hideOverlap`
  단독은 겹침은 0 이지만 대형4사(東京海上·損保ジャパン·三井住友·あいおい) 중 1사만 살아남았다.
  `normalSorted`(원 큰 순)의 인덱스로 방향을 돌리면 **가장 큰 4개에 반드시 서로 다른 방향**이
  배정된다 → 19장/겹침 0쌍/대형4사 4/4, 컨테이너 밖으로 나간 라벨 0장. 회사 ID 하드코딩 없음.
- **결함③ 대형 원을 눌렀는데 소형사 상세로 갔다 — 클릭 대상을 "클릭점을 실제로 포함하는 원"으로
  재판정.** 라벨은 원보다 위에 그려지므로 소형사의 긴 라벨이 대형원 위에 얹힌다(실측: 東京海上의
  원 중심이 ペット＆ファミリー 라벨 사각형 안에 있었고, 東京海上을 눌렀더니 `pet_and_family` 로
  이동했다). ECharts 의 `params.data` 는 라벨을 눌러도 같은 데이터를 주므로 params 만으론 못 고친다.
  `params.event.offsetX/Y` 로 포함 판정, 복수 포함이면 **작은 원 우선**(큰 원 위에 얹힌 작은 원을
  누를 수 있게 — 그리기 순서와 같은 기준). 포함하는 원이 없으면 종전대로 params(=라벨만 조준한 경우).
  4종 클릭(최대원/대형원에 인접한 소형원/고립원/아웃라이어▲) 전부 의도한 회사로 이동 확인.
- **owner 지시 "원끼리 안 겹치게" 는 기본 표시에서는 수학적으로 불가능하다 — 대신 축소+확대 제공.**
  최근접 2사(三井ダイレクト 64.3/28.9 · ペット＆ファミリー 64.2/28.6)의 화면상 중심거리가 **2.0px**
  라서, 이 둘이 안 닿으려면 두 원의 지름 합이 4.1px 이하 = 전 회사를 2px 점으로 만들어야 한다
  (원 크기=보험료 정보가 사라진다). 대형4사도 손해율 2.9pt·사업비율 2.9pt 상자 안에 있고, 이건
  "대형4사는 율이 거의 같고 규모만 다르다"는 실데이터 사실 그 자체다. 좌표를 밀어 떼어놓는 건 값의
  거짓말이라(owner: 좌표는 밀지 마라) **① 원 지름 천장 46→34**(실측 겹침 20쌍/최악 -30.7px →
  **10쌍/최악 -20.4px**) **② toolbox 「範囲を指定して拡大」+「初期表示に戻す」**로 처리.
  원 지름은 확대해도 일정하므로 배율만 올리면 반드시 떨어진다 — 실측 확대(손해율62~67/사업비27~35)
  후 최근접쌍 **+17.9px**, 損保ジャパン×あいおい **+132.8px**. 실 UI 경로로 검증: 아이콘 클릭 후
  드래그한 사각형 그대로 58.04~68.06/25.97~36.02 로 들어가고, 되돌리기로 0~90/0~80 완전 복귀.
- **`dataZoom` 의 `type:'inside'` 는 일부러 넣지 않았다 — 넣으면 도표 위에서 페이지 스크롤이 죽는다.**
  실측: `zoomOnMouseWheel:'ctrl'` 로 해도, 휠 옵션을 전부 `false` 로 해도 素 휠이 페이지로 안 간다
  (도표 위 scrollY Δ0 / 도표 밖 Δ+263). 이 도표는 높이 520px 로 세로로 긴 페이지 한가운데 있어서
  독자가 아래로 스크롤할 때마다 커서가 도표에 들어가 멈추는 = 전원이 밟는 사고가 된다. Ctrl+휠 확대와
  드래그 pan 이 편하긴 하지만 페이지가 안 움직이는 대가가 더 크다고 보고 버렸다(확대는 toolbox 로).
- **모바일(375px)은 발주대로 전건 확인.** 버블 wrap `display:none`·인스턴스 미생성(0×0 init 방지),
  31사 목록이 **정미수입보험료 내림차순**(MS&AD HD 3,225,600 → … → 全管協れいわ 26백만엔, 31/31
  단조), 막대는 손해율+사업비율 **2구간 누적**이고 폭비 0.6693 vs 값비 0.6695(차 0.0002 — flex-grow
  기준0 분할이라 퍼센트 이중계산 오차가 안 생긴다), 가로스크롤 없음, 콘솔 에러 0.
- **다크모드 동시 확인**(toolbox 아이콘·라벨 textBorder 가 테마색을 따라간다). 옛 주석 1줄 정정:
  도넛 폐지 때 적은 "이 페이지는 이제 ECharts 를 쓰지 않는다" 는 같은 날 버블 도입으로 사실과 반대가 됐다.
- **다음**: 라이브 배포는 폰 Termux 번들(이 PC 는 push 차단). 배포 후 `public_exports/manifest.json`
  `build_id` 로 확인.

**Recent (2026-09-14b, value_verified 화면 배지 — owner 발주(직접 지시, UH-25), 커밋만·라이브 미배포):**
- **배경: 같은 날 jp 게이트에 `JP_ESR_UNVERIFIED_VALUE` 가 배선됐지만(T&D 222% 출처가 목록
  페이지였던 사고 후속) 화면은 여전히 "검증 못 함"과 "검증 통과"가 같은 모양이었다.** publishing
  과 계약된 `value_verified:{state,reason}`(state: verified/unverified/exempt, ratio_only 회사의
  ESR 축처럼 이 축 대상이 아니면 null)을 렌더하는 게 이번 라운드 — **오늘 실 마스터엔 이 필드가
  아직 없다**(16사 전부 verified 가 됐을 미래 상태), 그래서 스크래치패드 fixture(원본 `jp/jesr_esr.json`·
  `jp/jesr_detail.json` 을 복사해 값만 주입, 실 마스터 무수정)로 verified/unverified/exempt/필드없음
  4갈래를 전부 실렌더 확인했다.
- **caveat-badge(같은 날 손해율 라운드에서 신설, "값은 검증됐지만 단순비교 주의")와 성격이 다르므로
  같은 배지 "언어"(작은 표식+title 툴팁, 색만으로 구분 안 함)를 쓰되 실루엣을 확실히 다르게 했다.**
  `.caveat-badge`는 둥근 pill(얇은 테두리, 균일 배경색) — 새 `.verify-badge`는 아이콘칩(굵은
  2px 테두리 + 채워진 머리글자 블록 `.vb-ic`/라벨 `.vb-tx` 두 부분 구조)으로 실루엣 자체가 다르다.
  unverified=주황(`?` "値 未検証"), exempt=파랑(`免` "確認対象外"), verified/null 은 배지 자체를
  렌더하지 않는다(jesr_app.js `verifyBadgeHtml()`/`VERIFY_META`, jp/index.html 은 §5.2 관례대로
  DOM 버전 `makeVerifyBadge()`로 파일별 복사). `reason` 은 publishing 문자열 그대로 배지 `title` 에
  노출 — designer 가 다시 쓰지 않음.
- **「根拠資料 ↗」 링크는 지우지 않고 옆에 사실을 붙였다.** `renderMeta()`(jesr_app.js, 3페이지
  공통 metaLine)에서 `state!=='verified'` 면 verify-badge 를 링크 바로 뒤에 병기 + 앵커
  `aria-label` 에도 "（値 未検証）"/"（確認対象外）" 를 덧붙여 스크린리더에서도 "여기가 근거다"라는
  단독 약속이 안 남게 했다. 링크가 없는 회사(`source_url` null)도 배지는 그대로 뜬다.
  실측(T&D Holdings 실데이터 222%를 fixture 에서 unverified 로 재현 — 실제 09-13 사고 케이스):
  aria-label = "T&Dホールディングスの根拠資料、別タブで開く（値 未検証）", 배지 title 에
  publishing reason 전문 노출 확인.
  **적용 3곳(owner 지시): 값 옆(=caveat-badge 와 동일 위치 관례)** — ① jesr.html ESR 헤드라인
  카드(`cardEsr`, `renderHeadline()`이 `cardPrelim` 슬롯에 速報배지와 나란히 병기) ② jgaap.html
  上段KPI 合算率 카드(ratio_only 전용 카드, `renderJgaapCards()`) + 収益性指標 合算率 카드
  (`renderProfitability()`→`ratioCard()`, caveat-badge 와 같은 자리에 이어붙임) ③
  jp/index.html ESRランキング 리스트 행 + 損害率一覧 리스트 행(둘 다 `.li-name`, caveat-badge 와
  동일 위치 관례). 그 밖에(当期純利益 등 손익 라인아이템, 감응도 표 등) 추가하지 않음 — 계약이
  "posted record/company record 단위" 라 헤드라인성 지표(ESR·合算率)로 스코프를 한정, 근거는
  이 파일 답변에 기록.
- **함정 선제 대응(모바일): caveat+verify 두 배지가 한 회사에 동시에 뜰 수 있다** (예:
  MS&AD/토어재보험처럼 이미 ratio_caveat 가 있는 회사가 value_verified 도 unverified/exempt 인
  경우) — 같은 날 오전 라운드가 겪은 "칩이 회사명을 밀어낸다" 재발을 막기 위해 `#lossRatioList`
  전용이던 모바일 折り返し 규칙을 `.verify-badge` 까지 확장하고 **`#esrListLife`/`#esrListNonlife`
  에도 선제로 같은 규칙을 걸었다**(ESRランキング은 기존에 速報/単体詳細 chip 이 행당 ≤1개라 문제가
  없었지만, verify-badge 가 chip 과 동시에 뜨면 다시 2개가 되므로). 실측(fixture 로 T&D 에
  `preliminary:true` 를 임시로 얹어 速報chip+verify-badge 2배지 스트레스 테스트, msad_holdings/
  toa_re 에 caveat+verify 2배지 스트레스 테스트): 375px 에서 `.li-nm` 폭 137px 유지(오전 라운드가
  고친 71.5px 붕괴 재발 없음), 어느 조합도 `body.scrollWidth>innerWidth` 0건.
- **A11y**: `a11y_contrast_check.py` 실측 — unverified 글자#7c2d12/배경#fff7ed 8.83:1, 아이콘
  흰글자/배경#c2410c 5.18:1, exempt 글자#1e3a8a/배경#eff6ff 9.52:1, 아이콘 흰글자/배경#1d4ed8
  6.70:1 — 전부 AA(4.5:1) 통과. `cbcheck`: unverified↔exempt 아이콘색 delta-RGB 212(protan)/220
  (deutan), unverified↔caveat 기존 amber(#f59e0b) delta 95+ — 전부 안전선(60) 상회, 게다가
  아이콘 머리글자(?/免)+라벨 문구+아이콘칩 실루엣 자체가 이미 달라 색만으로 구분하지 않음(스킬
  §3-4 fully-additive 판정). `.vb-ic` 는 `aria-hidden`(장식 글리프, 바로 옆 `.vb-tx` 가 같은 뜻을
  텍스트로 이미 담음). 다크모드(`color-scheme:dark` viewport)에서 배지 고정 hex 색 유지 확인
  (`.prelim-badge`/`.repro-badge`/`.caveat-badge` 와 동일한 "테마 비의존 고정색" 기존 컨벤션 유지,
  Playwright computed-style 로 라이트/다크 동일 rgb 확인).
- **검증**: `node --check` jesr_app.js + index.html 인라인 스크립트 2블록 전부 통과. 4 HTML
  html.parser 태그균형 0 오류·BOM 0(3 파일: index.html/jesr_app.js/jp.css 만 수정, jesr.html/
  jgaap.html/disclosure.html 은 공유 스크립트·CSS 변경만으로 무수정). 로컬 `http.server`(스크래치
  패드 사본 — 저장소 루트를 복사해 `common.css`/`theme.js` 404 안 나게, 포트 8931) +
  Playwright(`/opt/pw-browsers/chromium-1194`)로 데스크톱 1280px·모바일 375px 다수 실측:
  ESRランキング(T&D=unverified, 東京海上HD=exempt, SOMPO=명시적 verified→배지 없음, かんぽ=필드
  자체 없음→배지 없음 확인) · 損害率一覧(au損保=unverified, SBI損保=unverified, MS&AD/トーア=
  caveat+verify 동시 렌더, 三井住友海上=exempt) · jesr.html 헤드라인 카드+메타라인 링크(au_nonlife
  실 자본층 데이터로 unverified, mitsui_sumitomo 로 exempt, T&D/東京海上HD/SOMPO/かんぽ 4종
  headline-only 경로) · jgaap.html 上段KPI+収益性指標 카드(msad_holdings/toa_re 2배지 동시,
  au_nonlife 단독) · disclosure.html metaLine(3페이지 공유 확인). 전 케이스
  `body.scrollWidth<=innerWidth`(가로스크롤 0), `pageerror` 콘솔 0(외부 CDN 연결실패만 — 개발망
  차단, 기존 패턴, 코드와 무관). fixture·검증 스크립트는 스크래치패드에만 존재, `jp/*.json` 실
  마스터·`J-ESR/`·census·tests·docs/postmortems 전부 무수정, commit/push 없음.
- **손대지 않음(소유권 경계)**: `jp/jesr_esr.json`·`jp/jesr_detail.json`·`J-ESR/`·`scripts/`·
  `TODO_jp.md`·census·한국 자산(`index.html`·`K-ICS.html`·`IFRS17.html`·`공시보고서.html`) 전부
  무수정. `jesr.html`/`jgaap.html`/`disclosure.html` 자체 HTML도 무수정(공유 스크립트/CSS 변경만
  으로 3페이지 모두에 반영되는 구조라 손 댈 필요가 없었다).
- **모델·소요**: Claude Sonnet 5, 단일 세션 약 1시간(탐색+구현+fixture 3종+Playwright 4라운드
  검증 포함).


## 🔴 Open — P1

### BS-TACCOUNT — IFRS17.html Panel 1 (was Panel 7) 재무상태표 (formerly BS-DRILLDOWN, renamed 2026-08-14d)
Now a T-account at the **top** of the dashboard (owner's own explicit ask this round — `inbox/designer/20260814T1250Z__owner__IFRS17__bs_taccount_top_panel.md`, answered), not a mockup panel anymore in intent. Data-contract-driven by `섹션`/`레벨` fields on `IFRS17_BS.json` (parser landing separately, `inbox/parser/20260814T1250Z…`) — no item-number branching in the render code.
- [x] **T-account + reposition (2026-08-14d)**: moved above Panel "2) CSM 이동" (was 7, all panels renumbered 1-7). 좌 자산 / 우상단 부채 / 우하단 자본, right-column height ∝ value ratio. Per-zone `+` (`.subtoggle`, reused from the PL panel) toggles a 레벨2 detail list; disabled+`aria-disabled`+"세부 미공시" when a section has zero 레벨2 rows (covers both "parser hasn't landed detail yet" and "company doesn't disclose" with the same code path — no special-casing needed). 준비금 kept structurally separate from 자본 (own side-note block, excluded from the capital total/detail) per owner's explicit double-counting warning.
- [x] `EQ_SECTION_LEVEL_BRIDGE` bridges the *current* pre-migration schema (items 1-7, no 섹션/레벨 columns yet) so the frame renders today; disappears in effect the moment parser's real columns land (row data wins over the bridge automatically, zero HTML changes needed).
- [x] **This time actually deleted** (not hidden) the 08-14b/c dead L2/L3 functions — preserved-uncalled twice already, proven unreusable both times because the schema kept moving under them. History is in the changelog, not in commented-out code.
- [x] Verified 4 companies incl. all 3 of owner's named edge cases (has-detail / listed-no-detail-yet / non-listed-never-has-detail / zero-BS-data). 0 console errors. `pytest tests/test_deploy_assets.py` 10/10.
- [x] **Real-viewport recheck (2026-08-18, resolved after 3 carried-over sessions)**: this session's Browser pane returned a real `window.innerWidth===375` (not the `0` bug from 08-14b/c/d) — confirmed via `resize_window`+JS query: `.bs-t` switches to `flex-direction:column`, detail/sub rows collapse to 1 grid column, `body.scrollWidth` never exceeds `innerWidth` (no horizontal overflow), 0 console errors. Screenshot pixels still unavailable (pane still doesn't composite for actual frame capture), but this is real DOM/computed-style verification, not a skip.
- [x] **Schema landed same session** (owner shrank scope to 13 detail items, not the original ~60 — `inbox/_resolved/20260815T0100Z__parser__MULTI__ifrs17bs_taccount_schema_ready.md`): confirmed compatible with zero HTML changes (contract design worked as intended). Data shape + render-code field matching verified by direct inspection (`fetch(...,{cache:'no-store'})` vs. `renderBsZone`); a true fresh-browser render wasn't achieved that session — local server's HTTP cache kept serving the pre-migration snapshot. **2026-08-18: confirmed live** — 자산/부채/자본 `+` all enable and render real rows for KR0008 (Tier-1), verified via `.click()` + `box.hidden`/`getComputedStyle(...).display` in a clean preview.
- [x] **Partial-detail confusion fixed (2026-08-15, inbox `20260814T1710Z__validation__IFRS17__bs_detail_is_highlight_label_it.md`)**: validation caught that the 레벨2 detail is an intentional "≤15-line highlight" (owner scope, not full closure — `scripts/build_ifrs17_bs.py`), so a section's shown detail routinely undershoots its total (worst case validation found: 신한라이프 자산 세부 17-21조 vs 59조+ total) with zero on-screen explanation — reads as broken. Fixed by computing a "기타·미표시" residual row client-side (`total − Σshown`, no master change) plus a short caption clause. Re-verified on the exact worst-case company (신한라이프/KR0094): shown-detail + residual now ties out to the total within rounding.
- [x] **🔴 `+` toggle dead-on-arrival bug fixed (2026-08-18, owner live-QA `inbox/designer/20260818T0026Z` D-3)**: `.bs-l2-rows{display:flex}` was beating the UA `[hidden]{display:none}` default in cascade, so `box.hidden` toggling never changed the rendered layout — the button looked completely dead (aria-expanded flipped, screen didn't). Fixed with one CSS rule, `.bs-l2-rows[hidden]{display:none}`. Audited all 4 HTML pages for the same display+hidden collision pattern — none found elsewhere (K-ICS/index/공시보고서 don't use the `hidden` attribute at all; the PL 재보험 subrow toggle uses `style.display`, unaffected).
- [x] **법정준비금 재배치 (2026-08-18, D-4)**: moved from a standalone `#bsReserveNote` block (deleted, along with its render code + CSS) into the 자본 zone's own detail list, as indented sub-rows anchored right after the "이익잉여금" row (name-matched, not item-number — new `renderReserveSubrows()`). Still excluded from the shown/residual sum (rendered via a separate pass, owner's double-counting warning preserved) — verified on KR0008 the residual stayed a small △81억 (not off by the ~6.95조 it would be if reserves had leaked into the sum). Companies without an 이익잉여금 row (non-listed) get the sub-rows inserted before the residual row instead.
- [x] **버그 수정(같은 대화, owner 즉시 재확인): 연도모드 "직전 3년" 위반** — 재사용한 `selectPeriods()`가 무상한(전체 4Q) 반환이라 BS가 2021년까지 있는 회사(메리츠화재·현대해상·KB손보·코리안리 등)에서 6열까지 붙었음. BS 전용 `eqYearPeriods()`(최신+직전3개년말 하드캡, `wfYearBuckets()`와 동일 패턴) 신설로 교체, 공유 함수는 미변경(CSM/PL/NB 마스터는 실측상 전부 2023년 시작이라 이 결함이 잠재적일 뿐 미발현 — 확인만 하고 안 건드림). 6개사 전부 재검증 완료.
- [x] **시계열 원천 테이블 신설 (2026-08-19, owner 채팅 발주)**: T자 밑에 다분기(`#wfPeriod` 연동, `selectPeriods` 재사용) 표 추가 — 분기=직전5분기 / 연도=최신+직전3개년말, 분기 미제공사는 CSM 패널과 동일 문구의 stub. 자산/부채/자본[+] → 세부[+] → 자본 세부의 "이익잉여금"은 자체 중첩 [+]로 법정준비금(이제 4항목 — `보증준비금 기적립액` 신규, 생보 16사만) 한 겹 더. 항목은 선택 기간 전체의 이름 유니온(`eqUnionNames`)이라 항목번호 하드코딩 없음. 상위 토글 접을 때 중첩 하위 토글도 재귀 리셋(`collapseGroup`). `renderBsTable`/`buildBsTableDom`/`eqHasQuarterly`/`eqUnionNames`/`eqValByName` 신설. 브라우저 실측 다수(연도/분기 헤더 owner 예시와 정확 일치, 생보/손보 준비금 항목수 차이 확인, stub 전환, zero-BS-data 회사 무충돌, 375px 표 자체 스크롤). `pytest` 10/10.
- [x] **(종결 2026-08-20)** Deploy 차단 해소 — 게이트 `RED=0 YELLOW=276 exit=0`, main 배포 실제로 진행됨(`a0979b9`, 오늘만 3회). 원문: (unrelated to this rebuild, standing condition). No push attempted.

### DIVIDEND-PAGE — 공시보고서.html 배당현황 (built 2026-08-15)
Owner's C-4 chain, designer leg (`inbox/_resolved/20260814T2230Z__parser__MULTI__dividend_json_ready_for_gongsi_page.md`). Fills the page's long-standing "준비 중" shell — no new tab/page, per owner's explicit constraint.
- [x] Company selector (24-company registry, drawn from `dividend.json` itself, not the 39-company kics universe — the 15 non-listed companies structurally never have this DART disclosure, so they're left out of the picker rather than showing a permanent empty stub) + KPI strip + company-level table (항목 1-7) + per-종류주 mini-tables (항목 8-10, auto-detected classes, no hardcoded company list).
- [x] `0` vs `"정보없음"` kept strictly separate everywhere (owner's own repeatedly-flagged trap) — verified on real data, not just written and assumed.
- [x] `claude-agent-designer.md` §1 doc-table gap fixed (my half of `test_docs_agree_with_what_pages_fetch`).
- [x] **(종결 2026-08-20)** `dividend.json`은 **git 추적 중**이고(`git ls-files` 확인) 2026.2Q 24사까지 배포됐다. 'untracked·deploy far off' 전제 stale. 원문:, `claude-agent-publishing.md` doesn't mention it yet, and `validate_data_contract.py` doesn't wire this master into its gate at all — all three already ticketed in `inbox/publishing/20260814T2230Z` (P-1/P-2/P-4), not this stage's files to touch.
- [x] **Period selector added (2026-08-18, owner live-QA `inbox/_resolved/20260818T0026Z` D-5)**: the "shows all 14 raw quarters" gap above is closed — added a K-ICS.html-style 기간(분기/연도) toggle. Quarter mode = last 5 quarters, year mode = latest + prior 3 fiscal year-ends (partial current year labeled "…누계", e.g. "2026.2Q누계"), both derived from `dividend.json`'s own data (`GLOBAL_QUARTERS`), not hardcoded. Window is **global** (same header columns regardless of which company is selected), not per-company — deliberate, so a company's missing quarter shows as a 정보없음 cell under a stable header rather than shifting the whole column set. Also removed 항목1 주당액면가액 (owner: "필요없으니까 빼고"). KPI strip decision: stays anchored to "latest 4Q" regardless of the new period selector (a multi-quarter window doesn't map to a single KPI snapshot) — documented in `#divKpiCap`'s caption per owner's explicit ask to decide-and-state. Verified live on KR0008: quarter headers 2025.2Q~2026.2Q, year headers 2023/2024/2025/2026.2Q누계, `0`-vs-정보없음 distinction intact (현금배당금총액 real 0 for 3 quarters vs 정보없음 for the undisclosed 2026.2Q cell), 0 console errors, 375px no horizontal overflow.
- [x] Real-viewport mobile recheck done for this page too (2026-08-18, same session as BS-TACCOUNT above) — `resize_window`+JS query confirmed `.controls` wraps, period selector visible, no horizontal overflow at 375px.

### KEYCOLOR-V1 — 회사 키컬러 액센트 시스템 ~~(K-ICS 취소, IFRS17 재검토 대기)~~
IFRS17 적용 완료 2026-06-13. K-ICS 적용은 **owner가 2026-06-17 취소** (IFRS17 구현 불만족). IFRS17 키컬러도 재검토 필요 — owner 피드백 대기.
- [x] IFRS17 적용 완료 (2026-06-13)
- [~] K-ICS 적용: **owner 취소 (2026-06-17)**
- [ ] (보류) 전체 키컬러 방향 재검토 — owner 피드백 후

### DESIGN-V2 — de-AI 디자인 오버홀 (proposal delivered 2026-06-11, awaiting owner sign-off)
Owner complaint: site looks AI-generated. Audit done (4 pages + barabom.me reference — actual findings: Spoqa Han Sans Neo webfont + restrained neutrals + 0.1-0.2s micro transitions, NOT heavy animation). Phases:
- [~] **P1 quick wins** — **3/4 이미 배포돼 있다 (2026-08-30 `origin/main` 실측)**: Pretendard 4페이지+common.css 전부 적용 · `tabular-nums` 적용 · `rel="icon"` 4페이지 전부 존재. **남은 것은 둘뿐** — 부트스트랩 잔재 색(`#0d6efd`·`#f8f9fa`)이 4페이지+common.css 에 아직 있고, `og:image` 는 0건이다. 종전 문구 —: Pretendard Variable + `font-variant-numeric:tabular-nums` 전역 / 탈부트스트랩 팔레트(#0d6efd·#f8f9fa 교체, 잉크+페이퍼+딥블루 1액센트) / favicon(IQ 모노그램)+OG+meta description / footer(출처·기준분기·면책) / 이모지 placeholder 제거 / radius 12→6px / Chart.js·ECharts 색 CSS 변수화 (기본 teal/pink 퇴출). [부분 착수: P1-QUICKWIN 일부 done 2026-06-12, 팔레트 교체는 보류]
- [x] **P2 structural (1~2d)**: ✅ common.css · ✅ index 히어로 KPI 스트립+typeahead · ✅ scroll-reveal · ✅ 차트 공통 테마 · ✅ KPI 카운트업 애니(index 3개+IFRS17 Panel7 4개, ease-out 600ms, 2026-06-20) — **완료**
- [x] **P3 — 문서가 낡아 있었다(2026-09-19 정정, 이 트리에서 직접 확인).** 다크모드는 이미 구현돼 있다:
  `theme.js` L93-94 가 `id='iqThemeToggle'` · `class='theme-toggle'` 버튼을 **런타임에 주입**한다(그래서
  HTML 을 grep 하면 0건 — 없는 게 아니라 JS 가 만든다). `common.css` 에 `:root[data-theme="dark"]` 토큰
  (L76)·`@media (prefers-color-scheme:dark)`(L85)·`.theme-toggle` 스타일(L151·L160)이 전부 있고,
  OS 자동감지가 아니라 사용자가 누르는 토글 + localStorage 고정이다. "M3 잔여(도넛 stack·범례) 흡수" 도
  아래 M3 절에서 이미 둘 다 [x] — P3 는 사실상 완료다.
- [x] **TREEMAP-SCALE**: 트리맵 색 임계 앵커 130/200% + 범례 임계 표기 — done 2026-06-13 (권고선=130%, 민감도 패널 150%→130% 정합)
- [ ] **COMPANY-ACCENT**: 회사 키컬러는 배경 틴트 대신 "액센트 1곳" 원칙(패널 제목 2px 룰 + 회사명 칩 + 차트 주 시리즈, 저채도 변형 23사 맵) — 시안 owner 승인 후

## 🟠 Open — P2

### MOB-KICS — K-ICS.html full mobile layout (scope confirmed by owner 2026-06-12)
Owner confirmed scope: **full-panel mobile pass + alternative render** (not foundation-only). M1 foundation already in place (header/tabs/table scroll, chart heights ↓).
- [x] Donuts stacked vertically — `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap`으로 375px에서 자동 1열 스택. 이미 구현됨 (2026-06-17 확인).
- [x] Forward-chart legend reposition — `position: window.innerWidth < 640 ? "bottom" : "top"` (2026-06-17)
- [x] Dense table → card view (가/나/다 sub-items) — `renderMobileCards` ≤640px (2026-06-20)
- [ ] **(owner open rec 1)** horizontal-scroll range for dense panels — decide which panels scroll vs reflow
- [ ] **(owner open rec 2)** breakpoint set — confirm thresholds beyond the single 640px (e.g. <400px sub-query)

### MOB-IFRS17 — IFRS17.html full mobile layout (scope confirmed by owner 2026-06-12)
Owner confirmed scope: **full-panel mobile pass + alternative render**. M1 foundation only so far.
- [ ] Panel 1–6 mobile policy: which to keep, which to collapse, which to swap for alternate viz
- [x] **Panel 7 (BS-DRILLDOWN) 모바일 실측 — 문서가 낡아 있었다(2026-09-19 정정).** 같은 사실이 두 티켓에
  다른 상태로 남아 있었다: 위 **BS-TACCOUNT 티켓 L208** 에 2026-08-18 real-viewport recheck 기록이
  이미 있다(`window.innerWidth===375` 실측, `.bs-t` 가 `flex-direction:column` 으로 전환, 세부·하위 행이
  1열로 접힘, `body.scrollWidth` 가 `innerWidth` 를 안 넘음 = 가로 넘침 0, 콘솔 오류 0). 이 티켓에만
  반영이 안 됐던 것이다. 코드 변경 없음, 체크박스만 정정.
- [ ] **(owner open rec 1)** horizontal-scroll range for dense panels
- [ ] **(owner open rec 2)** breakpoint set confirmation
- (shares the two owner open recs with MOB-KICS — resolve once for both pages.)

### VIS-DONUT — K-ICS donut row stacks on phones ✅ 완료
- [x] `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap` → 375px 화면에서 자동 1열 스택. 명시적 flex-direction:column 불필요. 이미 구현됨 (2026-06-17 확인).
- [x] Labels legible: 각 도넛이 전체 너비 차지, 레이블 공간 충분.

### VIS-CHARTLEGEND — chart legend/axis density on mobile
- [x] K-ICS forward + IFRS17 hist/NB legend → bottom on mobile (`window.innerWidth < 640`) (2026-06-17)
- [ ] IFRS17 amort + index bubble legend (amort display:false OK, bubble ECharts top=8 review later)

### M3 — chart fine-tuning (roll-up of VIS-DONUT + VIS-CHARTLEGEND + misc)
- [x] K-ICS 도넛 2개 세로배치 (= VIS-DONUT) — 이미 구현됨
- [x] Forward 라인 범례 위치 (= VIS-CHARTLEGEND) — done 2026-06-17
- [ ] 차트 미세조정 across pages

### Panel 7 — 원천지표 카드 ✅ 완료 (2026-06-17)
IFRS17.html 대시보드 최상단에 4-card KPI strip 추가(기말 CSM 잔액·CSM 상각·신계약 CSM·NB CSM 배수). `wfVal(company,latestQ,6/5/2)` + `ix.nbm` 기반. 2열 모바일 그리드.

### INDEX-BUBBLE-V2 HTML side — 4축 bubble rendering
Publishing ships the data (`TODO_publishing.md` INDEX-BUBBLE-V2). Designer ships the ECharts spec:
- [x] **🚫 폐기 — 재착수 금지 (2026-08-20 확인)**. 4축 V2는 owner가 폐기했고 **3축이 이미 라이브 완결**이다: `index.html` L165 *"X: 신계약 CSM 규모 · Y: NB CSM 배수 · 크기: 기말 CSM 잔액"*. 이 줄을 열린 항목으로 두면 다음 세션이 완결된 기능을 다시 만든다. 원문:
- [x] **Mobile rendering — 문서가 낡아 있었다(2026-09-19 정정, 이 트리에서 직접 확인).** 이미 구현돼 있다:
  `index.html` L83 `#bubble-list{display:none}`(데스크톱) + 모바일 폭에서 노출, L107-108 에 행 레이아웃
  CSS, L1363 에 행 클릭 핸들러. 버블맵 대신 리스트로 떨어지는 대체 렌더가 라이브다. 코드 변경 없음.
- [x] **Click → cross-nav — 문서가 낡아 있었다(2026-09-19 정정, 이 트리에서 직접 확인).** `index.html`
  L1125-1127 `bubbleChart.on('click', ...)` → `window.location.href='IFRS17.html?company='+encodeURIComponent(...)`.
  모바일 리스트 행도 같은 이동(L1363), 상단 typeahead 도 같은 패턴(L446). 코드 변경 없음.

### F17 Panel 3 — Tier2 LOB drill-down rendering (when publishing ships Tier2 JSON)
Publishing currently has Tier1 4-bar in production. Tier2 (LOB 장기/자동차/일반 stacked) waits on parser F17 decision + publishing assembly.
- [ ] Stacked bar / waterfall design (손보만, LOB visible)
- [ ] 생보 alt-rendering (장기 전사 fallback)
- [ ] Caption variant per-company taxonomy (장기/자동차/일반 vs 보장성/물보험/저축성)

## ✅ Done (archive)
완결 항목 25+개(2026-05-28~06-14) — M1 모바일 foundation, KEYCOLOR/TREEMAP-SCALE, △(세모) 전면화, 생명장기·시장위험액 토글, PL/CSM 워터폴 패널, HTML single-source refactor, dead-CDN 제거 등. 상세는 `docs/changelog_designer.md`(당시 `(changelog MM-DD)`로 인덱싱) + git log.


## 🗂️ Conventions reference

**Responsive breakpoints**
- M1 foundation: `@media (max-width:640px)` on all 4 pages. Header/tabs/chart heights/table scroll.
- M2: index.html ≤640px swaps treemap → vertical list (`renderList()` mirrors `render()`).
- M3: donut stack + legend reposition + chart fine-tuning.

**Chart libraries (committed)**
- Chart.js: IFRS17 Panels 2–6
- ECharts: Panel 1 (CSM waterfall), index treemap, bubble

**Page roster (root single-source since 2026-05-28)**
- `index.html` — market map + IFRS17 quadrant + bubble
- `K-ICS.html` — per-insurer detail + sub-items + forward outlook
- `IFRS17.html` — 7-panel dashboard (1=BS T-account, 2-7=CSM/PL/NB/sensitivity)
- `공시보고서.html` — 배당현황 (per-company dividend disclosure, filled in 2026-08-15; was a static "coming soon" shell before)

**Local preview:** `python -m http.server 8000` from repo root. (preview_eval 반복 행 시 Edge headless `--dump-dom` 대체; 좀비 포트 회피로 현재 8889.)

## Reading order for designer subagent
1. This file (`TODO_designer.md`) — current state (changelog is deferred: [`docs/changelog_designer.md`](docs/changelog_designer.md) is history, open only when you need a past decision's background)
2. [`docs/agents/claude-agent-designer.md`](docs/agents/claude-agent-designer.md)
3. Root HTML page(s) in scope
4. Master JSON schema (publishing's output) for the panel you touch — read-only
5. Root [`TODO.md`](TODO.md) for cross-stage roadmap notes

## Hand-off
- **From publishing**: notification that a master JSON changed (`manual_html_edit` warn) or that a new field needs rendering.
- **To human**: designer never pushes. Hand off to publishing for the commit message + push recommendation.
