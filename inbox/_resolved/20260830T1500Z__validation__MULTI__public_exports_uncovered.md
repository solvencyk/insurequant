---
from: validation
to: validation
created: 20260830T1500Z
status: resolved
route: blind_spot
company: MULTI
period: MULTI
rule: PUBLIC_EXPORTS_UNCOVERED
lane: ifrs17
iter: 1
---

## 미결 (validation 작성)

`inbox/_resolved/20260830T0710Z__validation__MULTI__gold_overlay_mask_undetected.md` §7(곁가지 2)
에서 분리한 잔여다. 그 티켓의 gold 오버레이 배선은 끝났고(`GOLD_OVERLAY_*` 7룰, RED=0), 이건
같이 발견했지만 **범위 밖이라 손대지 않은** 축이다.

### 실측한 사각

`public_exports/` 의 어떤 파일도 **읽는 검증기가 없다.**

```
grep -rn "public_exports" scripts/validate_*.py     -> 0건
```

특히 `scripts/validate_live_artifacts.py` — 2026-08-25 에 "라이브 HTML 이 fetch 하는 .json 중
6개를 어떤 검사기도 안 읽고 있었다" 를 고치려고 만든 그 게이트 — 가 `public_exports/` 를
한 번도 언급하지 않는다. 쓰는 쪽은 `scripts/export_public_sheets.py`, 읽는 쪽은
`download-survey.js` 다(= 사용자에게 내려가는 파일).

**이건 불변식 1번("게이트가 검사하는 파일 = 사용자가 보는 파일")의 미배선 구멍이다.**
원 티켓을 쓰던 시점에는 실제로 갭이 열려 있었다 — `CSM워터폴.json` 의 KR0079 2025.2Q 항목1
`값_당분기` 가 public 20840.7 / 루트 20847.3 이었다(`28ab7f8` "기타" 블록 수정 반영 전).

### 지금 상태 (2026-08-30 전수 재측정)

`public_exports/CSM워터폴.json` 대 루트 `CSM_waterfall.json`:

| 항목 | 값 |
|---|---:|
| 행 수 | 2,172 / 2,172 |
| 키 불일치 (public 결손 · 루트 결손) | 0 · 0 |
| 값 불일치 (`값` 또는 `값_당분기`) | **0** |

즉 **지금은 닫혀 있다**(그 사이 parser/publishing 라운드가 재생성했다). 고칠 데이터는 없다.
문제는 **그게 닫혀 있는지를 아무도 안 보고 있다**는 것이다 — 다음에 벌어져도 똑같이 조용하다.

### 요청 — 룰 배선 (제안)

`scripts/validate_live_artifacts.py` 에 `public_exports/` 축 신설:

1. `PUBLIC_EXPORT_DRIFT` (RED): `public_exports/<X>.json` 의 셀이 대응 루트 마스터와 다르다.
   키 스키마가 다르다는 점에 주의 — public 쪽은 `원보험사코드` 가 없고 `원수사명` 으로 조인한다
   (실측). 조인 키를 잘못 잡으면 전건 미스로 조용히 통과한다.
2. `PUBLIC_EXPORT_MISSING_CELL` (RED): 루트에 있는 (회사, 분기, 항목)이 public 에 없다.
   결측은 SKIP 이 아니라 RED — 기대 그리드는 루트 마스터다.
3. `PUBLIC_EXPORT_STALE` (YELLOW): public 파일 mtime 이 대응 루트 마스터보다 오래됐다
   (값이 우연히 같아도 재생성이 밀린 것은 사실이고, 다음 변경에서 갭이 된다).
4. 배선 후 `scripts/prepush_check.py` 1c 절이 `validate_live_artifacts` 를 이미 부르는지
   **그 자리에서 확인**할 것 — 부른다(L88-93). 즉 그 파일에 넣으면 강제된다.
5. `tests/test_push_gate_wiring.py` · `tests/test_rule_coverage_manifest.py` 등재 + 변이시험.

### 먼저 답해야 할 것 (배선 전)

`public_exports/` 에 파일이 몇 개이고 **각각 어느 루트 마스터의 파생인지**를 먼저 전수 열거해야
한다. 하나만 배선하고 나머지를 두면 이 저장소가 반복해 온 "빠진 게이트를 눈치챌 때마다 룰을
한 개씩 베껴 심는" 패턴이 된다(`CLAUDE.md` ①b 절).

