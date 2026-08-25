# Insurequant TODO — Downloader Stage

> Last updated: 2026-08-25 · Stage 1/5 — downloader
> Prompt: docs/agents/claude-agent-downloader.md (+ docs/agents/source-catalog.yaml) · Changelog: docs/changelog_downloader.md

**Cross-stage TODO:** `TODO.md` (root). **This file:** active + done items scoped to data collection only.

## Status

**🟢 2026-08-25 인박스 처리 — DART raw 유실 45칸 복구 + 유실 탐지기 신설·배선
(`inbox/downloader/20260825T0001Z`):** parser(ifrs17)가 KB손해보험 2024.3Q~2025.3Q PL 5개 분기
결측을 회부. census 를 직접 떠 보니 **KB 만이 아니라 손보 상장 코호트 9개사 × 2024.3Q~2025.1Q**
가 본체 구멍이었고(KR0001·KR0010 만 2025.3Q 까지), 티켓이 KB 만 짚은 건 그 회사 census
관측범위만 앞당겨져 있었기 때문이다.

- **원인 = 디스크 유실.** 원천 부재 ❌(필링 전부 존재) · negative cache ❌ · 유실 ⭕.
  근거: `_inventory_manifest.json`(2026-05-30 디스크 스냅샷)의 zip 바이트와 오늘 재취득한
  바이트가 **정확히 일치**. `data/_archive/` 에도 없어 Reorg 이동이 아닌 삭제.
  **누가 지웠는지는 특정 못 했다** — `.gitignore:41` 이 `data/dart/**/raw/` 를 제외해 git 에
  기록이 없다(추측 금지).
- **FS-API 음성캐시는 깨끗했다(실측).** 굳은 013 622개 중 113개 표본 라이브 재호출 →
  **113/113 여전히 013, 회수 0**. 2026-08-19 근본수정은 제대로 먹었고 이 건과 무관.
  다음 세션은 이 축을 다시 의심하지 말 것.
- **복구 45칸** 검증 통과(PK 매직·testzip·본문 XML·`보험계약마진` 25~405회).
  재취득 후 manifest 303칸 대조 **누락 0**.
- **재발 방지 배선 완료**: `scripts/check_dart_raw_coverage.py`(high-water mark 395칸,
  `data/dart/_raw_coverage_baseline.json`) → **`scripts/prepush_check.py` 1d 단계**.
  유실 발생 시 push 차단. slim 워크트리는 자동 skip.
- parser raw-ready: `inbox/parser/20260825T0430Z`.

**🟡 잔여(우선순위 낮음) — `raw_annual` 미보유 5건.** baseline 의 `known_absent` 에 사유와 함께
등재돼 매 실행 인쇄된다. AIG 2022.4Q 감사보고서 2건(사유 미확정, 조사 필요) · 교보라이프플래닛
2025.4Q 연결 · 하나손해 2025.4Q 연결(둘 다 "별도가 본체" 관례 추정이나 명시 기록 없음 —
확정하면 사유를 갱신할 것). AIG 2023.4Q `…2106` 은 의도적 미취득으로 **확정**(2026-08-17 티켓).

**🟢/🔴 2026-08-21 인박스 처리 — KR0005 흥국화재 wrong-document 재취득 완료, KR0071 흥국생명은
원천 자체 오문서 확인 (honest gap, `inbox/downloader/20260821T1625Z`):** validation이 두 회사
2024.4Q raw가 K-ICS 정기경영공시가 아니라 DART 사업보고서(경과조치 0회, dart.fss.or.kr 꼬리말)
라고 지적, 이 때문에 잘못 등재됐던 "발행사 미공시" 면제 2건도 해제해 넘겨받음.

- **KR0005**: kpub.knia.or.kr(손보협회 통합공시) 결산 2024 열에서 정본 재취득
  (`scripts/refetch_kr0005_kr0071_fy2024q4.py`, 일회성). 표지 "보험업감독규정 제7-44조" +
  p37 "[지급여력비율 총괄]" 표에 경과조치 전(154.01%)/후(199.56%) 24.4Q 수치 명시로 정본
  확인. `fitz` 텍스트검색 "경과조치" 0회는 **오탐**이었다 — 데이터표가 래스터 이미지라
  240dpi 렌더+육안 판독으로 확인함(티켓이 미리 경고한 스캔본 케이스). 기존 오문서는
  `data/_archive/20260821T044328Z/`로 이동, 신규본(96p, 38.96MB) 설치.
- **KR0071**: **독립된 두 경로**(pub.insure.or.kr 생보협회 일괄공시 결산 컬럼 / 흥국생명
  자사 사이트 `manageList.do` 번호101 "FY2024 결산 경영공시")가 **SHA256 완전 동일한 오문서를
  반환** — 기존에 디스크에 있던 것과도 동일. 즉 **흥국생명이 공시 채널 자체에 잘못된 파일을
  올려둔 상태**로, 다운로더가 접근 가능한 표준 경로로는 정본을 구할 수 없음(538p 내용
  확인 — K-ICS 일반설명 boilerplate뿐, 회사 고유 수치 없음). 기존 파일은 그대로 두고(대체본
  없이 지우지 않음) honest gap으로 답변. 면제 재등록 안 함 — RED 유지가 맞음.
  owner 판단 필요: 흥국생명 직접 문의 또는 정정 게시 대기.

parser hand-off: KR0005는 raw ready이나 **경과조치 표가 이미지라 OCR 경로 필요**(기존
pdfplumber EOF→fitz fallback과 다른 문제); KR0071은 raw 여전히 못 넘김,
`POST_TRANSITION_PARENT_MISSING` RED 4건 유지. 상세: `inbox/downloader/20260821T1625Z` 답변.

**🟢 2026-08-20 인박스 처리 — alotMatter census stale-after-refresh 버그 수정
(`inbox/downloader/20260820T1810Z`):** 위 negative-cache 재취득 직후 parser가 발견한 후속
버그. `refresh_year_reprt()`는 캐시 파일만 갱신하고 `data/_derived/alotmatter_fetch_census.json`
을 다시 쓰지 않았다(census 갱신은 `main()`에만 있음) — 그래서 게이트가 기대 그리드를 여전히
구캐시(2026/11012 slice 000=5)로 세고 있었다. `refresh_year_reprt()`에 census in-place patch
추가(해당 (year,reprt) 셀만 status 갈아끼움, 다른 slice 무영향) + `--refresh 2026 11012`
재실행으로 census 즉시 동기화(000=5→24). `validate_data_contract.py` 재확인: `DIV_CENSUS_MISSING`
0건, RED=0. 종결.

**🟢 2026-08-20 인박스 처리 — alotMatter negative-cache 버그 수정 + 2026.2Q 배당 재취득 19사
복구 (`inbox/downloader/20260820T1600Z`):** `fetch_dart_fs.py`가 8/19에 고친 것과 **동일한
버그**가 `fetch_dart_alotmatter.py`엔 안 고쳐져 있었다 — 8/14 반기법정기한 당일에 013을
영구캐시해 39사 중 34사가 2026.2Q 배당 데이터를 영원히 못 얻는 상태였다. 동일 가드
이식(`status==000`만 캐시) + 신규 `--refresh <year> <reprt>` 플래그 추가 후 재취득:
**000=5→24, 013=34→15**(19사 복구). 남은 15개 013은 8/13 FS-API 온보딩 때 확인된 "XBRL
전무 15개사(감사보고서만 제출, 반기/사업보고서 자체를 안 냄)" 집합과 정확히 1:1 일치 —
캐싱 문제가 아니라 구조적 legit-absent로 확정(AIG는 `resolve_corp` 이름검색 quirk로 유니버스
스윕에서 빠져 corp_code 직접지정으로 별도 확인, 15개 안에 포함). 기존 2023~2025 캐시는
`(year, reprt)` 스코프라 무영향. parser raw-ready: `inbox/parser/20260820T1720Z`(→
`20260820T1540Z` blocked_on 해소, `build_dividend.py` 재빌드+golden `--update` 대기).

**🟢 2026-08-20 재드레인 — 악사손해 등 5사 연혁 백필 완료 + status-sweep 정리:** owner가
IFRS17.html에서 악사손해보험이 2024/2025년치만 보이는 걸 지적(`inbox/downloader/
20260819T0620Z`) → `data/dart/FY*/raw/KR0049_*` 실측하니 **FY2025_Q4 딱 1건뿐**, KR0050·
KR0051·KR0076·KR1010도 동일 패턴. **5개사 전부 비상장이라 사업보고서를 안 내고 감사보고서/
연결감사보고서만 낸다**(어제 AIG와 동일 함정 — "사업보고서"라는 단어를 그대로 찾았으면
전부 실패했을 것). FY2022~2024 21건 전부 fetched(신규 `scripts/fetch_annual_only5_history.py`),
zip무결성+`보험계약마진` 키워드 확인(4~60회). "전사 FY2022_Q4 백필" 스트레치 목표는 잔여
28개사 코드까지 정확히 뽑아만 두고 미착수(회사별 사업보고서/감사보고서 split 위험, 별도
발주 시 처리) — 상세는 `inbox/downloader/20260819T0620Z` 답변. parser raw-ready:
`inbox/parser/20260820T0052Z`.

**같은 회차, owner의 전 프로젝트 status-sweep**(`inbox/downloader/20260820T0033Z`, 78건 활성
스레드 중 51건이 `answered`인 채 방치된다는 지적) 대응: `20260614T1232Z`의 `status:` 필드가
resolved된 (1) 이후에도 `open`으로 안 바뀌어 있던 걸 `answered`로 정정(OCR-MARKETRISK는
owner가 이미 보류 결정한 상태이지 미결이 아님). `20260819T0116Z`(negative-cache)는 owner
sign-off 받아 `_resolved/`로 이동. `20260819T0820Z`의 E항목(2022.4Q 24사)은 어제 owner에게
직접 물어 "보류" 확정된 게 sweep 스냅샷엔 안 잡혔던 것 — 이미 반영돼 있다고 회신.

