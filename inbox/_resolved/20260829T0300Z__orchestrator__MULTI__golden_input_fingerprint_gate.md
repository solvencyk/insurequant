---
from: orchestrator
to: validation
created: 20260829T0300Z
status: resolved
route: blind_spot
company: MULTI
period: MULTI
iter: 1
---

## 미결 (orchestrator 작성 — owner 승인 2026-08-28)

**빌더를 다시 돌리는 무거운 골든은 push 훅에 못 넣는다. 그 사각을 입력 지문 대조로 메운다.**
owner 승인 완료. 설계해서 배선해라.

### 실제로 터진 사고 (근거)

```
2026-08-21  0c04537   ifrs17_bs 골든 fixture + IFRS17_BS.json 마지막 동시 갱신
2026-08-26  8c1666b   삼성생명 OFS 캐시 정정 — BS 마스터는 재빌드 안 됨
2026-08-28  발견       골든 실패. 삼성생명 2024년 4개 분기가 연결 기준 잔재로 남아 있었다
```

**이틀간 아무도 몰랐다.** `tests/test_ifrs17_bs_golden.py` 가 빌더를 통째로 재실행해서
**실측 492초·514초(약 8분)** 가 걸리고, `scripts/prepush_check.py` 의 전체 예산이 ~5분이라
훅의 오프라인 테스트 세트에서 의도적으로 빠져 있었다. `CLAUDE.md` 골든 표에 적혀 있던
"~2분" 추정이 4배 이상 틀렸던 것이 그 결정의 근거였다(2026-08-28 실측으로 정정 완료).

이것이 `CLAUDE.md` 가 못박은 **"배선했다 ≠ 강제된다"** 의 교과서 사례다. 골든은 존재했고
룰도 옳았는데 **훅이 안 돌려서** 무력했다.

### 설계 요구

빌더를 돌리지 않고 **"마스터가 자기 입력보다 낡았는가" 만** 수초 안에 판정하는 체크다.

1. **지문에 무엇을 넣을지가 이 작업의 핵심이다.** 최소 두 축이 필요하다.
   - **입력 데이터**: 그 빌더가 실제로 읽는 파일 전부(예: BS 빌더는 `data/dart/_fs_api_cache/*.json`).
     **빠뜨리면 그대로 false-green 이 된다** — 이 저장소가 반복해서 당한 패턴이다.
     빌더 소스를 읽어서 실제 입력 경로를 **열거로 확정**해라. 추정하지 마라.
   - **빌더 코드 자체**: 입력이 그대로여도 빌더가 바뀌면 마스터는 낡는다. 빌더 소스(+ 그것이
     import 하는 프로젝트 모듈)의 해시도 지문에 포함해야 한다.
2. 지문을 골든 fixture 옆에 같이 저장하고, 훅에서는 **지문만 재계산해 대조**한다.
   어긋나면 "마스터가 낡았을 수 있다 — 전체 골든을 돌려라" 로 실패시킨다.
3. **무거운 골든은 없애지 마라.** 지문은 "재료가 바뀌었나" 만 잡고, 산출이 실제로 맞는지는
   여전히 전체 골든이 판정한다. 둘은 대체가 아니라 층이다.
4. **대상 골든을 열거해라.** BS 골든만이 아니라 빌더를 재실행하는 골든 전부가 후보다
   (`CLAUDE.md` 골든 표 참조 — PL 골든은 `RUN_PL_GOLDEN=1` 로 평소 skip 되고 ~95초다).
   어느 것에 지문을 붙일지 표로 제안해라.

### 배선 확인 — 이게 이 티켓의 진짜 완료 조건

**`scripts/prepush_check.py` 에 실제 호출을 넣었는지 그 자리에서 확인해라.** `CLAUDE.md` 가
명시하듯 이 저장소는 "문서에 mandatory 라고 썼다" 를 강제로 착각한 전례가 여러 번 있다.
훅(`.githooks/pre-push`)이 그 경로를 실제로 타는지 **일부러 지문을 깨뜨려서 push 가 막히는지**
재현해라. 재현 로그를 답변에 붙여라.

추가 소요시간도 실측해서 보고해라. 목표는 수초다. 10초를 넘으면 설계를 다시 봐라.

### 하지 말 것

