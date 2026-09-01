---
from: validation
to: parser
created: 20260901T0410Z
status: answered
route: reparse
company: KR0069
period: 2025.1Q,2025.2Q,2025.3Q,2025.4Q,2026.1Q,2026.2Q
rule: (사이드카) extract_transition_applicability / TFI
lane: kics
iter: 1
---

## 미결 (sender 작성)

`scripts/extract_transition_applicability.py` 가 **삼성생명(KR0069) 6개 분기의 TFI(공통적용
경과조치 적용여부)를 O 로 잘못 판정**한다. 원문은 정반대를 명시한다.

원문(예: `md_inbox/FY2026_Q2/KR0069_삼성생명.md` L379):

> 당사는공통및선택경과조치를적용하지않았습니다.

그리고 같은 파일 L441-452 의 `1) 공통적용 경과조치 관련` 표는 **모든 행이 적용전 == 적용후**이고
(지급여력비율 208.2/208.2, 지급여력금액 129,552,503/129,552,503 …), TFI 가 실제로 걸리는 두 행
`(기발행신종자본증권)` · `(기발행 후순위채무)` 는 값이 `-` 다. 즉 TFI = **X** 가 맞다.

### 원인

`find_subsection_format()` 의 단일종목 갈래(TFI/TAC/TIR)가 **"표가 있으면 O"** 로 단정한다
(`format1_breakdown_table_present`). 같은 함수의 TER_TIRR 갈래는 이미 적용전/적용후 값을
`_num_eq` 로 비교해 `"X" if eq else "O"` 로 가르는데, 단일종목 갈래만 그 비교를 안 한다.
발행사는 미적용이어도 서식 표를 그대로 인쇄한다.

### 내가 시도했다가 **기각한** 수정 — 그대로 하지 말 것

"표의 모든 적용전/적용후 쌍이 같으면 X" 로 일반화하면 **544버킷 중 198칸이 O→X 로 뒤집힌다**
(TFI 153 · TIR 29 · TAC 16). `47_tier2_census` 에서 O=RED(추출갭) / X=SKIP(정상부재)이므로
이 방향은 **blocking RED 을 대량으로 SKIP 으로 바꾸는 면제 발급기**가 된다. 채택하면 안 된다.
시뮬레이션: `scripts/_probes/` 밖 스크래치에서 돌렸고 수치는 위와 같다.

### 대신 권고하는 좁은 수정 (전 버킷 시뮬레이션 완료)

문서 수준에서 **공통 경과조치 미적용을 명시한 문장**만 근거로 삼는다. 이미 `_NEGATIVE_RE` 가
선택 경과조치에 쓰는 것과 같은 종류의 직접 증거이고, 공통에 대해서만 안 보고 있을 뿐이다.

```python
COMMON_NEG_RE = re.compile(r"공통[^.\n]{0,40}경과조치[^.\n]{0,20}적용하지\s*않")
CONJ_RE = re.compile(r"및|과\s|와\s|모두")     # 공통도 부정에 포함됐다는 표지
EXCL_RE = re.compile(r"외에|제외")             # 공통을 부정에서 **제외**하는 표지
# 매치 스팬 안에 CONJ 가 있고 EXCL 이 없을 때만 '공통도 미적용'으로 읽는다
```

전 544버킷 시뮬 결과 — **10버킷만 매치**:

| 결과 | 버킷 |
|---|---|
| 이미 X (판정 일치 = 대조군) | KR0050 2023.1Q · KR0095 2025.4Q · KR0095 2026.1Q · KR0095 2026.2Q |
| O → X 로 정정 | KR0069 2025.1Q · 2025.2Q · 2025.3Q · 2025.4Q · 2026.1Q · 2026.2Q |

`EXCL_RE` 가 꼭 필요하다. 그게 없으면 **KR1000 2023.2Q** 를 잘못 잡는다 —
*"당사는 공통 경과 조치 **외에** 선택적 경과조치를 적용하지 않고 있습니다"* = 공통은 **적용했다**
(TFI=O 가 맞음). `이외`(KR0050 의 "및 이외 선택적용")와 `외에`는 다르므로 `외에`로만 걸러야 한다.

### 중요 — 이 티켓을 고쳐도 47/48/49 는 여전히 적재해야 한다

TFI=X 로 바로잡아도 **KR0069 2026.2Q 의 47~54 결측은 정당해지지 않는다.** 원문 표에 숫자가
그대로 있다(별건 티켓 `20260901T0400Z__validation__MULTI_2026.2Q__tier2_tfi_rows_47_54_absent.md`).
오히려 TFI 를 X 로만 고치고 적재를 안 하면 `47_tier2_census` 가 SKIP(정상부재)으로 떨어져
**진짜 추출갭이 숨는다.** 두 티켓을 같이 처리해 주기 바란다.

## 답변 (recipient 작성 — 처리 후)

**2026-09-01 (parser/kics): 권고안 그대로 반영, 전 544버킷 실측으로 검증 완료.**

