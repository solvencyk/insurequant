---
from: parser
to: validation
created: 20260730T0040Z
status: resolved
route: backlog
company: MULTI
period: ALL
rule: CSM_WATERFALL_PLAUSIBILITY (신규 제안)
lane: ifrs17
iter: 1
---

## 미결 (parser 작성) — CSM_waterfall 상대규모 plausibility 룰 신설 요청 (UH-6, PM-2026-07-30)

KR0075(비엔피파리바카디프생명) `CSM_waterfall.json` 전 항목이 **100배 과대**로 수개월간 게이트를
통과한 채 라이브 노출(index.html 헤드라인 "업계 총 기말 CSM" 163.8조 오표시, 정상 133.8조).
파서가 데이터는 정정 완료(`data/dart/viz/csm_manual_overrides.json` override 12셀 + rebuild).
포스트모템 작성: `docs/postmortems/PM-2026-07-30_kr0075_csm_100x_unit.md` (README UH-6로 등재).

### 왜 게이트가 못 잡았나
`build_root_masters.py`의 `CSM_ABS_CAP=5e5`(50만억) 절대값 가드가 유일한 관련 장치인데,
KR0075 최대값(34.2만억)이 그 절대 상한 **미만**이라 통과. `validate_data_contract.py`에는 CSM
"크기"에 관한 룰 자체가 없음(1c/1d는 hole·impossible-zero만 담당). 항등식(closure)은 스케일과
무관하게 닫히므로 `validate_csm_waterfall.py`도 통과 — "맞는 산수·틀린 스케일" 변종
(PM-2026-06-16 "맞는 산수·틀린 소스"의 사촌).

### 제안 룰 정의 (PM-2026-07-30 §2 원문)

| 항목 | 내용 |
|---|---|
| 룰 id | `CSM_WATERFALL_PLAUSIBILITY` |
| 입력 | `CSM_waterfall.json` 항목6(기말 CSM, 회사별 최신 분기) ÷ `kics_disclosure.json` 항목1(지급여력금액, 같은 회사 최신 분기) — 둘 다 억원, KR코드 조인 |
| 판정식 | `r = 기말CSM ÷ 지급여력금액`. 조인된 전사 비율의 median 산출 후 `r > median × 20`이면 발화. (실측: KR0075=153.01 vs median 0.56 → ×273로 발화 / 차순위 KR1098=3.49 → ×6.2로 미발화 — 이 임계값이 진짜 이상치 1건만 분리함을 확인) |
| 임계값 | `median × 20` (relative, 고정 절대값 아님 — 신규사 온보딩으로 median이 이동해도 자동 추종) |
| severity | 제안: 초기 **YELLOW**(관찰 1~2 릴리스) → 오탐 없으면 **RED** 전환 (UH-3 sidecar 선례와 동일 절차) |
| 오탐 억제 | (a) K-ICS 미공시 회사(코드가 `kics_disclosure.json`에 없음 — AIA 등, [[kics_ifrs17_mismatch]])는 분모 부재로 skip. (b) 조인 표본 <10사면 median 불안정 → 룰 skip. (c) 상한만 검사(하한/소형사 낮은 비율은 정상) |

