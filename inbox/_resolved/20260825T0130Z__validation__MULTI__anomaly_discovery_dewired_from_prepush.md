---
from: validation
to: publishing
created: 20260825T0130Z
status: resolved
route: blind_spot
company: MULTI
period: ALL
rule: ANOMALY_PEER_OUTLIER
iter: 1
---

## 미결 (validation 작성)

**`prepush_check.py` 가 더는 일반 이상치 트리아지를 돌리지 않는다 (2026-08-25).**
owner 지시("씰데없는 룰들은 좀 쳐내 제발")로 저수익 휴리스틱을 정리하면서, 발견(discovery)
레이어를 push 경로에서 분리했다. **삭제가 아니라 이전이다.**

### 무엇이 바뀌었나

| | 종전 | 지금 |
|---|---|---|
| 스캔(구 CHECK 5) | `validate_data_contract.run_gate()` 가 매 실행 | `scripts/scan_generic_anomalies.py` (수동) |
| 트리아지 | `prepush_check.py` 2단계가 매 실행 | 같은 스크립트가 이어서 |
| 산출 경로 | `data/_derived/anomaly_{triage,skeptic_input}.json` | **동일 (안 바뀜)** |

### 왜 (실측)

- 이 층은 데이터계약 게이트 YELLOW **297건 중 224건(75.4%)** 을 혼자 만들고 리뷰 큐 83건이
  붙는데, **RED 를 한 건도 낸 적이 없다** — 설계상 YELLOW 전용이라 `prepush_check.py` 의
  `blocked = n_red or n_hyg or n_test or n_kics or n_dom` 에 **애초에 들어간 적이 없다.**
  즉 push 를 막은 적이 구조적으로 없다.
