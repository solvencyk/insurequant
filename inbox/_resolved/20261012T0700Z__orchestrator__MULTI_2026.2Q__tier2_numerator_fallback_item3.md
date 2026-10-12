---
from: orchestrator
to: publishing
created: 20261012T0700Z
status: resolved
route: bugfix
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지적(2026-10-12, 화가 많이 나 계심 — 빠르고 정확하게): K-ICS 화면에 적힌 정의 「기본자본 자본증권(보통주 제외): 공시 인정액 / (SCR×15%)」 · 「보완자본(전체): 한도 적용 전 보완자본 / (SCR×50%)」 에 따르면 **보완자본이 조금이라도 있으면 소진율이 0% 보다 커야** 하는데 재보사·외국계가 0 또는 「미공시」로 나온다. 신종자본·후순위 발행이 0 이라는 것과 소진율 0 은 다른 말이다.

### 원인(오케스트레이터 실측, `kics_disclosure.json` 2026.2Q × `kics_tier2_utilization.json`)
분자를 항목 47(보완자본 한도 적용 전)로만 쓰는데, 일부 회사는 경영공시 「보완자본 한도 적용 전」·「한도」 칸이 **「-」(마스터 0 또는 NA)** 로 인쇄되고 항목 3(보완자본)은 크다. 그런 회사가 0% 또는 미산출이 된다:

| 회사 | 항목3 보완자본(억) | 항목47 | 한도(SCR×50%) | 현재 | 항목3 분자로 쓰면 |
|---|---|---|---|---|---|
| 스위스리아시아 KR1102 | 4,274 | 0(「-」) | 2,043.5 | **미산출**(`numerator_undisclosed`) | ≈209% |
| 라이나생명 KR0074 | 18,652 | 0 | 10,195 | 0.0% | ≈183% |
| 메트라이프생명 KR0095 | 21,854 | 0 | 10,447 | 0.0% | ≈209% |
| AIG손해 KR0029 | 754 | 0 | 1,390 | 0.0% | ≈54% |
| 교보라이프플래닛 KR1010 | 364 | NA | 388.5 | 0.0% | ≈94% |

(항목 47 이 정상 인쇄된 42곳은 건드리지 않는다. 알지에이 KR1105 는 항목 47=5,499 이지만 보완자본(항목 3)=0 이고 발행사 인쇄 오기라 `issuer_item47_inconsistent` 로 0 유지가 맞다. 뮌헨·퍼시픽은 항목 3=0 이라 0 이 맞다.)

### 해 줄 것
1. `scripts/compute_tier2_utilization.py` 의 분자 결정에 **폴백 규칙** 추가: 항목 47(한도 적용 전)이 **없거나 0 인데 항목 3(보완자본) > 0** 이면 분자 = 항목 3 (억원), 한도는 기존대로(항목 48 이 0/NA 이면 항목 14 × 50% — 현재 코드가 이미 쓰는 한도 산출을 확인하고 일관되게), `quality_flag` = `numerator_from_item3`(새 값, 기존 `ok`와 구분되게 `data_source`·`numerator_source` 같은 기존 필드에 근거 문자열). 항목 47 이 정상(>0)이거나 항목 3 = 0 이면 **기존 결과 그대로**. 위 5곳 외 42곳 행은 재산출 전후 바이트 동일해야 한다(키 단위 diff 로 증명). 수동 입력·하드코딩 금지, 규칙으로 구현하고 다른 분기에도 같은 규칙이 적용되도록.
2. **기본자본(tier1)** 쪽도 같은 관점으로 점검(읽기): 분자 = 항목 6(자본항목 중 보통주 이외의 자본증권, 공시 인정액). 항목 6 이 0/음수인데 같은 표에 기본자본 자본증권이 따로 인쇄되는 회사가 있는지(항목 53 기발행 신종자본증권(TFI표)·항목 13 재분류 등) 47사 전수로 비교해 **보고**한다(코드 변경은 하지 말고, 불일치가 있으면 회사·값·근거 쪽을 목록으로).
3. 산출물 재생성·동기화: `kics_tier2_utilization.json`(+ 같은 계산을 쓰는 `kics_forward_capital.json`·`data/bonds/capital_securities_forward_outlook.json` 등 파생물이 이 숫자에 의존하면 영향 확인 — 의존하면 재생성, 아니면 보고만), xlsx `보완자본소진율` 시트(`scripts/sync_master_xlsx_sheet.py "보완자본소진율"`, 기존 행 불변 증명), `public_exports/보완자본소진율.json`(`export_public_sheets.py` 는 커밋된 HEAD 를 읽으니 마스터·xlsx 를 먼저 커밋한 뒤 실행·재커밋), `scripts/check_master_xlsx_drift.py`·`validate_data_contract.py`(MASTER_XLSX_* 0).
4. 시험·게이트(한 번에 하나씩): 이 계산을 다루는 기존 단위시험(`tests/` 에서 `tier2`·`utilization` 로 찾기)에 폴백 케이스를 추가하고(스위스리형: 항목 47=0·항목 3>0 → 분자=항목 3; 알지에이형: 항목 47>0·항목 3=0 → 0; 정상형 불변) 변이시험(폴백을 지우면 실패), `tests/test_push_gate_wiring.py`·`tests/test_deploy_assets.py`, `validate_kics_disclosure.py` 가 `kics_tier2_utilization.json` 를 읽는 룰이 있으면 영향 확인. 풀 훅·전체 pytest 는 돌리지 않는다.
5. 화면 문구(K-ICS.html)는 바꾸지 않는다(분자 값이 데이터에서 나오고 이미 「한도적용전 N억원 / 한도 M억원」 으로 표시) — 단 `numerator_undisclosed` 였던 스위스리가 값을 받으면 화면이 정상 렌더되는지 `?iq_internal=1` 로 한 번 확인해 보고(HTML 수정 필요 시 보고만, designer 몫).

### 규칙
- `kics_disclosure.json`·다른 마스터 수정 금지. 예외 등재 금지. 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json` 제외, `.gitignore` 경로를 `git add` 에 넣지 말 것), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push·배포 금지**(오케스트레이터가 push 한다). 서브에이전트 금지, docling 금지. 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·맨 `python`·stdin heredoc 금지), `encoding` 명시. 이 공유 티켓은 고치지 않는다.

### 보고 (2~5줄 존댓말 + 파일 경로)
- 재산출 전후(5곳 값·플래그, 나머지 42곳 바이트 동일 증명), tier1 점검 결과(불일치 목록), 파생물·xlsx·공개본 처리, 시험 결과, 커밋 해시. `TODO_publishing.md` Status + `docs/changelog_publishing.md`.

## 답변 (recipient 작성 — 처리 후)
(orchestrator 종결 2026-10-12) 착수 직후 중단·취소: 「항목 3 폴백」 방안은 규정상 틀린 것으로 조사(Opus, 티켓 20261012T0710Z)에서 확인됨 — 해약환급금 부족분 상당액 중 준비금 초과분은 보완자본 한도 계산에서 제외되므로 보완자본 전체를 분자로 쓰면 안 된다. 코드·마스터 변경 0(미커밋 변경 없음). 대체 티켓: 20261012T0800Z(규정 근거 재정의 반영).
