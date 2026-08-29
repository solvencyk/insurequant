---
from: orchestrator
to: parser
created: 20260829T2330Z
status: resolved
route: reparse
company: KR0005,KR1000,KR0032
period: MULTI
lane: ifrs17
iter: 1
---

## 미결 (orchestrator 작성 — census 후속)

**빈칸 압축 지뢰 3건을 제거한다.** 선행 census(`20260829T2200Z`)가 383개 회사-분기를
실측해 확정한 결과다.

```
확정 오염 2건 (둘 다 이미 수정됨)
  흥국화재 KR0005 2026.2Q      fb9c9bf 로 오늘 수정
  악사손해 KR0049              이전에 전용 핸들러로 수정 (그 docstring 이 과거 사고를 증언)

근접-미스 3건 (미수정 — 이 티켓 대상)
  KR0005  extract_tier2_heungkuk_single   오늘 패치가 안 간 형제 함수
  KR1000  _coreanre_old.val               노출 idx 가 관측된 대시 위치와 겹침
  KR0032  _nh_gmm_incurred4               이미 고친 _nh_gmm_re_incurred 의 미패치 쌍
```

### 왜 지금 고치나

**이 부류는 전에도 물었고, 그때 그 회사만 임시로 고치고 일반화를 안 해서 오늘 또 나왔다.**
악사 핸들러의 docstring 이 그 증거다. 세 건 다 "아직 안 맞았을 뿐 구조가 같은" 상태다.
빈칸 하나가 생기는 시점은 우리가 통제할 수 없다 — 다음 분기 원문에서 언제든 생긴다.

그리고 이 부류는 **잡히기 어렵다.** 라벨은 다 맞고 표도 하나뿐이라 오늘 쓴 세 탐지법이
전부 통과한다. 흥국화재는 값이 55배 튀어서 우연히 잡혔고, **밀림이 작으면 폐쇄식도 닫힌다.**

### 요청

1. **세 함수를 raw 인덱싱으로 재작성해라.** 이미 고쳐진 짝(`_nh_gmm_re_incurred`,
   `extract_tier2_heungkuk` 의 `totrow()`, 악사 전용 핸들러)이 참조 구현이다. **같은 방식을
   쓰고 새 방식을 발명하지 마라.**
2. **회귀 검증이 이 티켓의 핵심이다.** 세 회사 전 분기를 전수 스윕해서 **바이트 단위 무변화**를
   확인해라. 값이 하나라도 바뀌면 그건 지금까지 틀렸던 것이거나 네 수정이 틀린 것이다 —
   어느 쪽인지 원문으로 가려서 보고해라. gold-validated 분기는 특히 주의.
3. 선행 census 의 재현 하네스가 스크래치패드에 있다(`census_row_nums_blank.py`, 오프라인
   ~150초, 마스터 무변경). **수정 후 그것을 다시 돌려 노출 지점이 줄었는지 확인**하고 결과를 보고해라.
4. 마스터 값이 안 바뀌면 골든·지문 갱신은 불요다. 바뀌면 이유를 대고 갱신해라.

### 하지 말 것

- **`_row_nums()` 자체를 고치지 마라.** 파급 범위가 크고 이 티켓 범위 밖이다. 호출부만 고친다.
- 값이 바뀌는데 이유를 모르면 **커밋하지 말고 보고해라.**
- `kics_disclosure.json`·`data/disclosure/` 금지. `index.html`·`IFRS17.html`·`public_exports/` 금지.
- `scripts/validate_*`·`prepush_check.py`·`_quarter_horizon.py` 금지.
- 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.

## 답변 (recipient 작성 — 처리 후)

**세 함수 전부 참조 구현(위치보존 raw 인덱싱, 빈칸/대시→그 자리 0.0)으로 재작성 완료.
`scripts/pl_breakdown/companies.py`만 수정(3개 함수, `_row_nums()` 자체는 무수정).
42개 filing(3사×14개 분기) 전수 스윕 결과 t1·t2 출력 **바이트 단위 완전 무변화** —
KR1000의 실제 빈칸 관측 3개 분기·KR0032의 실제 라이브 11개 분기 포함. census 재실행:
distinct call sites 13→12, dense-candidate 434→362(-72, 전부 KR1000 val 소거분).**

