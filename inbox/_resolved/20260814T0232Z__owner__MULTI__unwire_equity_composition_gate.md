---
from: owner
to: validation
created: 20260814T0232Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (sender 작성)

**owner 지시 (2026-08-14): `equity_composition.json`(항목 1-49) 아카이브.** 17BS 정본은
**`IFRS17_BS.json`**(항목 1-5 = 자산/부채/자본/AOCI/해약환급금준비금) 한 벌이 된다.
파서 발주: `inbox/parser/20260814T0232Z`.

**직전 발주 `20260814T0216Z` 를 이걸로 대체한다** — 거기 V-1(흐름 등식 4개 해제)은 아카이브로
자동 소멸하니 따로 손댈 필요 없다. 아래만 하면 된다.

### 할 일

1. **게이트에서 `equity_composition` 도메인을 걷어내라.**
   `validate_data_contract.py` 의 `check_equity_composition` · `Env.MASTER_FILES["equity_composition"]` ·
   `_load_equity_findings` · `_equity_is_published`. **`scripts/validate_equity_composition.py` 는
   파서가 옮기는 아카이브 묶음에 같이 넣어라**(되살릴 때 룰이 통째로 붙어 있게).
2. **그 자리에 `IFRS17_BS.json` 을 등록하라. 룰은 딱 하나.**
   - `BS_IDENTITY`: 항목 1(자산총계) == 항목 2(부채총계) + 항목 3(자본총계) → **RED**
   - census 코어 = **항목 1·2·3·4** 결측 = RED. **항목 5·6·7(준비금 3종)은 optional** — owner
     원문 *"가능하면 찾아서 추가하되 안 되면 pass"*. 코어로 올리지 말 것.
   - 그 외 **아무것도 만들지 마라.** 자본총계 폐쇄식(1=2+3+4+5+6+7)은 `IFRS17_BS.json` 에
     자본 세부항목이 없으니 성립하지 않는다 — 대신 파서가 AOCI 태그를 채택할 때 자체 검산하도록
     `20260814T0216Z` P-2 에 못박아 뒀다.
3. `data/_gold/equity_census_exceptions.json` · `equity_value_overrides.json` — 새 게이트가 안 쓰면
   파서 아카이브 묶음으로 같이 보내라. **삼성생명 예외가 등재돼 있으면 반드시 빼라**
   (`20260814T0216Z` V-3: OFS 전환으로 소멸해야 하는 건이다).

### 기대 결과

**RED 21 → 0.** 내역: 롤포워드 6 + AOCI 결측 13 = 아카이브로 소멸 / 삼성생명 2 = 파서 OFS 전환으로 소멸.
남는 건 `IFRS17_BS.json` 의 BS 항등식뿐이고, OFS 기준에선 캐시 254건 전수 위반 0건이다.

### 확인

- `validate_data_contract.py --selftest` 통과(케이스 수가 줄어드는 건 정상 — 몇 개가 왜 줄었는지 답신에)
- `pytest tests/test_deploy_assets.py` 통과
- 라이브 게이트 재실행 RED/YELLOW 수치

### 하지 말 것

- **새 룰 금지.** 이번엔 지우는 작업이다.
- 룰 파일을 지우지 말고 **아카이브로 이동**(나중에 되살린다).

## 답변 (recipient 작성)

**(validation, 2026-08-14T05:00Z) 완료 — 게이트 RED 21 → 0. 지시대로 줄이는 작업만 했다(신규 룰 0개).**

### 1. `equity_composition` 도메인 철거

`scripts/validate_data_contract.py` 에서 4곳 전부 제거: `check_equity_composition` ·
`Env.MASTER_FILES["equity_composition"]` · `_load_equity_findings` · `_equity_is_published`
(+ `Env.equity_findings` / `equity_published` 필드와 그 inject 격리 분기).

`archive/2026-08_equity_composition/` 신설 + 3개 이동(전부 미커밋 신규파일이라 `git mv` 아님):

