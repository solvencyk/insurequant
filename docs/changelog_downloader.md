# Insurequant Changelog — Downloader Stage

> Last updated: 2026-08-25 · Stage 1/5 — downloader
> Prompt: docs/agents/claude-agent-downloader.md · TODO: TODO_downloader.md

## 2026-08-25 -- DART raw 유실 45칸 복구 + 유실 탐지기 신설·배선 (`inbox/downloader/20260825T0001Z`)

parser(ifrs17)가 KB손해보험(KR0010) 2024.3Q~2025.3Q PL 이 5개 분기 통째로 비어 있다고 회부.
티켓 주장을 그대로 믿지 않고 `data/dart/FY*/raw/` 를 전수 census 했더니 **KB 만의 문제가
아니었다** — 구멍의 본체는 **손보 상장 코호트(KR0001·0002·0003·0005·0008·0009·0010·0011·1000)
× 2024.3Q~2025.1Q** 이고, KR0001·KR0010 만 2025.2Q·2025.3Q 까지 길었다. 티켓이 KB 만 짚은 건
그 회사의 census 관측범위만 2023.1Q 로 앞당겨졌기 때문이지, 나머지 8개사도 같은 상태였다.

**원인 = 디스크 유실.** 세 갈래를 각각 반증했다.
1. **원천 부재 아님** — `list.json` 조회 시 5개 분기 전부 원본 필링 존재(KB: `20241114002445`
   `20250314001697` `20250515001437` `20250814003072` `20251114001554`).
2. **negative cache 아님** — DART 문서 fetch 경로엔 영구 음성캐시가 구조적으로 없다
   (`process_one_period` 는 `meta.json` 에 `no_filing: true` 만 남기고 다음 실행에서 재조회).
   그래도 티켓 지시대로 FS-API 캐시를 전수 점검: 1,006개 중 **013 이 622개**, 전부 2026-08-19
   근본수정 이전 mtime 이라 원리상 영구히 굳어 있다 → **라이브 재호출로 실측**(제출기한 미도래
   100건 제외 522개 중 113개 표본 = KR0010 전건 + 2026.1Q/2Q 전건 + 연도별 층화). **113/113 이
   여전히 013, 회수 0건.** 남은 013 은 진짜 구조적 부재(비상장 XBRL 전무·2023 1Q/2Q 공백)이고
   8-19 수정은 제대로 먹었다. **깨끗한 축도 기록해 둔다** — 다음 세션이 다시 의심하지 않도록.
3. **유실이 맞다** — `data/dart/_inventory_manifest.json`(`audit_date: 2026-05-30`, 디스크
   스냅샷)에 그 칸들의 **zip 바이트 크기**가 적혀 있었고, 오늘 재취득한 zip 이 **정확히 일치**
   (KB: 183007·716493·207768·277541·219642). manifest 가 디스크 스냅샷이라는 것도 교차확인
   (2026.1Q 207195 = `data/_archive/20260813T235249Z/.../KR0010_KB손해보험/document.zip` 바이트).
   `data/_archive/` 어디에도 없으니 Reorg 이동이 아니라 삭제. **누가 지웠는지는 특정 못 했다** —
   `.gitignore:41` 이 `data/dart/**/raw/` 를 제외해 git 에 기록이 없다. 추측으로 적지 않는다.

**복구 45칸.** `ifrs17_batch_historical.py --skip-extract` + `extract_dart_zips.py`(zip→본문 XML).
검증 45/45: PK 매직 · `zipfile.testzip()` 무결 · 본문 XML 존재 · `보험계약마진` 25~405회(0건 없음),
`신계약`·`보험료배분접근법`·`보험손익`·`투자손익` 전건 확인. 재취득 후 `_inventory_manifest.json`
303칸 전수 대조 **디스크 누락 0**(2026.1Q 18건은 이후 재취득으로 바이트만 다름 — 정상).

**재발 방지 — 배선까지 했다.** 원인이 013 가드가 아니었으므로 거긴 손댈 게 없었고, 진짜 사각은
**"한 번 받아 놓은 raw 가 사라져도 아무도 모른다"** 였다. raw 는 gitignore 라 git 이 탐지도 복구도
못 하고, 이 구멍은 3개월 가까이 방치되다 다른 레인의 census 가 우연히 건드려 드러났다.
- 신설 `scripts/check_dart_raw_coverage.py` — 디스크에 한 번이라도 있었던 (period, 회사) 칸을
  `data/dart/_raw_coverage_baseline.json` 에 박제(high-water mark, **절대 줄지 않음**), 사라지면 RED.
  칸 판정 = `document.zip` 존재 + PK 매직(빈 껍데기 `no_filing` 은 칸이 아니다). 의도적으로 뺀
  칸은 `known_absent` 에 **사유와 함께** 옮기게 강제. 씨앗 395칸.
- **`scripts/prepush_check.py` 1d 단계로 배선** — `n_raw` 가 `blocked` 계산에 들어가므로 유실이
  있으면 **push 가 막힌다**. `CLAUDE.md` 의 "배선했다 ≠ 강제된다" 를 이번엔 처음부터 지켰다.
  raw 가 통째로 없는 slim 워크트리(main)에서는 스스로 skip → 배포 경로를 막지 않는다. 현재 exit 0.
- `tests/test_push_gate_wiring.py` 는 `scripts/validate_*.py` 만 열거하므로(`check_*` 는 대상 밖)
  매니페스트 수정 불필요 — `check_inbox_hygiene.py` 와 같은 취급. 테스트 55 passed 확인.

**잔여(스코프 밖, 기록만).** `raw_annual` 76건 중 디스크에 없는 5건을 추가 발견해 전부
`known_absent` 에 사유와 함께 등재(매 실행 인쇄): AIG 2022.4Q 감사보고서 2건(사유 미확정) ·
AIG 2023.4Q `…2106`(**연결감사보고서, 2026-08-17 티켓에 "참고용, 본체 아님" 으로 명시된 의도적
미취득**) · 교보라이프플래닛 2025.4Q 연결 · 하나손해 2025.4Q 연결(뒤 2건은 같은 "별도가 본체"
관례 추정, 명시 기록 없음).

parser raw-ready: `inbox/parser/20260825T0430Z__downloader__MULTI_2024.3Q-2025.3Q__pl_raw_gap_45cells_ready.md`.
원 티켓은 `inbox/_resolved/` 로 이동.

## 2026-08-21 -- KR0005/KR0071 2024.4Q wrong-document 재취득 — 1건 해결, 1건 원천 오문서 확인

`inbox/downloader/20260821T1625Z`(validation): 두 회사의 2024.4Q raw가 K-ICS 정기경영공시가
아니라 DART 사업보고서였고(텍스트레이어는 멀쩡한데 "경과조치" 0회, 꼬리말 dart.fss.or.kr),
그 상태로 "발행사 미공시" 면제가 잘못 등재돼 있었다 — 면제 해제 후 downloader로 회부.

**KR0005 흥국화재 — 해결.** kpub.knia.or.kr(손보협회 통합공시) 결산 2024 열에서 재취득
(일회성 `scripts/refetch_kr0005_kr0071_fy2024q4.py`, `backfill_nonlife_disclosure_kpub.py`와
같은 라우트, 기존 `WANT` 리스트는 안 건드림). 표지 "보험업감독규정 제7-44조" 문구 + p37
"[지급여력비율 총괄]" 표에 경과조치 전(154.01%)/후(199.56%) 24.4Q 수치가 명시돼 있어 정본
확인. `fitz` 텍스트검색으로 "경과조치" 0회가 나왔던 건 오탐이었다 — 이 문서는 프로즈/헤더는
네이티브 텍스트지만 **데이터 표는 래스터 이미지**라 텍스트 레이어 검색이 안 먹는다(240dpi
렌더 + 육안 판독으로 재확인). 기존 오문서(28,358,329B/367p)는
`data/_archive/20260821T044328Z/data/disclosure/FY2024_Q4/raw/`로 이동, 신규 검증본
(38,960,137B/96p)을 `data/disclosure/FY2024_Q4/raw/KR0005_흥국화재.pdf`에 설치.

**KR0071 흥국생명 — 원천 자체가 오문서, honest gap.** 독립된 두 경로를 시도했다:
(A) pub.insure.or.kr(생보협회 통합공시) 결산 컬럼, (B) 흥국생명 자사 사이트
(`heungkuklife.co.kr/front/public/manageList.do`, 번호101 "FY2024 결산 경영공시"). **둘 다
디스크의 기존 오문서와 SHA256이 완전히 동일한 파일을 반환** — 협회 일괄 경로와 자사 공시
채널이 모두 같은 잘못된 파일을 걸어두고 있다는 뜻이다. 538p 본문을 직접 열어 확인(p250·
p421 "지급여력" 부분매치)해도 K-ICS 제도 일반설명(적기시정조치 구간표)뿐, 흥국생명 고유
수치·표는 없다 — DART 사업보고서 그대로. 다운로더가 접근 가능한 표준 경로로는 정본을 구할
수 없다고 결론. 기존 파일은 그대로 둠(대체본 없이 지우면 자리표시만 사라짐), 면제 재등록
안 함(RED 유지가 맞음). owner 판단 필요 — 흥국생명 직접 문의 또는 정정 게시 대기.

**참고 (자사 사이트 접근 함정)**: `heungkuklife.co.kr`은 직접 URL 진입(특히 `www.` 없이,
또는 첫 headless goto)에 "현재 잘못된 접근경로" 에러를 반환한다 — 메뉴 클릭 흐름(session/
referer)을 요구하는 사이트. `www.` prefix + 홈 방문 후 진입으로 재현 가능하게 우회함.

parser hand-off: KR0005는 raw ready이나 경과조치/지급여력기준금액 상세 표가 이미지라 OCR
경로 필요(기존 pdfplumber EOF→fitz fallback과는 다른 갭). KR0071은 여전히 못 넘김,
`POST_TRANSITION_PARENT_MISSING` RED 4건 유지. 상세: `inbox/downloader/20260821T1625Z` 답변
(status: answered, 완결 아님).

## 2026-08-20b -- alotMatter negative-cache 버그 수정, 2026.2Q 배당 19사 복구

owner가 "26.2Q 배당현황 다시 시작하자"며 `inbox/downloader/20260820T1600Z`를 남김.
`dividend.json` 2026.2Q가 24사 중 5사뿐이라 파고들어 보니, **`fetch_dart_fs.py`가 8/19에 고친
것과 완전히 동일한 버그**가 `fetch_dart_alotmatter.py`엔 이식이 안 돼 있었다: alotMatter
도메인 온보딩이 2026-08-14였는데 그날이 반기보고서 법정기한 당일이라 DART가 색인하기 전에
013("조회된 데이터가 없습니다")이 돌아왔고, `fetch_one()`이 status를 안 가리고 무조건
캐시에 썼다 — 게다가 `--refresh` 플래그 자체가 없어서 스크립트를 다시 돌려도 이미 파일이
있으니 그대로 013을 반환, 재취득 경로가 원천 차단돼 있었다.

**수정**: `fetch_one()`이 `status=="000"`일 때만 디스크에 쓰도록(`fetch_dart_fs.py` L134와
동일 패턴), 신규 `refresh_year_reprt(client, year, reprt)` + CLI `--refresh <year> <reprt>`로
지정 슬라이스를 유니버스 전체 강제 재조회. `fetch_dart_fs.py`의 `--refresh <corp> <year>`와
스코프 축이 다른 이유: 이번 사고는 특정 회사가 아니라 **특정 회차(반기법정기한 당일에 긁은
배치) 전체**가 오염됐으므로 (corp, year) 단위보다 (year, reprt) 단위가 이 사고 형태에 맞다.

**재취득 결과** (`python scripts/fetch_dart_alotmatter.py --refresh 2026 11012`, 39사 유니버스):
`000: 5→24`, `013: 34→15`(19사 복구). AIG(KR0029)는 `resolve_corp()` 이름검색 quirk로 유니버스
루프에서 빠져 corp_code `00983606` 직접 지정으로 별도 확인 — 역시 013, 최종 15개 안에 포함
(39/39 전수 확인 완결). **남은 15개 013은 캐싱 문제가 아니라 구조적 legit-absent** —
2026-08-13 FS-API 온보딩 때 독립적으로 확인된 "XBRL 전무 15개사(14+예별, 전부 비상장
감사보고서만 제출)" 집합과 정확히 1:1 일치한다. 두 서로 다른 DART API(fnlttSinglAcntAll,
alotMatter)가 같은 15개사에서 같은 이유(사업보고서/반기보고서 자체를 안 냄)로 막힌 것 — 우연이
아니라 구조. 기존 2023~2025 캐시는 `(year, reprt)` 스코프 밖이라 무영향.

parser raw-ready: `inbox/parser/20260820T1720Z` (blocked_on이던 `20260820T1540Z` 재개 트리거,
`build_dividend.py` 재빌드 + `tests/test_dividend_golden.py --update` 필요).

