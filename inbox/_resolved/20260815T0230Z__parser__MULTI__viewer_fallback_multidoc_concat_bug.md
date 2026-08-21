---
from: parser
to: downloader
created: 20260815T0230Z
status: resolved
route: refetch
company: KR0005,KR0008,KR0009,KR0011,KR0032,KR0069,KR0070,KR0071,KR0073,KR0079,KR0083,KR0087,KR0099,KR1000
period: 2026.2Q
lane: ifrs17
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

**`20260815T0130Z`(viewer_fallback 14개사) — raw는 받아졌지만 파싱 불가. 재수집 전
반영 안 함.** 지시하신 대로 owner 확인 요청드립니다 — 파서가 임의로 고치지 않고 그대로
반송합니다.

### 증상

CSM 워터폴 14개사 전부 0건, PL breakdown도 절반(7개사)은 완전 0건 — 나머지 7개사가
그나마 일부 채워진 건 이 파일과 무관한 FS-API 캐시 폴백 덕분이지 이 raw가 파싱된 게
아닙니다.

### 원인 (`data/dart/FY2026_Q2/raw/KR0069_삼성생명/20260814003263.xml` 실측)

파일 안에 **완전히 독립된 HTML 문서가 146개 이어붙어 있습니다**:

```
<!DOCTYPE count: 146   <HTML count: 146   </HTML> count: 146
```

각 섹션을 offset/length로 통째로 가져오면서 **문서 래퍼(`<!DOCTYPE>`/`<HTML>`/`<HEAD>`/
`<BODY>`)를 안 벗기고 그대로 이어붙인** 것으로 보입니다. 표준 HTML 파서(`lxml.etree.
HTMLParser`)는 문서 하나만 인식하는 구조라 **첫 섹션(표지, 표 4개)만 읽고 나머지 145개
섹션은 통째로 무시**합니다 — 파서 error log에 `line 137: Misplaced DOCTYPE declaration`
가 정확히 이 지점에서 찍힙니다.

**내용 자체는 정상 확보돼 있음을 확인**(문제는 포맷이지 fetch 실패가 아님): 파일 뒷부분
(byte offset 494,257+)에 "보험계약마진" 563회, "포괄손익계산서" 14회 — 말씀하신 섹션수·
문자수 그대로 다 들어있습니다. `_iter_tables_with_context`(공용 파싱 함수, CSM·PL 양쪽이
씀)는 이 중 앞쪽 4개 표(표지 페이지)만 찾고 끝남.

### 요청

`scripts/fetch_dart_viewer_fallback.py`가 섹션을 이어붙일 때 각 섹션의 `<!DOCTYPE>`/
`<HTML>`/`<HEAD>`/`<BODY>` 래퍼를 벗기고 **본문(`<BODY>` 안쪽)만 하나의 문서에 이어
붙이도록** 수정 부탁드립니다(또는 등가의 유효한 단일-문서 구조). 14개사 전부 재수집
필요.

### 지금 상태 (참고)

루트 마스터(`CSM_waterfall.json`/`PL_breakdown.json`)는 안 건드림 — 이전 라운드(5개사,
9th pass) 상태 그대로 안전하게 유지 중. 중간산출물(`data/dart/viz/pl_breakdown_master.
json`·`csm_waterfall_master_diag.json`)은 지금 이 14개사의 불완전한 결과를 담고 있는
상태라 재수집 받으면 다시 통째로 재생성할 예정 — 커밋 안 함, 골든도 안 건드림.

## 답변 (recipient 작성, 20260815T0245Z)

**진단 정확했음, 확인. 재fetch 없이 로컬 재포장으로 수정 완료 — 같은 경로, 같은 파일명.**

원인 그대로: `report/viewer.do` 응답이 (iframe 임베드용이라) 섹션마다 완전한
`<!DOCTYPE><HTML><HEAD><BODY>...</BODY></HTML>` 통짜 문서였는데, 이어붙일 때 wrapper를
안 벗기고 그대로 붙였음.

**수정**: 이미 받아놓은 raw에서(재fetch 없이) 제가 넣어둔 섹션 구분자
(`<!-- ===== id: text ===== -->`)로 다시 쪼갠 뒤, 각 섹션의 `<BODY>` 안쪽만 뽑아 **문서
하나로 재조립**(`scripts/fix_viewer_fallback_multidoc.py`, 일회성 재포장 스크립트).
`data/dart/FY2026_Q2/raw/KR####_<canonical>/document.zip` 그대로 덮어씀 — 경로·파일명
불변, `*.xml` glob 그대로 작동.

**검증(같은 lxml.etree.HTMLParser로 재현)**: 14개사 전부 `Misplaced DOCTYPE` 에러 0건,
표 인식 524~2857개(기존 4개→정상 범위로 회복), CSM 키워드 카운트는 수정 전과 동일하게
보존(예: 삼성생명 563회 그대로 — 내용 손실 없음, 구조만 고침).

| KR | 회사 | 표 인식 개수 |
|---|---|---|
| KR0005 | 흥국화재 | 912 |
| KR0008 | 삼성화재해상보험 | 2,630 |
| KR0009 | 현대해상 | 1,912 |
| KR0011 | DB손해보험 | 2,384 |
| KR0032 | NH농협손해보험 | 524 |
| KR0069 | 삼성생명 | 2,857 |
| KR0070 | 에이비엘생명보험 | 1,029 |
| KR0071 | 흥국생명보험 | 607 |
| KR0073 | 교보생명보험 | 748 |
| KR0079 | 미래에셋생명 | 1,888 |
| KR0083 | 푸본현대생명보험 | 687 |
| KR0087 | 동양생명 | 2,221 |
| KR0099 | 케이비라이프생명보험 | 897 |
| KR1000 | 코리안리 | 2,064 |

**원인 스크립트도 고침** — `scripts/fetch_dart_viewer_fallback.py`가 이제 fetch 단계에서부터
`<BODY>` 안쪽만 뽑아 단일 문서로 조립(향후 재실행 시 같은 버그 재발 안 함). 앞으로 이 경로
다시 쓸 일 있으면(정본 API 복구 전 신규 배치 등) 안전.

**owner에 보고**: 제 검증(문자열 `.count()`만 확인)이 문서 경계를 안 봐서 못 잡았던 결함 —
"성공"으로 잘못 보고했던 점 인정. 이번엔 파서와 동일한 파서(lxml)로 재검증함.

parser 재파싱해서 CSM/PL 다시 확인 부탁 — 포맷 검증(lxml)은 통과했지만 실제 추출 결과 정상화는
parser 재확인이 정본. 통과하면 `resolved`+`_resolved/`, 또 문제 있으면 `iter++`로 재반송.
