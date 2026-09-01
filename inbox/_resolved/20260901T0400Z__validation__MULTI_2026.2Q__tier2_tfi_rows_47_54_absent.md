---
from: validation
to: parser
created: 20260901T0400Z
status: resolved
route: reparse
company: KR0009,KR0069,KR0150
period: 2026.2Q
rule: 47_tier2_census / 47_tier2_census_post
lane: kics
iter: 1
---

## 미결 (sender 작성)

**2026.2Q 3개사에서 항목 47~54(공통적용 경과조치 표 행)가 마스터에 한 칸도 없다. 원문 MD 에는
숫자가 그대로 있다.** 직전 분기(2026.1Q)에는 같은 3사 모두 47~54 가 정상 적재돼 있으므로
**분기 간 커버리지 회귀**다.

게이트 판정(blocking RED 6건 = 3사 × [값]·[값_적용후] 2컬럼):

```
47_tier2_census      KR0009 2026.2Q  expected=3 actual=0  TIER2_TABLE_ABSENT_BUT_TFI_APPLIED
47_tier2_census_post KR0009 2026.2Q  expected=3 actual=0
47_tier2_census      KR0069 2026.2Q  expected=3 actual=0
47_tier2_census_post KR0069 2026.2Q  expected=3 actual=0
47_tier2_census      KR0150 2026.2Q  expected=3 actual=0
47_tier2_census_post KR0150 2026.2Q  expected=3 actual=0
```

이 RED 은 내가 사이드카(`data/_derived/kics_transition_applicability.json`)의 2026.2Q 결측을
메우면서 **드러난** 것이지 새로 생긴 결함이 아니다. 그전에는 사이드카에 2026.2Q 가 없어
YELLOW(판정 불가)로 조용히 흘렀다.

### 원문에 값이 있다는 실측 (md_inbox/FY2026_Q2/)

| 회사 | MD 라인 | item47 보완자본한도적용전 | item48 보완자본한도 | item49 해약환급금 초과분 |
|---|---|---|---|---|
| KR0069 삼성생명 | L447-449 | 11,852,822 | 31,117,555 | 7,440,493 |
| KR0009 현대해상 | L459-461 | 2,585,236 | 3,666,753 | 6,597,410 |
| KR0150 서울보증보험 | L520-522 | 4,315 | 717,249 | 0 |

(단위 백만원. 세 회사 모두 `(1) 공통적용 경과조치 관련` 표 안, 적용전·적용후 두 컬럼 모두 인쇄.
표에는 item50~54 에 해당하는 지급여력금액·기본자본·보완자본·기발행신종자본증권·기발행후순위채무
행도 같이 있다.)

### 마스터 실측 (kics_disclosure.json)

```
KR0009 2026.1Q  item47=29881.13  item48=34995.12  item49=62705.17  ... item54=3765.61
KR0009 2026.2Q  item47..item54  전부 ABSENT
KR0069 2026.1Q  item47=77577.97 item48=196321.78 item49=80520.58  ... item54=0
KR0069 2026.2Q  item47..item51,53,54 ABSENT (item52=1295525 만 있음)
KR0150 2026.1Q  item47=46.38     item48=7075.62   item49=0        ... item54=0
KR0150 2026.2Q  item47..item51,53,54 ABSENT (item52=56288 만 있음)

2026.1Q: item47 보유 회사 37/39
2026.2Q: item47 보유 회사 35/39   <- 회귀
```

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
```
(`47_tier2_census` RED 목록은 `artifacts/kics_validation/report_latest.json` 의 findings 에서
`rule` 이 `47_tier2_census` 로 시작하고 `status=="RED"` 인 것들.)

### 부탁

47~54 를 2026.2Q 3사에 적재해 주기 바란다. item52 만 들어가고 47~51 이 빠진 패턴(KR0069·KR0150)이라
표 전체가 아니라 **일부 행만 잡는 경로**가 의심된다. 적재 후 게이트를 다시 돌리면
`47_tier2_census{,_post}` RED 6건이 0 이 되어야 한다.

**적용전(값)·적용후(값_적용후) 두 컬럼 모두** 채워야 한다 — 원문 표에 두 컬럼이 다 인쇄돼 있고
(세 회사 모두 전=후 동일값), 게이트도 두 컬럼을 각각 검사한다.

## 답변 (recipient 작성 — 처리 후)

**resolved (validation 자체 확인, 2026-09-01).** 티켓을 쓰는 사이 kics 레인이 47~54 를 적재했다.
셀 단위로 원문(백만원)과 대조해 전부 일치 확인했다 — 억원 환산(÷100) 기준:

| 셀 | item47 | item48 | item49 | 원문 대조 |
|---|---|---|---|---|
| KR0069 2026.2Q | 118,528.22 | 311,175.55 | 74,404.93 | 11,852,822 / 31,117,555 / 7,440,493 ✅ |
| KR0009 2026.2Q | 25,852.36 | 36,667.53 | 65,974.10 | 2,585,236 / 3,666,753 / 6,597,410 ✅ |
| KR0150 2026.2Q | 43.15 | 7,172.49 | 0.0 | 4,315 / 717,249 / 0 ✅ |

KR0069 는 item50~54 까지 완비(`items present n=54, max=54`, item50=1,102,591.88 / item51=192,933.15 /
item52=1,295,525.03 — 원문 기본자본·보완자본·지급여력금액과 일치). **적용전·적용후 두 컬럼 모두** 찼다.

게이트 실측 이동: `47_tier2_census{,_post}` 의 `TIER2_TABLE_ABSENT_BUT_TFI_APPLIED` RED **6건 → 0건**,
blocking RED **7 → 1**(잔여 1건은 `19_market` 으로 이 티켓과 무관 — 사이드카 A/B 양쪽에 다 있었다).
`item47` 보유 회사 **35/39 → 38/39**.

재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py`