## 2026-08-20 -- 재드레인: 악사손해 등 5사 연혁 백필 + status-sweep 정리

owner가 IFRS17.html에서 직접 지적(`inbox/downloader/20260819T0620Z`): "악사는 2025.4Q밖에
BS정보가 없네 왜지?" 실측하니 KR0049(악사)·KR0050(하나손해)·KR0051(신한이지)·KR0076(아이엠
라이프)·KR1010(교보라이프플래닛) 5개사가 전부 `FY2025_Q4` 딱 1건 raw만 있고 그 이전은
아예 폴더가 없었다 — FY2025_Q4 온보딩 때 처음 받은 회사들이라 과거분을 받은 적이 없었음.

**진단 먼저, 그다음 fetch.** 어제 AIG(KR0029)에서 "사업보고서"로 검색하면 no_filing만
나온다는 걸 직접 겪었던 터라, 이번엔 5개사 전부 `list_filings(pblntf_ty=None)`로 먼저
전체 필링 이력을 뽑아봤다 — 예상대로 **5개사 전부 비상장이라 감사보고서/연결감사보고서만
내고 사업보고서는 한 번도 안 냈다.** 원 요청 문구가 "사업보고서 raw 취득"이었지만 그대로
따라 검색했으면 21건 전부 `no_filing`으로 끝났을 것.

**FY2022~2024 3개년 21건 전부 알려진 rcept 직접 fetch로 확보**(신규 `scripts/
fetch_annual_only5_history.py`, AIG 우회와 동일 패턴 — `annual_raw_dir`+
`client.fetch_document_xml`만 직접 호출, `process_one_period`의 A001 검색은 안 씀). 하나손해·
교보라이프플래닛은 감사+연결감사 둘 다(기존 FY2025_Q4 확보 관례와 동일), 나머지 3사는 감사만
존재. 21/21 zip무결성 통과, `보험계약마진` 키워드 전부 확인(4~60회, zero-hit 없음).

**"가능하면 전사 FY2022_Q4 백필"은 스코프만 정확히 잡고 미착수.** 현재 `FY2022_Q4/raw/`
보유 코드 11개(요청 원문의 6개 + 이번 5개)를 kics_disclosure 39사 전체와 대조 — **28개사
잔여**(KR0001·2·3·4·5·8·9·10·11·29·32·68·69·70·71·72·73·75·79·82·83·87·94·99·104·150·
1000·1098). 이 중 상당수는 정상 상장사라 표준 경로로 되겠지만 `ifrs17_batch_historical.py`의
`_make_targets()`가 2023.1Q부터 시작이라 2022.4Q 타깃 자체가 없고(새로 만들어야 함), 오늘
겪은 대로 회사별로 사업보고서/감사보고서가 갈릴 수 있어(AIG·5개사 전부 그랬다) 28개사를
한 번에 밀면 조용히 틀린 fetch가 섞일 위험이 있다고 판단 — 원 요청이 "없으면 5개사만이라도"
로 스코프를 열어뒀으므로 이번엔 필수분만 완결. parser raw-ready:
`inbox/parser/20260820T0052Z`.

**같은 회차, owner의 status-sweep 인박스 처리**(`inbox/downloader/20260820T0033Z`) — 78건
활성 스레드 중 51건이 answered인 채 원 sender 재확인 없이 방치돼 있다는 전 프로젝트 지적.
downloader 몫 3건 대응: ①`20260614T1232Z`가 (1) resolved 이후에도 `status: open`인 채
남아있던 걸 `answered`로 정정(OCR-MARKETRISK는 owner가 이미 보류 결정, 미결 아님) ②
`20260819T0116Z`(negative-cache)는 owner sign-off받아 `_resolved/`로 이동 ③
`20260819T0820Z`의 E항목(2022.4Q 24사)은 이미 전날 owner에게 직접 물어 "보류" 확정돼 있던
게 sweep 스냅샷엔 반영이 안 됐던 것뿐이라고 회신. sweep 자체도 resolved.

## 2026-08-19b -- 법정준비금 raw gap 인박스 처리 (A/B/C/D 완료, E owner 대기)

parser가 IFRS17_BS 항목5-8(해약환급금·비상위험·대손·보증준비금) 재작업 끝에 남은 결측이
전부 raw 미수집임을 확인하고 발주(`inbox/downloader/20260819T0820Z`, HIGH). 5갈래 요청 중
4갈래 처리:

**A(2023.2Q 19사 중 18사)+B(2023.1Q 11사 중 10사)** — `ifrs17_batch_historical.py --pilot
... --skip-extract` 표준 경로로 28건 전부 `fetched`, zip 안 `보험계약마진` 키워드 전부
실측(28~212회, zero-hit 없음).

**C(KR0150 서울보증, 2023.1Q~2024.4Q 8분기)** — `EXCLUDED_SKIP` 유니버스 필터라 표준
`--pilot`에 안 걸림(기존 `fetch_kr0150_item10_quarters.py`와 동일 우회 필요) → 신규
`scripts/fetch_reserve_gap_kr0150_kr0029.py`. **7분기 `no_filing` 확정**(DART에 정기보고서
자체가 없음 — 기존 문서화된 "2024.4Q부터 정기공시 재개" 사실과 정확히 일치, 새 결손
아니라 재확인), **2024.4Q만 fetched**(rcept `20250324000440`). 여기서 `보험계약마진`=0이
나와서 처음엔 오문서 의심했으나, 서울보증은 보증보험 전업이라 구조적으로 CSM이 없는
회사(기존 "CSM-0 정상" 판정과 동일 선상) — 대신 준비금 특정 키워드(비상위험준비금 32회·
대손준비금 26회)로 재확인해 진짜 재무제표 본문임을 확정. PDF-wrong-document 패턴과 같은
함정이라 반드시 다른 키워드로 교차확인했다.

**D(AIG KR0029 FY2024_Q4)** — 처음엔 `process_one_period`(사업보고서/A001 검색)로
시도했는데 `no_filing`. `pblntf_ty` 필터 없이 전종류 재조회해보니 **AIG는 2023~2026 전
기간 사업/반기/분기보고서를 아예 안 내고 감사보고서·연결감사보고서만 낸다** — 기존에
이미 확보돼 있던 FY2023_Q4 raw(`20240403002101`)도 실은 감사보고서였는데, 폴더가
annual(`FY..._Q4`) 버킷에 들어가다 보니 지금까지 아무도 눈치 못 챘던 것. 알려진 rcept
직접 fetch로 감사보고서(`20250409001949`)+연결감사보고서(`20250409001951`) 2건 확보,
`보험계약마진` 51회씩. 이 사실은 parser에게도 참고사항으로 명시(사업보고서 구조를
가정하는 코드가 있다면 이 회사엔 안 맞을 수 있음).

**E(2022.4Q 24사)** — 미착수. 원 티켓이 스스로 "owner 판단 필요"로 스코프를 열어뒀음
(항목5는 2023년 신설 제도라 2022년말 값은 회사가 FY2023 필링에 소급 가정치로만 남긴
전기열이고, 항목6·7만 목적이면 지금 받아도 되지만 항목5까지 필요하면 파서 쪽에 소급
전기열 수확기를 별도로 만들어야 함) — downloader가 임의로 결정하지 않고 owner에게
그대로 질문 전달.

parser raw-ready: `inbox/parser/20260819T0841Z`. 같은 드레인에서 완결된 스레드 4건도
정리(halfyear scout D-1/D-2/D-3 최종 완결 확인, viewer_fallback 사후확인 2건, IR
factsheet 재수집 완료분) → `_resolved/`.

## 2026-08-19 -- FS API 영구음성캐시 버그: 2026.2Q 9/10사 복구 + 근본 수정

owner가 마스터 xlsx "17BS" 시트에서 `IFRS17_BS.json` 2026.2Q가 24사 중 14사뿐임을 발견,
직접 원인까지 진단해서 발주(`inbox/downloader/20260819T0116Z`) — 캐시 파일 mtime이 전부
반기보고서 접수(8/14) 다음날 새벽(8/15 00:32~02:00)이라, DART FS API가 아직 재무제표를
색인하기 전에 긁혀서 013(무응답)이 그대로 굳었다고 정확히 짚었다. 이 시점은 나의 8/15
새벽 시간당 재시도 루프(2026.2Q body XML 스카우팅)와 겹치는 창 — 그 세션의 `--refresh`
호출들이 원인일 가능성이 높음.

**9개사 재취득**: 메리츠화재해상보험·삼성생명보험·현대해상·교보생명보험·농협생명보험·
동양생명·미래에셋생명보험·NH농협손해보험·KB라이프생명 — 전부 OFS `status=000` 회복,
BS 항등식(자산=부채+자본) 검산 전부 통과. **흥국화재(10번째)는 재취득해도 BS 1행
(사용권자산)뿐** — owner가 미리 예견한 "한화손보 4-row blank shell"류로 확인, 캐시버그가
아니라 DART API 응답 자체의 빈 껍데기. parser에 본문 XML 폴백 대상으로 명시해 raw-ready
통지(`inbox/parser/20260819T0140Z`).

**근본 수정** (`scripts/fetch_dart_fs.py`): `_fetch_raw`가 `status=000`(성공)일 때만
캐시 파일에 쓰도록 변경 — 013은 그 호출에서만 반환되고 디스크엔 안 남아, 다음 호출 때
다시 라이브로 확인한다. 부수 수정: `_refresh_cache`가 재fetch 전에 기존 파일을 먼저
지우던 구조였는데, 이제 013을 안 쓰다 보니 "지우고 → 013 받으면 → 완전 결측"이 될 수
있어 **사전삭제 제거**(force=True가 성공시에만 덮어써서, 실패해도 기존 좋은 캐시가
보존됨). 기존에 이미 확정된 영구결측(2023 1Q/2Q 24개사, 비상장 15개사 등)은 캐시 파일이
이미 있어 매번 재확인 없이 그대로 재사용 — 이번 변경으로 API 호출이 늘지 않음.

## 2026-08-17 -- 인박스 드레인: AIG 2023.4Q raw(push게이트 마지막 RED) + IR D-1/D-2 종결

**AIG손해보험(KR0029) 2023.4Q 감사보고서** — validation이 push 게이트 마지막 RED 1건
(`PL_CSM_AMORT_VS_WATERFALL`)의 근거로 정확한 corp_code(`00983606`, 이름검색 불가 등록명
"AIG")와 rcept(`20240403002101`)를 지정해서 요청 → 직접 fetch,
`data/dart/FY2023_Q4/raw/KR0029_에이아이지손해보험_20240403002101/`, 보험계약마진 52회·
상각 117회 확인. FY2024_Q4는 요청 스코프 밖(parser가 FY2025 전기컬럼으로 이미 해결)이라
안 받음. parser raw-ready `inbox/parser/20260817T0231Z`.

**IR D-1(실패3사 재시도)/D-2(9사 우선순위 확인) 종결** — `inbox/downloader/20260815T0907Z`
(2026-08-15에 발주됐던 LOW 우선순위 티켓, 오늘 드레인하며 마무리):
- 삼성생명(KR0069): 실패 dump 확인 결과 SPA(sslife_v1) JS 렌더링이 기존 wait_ms=3000보다
  오래 걸리는 문제로 진단 → `wait_networkidle: True` + `wait_ms: 6000`으로 스크립트 수정,
  재시도 성공(`SLI 1HFY26 Factsheet_KOR.xlsx`, 799KB).
- 코리안리(KR1000): 재시도해도 동일 `ERR_EMPTY_RESPONSE` → 루트 도메인에 순수 HTTP로
  직접 찔러봐도 연결 자체가 거부됨 확인 — 이 페이지만이 아니라 `koreanre.co.kr` 전체 장애.
  재시도로 해결 불가, documented gap으로 보류.
- 롯데손보(KR0003): WAF 차단 페이지("Web firewall security policies") 재확인, 스크립트·
  수동 브라우저 동일 — bot-detection 우회 시도 안 함(정책), documented gap.
- 한화손보(KR0002): 9사 우선순위 목록에 있었지만 IR 소스 카탈로그에 없던 이유를 site
  직접 확인으로 규명 — `/notice/ir/main.do`("공시실")가 유일 IR 경로인데 이건 정기경영공시
  성격(Source 1a)이지 별도 factsheet 코너가 아님. 구조적 결측으로 확정.
- 최종 11/13(삼성생명 신규 확보분 반영), 9사 우선순위 중 7/9.

**부수 발견 + 자체 수정 2건** (`scripts/download_ir_2026q2.py`):
1. **매니페스트 통째-덮어쓰기 버그.** 부분 재실행(2사만 타겟)했더니 원래 13사 매니페스트가
   2건으로 축소됨 — 실물 파일은 무사(경로 착각으로 "유실"로 오판할 뻔했다가 재확인), 기존
   매니페스트를 key 기준 merge하도록 수정해 재발 방지. `_meta.period`의 "FY2026_Q1" 복붙
   잔재도 "FY2026_Q2"로 수정.
