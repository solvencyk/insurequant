---
from: orchestrator
to: designer
created: 20261012T1100Z
status: open
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): 자본성증권 인정한도 소진율을 규정 근거로 재정의했다(publishing, 커밋 `c3ebcc3`; 정의·근거 `data/_derived/capital_utilization_definition_20261012/definition_memo.md`). 화면(`K-ICS.html` 의 기본자본·보완자본 소진율 도넛/표 14곳)의 문구와 표시 규칙을 새 정의에 맞춘다. **화면 이름은 공시·규정 표기 그대로, 의역·설명 덧붙이기 금지, 설명은 `?` 팝오버 안에만**(owner 2026-10-12 질책 이후 확정; 메모 §5 가 이 원칙으로 쓰였다).

### 해 줄 것
1. **문구**: 메모 §5 를 그대로 채택한다(읽고 그대로 옮길 것):
   - 부제 1: `기본자본 자본증권 / 기본자본 자본증권의 인정한도 (총요구자본 × 10%, 기발행분 15%)`, 부제 2: `보완자본 한도 적용 전 / 보완자본 한도 (총요구자본 × 50%)`. 현행 「공시 인정액」·「(전체)」·「(보통주 제외)」 문구는 삭제.
   - 도넛 캡션: `기본자본 자본증권` · `보완자본`. 숫자 줄: `기본자본 자본증권 X억원 / 인정한도 Y억원` · `보완자본 한도 적용 전 X억원 / 보완자본 한도 Y억원`.
   - `?` 팝오버(tier1·tier2) 문장은 메모 §5 의 두 문장 그대로.
2. **새 JSON 필드를 읽는다**(기존 필드는 그대로 있다; 전체 명세는 `docs/changelog_publishing.md` 맨 위 항목 + `kics_tier1_utilization.json`·`kics_tier2_utilization.json`): 
   - tier1: 숫자 줄 「X억원 / 인정한도 Y억원」 에는 `tier1_hybrid_recognized_eok` / `tier1_hybrid_limit_eok`(두 한도 중 먼저 차는 쪽의 값, 그 쪽 표시는 `binding_leg` = `legacy_15` | `basic_10` | null). `type_unconfirmed=true` 인 회사(코리안리·농협생명·푸본현대)는 숫자는 상한값을 그대로 보이되 툴팁/`?` 에 「기본자본형/보완자본형 미확정 신종 포함, 보완자본형이면 `tier1_pct_if_unconfirmed_tier2`%」 만 적는다(설명 문장 늘리지 말 것).
   - tier2: `rule`(R0~R5·R-none·NA)·`reason`·`numerator_eok`·`utilization_pct`. `rule` 이 NA 면 값이 null 이고 `reason`(「경과조치 표 미공시」)이 붙는다.
3. **표시 규칙(메모 §5 마지막 불릿 그대로)**: 분모가 있고 분자 0 → `0%`. 자본증권이 아예 없는 회사(`no_capital_securities=true`)의 tier1 은 가운데 `0%` + 캡션 아래 작은 글씨 `발행 없음`. tier2 가 0 인데 보완자본 > 0 이면 숫자 줄에 공시 표기 `해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 X억원`(`lapse_excess_item49_eok`)을 그대로. 원문 부재(NA) → 가운데 `—` + 툴팁 `경과조치 표 미공시`(현재 「데이터 없음」과 구분; 교보라이프플래닛 tier2 는 「산출 불가」). 100% 초과 → 기존 `100%+` 유지, 툴팁만 tier1 「초과분은 보완자본으로 재분류」 / tier2 「초과분은 지급여력금액에서 불인정」으로 구분.
4. 재보사(스위스리 등)·구판 JSON(새 필드 없음)에서도 깨지지 않게 폴백. 음수는 △(해당 시). 데이터 인라인 금지(fetch).
5. **점검**: 헤드리스 렌더(`?iq_internal=1`) 로 대표 회사 확인 — 한화생명(tier1 0%·tier2 70.5%), DB손해(151.6% → `100%+`), 스위스리(tier2 0%·발행 없음), 교보라이프플래닛(tier2 `—`), 코리안리(`type_unconfirmed`), 흥국생명. 1280px·375px, 다크 모드, 콘솔 오류 0. `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py`(·`tests/test_share_screenshot.py`) 한 번에 하나씩 끝까지(건너뛰지 말 것).

### 규칙
- 쓰는 파일: `K-ICS.html`(필요 시 index.html 의 같은 문구, `grep` 으로 확인). 마스터 JSON·xlsx·`public_exports/`·패널 수정 금지. 다른 designer 작업(IFRS17.html·theme.js)은 끝났다. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 파일 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~5줄 존댓말)
- 바뀐 곳(줄)·확인한 회사·시험 결과·커밋 해시. `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
