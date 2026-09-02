# PM-2026-09-02 — 마스터 xlsx 가 마스터 JSON 과 갈라져도 게이트가 못 봤다 (owner 라이브 QA 로 발견)

> 상태: `closed` (5칸 전부 채움)
> 발견 경로: **owner 라이브 QA** (사고 1) → **owner 반문 후 전수 측정** (사고 2)
> 관련 커밋: 데이터 수정 `d1f1e7f`(자본비율전망) · `ee11c1d`(K-ICS공시) / 룰 신설 이 커밋
> 관련 inbox: 없음 (owner 구두 지시 2026-09-02 "신설한다 — 14개 시트 전수")

## 0. 사실관계 (blameless)

`insurequant_master_tables.xlsx` 는 owner 가 직접 받아 검토하는 산출물이고, 그 손질이 gold
리뷰 루프(`data/_gold/user_kics_cells.json` 계열)의 입력이 된다. 즉 **틀린 xlsx 는 다음
라운드의 데이터까지 오염시킬 수 있는 자리**다.

**사고 1 (2026-09-02 오전).** owner 가 라이브 사이트를 보다 발견했다 — NH농협손해보험 2026
`기본자본비율 전망` 이 라이브·마스터는 **102.77** 인데 xlsx `자본비율전망` 시트만 **79.8**.
숫자의 정체를 `kics_disclosure.json` item28 적용후로 확인한 결과 79.80 = 농협손해 **2026.1Q**
기본자본비율, 102.77 = **2026.2Q**. 마스터 `kics_forward_capital.json` 은 `baseline_quarter` 를
2026.2Q 로 갱신했는데 **xlsx 시트만 1Q 기준으로 돌린 옛 산출이 남아 있었다.** 라이브가 옳고
xlsx 가 틀렸다. 전수 측정 결과 농협손해 한 곳이 아니라 **38개사 전부, 2090칸 중 1219칸 stale**
(행 키는 100% 일치하고 값만 다름 = 베이스라인이 통째로 밀린 형태).

**사고 2 (같은 날).** owner 가 "그럼 기본자본소진율·보완자본소진율도 stale 하겠네" 라고 지적해
13개 시트를 전수 측정했다. **가설과 결과가 달랐다** — 소진율 2종은 드리프트 0(깨끗)이었고,
대신 아무도 안 보던 **`K-ICS공시`** 가 stale 이었다(변경 33셀 · 추가 121행, 25,208 → 25,329행).
교훈은 "어느 시트가 stale 한지 추측하지 말고 전수로 재라" 이다.

영향 범위: 라이브 사이트·마스터 JSON·`public_exports/` 는 **전부 옳았다.** 틀린 것은 xlsx
워크북 2개 시트뿐이고, 라이브 노출은 없다. 다만 owner 가 그 워크북으로 검토했으므로 검토
판단이 오염될 수 있었다.

---

## 1. 무엇이 통과했나 (어떤 게이트가 왜 못 잡았나)

- 통과 당시 게이트 상태: `validate_data_contract.py` **RED=0** · `validate_kics_disclosure.py`
  blocking RED 0 · `validate_live_artifacts.py` `public_exports` 발견 0 · 오프라인 테스트 전부
  통과. **모든 게이트가 초록인 채로 두 시트가 뒤처져 있었다.**
- **못 잡은 이유**: 구조적 **검사 축 부재**다. 마스터 JSON 의 하류 사본을 대조하는 룰은
  `PUBLIC_EXPORT_*`(`validate_live_artifacts.py` check 6) 하나뿐인데, 그것은
  **마스터 ↔ `public_exports/` 스냅샷**만 본다. **마스터 ↔ `insurequant_master_tables.xlsx`
  를 대조하는 룰은 저장소에 0건이었다.**
  `sync_master_xlsx_sheet.py` 는 **요청받은 시트 하나만** 동기화하고 스스로 뒤처짐을 탐지하지
  않는다(사후검증도 "그 시트가 목표와 일치하는가"까지다). 즉 **누가 어느 시트를 동기화할지
  기억하는 것**에 정합성이 걸려 있었고, 기억이 곧 게이트였다.

> false-green 메커니즘 한 문장: **하류 사본이 두 개(공개 스냅샷 · xlsx)인데 검사기는 하나뿐이라,
> 검사받지 않는 쪽이 뒤처져도 RED 는 구조적으로 나올 수 없었다.**

부차적으로, 이 사각은 이 저장소 불변식 1번("게이트가 검사하는 파일 = 사용자가 보는 파일")의
**세 번째** 발현이다 — PM-2026-08-25 가 라이브 HTML 이 fetch 하는 .json 6개에서, 그 후속이
`public_exports/` 에서 같은 병을 닫았고, 남아 있던 것이 xlsx 였다.

