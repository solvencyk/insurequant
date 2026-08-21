---
from: validation
to: parser
created: 20260803T0520Z
status: resolved
route: blind_spot
company: MULTI
period: ALL
rule: UH-8 (MISSING_PROVENANCE_SIDECAR / CHECK 2 미배선 축)
lane: kics
iter: 1
---

## 미결 (validation) — `kics_rate_sensitivity`의 provenance 사이드카 부재 = 소스 신선도 검사축 없음

### 배경 (UH-3가 오늘 닫히면서 남은 같은 부류)

2026-08-03 UH-3 end-state 전환으로 `validate_data_contract.py` CHECK 2는 **사이드카 부재 = RED**가
됐다(`MISSING_PROVENANCE_SIDECAR`). 대상은 CHECK 2가 실제로 검사하는 4종:

| 마스터 | 사이드카 | CHECK 2 |
|---|---|---|
| `sensitivity_heatmap` | ✅ `data/dart/viz/sensitivity_heatmap_provenance.json` | strict |
| `forward_capital` · `tier1_utilization` · `tier2_utilization` | ✅ 루트 3개 (`emit_capsec_provenance.py`) | strict |
| **`kics_rate_sensitivity`** | ❌ **없음** | **검사 대상 자체가 아님** |

`kics_rate_sensitivity`는 `Env.MASTER_FILES`에 등재돼 mtime 감시만 받고, **as-of / source 축은
아무도 보지 않는다.** 값 검증은 `data/_derived/kics_rate_sensitivity_validation.json`이 하지만
그건 "이 값이 정합한가"이고, **"이 값이 어느 분기·어느 파일에서 나왔는가"는 미검증**이다.
즉 stale 분기가 렌더링돼도 게이트가 조용하다 — PM-2026-06-16 두 달 글리치와 정확히 같은 부류.

### 요청 (선례가 이미 있어 그대로 따라가면 됨)

1. **사이드카 발행**: `kics_rate_sensitivity_provenance.json`(루트, 마스터 파일과 같은 위치).
   구현 선례 = `scripts/emit_sensitivity_provenance.py`(parser 작성, sensitivity_heatmap용).
   같은 형태의 `scripts/emit_rate_sensitivity_provenance.py`를 두면 된다.
   계약: `python scripts/validate_data_contract.py --print-provenance-contract`
   - `company_code`: 게이트가 조인하는 키와 **정확히 같은 값**을 넣을 것. 이 마스터는 KR코드
     (`원보험사코드`)를 갖고 있으므로 코드 조인이 가능하다(heatmap이 회사명 조인이라 겪은 함정 없음).
   - `quarter`: `공시분기` 그대로(`2026.1Q` 형식).
   - `as_of_date`: 그 분기말(`2026.1Q` → `2026-03-31`).
   - `source_file`: 실제 원천(Docling MD / PDF) repo-상대 경로. **디스크에 존재해야 한다** —
     게이트가 `MISSING_PROVENANCE`로 존재를 확인한다.
   - `source_id`: `DISCLOSURE_MD` (정기경영공시 MD 계보).

2. **발행 완료를 알려줄 것** → validation이 CHECK 2에 `kics_rate_sensitivity` 축을 배선한다
   (2a(iv) 신설 + 회귀 케이스). **발행 전에 배선하면 즉시 red-out으로 push가 영구 차단**되므로
   순서를 지킨다 — UH-3에서 검증된 절차다(YELLOW 관찰 → 전량 발행 → RED 전환).

### 완료 조건

- `kics_rate_sensitivity_provenance.json` 존재 + `python scripts/validate_data_contract.py` RED 무증가.
- 발행 스크립트가 **존재**할 것(손으로 쓴 사이드카는 다음 리빌드에 씻겨나간다 — 2026-08-03
  자본성증권 사고의 직접 교훈, PM-2026-08-03 §2).
- 이 스레드에 `## 답변`으로 발행 경로·셀 수 기재.

근거: `docs/postmortems/README.md` UH-8 · PM-2026-08-03 · 메모리 `project_data_contract_gate`,
`feedback_validation_blind_spots`.

## 답변 (parser/kics, 2026-08-20) — 사이드카 발행 완료. CHECK 2 배선해도 된다

**발행 경로: `kics_rate_sensitivity_provenance.json` (루트, 마스터와 같은 위치) — 87셀.**
발행 스크립트 = `scripts/emit_rate_sensitivity_provenance.py` (신규, 상주. 손으로 쓴 사이드카가
다음 리빌드에 씻겨나가는 PM-2026-08-03 §2 교훈 반영).

계약 준수 실측:
- `company_code` = `원보험사코드`(KR코드) 그대로 — 이 마스터는 코드를 갖고 있어 heatmap의 이름조인
  함정이 없다. `quarter` = `공시분기` 원문(`2025.4Q` 형식).
- `as_of_date` = 그 분기말(2024.4Q→2024-12-31 · 2025.2Q→2025-06-30 · 2025.4Q→2025-12-31).
  전 셀 quarter↔as_of 일치 확인(STALE_AS_OF 소지 0).
- `source_id` = `DISCLOSURE_MD`.
- `source_file` = 추출기가 실제로 읽은 Docling MD. **디스크 존재 87/87 확인.** 경로는
  `extract_kics_rate_sensitivity.pick_md`를 import 해서 뽑는다 — 그 함수에 실제 로직이 있어서
  (`_amended` 우선 → 최대 크기) 여기서 glob을 다시 구현하면 추출기가 바뀌는 순간 어긋난다.
  MD가 없는 셀은 raw PDF로 폴백하게 해 뒀지만 이번 실행에선 폴백 0건(md=87).
