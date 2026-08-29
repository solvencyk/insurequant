---
from: orchestrator
to: parser
created: 20260829T2200Z
status: answered
route: blind_spot
company: MULTI
period: MULTI
lane: ifrs17
iter: 1
---

## 미결 (orchestrator 작성 — 조사 전용, 마스터 수정 금지)

**공용 `_row_nums()` 가 빈칸을 압축하기 때문에, 위치(고정 오프셋)로 읽는 모든 핸들러가
같은 방식으로 조용히 밀릴 수 있다. 어디가 노출돼 있는지 전수로 세라.**

### 방금 실제로 터진 사례

흥국화재(KR0005) 2026.2Q — 커밋 `fb9c9bf`. DART 원문에서 "보험서비스비용" 총계 행의
자동차보험·비PAA·3개월 칸 하나가 **리터럴 `"0"` 이 아니라 빈 문자열**로 렌더됐다
(같은 행 나머지 15칸과 이웃 세 다리 총계 행은 전부 정상). `_row_nums()` 가 그 빈칸을
건너뛰면서 **그 뒤 모든 고정 인덱스가 한 칸씩 밀렸고**, item13 이 −620,653(직전 분기 대비
55배)으로 튀어 `assemble()` 의 Tier-2 RC 게이트가 item2~14 를 통째로 null 처리했다.

**이게 왜 위험한가.**

- 라벨 매칭은 네 표 전부 성공한다 — 라벨 변형 탐지법으로 못 잡는다.
- 표가 하나뿐이라 중복표 오염 탐지법으로도 못 잡는다.
- **값이 55배 튀어서 우연히 잡혔다.** 밀림이 작은 칸에서 일어나 값이 그럴듯하면
  **아무것도 안 잡는다.** 폐쇄식은 밀린 값들로도 닫힐 수 있다.
- 게이트의 반응이 "통째 null" 이라 **오류가 결측으로 위장**됐다. 최신 분기가 검증 사각이던
  덕에 두 겹으로 숨었다.

### 조사할 것

1. **`_row_nums()`(및 같은 계열 헬퍼)가 빈칸을 어떻게 다루는지 코드로 확정해라.**
   압축인지, `None` 을 채우는지, 핸들러마다 다른지.
2. **위치 기반으로 읽는 핸들러를 전수로 열거해라.** `scripts/pl_breakdown/` 전체와 다른
   추출 경로에서 고정 오프셋·슬라이스로 칸을 집는 곳을 찾아라. 라벨로 집는 곳은 안전하다.
3. **각 노출 지점에서 실제로 밀림이 일어난 적이 있는지 실측해라.** 원문에서 해당 표의
   칸 수를 세어 기대 칸 수와 다른 (회사,분기)를 census 하면 된다. **이게 이 티켓의 핵심 산출이다.**
4. **탐지 방법을 제안해라.** 지금은 값이 크게 튈 때만 우연히 잡힌다. 후보:
   - 파싱 시점에 행의 칸 수를 기대값과 대조하고 불일치면 실패시키기(값 검증이 아니라 구조 검증)
   - `_row_nums()` 가 빈칸을 건너뛰지 말고 `None` 을 채우게 바꾸기(파급 범위를 먼저 재라)
   - Tier-2 RC 게이트가 "통째 null" 대신 **왜 죽었는지 남기게** 하기 — 지금은 오류가
     결측으로 위장돼 원인 추적이 불가능하다
5. **결론을 내라.** 노출 지점이 흥국화재 하나뿐이면 그것도 결과다. 여러 곳이면 우선순위를 매겨라.

### 하지 말 것

- **마스터를 고치지 마라. 조사 전용이다.** 밀림이 발견되면 목록만 만들어라 — 수정은 별도 발주.
- **`_row_nums()` 를 이 티켓에서 고치지 마라.** 파급 범위가 크다. 제안까지만.
- `index.html`·`IFRS17.html`·`public_exports/` 금지. `scripts/validate_*`·`prepush_check.py` 금지.
- `data/disclosure/`·`kics_disclosure.json` 금지 — kics 레인이 작업 중이다.
- 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.

## 답변 (recipient 작성 — 처리 후)