**🟢 2026-08-19 법정준비금 raw gap 인박스 처리 — A/B/C/D 완료, E는 owner 결정 대기:** parser
(`inbox/downloader/20260819T0820Z`, HIGH)가 IFRS17_BS 항목5-8(해약환급금·비상위험·대손·보증
준비금) 재작업 후 남은 결측이 raw 미수집임을 확인해 발주. 처리 결과:

- **발주 A(2023.2Q, 19사 중 18사)+B(2023.1Q, 11사 중 10사)**: `ifrs17_batch_historical.py
  --pilot ... --skip-extract`로 28건 fetched, `보험계약마진` 키워드 전부 확인(0건 없음).
- **발주 C(KR0150 서울보증, 2023.1Q~2024.4Q 8분기 전수)**: `EXCLUDED_SKIP` 우회 신규
  `scripts/fetch_reserve_gap_kr0150_kr0029.py` — **7분기는 `no_filing` 확정**(DART에
  정기보고서 자체가 없음, 기존 "2024.4Q부터 정기공시 재개" 문서와 일치, 새 결손 아님),
  **2024.4Q만 fetched**(rcept `20250324000440`). `보험계약마진`=0은 서울보증 특성상 정상
  (구조적 CSM-無 기존 판정과 동일), 대신 비상위험준비금 32회·대손준비금 26회로 진짜
  재무제표 본문임을 재확인.
- **발주 D(AIG KR0029 FY2024_Q4)**: 진단 결과 **AIG는 2023~2026 전 기간 사업/반기/분기보고서
  자체를 안 내고 감사보고서만 낸다**(기존 FY2023_Q4 raw도 사실 감사보고서였음, 우연히
  안 드러났을 뿐). FY2024.12 감사보고서+연결감사보고서 rcept 직접 fetch로 2건 확보,
  `보험계약마진` 51회씩 확인.
- **발주 E(2022.4Q 24사)**: owner에게 직접 질문 → **보류 확정**(2026-08-19, "지금 안 받음").
  재요청 전까지 미착수, gap 추적 안 함.

parser raw-ready: `inbox/parser/20260819T0841Z`. 원 티켓 답변 완료(`status: answered`),
인박스 드레인 중 완결된 스레드 4건(`20260814T0149Z` halfyear scout, `20260815T0230Z`/
`20260815T0310Z` viewer_fallback, `20260815T0907Z` IR factsheet)도 `_resolved/`로 정리.

**🟢 2026-08-19 FS API 영구음성캐시 버그 발견+수정 — 2026.2Q 9/10사 복구:** owner가 마스터
xlsx에서 `IFRS17_BS.json` 2026.2Q가 24사 중 14사뿐임을 발견(`inbox/downloader/
20260819T0116Z`). **원인**: 반기보고서 접수(8/14) 다음날 새벽 FS API 캐시를 긁었는데 DART가
아직 색인 전이라 013(무응답)이 나왔고, `fetch_dart_fs.py`가 013도 성공응답과 똑같이 영구
캐시에 써버림 — "공시 직후 한 번 긁으면 그 분기는 영원히 결측"되는 구조적 함정.

**즉시 수정**: 메리츠화재·삼성생명·현대해상·교보생명·농협생명·동양생명·미래에셋생명·
NH농협손해·KB라이프 9사 재취득, OFS 전부 BS 항등식(자산=부채+자본) 검산 통과. **흥국화재는
재취득해도 BS 1행(사용권자산)뿐** — 캐시 문제 아니라 DART 응답 자체가 빈 껍데기(한화손보
4-row blank shell 동류), parser에 본문 XML 폴백 대상으로 명시해 넘김.

**재발방지(근본수정)**: `scripts/fetch_dart_fs.py`의 `_fetch_raw`가 이제 **status=000만
캐시 파일에 씀** — 013은 그 호출에만 반환, 디스크엔 안 남아서 다음 호출 때 다시 라이브
확인함. `_refresh_cache`의 기존 파일 사전삭제도 제거(013 응답 시 "지우고 못 채움" 리스크
차단, force=True가 성공시에만 덮어씀). 기존 확정 영구결측(2023 1Q/2Q 24개사·비상장 15개사
등)은 캐시 파일이 이미 있어 이 변경과 무관 — 계속 그대로 재사용. parser 통지:
`inbox/parser/20260819T0140Z`.

**🟢 2026-08-17 인박스 드레인 — AIG 2023.4Q raw(마지막 push RED) + IR 재시도 11/13 (D-1/D-2 종결):**
① validation 요청(`inbox/downloader/20260817T0100Z`, HIGH — push 게이트 마지막 RED 1건):
AIG손해보험 corp_code `00983606`(이름검색 안 걸림, "AIG" 등록명) + rcept `20240403002101`
직접 fetch → `data/dart/FY2023_Q4/raw/KR0029_에이아이지손해보험_20240403002101/`, 보험계약마진
52회·상각 117회 확인. parser raw-ready `inbox/parser/20260817T0231Z`.

② IR 재시도(`inbox/downloader/20260815T0907Z` D-1/D-2) 마무리: **삼성생명 해결**(SPA 렌더링
타이밍 문제 — `wait_networkidle`+`wait_ms` 6000으로 재시도 성공), **코리안리는 사이트 전체
다운**(루트도메인 자체 연결거부, 재시도 무의미), **롯데손보는 WAF 차단 재확인**(우회 안 함).
한화손보는 애초에 IR 소스 자체가 없음 확인(공시실=정기경영공시와 동일 성격). 최종 **11/13**.
9사 우선순위 중 7/9 확보.

**부수 버그 발견+수정**: `download_ir_2026q2.py`가 부분 재실행 시 매니페스트를 통째로
덮어쓰는 구조였음(key 기준 merge로 수정, 향후 안전) — 실물 파일은 무사했으나 매니페스트가
13→2건으로 축소될 뻔함, 디스크 스캔으로 수동 복구. `_meta.period` "FY2026_Q1" 잔재도 수정.
IR 저장 경로가 두 관례 혼재 확인(`FY2026_Q2/<key>/` vs `FY2026_Q2/raw/<key>/`) — 이번 스코프
밖이라 안 건드림, 기록만.

**🟡 2026.2Q IR공시 13소스 스윕 — 10/13 확보(2026-08-15, owner "사별 IR공시자료 싹 돌면서"):**
신규 `scripts/download_ir_2026q2.py`(Q1 템플릿 복사, XPath 대부분 positional이라 무변경으로도
동작). **10개사 성공**(메리츠화재·삼성화재·현대해상·KB금융그룹·DB손보·신한금융그룹·
NH농협금융지주·한화생명·미래에셋생명·동양생명) — 메리츠·신한·동양생명은 Q1엔 실패했던
소스가 이번엔 성공(Q1 8/13→Q2 10/13 개선). `data/ir/FY2026_Q2/raw/`, 매직바이트 xlsx 확인.

**실패 3건 — 전부 downloader가 우회하면 안 되는 외부 차단, bot-detection 우회 시도 안 함:**
- **롯데손보(KR0003)**: WAF 차단("Web firewall security policies") — 스크립트+수동 브라우저
  둘 다 동일 차단 페이지 확인. 회피 시도 안 함(정책상 금지), 시간 두고 재시도 또는 owner
  판단 필요.
- **코리안리(KR1000)**: 접속 자체 거부(`ERR_EMPTY_RESPONSE`) — 수동 확인도 동일, 사이트 쪽
  일시적 이슈로 추정. Q1엔 성공했던 소스라 재시도 유력.
- **삼성생명(KR0069)**: 딥링크가 홈으로 리다이렉트되는 것으로 보임(URL 변경 추정) — 새
  URL 찾기 필요(DL-FYR: 분기마다 URL 직접 찾기 원칙), 아직 미해결.

**🔴→🟢 viewer_fallback 14개사 — 파서 빠꾸(다중문서 이어붙임 버그), 로컬 재포장으로 수정
완료 (2026-08-15, parser `20260815T0230Z`):** 어제 만든 우회경로(`fetch_dart_viewer_fallback.
py`)가 섹션별 `report/viewer.do` 응답(각각 완전한 `<!DOCTYPE><HTML>...</HTML>` 통짜 문서)을
wrapper 안 벗기고 그대로 이어붙여서, 파일 하나에 독립 HTML 문서가 최대 146개 겹쳐 있었음.
lxml 등 표준 HTML 파서는 첫 문서(표지, 표 4개)만 읽고 나머지는 통째로 무시 — **CSM 14개사
전부 0건, PL도 절반은 완전 0건**으로 parser가 잡아냄. **내 검증(문자열 `.count()`만 확인)이
문서 경계를 안 봐서 놓쳤던 결함** — "성공"으로 잘못 보고했음, 인정.

**수정은 재fetch 없이 로컬에서**: 이미 받은 raw를 섹션 구분자로 재분해 → 각 섹션의 `<BODY>`
안쪽만 추출 → 문서 하나로 재조립(`scripts/fix_viewer_fallback_multidoc.py`, 일회성). 원인
스크립트(`fetch_dart_viewer_fallback.py`)도 fetch 단계에서부터 같은 로직 적용하도록 고쳐서
재발 방지. **검증은 parser와 동일한 도구(lxml.etree.HTMLParser)로 재현**: 14개사 전부
Misplaced DOCTYPE 에러 0건, 표 인식 524~2857개(기존 4개→정상 회복), CSM 키워드 카운트는
수정 전후 동일(내용 손실 없음, 구조만 고침). parser 재확인 요청 회신: `inbox/downloader/
20260815T0230Z`(status: answered, parser 재파싱 확인 대기).

