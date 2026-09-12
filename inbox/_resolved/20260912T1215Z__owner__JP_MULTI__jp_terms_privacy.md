---
from: owner
to: designer
created: 20260912T1215Z
status: resolved
route: html
company: JP_MULTI
period: -
track: J-ESR
---

## 미결 (owner) — `jp/terms.html` 일본어 이용규약·프라이버시 + `/jp/` 두 페이지 GA4 태그·푸터 링크

**배경.** owner 2026-09-12: "일본 사이트에 이용약관이 없다. 해외야말로 데이터 유료화·사업화 여지가 있어(이해상충·겸업 문제 해소)
약관을 잘 써 둬야 한다." 한국 `privacy.html`(이용안내 5절 + 개인정보처리방침 8절)을 정본 구조로 삼아 일본어판을 만든다.

**산출물.**
1. `jp/terms.html` 신규 — chrome·`../common.css`·hreflang(ko=`/privacy.html`, ja=이 페이지)·noindex(초안) 는 `jp/index.html` 과 동일.
   문서 구조(일본어, 법률 문서 톤·敬体):
   **利用規約**
   1. 本サイトについて — 個人運営の情報サイト、会員登録・決済なし(現時点)、各社の保険業法に基づく開示資料(ディスクロージャー誌・決算説明資料)と
      金融庁告示を自動収集・正規化・検証して表示。誤りの可能性、投資・契約・規制対応の判断根拠には使えない、原数値の権利は各開示主体、
      本サイトは原資料を代替しない。
   2. 許諾される利用 — 閲覧・キャプチャ、出典(InsureQuant, www.insurequant.com/jp/, 参照日)明示の引用(報道・研究・教育・社内報告)、
      ダウンロードファイルの組織内分析。
   3. 禁止事項 — クローラ・スクリプト等による自動収集(AI学習目的を含む)、データの全部または相当部分の再配布・再販売、同種サービスの構築、
      本サイトの表示・データを自社サービスに組み込むこと。理由: 個々の数値は公開事実でも、会社×期×項目に整理した画面とデータは編集著作物・
      データベース(著作権法第12条・第12条の2)として本サイトに権利が帰属する。
   4. **有料サービス・ライセンスの留保** — 運営者はデータ提供・API・レポート等の有償サービスやライセンスを別途の契約条件で提供することがある。
      本規約はいかなる商用利用権も付与しない。商用・大量利用は問い合わせ窓口から個別協議。
   5. データ出典 — 표: ESR(各社開示資料: ディスクロージャー誌・別冊・決算説明資料・決算短信), 算定規定(金融庁告示), 公表状況(各社サイト実査).
      出典機関は本サイトと無関係。最終反映時点は画面上部の基準時点表示。
   6. 免責 — 正確性・完全性・最新性を保証しない、利用による損害に責任を負わない(法令上免責できない場合を除く)。
   7. 規約の変更 — 予告なく変更、掲載時点から効力。
   8. 運営者・問い合わせ・準拠法 — 運営者: 韓国 `privacy.html` §5 와 동일 표기(InsureQuant、運営者 조상욱、個人運営)를 **한 곳의 변수처럼
      한 문단에만** 둔다(향후 법인 전환 시 그 문단만 교체). 準拠法は大韓民国法、管轄は運営者所在地の裁判所(owner 확정 전 초안).
      日本語版は `/jp/` 配下に適用、韓国語版(`/privacy.html`)は韓国語サイトに適用、両者に矛盾がある場合はそれぞれのサイトで各版が優先。
   **プライバシーポリシー**(일본 個人情報保護法이 해외 사업자에도 적용되는 점을 전제)
   1. 取得する情報と方法 — (1) アクセス解析 Google Analytics 4(Cookie・識別子・閲覧ページ・端末情報、IPは Google 側で匿名化処理)、
      운영자 본인 접속은 内部トラフィックとして除外. (2) 問い合わせ・誤り報告フォームがあれば入力内容(현재 jp 에는 없음 — "設置時に本項を
      更新" 로 표기).
   2. 利用目的 — 利用状況の把握と改善、不正利用の検知、有償サービス検討時の需要把握(集計値のみ)。
   3. 第三者提供・外国にある第三者への提供 — Google LLC(米国)へ解析データが送信される旨、Google の利用規約・プライバシーポリシー・
      データ保護の仕組み(EU-U.S. DPF 등 일반 표현)へのリンク、韓国 privacy.html §3 와 대응.
   4. Cookie の無効化 — ブラウザ設定、Google Analytics オプトアウトアドオン URL。
   5. 保有期間 — GA4 の保持設定(韓国판과 동일 값이면 그 값, 모르면 "Google Analytics の設定に従い最長14か月" 류로 owner 확인 표기).
   6. 開示・訂正・利用停止の請求 — 問い合わせ窓口。
   7. 安全管理 — 運営者は集計データのみ閲覧、個別識別情報を保有しない。
   8. 施行日 — 2026-09-12.
2. `jp/index.html`·`jp/jesr.html` 푸터에 「利用規約・プライバシーポリシー」 링크(`terms.html`) 추가, 한국어 사이트 링크 옆.
3. `/jp/` 두 페이지 `<head>` 에 루트 5페이지와 동일한 GA4 스니펫(측정 ID `G-F8NSCQZBZK`, `iq_internal` 플래그 포함 — 루트 `index.html`
   9~26행 그대로) 추가 + CSP 를 루트 `index.html` 6행과 동일 형식으로 확장(googletagmanager·google-analytics 호스트, `analytics.google.com`
   apex 별도 등재 함정 유지). SRI 예외 주석도 루트와 동일.
4. `scripts/android_push_and_deploy.sh` `NEW_FILES` 에 `jp/terms.html` 추가(한 줄).

**규칙.** 일본어 법률 문서로서 자연스럽고 정확하게(기계번역 투 금지). 한국 `privacy.html` 의 문장을 그대로 옮기되 일본 법제(個人情報保護法·
著作権法 조문)에 맞게 조정. 데이터 인라인 금지 원칙은 정적 문서라 해당 없음. UTF-8 BOM 없음, 서브에이전트 금지, 멀티라인 `python -c` 금지.
검증: 로컬 서버로 3 페이지 렌더·링크·콘솔 에러 0, `tests/test_deploy_assets.py` 통과, 375px 스크린샷 1장(`artifacts/designer/jesr_jp_terms_mobile_20260912.png`).
끝나면 답변란에 파일 목록과 owner 확인 필요 항목(운영자 표기·준거법·GA 보유기간)을 적고 `status: answered`, `TODO_jp.md`·`docs/changelog_jp.md`
갱신. 보고문 일본어 문자 금지.

## 추가 (owner 2026-09-12, 같은 라운드) — 우측하단 오류제보 팝업 + 상세 페이지 nit 3건

5. **오류제보 팝업(일본어).** 루트 `report-widget.js`(한국어 문자열·한국 시트/회사/분기 목록 하드코딩)를 복사해 `jp/report-widget.ja.js` 로:
   - 문자열 전부 일본어(「⚑ 誤りを報告」, 「数値の誤りを報告」, 「対象シート」「対象会社」「対象期」「誤りの内容」「送信」「送信中…」
     「送信完了 — ありがとうございます」「一時的に送信できません」, 필수 안내).
   - 시트 선택지 = `ESRランキング (jesr_esr)` / `会社別詳細 (jesr_detail)` 2개. 회사 목록은 `jesr_esr.json` 의 13사(company_jp) + 상세 2사,
     기(期) 선택지는 `2025年度 4Q` 1개(`_meta.as_of` 규칙으로 생성). 제출 payload 의 sheet 값 앞에 `JP:` 접두사(백엔드 무변경으로 구분).
   - 백엔드는 루트 `../forms-config.js` 그대로 재사용(같은 Apps Script). `jp/index.html`·`jp/jesr.html` 에 `<script src="../forms-config.js">`
     + `<script src="report-widget.ja.js">` 를 루트와 같은 위치(본문 끝)에 추가.
   - CSP `connect-src` 에 `https://script.google.com https://script.googleusercontent.com` 추가(루트 index.html 6행과 동일 — 리다이렉트
     목적지 도메인 누락 함정, 도메인 문서·메모리 CSP 항목). `form-action` 도 루트와 맞춘다.
   - 프라이버시 절 1-(2) 를 "設置済み" 로 갱신: 取得項目(対象シート・会社・期・自由記述, 任意のメール等は求めない), 保存先(Google スプレッドシート・
     米国), 利用目的(誤り確認・修正), 保有期間.
   - `scripts/android_push_and_deploy.sh` `NEW_FILES` 에 `jp/report-widget.ja.js` 추가.
6. **`jp/jesr.html` nit 3건(orchestrator 검수):** ① 소요자본 워터폴 y축 제목 "(億円)" 잘림 + y축 최소값이 음수(−2.2/−11.5)로 내려감 →
   min 0 고정·제목 여백 확보 ② 適格資本 구성표의 構成比가 하위 행은 Tier 基礎項目 대비라 138.8 > 91.0 인데 100.0% 로 보여 혼동 →
   하위 행 構成比 열은 비우거나 "適格資本総額比" 로 통일 ③ 모바일(375px) 자본 구성표에서 금액 열이 잘려 안 보임 → 会社名 열 폭 축소
   또는 첫 열 고정으로 금액·構成比가 보이게.
검증 항목에 추가: 팝업 열기→제출(콘솔 `[IQ_FORMS]` 로그 또는 네트워크 POST 시도)까지 로컬 확인, 375px 팝업 스크린샷.

## 답변 (designer 2026-09-12)

**산출 파일.**
- `jp/terms.html` 신규 — 利用規約 8절(第1条~第8条) + プライバシーポリシー 8절. chrome·`../common.css`·CSP(루트 index.html 6행 동일)·GA4 스니펫(iq_internal 포함)·
  hreflang(ko=`/privacy.html`, ja=`/jp/terms.html`, x-default=ko)·noindex 는 `jp/index.html` 과 동일. 스타일은 루트 `privacy.html` 읽기 페이지 블록 이식.
  第3条 에 編集著作物(著作権法第12条)·データベースの著作物(第12条の2) 명시, 第4条 有料サービス・ライセンス 유보(商用利用権 불부여), 第8条 運営者 표기는
  그 문단 한 곳에만. プライバシー 1-(2) 는 誤り報告フォーム "設置済み" 로 작성(取得項目·保存先 Google スプレッドシート(米国)·利用目的·保有期間).
- `jp/report-widget.ja.js` 신규 — 루트 `report-widget.js` 복제·일본어화. 시트 2개(`jesr_esr`/`jesr_detail`), 회사·期 선택지는 `jesr_esr.json`+`jesr_detail.json`
  fetch 로 동적 생성(회사 14 = 랭킹 13 + 明治安田損害保険, 期 = `_meta.as_of`→`jaFiscalQuarter` = "2025年度 4Q" — 분기 리터럴 하드코딩 안 함, fetch 실패 시만 정적
  폴백), payload `sheet` 값 `JP:` 접두. 루트 대비 추가: `<label for>` 연결(select·filter·textarea), 오류문 `role="alert"`, 허니팟 `aria-hidden`.
- `jp/index.html`·`jp/jesr.html` — CSP 를 루트 6행과 동일 문자열로 교체(googletagmanager·google-analytics·`analytics.google.com` apex·script.google.com·
  script.googleusercontent.com), GA4 스니펫(루트 9~26행 그대로) 추가, 푸터에 「利用規約・プライバシーポリシー」→`terms.html` 링크(한국어 사이트 링크 앞),
  본문 끝에 `<script src="../forms-config.js">` + `<script src="report-widget.ja.js" data-sheet-hint="jesr_esr|jesr_detail">`.
- `jp/jesr.html` nit 3건 — ① 워터폴 `yMin = lo<0 ? … : 0`(실측 au △2.2→0, 明治安田損保 △11.5→0 억엔), y축 제목 `(億円)`+`nameGap:12`+`grid.top 20→40`
  ② 適格資本 구성표 構成比는 Tier1/Tier2/適格資本の額 3행만 총액 대비 표시(98.1%/1.9%/100.0%), 세부행은 빈칸 + 각주 문구 교체
  ③ 375px 에서 `#capitalTable{min-width:0}` + 항목명 `overflow-wrap:anywhere` + 숫자열 `nowrap` → 마지막 열 오른쪽 끝 351.5px < 뷰포트 375px(스크롤 없이 보임).
- `scripts/android_push_and_deploy.sh` NEW_FILES 에 `jp/terms.html jp/report-widget.ja.js` 추가.

**검증(실측).** 로컬 `python -m http.server 8931` + Playwright(venv) 3페이지 × 데스크톱 1280/모바일 375:
- 콘솔 에러 0(jsdelivr/gtag `ERR_NETWORK_ACCESS_DENIED` 만 ignore, 페이지당 2~3건 — 이 PC 공통현상), 상대 링크·script/css 참조 전부 200(bad_links=[]),
  `typeof gtag==='function'`, `window.IQ_FORMS` object, 푸터 terms 링크 1개씩, 모바일 body scrollWidth 375(가로 스크롤 없음).
- 팝업: FAB 클릭→dialog 표시, 시트 옵션 2개·hint 프리셀렉트(index=jesr_esr, jesr=jesr_detail), 회사 14·期 "2025年度 4Q", 빈 제출→오류문 표시,
  값 채워 제출→네트워크 `POST https://script.google.com/macros/s/AKfycbz…/exec` 시도 확인(이 PC 는 외부 443 차단이라 `[IQ_FORMS] … Failed to fetch` 로
  종료 — 실서버에선 정상 경로). `label[for]` 18개 전부 대상 존재.
- 워터폴은 CDN 차단으로 이 PC 에서 echarts 를 못 받아(curl/requests 000·WSAEACCES) `add_init_script` 로 `setOption` 캡처 스텁을 심어 옵션만 검증:
  2사×2뷰포트 전부 `yAxis.min=0`, `name="(億円)"`, `grid.top=40`, series data 8막대 y0/y1 정상.
- `pytest tests/test_deploy_assets.py` 11 passed. 5개 파일 UTF-8 BOM 없음·LF 유지(`file`/`grep -c $'\r'`=0).
- 스크린샷: `artifacts/designer/jesr_jp_terms_mobile_20260912.png`(375×7640 full) · `jesr_jp_report_mobile_20260912.png`(팝업 입력 상태) ·
  `jesr_jp_jesr_mobile_nits_20260912.png`(구성표 금액열 확인).
- 재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m http.server 8931` 후 `http://127.0.0.1:8931/jp/terms.html` 등 3페이지.

**owner 확인 필요.**
1. 運営者 표기(第8条): `運営者: InsureQuant(個人運営)、運営責任者: Cho Sangwook(조상욱)` — 일본어 페이지에 한글 병기·영문 표기 유지 여부.
2. 準拠法·관할(第8条): 大韓民国法 + 運営者所在地の裁判所 専属的合意管轄 로 초안(한국판은 서울중앙지방법원 명시 — 동일하게 명시할지).
3. GA 보유기간: 한국판 값(최대 14개월) 그대로 "最長 14 か月" 로 표기 — GA4 실제 설정값 확인.
4. 시행일 2026年9月12日(利用規約·プライバシー 공통). 誤り報告 시트 값은 `JP:jesr_esr`/`JP:jesr_detail` 로 들어오니 Apps Script 시트에서 접두로 구분.
5. 커밋 범위: `TODO_jp.md`·`docs/changelog_jp.md` 는 publishing 세션의 미커밋 (11) 항목이 같은 파일에 있어 이 라운드 커밋에서 제외(갱신은 해 둠).

## 종결 재확인 (orchestrator 2026-09-12)

검수 완료: terms.html 핵심 조항(有料サービス留保·編集著作物/DB 권리·準拠法·運営者·内部トラフィック·誤り報告) 확인, CSP connect-src 에 script.google.com/googleusercontent 포함, NEW_FILES 7개, 팝업 모바일 스크린샷 정상, BOM 없음. profit 블록은 au 확정(経常利益 1,654·当期純利益 1,171·合算率 71.1), Meiji 는 본편 확보 후 재빌드 예정(별도 jp-collector 진행 중). owner 확인 항목(運営者 표기·準拠法·GA 보유기간·施行日)은 owner 에게 전달.

status: **resolved**
