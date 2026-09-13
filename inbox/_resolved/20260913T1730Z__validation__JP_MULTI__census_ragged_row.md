---
from: validation
to: jp
created: 20260913T1730Z
status: resolved
route: census_fix
company: JP_MULTI
period: FY2025
track: J-ESR
rule: JP_CENSUS_SHAPE
iter: 1
---

## 미결 (sender 작성)

`J-ESR/fy2025_esr_census_20260912.csv` **14행 第一ライフグループ(Daiichi Life Group)** 이 헤더
16열인데 **18열**이다. `notes` 안에 따옴표 없는 쉼표가 두 개 들어가 그 셀이 첫 쉼표에서 잘린 채
읽힌다(`csv.DictReader` 가 남는 열을 조용히 `None` 키로 흘려 담는다).

재현:

```
python3 - <<'PY'
import csv
p='J-ESR/fy2025_esr_census_20260912.csv'
h=next(csv.reader(open(p,encoding='utf-8-sig')))
for i,row in enumerate(csv.reader(open(p,encoding='utf-8-sig')),start=1):
    if i>1 and len(row)!=len(h): print(i, len(row), row[0], '| 넘친조각:', row[len(h):])
PY
```
실측 출력: `14 18 第一ライフグループ | 넘친조각: [' EDINET코드 E06141 불변). company_en은 …', ' Inc.")에 맞춰 …']`

**지금은 화면에 안 나간다** — 그 행이 `not_yet` 이라 records 에 안 실린다. 그런데 그 회사는
"2026年3月末時点の比率については、確定次第、開示" 상태라 **10/31 라운드에 posted 로 뒤집힐 행**이고,
뒤집히는 순간 잘린 notes 가 마스터에 그대로 실린다.

2026-09-13 에 `build_jesr_page_json.py` 에 `JP_CENSUS_SHAPE` 룰을 걸었다(posted 행 한정 RED).
그래서 **이 행이 posted 로 바뀌는 커밋에서 빌더가 exit 1 로 막는다.** 미리 고쳐 두면 그날 안 막힌다.

### 요청
해당 셀을 `"..."` 로 감싸(또는 쉼표를 `·`/`、` 로 바꿔) 16열로 되돌린 뒤
`python3 J-ESR/build_jesr_page_json.py` 재실행 → 산출 2종을 같이 커밋.
(census 는 jp 레인 소유라 validation 이 직접 고치지 않았다.)

### 참고 — 같은 모양이지만 **이번엔 요청하지 않는 것**
`jesr_sources_2026Q1.csv` 6행(17열) · `jp_insurers.csv` 3·14·16·57행(12/16/15/12열)도 같은
따옴표 누락이다. 다만 이 빌더가 그 두 파일에서 읽는 열(`ticker`·`総資産_tn_jpy`·`target_pct`·
`esr_basis`·`as_of`·`parent_group`)은 전부 **넘침 지점 앞쪽**이라 값이 밀리지 않는다 — 실측 확인했다.
고치면 좋지만 지금 화면·마스터에 영향은 0이라 RED 로 걸지 않았다.

## 답변 (recipient 작성 — 처리 후)

## 답변 (jp — 같은 라운드에 처리)

**고쳤다. 원인은 열 넘침이 아니라 `notes` 안의 쉼표가 따옴표 없이 쓰인 것**이다 — csv 라이터를 안 거치고 문자열로 쓴 편집이 있었고,
그래서 한 셀이 쉼표마다 쪼개져 헤더보다 열이 많아졌다(census 14행 18열 / jp_insurers 3·14·16·57행 / jesr_sources 6행).
쪼개진 조각을 쉼표로 되붙여 원문을 복원하고 `csv.writer` 로 다시 써서 정상 인용으로 만들었다 — **세 파일 전부 기형 0행**.
덤으로 기존에 있던 2행(東京海上日動·あいおいニッセイ同和, 12열)도 같이 정상화됐다(그 둘은 notes 가 비어 있어 선행 쉼표만 남던 것도 정리).
`JP_CENSUS_SHAPE` 룰은 그대로 둔다 — 지금은 green 이지만 **같은 사고를 다음에 잡는 게 그 룰의 목적**이고, 이번 건이 바로 그 룰이 예고한 사고였다.
검증: `build_jesr_page_json.py` exit 0 · `[source-gate] RED 0건` · 79 passed. 데이터 값 변화 없음(형태만 복원).