**⏰→⏹ 시간당 재시도 loop 종료 (2026-08-15, cron `6db8c7f4` 정상firing 중 자체 판단으로 정지).**
재스캔 결과 `scripts/scout_2026q2_halfyear.py`가 24/24 전부 "fetched (already had)"로 보고
(`other=0`) — 14개사 fallback raw를 정본과 동일 canonical 경로에 둔 부작용으로, 스크립트의
"이미 있으면 skip" 로직이 이제 그 14개사에 대해 정본 API 재시도 자체를 안 함. 즉 이 loop는
더 이상 할 일이 없어 자연 종료 조건 충족 → **loop 정지, cron 삭제.** **후속 고려사항(미착수,
owner 판단 필요 시)**: 정본 `document.xml`이 나중에 열렸는지 확인하려면 파일존재 여부와
무관하게 강제 재조회하는 별도 체크가 필요(현재 스크립트로는 안 됨) — 지금은 불필요 판단,
필요해지면 새로 발주.

**🟢 2026.2Q body XML 정체 완전 해소 — 우회경로(DART 웹뷰어) 신규 확보, 24/24 전원 raw 확보
(2026-08-15, owner "당장 실시 후 파서에게 발주"):** API(`document.xml`)가 안 열리는 나머지
14개사(흥국화재·삼성화재·현대해상·DB손해·NH농협손해·삼성생명·ABL생명·흥국생명·교보생명·
미래에셋생명·푸본현대생명·동양생명·KB라이프·코리안리)를 신규 우회경로로 전부 확보 →
**상장 24개사 전원 body raw 확보 완료.**

**신규 `scripts/fetch_dart_viewer_fallback.py`** — DART 문서뷰어(`dsaf001/main.do` +
`report/viewer.do`)는 API가 막힌 회사도 이미 문서 전체를 렌더링하고 있음(인증·세션 불요,
순수 HTTP GET). 뷰어 첫 페이지에 전체 문서목차(섹션별 offset/length)가 JS로 박혀있어 그것만
파싱하면 나머지는 반복 요청. **버그 2개 발견·수정 후 최종 14/14 성공**(섹션 48~146개,
1.2M~4.8M자, IFRS17 키워드 전부 확인):
1. 트리 변수명이 깊이별로 `node1/node2/node3`로 다른데 `node3`만 잡던 정규식 → 6개사가
   4~8섹션만(주석 섹션째 통으로 누락) 잡히는 버그. `node\d+` 전체 매치로 수정.
2. 부모 트리노드가 자식 전체를 포함하는 큰 offset/length를 같이 갖고 있어(삼성생명 630만자
   중복 확인) 부모+자식을 같이 받으면 통째 중복 위험 → offset/length **포함관계 기반 leaf
   선별 로직**으로 해소(트리 구조 몰라도 순수 범위 연산으로 판별).
3. 네트워크 타임아웃 6건 → 재시도 로직(백오프) 추가로 해소.

`data/dart/FY2026_Q2/raw/KR####_<canonical>/document.zip`(정본과 동일 zip+xml 명명, `*.xml`
glob 그대로 작동) + `meta.json`에 `"source": "viewer_fallback"` 명시(정본 API와 출처 구분,
나중에 진짜 document.xml 열리면 교체 여부는 owner/parser 판단). parser 통지:
`inbox/parser/20260815T0130Z`. 동양생명만 "신계약" 키워드 0회(라벨 변형 추정, parser 판단).

앞서 정상 API로 확보된 5개사(메리츠화재·KB손해보험·KDB생명·DB생명·서울보증) CSM/PL은 parser가
이미 반영 완료 확인(`inbox/parser/20260815T0015Z`, resolved) — 4개사 CSM 폐쇄 정확, 서울보증은
구조적 CSM-0 정상 판정.

**⏰ 시간당 재시도 loop 가동 (2026-08-15, owner "트래픽 몰려서 그런듯, 밤새 1시간마다 재시도"):**
CronCreate job `6db8c7f4`(매시 :07, 세션 종속·7일 자동만료) — 39사 재스카우팅→신규 확보사
FS API refresh+검산→parser 통지→TODO/changelog 갱신을 매시 자동 반복. 무변화 회차는 짧게만
기록. 즉시 1회차 실행 확인: 변화 없음(8/24 그대로) — 바로 아래 항목과 동일 상태.

**🟡 2026.2Q body XML 정체 — 24h+ 경과, propagation-lag 가설 재검토 필요 (2026-08-15, owner
재질문 "지금도 안되니"):** 재스카우팅 → **5개사 추가 확보**(메리츠화재·KB손해보험·KDB생명·
DB생명·서울보증, body+FS 캐시 둘 다) — body 확보 3→8/24. **그러나 16개사는 24시간+ 지나도
여전히 `document.xml status:014`.** DART 웹뷰어(`dsaf001/main.do?rcpNo=`)로 삼성생명·코리안리
직접 확인 결과 **웹에는 문서목차·다운로드 버튼까지 완전히 떠 있음** — 즉 문서 자체는 DART에
존재하고 서빙도 되는데, **OpenDART API의 `document.xml`(zip export)만 별도로 안 열리는 상태**.
같은 rcept로 재시도해도(즉시 재확인) 동일 014 — 단순 index-vs-serving 전파지연이 아니라
**API 전용 export 파이프라인이 이 배치만 막혀있을 가능성**으로 진단 상향. 24시간을 넘겼는데도
안 풀리는 건 처음 있는 패턴(기존 propagation-lag 사례는 보통 시간 단위 내 해소). FS API
(fnlttSinglAcntAll) 쪽도 나머지 16개사 재확인 진행 중(백그라운드). **owner 판단 필요**: 계속
대기할지, 웹뷰어 스크레이핑 같은 대체경로를 검토할지 — 다음 재호출까지는 대기 유지.

**FS API 재확인 완료(같은 라운드 후속) — 6개사 추가**: 삼성화재·DB손해·ABL생명·흥국생명·
푸본현대생명·코리안리, OFS BS 항등식 전부 검산 완료. **함정 발견 — 흥국화재는 `status=000`인데
BS 섹션이 사실상 비어있음**(CIS는 정상 채워졌는데 BS는 `사용권자산` 1행뿐, 그마저
`thstrm_amount=''`) — **status=000을 "BS 데이터 있음"으로 오독하면 안 됨**, sj_div별 완성도가
다를 수 있다는 신규 확인(문서 자체 vs API export 분리 문제와 별개로, API 안에서도 재무제표
종류별 처리시점이 다를 수 있음). parser 통지: `inbox/parser/20260815T0015Z`(흥국화재 파싱주의
포함). 순수 잔여(body+FS 둘 다 안 열림) = 9개사(롯데손보·현대해상·NH농협손해·삼성생명·교보생명·
미래에셋생명·동양생명·KB라이프·농협생명).

**🟢 신규 도메인 온보딩 완료 — 배당에 관한 사항(DART alotMatter), 39개사 전수 (2026-08-14,
owner HIGH):** `inbox/downloader/20260814T0746Z`(scope C-1~C-4) 처리, `_resolved/`로 이동.
신규 `scripts/fetch_dart_alotmatter.py`(`OpenDARTClient` 무수정, `_get` 직접 호출만 추가) —
39/39개사(AIG는 corp_code `00983606` 직접 지정, 이름검색 quirk) × FY2023-2026 × 4개
reprt_code = 624셀 전수 fetch, 레이트리밋/에러 0건. 캐시: `data/dart/_alotmatter_cache/`(원본
그대로, `_fs_api_cache`와 동일 관례). status 000=310·013=314, 013은 기존 확인된 14개
구조적 미제출사 + 2026 미도래 분기에 수렴(신규 결측 패턴 아님) — census `data/_derived/
alotmatter_fetch_census.json`.

owner의 오늘 1회성 참조답지(`배당현황_OpenDART_2023Q4-2026Q2.xlsx`, 루트)와 교차검증 —
**한화생명 2023.4Q 1건 불일치 발견**: 그 xlsx는 API 호출을 생략하고 웹조사로 "무배당" 단정한
셀인데, 재수집 raw는 실제 배당(현금배당금총액 112,709백만원, 보통주 주당 150원) 확인 — **재수집
쪽이 정답**, xlsx는 참조용 오답 1건. 파싱 함정 2종(보통주/종류주 중복 se행·status=000 전항목
"-" vs status=013 구분)도 raw에서 실측 확인, parser 통지에 명시. parser 후속 발주:
`inbox/parser/20260814T0938Z`(마스터 `dividend.json` 빌드 → designer가 `공시보고서.html`
채우는 체인, C-4).

**🟢 2026.2Q 반기보고서 — 상장 24개사 전원 제출 완료, FS API 4/24 · 본문 3/24 확보 (2026-08-14,
owner "거의 다 올렸을걸?" 재확인 → 재스카우팅으로 3회차 완결):** 3회차는 두 스냅샷으로 진행—
1차 스냅샷(위 changelog 2026-08-14c)은 6개 신규 rcept만 포착(KB손보·KDB생명·DB생명 FS API
확보, 메리츠화재·롯데손보·서울보증은 아직 미반영) → parser 통지 `inbox/parser/20260814T0245Z`.
**이어진 2차 스냅샷(같은 회차, 몇 분 뒤 재확인)에서 실제로는 21개사가 한꺼번에 신규
제출된 상태였음이 확인됨**: 메리츠화재·롯데손보·흥국화재·삼성화재·현대해상·KB손보·DB손해·
NH농협손해·삼성생명·ABL생명·흥국생명·KDB생명·교보생명·미래에셋생명·DB생명·푸본현대생명·
동양생명·KB라이프·농협생명·서울보증·코리안리(전부 오늘자 "반기보고서 (2026.06)" 원본 1건씩,
정정 아님). 신한라이프(2회차)까지 합쳐 **오늘 신규 22사 + 8/13 한화 2사 = 상장 universe
24/24 제출 완료.** 나머지 14사는 구조적 미제출(NON_LISTED_SKIP/AUDIT_REPORT_ANNUAL — 이
문서양식 자체를 안 냄), AIG는 `NO_CORP_MATCH` 불변.

