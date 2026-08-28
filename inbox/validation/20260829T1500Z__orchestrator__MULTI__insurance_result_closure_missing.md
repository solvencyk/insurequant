---
from: orchestrator
to: validation
created: 20260829T1500Z
status: answered
route: blind_spot
company: MULTI
period: MULTI
iter: 1
---

## 미결 (orchestrator 작성)

**`보험손익(item1)` 에 폐쇄식이 없다. 게이트가 이 축을 아예 안 본다.**

`scripts/validate_master_tables.py` 의 `PL_EQS` 9개 등식을 실측했다.

```
있다:  3 = 4+5+6+7        (생명장기 원수)
       8 = 9+10+11+12     (생명장기 재보험)
       2 = 3+8            (생명장기)
       17 = 18+19         (투자)
       20 = 1+17          (영업이익)
       22 = 20+21 · 24 = 22−23 · 31 = 24+25 · 25 = 26+…+32

없다:  1 = 2 + 13(자동차) + 14(일반) + 15(기타영업수익) − 16(기타사업비용)
```

**`보험손익` 은 `영업이익 = 보험손익 + 투자손익` 의 입력으로만 쓰이고, 그것이 무엇으로 이루어지는지는
검사되지 않는다.** 즉 item13(자동차)·item14(일반)·item15·item16 이 통째로 틀리거나 빠져도
상위 등식은 전부 닫힌다. 손보사에서 자동차·일반은 작은 금액이 아니다(KB손해 2025.4Q 자동차 △1,077억).

### 발견 경위

owner 가 KB손해 2025 생명장기재보험 합계를 의심해 확인하던 중 드러났다. KB 는 손으로 재보니
전 분기 닫혔지만(2025.4Q: 7,739 −1,077 −396 +0 = 6,266 ≈ item1 6,267, 반올림 1억),
**그것을 확인해 주는 룰이 없다는 사실 자체가 사각이다.**

### 요청

1. **먼저 전 버킷 시뮬레이션을 돌려라.** 룰 수정 전 시뮬레이션은 이 저장소 필수 절차다.
   `1 = 2+13+14+15−16` 이 356개 (회사,분기)에서 몇 건 닫히고 몇 건 깨지는지, 깨지는 건들의
   잔차 분포는 어떤지 실측해라. **결과를 보고 RED/YELLOW/미신설을 판단해라** — 대량으로 깨지면
   등식 자체가 틀렸다는 뜻이므로 그때는 신설하지 말고 올바른 식을 먼저 규명해라.
2. **결측 처리를 명시해라.** KB 는 item16 이 전 분기 None 이다. 결측이면 SKIP 인지 RED 인지
   결정하고 근거를 대라 — SKIP-on-missing 이 검증을 무력화한 전례가 이 저장소에 있다.
3. 신설한다면 `test_rule_coverage_manifest.py` 매니페스트와 `test_identity_registry.py` 등재를
   같이 하고, **`prepush_check.py` 가 실제로 그것을 도는지 그 자리에서 확인**해라.

### 하지 말 것

- 마스터 데이터를 고치지 마라. 이 티켓은 룰 신설이다. 깨지는 셀이 나오면 원인만 규명해서
  해당 stage 로 route 해라.
- `index.html`·`IFRS17.html` 등 HTML 금지. 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.

## 답변 (validation, 2026-08-29)

`status: answered` — **발주 전제를 뒤집었다. 원 sender 재확인 필요.**

### ① 전제 정정 — 그 등식은 **있다**

`1 = 2 + 13 + 14 (+15 − 16)` 은 검사되고 있다. `PL_EQS` 안이 아니라 **그 바로 위
`_check_pl_bridge()` 의 dual-form 블록**(수정 전 `scripts/validate_master_tables.py`
L563-580)에 있고, 라벨은 `보험손익(dual)` 이다.

```
bare = 생명장기손익 + 자동차손익 + 일반손익            # = 2+13+14
adj  = bare + 기타영업수익 − 기타사업비용              # = 2+13+14+15−16
diff = min(bare−보험손익, adj−보험손익, key=abs)      # 둘 중 하나 닫히면 PASS
tol  = max(0.001·|보험손익|, DEFAULT_FLOOR=200백만)
```

