"""KR0068 iter-2 결과를 티켓/TODO/changelog 에 기록. UTF-8 no BOM."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TICKET = ROOT / "inbox" / "validation" / (
    "20260824T0410Z__validation__KR0068_2025.2Q__tier1_bridge_residual_unexplained.md")
TODO = ROOT / "TODO_validation.md"
CHANGELOG = ROOT / "docs" / "changelog_validation.md"

ANSWER = """

## 답변 (validation, 2026-08-24 iter-2) — **인과 규명됨. 발행사 모순이 아니라 우리 룰의 결함이다.**

§4-1(`item12` 스코프)과 §4-3(`item47` 스코프)을 끝까지 밀었다. 둘은 같은 원인의 두 얼굴이었다.
**`item12` 는 정상이다. 틀린 것은 `item47` 의 스코프를 읽는 우리 룰이다.**

### 1. 결론 한 줄

`item47`(보완자본 한도 적용 전)의 **스코프가 발행사마다 다르다.** 한화생명은 `item47` 에
`item49`(해약환급금 부족분 상당액 중 해약환급금 상당액 초과분)를 **포함해서** 인쇄하고,
한도(`item48`)는 그 나머지(채무성 자본 = `item47 − item49`)에만 걸린다. 우리 룰은 `item47` 이
채무성 자본만이라고 **가정**하고 `한도초과 = max(0, item47 − item48)` 을 쓴다. 한화생명에서는
그 값이 `item49` 만큼 과대해지고, 2025.2Q 는 **이 회사에서 한도가 실제로 구속한 유일한 분기**라
그 과대값이 다리에 그대로 들어가 −30,095 를 만들었다.

### 2. §4-3 — 원문 확인: **"한도로 안 잘림"은 오독이었다. 한도는 정상 적용된다**

`data/disclosure/FY2025_Q2/raw/KR0068_한화생명.pdf` p18 `(1) 공통적용 경과조치` (백만원,
fitz 단어좌표로 컬럼 확정 — 적용전 x≈341/347, 적용후 x≈489/494):

```
                            적용전          적용후
지급여력비율(%)              160.0          160.6
지급여력금액              22,180,868     22,263,443
기본자본                   8,250,615      8,250,615
보완자본                  13,930,253     14,012,828
 보완자본 한도 적용 전      14,012,828     14,012,828   <- 두 컬럼 같은 값
 보완자본 한도               6,930,699      6,930,699   = SCR 13,861,397 x 50%
 해약환급금...초과분         6,999,555      6,999,555
 (기발행 신종자본증권)               0
 (기발행 후순위채무)          1,649,118
지급여력기준금액            13,861,397     13,861,397
```

`한도적용전(14,012,828)` 이 `보완자본(13,930,253)` 보다 **크고**, `해약환급금(6,999,555)` 보다도
크다 → `item47` 은 **총액**이다. 채무성 부분 = `14,012,828 − 6,999,555 = 7,013,273` 이
한도 `6,930,699` 를 **82,574백만원(=825.74억) 초과**한다. 그래서

```
보완자본(적용전) = min(7,013,273, 6,930,699) + 6,999,555 = 13,930,254   (인쇄 13,930,253, 반올림 1)
보완자본(적용후) = 14,012,828  (TFI 가 한도 제약을 풀어 준 값 = 한도적용전 그대로)
```

**즉 적용후만 "안 잘린" 것이고, 적용전은 정확히 한도로 잘렸다.** iter-3 §2 의
"보완자본 = 한도적용전 그대로(한도로 안 잘림)" 은 **한도가 안 걸린 분기를 보고 관행으로
일반화한 오독**이다.

**같은 회사 이웃 분기 raw 로 반증 시도 — 반증되지 않았다**
(`scripts/_probes/probe_20260824_tfi_table_scan.py`):

| 분기 | 한도적용전 | 해약환급금 | 채무성(=차) | 한도 | 구속? | 인쇄된 보완자본 |
|---|---|---|---|---|---|---|
| 2025.1Q (p18) | 12,225,226 | 6,432,843 | 5,792,383 | 6,838,221 | 아니오 | 12,225,226 = 한도적용전 |
| **2025.2Q (p18)** | 14,012,828 | 6,999,555 | **7,013,273** | **6,930,699** | **예 (+82,574)** | **13,930,253 = 한도+해약** |
| 2025.3Q (p19) | 14,428,486 | 7,405,260 | 7,023,226 | 7,122,730 | 아니오 | 14,428,486 = 한도적용전 |

