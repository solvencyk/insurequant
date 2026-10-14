# Insurequant Changelog — Downloader Stage

> Last updated: 2026-10-11 · Stage 1/5 — downloader
> Prompt: docs/agents/claude-agent-downloader.md · TODO: TODO_downloader.md

> 보관: 이전 달 항목은 `docs/changelog_archive/downloader/` 에 월별로 무수정 보관한다(관리 `scripts/doc_rotate.py changelog`, 현행 = 최신 항목 달과 그 전 달).

## 2026-10-11 -- 사이트 현행판 vs raw 전수 대조 (48코드 x 14분기, 605칸 대조, 신판 21칸 저장)

inbox `20261011T1100Z`(orchestrator, route: backfill, 공유 티켓이라 종결은 오케스트레이터). 직전 별첨 수집에서 11사만 대조해 새 판 3건이 나온 것의 전수판.
방법: raw 인벤토리(sha256·쪽수) → 채널별 현행 게시본 다운로드 후 sha256 대조(동일 파일은 저장 안 함) → 다르면 쪽 단위 텍스트·숫자·렌더링(36dpi 해시, 필요 시 평균 픽셀 차) 비교 + PDF 메타 생성일로 방향 판정.
채널: 손보 16사 회사 사이트 14분기 전수(메리츠 json.smart+클릭, 한화 직접 URL, 롯데 POST 목록, 예별 id 클릭, 흥국화재 `fn_filedownX`, 삼성화재 zip URL, 현대해상 상세 파일목록, KB 단일표, DB 상세 pdf, AIG `bomservice.do`(curl.exe), NH `downloadFile.ajax`, 악사·하나·신한이지·카카오·BNP 앞선 수집 방식) + 손보협회 kpub 결산 zip(Q4 42칸 교차, 코리안리 3칸) · 생보 22사 협회 308칸 전수 + 회사 사이트 171칸 · 재보사 매니페스트 URL 재다운로드 + 사이트 목록 재조회.

| 결과 | 칸 | 비고 |
|---|---|---|
| 동일 | 558 | 대조 전 약 80칸 → 605칸 |
| 신판 raw `_v20261011` | 16 | K-ICS 수치 변경 7(예별 2025.4Q · NH손보 2025.1Q · KDB 2025.3Q · 교보 4) · 그 외 수치 변경 7(현대해상 3 · 한화생명 2 · 하나생명 · KB라이프) · KB 스캔→텍스트판 2 |
| 신판/상위집합 attachments | 5(+앞선 수집 2) | 한화손보 2025.4Q · 흥국화재 2024.4Q · AIG 2023.4Q · 농협생명 2025.4Q(감사보고서 추가) · 신한이지 2025.4Q(재배열) |
| 바이트만 다름 · 서식만 · raw 가 더 완전 | 16 · 6 · 2 | 렌더링 해시/픽셀 차로 확인 |
| 대조 못 함 | 40 | 코리안리 11(443 TLS 재설정) · 서울보증 6·캐롯 9(범위 밖) · 퍼시픽 9(Incapsula) · 마이브라운 5 |

- **K-ICS 수치 변경 예:** 예별 2025.4Q 지급여력비율 △8.24% → △13.53%(금액 △714 → △1,171, 마스터는 옛 판 값) · 교보 2025.4Q 165.66 → 164.02. 새 판 PDF 생성일이 raw 보다 뒤인 칸은 16/16.
- **KB손보 2025.4Q·2026.2Q raw 는 스캔**(2026.2Q 64쪽 전쪽 텍스트 없음), 사이트가 2026-09-17 에 같은 내용의 텍스트층 판으로 교체. OCR 없이 추출 가능.
- parser 티켓: `inbox/parser/20261011T1210Z…newer_site_editions_census_kics.md`(16칸, 칸별 옛/새 파일·바뀐 쪽 숫자·마스터 현재값, 첨부 JSON `site_edition_census_parser_kics_20261011.json`) · `…T1215Z…site_editions_attachments_fyi_ifrs17.md`.
- 한계: 생보 회사 사이트 137칸은 협회 현행본만 대조(AIA 2026.1Q 처럼 두 채널이 다른 판인 경우가 이미 있었음). 런로그 `data/disclosure/_meta/site_edition_census_runlog_20261011.md` · 칸별 결과 `site_edition_census_result_20261011.json`.
- 실수: 빈 heredoc `python -` 를 여러 번 잘못 실행(EOF 로 즉시 종료, 고아 없음), `| head` 로 장시간 스크립트를 받다 남은 프로세스 1건 `taskkill`(내 PID).

## 2026-10-11 -- 경영공시 BS·PL 별첨 수집 70칸 (별첨 60건 수령, 25칸은 원문이 이미 raw 에 있음)

inbox `20261011T0830Z`(orchestrator, route: backfill; 공유 티켓이라 종결은 오케스트레이터) + 옛 티켓 `20261007T1400Z`(KR0075 2024.2Q 잘린 PDF, 답변 작성 `answered`).
대상 = `data/_derived/bspl_granularity_20261011/attachments_needed_20261011.json` 의 nofull 56 + nodoc 14.

| 분류 | 칸 | 비고 |
|---|---|---|
| 별첨 수령 | 11 | 하나손보 7(14분기 전부 수령) · 신한이지 2 · 카카오페이 2 |
| 원문이 raw 에 이미 있음(8-1/8-2 이미지 쪽) | 25 | BNP 9 · 하나생명 9 · RGA 4 · AXA 3 — 텍스트층 기준 「8-1 없음」 판정이 틀렸음. 렌더링으로 확인, 판독은 parser |
| 연말(감사 XML 이 data/dart 에 이미 있음) | 5 | |
| 스캔 PDF 가 원천 · 통째 스캔 | 4+3 | 카카오 2024.2Q·3Q, 하노버 2023.3Q, 하나생명 2024.2Q / AIA 3 |
| BS 는 있으나 줄 자체가 없음 | 2 | 카카오 2025.1Q·2026.2Q (상각후원가 금융자산만 보유) |
| 원천 부재 | 7 | 하노버 6(8-1 없음 5 + 2025.3Q 미게시) · BNP 2024.2Q(회사 파일 잘림) |
| 수집 정책 · 해당 없음 | 4 · 9 | 퍼시픽 2023.x(owner 규칙) · 마이브라운 2023.1Q~2025.1Q(설립 전) |

