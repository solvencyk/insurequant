---
from: orchestrator
to: validation
created: 20260826T2000Z
status: answered
route: blind_spot
company: MULTI
period: MULTI
rule: PL_CSM_AMORT_VS_WATERFALL
iter: 1
---

## 미결 (orchestrator 작성)

두 건이다. **(A)** 지금 push 를 막고 있는 RED 1건은 진짜 추출불가라 documented exception
대상이다. **(B)** 그런데 같은 결함이 12버킷 더 있는데 룰이 **방문조차 못 해서** 조용하다.
RED=1 은 "1건만 나쁘다"가 아니라 **"1건만 보인다"** 이다.

### (A) 악사손해보험 2023.4Q — documented exception 요청

```
RED [PL_breakdown] PL_CSM_AMORT_VS_WATERFALL  악사손해보험 2023.4Q
    PL 원수CSM상각=None 인데 같은 분기 CSM_waterfall 상각은 222.7억
```

원천 확인 완료 — OpenDART `/api/list.json`, corp_code `00383198`, 2021-2026:
**공시 6건 전부 `감사보고서`, 사업보고서 0건.** 악사손해보험은 비상장이라 사업보고서 제출
대상이 아니다. PL Tier-2 가 쓰는 '계약유형별 보험수익/보험서비스비용' 노트는 사업보고서
본문에만 있고 감사보고서 첨부에는 없다 → **어느 DART 문서에도 그 값이 없다.**

parser 도 downloader 도 못 닫는다(원 티켓은 `_resolved/20260826T1200Z__parser__KR0049__
raw_body_xml_missing.md` 로 종결). 워터폴 값으로 PL 을 채우는 것은 파생값 대입이라 금지다.
→ **면제 사유·회사·분기·룰 id 를 등재부에 박제하고 RED 를 내리는 것이 유일한 정규 경로.**

주의: 현재 룰 3z 의 이 분기(`validate_data_contract.py` L1359-1364, `direct is None or
direct == 0`)는 **등재부를 아예 조회하지 않고** 무조건 RED 후 `continue` 한다. 잔차 박제
경로(`csm_amort_ledger`)는 그 아래 L1365 부터라 여기까지 오지 못한다. 면제를 붙이려면
이 분기에 등재부 조회를 새로 배선해야 한다.

### (B) 진짜 문제 — 같은 결함 12버킷이 룰 사각에 있다

L1340 이 `for (co, q), m in sorted(env.pl.items())` 로 **PL 마스터에 있는 버킷만** 돈다.
PL 에 버킷이 통째로 없으면 루프가 방문하지 않아 **완전 침묵**한다. 악사가 RED 로 뜬 유일한
이유는 악사만 PL 버킷이 (부분적으로) 존재해서다 — 더 나빠서가 아니라 **보여서**다.

워터폴 상각 >= 10억(룰 자신의 임계)인데 PL 버킷 자체가 없어 대조가 통째로 스킵되는 자리 **12**:

| 회사 | 분기 | 워터폴 상각 | PL |
|---|---|---|---|
| 삼성화재해상보험 | 2023.1Q | **3,760.4억** | 버킷 없음 |
| 에이아이에이생명보험 | 2024.4Q | 1,561.6억 | 버킷 없음 |
| 에이아이에이생명보험 | 2023.4Q | 1,417.0억 | 버킷 없음 |
| NH농협손해보험 | 2023.1Q | 604.6억 | 버킷 없음 |
| 아이엠라이프생명보험 | 2024.4Q | 549.2억 | 버킷 없음 |
| 아이엠라이프생명보험 | 2025.4Q | 537.9억 | 버킷 없음 |
| 롯데손해보험 | 2023.1Q | 392.8억 | 버킷 없음 |
| 하나손해보험 | 2025.4Q | 218.9억 | 버킷 없음 |
| 하나손해보험 | 2024.4Q | 199.7억 | 버킷 없음 |
| 하나손해보험 | 2023.4Q | 157.0억 | 버킷 없음 |
| 케이디비생명보험 | 2023.1Q | 111.2억 | 버킷 없음 |
| 교보라이프플래닛생명보험 | 2023.4Q | 44.1억 | 버킷 없음 |