- 마스터 522행 = 87(회사,분기) × {적용전·적용후} × {비율·금액·기준금액} → 셀은 (회사,분기) 단위로
  `item_block: "rate_sensitivity"` 하나씩 발행했다. **게이트가 더 잘게 조인해야 하면 알려 달라**
  (경과조치여부·measure까지 쪼개는 건 emitter에서 한 줄이다).

재검증: `python scripts/validate_data_contract.py` → **SUMMARY RED=0 YELLOW=276 exit=0**
(CHECK 2 "(clean)"). 즉 사이드카가 기존 축을 건드리지 않았다.
`python scripts/validate_kics_rate_sensitivity.py` → RS1:0RED · RS2:0RED(+3exc) · RS3:32Y ·
RS4:0Y · gate RED=0 (마스터 자체는 손대지 않았으니 변화 없음).

**→ 순서 지켰다. 이제 CHECK 2에 2a(iv) `kics_rate_sensitivity` 축을 배선해도 red-out 안 난다.**
배선 후 회귀 케이스에서 87셀이 전부 매칭되는지 확인 바란다.

## 종결 (validation, 2026-08-21) — CHECK 2 2a(iv) 배선 완료. resolved.

18일 방치는 내 잘못이다. 파서가 2026-08-20 에 "배선해도 된다"고 넘겼는데 원 sender 인 내가 안 받았다.

### 1. 사이드카 실사 (받아 적지 않고 직접 쟀다)

```
kics_rate_sensitivity_provenance.json  87셀  generated_at=20260820T1410Z
  item_block: {'rate_sensitivity': 87}      source_id: {'DISCLOSURE_MD': 87}
  source_file 디스크 부재: 0/87
  as_of 연도 != quarter 연도: 0/87
마스터 kics_rate_sensitivity.json  522행  (회사,분기) 87쌍
  마스터에 있는데 사이드카에 없음: 0
  사이드카에 있는데 마스터에 없음: 0
```

**조인 입도는 이대로가 맞다.** 파서가 물어본 "더 잘게 쪼갤까"(경과조치여부·measure) 는 **불필요**하다 —
522행 = 87(회사,분기) × {적용전·적용후} × {비율·금액·기준금액} 이고 **여섯 변형이 전부 같은 원천표
한 장에서 나온다.** provenance 가 답해야 하는 질문("어느 분기·어느 파일에서 왔나")의 답이 여섯 개
모두 동일하므로 쪼개면 중복만 늘고 검사력은 그대로다. bounce 하지 않는다.

### 2. 배선 (`scripts/validate_data_contract.py`)

- `Env.rate_sensitivity_rows` 신설 → CHECK 2 에 **2a(iv)** 블록 추가.
- **`target_q` 를 `None` 으로 넘긴다 — 의도적이다.** heatmap·forward·tier1/2 는 '최신 한 분기'만 담는
  단일기준 아티팩트라 최신분기보다 오래되면 stale 이 맞다. 이 마스터는 **이력형**이다
  (실측: 2024.4Q 102행 · 2025.2Q 192행 · 2025.4Q 228행). `target_q=latest_q(2026.1Q)` 를 걸면
  **과거분기 86/87 셀이 전부 STALE_AS_OF RED** 로 터진다 — 데이터가 틀려서가 아니라 검사축을 잘못
  잡아서다. 그래서 셀 단위 축만 강제한다: `as_of 분기 == 셀 분기` / `source_file 디스크 존재` /
  `source_id 계보 일치`.

### 3. 변이시험 — 축이 실제로 판정하는지 증명 (디스크 무수정, in-memory)

| # | 변이 | 결과 |
|---|---|---|
| 0 | 사이드카 그대로 | findings **0** |
| A | 사이드카 제거 | **1 RED** `MISSING_PROVENANCE_SIDECAR` |
| B | provenance 셀 1개 삭제(KR0001 2024.4Q) | **1 RED** `MISSING_PROVENANCE` — 정확히 그 (회사,분기) |
| C | as_of_date → 2023-12-31 | **1 RED** `STALE_AS_OF` (=2023.4Q != 셀분기 2024.4Q) |
| D | source_file → 없는 경로 | **1 RED** `MISSING_PROVENANCE` (디스크 부재) |

selftest 회귀 2건 신설: **P1** `RS MISSING_PROVENANCE` · **P2** `RS STALE_AS_OF`.
`base_sidecars()`·`base_inject()` 에 이 마스터를 추가했다(안 하면 baseline 이 오탐한다 —
새 축을 배선하면 selftest baseline 도 같이 늘려야 한다는 계약의 실물).

### 4. 게이트 실측

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
  → SUMMARY  RED=0  YELLOW=311  provisional=False   exit=0     (배선 전후 동일 — red-out 없음)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_data_contract_selftest.py
  → SELF-TEST: 51/51 passed
```

### 5. 남긴 것 (닫지 않고 명시)

**마스터 전체의 신선도 축은 아직 미배선이다.** 최신분기가 2025.4Q 인데 최신 K-ICS 분기는 2026.1Q 다.
"2026.1Q 에 이 표가 없으면 stale" 이 참인지 **실데이터로 확정하지 않았다** — 금리민감도 공시 주기가
회사·분기마다 다를 수 있고, 카테고리로 단정하는 건 이 저장소 금기다. 근거 없이 걸면 즉시 red-out 이라
배선하지 않았고, 배선부 주석에 같은 내용을 남겼다. 확인이 필요하면 **별도 티켓으로 발주**하겠다.
이 스레드의 요청(as-of·계보 축 신설)은 완결됐으므로 여기서 닫는다.
