---
from: orchestrator
to: publishing
created: 20261018T0700Z
status: open
route: defect
company: ALL
period: 2025.4Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

IFRS17.html 8절(손해율 가정)에 구분 선택기를 넣으면서(2026-10-18, `docs/changelog_designer.md`) 독립 검증이 찾은 건 1개.
현재가치 숫자의 **구분 소계**가 이중 반올림이다.

- 원인: `scripts/viz_build_ifrs17_panels.py` 가 `data/loss_ratio/panel_loss_ratio.json` 의 소계 행을 소수 둘째 자리까지만 저장하고, 화면(IFRS17.html)이 다시 소수 첫째 자리로 반올림한다.
- 실측(2025.4Q, 최신 분기): 마스터 금액 재계산과 0.05pp 를 넘는 칸 5개, 최대 0.0543pp — 메리츠화재 합계(화면 102.2 대 재계산 102.148), AIA생명 합계, 라이나생명 · BNP카디프생명 · 동양생명 Direct-Par. 합계 2건은 이번 변경 이전부터 있던 것이다. 빌더 보고는 전 분기 기준 17건.
- 곡선(경과차년 칸)은 최대 0.005pp 로 문제없다. 현재가치 숫자 칸만이다.
- 할 일: 소계 현재가치를 3자리 이상으로 저장(또는 화면이 반올림 전 값을 쓰도록)하고 `tests/test_viz_ifrs17_panels_golden.py` 를 `--update` 로 갱신(이유를 커밋에 적는다). 화면 쪽 수정은 필요 없다.
- 수용 기준: 위 5칸을 포함해 전 회사 · 구분의 현재가치 표시값과 마스터 재계산값의 차이가 0.05pp 이하, 골든 갱신 사유 기록.

## 현황 (receiver 작성)