FS API 캐시 21개사 일괄 `--refresh` → **4개사만 즉시 반영**(KB손보·KDB생명·DB생명 +
**서울보증(KR0150)도 이 시점엔 반영 완료** — 1차 스냅샷 때의 013에서 갱신됨, OFS BS 항등식
전부 검산: 자산 9,259,640=부채 4,265,939+자본 4,993,701 백만원), 나머지 17개사는 DART
쪽 아직 013. **본문 XML은 22개사 전부 여전히 `status:014`**(list 등재 vs 문서서빙 간
DART 전파지연 — 21사가 한꺼번에 몰려 큐가 밀린 것으로 추정, 정정-rcept 오선택 버그 아님).
parser 통지(완결판, 1차 스냅샷 결과 포함): `inbox/parser/20260814T0612Z`. 회신 3차 완결:
`inbox/downloader/20260814T0149Z`(status: open). **owner 지시대로 재스카우팅 계속** — 다음
재호출 시 22개사 body XML + 17개사 FS API 재시도.

**4회차 재확인(같은 날, 후속 호출) — 변화 없음.** body XML 22개사 재시도 전부 동일 `014`,
FS API 미확보 17개사 라이브 `--refresh` 재실행도 신규 반영 0건(4/21 그대로) — 두 시스템 모두
DART 쪽에서 정체 중인 상태 그대로. **owner 지시대로 재스카우팅 계속 필요**, status `open` 유지.

**🟡 2026.2Q 반기보고서 스카우팅 2회차 — 신한라이프 신규 확보, body는 DART 전파지연 (2026-08-14,
owner HIGH):** `scripts/scout_2026q2_halfyear.py` 재실행 → **신한라이프생명보험(KR0094) 신규
확보**(rcept 20260814001090, 3번째 확보사). FS API 캐시는 즉시 확보(`00137517_2026_11012_
{OFS,CFS}.json`, status=000, OFS 기준 BS 항등식 59,078,872=51,810,614+7,268,258 검산 완료) →
parser raw-ready `inbox/parser/20260814T0538Z`. **본문 XML은 `status:014`**(list.json엔
등재됐는데 document.xml 서빙이 아직 안 붙음 — 5분 간격 재시도 2회 동일, DART 쪽 전파 지연으로
판단, 정정-rcept 오선택 버그 아님) → 다음 재호출 때 재시도. 한화생명·한화손보 불변, 나머지
35사 미제출, AIG손해 기존 `NO_CORP_MATCH` 불변. 회신 2차: `inbox/downloader/20260814T0149Z`
(status: open, 실질 36사 잔여). **owner 지시대로 재스카우팅 계속** — 다음 재호출 시 동일 스크립트.

**🟡 2026.2Q 반기보고서 법정기한 당일 스카우팅 1회차 (2026-08-14, owner HIGH):** 오늘이
반기보고서(A형) 법정기한. 39사 `resolve_corp` 재조회 1회차 결과 **8/13과 변화 없음 —
2/39 확보(한화생명 KR0068·한화손보 KR0002), 나머지 36사 미제출, AIG손해는 기존
`NO_CORP_MATCH`.** 재사용 스크립트 `scripts/scout_2026q2_halfyear.py` 신규 작성(반복
스카우팅용, PeriodTarget 로컬 구성 — 기존 `ifrs17_batch_historical.py` 전역 레지스트리
불변). FS API 캐시(`fetch_dart_fs.py`, 소유권=downloader)는 확보된 2사분 11012 OFS+CFS
실데이터 확인 완료. **owner 지시대로 "한 번 돌고 끝내지 않기" — 오늘~내일 재스카우팅 필요**
(다음 세션 또는 재호출 시 위 스크립트 재실행). 상세: `docs/changelog_downloader.md` 2026-08-14.

**equity_composition item10 백필 라운드3 완료 (2026-08-14):** parser 요청 24셀(KR0001/2/3
×4분기, KR0005/8/9/10/11×2분기, KR0079×1, KR0150 2026.1Q) 전부 fetch+무결성 확인.
KR0150은 `EXCLUDED_SKIP` 우회 신규 `scripts/fetch_kr0150_2026q1.py`. parser raw-ready
통지 완료(`inbox/parser/20260814T0235Z`). 상세: `docs/changelog_downloader.md` 2026-08-14.

**18사 2026.1Q 정정본 FS API 캐시 확인 완료 (2026-08-14):** `2026_11013`(1Q) 캐시가
세션 시작 전 이미 일괄 갱신되어 있던 상태를 발견·검증(mtime 오늘 07:33경, 교보생명 8/13
2차 정정 이후, 전부 status=000) — 재페치 불필요로 확정, `inbox/downloader/20260814T0149Z`
D-3 답변에 반영.

**🔴 2026.1Q 정정공시 18사 raw 교체 (2026-08-13/14, owner 지시):** "26.1Q 정정공시 뜬 애들도 다 받아서
넘겨" → 39사 전수 재조사(bgn_de=20260101) 결과 **18사가 [기재정정]분기보고서(2026.03)를 냈는데 raw는
전부 정정 전 구버전(5/14~15 최초본)이었음.** 구버전 zip+xml을 `data/_archive/20260813T235249Z/`로
이동(보존) 후 정정본 재취득 + xml 재추출, 18사 전부 보험계약마진 키워드 확인. 교보생명만 오늘(8/13) 2차
정정, 나머지 17사는 5/29~6/1 1차 정정(기존에 이미 이 구버전으로 파싱됐을 가능성 — 수치 변경 여부 미확인).
parser/ifrs17 핸드오프 `inbox/parser/20260814T0000Z`(우선순위: 교보생명 → 나머지 17사, raw diff로
숫자변경 여부 판단 후 재적재 필요분만). 나머지 21사는 정정 이력 없음(원본 그대로 유효).

**재스카우팅 (2026-08-13, owner "한화생명 반기보고서 게시" 제보 → 39사 전사 재조사):** DART 39사(kics_disclosure
원수사명 기준, `resolve_corp` name-search) 전수 조회 — **한화생명(KR0068)·한화손해보험(KR0002) 둘 다 8/13
반기보고서(2026.06) 게시 확인**(같은 날 동시). 나머지 37사는 미게시(교보생명 2건·농협생명 1건·미래에셋생명
1건 A형 신규는 전부 `[기재정정]`뿐, 반기 아님). AIG손해만 상시 `NO_CORP_MATCH`(기지 known, EXCLUDED_SKIP).
raw 취득 완료: `data/dart/FY2026_Q2/raw/KR0068_한화생명/20260813001536.xml`(22.3M자)·
`.../KR0002_한화손해보험/20260813001433.xml`(16.2M자), 키워드 확인(보험계약마진 366·170회) →
parser/ifrs17 raw-ready `inbox/parser/20260813T0600Z`. 법정기한(8/14) 하루 전 조기게시 — 한화그룹이 최초
필러. 나머지 37사는 8월 중~말 순차 예상(KB손보 과거패턴 8/29~31), 재스카우팅 계속.

**4-source 체제 (2026-08-03부터)** — `bonds`(FSC data.go.kr) 소스 폐지, 5→4(정기경영공시/DART/KIDI/IR). 상세: `docs/changelog_downloader.md` 2026-08-03. 자본성증권 데이터 자체는 소멸 아님 — DART per-bond로 이미 대체(2026-06-20).

이전 5-source 전수 수집 완료 (as of 2026-06-01). 무결성 **2,041/2,041 OK**. **전 source 실질 gap 0** (NONLIFE-Q123 26셀 자체사이트 backfill + 서울보증 분기/DART는 미상장·롤오프 구조적 drop). 상세 history는 `docs/changelog_downloader.md`.

**Parser 핸드오프 주의 (Q2=반기):** AIG손해(KR0029)는 별도 2분기 공시가 없고 **상반기(반기) 누적** 공시로 FY{Y}_Q2를 채움(1.1~6.30 누적, 독립 분기 아님). 신한EZ(KR0051)·카카오페이(KR1098)의 Q2도 "상반기" 라벨. parser/validation에서 이들 Q2를 standalone-quarter가 아닌 cumulative-반기로 해석할 것.

검증 도구: `scripts/audit_all_periods.py`(전수 gap audit) + `scripts/check_data_file_integrity.py`(파일 무결성). 신규 다운로드 후 이 둘을 게이트로 실행.

**2026.2Q 공시 스카우팅 (2026-07-30):** K-ICS 정기경영공시 = 아직 전무. 생보협회 일괄페이지(pub.insure.or.kr) 22사 전부 2분기열 "-" 확인, 손보 3사(KB·삼성화재·한화손보) 개별사이트도 Q1만. DART는 39사 전수(corp_code 재검색, 영구매핑 없음) 반기보고서(A유형) 0건 — 법정기한 반기말+45일=8/14 전이라 정상. IR도 대부분(현대해상·삼성생명·한화생명) Q1만. **예외: 동양생명(KR0087)만 자체 IR자료실에 "FY2026 상반기실적발표자료" 선공시(07-27)** — DART "연결재무제표기준영업(잠정)실적(공정공시)"도 동일자 병행 공시. KB손보 과거 패턴(2015~2025 전부 8/29~31)상 나머지는 8월말 예상. 재스카우팅은 8월 중순 이후 권장.