- **저장 위치:** `data/disclosure/FY*/attachments/KR####_<이름>_attachment_<종류>.pdf` — raw/ 가 아니다. raw/ 는 `KR####_*.pdf` 글롭과 `run_harness` `normalize_tree(pdf_root, "*.pdf")` 가 전부 만져서 별첨이 섞이면 안 된다. 매니페스트 `data/disclosure/_meta/attachments_manifest.json`(60건, sha256·쪽수·표지 확인).
- **새 판 3건(raw/ `_v`):** KR0049 2024.3Q `_v20251020`(K-ICS 완성본, 경과조치 후 286.5%, 기존 raw 는 「공시 예정」) · KR0051 2025.3Q `_v20260429` · KR0050 2025.4Q `_v20261010`. parser(kics) 티켓.
- **방법:** 하나손보 `POST getRegularMngDisclosure.json` · BNP `POST selectRegularNoticeDocList.do`(JSON 본문, 폼 본문은 점검 페이지로 302) · 카카오 `papi.kakaoinsure.com/notilus/v1/notices?categoryId=11` · 신한이지 `hpgpub0001r`(탭 4=결산공고) + `POST /cmn/fileDown` · 하노버는 curl 403 이지만 내장 브라우저로 목록 DOM 전수(2025.3Q 미게시 첫손 확인) · 생보협회 `/FileDown.do?fileNo&seq` 로 교차 대조.
- **실수·복구:** 신한이지 zip 내부 파일명(cp949)을 못 읽어 감사보고서를 잘못 분류해 저장 → 12개를 `data/_archive/<stamp>/` 로 옮기고 재분류(삭제 없음, `attachments_20261011/archive_log.txt`). 맨 `python3 -` 를 한 번 잘못 실행해 CPU 점유 프로세스가 생겨 내 것만 `taskkill`.
- 런로그·칸별 결과 `data/disclosure/_meta/attachments_fetch_runlog_20261011.md` · `attachments_20261011/census_result.json`. parser 티켓 `inbox/parser/20261010T2350Z__downloader__…attachments_raw_ready_bspl.md`(ifrs17) · `…20261010T2351Z__downloader__KR0049-KR0051-KR0050__newer_site_editions_kics.md`(kics).

## 2026-10-10 -- 재보사(외국 재보험사 국내지점) 헤드라인 전용 12칸 재확인 (2칸 해소)

inbox `20261010T1230Z`(orchestrator, route: refetch): KR1102·1104·1105·1107 의 K-ICS 문서 부재 12칸(validation 단계 8 런로그 §7-1)이 지금 받을 수 있는지 재확인.

- **받음 2칸:** KR1102 스위스리 2023.4Q — 사이트 목록에 게시된 판(20240510, 85쪽, 1,599,798 B, sha db423931…)이 기존 보유 판(20240329, 60쪽, "4월말 공시 예정")과 다른 K-ICS 완성본이라 `KR1102_스위스리아시아_v20240510.pdf` 로 병존 저장(기존 보존, `_versions.json` 기록). KR1107 퍼시픽라이프리 2024.3Q — 15쪽, 362,112 B, sha 30ba5b4d…, 회사의 다른 공개 호스트(mo-ams.pacificlife.com)에서 수령(www 는 Incapsula 확인창, 풀지 않음). 이 수령으로 KR1107 2023.3Q 의 `source_unavailable` 사유도 해소(2024.3Q 문서 전년동기 칸).
- **여전히 부재 6:** KR1102 2023.2Q·3Q, KR1104 2023.4Q·2024.1Q, KR1105 2023.2Q = 사이트 게시 판 재수령 sha 동일 + "지급여력비율은 N월말 공시 예정임(부칙 제3조)" 쪽 번호 증거, 후속 문서 없음. KR1104 2025.3Q = 사이트 목록에 항목 없음(첫손 확인). **수집 정책 4:** KR1107 2023.1Q~4Q(owner 규칙 2026-10-09, 정책 불변).
- 이번 하노버 목록 페이지는 curl 200(10-08 에는 403) — 목록 JSON 을 직접 파싱. 스위스리 목록은 curl/WebFetch 403 이지만 브라우저 탭으로 정상 열림(확인창 없음).
- 증거·재현: `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_9d.md`. parser(kics) 티켓 2건 `inbox/parser/20261010T1135Z__downloader__KR1102_2023.4Q__…` · `…KR1107_2024.3Q__…`.

## 2026-09-18 -- KR0150 서울보증 8분기 정기경영공시 재확인 (신규 결측 아님, 기존 판정 재확정)

inbox `20260918T0205Z`(orchestrator, route: refetch): 서울보증(KR0150) 2023.1Q·2023.2Q·2023.3Q·
2024.1Q·2024.2Q·2024.3Q·2025.2Q·2025.3Q 8개 분기 정기경영공시 PDF 부재 재확인 요청. 17BS
PL_breakdown 백필 172칸 중 서울보증 7칸이 이 부재로 막혀 있다는 게 발주 동기.