| 파일 | 원위치 |
|---|---|
| `validate_equity_composition.py` | `scripts/` |
| `equity_census_exceptions.json` | `data/_gold/` |
| `equity_value_overrides.json` | `data/_gold/` |

`README.md` 도 같이 넣었다(왜 아카이브했는지 + 되살리는 절차 3단계). 빌더·골든은 parser 몫이라
안 건드렸다.

**삼성생명 예외는 애초에 등재된 적이 없다** — `equity_census_exceptions.json` 전문 확인,
`KR0069`/`삼성생명` 0건(등재 항목은 2023.1Q-2Q 전사 013 · KR0150 · Tier-2 15개사뿐).
V-3 위반 없음.

### 2. `IFRS17_BS.json` 등록 — 룰 둘뿐

`MASTER_FILES["IFRS17_BS"]` 등록(mtime 감시 포함) + `check_ifrs17_bs()` 신설:

| rule | 식 | 비고 |
|---|---|---|
| `BS_IDENTITY` | 항목1(자산총계) == 항목2(부채총계) + 항목3(자본총계) | 허용오차 max(1백만원, 0.1%) — 종전 `EQ_BS_IDENTITY` 와 동일 |
| `BS_CENSUS_MISSING_ITEM` | 코어 1·2·3·4 결측 | 5·6·7(준비금 3종)은 **검사 안 함** |

그 외 아무것도 안 만들었다. 자본총계 폐쇄식은 지시대로 미구현(세부항목이 없다).
심각도는 **기존 방식 그대로 배포 fetch 여부**가 정한다(0216Z V-5): 지금은 어떤 HTML 도
`IFRS17_BS.json` 을 안 읽으므로 **YELLOW**, designer 가 `IFRS17.html:267` 을 갈아끼우는 순간
**코드 수정 없이 RED 로 자동 승격**된다.

### 3. 확인 결과

| 항목 | 전 | 후 |
|---|---|---|
| `validate_data_contract.py` RED | **21** | **0** (exit 0) |
| YELLOW | 396 | 259 |
| `--selftest` | 22/22 | **25/25** |
| `pytest tests/test_deploy_assets.py` | 1 FAIL | **1 FAIL (동일건, 내 소관 아님 — 아래 5)** |

**selftest 케이스는 줄지 않았다.** equity 도메인을 태우는 케이스가 **원래 0개**였기 때문이다
(2026-08-14 의 0/22 붕괴는 케이스가 아니라 `Env` 의 inject 격리 누락 때문이었고 그때 고쳤다).
대신 **3개 늘렸다** — `I1 BS_IDENTITY` / `I2 BS_CENSUS_MISSING_ITEM` / `I3 미배포면 YELLOW`.
이 마스터에 남은 룰이 딱 둘이라 조용히 죽으면 17BS 검사축이 통째로 사라진다(키 이름만 바뀌어도
0건이 된다). **룰 신설이 아니라 발주된 룰의 회귀보호**이고, "지우는 라운드" 취지에 어긋난다고 보면
`scripts/_data_contract_selftest.py` 의 I1-I3 세 줄만 빼면 된다.

### 4. 지금 `IFRS17_BS.json` 이 내는 40건 (전부 YELLOW — 미배포라 push 안 막음)

| 무엇 | 셀 | 회사·분기 | 처분 |
|---|---|---|---|
| Tier-2 본문 XML 이 **item5(해약환급금준비금)만** 뽑음 → 1·2·3·4 통째 결측 | 20 | AIG(2025.4Q) · 메트라이프(2024.4Q·2025.4Q) · IBK연금(2024.4Q·2025.4Q) | parser |
| Tier-2 가 **item4 만** 뽑음 → 1·2·3 결측 | 6 | 하나손해보험 · 신한이지손해보험 (각 2025.4Q) | parser |
| **AOCI(4) 결측** = P-2 태그 조건부 채택 대상 | 12 | 한화생명 3(2023.4Q·2024.4Q·2025.1Q) · 흥국생명 5(2025.1Q-2026.1Q) · AIA생명 3 · 아이엠라이프 1 | parser (P-2) |
| `BS_IDENTITY` | 2 | 삼성생명 2025.2Q·3Q (자산 318,858,553 3분기 동일 = stale CFS) | parser (P-1 OFS 고정). **예외 등재 안 했다** |

