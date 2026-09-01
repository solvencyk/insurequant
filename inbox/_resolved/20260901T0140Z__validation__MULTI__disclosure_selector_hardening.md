---
from: validation
to: downloader
created: 20260901T0140Z
status: resolved
route: refetch
company: MULTI
period: 2026.2Q
lane: kics
iter: 1
---

## 미결 (sender 작성)

2026.2Q 라운드에서 **세 회사가 직전 분기 PDF 를 그대로 받아왔다** — KR0011 DB손해 ·
KR0029 AIG손해 · KR0150 서울보증. 셋 다 재수집으로 데이터는 복구됐고 해당 티켓 3건은
`_resolved/` 로 종결했다(`20260831T111450Z` x2, `20260831T1049Z`). **남은 것은 재발 원인인
셀렉터/파라미터 고정이다.** 세 티켓 모두 이 항목을 "선택" 또는 "downloader 소관"으로 남긴 채 닫혔다.

### 실측 (2026-09-01, `docs/agents/source-catalog.yaml`)

| 회사 | 줄 | 현재 값 | 왜 매 분기 재발하나 |
|---|---|---|---|
| KR0011 DB손해 | L72 | `xpath: '//*[@id="content"]/.../ul/li[1]/a'` | 목록의 **첫 항목 위치 고정** — 새 분기가 추가돼도 옛 항목을 가리킬 수 있음 |
| KR0029 AIG손해 | L78 | `url2: ...&pancId=15467` | `notes` 에 "pancId varies per quarter" 라고 적혀 있는데 **값은 1분기 것으로 하드코딩** |
| KR0150 서울보증 | — | 사이트가 다운로드 링크 5개에 `id="test1"` 중복 사용 | 고정 xpath 가 항상 첫(1분기) 링크를 집음 |

### 요청

분기 라벨("상반기"/"2분기"/"26.2Q") 텍스트 매칭 등 **위치가 아니라 내용으로 고르는 선택자**로
바꾸고, `pancId` 류 분기별 파라미터는 목록 페이지에서 매번 해석하도록 할 것.

### 지금 안전한 이유 (급하지 않은 근거)

`scripts/validate_disclosure_freshness.py`(2026-08-31 신설)가 `scripts/prepush_check.py` L94
도메인 게이트 묶음에 배선돼 있고, 그 exit code 가 L228 `blocked = ... or n_dom ...` 로 흘러
**재탕이 다시 들어오면 push 가 막힌다**. 2026-09-01 10:18 KST 실행 결과
`[FY2026_Q2] RED=0 YELLOW=0 GREEN=39`. 즉 조용한 통과는 더 이상 불가능하고, 이 티켓은
"매 분기 사람이 손으로 재수집하는 일" 을 없애는 것이 목적이다.

## 답변 (downloader 작성 — 2026-09-01, 처리 후)

세 회사 모두 **위치/id/하드코딩 파라미터 → 분기 라벨 텍스트 매칭**으로 교체했다. 실제 사이트를
열어 현재 마크업을 확인한 뒤 고쳤다(추정 없음) — 세 회사 다 요청 기간(2026년 상반기) 라벨이
이미 게시돼 있었고, 그 라벨을 앵커로 삼았다. 수정 위치: `docs/agents/source-catalog.yaml`
(KR0011/KR0029/KR0150 세 entries) + `scripts/download_disclosure_2026q2_nonlife.py` (실제 다운로드
엔진 — INSURERS 딕셔너리 + `_run_one`).

### 회사별 변경

- **KR0011 DB손해**: 사이트가 `list.jsp`를 `dl>dd>ul>li` 목록에서 **표(table)로 리뉴얼**했다
  (실측). `url2`(고정 `i=` 상세페이지 id, 1분기 값 `4c3187cc8627450a93bc` 하드코딩)를 없애고
  `mode: two_step`으로 전환 — `list.jsp`를 매번 열어 링크 자체 텍스트가
  `contains(., "2026")` and `("상반기" or "2분기")` and `not("1분기")` 인 행을 클릭, 상세페이지의
  `i=`는 그 결과로 스스로 정해진다. 상세페이지 내 `li[1]` (첫 첨부파일)은 그대로 뒀다 — 그 페이지는
  이미 올바른 분기로 좁혀졌으므로 위치 선택이 안전함을 확인(첨부 3개 전부 `20260831NN.pdf`, 동일
  분기).
- **KR0029 AIG손해**: 실측 결과 사이트가 **2단계 자체를 없앴다** — PDF 다운로드 href
  (`/downLoadFiles.do?fileId=...`)가 이제 목록 페이지(`dpwom012.html`) 안, 분기 라벨을 담은
  `<div class="conBox"><strong>` 바로 옆에 직접 있다. `url2`/`pancId=15467` 하드코딩을 통째로
  제거하고 `mode: direct_href`로 단순화 — 라벨 텍스트로 `conBox`를 고른 뒤 그 안의 다운로드
  링크를 바로 읽는다. 2단계가 없어졌으니 pancId 자체가 더 이상 코드에 존재하지 않는다.
