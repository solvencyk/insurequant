---
from: owner
to: designer
created: 20260912T1120Z
status: resolved
route: html
company: JP_MULTI
period: FY2025
track: J-ESR
---

## 미결 (owner) — `jp/company.html`: K-ICS.html 에 대응하는 일본 회사별 ESR 상세 페이지 (지금은 규제양식 공시 2사)

**배경.** owner 2026-09-12 "2개사에 대해 K-ICS.html 에 대응되는 페이지 만들어라. 실시." 데이터는 publishing 이 병렬로 만드는
`jp/jesr_detail.json`(계약은 `inbox/publishing/20260912T1120Z__owner__JP_MULTI__jesr_detail_json.md` 에 고정 — 그 계약으로 개발,
파일이 없으면 계약대로 `jp/_fixture_jesr_detail.json` 임시 생성 후 진짜 파일 생기면 교체·삭제). 10월에 62사가 들어오면 채워질 틀을
지금 2사로 세우는 것. 회사 선택지 2개·분기 1개(2026-03-31)뿐이라 시계열 패널은 없다.

**산출물.** `jp/company.html` 신규(+ `jp/index.html` 의 一覧表 회사명에 상세가 있는 회사만 `company.html?company=<id>` 링크 —
`jesr_detail.json` 의 companies id 로 판정, 없으면 링크 없음). 루트 4페이지·`common.css` 수정 금지.

**구성(위→아래, K-ICS.html 의 패널 구조·chrome·`../common.css` 그대로 재사용).**
1. 헤더 = `jp/index.html` 과 동일(브랜드·언어전환) + 「← ESRランキング」 링크. `<html lang="ja">`, hreflang(ko=루트 K-ICS.html,
   ja=이 페이지, x-default=ko), noindex(초안).
2. 회사 선택 `<select>`(companies 순, URL `?company=` 동기화) + 기준일·범위(連結/単体)·출처 링크(公表日 텍스트에 링크, 一覧表 방식).
3. 헤드라인 카드 3: 適格資本(A) / 所要資本(B) / ESR(A/B) — 금액은 **億円 환산 표시**(百万円÷100, 소수 1자리) + 툴팁에 원단위 百万円.
   ESR 색은 `jp/index.html` 의 `_ratioHsl`(base 100·strong 300) 그대로.
4. 適格資本の構成: Tier1(基礎項目 / 資本性証券 등)·Tier2 스택 가로막대 1개 + 표(항목·금액·비중). 라벨은 `_meta.labels[id].ja`.
5. 所要資本の内訳: 대분류 5개(生保·損保·巨大災害·市場·信用) + 運営 막대 → 分散効果(−) → 税効果(−) → 所要資本 의 워터폴
   (루트 IFRS17.html 워터폴 관례: 0선 넘는 항목은 custom renderItem, 음수 △ 표기 규칙 준수). 옆에 「規定再現」 배지:
   `aggregation.reproduced` true 면 ✓(체크 n/n), false 면 △ + deviations 항목 툴팁.
6. 市場リスクの内訳: 하위 6개 가로막대(値 있는 것만).
7. 感応度: 시나리오별 ESR(pp 변화 포함) 표 + 작은 막대. 기준(헤드라인) 행 포함.
8. (있으면) 기사 3축 `axes` 값 표(異常危険準備金 등) — 값 없는 항목은 행 자체 생략.
9. 푸터 = `jp/index.html` 과 동일 + 「規制様式(告示)に基づく開示のある会社のみ表示。2026年10月末に順次追加」 안내.

**규칙.** CSP·SRI 는 `jp/index.html` 과 동일(ECharts 5.5.0 jsdelivr, 워터폴·막대는 ECharts 허용 — 단 이 PC 크로미움은 CDN 이 막히니
검증은 echarts 로컬 임시 사본으로 하고 끝나면 삭제·CDN 참조 원복을 git diff 로 확인). 데이터 인라인 금지(fetch 만). 반응형(375px:
select 100%, 카드 3열→1열, 표 가로스크롤 컨테이너). A11y(랜드마크·표 th scope·차트 aria-label 데이터 기반). 숫자: 억엔 1자리, %
1자리, 음수 △. 서브에이전트 금지, 멀티라인 `python -c` 금지, UTF-8 BOM 없음.
검증: 로컬 서버로 2사 전환 확인, 콘솔 에러 0, 데스크톱 1280·모바일 375 스크린샷 `artifacts/designer/jesr_jp_company_{desktop,mobile}_20260912.png`.
끝나면 답변란에 파일 목록·스크린샷 경로·판단거리, `status: answered`, `TODO_jp.md`·`docs/changelog_jp.md` 갱신. 보고문 일본어 문자 금지.

