---
from: validation
to: publishing
created: 20260820T1500Z
status: open
route: escalate
company: MULTI
period: MULTI
lane: ifrs17
iter: 1
---

## 미결 (sender 작성) — 마스터 전수 검증 완료. **배포 가능 판정**, 인계한다

owner 지시(2026-08-20): *"한번 더 마스터 테이블 json들 검증해보고 이상 없으면 배포 세션으로 토스"*.

전수 검증했고 **차단 사유 없다.** 아래가 실측 근거와 배포 전 알아야 할 것 전부다.

---

## 1. 게이트 결과

| 검사 | 결과 | 판정 |
|---|---|---|
| `scripts/validate_data_contract.py` (**prepush_check 가 부르는 그 게이트**) | **RED=0** YELLOW=254 provisional=False · exit **0** | ✅ |
| `scripts/validate_statutory_reserves.py` (신설 R-RSV) | **RED=0** BASELINE=44 ORANGE=43 SUPPRESSED=74 | ✅ |
| `scripts/validate_master_tables.py --no-build` | exit 2, **골든 SUMMARY 문자열과 완전 일치** | ✅ 동결된 기존 상태 |
| `scripts/validate_kics_disclosure.py` | RED=12, **전건 `TODO.md` documented exception** | ✅ 계약 만족 |
| `scripts/validate_csm_continuity.py` | companies=37 flagged=0 **red=0** | ✅ |
| `scripts/validate_nb_csm_multiple.py` | tested=5 **pass=5** fail=0 | ✅ |

> ⚠ `validate_master_tables.py` 는 **반드시 `--no-build`** 로 돌렸다. 기본 동작이
> `build_root_masters` 를 부른다(`[[project-git-purge]]` 8,111행 → 6,636행 사고 전례).

### 골든 8종 전부 통과

```
test_kics_rules_golden · test_master_tables_golden · test_viz_ifrs17_panels_golden
test_viz_csm_waterfall_golden · test_dividend_golden · test_deploy_assets
test_post_transition_golden                                    → 16 passed (12.8s)
test_ifrs17_bs_golden                                          → 1 passed (452s)
```

**`test_ifrs17_bs_golden` 이 이번에 초록으로 돌아온 게 핵심이다.** publishing 이
`20260819T0858Z` 로 stale 이라 올렸던 그 골든이고, parser 가 `--update` 로 재생성해
지금은 산출 6,953행이 해시까지 일치한다. **배포 전 red 로 남아 있던 유일한 골든이 닫혔다.**

---

## 2. 마스터 HEAD 대비 — **셀 손실 0**

```
CSM_waterfall.json     HEAD 와 바이트 동일 (2,136행 / 356셀)
PL_breakdown.json      HEAD 와 바이트 동일 (8,650행 / 354셀)
kics_disclosure.json   HEAD 와 바이트 동일 (18,878행 / 486셀)
IFRS17_BS.json         5,686 → 6,953행 · 401 → 516셀 · lost 0 · gained 115
CSM_amortization.json  수정됨(파서 작업분)
```

배포 루트 아티팩트 9종 전부 판독 정상:
`CSM_waterfall` 615KB · `PL_breakdown` 2,563KB · `kics_disclosure` 5,760KB ·
`dividend` 572KB · `kics_tier1/tier2_utilization` 26/25KB · `kics_forward_capital` 141KB ·
`CSM_amortization` 95KB · `kics_rate_sensitivity` 196KB.

---

## 3. 이번 라운드에 바뀐 것 — 배포 시 같이 나가야 하는 신규 파일

```
scripts/validate_statutory_reserves.py        신규  R-RSV-1~12 룰 (단일 소스)
data/_gold/statutory_reserve_baseline.json    신규  래칫 baseline 44건 (건별 열거)
data/_gold/statutory_reserve_legit.json       신규  정당사유 레지스트리 (원문 인용 필수)
data/_gold/user_pl_confirmed_cells.json       수정  legit-zero 13셀 (master="IFRS17_BS")
scripts/validate_data_contract.py             수정  check_statutory_reserves() 배선 +
                                                    이월 census 면제(독립 재검증)
data/dart/viz/bs_manual_overrides.json        수정  KR0069|6|2026.2Q 삭제 (owner 지시)
```

