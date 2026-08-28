---
from: orchestrator
to: parser
created: 20260829T1600Z
status: answered
route: reparse
company: KR0079
period: 2025.2Q,2025.3Q
lane: ifrs17
iter: 2
---

## 미결 (orchestrator 작성 — 앞 작업의 오판 정정)

**미래에셋생명(KR0079) 2025.2Q·2025.3Q 는 원문이 멀쩡히 있다. 앞 작업이 glob 을 잘못 잡았다.**

`_resolved/20260828T2300Z` 작업이 이 두 분기를 *"raw 가 zip 뿐이라 확인 불가"* 로 남겼는데
틀렸다. XML 은 이미 풀려 있고 **`xml/` 하위**에 있다.

```
data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml   6,542,745자
data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml   9,730,586자
```

**이건 알려진 레이아웃 규약이다.** `scripts/build_csm_waterfall_master.py:13` 주석:
*"quarterly = KR000X_name/xml/<rcept>.xml ; annual = KR000X_name_<rcept>/<rcept>.xml"*.
**분기보고서는 `xml/` 하위, 사업보고서는 최상위**다. 그 빌더는 `rd.glob("*.xml") +
rd.glob("xml/*.xml") + rd.glob("extracted/*.xml")` 로, `build_ifrs17_bs.py` 는 `**/*.xml` 로
제대로 훑는다. 평범한 `raw/KR0079_*/*.xml` 만 쓰면 분기보고서를 통째로 못 본다.

### 노트 존재 확인 (orchestrator 실측)

두 분기 다 2026.2Q 와 같은 구조다.

```
보험료배분접근법을 적용한 보험계약 외의 보험계약   16회
보험손익의 변동내역                    2회
잔여보장부채 변동분과 발생사고부채 변동분의 차이조정  6회
일반보험서비스수익                     3회
```

### 요청

1. **두 분기에 item6 추출을 시도해라.** 방법은 2026.2Q 와 동일하다
   (`_resolved/20260828T2300Z` 답변 + `scripts/_probes/mirae_item6_extract_test.py`).
2. **모집단 3중 대사를 각 분기에서 다시 확인해라** — 표2 7성분 합 = 표3 보험수익 lump =
   Tier-1 별도 일반보험서비스수익. 2026.2Q 는 594,378,172,139원으로 닫혔다. 안 닫히면
   뽑지 말고 보고해라.
3. **경계 규칙도 다시 대조해라** — 표3 손실요소열 합 = 표2 손실요소배분액 합. 2026.2Q 는
   원 단위로 일치했다. 베끼지 말고 그 분기에서 확인해라.
4. **발생 측 열**: 2026.2Q 는 LRC 손실요소외 열이 5개 상품 전부 리터럴 `0` 이라 두 후보
   공식이 동일했다. **이 두 분기에서도 그런지 확인**하고, 아니면 NH식(합계열에서 손실요소배분
   되돌림)으로 계산해라.

### 같이 확인할 것 — 이게 더 중요하다

**같은 glob 사각이 다른 곳에도 있는지 census 를 돌려라.** orchestrator 실측으로
`data/dart/FY*/raw/KR*` 중 최상위에 xml 이 없고 `xml/` 하위에만 있는 디렉터리가 **64건**,
둘 다 있는 것이 18건이다. 빌더들은 대부분 `xml/` 을 훑지만, **`scripts/build_net_income_breakdown.py:550`
은 `*.xml` + `extracted/*.xml` 만 보고 `xml/` 을 빠뜨린다.**

- 그 스크립트가 지금 쓰이는지 확인하고, 쓰인다면 몇 건을 못 보고 있는지 실측해라.
- ifrs17 레인의 다른 추출 경로에도 같은 패턴이 있는지 훑어라.
- **결과를 보고해라. 고칠지는 그 다음 판단이다.**

### 하지 말 것

- 확신이 안 서면 채우지 마라. 이 축은 폐쇄식이 예실차 0 이어도 닫혀서 틀린 값을 게이트가 못 잡는다.
- item11(재보험)은 Tier-1 대사가 안 닫힌 상태 그대로 두고 손대지 마라.
- `index.html`·`IFRS17.html`·`public_exports/` 금지. 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.
- 마스터 재빌드 시 골든 `--update` + `scripts/validate_golden_input_fingerprints.py` 지문 갱신 같이.
- `build_root_masters.py` 의 `main()` 통짜 실행 금지. openpyxl 로 xlsx 재저장 금지.

## 답변 (recipient 작성 — 처리 후)

