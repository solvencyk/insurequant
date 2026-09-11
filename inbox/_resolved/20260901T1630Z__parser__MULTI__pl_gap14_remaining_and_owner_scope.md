---
from: parser
to: parser
created: 20260901T1630Z
status: resolved
route: reparse
company: KR0050,KR0076,KR1098,KR1010,KR0150,KR0003,KR0008,KR0032,KR0072,KR0080
period: 2023.1Q,2023.4Q,2024.4Q,2025.4Q
rule: (census) pl_coverage / no_income_statement
lane: ifrs17
iter: 2
---

## 미결 (sender 작성)

`20260901T1600Z__orchestrator__KR0080_MULTI__pl_coverage_census_and_aia_backfill.md` 의
잔여분. AIA 2칸은 채웠고, census 가 드러낸 **(b) raw 는 있는데 PL 이 없는 14칸**이 남았다.
`route: escalate` 인 이유는 파싱 난이도가 아니라 **범위 결정 2건이 owner 몫**이기 때문이다.

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_pl_coverage_census.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_gap16_statement_survey.py
```

### 남은 14칸 (실측: 14/14 전부 raw 표를 갖고 있고 `extract_tier1` 은 14/14 None)

| 회사 | 분기 | 성격 |
|---|---|---|
| KR0050 하나손해보험 | 2023.4Q · 2024.4Q · 2025.4Q | 마스터에 **아예 없는 회사**(0/14) |
| KR0076 아이엠라이프생명보험 | 2023.4Q · 2024.4Q · 2025.4Q | 마스터에 아예 없는 회사(0/14) |
| KR1098 카카오페이손해보험 | 2024.4Q · 2025.4Q | 마스터에 아예 없는 회사(0/14) |
| KR1010 교보라이프플래닛생명보험 | 2023.4Q | 기존 회사의 과거 1칸. 계산서형 표가 안 잡힘 |
| KR0150 서울보증보험 | 2024.4Q | 기존 회사. xml 3개·표 1,333개, 계산서 후보 10개 |
| KR0003 롯데손해 · KR0008 삼성화재 · KR0032 NH농협손보 · KR0072 케이디비생명 | 2023.1Q | IFRS17 전환 첫 분기(양식 과도기) |

### 왜 일반화(`extract_tier1` 확장)로 풀면 안 되나 — 실측 근거

세 회사 표를 직접 떠 보니 **양식이 서로 다르다**:

- **KR0080 AIA**(이번에 처리): `Ⅰ.보험영업수익 / Ⅱ.보험영업비용 / Ⅲ.투자영업수익 / Ⅳ.투자영업비용`
  4블록형, 단위 천원.
- **KR0076 아이엠라이프**: 평면 `Ⅰ.영업수익 / Ⅱ.영업비용`. **보험금융수익이 영업수익 안에**
  들어 있어 보험손익을 뽑으려면 하위행을 골라야 한다. 단위 **원**.
- **KR1098 카카오페이손보**: `Ⅰ.보험손익 / Ⅱ.투자손익` 을 **명시적으로** 찍어 준다
  (가장 쉬움). 단위 원.

`extract_tier1` 을 일반화하면 이미 값이 있는 **358칸 전부가 사정권**에 들어온다.
회사별 핸들러(`scripts/pl_breakdown/companies.py` + `LIFE_HANDLERS`/`SONBO_HANDLERS` 등록)로
가야 하고, AIA 때처럼 **회사마다 독립 교차검증**(자기 산문 / CSM_waterfall / 표 내부 항등식)이
따로 필요하다.

## owner 결정이 필요한 것 2건

### Q1. KR0050 하나손해 · KR0076 아이엠라이프 · KR1098 카카오페이손보를 PL 화면에 새로 올릴까?

raw 는 셋 다 있고 파싱 가능해 보인다(8칸). 채우면 **PL 마스터 회사수가 36 → 39** 가 되고
사이트에 새 회사 3곳이 등장한다. 이건 파서 판단이 아니라 제품 결정이라 손대지 않았다.

참고로 이 3사는 **CSM 쪽에는 이미 들어와 있다**(예: 커밋 `9a067dd` 가 KR0050/KR0076
2023.4Q CSM 을 다루고 있다) — 즉 PL 만 비어 있는 비대칭 상태다. 그 점에서 "채우는 게
자연스럽다" 는 쪽에 무게가 실린다. 승인만 주면 진행한다.

### Q2. AIA item18/19(투자이익·보험금융손익)를 채울까?

`extract_tier2_aia` docstring 이 "산문 한 줄뿐이고 독립 확증이 없어 보류, owner 에게 보고"
라고 적어 둔 항목인데, 이번 census 에서 **그 확증이 나왔다**: 감사받은 포괄손익계산서가
보험금융비용·재보험금융비용을 **별도 행으로** 싣고 있고(2025.4Q: 735,954 + 8,603 = 744,557
백만원), 같은 해 산문의 "보험금융비용은 (-)7,446억원" 과 일치한다. 2023/2024 도 동일 구조다.

채우려면 **2025.4Q 도 같이 바꿔야** 계열이 일관된다(owner 검토필 칸이라 무단 변경 금지).

곁가지로 같은 결정에 묶이는 것: 2025.4Q 는 지금
`pl_bridge [보험손익(dual)] diff=+1000.0` 로 baseline 35건 중 1건으로 등재돼 있는데,
원인은 그 해 값이 **산문의 억 단위 반올림**이라서다. 이번에 넣은 2023/2024 는 계산서
기반이라 항등식이 ±1백만원으로 닫힌다. **2025.4Q 도 계산서 기반으로 갈아타면 그 baseline
1건이 사라진다**(정확도도 올라간다). Q2 와 한 덩어리로 결정하면 된다.

## owner 결정 (2026-09-11, 오케스트레이터 전달 — 채팅 확답)

- **Q1 = 올린다.** KR0050 하나손해·KR0076 아이엠라이프·KR1098 카카오페이손보를 PL 마스터에 신규 등재(36사→39사). 회사별 핸들러(`scripts/pl_breakdown/companies.py` 등록) + 회사마다 독립 교차검증(자기 산문/CSM_waterfall/표 내부 항등식). 같은 결정으로 KR1010 2023.4Q·KR0150 2024.4Q·전환 첫 분기 4사(KR0003/KR0008/KR0032/KR0072 2023.1Q)도 회사별 핸들러로 채운다(14칸 전부 대상, 칸 단위 skip만 허용·사유 기록).
- **Q2 = 채우고 갈아탄다.** AIA(KR0080) item18/19를 감사받은 포괄손익계산서 기준으로 2023/2024 채우고, 2025.4Q도 산문(억 반올림) 기준에서 계산서 기준으로 교체. `pl_bridge [보험손익(dual)] diff=+1000.0` baseline 1건이 사라지는지 확인해 baseline 파일에서 제거.
- route 를 `escalate` → `reparse` 로 내린다(owner 결정 완료). 담당: parser/ifrs17. 처리 후 `status: answered`, 오케스트레이터가 재확인해 닫는다.

## 답변 (parser/ifrs17, 2026-09-12)

KR0050·KR0076·KR1098 8칸은 이전 세션(커밋 `09b4b26`/`fe3a20f`)이 이미 처리해 뒀다(재확인만).
남은 **14칸 중 6칸**(KR1010/KR0150/KR0003/KR0008/KR0032/KR0072)을 하위 에이전트 6개+AIA
조사 1개(총 7개, 병렬 조사 전용·파일쓰기 없음)로 원문을 확보해 이 세션이 직접 적재했다.

### Q1 결과 (6칸 신규 등재)

| 회사·분기 | 채운 항목 수 | 방법 | 비고 |
|---|---|---|---|
| KR1010 교보라이프플래닛 2023.4Q | 24/32 | 연결기준(기존 마스터와 basis 일치) | item2≠item3+item8 4,698백만원 불일치, `pl_bridge_baseline.json`에 원인미규명으로 등재 |
| KR0150 서울보증 2024.4Q | 13/32 | `_sgi_re_legs` 라벨변형("재보험영업수익:") 코드수정 + override | item1≈13+14+15-16 잔차 0.000346 |
| KR0003 롯데손해 2023.1Q | 5/32 | override(항목20-24만) | 원문 "4.재무제표~5.주석" 섹션 자체가 공백이라 1-19는 억지로 안 채움. CSM_waterfall엔 값 있어 `pl_csm_amort_missing_ledger.json`에 등재 |
| KR0008 삼성화재 2023.1Q | 24/32 | 주석20 직접판독 + override | item1=2+13+14-16 원단위 1 이내 정합 |
| KR0032 NH농협손보 2023.1Q | 22/32 | 주석14+MD&A 직접판독 + override | item2=3+8·item20=1+17·item22=20+21·item24=22-23 전부 EXACT |
| KR0072 KDB생명 2023.1Q | 18/32 | 2023.2Q와 동일 메커니즘(`_GOLD_CELL_OVERRIDE`) | 부수 발견: 빌더가 t1=t2=None이면 override 존재와 무관하게 무조건 skip하던 버그를 fix(다른 회사 영향 0, 전사 재빌드로 확인) |

### Q2 결과 — AIA(KR0080)

item18/19는 2023/2024/2025.4Q 전부 이미 정확(재확인, 무변경). 2025.4Q의 나머지 12항목
(1/3/7/8/16/17/20/21/22/23/24, item2는 파생)을 산문(억원 반올림) 기준에서 감사받은
포괄손익계산서(천원 정밀) 기준으로 전환했다(`extract_tier2_aia` 수정). item4/5/6(CSM/
RA/예실차)은 계산서에 측정요소 분해가 없어 계속 산문 소스 — 2025.4Q만 부분적으로 두
소스가 섞인 상태, 후속으로 더 정밀한 주석표가 발견되면 갈아탈 수 있음. **`pl_bridge_
baseline.json`의 `에이아이에이생명보험|2025.4Q|보험손익(dual) diff=+1000.0` 항목이
실측 0.000으로 닫혀 등재부에서 제거했다.**

### 검증

회사 스코프 재실행(discover_filings 결과를 TARGET_CODES로 필터링, `main()` 미실행) +
combo-diff 2층(LOST=0 전 구간, 예상 밖 회사 터치 0) 매 단계 확인. `RUN_PL_GOLDEN=1
pytest tests/test_pl_breakdown_golden.py`가 전체 39사 재빌드로 회사스코프 결과와
바이트 동일함을 재확인(로우/회사분기/논널 카운트 일치, 다른 회사 회귀 0). 부수로
`coverage_holes()`에 `na_registry` 파라미터를 신설해 서울보증의 구조적 item2 결측을
`LOB_LEG_NA` 등재로 흡수(이 회사가 active_min=7 문턱을 넘으며 새로 터진 MASTER_HOLE
7건의 근본 해결). `PL_CONSTRUCTIVE_BLIND`에서 item23(법인세)을 GUARDED로 이동
(KR0072 2023.1Q 신규 등재로 `PL_YTD_COLLAPSE_TO_ZERO`가 처음으로 이 항목을 포착할 수
있게 됨을 변이시험으로 실측 확인). `validate_data_contract.py` **RED=0**,
`test_master_tables_golden.py`/`test_rule_coverage_manifest.py`(83개) 전부 PASS.
`sync_master_xlsx_sheet.py "손익분해PL"` 검증 OK.

### 재현 명령
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260912_pl_scoped_build_round2.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260912_pl_scoped_build_kr0072_kr0150.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260912_pl_scoped_build_aia.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260911_run_build_pl_only.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
```