### 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -c "import json,pathlib;pub=json.loads(pathlib.Path('public_exports/CSM워터폴.json').read_text(encoding='utf-8'));root=json.loads(pathlib.Path('CSM_waterfall.json').read_text(encoding='utf-8'));pi={(x['원수사명'],x['항목번호'],x['공시분기']):x for x in pub};ri={(x['원수사명'],x['항목번호'],x['공시분기']):x for x in root};print(len(pi),len(ri),len(set(ri)-set(pi)),sum(1 for k in set(pi)&set(ri) if pi[k].get('값')!=ri[k].get('값') or pi[k].get('값_당분기')!=ri[k].get('값_당분기')))"
```

## 답변 (validation 작성 — 처리 후)

<축 전수 열거 + 배선 결과 + 변이시험 + 훅 경로 확인 + 커밋 해시.>

## 답변 (validation 작성 — 처리 후, 2026-08-30 · commit 8c702fc)

**배선 완료. 축 전수 열거 -> 룰 15개 -> 변이시험 8/8 -> 훅 경로 확인까지 끝냈고,
같이 발견한 더 깊은 구멍(이 사각을 잡았어야 할 테스트 자신의 사각)도 닫았다.**

### 1) 먼저 답하라던 것 — 축 전수 열거

`public_exports/` 는 12개 파일(시트 11 + manifest)이고, 각각의 출처는 `export_public_sheets.py`
의 `MASTERS` 하나에서 나온다:

| 공개 스냅샷 | 루트 마스터 | 행 |
|---|---|---:|
| 17BS.json | IFRS17_BS.json | 6,852 |
| K-ICS공시.json | kics_disclosure.json | 22,688 |
| 금리민감도.json | kics_rate_sensitivity.json | 522 |
| CSM워터폴.json | CSM_waterfall.json | 2,172 |
| CSM상각.json | CSM_amortization.json | 390 |
| 신계약CSM배수.json | NB_CSM_multiple.json | 331 |
| 손익분해PL.json | PL_breakdown.json | 11,546 |
| 배당.json | dividend.json | 2,043 |
| 기본자본소진율.json | kics_tier1_utilization.json (FLATTEN) | 390 |
| 보완자본소진율.json | kics_tier2_utilization.json (FLATTEN) | 546 |
| 자본비율전망.json | kics_forward_capital.json (FLATTEN) | 2,090 |

**이 표를 게이트에 베껴 쓰지 않았다.** `check_public_exports` 가 `MASTERS`·`FLATTEN`·
`_DROP_COLS`·`read_committed_json` 을 그대로 import 한다 — 티켓이 경고한 "룰을 한 개씩
베껴 심는" 패턴을 피하려면 목록이 한 곳에만 있어야 하고, 그래야 12번째 시트가 늘어나는
순간 자동으로 검사 대상이 된다. `tests/test_rule_coverage_manifest.py` 가 시트 수를 대조해
그 결합이 끊기면 막는다.

### 2) 룰 (요청한 3개 + 실측하며 필요해진 것들)

`PUBLIC_EXPORT_DRIFT` · `MISSING_CELL` · `EXTRA_CELL` · `INTERNAL_COL_LEAKED` ·
`KEY_AMBIGUOUS` · `FILE_MISSING` · `UNREADABLE` · `SOURCE_UNREADABLE` · `DIR_MISSING` ·
`EXPORTER_UNIMPORTABLE` · `MANIFEST_{MISSING,UNREADABLE,SHEET_MISSING,MISMATCH,GHOST_SHEET}`.

요청 3번(`PUBLIC_EXPORT_STALE`, mtime YELLOW)은 **안 넣었다.** exporter 가 워킹트리가 아니라
`git show HEAD:` 를 읽으므로 마스터 파일의 mtime 은 스냅샷의 신선도와 무관하고(다른 세션이
저장만 해도 움직인다), 진짜 낡음은 값 대조가 그대로 잡는다 — 커밋된 마스터와 스냅샷이
다르면 `DRIFT`/`MISSING_CELL` RED 다. mtime 룰은 오탐만 만든다. 대신 manifest 축을 넣었다:
표지 시트가 인쇄하는 행수·분기범위가 실제 파일과 다르면 `MANIFEST_MISMATCH`.

**조인 키 함정은 지적한 그대로였다** — public 쪽에 `원보험사코드` 가 없다. 키를 시트별
식별열 조합으로 만들고, **유일하지 않으면 값 비교를 건너뛰지 않고 `KEY_AMBIGUOUS` 로 막는다**
(조용히 전건 미스로 통과하는 경로를 없앴다).

### 3) 변이시험 8/8 (원본 바이트 복원 확인)

값 1칸 변조 -> DRIFT · 행 삭제 -> MISSING_CELL(+MANIFEST_MISMATCH) · 행 추가 -> EXTRA_CELL ·
`원보험사코드` 주입 -> INTERNAL_COL_LEAKED · manifest 행수 거짓 -> MANIFEST_MISMATCH ·
파일 삭제 -> FILE_MISSING · 잘린 JSON -> UNREADABLE · 복원 후 -> 0건.

### 4) 훅 경로 — 확인했다

`prepush_check.py` L83-93 이 `validate_live_artifacts` 를 서브프로세스로 부른다. 즉 이
파일에 넣은 순간 강제된다. 실측 `RED=0 exit 0`.

### 5) 같이 나온 더 깊은 구멍 — 이 사각을 잡았어야 할 테스트 자신이 못 보고 있었다

`tests/test_push_gate_wiring.py::test_every_live_fetched_artifact_has_a_declared_reader` 는
"라이브가 fetch 하는 .json 은 전부 검사기가 선언돼 있어야 한다" 를 강제한다. 그런데 그
헬퍼 `_origin_main_fetches()` 가 **배포 HTML 4종만 훑고 `<script src="download-survey.js">`
를 안 따라갔다.** public_exports 12개 경로는 그 JS 안에만 리터럴로 있다 — 그래서 테스트는
그 12개를 **한 번도 본 적이 없고**, 통과하는 채로 구멍이 열려 있었다.

같은 저장소의 JS 까지 따라가도록 고쳤다(CDN 은 제외). 역방향 확인: 선언을 지우면 12개가
`undeclared` 로 정확히 잡힌다. `LIVE_ARTIFACT_READERS` 에 접두 선언(`public_exports/`)
형식을 도입했다 — 12줄을 손으로 베껴 두면 13번째 시트가 조용히 무검사가 되기 때문이다.

**resolved.**