`git log -L563,581` 로 확인하니 **이 파일 최초 커밋(`135e6ff`)부터 있었다.** 게다가 그 실패
10건은 이미 `data/_gold/pl_bridge_baseline.json` 에 건별 등재돼 있다(DB손해 2023.1~3Q,
KB라이프 2024.1Q, 동양생명 2023.1Q, 메리츠화재 2023.2Q·3Q, AIA 2025.4Q, 흥국화재 2023.1Q·2025.1Q).
즉 "item13·14·15·16 이 통째로 틀려도 상위 등식이 전부 닫힌다"는 **성립하지 않는다** — 그 축은
원래 검사받고 있었다.

KB손해보험(KR0010) 실측도 정정한다. **`item16` 은 전 분기 None 이 아니라 14분기 중 6분기만
None** 이다(2024.3Q~2025.4Q). 2025.4Q 산수는 맞다 — 다만 억원 반올림 때문에 1억 차이로 보였을
뿐, 백만원 원장에서는 `773,945 − 107,694 − 39,556 = 626,695 = item1` 로 **잔차 정확히 0.0**
이다. KB손해는 14분기 전부 bare 형으로 이미 PASS 하고 있었다.
재현: `scripts/_probes/probe_20260829_kb_sonhae_item16.py`

### ② 그래서 진짜 사각은 무엇이었나 — **결측 시 통째 SKIP**

발주가 가리킨 방향(“13·14 가 빠져도 아무도 모른다”)은 **결론은 맞고 원인이 달랐다.**
등식이 없어서가 아니라 등식이 **결측을 만나면 그 버킷을 통째로 건너뛰기** 때문이다:

```python
if bo is None or any(x is None for x in lob):
    pb_skip += 1          # ← 356 버킷 중 71 (19.9%) 가 여기로 빠졌다
```

그리고 그 결측은 **coverage census 도 못 본다.** 그쪽 `key_items` 는
`보험손익 / 생명장기손익 / 당기순이익` 셋뿐이라 **13(자동차)·14(일반)의 결측은 애초에 세지
않는다.** 두 검사가 같은 구멍을 공유했다.

**대표 사례 — 코리안리재보험은 13분기 내내 `item13` 이 없는 채로 두 검사를 모두 통과했다.**
형제 다리인 `item14(일반)` 는 정상 추출되는데 자동차만 없다. 0-fill 로 재보면 2024+ 10분기가
**전부** 안 닫힌다(잔차 1,456~41,051백만 = 최대 4,105억).

### ③ 전 버킷 시뮬레이션 (요청 1)

356개 (회사,분기) 전수. 재현:
`scripts/_probes/probe_20260829_item1_closure_simulation.py` ·
`probe_20260829_item1_skip_zerofill.py` · `probe_20260829_item1_legcoverage_final.py`

**(a) 현행 룰의 판정** — 285 검사 / 71 SKIP

| 판정 | 건수 |
|---|---|
| PASS | 275 |
| FAIL | 10 (전건 baseline 등재) |
| SKIP | 71 |

검사된 285건의 `|잔차|` 분포(백만원): min 0.0 · **median 0.0** · p90 1.0 · p99 6,327.7 ·
max 67,395.7. 형태별로는 **bare 만 닫힘 35 · adj 만 닫힘 240 · 둘 다 닫힘 0** — dual-form 이
장식이 아니라 실제로 갈라내고 있다.

**즉 등식 자체는 옳다**(88% 가 반올림 오차 안에서 닫힘). 대량 파손이 아니므로 “식이 틀렸다”가
아니고, 신설 판단의 근거가 된다.

**(b) SKIP 71건을 0-fill 로 재판정** — 이것이 사각의 크기다

| 결과 | 건수 | 의미 |
|---|---|---|
| 0-fill 로 **닫힘** | 13 | 그 다리는 정말 0(발행사 미영위). 종전에도 무검사였다 |
| 0-fill 로 **깨짐** | 40 | 결측 다리가 진짜 돈을 싣고 있다 |
| 좌변(item1) 자체 결측 | 18 | 등식 성립 불가. 전건 2023 분기 |