- **신규 발견 아님** — 요청 8분기는 `scripts/audit_all_periods.py:35-39`의
  `SGI_QUARTERLY_STRUCTURAL` 레지스트리와 정확히 일치(2026-06-01 최초 판정, 2026-06-15
  재확인). 6분기(2023.1Q~2024.3Q)는 2026-09-12에 owner가 SGIC 사이트를 직접 확인해 "원문
  부재"로 이미 확정(`inbox/_resolved/20260911T0115Z`).
- **오늘 라이브 재검증** (`mcp__Claude_Browser__navigate` → `https://www.sgic.co.kr/biz/ccg/index.html?p=CCGIRI010101F01`
  → `get_page_text`): 정기공시 탭에 뜨는 항목은 "2026년 1분기/상반기" + "2025·2024·2023년
  각 연간 경영공시 자료"뿐. 과거 분기 항목은 UI에 존재하지 않는다 — SGIC 공시 SPA가
  "연간 + 최신 1분기만 노출, 지난 분기 롤오프"하는 구조라는 기존 판정(2026-06-01)이 오늘도
  그대로 재현됨. 2025.2Q/2025.3Q도 같은 메커니즘(당시 "최신 분기"였을 때 캡처를 놓쳐 지금은
  물리적으로 회수 불가)으로 설명된다 — 보유 중인 2025.1Q·2025.4Q는 각각 그 순간의 "최신
  분기"·"연간"으로 캡처됐던 것과 정합.
  - 부수 관찰: `curl -m 15 https://www.sgic.co.kr/...`는 이 세션에서 `HTTP=000`이었으나
    브라우저 도구(`Claude_Browser`)로는 정상 로드됨 — 접근 차단이 아니라 curl 경로 문제,
    브라우저로 우회 확인 완료. opendart.fss.or.kr는 curl로도 200 정상.
- DART 경로도 재확인: 서울보증은 미상장(IPO 철회)이라 정기공시가 원천적으로 없음
  (`DART_DROP = {"KR0150"}`, 2026-06-01 owner "걍 버려" 결정) — 대체 소스 없음.
- **재수집 시도 없음**(원천에 파일 자체가 없어 시도할 대상이 없음). `data/disclosure/**`·
  `data/dart/**` 변경 없음. 티켓 `## 답변`에 분기별 표 + 재현 절차 기록 후 `status: resolved` →
  `inbox/_resolved/`로 이동. parser 두 레인(17BS·PL_breakdown 백필)은 이 8칸을 정당 결측으로
  처리.

## 2026-09-12 -- J-ESR FY2025 ESR 공시 게재 census (킥오프 1차 조각, 79사)

owner 09-12 정정: 개별사 ESR 정본은 EDINET XBRL 이 아니라 회사별 공시(IR) 사이트 PDF, 공시 기한 2026-10-31
(06-24 probe 에서 FY2024 XBRL 에 ESR 구성요소 0건이었던 사실과 일치). 킥오프(9월 말) 전에 분모를 재기 위해
downloader 에이전트 2개(행 1~41 / 42~81)로 `jp_insurers.csv` 81행 전수 조회.

- 산출: `J-ESR/fy2025_esr_census_20260912.csv` (utf-8-sig, 14열, 완전 중복 2사 제거 → 79사),
  `J-ESR/jp_insurers.csv` ir_url 공란 41 → 2 (39칸만 diff, 행 순서·다른 열 불변). part csv 는 `J-ESR/raw/`(gitignore).
- 집계: posted 15(생보 10·손보 5) / not_yet 62 / not_found 2. posted = HD 상장 5 그룹값 + 대형 생보 8(상호사 4 포함)
  + 소형 손보 2 solo. 이상치 2건(au 791.7%, Meiji Yasuda Non-Life 743.2%) orchestrator 가 원문 PDF fitz 로 재확인.
- 핵심 사실: 손보 원문 13건 중 11건 + 생보 일부(NN Life·Rakuten Life)가 "신기준 비율은 2026년 10월 말 공표 예정"
  명시. 9월 말 킥오프에서 얻는 것은 페이지 존재(77/79)와 15사 값, 나머지는 10월 말 일괄.
- 한계: not_yet 일부(Zurich Life·AXA Life 등)는 PDF 미열람 패턴 판정으로 notes 에 명시. 10월 말 재census 때 그 행부터.
- 운영 교훈: 에이전트 생존 판정은 `tasks/<id>.output`(placeholder, 0바이트) 가 아니라 세션 `subagents/agent-<id>.jsonl`
  mtime — 살아 있는 에이전트를 죽여 13분 재작업. 이 PC 는 시간대별로 curl 이 막혔다 풀림(part1 은 WebFetch 만으로 수행).

## 2026-09-12 (2) — 정정본 병존 저장 구현 + KR0075 2023.4Q 0.08% 차 정정공시 조사(정정 없음)

오케스트레이터 발주 2건(직접 처리, 하위 에이전트 미사용). 첫 동작 네트워크 확인
(`curl opendart.fss.or.kr` → 200) 후 작업 1(코드, 네트워크 무관) → 작업 2(DART 조회) 순서로 진행.

### 작업 1 — 정정본 병존 구조

**문제**: 같은 (분기,회사) 로 새 게시물이 오면 기존 raw 를 조용히 덮어썼다. 착수 전 실측
census(`data/disclosure/*/raw/*_amended*.pdf`) — 110개 중 원본과 실제로 병존한 건 **1건뿐**
(`FY2025_Q3/raw/KR0011_DB손해보험_amended2.pdf` ↔ `KR0011_DB손해보험.pdf`)이고 그나마 바이트가
동일했다. 나머지 109개는 애초에 원본이 저장된 적이 없는 "정정본만 단독 저장"이었다 — 과거
백필 스크립트들이 최신본 하나만 받아 `_amended` 라는 이름만 붙인 것으로, 병존 메커니즘 자체가
없었다. 이번 수정은 **호출 시점부터**만 적용된다(과거분 소급 복원 없음, 이미 덮어써진 원본은
복구 불가).