### 1. 세 함수를 어떻게 고쳤는지

| 회사 | 함수 | 이전 | 이후 |
|---|---|---|---|
| KR0005 | `extract_tier2_heungkuk_single.totrow()`(companies.py:1350) | 라벨매칭 후 `ns=_row_nums(r)`를 그대로 반환 | 라벨매칭(행 선택)은 그대로 `_row_nums(r)` truthy 게이트 유지, **반환값만** `[to_num(c) if to_num(c) is not None else 0.0 for c in r[1:]]`(위치보존)로 교체 — `extract_tier2_heungkuk.totrow()`(fb9c9bf)와 100% 동일 패턴 |
| KR1000 | `_coreanre_old.val()`(companies.py:1500 근방) | `ns=_row_nums(r); if ns and len(ns)>idx: return ns[idx]` | `_row_nums()` 호출 자체를 제거, `if len(r) > 1+idx: return to_num(r[1+idx]) or 0.0`로 직접 raw 인덱싱 |
| KR0032 | `_nh_gmm_incurred4()`(companies.py:1948) | `ns=_row_nums(r); if len(ns)<5: return None; excl_lc,...,_total = ns[:5]` | `_nh_gmm_re_incurred`(item11)와 동일하게 `if len(r)<6: return None` + `r[1:6]`을 `to_num()`으로 개별 변환(빈칸→0.0) |

세 곳 다 diff는 `git diff scripts/pl_breakdown/companies.py`에 있음(각 함수에 근거·census
인용을 단 인라인 주석 포함).

