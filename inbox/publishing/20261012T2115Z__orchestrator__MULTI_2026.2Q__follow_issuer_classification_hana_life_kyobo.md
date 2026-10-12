---
from: orchestrator
to: publishing
created: 20261012T2115Z
status: open
route: fix
company: KR0097,KR0073
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
### owner 결정 기록 (2026-10-12 채팅)
owner: 「회사에서 그렇게 분류했으면 회사 분류를 따르는 게 맞지 않나」 — 발행사가 K-ICS 공시에서 처리한 방식(항목 13-49 이 발행 때 오르는지 = 메모 `data/_derived/capital_utilization_definition_20261012/definition_memo.md` 82~93행의 X 검정, 발행사 K-ICS 표)이 우리가 발행조건·기사로 읽은 분류와 다르면 **발행사 처리를 따른다.** 기사·발행조건 해석은 등재부 비고(내부 메모)에만 남기고 화면 문장으로 쓰지 않는다. 같은 화면의 기본자본비율·지급여력비율이 발행사 공시값이라 소진율도 같은 기준이어야 한다.

### 해 줄 것
1. **등재부 갱신**(`data/bonds/capital_tier_registry.json`): 증권 `type` 을 발행사 처리 기준으로 맞춘다. 대상 확인된 2건: 하나생명 제1회(2023-03-31, 1,800억) → `tier1`(발행사는 1,799억 중 한도 초과분만 보완자본으로 재분류: 2026.2Q 항목 13-49 = 1,276 < 항목 6 = 1,799, 메모 93행과 같음), 교보 2024-11-12 6,000억 → `tier1`(`issuer_type` 과 일치시킴; 기발행분이 결속이라 교보 소진율 70.1% 는 불변이어야 함). 발행조건·기사 읽기(스텝업 등)는 비고 필드에만 남긴다. 나머지 증권은 건드리지 않되, **등재부 `tier2` 로 된 모든 증권(10개사)에 대해 발행사 처리와 일치하는지 건별로 다시 확인**해 어긋나는 건이 더 있으면 같은 원칙으로 맞추고 보고한다(총액 비교 항목 13-49 ≥ 차감액 은 증명이 아니다 — 항목 13 에는 보완자본형 증권·기본자본형 한도 초과분·기타가 섞여 있으므로 증권별 X 검정 또는 발행사 표로 판정).
2. **소진율 재산출**: `kics_tier1_utilization.json` 갱신. 기대 변화: 하나생명 기본자본 소진율 0.0 → 약 238.2(발행액 1,799 ÷ SCR×10%), 교보 불변, 다른 회사는 위 확인에서 어긋난 건이 있을 때만. 보완자본 소진율은 불변(항목 47 기반). 전후 표를 `data/_derived/capsec_reinstate_20261012/` 에 추가.
3. **Forward Outlook**: 하나생명·교보의 `baseline_basis_flag` 는 분류 기준이 같아졌으므로 필요 없어진다 — 제거하되(필드가 없을 때 designer 폴백 확인) `basic_ratio_by_type_pct` 등 새 필드가 일관되게 정리되게 한다. 총자본(지급여력비율) 경로는 불변이어야 하고, 하나생명·교보 기본자본비율 경로는 재계산·손계산 검산. 단위·변이시험 갱신(분류 변경이 이유임을 적고 느슨하게 풀지 말 것).
4. 재공개 데이터(`public_exports` 3시트·manifest·xlsx 시트)를 같은 방식으로 재생성. 게이트·시험(`validate_data_contract`·`validate_live_artifacts`·`check_master_xlsx_drift`·`tests/unit/test_capital_utilization_rules.py` 등) 한 번에 하나씩. `TODO_publishing.md` Status + `docs/changelog_publishing.md`(바뀐 필드·되돌리는 방법).

### 규칙
- 정의(분자·분모)를 바꾸지 않는다. 마스터 `kics_disclosure.json`·HTML 수정 금지, 예외 등재 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만. 이 공유 티켓은 고치지 않는다.

### 보고 (3~5줄 존댓말)
- 바뀐 증권·회사, 소진율 전후(하나생명 등), 전망 변화(총자본 경로 불변 여부), 10개사 건별 재확인 결과, 시험, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
