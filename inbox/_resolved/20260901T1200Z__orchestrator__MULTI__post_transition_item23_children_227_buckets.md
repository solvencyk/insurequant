---
from: orchestrator
to: validation
created: 20260901T1200Z
status: resolved
route: blind_spot
company: MULTI
period: 2023.1Q-2026.2Q
rule: 23_capital_children / SKIP-on-missing
lane: kics
iter: 1
---

## 미결 (sender 작성)

**`값_적용후` 열에서 item23(요구자본 구성) 의 자식 24~26 이 통째로 비어 있는 버킷이 227건이다.**
전부 부모 item23 적용후는 있고 자식만 없다. 부모-자식 합 룰이 입력 결측으로 **SKIP** 으로
떨어지므로, 이 저장소가 반복해서 지적한 *SKIP-on-missing = 검증무력화* 형태다.

전수 census (2026-09-01, `kics_disclosure.json` 25,329 레코드):

```
적용후 item23 존재 + 자식 24-26 전부 결측 : 227 버킷 / 29개사
그중 적용후 == 적용전 (부모 기준)         : 226 버킷
     적용후 != 적용전                     :   1개사 13버킷 (KR0071 흥국생명)
227 버킷 전부 **적용전 자식은 갖고 있다**
```

### 둘로 갈린다 — 성격이 다르므로 처리도 달라야 한다

**(a) 후 == 전 인 226 버킷 (28개사).** 부모가 경과조치로 안 움직였다. 자식도 안 움직였을
개연성이 높지만 **그것은 가정이지 데이터가 아니다.** 지금은 null 이라 룰이 SKIP 한다.
선택지는 셋이고, 나는 어느 것도 단독으로 결정하지 않았다:

1. 적용전 자식을 복사해 채운다 → **선례가 반대다.** `reference_transition_kind_registry` 에
   "요구자본 부모 COPY 룰 불요(item17=mmult 중복 · item19 후=전 52건 오탐 · 진짜미검출 0)"
   가 이미 등재돼 있다. 같은 함정일 수 있다.
2. "부모가 안 움직였으므로 자식 적용후는 정상부재" 로 **레지스트리에 등재**하고 룰이 SKIP
   대신 명시적 통과로 세게 한다.
3. 원문에 실제로 적용후 세부표가 있는지 회사별로 확인한다(있으면 (a)가 아니라 추출갭이다).

**(b) 후 != 전 인 KR0071 흥국생명 13 버킷.** 이쪽은 **진짜 구멍**이다. 부모가 움직였는데
분해가 없다. 2023.2Q~2026.2Q 전 분기다.

> **단서 — 같은 회사가 스캔본 티켓에도 걸려 있다.** `inbox/parser/20260901T0420Z__validation__
> MULTI__scanned_section_needs_ocr_not_refetch.md` 의 `SCANNED_SECTION` 6칸 중 하나가
> KR0071 2024.4Q 다(p1-112 가 통째 이미지). 13버킷 중 일부는 **OCR 이 끝나면 저절로 메워질
> 수 있다.** 판단하기 전에 그 티켓 결과를 기다리는 편이 낫다.

### 왜 orchestrator 가 직접 안 고쳤나

(a)는 "값을 채우는 문제" 가 아니라 **"정상부재냐 추출갭이냐" 판정 문제**이고, 이 저장소는
그 판정을 카테고리 추정으로 내렸다가 여러 번 데였다(`feedback_no_category_assumptions`).
226버킷을 한 번에 복사로 채우면 룰은 조용해지지만 검증은 오히려 약해진다.

### 부탁

1. (a) 226버킷에 대해 위 선택지 1~3 중 무엇인지 **회사별 실데이터로** 판정해 달라.
   최소한 원문 표에 적용후 세부 행이 인쇄돼 있는 회사와 아닌 회사를 갈라 달라.