**item6 두 분기 다 채움 완료. glob 사각 census도 완료 — `build_net_income_breakdown.py`는
실제 버그이나 현재 라이브 경로 아님(report only, 미수정).**

### 1) 2025.2Q / 2025.3Q item6 추출 결과

원문(`xml/` 하위, 지적하신 그대로): 두 분기 다 2026.2Q와 같은 표 구조(표2 예상측 7성분 /
표3 발생측 LRC·LIC 롤포워드)를 확인했지만, **표2(예상측)의 라벨이 2026.2Q와 다르다**
(발생측 라벨은 원래 상수와 그대로 일치). 원문 직접 대조
(`scripts/_probes/mirae_2025q2q3_dump_texp_candidate.py`):

```
2026.2Q     : "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가"
2025.2Q/3Q  : "발생한 보험금 및 그 밖의 발생한 보험서비스비용에 따른 증가분(감소분), 보험계약부채(자산)"
```

같은 개념의 DART XBRL 택소노미 패러프레이즈(표 구조·값 위치 동일, 5상품×3전환유형=15열
wide table). 7성분 중 1/3/5번만 다른 문구, 2/4/6/7번은 두 라벨 era 모두에서 substring
일치라 손 안 댐.

**모집단 3중 대사 + 경계 규칙 — 베끼지 않고 각 분기 직접 재계산**
(`scripts/_probes/mirae_2025q2q3_full_recon.py`):

```
2025.2Q: 후보A(LIC열단독)=277,903,899,183  후보B(합계−손실요소배분)=277,903,899,183  (A−B=0.000000)
         경계: 표3 손실요소열 합=−1,746,487,144  =  표2 손실요소배분액 합=−1,746,487,144  (원 단위 일치)
         내부검산: 표2 7성분 합=520,920,018,629  vs  표3 보험수익 lump=−520,920,018,629 (부호반전, |diff|=0)
         Tier-1 앵커: 별도 일반보험서비스수익=520,920,018,629 (7성분 합과 diff=0)
         exp(예상4종)=285,824,182,112 → item6 = (285,824,182,112 − 277,903,899,183)/1e6
                    = 7,920.282929백만원

2025.3Q: 후보A=후보B=437,835,809,466 (diff=0)
         경계: −2,882,700,242 = −2,882,700,242 (일치)
         내부검산·Tier-1앵커 전부 원 단위 일치 (총7성분=795,957,570,679)
         exp=435,481,967,258 → item6 = (435,481,967,258 − 437,835,809,466)/1e6
                    = −2,353.842208백만원
```

**발생 측 열 — 두 분기 다 LRC_손실요소외 열이 5개 상품 전부 리터럴 `0`**(대시 아님, 원문
그대로): 사망/건강/연금/저축/기타 전부 `0.0` 확인. 2026.2Q와 같은 이유로 후보A=후보B가
소수점까지 동일(구조적으로 항상 그런 게 아니라 이 3개 분기 전부 우연히 그런 것 — 코드는
일반식 B `act = full_row − loss_alloc`를 무조건 쓴다, LIC열 단독 픽 아님).

**구현**: `scripts/pl_breakdown/companies.py`에 `_MA_EXP4_ROW_ALT` + `_MA_EXP4_ROW_VARIANTS`
신설, `_MA_7COMP_ROWS`의 1/3/5번 성분을 (원문,ALT) 튜플로 확장, `_ma_row_sum`/
`_ma_find_product_table`가 str 또는 tuple 둘 다 받도록 일반화. `_ma_yesilcha_direct`는
`_MA_EXP4_ROW_VARIANTS`로 t_exp를 찾는다 — 위 두 숫자는 하드코딩이 아니라 **실제
프로덕션 함수를 raw XML에 직접 돌려 재확인**했다
(`scripts/_probes/mirae_2025q2q3_verify_production.py`):

```
2025.2Q: _ma_yesilcha_direct = 7920.282929   extract_tier2_miraeasset() item4=99207.397518 item5=18416.51587 item9=-3842.019626 item10=-740.366241 item6=7920.282929
2025.3Q: _ma_yesilcha_direct = -2353.842208  item4=153120.516457 item5=27703.562474 item9=-5933.374183 item10=-1054.741468 item6=-2353.842208
2026.2Q(회귀확인): _ma_yesilcha_direct = -18120.139965  (기존 커밋값과 정확히 일치 — 회귀 0)
```

item4/5/9/10은 라벨 변경과 무관한 별도 경로라 완전 불변.