## 2. 어떤 룰이었으면 잡았나 (구체 룰 정의)

| 항목 | 내용 |
|---|---|
| 룰 id | `MASTER_XLSX_DRIFT` (+ 동축 13종, 아래 목록) |
| 입력 | `insurequant_master_tables.xlsx` 의 **13개 데이터 시트 전수** × 각 시트의 값 컬럼 전 칸. 목표값은 `build_master_xlsx.MASTERS` 가 선언한 루트 마스터 JSON 에서 `FLATTEN`+`coerce`+`target_rows` 로 생성 (전부 **import**, 재타이핑 금지) |
| 판정식 | 행 식별키 = 값이 아닌 컬럼 전부(`TEXT_COLS` ∪ `{항목번호}`) — `sync_master_xlsx_sheet.py` 와 **동일 규칙**. 키로 조인한 뒤 값 컬럼을 `norm()` 적용 후 **정확일치** 비교. 키 불일치는 `ROW_MISSING`/`ROW_EXTRA` |
| 임계값 | **추가 tolerance 없음.** `norm()` 이 접는 것만 흡수한다 — ① 정수형 float ↔ 정수형 문자열(`154.0` ↔ `'154'`) ② float 를 `%.15g`(xlsx 가 실제로 저장하는 정밀도)로 접기 ③ `None`/`""` 동일시. 그 위에 밴드를 두면 진짜 값 차이를 놓치고, 더 엄하게 하면 **동기화 스크립트가 만들 수 없는 상태**를 요구해 영원히 못 고치는 RED 이 된다 |
| severity | **RED**(차단). owner 가 받는 산출물의 값이 마스터와 다른 상태이고, 항상 기계적으로 고칠 수 있다(`sync_master_xlsx_sheet.py <시트>`) — RED 의 조건을 충족한다 |
| 오탐 억제 | ① 셀 **타입** 차이(`'154'` vs `154.0`)는 드리프트가 아니다 — `coerce()` 가 값 아닌 열을 문자열로 만드는데 owner 가 Excel 로 열어 저장하면 숫자로 되돌아간다. 어느 쪽도 값을 안 바꾼다 ② float 16자리째 차이 무시(시트가 담을 수 없는 정밀도) ③ `요약` 시트는 **행수만** 검사, **설명 열은 검사하지 않는다**(다른 레인이 손으로 관리하는 문구 — `sync_master_xlsx_sheet.py` L21-22·L271-272) ④ `MASTERS` 밖 수기 시트(피벗 등)는 허용된 설계라 RED 이 아니라 **YELLOW census** ⑤ 티커 `'000060'` 은 선행 0 이 깨지므로 문자열로 유지 |

동축 룰 전량(13 + census 1):
`MASTER_XLSX_FILE_MISSING` · `MASTER_XLSX_UNREADABLE` · `MASTER_XLSX_FORMULA_PRESENT` ·
`MASTER_XLSX_SHEET_MISSING` · `MASTER_XLSX_COLUMN_MISMATCH` · `MASTER_XLSX_MASTER_UNREADABLE` ·
`MASTER_XLSX_KEY_AMBIGUOUS` · `MASTER_XLSX_ROW_MISSING` · `MASTER_XLSX_ROW_EXTRA` ·
`MASTER_XLSX_DRIFT` · `MASTER_XLSX_SUMMARY_ROWCOUNT` · `MASTER_XLSX_SUMMARY_SHEET_MISSING` ·
`MASTER_XLSX_UNTRACKED_SHEET`(YELLOW) · `MASTER_XLSX_CENSUS`(YELLOW).

### 되돌려 재본 결과 — 이 룰이었으면 실제로 잡았나 (실측)

수사가 아니라 측정으로 답한다. 두 수정 커밋은 **xlsx 만** 건드렸으므로(각 `1 file changed`)
그때의 워크북을 꺼내 **오늘의 마스터**로 대조하면 그날 게이트가 봤어야 할 것이 그대로 재현된다:

| 워크북 시점 | RED | 발견 내역 |
|---|---|---|
| `d1f1e7f~1` (두 수정 **전**) | **5** | `자본비율전망` DRIFT **1111** + ROW_MISSING **169** + ROW_EXTRA **169** · `K-ICS공시` DRIFT **33** + ROW_MISSING **121** |
| `ee11c1d~1` (자본비율전망만 고친 뒤) | **2** | `K-ICS공시` DRIFT 33 + ROW_MISSING 121 |
| `HEAD` (현재) | **0** | (clean, 13시트 53,288행) |

