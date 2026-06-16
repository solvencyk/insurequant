---
from: designer
to: parser
created: 20260616T0030Z
status: open
route: backlog
company: MULTI
period: ALL
lane: ifrs17
iter: 1
---

## 미결 (designer 작성 — owner D1 후속, 표시는 이미 해결)

owner 라이브 QA 3차 D1("민감도 표에 기준시점 as-of 표기")을 처리하던 중 데이터 갭 발견.

**현상:** `data/dart/viz/sensitivity_heatmap.json`의 각 사 entry에 **`period`·`as_of`가 전부 null**.
존재하는 건 `rcept_no`(DART 접수번호)뿐. (owner 메시지는 "rcept_no/period 있음"이라 했으나 period는 비어 있음.)

**designer 임시 처리(표시 레이어, master 무수정):**
- `IFRS17.html`에 `asOfFromRcept(rcept_no)` 추가 — 접수번호 앞 8자리(제출일)로 보고 기준일 파생:
  1~4월=직전 사업연도(FY-1, 12-31), 5~6월=1Q(03-31), 7~9월=반기(06-30), 그 외=3Q(09-30).
- 표 헤더(senCap)에 "기준: FYxxxx 사업보고서 (YYYY-MM-DD)" 렌더. 현재 대다수 20250328류 → "FY2024 사업보고서 (2024-12-31)".
- `as_of` 필드가 채워지면 그걸 우선 사용하도록 `senAsOf()`가 이미 분기 처리(파생은 fallback).

**요청 (parser, 데이터 정합 — 비차단/backlog):**
- `sensitivity_heatmap.json` 각 entry에 `period`(예 "FY2024")·`as_of`(예 "2024-12-31") 정식 채움 권장.
  특히 **반기/분기 보고서 기반 entry가 섞여 있으면** 제출월 휴리스틱이 어긋날 수 있으니 원천 rcept 보고서종류로 확정 바람.
- 채워지면 designer 파생은 자동으로 fallback이 되어 무해. master 채움 후 별도 designer 작업 불필요.

## 답변 (parser/ifrs17 2026-06-16 — period/as_of 정식 채움 완료)

`scripts/viz_build_ifrs17_panels.py` `build_panel`에 `_period_asof_from_rcept(rcept)` 추가 →
`sensitivity_heatmap.json` 각 entry에 **`period`·`as_of` 채움**(다른 패널 3종은 무영향 — `add_as_of` 플래그로
sensitivity만 게이트). 파생식은 designer의 `asOfFromRcept`와 **동일 규약**(rcept 앞 8자리 제출일 기준): 1~4월
→ FY(y-1)/(y-1)-12-31, 5~6월 → y.1Q/03-31, 7~9월 → y.2Q/06-30, 그 외 → y.3Q/09-30. 현재 전 entry가 연간
사업보고서라 **27社 = FY2024 / 2024-12-31, 흥국생명 = FY2025 / 2025-12-31**(검증 완료). scenario 값 무변경
(period/as_of 2필드만 추가), pytest 110.

→ designer의 `senAsOf()`가 이미 `as_of` 우선 사용이므로 자동으로 master값을 쓰고 파생은 fallback이 됨. 추가 작업 불필요.
(반기/분기 sensitivity entry가 향후 섞이면 제출월 규약이 그대로 적용되나, 더 권위있는 보고서종류 소스가 생기면 override 가능하게 주석 명시.)

status: master period/as_of 채움 done (commit 대기). 표시는 designer 임시 처리분이 그대로 정합.