동양생명 건은 owner 지시로 **fetch 완료**: `scripts/download_ir_2026q2_dongyang.py` 신규(source-catalog KR0087 셀렉터가 신규 행 prepend로 밀림 → board-item 텍스트 anchor로 교체) → `data/ir/FY2026_Q2/raw/KR0087_동양생명/`에 PDF(1.18MB)+XLS(233KB) 확보, magic bytes 확인. parser/ifrs17 raw-ready `inbox/parser/20260730T0010Z`. 나머지 12개 IR 출처는 8월 중순 이후 `download_ir_2026q2.py` 풀패스로 별도 처리 예정(아직 미작성 — Q1 스크립트가 13사 중 8사만 성공했던 이력 있으니 재작성 시 실패 5사도 같이 점검).

**재스카우팅 (2026-08-03, owner 요청):** DART 22사 재확인 — Q2 반기/분기보고서 여전히 0건, 신규 항목은 전부 routine(임원소유상황·자율공시 등). 삼성화재가 07-31 IR개최 안내공시 신규 등록했지만 자체 IR페이지 확인 결과 아직 FY26 1분기까지만 게시(과거 패턴상 상반기는 08-13경 예상, IR개최공시=실적공개 아님). 생보협회 일괄페이지 22사 전부 여전히 2분기열 "-". **동양생명 외 변동 없음.**

**🔴 KIDI(보험개발원) 발견 — `data/kidi/premium_summary.json` 부재:** owner가 "신규매출 데이터 확인 중이냐"고 질문해서 처음 점검. `data/kidi/FY*_Q*/raw/`에 회사당 1개씩(KR0080 AIA만, 2026-06-08 단발성 디버그런 추정)만 남아있고 TODO의 "F2 완료(38사×13Q=494)" 산출물인 `premium_summary.json`은 디스크에 없음(`data/kidi/`는 gitignore 대상이라 git으로 복구 불가). 소비측 `scripts/crawl_assoc_nb_premium.py`가 이 파일 부재 시 **에러 없이 조용히 빈 dict로 스킵**해서 `nb_premium_wolnap.json`/`NB_CSM_multiple.json`이 KIDI 교차검증 없이 override/IR-benchmark만으로 돌고 있었을 가능성 — 원인 미상, 조사 필요. 라이브 `getML01LastYM`/`getMN07LastYM` 확인 결과 최신월=202604(4월)로 아직 6월(Q2) 데이터는 미공개. **`scripts/ingest_kidi_monthly_premium.py` 풀재실행(39사×13분기말, rate-limit 코드 없음 주의)으로 복구 필요 — owner 승인 대기.**

**재스카우팅 (2026-08-06, owner 요청 — 생보/손보 top5=10사 표적조사):** DART API(list.json, pblntf_ty=A, 20260601~20260806): 10사 전원 반기보고서 0건(NH농협생명만 1분기 [기재정정] 1건, Q2 아님) — 법정기한(반기말+45일=8/14) 전이라 정상. KIDI latest=202604(4월) 그대로, 8/3과 동일. 생보협회 일괄페이지: 22사 전부 2분기열 "-" 불변(타깃 5사 포함). 손보 개별사이트 4/5 직접확인(메리츠·삼성화재·KB손해·DB손해 전부 1분기가 최신, 작년도 등록일 패턴상 8월말 예상) — 현대해상만 hi.co.kr 홈페이지가 브라우저 도구에서 반복 렌더링 hang(WebFetch도 JS라 콘텐츠 미포착)이라 미확인, 나머지 4사와 동일할 것으로 추정되나 미검증.

**신규 발견: IR(그룹 팩트북) 채널이 정식 공시보다 먼저 상반기를 냄** — KB금융그룹 팩트북에 `2026년도 상반기`(1분기보다 최신), NH농협금융지주 팩트북에 `NHFG Factbook 1H26` 확인됨(둘 다 kbfg.com/nhfngroup.com 직접 조회). 동양생명 07-27 선공시(`FY2026 상반기실적발표자료`)와 동일 패턴 — 그룹 IR이 DART/경영공시보다 먼저 잠정 상반기 실적을 공개. DB손보 팩트시트는 아직 1분기뿐(2026.05.15 등록). 나머지 IR(삼성생명·삼성화재·현대해상·신한금융그룹·메리츠금융그룹)은 JS-heavy라 이번 세션 도구(Browser+WebFetch)로 콘텐츠 확인 실패 — 차기 세션 재시도 필요. **owner 승인(같은 세션) → fetch 완료**: `data/ir/FY2026_Q2/raw/_groups/kb_financial/kbfg_2026_2Q.pdf`(1.94MB, `%PDF-1.7` 확인) + `.../nh_financial/nhfg_2026_2Q.xlsx`(2.61MB, `PK\x03\x04` 확인 — **주의: NH는 이번 분기 xlsx만 제공**, 작년 동분기 `nhfg_2025_2Q.pdf`는 PDF였음, 사이트 자체가 xlsx 아이콘으로 명시했으니 오류 아님). 둘 다 direct href(fileDownUtil.jsp / disclosureDown.do)라 PowerShell `Invoke-WebRequest -UseBasicParsing`으로 직접 fetch(브라우저 클릭다운로드 아님). **파서 handoff 전 확인 필요**: 그룹 합산표라 KB손해/KB라이프, NH농협손해/농협생명 사별 분해가 안 되면 parser가 못 쓸 수 있음(source-catalog "group factbook" 기존 caveat과 동일 이슈) — parser가 열어보고 사별 분해 가능한지 우선 확인할 것.

**교차확인(같은 날 별도 스레드):** `inbox/_resolved/20260730T0823Z__owner__KR1098...kakaopay_nb_csm_1000x_half_done.md`에서 parser/ifrs17도 독립적으로 동일 gap에 부딪힘 — `NB_CSM_multiple.json` 재계산 중 "`data/kidi/premium_summary.json`이 로컬에 없음... 이 세션 네트워크 스코프 밖"이라 월납월초보험료 값을 그냥 보존만 하고 넘어감. **두 세션이 독립적으로 같은 결손을 확인** — 우연/일회성 아님, 실제로 다운스트림을 막고 있음. owner 승인 시 재수집 진행.

**인박스 드레인 (2026-08-03):** `inbox/downloader/` 7건 처리 — 3건(BNP KR0075 FY24/25, 신한이지 KR0051 FY25, 카카오페이 KR1098 FY24) DART 감사보고서 raw 재취득 완료(전부 비상장·F유형만 존재, corp_code 신규 검색) → `data/dart/FY{2024,2025}_Q4/raw/KR####_.../`, `extract_dart_zips.py`로 언집, 보험계약마진/보험금융손익 키워드 확인. parser/ifrs17 raw-ready 회신 남김. 흥국화재/흥국생명 "wrong document type" 티켓(07-07)은 **이미 07-07 당일 다른 세션이 vision-read로 해결 완료된 건의 미정리 사본**이었음 — fitz 렌더링으로 재검증 후 중복 제거, `_resolved/`의 정본 기록 확인. 백로그 다이제스트 2건은 TODO 추적으로 정리(OCR-MARKETRISK 1건만 여전히 open, owner 결정 대기).

**bonds 소스 폐지 게이트 재확인 (owner 질문, 2026-08-03 T01:50Z):** 선행조건 2개 상태 재조회 —
validation(`20260803T0056Z`) **✅ resolved**(5건 전부 착지, RED=0, mutation-test 통과). parser
(`20260803T0055Z`)는 **status: answered**(소스교체 자체는 완료·RED=0이지만, 자기 완료조건 ①"발행잔액
회사 ≥24사"가 하나손보(KR0050)·아이엠라이프(KR0076) DART raw 부재로 미충족 — 이 2사분을 downloader에
새 티켓(`20260803T0123Z`)으로 재발주해둔 상태였음). **즉 착수 아직 불가 — "resolved 둘 다"라는 원 게이트
문구를 아직 못 채움(answered≠resolved).** 다만 그 신규 티켓은 그 자리에서 바로 처리: KR0050/KR0076
FY2025 감사보고서(별도) raw 재취득 완료 → `data/dart/FY2025_Q4/raw/KR00{50,76}_.../`, 신종자본증권
키워드 확인, parser에 raw-ready 통지(`inbox/parser/20260803T0150Z`, 나머지 4건도 함께 배치 통지 —
이전에 개별 티켓 답변만 하고 parser 자신의 inbox엔 새 알림을 안 남겼던 누락을 이번에 같이 보정).
**parser가 이 2사를 편입 → forward_capital 재실행 → 완료조건 충족 후 owner가 최종 resolved로 확정하면
그때 착수 가능.**

**같은 체인 3파(owner "inbox 확인+중단작업 처리" 요청, 2026-08-03 T05:46Z):** 재드레인 결과 신규 2건 도착
— validation(`20260803T0405Z`)·parser(`20260803T0535Z`) 둘 다 **같은 3사**(KR0049 악사손해·KR0150
서울보증·KR1010 교보라이프플래닛) capsec raw 부재를 지목(새 게이트 `CAPSEC_COVERAGE_REGRESSION`,
RED 13→3으로 좁혀진 잔여분). 두 티켓 통합 처리: 3사 FY2025 raw 전부 fetch(**서울보증은 상장이라 사업
보고서 확보** — 2024.4Q부터 정기공시 재개된 상태, 본문에 신종자본증권/후순위 각 1회. 악사손해·교보라이프
플래닛은 감사보고서만). `validate_data_contract.py` 직접 재실행해 RED=3이 정확히 이 3사와만 일치함을
확인(추가 미발견 gap 없음) — parser raw-ready 통지(`inbox/parser/20260803T0546Z`). **interrupted-work
점검**: data/dart 전역에서 document.zip/xml 없이 meta.json만 있는 디렉터리 23개 스캔 — 전부
`{"no_filing": true}` 정당 마커(비상장 감사보고서 전용사의 Q1-Q3 없음, 예별·IBK연금 등)로 확인, 진짜 미완료
fetch 0건. zero-byte/1KB 미만 document.zip도 0건 — downloader 도메인엔 그 외 중단 작업 없음.