**요약: 위치기반 노출 지점은 30개+ 함수(코드로 확정). 실제 밀림(회사×분기×행)은 census로
9,664건 잡혔으나 대부분 노이즈이고, "값이 실제로 틀어질 수 있는" 밀림은 손보 5곳
(KR0005 2건·KR1000·KR0032·생보 3사 공용 헬퍼)뿐이며, 그중 확정 오염(실제로 화면 숫자가
틀렸던 사례)은 2건 — 흥국화재(KR0005) 2026.2Q(오늘 fb9c9bf로 수정 완료)와 악사손해
(KR0049, 이 티켓 이전에 이미 전용 핸들러로 수정됨) — 둘 다 이미 닫혀 있다. 나머지는
"같은 매커니즘이 같은 회사의 형제 함수에 아직 안 고쳐진 채 남아있고, 실제 빈칸이 그
함수를 스쳐 지나갔지만 읽는 위치를 비켜갔다"는 근접-미스(near-miss) 3~4건이다. 마스터·
`_row_nums()` 둘 다 손대지 않았다(조사 전용 준수). 재현 스크립트·원시 로그는 세션
스크래치패드에 남겨뒀다(경로는 §3 끝).**

### 1. `_row_nums()` 계열의 빈칸 처리 방식

`scripts/pl_breakdown/common.py::_row_nums(r)`(L20-27):
```python
def _row_nums(r):
    out = []
    for c in r:
        v = to_num(c)
        if v is not None:
            out.append(v)
    return out
```
**행 전체(라벨 칸 포함)를 훑어 `to_num()`이 성공하는 칸만 원래 순서로 남기고 실패한
칸(라벨 텍스트·빈 문자열·`"-"/"–"/"—"`류 대시·비정상 텍스트 전부)은 위치 정보 없이
그냥 버린다 — `None` 을 채우는 압축이 아니라 완전 삭제(list comprehension 압축)다.**
`to_num()`(`scripts/build_net_income_breakdown.py` L38-55)은 `""`와 `"-"/"–"/"—"`를
동일하게 `None`으로 처리하므로, **`_row_nums()` 입장에서 "진짜 빈 문자열"과 "정상적인
대시 표기(값 없음/0)"는 구분되지 않는다.** 흥국화재 사고를 일으킨 건 전자(원래 "0"이어야
할 칸이 빈 문자열로 렌더)지만, 위험한 칸은 후자(대시)도 똑같이 만든다 — 대시가 훨씬
흔하므로 노출 표면은 더 넓다.

**동일 계열이지만 별도 사본:**
- `scripts/pl_breakdown/tier1.py`·`tier2.py`·`companies.py`는 전부
  `from .common import _row_nums`로 **같은 함수 객체를 자기 모듈 전역에 바인딩**한다 —
  파이썬 free-variable 조회가 호출 시점에 함수의 `__globals__`(정의된 모듈의 전역
  딕셔너리)를 보므로, 이 세 파일 안의 모든 함수(중첩 클로저 포함)는 `common._row_nums`를
  간접적으로 참조하는 게 아니라 **자기 모듈에 복사된 이름**을 참조한다(census 스크립트가
  4개 모듈 각각의 바인딩을 따로 몽키패치해야 했던 이유).
- `scripts/build_net_income_breakdown.py`(L176-181)는 **자체 정의**(`extract_tier2_lob`이
  쓰는 `_row_with`/`_comp_sum`/`_exact_total`)를 갖고 있다 — `common.py`를 import하지
  않는 완전히 독립된 사본, 로직은 동일(`[to_num(c) for c in r if to_num(c) is not None]`).
  **단, `build_pl_breakdown.py`의 import 목록(L38-54)에 `extract_tier2_lob`이 없다 —
  이 사본은 현재 파이프라인에서 도달 불가능한 죽은 코드다**(census 몽키패치를 걸고
  383개 회사-분기를 전부 돌렸는데 단 한 번도 호출되지 않음, §3 확인).
