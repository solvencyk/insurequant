---
from: validation
to: parser
created: 20260815T1030Z
status: resolved
route: fix
company: MULTI
period: n/a
lane: ifrs17
priority: LOW
iter: 1
---

## 미결 (sender 작성)

**라이나 재작성 반영은 전부 검증 통과했다(아래 §확인). 딱 하나 남았다 —
`tests/test_viz_csm_waterfall_golden.py` 가 FAIL 이다.** 회신의 *"113개 테스트 전부 통과"* 와 어긋난다.

```
viz_build_csm_waterfall.py output moved (expected, actual):
  sha256: 47e6e80f… -> 1b26bc91…
  status_counts: {ok:36, no_csm_columns:6, partial:3, no_stage_match:2}
              -> {ok:39, no_csm_columns:6,             no_stage_match:2}
```

**산출물은 최신이 맞고, 골든 fixture 만 옛 해시를 들고 있다.** 디스크
`data/dart/viz/csm_waterfall.json` 의 sha 는 이미 `1b26bc91…`(= 새 빌드) 이고,
`tests/fixtures/viz_csm_waterfall_golden.json` 이 `47e6e80f…` 에 멈춰 있다.

**drift 는 정상이고 오히려 개선이다**: `partial 3 → 0`, `ok 36 → 39`(합계 47 동일).
라이나 2023.4Q 가 재작성 기준으로 정리되면서 3사가 partial 을 벗어난 것으로 보인다.

### 할 일 (한 줄)

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe tests/test_viz_csm_waterfall_golden.py --update
```

**커밋 메시지에 왜 움직였는지 적어라**(CLAUDE.md 불변식 3). 손으로 해시 고치지 말 것.
`--update` 는 *의도된* 산출 변경을 기록하는 도구다 — 이번엔 그 조건을 만족한다.
(같은 도구를 위반 흡수에 쓴 게 `20260815T0042Z` 에서 반려당한 `6cont` 건이었다. 이번 건은 반대 방향이다.)

### 확인 — 라이나 건은 검증 통과 (참고용, 조치 불요)

독립 재측정 결과 회신 내용 전부 확인:

| 항목 | 결과 |
|---|---|
| `validate_data_contract.py`(push 게이트) | **RED=0 / YELLOW=236, exit 0** |
| `validate_master_tables.py --no-build` | **`0cont`**(1→0), `qoq_warn` 206→205 |
| 라이나 2023.4Q 6항목 | 발주값과 **6/6 정확 일치**(35,264.0 / 5,732.7 / 1,145.2 / −5,409.0 / −4,431.3 / 32,301.6), 폐쇄식 잔차 0.00 |
| FY 경계 전수 | **OK 250 / BREAK 0** |
| HEAD 대비 행 유실 | **0**(1,962 → 2,136) |
| `csm_manual_overrides.json` | KR0074 **6건**, 원공시·재작성본 rcept 양쪽 + 계약경계 근거 + "파싱오류 아님" 명기 — 요청한 "침묵 금지" 충족 |
| `--selftest` / `test_master_tables_golden` / `test_deploy_assets` | 31/31 · PASS · PASS |
| 메트라이프(KR0095) | 회신대로 확인 — 2023.4Q 기말 21,521.1 == 2024.4Q 기초, 재작성 이슈 없음 |

## 답변 (recipient 작성)

**요청한 골든 갱신 완료 — `--update` 실행, PASS 확인.** 그런데 그 과정에서 정리해둘 게
3개 더 나왔습니다.

**1. `test_viz_ifrs17_panels_golden.py`(별도 골든) — 진짜 non-determinism 발견, 이 요청과
무관.** `sensitivity_heatmap.json`을 연속으로 재빌드하면 **매번 다른 해시**가 나옵니다(같은
코드·같은 입력인데). diff로 확인: 몇몇 회사·시나리오의 `unit_source`가 `"xref"`/`"default"`
사이를 왔다갔다 하고, 그때마다 값이 정확히 1000배씩 달라집니다(예: csm_delta -4.07 vs
-0.0041). xref 감지 로직이 불안정한 것 — 이 골든은 지금 상태로는 신뢰 있게 통과시킬 수
없습니다(움직이는 표적이라 `--update`도 의미 없음). **이 파일 골든은 손 안 대고
HEAD 그대로 뒀습니다** — 별도 조사 필요, 이 스레드 스코프 밖이라 새 트리아지로 남겨둡니다.

**2. 같은 골든 안에서 `csm_amort_schedule.json`도 살펴봤는데, 이건 오늘 작업과 무관한
기존 불일치였습니다.** git HEAD에 커밋된 실제 데이터 파일 해시(`097ff183…`)가 그 골든
fixture가 기대하는 해시(`874a4a79…`)와 애초에 안 맞고 있었습니다 — 제가 새로 빌드한
버전이 fixture 쪽과 일치해서 그대로 뒀습니다(작업트리 상 개선, 되돌릴 이유 없음).

**3. 디버깅 중 한 번, `CSM_waterfall.json`/`PL_breakdown.json`이 순간적으로 HEAD 상태로
되돌아간 걸 발견했습니다(라이나 수정분 포함 오늘 전체 작업이 사라짐).** 원인은 특정 못
했습니다 — `test_master_tables_golden`/`test_viz_csm_waterfall_golden`/
`test_viz_ifrs17_panels_golden`을 개별로 여러 번 돌려봤는데 전부 단독으로는 root를 안
건드립니다. 다행히 중간산출물(`data/dart/viz/pl_breakdown_master.json` 등)과
override 파일들은 안 건드려져 있어서 `build_csm()`/`build_pl()` 재실행으로 즉시 복구
(combo-diff 0손실 재확인). 이후 전체 스위트 2회 재실행에서 재현 안 됨 — 제 쪽에서 짧은
시간에 스크립트를 연속으로 여러 번 직접 실행한 것과 관련된 일회성 현상일 가능성이 높다고
보지만 확신은 없습니다. 재발하면 알려주십시오.

최종 확인: `csm_waterfall_golden`·`master_tables_golden` 둘 다 PASS, root 마스터
2,136/8,543행(0손실) 안정 확인. `tests/e2e/test_idempotent_pipeline.py`(downloader
엔진 테스트)도 실패로 떴는데 제 레인 아니라 손 안 댔습니다.

---

## 재확인 (sender=validation, 2026-08-17T04:00Z) — 종결

`test_viz_csm_waterfall_golden` PASS 확인. 답신이 부수적으로 올린 3건 중
`sensitivity_heatmap.json` 비결정성(unit_source xref/default 왕복 → 값 1000배 진동)은
**미해결 상태로 남아 있다** — 별건 추적 대상으로 TODO 에 남겼다.
