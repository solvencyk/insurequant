---
from: owner
to: publishing
created: 20260803T0743Z
status: open
route: escalate
company: MULTI
period: MULTI
iter: 1
---

## 미결 (sender 작성)

**마스터 JSON 4종이 갱신·라이브 배포됐는데 `insurequant_master_tables.xlsx`가 stale이다. 재생성해라.**

### 근거 (mtime)

```
insurequant_master_tables.xlsx   2026-07-30 17:16   <- stale
CSM_waterfall.json               2026-08-03 15:03
PL_breakdown.json                2026-08-03 15:04
kics_forward_capital.json        2026-08-03 14:59
NB_CSM_multiple.json             2026-08-03 11:56
```

### 무엇이 바뀌었나 (xlsx에 반영돼야 할 델타)

| 파일 | 델타 | 출처 커밋 |
|---|---|---|
| `CSM_waterfall.json` | KR0075 비엔피파리바카디프 CSM 단위 재정정 + **KR0004 예별손해 3개년(2023.4Q/2024.4Q/2025.4Q) 18셀 신규 온보딩** (1944 -> 1962행) | `184286c`, `08321db` |
| `NB_CSM_multiple.json` | 위 두 건 반영 재산출 (321 -> 327행) | `184286c`, `08321db` |
| `PL_breakdown.json` | **KR0051 신한이지손해보험** 2025.4Q 투자이익 -3890.709458 -> -1603.902737, 보험금융손익 0.0 -> -2286.806721 (부모 투자손익 -3890.709458 불변, 행수 7799 유지) | `08321db` |
| `kics_forward_capital.json` | 자본증권 소스를 FSC bonds -> DART 개별사채로 리베이스 (38사 유지, 값만 전면 갱신) | `cb084e7` |

### 실행 계약 (반드시 지킬 것)

1. **공식 `xlsx` skill 워크플로우로만 작업한다.** (`project_master_xlsx_formula_cache`, `feedback_rebuild_master_xlsx`)
2. **openpyxl `load_workbook` + `save`로 마스터를 재저장하지 말 것.** 값 열이 `=H누계` 수식이라
   캐시가 전부 wipe되고, 이후 `data_only=True` 읽기가 None을 반환해 sync/build가 조용히 오작동한다.
3. `scripts/build_csm_waterfall_master.py`는 실행하지 않는다 (2026-06 owner 지시).
4. 작업 전 `.bak` 백업을 남긴다. 손상 시 복구 절차는 `docs/launch_runbook.md` §6b.
5. 재생성 후 검증: mtime이 위 4개 JSON보다 최신인지 + KR0004 3개년 행이 실제로 나타나는지
   + **KR0051 신한이지손해보험** 2025.4Q 투자이익/보험금융손익이 분리된 값으로 보이는지 **눈으로 1곳 이상 확인**.

   > 주의: 배포 커밋 `255e445`의 메시지는 이 PL 델타를 KR0075로 잘못 적었다(실제는 KR0051).
   > main은 공개 배포 브랜치라 force-push로 고치지 않는다 — 정정 사실은 여기와 changelog에만 남긴다.
6. xlsx는 배포 에셋이 **아니다**(main keep-list에 없음) — 재생성만 하고 push 대상에 넣지 말 것.

### 참고 — 이미 완료된 것 (중복 작업 금지)

라이브(main) 배포는 **이미 끝났다**: `255e445` (`a4e8a7c..255e445`), 위 4개 JSON만 cherry-push.
HTML 4종(`index.html`/`K-ICS.html`/`IFRS17.html`/`공시보고서.html`)과 `common.css`는 main과 이미 동일 —
이번 배포 대상 아님. 게이트: `validate_data_contract.py` SUMMARY **RED=0** YELLOW=219 provisional=False.

## 답변 (recipient 작성 — 처리 후)

<처리 결과 1~3줄. 못 했으면 왜 못 했는지.>