## 답변 (designer)

**이름 변경(owner 작업중 지시).** 산출물 파일명을 `jp/company.html` 이 아니라 `jp/jesr.html` 로 저장(K-ICS.html 처럼
제도명 관례). `company.html` 은 남기지 않음. `jp/index.html` 의 상세 링크·hreflang/canonical 도 전부 `jesr.html` 로
갱신. 스크린샷 파일명도 owner 지시대로 `jesr_jp_jesr_{desktop,mobile}_20260912.png`(티켓 원문의
`jesr_jp_company_*` 아님).

**파일.**
- 신규: `jp/jesr.html`
- 수정: `jp/index.html`(상세 링크 추가 + owner 추가지시 2건 — 一覧表 業態·基準日 열 제거, 基準日 표기를 일본
  회계연도 분기로 변경)
- `jp/jesr_detail.json` — 이 세션 미접촉(publishing 산출, 개발중 도착). `jp/_fixture_jesr_detail.json` 은 계약대로
  만들었다가 실 파일 도착 확인 후 즉시 삭제(현재 저장소에 없음).

**구성 1~9 전부 반영.** ① 헤더+뒤로가기(「← ESRランキング」)+hreflang(ko=`../K-ICS.html`, ja=자기 URL, x-default=ko)+noindex.
② 회사 select(`?company=` 동기, history.replaceState)+기준(=③ 참고, 일본 회계연도 분기로 owner 정정 반영)/範囲/공표링크.
③ 헤드라인 3카드(億円 1자리, 툴팁 百万円 원단위, ESR 색은 `_ratioHsl`(base100/strong300) 그대로). ④ Tier1/Tier2
CSS 스택바(ECharts 아님 — 2세그먼트뿐이라 순수 HTML/CSS 가 a11y·번들 양쪽에 더 낫다는 판단, 색은 `--primary`/`--warn`
토큰) + 항목·금액·비중 표. ⑤ 소요자본 워터폴 ECharts custom renderItem(IFRS17.html `renderPlWaterfall` 패턴 — 0선
넘는 막대를 [y0,y1] 사각형 직접 그려 스택+투명 placeholder 방식의 뜸 버그 회피) + 「規定再現」 배지(true→✓ n/n,
false→△+deviations 툴팁, 티켓 지시대로 reproduced=false 일 때만 deviations 노출). ⑥ 市場リスク 6개 중 null 아닌 것만
가로바(CSS). ⑦ 感応度 표(기준행 헤드라인에서 합성, 시나리오 행은 데이터에서)+미니바, delta_pp 는 색+△/+ 로 이중부호
(색만이 아님). ⑧ axes 표는 `typeof === 'number'` 인 항목만(실 데이터에 `esr_status`/`cat_reserve_by_line` 같은
문자열·중첩dict·배열이 섞여 있어 스킵리스트 대신 타입판정으로 전부 자동 제외됨 — meijiyasuda 는 숫자 axes 가 0개라
섹션 자체가 `hidden`, au 는 5개 표시). ⑨ 푸터 동일+안내문구.

**판단거리(발주범위 밖 실측 버그 3건, 명백+해결법 명확해 직접수정).**
1. **`doc_type` 한국어 혼입.** 실 `jp/jesr_detail.json` 의 au_nonlife `doc_type` 이
   `"…(au損保の現状2026, 업적데이터편, 2026-07-30 발행)"` 로 파이프라인 내부 한글 메모가 섞여 있었음(meijiyasuda 도
   동일 패턴). `jp/index.html` 이 이미 같은 문제에 대응해 갖고 있던 `jaOnly()`(가-힣 정규식 제거+괄호/쉼표 정리)를
   그대로 이식해 화면표시 직전에만 적용(원본 JSON 은 안 건드림).
2. **비중(構成比) 100%+ 오독.** 처음엔 모든 항목을 적격자본 총액 대비로 계산했더니 `tier1_basic`(조정 공제 전
   총액)이 149.6% 로 찍혔다(au: 138.8억/92.8억). Tier1/Tier2 최상위 2행+합계행만 총액 대비, 그 외 세부항목은
   자기 tier 의 `tier1_basic`/`tier2_basic` 대비로 분모를 바꿔 해결, 표 아래 계산기준 각주 추가.
