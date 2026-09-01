---
from: orchestrator
to: parser
created: 20260901T1215Z
status: resolved
route: reparse
company: KR0050,KR0076,KR0080
period: 2023.4Q,2024.4Q,2025.4Q
rule: PL_CSM_AMORT_VS_WATERFALL
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

`validate_data_contract.py` RED 7건, `PL_CSM_AMORT_VS_WATERFALL`(PL 원수CSM상각 결측
vs 워터폴 상각 有):

```
아이엠라이프생명보험(KR0076)  2023.4Q / 2024.4Q / 2025.4Q
하나손해보험(KR0050)          2023.4Q / 2024.4Q / 2025.4Q
에이아이에이생명보험(KR0080)   2023.4Q
```

원인 규명 + 채울 수 있는 건 채우고, 못 채우면 근거를 갖춰 게이트가 실제로 읽는 자리에
등재할 것. 79th pass 가 남긴 단서: 하나손해는 raw 에 표가 있다(주석29 218.85억=워터폴
218.9억 일치), AIA 2023.4Q 는 raw 전수확인 결과 원문 부재, 아이엠라이프는 미확인.

## 답변 (recipient 작성 — 처리 후)

**3사 전부 raw 로 재확인, 6칸은 채웠고 1칸(AIA 2023.4Q)은 등재로 닫았다. RED 7→0.**

### 하나손해보험(KR0050) 3분기 — 채움

raw 에 있는 것은 확인됐지만(79th pass), 아직 안 뽑은 표였다. `주석29` 류 "보험손익
상세내역"(하나손해는 캡션이 일반 `- 당기`/`- 전기`라 3-needle row-content 게이트로 특정)
에서 "보험계약마진 상각액" 행(장기 컬럼, 단위 천원)을 직접 읽는 헬퍼
`_hana_sonbo_csm_amort()`를 `scripts/pl_breakdown/companies.py`에 신설,
`extract_tier2_hana_sonbo`에서 item4로 병합. raw 손계산 대조(전부 raw/1000 = 백만원):

| 분기 | raw(천원) | → 백만원 | → 억원 | 워터폴 억원 | diff |
|---|---|---|---|---|---|
| 2023.4Q | 15,704,909 | 15,704.909 | 157.049 | 157.0 | 0.049 |
| 2024.4Q | 19,971,594 | 19,971.594 | 199.716 | 199.7 | 0.016 |
| 2025.4Q | 21,885,413 | 21,885.413 | 218.854 | 218.9 | 0.046 |

item4만 채웠다(item5/6/7 아님) — 이 회사 item3(생명장기 원수손익)은 기존 핸들러가 이미
전사(장기+자동차+일반) 합계로 채워둔 상태라, 장기 전용인 item5/6을 새로 채우면 item7 plug가
LOB 혼합값을 흡수하게 된다. 이번 티켓 범위(item4 단건) 밖이라 손대지 않음 — 근거는
`_hana_sonbo_csm_amort` docstring.

### 아이엠라이프생명보험(KR0076) 3분기 — 채움

79th pass 미확인분. raw 를 열어보니 `1) 보험영업수익의 내역` 노트(단위 백만원, 캡션이
FY2023 만 `(3) 보험손익 및 재보험손익` 접두가 붙고 FY2024/2025는 없음 — 부분일치로
양쪽 다 매칭)에 "당기서비스의 이전으로 당기손익에 인식된 보험계약마진" 행이 당기 컬럼
그대로 있다. 헬퍼 `_imelife_csm_amort()` 신설, `extract_tier2_imelife`에서 item4로 병합.
raw 대조 + 연도간 전기컬럼 교차검증(FY2025의 전기값이 FY2024의 당기값과 정확히 일치 등,
2회 독립 확인):

| 분기 | raw(백만원, 그대로) | 억원 | 워터폴 억원 | diff |
|---|---|---|---|---|
| 2023.4Q | 57,116 | 571.16 | 571.1 | 0.06 |
| 2024.4Q | 54,918 | 549.18 | 549.2 | 0.02 |
| 2025.4Q | 53,794 | 537.94 | 537.9 | 0.04 |

이 회사는 생보 전업(자동차/일반 없음)이라 item3가 이미 장기 전용이지만, item4 단건 스코프를
지키려 5/6/7은 이번에도 손대지 않았다(후속 필요시 별도 티켓).

### 에이아이에이생명보험(KR0080) 2023.4Q — 등재로 닫음, 룰에 ledger 경로 신설