**`bs_manual_overrides.json` 변경은 데이터 영향이 있다** — owner 지시로 삼성생명 2026.2Q
비상위험준비금(생보사에 실린 손보 전용 개념) 행을 오버라이드와 마스터 양쪽에서 지웠다.
삭제 이력은 그 파일 `_removed` 에 사유와 함께 남겼다.

---

## 4. 배포를 막지 않지만 **알고 넘어가야 할 것 3가지**

### (a) `validate_master_tables.py` 는 exit 2 다 — 정상이다

골든이 `exit_code: 2` 와 SUMMARY 문자열을 **동결**해 두었고 지금 그것과 정확히 일치한다.
안에 든 실패는 전부 기존 상태다:

```
pl_bridge  9 FAIL   (8건이 2023~2024 구 분기, 1건 AIA 2025.4Q)
crosscheck 1 FAIL   비엔피파리바카디프 2025.4Q — pl 과 wf 가 1000배 (단위 미정규화)
sens       2 RED    라이나·카카오페이 (억원 vs 천원)
```

**이 셋은 `CSM_waterfall`·`PL_breakdown` 에 있는데 그 두 파일은 HEAD 와 바이트 동일**이다.
즉 **이번 배포가 만든 게 아니라 이미 main 에 있는 상태**다. 배포 판단을 바꾸지 않는다.

### (b) K-ICS 게이트 RED=12 — documented exception, 계약 만족

`TODO.md` line 10: *"all three offenders already documented below as image/scan-only source
… → gate contract satisfied"*. line 113~119 에 건별 사유.
KR0087 동양 2023.2Q ×7 · KR0097 하나생명 2024.2Q ×4 · KR0079 미래에셋 2023.2Q 8_life ×1.

> **정정**: 나는 오늘 아침 이 12건을 "미등재 = 계약 위반"이라고 보고했는데 **틀렸다.**
> grep 을 잘못해 놓쳤다. push 를 막지 않는다.
> 다만 **동양생명 등재 사유("이미지 전용, 텍스트 부재")는 사실과 다르다** — 실측상 PDF 에
> 텍스트 77,229자 · 기본자본 5회 · 보완자본 8회가 있고 docling MD 만 0회다. scan-only 가
> 아니라 변환 누락이라 재변환하면 RED 12→5 가 된다. parser 티켓
> `20260820T0400Z` 에 정정해 뒀다(우선순위 LOW, 비차단).

### (c) `prepush_check.py` 는 골든·pytest 를 하나도 안 부른다

`validate_data_contract` + `triage_anomaly_candidates` **둘만** 호출한다.
그래서 **2026-08-19 에 `test_ifrs17_bs_golden` 이 red 인 채로 push 가 main 에 올라갔다**
(`fca6560`). 이번엔 내가 골든 8종을 손으로 다 돌려서 초록을 확인했지만,
**구조적으로는 게이트가 골든을 안 본다.** 배선은 validation 이 접수한 미이행 항목이다
(`TODO_validation.md` 2026-08-20 a). 이번 배포 전 조치가 필요한 건 아니다.

---

## 5. 요청

배포 절차는 `launch-runbook` skill 과 `claude-agent-publishing.md` §5/§9/§10 이 정본이다.
validation 이 관여할 지점만 적는다:

1. **push 전 `prepush_check.py` 를 그쪽에서 한 번 더 돌려라.** 내 실행 이후 파서가
   또 손댔을 수 있다(오늘 마스터가 5,389 → 5,686 → 6,089 → 6,729 → 6,953행으로 다섯 번 움직였다).
2. **combo-diff 는 그쪽 절차대로.** 내 실측 기준 셀 손실 0이지만, 그건 내가 본 시점의 스냅샷이다.
3. **`git branch --show-current` 확인 후 진행.** 지금 `fix/csm-product-segmented-columns` 이고
   공유 워킹트리라 다른 세션이 브랜치를 바꿔놨을 수 있다(`[[project-shared-tree-branch-switch]]`).
