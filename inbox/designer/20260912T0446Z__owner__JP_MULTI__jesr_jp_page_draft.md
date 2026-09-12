---
from: owner
to: designer
created: 20260912T0446Z
status: answered
route: html
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260624T0337Z
---

## 미결 (owner) — `/jp/index.html` 일본 ESR 페이지 **초안** (일본어 UI, 15사 값 + 79사 커버리지) [J-ESR 킥오프 2차 조각]

**배경.** owner 2026-09-12 결정: 접속지(IP) 차등이나 `.co.jp` 도메인 대신 **같은 사이트 안 `/jp/` 경로**에 일본어 페이지를
둔다(나중에 `jp.insurequant.com` 승격 가능). 2026-07-21 revert 된 `J-ESR/index.html` MVP 와는 별개로 새로 만든다
(그 revert 는 "데이터가 그룹값뿐" 이 이유였고, 지금은 79사 census + 15사 확정값이 있다).
데이터는 publishing 이 같은 시각 발주로 만드는 **`jp/jesr_esr.json`** (스키마는 아래, 파일이 아직 없으면 스키마대로 임시
fixture 를 `jp/_fixture_jesr_esr.json` 에 만들어 개발하고, 진짜 파일이 생기면 그걸로 바꿔 확인 후 fixture 삭제).

**산출물.** `jp/index.html` 하나(+ 필요하면 `jp/jp.css` 소량). **루트 `index.html` 등 기존 4개 페이지는 이번 라운드에
수정 금지** — 대신 답변란에 "루트 index.html 에 넣어야 할 것"(hreflang 링크 2줄, 상단 언어 전환 링크, 일본어 브라우저 안내 띠)
을 코드 조각으로 적어라. 라이브 배포는 owner 가 초안을 본 뒤 결정한다.

**데이터 계약 (`jp/jesr_esr.json`, 페이지는 `fetch('jesr_esr.json')` 상대경로).**
```json
{"_meta": {"as_of": "2026-03-31", "as_of_label_ja": "2026年3月31日", "generated_at": "...", "next_update": "2026-10-31",
           "census": {"total": 79, "posted": 15, "not_yet": 62, "not_found": 2}},
 "records": [{"company_jp": "...", "company_en": "...", "ticker": "8766"|null, "sector": "life"|"nonlife"|"reinsurance",
              "category": "...", "scope": "group"|"solo", "esr_pct": 238.0, "basis": "J-ICS", "as_of": "2026-03-31",
              "preliminary": false, "total_assets_bn_jpy": 319600|null, "target_pct": "190%+"|null,
              "doc_type": "...", "doc_date": "..."|null, "source_url": "https://...", "notes": "..."}]}
```

**화면 구성(초안, 위→아래).**
1. 헤더: 브랜드 InsureQuant + "日本 ESR ダッシュボード" + 언어 전환(`日本語 | 한국어`, 한국어는 `../index.html`).
   `<html lang="ja">`, `<link rel="alternate" hreflang="ko" href="https://www.insurequant.com/">` 과
   `hreflang="ja" href="https://www.insurequant.com/jp/"`, `x-default` = ko.
2. 상단 요약 카드 3개: 公表済み 15社 / 10月末公表予定 62社 / 未確認 2社 (분모 79社), `_meta.census` 에서.
   그 옆에 한 줄 안내: "各社の経済価値ベースのソルベンシー比率(ESR)は2026年10月末までに全社反映予定".
3. 메인 차트: **ESR 랭킹 가로 막대**(15사, esr_pct 내림차순). 색 = sector(life/nonlife/reinsurance) 3색,
   `scope==group` 은 막대에 빗금 패턴 + 범례 "グループ連結", `preliminary` 는 라벨 뒤 "速報" 배지. 툴팁에 회사명(일/영)·
   ESR·기준일·문서종류. 목표비율(`target_pct`) 있으면 막대 끝에 작은 마커. 회사명 라벨은 일본어, 좁은 화면에선 영문 약칭.
4. 커버리지 도넛(公表済み/予定/未確認) 1개 — 랭킹 옆 또는 아래.
5. 표: 会社名 / 業態 / 範囲(連結·単体) / ESR / 基準日 / 出所(문서종류, `source_url` 링크 새 창) / 備考(速報 등).
   정렬 가능 안 해도 됨.
6. 푸터: 出所 = 各社開示資料, "数値の権利は各開示主体に帰属", InsureQuant 표기, 한국 사이트 링크.