**부수 발견 — 2026.1Q도 같은 ALT 라벨로 게이트를 통과하지만 이번 티켓 스코프 밖이라
마스터는 손대지 않았다.** 전 분기 스윕(`scripts/_probes/mirae_full_sweep_with_alt.py`,
2023.2Q~2026.2Q 전체)에서 2026.1Q가 check_a/check_b 둘 다 원 단위로 통과
(item6=△7,139.787657) — 원래 라벨로는 후보 0개, ALT로만 매치함을 별도 확인
(`mirae_2026q1_alt_sanity.py`). 코드가 분기별 allowlist 없이 라벨/모양 게이트만 쓰는
설계라 이 값 자체는 이미 계산되지만, 이 티켓이 요구한 "각 분기 원문 행 직접 대조"
수준의 검증을 2026.1Q에는 안 했고 티켓 스코프도 "두 분기"로 명시돼 있어 **패치하지
않았다** — `companies.py` 주석에 근거를 남기고 여기 보고만 한다. 2025.4Q는 여전히
check_a 실패로 정상 자기기권(회귀 없음, `_MA_ACT4_ROW`/`_MA_EXP4_ROW_VARIANTS` 둘 다
line=65535라는 의심스러운 매치가 있지만 population check가 걸러 최종 None).

### 2) glob 사각 census (report only — 요청대로 수정은 안 함)

**orchestrator 실측(64/18)과 정확히 일치.** `data/dart/FY*/raw/KR*` 재계산
(`scripts/_probes/glob_blindspot_census.py`):

```
xml/ 하위만(분기보고서 규약) : 64건
최상위만(사업보고서 규약)    : 313건
둘 다                      : 18건
둘 다 없음(zip-only 등)     : 43건
총 회사-필링 디렉터리        : 438건
```

**`build_net_income_breakdown.py:550`은 실제 버그이나, 현재 라이브 파이프라인이 아니다.**
근거 4가지:
1. `main()`을 호출하는 곳이 저장소 전체(`archive/` 제외)에 **0건**. `if __name__ ==
   "__main__": main()`으로만 실행 가능한 순수 CLI 스크립트다.
2. `scripts/pl_breakdown/{common,companies}.py`가 이 모듈을 임포트하긴 하지만 **`to_num`
   헬퍼 함수 하나뿐**(순수 문자열→숫자 파서, raw XML과 무관) — 이게 지문 게이트가
   `build_net_income_breakdown.py`를 `pl_breakdown` spec의 code_files에 넣는 이유이지,
   `main()`이 돈다는 뜻이 아니다.
3. 산출물 `data/dart/viz/net_income_breakdown.json`의 **마지막 git 커밋이 2026-06-07**
   (오늘 기준 84일 정체) — FY2025_Q2~FY2026_Q2 전체가 반영 안 된 채다.
4. 유일 소비자 `scripts/_build_lob_cross_check.py`도 **자기 자신 외 어디서도 호출되지
   않고**, 2026-05-31 최초 WIP 커밋 이후 한 번도 안 바뀌었다(`docs/LESSONS_2026-06-07.md`
   참조 1건뿐, 실행 계보 없음) — dead-end 체인.

그래도 "쓰인다면 몇 건" 실측은 했다(`scripts/_probes/net_income_breakdown_glob_impact.py`,
SONBO 11사 = 이 스크립트의 전체 대상 범위):

```
_resolve_raw_dirs 발견 dir: 149개
per_dir 생존 엔트리(더 심각한 별개 버그로 걸러진 후): 48개
  -- collision으로 사전 폐기: 101개(!)  <- xml/ 사각보다 훨씬 큰 원인
현재 glob(top-level+extracted/)으로 xml 0건인 엔트리: 4개
  중 실제로 xml/ 하위에 XML이 있는 것(보고된 사각): 3개
  중 진짜 결측(zip-only)인 것: 1개
```

**101개 사전 폐기가 무엇인가**: 분기 디렉터리명(`KR0008_삼성화재해상보험` 등)에는
rcept가 안 붙어 `per_dir = {os.path.basename(d).split("_")[-1]: d for d in dirs}`의
key가 **회사명 하나로 충돌**한다 — 딕셔너리 덮어쓰기라 사전순 마지막(=가장 최근 분기) 1개
빼고 전부 조용히 사라진다(11사 중 9사가 14개 dir→4개 key, 즉 10개씩 폐기). **`xml/` 사각은
이 사전-존재 버그에 가려진 훨씬 작은 2차 문제**다 — 이 스크립트를 realistically 고치려면
두 버그를 같이 봐야 한다.