**구현**: `scripts/_disclosure_pdf_paths.py`(기존 raw/pdf 해석기 모듈)에 `save_versioned_pdf()`
신규 — stdlib(`hashlib`/`json`/`datetime`)만 사용, 새 의존성 없음.

- 대상 파일 없음 → 그냥 저장, `"new"`.
- 있고 새 바이트 sha256 이 기존과 동일 → 재저장 skip(로그 1줄), `"unchanged"`.
- 있고 sha256 이 다름(정정본 추정) → 원본은 그대로 두고 `<stem>_v<YYYYMMDD><ext>` 로 병존
  저장 + 같은 폴더 `_versions.json` 사이드카에
  `{기본파일명: [{file, sha256, posted, title, url, fetched_at}, ...]}` append, `"versioned"`.
  날짜는 `posted`(게시일, YYYYMMDD)가 있으면 그걸 쓰고 없으면 다운로드 시각(UTC) 날짜.
  같은 날짜로 같은 바이트를 또 받으면(재실행) 중복 파일 없이 idempotent, 같은 날짜에 세
  번째로 다른 바이트가 오면 `_v<날짜>_2` 로 추가 분기.

**배선**: `download_disclosure_2026q2_nonlife.py::_save()`(회사별 정기경영공시 저장 단일
지점)와 `download_disclosure_2026q2_life_sites.py`(생보 자사 사이트 직접 수집, 2026-08-30
신설분)의 저장 호출부를 이 함수로 교체. 둘 다 `sys.path.insert(0, str(ROOT/"scripts"))` +
`from _disclosure_pdf_paths import save_versioned_pdf` 패턴(`report_collection_status.py`
기존 관례와 동일). Import-only 스모크(모듈을 `importlib` 로 직접 로드, `main()` 미호출)로
sys.path 배선 확인. **생보 일괄 zip 다운로더(`download_disclosure_2026q2_life.py`)는 건드리지
않았다** — 회사별 고정 파일명이 아니라 협회 페이지의 `suggested_filename` 을 그대로 쓰는
단일 아카이브라 이 정정-병존 모델과 모양이 달라 범위를 넓히지 않음(알려진 한계로 기록).

**공유 해석기 안전성 확인(발주 원문의 명시 요구)**: `disclosure_pdfs()` 가 `_v*` 파일을 별개
회사로 오인하는지 실측 확인 — 오인하지 않는다. glob 패턴이 `f"{code}_*.pdf"` 로 회사코드 +
언더스코어를 정확히 앵커링하고, 이 저장소의 KR 코드는 전부 고정폭(KR + 4자리)이라 한 코드가
다른 코드의 prefix 가 될 수 없다(예: `KR0150_...` 는 `KR0015_*.pdf` 패턴과 매칭 불가). 호출부
`report_collection_status.py::check_disclosure()` 도 `bool(matches)` 판정이라 파일 개수와
무관. 회귀로 고정: `tests/unit/test_disclosure_pdf_versioning.py` 신규 6개 — `save_versioned_pdf`
4분기(new/unchanged/versioned/idempotent) + `disclosure_pdfs()` 회사-수 불변 케이스(KR0150 에
`_v20260912` 파일을 추가해도 그 기간의 distinct 회사코드 집합이 3 그대로임을 검증, 발주가 예시로
든 파일명 그대로 사용). `pytest tests/unit/ tests/test_disclosure_raw_pdf_wiring.py` — 405 passed
(기존 399 + 신규 6, 회귀 0).

**문서**: `docs/agents/claude-agent-downloader.md` "Canonical Folder Layout" 아래 새 절
"Amended filings coexist, never overwrite" 추가(다음 분기 스크립트 복제 시 이 저장 호출
패턴을 그대로 가져가라는 지시 포함) · `docs/agents/source-catalog.yaml` `validation.versioning`
한 줄 추가.

### 작업 2 — KR0075(비엔피파리바카디프생명보험) 2023.4Q 0.08% 차 조사

**배경**: `inbox/_resolved/20260902T1200Z`(ifrs17 레인 답변, 2026-09-11)이 남긴 미해결 —
2023.4Q 감사보고서 원문(rcept `20240403001384`, 비정정)의 자산총계·부채총계가 마스터
(`IFRS17_BS.json`, vision-read + 2024.1Q/2024.3Q 비교열 3중교차확인)보다 2,411.95백만원(0.08%)
작았다. ifrs17 레인의 가설: 정정공시(기재정정)가 나중에 제출돼 마스터가 정정본을 반영했을
가능성.

**결과 = 정정공시 없음, 확정.** `find_corp_codes_by_name("비엔피파리바카디프")` → corp_code
`00460798`(1건, 모호성 없음). `list.json`(corp_code=00460798, bgn_de=20240101, end_de=20260912,
pblntf_ty 미지정=전체 유형) → **총 3건**, 전부 평범한 연간 감사보고서 1건씩(2023/2024/2025
결산): `20240403001384`(2024-04-03) / `20250404003021`(2025-04-04) / `20260406004430`
(2026-04-06). `report_nm` 어느 것도 `[기재정정]`/`[첨부정정]` 대괄호 접두 없음, `rm` 필드
3건 전부 공백. **KR0075 는 FY2023 실적에 대해 단 한 번도 정정 제출을 하지 않았다** — ifrs17
레인의 가설은 반증됨. 지침대로(정정본 없으면 티켓 없이 보고) `inbox/parser/` 티켓은 만들지
않았고, 이 결과는 이 changelog 항목과 `TODO_downloader.md` Status 로 기록만 한다.