- `scripts/pl_breakdown/companies.py`의 `_life_comprehensive_core`(L2888-2987, 신한라이프/
  농협생명/흥국생명/케이디비생명/푸본현대생명 — `extract_tier2_life_comprehensive` 5개사
  공용)와 `_life_product_split`은 `_row_nums()`를 안 쓰고 **자기 안에서 같은 필터링을
  인라인으로 재구현**한다(`[v for v in (to_num(c) for c in r) if v is not None]`) — 이름은
  다르지만 압축 동작은 동일. 다만 `_life_comprehensive_core`는 이 리스트를 위치로 읽지
  않고 `max(..., key=abs)`/첫 숫자 스캔만 쓰므로(§2 참고) 압축이 일어나도 값이 안 틀린다.

### 2. 위치 기반(고정 오프셋)으로 읽는 핸들러 전수

`_row_nums(` 호출부는 `companies.py` 67곳·`tier2.py` 10곳·`tier1.py` 4곳·
`build_net_income_breakdown.py` 4곳(죽은 코드) = 85곳. 전부 손으로 읽고 "결과 리스트를
고정 인덱스/슬라이스로 소비하는가"로 갈랐다. **안전(라벨재매칭·truthy 체크·길이 체크만·
순서무관 `max`/첫 값 스캔만 쓰는 곳)은 제외.** 아래는 **인덱스로 읽는(=노출된)** 함수만
집계 — 30개+ (동일 회사 내 유사 클로저는 한 줄로 묶음):

**손보(SONBO_HANDLERS, 11사 중 9사 노출)**
| 회사 | 함수 | 위치 | 패턴 |
|---|---|---|---|
| KB(KR0010) | `_kb_note.jang_total/jang_rev`, `extract_tier2_kb.{_pick,jang}`, `extract_tier2_kb_quarterly.cum0` | companies.py:39-186 | `n[-1]`·`n[0]`·**`n[len(n)//2]`**(2분할, 가장 위험) |
| 현대(KR0009) | `_hyundai_section.mag`, `_hyundai_old_components`, `_hyundai_old_split`, `extract_tier2_hyundai.{jang,_ytd_triple}` | companies.py:219-454 | `n[0]`·`n[1]`·`n[1::2][:3]`·`n[2]` |
| 한화(KR0002, NEW) | `extract_tier2_hanwha.rnum` | companies.py:588-593 | `n[JC]`(JC/GEN/AUTO = 행 길이로 산출한 고정 offset) |
| DB(KR0011) | `extract_tier2_db.{d1,rownums,at}` | companies.py:862-914 | `ns[off]`·`at(rsr, off+lob*st)` |
| 삼성화재(KR0008) | `extract_tier2_sonbo_component.{d,at}` | companies.py:1003-1053 | 위와 동일 패턴(gold-validated 핸들러도 예외 아님) |
| 흥국화재(KR0005) | `extract_tier2_heungkuk.{totrow,cum,comp}` | companies.py:1084-1151 | `totrow`는 **오늘 fb9c9bf로 위치보존 재파싱으로 수정됨**(행 선택 게이트만 `_row_nums` 잔존, 무해). `cum`/`comp`는 미수정, `ns[1+2p]` 등 |
|  | `extract_tier2_heungkuk_old.{totrow,rv}` | companies.py:1217-1236 | `ns[idx]` |
|  | **`extract_tier2_heungkuk_single.{totrow,jang,paa_lob,jang_tot}`** | companies.py:1350-1436 | **미수정** — `heungkuk.totrow`의 형제 함수인데 패치가 안 갔다. `ns[0]`·`ns[-1]`·`ns[-2]`·`ns[-3]` |
| 코리안리(KR1000) | `_coreanre_old.val`, `extract_tier2_coreanre.{cum,comp}` | companies.py:1484-1609 | `ns[idx]`, idx 최대 5까지 |
|  | `_old_rv/_old_total/_old_present/_old_lobcum`(구형식 공용, 삼성·DB 등) | companies.py:1700-1762 | `ns[idx]` — 단, `_old_present`의 `len(ns)>=full` 선택 게이트가 압축된 행을 애초에 `best`로 못 뽑게 막는 구조 |
| NH(KR0032) | `_nh_gmm_incurred4`(item6) | companies.py:1948-1978 | `ns[:5]` unpack, `len(ns)<5` 가드는 있음(§3) |
| 롯데(KR0003) | `_extract_tier2_lotte_combined.{g,tot,net}`, `_lotte_row_val`, `_lotte_from_sections.{grand,at}` | companies.py:2231-2413 | 전 회사 통틀어 가장 여러 형태(3가지 레이아웃 변형 전부 노출) |

