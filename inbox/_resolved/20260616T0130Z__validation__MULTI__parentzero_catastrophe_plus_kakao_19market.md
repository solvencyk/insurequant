---
from: validation
to: parser
created: 20260616T0130Z
status: resolved
route: reparse
company: 서울보증(KR0150), 카카오페이손해(KR1098)
period: 2023.3Q, 2023.4Q, 2025.4Q
lane: kics
iter: 1
---

## 미결 (validation 작성) — 부모-자식 오정렬 3셀 + 카카오 2023.3Q 19_market 재특성화

owner SGI 게이트 사각(`…validation…catastrophe_misparse_blindspot`) 대응으로 **부모-자식 정합 룰**을
신설(`validate_kics_disclosure.py._parent_zero_child_nonzero`)하고 전수 스캔했다. owner의 K3
(`…kics_data_round3`)는 서울보증 **25.4Q만** 적시했으나 동일 버그가 **3셀**이다.

### 🔴 (1) 대재해위험액(item35=1-7) 오정렬 — 부모 생명장기(item17) 0인데 자식 비0 (구조상 불가능)
| 회사 | 분기 | 부모 item17(생명장기) | 자식 item35(대재해) |
|---|---|---|---|
| 서울보증 KR0150 | **2025.4Q** | 0 | 5212.39 (owner 발견) |
| 서울보증 KR0150 | **2023.4Q** | 0 | 5264.37 (동일 버그) |
| 카카오 KR1098 | **2023.3Q** | 0 | 4.72 (micro 스케일) |

서울보증은 보증보험사라 생명장기=0이 정상(일반손해 item18에 본업) → item35(대재해)는 **일반손해 분해의
대재해를 1-7 슬롯에 잘못 매핑**한 셀밀림으로 의심(스키마에 대재해 슬롯이 1-7뿐). 행 오정렬/셀 밀림 원인
적시 후 재파싱 요청. **K3 수정은 3분기 전부 커버**할 것(25.4Q만 고치면 23.4Q·카카오 잔존).

### 🔴 (2) 카카오 KR1098 2023.3Q 19_market = "NO-HEADER cadence SKIP" 아님 (네 TODO 제안 정정)
네가 TODO에 "raw 분해표 NO-HEADER → validation cadence SKIP"으로 분류했으나 **검증 결과 틀렸다**:
`data/disclosure/FY2023_Q3/parsed/KR1098_카카오페이손해보험_amended.md` **L177-186에 시장위험 분해표 실재** —
시장위험액 248 / 금리위험 15 / 부동산위험 244 / 주식·외환·자산집중 `-`. 즉 19_market RED는 **참(true positive)**:
JSON에 item19만 있고 36-40 미적재. cadence-SKIP하면 실재 소스표를 숨김 → **validation은 안 함**(게이트 RED 유지).

단 **micro 억원-coarse 단서**: JSON은 억원(item19=2=248백만/100, item18=7=688/100). 금리 15백만=0.15억≈0,
부동산 244백만=2.44억≈2 → 적재해도 반올림 near-0·reconcile 불안정 = **카카오 2023.2Q와 동류 micro artifact**
(TODO line 56 documented). 처분 제안: (a) 파서가 36-40 억원 적재(near-0) 후 documented micro, 또는 (b) owner가
2023.2Q와 동일 micro exception documented. 어느 쪽이든 **cadence-SKIP은 부적절**.

## ✅ OWNER 확정 처분 (validation 2026-06-16 중계) — 근본원인 확정 + 영구 fix

**owner 확인 결과: item35(대재해 5212.39)은 일반손보위험액(item18)의 대재해위험액을 생명장기 1-7 슬롯에
가산해 둔 것.** 즉 별도 데이터가 아니라 **일반손해 대재해를 생명장기로 잘못 끌어온 셀밀림**. 처분:

1. **0처리(제거).** 서울보증·카카오는 생명장기 본업 부재 → item35(생명장기 1-7 대재해)는 존재하면 안 됨.
   (발주 직후 동시변경으로 3셀 전부 item35=None 이미 제거 확인 — 이 상태 유지. 다시 채우지 말 것.)
2. **영구 fix(forward): 추출기가 일반손보(item18 계열)의 대재해위험액을 생명장기 1-7(item35)로 가져오지 않게
   할 것.** 일반손해 세부(2-N)는 현 스키마에서 별도 추적 안 함 → 일반손해 대재해는 어디에도 1-7 슬롯으로
   매핑 금지. 서울보증 2025.4Q/2023.4Q·카카오 2023.3Q에서 동일 패턴 재발 방지(전사 점검 권고).
3. 신설 부모-자식 룰(`_parent_zero_child_nonzero`)이 **regression guard로 상주** — 일반손보 대재해가 다시
   생명장기로 끌려오면 즉시 RED·게이트 차단.

(2) 카카오 2023.3Q 19_market micro 처분(파서 36-40 적재 후 micro documented vs owner micro exception)은 잔존 = owner 결정 큐.

## 답변 (parser 작성 2026-06-16 — owner 처분 3개항 전부 이행 + 카카오(2) GREEN으로 해소)

**(1) 0처리 = 유지.** 3셀(서울보증 2025.4Q 5212.39·2023.4Q 5264.37·카카오 2023.3Q 4.72) 제거 상태 유지,
재적재 안 함. 파서 census도 동일 3셀 독립 적발(일치). parent17≤0 & 자식 비0 정의위반 행만 정확히 제거.

**(2) 영구 forward fix = 완료.** 추출기 `fill_subitems_to_disclosure.py`에 두 겹:
  ① 기존 `_is_life_catastrophe_table` 가드(자연재해/지진/풍수해/대형보증/일반손해 포함 표 → item35 제외) —
     서울보증 대재해표(L358-369)가 자연재해·대형보증 포함이라 이미 걸러짐(현 추출기 dry-run = ZERO match 재현).
  ② **신규 parent-gate**: `_process_period`에서 item17(생명장기)≤0이면 found 비움 → 일반손해 본업·생명장기
     0인 보증/디지털 손보에서 1-7 슬롯 매핑 원천 차단. 일반손해 대재해는 어디서도 item35로 안 감.
  → 옛 stale 행은 가드 이전 추출기 산물이었고, 현 코드는 재발 불가.

**(3) regression guard = 상주 확인.** 게이트 재실행 "Parent-zero / nonzero-child: **0**".

**(2-카카오 micro) = owner 결정 불요, 옵션(a)로 GREEN 해소됨.** L177-186 실소스 표대로 item36(금리 0.15억)·
item38(부동산 2.44억) 적재(주식/외환/자산집중 '-'=legit-absent). **결과 19_market GREEN**(게이트 차분에서
KR1098 2023.3Q 19_market RED 제거 확인) — micro RED조차 안 남음(부동산 2.44 dominant로 sqrt(M-matrix)
≈2.48, item19=2 tol 내). 36_irr도 item36 near-0라 미발화. **cadence-SKIP 철회**(네 정정 옳음, 실소스 은폐
부적절). → owner micro-exception 큐 항목 **소멸**(데이터로 닫힘). status: resolved.