0.08% 차이의 실제 원인(마스터 vision-read 오독인지, 정정 없이 이뤄진 비-DART 소급 재작성인지)은
**여전히 미확정**이다 — 파싱/마스터는 downloader 소관이 아니라 손대지 않았다. 추가 진단으로
FY2024 감사보고서(`20250404003021`, 2023.12.31 비교열을 담고 있어 마스터 수치와 대조 가능)
본문을 받으려 시도했으나 아래 네트워크 단절로 착수만 하고 완료하지 못함 — 다음 세션이 필요시
이어받을 수 있는 지점(rcept_no 확보 완료)만 남겨 둔다.

**네트워크**: list.json 2회 성공 직후 document.xml 요청부터 `curl` exit 56(recv error) →
재시도 exit 7(connect fail) → opendart·github 순수 reachability 재확인도 exit 7/`000`. 어제
기록된 "01:10 KST 외부 443 전면 차단"과 같은 패턴으로 판단해 루프 재시도 없이 중단(100분
무산출 kill 재발 방지, 발주 지시 그대로). **추가 관찰(미확정, 표본 1회)**: 이 단절 이전에
`curl` 은 살아있는 채로 python venv 의 `requests`(`OpenDARTClient._get`)만 같은 호스트에서
`WinError 10013`(WSAEACCES)로 실패한 구간이 있었다 — `dangerouslyDisableSandbox=true` 로도
동일. 재현 안 해 확정은 아니지만, 다음 세션이 "curl 200 = python 기반 DART 스크립트도 정상"
으로 곧장 등치하지 않도록 기록해 둔다.

**재현**:
```
curl -s -m 30 "https://opendart.fss.or.kr/api/list.json?crtfc_key=$OPENDART_API_KEY&corp_code=00460798&bgn_de=20240101&end_de=20260912&page_count=100"
# status":"000" · total_count":3 · 세 rcept 모두 report_nm에 대괄호 없음/rm 공백이면 재현 성공
```

## 2026-09-12 — 서울보증 과거 분기 경영공시 = 원문 부재 (owner 확정)

> inbox `20260911T0115Z` 종결. 서울보증은 2023·2024 분기 경영공시를 자체 게시하지 않아 KR0150 6분기(2023.1Q~2024.3Q)는 정당 결측. 미래에셋 2023.2Q MD 갭은 parser 티켓 `20260912T0115Z`. 정정본 병존 구조는 TODO follow-up 으로 이월. 부수: PC 외부 443 차단으로 downloader 에이전트 100분 무산출 → kill(네트워크 사전 확인 규칙).

## 2026-09-03 -- FY2026_Q2 정기경영공시 raw/ 정본화(1→39) + 항목5 해약환급금준비금 3분기 이월버그 발견

owner 직접 지시: "FY2026_Q2 정기경영공시 PDF가 거의 통째로 빠져 있다. 회수해라." 근거로 든
실측은 `data/disclosure/FY2026_Q2/raw/*.pdf` count=1(하나손해보험뿐). 동기: owner가 해약환급금
준비금을 정기경영공시 기준으로 정정 지시했는데 삼성생명(KR0069) 2026.2Q가 마스터에 2025.4Q
값(832,412백만)이 그대로 이월돼 stale인데 대조할 원문이 없다는 것.

### 1단계 — "거의 다 빠졌다"는 관찰은 맞았지만 원인이 달랐다

`raw/` count=1은 사실이었다. 하지만 `data/disclosure/FY2026_Q2/pdf/`를 보니 **39개 파일이 전부
있었다**(8/31 18:41~21:28 mtime, KR0001~KR1098 39사 전원, 개별 SHA256 전부 FY2026_Q1 raw와
다름 — 재탕 아님). `git log -- data/disclosure/`는 아무것도 안 나온다(`data/disclosure/`는
`.gitignore:36`으로 통째 제외라 이 디렉터리는 브랜치 무관 로컬 디스크 상태). git 이력이 아니라
스크립트 소스로 추적: `download_disclosure_2026q2_nonlife.py`·`download_disclosure_2026q2_
life_sites.py` 둘 다 `OUT_DIR = .../FY2026_Q2/pdf`로 이미 **커밋돼 있었다**(`8f5e3b8`, 2026-09-01
04:56, "정기경영공시 39사 전원 적재 + 검증 RED 0 (라운드 완주)" — 이 커밋은 `fix/csm-product-
segmented-columns` 브랜치, 즉 이 세션과 같은 브랜치의 조상). 그 커밋 메시지 자체가 KR0011
(DB손해)·KR0029(AIG)·KR0150(서울보증)의 직전분기-재탕 버그를 잡아 `validate_disclosure_
freshness.py`를 신설한 라운드였고, `TODO_downloader.md`의 "2026-09-01 선택자 하드닝" 항목과
겹치는 작업인데도 **`raw/`가 아니라 `pdf/`에 쓰는 것으로 관례가 바뀐 사실 자체는 downloader
TODO 어디에도 기록되지 않았다.** 그래서 이번 세션 시작 시점까지 아무도(TODO를 읽는 한) 몰랐다.

같은 시기 validation이 이 어긋남을 이미 발견해 처리한 기록이 `inbox/_resolved/20260901T0430Z
__validation__MULTI__raw_vs_pdf_dir_assumption_11_scripts.md`에 있다: `raw/` 39곳 glob 스크립트
11개를 공유 해석기 `scripts/_disclosure_pdf_paths.py::disclosure_pdfs()`(raw 우선, 없으면 pdf
폴백)로 교체 완료, flip 0건 회귀검증까지 끝나 있었다. 즉 **K-ICS 파싱·검증 파이프라인은 이미
`pdf/`를 정상적으로 읽고 있어서 안 깨졌다** — 깨진 건 "owner가 census를 낼 때 보는 위치"뿐이었다.
같은 티켓이 "어느 쪽으로 통일할지는 downloader/orchestrator 결정"이라고 명시적으로 넘겨놓은
상태였는데, 그 결정이 이번까지 안 내려져 있었던 것.