→ `inbox/parser/20260814T0500Z__validation__MULTI__ifrs17_bs_census_and_identity.md` 로 발주.
전부 소스 라우팅이고 값 보정은 0건이다.

### 5. 남은 FAIL 1건 — designer/publishing 대기 (내가 못 고치는 자리)

```
claude-agent-designer.md never mentions equity_composition.json (fetched by IFRS17.html)
```

`IFRS17.html` 이 아직 `equity_composition.json` 을 fetch 하고 있어서 나는 테스트다.
owner 가 이미 `inbox/designer/20260814T0232Z`(Panel 7 repoint) · `inbox/publishing/20260814T0232Z`
(keep-list swap)로 발주했고, 그 둘이 끝나면 풀린다. HTML·stage 문서는 내 소관이 아니라 안 건드렸다.

내가 어제 보냈던 `20260814T0135Z` 2건(= "표에 `equity_composition.json` 을 넣어라")은 이제
**틀린 지시**라 양쪽 다 `status: superseded` 로 바꾸고 상단에 경고를 달았다 — 그대로 따르면 곧
사라질 파일을 keep-list 에 올린다.

### 6. parser 가 알아야 할 함정 1개

`scripts/build_equity_composition.py:169` 가 `data/_gold/equity_value_overrides.json` 을 읽는데
그 파일을 지시대로 아카이브로 옮겼다. **빌더를 아카이브하기 전에 돌리면** KR0032 2024.4Q item30
부호 override 가 조용히 빠져 골든이 흔들린다. 순서상 그냥 **아카이브부터** 하면 된다
(parser 티켓에도 적었다).

### 7. owner 판단 요청 1건 — census 의 회사축

새 census 는 **"마스터에 행이 있는 (회사,분기)"** 안에서만 코어 1-4 를 요구한다. 그래서
**회사가 통째로 빠지면 안 잡힌다**: 지금 `kics_disclosure` 39사 중 `IFRS17_BS.json` 에 행이
**0건인 회사가 2사**(KR0075 비엔피파리바카디프생명 · KR1098 카카오페이손해보험)인데 RED/YELLOW
0건이다. 기대 그리드(39사 × 표시 7분기)로 올리면 이 2사는 잡히지만 366셀이 뜨고, 그걸 누르려면
방금 아카이브한 예외 레지스트리가 다시 필요해진다 — "줄이는 라운드"에 정면으로 어긋나서
**이번엔 안 붙였다.** 회사축을 살릴지는 owner 판단.

(참고: 마스터에 2022.4Q·2023.3Q·2026.2Q 행도 있지만 게이트 census 는 기존 규칙대로 화면 표시
7분기만 본다 — 2026.2Q 는 아직 배포 대상이 아니다.)

---

**재검증 종결 (validation, 2026-08-14T06:20Z).** 게이트 독립 재실행으로 확인: `validate_data_contract.py` **RED=0 / YELLOW=261**(exit 0) · `--selftest` **25/25** · `pytest tests/test_deploy_assets.py` **1 FAIL**(designer/publishing 대기건 1개뿐, validation 소관 아님). 파서 재빌드(`IFRS17_BS.json` 14:42) 반영 후 17BS findings 40→42이고 삼성생명 `BS_IDENTITY` 2건·한화생명/흥국생명 AOCI 8건은 **소스 수정으로 소멸 확인**(예외 등재 0건). 잔여 42건 델타는 `inbox/parser/20260814T0620Z…ifrs17_bs_delta_after_ofs_rebuild.md`(iter 2). → `status: resolved`, `_resolved/` 이동.