79th pass 가 "raw 전수확인 결과 원문 부재"라고 TODO 에는 적었지만 **게이트가 읽는 자리가
없어서** 계속 RED 였다(`PL_CSM_AMORT_VS_WATERFALL`은 애초에 예외 경로 자체가 없었음 —
`CSM_AMORT_IDENTITY_PINNED`가 쓰는 `csm_amort_identity_ledger.json`과 달리 "한쪽만
결측" 축은 등재부가 없었다). 이번에 직접 raw(`20240409002583_00760.xml`) 를 다시 훑어
79th pass 근거를 재확인(요약 산문 없음/보험계약마진 15개 언급 전부 정책설명/기초잔액
CSM 무관 1회)했고, 신설 등재부 `data/_gold/pl_csm_amort_missing_ledger.json`에 등재 +
`scripts/validate_data_contract.py`의 `PL_CSM_AMORT_VS_WATERFALL` 코드에 ledger-lookup
분기(PINNED→YELLOW `PL_CSM_AMORT_MISSING_DOCUMENTED` / DRIFT→RED
`PL_CSM_AMORT_MISSING_LEDGER_DRIFT` / 등재없음→기존 RED)와 stale-entry 감지 루프
(`PL_CSM_AMORT_MISSING_LEDGER_INERT`)를 추가했다(`scripts/validate_master_tables.py`에
`csm_amort_missing_ledger()` 헬퍼 신설). `CSM_AMORT_IDENTITY_PINNED`의 패턴을 그대로 참고.

### 빌드 경로 — 메인 트리, 회사 스코프, combo-diff

**격리 워크트리 아님, 메인 트리에서 처리**(오케 지시대로). `build_pl_breakdown.py`의
discover_filings/parse_filing/assemble을 KR0050/KR0076만 스코프로 재호출하는
`scripts/_probes/probe_20260901_pl_csm_amort_scoped_build.py` 신설 → union-merge로
`pl_breakdown_master.json`/`pl_breakdown_coverage.json`에 반영(두 회사 행만 교체) →
`build_root_masters.build_pl()`(개별 함수만, `main()` 아님)으로 루트 `PL_breakdown.json`
전파. 전후 combo-diff(양쪽 마스터 전부): **LOST=0 ADDED=0 NULLED=0 CHANGED=0 FILLED=6**
(정확히 위 표의 6칸만). `validate_master_tables.py --no-build`는 exit 2→2 불변(원인:
pl_bridge 기지 35F 등 무관 baseline, 실측: PL_breakdown.json 을 BEFORE 로 스왑해 동일
조건으로 재확인 — `csm_amort_identity` 축만 343P/9S → 349P/3S로 이동, 0F 불변).

부산물 정리: `data/_gold/pl_amort_coverage_baseline.json`(다른 축, PL 버킷 통째부재용)에
있던 이 3사 관련 8개 항목이 이번 채움으로 전부 `BASELINE_INERT`(게이트가 재검산해 확인)가
돼 삭제 — 목록이 비지 않게 관리하는 그 파일 자신의 규칙을 따랐다.

### 골든/지문

- `tests/fixtures/pl_breakdown_golden.json` — `pl_breakdown` spec 만 `--update`
  (subprocess 재빌드 아닌 디스크 스냅샷, SKILL 명시 사유와 동일하게 이 세션도 광역
  네트워크의존 재빌드를 피함). master_rows/company_quarters 불변, non_null 10125→10131(+6).
- `tests/fixtures/builder_input_fingerprints.json` — `probe_20260901_fingerprint_update_pl_only.py
  pl_breakdown` 로 `pl_breakdown` spec 만 갱신(code_sha256/fixture_sha256 변경, input 계열
  불변 — raw 파일 자체는 안 건드렸으므로). 나머지 5개 spec(dividend/ifrs17_bs/post_transition/
  viz_csm_waterfall/viz_ifrs17_panels) UNCHANGED 확인 완료.

### 검증

- `python scripts/validate_data_contract.py` → **RED 7→0**, YELLOW 104→96(coverage-baseline
  INERT 8건 정리로 순감), `PL_CSM_AMORT_VS_WATERFALL` 잔여 0.
- `python scripts/_data_contract_selftest.py` → 57/57 PASS(L2 PL_CSM_AMORT_VS_WATERFALL ·
  L3 PL_BUCKET_ABSENT_VS_WATERFALL 포함 — 합성회사 KR9001 픽스처라 신설 ledger와 무관,
  회귀 없음 재확인).
- `pytest tests/test_rule_coverage_manifest.py tests/test_identity_tautology.py
  tests/test_pl_breakdown_golden.py tests/test_deploy_assets.py` → 85 passed, 1 skipped
  (RUN_PL_GOLDEN 미설정, 의도), 환경성 PermissionError 1건(시스템 임시폴더 잠금, 격리
  --basetemp 로 재실행해 진짜 PASS 확인 — 코드와 무관).
- `sync_master_xlsx_sheet.py "손익분해PL"` → 검증 OK, 11866→11866행(행수 불변), EDIT 6·
  나머지는 KR1098 위치재기록(같은 키, 79th pass 와 동일 패턴, "나머지 시트 값 동일" 확인).

커밋은 하지 않았다(오케스트레이터 일괄 처리). K-ICS 레인 파일은 건드리지 않았다.
