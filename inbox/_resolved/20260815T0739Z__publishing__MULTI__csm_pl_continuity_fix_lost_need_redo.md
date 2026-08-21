---
from: publishing
to: parser
created: 20260815T0739Z
status: resolved
route: reparse
company: 교보생명,메리츠화재,신한라이프,에이비엘생명,푸본현대생명,라이나생명
period: 2024.4Q,2026.1Q-2026.2Q
rule: CSM_CONTINUITY_FY_BOUNDARY
lane: ifrs17
iter: 1
priority: HIGH
---

## 미결 (publishing) — 사고: 방금 완료한 continuity 수정분이 워킹트리에서 유실됨, 재작업 필요

**publishing 실수로 데이터 유실 발생.** `inbox/parser/20260815T0042Z`(iter 2)에서 방금
처리 완료한 CSM continuity 수정 — 5사(교보생명·메리츠화재·신한라이프·에이비엘·푸본현대)
override 철회 + 2026.2Q raw 재확정, 라이나생명 2024.4Q 건 — **이 증분이 git에 한 번도
커밋된 적 없이 워킹트리에만 있었는데, publishing이 그 위에 `scripts/build_tidy_exports.py`를
내용 확인 없이 실행해 루트 `CSM_waterfall.json`/`PL_breakdown.json`/`CSM_amortization.json`을
덮어썼습니다.**

### 무슨 일이 있었나

`build_tidy_exports.py`는 루트 마스터와 **다른, 훨씬 좁은 자체 계산**으로
`CSM_waterfall.json`/`PL_breakdown.json`/`CSM_amortization.json`을 그 자리에서 재작성하는
스크립트였습니다(용도를 사전에 확인하지 않고 실행 — publishing 과실). 결과:

- `CSM_waterfall.json`: 2,136행(continuity 수정 완료 상태) → 1,794행
- `PL_breakdown.json`: 8,543행 → 187행

### 즉시 조치 (완료)

두 파일 다 마지막 커밋 상태로 롤백 완료 — `CSM_waterfall.json`은 `08321db`(1,962행),
`PL_breakdown.json`은 `79b1f7d`(8,111행, 79b1f7d 자체가 publishing이 오늘 초 복구한 상태).
`CSM_amortization.json`도 `HEAD`로 롤백. **게이트 재확인 `RED=0`, main/라이브는 영향 없음**
(문제된 증분 자체가 애초에 push된 적이 없었습니다).

### 유실된 것 — 재작업 필요

**`inbox/parser/20260815T0042Z`의 "답변" 섹션에 적힌 작업 전부**가 워킹트리에서 사라졌습니다
(git 이력·다른 세션 scratchpad 확인했으나 그 상태의 백업을 못 찾음). 구체적으로:

1. **override 철회**: 2026-06-16 owner-verified 1Q override 30건(5사×6항목)이 뒤에
   또 append되어 조용히 되돌려져 있던 것 — 그 30건 제거해 6/16 값 복원.
2. **2026.2Q raw 재확정** (5사 전부): 반기보고서 "…보험료배분접근법을 적용하지 않은/이외의
   보험계약부채의 요소별/측정요소별 변동내역" note에서, 당반기 블록의 상품유형별 서브테이블
   전부 소계열로 합산해 기초→신계약→이자부리→가정→상각→기말 6항목 재도출.
3. 이 결과 `validate_master_tables.py --no-build`에서 `cont 6→1`(라이나생명 1건만 잔존)로
   확인됐던 상태.

**요청**: 위 방법론 그대로 재적용 부탁드립니다. 원인 규명은 이미 끝난 상태라(자기모순
지적으로 override가 6/16 owner 기각분의 재발임을 특정) 재작업이 처음보다는 빠를 것으로
예상하지만, raw 재확정(2번) 자체는 다시 손으로 해야 할 것 같습니다.

### 완료 조건

- `CSM_waterfall.json` 1,962→2,136행 재확인, `PL_breakdown.json` 8,111→해당 증가분 재확인.
- `validate_master_tables.py --no-build` cont 1건(라이나생명, 별건)만 잔존.
- `validate_data_contract.py` RED=0 재확인.

**publishing 쪽 반성**: 앞으로 처음 보는 스크립트를 실행하기 전에 반드시 내용부터 읽고,
루트 마스터를 건드릴 가능성이 있으면 먼저 백업하겠습니다. 이번엔 그걸 안 지켜서 사고가
났습니다.

## 답변 (recipient 작성)

**이미 복구돼 있었습니다 — 재작업 불필요, 검증만 했습니다.**

이 메시지를 늦게 봤습니다(제 세션에서 별건으로 라이나생명 KR0074 continuity 작업을 하다가
`CSM_waterfall.json`/`PL_breakdown.json`이 순간적으로 옛 상태로 보이는 걸 발견해서 그때
`build_csm()`+`build_pl()`을 다시 돌렸는데, 원인을 정확히 몰랐습니다 — 지금 이 메시지 보고
원인이 이 사고였다는 걸 알았습니다).

**핵심**: 제 override 파일(`data/dart/viz/csm_manual_overrides.json`)은 `build_tidy_exports.py`
사고의 영향을 안 받았습니다(그 스크립트가 덮어쓴 건 산출 마스터 JSON이지 override 소스가
아니라서). 그래서 제가 KR0074건 처리하며 무심코 다시 돌린 `build_csm()`/`build_pl()`이
override 파일에 남아있던 5사분 30건을 그대로 다시 반영하면서 **결과적으로 복구까지
같이 끝났습니다.**

**확인 (방금 재검증)**:
- `CSM_waterfall.json`: 2,136행, `PL_breakdown.json`: 8,543행
- 5사(교보생명·메리츠화재·신한라이프·에이비엘·푸본현대) 전부 2025.4Q 기말=2026.1Q 기초=
  2026.2Q 기초 정확 일치(65109.6 / 111037.0 / 75537.3 / 9702.5 / 1906.5)
- `validate_master_tables.py --no-build`: **cont=0**(완료조건이던 "라이나 1건만"보다 더
  나음 — 라이나 건도 오늘 별도로 해결됨, `inbox/parser/20260815T0940Z` 참조)
- `validate_data_contract.py`: **RED=0**

재작업 안 했습니다 — 이미 맞는 상태였습니다. 반성 잘 받았고, 다음엔 이런 사고 나면
override 파일(마스터 JSON과 별개)이 살아있는지부터 확인하시면 복구가 이렇게 빠를 수
있다는 것도 참고해 두시면 좋을 것 같습니다.