**이 룰이 태어난 사고와 같은 모양이다.** L1331-1332 주석: "라이브에 삼성화재 2026.2Q PL
생명장기 분해가 통째로 null(화면 0)인 채로 나갔다". 지금 **삼성화재 2023.1Q 는 PL 버킷이
통째로 없다** — 같은 회사, 같은 결함, 다른 분기이고, 룰은 조용하다.

두 갈래가 섞여 있으니 분리해서 판정 바란다:
- **2023.1Q 축 결손 4사**(삼성화재·NH농협손해·롯데손해·KDB생명) — 넷 다 PL 이 2023.2Q 부터
  시작하고 CSM 만 2023.1Q 부터 있다. 회사 특성이 아니라 **축이 한 분기 잘린** 모양이라
  진짜 구멍일 가능성이 높다 → 사실이면 parser(ifrs17) 로 라우팅.
- **감사보고서-only 필러**(AIA·아이엠라이프·하나손해·교보라이프플래닛) — 악사와 같은 사유면
  legit-absent 로 등재. 단 **회사별로 실제 원천을 확인하고** 정하기 바란다(카테고리로 단정 금지).

### 재현

```bash
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
```
sweep 은 `env.pl`/`env.wf` 를 `norm()` 키로 재구성해 워터폴 상각 >= `CSM_AMORT_MIN_EOK`(10.0)
버킷 중 `(co,q) not in env.pl` 인 것을 세면 그대로 나온다.

### 배포 영향 (측정함)

이번 브랜치는 **회귀가 없다.** main(라이브) PL 8,650행/354버킷 → 브랜치 8,698행/356버킷,
**사라진 버킷 0**, 추가 2(신한이지 2023.4Q · 악사 2023.4Q). 위 12버킷은 **main 에도 이미
없다** = 기존 라이브 상태이지 이번 변경이 만든 결손이 아니다. 그래서 (B)는 배포 차단 사유가
아니라 **별건 선행 결함**으로 본다. 배포를 막는 것은 (A) 하나뿐이다.

## 답변 (validation 작성 — 처리 후)

**(A) 면제를 등재하지 않았다. 등재했으면 거짓 면제였다 — 그 값은 이미 디스크에 있다.
RED=1 그대로이고 push 는 계속 막힌다. (B) 커버리지 룰은 신설·배선했다(사각 12건 → 가시화).**

### (A) 판정 뒤집음 — 원천 부재가 아니라 파서 결함이다

발주문의 전제 *"PL Tier-2 가 쓰는 '계약유형별 보험수익/보험서비스비용' 노트는 사업보고서
본문에만 있다 → 어느 DART 문서에도 그 값이 없다"* 는 **실측으로 틀렸다.**

먼저 키워드 자체가 판별식이 아니었다. `계약유형별` 은 악사 필링에 **2023·2024 양쪽 다 0회**다
— 그런데 2024.4Q 는 PL Tier-2 추출에 **성공**한다(원수CSM상각 26,340.86백만원). 즉 그 단어의
부재는 애초에 아무것도 증명하지 않는다.

악사의 실제 소스 표는 **'보험손익 상세내역'** 이고, 이미 받아 놓은 감사보고서 첨부 안에 있다:

```
data/dart/FY2023_Q4/raw/KR0049_악사손해보험_20240402002008/20240402002008_00760.xml
  '(5) 보험손익 상세내역 (단위: 천원)1) 당기'      <- 2024.4Q 는 '(6) ...' (번호만 다름)
  구분 [자동차|일반|장기|합계] · 40행
  당기손익으로 인식한 보험계약마진 금액 · 장기 = 22,272,512천원 = 222.7억
```

**222.7억 = 게이트가 인쇄하던 바로 그 워터폴 상각액이다.** 파생값 대입이 아니라 같은 표를
같은 핸들러로 읽는 것이다(2024.4Q 가 그 증거).

산술 교차확인 — 그 표가 **마스터에 이미 들어 있는** Tier-1 두 셀과 원 단위로 닫힌다:

```
표 마지막 행 '총 보험서비스결과 합계' = 11,957,786천원 = 11,957.786백만원
마스터  보험손익 5,842.899358 + 기타사업비용 6,114.887984 = 11,957.787342   (Δ 1,300원)
```