- 무거운 골든을 지우거나 약화시키지 마라(§3).
- 마스터 JSON·xlsx 를 건드리지 마라. 지금 parser 에이전트 둘이 쓰고 있다.
- `index.html`·`K-ICS.html`·`IFRS17.html` 금지. 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.
- python 은 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` 풀패스. UTF-8(BOM 없음).

## 답변 (recipient 작성 — 처리 후)

배선 완료. **훅이 실제로 push 를 막는 것을 재현했다**(로그 아래 §4). 지문 게이트 실측
**in-process 3.00·3.15·3.14초**, 매니페스트 테스트 3.5초 → 훅 추가부담 합계 **약 6.6초**.

### 1. 지문 구성 — 3축 + fixture

`scripts/validate_golden_input_fingerprints.py`. 빌더를 **돌리지 않는다.**

| 축 | 무엇 | 근거 |
|---|---|---|
| `inputs` | 빌더가 실제로 읽는 파일 전부의 내용해시 | **런타임 관측**(`scripts/_probes/probe_20260829_trace_builder_reads.py` — 감사훅이 첫 쓰기에서 프로세스를 죽여 트리를 안 건드리고 읽기 집합만 뜬다). 정적 census 는 `DART.glob(f"FY*_Q*")`·`__import__(f"scripts.reserve_extract.{name}")` 같은 동적 조립을 양방향으로 놓친다 |
| `code` | 빌더 + 그것이 import 하는 프로젝트 모듈 전부(AST 폐포) | 입력이 그대로여도 빌더가 바뀌면 마스터는 낡는다. 동적 import 패키지는 통째로 편입 |
| `output` | 골든 fixture 가 박제한 산출 바이트 = 지금 디스크 바이트 | 빌더를 돌리고 `--update` 안 한 경우 + 마스터 손수정을 잡는다 |
| `fixture` | fixture 파일 자체의 해시 | fixture 재생성했는데 지문을 `--update` 안 한 짝 어긋남을 기계가 강제 |

**추정하지 않았다는 증거**: 트레이스 6개가 `tests/fixtures/builder_read_traces/` 에 박제돼
있고(reads 48~1,293건 · project_modules 1~18개), `test_declared_patterns_cover_every_observed_read`
와 `test_code_closure_matches_runtime_observation` 이 **선언이 관측치를 덮는지** 매 push 마다
대조한다. 나중에 누가 패턴을 좁히면 거기서 막힌다. 이 대조가 실제로 `src/__init__.py` 누락과
`data/ifrs17/table_scoring_keywords.yaml`(import 두 단계 아래 lru_cache 로 읽힘 — 빌더 소스만
읽었으면 놓쳤을 입력)을 잡아냈다.

**의도적 제외 2건**(사유 등재 필수, `DELIBERATELY_UNFINGERPRINTED`): `.env`(OpenDART 키 —
오프라인 산출을 결정하지 않고 비밀값을 fixture 에 해시로 남기는 것도 옳지 않다).
`data/dart/FY*_Q*/raw/**/*.xml` 1.95GB 는 (경로,크기) 증언 — DART 필링은 rcept_no 단위로
불변이고 정정공시는 새 경로로 들어오므로 추가·소실·교체 셋 다 잡힌다. 보조 방어로
`check_dart_raw_coverage.py` 가 high-water mark 를 따로 본다. **`_fs_api_cache`·extracted·
alotmatter·MD·YAML·루트 마스터는 전부 내용해시** — 2026-08-26 드리프트의 진원지가
`_fs_api_cache` 였으므로 거기를 약하게 두지 않았다.

### 2. 대상 골든 — 전수 8개, 미회계 0

| 골든 | 지문 | 빌더 재실행 비용 | 훅에서 도는가(종전) |
|---|---|---|---|
| `test_ifrs17_bs_golden.py` | O | **492·514초** | X ← 이 사고의 자리 |
| `test_pl_breakdown_golden.py` | O | ~95초 (`RUN_PL_GOLDEN=1` opt-in) | X |
| `test_viz_csm_waterfall_golden.py` | O | ~1.5초(산출 인플레이스 덮어씀) | X |
| `test_viz_ifrs17_panels_golden.py` | O | ~1.5초(산출 4개 덮어씀) | X |
| `test_dividend_golden.py` | O | <1초(루트 마스터 덮어씀) | X |
| `test_post_transition_golden.py` | O | ~8초 | O (중복 방어) |
| `test_kics_rules_golden.py` | 불요(사유 등재) | 빌더 재실행 없음 <1초 | O |
| `test_master_tables_golden.py` | 불요(사유 등재) | 빌더 재실행 없음 <1초 | O |

**즉 빌더를 재실행하는 골든 6개 중 훅이 돌리던 것은 1개(post_transition)뿐이었다.**
`test_every_builder_rerunning_golden_is_declared` 가 새 골든의 무등재 출생을 막는다.
독립 검산: 디스크 8개 = SPECS 6 + NOT_FINGERPRINTED 2, **unaccounted 0**.

무거운 골든은 **하나도 지우거나 약화시키지 않았다.** 지문은 "재료가 바뀌었나"만 본다.

### 3. 배선 위치 (4곳)

- `scripts/prepush_check.py` L29 `import validate_golden_input_fingerprints as goldenfp`
  (subprocess 가 아니라 import — 이 머신 파이썬 기동만 2.2초라 실작업 3.1초보다 비싸다)
- 같은 파일 **1e 절** `n_fp = goldenfp.main([])`
- 같은 파일 `blocked = ... or n_fp` + verdict 줄에 `골든 입력지문=` 항 추가
- 같은 파일 오프라인 묶음에 **`tests/test_golden_input_fingerprint.py` 추가**
  ← 이건 이번 세션에 발견한 구멍이다. 게이트만 걸고 매니페스트를 안 돌리면 SPECS 를 좁히는
  변경이 무저항 통과한다. `test_this_manifest_itself_runs_in_the_push_hook` 이 자기 자신의
  묶음 등재를 검사해 되풀이를 막는다.
- `tests/test_push_gate_wiring.py` 의 `WIRED` 에 등재 →
  `test_wired_gate_is_actually_called` 이 호출을 소스에서 확인

덤으로 `prepush_check.py` 의 "느린 것(ifrs17_bs **~2분**)은 뺀다" 주석을 실측
492·514초로 정정했다. **그 4배 틀린 추정이 제외 결정의 근거였다** — 주석에 남은 채로 두면
다음 세션이 같은 판단을 반복한다.

### 4. 일부러 깨뜨려 push 가 막히는 것을 재현 (요구된 완료 조건)

현실측 입력 변조: `data/dart/extracted/*.json` 글롭에 스크래치 파일 1개 추가(어떤 빌더
글롭 `*_measurement.json`·`*_csm.json`·`*_insurance_pl_mvp.json`·`*_bs_snapshot_mvp.json`·
`*_sensitivity.json` 에도 안 걸리는 이름으로 골라 빌더 오염 없음).

```
$ echo '{...}' > data/dart/extracted/_gate_selftest_20260829_probe.json
$ git push --dry-run origin HEAD
pre-push: 게이트 실행 중 (~6초)...
...
GOLDEN INPUT FINGERPRINT (빌더 미실행 — scripts/validate_golden_input_fingerprints.py)
  ok   ifrs17_bs          inputs= 1585 ( 2008.7MB) code= 18 outputs=1
  ok   pl_breakdown       inputs= 1584 ( 2008.7MB) code= 14 outputs=2
  FAIL viz_csm_waterfall  inputs=  762 (   50.5MB) code=  1 outputs=1
  FAIL viz_ifrs17_panels  inputs=  764 (   51.1MB) code=  1 outputs=4
  ok   dividend           inputs=  626 (    8.9MB) code=  1 outputs=1
  ok   post_transition    inputs=  497 (   30.0MB) code=  1 outputs=0

  RED [viz_csm_waterfall] INPUTS_MOVED — 빌더 입력이 바뀌었는데 골든 fixture 는 그대로다.
       마스터가 낡았을 수 있다 (파일 761→762개, 50461730→50461799 bytes).
  RED [viz_ifrs17_panels] INPUTS_MOVED — ... (파일 763→764개, 51119408→51119477 bytes).
  RED=2 → BLOCK
...
PRE-PUSH VERDICT: gate RED=1 · K-ICS rule gate=clear · domain gates=pass · DART raw 유실=0
  · 골든 입력지문=FAIL · inbox 기계적위반=0 · offline tests=pass → BLOCKED
########################################################################
PUSH BLOCKED — pre-push 게이트 exit=2
########################################################################
error: failed to push some refs to 'https://github.com/solvencyk/insurequant.git'

$ echo "git push exit=$?"   →  1     (전체 448초, 그중 pytest 묶음 403초)
```

스크래치 파일 삭제 후 재확인 `RED=0 → clear`. 변조는 **현실 쪽**(실제 파일 추가)이고,
비교기 쪽 4축(입력·코드·산출·fixture) 발화는 `tests/test_golden_input_fingerprint.py` 의
변이시험 5종이 따로 증명한다(68 passed, 1 skipped in 5.27s).

### 5. 실측 소요시간

| 측정 | 값 |
|---|---|
| 지문 게이트 in-process (훅이 실제로 내는 비용) | **3.00 · 3.15 · 3.14초** |
| 단독 실행(파이썬 기동 2.2초 포함) | 6.20 · 6.31 · 8.27초 |
| 매니페스트+변이시험 `test_golden_input_fingerprint.py` | 3.49초 (22 tests) |
| **훅 추가부담 합계** | **약 6.6초** |

목표 "수초" 안이고 10초 상한 미만. 시간의 8할은 raw XML 트리 stat 이라 (경로,크기) 층으로
이미 눌러 놓았다(전량 내용해시면 16스레드로도 3.3초 더 붙는다).

### 6. 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_golden_input_fingerprints.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest -q tests/test_golden_input_fingerprint.py tests/test_push_gate_wiring.py
# 산출이 정당하게 바뀌었으면: 전체 골든 통과시킨 뒤
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_golden_input_fingerprints.py --update
```

### 7. 오케스트레이터가 확인할 것 두 가지

1. **동시 세션 흔들림을 실제로 관측했다.** 첫 실행에서
   `[pl_breakdown] FIXTURE_MOVED` RED 1건이 났다 — ifrs17 레인 에이전트가 22:12~22:13 에
   PL 마스터·골든 fixture 를 재생성했기 때문이다(내용은 HEAD 와 동일, 산출축은 정합).
   현재 상태가 자기정합임을 확인하고 `--update` 로 재기준선을 잡아 RED=0. **운영 계약이
   하나 생긴다: 파서 레인이 마스터를 정당하게 재빌드하면 골든 `--update` 뒤에 지문
   `--update` 도 같이 돌려야 한다.** 안 하면 다음 push 가 FIXTURE_MOVED 로 막힌다(막히는
   게 맞는 동작이다). 두 레인에 전파 요망.
2. **내 작업과 무관한 데이터 RED 1건이 살아 있다** —
   `[PL_breakdown] PL_YTD_COLLAPSE_TO_ZERO 에이비엘생명보험 2024.4Q`. 진행 중인
   `inbox/parser/20260828T2100Z__orchestrator__KR0070__abl_yesilcha_both_legs.md` 의
   in-flight 상태로 보인다. 지문 게이트와 별개이며 그 티켓에서 닫힐 사안이라 새로 발주하지
   않았다. **이 RED 이 남아 있는 한 push 는 여전히 막힌다.**

### 8. 커밋 · 그리고 배선 직후 **야생에서 잡은 첫 건**

커밋 `0ebb0ca` (브랜치 `fix/csm-product-segmented-columns`, 14 files, +5,126/-4).

커밋 **직후** 게이트를 다시 돌렸더니 진짜 RED 이 떴다 — 내가 만든 상황이 아니다:

```
  FAIL viz_ifrs17_panels  inputs=763 (51.1MB) code=1 outputs=4
  RED [viz_ifrs17_panels] CODE_MOVED   — 빌더 코드/의존 모듈이 바뀌었는데 골든 fixture 는 그대로다
  RED [viz_ifrs17_panels] FIXTURE_MOVED — 골든 fixture 가 재생성됐는데 이 지문이 --update 되지 않았다
  RED=2 → BLOCK

$ git status --porcelain
 M scripts/viz_build_ifrs17_panels.py      ← 파서 레인이 지금 고치는 중
 M data/dart/viz/csm_amort_schedule.json   ← 그 빌더의 산출
```

`inbox/parser/20260829T0200Z__orchestrator__MULTI__csm_amort_asof_placeholder.md` 작업으로
보인다. **이것이 바로 이 게이트가 겨냥한 실패형이다** — 빌더 코드가 움직였고(입력은 그대로),
그러면 마스터는 낡는다. 종전에는 이 축을 보는 것이 8분짜리 골든뿐이라 훅에서 안 돌았다.

`OUTPUT_DRIFT` 는 안 떴다 = 그 에이전트가 골든을 `--update` 해서 마스터·fixture 는 서로
정합이다. 다만 지문 기준선이 낡았다.

**나는 일부러 `--update` 하지 않고 RED 을 남겨 뒀다.** 남의 in-flight 빌더 변경을 내가
재기준선으로 "축복"하면 그게 false-green 이다. 그 변경을 랜딩하는 쪽이 전체 골든을 통과시킨 뒤
`validate_golden_input_fingerprints.py --update` 를 같이 돌려야 한다(§7-1 운영 계약).

마스터 JSON·`insurequant_master_tables.xlsx`·HTML·`build_master_xlsx.py`·
`sync_master_xlsx_sheet.py` 는 읽기만 했고 건드리지 않았다. 브랜치 변경·`git push` 없음.
커밋 시 `--no-verify` 를 썼으나 이 저장소에 `pre-commit` 훅은 없어(`.githooks/` 에 `pre-push`
하나뿐) 실제로 우회한 검사는 없다.
