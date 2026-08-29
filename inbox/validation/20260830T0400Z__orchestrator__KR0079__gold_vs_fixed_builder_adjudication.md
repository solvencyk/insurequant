---
from: orchestrator
to: validation
created: 20260830T0400Z
status: open
route: verify
company: KR0079
period: MULTI
rule: CSM_GOLD_VS_FIXED_BUILDER
lane: ifrs17
iter: 1
---

## 미결

parser 가 `20260830T0200Z` 로 KR0079 CSM 결함 2개를 고쳤다(commit `28ab7f8`). 그 결과
**gold override 와 빌더 산출의 관계가 뒤집힌 자리가 생겼다.** 값 채택 판단은 validation 몫이라
넘긴다. **parser 는 gold 를 한 글자도 안 건드렸다.**

### 1) 배분 불일치 2건 — 어느 쪽을 채택할지

`KR0079 2025.2Q 항목4(조정) / 항목5(CSM상각)`:

| | 항목4 | 항목5 | 합계 |
|---|---:|---:|---:|
| 현재 gold(화면에 나가는 값) | **-886.27** | **-791.3** | -1677.57 |
| 고친 빌더 산출 = raw 직접 재구성 | **-685.5** | **-992.1** | -1677.6 |

**200.77억이 두 항목 사이에서 반대 방향으로 어긋나고 합계는 같다.** 그래서 폐쇄식
(항목6=Σ항목1~5)은 어느 쪽을 써도 닫힌다 — **산수로는 판별 불가**다.

판단에 쓸 재료:
- `20260825T2200Z` 답변: raw(rcept 20250814003532) WIDE 상품별 표에서 항목5 행
  `보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진` 5상품 합 = **-992.07억**
  (=-99,207,397,518원). 그 티켓이 "PL쪽 992.07 은 소수 6자리 파생값이라 원천 미확정"이라
  적었는데, **파생값이 아니라 CSM표 원문 직접값이었다.**
- 같은 회사 **2025.3Q·2026.1Q 는 같은 방법으로 raw = gold 완전 일치**. 2025.2Q 만 이례적.
- 그 200.77 은 `20260825T1520Z` 등재부의 `WATERFALL_SUSPECT 잔차 200.77억(25.4%)` 과 같은 크기.
- gold 셀의 `why` 는 이번에 채웠는데(`8781725`), 이 2건은 **"원천 특정했으나 gold 와 불일치"**
  로 기재돼 있다. 즉 출처가 gold 를 지지하지 않는다.

**요청**: 어느 쪽을 채택할지 판정하고, gold 쪽을 버린다면 그 2건을 제거할지
`why` 에 근거를 남긴 채 둘지까지 지정할 것. **화면 숫자가 바뀌는 건이다.**

### 2) gold 제거 후보 19건 — 이제 코드가 같은 값을 낸다

parser 가 확인: 아래는 고친 빌더가 **gold 와 오차 0** 으로 재현한다. override 가
불필요해졌다는 뜻이지만, 지우면 다음 회귀 때 방어막이 사라진다 — **남길지 지울지는 판단 사항.**

- 2025.2Q 항목1·2·3·6 (4건)
- 2025.3Q 항목1~6 (6건)
- 2025.4Q 항목1~6 (6건)
- 2026.1Q 항목1·4·5 (3건)

불변 6건(2023.1Q 항목1~6)은 표 자체가 스코어러 미달로 안 잡혀 **gold 가 계속 필요**하다.

## 참고 — 오케스트레이터가 직접 검증한 것 (재확인 불필요, 반증은 환영)

- `CSM_waterfall.json` 2172행→2172행, 추가·삭제 0, **변경 41셀 전부 KR0079**
  (2023.2Q~2025.2Q). non-null 2172→2172.
- `validate_data_contract.py` **RED=0** (exit 0). `validate_master_tables.py --no-build`
  는 골든이 박제한 기존 SUMMARY·exit 그대로.
- `pytest tests/test_master_tables_golden.py tests/test_viz_csm_waterfall_golden.py
  tests/test_deploy_assets.py` → **12 passed**.
- **독립 교차확인**: `data/dart/viz/csm_waterfall.json`(별개 코드경로, SEPARATE-블록 파싱)의
  미래에셋 FY2024 값이 **opening 2,021,450 / closing 2,078,210 백만** — 즉 **20,214.5 / 20,782.1억**
  으로 **고친 마스터와 정확히 일치**하고 고치기 전 마스터(20,205.4 / 20,775.6)와는 불일치했다.
  패널이 처음부터 옳았고 루트 마스터만 틀렸던 것 — 수정 방향의 독립 증거다.

## 하지 말 것

- 브랜치 변경 금지(`fix/csm-product-segmented-columns`), `git push` 금지, `git add -A` 금지.
- `build_root_masters.py` main() 통짜 실행 금지. `build_csm_waterfall_master.py` 실행 금지.
- python 은 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` 풀패스,
  UTF-8(BOM 없음), 멀티라인 `python -c` 인라인 Bash 금지.

## 답변 (validation 작성 — 처리 후)

<판정 결과.>