**손보 공용(tier2.py, 전용 핸들러 없는 회사가 떨어지는 fallback)**
| 함수 | 위치 | 패턴 |
|---|---|---|
| `_val_at`(Format-A, `extract_tier2_sonbo`) | tier2.py:51-60 | `nums[pos]`, pos∈{0,1,2} — **악사손해가 실제로 이걸로 사고났던 이력**(§3) |
| `extract_tier2_sonbo_structured.col0`(Format-B, 메리츠 등) | tier2.py:200-280 | `nums[st-1]`·`nums[3*st-1]`·`nums[-1]-nums[st-1]-out[13]` |

**생보(LIFE_HANDLERS, 15사 중 6사 노출)**
| 회사 | 함수 | 위치 | 패턴 |
|---|---|---|---|
| 교보/DB생명/동양(KR0073/82/87) | `_life_first_num` | companies.py:2665-2680 | `nums[col]`, col∈{0,1} — 당기 칸이 빈칸이고 전기만 살아있으면 전기값이 당기로 오채택될 수 있는 정확한 조건이 실데이터에 존재(§3, 단 지금까지 타깃 행 자체에는 미적중) |
| 미래에셋(KR0079, Family B) | `_life_product_split.block_sum` | companies.py:2990-3049 | `nums[-1]` |
| tier1.py 전체(`_pick_line/_pick_priority/_pick_op_line/_other_op_revenue`) | tier1.py:115-389 | `nums[0]`·`nums[col]` — **2026-06-05부로 deprecated, FS-API 우선이라 현재 fallback으로만 도달**(파일 자체 docstring L198) |

**안전(같은 `_row_nums` 패턴이지만 인덱싱을 안 하거나 raw 인덱싱으로 우회 — 대조군)**
- `extract_tier2_hanwha_old`(한화 구형식): 자체 주석(companies.py L670) *"Index RAW cells
  (NOT `_row_nums`, which drops '-' and shifts columns)"* — `cell()`/`tot()`가
  `to_num(r[col])`로 원본 행을 직접 인덱싱. **이 버그 계열을 이미 알고 우회 설계된
  코드**.
- `_nh_gmm_re_incurred`(NH item11): 자체 주석(companies.py L1989-1991) *"Cells are read
  via to_num() directly on r[1:6] (NOT via _row_nums...)"* — 형제 함수 `_nh_gmm_incurred4`
  (item6, 위 표 참고)는 **아직 이 우회를 안 받았다** — 같은 5칸 구조, 같은 회사, 같은
  "손실요소외 칸이 매 분기 '-'"라는 형제 함수 docstring의 관찰이 그대로 적용될 가능성이
  높은데 item6만 미수정 상태.
- `extract_tier2_axa`(악사손해): raw 인덱싱(`to_num(_norm(c)) for c in r[1:]` + 헤더맵)
  으로 재작성됐고, 자체 docstring(companies.py L2521-2522)이 **"generic Format-A fallback
  collapsed '-' cells via _row_nums and mis-assigned the columns"**라고 못박아
  이 티켓 이전에 이미 실제 사고가 있었음을 증언한다.
- `_life_comprehensive_core`(신한라이프 등 5사): `max(nums, key=abs)` 또는 첫 숫자 스캔만
  사용 — 순서 무관이라 압축이 일어나도 안전.
- `src/ifrs17/{csm,bs_snapshot,measurement,reinsurance,insurance_pl,sensitivity}_extractor.py`:
  grep으로 `to_num`/`_row_nums`류 패턴 전무 확인 — **완전히 다른(라벨/스코어링 기반)
  아키텍처**라 이 버그 계열 자체가 성립하지 않는 것으로 보인다. 단, companies.py만큼
  줄 단위로 정독하지는 않았다 — "노출 없음"이 아니라 "이 계열의 흔적 없음" 수준의
  확인이다.

### 3. 실제 밀림 census — 재현 가능한 실측