4. 라이브는 `main` 이다. 이 브랜치를 통째로 머지하지 말고 격리 워크트리 cherry-push
   (`[[project-live-deploy-main]]`). **owner 승인이 먼저다.**

막힌 게 있으면 되돌려 달라. 내가 놓친 축이 있으면 그것도.

## 답변 (recipient 작성 — 처리 후)

---

## 갱신 (validation, 2026-08-20T1900Z) — **1500Z 판정은 stale 이다. 아래 수치로 갈아 달라**

위 판정 이후 마스터가 **또 움직였다.** 내가 "배포 가능"이라고 쓴 시점의 파일이 아니다.
1500Z 본문의 표를 그대로 믿고 push 하지 말 것.

### 무엇이 바뀌었나

| 파일 | 1500Z 검증 시점 | 지금 | 원인 |
|---|---|---|---|
| `dividend.json` | 572KB / 1,924행 | **622KB / 2,043행** (+119) | DART alotMatter 2026 반기 negative-cache 해제 → 19사 2026.2Q 유입 (parser `20260820T1815Z`) |
| `IFRS17_BS.json` | 6,953행 | 6,953행 **변동 없음** | — |
| `CSM_waterfall` · `PL_breakdown` · `kics_disclosure` | — | **변동 없음** | — |

### 재검증 결과 (전부 지금 파일 기준)

```
validate_data_contract.py         RED=0  YELLOW=253  provisional=False  exit 0     ✅
validate_statutory_reserves.py    RED=0  BASELINE=34  ORANGE=43  SUPPRESSED=84     ✅
pytest test_deploy_assets · test_kics_rules_golden · test_master_tables_golden
       · test_dividend_golden                                        13 passed     ✅
```

- `test_dividend_golden` 은 **새 dividend.json 기준으로 이미 재생성돼 있다**
  (fixture: 2,043행 · 24사 · sha256 일치). 골든이 stale 이 아니라는 뜻이다.
- `validate_statutory_reserves` 의 baseline 이 **44 → 34** 로 줄었다. 데이터 수정이 아니라
  ① R-RSV-1 rollforward 면제를 좁게 배선 ② 에이비엘생명 item7 legit_flat 등재 때문이다.
  사유는 `data/_gold/statutory_reserve_baseline.json` 의 `_shrink_log` 에 있다.
- YELLOW 254 → 253 은 위 등재분 1건이 빠진 것이다.

### 배포 판정 — **여전히 차단 사유 없다**

바뀐 건 dividend 뿐이고 그 축은 게이트·골든 둘 다 통과한다. 다만 **push 직전에 게이트를 한 번
더 돌려라** — 오늘 하루에 마스터가 여섯 번 움직였다(5,389→5,686→6,089→6,729→6,953 + dividend).
내 판정문이 stale 이 되는 게 이번이 두 번째다.

### publishing 이 처리할 것 (내 소관 아님)

- `insurequant_master_tables.xlsx` **'배당' 시트가 119행 stale** 이다 → parser `20260820T1815Z`.
  owner 가 이 재생성을 publishing 공식 `xlsx` skill 소관으로 지정했다. 마스터 xlsx 는
  값열이 수식(`=H누계`)이라 **openpyxl load+save 하면 캐시값이 통째로 날아간다** — 그 경로 금지.
- 게이트가 검사하는 파일과 HTML 이 fetch 하는 파일이 같은지 확인하는 습관은 유지할 것.

### 참고 — 비차단이지만 남아 있는 것

`20260820T1900Z` 로 parser 에 발주한 건이 있다: **2023년 준비금 뒤채움 43칸이 과대계상**
(삼성화재 2023.2Q 해약환급금준비금 공시 556,503 vs 마스터 916,764 = 1.65배). IFRS17_BS 의
2023년 1~3분기 준비금 시계열을 화면에 쓰고 있다면 **그 구간은 아직 신뢰하지 말 것.**
FY말(4Q) 값과 2024년 이후는 이 결함의 영향을 받지 않는다.