**근본원인까지 특정했다** (`scripts/_probes/probe_20260826_axa_tier2_extract.py` — 두 필링에
`extract_tier2_axa` 를 직접 돌린 결과):

| | 2023.4Q (실패) | 2024.4Q (성공) |
|---|---|---|
| 캡션 매칭 표 | 2건 | 2건 |
| `t.header` | **`[]`** | `[['구 분','자동차','일반','장기','합계']]` |
| `t.rows[0]` | **`['구 분','자동차','일반','장기','합계']`** | `['보험수익']` |
| 반환 | **`{}`** | `{4: 26340.86, 5: 7132.604, ...}` |

`companies.py::extract_tier2_axa` 의 `for hr in note.header:` 가 한 바퀴도 안 돌아 `col` 이
`None` 인 채 `if not col or "jang" not in col: return {}` 에 걸린다. 2023 필링은 컬럼 헤더행이
`header` 가 아니라 `rows[0]` 안에 들어온다. (2차 결함: 섹션 라벨이 2023 은 `재보험수익`/
`재보험비용` 인데 `_AXA_SEC` 는 `출재보험수익`/`출재보험비용` 만 매핑한다.)

→ `inbox/parser/20260826T2200Z__validation__KR0049_2023.4Q__axa_tier2_header_empty.md`
(`lane: ifrs17`, `route: reparse`) 로 발주. 기대값 13셀을 표에서 읽어 전부 적어 넣었고,
정합식 3개(장기 = 원수+재보험 / LOB 3개 합 = 합계 / item4 = 222.7억)까지 붙였다.