숫자가 두 수정 커밋이 스스로 기록한 값과 **정확히 일치한다** — d1f1e7f 는 "변경 셀 1111 ·
재키잉 169행", ee11c1d 는 "변경 셀 33 · 추가 행 121". 즉 이 룰은 그날 **두 사고를 모두, 사람이
발견하기 전에** 차단했을 것이다. (169행이 EDIT 이 아니라 재키잉으로 잡히는 이유: `비고` 가
`TEXT_COLS` 에 있어 행 식별키의 일부다. 동기화 스크립트도 같은 키를 쓰므로 두 도구의 회계가 같다.)

재현: `scripts/_probes/probe_20260902_master_xlsx_retrodiction.py`

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code 반영 |
|---|---|---|---|---|
| 비교기 | `scan()` / `compare_sheet()` / `compare_summary()` | `scripts/check_master_xlsx_drift.py` (신설) | 13시트 전수 · 전분기 | — (모듈) |
| **push 게이트** | `check_master_xlsx(res, env)` | `scripts/validate_data_contract.py` (CHECK 8, `run_gate` 에 등재) | 13시트 전수 · 전분기 | ✅ `main()` 이 `2 if res.red` |
| K-ICS 게이트 | 해당 없음 (K-ICS 도메인 룰이 아니라 산출물 정합성 축) | — | — | — |

**실제로 push 를 막는가 — 확인함(줄 번호까지).** `scripts/validate_data_contract.py:3318` 정의 →
`:3347` 이 `run_gate()` 안에서 호출 → `scripts/prepush_check.py:40` `res = gate.run_gate(env)` ·
`:42` `n_red = len(res.red)` · `:246` `blocked = n_red or ...` → `return 2 if blocked` →
`.githooks/pre-push:35` `"$PY" "$GATE"` 가 그 exit code 로 push 를 막는다.
`.githooks/pre-push` 가 그 스크립트를 부르고, 이 클론의 `core.hooksPath` 가
`.githooks` 로 설정돼 있는 것도 확인했다(`git config --get core.hooksPath`).
즉 **문서가 아니라 코드 경로로 강제된다.**

배선이 사라지는 것을 막는 장치(전부 push 묶음 안에서 돈다):

- `tests/test_push_gate_wiring.py` — `DATA_CONTRACT_CHECKS` 에 `check_master_xlsx` 선언.
  선언과 `run_gate()` 본문이 어긋나면 실패한다(선언 없이 검사를 추가하면 **막힌다**. 실제로
  이번에 먼저 빨갛게 났고 그래서 선언을 넣었다).
- `tests/test_rule_coverage_manifest.py` — 신규 18개. 룰 id 매니페스트 · 시트 수 = 빌더
  `MASTERS` 수 **그리고 전부 실제로 대조됐는지**(`sheets_compared`) · import-대신-재타이핑 금지
  정적 검사 · 읽기전용 정적 검사 · 깨끗한 상태 RED 0 · **변이시험 8종**(값·행누락·행잉여·**행복제**·헤더·요약행수·요약행소실·미등재시트) · **2026-09-02 사고
  값 그대로 재생** · 타입변경 비드리프트(양방향) · 요약 설명열 비검사 · run_gate 배선.

**실행 비용(실측)**: 게이트 안에서 **+11.9초**(기존 15.2초 → 27.1초). 훅 전체는 17분 33초라
약 **+1.1%**. 테스트 쪽은 워크북을 모듈 픽스처로 **한 번만** 읽어 18개가 30.2초.

### selftest 케이스를 안 넣은 이유 (의도적)

`scripts/_data_contract_selftest.py` 는 `Env(inject=합성데이터)` 로 돌고, 이 검사는 실제 워크북
파일을 읽으므로 다른 디스크 축(`check_gold_overlay` · `check_kics_restatement`)과 같은 규칙으로
**`env.inject` 일 때 통째로 비켜간다** — 합성 케이스에 실파일 findings 가 섞이면 selftest 가
무너진다. 그 두 축도 selftest 케이스가 없고 대신 `test_rule_coverage_manifest.py` 의 변이시험이
덮는다. 이 룰도 같은 자리에 **18개**(변이 8 + 사고 재생 1 포함)를 뒀고, 그 파일은 훅의 오프라인
묶음에 이미 들어 있다. 실측: selftest **57/57 유지**(내 변경 전후 동일).

## 4. documented exception

**없음.** 면제 0건이고 등재부도 만들지 않았다. 현재 상태가 이미 RED=0 이므로(전수 sync 완료)
면제가 필요한 케이스가 존재하지 않는다. **의도적인 비검사 축은 하나뿐이고 면제가 아니라 설계다**:

- `요약` 시트의 **설명 열** — 기계가 정본을 갖고 있지 않고 다른 레인이 손으로 관리한다
  (`sync_master_xlsx_sheet.py` L21-22·L271-272 가 "손대지 않는다"고 명시). 근거를
  `scripts/check_master_xlsx_drift.py` 모듈 docstring 과
  `test_master_xlsx_summary_description_column_is_not_checked` 에 박아 뒀다. 같은 시트의
  **행수는 기계가 유지하므로 검사한다**(RED).
- `MASTERS` 밖 수기 시트 — 허용된 설계라 RED 이 아니지만 **조용히 두지 않고**
  `MASTER_XLSX_UNTRACKED_SHEET` YELLOW 로 센다("검사 안 되는 축"의 가시화). 현재 0건.

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 티켓 / 우선순위 |
|---|---|---|
| **UH-15** — 마스터 JSON 의 하류 사본을 **열거하는 매니페스트가 없다.** 지금까지 세 개(라이브 fetch .json · `public_exports/` · xlsx)가 **사고가 난 뒤에** 하나씩 검사 대상이 됐다. 네 번째 사본이 생기면 같은 순서를 또 밟는다 | 이 사각의 뿌리다. 사본이 늘어나는 것을 탐지하는 것이 아니라 **사람이 기억하는 것**에 걸려 있다 | 즉시 발주는 하지 않는다 — 먼저 실측이 필요하다(누가 루트 마스터를 읽어 파일을 쓰는지 런타임 추적). PM-2026-08-25 의 UH-14(추적 프로브가 push 묶음 밖)와 **같은 뿌리**라 그쪽에 합류시킨다 / P2 |
| **UH-16** — `sync_master_xlsx_sheet.py` 는 **시트에 변경이 있을 때만** `요약` 행수를 고친다(L210-212 조기반환이 L273 요약 블록보다 앞). 데이터 시트는 전부 동기인데 `요약` 만 틀어지면 `MASTER_XLSX_SUMMARY_ROWCOUNT` RED 을 그 스크립트로 못 고친다 | 지금은 무해(측정 결과 요약 전 행 일치). 발생하려면 워크북을 손으로 편집해야 하는데 그것 자체가 이 저장소에서 금지된 동작이다 | 발화하면 그때 `sync` 에 `--summary-only` 를 추가한다. 미리 만들지 않는다(측정된 이득 0 — UH-5·UH-9 선례: 오탐/필요가 확인되기 전에 배선하지 않는다) / P3 |
| **UH-17** — 이 검사는 **워킹트리 xlsx ↔ 워킹트리 마스터**를 본다. `PUBLIC_EXPORT_*` 는 마스터 쪽을 `git show HEAD:` 로 읽는데(`export_public_sheets.read_committed_json`) 여기는 그렇지 않다. 그래서 xlsx 를 동기화하고 **커밋하지 않은 채** push 하면 게이트는 깨끗한데 커밋된 상태는 어긋난다 | 공유 워킹트리에서는 다음 라운드에도 안 잡힌다(새 클론에서는 즉시 RED 이라 자기치유된다). 다만 워킹트리가 더러운 채 push 하는 것 자체가 `git status` 에 보인다 | **지금 안 만든다.** 커밋 기준으로 바꾸면 워크북을 한 번 더 읽어야 하고(+10초), 정상적인 sync 작업 중에는 **항상** 발화한다 — 오탐 억제를 설계하기 전에는 배선하지 않는다는 UH-5·UH-9 선례를 따른다. 값싼 대안(커밋 여부만 YELLOW)도 같은 상시발화 문제가 있다. 발화 조건: xlsx 를 sync 한 뒤 커밋 없이 push / P3 |
| 데이터 잔여 | **없음.** 13개 시트 전수 드리프트 0(53,288행), 게이트 RED=0 | — |

---

## close 체크

- [x] 1 무엇이 통과했나 — 하류 사본 2개 중 1개만 검사기가 있었다(검사 축 부재)
- [x] 2 구체 룰 정의 — 입력·판정식·임계값·severity·오탐억제 5종 + **되돌려 재본 실측**
- [x] 3 배선 위치 + scope — `validate_data_contract.py:3318/:3347` → `prepush_check.py:40/:246` → `.githooks/pre-push:35` (확인함), +11.9초
- [x] 4 exception 근거·등재 위치 — 면제 0건. 비검사 축 2개는 설계이며 근거를 코드·테스트에 박음
- [x] 5 미배선 잔여 + 후속 티켓 — UH-15(P2, UH-14 합류) · UH-16(P3, 발화 시) · UH-17(P3, 커밋기준 대조)