**방법**: `_row_nums`를 4개 모듈(common/tier1/tier2/companies) + `build_net_income_
breakdown`(별도 사본) 전부에서 몽키패치해, 실제 호출마다 (행 길이, 드롭된 칸이 빈
문자열인지/대시인지/라벨텍스트인지, 호출 함수명·줄번호, 회사·분기)를 로깅했다.
`discover_filings()` + `parse_filing()`과 동일한 디스패치 순서를 그대로 복제해 **디스크에
있는 회사-분기 전부(FY2022_Q4~FY2026_Q2, 39개사, 426개 filing 디렉터리)를 읽기 전용으로
돌렸다** — 마스터 JSON은 한 번도 안 씀, `main()`도 호출 안 함.

- 처리: 383건 성공(43건은 테이블 자체가 안 뽑힘, 에러 0건).
- **`_row_nums()`가 칸을 1개 이상 버린 호출**: 9,664건(대부분 후보 테이블 탐색 중 스쳐
  지나간 무관한 행 — 예: 라벨만 맞고 실제로는 다른 note인 5~9칸짜리 표, 또는 truthy
  체크에서 버려지는 완전-공백 행).
- **"조밀한 행(살아남은 값 ≥6개) + 작은 구멍(1~3칸 결손)"** — 그럴듯한 값으로 위장할 수
  있는 흥국화재 패턴과 구조적으로 같은 신호 — 로 필터링하면 **434건, 13개 콜사이트**로
  압축된다.
- 이 13곳을 각각 원본 셀 내용(`row_repr`)까지 열어서 실제 소비 함수(`totrow`/`d1`/`val`/
  `pmin` 등)가 그 구멍을 실제로 읽는 위치인지 손으로 추적했다. 결과:

  | 회사 | 콜사이트 | 판정 |
  |---|---|---|
  | KR0005 흥국화재 | `companies.totrow:1090`(=`extract_tier2_heungkuk`) | **확정 오염, 2026.2Q, 이미 수정됨**(fb9c9bf) |
  | KR0005 흥국화재 | `companies.totrow:1356`(=`extract_tier2_heungkuk_single`) | **근접-미스**: 2026.1Q 실측 원문에 `['보험수익','660,961','','0','660,961','0','39,692','33,824','73,516']`처럼 중간 칸(pos2 등)이 실제로 빈칸인 행이 있다. 이 함수의 모든 소비자(`jang()`의 `ns[0]`, `paa_lob()`/`jang_tot()`의 `ns[-1]/-2/-3`)가 끝점만 읽어서 **이번엔 안 틀렸지만, 다음 분기에 pos1(첫 데이터 칸)이나 마지막 3칸(일반/자동차/합계) 자체가 비면 그대로 흥국화재 2026.2Q와 같은 사고가 재현된다.** 미수정. |
  | KR1000 코리안리 | `companies.val:1489`(=`_coreanre_old`) | **근접-미스**: 2023.3Q/2024.2Q/2024.3Q 분기형 표에서 대시가 항상 raw 위치 5-6에 뜨는데, `COL["일반"]=5`가 정확히 그 위치. 실측 사례는 전부 idx=1(장기)/idx=3(생명)로 읽는 구성요소 행(CSM/RA/청구 등)이라 item14(일반)엔 아직 안 튀었지만, "총보험수익/총보험비용" 합계 행 자체가 같은 패턴을 보이면 item14가 조용히 틀어진다. 미수정. |
  | KR0001·KR0008·KR0011 | `_old_present:1728`/`_old_total:1719`(구형식 공용) | **안전**: 매 분기 동일한 대시 위치(예: KR0001 `dashes_at=[1,2]` 6분기 내내 동일) — 구조적으로 없는 LOB. `_old_present`의 `len(ns)>=full` 선택 게이트가 압축된 행을 애초에 `best`로 뽑지 않게 막는다. |
  | KR0003 롯데 | `_extract_tier2_lotte_combined_bycontent:2424` | **오탐(false positive)**: `if not _row_nums(r)` truthy 체크일 뿐, 값을 안 읽는다. |
  | KR0003 롯데 | `_extract_tier2_lotte_combined:2231` | **안전**: 대시가 raw pos5-6에 고정, 소비자는 index0-2만 읽음 |
  | KR0010 KB | `jang_rev:57` | **안전**(대시는 pos4, 소비자는 `n[0]`; 게다가 item1 fallback의 정렬 키일 뿐 최종 값 아님) |
  | KR0011 DB | `<lambda>:838/840/854`(`pmin`후보 정렬) | **안전**: 매우 지저분한(칸 최대 44개 결손) 후보 표들이지만 셋 다 진짜 마지막 칸은 항상 살아있어 `[-1]`이 안전. **실제 값 추출 라인(`d1`/`rownums`, L868·L901)을 별도로 추적**해 KR0011 전체에서 값 오염 0건 확인(§3 하단 재확인). |

