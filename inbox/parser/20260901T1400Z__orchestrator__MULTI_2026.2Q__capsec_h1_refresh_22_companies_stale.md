---
from: orchestrator
to: parser
created: 20260901T1400Z
status: open
route: reparse
company: MULTI
period: 2026.2Q
rule: (사이드카) capital_securities / numerator_as_of
lane: kics
iter: 1
---

## 미결 (sender 작성)

K-ICS 화면 자본성증권 패널에 **"발행잔액 기준일 2025-12-31" 이 22개사에서 아직 뜬다**
(owner 지적, 롯데손해 사례). 오늘 2개사를 고쳤고 나머지를 넘긴다.

### 오늘 고친 것 (참고 — 같은 함정이 남아 있다)

`scripts/build_capital_securities_fy2026h1.py` 는 후순위 잔액을 차입금 주석의 열그룹 표에서
읽는데, **템플릿 가정 네 개가 하드코딩**돼 있어 39사 중 KR0011 하나만 잡히고 있었다.
"이 표를 가진 회사가 하나뿐" 이 아니라 **정규식이 하나만 봤다**:

| # | 가정 | 실제 |
|---|---|---|
| 1 | `colspan` 소문자 + **폭 3 고정** | KR0003 은 `COLSPAN="10"` (폭 = 그 회사 후순위 차수 개수) |
| 2 | 금액 행 라벨 = `사채, 명목금액` | KR0003 은 `액면금액` · `장부금액` |
| 3 | 회차 키 = `제N회` | KR0003 은 `제 8차` |
| 4 | FY2025 짝짓기 = 회차 문자열 | FY2025 이름이 `08차 …` 처럼 `제` 없이 시작하는 사모 건이 있어 10건 중 4건이 짝을 잃었다 |

4번이 특히 조용했다. 짝을 잃으면 `call_date` 가 상속되지 않고 `발행일+5년` 으로 유도돼
**인정금액이 155억 움직였다**(실측). 합계만 보면 정상처럼 보인다.

또 하나 — **금액 라벨을 우선순위로 고르면 안 된다.** KR0011 은 명목(액면), KR0003 은
장부금액이 기존 기준이라, 라벨을 임의로 고르면 롯데의 806,732(장부) 이 810,000(액면) 으로
조용히 바뀐다. 그래서 **전기말 합계가 FY2025 기준선을 재현하는 행**을 골라 기준을 확정하도록
배선했다(`sub_basis_unreconciled` 로 실패를 보고한다).

신종자본증권 쪽은 `confirm_hybrids_still_outstanding()` 을 신설했다. 개별 주석
(`자본으로 인정되는 채무증권의 발행`)은 24개 제출사 중 9곳에만 있지만, 표준 절
`[채무증권의 발행 등과 관련된 사항] 가. 채무증권 발행실적` 은 **24곳 전부에 있고 기준일이
2026-06-30** 이다. 기존 채권이 (발행일, 발행금액) 으로 그 표에 미상환으로 그대로 있으면
**값은 한 칸도 안 바꾸고 시점만** 갱신한다. 전량 확인된 경우에만 적용한다(부분 확인은
`hybrid_confirm_partial` 로 보고, KR0001·KR0082 가 해당).

결과: 롯데 2025-12-31 → **2026-06-30**, 소진율 31.6% 불변(상각분 +0.7억만 이동).

### 남은 22개사

```
KR0001 KR0002 KR0005 KR0009 KR0010 KR0032 KR0049 KR0050 KR0068 KR0070 KR0071
KR0072 KR0073 KR0076 KR0079 KR0082 KR0083 KR0087 KR0094 KR0097 KR1000 KR1011
```

- **정당한 6사**: KR0049 KR0050 KR0076 KR0097 KR1011 (+KR0004) — 반기/분기보고서를 아예
  제출하지 않는다. FY2026 사업보고서 전까지 2025-12-31 이 정본이다. 갱신 대상이 아니다.
- **KR0073 교보 · KR0083 푸본현대**: 신종 쪽은 오늘 2026-06-30 으로 확인됐는데 후순위가
  낡아서, company as_of = min 규칙에 걸려 화면은 여전히 2025-12-31 이다. 후순위만 뚫으면 된다.
- **나머지**: 차입금 주석 열그룹 표가 또 다른 변형이거나 없다. `extract_subordinated_current`
  가 `<TH ...>후순위사채</TH>` 열그룹을 못 찾는 회사가 대부분이다.

### 부탁

1. 회사별로 후순위 잔액 표가 **어떤 형태인지** 먼저 열거해 달라(변형을 하나씩 때려잡지 말고
   축을 먼저 재는 것 — 이 저장소가 반복해서 데인 형태다).
2. 기준(액면/장부) 확정은 반드시 **전기말 대조**로 할 것. 대조가 안 되면 갱신하지 말고
   `sub_basis_unreconciled` 로 남길 것. 개념 절단이 숫자보다 위험하다.
3. `hybrid_confirm_partial` 2건(KR0001 3채권 · KR0082 1채권)은 왜 발행실적 표에 안 나오는지
   확인해 달라(사모라 창 밖일 가능성).

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_capital_securities_fy2026h1.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/wire_capital_securities_to_utilization.py --quarter 2026.2Q --bonds-source data/bonds/capital_securities_fy2026h1.json
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/sync_tier_utilization_to_deploy.py --apply
```

> `wire_capital_securities_to_utilization.py` 의 기본값이 `--quarter 2026.1Q` ·
> `--bonds-source …fy2025.json` 이다. 인자 없이 돌리면 **1분기 산출을 덮어쓴다**(내가 한 번
> 밟았다). 기본값을 최신 분기로 올리거나 인자를 필수로 만드는 편이 낫다.

## 답변 (recipient 작성 — 처리 후)