**KR0005 스코프 결정 — `jang()`은 안 고쳤다.** `extract_tier2_heungkuk_single`에는
`totrow()`(라벨이 정확히 1칸, col0..4 EQUALITY 매칭) 말고 `jang()`(라벨이 최대 3칸에
걸쳐 있을 수 있는 SUBSTRING 매칭, `r[0]+r[1]+r[2]` 연결)도 있는데, 이건 안 건드렸다.
이유: (a) census가 실측으로 짚은 노출 콜사이트는 정확히 `companies.totrow:1356` 하나뿐 —
`jang()`은 13개 콜사이트 목록에 없다. (b) 오늘 이미 고쳐진 참조 구현(`extract_tier2_
heungkuk.totrow()`, fb9c9bf)도 형제 함수 `comp()`(=`jang()`과 같은 다중칸 라벨 SUBSTRING
매칭 패턴)는 그대로 두고 `totrow()`만 고쳤다 — 같은 경계를 그대로 따랐다. (c) `jang()`은
라벨이 실제로 몇 칸에 걸치는지 행마다 달라 "라벨 다음 N칸부터 데이터"라는 고정 스킵값을
정할 근거가 없다 — `r[1:]`로 무조건 자르면 라벨이 2~3칸째까지 이어지는 행에서 데이터를
빼먹는 새로운 버그가 된다. 참조 구현이 없는 새 방식을 발명하는 셈이라 발주 지시("새 방식을
발명하지 마라")에 어긋난다. `jang()`은 여전히 열려 있는 노출이지만 이번 티켓 범위 밖으로
보고한다(§5).

### 2. 회귀 검증 — 바이트 단위 무변화 (핵심 산출)

**방법**: `build_pl_breakdown.discover_filings()` + `parse_filing()`을 그대로 호출(census
하네스와 동일한 read-only 경로, `main()` 미호출, 마스터 미쓰기)해 KR0005/KR1000/KR0032
**3사 × 14개 분기(2023.1Q~2026.2Q) = 42 filing 전부**의 `(t1, t2)`를 패치 전/후 각각 JSON
스냅샷으로 캡처하고 `diff -q`로 대조.

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe <스크래치패드>/verify_three_fn_regression.py <out.json>
```

결과:
```
$ diff -q three_fn_before.json three_fn_after2.json
(무출력 = 바이트 단위 완전 동일, 60,346 bytes 양쪽 동일)
```

개별 확인:
- **KR0005·KR1000·KR0032 각각 "ALL 14 quarters identical: True"** (t1+t2 딕셔너리 값
  비교, dict 재귀 `==`).
- **KR1000 2023.3Q/2024.2Q/2024.3Q** — census가 지목한, `_coreanre_old.val()`이 실제로
  대시를 만난 바로 그 3개 분기. 패치 전/후 `t2` 완전 동일(예: 2023.3Q item4=63815.0,
  item14=132288.0, `_extra_items` 11개 항목 전부 동일값) — idx=5("일반")가 아니라
  idx=1/3("장기"/"생명")만 읽는 호출들이라 대시를 실제로 밟지 않았다는 census의 판정이
  코드 레벨에서도 확인됨.
- **KR0032 전 분기** — `_nh_gmm_incurred4`는 2023.4Q~2026.2Q 11개 분기에서 item6이
  실제로 non-null(예: 2026.2Q=-10243.0)로 살아있는 라이브 경로. 11개 분기 전부 패치
  전/후 값 무변화 — 빈칸을 한 번도 안 만났지만(census 노출 0건과 일치) 로직 자체는
  등가임을 확인.
- **KR0005 2026.1Q/2026.2Q** — census가 지목한 실제 빈칸 관측 지점(`totrow:1356`,
  2026.1Q `blanks_at=[2]`/`[2,3]`). item4~14 전부 패치 전/후 무변화(2026.1Q item13=
  -11182.0, 2026.2Q item13=-16656.0 — fb9c9bf가 이미 고친 값 그대로, 이번 패치로도
  안 흔들림).

**골든/지문 갱신 불요** — 마스터 값이 그대로이므로(발주 지시 §요청 4). `git status`로도
확인: 이번 세션에서 수정된 추적 파일은 `scripts/pl_breakdown/companies.py` 단 하나뿐,
`PL_breakdown.json`/`data/dart/viz/pl_breakdown_master.json`/xlsx 전부 무변경.

**골든 게이트(`RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py`)는 의도적으로
미실행.** 그 게이트는 `build_pl_breakdown.py`를 처음부터 다시 돌려 마스터를 재생성하는데,
이 브랜치는 raw가 git-purge된 이력이 있어(SKILL "destructive rebuild" 트랩) 전체 재빌드
자체가 위험 신호로 분류돼 있다. 지금 작업트리엔 39개사 raw가 실제로 다 있어 재빌드가
안전할 가능성이 높지만, 이번 변경은 KR0005/KR1000/KR0032 세 함수로 완전히 스코프가
닫혀 있고 위 42-filing 스윕이 그 세 함수의 유일한 소비 경로(`parse_filing`)를 통째로
커버하므로, 전체 재빌드보다 이 스윕이 **더 정밀한 증거**다. 마스터가 실제로 안 바뀌었다는
것도 이미 확인했으니 골든 재실행의 한계 편익이 이 브랜치 특유의 재빌드 리스크를
정당화하지 못한다고 판단해 스킵했다.

### 3. census 재현 결과 — 노출 지점 변화

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe <스크래치패드>/census_row_nums_blank.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe <스크래치패드>/analyze_census.py
```

| 지표 | 패치 전 | 패치 후 |
|---|---|---|
| total log entries | 9,664 | 9,448 (−216) |
| dense-row/small-gap candidates | 434 | 362 (−72) |
| distinct call sites | 13 | 12 (−1) |

**`KR1000 companies.val:1489` (72 candidate entries, 216 raw log entries) 완전 소거** —
유일하게 사라진 콜사이트. `_row_nums()` 호출 자체를 제거했으므로 몽키패치 계측기가 더
이상 이 지점을 볼 수 없다(정확히 이전 census가 이 콜사이트에 붙였던 entry 수와 일치).

**`KR0005 companies.totrow:1356`(heungkuk_single)은 패치 후에도 여전히 census에
나타난다** — `blanks_at=[2]`/`[2,3]`(2026.1Q)·`blanks_at=[5]`(2026.2Q, wide-form 스침)
그대로, 정확히 패치 전과 동일. **이건 예상된 결과이지 미수정이 아니다**: 이미 고쳐진
참조 구현 `KR0005 companies.totrow:1090`(=`extract_tier2_heungkuk`, fb9c9bf)도 census가
`row_len=17, blanks_at=[5]`로 계속 잡는다(둘 다 행-선택 게이트로 `_row_nums(r)` truthy
체크를 그대로 남겨뒀기 때문 — 기계식 계측기는 "호출됐다"만 보지 "반환값을 실제로
위치기반으로 소비하는가"는 모른다). 진짜 판정 기준은 §2의 바이트 무변화 스윕이다 —
2026.1Q의 관측된 빈칸이 이번 패치로 실제 계산 경로에서 위치보존으로 처리됐음을
값 레벨에서 확인했다.

**`KR0032`(_nh_gmm_incurred4)는 패치 전/후 둘 다 census 후보 목록에 없다** —
처음부터 노출 0건(§2에서 확인했듯 11개 분기 라이브인데도 빈칸을 한 번도 안 만남).
이 함수는 "관측된 근접-미스"가 아니라 "이미 고쳐진 형제와의 구조적 비대칭 제거"였다.

### 4. 하지 않은 것 (지시 준수 확인)

`_row_nums()` 자체 미수정. `kics_disclosure.json`·`data/disclosure/`·`index.html`·
`IFRS17.html`·`public_exports/`·`scripts/validate_*`·`prepush_check.py`·
`_quarter_horizon.py` 미접근. 브랜치 그대로(`fix/csm-product-segmented-columns`).
`git push`·`git add -A` 없음(파일 3개만 명시적으로 스테이징 예정: `companies.py` +
이 티켓 + `TODO_parser_ifrs17.md`). `build_root_masters.py`/`build_pl_breakdown.py`의
`main()` 미실행. openpyxl로 xlsx 재저장 없음(xlsx 자체를 안 건드림 — 마스터 무변경이므로
sync 대상 없음).

### 5. 후속(발주 범위 밖, 보고만)

- `extract_tier2_heungkuk_single.jang()`(§1에서 설명한 다중칸 라벨 SUBSTRING 매칭)은
  여전히 열린 노출 — `ns[0]`이 첫 데이터 칸이 실제로 빈칸이 되는 날 형제 함수들과 같은
  사고가 날 수 있다. 고치려면 "라벨이 몇 칸을 차지하는지" 행별로 판별하는 새 방식이
  필요해 이번 참조-구현-복사 스코프를 벗어난다.
- `extract_tier2_heungkuk.comp()`/`cum()`(fb9c9bf가 안 고친 형제, census §2에 이미
  기록)도 동일 계열로 열려 있음 — 오늘 손 안 댐.
- 이 세 가지 다음으로 census §4가 제안한 구조적 탐지(파싱 시점 `len(r)-1` vs
  `len(_row_nums(r))` 대조 로깅)는 여전히 미착수.

status: answered — orchestrator 재확인 대기 (재현 명령·수치 전부 위에 있음)

커밋: `de4e582`

## 답변 追記 — 코디네이터 골든-체크 후속 (2026-08-29)

**결론: 늘어난 값 1개(non_null_values 10006→10007)는 내 3함수 패치와 무관하다 — A/B
재현으로 반증 완료. 원인은 완전히 다른 회사(KR0079) 셀 1개 + 무관한 반올림 잔재(KR0070)
5셀, 둘 다 이 세션에서 처음 발견된 별개 사전존재 드리프트다. KR0070 5셀은 반영(순수
반올림, gold override 무충돌 확인), KR0079 1셀은 데이터계약 게이트가 RED로 반대해서
되돌렸다. 두 게이트(지문·validate_data_contract) 전부 RED=0 확인.**

### 1. "늘어난 값 하나"의 정체 — A/B 재현으로 내 패치 혐의 기각

`python scripts/build_pl_breakdown.py`(골든 테스트가 쓰는 것과 동일 경로, `main()` 직접
호출)를 내 패치본 코드로 2회, **패치 되돌린(`fb9c9bf`) 코드로 1회** 돌려 셋을 서로 대조:

```
패치본 rebuild #1  vs  패치본 rebuild #2   : diff 0건 (결정론적, 확인)
패치 되돌린 rebuild vs  패치본 rebuild #1   : diff 0건  ← 내 3함수 패치가 원인이면 여기서 갈려야 하는데 안 갈림
```

즉 **`_row_nums()` 근접-미스 3함수 패치를 아예 안 하고 돌려도 정확히 같은 드리프트가
난다** — KR0079/KR0070은 KR0005·KR1000·KR0032와 코드 경로가 완전히 분리돼 있고(각 함수는
자기 회사 dispatch 한 곳에서만 호출, 이전 답변 §1에서 이미 확인), 이 A/B가 그걸 실측으로
확정한다. 커밋된 `pl_breakdown_master.json`(11546행)과 fresh rebuild를 (회사,분기,항목번호)
키로 전수 대조하니 **정확히 6개 셀**만 갈렸다:

| 회사 | 분기 | 항목 | committed | fresh rebuild |
|---|---|---|---|---|
| KR0079 미래에셋생명 | 2025.4Q | 6(원수 예실차) | `null` | `0.0` |
| KR0070 에이비엘생명 | 2025.2Q | 7(기타 생명장기 원수손익) | -11399.469519999999 | -11399.46952 |
| KR0070 | 2025.2Q | 12(기타 생명장기 재보험손익) | -72.9970030000004 | -72.997003 |
| KR0070 | 2025.3Q | 12 | 842.7793600000005 | 842.77936 |
| KR0070 | 2026.1Q | 12 | 600.4900280000002 | 600.490028 |
| KR0070 | 2026.2Q | 7 | -99087.56994300001 | -99087.569943 |

KR0070 5개는 **전부 `round(committed, 6) == fresh` 로 수학적으로 완전 동일값** — `main()`이
매 셀에 거는 `round(v[n], 6)`을 거치지 않은 구값이 어딘가 남아 있던 반올림 잔재다(어느
과거 서지컬 패치가 반올림 없이 값을 썼는지는 특정 못 함, 반올림 규칙 위반만 확정).
KR0079는 별개 — item6이 `null`→`0.0`으로 non_null_values를 정확히 +1 시켜, 좌표 하나로
전체 델타를 설명한다(`coverage.json`의 `sha256_coverage` 이동도 이 셀의 status
partial→ok/missing [6]→[] 하나로 전부 설명됨, 아래 §2).

### 2. KR0079 2025.4Q item6 — 원문/코드 추적, 왜 0.0 이 아닌지

**메커니즘은 완전히 규명했다 — 버그는 아니고 두 개의 기존 의도적 규칙이 만나 생긴 부작용.**

`_ma_yesilcha_direct(tables)`를 직접 계측 호출: `t_exp`/`t_act` 둘 다 실제로는 "당기말 및
전기말 현재 **관계종속기업투자주식**의 내역" — 예실차 노트와 무관한 표를 후보로 집는다
(`_ma_find_product_table`의 `line_no` 동점 처리가 진짜 "18-1" 노트 대신 이 표를 고름,
`line_no=65535`=센티널 값인 것도 신호). 그 결과 `rev_lump=None`이라 check A가 정확히
문서화된 대로 **self-abort → return None**(`총 587,701`백만원짜리 exp, `act` 계산하면
366,026.947308 — 1b958d7가 이미 "20~50배 이상치"로 기각한 바로 그 값과 소수점까지 일치,
같은 원인 재확인).

**여기까진 1b958d7의 결론과 100% 일치(회귀 아님). 그런데 그 다음이 다르다.**
`extract_tier2_miraeasset`가 `item6=None`을 반환하면, `build_pl_breakdown.py::assemble()`의
기존 규칙(line 172-174, **owner 2026-06-08 결정, 오늘 이전부터 있던 코드, 내가 안 건드림**):

```python
elif v[3] is not None and v[4] is not None and v[5] is not None and v[6] is None:
    v[6] = 0.0
    v[7] = v[3] - v[4] - v[5]
```

가 "예실차 미공시 시 0으로 표시, 잔차는 기타(item7)로" 라는 **다른 회사들(농협·교보·동양)
용으로 이미 있던 규칙**을 그대로 적용해 `item6=0.0`을 만든다. `assemble()` 전체 벡터를
직접 찍어보면 `_reconciled=True`(RC게이트 통과), item7=-67158.636681이 이미 **패치 전부터
커밋된 값과 정확히 일치** — 즉 이 규칙은 이미 예전에 한 번 발동해서 item7까지는 반영됐는데
item6만 나중에 손으로 `None`으로 되돌려진 흔적으로 보인다(`_GOLD_CELL_OVERRIDE`·
gold-overlay 둘 다 KR0079 항목 0건 확인 — 공식 override 아님).

**되돌린 이유 — 데이터계약 게이트가 정확히 이 셀을 잡았다.** 되돌리기 전 상태로
`validate_data_contract.py`를 돌리니:

```
RED [PL_breakdown] PL_YTD_COLLAPSE_TO_ZERO  미래에셋생명보험 2025.4Q
  원수예실차 누계가 직전분기 -2,353.8 → 이번분기 정확히 0.0
  — FY 누계는 이렇게 사라지지 않는다. 재빌드 결손 의심
```

**이 RED는 옳다.** 농협/교보/동양은 예실차를 아예 한 번도 못 뽑아 매 분기 0.0이 상수라
이 패턴이 안 뜬다. KR0079는 2025.2Q/2025.3Q/2026.1Q/2026.2Q **전부 실제 0 아닌 값**을
뽑는 회사라, 딱 한 분기(2025.4Q)만 표 오선택으로 미공시 취급돼 0.0이 되면 "직전분기
-2,353.8에서 이번 분기 0.0으로 점프"라는, 실제로는 없었던 급변을 만들어낸다.
CLAUDE.md 원칙 "틀린 값을 싣느니 빈 칸" 그대로 — **되돌렸다.**

**그래서 master/coverage/root/xlsx 전부 KR0079 2025.4Q item6=None(원래 상태)으로 유지,
KR0070 5셀만 반영.** `scripts/build_pl_breakdown.py::assemble()`의 해당 분기 규칙 옆에
이 경위를 주석으로 남겨(코드 라인 172 부근) 다음 전체 재빌드 때 같은 혼란이 재발하지
않게 했다 — **주의: 코드를 안 고쳤으므로 다음에 누가 `build_pl_breakdown.py`를 진짜로
전체 재실행하면 이 셀은 또 0.0으로 나온다.** 진짜 근본수정은 `_ma_find_product_table`의
후보표 동점처리(관계종속기업투자주식 표를 걸러내는 캡션/라벨 가드 추가)인데, 이건
KR0079 전담이라 이 티켓 범위 밖 — 후속 필요(§5).

### 3. 적용한 반영 — 셀 단위 패치, combo-diff 검증

`data/dart/viz/pl_breakdown_master.json` 4셀 + `data/_derived/pl_breakdown_coverage.json`
3개 entry(KR0070 2024.1Q/2Q/3Q item11 missing-list 잔재, master 실값은 이미 정상이었던
순수 bookkeeping 오차) 손으로 지정 패치(`git diff` 6줄) → `build_root_masters.build_pl()`
개별 호출(`main()` 미실행) → combo-diff: **11546 키 전후 완전 동일(LOST 0·NEW 0), diff
정확히 4건**(item7×1@2026.2Q + item12×3, 전부 반올림값만) — item7@2025.2Q/2025.3Q는
gold-overlay(`data/_gold/user_pl_cells.json`)가 이미 별도 override 중이라(item4/item7
쌍으로 관리되는 잔차-보정 이력, `build_root_masters.build_pl()`의 `_apply_pl_overrides`가
무조건 덮어씀) 내 raw 반올림 수정이 root에는 애초에 안 보임 — 충돌 없음, 확인 완료.
`sync_master_xlsx_sheet.py "손익분해PL"` cherry-pick(검증 OK, 나머지 시트 무변화).

### 4. 게이트 재확인

```
$ python scripts/validate_golden_input_fingerprints.py
  RED=0 → clear   (6개 스펙 전부 ok — pl_breakdown 포함)

$ python scripts/validate_data_contract.py
  SUMMARY  RED=0  YELLOW=92  provisional=False   (패치 전 베이스라인과 YELLOW 카운트 동일 —
  신규 YELLOW 0건)

$ RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py
  FAILED — non_null_values: 10006 -> 10007 (fresh rebuild는 여전히 KR0079 item6=0.0을
  재생산함 — §2에서 설명한 대로 코드를 안 고쳤으니 당연한 결과). 무거운 골든은 push
  훅에 안 걸려 있어(95초, CLAUDE.md 확인) 차단 안 함 — 알려진 상태로 코드 주석에 기록.

$ python -m pytest tests/ (heavy golden 2종 제외)
  484 passed, 1 skipped, 0 failed
```

### 5. 교훈 (요청하신 부분)

**"값이 안 바뀐다"가 아니라 "드롭되던 0이 살아난다"가 위치기반 파싱 수정의 기대 동작이란
가설은, 이번 구체 사례에서는 틀렸다 — 늘어난 값은 내 수정과 무관한 별개 회사였다.** 더
일반화하면 이번 사고의 진짜 교훈은:

1. **좁은 스코프 회귀검증(3사×14분기 read-only sweep)은 "내 코드가 무해하다"를 증명하는
   데는 완벽하지만, "전체 골든이 통과한다"를 보장하지 못한다** — 골든은 전체 우주(39개사)
   기준이라, 내가 안 건드린 회사의 사전존재 드리프트도 내 코드 변경이 지문의 CODE_MOVED를
   트리거하는 순간 같이 딸려 나온다. 다음에 비슷한 패치를 하면: 좁은 스코프 검증 통과 후
   **전체 골든을 먼저 돌려서** 드리프트가 있는지 확인 → 있으면 A/B(패치 있음/없음)로
   내 코드 탓인지부터 가르는 순서를 스킵하지 말 것(이번엔 이 단계 덕분에 KR0079가 무죄로
   밝혀졌다).
2. **지문 게이트는 산출뿐 아니라 코드 해시도 축으로 잡는다** — 값이 안 바뀌어도 코드가
   바뀌면 지문 갱신 대상. 원 티켓 §요청4("마스터 안 바뀌면 갱신 불요")는 부정확했다(코디네이터
   본인 지적).
3. **자동 게이트(PL_YTD_COLLAPSE_TO_ZERO)가 사람의 추론(코드 추적으로 "0.0이 맞는 것
   같다")보다 더 신뢰할 근거를 가질 수 있다** — 코드 메커니즘을 완전히 이해했다고 해서
   그 산출이 "표시해도 되는 값"이라는 뜻은 아니다. 게이트가 반대하면, 내 추론이 아무리
   그럴듯해도 게이트 쪽을 따르고 보고한다("틀린 값을 싣느니 빈 칸").
4. **셀 패치가 마스터(`pl_breakdown_master.json`)에만 반영되고 루트(`PL_breakdown.json`)엔
   `_additive_merge`의 "fresh가 None이면 기존 값 유지" 안전장치 때문에 안 먹힐 수 있다** —
   되돌리기 작업 중 실제로 걸림(§2). 루트에 이미 반영된 값을 되돌릴 땐 마스터만 고치고
   `build_pl()`을 다시 돌리는 걸로 안 끝난다 — 루트도 직접 패치해야 한다.

### 6. 잔여 (이 티켓 범위 밖, 보고만)

- **`_ma_find_product_table`의 후보표 동점처리 버그**(§2) — KR0079 2025.4Q 한정, "관계종속
  기업투자주식" 표를 예실차 노트로 오인. `line_no=65535` 센티널이 단서. 고치면 item6이
  진짜 값(아마 0.0 아닌 다른 수)으로 채워질 수 있고, 그러면 `PL_YTD_COLLAPSE_TO_ZERO`도
  자연히 안 뜬다 — 근본수정. KR0079 담당 후속 세션 필요.
- `scripts/build_pl_breakdown.py::assemble()` line 172 부근에 이 전말을 주석으로 남김
  (코드 자체는 미수정, 다음 세션이 같은 혼란 없이 바로 맥락을 잡게).

status: answered — orchestrator 재확인 대기 (§1-4 재현 명령·수치 전부 위, KR0079 근본수정은
별도 후속)

커밋(이 후속): `568eebb`