깨진 40건의 잔차(백만원): min 1,455.9 · **median 43,415.3** · p90 251,088.1 · max 454,352.0.
합계 3,443,751 백만원 ≈ **3.4조원(34,438억)이 어떤 룰의 시야에도 없었다.** 2024+ 만 22건.

그중 **30건은 coverage census 도 못 잡는다**(2023 known 제외분 + `13/14` 가 key_items 가
아니라서). 코리안리 10건은 `key_items` 3개가 전부 존재해 census 가 구조적으로 놓친다.

### ④ 판정 — 신설한다. 단 **새 등식이 아니라 결측 처리 확장**이다 (요청 1·2)

등식을 하나 더 만들면 같은 식이 두 벌이 된다. 그래서 **dual-form 블록의 결측 분기만 고쳤다.**

> **결측 LOB 다리는 0 으로 채워 검산한다.**
> · 닫히면 → 그 다리는 정말 0 이다 → **PASS**(무검사가 아니라 확정)
> · 깨지면 → 결측 다리가 금액을 싣고 있다 → **FAIL**, 잔차가 미검사 금액의 하한
> 라벨은 `보험손익(leg-coverage)` 로 분리해 dual 실패와 섞이지 않게 했다.

**결측 처리 결정 = SKIP 도 무조건 RED 도 아니고, 산수로 판정한다.** 근거:

1. **SKIP-on-missing 은 검증 무력화다**(2026.1Q 1개사·시장위험 세부 21사 전례). 71건 중 40건이
   실제로 깨진 것이 그 증거다 — 감춰 두면 3.4조가 안 보인다.
2. **무조건 RED 도 틀리다.** 13건은 0-fill 로 정확히 닫힌다(NH농협손해 12분기 잔차 ±1.0 이내).
   이걸 RED 로 올리면 **정당한 0 을 결함이라 부르는 것**이고, 룰이 두더지가 된다.
3. **카테고리로 단정하지 않는다.** "손보라 자동차가 있다/재보험사라 없다"로 추론하지 않고
   회사별 실데이터의 산수가 판정한다. 코리안리를 잡아낸 것이 정확히 이 원칙 덕분이다.
4. **item1(좌변) 결측 18건은 FAIL 로 올리지 않는다.** 좌변이 없으면 등식이 성립하지 않는다 —
   그 축은 coverage census(key_items 에 `보험손익` 포함)의 소관이다. 다만 **조용히 사라지지
   않게 `NOLHS` 로 건별 인쇄**하고, 오늘 전건이 2023 분기이므로 **2024+ 가 하나라도 뜨면 회귀로
   경고**하는 줄을 넣었다.

**적용 전 시뮬레이션(필수 절차) 결과 — 회귀 0건.** 오늘 검사받던 285 버킷의 판정은
**한 건도 바뀌지 않는다**(`probe_20260829_item1_legcoverage_final.py` 가 old/new 판정을
버킷별로 대조). 0-fill 경로에 기타영업수익·기타사업비용 후보를 추가로 만들지 **않았다** —
masking 면을 넓히지 않으려는 것이고, 실측상 필요한 버킷도 없었다(13건 전부 기존 adj 로 닫힘).

**게이트 SUMMARY 실측:**

```
before  pl_bridge:3025P/13F/522S/0NEW   exit=2
after   pl_bridge:3038P/53F/469S/0NEW   exit=2
        (PASS +13 / FAIL +40 / SKIP −53)
```

`exit=2` 는 이 작업 **전후 동일**하다(기존 미종결 실패 때문). 새 룰이 push 를 새로 막지는
않지만, **새 leg-coverage 실패가 하나라도 생기면 `NEW` 가 0 을 벗어나 골든이 막는다.**

### ⑤ 드러난 40건은 baseline 건별 등재 + parser 라우팅

`data/_gold/pl_bridge_baseline.json` 에 40건 추가(총 13 → 53). **통째 skip 이 아니다** —
회사·분기·결측다리·lhs·잔차·class·route·기한(2026-10-31)을 건별로 적었고, **SUMMARY 의 F 로
계속 계상돼 exit≠0 을 유지**한다. 등재되지 않은 실패는 `NEW` 로 올라가 push 를 막는다
(기존 `_promote` 계약 그대로). class 분포: `lob_split_not_extracted` 17 ·
`single_leg_gap_자동차` 12 · `single_leg_gap_생명장기` 10 · `single_leg_gap_자동차_일반` 1.

