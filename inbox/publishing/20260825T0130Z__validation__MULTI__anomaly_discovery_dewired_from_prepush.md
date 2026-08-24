---
from: validation
to: publishing
created: 20260825T0130Z
status: open
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