- **KR0150 서울보증**: 실측으로 `id="test1"` 중복(5개 링크 전부)을 재확인. `xpath`를
  `//a[@id="test1" and contains(., "2026") and (contains(., "상반기") or contains(., "2분기")) and
  not(contains(., "1분기"))]`로 교체 — id 대신 그 링크 자신의 표시 텍스트로 고른다.

### 다운로더 자체 검증 (요청 2)

세 entry 모두 `period_include_regex`/`period_exclude_regex`를 추가하고, `_run_one`에 새
`_verify_period()` 훅을 넣었다 — 선택자가 실제로 집은 요소의 텍스트를 다운로드 **직전**에
정규식으로 재검사해서, 기대 분기가 아니면 (조용히 저장하지 않고) `RuntimeError`로 즉시
실패시킨다. 부수효과로 `two_step_direct_url` 모드는 이 세 회사가 유일한 사용처였는데 둘 다
전환됐으므로 죽은 코드가 돼 `_run_one`에서 같이 제거했다.

### 실제 재수집 검증 (요청 3)

`data/disclosure/` 는 건드리지 않고, 스크래치 디렉토리에서 실제 엔진(import한 실코드, 사본 아님)을
그대로 돌렸다:

| 회사 | 대상분기(2026.2Q) 재수집 | 회귀(2026.1Q, 같은 코드에 라벨만 뒤집어 재수집) |
|---|---|---|
| KR0011 | `period verify OK: '2026년 상반기 DB손해보험 현황(경영공시)'`, 1,421,268 bytes, **repo FY2026_Q2 파일과 sha256 완전 일치** | 767,251 bytes, **repo FY2026_Q1 파일과 sha256 완전 일치** |
| KR0029 | `period verify OK: '2026년 상반기 경영공시N'`, 1,178,606 bytes, **sha256 일치** | 708,152 bytes, **sha256 일치** |
| KR0150 | `period verify OK: '2026년 상반기 경영공시 자료'`, 1,008,866 bytes, **sha256 일치** | 579,028 bytes, **sha256 일치** |

PDF 본문(fitz 1페이지 추출)도 셋 다 "2026년 상반기 ... 현황, 기간: 2026.1.1-2026.6.30" 로 시작해
라벨만이 아니라 **문서 내용도 2026.2Q**임을 확인. 회귀 케이스는 정확히 기존
`data/disclosure/FY2026_Q1/raw/` 파일과 sha256이 일치 — 같은 선택자 로직이 "요청한 분기"를
실제로 따라간다는 뜻(우연히 항상 2Q만 집는 게 아님).

이후 `python scripts/validate_disclosure_freshness.py --period FY2026_Q2` → `[FY2026_Q2] RED=0
YELLOW=0 GREEN=39` (변경 전과 동일, `data/disclosure/`는 무변경이므로 당연한 결과지만 회귀 확인).

### 정적검사 (요청 4)

`tests/test_disclosure_selector_hardcoding.py` 신설(12 tests) — 세 회사의 selector가 다시
위치/id/pancId 리터럴로 되돌아가면 실패한다. **원본(수정 전) 파일에 대해 실제로 돌려 12개 전부가
FAIL함을 확인**(mutation test, `git stash`로 왕복) — 공허한 통과가 아님. 단,
**`scripts/prepush_check.py`의 `fast` 리스트에는 추가하지 않았다** — 그 파일이 지금 이 워킹트리의
다른(validation) 세션에 의해 동시에 수정 중인 것을 `git stash`/`git status`로 확인했고, 티켓
지침상 내 담당은 source-catalog.yaml + downloader 엔진 코드뿐이라 충돌 위험이 있는 공용 게이트
파일은 손대지 않았다. **테스트 파일은 존재하지만 아직 훅에 배선되지 않은 상태** — validation/
orchestrator가 `fast` 리스트에 `"tests/test_disclosure_selector_hardcoding.py"` 한 줄을 추가해야
실제로 push를 막는다(CLAUDE.md "배선했다 != 강제된다" 그대로 재현하지 않으려면 이 한 줄이 필요).

### 결론

status: resolved. 세 회사 selector 하드닝 완료 + 실제 재수집으로 대상분기·회귀분기 양방향
검증(byte-for-byte 기존 데이터와 일치) + freshness 게이트 RED=0 유지 확인. 잔여 항목은 위 정적검사
훅 배선 한 줄뿐이며 데이터/코드 정합성과는 무관.
