---
from: owner
to: jp
created: 20260913T1325Z
status: resolved
route: escalate
company: JP_MULTI
period: FY2025
iter: 1
---

## 미결 (sender 작성)

다른 세션(`session_01F9N5Bt…`, repo `solvencyk/solvency` 브랜치 `claude/pc-performance-dev-setup-kwpo45`)에서
egress 해제 직후 **기게시 15사 1차 출처 URL 리허설**을 돌려 5건의 문제를 찾았는데, 그 세션은 insurequant
push 권한이 없어 티켓을 못 남기고 끝났다(work log `work_logs/2026-09-13_egress해제-15사-소스URL-리허설.md`).
그 세션의 후속 5건을 이 레인으로 이관한다. 추가로 **EDINET 키가 이 세션 환경변수(`EDINET_KEY`)에 들어왔다.**

1. 수집기에 브라우저 헤더 기본값(UA·Accept-Language·Referer) — 없으면 10/31 census 가 멀쩡한 출처를 `not_found` 오탐
2. "1차 출처로 TDnet(`release.tdnet.info`)을 쓰지 않는다" 규칙화 + T&D 출처 교체 (만료되는 URL)
3. 재census 전 대상 사이트 **정적/JS 렌더링 판별** 단계 추가 (東京海上HD IR 이 HTML 364B·링크 0)
4. 404 3건(東京海上HD·T&D·日本生命) 대체 URL 확보
5. 새 세션에서 `jesr_edinet_fetch.py --key $EDINET_KEY --smoke`

## 답변 (recipient 작성 — 처리 후)

**5건 전부 처리. 처리 과정에서 화면 수치 오류 2건·출처 오인용 1건을 추가로 잡았다.**

**1·3. 공용 HTTP 헬퍼 `J-ESR/jesr_http.py` 신설** — 브라우저 헤더 기본값 + 판정 6종
(`ok` / `ok_requires_headers` / `blocked` / `tls_client_issue` / `spa_shell` / `dead`).
점검기는 `J-ESR/check_source_urls.py`(화면 출처 / `--census` / `--insurers` / `--all`).
**리허설의 "SPA" 진단은 오진이었다** — 東京海上HD `/ir/event/presentation/` 364바이트의 정체는
`<meta http-equiv="refresh">` 한 줄이고, 따라가면 링크 25개·PDF 6개가 정적으로 다 있다
(requests 도 `curl -L` 도 meta refresh 는 안 따라간다). probe 가 2홉까지 따라가게 했다.
`www.sonylife.co.jp` 는 파이썬만 TLS 악수 실패·curl 200 → `tls_client_issue` 로 분리(죽음 아님).

**2. TDnet 금지 규칙화** — `jesr_http.EXPIRING_HOSTS`, 도메인 문서 §4c 규칙 2. 지금 200 이어도 `expiring_host` 로 경고.
T&D 출처를 회사 IR 상설 경로(`td-holdings.co.jp/ir/document/results.html`)로 교체.

**4. 404 3건 대체 URL 확보 + 검증**
- 東京海上HD: 게시 디렉토리 이동(`gi58a8000000246z-att` → `gi58a80000002zwa-att`). 決算プレゼン資料로 교체.
- 日本生命: 사이트 개편(`/kaisha/annai/` → `/kaisha/gyoseki/`). 2025年度決算の概要 PDF 로 교체(p8 규제ESR 連結195%·単体204%).
- T&D: 위 2번.

**5. EDINET 키 — smoke PASS, 그 뒤로 루트 전체를 실측으로 다시 깔았다.**
- 호스트 정정: `api.edinet-fsa.go.jp/api/v2`(종전 `disclosure…` 는 301→302). 키 없으면 **HTTP 200 + 본문 StatusCode 401**.
- 코드 검증: 공식 코드리스트 11,389건 대조 → **기재 13개 중 7개가 다른 회사 코드**(E04979=パーク24, E04506=九州電力 …).
  `jp_insurers.csv` TBD 62행 해소(매칭 27 · 미등록 확정 51 · 보류 3). 도구 `edinet_codelist.py`, 증거 `edinet_code_match.json`.
- FY2025 有報는 **이미 6월에 14사가 제출**돼 있었다(10월 제출이라던 기존 가정이 틀렸다 — 10/31 은 J-ICS 공시 기한).
- XBRL 태그엔 ESR 없음(기존 결론 유지) / **본문 iXBRL 엔 서술로 있다** → `edinet_esr_probe.py` 로 15건 전부 검출.

**추가 적발 3건(리허설 범위 밖, 1차 원문으로 확정)**
- 東京海上HD **238% → 268%**: 238% 는 원문에 없는 2차보도 인용값. 決算プレゼン p5/p44 · 有報 S100YLS8 본문 모두 268%
  (自己株取得 반영 255%, 사업계획 리스크테이크까지 234%).
- かんぽ生命 **220% → 181%**: 220% 는 「大量解約リスクを除いた場合」의 조정치. 원문 p35·p37 과 有報 S100YD29 모두 181%(監査未済 暫定).
- MS&AD 출처 오인용: URL 이 200 이라 살아있다고 봤지만 내용은 **2026-02-13 합병 보도자료**(ESR 미수록).
  2025年度通期決算 電話会議資料(p17 226%→214%)로 교체 — 수치 214% 는 종전과 동일.
- 부수 버그: `build_jesr_page_json.py` 의 preliminary 키워드가 한국어(속보·잠정)뿐이라 일본어 원문(暫定値·監査未済)을
  인용하면 확정치로 표시됐다 → 키워드 추가, かんぽ生命이 preliminary=true 로 정상 복귀.

**10월 라운드 인수인계**: `check_source_urls.py --all` 을 census 전에 먼저 돌린다. 2026-09-13 기준
254건/고유 139건에서 blocked 21 · spa_shell 8 · requires_headers 17 · dead 5 — 헤더 없이 훑으면 46건이 오탐난다.
