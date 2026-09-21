---
from: publishing
to: validation
created: 20260921T0335Z
status: open
route: propose
company: ALL
period: N/A
rule: USER_FACING_META_TEXT (proposed)
iter: 1
---

## 미결 (sender 작성)

원 티켓: `inbox/publishing/20260921T0320Z__owner__ALL__internal_jargon_in_public_exports.md`
(owner, 2026-09-21) — `public_exports/자본비율전망.json`의 `비고` 610여 행에
`compute_confidence()`(`scripts/forward_capital_simulation.py`)의 내부 게이트 진단
문자열(필드명 `subordinated_eok`·`tier1_hybrid_issued_eok`·`numerator_eok_fallback`,
게이트 용어 `advisory, not in overall`)이 그대로 노출돼 있었다.

**처리 완료**(이 티켓의 목적은 그 재발 방지 검사 신설 제안이지 그 자체 수정 요청이 아니다):
- `scripts/build_master_xlsx.py::_flatten_forward_capital()`에서 `conf["reasons"]`를
  `비고`에 join하던 지점을 고쳐 `비고`에는 사용자 문구만 남기고, 원문 reasons는 신설
  컬럼 `_diagnostics`로 분리(커밋 `44ae5fb`).
- `scripts/export_public_sheets.py`의 `_DROP_COLS`에 `_diagnostics` 추가 — 공개
  다운로드에서만 제외, 내부 마스터 xlsx(`insurequant_master_tables.xlsx`)에는 남음.
- `insurequant_master_tables.xlsx` "자본비율전망" 시트 sync(커밋 `a61c8b2`), 마스터
  JSON은 무변경 확인(숫자 셀 이동 0, 키셋 동일, 값 불일치 0 — cell-level diff 완료).
- `public_exports/자본비율전망.json` 재생성(커밋 `c130062`) — jargon 행 660 → 0 확인.

### 제안: 같은 유형(내부 게이트 진단 문자열의 공개 산출물 유출) 재발 방지 검사

`public_exports/*.json`의 **사용자용 자유텍스트 컬럼**(`비고`·`구분` 등)에 필드명·영문
게이트 용어가 섞이면 잡는 검사. 배선 위치는 owner/validation 판단 — `validate_data_contract.py`
CHECK 추가든 별도 스크립트든.

**정규식 후보** (owner가 이미 낸 예시 기준, 필요시 조정):
```
r"advisory,\s*not\s+in\s+overall"       # 게이트 용어 그대로
r"\b[a-z][a-z0-9_]*_eok\b"              # 필드명 패턴: xxx_eok (subordinated_eok, tier1_hybrid_issued_eok, numerator_eok_fallback 등)
r"\bT[12]\s+(face/BS|FSC)\s+gap\b"      # "T1 face/BS gap", "T2 FSC gap" 류
r"\blimit breach\b"                      # "> 100 (limit breach)"
```
스캔 대상 컬럼: 각 시트별로 자유텍스트 성격의 열만(`비고`·`구분` — `build_master_xlsx.py`의
`TEXT_COLS`에서 식별자성 열 제외하고 "설명/코멘트류"만 추려야 함, 전체 TEXT_COLS를 스캔하면
`항목명`·`위험구분` 같은 정상 한글 라벨도 걸릴 수 있음).

### 알려진 false-positive 2건 (스캔 설계 시 반드시 넣을 것 — 정규식이 이 둘을 안 건드리는지 확인)

이 둘은 원 티켓이 "내부 용어가 아니라 데이터 단서"로 판정해 **건드리지 않은** 항목이다:

1. `public_exports/가정민감도.json` `비고`: `"같은 충격이 이 회사 표에 2벌 있다(재보험 경감
   전/후로 추정, 원문 라벨 미확인) — 순번으로 구분"` (10행) — 순수 한글, 위 정규식 후보들과
   매칭 안 됨(확인됨).
2. `public_exports/자본성증권발행현황.json` `구분`: `"… 후순위 명시 라벨 없음, 구조 기반
   추정"` (3행) — 마찬가지로 순수 한글, 매칭 안 됨(확인됨).

두 문자열 모두 위 4개 정규식 후보에 매칭되지 않음을 이 티켓 처리 중 직접 대조했다(문자열
검색으로 "eok"·"gap"·"advisory"·"breach" 부재 확인) — 검사를 배선할 때 이 둘을 fixture로
넣어 회귀시키면 됨.

### 시킬 일 (validation 판단)

1. 위 검사를 어느 게이트에 넣을지 결정 (`validate_data_contract.py` 신규 CHECK vs
   `check_inbox_hygiene.py`류 별도 스크립트 vs `test_deploy_assets.py`류 골든).
2. 정규식 후보를 실제 13개 `public_exports/*.json` 전체에 먼저 시뮬레이션해 현재 RED/
   false-positive 규모를 파악(이 티켓은 시뮬레이션 없이 후보만 제안한 상태).
3. 배선 후 이 두 false-positive 케이스를 회귀 fixture로 등재.

## 답변 (recipient 작성 — 처리 후)