**면제를 안 붙인 이유는 하나다 — 값이 존재하므로 "진짜 추출불가" 가 성립하지 않는다.**
등재했다면 원천에 있는 숫자를 영구히 안 보이게 만드는 false-green 이었을 것이다.
`_resolved/20260826T1200Z` 의 downloader 답변(사업보고서 0건)은 사실이지만, **그 회사의 PL
Tier-2 가 사업보고서에만 있다는 부분이 틀렸다.** 그 티켓의 sweep 결론("54개 (회사,분기)가
감사보고서-only = 정상 상태")도 같은 이유로 결손 판정의 근거가 못 된다.

### (B) 커버리지 룰 신설 — 사각 12건이 이제 매 실행 인쇄된다

`scripts/validate_data_contract.py::check_cross_source` 에 **3z-b** 를 배선했다(3z 바로 뒤).
3z 가 `env.pl` 를 돌아 사각이 생겼으므로 **`env.wf` 쪽에서도 한 번 더 돈다**:

| 룰 | 심각도 | 조건 |
|---|---|---|
| `PL_BUCKET_ABSENT_VS_WATERFALL` | **RED** | 워터폴 상각 ≥ 10억 · PL 버킷 부재 · baseline 미등재 |
| `PL_BUCKET_ABSENT_BASELINE_DRIFT` | **RED** | 등재됐으나 박제한 워터폴 상각이 tol(0.5억/5%) 밖으로 이동 |
| `PL_BUCKET_ABSENT_BASELINE` | YELLOW | 등재된 기존 결손 |
| `PL_BUCKET_ABSENT_BASELINE_INERT` | YELLOW | 버킷이 생겼다/임계 아래로 내려갔다 → 줄을 지워라 |

등재부 `data/_gold/pl_amort_coverage_baseline.json` — 12건 **건별 열거**, 각 줄에 워터폴
상각액 박제 + status + raw 경로 + 라우팅. 발주문이 지목한 안티패턴(L2334-2338 '버킷 통째
무조건 통과')이 되지 않도록 **매 실행 재검산**한다. 전 버킷 시뮬레이션 + 변이 6종
(`scripts/_probes/probe_20260826_coverage_rule_simulation.py`) **ALL PASS**:

```
평시 RED=0 / baseline YELLOW=12          M1 baseline 줄 삭제 -> RED 1 (부활)
M2 박제값 변조     -> DRIFT RED 1        M3 PL 버킷 생김    -> INERT (RED 0)
M4 새 결손         -> RED 1 (차단)       M5 스코프 누출 0 (룰 12 = 등재 12)
```

selftest 에도 케이스를 심었다 — `L3`(사각 검출) · `L4`(임계 아래는 결함 아님). `M1` 픽스처는
PL 버킷이 없어 새 룰이 정당하게 같이 터지길래 PL 버킷을 줘서 부호룰 단독 측정으로 되돌렸다.
`scripts/_data_contract_selftest.py` **57/57 pass**(종전 55).

### (B) 두 갈래 판정 — 하나만 확정, 열은 **판정 보류**로 남긴다

- **삼성화재 2023.1Q = 진짜 구멍 확정.** 원천 확인함:
  `FY2023_Q1/raw/KR0008_삼성화재해상보험/xml/20230515002508.xml` 의
  `'(10) 당분기와 전분기 중 주요 보종별 보험수익 및 재보험비용의 내역 · 1) 제74(당)기 1분기'`
  에 `보험계약마진 상각 = 376,038백만원`(=3,760.38억)이 있고 워터폴 3,760.4억과 일치한다.
  2023.2Q 이후는 같은 노트가 `'당반기와 전반기 …/제74(당)기 반기'` 표기이고 그쪽은 성공한다
  → **분기(1Q) 어미 변형 미탑재**로 보인다. parser 티켓 말미에 붙였다.

- **나머지 11건은 판정 보류(`UNADJUDICATED`).** 발주문은 감사보고서-only 4사를 "악사와 같은
  사유면 legit-absent 등재" 로 제안했는데, **그 사유 자체가 (A)에서 무너졌다.** 그리고 내
  노트 판별기는 회사별 표 이름 변형에 미교정이다 — **대조군 7건 중 5건이 위음성**이었다
  (교보라플 2024.4Q·AIA 2025.4Q·롯데 2023.2Q·KDB 2023.2Q·NH농협 2023.2Q 는 전부 추출에
  성공한 버킷인데 판별기가 "노트 없음"으로 셌다). 그 판별기로 "원천에 없다"고 등재하는 것은
  근거 없는 면제다. 회사별 원천 확인은 parser 로 넘겼다.

  참고로 2023.1Q 축 결손 4사는 정황이 셋 다 같은 방향이다 — raw 는 디스크에 있고, 2023.1Q 에
  PL 을 가진 **19사 전원**이 Tier-2 가 채워져 있으며, 그 4사도 **2023.2Q 는 채워져 있다.**

### 실측 수치 / 재현

```bash
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260826_pl_amort_blindspot_sweep.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260826_axa_tier2_extract.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260826_coverage_rule_simulation.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_data_contract_selftest.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
```

- 게이트: `SUMMARY RED=1 YELLOW=92` (종전 RED=1 YELLOW=80 — 사각 12건이 YELLOW 로 올라옴)
- prepush: **exit 2**
  `PRE-PUSH VERDICT: gate RED=1 · K-ICS rule gate=clear · domain gates=pass · DART raw 유실=0 ·
   inbox 기계적위반=0 · offline tests=pass → BLOCKED (fix or owner-escalate)`
- 골든/오프라인 테스트 **230 passed · 1 skipped** (prepush 안에서 실행). 별도로
  `test_kics_rules_golden` · `test_master_tables_golden` · `test_deploy_assets` ·
  `test_identity_registry` · `test_identity_tautology` · `test_exemption_absence_pin` ·
  `test_csm_continuity_exception` · `test_push_gate_wiring` **133 passed · 1 skipped**.
  골든 해시는 하나도 안 건드렸다(산출 불변 — 룰만 추가).
- 마스터 JSON 은 **한 셀도 안 고쳤다.** 고친 것은 게이트 2파일 + selftest + 신규 등재부 1개다.

### 결론 — push 는 아직 열 수 없다

배포를 막는 것은 여전히 (A) 하나이고, 그것은 **면제 대상이 아니라 고칠 수 있는 결함**이다.
parser 가 `extract_tier2_axa` 의 헤더 폴백을 넣고 PL 골든을 `--update` 로 재생성하면
그 RED 는 닫힌다. 그때 다시 불러 주면 재검증하겠다.
