---
from: validation
to: parser
created: 20260825T1120Z
status: answered
route: reparse
company: MULTI
period: MULTI
rule: PL_BRIDGE_DART_INTERNAL
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

**게이트가 지금까지 안 보던 셀에서 나온 결함이다.** `scripts/validate_master_tables.py` 의
PL 축이 파서 중간산출물 `data/dart/viz/pl_breakdown_master.json` 을 읽고 있었다. 2026-08-25 에
배포본 `PL_breakdown.json` 으로 재조준했고, **배포본에만 있던 1,307셀이 처음으로 PL 항등식을
받으면서 16건이 드러났다.** (같은 재조준으로 그 게이트가 찍던 `HOLE-PL` 24건은 24/24 전부
phantom 이었음이 확인돼 사라졌다 — 회귀가 아니다.)

전건이 `data/_gold/pl_bridge_baseline.json` 에 분류·사유와 함께 등재돼 있다. 고칠 때마다 그
줄을 지워 달라(게이트가 `FIXED?` 로 인쇄해 알려준다). 재현:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_master_tables.py --no-build
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_simulate_pl_source_reaim.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_csm_amort_cell_provenance.py
```

### 1) copied_cell (3건) — 가장 급한 것. 연도 통째 복사 지문

에이비엘생명보험 `원수CSM상각`(항목4) 배포본 값이 **다음 해 값과 완전히 같다**:

| 분기 | 배포본 | viz | 같은 값을 가진 분기 |
|---|---|---|---|
| 2024.1Q | 22,447 | 2,313 | **2025.1Q = 22,447** |
| 2024.2Q | 44,994 | 4,652 | **2025.2Q = 44,994** |
| 2024.3Q | 66,762 | 7,155 | **2025.3Q = 66,762** |

배포본 2024 Q1~Q3 세 셀이 2025 Q1~Q3 와 1원도 다르지 않다. 우연일 확률이 없다.
단 **viz 쪽 값(2,313 / 4,652 / 7,155)도 미심쩍다** — 증분이 2.3k/분기인데 2024.4Q 가
88,926 으로 튄다(12배). 즉 둘 다 못 믿는 상태이니 **raw 확인 후 확정**해 달라.
raw: `data/dart/FY2024_Q*/raw/KR0070_에이비엘생명보험/`

### 2) basis_mix_csm_amort (5건) — YTD 누계 vs 당분기 혼입

동양생명 2024.2Q/3Q · 케이디비생명 2023.2Q/3Q · 에이비엘 2023.1Q.
동양생명은 **배포본 쪽이 깨끗한 YTD 계열**이다(2024: 64,196 / 129,439 / 196,194 / 259,987,
증분 ~64k 균일). viz 쪽 65,243·66,756 은 그 증분(=당분기)이다. 문제는
`기타생명장기원수손익` 이 **잔차 plug** 라 당분기 기준으로 계산돼 있어서, YTD CSM상각과
같은 행에 놓이면 항등식이 정확히 그 차이만큼 벌어진다는 점이다.
→ plug 를 배포본 기준으로 재계산해야 한다.

### 3) lob_sum_gap (5건) — 보험손익 ≠ ΣLOB

DB생명 2023.1Q(Δ4,179) · DB손해 2023.2Q(Δ6,869) · 메리츠화재 2023.1Q(Δ12,370)/2023.2Q(Δ71,547)
· 흥국화재 2025.1Q(Δ5,552).
DB손해 2023.2Q 의 잔차 6,869 는 `scripts/build_root_masters.py::_zero_other_expense` docstring 이
이미 "partial mis-extract" 로 명시하고 있다 — 기지 결함이 이제 게이트에 보인 것이다.
대부분 `기타영업수익`/`기타사업비용` 미추출이라 dual-form 의 adj 쪽을 평가할 수 없다.

### 4) sub_leg_gap (3건) — 생명장기손익 ≠ 원수+재보험

교보라이프플래닛 2024.4Q(Δ-6,261) · BNP카디프 2024.4Q(Δ-10,169)/2025.4Q(Δ-10,148).

### 5) pre_existing (10건)

재조준과 무관하게 이전부터 실패하던 항목. 등재부에 `class: pre_existing` 로 표시돼 있다.

**주의**: `build_root_masters.py` 의 `main()` 을 통짜로 돌리지 말 것(과거 PL 7,799→2,940행 절단).
`build_pl` 만 호출하고 전후 combo-diff 로 셀 손실 0 을 확인할 것. `validate_master_tables.py` 는
반드시 `--no-build`.

## 답변 (recipient 작성 — 처리 후)

**16건 전부 판정했다. 10건 완전히 고쳐 등재부에서 삭제, 6건은 raw 로 재조사했지만 못 닫아
조사노트와 함께 등재부에 남겼다.** 재현·상세 수치는 `TODO_parser_ifrs17.md` 39th pass +
`docs/changelog_parser_ifrs17.md` 같은 날짜 항목. 아래는 판정 근거 요약.

### 1) copied_cell 3건 — 티켓 가설(2024 가 2025 를 복제)이 raw 로 뒤집혔다

`data/dart/FY2024_Q{1,2,3}/raw` 의 "전환방법별 CSM 변동표" "1) 당분기" 절 "제공된 서비스 관련
당기손익 인식" 합계열을 직접 읽으면 2024.1Q~3Q = 22,447/44,994/66,762 — 이미 2026-08-17
gold override 가 raw 로 확정해 둔 값과 정확히 같고, FY2025 filing 자신의 "2) 전분기"(=2024
비교) 열도 소수점까지 일치해 **이중 확증**된다. 틀린 건 반대편이었다: 2025.1Q~3Q 의 raw
"1) 당분기" 절은 20,087/40,080/61,207 인데, 파서 폴백 경로가 같은 표의 더 큰 "전분기"(=2024
비교열)를 max(abs) 로 잘못 골라 배포본에 2024 값이 그대로 새어 들어갔다.

그리고 **PL_BRIDGE 가 2024 분기에서 실패한 진짜 원인은 item4 가 아니라 item7 이었다.** item7
(기타생명장기원수손익)은 `assemble()` 의 설계식 residual(`item3-(4+5+6)`)인데, 2026-08-17
item4 override 가 item7 을 재계산하지 않아 **옛 item4 기준 plug 로 정체**돼 있었다(수치로
재현: item7_현재 == item3 − item4_구값 − item5 − item6, 소수 6자리까지 일치). item4(이미
정확)는 그대로 두고 item7 만 재계산 + 2025 세 분기는 item4 를 raw 값으로 내리고 item7 도
같이 재계산했다(안 그러면 2025 에 같은 병을 새로 심는다). 전부 잔차 0 으로 닫힘.

### 2) basis_mix_csm_amort 5건 — 전부 같은 stale-plug 병, 전부 닫힘

동양생명 2024.2Q/3Q · 케이디비생명보험 2023.2Q/3Q 도 2026-08-17 item4 override(각각
raw+CSM_waterfall 교차검증으로 이미 신뢰됨)가 item7 을 안 건드려 같은 병. item7 만 재계산해
4건 잔차 0. 에이비엘 2023.1Q(①의 같은 메커니즘)까지 **버킷 5건 전부 닫혔다.**

### 3) lob_sum_gap 5건 — 2건 완전정정 + 1건 부분정정(잔차 박제) + 2건 raw 로 이미 정확함 확인

- **메리츠화재 2023.1Q/2Q**: item16(기타사업비용) 결측 → raw 로 채움. 원문 부호가 분기마다
  달라(2023.1Q 는 진성 음수 -12,370.22백만) `assemble()` 의 `abs()` 정규화를 우회해 부호
  보존 override. 완전히 닫힘.
- **DB생명보험 2023.1Q**: item16 raw 보강(2,577.05, 라벨변형 "기타사업비") 했지만 완전히는
  안 닫힌다 — 잔차가 정확히 item8(생명장기재보험손익) 크기와 일치, 이 회사 원표가 "1.보험손익"
  과 "2.재보험손익"을 별도 최상위 항목으로 병기해(56행 표) 재보험을 구조적으로 제외하기
  때문. **룰 완화(item3 단독 후보 추가)를 3개사로 시뮬레이션했더니 메리츠 양쪽이 오히려
  더 벌어져 범용 반영은 기각** — `issuer_structural_residual` 로 재분류 + 박제.
- **DB손해보험 2023.2Q**: item16 이 이미 raw 와 정확히 일치(70,375.73). 그 값을 등식에
  적용하면 잔차가 6,869→63,507 로 악화(이중차감 의심) — 기존 코드 주석(`_zero_other_expense`
  docstring)의 "partial mis-extract" 진단을 재확인만 했고 새 근거는 못 찾았다.
- **흥국화재 2025.1Q**: item16 도 이미 raw 와 정확히 일치(6,266). 잔차 -714(허용오차 200 를
  살짝 초과)를 설명할 추가 항목을 원문에서 못 찾았다.

### 4) sub_leg_gap 3건 — 전부 raw 교차검증했으나 못 닫음, 조사노트만 등재

- **비엔피파리바카디프 2024.4Q/2025.4Q**: item3·item8 을 별도 raw 표(보험계약부채 변동표
  "보험서비스결과 합계", 직접은 부채감소=이익이라 부호반전 주의)로 0.01 이내 교차검증 완료 —
  둘 다 신뢰 가능. 그런데도 item2(Tier1 헤드라인)와 item3+item8(Tier2 합) 갭이 연도 간
  비슷한 크기(10,169.1 / 10,147.6)로 지속 — 구조적 성분이 있는데 특정 못 했다.
- **교보라이프플래닛 2024.4Q**: PAA(보험료배분접근법) 노트 캡션 4건을 찾았으나 그 표가
  파서에서 `rows=1`/빈 nums 로 쪼개져 수치를 못 읽었다(멀티페이지 표 분리 아티팩트 추정).
  같은 회사 2025.4Q 는 이 등식이 정확히 닫혀(diff=0.000) 스키마 자체는 유효 — **2024.4Q
  한정 추출 결함**으로 추정되나 표 분리 로직 복구가 필요해 이번 라운드엔 못 고쳤다.

### 등재부 갱신

`data/_gold/pl_bridge_baseline.json`: 26건→16건(10건 완전 삭제, `_counts` 갱신). 남은 6건은
`class` 를 실태에 맞게 조정(DB생명 2023.1Q → `issuer_structural_residual` 신설)하고
`investigated_20260825` 필드에 raw 인용·재현 스크립트 경로를 남겼다. `pre_existing` 10건은
발주문이 "나머지 13건"으로 명시한 범위 밖이라 손대지 않았다.

### 검증

- combo-diff: `PL_breakdown.json` 8698행→8698행(0 손실), 정확히 13셀(값+당분기 캐스케이드
  포함 40줄)만 변경, 전부 KR0070/KR0072/KR0087/KR0001/KR0082.
  `build_pl()` 개별 호출만 3회(매회 diff 확인) — `build_root_masters.main()` 미실행.
- `user_pl_confirmed_cells.json` 조회 — 16건 관련 회사 전부 무관(그 레지스트리 엔트리는
  `IFRS17_BS`/케이디비 보증준비금뿐), owner 확정 셀 미접촉 확인.
- `tests/fixtures/master_tables_golden.json` `--update` 재생성
  (`pl_bridge:2503P/26F/319S/0NEW` → `2513P/16F/319S/0NEW`, exit_code 2 불변).
- `insurequant_master_tables.xlsx` "손익분해PL" 시트만 `sync_master_xlsx_sheet.py` 로
  cherry-pick 동기화, 사후검증 통과("8698행×9열 마스터와 완전 일치, 나머지 시트 동일").
- `pytest`(골든 6종 + 룰커버리지매니페스트 + 동어반복 + 게이트배선 + unit) 198 passed/1 skipped.
- `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py`
  (FULL_COVERAGE_SWEEP=1 포함, ~9.5분) → **exit 0**. RED=0 · K-ICS gate clear ·
  domain gates pass · DART raw 유실 0 · inbox 위반 0 · offline tests 216 passed/1 skipped.

### 남는 것 (재확인 요청)

6건이 등재부에 남아 있다(기한 2026-10-31): DB생명 2023.1Q(`issuer_structural_residual` 신규
분류 — 이 판단에 동의하는지 확인 부탁), DB손해 2023.2Q · 흥국화재 2025.1Q(둘 다 원인 후보를
소진했다, 재조사 필요), 교보라이프플래닛 2024.4Q(멀티페이지 표 분리 로직 버그 — parser 후속
필요), BNP카디프 2024.4Q/2025.4Q(item2 vs item3+8 구조 성분 미특정). 통째 skip 아니고 전부
raw 인용·재현 스크립트가 붙어 있다.

status: **answered** (완결이 아니라 재확인 요청 — 6건 잔존 + `issuer_structural_residual`
신규 분류 판단에 대한 validation 재확인 필요).