2. IR 저장 경로가 두 관례로 혼재 확인 — 스크립트 자체 fetch는 `data/ir/FY2026_Q2/<key>_
   <name>/`(raw 하위폴더 없음), 기존 수작업 fetch(동양생명·KB/NH그룹)는 `data/ir/FY2026_Q2/
   raw/<key>_<name>/`. 이번 스코프 밖이라 통일 안 함, 기록만 남김(향후 세션 주의).

parser raw-ready는 IR 쪽은 발주 안 함(owner 지시 — KIDI 통계 나온 뒤 대조용으로만 씀).

## 2026-08-15c -- viewer_fallback 다중문서 이어붙임 버그, parser 빠꾸 → 로컬 재포장으로 수정

parser가 `inbox/downloader/20260815T0230Z`로 어제(2026-08-15b) 배송한 14개사 viewer_fallback
raw를 반송. **원인**: `report/viewer.do`가 섹션마다 완전한 `<!DOCTYPE><HTML><HEAD><BODY>
...</BODY></HTML>` 통짜 문서를 돌려주는데(실제 뷰어에서 iframe 임베드용으로 쓰는 형식),
내 스크립트가 이걸 wrapper 안 벗기고 그대로 이어붙여서 파일 하나에 독립 HTML 문서가 최대
146개(삼성생명) 겹쳐 있었음. `lxml.etree.HTMLParser`가 두 번째 문서부터 "Misplaced DOCTYPE"
에러를 내고 첫 문서(표지, 표 4개)만 파싱 — **CSM 워터폴 14개사 전부 0건, PL breakdown도
7개사 완전 0건**(나머지 7개사는 이 raw와 무관한 FS-API 캐시 폴백 덕에 일부만 생존)으로
parser가 실제 파싱 시도 중 발견.

**내 검증 방법(`full_doc.count(keyword)`) 자체가 맹점이었음** — 문자열 카운트는 문서 경계를
안 보니 146개 문서에 흩어진 키워드를 다 세어서 통과한 것처럼 보였다. "성공"으로 잘못 보고한
점 인정.

**수정 — 재fetch 없이 로컬 재포장:**
1. 이미 받은 14개사 raw를 내가 넣어둔 섹션 구분자(`<!-- ===== id: text ===== -->`)로 재분해.
2. 각 섹션의 `<BODY>` 안쪽만 정규식으로 추출(`<BODY[^>]*>(.*?)</BODY>`).
3. 전체를 새 DOCTYPE/HTML/HEAD/BODY 껍데기 하나로 재조립, 같은 `document.zip`/`<rcept>.xml`
   경로에 덮어씀(경로·파일명 불변, parser의 `*.xml` glob·raw-ready 포인터 그대로 유효).
4. 일회성 스크립트 `scripts/fix_viewer_fallback_multidoc.py`로 실행(14개사 전부 자동).

**검증은 parser와 동일한 도구(lxml)로 재현**: `Misplaced DOCTYPE` 에러 14개사 전부 0건, 표
인식 524(NH농협손해)~2857개(삼성생명) — 기존 "4개만 인식"에서 정상 범위로 회복. CSM 키워드
카운트는 수정 전후 완전 동일(예: 삼성생명 563회 그대로) — 내용 손실 없이 구조만 교정 확인.

**원인 스크립트도 수정** — `scripts/fetch_dart_viewer_fallback.py`가 이제 fetch 단계에서부터
`<BODY>` 추출→단일문서 조립을 하도록 고쳐서, 이 경로를 다시 쓸 때(정본 API 복구 전 신규
배치 등) 같은 버그가 재발하지 않음.

parser 재확인 요청 회신: `inbox/downloader/20260815T0230Z`(status: answered — 포맷 검증은
통과했지만 실제 CSM/PL 추출 정상화는 parser 재파싱이 정본, 그쪽 확인 대기). 중복 방지로
원 raw-ready 티켓(`inbox/parser/20260815T0130Z`)은 이 스레드로 합류시켜 `_resolved/`.

## 2026-08-15b -- DART 웹뷰어 우회 fallback 신설, 2026.2Q body 정체 14사 전부 해소

owner "당장 실시 후 파서에게 발주" — API가 24h+ 막힌 나머지 14개사를 신규 우회경로로 확보,
상장 24개사 전원 body raw 확보 완료.

**메커니즘**: `dsaf001/main.do?rcpNo=`(뷰어 셸)를 열면 전체 문서목차가 `node1/node2/node3`
JS 객체(text/id/rcpNo/dcmNo/eleId/offset/length/dtd)로 인라인 임베드돼 있음 — 이걸 정규식으로
파싱해 각 섹션을 `report/viewer.do?rcpNo=&dcmNo=&eleId=&offset=&length=&dtd=`로 순회
요청하면 그 섹션 HTML을 돌려줌. 둘 다 인증/세션 불요, 브라우저로 첫 발견 후 순수
`requests.get()`으로 재현 확인. 신규 `scripts/fetch_dart_viewer_fallback.py`.

**1차 시도 버그 2개 → 재수정 후 14/14 성공:**
1. **트리 깊이별 변수명 불일치.** `node3`만 매치하는 정규식으로 1차 실행 → 6개사(NH농협손해·
   ABL생명·흥국생명·교보생명·푸본현대생명·KB라이프)가 4~8섹션만 잡힘(주석 섹션 전체
   누락 — 예: NH농협손해는 재무제표(4-1~4-4)만 잡히고 "5. 재무제표 주석"(76만자)이 통째
   빠짐). 원인: 회사마다 노트가 `node3` 자식들로 잘게 쪼개지거나(삼성생명류, ~30개 소단위)
   `node2` 하나로 통짜(NH농협손해류)로 실려있어 트리 깊이가 다름. `node\d+`로 전체 매치하도록
   수정.
2. **부모-자식 중복 위험.** 위 수정만 하면 삼성생명류(부모 "3. 연결재무제표 주석" 자체가
   630만자로 자식 30개 전체를 포함)에서 부모+자식을 같이 받아 노트 섹션이 통째 중복.
   트리 구조를 몰라도 되는 방법으로 해소: **offset/length 수치 범위가 다른 노드를 포함하면
   그 노드는 제외**(leaf만 채택) — 삼성생명류는 부모 제외+자식 유지, NH농협손해류는 애초에
   포함관계가 없어 그대로 유지, 양쪽 다 정확히 동작 확인.
3. 네트워크 타임아웃 6건(흥국화재·삼성화재·DB손해·삼성생명·동양생명·코리안리) → 백오프
   재시도(최대 3회) 추가로 해소.

**최종 14/14**: 섹션 48~146개, 1.2M~4.8M자, IFRS17 핵심 키워드(보험계약마진/보험료배분접근법/
신계약/보험손익) 전부 확인(동양생명만 "신계약" 0회 — 라벨 변형 추정, parser 판단으로 라우팅).
저장 경로는 정본과 동일(`document.zip`에 `<rcept>.xml`, `*.xml` glob 그대로 작동) +
`meta.json`에 `"source": "viewer_fallback"`로 출처 구분. parser 통지: `inbox/parser/
20260815T0130Z`.

**앞서 확보한 5개사(메리츠화재·KB손해보험·KDB생명·DB생명·서울보증) 결과 확인**: parser가
CSM/PL 반영 완료 회신(`inbox/parser/20260815T0015Z`) — 4개사 CSM 워터폴 정확히 폐쇄, 서울보증은
PAA 구조상 CSM 없는 게 정상 판정. 확인 후 `_resolved/`로 아카이브.

## 2026-08-15 -- 2026.2Q body XML 24h+ 정체 확인: 웹뷰어엔 있는데 API export만 막힘

owner 재질문("지금도 안되니") → 재스카우팅. **5개사 신규 확보**(메리츠화재·KB손해보험·KDB생명·
DB생명·서울보증, body+FS 캐시 둘 다 refreshed) — body 확보 누계 3→8/24. 나머지 16개사는
여전히 `document.xml status:014`(어제 rcept 그대로).

**진단 상향 — 단순 propagation-lag가 아닐 수 있음.** DART 웹뷰어(`https://dart.fss.or.kr/
dsaf001/main.do?rcpNo=<rcept>`)로 삼성생명(20260814003263)·코리안리(20260814003862) 직접
확인: **둘 다 문서목차·다운로드 버튼까지 완전히 렌더링됨**(회사개요 등 정상 트리). 같은
rcept로 API `document.xml` 즉시 재시도해도 여전히 014. → **문서 자체는 DART에 존재·서빙되고
있는데 OpenDART API의 zip export 파이프라인만 별도로 막혀있는 상태**로 재진단(index만 뜨고
본문이 안 붙은 게 아니라, 본문은 이미 붙어있고 API 전용 패키징만 안 됨). 24시간을 넘긴 정체는
기존 propagation-lag 사례(보통 시간 단위 내 해소)와 다른 패턴. FS API(fnlttSinglAcntAll)
쪽 16개사 재확인은 백그라운드 실행 중, 결과는 다음 항목에서 갱신.

TODO 상태를 🟢(안정)에서 🟡(재검토 필요)로 되돌림 — owner 판단 대기(계속 대기 vs 웹뷰어
스크레이핑 등 대체경로).

## 2026-08-14e -- 신규 도메인 온보딩: 배당에 관한 사항(DART alotMatter) 39사 전수

owner `inbox/downloader/20260814T0746Z` — KRFS 세션에서 19사×4시점 1회성 수집했던 배당현황을
정식 회기별 정기 수집 도메인으로 편입, 후속 addendum(20260814T1250Z)에서 스코프를 최소안(19사)
대신 **전사안**(kics_disclosure 커버리지 39사 × FY2023-2026 × reprt_code 4종)으로 확정.

신규 `scripts/fetch_dart_alotmatter.py`: `OpenDARTClient` 클래스는 무수정, `client._get(
"/api/alotMatter.json", ...)` 직접 호출만 추가(지시 준수). corp_code 해결은 `fetch_dart_fs.py`의
`resolve_corp` 재사용("OO생명보험"→"OO생명" alias가 삼성생명·미래에셋생명에 이미 적용됨). 2-pass
설계(11011+11012 우선완주 → 11013+11014, rate-limit 대비) — 실제로는 에러 0건, 전량 1패스에
가깝게 완주. 캐시 `data/dart/_alotmatter_cache/{corp_code}_{year}_{reprt}.json`(원본 그대로,
`_fs_api_cache`와 동일 컨벤션 — 존재 시 skip, `--refresh` 강제갱신).

**KR0029 AIG손해보험만 이름검색 실패**(기존 문서화된 quirk) — 문서화된 corp_code `00983606`으로
직접 16셀 fetch(전부 013=배당공시 없음, resolve 실패지 fetch 실패 아님). 최종 **39/39개사 ×
624셀 전수 완주, status 000=310·013=314.** 013 분해: reprt별(11011 81·11012 77·11013 58·11014
82) · 연도별(2023 60·2024 59·2025 56·2026 123 — 2026이 압도적으로 높은 건 3Q·사업보고서가
아직 안 왔기 때문, 구조적). 013 전량이 기존에 이미 확인된 14개 구조적 미제출사(NON_LISTED_SKIP/
AUDIT_REPORT_ANNUAL — 오늘 반기보고서 스카우팅에서도 동일 14사가 "no_filing"이었음, 완전히
독립적인 두 도메인이 같은 회사 리스트로 수렴 — 강한 교차검증)와 2026 미도래 분기에 수렴. 상장사
16/16 완전커버 0개사이지만 이 역시 구조적(2026 최대 도달치가 14/16).

**함정 2건 raw 실측 확인** (owner 원 티켓 경고 그대로 재현):
1. 삼성생명 2023.4Q `주당 현금배당금(원)` 두 행 — 종류주 없어 두번째 행이 `thstrm='-'`
   placeholder(값 3,700 vs `-`). 한화생명 2023.4Q는 `stock_knd`가 실제 "보통주"/"우선주"로
   나뉨(150원/`-`) — 정상 케이스도 확인.
2. status=000+전항목`-`(무배당) vs status=013(무공시) 구분 필요 — census status 필드로 판별 가능.

**루트 `배당현황_OpenDART_2023Q4-2026Q2.xlsx`(owner 1회성 KRFS 산출물) 교차검증 — 1건 불일치.**
19사×4시점 대조: 53/53 대부분 일치(27 "배당있음" + 26 "무배당,전항목`-`"), `무배당(웹조사,
API조회 생략)` 표기 7건 중 6건도 일치하지만 **한화생명 2023.4Q는 그 xlsx가 오답** — 그 셀만
API를 안 부르고 웹조사로 "무배당" 단정했는데 raw는 실제 배당(현금배당금총액 112,709백만원,
보통주 주당 150원)을 보여줌. 재수집(API 기반)이 정답, xlsx는 참조로만 쓰고 마스터 소스로
승격하지 말 것(owner 지시 그대로 준수).