채무성 자본이 2025.1Q 5,792,383 → 2025.2Q 7,013,273 으로 뛰면서 한도를 처음 넘었고, 2025.3Q 는
SCR 상승으로 한도가 7,122,730 까지 올라 다시 안 걸린다. **13분기 중 이 한 분기만 구속한다.**
(왜 채무성이 뛰었는지는 이 표만으로 단정하지 않는다 — 기발행 후순위채무는 1,722,937 → 1,649,118
로 **줄었으므로** 신규 발행 쪽이지만, 발행내역은 이 공시에 없다.)

### 3. §4-1 — `item12` 는 정상. 대조군을 세우니 클램프가 밴드에이드였음이 드러난다

주2) 각주 그대로 계산하면 **닫힌다**:

```
기본자본 = 순자산 − (불인정 − 한도초과) − 재분류
        = 213,475 − (30,921 − 825.74) − 100,874 = 82,505.74     vs 인쇄 82,506  → 잔차 0.26
```

`한도초과 = 825.74` 이므로 `item12(30,921)` 안에 **당연히 들어간다.** 클램프
(`min(raw_exc, item12)`)가 필요했던 것은 `raw_exc` 가 애초에 틀렸기 때문이다.

**대조군(§4-1 이 요구한 나머지 9칸) — `probe_20260824_kr0068_clamp_control_group.py` 전수:**

| 회사·분기 | item12 | raw_exc | 배율 | 클램프 후 diff |
|---|---|---|---|---|
| KR0032 2026.1Q | 0.00 | 41.95 | ∞ | −1.00 |
| KR0072 2024.3Q/2024.4Q/2025.1Q/2025.2Q | 0.00 | 913.29 / 73.74 / 262.91 / 327.68 | ∞ | 0.00 / 1.00 / 0.00 / 0.00 |
| KR0072 2025.3Q | 203.00 | 203.10 | 1.00 | 1.00 |
| KR0076 2024.4Q | 1,067.00 | 1,191.20 | 1.12 | 0.00 |
| KR0076 2025.2Q | 2,015.00 | 2,015.35 | 1.00 | 1.00 |
| KR1011 2025.3Q | 513.00 | 513.09 | 1.00 | −1.00 |
| **KR0068 2025.2Q** | **30,921.00** | **70,821.29** | **2.29** | **−30,095.00** |

나머지 9칸은 배율이 1.00~1.12 이거나 `item12=0` 이라, 클램프가 사실상 아무것도 안 자르거나
`불인정항목 전액 = 한도초과` 를 표현한다. 배율 2.29 는 한화생명뿐이고 — **그 2.29 배가 바로
`item49` 를 잘못 포함시킨 결과다** (`70,821.29 − 825.74 ≈ 69,995.55 = item49`).

### 4. 반증 쿼리를 먼저 돌렸다 (§3.1 규율) — 그리고 **첫 가설은 실제로 반증됐다**

가설 "`item47` 은 모든 회사에서 `item49` 를 포함한다" 를 전수로 걸었다
(`probe_20260824_kr0068_excess_convention_sim.py`): **구성식 461칸이 깨지고 다리 31칸이
깨진다.** → **이 가설은 틀렸다. 전역 룰로 바꾸면 안 된다.**

스코프가 **회사 속성**이라는 쪽으로 좁혀 다시 전수
(`probe_20260824_i47_scope_per_company.py` · `probe_20260824_scope_aware_bridge_sim.py`):

```
회사별 스코프 투표(모호 버킷 제외):  EXCL 27사 · INCL 5사(KR0004·KR0068·KR0075·KR0079·KR0080) · CONFLICT 4사
```

원문 대조군으로 확증했다 — **IBK연금 2025.3Q(EXCL)** p16: `한도적용전 403,778` 이
`보완자본 695,572` 보다 **작고** `해약환급금 343,103` 을 따로 더한다
(`min(403,778, 352,469) + 343,103 = 695,572` 정확히 일치). **같은 행 이름이 두 관행으로
인쇄된다는 직접 증거이고, 추론이 아니라 두 PDF 를 나란히 놓은 실측이다.**

**스코프 인식 한도초과 전수 시뮬레이션 (닫힘/깨짐 양방향):**

```
cur=OK new=OK    600      새로 닫히는 칸 = 1  (KR0068 2025.2Q  −30,095.00 → 0.26)
cur=RED new=OK     1      새로 깨지는 칸 = 0
cur=RED new=RED   64
```

### 5. 그런데도 **이번 세션에서 룰을 안 고쳤다** — 이유를 박아 둔다

시뮬레이션이 1 fix / 0 break 로 깨끗해도, 이 수정은 한 커밋 안에서 **동시에** 움직여야 한다:

1. `src/solvency/validation/kics_json_rules.py::_validate_tier2_limit` 의 한도초과 계산 + `_tier2_branch`
2. `tests/test_kics_rules_golden.py` (**라이브 `kics_disclosure.json` 에 물려 있다**)
3. `scripts/validate_kics_disclosure.py::gate._TIER2_ISSUER_INCONSISTENT` 의 박제값 −30,095.0
4. `data/_gold/kics_exemption_provenance.json` 의 KR0068 항목(등재 해제)
5. `tests/test_tier2_issuer_inconsistent_exemption.py` 의 변이시험 4~6건

**지금은 다른 서브에이전트가 `kics_disclosure.json` 을 병렬로 만지고 있다.** 그 상태에서 룰
골든을 `--update` 하면 **반쯤 쓰인 마스터가 골든에 박제**되고, 나중에 그쪽 편집이 들어오면
누군가 이유를 모른 채 또 재생성한다 — 이 저장소가 이미 데인 lost-update 형태다. 그래서
**조사 결과만 남기고 룰은 손대지 않았다.**

### 6. 면제 등재 — **해제하지 않았다. 사유만 정정했다**

지금 등재를 풀면 룰이 여전히 −30,095 를 내므로 게이트가 RED 가 되어 push 가 막힌다. 순서는
**룰 수정 → RED 소멸 → 게이트가 `TIER2_EXEMPTION_INERT` 로 "등재를 풀어라" 인쇄 → 해제** 다.

`data/_gold/kics_exemption_provenance.json` KR0068 2025.2Q 에서 **자유텍스트 6곳만** 고쳤다
(`scripts/fix_20260824_kr0068_exemption_reason.py`, 실행 로그 재현 가능):

- `claim` — "인과는 규명되지 않았다" → 규명 내용 + 재현 스크립트 경로
- `claim_kind` — `ISSUER_UNEXPLAINED_RESIDUAL_OWNER_ACCEPTED` → `OUR_RULE_MISREADS_item47_SCOPE__owner_accepted_pending_rule_fix`
- `note` — **"어느 해석에서도 826/30,095 에 해당하는 항목은 원문에 없다" 는 틀렸다.** 826 은 p18 세 행에서 그대로 나온다: `(14,012,828 − 6,999,555) − 6,930,699 = 82,574백만원`. (30,095 쪽은 원문에 없는 게 맞다 — 룰의 산물이다.)
- `owner_confirmation.open_lead` — 게이트가 매 실행 인쇄하는 줄. 여기에 규명 사실을 넣어 조용해지지 않게 했다
- `scope` — "인과 미규명이므로" 삭제, INCL 5사는 면제가 아니라 룰 수정 대상임을 명시
- `release_condition` — 해제 경로를 "룰 수정" 한 가지로 확정 + 동시 갱신 대상 5개 열거

**안 건드린 것:** `status`(VERIFIED_BY_OWNER) · `expected_residual`(−30,095.0) ·
`expected_residual_alt_reading`(826.0) · `pin_tolerance`(0.01) · `verify` 마커 ·
`owner_confirmation` 의 read_by/date/what_was_read/verdict. 허용오차도 안 건드렸다.

> §5 의 "825.75 ≈ 826 으로 박제하지 말 것" 은 그대로 지켰다. 지금 적은 것은 근접이 아니라
> **원문 세 행에서 나오는 산식**이다: `(item47 − item49) − item48 = 825.74`. 그리고 그 값으로
> 다리가 `82,505.74 vs 82,506` 으로 닫힌다. 박제값 −30,095 는 **룰이 실제로 내는 값**이라 그대로 뒀다.

### 7. 검증 (재현 명령 + 실측)

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260824_kr0068_clamp_control_group.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260824_kr0068_raw_pages.py "data/disclosure/FY2025_Q2/raw/KR0068_한화생명.pdf" 16,17,18,19 kr0068_2025q2_p16_19.txt
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260824_tfi_table_scan.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260824_kr0068_excess_convention_sim.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260824_i47_scope_per_company.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260824_scope_aware_bridge_sim.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_tier2_issuer_inconsistent_exemption.py tests/test_tier2_limit_rules.py tests/test_kics_rules_golden.py tests/test_rule_coverage_manifest.py -q
  -> 142 passed
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
  -> EXIT 0 · 박제잔차=-30095.0 실측=-30095.0 Δ=+0.0 (tol 0.01) 일치
  -> RED 라인 · Top RED offenders 가 정정 **전과 완전히 동일**(diff 결과 IDENTICAL)