- **소규모(각 1~2 콜사이트) 추가 확인**: 한화(KR0002, `rnum:592`) — 비PAA 장기 단일
  구조(6칸 연속 빈칸)가 5개 분기 전부 동일 패턴, 압축 후 정확히 의도된 8원소로 재구성됨
  (구조적, 정상). ABL(KR0070) — 전부-대시 행은 `if not nums: return None`으로 안전하게
  막힘. 교보(KR0073)/DB생명(KR0082) — 확인된 빈칸은 전부 타깃 라벨(CSM/RA)이 아닌 다른
  행. 미래에셋(KR0079) — 확인된 빈칸 전부 안전한 길이체크/`max(key=abs)` 라인. 처브
  (KR0100, tier1) — 관측된 빈칸은 각주 칸 자리라 압축이 오히려 의도대로 동작.

- **회사별 "밀림 이벤트 0건"(census가 아예 아무것도 못 잡은, 즉 지금 디스크에 있는
  모든 분기에서 표가 전부 조밀)**: 예별손해(KR0004)·NH(KR0032)·악사손해(KR0049)·
  삼성생명(KR0069)·`_life_comprehensive` 5개사(KR0071/72/83/94/104)·AIA(KR0080)·
  동양생명(KR0087)·하나생명(KR0097)·KB라이프(KR0099).

- **`build_net_income_breakdown.py`의 `extract_tier2_lob`(별도 `_row_nums` 사본)**: 383건
  전부에서 **단 한 번도 호출 안 됨** — 죽은 코드 재확인(§1).