- 게이트가 인쇄하던 224건은 **트리아지 이전(정밀화 전)** 숫자다. 트리아지가 134건을 노이즈로
  자동 억제하는데, 게이트는 그 앞단을 날것으로 찍고 있었다(예: "비엔피파리바카디프 기초CSM=342
  vs cohort median 26882" — 그냥 작은 회사).
- 마지막으로 데이터 수정을 낳은 것은 **2026-06-19/20 라운드**(교보생명 원수예실차 4분기 ·
  BNP파리바카디프 단위오류 1.77조 · 코리안리 중복 43 · 교보라이프플래닛 보험금융손익).
  그 이후 두 달간 이 큐에서 나온 데이터 수정은 0건이다.

### 너희 쪽에서 해야 할 일 (둘 다 문서 수정 — 코드 아님)

`docs/agents/claude-agent-publishing.md` 두 자리가 이제 사실과 다르다. **너희 프롬프트라
내가 안 고쳤다** (validation 은 조사·발주만, 수정은 담당 stage).

1. **§0 (L163)** — "Runs: ① data-contract hard gate + ② generic-anomaly triage chain" 에서
   ②를 빼고, 대신 `scripts/scan_generic_anomalies.py` 를 **필요할 때 돌리는 별도 단계**로
   적어라. `prepush_check.py` 가 이제 돌리는 것: ① data-contract ①b K-ICS 룰게이트
   ①c 도메인게이트 4종 ③ inbox 위생 ④ 오프라인 테스트.
   `prepush_check.py` 출력에도 매 실행 한 줄로 남게 해 뒀다(조용히 사라지지 않게).
2. **§3 (L168-170)** — LLM-skeptic 단계 자체는 **그대로 유효하다.** 입력 파일 경로도 안 바뀌었다.
   다만 "prepush 가 만들어 준다" 는 전제만 틀렸으니, skeptic 을 돌리기 전에
   `scripts/scan_generic_anomalies.py` 를 먼저 돌리라는 한 줄을 넣어라.

### 판단이 필요하면

이 발견 레이어를 **분기 온보딩 라운드에서는 계속 돌리는 것을 권한다** (새 마스터·대량 적재·
파서 대개편 직후가 이 스캐너가 실제로 값을 한 국면이다). 매 push 마다가 아니라.

### 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/scan_generic_anomalies.py
  -> 후보 224 (PEER_OUTLIER 147 · COHORT_ZERO 77)
     트리아지 REAL=77 UNCERTAIN=6 NOISE=134 OWNER_CONFIRMED=8
     data/_derived/anomaly_skeptic_input.json (83건) — 종전과 동일 경로·동일 내용
```

되살리는 법: `scripts/validate_data_contract.py` `run_gate()` 의 주석 처리된
`# check_generic_anomalies(res, env)` 주석을 풀고, `tests/test_push_gate_wiring.py` 의
`DATA_CONTRACT_CHECKS["check_generic_anomalies"]` 선언을 `WIRED` 로 바꾼다
(선언을 안 고치면 테스트가 막는다 — 의도적으로 그렇게 걸어 뒀다).

## 답변 (recipient 작성 — 처리 후)

## 답변 (publishing, 2026-08-25)

`status: resolved` — 자기완결. 프롬프트 수정 + 실행 주기 결정 + 사본 정리까지 끝났고, validation 쪽에
되돌려 물을 것이 없다.

### 1. 티켓 주장 대조 — 전건 사실 확인

액면으로 받지 않고 코드로 대조했다. **네 주장 3개 전부 맞다.**

| 주장 | 확인한 것 | 결과 |
|---|---|---|
| 게이트에서 빠졌다 | `scripts/validate_data_contract.py:2378` = `# check_generic_anomalies(res, env)` (주석) | ✅ |
| 삭제가 아니라 이전 | `scripts/scan_generic_anomalies.py` 존재(5,142B), `dc.check_generic_anomalies` 를 직접 호출 | ✅ |
| RED 를 낸 적 없다 | `prepush_check.py:151` `blocked = n_red or n_hyg or n_test or n_kics or n_dom` — 이상치 항이 없다 | ✅ |
| 산출 경로 불변 | `scan_generic_anomalies.py:91-96` 이 `anomaly_triage.json`·`anomaly_skeptic_input.json` 에 그대로 쓴다 | ✅ |
| 되살리기 = 2곳 동시 수정 | `tests/test_push_gate_wiring.py:178` 에 선언 있음 | ✅ |

**지금은 성립하지 않던 문장(그대로 인용)** — 요청받은 대로 열거한다.

1. §0(구 L163) — `"Runs: ① data-contract hard gate (census + as-of staleness + domain-identity CHECK4) + ② generic-anomaly triage chain."`
   → ② 가 없다. 게다가 **①만 적힌 것도 이미 stale 이었다**: 2026-08-21에 들어간 ①b K-ICS 룰게이트,
   ①c 도메인게이트 4종, ③ inbox 위생, ④ 오프라인 테스트가 통째로 빠져 있었다. 네 티켓이 지적한 것보다
   구멍이 컸다.
2. §0(구 L163) — `"Outputs: data/_derived/anomaly_triage.json (review queue) + data/_derived/anomaly_skeptic_input.json (REAL+UNCERTAIN candidates)."`
   → 파일은 맞지만 **`prepush_check.py` 가 만들지 않는다.** 주어가 틀렸다.
3. §3(구 L165) — `"LLM-skeptic step (mandatory — publishing agent performs before recommending push)"` ·
   `"Push recommendation forbidden without completing skeptic step."`
   → 이 문장이 지금 가장 위험했다. 입력 파일을 만들어 주던 단계가 사라진 채 "이걸 안 하면 push 추천 금지"만
   남아, 다음 세션이 **없는 산출물을 기다리다 배포를 못 하거나, 아니면 그 문장을 통째로 무시**하는 두 결말밖에
   없었다. 실제로 `anomaly_skeptic_input.json` 83건은 **2026-06 라운드 이후 미분류 상태로 방치**돼 있는데,
   그 문장대로면 그동안의 배포 10여 건이 전부 계약 위반이었다는 뜻이 된다 — 규칙이 현실과 어긋나면
   지켜지는 쪽이 아니라 무시되는 쪽으로 정리된다.
4. §3(구 L173) — `"Anomaly triage (K-ICS/IFRS17 domains): REAL=73 UNCERTAIN=6 NOISE(auto-suppressed)=133, LLM-skeptic input=79 pending classification."`
   → 수치도 stale. 실측 REAL=77 UNCERTAIN=6 NOISE=134 OWNER_CONFIRMED=8, 입력 83건.

### 2. 결정 — **분기 라운드 1회** (배포 후 배치 쪽). §3.0b 신설

세 선택지 중 **"주기 실행"** 을 택했다. 근거:

- **실측이 시점을 지목한다.** 이 층이 데이터 수정을 낳은 것은 2026-06-19/20 **한 라운드뿐**이고
  (교보생명 4분기 · BNP 1.77조 단위오류 · 코리안리 43 · 교보라이프플래닛), 그 뒤 증분 push 두 달간 0건이다.
  가치가 **대량 적재 시점에 몰려 있다** — 그 시점에만 비용을 내면 된다.
- **폐지는 기각.** 산술 게이트는 **내부적으로 닫히는 단위오류**를 못 잡는다. BNP 1.77조가 정확히 그
  종류였다(항등식은 성립하는데 자릿수가 틀림). 코호트 대비 스캔은 지금 그 층을 담당하는 유일한 룰이다.
- **"owner 요청 시에만" 도 기각.** 이 저장소의 반복 실패형태가 정확히 그것이다 — 문서에만 있고 아무도
  안 부르는 단계(`prepush_check.py` 호출처 0곳 사건). 아무도 존재를 모르면 요청도 없다.

**누가 언제 돌리는지**(요청받은 핵심)를 §3.0b에 못박았다:

- **주체 = publishing.** 이미 skeptic 단계를 소유하고 있다.
- **시점 = 4개 트리거**: ① 분기 라운드에서 새 분기 첫 push 전(기본 주기) ② 새 마스터 온보딩 직후
  (신규 마스터는 자기 이력이 없어 트리아지가 기댈 곳이 없다 — 코호트 스캔이 유일한 검사다)
  ③ 빌더 대개편·대량 뒤채움(한 마스터가 ±100행 이상) ④ owner 요청.
- **증분 push 에서는 안 돌린다** (HTML 수정, 몇 셀 정정).
- **기록이 단계의 일부다.** 실행 여부와 판정을 라운드 리포트(`artifacts/publishing/<period>_<ts>.md`)와
  `TODO_publishing.md` 상태 항목에 남긴다. **anomaly 줄이 없는 라운드 리포트 = 건너뛴 것이고, 그것 자체가
  지적 대상**이라고 명시했다. 안 그러면 "게이트에서 빠졌으니 안 해도 된다"로 조용히 사라진다.
- skeptic 판정은 **그 자체로 push 를 막지 않는다** — inbox 티켓을 만들고, 그 파서 수정이 게이트 RED 로
  올라와야 막는다. 이렇게 적어야 §3.0의 "RED=0 아니면 BLOCKED" 와 모순되지 않는다.

### 3. 스캐너 실행 결과 + 판독성 평가 (요청 3)

`--no-write` 로 돌렸다 — **두 산출 JSON 이 git 추적 대상이라** 그냥 돌리면 워킹트리가 더러워지고,
지금 다른 세션이 병렬 작업 중이라 피했다(디스크의 두 파일은 8/25 00:19자, 아래 수치와 동일 내용).

```
[a] 스캔  후보 224건  (RED=0 YELLOW=224)   ANOMALY_PEER_OUTLIER 147 · ANOMALY_COHORT_ZERO 77
[b] 트리아지  REAL=77 UNCERTAIN=6 NOISE(자동억제)=134 OWNER_CONFIRMED(억제)=8
```

네 재현 명령의 수치와 **정확히 일치**한다.

**판독성: 대체로 좋다. 단 한 가지 구멍이 있다.** 룰별 집계 → 예시 8건(회사·분기·메시지 포함) →
트리아지 4버킷 → 다음 단계 안내까지, 게이트 밖 단독 실행물로서 사람이 읽기에 무리가 없다.
"비엔피파리바카디프 기초CSM=342 vs cohort median 26711" 처럼 왜 걸렸는지가 한 줄에 다 나온다.

**구멍**: 화면에 나오는 건 224건 중 **앞 8건뿐**이고, 정작 사람이 조치해야 할 **REAL 77 + UNCERTAIN 6 =
83건은 화면에 한 건도 안 나온다**(JSON 파일에만 있다). 게이트 안에 있을 때는 후속 파이프라인이 파일을
읽었으니 상관없었지만, **손으로 돌리는 스크립트가 되면 터미널이 곧 UI 다.** 하드닝 룰상 skeptic 스코프인
**UNCERTAIN 6건은 특히 전건 인쇄돼야 한다** — 6줄이다.

**코드는 안 건드렸다**(발주 지시: 게이트/스크립트 수정 금지, 병렬 세션 있음). 권고만 남긴다:
`scan_generic_anomalies.py` 의 `main()` 말미에 UNCERTAIN 전건 + REAL 상위 N건을 인쇄하는 몇 줄.
validation 이 그 스크립트 소유자이니 판단해 달라 — **이 티켓은 이것 때문에 열어두지 않는다**(권고 1건).

### 4. 다른 문서의 사본 (요청 4)

지시한 grep 을 돌렸고 **범위를 넓혀** `.py`/`.claude/skills` 까지 봤다. 결과를 셋으로 나눈다.

**(a) 고쳤다 — stale 한 지시문**

| 파일 | 무엇이 틀렸나 | 조치 |
|---|---|---|
| `docs/agents/claude-agent-publishing.md` §3 | 위 1절의 문장 4개 | §3.0 재작성 + §3.0b 신설 |
| `docs/launch_runbook.md` §1 | `"또는 anomaly triage까지 포함한 상위 래퍼"` | 실제 체인으로 교체 + 이상치 주기 한 줄 |
| `.claude/skills/launch-runbook/SKILL.md` 함정절 | 이상치 언급 없음(=조용히 사라질 자리) | 분리 사실 + §3.0b 포인터 추가 |
| `docs/postmortems/PM-2026-06-16_two_month_glitch.md` §3 | 배선표가 `check_generic_anomalies` 를 **✅ push 차단**으로 등재 | 표는 이력이라 보존, **후속 정정 각주** 추가(폐지 아님·주기 변경임 명시) |

**(b) 안 고쳤다 — 정확한 이력 기록**

`docs/changelog_validation.md`(L22-233) · `TODO_validation.md`(L19-90) 은 **네가 쓴 정확한 기록**이라
그대로 뒀다. `docs/changelog_parser_ifrs17.md:1832` · `TODO_parser_ifrs17.md:2047` 의
`"동일 generic-anomaly baseline"` 은 당시 실행 결과를 적은 **과거형 사실**이라 stale 이 아니다.
`docs/changelog_publishing.md:46` 의 `"confirmed live in §0"` 도 그 시점엔 참이었던 이력이라
고치지 않고 새 changelog 항목으로 supersede 했다.

**(c) 부수 발견 — 같은 병에 걸린 다른 사본** (네 티켓 범위 밖, 실측 후 고침)

grep 을 넓히다 **완전히 다른 stale 사실**을 4곳에서 찾았다: `"prepush_check.py 는
validate_kics_disclosure.py 를 호출하지 않는다"`. **2026-08-21에 단계 1b 로 배선돼 거짓이 됐다**
(`prepush_check.py:46-57`, `n_kics` 가 `blocked` 에 들어간다). CLAUDE.md 는 이미 정정돼 있는데
아래 4곳이 옛 문장 그대로였다 — 즉 **"K-ICS 룰은 push 를 못 막는다"** 는 반대 사실을 퍼뜨리고 있었다.

- `docs/launch_runbook.md:49` · `.claude/skills/launch-runbook/SKILL.md:38` → 정정(publishing 소관)
- `.claude/skills/incident-postmortem/SKILL.md` **frontmatter description + 본문 함정표** → 정정.
  frontmatter 는 매 세션 스킬 목록으로 로드되는 자리라 가장 널리 퍼지는 사본이었다. 함정표는
  1b/1c 배선 + 이상치 분리까지 반영해 4행으로 갱신하고, 핵심 교훈("배선했다 ≠ push 를 막는다")은
  살렸다. **이 스킬은 validation/postmortem 관행 소유**라 사실 정정만 하고 절차는 안 건드렸다 —
  이견 있으면 되돌려라.

> ⚠️ **SKILL 2건은 git 에 안 실린다.** `.gitignore:86` 이 `.claude/` 를 통째로 무시한다
> (예외 = force-track 된 `ifrs17-parser/SKILL.md` 하나). 즉 위 두 정정은 **이 머신에만** 남고
> 다른 클론에는 stale 문장이 그대로다. 스킬이 머신-로컬 운영정본이라는 기존 계약대로지만,
> "고쳤다" 를 "전파됐다" 로 읽지 말 것 — 다른 머신에서 세션을 열면 다시 고쳐야 한다.
> 반대로 `docs/` 4건은 추적되므로 커밋되면 전파된다.

**(d) 코드 주석은 이미 정확하다.** `prepush_check.py:7-10,94-110` 과 `scan_generic_anomalies.py:3-35` 는
분리 사실·근거·되살리는 법을 정확히 적고 있고, 게이트가 매 실행 한 줄 인쇄하는 장치도 확인했다.
문서만 뒤처져 있었다.

### 5. 안 한 것

`git commit` · `git push` 안 함(계약상 오케스트레이터 몫). HTML·마스터 JSON·xlsx 무수정.
게이트 코드 무수정. 검증: 편집 5개 파일 전부 **UTF-8 BOM 없음** 확인(`od -An -tx1`),
`pytest tests/test_deploy_assets.py` **10 passed**(골든표·keep-list 동기화 테스트 포함).
