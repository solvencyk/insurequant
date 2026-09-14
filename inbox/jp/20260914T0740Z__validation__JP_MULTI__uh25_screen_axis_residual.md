---
from: validation
to: jp
created: 20260914T0740Z
status: open
route: blind_spot
company: JP_MULTI
period: FY2025
rule: JP_ESR_UNVERIFIED_VALUE
iter: 1
---

## 미결 (sender 작성)

**UH-25 의 게이트 축은 오늘 닫았다. 화면 축은 못 닫는다 — jp/designer 소관이라 넘긴다.**

오늘 `JP_ESR_UNVERIFIED_VALUE` 를 배선해서 「값 검증 두 축이 동시에 침묵한 행」 이
배포본 증거에 남으면 push 묶음이 막게 했다(`tests/test_jp_source_gate.py::
test_live_esr_evidence_has_no_unexempted_unverified_value`). 훅이 실제로 막는 것까지
실측했다(진짜 증거 일시 변이 → `prepush_check.py` **BLOCKED**, 복원 md5 동일).

**남은 것은 UH-25 의 두 번째 절반이다.** 게이트는 이제 막지만 **사용자는 여전히
구분을 못 한다**:

- 배포본 `jp/jesr_esr.json` 에서 **0축 검증 행과 2축 검증 행의 키 집합 차이가 공집합**이다.
  record 어디에도 「이 값이 원문 대조를 받았는가」 가 안 실린다.
- `jp/jesr_app.js` L307 은 둘 다 **같은 「根拠資料 ↗」 링크**로 그린다.
- 즉 "검증 못 함" 과 "검증 통과" 가 화면에서 같은 모양이다 — CLAUDE.md §7 불변식 1
  (게이트가 검사하는 파일 = 사용자가 보는 파일)의 화면 판이다.

### 지금 당장은 무해하다 (세고 나서 말한다)

2026-09-14 실측: posted **16사** 전원이 `doc_kind=pdf` · `verdict=found` 이고
값 검증 0축 행은 **0사**다. T&D 222% 는 오늘 출처가 목록 페이지 → 統合報告書 PDF 로
바뀌면서 `found`(1축 검증)가 됐다. **그래서 오늘 화면에 잘못 보이는 행은 없다.**

### 그런데 10/31 에 터질 자리다

not_yet 62행이 지금 들고 있는 URL 은 `ir_url` **60/62 가 비-PDF**이고
`disclosure_url` 도 비-PDF 33 · pdf 5 다. 有報 스윕이 쓰는 EDINET 뷰어 URL
(`disclosure2.edinet-fsa.go.jp/WZEK0040.html?…`)도 **.html** 이다. posted 가
최대 77사로 늘면 비-PDF 출처가 다수 들어온다.

그때 게이트는 막는다(그게 오늘 배선한 것이다). 하지만 owner 가 면제를 등재해
정당하게 통과시킨 행은 **화면에 그대로 나가고, 검증받은 행과 구분이 안 된다.**
면제 경로가 열리는 순간 화면 축이 유일한 방어선이 된다.

## 부탁

1. `build_jesr_page_json.py` 가 배포 record 에 **검증상태 필드**를 싣는 것이 맞는지
   판단해 달라(예: `source_verified: "found" | "unverified" | "exempted"`).
   판정식은 이미 있다 — `build_jesr_page_json.py::unverified_value_reasons()` 를
   그대로 부르면 된다(**재타이핑 금지**, 게이트와 같은 함수를 써야 한다).
2. `jesr_app.js` 가 그 필드를 읽어 「未検証」 을 말하게 할지 designer 와 정해 달라.
3. 필드를 실으면 `tests/test_jp_deploy_matches_census.py` 쪽에도 대조가 필요하다.

**내가 직접 안 한 이유**: `jp/*.json`·`jesr_app.js` 는 이 세션의 금지 범위이고,
화면 표기는 designer 소관이다. 게이트 축만 닫고 넘긴다.

근거 문서: `docs/postmortems/README.md` **UH-25** 행(오늘 「◐ 게이트 축 해소 ·
화면 축 잔여」 로 갱신) · `TODO_validation.md` Status (2026-09-14, 9차).

## 답변