xml/ 사각이 실제로 걸리는 3건: 현대해상 FY2023_Q4, 코리안리 FY2023_Q4, 코리안리
FY2024_Q4 — 주의: 이 셋은 디렉터리명에 rcept suffix가 붙은 "연차(사업보고서)" 명명인데도
XML은 `xml/` 하위에 있는 **명명규약의 예외 케이스**다(순수 분기 규약 위반이 아니라
사업보고서인데도 xml/를 쓴 경우). 하나손해보험 FY2026_Q2는 xml/도 없는 진짜 zip-only
결측.

**같은 glob 패턴이 딱 한 곳 더 있다**: `scripts/build_equity_composition_tier2.py:708-711`
(`glob(f"{d}/*_00760.xml")` → `glob(f"{d}/*.xml")`만, `xml/` 미커버). 단 이 스크립트도
다운스트림 전체(`emit_equity_composition_provenance.py`·`fill_equity_item10_notes.py`·자체
골든 테스트)가 2026-08-14에 `archive/2026-08_equity_composition/`로 이미 옮겨졌고
(`IFRS17_BS.json`이 유일 17BS 마스터라는 기존 결정과 일치, project memory
`project_ifrs17_bs_sole_master`), 이 스크립트를 호출하는 곳도 0건 — `build_net_income_
breakdown.py`와 같은 "dormant" 분류다.

**다른 라이브 경로는 이 패턴이 아님을 확인**(`grep -rn "\.xml['\"]" | grep glob\|rglob`로
ifrs17 레인 `scripts/`+`src/ifrs17/` 전수 스캔):
- **이미 안전(명시적으로 `xml/` 커버 또는 재귀 glob)**: `build_csm_waterfall_master.py`
  (2곳, `*.xml`+`xml/*.xml`+`extracted/*.xml`), `build_pl_breakdown.py`의 `_xmls_in`
  (`discover_filings()`가 실제로 쓰는 라이브 소스 — 이게 KR0079 2025.2Q/3Q의 item4/5/9/10
  이 이미 정상 채워져 있던 이유), `build_ifrs17_bs.py`(4곳, `**/*.xml` 재귀),
  `check_csm_coverage.py`, `extract_dart_zips.py`.
- **top-level-only가 설계상 맞음(항상 rcept-suffix "연차" dir만 다룸)**:
  `scripts/_dart_path_helpers.py`의 `annual_raw_dir`(→ `ifrs17_batch_all.py`·
  `ifrs17_ingest_audit_annual.py`가 사용), `ifrs17_batch_sensitivity_fy2025.py`
  (`FY2025_Q4` 하드코딩), `emit_sensitivity_provenance.py`의 `_find_raw`(glob 패턴 자체가
  `*_{rcept}` suffix 매치를 요구해 분기 dir은 애초에 안 걸림), `companies.py`의
  `extract_tier2_aia`(KR0080 전용, AIA는 연 1회 공시사라 `dirs`가 분기엔 비어있음) —
  단 위 3개 예외(현대해상/코리안리)처럼 "연차" dir이 실제로 `xml/`을 쓰는 사례가 존재하는
  건 확인했으니 "완전히 안전"이라 단정하지는 않는다(지금까지 이 4개 경로에서 실제 충돌
  사례는 0건).
- **반대로 `xml/`만 의도적으로 보도록 짜여 있음(해당 없음)**: `ifrs17_batch_historical.py`
  (`extract_dir = out_dir / "xml"`), `ifrs17_promote_history_to_measurement.py`
  (`xml_dir = period_dir / "xml"`).
- **이 패턴과 무관하게 이미 비활성**: `ifrs17_batch_measurement.py`·
  `ifrs17_batch_sensitivity.py`는 `settings.raw_dir`(레거시 `data/dart/raw/` — 지금
  `CORPCODE.xml` 하나만 있는 빈 트리)를 봐서 전량 `no_raw_cache`로 이미 죽어있다(별개
  이유, xml/ 사각과 무관).

**고칠지는 다음 판단** — 요청대로 코드/데이터 수정 없이 실측만 남긴다.

### 3) 반영 + 전수 감사

`data/dart/viz/pl_breakdown_master.json` 서지컬 패치(백업 `.bak_20260829_mirae_2025q2q3`):
item6/item7 × {2025.2Q,2025.3Q} 정확히 4셀 변경(item7은 잔차 흡수, 61st pass와 동일 공식
item7_new=item7_old−item6_new: `1165.706406→−6754.576523` / `−12223.519936→−9869.677728`).
gold override(`data/_gold/user_pl_cells.json`) KR0079 grep 0건 — ABL 함정 재발 없음.