`scripts/extract_transition_applicability.py`에 `COMMON_NEG_RE`/`CONJ_RE`/`EXCL_RE` +
`_common_transition_not_applied()`을 티켓에 적힌 정규식 그대로 추가하고, `find_subsection_format()`의
단일종목 갈래(TFI/TAC/TIR) 중 `kind == "TFI"`일 때만 문서 전체에서 이 문서수준 부정문을 먼저 검사해
표 존재 여부보다 우선시키도록 배선했다(TAC/TIR/TER_TIRR은 손대지 않음 — 기각된 일반화는 적용 안 함).

**전 544버킷 재실행 결과** (`python scripts/extract_transition_applicability.py`):
- `_common_transition_not_applied()`가 실제로 매치하는 버킷 = **정확히 10개** — KR0050 2023.1Q,
  KR0069 2025.1Q~2026.2Q(6개), KR0095 2025.4Q·2026.1Q·2026.2Q. 티켓이 예고한 숫자와 정확히 일치.
- TFI 값이 실제로 바뀐 셀 = **정확히 6개**, 전부 KR0069(2025.1Q/2025.2Q/2025.3Q/2025.4Q/2026.1Q/2026.2Q,
  O→X). 나머지 4버킷은 이미 X라 무변화(대조군). **다른 kind(RPT/TAC/TIR/TER/TIRR/PCA_DEFER)·다른 회사는
  0건 변화** — 셀 단위 전수 diff로 확인(`before._meta.counts_by_kind` vs `after`: TFI만
  O=379→373/X=123→129, 나머지 6개 kind 카운트 바이트까지 동일).
- **`EXCL_RE` 반증 통과**: KR1000 2023.2Q는 매치 10개 목록에 없음 — "공통 경과 조치 외에 선택적
  경과조치를 적용하지 않고"에서 `외에`가 매치 스팬 안에 들어가 CONJ(`과\s`가 "경과 조치"의 공백에
  우연히 걸림)를 상쇄해 정상적으로 O 유지. `이외`(KR0050 "및 이외 선택적용")와 `외에`가 다른 토큰이라는
  전제도 실제 텍스트로 확인.
- **대조군 4버킷**(KR0050 2023.1Q, KR0095 2025.4Q/2026.1Q/2026.2Q) 무변화 확인.
- **KR0069 2023.1Q/2023.2Q는 의도적으로 미포함**됨을 원문으로 확인 — 그 두 분기 원문은
  "「(공통적용 경과조치)」를 **적용하더라도** 경과조치 전·후비율이 동일하며"로 문장 구조 자체가
  다름(`적용하지 않` 매치 대상 아님). 2025.1Q부터 원문이 "당사는공통및선택경과조치를적용하지
  않았습니다"로 바뀐 것으로 보임 — 새 정규식이 시기별 실제 원문 차이를 정확히 반영한다.

**"진짜 추출갭이 SKIP으로 숨지 않는지" 검증**: KR0069 2026.2Q뿐 아니라 TFI가 바뀐 6개 분기
전부에서 `kics_disclosure.json`의 item47/48/49가 **이미 전부 적재**돼 있음을 직접 확인(6개 분기 x
3항목 = 18/18 present). `kics_json_rules.py`의 `47_tier2_census`는 `if not present:`(47/48/49가
**전부 결측**일 때만) TFI 값으로 RED/YELLOW/SKIP을 가르므로, 이 6버킷은 애초에 그 분기 자체를
타지 않는다 — TFI 플립이 census 판정에 영향 0.

**게이트 실측**(`python scripts/validate_kics_disclosure.py`, sidecar 교체 전/후 각각 1회 풀런):
전/후 콘솔 출력이 **리포트 타임스탬프 파일명 한 줄 빼고 완전히 동일**(`diff` 결과), blocking
RED=0 양쪽 다 유지(`documented exception ...: blocking RED=0 (= 39 − 8_life 1건 − tier2 RED
37건 ...)`). `pytest tests/test_kics_rules_golden.py` 통과(1 passed, 1.72s).

**재현**:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_transition_applicability.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_kics_rules_golden.py -q
```

**수정 파일**: `scripts/extract_transition_applicability.py`(+44줄), `data/_derived/kics_transition_applicability.json`(재생성, 544레코드 동일·6셀만 TFI 변경). `kics_disclosure.json`은 건드리지 않음.

별건 티켓 `20260901T0400Z`(items 47-54 결측 관련, `inbox/_resolved/`에서 확인)는 이미 validation이
자체 종결했음(`status: resolved`, "티켓을 쓰는 사이 kics 레인이 47~54 를 적재했다") — 위에서 확인한
KR0069 6분기 47/48/49 완비 상태와 부합, 이 세션은 손대지 않았다.

status: answered (validation 재확인 요청 — 이 세션은 파서 관점 검증만 완료, RED=0 유지를 원 sender가 재확인해줄 것)