### 2단계 — 정리 도중 동시 세션 개입 관측

이 사실을 확인하고 `pdf/`→`raw/` 정규화를 하려던 시점(census A: pdf=39·raw=1), 검증 스크립트를
준비하는 사이 재확인하니(census B, 수 분 후) **이미 pdf=0·raw=39로 바뀌어 있었다** — mtime은
8/31 그대로 보존(재다운로드가 아니라 순수 이동). 공유 워킹트리에서 동시에 다른 세션이 같은
정규화를 수행한 것으로 판단, 내가 한 것이 아니다. 결과는 원하던 상태와 동일해 그대로 인정하고
검증만 이어갔다.

### 3단계 — 39사 내용검증

신규 `scripts/_probes/probe_20260903_verify_2026q2_disclosure_pdfs.py`(fitz 텍스트추출 +
페이지밀도 + 기간마커 + "해약환급금준비금" 절 검출, 산출 `data/_derived/disclosure_2026q2_
content_verify.json`):

- **회사 커버리지**: raw/ 39개 KR코드가 `source-catalog.yaml`의 disclosure 계열 기대 집합
  39개와 **정확히 일치**(과부족 0).
- **기간마커**("2026년2/4분기"·"2026.1.1~6.30"류) 36/39 전자검출. 나머지 3사(KR0010 KB손해보험·
  KR0079 미래에셋생명·KR0087 동양생명)는 fitz 추출 문자수가 각각 0·4,917·258(65~59페이지
  분량 치고 극단적으로 낮음) — 스캔본 의심. **240dpi 렌더(`scripts/_probes/_render_20260903_
  scan_check.py`)로 표지+본문 페이지 육안 확인**: 셋 다 회사명·"2026년 2/4분기"·"2026.1.1~
  6.30"이 이미지로는 선명하게 보임(KB손해보험 표지, 미래에셋생명 표지, 동양생명 표지 확인) —
  **키워드 0회가 원문 없음이 아니라 텍스트레이어 없음이었다**(이 저장소가 반복 지적하는
  함정 그대로). 진짜 그 회사·그 분기 원문 맞음, OCR 필요(parser 소관, downloader가 처리 안 함).
- **freshness 게이트**: `validate_disclosure_freshness.py --period FY2026_Q2` → RED=0 YELLOW=0
  GREEN=39(직전분기 파일과 전부 다름 — 재탕 없음, 8/31 라운드에서 이미 고친 버그가 유지 확인).

### 4단계 — 7-3 절(해약환급금준비금등의 적립) 39/39 보유 확인 + owner 지시 정정

owner 지시문은 "생보 7-2/7-3, 손보 5-3"이라 했으나 **손보도 "7-3"을 쓴다** — KR0049(악사손해
보험)·KR0051(신한이지손해보험) 두 손보사의 raw에서 직접 "7-3. 해약환급금준비금 등의 적립"
절을 확인(정규식이 "5-3"만 찾다가 처음엔 손보 17사 전원 0건으로 나와서 발견, 내 정규식
가정이 틀렸던 것이지 원문이 없는 게 아니었다). 최종 39/39 전원 절 보유 확인 — 37사는 전자
텍스트(일부는 라벨→절번호 순서가 레이아웃상 뒤바뀌어 근접매칭 폴백 필요, KR0068·KR0072·
KR0079·KR0083·KR0097·KR1098), 2사(KR0010·KR0087, 완전 스캔본)는 절 자체 유무를 OCR 전엔
전자적으로 확정 못 함(대조 불가 사유로 명시, 값을 만들어내지 않음).

### 5단계 — KR0069 실측 및 파생 발견: 항목5(해약환급금준비금) 3분기 이월버그 4사

KR0069 raw p48 "7-3.해약환급금준비금등의적립" 표를 240dpi 렌더로 직접 육안 확인(fitz 텍스트
추출 순서가 열/행이 뒤섞여 나와 표를 정확히 읽으려면 렌더가 필요했다):

| 구분 | 2026.2Q(2026년6월) | 2026.1Q(2026년3월) |
|---|---|---|
| 이익잉여금 | 163,100 | 161,340 |
| 대손준비금 | 2,875 | 2,999 |
| **해약환급금준비금** | **31,260** | **16,518** |
| 보증준비금 | - | - |

(단위 억원). `IFRS17_BS.json` 항목5 "해약환급금준비금 적립액"을 대조하니 **2025.4Q=2026.1Q=
2026.2Q 세 분기가 832,412(백만원)로 완전히 동일** — 원문은 분기마다 크게 움직이는데(억원
단위 환산: 1,651,800백만→3,126,000백만) 마스터는 3분기째 얼어 있다. owner 의심이 정확했다.

**같은 패턴이 더 있는지 IFRS17_BS.json 전수 스캔** — 항목5에서 2025.4Q=2026.1Q=2026.2Q
완전동일값인 회사 6개사를 찾아 각각 raw로 대조:

- **버그 확정 4사**(원문이 매 분기 실제로 다른데 마스터는 얼어 있음): KR0069 삼성생명(위 표),
  KR0049 악사손해보험(마스터 41,366.023 고정 vs raw 452억/349억=45,200/34,900백만),
  KR0097 하나생명보험(마스터 88,526.971 고정 vs raw 924억/969억=92,400/96,900백만),
  KR0080 AIA생명(마스터 751,339.0 고정 vs raw 7,484억/7,586억=748,400/758,600백만 — 변동폭이
  작아 마스터값이 두 분기 사이에 있지만 **어느 쪽과도 정확히 일치하지 않아** "갱신 안 됨"의
  증거로 채택).