**규칙(designer 프롬프트 §4·§5 그대로 + 아래).**
- 데이터 HTML 인라인 금지(fetch 만). 루트 `common.css` 재사용(`../common.css`), 페이지 전용 스타일은 최소.
- CSP meta 는 루트 `index.html` 6행과 같은 형식(jsdelivr 만 허용) + ECharts 5.5.0 `integrity` SRI 는 루트 것과 동일 값 복사.
- 반응형(모바일 375px 에서 막대 라벨 안 잘리게), A11y(차트에 `aria-label` 요약 + 표가 대체 텍스트 역할).
- 음수는 없지만 숫자 포맷은 `238.0%` 한 자리 고정. 일본어 문구는 페이지 안에서만 쓰고, **답변·보고문에는 일본어를 넣지 말 것**.
- 검증: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m http.server 8896` 를 백그라운드로 띄워
  `http://localhost:8896/jp/` 를 브라우저 도구로 열어 콘솔 에러 0·차트 렌더·모바일 스크린샷 확인(회사망에서 localhost 는 문제없음).
  브라우저 도구가 행 걸리면 Edge headless `--dump-dom` 으로 대체(프롬프트의 preview 유의사항).
- 서브에이전트 생성 금지. 멀티라인 `python -c` 금지. 파일 UTF-8(BOM 없음).

끝나면 답변란에: 만든 파일 목록, 스크린샷 경로(데스크톱·모바일 각 1장, `artifacts/designer/` 아래), 루트 index.html 삽입 조각,
남은 판단거리(owner 결정 필요한 것만). `status: answered`.

## 답변 (designer, 2026-09-12)

### 산출물

- `jp/index.html` (신규, UTF-8 BOM 없음, 380행). fixture는 만들지 않았다 — 착수 시점에 이미
  publishing이 만든 진짜 `jp/jesr_esr.json`(79사 census, 15사 레코드)이 있었다
  (`ls jp/` 로 확인, `_meta.generated_at: 2026-09-12T05:01:24Z`). 이 파일은 읽기만 했고
  수정하지 않았다.
- 스크린샷 2장: `artifacts/designer/jesr_jp_draft_desktop_20260912.png`(1280px, full-page),
  `artifacts/designer/jesr_jp_draft_mobile_20260912.png`(375px, full-page).

### 화면 구성 — 티켓 6절 그대로 구현

헤더(브랜드+언어전환 `日本語|한국어`) → 공표상황 카드 3개+안내문+기준일 → ESR랭킹 가로막대
(15사, 내림차순, 색=업태 3색, 빗금=연결, 速報 배지, ▲목표마커, 범례) → 커버리지 도넛
→ 一覧表(7열) → 푸터. `../common.css` 재사용, 페이지 전용 스타일은 인라인 `<style>`
(다른 4개 배포 페이지와 같은 패턴이라 `jp/jp.css`는 만들지 않았다).

### 실데이터에서 발견해 방어 처리한 것 (스키마 예시엔 없던 것)

1. **`notes` 필드는 한국어 내부 검증 메모다** (예: "PDF p21-22 직접 열람 확인: 적격자본(A)=...").
   화면에 노출하지 않았다 — 備考 열은 `preliminary`→速報 배지, `basis`≠"J-ICS"→짧은 표식만
   보여준다. 공개용 비고가 따로 필요하면 publishing에 별도 필드 요청이 필요하다(owner 판단거리 1).
2. **`doc_type` 3건에 한국어 단어가 섞여 있었다**(au損害保険 "…업적데이터편…발행)", 明治安田損害保険
   "…게시)", SOMPOホールディングス "…VaR99.5%기준)"). 화면 표시 직전에만 한글 토큰을 제거하는
   `jaOnly()`를 넣어 방어했다(원본 JSON은 불변) — 표시 결과 확인:
   `ディスクロージャー誌(au損保の現状2026, 2026-07-30)`,
   `ディスクロージャー誌【別冊】業績データ(明治安田損害保険の現状2026, 2026-09-04)`,
   `決算説明資料(2026-05-20, VaR99.5%)`. 브라우저에서 `document.body`(script/style 제외) 전체를
   정규식 `[가-힣]+`로 스윕해 잔여 한글 0건 확인.
   근본 수정(doc_type에 한글이 안 섞이게)은 publishing 쪽 파이프라인 이슈라 이번 라운드에서
   JSON은 건드리지 않았다 — owner 판단거리 2.
