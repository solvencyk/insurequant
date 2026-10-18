---
from: orchestrator
to: publishing
created: 20261018T0700Z
status: resolved
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

2026-10-19 publishing. 원인 정정: 저장 값을 쓰는 빌더는 `scripts/viz_build_ifrs17_panels.py` 가 아니라 `scripts/viz_build_persistency_lossratio_panels.py` 이다(`data/loss_ratio/panel_loss_ratio.json`). 소계는 `_agg` 가, 합계·잎 행은 마스터 공시값(소수 2자리)을 그대로 싣고 있었다. 합계 행(메리츠화재·AIA생명)도 같은 이중 반올림이었다.
수정: `_ratio()` 를 추가했다. 공시 2자리 값이 금액(Σ예상보험금÷Σ위험보험료)으로 재현되면(차이 0.005 이하) 반올림 전 비율을 소수 6자리로 싣고, 재현되지 않으면 공시 2자리 값을 그대로 둔다(재계산으로 갈아끼우지 않음). 위험보험료가 음수인 잎도 같은 검사를 거친다(재검증에서 `b > 0` 가드가 KR0068 2024.4Q 연금저축 2칸을 빠뜨린 것을 찾아 `b != 0` 으로 풀었다). 소계는 `RATIO_DP=6`. 마스터 JSON·HTML은 건드리지 않았다.
실측: 새 패널 전 칸(합계·구분·상품구분·잎, 전 경과차년, 21,000여 칸)을 마스터 금액 재계산과 대조하니 화면 표시값 차이 0.05pp 초과 0건이다(현재가치 칸 1,500여 개 포함, 수정 전 현재가치 칸 77개 초과). 구 패널과 대조하면 키·구조 동일, 바뀐 숫자 18,853개 전부 |차이| 0.005 이하, 바뀐 문구는 meta.note 1곳. 지속률 패널은 바이트 동일. 크기 206,474 → 281,737 바이트(한도 1.5MB).
골든: 이 패널을 고정하는 골든 테스트는 없다(`test_viz_ifrs17_panels_golden.py` 는 다른 빌더). 그래서 `--update` 는 하지 않았고 푸시 게이트의 `--check`(`tests/test_push_gate_wiring.py` 의 파생 선언)가 대신 고정한다.
재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/viz_build_persistency_lossratio_panels.py --check` (OK), `pytest tests/test_deploy_assets.py tests/test_push_gate_wiring.py -q` (78 passed, 1 skipped). 커밋은 오케스트레이터가 한다(빌더 + 패널 JSON + 이 티켓).
