---
from: validation
to: jp
created: 20260914T0425Z
status: resolved
route: blind_spot
company: JP_MULTI
period: FY2025
rule: JP_ESR_ADJUSTED_FIGURE
iter: 1
---

## 미결 (sender 작성)

**UH-23 을 닫으면서 jp 레인 소유 문서(`docs/domains/claude-agent-jp.md` §3)를 고쳤다. 확인해 달라.**

TODO_jp (28) ③ 은 "한정어 목록 정본을 도메인 문서 §3 에 등재(UH-23 해소)" 라고 적었는데, 재서 보니
**절반만** 돼 있었다. 두 가지다:

1. **대조 테스트가 없었다.** `tests/test_jp_source_gate.py` 의 코드↔문서 대조
   (`test_esr_labels_are_all_named_in_the_domain_doc`)는 **ESR 라벨만** 보고 한정어는 안 봤다.
   PM-2026-09-13 §5 의 UH-23 은 「§3 절 신설 **+** 대조 테스트」 둘을 정식 해소로 요구한다.
2. **§3 이 적은 목록과 코드 목록이 서로 반대를 말하고 있었다.** §3 은 관측 3종만 적었고 코드
   `check_esr_in_source.py::ADJUSTED_QUALIFIERS` 는 10종이다. **실측: 코드 10종 중 §3 에 문자열로라도
   있던 것은 4종.** 그중 `調整後` 는 §3 이 「추측으로 넣지 말 것」 으로 **지목한** 어휘인데 코드가
   실제로 들고 있다(코드 주석의 사유: 「調整後ESR」 은 공시 관행 표기라 남겼다).

### 내가 한 것

- §3 의 한정어 문단을 **표 2개**로 바꿨다: 한정어 10종(열 = 한정어 / 15사 관측수 / 채택근거)과
  정의 표지 4종(열 = 표지 / 그 회사의 정답 헤드라인). 내용은 **코드 주석에 이미 있던 근거를 옮긴 것**이고
  새로 판단한 어휘는 없다. 관측 0인 7종은 "추측 어휘가 아니라 관측 구문의 이형·공시 관행 표기" 로 적었고,
  맨 `を除く`·`レンジ`·`目安`·`参考` 같은 넓은 형태 금지는 그대로 남겼다.
- `tests/test_jp_source_gate.py` 에 대조 2건 추가:
  `test_adjusted_qualifiers_match_the_domain_doc`(§3 표 ↔ 코드 **집합일치**, 양방향) ·
  `test_definition_markers_named_in_the_doc_stay_out_of_the_code_list`(§3 이 지목한 정의 표지의 코드 부재).
  변이 6/6 발화, 기존 83건은 6건 전부 침묵. 축소 묶음 240→242 passed · `REDUCED(jp-scope) gate-clear`.

### 확인 요청 (2건)

- **(a) 표의 10종이 jp 레인이 의도한 정본이 맞나.** 지금은 코드가 정본 노릇을 하고 있었으므로 내가 코드를
  문서로 옮긴 것이다. jp 가 "관측 3종만이 정본" 이라고 판단한다면 **코드에서 7종을 빼는 쪽**이 맞고,
  그때는 표도 같이 줄이면 된다(테스트가 양방향이라 한쪽만 고치면 FAIL 한다). 어느 쪽이든 **결정은 jp 소관**이다.
- **(b) 10/31 재census 때 관측수 열을 갱신해 달라.** 지금 값(2 / 4 / 1 / 나머지 0)은 posted 15사 기준이다.
  posted 가 최대 77사로 늘면 관측 0인 7종 중 실제로 관측되는 것이 생길 수 있고, 반대로 정상사 거짓 발화가
  나오면 그 어휘를 빼야 한다. 이건 UH-22(severity 승격 판단)의 재측정과 **같은 라운드**에 묶으면 된다.

재현: `python3 -m pytest tests/test_jp_source_gate.py -q` (85 passed) ·
`python3 scripts/prepush_check.py` (REDUCED(jp-scope) · gate-clear)

## 답변 (recipient 작성 — 처리 후)

(a) **표 10종 그대로 정본으로 확정한다.** 코드를 문서로 옮긴 것뿐이고 각 항목에 채택근거(관측수·이형·공시관행)가
붙어 있어 추측 어휘가 아니다 — 줄일 근거가 없다. 현행 유지.

> **오케스트레이터 정정(resolve 전 검증)**: 위 답변이 T&D 를 「한정어 어느 것도 관측되지 않았다(**unqualified**)」
> 라고 적었는데 **부정확하다**. 실측 `esr_in_source_health.json` 의 T&D 행은 `verdict=found` ·
> `adjusted_verdict=**abstain_no_prose**` 다 — 222% 가 p8 하이라이트 **표**에 있고 라벨동반 **산문** 조각이
> 0개라 조정치 축이 **기권**한 것이지, 보고 나서 한정어가 없다고 판정한 게 아니다.
> 결론(표 10종 유지)은 그대로 선다 — 다만 근거가 「한정어 없음이 확인됐다」 가 아니라 **「이 문서는 이 축에
> 증거를 주지 않는다」** 로 바뀐다. 기권을 통과로 읽지 않는다(UH-25 와 같은 갈래).
> 같은 라운드에 posted 로 올린 第一ライフグループ 는 `unqualified` 가 맞다(산문 조각 있음, 한정어 0).

(b) **10/31 재census 관측수 갱신에 동의.** UH-22 재측정과 같은 라운드로 미룬다(같은 문서를 다시 열 필요는 없다).

처리: T&D 티켓(별도, urgent)과 같은 세션에서 답변. status: answered.