3. **`basis`가 "J-ICS" 아닌 값**(SOMPOホールディングス만 `J-ICS_VaR99.5`)은 랭킹 차트가
   서로 다른 산정기준을 나란히 비교하는 셈이라, 차트 밑에 상시 캡션
   ("※ 算定基準(標準式・内部モデル・VaR水準等)は各社で異なる場合があり…")과 表 備考에
   `算定基準:VaR99.5` 표식을 추가했다. `basis` 접두사 `J-ICS_`를 떼는 일반식이라
   향후 다른 basis 값에도 하드코딩 없이 동작한다.
4. `doc_date`가 "2026-05-20" 외에 "2026-05"(일자 없음) 형식도 3건 있어 `jaDateFlexible()`이
   2-분절/3-분절 모두 처리하도록 만들었다(월-only는 "2026年5月"로 표시).
5. `_meta.built_from`(소스 CSV 목록)·`total_assets_bn_jpy`·`ticker`·`category`는 티켓 6절에
   화면 자리가 없어 노출하지 않았다(`category`만 회사명 셀의 `title` 툴팁으로 조용히 부가).

### 버그 2건 — 발견 즉시 직접 수정(발주 범위 밖이지만 명백+해결 쉬움)

- **도넛 라벨 겹침**: 未確認(2社)과 公表済み(15社) 슬라이스가 인접해 ECharts
  `avoidLabelOverlap`이 "公表済..."로 말줄임했다. 온차트 라벨을 끄고 옆 범례 텍스트에
  건수를 병기(`公表済み（15社）`)하는 쪽으로 바꿔 해결 — 정보 손실 없음(카드가 이미 숫자를
  더 크게 보여주고 있어 중복이었다).
- **모바일 헤더 줄바꿈**: 375px에서 "InsureQuant 日本 ESR ダッシュボード"+언어전환이 한 줄에
  안 들어가 2줄로 깨졌다. 루트 4개 페이지의 기존 관례(`.brand .hint{display:none}` at
  ≤640px)를 그대로 적용해 모바일에서 부제를 숨기는 것으로 해결.

### 검증 — 재현 명령과 실측

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m http.server 8896   # repo root, background
# 브라우저에서 http://localhost:8896/jp/ 열기
```

- **Claude Browser 도구**로 데스크톱 1280px·모바일 375px 둘 다 확인: 카드/차트/범례/캡션/도넛/
  표/푸터 렌더 확인, `body.scrollWidth`(375)`===innerWidth`(375) → 가로스크롤 0,
  표는 `.table-container` 안에서만 가로스크롤(의도대로, 出所/備考 도달 확인),
  `esrChart`/`covDonut`의 `aria-label`이 실제 수치로 채워짐 확인
  (예: "ESRランキング棒グラフ。全15社中、最高はau損害保険 791.7%、最低はソニー生命保険 162.0%…").
  이 도구 자체의 네트워크 샌드박스가 jsdelivr(외부 CDN)을 차단해서
  (`net::ERR_NETWORK_ACCESS_DENIED`, `curl`로는 동일 URL이 200으로 확인되므로 회사망 차단이
  아니라 이 브라우저 도구 특유의 제한 — TODO_designer.md 2026-09-11 항목과 같은 유의 현상),
  검증 목적으로만 echarts.min.js 로컬 사본을 임시로 만들어 차트 렌더를 확인한 뒤 즉시 삭제했다
  (`jp/index.html`은 처음부터 끝까지 CDN 경로만 가리키고 있고 변경한 적 없다).
- **Playwright(실네트워크, 진짜 배포 파일 그대로)**로 최종 검증: 위 스크린샷 2장을 이 경로로
  생성했고, `console` 이벤트 리스너로 데스크톱·모바일 둘 다 **콘솔 에러 0건**(Pretendard·ECharts
  CDN 포함 전부 정상 로드) 확인 — 이 결과가 실제 방문자 환경을 더 정확히 대표한다.
- 색상 대비/색맹 안전성은 `scripts/a11y_contrast_check.py`로 실측(눈대중 아님):
  업태 3색 life `#2f6fed`/nonlife `#f59e0b`/reinsurance `#0f766e` 는 상호 delta-RGB
  103~236(임계 60 이상, protan/deuteran 둘 다) · 도넛 3색 posted `#0d6efd`/scheduled `#f59e0b`/
  unconfirmed `#475569` 도 상호 123~255. `速報` 배지는 처음 흰 글자+amber 배경으로 짰다가
  2.15:1 FAIL 나와서 진한 텍스트(`#212529`)로 바꿔 7.18:1 통과시켰다.