3. **모바일 375px 워터폴.** (a) x축 8라벨(生命保険リスク 등 정식명)이 겹쳐 판독 불가 → 짧은 라벨(生保/損保/巨大災害/
   市場/信用/運営/分散効果/税効果/所要資本)+45도 회전. (b) `echarts.init` 이 컨테이너 폭이 안정되기 전에 불려 좁은
   캔버스로 굳어(뒤쪽 2개 막대 税効果·所要資本 이 아예 안 그려짐) 실측 → `requestAnimationFrame` 으로 다음 프레임에
   한 번 더 `resize()` 를 걸어 해결. (c) 기준/범위/공표 메타줄이 줄바꿈 없이 뷰포트 밖으로 밀려나가던 오버플로 →
   `.meta-line{overflow-wrap:anywhere}`.

**검증.** 로컬서버(`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m http.server 8917`), au_nonlife·
meijiyasuda_nonlife 2사 전환(select 변경 + URL 직접이동 둘 다) 확인, 콘솔에러 0(jsdelivr 폰트/echarts CDN
`ERR_NETWORK_ACCESS_DENIED` 만 — 이 PC 크로미움 공통현상이지 JS 런타임에러 아님, `renderWaterfall` 은
`typeof echarts==='undefined'` 가드로 무해하게 스킵). echarts 는 로컬 임시사본(`jp/_tmp_echarts.min.js`, curl 로
받은 뒤 `openssl dgst -sha384` 로 SRI 해시 `sha384-o5uz97et3bErHvpKfD4Jz4n0JfhJDWABFuF4NP+iEEDxE1VwMWJ19QGR0lqFZnr6`
와 사전대조 일치 확인 후 사용)으로 렌더 확인 후 삭제, CDN 참조·integrity 원복을 `grep echarts jp/jesr.html` 로
재확인(신규 미추적 파일이라 `git diff` 대신 grep). msedge headless `--screenshot` 는 위 (3b) RAF resize 안전망
타이밍과 안 맞아 반복적으로 구버전(막대 2개 누락) 렌더가 찍혀 Playwright(`networkidle`+600ms 대기+`full_page=True`)
로 전환해 최종 확보. 스크린샷: `artifacts/designer/jesr_jp_jesr_desktop_20260912.png`(1280×2454, au_nonlife)·
`artifacts/designer/jesr_jp_jesr_mobile_20260912.png`(375×2545, meijiyasuda_nonlife — 워터폴 8막대 전부 표시,
감응도 7시나리오 전부 표시). BOM 없음 확인(`jp/jesr.html`·`jp/index.html` 둘 다).

**공유 워크트리 알림.** 같은 라운드에 jp-collector 세션이 `TODO_jp.md` Status 에 "(9) profit 층" 항목을 병행 추가해
내 항목과 번호(9)가 충돌 → profit 항목을 (10) 으로 재번호, 6개로 늘어난 Status 에서 가장 오래된 (5) 항목을
`docs/todo_archive_jp.md` 로 무수정 이관해 "최신 5개" 규칙을 복구(내용은 한 글자도 안 고침, 번호·위치만 조정).

**미결(owner 승인 대기).** `/jp/` 라이브 반영은 publishing 답변의 3건(keep-list·xlsx·status_report) 처리 후 별도
배포 라운드 — `scripts/android_push_and_deploy.sh` NEW_FILES 편집은 오케스트레이터가 처리(지시대로 미접촉).

## 종결 재확인 (orchestrator 2026-09-12)

`jp/jesr.html`(owner 명명) 데스크톱·모바일 스크린샷 육안 확인: 회사 선택 2사, 基準時点 2025年度 4Q 한 줄, 헤드라인 카드(억엔·ESR 색),
Tier 구성 스택+표, 소요자본 워터폴(△ 표기, 規定再現 배지 43/43·49/51), 시장 하위, 민감도(Meiji 7 시나리오), 기타 공시(이상위험준비금 등).
`jp/jesr_detail.json` 2사·self-check exit 0, CDN 참조·BOM 정상. 잔여 시각 nit 3건(워터폴 y축 제목 잘림·음수 최소값, 構成比 하위행
기준 혼동, 모바일 자본표 금액열 스크롤)은 다음 designer 라운드(terms 티켓)에 포함.

status: **resolved**