- **대조군 2사**(같은 3분기-플랫이지만 원문도 0이라 정상, 손대면 안 됨): KR0004 MG손해보험
  (원문 "0", 미처리결손금으로 대손준비금 등 무적립 각주 명시), KR0075 비엔피파리바카디프생명
  (원문 "-" 양분기 모두).
- 참고로 KR0072(케이디비생명)는 2026.1Q=23,550 vs 2026.2Q=4,323로 마스터가 이미 분기별로
  다른 값을 갖고 있고 raw(235억/43억=23,500/4,300백만)와 오차 0.2% 이내로 근접 — 정상 갱신
  중인 항목이라 이 버그 패턴에서 제외.

값 산출 로직은 parser(ifrs17) 소관이라 downloader가 고치지 않고, 근거(raw 경로·페이지·양쪽
수치)를 갖춰 `inbox/parser/20260903T0048Z__downloader__MULTI_2026.2Q__item5_surrender_
reserve_frozen_3q.md`로 발주. 3분기 윈도우만 스캔했으므로 더 이전부터 얼어있을 가능성,
같은 표의 다른 행(대손준비금·보증준비금 등)도 같은 경로를 타는지는 미확인 — parser 후속 필요.

### census

```
data/disclosure/FY2026_Q2/raw  1 -> 39  (39/39 = source-catalog 기대 집합과 정확히 일치)
```

미게시(not_posted) vs 다운로드 실패(failed) 구분은 이번엔 불필요했다 — 39사 전원 이미
posted+fetched 상태(8/31 라운드 산출물)였고, owner가 우려한 "일부 미게시"는 해당 사항 없음.

### 산출물

- `scripts/_probes/probe_20260903_verify_2026q2_disclosure_pdfs.py` (재사용 가능, 39사 내용
  검증 — 기간마커/절검출/스캔의심 3종)
- `scripts/_probes/_render_20260903_scan_check.py` · `_render_20260903_kr0069_p48.py` ·
  `_dump_20260903_surrender_context.py` (일회성 진단 렌더/텍스트덤프)
- `data/_derived/disclosure_2026q2_content_verify.json` (39사 검증 결과 원장)
- `inbox/parser/20260903T0048Z__downloader__MULTI_2026.2Q__item5_surrender_reserve_frozen_
  3q.md` (신규 발주)
- `inbox/downloader/20260901T1600Z__parser__MULTI_2023.4Q__missing_annual_raw_3_companies.md`
  → `_resolved/`로 이동(2026-09-02 census에서 이미 회수 완료였는데 `## 답변`이 안 채워진 채
  방치돼 있던 것을 이번 드레인에서 확인 후 종결 — memory "Auto-close answered inbox" 재확인).

### 다음 세션 참고

`download_disclosure_2026q2_{nonlife,life_sites}.py`의 `OUT_DIR`은 여전히 `pdf/`로 박혀 있다
(고치지 않음 — 명시 지시 없이 `scripts/` 건드리지 않는 범위 규칙). 다음에 이 스크립트로
FY2026_Q3 이후를 새로 받을 때 그대로 실행하면 다시 `pdf/`에 쓰고 `raw/`는 안 채워진다.
orchestrator/owner가 이 관례를 `raw/`로 되돌릴지, 아예 `pdf/`를 신정본으로 승격하고
`source-catalog.yaml`·13분기 레거시 관례까지 다 맞출지 결정이 필요 — 이번엔 raw/ 로
정규화하는 쪽으로 처리했지만 스크립트 자체를 안 고쳤으므로 다음 라운드에서 또 벌어진다.

## 2026-09-02 -- DART 본문 XML 전수 census: 발주된 "결측" 은 전부 오탐, 진짜 결손 3칸은 회수

IFRS17_BS(별도/OFS 기준) 를 DART 본문 XML 원문과 전수 대조하려는데 원문이 없는 (회사,분기)
가 있다는 발주. 실측 예로 **삼성생명보험 2026.2Q · 미래에셋생명보험 2026.2Q 는
`data/dart/FY2026_Q2/raw/` 에 디렉터리 자체가 없다** 고 명시돼 왔다.

### 그 두 칸은 결측이 아니었다 — 이름으로 훑은 탐지기의 오탐

디스크에 **둘 다 멀쩡히 있다**: `KR0069_삼성생명/20260814003263.xml`(5,304,327B) ·
`KR0079_미래에셋생명/20260814004054.xml`(3,694,785B). raw 리프는
`KR####_<DART canonical name>` 인데 **DART canonical 이 K-ICS 원수사명과 다르다** —
DART 는 '삼성생명'·'미래에셋생명', K-ICS 는 '삼성생명보험'·'미래에셋생명보험'.
`_dart_path_helpers.py` 의 `quarterly_raw_dir` docstring 이 이 차이를 이미 명시하고 있는데,
회사명으로 디렉터리를 찾은 쪽이 그걸 안 보고 "원문 자체가 없음" 으로 결론냈다.
**KR 코드로 키를 잡으면 안 생기는 오탐이다.**

### 전수 census 를 뜨니 함정이 하나 더 있었다

39사 x FY2023_Q1..FY2026_Q2 = **546칸** 을 실측했다. 처음 판정에서 **64칸이 "zip 만 있고
본문 XML 없음"** 으로 나왔는데, 전부 `leaf/xml/*.xml` 로 **이미 풀려 있었다.**
`extract_dart_zips.py` 는 세 레이아웃(`*.xml` · `xml/*.xml` · `extracted*/*.xml`)을 다
인정하는데 리프 바로 밑만 glob 하면 그 64칸이 통째로 거짓 결측이 된다.

### census 결과 (before -> after)

