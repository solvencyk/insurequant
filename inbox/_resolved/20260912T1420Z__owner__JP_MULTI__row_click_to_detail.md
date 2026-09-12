---
from: owner
to: designer
created: 20260912T1420Z
status: resolved
route: html
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T1330Z
---

## 미결 (owner) — `/jp/` 랭킹 막대 행 클릭 → `jesr.html` 이동, 상세 없는 회사는 기본 페이지(「追って公表予定」)

**owner 2026-09-12 지적.** "index.html 어디를 눌러도 상세로 못 간다. 막대 목록을 누르면 jesr.html 로 넘어가게 하고, 세부공시 없는 회사는
'추후 공시 예정' 기본 페이지를 남겨라." 루트 index.html 의 `.li-row` 클릭 → `K-ICS.html?company=` 관례와 동일.

**할 일.**
1. `jp/index.html`: 랭킹 리스트 `.li-row` 전부(13사)에 클릭/Enter/Space → `jesr.html?company=<key>` 이동(루트 877~948행 `goToDetailRow` 패턴:
   `role="link"`, `tabindex=0`, `cursor:pointer`, `:active`). key = `jesr_detail.json` 에 있으면 그 `id`, 없으면 `company_jp` 를 `encodeURIComponent`.
   一覧表 회사명 링크도 같은 규칙으로 전 회사에 건다.
2. `jp/jesr.html`: `jesr_esr.json`(13사 헤드라인)과 `jesr_detail.json`(2사 상세)을 둘 다 읽어 드롭다운은 **헤드라인 13사 + 상세만 있는 회사(明治安田損保)**
   = 14사, 정렬은 index 와 같은 2단 버킷·ESR desc(상세만 있는 회사는 뒤에). `?company=` 는 id 또는 company_jp(URL 디코드) 둘 다 해석.
   - 상세 있음(2사): 지금 화면 그대로.
   - 상세 없음(11사): 회사 선택·基準時点 줄·헤드라인 카드(ESR 색 규칙, 적격/소요자본은 「—」)·範囲·公表日 링크(jesr_esr 의 source_url) 만 표시하고, 그 아래
     안내 패널 1개: 「規制様式(告示)に基づく詳細開示は、2026年10月末までに順次追加する予定です。現在は決算説明資料等の速報値のみ掲載しています。」
     + 速報 배지(preliminary 면). 다른 패널(適格資本の構成·所要資本の内訳·市場リスク·感応度·損益·その他)은 렌더하지 않음(빈 패널 금지).
   - 존재하지 않는 key 면 「該当する会社がありません」 + 드롭다운으로 유도.
3. hreflang/canonical/noindex/GA/오류제보 팝업은 기존 그대로. 데이터 JSON·CSS 공유 파일 수정 금지.

**검증·시간 규칙(중요).** 이 라운드는 **25분 안에** 끝낸다: 로컬 서버에서 (a) index 의 au 행 클릭 → jesr.html?company=au_nonlife 로 이동, (b) 상세 없는
회사(예: ライフネット) 행 클릭 → 기본 페이지 렌더, (c) 드롭다운 14사, (d) 콘솔 에러 0(CDN 차단 제외) 를 **DOM/URL 로 확인**하면 끝. echarts 로컬 사본
시각 검증은 하지 않는다(이번 변경은 차트 무관). 스크린샷은 기본 페이지 모바일 1장만(`artifacts/designer/jesr_jp_placeholder_mobile_20260912.png`).
띄운 http.server 는 끝나기 전에 반드시 종료(프로세스 kill 확인). 서브에이전트 금지, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 줄바꿈 보존, 커밋 금지.
끝나면 답변란 요약, `status: answered`, `TODO_jp.md`(Status 5개 유지)·`docs/changelog_jp.md` 한 항목. 보고문 일본어 문자 금지.

## 종결 재확인 (orchestrator 2026-09-12)

28분 초과로 에이전트 종료 후 orchestrator 가 Playwright DOM 검증: 리스트 행 9개 전부 role=link, LifeNet 행 클릭 → jesr.html?company=<company_jp> 기본 페이지(順次追加 안내·헤드라인 카드), 드롭다운 14사, au 상세 전 패널 정상, 미존재 key 안내, pageerror 0. 서버 종료 확인.

status: **resolved**