parser 후속 발주(마스터 `dividend.json` 빌드 → designer가 `공시보고서.html` "준비 중" 채우는
체인): `inbox/parser/20260814T0938Z`. downloader 몫은 완결 — 원 티켓 `resolved`로
`inbox/_resolved/`.

## 2026-08-14d -- 반기공시 스카우팅 3회차 완결: 실제로는 21사 동시제출, 상장 24/24 전원 확인

owner 재확인("지금은? 거의 다 올렸을걸?") → 2026-08-14c 스냅샷(6개 신규 rcept, 3사 FS
확보) 직후 재스캔했더니 **실제로는 21개사가 한꺼번에 신규 제출된 상태**였음(2026-08-14c가
잡은 6사는 이 21사의 부분집합). 전체 목록: 메리츠화재·롯데손보·흥국화재·삼성화재·현대해상·
KB손보·DB손해·NH농협손해·삼성생명·ABL생명·흥국생명·KDB생명·교보생명·미래에셋생명·DB생명·
푸본현대생명·동양생명·KB라이프·농협생명·서울보증·코리안리 — 전부 오늘자 "반기보고서
(2026.06)" 원본 1건씩(정정 아님). 신한라이프(2026-08-14b)까지 합쳐 오늘 신규 22사 + 8/13
한화 2사(2026-08-14) = **상장 universe 24/24 제출 완료**, 나머지 14사는 구조적 미제출,
AIG는 `NO_CORP_MATCH` 불변.

FS API 21개사 일괄 `--refresh`(`fetch_dart_fs._refresh_cache`, 스크래치 배치 스크립트로
루프 — `scripts/` 구조는 안 건드림) → **4개사 반영**: 2026-08-14c의 KB손보·KDB생명·DB생명
3사에 더해 **서울보증(KR0150)도 이 시점엔 013→000으로 전환 확인**(OFS 자산 9,259,640=
부채 4,265,939+자본 4,993,701 백만원, 항등식 검산). 나머지 17개사는 FS API도 여전히 013.
10분 간격 재스캔 2회, 4/21에서 변화 없음(스냅샷 안정 확인).

**본문 XML은 22개사(신한라이프 포함) 전부 `status:014` 불변** — list.json 색인과 문서서빙
간 DART 쪽 전파지연으로 판단(21사가 한꺼번에 몰려 큐가 밀린 것으로 추정, BATCH-HISTORICAL-FIX
류 정정-rcept 오선택과는 무관 — 후보 rcept가 회사마다 1건뿐이라 선택 로직 자체가 개입할
여지가 없음). parser 완결 통지(2026-08-14c의 3사 재확인 + 서울보증 신규 + 17사 pending
명시): `inbox/parser/20260814T0612Z`. owner 티켓 3차 답변 완결: `inbox/downloader/
20260814T0149Z`, status open 유지 — 다음 재호출 시 22개사 body + 17개사 FS 재시도.

## 2026-08-14c -- 반기공시 스카우팅 3회차: FS API가 body보다 먼저 열리는 패턴이 3사로 확산

owner 제보("지금 꽤 많이 올라와있다") → `scripts/scout_2026q2_halfyear.py` 재실행. body XML
기준 확보사는 3사(한화생명·한화손보·신한라이프) 불변, 신한라이프 body 재시도도 여전히
`014`. **신규 rcept 6사 발견** — 메리츠화재(KR0001)·롯데손보(KR0003)·KB손보(KR0010)·
KDB생명(KR0072)·DB생명(KR0082)·서울보증(KR0150), 전부 오늘 "반기보고서 (2026.06)" 원본
1건씩(정정 아님).

**FS API를 body와 무관하게 직접 시도(`fetch_dart_fs._fetch_raw` 직접 호출, reprt=11012) —
2회차 신한라이프 패턴이 재현**: 6사 중 3사는 이미 열려 있었음.
- KB손보(KR0010): OFS+CFS 둘 다 `status=000`, BS 항등식 검산(44,555,655=38,226,369+6,329,286)
- KDB생명(KR0072): OFS만(CFS `013`), 항등식 검산(16,143,656=15,617,471+526,186)
- DB생명(KR0082): OFS+CFS 둘 다, 항등식 검산(11,968,742=10,169,214+1,799,528)
- 메리츠화재·롯데손보·서울보증 3사는 FS API도 `013`(body·FS 둘 다 아직).

parser 통지(FS-raw-ready, body pending 명시): `inbox/parser/20260814T0245Z`. owner 티켓
3차 회신 완료, status open 유지(실질 잔여 33사, FS만 확보 3사, rcept만 찍힌 3사 별도 추적).

**부수 정리**: 이전 턴에서 KR0094 관련 중복 알림 파일(`inbox/parser/20260814T0245Z__downloader
__KR0094__halfyear_2026q2_raw_ready.md`)을 실수로 새로 만들었다가, 이미 더 상세한
`inbox/parser/20260814T0538Z`(2회차 산출물)가 존재함을 뒤늦게 확인하고 삭제 — 세션 중간
컨텍스트 압축으로 직전 라운드 작업 내역을 놓쳤던 것. 재발 방지: 반복 스카우팅 재호출 시
TODO/inbox 최신 상태를 먼저 읽고 회차 번호를 확인할 것.

## 2026-08-14b -- 반기공시 스카우팅 2회차: 신한라이프 신규 확보 (FS API 확보, body는 DART 전파지연)

owner 재호출(`inbox/downloader/20260814T0149Z` 2차) — `scripts/scout_2026q2_halfyear.py`
재실행. **신한라이프생명보험(KR0094, corp 00137517) 신규 확보**(rcept 20260814001090,
DART list.json에 "반기보고서 (2026.06)"로 오늘 신규 등재, 정정 아님 유일후보). `fetch_dart_fs.py
--refresh 00137517 2026` → FS API 캐시 `00137517_2026_11012_{OFS,CFS}.json` 둘 다 status=000
실데이터(OFS 213줄/CFS 244줄) 확보, OFS 기준 BS 항등식 직접 검산(자산 59,078,872 = 부채
51,810,614 + 자본 7,268,258 백만원, 정확히 닫힘) — `IFRS17_BS.json` 항목1-4 즉시 반영 가능.

**본문 XML은 아직 불가**: `document.xml`이 `status:014`("파일이 존재하지 않습니다") 반환,
5분 간격 2회 재시도 동일 결과 — list.json 색인과 문서 서빙 간 DART 쪽 전파 지연으로 판단
(BATCH-HISTORICAL-FIX의 정정-rcept 오선택 패턴과는 다름, 후보 rcept가 애초에 1건뿐). 다음
재호출 시 재시도 필요. parser에 FS API만 raw-ready로 통지(본문 pending 명시):
`inbox/parser/20260814T0538Z`. 한화생명·한화손보 불변 재확인, 나머지 35사 미제출, AIG손해
기존 `NO_CORP_MATCH` 불변. owner 티켓 `inbox/downloader/20260814T0149Z` status open 유지
(실질 36사 잔여), 재스카우팅 계속.

## 2026-08-14 -- inbox 드레인: equity item10 라운드3 backfill(24셀) + 반기공시 법정기한 당일 스카우팅

인박스 2건 처리(둘 다 8/14 신규). ① parser `20260814T0000Z`(equity_composition item10-notes
백필 라운드3, `_resolved/`로 이동): 24셀 전부 fetch — KR0001/2/3(2023.3Q,2023.4Q,2024.1Q,
2024.2Q)+KR0005/8/9/10/11(2024.1Q,2024.2Q)+KR0079(2024.1Q)는 `ifrs17_batch_historical.py
--pilot <9사> --periods <4개 라벨> --skip-extract` 1회(36 combo, 기존 12개는 zip 존재로
자동 skip). KR0150(2026.1Q)만 `EXCLUDED_SKIP` 우회 신규 `scripts/fetch_kr0150_2026q1.py`
(기존 `fetch_kr0150_item10_quarters.py` 패턴 재사용). parser에 raw-ready 재통지
(`inbox/parser/20260814T0235Z`). 검증 스크립트가 KR0001/2/3의 2023.4Q(사업보고서, annual_raw_dir
경로)를 quarterly_raw_dir로 잘못 짚어 "MISSING" 오탐 냈던 것 정정 확인 — 실제론 24/24 정상.
parser가 물었던 "KR0001/2/3 raw git-purge 영향권" 질문엔 별도 사유 없음 확인, 표준 재수집으로 처리.