### 못 한 것 / 후속 필요
- KR1010 item2 vs item3+item8 불일치 원인 미규명(등재만, 추측 안 함).
- KR0080 item4/5/6은 여전히 산문 소스 — 더 정밀한 별도 주석표가 있는지는 미탐색.
- `validate_golden_input_fingerprints.py`의 dividend/post_transition 2그룹은 kics 레인이
  병행 수정 중인 `kics_disclosure.json`이 원인이라 손대지 않음(별도 task로 등록해 둠,
  kics 레인 작업 완료 후 그쪽에서 재검증 필요).

status를 `answered`로 바꾼다 — 오케스트레이터가 재확인해 닫아 주길 바란다.

## 종결 재확인

재확인(orchestrator, 2026-09-12): PL_breakdown 11,930→12,122행(+192 = 6사×32항목), 회사 36→39. 중계값 스팟체크 12칸 전부 일치(KR0008 item20 808,970 · KR0032 item1 54,280 · KR0150 item24 210,955.000581 · KR1010 item24 −22,036.475809 · KR0072 item4 11,125 · KR0003 item24 79,375 · KR0080 item1 39,225.455). `pl_bridge_baseline.json` 의 AIA 2025.4Q diff=+1000 항목 소멸 확인. `validate_data_contract.py` RED 0, PL 골든 재생성. 미처리로 남긴 것: KR0080 item4/5/6 은 산문값 유지(하위 조사에서 주석18(4) 표 153,059/30,499/−25,069 확인됨 — 다음 ifrs17 라운드에 주석 기준으로 교체 권장, TODO 기록) · KR1010 item2≠3+8 원인. **resolved.**
