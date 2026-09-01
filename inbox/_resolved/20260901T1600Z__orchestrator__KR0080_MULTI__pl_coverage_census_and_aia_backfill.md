---
from: orchestrator
to: parser
created: 20260901T1600Z
status: resolved
route: reparse
company: KR0080
period: 2023.4Q,2024.4Q
rule: (census) pl_coverage / no_income_statement
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

owner 2026-09-01: "AIA생명은 왜 또 PL breakdown이 2025부터만 있냐 응? 2024 2023 어따빼먹었누"

발주 내용: 36사 x 14분기 기대 그리드를 (a) 마스터에 있음 / (b) 원천은 있는데 파싱 안 됨 /
(c) 원천 자체가 없음 으로 기계 판정하고, AIA 를 우선 규명한 뒤 파싱 가능한 칸을 채울 것.
raw 가 없으면 downloader 로 라우팅.

## 답변 (recipient 작성 — 처리 후)

### 1. census — 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_pl_coverage_census.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_c_breakdown.py
```

산출: `data/_derived/pl_coverage_census_20260901.json` (39사 x 14분기 = 546칸 전수 판정)

| 판정 | 작업 전 | 작업 후 |
|---|---|---|
| (a) 마스터에 있음 | 356 | **358** |
| (b) raw 는 있는데 PL 없음 | 16 | **14** |
| (c) 원천 없음 | 174 | 174 |

**(c) 174칸의 내역 — 결측이 아니다:**

- **165칸 = 연1회 공시사 15사 x 중간분기 11개.** 구조적 정상이다. 이 15사(KR0004·0029·
  0049·0050·0051·0074·0075·0076·0080·0095·0097·0100·1010·1011·1098)는 분기·반기보고서를
  내지 않고 사업보고서/감사보고서만 낸다. `data/dart/FY*/raw/` 실측이 그대로 이 축을 보여준다
  — **Q1/Q2/Q3 디렉터리는 25개사뿐이고 Q4 만 38~44개사**다. TODO 78th pass 가 live DART
  `list_filings` 로 15사 전원 `pblntf_ty=A` **0건**을 이미 확인했다(독립 확인).
  발주서가 지목한 "3/14분기 · 최소 2023.4Q 가 9개사에서 똑같이 나온다" 는 우연이 아니라는
  가설은 **맞았고**, 그 9개사의 3/14 는 결측이 아니라 **연1회 공시사로서 완전한 커버리지**다
  (창 안의 연간분기 = 2023.4Q·2024.4Q·2025.4Q 세 개뿐).
- **9칸만이 공시주기로 설명되지 않는다** (아래 §4 downloader 라우팅).

### 2. AIA(KR0080) 원인 — 원천은 있었다. 문서가 틀렸다

**"2025부터만" 이 아니라 "2025만" 이었다(1/14).** 원인은 다운로드 누락이 아니다.

`data/dart/FY2023_Q4/raw/KR0080_..._20240409002583/` 와 `FY2024_Q4/.../20250401000094/` 에
**감사보고서 raw XML 이 처음부터 있었다.** 두 파일 모두 완전한 **포괄손익계산서(별도)** 를
담고 있다. 못 읽은 이유는 두 겹이다:

1. `extract_tier1` 이 AIA 의 **4블록 영업수익/영업비용 양식**(Ⅰ.보험영업수익 / Ⅱ.보험영업비용 /
   Ⅲ.투자영업수익 / Ⅳ.투자영업비용)을 인식하지 못해 전 연도에서 `None` 을 돌려줬다.
   DART FS-API 도 이 회사는 정기공시가 없어 데이터가 없다(`data/dart/_fs_api_cache/` 에
   AIA 파일 0개) — 그래서 Tier-1 이 통째로 비어 있었다.
2. 그 결과 coverage 가 `status=no_income_statement` 로 찍혔는데, **그건 추출기에 대한 진술이지
   원천에 대한 진술이 아니다.** 그런데 `extract_tier2_aia` 의 docstring 이 그것을 근거로
   *"There is no table anywhere in the filing carrying this data"* 라고 단정해 놓았다.
   이 문장이 1년간 재조사를 막았다. **삭제하고 CORRECTION 절로 교체했다**
   (`scripts/pl_breakdown/companies.py`).

2025.4Q 만 값이 있었던 이유: 그 해 주석 1.일반사항 의 **산문 문단**을 읽는 핸들러가 있었고,
FY2025 문구에만 맞춰져 있었다. FY2024 는 같은 문단이 **다른 말투**로 쓰였고(보험손익→보험이익,
억원→억, `(-)` 대신 이익/손실 접미사), FY2023 은 그 문단 자체가 없다.

### 3. 고친 것 — `scripts/pl_breakdown/companies.py` 만 수정

신설 함수 4개(전부 KR0080 전용, 다른 회사 경로 무영향):

- `_aia_ofs_text(dirs)` — 별도(`_00760.xml`) 첨부만 읽는다. AIA 는 FY2025 부터 연결
  (`_00761.xml`, "…주식회사와 그 종속기업")도 같이 내므로 파일명으로 연결을 배제한다.
- `_aia_statement_unit(text)` — 포괄손익계산서 제목 블록의 `(단위 : 천원)` cue 를 읽는다.
  **cue 없으면 None → 아무것도 내보내지 않는다**(기본값 가정 금지).
- `_aia_statement(tables, f)` — 위 4블록 양식을 읽어 item 1/3/8/15/16/17/20/21/22/24 산출.
  항등식 3개를 사후 게이트로 건다(±2백만원).
- `_aia_prose_fy2024(text, stmt)` — FY2024 말투 산문에서 item 4/5/6 만 추가로 뽑되,
  **그 문단의 헤드라인 수치가 감사받은 계산서와 일치할 때만** 채택한다.

`extract_tier2_aia` 의 기존 FY2025 산문 경로는 **한 줄도 바꾸지 않았다.** 새 경로는 산문이
안 맞을 때만 타는 fallback 이라, owner 가 이미 검토한 2025.4Q 칸이 움직이지 않는다
(아래 무드리프트 실측).

**교차검증 3중 (추측 아님):**

| 확인 | 결과 |
|---|---|
| FY2024 감사계산서 ↔ **그 해 자기 산문** | 영업이익 2,294억 · 보험이익 766억 · 투자이익 1,528억 · 영업외손실 15억 · 법인세 541억 · 당기순이익 1,738억 — **6/6 정확일치** |
| 산출 item4(원수 CSM상각) ↔ **`CSM_waterfall.json`**(다른 추출기) | 2024.4Q 내 값 1,562.0억 vs 워터폴 CSM상각 **1,561.6억** (억 반올림 내 일치) |
| 계산서 내부 항등식 | 2023.4Q: 174,249 − 27,674 − 81,973 = **64,601 = item1** · 2024.4Q: 185,663 − 51,171 − 57,863 = **76,630 = item1** (둘 다 ±1백만원) |

**채운 칸: 2칸(company-quarter) / 32칸(non-null item)**

- 2023.4Q — 14/24 non-null. item 4/5/6/7 은 **비웠다**(그 해 산문이 없어 CSM상각·위험조정·
  예실차를 원천에서 확정할 수 없다). 0-fill 은 `zero_fill_ok` 2-pass 로직이 자동 억제했다
  (`ever_extracted=[6]` → item6 의 0채움 금지) — 가짜 0 대신 빈 칸.
- 2024.4Q — 18/24 non-null (위 3중 검증한 4/5/6 포함).
- item 18/19(투자이익·보험금융손익)는 **의도적으로 비웠다** — 2025.4Q 의 기존 결정과 보조를
  맞췄다. 다만 이제 근거가 생겼다(§5 owner 문의).
- 2022.4Q 는 구 1104 양식이라 게이트가 거부했다 — **창 밖 분기를 만들어내지 않았다**(정상).
- 값_당분기는 전 분기 None — 연1회 공시사라 직전 3Q YTD 가 없어 유량을 알 수 없다(2025.4Q 와 동일).

### 4. downloader 로 넘긴 것 — 3칸

`inbox/downloader/20260901T1600Z__parser__MULTI_2023.4Q__missing_annual_raw_3_companies.md`

공시주기로 설명되지 않는 9칸 중, **연간(4Q) 셀인데 raw 디렉터리가 아예 없는 3칸**만 라우팅했다:
KR0075 비엔피파리바카디프 2023.4Q · KR0150 서울보증 2023.4Q · KR1098 카카오페이손보 2023.4Q.
나머지 6칸은 서울보증 2023.1Q~2024.3Q 중간분기로 **이미 `no_filing:true` 마커가 붙어 있다**
(상장 전이라 정기공시 의무 없음 — downloader 가 이미 판정한 것).

### 5. 남은 (b) 14칸 — 이번 세션에서 채우지 않았다. 이유를 적는다

| 회사 | 분기 | 상태 |
|---|---|---|
| KR0050 하나손해 | 2023.4Q·2024.4Q·2025.4Q | 마스터에 **아예 없는 회사**(0/14) |
| KR0076 아이엠라이프생명 | 2023.4Q·2024.4Q·2025.4Q | 마스터에 아예 없는 회사(0/14) |
| KR1098 카카오페이손보 | 2024.4Q·2025.4Q | 마스터에 아예 없는 회사(0/14) |
| KR1010 교보라이프플래닛 | 2023.4Q | 계산서형 표 자체가 안 잡힘 |
| KR0150 서울보증 | 2024.4Q | xml 3개·표 1,333개, 계산서 후보 10개 |
| KR0003·KR0008·KR0032·KR0072 | 2023.1Q | IFRS17 전환 첫 분기(양식 과도기) |

전수 확인은 `scripts/_probes/probe_20260901_gap16_statement_survey.py` (14칸 전부 raw 표를
갖고 있고 `extract_tier1` 은 14/14 전부 None). **공통 양식이 없다** — 실측한 것만 적으면
KR0076 은 평면 `Ⅰ.영업수익/Ⅱ.영업비용`(보험금융수익이 영업수익 안에, 단위 원),
KR1098 은 `Ⅰ.보험손익/Ⅱ.투자손익` 명시형(단위 원), AIA 는 4블록형으로 **셋 다 다르다.**
`extract_tier1` 을 일반화해서 한 번에 잡으려 하면 이미 값이 있는 358칸 전부가 사정권에
들어온다 — 회사별 핸들러로 가되 각각 별도 교차검증이 필요하다.

또 하나 **범위 밖 판단**: KR0050·KR0076·KR1098 은 지금 마스터에 없는 회사라, 채우면
PL 마스터 회사수가 36 → 39 로 늘고 사이트에 새 회사가 등장한다. 이건 파서 판단이 아니라
**owner 승인 사항**이라 손대지 않았다(§6).

### 6. owner 에게 올릴 것 2건

1. **KR0050 하나손해 · KR0076 아이엠라이프 · KR1098 카카오페이손보를 PL 화면에 새로
   등장시켜도 되나?** raw 는 셋 다 있고 파싱 가능해 보인다. 회사수가 36→39 가 된다.
2. **AIA item18/19 를 채울까?** 기존 docstring 은 "산문 한 줄뿐이고 독립 확증이 없어
   보류, owner 에게 보고" 라고 적어 두었다. 이번에 그 확증이 나왔다 — 감사계산서가
   보험금융비용/재보험금융비용을 **별도 행으로** 싣고 있고(2025: 735,954 + 8,603 = 744,557
   백만원), 그 해 산문의 "보험금융비용은 (-)7,446억원" 과 일치한다. 다만 채우면 2025.4Q 도
   같이 바꿔야 계열이 일관되므로(owner 검토필 칸) 승인 전에는 안 건드린다.

부수 관찰: 2025.4Q 는 `pl_bridge [보험손익(dual)] diff=+1000.0` 로 baseline 35건 중 하나로
등재돼 있는데, 이는 산문이 억 단위로 반올림돼 있어서다. 이번에 넣은 2023/2024 는 계산서
기반이라 항등식이 ±1백만원으로 닫힌다 — 즉 **2025.4Q 도 계산서로 갈아타면 그 baseline 1건이
사라진다.** 위 2번과 같은 결정이라 묶어서 올린다.

### 7. 게이트 실측

| 게이트 | 결과 |
|---|---|
| combo-diff (viz master, 전후) | **LOST 0 · NULLED 0 · CHANGED 0 · ADDED 64** (KR0080 2023.4Q/2024.4Q 만) — `probe_20260901_combo_diff.py` |
| combo-diff (root `PL_breakdown.json`, 전후) | 동일 — LOST 0 · NULLED 0 · CHANGED 0 · ADDED 64 |
| AIA 2025.4Q 회귀 | **NO DRIFT** (24항목 전부 커밋값과 동일) — `probe_20260901_aia_handler_verify.py` |
| `tests/test_pl_breakdown_golden.py` (`RUN_PL_GOLDEN=1`) | 갱신 전 FAIL 이 정확히 +64행/+2분기/**+32 non-null**(=14+18) 를 지목 → `--update` 후 **1 passed** (349초) |
| `scripts/validate_master_tables.py --no-build` | `pl_bridge 35F` **불변**(신규 0) · `coverage_hole:0CSM/0PL` · 골든 갱신 |
| `scripts/validate_data_contract.py` | RED=1 — **내 것 아님**(K-ICS 레인 진행 중 항목). PL 축 신규 RED 0 |
| `scripts/validate_golden_input_fingerprints.py` | pl_breakdown **ok**. `post_transition` RED 1건은 K-ICS 레인 것이라 **일부러 안 건드렸다**(§8) |
| `pytest tests/unit/` | 131 passed |
| `pytest test_master_tables_golden + test_deploy_assets + test_identity_tautology` | 21 passed |
| xlsx `sync_master_xlsx_sheet.py "손익분해PL"` | **변경 셀 0 · 추가 64행 · 삭제 0**, 사후검증 "나머지 시트 값 동일" |

**골든 갱신의 귀속을 따로 증명했다.** 공유 워크트리라 남의 드리프트를 내 골든에 흡수할
위험이 있어, 변경 **전** 마스터로 `validate_master_tables --no-build` 를 한 번 더 돌려
그 SUMMARY 가 저장된 골든과 **완전 일치**함을 확인했다. 따라서 SUMMARY 의 모든 델타
(pl_bridge 3038→3049P, tax22_src 74→76S, zero_legs 3→4, csm_amort_identity 342→343P/0→1S)는
전부 내 2칸에서 왔다. `zero_legs` 신규 1건은 AIA 2024.4Q `zero=0 none=4` 로, 이미 수용된
2025.4Q 와 **모양이 같다**(가짜 0 없음, 재보험 세부 4항목이 진짜 미공시).

### 8. 공유 워크트리 주의 (사고 없이 종결)

`validate_golden_input_fingerprints.py --update` 는 **6개 spec 전부를 현재 트리로 덮어쓴다.**
지금 `post_transition` 이 K-ICS 레인의 md_inbox 수정 때문에 INPUTS_MOVED RED 인데, 그대로
`--update` 하면 아무도 그 골든을 돌리지 않은 채 "검증됨" 으로 도장이 찍힌다(false-green).
그래서 `scripts/_probes/probe_20260901_fingerprint_update_pl_only.py` 로 **`pl_breakdown`
한 spec 만** 갱신하고 나머지 5개가 바이트 그대로임을 출력으로 증명했다. `post_transition`
RED 은 **일부러 남겨 뒀다** — 그 레인 세션이 닫을 것.

커밋은 하지 않았다(오케스트레이터 일괄 커밋).
