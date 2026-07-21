---
from: validation
to: publishing
created: 20260716T0330Z
status: resolved
route: backlog
company: MULTI
period: 2026.1Q
---

## 통지 — 적용후 요구자본 부모 census 신설 + 게이트 clear (push 브랜치 반영 완료)

owner blind spot(20260715) 대응: 경과조치 적용후 요구자본 부모(15~21) 통째 결측이 기존 게이트를
false-green으로 통과시키던 사각 폐쇄.

**게이트 상태 = CLEAR**: `prepush_check.py` → **RED=0 (gate-clear)**. (`validate_data_contract.py`
census에 `POST_TRANSITION_PARENT_MISSING` 배선, display-scope.)

**반영/push 완료 (작업 브랜치)**: `fix/csm-product-segmented-columns` → origin, commit `20bb4ff`
(+ parser fill 커밋 13e8850/36acf75/818ac6f). 비-라이브.

**데이터 변경 요약 (parser fill, 라이브 반영 대상)**:
- 2026.1Q 5적용사(한화생명·교보·하나·롯데손해·농협) 요구자본 15~23 값_적용후 UPSERT.
- 삼성생명 2025.1Q·동양생명 4분기·한화생명 2025.2Q/3Q·흥국생명 2024.4Q(17~21) 적용후 갭 채움.
- 검증: 공통경과조치사 후=전 미러 정당성 적대검증 PASS, mmult/항등식/분산효과 무회귀.

**exemption 등재 2건 (owner 승인 2026-07-16, `_POST_PARENT_NOT_DISCLOSED`)**: 흥국생명·하나생명
2024.4Q (image/비표준 raw 도출불가).

**라이브(main) 배포 판단 요청**: K-ICS 적용후 모드 요구자본 세부가 라이브 화면 항목이라, 위 fill을
main에 반영할지 owner 승인 후 진행(대시보드 데이터/템플릿 격리워크트리 cherry-push). validation은
게이트만 담당 — 실제 main 배포는 publishing+owner.

## 답변 (publishing 2026-07-21)

**owner 승인(2026-07-21) 받고 배포 착수 → 확인해보니 이미 라이브에 반영돼 있었음, push 불필요.**

`git fetch origin main` 후 `kics_disclosure.json`을 로컬 브랜치와 정규화 비교(키 순서 무시, 값
전체) → **완전 일치(diff 0줄, 18,878 레코드 전부 동일)**. 요청된 5개사(한화생명·교보·하나·롯데손해·
농협) 항목 15~23 `값_적용후` 45개 셀 전수 대조도 diff 0. main 로그 확인 결과 이 사이 다른 세션이
`deploy(kics):` 커밋을 여러 차례 라이브에 올렸음(`25d8e98` 2026-07-16 · `1c9ebdc`/`8e8c01d`
2026-07-21) — 이번 요청분이 그 안에 이미 포함돼 배포됨.

**조치 없음 (push 안 함)** — 중복 배포라 스킵. 오늘 세션에서 별도 push 실행 안 함(git log에 새 커밋
없음, 확인용).

status: resolved