**재스카우팅 (2026-08-13, owner 질문 — 뉴스 당기순이익 vs 정식공시 구분):** owner가 메리츠화재·
한화생명·한화손보 당기순이익 뉴스를 보고 2026.2Q 정식 소스 공시 여부 질문 → 실시간 재확인. **뉴스 출처
= DART "영업(잠정)실적(공정공시)"/"연결재무제표기준영업(잠정)실적(공정공시)"** 3사 전부 2026-08-12
신규 제출 확인(메리츠화재는 비상장 자회사라 지주사 메리츠금융지주 명의로 "자회사의 주요경영사항" 공시).
**정식 반기보고서(DART A유형, IFRS17 CSM 주석 포함)는 3사 전부 여전히 0건**(법정기한 반기말+45일=8/14,
오늘 8/13=마감 하루 전이라 정상). K-ICS 정기경영공시도 3사 전부 미공시 재확인: 메리츠화재
meritzfire.com 최신=CY2026 1/4분기(상반기 행 없음), 한화손보 hwgeneralins.com "2026년" 행 1/4분기만
채워지고 상반기 열 공백, 생보협회 일괄페이지(pub.insure.or.kr) 22사 전부 2분기열 "-"(한화생명 포함).
08-06 스캐닝과 동일 결론 — **잠정실적(공정공시)와 정식 K-ICS/IFRS17 공시는 별개 트랙**, 후자는 아직.
재스카우팅은 반기보고서 법정기한(8/14) 경과 후 권장.

**인박스 드레인 (2026-08-13, 오늘자):** 3건 확인. D1-D4(아래 항목, 이미 답변완료)는 `_resolved/`로
정리만. 신규 1건 처리: validation이 `20260813T1330Z`에서 삼성생명(KR0069) DART FS API 캐시 2개
(`00126256_2025_{11012,11014}_CFS.json`, 반기·3분기)의 재무상태표 자산·부채총계가 1분기 값에
붙박여 있다고 신고(자본총계는 분기마다 정상 갱신 — 파일 통째 stale이 아니라 그 안의 특정 계정만
고정). `fetch_dart_fs.py --refresh 00126256 2025`로 라이브 재조회 → **같은 값이 소수점까지 동일하게
재확인됨**(4개 reprt 전부 status=000, 013 아님) — 캐시 문제 아니라 **DART API가 반기·3분기보고서
조회 시 재무상태표 자산·부채 태그만 1분기 값을 돌려주는 소스 결함**으로 확정. PL_breakdown(IS만
읽음)은 무관, 신규 equity_composition의 BS 항등식 체크에만 영향. 캐시 교체 불필요, validation에
documented exception 등재 근거로 회신(`status: answered`, validation 재확인 대기).

**인박스 처리 (2026-08-13, owner 발주 — equity_composition 신규 마스터용 소스 확보):**
`inbox/downloader/20260813T0422Z` (D-1~D-4) 처리 완료(resolved). ① `source-catalog.yaml`
dart 블록에 누락돼 있던 `fnlttSinglAcntAll`(fs_all) 엔드포인트 선언 추가. ② 24개사
`fetch_dart_fs.py --refresh <corp> 2023`로 라이브 강제 재조회 → **24/24 전부 2023 1Q·2Q
공히 status=013 확정**(캐시버그 아님, DART API 구조적 공백) → 영구결측 등록. ③ XBRL 전무
15개사(14+예별) 전부 비상장 감사보고서(F형) 전용 확인(`universe.py` 분류와 1:1 일치), 본문
XML 전부 이미 `data/dart/FY*/raw/`에 확보돼 있어 신규 fetch 0건(AIA생명=KR0080도 6건 확보
완료 확인 — source-catalog "non-KR AIA" 표기가 stale이었을 뿐). 'None_*.json' 캐시 버그
원인 = KR0029 AIG손해보험 name-search 실패(기존 문서화된 quirk, 신규 아님) — 무해한 잔재라
삭제 안 함. ④ FISIS 앵커는 타당성만 확인(API 실재+별도 인증키 필요, 보험사 코드체계/AOCI
listNo는 미탐색 — 파이프라인 구현 안 함, owner 판단 대기). parser raw-ready
`inbox/parser/20260813T0530Z`.

**같은 세션 후속 확인 (owner가 "전분기 다 받았냐" 재질문) — 24개사 나머지 10분기까지 전수
재검증하다 서울보증보험(00112998/KR0150) 추가 gap 발견·해결.** 다른 23개사는 2023 1Q/2Q만
결측이지만 KR0150은 **2023 전체 + 2024 전체가 013**, 실질 Tier-1은 **2025.1Q~2026.1Q(5개
분기)뿐**. 2024 세 분기는 fetch 시도 자체가 없었던 것(파일 부재)이라 방금 최초로 라이브 fetch해
013 확인(캐시버그 아님). parser 통지에 반영 완료.

**인박스 드레인 (2026-08-13, 추가분 — equity_composition item10 주석백필 raw)**: parser가 남긴
2건 처리(`inbox/downloader/20260813T1425Z` KR0104 전체 + `20260813T1954Z` 18개사 부분,
둘 다 resolved→`_resolved/`). **KR0104 티켓의 "0건 전체 FY" 주장은 오탐**이었음 — 티켓이 쓴
`find -maxdepth 2`가 실제 leaf 깊이(3)보다 얕아 애초에 아무것도 못 찾는 명령이었음; canonical
path helper로 재검증하니 2025.4Q·2026.1Q는 이미 raw 有, 실결측은 9개 분기뿐. 18개사 티켓 쪽
gap 목록(108셀)은 재검증 결과 정확했음(같은 오탐 아님). **총 117셀 fetch, 전부 zip무결성+
IFRS17키워드 확인**: 표준 유니버스 17개사는 `ifrs17_batch_historical.py --pilot --periods
--skip-extract`를 period-set 서명별 8회 그룹 실행(KR0104 포함 — 9분기 gap이 다른 6개사와
동일 서명이라 합류). **서울보증(KR0150) 3건은 `EXCLUDED_SKIP` 유니버스 필터에 걸려 표준
CLI 불가** → `resolve_corp`+`process_one_period` 직접 호출하는 신규 `scripts/
fetch_kr0150_item10_quarters.py`로 우회(KR0004류 기존 one-off 패턴 재사용), 3/3 성공.
parser raw-ready `inbox/parser/20260813T2153Z`.

**부수 발견·수정 — `BATCH-HISTORICAL-FIX` 실발화**: KR0104 2023.4Q fetch 중 기존 문서화된
정정-rcept 오선택 버그가 처음으로 실제 에러(status=014)를 냄 — FY2023 사업보고서 후보 중
`[첨부정정]`이 원본보다 먼저 골라짐. `ifrs17_batch_historical.py:fetch_rcept_no`를 "대괄호로
시작하는 report_nm 전부 제외"로 수정 후 재시도해 해결(정정 아닌 원본 rcept 20240401002122
확보). 이번 배치 나머지 116셀은 원래 원본이 primary[0]라 버그 영향 없었음. **미확인 잔여
리스크**: 2026-05-30 이래 누적된 전체 DART 이력 중 이 버그로 조용히(에러 없이) 정정본이
골라진 셀이 있을 가능성 — `[첨부정정]`이어도 document.xml이 성공 응답하는 경우가 있어 항상
에러로 드러나지는 않음. 이번 세션은 오늘 두 티켓 스코프만 처리, 소급 전수 재검사는 안 함
(아래 BATCH-HISTORICAL-FIX 행에 상태 갱신).

---