② owner `20260814T0149Z`(반기보고서 법정기한 당일, HIGH): 39사 `resolve_corp` 재스카우팅
1회차 — **8/13 대비 변화 없음(2/39: 한화생명·한화손보, 36사 미제출, AIG손해 기존
NO_CORP_MATCH)**. 결과 `data/_derived/scout_2026q2_halfyear.json`. 재사용 가능한 신규
`scripts/scout_2026q2_halfyear.py`(PeriodTarget 2026.2Q를 로컬 구성, 기존
`ifrs17_batch_historical.py`의 전역 레지스트리는 안 건드림 — "새 스크립트 구조 손대지
말 것" 지시 준수, 파이프라인 자체는 그대로 재사용). FS API 캐시(`fetch_dart_fs.py --refresh`)
는 확보된 2사분 이미 11012 OFS+CFS 실데이터(158~302 items) 확인, 신규 확보 없어 추가 조치 없음.
**18사 2026.1Q 정정본 FS 캐시 확인**: 이번 세션 이전에 이미 일괄 갱신되어 있던 상태 발견(mtime
전부 오늘 07:33경, 교보생명 8/13 2차 정정 이후) — 전부 status=000 정상, 재페치 안 함(지시대로
"재페치 남발 금지"). owner 티켓은 37사 잔여로 `status: open` 유지, 재스카우팅 계속 필요.

## 2026-08-13 -- equity_composition item10 주석백필 raw (117셀) + rcept-picking 버그 fix

parser inbox 2건 드레인: `inbox/downloader/20260813T1425Z`(KR0104 농협생명 "전체 결측" 주장)
+ `20260813T1954Z`(18개사 부분 결측 108셀). 둘 다 `inbox/_resolved/`로 이동, parser에
raw-ready 통지(`inbox/parser/20260813T2153Z`).

**KR0104 티켓 재검증 결과 오탐 정정**: 티켓이 근거로 든 `find data/dart -maxdepth 2
-iname "*KR0104*"` 는 실제 leaf 디렉터리 깊이(`FY<y>_Q<q>/raw/KR####_<name>/` = repo 루트
기준 depth 4, `data/dart` 기준 depth 3)보다 얕은 `-maxdepth 2`라 애초에 아무것도 못 찾는
명령이었음 — "0건 전체 FY"는 명령 자체의 한계였지 실제 결측이 아니었다. `scripts/
_dart_path_helpers.period_label_to_dir` 기준으로 재검증하니 2025.4Q·2026.1Q는 이미
raw 有, 실결측은 9개 분기(2023.3Q~2025.3Q)뿐. 18개사 티켓의 108셀 gap 목록은 재검증
결과 전부 정확했음(같은 종류의 오탐 아님, 별개 방법으로 도출된 목록이었던 것으로 보임).

**117셀 전부 fetch + 검증 완료**(zip 무결성 + IFRS17 본문 키워드 ≥1: 보험계약마진/신계약/
보험료배분접근법/보험손익의 상세/이익잉여금). 실행: 표준 유니버스 17개사(KR0104 포함)는
`ifrs17_batch_historical.py --pilot <KR목록> --periods <목록> --skip-extract`를 동일
period-set 서명별로 8회 그룹 실행(전체 조합을 일일이 안 부르고 서명이 같은 회사를 묶음).
서울보증(KR0150) 3건은 `src.ifrs17.universe.EXCLUDED_SKIP`에 걸려 있어(K-ICS PAA-only 취급
때문에 유니버스에서 제외됨, DART 자체엔 필진 有) 표준 CLI로 안 됨 → `resolve_corp` +
`process_one_period`를 직접 호출하는 신규 `scripts/fetch_kr0150_item10_quarters.py`로
우회(기존 KR0004류 one-off 스크립트와 동일 패턴, 재사용 가능하게 유지).

**부수 발견·수정 — `BATCH-HISTORICAL-FIX`(TODO 기존 문서화 버그) 실발화**: KR0104 2023.4Q
fetch 중 DART가 status=014('파일이 존재하지 않습니다')로 거부. 원인: FY2023 사업보고서
후보 3건(원본 + `[기재정정]` + `[첨부정정]`) 중 기존 `fetch_rcept_no` 필터
(`"기재정정" not in report_nm`만 제외)가 `[첨부정정]`을 못 걸러 그 rcept를 골랐던 것.
`scripts/ifrs17_batch_historical.py:fetch_rcept_no` 필터를 "대괄호로 시작하는 report_nm
전부 제외"로 수정 후 재시도 → 원본 rcept(20240401002122) 확보. 이번 배치 나머지 116셀은
원래 원본이 filings 목록 첫 항목이라 버그 영향 없었음. **잔여 리스크(미조치)**: 2026-05-30
Reorg #2 이후 누적된 전체 DART 이력 배치 중, `[첨부정정]`이어도 document.xml이 에러 없이
성공 응답하는 경우가 있어 이 버그로 조용히 정정본이 골라진 셀이 더 있을 가능성 — 이번
세션은 오늘 두 티켓 스코프만 처리, 소급 전수 재검사는 안 함(`TODO_downloader.md`
BATCH-HISTORICAL-FIX 행에 기록, validation 우선순위 판단 대기).

## 2026-08-03 -- `bonds`(FSC data.go.kr) 소스 폐지: 5대 소스 → 4대

owner 발주 `inbox/downloader/20260803T0057Z`. 2026-06-20 owner 결정으로 자본성증권 인정한도
소진율(tier1/tier2)의 발행잔액 분자가 이미 FSC→DART per-bond로 교체돼 있었고, 2026-08-03 전수
조사 결과 FSC에 남은 라이브 의존은 `kics_forward_capital.json` 한 곳뿐이었음 — 그마저 같은 날
parser 발주(`20260803T0055Z`, resolved)로 DART로 이관돼 FSC 소스 자체를 접을 수 있게 됨.
선행조건(parser `20260803T0055Z` resolved + validation `20260803T0056Z` resolved) 확인 후 착수.

**카탈로그/프롬프트**: `source-catalog.yaml`의 `- id: bonds` 블록 삭제(api_ids 중 nonlife/life_metrics·
private_health 3개는 F9 future_sources_planned 엔트리로 이관, capital_securities 15059611은 폐기).
`claude-agent-downloader.md` 5→4 소스 리넘버링(Source 2 DART / 3 KIDI / 4 IR로 당김) + 은퇴 note 삽입.

**코드**: `src/bonds/{__init__,config,fsc_client,universe}.py` · `scripts/ingest_fsc_bonds.py` ·
`scripts/normalize_bond_schedule.py` → `git mv`로 `data/_archive/20260803T063432Z/`(삭제 아님).
`scripts/emit_bonds_provenance.py`는 FSC 절반(bonds/normalized 생성부)만 제거, DART supplement
(`disclosure_bonds_provenance.json`) 절은 그대로 — 재실행 확인 완료.

**데이터**: `data/bonds/normalized/**` + 레거시 bare-timestamp 잔재 2건(`20260525T050327Z`,
`20260616T060238Z` — gitignore `[0-9]*/` 패턴 대상, 구버전 FSC raw pull 잔여물)을 같은 archive
stamp로 이동. `data/bonds/raw/`는 빈 디렉터리였음(삭제). **유지**: `capital_securities_fy2025.json` /
`capital_securities_forward_outlook.json` / `capital_securities_utilization_20261Q.json` /
`disclosure/**`(전부 DART lineage, 라이브 소스) — `_census_fy2025.json`도 mtime 2026-06-20(FSC→DART
전환 당일 census 산출물, `hybrid_hits`/`sub_strict` 필드가 DART raw 스캔 결과) 확인 후 유지.

env 키(`DATA_GO_KR_BOND_ISSUANCE_KEY`/`DATA_GO_KR_BOND_REDE_KEY`)는 F9가 같은 data.go.kr 포털을 쓸 수
있어 삭제 안 함(`TODO_downloader.md` D5에 주석 추가).

**검증 4건 전부 통과**: (1) `grep -rn "src/bonds\|bonds_by_insurer\|ingest_fsc_bonds" --include=*.py .`
→ archive 경로 외 0건(`report_collection_status.py`/`validate_data_contract.py`의 잔존 참조는 각각
graceful-degrade 코드와 lineage-게이트 dead path로 확인, 안전). (2) `pytest tests/test_deploy_assets.py`
9 passed. (3) `validate_data_contract.py` RED=0. (4) `report_collection_status.py` 크래시 없음 —
단 **"자본성증권 발행" 컬럼이 이제 영구 0/39(0%)로 뜬다**(그 컬럼이 여전히 FSC 전용 경로만 읽음, DART로
안 돌아섬) — 이 컬럼을 DART 소스로 재조준할지는 이번 발주 범위 밖(owner 결정 필요, 별도 발주 권장).

⚠️ 이 폐지로 5-source 체제가 시작된 이래 최초로 **4-source 체제**가 됨(정기경영공시/DART/KIDI/IR).
`TODO_downloader.md` 최상단 Status 갱신, `claude-agent-downloader.md` 전체 리넘버링 완료.

**gotcha (재발 방지)**: `data/bonds/normalized/`는 `.gitignore` 대상이 아니어서 stamp dir 3개 중
1개(`20260525T061945Z`, 3파일)가 실제로 git에 추적돼 있었음 — plain `mv`로 archive(gitignore 대상)에
옮기면 git이 새 위치를 못 보고 옛 경로만 "unstaged 삭제"로 남긴다. **git 추적 여부가 불확실한 디렉터리를
archive로 옮길 땐 `git ls-files <dir>`로 먼저 확인**, 추적 파일이 있으면 `git mv`(또는 이동 후 `git add`로
삭제 스테이지) 해서 정리할 것 — plain `mv`만 쓰면 조용히 dangling deletion이 남는다.

## 2026-07-07 -- KR0005·KR0071 FY2024_Q4 "원본 결측" 판정 정정 — 실제로는 raw가 처음부터 맞았음

같은 날 앞선 inbox 드레인 항목(바로 아래)에서 "원천에서부터 감사보고서가 잘못 올라간 진짜 결측"이라 결론
냈던 것을 뒤집음. owner가 "다른 세션에서 OCR로 수치 불러오던 작업 있을 거다, 마저 해봐"라고 지적해 재조사.

**원인**: fitz `get_text()` 전체검색으로만 "경과조치" 키워드 유무를 판단했는데,
- **흥국생명(KR0071)**: raw 538p 중 0-111p가 **스캔 이미지**(텍스트레이어 없음) — 112p부터 감사보고서
  텍스트가 잡히니 "감사보고서만 있다"로 오판. 실제로 0-111p를 렌더링(`fitz.Pixmap`)해 비전으로 읽으면
  정상 "2024년 흥국생명보험회사의 현황" 정기경영공시 전체(총괄표 p.44, 세부표 p.47-50, 시장위험 p.64-70)가
  들어있음.
- **흥국화재(KR0005)**: 스캔이 아니라 **폰트 인코딩 문제로 fitz 텍스트추출 자체가 실패**(이미지 0개인데도
  거의 빈 문자열). 렌더링하면 정상 "2024년 결산 흥국화재해상보험 현황"(총괄표 p.37, 세부표 p.40-44).
- owner가 오전에 자사 홈페이지에서 수동 다운로드해 SHA256이 기존 raw와 동일함을 확인한 것도 "내용이
  틀렸다"가 아니라 "그 파일이 원래부터 맞는 파일이었다"는 뜻이었음 — WAF도 애초에 우회할 필요가 없었음.

**반영**: `kics_disclosure.json`에 양사 24.4Q item1-28(전/후)·item36 등을 raw 이미지 직접 판독으로 채움/정정
(KR0071 item14_후·27_후·28_후는 4개 경과조치 중 하나만 반영한 격리표에서 잘못 소싱된 버그도 같이 잡음;
KR0005는 item8/10/12/13/23-26 등 타사엔 있던 표준 그리드 항목 자체가 비어있던 걸 채움). 게이트 재실행 →
두 회사 관련 RED 0. `TODO_parser_kics.md` 8차 항목에 상세 기록, parser inbox 정정판(`20260707T0230Z`) 발송.

**교훈**: 대용량(수십MB) raw에서 "경과조치"/특정 키워드가 fitz 텍스트검색으로 0회 나온다고 바로 "다른 문서"로
단정하지 말 것. 스캔(이미지 페이지) 또는 폰트 인코딩 문제로 텍스트추출 자체가 실패하는 경우가 있음 —
페이지를 렌더링해서 비전으로 직접 확인하는 게 먼저.

## 2026-07-07 -- inbox 드레인: KR0005·KR0071 FY2024_Q4 wrong-document-type + KR0083 스레드 정리

`inbox/downloader/` open 2건 처리.

- **KR0083 2025.2Q wrong_company_pdf (2026-07-03 발) — 재확인·resolved.** PDF 교체(07-05 응답) 이후 parser 재파싱이 실제 완료됐는지 이번에 확인: `kics_disclosure.json` items 1-46 전부 적재, 게이트 KR0083 2025.2Q RED 없음. 원 스레드 + downloader 응답 스레드 둘 다 `_resolved/`로 이동.
- **KR0005(흥국화재)·KR0071(흥국생명) FY2024_Q4 wrong_document_type (2026-07-07 발) — 부분 처리.**
  - **KR0071**: 현재 raw / 생보협회 2024결산 일괄zip(`quarterfileDown.do`) / 흥국생명 자사 홈페이지(`manageList.do`→`DownLoadEnc.do`) **3채널 SHA256 완전 동일**(감사보고서 538p, 경과조치 키워드 0회) → **원천 데이터 오류 확정, refetch 불가**.
  - **KR0005**: 흥국화재 자사 아카이브(`manageRegular.do` "지난경영공시" 표)에서 정확한 항목(번호112, `[흥국화재] 2024년 결산 경영공시(최종).pdf`, saveName `1743410024285414.pdf`) 특정했으나 다운로드가 nProtect WAF에 막힘(curl 각종 헤더 조합 실패) + Chrome 확장 미연결로 브라우저 자동화도 불가 → **미해결 잔여, 재시도 필요**.
  - **대안 경로**: 두 회사 다 기존 수집된 `FY2025_Q1/raw/`의 `[지급여력비율 총괄]` 비교표(직전분기=24.4Q 컬럼)로 items 1-28 복원 가능 확인(KR0005 154.01%/199.56% 등 parser anchor와 일치). `inbox/parser/20260707T0230Z`로 안내. items 29-46은 이 경로로도 복원 불가.

**Scope:** data collection only — raw fetch from external sources (정기경영공시 / DART / FSC bonds / KIDI / IR factbooks).
**Cross-stage history:** `docs/claude-changelog.md` (parser/validation/gathering/pushing/refactor entries).
**This file:** entries scoped to downloader work only, extracted from the root changelog 2026-05-30.

Cross-stage entries that touch downloader as one phase but are primarily parser/gathering/viz (e.g. F11 foreign-affiliate viz integration, IR factsheet 전사 수집 + 손보 NB CSM 배수 파싱, F17 LOB parsing) remain in `docs/claude-changelog.md`. The compressed historical archive (pre-2026-05-25) also remains there.

## 2026-06-24 -- J-ESR 파이프라인 인프라 구축 (10월 EDINET 全수 대비)

Owner `inbox/downloader/20260624T0337Z` 처리. 인프라 목표(데이터 채우기 X).

- **`J-ESR/jp_insurers.csv`**: 생보 41 + 손보 31 + 재보험 2 = 74사 마스터리스트
  - 확인된 EDINET 코드 13사(HD 7 + 자회사 6) · 상호사 5사 EDINET 비대상 명시
- **`J-ESR/jesr_edinet_fetch.py`**: XBRL fetcher scaffold
  - `--smoke` (키 확인) · `--all --year 2026` (13사 전수 有報 검색) · math validator 내장
  - ESR XBRL 태그: FSA J-ICS 택소노미 미공개 → STUB, 10월 공개 시 채울 것
- **`J-ESR/jesr_mutual_irpdf.py`**: 상호사 5사 IR-PDF 루트
  - `--check` / `--download` / `--extract` 플래그 · seed ESR 값 내장(직전분기)
  - pdf_url_pattern = TBD (연도별 결산프레스 URL 업데이트 필요)
- **`J-ESR/jesr_pipeline_status.md`**: 10월 체크리스트 + 커버리지 추정(~44/74사)

잔여: owner가 EDINET Subscription-Key 등록(무료) → `--smoke` 확인 → TBD 코드 bulk lookup

## 2026-06-24 -- J-ESR 트랙 신규 착수: 일본 ESR(J-ICS) 2026.3末 headline 수집

Owner `inbox/downloader/20260624T0113Z` 처리. J-ICS 첫 의무 사이클(2026-03-31) 대상.

**확정 2026.3末 J-ICS ESR 4사:**
- 東京海上HD 238% · MS&AD HD 214% · Sompo HD 270% · ソニーFG 177%

**직전분기 proxy 5사** (2026.3末 미확인; as_of 컬럼 명시):
- 第一生命HD 213%(2025.12末) · 日本生命 224%(2025.3末) · 住友生命 184%(2025.9末)
- 明治安田生命 216%(2025.3末) · 富国生命 260.9%(2025.9末)

**미수집 2사:** T&D HD · かんぽ生命 (IR PDF 바이너리)

**EDINET API v2 실측:** Subscription-Key 필요(무료등록, https://disclosure2.edinet-fsa.go.jp/).
비상장 4사(日本生命·住友生命·明治安田·富国生命) EDINET 비대상 확인.

산출물: `J-ESR/jesr_sources_2026Q1.csv` (utf-8-sig, 11사) + `J-ESR/raw/` + `J-ESR/probe_edinet.py`
Parser handoff: `inbox/parser/20260624T0200Z__downloader__JP_MULTI__jesr_2026Q1_collected.md`

## 2026-06-17 -- 전체 보험사 2026.1Q DART 분기보고서 + 교보 3개 분기 전기 추출용 raw

**전사 2026.1Q DART fetch** (`ifrs17_batch_historical --all --periods 2026.1Q`):
- 36사 전수 처리: ok 13사 / no_filing 13사(외국계·소형, 구조적) / no_csm_table_found 10사
- 모든 파일 `data/dart/FY2026_Q1/raw/<KR>_<회사명>/document.zip` + `xml/` 저장
- no_csm_table_found: 롯데·미래에셋·삼성생명·삼성화재·에이비엘·코리안리·한화생명·한화손해·현대해상·흥국화재

**교보생명(KR0073) 전기 추출용 3개 분기 raw** (`--pilot KR0073 --periods 2024.4Q,2025.1Q,2025.2Q`):
- 목적: 2023.4Q(←2024.4Q 전기), 2024.1Q(←2025.1Q 전기), 2024.2Q(←2025.2Q 전기) 복구
- 2024.4Q XML 구조 확인: 주석 17-4 등이 "1) 당기" / "2) 전기" 페어 테이블 구조, 전기 333회 출현
- 현재 `csm_extractor.py` period_type 필드 없음 → parser(ifrs17) 발주 `inbox/parser/20260617T1130Z`
- 주의: 2024.4Q에 소급재작성(retrospective restatement) 언급 있음 → 전기 테이블 해석 시 기록 필요

## 2026-06-17 -- 흥국화재 신종자본증권1 콜 미행사 fix + normalize 재실행

`normalize_bond_schedule.py` bug: "5y call assumed exercised" 규칙이 콜 미행사 채권을 잘못 분류.
- **흥국화재 신종자본증권1** (KR60005416C3, 920억, 2016-12-29 발행, call 2021-12-29) — FSC API에 정상 존재, normalize가 `effective_call_date(2021-12-29) <= today` 조건으로 `status=called` 오분류
- 2026.1Q FS appendix(parser `2026q1_per_bond.json`) 에서 920억 잔존 확인 → 실제 콜 미행사
- Fix: `scripts/normalize_bond_schedule.py` 에 `_CALL_NOT_EXERCISED = {"KR60005416C3"}` override 추가 (line 59-64)
- 재실행: `20260616T153258Z` stamp 생성 → KR0005 tier1_hybrid 3,200억 → **4,120억** (FS appendix 일치)
- `emit_bonds_provenance.py` 재실행 → `20260616T153258Z/bonds_provenance.json` 갱신
- `forward_capital_simulation.py` `_latest_bonds_dir()` auto-pick → 재실행 시 자동 반영

## 2026-06-16 -- 자본성증권 in-force per-bond DART fetch + provenance 사이드카 emission

publishing `inbox/downloader/20260616T1200Z`(in-force 자본성증권 FSC vs BS 괴리 해결) 처리.

**FSC API 조사 결과**: 6개 누락사(삼성생명·악사손해·KDB생명·하나손해·AIA·삼성화재) → FSC `GetBondTradInfoService_V2` 전수 0건. 사모발행(프라이빗플레이스먼트) 또는 외국계 모회사 자본 구조 → 공개 등록 없음.
**DART 주요사항보고서** B-type 조사: "자본으로인정되는채무증권발행결정" 공시 = KDB생명 3건·농협생명 4건·교보생명 2건(단 교보 전건 미발행 확인).
**현대해상 재진단**: FSC 4건(26,000억) 모두 2024~2025 신규발행 stale 아님 → FSC 정확, parser `subordinated_eok` 오파싱이 원인.

- **KDB생명 (KR0072)**: 신종자본증권 2건 — 2,160억(2023.05.19 issue, call 2028.05.19) + 250억(2024.12.26 issue, call 2029.12.26) = 2,410억. BS 신종 2,403억과 일치.
- **농협생명 (KR0104)**: 신종자본증권 2건 — 2,500억(2022.09.28, call 2027.09.28) + 2,500억(2022.12.26, call 2027.12.26) = 5,000억. FSC Face 5,000억과 일치.
- **교보생명 (KR0073)**: DART 2023 미발행(시장 불확실성). 별도 데이터 없음.
- **산출물**: `data/bonds/disclosure/2026q1_capital_securities.json` + `disclosure_bonds_provenance.json`
- **스크립트**: `scripts/fetch_capital_securities_dart.py`
- **publishing 핸드오프**: `inbox/publishing/20260616T1300Z` (FSC/DART per-bond 데이터 ready + 현대해상/농협생명 후순위 오파싱 parser 발주 권고)

**Phase 2 provenance 사이드카 emission** (owner `0616T1242Z` + validation `0616T1250Z`):
- `data/bonds/normalized/20260616T060817Z/bonds_provenance.json` (24개사, source_id=FSC_BONDS, as_of=2026-03-31, effective_filtered=true)
- `data/bonds/disclosure/disclosure_bonds_provenance.json` (2개사 DART supplement)
- 스크립트: `scripts/emit_bonds_provenance.py`
- 잔여: DART raw provenance(23사×13분기 source_file+as_of) = 다음 세션

## 2026-06-16 -- CSM 워터폴 연속성(전기 기말≠당기 기시) 복구용 DART raw 재취득 (33셀)

validation `inbox/downloader/20260616T0600Z`(owner: 2026.1Q 기시 CSM 전사 misparse, 정답=직전 2025.4Q 기말)
+ 사용자 지시("26.1Q 전부 말고 5사 먼저, 24.4Q/25.1Q는 continuity break만"). `data/dart/FY2026_Q1/`는
git-purge로 통째 부재(0 dirs) → 재추출 불가 → DART 재취득. `ifrs17_batch_historical.py --skip-extract`(fetch-only).

- **우선 5사 2026.1Q**: 교보(KR0073)·메리츠화재(KR0001)·신한라이프(KR0094)·에이비엘(KR0070)·푸본현대(KR0083) = 5/5.
- **continuity 전수 점검**(`validate_csm_continuity.py`): break는 **24.4Q/25.1Q 경계 아님** — 실제 = 코리안리
  2023.4Q기말 8032≠2024.1Q기초 10641(Δ32.5%) FY경계 + FY2023 기초드리프트(현대·에이비엘·KDB·교보) +
  FY2024 드리프트(KB라이프·코리안리). → **FY2023 Q1-Q4**(현대·에이비엘·KDB·교보·코리안리, 20셀) +
  **FY2024 Q1-Q4**(KB라이프·코리안리, 8셀) 동반 재취득.
- **합계 33/33 fetched, CSM 블록 결손 0**(보험계약마진 48~382 전수 존재). 회사명 검색(영구매핑 없음).
  Q4=사업보고서(A001)·Q1-3=분기/반기. raw gitignore(origin/data 재팽창 아님 — 원천 DART 신규 fetch).
- **핸드오프**: parser/ifrs17 raw-ready(`inbox/parser/20260616T0640Z`, continuity 진단표+owner 정답값 포함).
  파서 재추출 → 2026.1Q 기시=2025.4Q 기말 정상화 + 드리프트/경계 수렴 → `validate_csm_continuity.py` RED 수렴.
  ⚠️ 마스터 rebuild은 복원분+기존 raw 범위 내(전체 부재 시 파괴적). status: resolved, `_resolved/` 이동.

## 2026-06-16 -- 자본성증권 발행현황 검증·수정 (owner 0506Z #2 선제) — registry bare-stem 오수집 fix

owner `inbox/parser/20260616T0506Z` #2(K-ICS tier 패널 신뢰도 점검 — 발행현황 크롤링 검증, data.go.kr
`15059611`)를 downloader가 선제 수행(조건부 바운스 대기 대신). **live 데이터 대체로 정확하나 실오수집 1·누락 1 발견·수정.**

- **근본원인**: `src/solvency/downloader/{nonlife,life}_insurer_registry.yaml`의 **짧은 그룹 약칭**이 FSC bond
  API substring 쿼리로 나가 계열사 채권을 보험사로 오태깅. `--max-pages` 키우자 메리츠 1.77조→**19.6조**,
  iM라이프 0.27→10조, 미래에셋 0.3→9.2조 폭증(메리츠캐피탈/증권/지주, 아이엠뱅크, 미래에셋증권 등).
- **수정**: bare-stem alias **4개 제거** — `"메리츠"`(KR0001)·`"아이엠"`(KR0076)·`"미래에셋"`(KR0079)·
  `"카카오"`(KR1098). specific 약칭은 유지. IBK/AIG/AXA/처브/푸본은 영문스템/고유명이라 무오염 확인(미수정).
- **재크롤+정규화**(clean: raw `20260616T060238Z` / normalized `20260616T060817Z`, as_of 2026-06-16):
  - **24사 중 22사 live 5/25와 동일** → big-3 Face는 live가 정확했음(page-cap이 deep 오염 우연 차단).
  - 🔴 **KR1098 카카오페이 3,202억→0**(live가 카카오 그룹 채권을 가짜로 적재; 카카오페이손보 자본성증권 미발행).
  - 🟢 **KR0099 KB라이프 0→1,200억**(live가 놓친 진짜 신종자본/후순위; 사명 전수 검증).
  - 🟡 KR0011 DB손해 −890억(3주 정상 call/만기 delta).
- **함의**: big-3 Face 정확 → owner T2 BS −11.6%는 **Face(downloader) 아님 → BS시가(parser #1)** 주원인 추정.
  단 KR1098 tier 패널은 0 반영 필요. clean normalized = `_latest_bonds_dir` auto-pick, 오염 intermediate 제거.
- **핸드오프**: parser-kics `inbox/parser/20260616T0615Z`(검증결과+수정+#1 BS시가 포인터). 재빌드는 publishing/parser gate.

## 2026-06-16 -- NB CSM 시계열 오염 복구용 interim DART raw 재fetch (10사 × 3분기, fetch-only)

parser/ifrs17 발주(`inbox/downloader/20260616T0400Z`; validation `20260616T0230Z`가 DART CSM_waterfall
partial 추출이 NB CSM YTD 시계열 오염 확정 — 롯데 2025.2Q YTD→0 등). git-purge로 해당 분기 raw 부재 →
파서 재추출 불가 → downloader가 반기/분기보고서 본문 raw 재취득.

- `scripts/ifrs17_batch_historical.py --skip-extract`(**fetch-only**; 파괴적 `build_csm_waterfall_master.py`
  미실행 — 발주 경고 준수) → **10사 × {2025.2Q 반기·2025.3Q 분기·2023.1Q 분기} = 30셀, 30/30 fetched.**
  대상: 롯데(KR0003)·미래에셋(KR0079)·한화생명(KR0068)·현대해상(KR0009)·삼성화재(KR0008)·DB손해(KR0011)·
  동양(KR0087)·코리안리(KR1000)·한화손해(KR0002)·흥국화재(KR0005). 회사명 검색(영구매핑 없음).
- canonical `data/dart/FY{Y}_Q{n}/raw/KR####_<canonical>/document.zip(+meta.json)`. raw gitignore.
- **CSM 블록 검증(zip 본문 보험계약마진 count): 29/30 존재** → 재추출 가능. 우선 7셀 전부 OK
  (롯데 2025.2Q NB=0.0 최악건 포함). **🔴 honest gap 1**: 롯데 2023.1Q(20230515002687) 보험계약마진 0
  (도입초 분기보고서 §14 축약 추정, 소스 부재; 우선셀 아님) → census whitelist 권장.
- **핸드오프**: parser/ifrs17 raw-ready(`inbox/parser/20260616T0420Z`, rcept·키워드 표 포함). 파서가
  `ifrs17_batch_historical.py` extract 모드로 재추출 → validation `check_nb_csm_history.py` 수렴 확인.
  마스터 rebuild은 raw 전체 복원 세션에서(이번 interim은 부분 rebuild 금지). status: resolved, `_resolved/` 이동.

## 2026-06-16 -- 예별손해(KR0004, 구 MG=엠지손해) DART 연간 감사보고서(별도) FY2023~FY2025 적재

위 K-ICS 11분기 건의 후속(owner): "예별/MG DART 공시도 전기간 받았나? 비상장이라 없으면 회기말 감사보고서라도."
조사 결과 **KR0004는 DART 데이터 통째로 0** — 비상장 손보사라 정기보고서(A) 미제출 → IFRS17 DART
universe(`src/ifrs17/universe.py`) 어느 리스트에도 부재. 단 외부감사법 주식회사라 **연간 감사보고서(F)** 제출.

- **DART entity = '엠지손해보험'**(corp_code `00962861`; 신규 '예별손해보험' `01974696`은 filing 0건).
  회사명 검색으로 감사보고서 8건 발견(별도/연결 × 2022~2025).
- **owner 스코프**: **별도만·FY2023~** (IFRS17 effective 2023; FY2022=IFRS4 제외, 연결 제외 —
  `build_csm_waterfall_master`는 별도 00760 사용). 8건 중 **3건 보존**, 5건(FY2022 별도/연결, 각 연결) 제거.
- 적재(5 audit-only 외국계 생보사와 동일 경로·레이아웃): `data/dart/FY<year>_Q4/raw/KR0004_엠지손해보험_<rcept>/`
  = `document.zip` + `<rcept>_00760.xml`(별도). FY2023=20240408000665 · FY2024=20250408000587 · FY2025=20260406003175.
- **IFRS17 주석 확인**(별도 키워드 카운트): 보험계약마진 36~59 · 보험료배분접근법 31~37 · 신계약 6~9 →
  CSM waterfall 추출 가능. 소형 PAA-heavy 손보사라 신계약 CSM 얇음(예상).
- 재현 스크립트 `scripts/fetch_kr0004_mg_dart_audit.py`(FILINGS=3 별도) + probe `scripts/_probes/_kr0004_dart_probe.py`.
- **핸드오프**: parser/ifrs17 raw-ready(`inbox/parser/20260616T0210Z`). 파서가 CSM/PL 추출 → 마스터 KR0004 라인 병합.
  raw는 gitignore(git 재팽창 무관).

## 2026-06-16 -- 예별손해(KR0004, 구 MG) 과거 11분기 K-ICS 정기경영공시 raw 전수 적재

parser(kics lane) → downloader bounce(`inbox/downloader/20260616T0055Z`, owner round3 K2):
예별 K-ICS가 26.1Q 1분기만 적재 → 그 이전 = 구 MG손해 명의. 사명변경 매핑해 과거 분기 시계열 병합.
파서 조사: kics_disclosure.json KR0004=2026.1Q 단건, 디스크 raw=FY2025_Q4+FY2026_Q1만 →
**2023.1Q~2025.3Q 11분기 raw 자체 부재** → downloader fetch.

- **소스 = 회사 자체 정기경영공시 페이지** `yebyeol.co.kr/PB021010DM.scp?menuId=MN0802001`
  (예별=구 MG 동일 법인). 이 페이지에 **2013~2026 전 분기 아카이브**가 한 화면에
  `<a id="quarter{N}_{YYYY}" href="javascript:fn_download(ID)">`로 노출. 매핑: quarter1→Q1 ·
  quarter2(상반기/반기보고서)→Q2 · quarter3→Q3 · quarter4(결산/연간)→Q4.
- **kpub.knia.or.kr(손보협회 통합공시)는 무용**: 결산(Q4)만 carry + MG/예별 row 자체 부재
  (`backfill_nonlife_disclosure_kpub.py` NAME_TO_KR에 KR0004 없음) → 회사 사이트가 유일 소스.
- **11/11 OK, 결손 0** (서울보증식 honest gap 없음). 회기말 Q4 2개(2023·2024 결산) 포함 전수.
- **구 MG 명의 확정**: 결산 ZIP 내부 본문 파일명 = "[엠지손해보험] 2023년 결산 경영공시 최종.pdf" /
  "2024년 엠지손해보험 현황_F.pdf" → 동일 법인 과거 공시. ZIP은 감사/재무제표 동봉 → 룰대로
  **경영공시 본문 PDF만** 추출(`extract_disclosure_pdf` kpub 로직 재사용).
- **text-layer 전수 OK**(6p 텍스트 1.9k~3.3k자, 지급여력·경과조치·K-ICS 키워드 존재) →
  **OCR 불필요**, docling 바로 가능. scan-only 아님(OCR-MARKETRISK 류 함정 회피).
- 파일명 `KR0004_예별손해보험.pdf`(기존 stem 컨벤션, parser glob `KR0004_*` 매칭).
  기존 FY2025_Q4·FY2026_Q1 미변경 → KR0004 = **2023.1Q~2026.1Q 13분기 연속** 확보.
  raw는 gitignore → git 재팽창 무관.
- 신규 스크립트 `scripts/backfill_kr0004_mg_quarters.py`(재사용; TARGETS만 수정해 타 분기 추가) +
  probe `scripts/_probes/_yebyeol_disclosure_probe.py`(2013~ 전 분기 fn_download ID 매핑).
- **핸드오프**: parser/kics raw-ready(`inbox/parser/20260616T0145Z`). 파서가 docling MD →
  core items 1-28 추출 → kics_disclosure.json 예별 시계열 병합 + 게이트 census 확장.
  status: resolved, `_resolved/` 이동.

## 2026-06-15 -- IFRS17 CSM 민감도 FY2025 raw 28사 전수 적재 (sensitivity FY2024→FY2025 갱신용)

owner 요청(`inbox/downloader/20260615T0435Z`): 사이트 CSM 민감도가 FY2024(24.4Q)에 고정 → 전 IFRS17
대상사 FY2025 사업/감사보고서 raw 다운로드(파서가 sensitivity 재추출). universe = DART sensitivity JSON
보유 28사(`data/dart/extracted/<canonical>_<rcept>_sensitivity.json`; `KR####_FY..._kics`=별개 K-ICS 분기 민감도라 제외).

- **fetch**: 회사명 검색(영구매핑 금지) → `/api/list.json` FY2025(2026-03~04 제출) 사업보고서(23 listed) +
  감사보고서(5 audit-only: 라이나·메트라이프·AIA·하나생명·처브) → `/api/document.xml` fetch+extract →
  canonical `data/dart/FY2025_Q4/raw/<KR>_<name>_<rcept>/`. **32 filings, 28/28 공시, 실패 0, 미공시 0.**
  raw-only(추출은 파서). data/dart raw는 gitignore → git 재팽창 무관(신규 HTTP fetch).
- **네이밍**: 전부 `KR####_` prefix 통일. KB라이프·코리안리는 kics명↔DART명 불일치로 annual_raw_dir가
  corp_code prefix(`00160393_`/`00113191_`)로 떨궈서 → `KR0099_`/`KR1000_`로 정정(G8 AIG와 동일 패턴).
  하나생명·AIA는 G8에서 받은 것 idempotent 재확인.
- **파일럿 흥국생명**(KR0071_흥국생명보험_20260331004251) raw sanity: 민감도 25·사망률 8·보험계약마진 114.
  리터럴 "장해질병"/"실손"=0이나 장해6·질병6·정액19 존재 → 라벨 변형(파서 추출에서 확인, 다운로드 갭 아님).
- **핸드오프**: parser/ifrs17 raw-ready(`inbox/parser/20260615T0520Z`). 파서가 sensitivity 재추출 +
  흥국생명 부호/행 파일럿 검증 → heatmap 재빌드. status: resolved, `_resolved/` 이동.

## 2026-06-15 -- 서울보증(KR0150) 8분기 raw 부재 재바운스 — 구조적 honest gap 재확인 (refetch 불가)

parser(kics lane, docling census) → downloader: 서울보증 8분기 disclosure raw 부재로 refetch 요청
(`inbox/downloader/20260615T0100Z`). **신규 누락 아님** — 요청 8분기(2023.Q1-3·2024.Q1-3·2025.Q2-3)가
`audit_all_periods.py:39-43` `SGI_QUARTERLY_STRUCTURAL` 집합과 정확히 일치. 2026-06-01 NONLIFE-Q123에서
이미 probe·판정·등록 완료. 사유: SGI 공시실(sgic.co.kr SPA)은 연간+최신분기만 보존(과거 롤오프) +
DART 미상장(IPO 철회) → 양쪽 미취득, 사용자 결정("걍 버려")=won't-fix. → census expected-absent로 처리하라
회신(파서 census가 `SGI_QUARTERLY_STRUCTURAL`+`DART_DROP` 예외표 참조 권장). status: resolved, `_resolved/` 이동.
다운로더 액션 없음(물리적으로 받을 원천 부재). present raw = 2023.4Q·2024.4Q·2025.1Q·2025.4Q·2026.1Q.

## 2026-06-14 -- G8: NB CSM배수 25.4Q 누락 3사 — FY2025 감사보고서 raw 복원 (추출은 parser로 라우팅)

owner QA(G8, `inbox/downloader/20260614T0712Z`): index.html CSM배수가 AIG(KR0029)·카카오페이손해
(KR1098)·하나생명(KR0097)에서 2025.4Q 누락 → 24.4Q fallback. inbox 프레이밍은 "DART refetch 3건"이었으나
**진단 결과 단순 refetch 건이 아니었음.**

- **원인 분리**: NB CSM배수 분자(신계약 CSM)는 `CSM_waterfall.json` 항목2(=파서 마스터) → 다운로더 산출물
  아님. 3사 FY2025 감사보고서 raw가 working tree에서 사라져 있었음(추출 후 정리/purge 추정; data/dart raw는
  gitignored). 인벤토리 `_inventory_manifest.json`(raw_annual)이 rcept를 기록 중이라 라이브 DART 재취득 가능.
- **복원(downloader 액션)**: 라이브 `/api/list.json`(회사명 검색, 영구매핑 없음) → FY2025 감사/연결보고서
  rcept 확정 → `/api/document.xml` fetch + extract, canonical `data/dart/FY2025_Q4/raw/<KR>_<name>_<rcept>/`:
  - KR0029 AIG: `20260407002104`(별도) + `20260407002109`(연결). annual_raw_dir가 kics명 "AIG손해보험" ↔
    DART명 "에이아이지손해보험" 불일치로 corp_code prefix(`00983606_`)로 떨궈서 → **빌더 글롭 `KR0029_*`에
    걸리도록 `KR0029_` prefix로 리네임 정정.**
  - KR1098 카카오페이: `20260323001537`(별도). KR0097 하나생명: `20260325000201`(별도)+`000202`(연결).
  - 검증: 보험계약마진 26~55회/신계약 3~12회 (IFRS17 본문 OK).
- **추출 스모크(read-only, 마스터 미변경)로 진짜 원인 확정** → 파서 이슈:
  - AIG: 신계약CSM=986,825.6억(≈2000배 과대, 롤포워드는 닫힘) magnitude/table misparse. (과거 FY2024=443.8)
  - 카카오페이: 신계약CSM=20,187.6억(현 마스터 stale값과 동일 → 이전 빌드도 같은 표를 같은 방식으로 읽음).
    배수는 build_nb_csm_multiple `_MULT_CAP=40`이 정상 null 처리 중.
  - 하나생명: build-waterfall 경로 no blocks → AUDIT_REPORT_ANNUAL이라 `ifrs17_ingest_audit_annual.py`
    (extract_csm_tables) 경로 필요(2024.4Q=3240.3이 그 산물).
- **핸드오프**: parser/ifrs17 inbox에 route:reparse 작성
  (`inbox/parser/20260614T1330Z__downloader__MULTI_2025.4Q__nb_csm_fy2025_raw_ready.md`).
  파서가 magnitude 교정 + 하나생명 audit-annual ingest → CSM_waterfall 재빌드 → build_nb_csm_multiple 재실행.
- G8 원 스레드 → `_resolved/` 이동(status: resolved). downloader 잔여 액션 없음.
- **미결(별개)**: `20260614T1232Z` qa_residual item(2) — KB/한화손해 2023.4Q 금리위험·카카오 2025.4Q
  시장위험 스캔-only(텍스트레이어 없음) OCR. downloader OCR 경로 부재 → owner 결정 대기, 메시지 open 유지.

## 2026-06-09 -- AIA 식별자 마이그레이션: 리터럴 "AIA" → KR0080 (코드+데이터 코디네이션)

AIA생명(에이아이에이생명보험)은 kics_disclosure 로스터에 없는 audit-only 외국계라 일부 스크립트가 코드 대신 리터럴 `"AIA"`를 식별자로 써왔고 → `AIA_*` 파일/폴더가 KR####_ 컨벤션을 깨고 있었음. KR0080은 이미 registry/_dart_path_helpers/_kr_map 등에서 AIA 정본 코드라, 누락분을 KR0080으로 통일.

- **코드 4스팟**(식별자로 쓰던 곳만): `ingest_kidi_monthly_premium.py:71` 키, `crawl_assoc_nb_premium.py:66` 키, `report_collection_status.py:68/123/142` 로스터 → `"AIA"`→`"KR0080"`.
- **유지(건드리면 안 됨)**: `ifrs17_find_missing.py`(=DART corp-name 검색 쿼리), `extract_dart_zips.py` INSURER_PREFIXES(백워드-compat), `audit_all_periods.py` alias, `one_off_reorg2_canonical.py`(1회성).
- **데이터 17경로 리네임** `AIA_`→`KR0080_`: KIDI 13(`data/kidi/FY*/raw/AIA_<yyyymm>.json`) + DART raw 3폴더(FY2024_Q4·FY2025_Q4) + disclosure 1(FY2026_Q1). `_archive`는 제외.
- **파생 JSON 코드필드** `"AIA"`→`"KR0080"` (JSON-aware, 이름 보존): premium_summary 13 + kidi_life_premium 13 + nb_csm_multiple 1.
- **검증**: `report_collection_status.py` exit 0, AIA→KR0080 "전체자료 입수 완료"; `_archive` 외 AIA_ 잔여 0; 파생 JSON bare "AIA" 0. 네트워크 크롤 미실행.
- **주의**: 데이터만 리네임하면 ingest가 "AIA" 키로 읽어/써서 깨짐 → 코드+데이터 동시 변경이 필수였음.

## 2026-06-04 -- KIDI 신계약 월납초회보험료 FY2026_Q1(202603) 재수집

사용자 재확인 요청 → 라이브 KIDI INCOS 엔드포인트 probe 결과 **2026.1Q(202603)이 그새
발표됨** (5/31 fetch 시점엔 항목 라벨만 있고 ITEM_VAL 비어있던 게, 이제 값 채워짐).
3개 크롤러 풀 리빌드(전 기간, 202603 포함):
- `crawl_kidi_life_premium.py` → `kidi_life_premium.json`: 264 → **286 records** (생보 22사 × 202603 추가)
- `crawl_kidi_longterm_premium.py` → `kidi_longterm_premium.json`: 184 → **200 records** (손보장기 16사)
- `ingest_kidi_monthly_premium.py` → raw per-company + `premium_summary.json`: **507 entries** (39사×13), errors 0

검증(202603 월납초회 실측): 삼성생 739.63억 / 한화생 621.18억 / 교보생 390.7억 /
삼성화재 455.89억 / DB손 417.66억 / 메리츠손 348.33억 / 현대손 298.75억. 전부 1Q 누계로 정합.

`audit_all_periods.py`: `KIDI_NOT_RELEASED`에서 FY2026_Q1 제거(빈 set) — 이제 실제 체크해도
KIDI REAL GAPS **0**. → KIDI 13분기 전수 수집 완료(구조적 0: 코리안리(재보험)·서울보증(보증, 미매핑)).

## 2026-06-04 -- 한화생명(KR0068) 분기 IFRS17 본문/별첨 확인 (parser 질의)

파서가 한화생명 분기 Tier-1 NO 보고 ("분기/반기보고서가 요약재무정보만 노출, 보험손익 분해
IFRS17 표 미수록(포맷 상이)") → downloader에 본문 vs 별첨 확인 요청.

**확인 결과: 전부 본문(body XML)에 있음. 별첨 아님. 재다운로드 불필요.**
- 분기 dir 구조: 단일 main XML(`<rcept>.xml`), document.zip 멤버도 1개뿐 (연간과 달리
  `_00760`/`_00761` 별첨 없음). 즉 받을 추가 문서 자체가 없음.
- 본문 term-scan (FY2025_Q1 분기, 4.9MB/913 tables): 보험수익=80, 보험서비스비용=68,
  보험금융=86, 보험계약마진=117, 보험서비스=112, 포괄손익계산서=11회, 영업부문=7.
  반기(Q2)·연간은 더 풍부. → IFRS17 보험손익 분해 데이터는 본문에 물리적으로 존재.
- 파서가 "요약만"으로 본 이유: 본문 **헤드라인 포괄손익계산서가 레거시 요약 워터폴**
  (매출액/영업이익/법인세차감전순이익/당기순이익/기타포괄손익) 포맷이라 first-match가 이걸 잡음.
  실제 IFRS17 보험손익 분해는 본문 뒤쪽 상세표/주석에 있고, 표준 `<TABLE>/<TD>`가 아닌
  비표준 markup(`<TE>` wide-table 또는 서술형 추정)이라 추출이 어려운 것 → **파서측 매칭 이슈**,
  다운로드 갭 아님. (한화생명 1사 한정, 파서 세션이 보류 중인 항목과 일치.)

## 2026-06-03 -- DART document.zip 미추출 수정 (parser raw_not_extracted unblock)

파서 세션이 `status=raw_not_extracted`(document.zip만 있고 본문 XML 없음)을 보고.
원인 + 수정:

**원인 (2가지 결합):**
1. 해당 dir들은 fetch-only 단계에 남아 있었음 — `document.zip`는 받았으나 unzip(extractall)이
   실행 안 됨. (batch 스크립트의 추출 로직 자체는 정상 `extractall`; --skip-extract 실행분이거나
   Reorg #2가 미추출 dir을 그대로 옮긴 케이스로 추정.)
2. 비상장·외국계 보험사의 공시는 standalone 감사보고서라 zip 내부에 main `<rcept>.xml`이 없고
   `<rcept>_00760.xml`(연결)/`_00761.xml`(별도)만 들어있음 → main xml만 찾는 점검은 "빈 dir"로 오판.
   IFRS17 공시(보험계약마진/포괄손익/부문)는 이 _0076x 멤버 안에 그대로 존재.

**수정:** 신규 `scripts/extract_dart_zips.py` — idempotent. `data/dart/FY*_Q*/raw/*/document.zip`를
스캔, 본문 xml(`*.xml`/`xml/*.xml`/`extracted*/*.xml`)이 없는 dir만 in-place로 extractall (메리츠 등
정상 dir과 동일 레이아웃). 보험사 prefix(KR / AIA)만 대상; 지주(corp_code) dir은 제외(--include-all로 포함).
네트워크 재다운로드 없음 — 이미 받아둔 zip을 풀기만.

**결과:** 보험사 dir 42개 추출(46 xml members), idempotent 재실행 0건. parser 좌표 기준
bucket A(zip有/xml無) 40 → **0**. spot-check: AIG `_00760` 보험계약마진=55, AIA=49, 메트라이프=124.
기존 파서가 `*.xml` glob으로 자동 인식 → raw_not_extracted 해소 예상(파서 측 코드 변경 불필요).

**부수 발견 (별개 이슈, bucket C = 빈 dir/zip無 121건):** 110건은 비상장사 Q1-3 = DART 분기보고서
구조적 미제출(정상, gap 아님). 11건은 비상장 11사의 **FY2023_Q4 연간 감사보고서 미다운로드**(이들의
FY2024_Q4·FY2025_Q4는 위에서 추출 완료). 비상장 감사보고서 fetch 여부는 사용자 결정 사항(과거
"비상장사 감사보고서 불필요" 결정 ↔ parser의 PL/CSM 요청 충돌) → 사용자에게 질의.

## 2026-06-02 -- Housekeeping: archived early IR auto-discovery probes

Archived `scripts/_probes/` (45 files, ~2,600 lines) to
`data/_archive/20260602T150745Z_downloader_ir_probes/_probes/` (git rename, not
deleted; README in that dir maps each probe family to its canonical replacement).

These were exploratory DOM-inspection / URL-discovery scripts from the early
"find and download everything yourself" IR phase (iterative `_*_probe`,
`_*_probe2` ... `_hi_ir_probe11`). They learned each insurer's IR board / click /
download mechanism but never wrote into the data tree; the working recipes were
folded into the config-driven `scripts/crawl_ir_*.py` crawlers (kept). Verified
nothing imports `_probes` and no doc references it; `report_collection_status`
still imports clean after the move. Kept (not deleted) as reference for onboarding
foreign insurers later.

Not touched: `scripts/dl_lotte_ir.py` — a clean but superseded one-off (Lotte
only, replaced by `crawl_ir_lotte_koreanre.py`). Flagged for the user to decide;
left in place.

## 2026-06-01 -- NONLIFE-Q123 종료: 손보 6사 분기공시 26셀 backfill (자체사이트)

손보 6사 분기(Q1-Q3) 정기경영공시를 각 사 자체사이트에서 사별 병렬 에이전트로 수집. 34셀 중 **26셀 수집, 8셀(서울보증) 구조적 미발행** → disclosure 실질 gap **0**. 무결성 2,041/2,041 OK, audit disclosure REAL GAPS 0.

신규 스크립트(사별): `scripts/backfill_q123_{aig,axa,shinhanez,sgi,koreanre,kakaopay}.py`. 저장: `data/disclosure/FY{Y}_Q{N}/raw/KR####_<name>.pdf` (기존 네이밍 일치).

사별 결과·사이트 구조:
- **AIG손해(KR0029)** 9/9: 사이트 cadence = `1분기/상반기/3분기/결산` (**별도 2분기 없음** → 상반기 누적으로 Q2 채움). list page `dpwom012.html?curPage=N`에 제목 anchor 옆 직접 다운로드 href(`downLoadFiles.do?fileId=`) — detail page 불필요.
- **악사(KR0049)** 4/4 (FY2023 Q1·Q3, FY2025 Q1·Q3): 표가 **FY행 1개 + 분기별 td 셀** 구조 → 셀별 `N/4분기` 라벨로 매핑(naive "행첫 a"는 Q1만 잡힘). 전체(결산)셀은 ZIP.
- **신한EZ(KR0051)** 4/4 (FY2023 Q1-Q3, FY2024 Q1): 카디프→신한EZ 개명에도 FY2023 풀 보존(페이지네이션 목록). Q2 라벨 = "상반기".
- **서울보증(KR0150)** 0/8 = **구조적 미발행**: SPA(`CCGIRI010101F01_listTmpl`)가 **연간 경영공시 + 최신 1분기만** 노출(과거 분기 롤오프), DART 미상장 → 양쪽 모두 미수집 불가. audit에 `SGI_QUARTERLY_STRUCTURAL` 예외 등록.
- **코리안리(KR1000)** 6/6 (FY2024·FY2025 Q1-Q3): `ir_03_1.asp` 단일 표에 전 연도 행, 셀 href가 직접 PDF(`/pdf/gyungyoung/<year>_<q>.pdf`). 파일 stem `KR1000_코리안리.pdf` 사용.
- **카카오페이(KR1098)** 3/3 (FY2024 Q2, FY2025 Q2·Q3): 정적 SPA 표 직접 href. 정정/KICS포함본 우선(FY2024_Q2는 5.1MB KICS본). Q2=상반기.

**Parser 핸드오프**: AIG/신한EZ/카카오 FY{Y}_Q2 = 반기(상반기) 누적(1.1~6.30), standalone 분기 아님 — validation에서 누적-반기로 해석 필요. (TODO_downloader Status에도 기재.)

서울보증 DART 8셀(`SEOULBO-DART`): 사용자 결정("걍 버려")으로 **drop (won't-fix)**. 미상장(IPO 철회) → DART 미공시 = 구조적. audit `DART_DROP` 등록 → **전 source REAL GAPS 0** 달성.

## Archive (pre-2026-06) — 2026-05-25 → 2026-05-31 (FY2026.1Q 수집 + Reorg)

> 1줄 요약. 전문은 git log/blame. 회사별 URL/XPath 정본은 source-catalog.yaml.

- 2026-05-31 (O~S) -- 데이터 수집 완결: 전수 audit + disclosure 28셀 backfill
- 2026-05-30 (N) -- DART batch script canonical-path refactor
- 2026-05-30 (M) -- File-integrity 검사기 + 현대해상 IR 재다운로드
- 2026-05-30 (L) -- Collection-Status Report step + 양식 추가
- 2026-05-30 (j) -- Reorg #2: DART/KIDI/assoc 마저 정리 (canonical 일관 적용)
- 2026-05-30 (i) -- Downloader workflow 정리 완료 (5 source audit + canonical reorg + master prompt)
- 2026-05-30 (h) -- DART raw 100% audit + gap fill (KPI "전부 다 성실하게" 달성)
- 2026-05-30 (g) -- DART 별첨 fetch 진단 철회 (본문에 다 있음, 회사별 라벨 변형 처리 필요)
- 2026-05-30 (f) -- FY2026.1Q 생보 22사 경영공시 일괄 다운로드 완료 (세션 file ingest A-Z 마무리)
- 2026-05-30 (e) -- FY2026.1Q IR 자료 13 source 다운로드 완료 + 한화손보 IR mis-classified 정리
- 2026-05-30 (d) -- FY2026.1Q 손보 17사 경영공시 PDF 다운로드 완료
- 2026-05-30 (c) -- F2 v3 KIDI ML01/MN07 crawler DONE — NB CSM 분모 6→328 entries, computed multiple 6→27/28
- 2026-05-25 -- IFRS17 historical 13Q ingest + CSM 시계열 panel (push #2)
- 2026-05-25 -- Bond tier `(신종)` fix + FSC bond normalize refresh

---

## Compressed historical archive (pre-2026-05-25)

The compressed one-liner archive in root `docs/claude-changelog.md` ("## Historical archive (compressed)") contains a few downloader-relevant lines, kept inline there for compactness:

- FSC bond ingest client `src/bonds/` + `scripts/ingest_fsc_bonds.py` (MISC-BOND-INGEST)
- FSC schedule API per-insurer full pull: 1720 rows / 19 insurers
- Bond calendar v3: 5y Call rule for ALL bonds, 3-status outstanding/called/matured
- FSC schedule API 15059611 [승인] confirmed

These remain in the root changelog rather than being re-extracted, since they're already condensed.