`build_root_masters.build_pl()`(개별함수, `main()` 미실행) 전후 전수 diff
(`scripts/_probes/mirae_2025q2q3_diff_census.py`): 6키 변경(패치 4개 + item6/7 2025.4Q의
**값_당분기만** — Q3→Q4 flow-diff 리플, `_flow_dangi` 설계상 당연한 부수효과, 2025.4Q의
값(YTD) 자체는 불변), non-KR0079 변경 **0건**, 회사 census 36개 불변, row 11546 불변.
`sync_master_xlsx_sheet.py "손익분해PL"` 10셀 동기화(값+값_당분기 8개 + 리플 2개), "11546행
×9열 마스터와 완전 일치" 자체검증 통과.

골든: `tests/test_pl_breakdown_golden.py --update`(빌더 재실행 없음, git-purge 브랜치 회피
— 선례와 동일 근거): sha256_master만 이동, coverage/rows(11546)/company_quarters(356)/
coverage_rows(426)/non_null_values(9994) 전부 불변. 신설 지문 게이트
`validate_golden_input_fingerprints.py`: 실행 전 다른 5개 spec(ifrs17_bs/viz_csm_waterfall/
viz_ifrs17_panels/dividend/post_transition) 전부 `ok` 확인(공유트리 오염 없음) → `--update`
후 `pl_breakdown`만 이동(code_sha256/fixture_sha256/master sha256), 재실행 RED
2(CODE_MOVED+FIXTURE_MOVED)→0(clear).

**전수 항등식 감사**(`scripts/_probes/mirae_2025q2q3_final_audit.py`):
```
항목32 356셀                                                       — 생존 ✓
KR0083 2024.3Q item27 = -265,226.939791 (≈△2,652억)                — 생존 ✓
KR0032 2026.2Q item6  = -10,243.0 (△102억)                         — 생존 ✓
KR0070 item6 2024.4Q = 586.0 / 2025.1Q = -3,591.0                  — 생존 ✓
KR0079 2026.2Q item6 = -18,120.139965 (불변) / item11 = 0.0        — 생존 ✓
KR0079 2025.2Q item6 = 7920.282929 / item7 = -6754.576523          — 신규 ✓
KR0079 2025.3Q item6 = -2353.842208 / item7 = -9869.677728         — 신규 ✓
KR0079 2025.2Q/2025.3Q item11 = 0.0 (그대로)                        — 유지 ✓
```
356개 (회사,분기) 전수 폐쇄식(item3=4+5+6+7, item8=9+10+11+12) 스캔: **7건 미달, 전부
KR0072(4개 분기)·KR0087(3건) — 61st pass가 기록한 것과 완전히 동일한 집합**(1백만원 미만
반올림 잔차, KR0079/이번 패치와 무관 확인). `validate_master_tables.py --no-build` exit
2·RED 2건(`SENSITIVITY_UNIT_SANITY`, 라이나생명·카카오페이손해, PL_breakdown/KR0079와
무관, pre-existing). 오프라인 pytest(`test_deploy_assets`·`test_rule_coverage_manifest`·
`test_identity_tautology`·viz golden 2종·`test_dividend_golden`·`test_master_tables_golden`·
`tests/unit/`·`test_push_gate_wiring`): **199 passed, 1 skipped, 0 failed**(`test_pl_
breakdown_golden.py`는 RUN_PL_GOLDEN 미설정으로 정상 skip).

### 하지 않은 것 (확인)

`index.html`·`IFRS17.html`·`download-survey.js`·`report-widget.js`·`public_exports/` 미수정.
브랜치 `fix/csm-product-segmented-columns` 그대로. `git push`·`git add -A` 없음.
`build_root_masters.py`의 `main()` 미실행(`build_pl()` 개별함수만). `validate_master_
tables.py`는 항상 `--no-build`. xlsx는 `sync_master_xlsx_sheet.py`로만 편집(openpyxl
재저장 없음). item11 미터치(0 유지). 2026.1Q 마스터 미패치(§1 참조).
`build_net_income_breakdown.py`/`build_equity_composition_tier2.py` 미수정(report only).

status: answered (2026.1Q 미패치 판단과 두 dormant 스크립트의 처리 방향은
orchestrator/owner 재확인 필요 — 자기완결 아님).

커밋: `2477b04`