## Active follow-ups (next sessions)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| ~~HKF-WAF-BLOCK~~ | ~~흥국화재(KR0005) FY2024_Q4 정기경영공시 재취득~~ | ✅ **2026-07-07 완료(재취득 불필요로 정정)** | WAF 때문에 재다운로드는 결국 못했지만 **필요 없었음** — 원인 재조사 결과 **기존 raw가 이미 맞는 파일**이었음(폰트인코딩 깨짐으로 fitz 텍스트추출만 실패, 렌더링+비전으로 읽으면 정상 정기경영공시). 흥국생명(KR0071)도 동일 패턴(스캔이미지+뒤에 감사보고서 합본). 양사 item1-28(전/후)·item36 등을 raw에서 직접 판독해 `kics_disclosure.json` 반영, 게이트 RED 0. 상세: `docs/changelog_downloader.md` 2026-07-07, `TODO_parser_kics.md` 8차 |
| F7 | **KOSIS 손보사별 손해율 시계열 ingest** | 🔴 P1 | 출처: 국가통계포털 KOSIS `orgId=382, tblId=TX_38202_A1561`. JSON API 공개 → 자동화 쉬움. 손해보험사별 원수보험료/보유보험료/경과손해율 (개별사 × 분기/연간). 현재 손해율은 PDF/HTML 파싱 기반 → KOSIS 교차검증으로 품질 보완. **액션**: `scripts/ingest_kosis_loss_ratio.py` 신규 + `data/kosis/<stamp>/` |
| F8 | **손보협회 비교공시 (consumer.knia.or.kr) — GA 인사이트** | 🔴 P1 | 핵심 항목: (a) **채널별 불완전판매비율** (GA/직판/방카 구분) (b) **설계사정착률** (c) **민원발생현황** (d) **보험금 부지급률** (e) **보험금 지급지연율**. **액션**: 사이트 구조 probe (JS-rendered 가능성 점검) → API 또는 scrape 결정 → `data/knia_consumer/` |
| F9 | **data.go.kr 금융통계 API 추가 연동** | 🟠 P2 | 이미 자본성증권 (15059611) 연동 패턴 있음. 추가: (a) `15061307` 금융통계손해보험정보 (b) `15061306` 금융통계생명보험정보 (c) `15094797` 실손보험정보. **액션**: `src/bonds/fsc_client.py` 패턴 재활용해서 `src/finstat/` 신규 모듈 작성 |
| F10 | **GA 통합공시 (gapub.insure.or.kr)** | 🟠 P3 | GA별 불완전판매비율/계약건수/모집실적. **액션**: 사이트 구조 probe |
| F14 | **규제 뉴스 피드** (roadmap §1E) | 🟠 P3 | 최근 1주 규제뉴스 스크래핑 + 키워드 피드백 학습 랭킹. 큐레이션 피드(자동발행 X) |
| DART-RAW-PROVENANCE | DART raw 23사×13분기 source_file+as_of 사이드카 (`emit_dart_raw_provenance.py`) | 🟠 P2 | Phase 2 gate: CSM_waterfall/PL_breakdown 마스터 provenance 필요. bonds 완료, DART raw 잔여 |
| CAPSEC-SAMO-GAP | 삼성생명·악사·하나손해·AIA·삼성화재 사모채 per-bond 데이터 없음 | 🟠 P2 | FSC 0건, DART 0건 확인. 공개소스 없음. forward-sim에서 BS 총계 기반 단순가정 처리 불가피 — publishing 결정 필요 |
| OCR-MARKETRISK | 시장위험 스캔-only PDF OCR 경로 | 🟢 low (2026-08-15 owner pass) | KB손해·한화손해 2023.4Q 금리위험 = full-page 이미지(텍스트레이어 없음); 카카오페이 2025.4Q 시장위험 = 스캔. 파서가 fitz/pdfplumber로 텍스트 못 뜸 → OCR 필요. **owner "됐어 패스" — 두 옵션(downloader OCR 스택 도입 / owner 수동 OCR) 다 보류, 재요청 전 미착수.** 출처 `inbox/downloader/20260614T1232Z` item(2) |
| MISC-SEIBRO | Seibro HTML fallback | 🟢 low | m.seibro.or.kr smoke ok; lower priority since FSC works |
| ~~REORG2-DART~~ | ~~DART batch script 3개 canonical-layout refactor~~ | ✅ **2026-05-30N 완료** | `scripts/_dart_path_helpers.py` 신규 + 3 script 갱신 + smoke 9/9. 다음 분기 fetch는 `data/dart/FY<year>_Q<q>/raw/` canonical 위치에 쌓임 |
| BATCH-HISTORICAL-FIX | ~~`ifrs17_batch_historical.py` 정정 rcept picking 버그~~ | 🟠 P2 (코드 fix 완료, 소급감사 잔여) | **2026-08-13 코드 fix 완료**: KR0104 2023.4Q fetch 중 실발화(status=014, `[첨부정정]`이 원본보다 먼저 골라짐) → `fetch_rcept_no`를 "대괄호로 시작하는 report_nm 전부 제외"로 수정, 재시도 확인. **잔여**: 2026-05-30 이래 누적 DART 이력 중 이 버그로 조용히(에러 없이) 정정본이 골라진 셀이 있을 수 있음(첨부정정도 document.xml이 성공 응답하는 경우 있음) — 소급 전수 재검사 미실시, 필요시 validation이 우선순위 판단 |
| F15-DL | 동양생명 2025.2Q~2026.1Q 재다운로드 검토 | 🟠 P2 | (F15 본체는 parser 버그 — `TODO.md`) 추출단계에서 wide `<TE>` 표의 잔액(기초/기말)행이 전부 0으로 들어옴 → 원본 다시 받아야 할 수도 있음. 재다운로드 후 재파싱이 효과적인지 먼저 확인 |
| FUTURE-DL | DART 별첨 fetch endpoint 조사 (KB/메리츠/NH FY2025 LOB) | 🟠 P2 | KB/메리츠/NH FY2025 사업보고서는 LOB 표를 별첨 감사보고서로 분리. 결정 2026-05-30: **fetch 안 함** (본문에 다 있음, 회사별 라벨 변형 처리로 해결). 단 별첨 endpoint 위치는 future reference로 기록 — 새 이슈에 필요 시 조사 |
| IR-SAMSUNGLIFE-23 | 삼성생명 IR FY2023 Q1/Q2/Q3 standalone factsheet 부재 | 🟢 low | samsunglife.com IR은 ~2년치만 보존 → FY23 Q1-Q3 standalone factsheet 롤오프됨 (2026-05-30P 확인). **단 데이터는 살아있음**: 보유 중인 `★ 4QFY23FactsheetKOR.xlsx`에 1Q~4Q 분기 컬럼 물리적 존재 → parser stage에서 구판 시트 레이아웃(`parse_factsheet`가 "월초대비 신계약CSM 배수" 라벨 못 찾음) 핸들링하면 복구 가능. **다운로더 액션 없음** — parser stage 이슈로 이관 |
| ~~NONLIFE-Q123~~ | ~~손보 6사 분기(Q1-Q3) 경영공시 — 회사 자체사이트 스크래퍼~~ | ✅ **2026-06-01 완료** | 34셀 중 **26셀 backfill 수집**(AIG 9 / 악사 4 / 신한EZ 4 / 코리안리 6 / 카카오 3), **8셀(서울보증)은 구조적 미발행** 판정. 사별 스크립트 `scripts/backfill_q123_<token>.py` (aig/axa/shinhanez/sgi/koreanre/kakaopay). 검증: 무결성 2,041/2,041 OK + audit disclosure REAL GAPS 0. ⚠️ AIG/신한EZ/카카오 Q2 = 반기 누적(위 핸드오프 주의 참조). 서울보증 = 자체사이트 연간+최신분기만 보존(audit `SGI_QUARTERLY_STRUCTURAL` 예외 등록) |
| ~~HEUNGKUK-CALL-FIX~~ | ~~흥국화재 신종자본증권1 콜 미행사 override~~ | ✅ **2026-06-17 완료** | normalize.py `_CALL_NOT_EXERCISED={"KR60005416C3"}` 추가 → 재실행 → KR0005 신종 3,200→**4,120억** (FS appendix 일치). normalize `20260616T153258Z`. provenance 재발행 |
| ~~CAPSEC-DART-FETCH~~ | ~~자본성증권 in-force per-bond DART fetch (KDB생명·농협생명)~~ | ✅ **2026-06-16 완료** | FSC 0→DART B-type 조사→KDB 2건(2,410억)+농협 2건(5,000억). 교보=미발행. 현대해상=FSC 정확(parser오류). `data/bonds/disclosure/2026q1_capital_securities.json`. `inbox/publishing/20260616T1300Z` |
| ~~PROVENANCE-BONDS~~ | ~~bonds provenance 사이드카 emission (Phase 2)~~ | ✅ **2026-06-16 완료** | `bonds_provenance.json`(24사) + `disclosure_bonds_provenance.json`(2사). as_of=2026-03-31, effective_filtered=true. `scripts/emit_bonds_provenance.py` |
| ~~CSM-CONTINUITY~~ | ~~CSM 워터폴 연속성(기말≠기시) 복구 raw~~ | ✅ **2026-06-16 완료** | owner: 2026.1Q 기시 전사 misparse(`FY2026_Q1` git-purge로 0 dirs). **우선 5사 2026.1Q**(교보·메리츠·신한라이프·에이비엘·푸본) + `validate_csm_continuity` break(코리안리 23.4Q→24.1Q 경계 + FY2023 드리프트 현대·에이비엘·KDB·교보 + FY2024 KB라이프·코리안리)→ **FY2023/FY2024 Q1-Q4 동반 = 33/33 fetched**, CSM블록 결손 0. break는 24.4Q/25.1Q 아니었음. parser raw-ready `inbox/parser/20260616T0640Z`. ⚠️rebuild은 복원분+기존 raw 범위 |
| ~~CAPSEC-VERIFY~~ | ~~자본성증권 발행현황 검증·수정 (owner 0506Z #2)~~ | ✅ **2026-06-16 완료** | registry **bare-stem alias 오수집** 발견·수정(메리츠/아이엠/미래에셋/카카오 → 계열사 채권 오태깅, 메리츠 1.77→19.6조 폭증). 4 alias 제거(`{nonlife,life}_insurer_registry.yaml`). 재크롤 clean(normalized `20260616T060817Z`): 22/24 live 동일, 🔴KR1098 카카오페이 3,202억→0(가짜), 🟢KR0099 KB라이프 0→1,200억(누락분), KR0011 −890(정상). big-3 Face 정확→owner T2 BS −11.6%는 parser BS시가측 추정. parser-kics `inbox/parser/20260616T0615Z`. ⚠️tier 재빌드는 publishing/parser gate |
| ~~NBCSM-INTERIM~~ | ~~NB CSM 시계열 오염 복구용 interim DART raw~~ | ✅ **2026-06-16 완료** | parser/ifrs17 발주(validation partial-extract 오염). git-purge로 부재한 반기/분기보고서 raw를 `ifrs17_batch_historical.py --skip-extract`로 **10사×{2025.2Q,2025.3Q,2023.1Q}=30셀 fetch-only 재취득**(30/30). CSM 블록 29/30 존재(우선 7셀 OK, 롯데 2025.2Q NB=0 최악건 포함). 🔴 honest gap: 롯데 2023.1Q CSM표 부재(도입초 축약, census whitelist). parser raw-ready `inbox/parser/20260616T0420Z`. ⚠️마스터 rebuild은 raw 전체복원 세션에서 |
| ~~KR0004-MG-DART~~ | ~~예별손해(구 MG=엠지) DART 감사보고서~~ | ✅ **2026-06-16 완료** | KR0004는 비상장 → DART 정기보고서 0 = universe 부재(통째로 0이었음). 외부감사 감사보고서(F)는 존재 = DART entity '엠지손해보험'(corp `00962861`). **별도·FY2023~ 3건 적재**(owner 스코프; FY2022 IFRS4·연결 제외). `data/dart/FY{Y}_Q4/raw/KR0004_엠지손해보험_<rcept>/`(00760 별도). IFRS17 주석 확인(보험계약마진 36~59). `scripts/fetch_kr0004_mg_dart_audit.py`. parser/ifrs17 raw-ready `inbox/parser/20260616T0210Z` |
| ~~KR0004-MG-HISTORY~~ | ~~예별손해(구 MG) 과거 11분기 K-ICS 공시~~ | ✅ **2026-06-16 완료** | parser bounce(round3 K2): KR0004가 26.1Q만 적재, 그 이전=구 MG 명의. 2023.1Q~2025.3Q **11분기 전수 fetch(11/11 OK)** from `yebyeol.co.kr`(예별=구 MG 동일 법인, 2013~ 전 분기 아카이브). 결산 ZIP 본문="엠지손해보험" 확인. text-layer OK(OCR 불필요). `scripts/backfill_kr0004_mg_quarters.py`. KR0004=2023.1Q~2026.1Q 13분기 연속 확보. parser raw-ready `inbox/parser/20260616T0145Z` |
| ~~SEOULBO-DART~~ | ~~서울보증 DART 8셀~~ | ✅ **2026-06-01 drop (won't-fix)** | 사용자 결정("서울보증 걍 버려"). 미상장(IPO 철회) → DART 분기/반기/사업보고서 미공시 = 구조적. audit `DART_DROP`에 등록 → 전 source REAL GAPS 0 |
| ~~IR-DONGYANG-401~~ | 동양생명 IR factbook (myangel) 401 — disclosure로 부분 해결 | 🟢 low | **2026-05-30R: 사용자 지적으로 생보협회 경영공시(pub.insure.or.kr)로 대체 → disclosure 13/13 완성** (`download_dongyang_disclosure_q4.py`로 FY2023_Q4·FY2024_Q4 결산 2개 받아 채움). 동양생명 검증 데이터는 disclosure(IFRS17 주석 포함)로 확보됨. IR factbook(myangel) 자체는 여전히 401 차단 — **IR factbook 전용 지표(CSM배수 등)가 disclosure에 없어 별도로 필요할 때만** 재시도: (a) non-headless+다른IP로 raon ozvid auth header 캡처 (b) DART 본문 fallback. 현재는 low priority |

**전략적 시너지 (코리안리 리포트 인과 체인 재현):**
- F8 (설계사정착률) + F8 (채널별 불완전판매비율) + 37회차 해지율 (별도 source)
- = "GA 채널 → 해지율 → 손해율" 인과 체인을 공시 데이터만으로 재현
- → insurequant 프리미엄 기능 후보

---

## User decisions (downloader-scoped)

| # | Decision | Date |
|---|----------|------|
| D5 | API keys: repo root `.env` only (gitignored). `OPENDART_API_KEY` / `DATA_GO_KR_BOND_ISSUANCE_KEY` / `DATA_GO_KR_BOND_REDE_KEY`. Never commit/log key values. **2026-08-03: `bonds` source retired (`inbox/downloader/20260803T0057Z`) — the two `DATA_GO_KR_BOND_*` keys are kept as-is (not deleted) since F9 (`source-catalog.yaml` future_sources_planned, same data.go.kr portal) may reuse them.** | 2026-05-24 |
| D6 | Bond Call rule: issue + 5y for ALL bonds (Korean market convention; ignore "콜" keyword gate). Past 5y = assume `called` (de facto mandatory per thebell/흥국 cases) | 2026-05-24 |
| DL-FYR | **Next quarter onwards (2026.2Q+)**: find URLs / XPaths yourself. 2026.1Q only was user-provided. Reuse existing configs, swap only period-specific labels. Escalate to user only if site structure fully changed | 2026-05-30 |
| DL-NOATTACH | **Don't fetch DART attachments (별첨/감사보고서 zip).** Body XML has all IFRS17 disclosures. Verified 2026-05-30 (한화 647 / KB 259 / 농협생명 176 / 라이나 audit 55 / AIG audit 55 occurrences of `보험계약마진` in body) | 2026-05-30 |
| DL-NOTSKIP | KR0029 AIG + KR0150 SGI **K-ICS skip** (no PDF on their own sites), BUT **DART**에서는 받을 수 있는 만큼 받음 (AIG = "에이아이지손해보험" corp_code 00983606 / SGI = 2024.4Q 이후 분기보고서 시작) | 2026-05-30 |
| DL-DART-C-FY23 | bucket C 빈 dir 121건 분류: 110 = 비상장 11사 Q1-3 (DART 분기보고서 구조적 미제출, gap 아님) + 11 = 비상장 11사 **FY2023_Q4 감사보고서 = 받지 않음** (사용자 결정 2026-06-03, "비상장사 감사보고서 불필요" 유지). → 비상장사 DART PL/CSM 시계열 = **FY2024_Q4 + FY2025_Q4 2포인트로 확정** (extract_dart_zips로 추출 완료). 다음 세션 재제기 금지 | 2026-06-03 |
| DL-2022Q4-HOLD | 법정준비금 항목5-8용 2022.4Q 본문 XML 24사 = **보류, 지금 안 받음**. 항목5(해약환급금준비금)는 소급가정치뿐이라 항목6·7(비상위험·대손준비금) 실측만 목적이면 받을 값어치 있었으나, 재요청 전까지 미착수(`inbox/downloader/20260819T0820Z` 발주 E) | 2026-08-19 |

---

## Done — recent (one-liners; detail in changelog / data manifests)

| ID | Task | Done |
|----|------|------|
| SENS-FY25 | IFRS17 CSM 민감도 FY2025 사업/감사보고서 raw 28사 전수 적재 (FY2024 고정 해소) — DART 회사명검색, `data/dart/FY2025_Q4/raw/`, 28/28 공시·실패0, KR prefix 통일. 추출(sensitivity)은 parser/ifrs17로 라우팅(`inbox/parser/20260615T0520Z`) | 2026-06-15 |
| G8 | NB CSM배수 25.4Q 누락 3사 FY2025 감사보고서 raw 복원 (AIG/카카오페이손해/하나생명) — 라이브 DART 재취득 + `KR0029_` prefix 정정 + IFRS17 키워드 검증. 추출 교정(magnitude misparse + 하나생명 audit-annual)은 parser/ifrs17로 라우팅(`inbox/parser/20260614T1330Z`). 단순 refetch 아님 = 파서 추출 이슈로 확정 | 2026-06-14 |
| F2 | KIDI ML01/MN07 NB CSM crawler (38사×13Q=494, premium_summary.json) | 2026-05-30 |
| DL-FY26Q1 | FY2026.1Q full ingest (손보17+생보22+IR13+DART) | 2026-05-30 |
| DL-DART-AUDIT | DART raw 100% audit + gap fill (`_inventory_manifest.json`) | 2026-05-30 |
| MISC-BOND | FSC bond issuance+Call ingest → per-ISIN calendar (tier1 63 + tier2 261) | 2026-05-25 |
| IFRS-HIST | Historical 13Q ingest 2023.1Q~2026.1Q (`ifrs17_batch_historical.py`) | done |
| DL-COMPLETE | 5-source 완결: 전수 audit + disclosure 28셀 backfill (gap 73→34) | 2026-05-31 |
| DL-ARCHIVE-PROBES | Archived 45 early IR auto-discovery probes (`scripts/_probes/`) → `data/_archive/20260602T150745Z_downloader_ir_probes/` (git rename, kept for foreign-insurer ref). Canonical `crawl_ir_*.py` untouched | 2026-06-02 |
| DL-DART-EXTRACT | Fixed parser `raw_not_extracted`: 42 insurer DART dirs had `document.zip` but no body XML (fetch-only + foreign filings have only `_00760`/`_00761` members, no main xml). New idempotent `scripts/extract_dart_zips.py` extracted them in-place; bucket A 40→0. Parser auto-picks via `*.xml` glob | 2026-06-03 |

---

## Reading order for downloader subagent

When invoked, read in this order:

1. This file (`TODO_downloader.md`) — current state and documented exceptions
2. `docs/agents/claude-agent-downloader.md` — master prompt (mission + 5 sources catalog + canonical layout)
3. `docs/agents/source-catalog.yaml` — machine-readable URL/XPath catalog
4. `data/dart/_inventory_manifest.json` — DART coverage; avoid re-fetching
5. `data/disclosure/_meta/FY*/_manifest.json` — per-period manifests
6. `data/ir/_*.json` — IR manifests (`_db_manifest.json`, `_db_decks_manifest.json`, `_hyundai_manifest.json`, `_kr_map.json`)

Deferred (2026-07-27): `docs/changelog_downloader.md` is history — open it only when you need the background of a past decision; most sessions don't. For cross-stage context, see root `TODO.md`.

---

NOTE: English only where Korean encoding is fragile. Korean content preserved here is read-only history; new entries prefer English. See `CLAUDE.md` "Document/TODO Encoding Rule".
