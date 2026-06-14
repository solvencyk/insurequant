# Inbox — 스테이지 간 handoff 계약 (정본)

스테이지(다운로더/파서/검증)가 **서로 md 메시지를 떨궈 주고받는** 비동기 메시지 큐.
사람이 세션 간 복붙하던 릴레이를 대체한다. 이게 정본 계약이고, 각 스테이지
프롬프트(`docs/agents/claude-agent-<stage>.md`)는 여기를 가리킨다.

> [!info] 정체 (framework 분류)
> filesystem-mediated **evaluator-optimizer** 인터페이스. 실시간 agent-team이 **아니다**
> (그래서 좋다 — 강결합 실시간 조율 함정 회피). inbox=메시지 형식, **dynamic Workflow=드라이버**.

---

## 폴더 layout

```
inbox/
  downloader/   ← 다운로더에게 오는 메시지 (parser/validation의 route: refetch)
  parser/       ← 파서에게 오는 메시지     (validation의 route: reparse / downloader의 raw-ready) — 2-lane(2026-06-13): frontmatter `lane: kics|ifrs17`로 구분
  validation/   ← 검증에게 오는 메시지     (parser의 재작업 status: answered)
  publishing/   ← 퍼블리싱에게 오는 메시지 (owner backlog / validation pass 통지) — 2026-06-12 신설
  designer/     ← 디자이너에게 오는 메시지 (owner backlog / publishing schema-delta 통지) — 2026-06-12 신설
  _resolved/    ← 종결 스레드 아카이브
```

폴더명 = 받는 스테이지(`to`). 메시지는 항상 **받는 쪽** 폴더에 넣는다.

## 메시지 파일

이름: `<UTCstamp>__<from>__<KR>_<period>__<topic>.md`
예: `20260608T0210Z__validation__KR0003_2025.4Q__continuity.md`

```markdown
---
from: validation          # 보낸 스테이지
to: parser                # 받는 스테이지 (= 폴더명)
created: 20260608T0210Z
status: open              # open | answered | resolved
route: reparse            # refetch | reparse | escalate | blind_spot
company: KR0003
period: 2025.4Q
rule: FY_BOUNDARY_DISCONTINUITY   # 해당 시 검증 rule id
lane: ifrs17              # parser 한정: kics | ifrs17 (2026-06-13 레인 split). 타 스테이지는 생략
iter: 1                   # evaluator-optimizer 회차 (max 5)
---

## 미결 (sender 작성)
롯데손해 2025.4Q 기초 CSM가 2024.4Q 기말과 12% 어긋남. 별도/연결 오선택 의심.
raw: data/dart/FY2025_Q4/raw/KR0003_.../_00760.xml

## 답변 (recipient 작성 — 처리 후)
<처리 결과 1~3줄. 못 했으면 왜 못 했는지.>
```

## route 의미 (어디로 가나 + 왜)

| route | 받는 곳 | 언제 |
|---|---|---|
| `refetch` | downloader | raw 누락/깨짐 (파싱가능 시그니처 실패, `raw_not_extracted`, `.xlsx.bad` 류) |
| `reparse` | parser | **시그니처성** 오류 — closing-identity break / continuity break / ×2 / 부호반전 / 단위. 파서가 고칠 수 있음 = **auto_loop** |
| `escalate` | 사람 큐 | 앙상블 불일치 / iter 5회 초과 / 원천 애매(별도-연결 무앵커) |
| `blind_spot` | 사람·2nd소스 | 룰로 못 잡는 부류(비-IR 균일오류 등, mutation-test가 식별) |
| `backlog` | 임의 스테이지 | owner가 떨구는 **작업목록 다이제스트** (정보성 — auto_loop 아님). 스테이지는 드레인 시 우선순위대로 소화, 완료분은 `## 답변`에 체크 후 resolved |

## 생명주기 (protocol)

1. **스테이지 시작 시 첫 동작 = 내 inbox 드레인.** `inbox/<me>/`의 `status: open` 전부 먼저 처리.
2. **상류 산출물에서 문제 발견 시** → 상류 inbox에 `status: open` 메시지 작성. **사람한테 복붙 요청 ❌.**
3. **처리 후** 같은 파일에 `## 답변` 추가 + status 갱신:
   - 재검증 필요(파서→검증 왕복) → `status: answered` (원 sender가 재확인)
   - 자기완결(refetch 완료 등) → `status: resolved` → `_resolved/`로 이동
4. **원 sender 재실행 시** → 자기가 보낸 `answered` 재확인 → 통과면 `resolved`+이동, 실패면 `iter++` 새 노트. **`iter==5`면 `route: escalate`로 바꿔 사람 큐.**

## 드라이버 (가장 중요한 제약)

에이전트는 inbox를 **백그라운드로 감시하지 않는다.** 호출돼야 드레인한다.
"딱 들어오는 순간 인식 & 재작업"은 **드라이버**가 시킨다:

- **dynamic Workflow (권장)**: `스테이지 실행 → inbox 확인 → 미결 route별로 다음 스테이지 dispatch → 루프`. goal = `auto_loop` 메시지가 빌 때까지 (또는 iter cap).
- 또는 사람이 차례로 kick / OS 파일워처·hook.
- **bounded**: reparse/refetch 루프 **max 5회**, 초과 → escalate (Ralph 안전장치).

## 기존 검증 JSON과의 관계

검증기가 뱉는 흩어진 JSON(`csm_continuity_validation.json`, `nb_csm_validation.json`,
`csm_waterfall_validation.json` 등)은 **데이터/근거**로 그대로 둔다.
**handoff의 정본은 inbox md** — 검증 스테이지가 그 JSON들을 읽어 route별 메시지로 변환해
해당 inbox에 넣는다. 이 변환은 **스크립트 `scripts/consolidate_inbox.py`** 가 한다 (기계적
작업이라 에이전트 불필요). idempotent: 이미 `parser/` 또는 `_resolved/`에 같은 (회사·기간·토픽)
메시지가 있으면 skip → 중복/해결건 재생성 안 함. 현재 continuity validator 처리, 신규 validator는
`VALIDATORS` 리스트에 핸들러 추가. **루프 = validator 실행 → `consolidate_inbox.py` → "inbox 확인해라".**

## Git

`inbox/*.md`는 스레드 audit trail이라 커밋 가치 있음. `_resolved/`는 주기적으로 archive.
`.gitkeep`로 빈 폴더 유지.