- HTML 태그 균형 `html.parser`로 기계 검사(0 오류, EOF 스택 비어있음), BOM 없음, ECharts
  5.5.0/Pretendard `integrity` 값 루트 `index.html`과 byte-diff 0.
- A11y: `<main>`/`<section aria-labelledby>` 랜드마크, 표 `<th scope="col">`, 두 차트
  `role="img"`+데이터기반 `aria-label`, 소스링크 새 탭+`aria-label`(…別タブで開く), 언어전환
  한국어 텍스트에 `lang="ko"`, `:focus-visible`는 `common.css` 상속.

### 루트 `index.html`에 넣을 조각 (이번 라운드엔 적용 안 함 — 코드만)

**1) hreflang (canonical 바로 아래, 24-25행 근처, 자기참조 포함 3줄):**
```html
<link rel="alternate" hreflang="ko" href="https://www.insurequant.com/"/>
<link rel="alternate" hreflang="ja" href="https://www.insurequant.com/jp/"/>
<link rel="alternate" hreflang="x-default" href="https://www.insurequant.com/"/>
```

**2) 상단 언어 전환 링크 (`.header-row` 안, 다운로드 버튼 앞):**
```html
<a href="jp/index.html" class="jp-lang-link" style="align-self:center;font-size:12px;color:var(--muted);text-decoration:none;padding:4px 8px;border:1px solid var(--border);border-radius:var(--r-pill);white-space:nowrap">日本語</a>
```

**3) 일본어 브라우저 안내 띠 (`</header>` 바로 다음, `.container` 앞):**
```html
<div id="jpBanner" hidden style="background:var(--card);border-bottom:1px solid var(--border);padding:8px 16px;font-size:13px;display:flex;align-items:center;justify-content:center;gap:12px;text-align:center">
  <span>日本語ページ（ESRダッシュボード）をご利用いただけます。</span>
  <a href="jp/index.html" style="font-weight:700;color:var(--primary)">移動する →</a>
  <button type="button" id="jpBannerClose" aria-label="閉じる" style="background:none;border:none;cursor:pointer;color:var(--muted);font-size:16px;line-height:1;padding:2px 6px">×</button>
</div>
<script>
(function(){
  try{
    var lang=(navigator.language||navigator.userLanguage||'').toLowerCase();
    if(lang.indexOf('ja')===0 && !localStorage.getItem('iq_jp_banner_dismissed')){
      var b=document.getElementById('jpBanner');
      if(b){
        b.hidden=false;
        var btn=document.getElementById('jpBannerClose');
        if(btn) btn.addEventListener('click', function(){
          b.hidden=true;
          try{ localStorage.setItem('iq_jp_banner_dismissed','1'); }catch(e){}
        });
      }
    }
  }catch(e){}
})();
</script>
```

### owner 판단거리 (owner 결정 필요한 것만)

1. **備考 열에 공개용 코멘트가 필요한가?** 지금은 `notes`(한국어 내부메모)를 안 보여준다.
   필요하면 publishing에 "공개용 비고" 필드를 별도로 요청해야 한다.
2. **`doc_type` 한글 오염의 근본 수정** — 화면단 `jaOnly()`로 방어했지만, 원인은 publishing
   파이프라인이 doc_type에 내부메모를 섞어 쓰는 습관으로 보인다. 이번 라운드는 JSON을
   안 건드렸다(읽기 전용 원칙) — publishing에 알릴지는 owner 판단.
3. **`robots.txt`/`sitemap.xml` 반영 시점** — 지금 `jp/index.html`엔 안전장치로
   `<meta name="robots" content="noindex,follow">`를 넣어뒀다. 라이브 확정 시 owner가
   이 줄을 빼야 검색엔진에 노출된다(사이트맵 등재는 별도 후속).
4. **GA(방문분석) 태그 포함 여부** — 이번 초안엔 넣지 않았다(티켓에 언급 없었음). 라이브 확정 시
   루트 4페이지와 같은 패턴으로 붙일지 owner 결정.
5. **위 3개 삽입 조각의 실제 반영 시점/문구** — 특히 안내 띠 문구·배치는 시안이라 owner 확인 후
   다음 라운드에 실제로 루트 `index.html`에 넣는다.