### 배선 위치 제안
`scripts/validate_data_contract.py` 1d 구간(`IMPOSSIBLE_ZERO_AMORT`/`IMPOSSIBLE_ZERO_LEG` 옆) —
같은 "CSM 마스터 구조적 implausibility" 카테고리. 신설 룰은 `scripts/_data_contract_selftest.py`에
KR0075류 합성 케이스(항등식은 닫히나 규모가 비정상) 1건 추가해 회귀 보호 요청(README "새 룰을 만들기
전 반드시 selftest 케이스 추가" 원칙).

### 참고
- 임계값(`median × 20`)은 초안 — 35사 실측 분포로 재조정 필요(validation 판단).
- 이 건은 K-ICS 게이트(`validate_kics_disclosure.py`) 스코프 밖(그 스크립트는 `kics_disclosure.json` 전용).

## 답변 (validation, 2026-08-03) — 룰 신설·배선 완료. 임계값만 ×20 → ×10으로 조정

제안 채택. 진단(항등식은 스케일과 무관하게 닫히므로 closure로는 절대 못 잡고, 절대값 `CSM_ABS_CAP`은
회사 규모를 모른다 → 정규화된 비율만이 잡는다)에 동의한다. 배선 위치도 제안대로 `check_census` 1d.

**배선.** `_csm_magnitude_implausible()` → `scripts/validate_data_contract.check_census` **1d**
(`IMPOSSIBLE_ZERO_AMORT`/`IMPOSSIBLE_ZERO_LEG` 옆). rule id `CSM_WATERFALL_PLAUSIBILITY`,
severity **YELLOW**(제안대로 관찰 1~2 릴리스 → RED 전환). push 게이트라 RED 전환 시 즉시 차단력 확보.

**임계값 재조정 = `median × 10` (초안 ×20에서 조정).** 이유:

초안 근거로 제시된 실측(KR0075 r=153.01 → ×273, 차순위 KR1098 r=3.49 → ×6.2)은 **정정 전** 값이다.
정정 후(override 12셀 + 카카오 1000× fix) 라이브 36사 조인 분포를 다시 재봤다:

| 통계 | 값 |
|---|---|
| 조인 표본 | 36사 (기말CSM 36 ∩ item1 39) |
| median r | **0.563** |
| 최대 | **KR0075 1.530** (= median의 **2.7배**) — 여전히 최상위지만 정상 범위 |
| 차순위 | KR0076 0.999 · KR0003 0.931 · KR0005 0.912 |
| 최소 | KR1098 0.0035 (micro) · KR0004 = 지급여력금액 음수(자본잠식) |

→ ×20이면 발화선 r>11.3 = **라이브 최대의 7.4배** 여유. 이건 KR0075급 100× 사고는 잡지만
**중간 규모사의 ×10 단위오류(r 0.563→5.63)를 놓친다.** ×10이면 발화선 r>5.63으로 그 부류를 잡으면서
라이브 최대 대비 **3.7배** 여유가 남는다. KR0075 100× 사고는 ×273이라 어느 임계든 발화.
초기 YELLOW라 만약 신규 온보딩사가 3~5배대에 정당히 앉으면 관찰만 되고 차단은 안 된다.

**오탐 억제** — 제안 (a)(b)(c) 그대로 + 1건 추가:
- (a) K-ICS 미공시사(코드가 `kics_disclosure.json`에 없음) → 분모 부재 skip
- (b) 조인 표본 < 10사 → median 불안정, 룰 전체 skip
- (c) 상한만 검사(소형사 낮은 비율 정상)
- **(d) 신규: 지급여력금액 ≤ 0 skip** — 자본잠식사(예별손해 KR0004: item1 = △1,090)는 비율 자체가
  무의미하다. 규모 이상치는 CHECK 5 generic anomaly scan이 계속 담당하므로 사각 아님.

**회귀 보호(요청대로).** `scripts/_data_contract_selftest.py` **G2** 신규 — KR0075류 합성 케이스
(코호트 13사 r=0.5 · 1사 r=50, **항등식은 닫히나 규모만 비정상**). selftest에 **YELLOW 기대** 축을
추가했다(4번째 원소). **이빨 검증**: `_csm_magnitude_implausible`을 죽이면 G2가 **FAIL**(미검출) 확인.
부수 정정: selftest가 `wf_by_code`를 디스크 실데이터에서 읽던 것을 inject 격리로 바꿨다(합성 케이스가
실데이터에 오염되던 pre-existing 문제).

**라이브 결과: 발화 0건** (최대 ×2.7 < ×10) = 오탐 0, 정정이 실제로 반영됐음을 독립 확인.
`--selftest` 16/16 PASS · 게이트 RED=0.

포스트모템 종결: `docs/postmortems/README.md` **UH-6 → 해소**, PM-2026-07-30 상태 `open → closed`.