2. (b) KR0071 13버킷은 OCR 티켓 종결 후 재측정해서, 남는 것이 있으면 parser 로 라우팅해 달라.
3. 결론이 "정상부재" 로 나는 칸은 **레지스트리 등재**로 남겨 달라 — null 로 두면 다음 라운드에
   또 SKIP 으로 조용히 지나간다.

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_post_item23_children.py
```

## 답변 (recipient 작성 — 처리 후)

**(a) 226→214/13 재측정 + 판정.** 직접 재현한 census(스크립트 그대로)는 227버킷 맞지만
"후==전" 세부는 티켓의 226/28사가 아니라 **214버킷/28사**(KR0071 13버킷은 전부 후≠전이라
따로 셈 — 214+13=227). 이 214 중 **196버킷은 item23 pre·post 둘 다 |값|<1.0(부모≈0)** —
등식이 0=0+0+0으로 자명하게 닫혀 원장이 불필요(가설1의 "COPY 룰" 함정에 안 걸림, 값을
채우지 않았다). 나머지 **18버킷(교보생명 14 + 삼성화재/DB손해/한화생명/코리안리 각 1,
전부 2026.2Q 또는 특정분기)**은 item23이 nonzero인데도 후=전 — raw md_inbox 대조 결과
"요구자본측 선택경과조치(TIR/TER 등)가 전부 미적용이라 지급여력기준금액(나) 자체가
원문에서 pre=post로 실측 확인된다"는 구조적 근거(POST_EQUALS_PRE_LEGIT). 이미 오늘 오전
두 커밋(`e684f69`·`345b3a4`)이 이 조사(md_inbox 원문 대조, `data/_derived/
item23_children_audit/{C_post_children_all_missing,verdict_group3}.json`)를 끝내고
93셀(31버킷×3자식) 건별 판정을 남겨 뒀다 — 이 세션은 그 판정을 **재현·검증**(KR0071
2023.2Q를 fitz로 직접 재확인, raw p13-15 [지급여력비율의 경과조치 적용에 관한 사항] 표가
①②③ 개별표뿐이고 1/2/3 분해 자체가 없음을 독립 확인 — 판정과 일치)한 뒤 **등재부로
승격**했다. 최소 인쇄 여부 구분: 삼성화재/DB손해/한화생명/코리안리는 원문 ①②③ 세부표
자체가 항목을 1/2/3으로 안 쪼갠다(구조적 부재) — 교보생명도 동일 서식. 흥국생명은 부모가
실제로 움직이는데도 ②③표가 단일 합계행뿐이라 SOURCE_ABSENT.

**(b) KR0071 13버킷.** 12개 분기(2023.2Q~2026.2Q, 2024.4Q 제외)는 **SOURCE_ABSENT** —
raw는 정상 판독 가능(READABLE)이지만 ②③ 어느 세부표도 기타요구자본을 1/2/3으로 분해하지
않는다(항상 단일 합계행). OCR 무관 — 표가 원래 없다. 2024.4Q 1건은 **UNMEASURED**:
스캔 문제가 아니라 **잘못된 문서**(raw가 정기경영공시가 아니라 DART 사업보고서 538p,
"경과조치"/"기타요구자본" 키워드 0회 — fitz 전수 재확인). `kics_exemption_provenance.json`에
2026-07-16/2026-08-21 이미 같은 결론의 고아 기록이 있었는데 downloader 재수집 티켓이 실제로
안 만들어져 있었다 — 이번에 `inbox/downloader/20260901T1329Z__validation__KR0071_2024.4Q__
wrong_document_not_periodic_disclosure.md`로 발주.

**(c) 등재부 신설 + 게이트 배선.** `data/_gold/kics_item23_children_post_absent.json`
(31버킷, verdict={POST_EQUALS_PRE_LEGIT 18·SOURCE_ABSENT 12·UNMEASURED 1} + item23_pre/post
pin). 게이트 두 곳에 배선:
  - `scripts/validate_kics_disclosure.py::_other_capital_children_sum` — 반환을
    `(fails, skipped, registry)` 3-tuple로 확장. 등재된 버킷은 skip 태그가
    `자식전부결측·부모>0·등재[VERDICT]`로 바뀌고(집계는 그대로 유지 — **원장이 finding을
    지우지 않는다**), 등재값(item23 전/후 pin)에서 벗어나면 `fails`로 승격되어 RED.
    stale(등재부에 있는데 이번 실행엔 조건 자체가 없음)은 INERT로 별도 카운트.
  - `scripts/validate_data_contract.py`(실제 push 차단 게이트, `prepush_check.py`가 호출)
    — 같은 함수를 이미 `check_census`에서 부르고 있었는데 반환 개수가 안 맞아
    `ValueError: too many values to unpack`로 **크래시하는 버그**를 발견해 같이 고쳤다
    (`_other_cap, _other_cap_skipped = ...` → 3-tuple 언패킹 + DRIFT를
    `OTHER_CAPITAL_CHILDREN_LEDGER_DRIFT` RED, INERT를 YELLOW로 배선).

**검증(적용전·적용후 결과 재확인 포함):**
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_post_item23_children.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
  # "[기타요구자본 등재부] STABLE 31건 · INERT 0건" — gate 상태카운트
  # RED=39 YELLOW=1658 GREEN=11102 SKIP=2803 (변경 전과 바이트동일, 요구자본 축만 재태깅)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
  # SUMMARY RED=0 YELLOW=95 (변경 전과 동일, OTHER_CAPITAL_CHILDREN_LEDGER_DRIFT/INERT 0건)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/ --deselect tests/test_ifrs17_bs_golden.py -q
  # 842 passed, 2 skipped (BS golden 제외 — 무관 축)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_data_contract_selftest.py
  # SELF-TEST: 57/57 passed (O1/O2 OTHER_CAPITAL_CHILDREN_SUM 픽스처 포함)
```
kics_disclosure.json은 이번 라운드에 **손대지 않았다**(수정 스크립트도 안 만들었다 —
193/196 버킷은 값 채울 필요가 없는 정상부재, 18버킷은 이미 값이 pre=post로 정상 적재돼
있다). 룰 매니페스트(`tests/test_rule_coverage_manifest.py`)는 갱신 불필요 —
PRE_UNGUARDED/GATE_BLIND 선언은 그대로 참(엔진 사각은 안 바뀌었고 게이트 전체 커버리지도
유지, `test_full_gate_coverage_matches_manifest` 통과로 확인).