```

산출물: `artifacts/validation/probe_20260824_*.txt` · `kr0068_2025q2_p16_19.txt` ·
`gate_20260824_{baseline,after}.txt`.

### 8. 남은 일 (이 티켓이 계속 열려 있는 새 이유)

**"인과 미규명" 이 아니라 "룰 수정 대기" 다.** 원장 `open_ticket` 이 이 파일을 가리키므로
`_resolved/` 로 옮기지 않는다(게이트가 매 실행 이 경로를 인쇄한다).

착수 조건: `kics_disclosure.json` 을 만지는 세션이 없을 것. 작업은 §5 의 5개 파일 한 커밋.
**착수 전 `probe_20260824_scope_aware_bridge_sim.py` 를 그날 마스터로 다시 돌려 1 fix / 0 break
가 유지되는지 재확인할 것** — 마스터가 바뀌면 이 수치도 바뀔 수 있다.

status: **open 유지** (사유 교체: 인과 미규명 → 룰 수정 대기)
"""

TODO_BLOCK = """**(2026-08-24 iter-2, KR0068 한화생명 2025.2Q 인과 규명) 🟢 `2_tier1_bridge` 잔차 −30,095 의
원인은 **발행사 모순이 아니라 우리 룰의 결함**이었다. `item47`(보완자본 한도 적용 전)의 스코프가
발행사마다 다르다 — 한화생명은 `item49`(해약환급금 초과분)를 **포함**해 인쇄하고 한도는 나머지
채무성 부분에만 걸리는데, 룰은 `한도초과 = max(0, item47 − item48)` 로 `item49` 만큼 과대계산한다.
raw 3분기 + EXCL 대조군(IBK연금 2025.3Q) 실측으로 확증. 스코프 인식 시뮬레이션 = **1 fix / 0 break**.
**룰은 안 고쳤다** — 골든이 라이브 마스터에 물려 있고 다른 세션이 그 마스터를 만지는 중이라
lost-update 위험. 면제도 **해제하지 않고 사유만 정정**(해제하면 RED → push 차단). 게이트 exit 0,
RED 카운트 무변화, 142 tests pass. 상세·재현·후속 착수조건:
`inbox/validation/20260824T0410Z__validation__KR0068_2025.2Q__tier1_bridge_residual_unexplained.md` §답변 iter-2.**

"""

CHANGELOG_BLOCK = """## 2026-08-24 (iter-2) — KR0068 한화생명 2025.2Q `2_tier1_bridge` −30,095 의 인과 규명

**결론: 발행사 자기모순이 아니었다. 우리 룰이 `item47` 의 스코프를 잘못 가정하고 있었다.**

`item47`(보완자본 한도 적용 전)이 `item49`(해약환급금 부족분 상당액 중 해약환급금 상당액
초과분)를 포함하는지 여부가 **발행사마다 다르다.** 룰은 "포함하지 않는다"만 알고
`한도초과 = max(0, item47 − item48)` 을 쓴다. 한화생명은 포함하는 관행이라 그 값이 `item49`
만큼 과대해진다(70,821.29 대신 825.74).

원문 실측(`data/disclosure/FY2025_Q2/raw/KR0068_한화생명.pdf` p18, 백만원):
`한도적용전 14,012,828 − 해약환급금 6,999,555 = 채무성 7,013,273 > 한도 6,930,699`
→ 초과 **82,574(=825.74억)** → `보완자본 = 6,930,699 + 6,999,555 = 13,930,254`(인쇄 13,930,253).
주2) 각주대로 `213,475 − (30,921 − 825.74) − 100,874 = 82,505.74` vs 인쇄 `82,506` → **잔차 0.26**.

- **13분기 중 한도가 실제로 구속하는 분기는 2025.2Q 하나뿐이다.** 2025.1Q 채무성 5,792,383 <
  한도 6,838,221 · 2025.3Q 7,023,226 < 7,122,730. 그래서 나머지 12분기는 `item3 == item47` 이
  되어 룰이 `UNCAPPED`(한도초과=0)로 우연히 맞혔고, 구속하는 그 한 분기만 `CAPPED` 로
  오분류돼 과대 한도초과가 다리에 들어갔다.
- **iter-3 §2 의 "보완자본 = 한도적용전 그대로(한도로 안 잘림)" 는 오독이었다** — 한도가 안
  걸린 분기를 관행으로 일반화한 것. 적용후만 안 잘리고 적용전은 정확히 잘린다.
- **`item12` 는 정상.** 클램프(`min(raw_exc, item12)`)는 틀린 `raw_exc` 를 가린 밴드에이드였다.
  클램프 발동 10칸 대조군에서 배율이 1.00~1.12 인 9칸과 달리 한화생명만 2.29 배이고,
  `70,821.29 − 825.74 ≈ 69,995.55 = item49` 로 그 차이가 정확히 `item49` 다.

**가설을 먼저 반증했다(§3.1 규율).** "모든 회사가 포함 관행" 가설은 전수에서 구성식 461칸 ·
다리 31칸을 깨뜨려 **기각**. 회사 속성으로 좁힌 뒤 전수 투표 = EXCL 27사 · INCL 5사
(KR0004·KR0068·KR0075·KR0079·KR0080) · CONFLICT 4사. 원문 대조군 **IBK연금 2025.3Q(EXCL)**
p16 은 `한도적용전 403,778 < 보완자본 695,572` 로 정반대 구조를 인쇄한다 — 두 관행이 같은 행
이름으로 존재한다는 직접 증거.

**스코프 인식 한도초과 전수 시뮬레이션: 새로 닫히는 칸 1 · 새로 깨지는 칸 0**(나머지 600칸 무변화).

**그런데 룰은 고치지 않았다.** 이 수정은 ① 룰엔진 ② `test_kics_rules_golden.py`(라이브 마스터에
물림) ③ 게이트 박제값 ④ 면제 원장 ⑤ 변이시험 4~6건을 **한 커밋에서 동시에** 움직여야 하는데,
당시 다른 세션이 `kics_disclosure.json` 을 편집 중이었다. 그 상태로 골든을 `--update` 하면
반쯤 쓰인 마스터가 박제된다(이 저장소의 lost-update 전례). → 후속 티켓으로 이월.

**면제는 해제하지 않고 사유만 정정했다** (`scripts/fix_20260824_kr0068_exemption_reason.py`).
지금 풀면 룰이 여전히 −30,095 를 내므로 RED → push 차단이다. 자유텍스트 6곳
(`claim`·`claim_kind`·`note`·`open_lead`·`scope`·`release_condition`)만 고치고 박제값·status·
마커·허용오차는 무변경. 특히 `note` 의 **"어느 해석에서도 826/30,095 에 해당하는 항목은 원문에
없다" 를 반증으로 정정**했다 — 826 은 p18 세 행에서 산식으로 나온다.

실측: `validate_kics_disclosure.py` exit 0, RED 라인·Top RED offenders 가 정정 전후 **완전 동일**,
`pytest` 142 passed. 프로브 5종 + raw 덤프는 `scripts/_probes/probe_20260824_*` ·
`artifacts/validation/probe_20260824_*.txt`.

"""


def main() -> None:
    # --- 티켓: 기존 내용 삭제 없이 추가 + frontmatter iter 갱신 -------------
    t = TICKET.read_text(encoding="utf-8", newline="")
    nl = "\r\n" if "\r\n" in t else "\n"
    t2 = re.sub(r"^iter: 1[\r]?$", "iter: 2", t, count=1, flags=re.M)
    assert t2 != t, "frontmatter iter 갱신 실패"
    t2 = t2 + ANSWER.replace("\n", nl)
    TICKET.write_text(t2, encoding="utf-8", newline="")

    # --- TODO: Status 절 맨 위에 삽입 --------------------------------------
    td = TODO.read_text(encoding="utf-8", newline="")
    nl2 = "\r\n" if "\r\n" in td else "\n"
    anchor = f"## Status{nl2}{nl2}"
    assert td.count(anchor) == 1, "TODO Status 앵커를 못 찾았다"
    td = td.replace(anchor, anchor + TODO_BLOCK.replace("\n", nl2), 1)
    td = re.sub(r"^> Last updated: [^\r\n]*$",
                "> Last updated: 2026-08-24 (iter-2 KR0068 인과 규명) · Stage 3/5 — validation",
                td, count=1, flags=re.M)
    TODO.write_text(td, encoding="utf-8", newline="")

    # --- changelog: 첫 '## ' 헤딩 앞에 삽입 --------------------------------
    cl = CHANGELOG.read_text(encoding="utf-8", newline="")
    nl3 = "\r\n" if "\r\n" in cl else "\n"
    m = re.search(r"^## ", cl, flags=re.M)
    assert m, "changelog 에 '## ' 헤딩이 없다"
    cl = cl[:m.start()] + CHANGELOG_BLOCK.replace("\n", nl3) + cl[m.start():]
    CHANGELOG.write_text(cl, encoding="utf-8", newline="")

    for p in (TICKET, TODO, CHANGELOG):
        assert p.read_bytes()[:3] != b"\xef\xbb\xbf", f"{p} BOM"
    print("OK: ticket + TODO + changelog updated (UTF-8, no BOM)")


if __name__ == "__main__":
    main()