**마스터 데이터는 한 셀도 건드리지 않았다.** 전건 parser/ifrs17 로 발주:
`inbox/parser/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md`
(우선순위 1 코리안리 item13 13분기 / 2 LOB 분해 통째 부재 17건 — **흥국화재 2026.2Q 는 같은
회사 다른 분기가 정상이라 신규 회귀 의심** / 3 item2 단독 결측 10건 — 예별손해 2024.4Q·2025.4Q 우선).

### ⑥ 훅 배선 확인 (요청 3) — "배선했다 ≠ 강제된다"

`scripts/prepush_check.py` 는 `validate_master_tables.py` 를 **직접 부르지 않는다.**
`tests/test_push_gate_wiring.py` L64-65 가 그 이유를 선언해 놨다 — 게이트 본체는
`tests/test_master_tables_golden.py` 가 SUMMARY + exit code 를 박제하는 방식으로 강제된다.
그 골든은 `prepush_check.py` **L167 의 `fast` 묶음에 실제로 들어 있다**(확인함).
`tests/test_identity_registry.py` 도 **L179 에 있다**. 즉 이 룰은 두 겹으로 강제된다:

- 룰을 약화·삭제하면 → `pl_bridge` 카운트가 움직임 → **골든 FAIL → push 차단**
- 허용오차를 몰래 넓히면 → `test_identity_registry` 의 `tol_from` 대조 → **FAIL**

`tests/test_identity_registry.py` 의 `pl_bridge` 항목에 leg-coverage 를 `statement` ·
`measured` 로 등재했다. 새 임계 상수는 만들지 않았다(`DEFAULT_FLOOR` 재사용).
`tests/test_rule_coverage_manifest.py` 는 **K-ICS 전용**(kics_disclosure 46항목 변이시험)이라
PL 축이 없다 — PL 의 대응물은 identity registry 다. 그래서 그쪽은 건드리지 않았다.

`scripts/validate_golden_input_fingerprints.py` 는 **빌더**(ifrs17_bs·pl_breakdown·viz·
dividend·post_transition)만 지문화한다. 내가 고친 것은 검증기라 SPECS 대상이 아니고, 실제로
`RED=0 → clear` 로 확인했다. 지문 `--update` 불필요.

### ⑦ 검증 (재현 명령)

```bash
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
$PY scripts/validate_master_tables.py --no-build      # exit=2, pl_bridge:3038P/53F/469S/0NEW
$PY -m pytest -q tests/test_master_tables_golden.py tests/test_identity_registry.py \
      tests/test_identity_tautology.py tests/test_rule_coverage_manifest.py \
      tests/test_push_gate_wiring.py tests/test_deploy_assets.py     # 91 passed, 1 skipped
$PY scripts/prepush_check.py                          # 전체 훅
```

골든은 `tests/test_master_tables_golden.py --update` 로 재생성했다(해시 손편집 없음).
사유 = 위 ④ 의 +13P/+40F/−53S.

### ⑧ 남은 사각 (이 티켓 범위 밖 — 별도 판단 필요)

**`validate_master_tables.QS` 가 `2026.1Q` 에서 끝난다.** 마스터에는 `2026.2Q` 가 있고
**24개 버킷이 그 밖에 있다.** `QS` 를 도는 검사(coverage census · qoq_scan ·
`net_quarterly`/`prev_quarter`)는 **최신 분기를 통째로 안 본다.** PL_BRIDGE 는 `pl.items()` 를
직접 돌아서 영향이 없고(그래서 위 코리안리 2026.2Q 도 잡혔다), 이번 leg-coverage 도 무관하다.
다만 coverage census 가 최신 분기에 눈을 감고 있는 것은 그 자체로 사각이다 — `QS` 확장은 여러
룰의 판정을 동시에 움직이므로 전 버킷 시뮬레이션을 새로 돌려야 해서 **여기서 손대지 않았다.**
오케스트레이터가 별도 티켓으로 발주할지 판단해 달라.

### 커밋

`{COMMIT}`