**재현 (읽기 전용, 마스터/`_row_nums()` 무변경)**:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe <스크래치패드>/census_row_nums_blank.py
```
스크래치패드(`C:\Users\sangwook.cho\AppData\Local\Temp\claude\...\c5d6e48d-...\scratchpad\`):
`census_row_nums_blank.py`(harness) · `census_row_nums_blank_out.json`(원시 9,664건) ·
`census_full_run.log`(실행 로그, 146초) · `analyze_census.py`+`census_analysis_summary.txt`
(13곳 압축 분석) · `dump_specific.py`/`dump_db_lines.py`/`dump_small_counts.py`+그 출력
(위 표 근거가 된 원본 셀 덤프). 세션이 사라지면 이 파일들도 사라지므로, 재추적이
필요하면 harness를 재실행하면 된다(오프라인, 네트워크·마스터쓰기 없음, ~150초).

### 4. 탐지 방법 제안

1. **파싱 시점 구조 검증 (구조 검증 ≠ 값 검증) — 가장 저렴하고 일반적**: `_row_nums(r)`을
   호출하는 대신(또는 나란히) `len(r) - 1`(라벨 칸 제외 원본 칸 수)과
   `len(_row_nums(r))`을 비교해, **차이가 나면서 그 행이 실제로 반환/소비될 예정인
   지점**에서 경고를 남기는 얇은 래퍼를 만드는 방법. 이번 census 하네스가 사실상 그
   프로토타입이다 — `common.py`에 `_row_nums_checked(r, expected_len, context)`류
   함수를 만들어 위치기반 소비자(§2 표)들이 점진적으로 갈아타게 하면, "몇 칸이 사라졌는지"
   가 **파싱 시점에 로그로 남는다**(지금처럼 값이 그럴듯해서 통과한 뒤에야 발견되는 게
   아니라).
2. **`_row_nums()`를 빈칸-스킵 대신 `None`-채움으로 바꾸는 안**: 파급 범위가 이번 census로
   드러났다 — 85개 호출부 중 최소 15곳 이상이 **"진짜로 순서 무관"**(truthy 체크,
   길이만 체크, `max(key=abs)`, 명시적 `len(ns)>=full` 게이트)이라 `None`이 섞이면
   오히려 그 안전장치들이 깨진다(`if not nums`가 `[None]*8`엔 여전히 truthy). **드롭인
   교체 불가 — 최소 별도 함수(`_row_nums_positional`)를 새로 만들어 §2의 "노출" 표
   함수들만 이관해야 한다.** 순서만 바꾸는 리팩터는 이번 티켓 범위 밖(발주 지시대로
   손 안 댐).
3. **Tier-2 RC 게이트가 "통째 null" 대신 사유를 남기게 하기**: `build_pl_breakdown.py::
   assemble()`의 RC 게이트가 왜 item2-14를 눌렀는지(item13이 이상치였다는 사실 자체)를
   지금은 버린다. `coverage.json`에 `"tier2": "suppressed"` 상태 옆에
   `"suppressed_reason": {"item": 13, "value": -620653.0, "vs_prior_quarter": -11182.0,
   "ratio": 55.5}`류 필드 하나만 추가해도, 이번처럼 owner가 라이브 화면에서 결측을 보고
   역추적할 필요 없이 **coverage.json만 보고 원인을 알 수 있다.** 이번 사고가 "최신
   분기가 검증 사각이었던 덕에 두 겹으로 숨었다"고 스스로 지적했듯, 이 필드는 검증
   사각과 무관하게 항상 동작하는 1차 방어선이 된다.
4. **인접 분기 대비 이상치 자동 스윕(보조)**: 이미 검증팀이 하는 방식과 유사하지만,
   census 하네스처럼 회사·항목별로 직전 분기 대비 배율을 계산해 "5배 이상 튀는데
   item2-14가 동시에 null이 아닌" 케이스(=RC게이트를 통과해버린 이상치)까지 잡는 별도
   스윕. §3의 "근접-미스" 항목들(코리안리 item14, 흥국화재 `_single`)은 지금은 값이
   안 틀렸으니 이 스윕으로도 안 잡히지만, 다음 분기에 실제로 틀어지면 이게 2차 방어선이
   된다.

### 5. 결론

- **코드로 확정된 위치기반(고정 오프셋) 노출 지점: 30개+ 함수/클로저**, 손보
  11사 중 9사(예별·NH 제외 전부) + 손보 공용 fallback 2종 + 생보 15사 중 6사
  + tier1.py 전체(단, deprecated fallback) + 죽은 코드 1개 사본.
- **실측(384개 처리된 회사-분기 전수 census)으로 "그럴듯한 값으로 위장할 수 있는" 밀림이
  실제로 관측된 지점: 5곳**(KR0005 2개 함수·KR1000·KR0032의 item6 형제·생보 3사
  `_life_first_num`) — 전부 §3에 근거와 함께 나열.
- **그중 실제로 화면 숫자가 틀렸던(확정 오염) 사례: 정확히 2건**, 흥국화재(KR0005)
  2026.2Q(오늘 커밋 fb9c9bf로 수정 완료)와 악사손해(KR0049, 이 티켓 이전에 이미 전용
  핸들러로 수정 완료). **흥국화재 하나만의 문제가 아니다** — 같은 매커니즘이 최소 한 번
  더(악사손해) 실제로 사고를 냈었고, 지금은 흥국화재의 형제 함수(`_single`)와 코리안리
  한 곳에 **거의 같은 조건의 빈 총이 장전돼 있다**(다음 분기 렌더링이 한 칸만 옆으로
  가면 발사).
- 후속 조치는 발주 범위 밖이라 안 함: (a) `extract_tier2_heungkuk_single`을
  `_nh_gmm_re_incurred`/`extract_tier2_axa`처럼 raw 인덱싱으로 재작성, (b) 코리안리
  `_coreanre_old.val`의 "총보험수익/총보험비용" 총계 행 읽기를 raw 인덱싱으로,
  (c) `_nh_gmm_incurred4`(item6)에 형제 함수의 우회를 그대로 적용 — 이 세 가지가
  가장 비용 대비 효과가 큰 후속 후보다.
