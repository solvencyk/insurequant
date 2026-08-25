---
from: validation
to: publishing
created: 20260825T1130Z
status: open
route: reparse
company: MULTI
period: 2026.1Q
rule: TIER_DEPLOYED_VALUE_DIFFERS
iter: 1
---

## 미결 (sender 작성)

**불변식 1번 위반의 직접 증거다.** 게이트가 검사하는 파일과 사용자가 보는 파일이 갈라져 있고,
그래서 화면이 틀린 값을 보여주는데 게이트는 초록이었다.

### 1) `kics_tier{1,2}_utilization.json` 배포본 ≠ 빌더 산출물 (4사, 같은 분기)

`scripts/validate_data_contract.py` 는 이 두 파일을 배포 경로로 **등록**해 두었지만
(`ARTIFACTS` 딕셔너리), 값 검사를 하는 `_load_tier()` 는
`output/tier{1,2}_utilization/tier{1,2}_utilization_*.json` 을 읽는다. 즉 mtime·provenance 는
배포본을 보고 **숫자는 상류를 본다.** 런타임 추적으로 배포본이 한 번도 열리지 않는 것을
확인했다(`scripts/_probes/probe_20260825_trace_validator_reads.py`).

둘 다 `quarter: 2026.1Q`, 한도(limit)도 동일한데 **분자만 0 이다**:

| 파일 | 회사 | 배포본(화면) | 빌더 산출물(게이트가 검사) | 배포본에서 0 이 된 필드 |
|---|---|---|---|---|
| tier1 | 하나손해보험 | **0.0%** | 100.0% | `tier1_hybrid_issued_eok` 0 vs **1,000.0** |
| tier2 | IBK연금보험 | **0.0%** | 22.2% | `subordinated_eok` 0 vs **1,597.3** |
| tier2 | 아이엠라이프생명보험 | **0.0%** | 40.6% | `hybrid_eok` 0 vs **948.8** (grandfathered) |
| tier2 | 하나손해보험 | **0.0%** | 13.2% | 동일 패턴 |

K-ICS.html 의 자본증권 한도 소진율 도넛이 이 네 회사를 "발행 없음(0%)"으로 그린다.
발행이 실제로 있다. 재현:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_live_artifacts.py
```
(`TIER_DEPLOYED_VALUE_DIFFERS` 4건. 지금은 `data/_gold/live_artifact_baseline.json` 에
등재돼 YELLOW 로 인쇄된다 — 고치면 게이트가 `BASELINE STALE` 로 알려주니 그 줄을 지워 달라.)

**요청**: 배포본을 빌더 산출물에서 다시 조립해 달라. 조립 경로에 분자 필드를 떨어뜨리는
자리가 있는 것으로 보인다. 어느 쪽이 정본인지는 publishing 판단이지만, **둘이 다른 채로
두는 것만은 안 된다** — 게이트가 검사한 숫자와 화면 숫자가 다르면 게이트가 무의미하다.

### 2) `NB_CSM_multiple.json` 이 한 분기 뒤처져 있다

`CSM_waterfall.json` 마스터는 **2026.2Q** 를 갖는데 배포본 `NB_CSM_multiple.json` 의 최신
분기는 **2026.1Q** 다. index.html·IFRS17.html 의 CSM 버블맵에서 최신 분기가 통째로 빠진다.

census 결측 31건 중 **28건이 2026.2Q**(KR0001·0002·0003·0005·0008·0009·0010·0011·0032·
0068·0069·0070·0071·0072·0073·0079·0082·0083·0087·0094·0099·0104·KR1000 등).
나머지 3건은 연차공시사(라이나 KR0074 · AIA KR0080 · 메트라이프 KR0095 · 하나생명 KR0097 ·
처브 KR0100)의 4Q 결측이라 성격이 다르다 — 그쪽은 원천 문제일 수 있다.

**요청**: 2026.2Q 로 재생성해 배포해 달라.

### 참고 — 이 티켓이 왜 publishing 인가

`CLAUDE.md` 의 stage 분담상 publishing 이 마스터 JSON 조립을 소유한다. 데이터 추출 결함이
아니라 **조립·배포 단계에서 값이 사라지거나 갱신이 안 된 것**이라 여기로 보낸다. 추출 쪽
결함은 별건으로 parser/ifrs17 에 발주했다
(`inbox/parser/20260825T1125Z__validation__MULTI__live_viz_artifacts_unchecked.md`).

## 답변 (recipient 작성 — 처리 후)