| 판정 | before | after |
|---|---|---|
| xml (본문 있음) | 372 | **375** |
| zip_only | 0 | 0 |
| no_filing (원천 부재 기록됨) | 43 | **45** |
| MISSING | 131 | **126** |
| └ 분기 공시사 = **진짜 결손** | **3** | **0** |
| └ 연1회 공시사 비-4분기 (원천에 분기 필링 없음) | 128 | 126 |

**우선순위 축(2026.2Q -> 2025.4Q -> 2024.4Q -> 2023.4Q)은 전부 닫혔다.**
2026.2Q 는 분기 공시사 24사 전원 본문 확보(결손 0), 2025.4Q·2024.4Q 도 이미 39/39 였고,
**2023.4Q 만 3칸이 비어 있었다 — 그 3칸이 이번에 회수한 전부다.**

### 회수한 3칸 — 전부 "사업보고서로 찾아서 못 찾았던" 케이스

셋 다 **사업보고서를 안 내고 감사보고서만 내는** 회사다. 그래서 `pblntf_detail_ty=A001`
(사업보고서) 로 훑던 과거 스윕이 `no_filing` 으로 기록했다. `pblntf_ty=None` 으로 전체를
훑으면 바로 나온다 — AIG(2026-08-19)·악사손해 등 5사(2026-08-20)와 **같은 함정의 세 번째
재발**이다.

| 칸 | rcept | 크기 | 내용검증 |
|---|---|---|---|
| KR1098 카카오페이손해 2023.4Q | `20240329002933` 감사보고서(2023.12) | 47,512B zip / 385,373자 | 제3(당)기 · 2023-12-31 x12 · 회사명 x13 · 보험수익 25 |
| KR0075 BNP파리바카디프 2023.4Q | `20240403001384` 감사보고서(2023.12) | 78,369B zip / 589,486자 | 제22(당)기 · 2023-12-31 x9 · 회사명 x16 · 보험계약마진 30 |
| KR0150 서울보증 2023.4Q | `20240403001186` 감사보고서(2023.12) | 104,319B zip / 878,776자 | 제57(당)기 · 2023-12-31 x16 · 회사명 x22 · 재무상태표 17 |

**KR0150 은 기존 판정을 뒤집는다.** 2026-08-19 발주 C 는 서울보증 2023.1Q~2024.3Q 7분기를
`no_filing` 으로 **확정**했는데(사유: "DART 에 정기보고서 자체가 없음"), 2023.4Q 는
정기보고서가 없는 게 맞지만 **감사보고서·연결감사보고서가 둘 다 있다.** 1~3분기는 진짜
부재가 맞다(감사보고서는 연 1회). 카카오페이의 `보험계약마진` 0회는 PAA 소액단기 특성,
서울보증의 2회는 기존 "구조적 CSM-無" 판정과 일치 — 둘 다 오문서 신호가 아니다.
연결감사보고서는 안 받았다(`known_absent` 의 "별도가 본체" 관례 유지).

경로: `OpenDARTClient.fetch_document_xml` + `_dart_path_helpers.annual_raw_dir` ->
`scripts/extract_dart_zips.py` (기존 2단계 그대로, 새 다운로드 스크립트 없음).
`meta.json` 은 기존 annual 포맷(period/rcept_no/corp_code/canonical/report_kind/fetched_at).

### 2026.2Q 본문 내용검증 — 24/24 통과 (발주 목적이 이것이었다)

디스크에 있다는 것만으로 끝내지 않고 24사 전원 본문을 열어 확인했다. 전원
**제 NN 기 · 2026-06-30 마커(50~203회) · 2025-12-31 비교기 · 재무상태표/자본총계/부채총계/
자산총계 키워드** 를 갖췄고, 문서 크기 1.2M~22.3M자로 스캔본·빈 껍데기 없음.
플래그 1건은 **NH농협손해 — 본문이 자기를 '농협손해보험' 이라 쓰는데 리프/meta canonical
은 'NH농협손해보험'** 이라 정확일치가 빗나간 것(32회 매칭됨). 데이터 문제가 아니라
**발주를 만든 것과 똑같은 종류의 탐지기 함정**이다. 서울보증만 `보험계약마진` 0 —
구조적 CSM-無로 기존 확정.

### 재발 방지 — 경로자산

**신규 `scripts/_probes/census_dart_body_xml.py`** (재사용 가능, exit 1 on 진짜 결손).
위 함정 2종을 docstring 에 실측 수치와 함께 박아 뒀고, 연1회 공시사 판정은 추측하지 않고
`data/_derived/bs_carry_forward_cells.json` 의 `hold_forward_annual_only_filer` 를 읽는다
(+AIG). `--json` 으로 셀 판정을 덤프한다.

`check_dart_raw_coverage.py` 와는 **축이 반대라 둘 다 필요하다** — 그쪽은 "한 번이라도
있었던 칸이 사라졌나"(high-water mark), 이쪽은 "기대 그리드에 애초에 없는 칸". 유실
축은 이번에도 clear(baseline 395 -> `--update` 로 398, missing=0, known_absent 5 유지).

AIG 2026.1Q/2Q 는 라이브로 `list_filings(pblntf_ty=None)` 확인해 2026년 필링이
감사보고서(2025.12) 2건뿐임을 재확인하고 다른 연1회 공시사와 같은 `no_filing` 마커를
남겼다(그래서 no_filing 43 -> 45). 나머지 126칸(연1회 공시사 x 비-4분기)은 마커가 없을
뿐 같은 성격이며, 레지스트리로 커버된다.

> 미착수(의도적): AIG 2022.4Q 2건은 owner 가 2026-08-19 에 2022.4Q 백필 전체를 보류
> 확정했으므로 손대지 않았다. `known_absent` 5건 그대로 유지.
