---
from: owner
to: parser
created: 20260616T0043Z
status: open
route: backlog
company: MULTI
period: ALL
lane: kics+ifrs17
iter: 1
---

## 발주 (owner) — `skill-creator`로 도메인 지식을 SKILL.md로 결정화 (두 레인 각자 병렬)

parser의 도메인 지식(라벨 변형·테이블 형태·회사별 quirk·검증 룰)이 이미 성숙해서 `docs/domains/*.md`에 쌓여 있다. 이걸 Anthropic 공식 `skill-creator` skill로 **SKILL.md(progressive disclosure)로 결정화**해서, 앞으로 parser 세션이 도메인 컨텍스트를 자동 로드해 작업이 수월해지게 한다. **kics·ifrs17 레인은 각자 자기 세션에서 병렬로** 처리(2-lane hard split 유지).

### KICS 레인 (lane: kics)
SKILL.md 후보 소스 (이미 존재, 결정화만):
- `docs/domains/claude-agent-kics.md` (라벨 변형·시장위험 세부·rate-sensitivity)
- `docs/agents/kics-json-validation-rules.md` (R4/R7 매트릭스·tolerance·item-label 매핑)
- 회사별 quirk (메모리 `reference_kics_company_quirks`, `reference_kics_capital_tiering`): AIA 경과조치 미적용(적용전=적용후)·코리안리 자동차 일반sub·기본자본 자본증권 한도 SCR×10/15%·보완자본 SCR×50%·tier1 100%+ 도넛 정당·dedup 항등식 채택 등.

→ `skill-creator`로 **kics 파싱·검증 SKILL.md** 작성: SKILL.md(트리거+요약) + reference 파일(룰/매핑/quirk). 새 분기 파싱 시 자동 트리거되게 description 튜닝.

### IFRS17 레인 (lane: ifrs17)
SKILL.md 후보 소스:
- `docs/domains/claude-agent-ifrs17.md` (DART 라벨 변형: 보험료배분접근법 vs 계약의 유형 등·CSM_waterfall/PL_breakdown 추출 quirk)
- 회사 매핑 원칙 (메모리 `feedback_ifrs17_company_mapping`: DART는 회사명 검색, 영구 매핑 파일 금지)
- 단위/부호 함정 (1억=100백만; sensitivity 부호 방향).

→ `skill-creator`로 **ifrs17 추출 SKILL.md** 작성: viz_build_ifrs17_panels 계열 + extracted JSON 스키마·라벨 변형 처리.

### 공통 제약
- **기존 docs/domains/*.md는 SOT(원본) 유지.** SKILL.md는 그 위에 얹는 트리거 레이어 — 내용을 docs에서 잘라 옮기지 말고 **요약+참조** 구조로(중복 최소화, progressive disclosure). 결정화 후 docs가 정본인지 SKILL.md가 정본인지 한 줄로 명시.
- 문서 인코딩 UTF-8(BOM 없음). 한글 깨질 환경이면 영어로.
- Windows 인라인 멀티라인 `python -c` 금지. python 풀패스.
- 이건 **인프라 작업** — round3 데이터 글리치(`…kics_data_round3`, `…ifrs17_pl_sensitivity_round3`)와 별개 트랙. 둘 다 열려 있으니 우선순위는 레인 판단.

## 답변 (parser/ifrs17 2026-06-16 — IFRS17 도메인 SKILL 결정화 완료)

**산출물:** `.claude/skills/ifrs17-parser/` (Anthropic `skill-creator`로 작성)
- `SKILL.md` — 트리거 description(새 분기 파싱·재추출, 패널 빌드/리프레시, 추출 디버그, 사이트 IFRS17 수치 질문
  시 자동 로드 + **K-ICS 레인 명시적 제외**) + 운영 코어(2-lane split·pipeline at a glance·6대 trap·작업법).
- `references/pipeline-map.md` — raw→extractor→extracted JSON→master/viz 배선, 파일맵, extracted-block /
  sensitivity_heatmap / PL-master(24항목·항등식) 스키마, run/verify 레시피.
- `references/quirks-and-traps.md` — destructive-rebuild(이 브랜치)·단위(1억=100백만)·부호·사별 레이아웃 quirk
  표(동양/흥국/푸본/하나/농협·케이디비/메트라이프…)·reconciliation 항등식·회사매핑·Windows/인코딩.

**SOT vs SKILL 정본 (owner 요구 — 1줄 명시):** `docs/domains/claude-agent-ifrs17.md` = 설계/스코프 **SOT**
(라벨변형·테이블폼 taxonomy·slice·Q1–Q9). SKILL = 그 위 **운영 트리거 레이어**(현행 pipeline map + traps).
내용 복붙 없이 요약+참조. **단 SOT의 2026-05 PoC-status가 현행 코드와 충돌하면**(특히 §7.3/Q8 "DART 민감도 =
skim PoC, K-ICS primary" — 지금은 DART CSM/PL 민감도가 실파이프라인) **코드 + SKILL 우선**임을 SKILL에 박아둠.

**위치 주의:** `.claude/`는 `.gitignore`(L80)라 SKILL은 **머신-로컬**(push 안 됨). 오히려 owner 모델과 부합 —
공유 정본은 tracked `docs/domains/*.md`(SOT), SKILL은 이 checkout의 parser 세션이 자동 로드하는 로컬 편의 레이어.

**description 튜닝:** 수기로 트리거 강화(파싱/재추출/패널빌드/새분기 온보딩/수치질문 포함 + K-ICS 네거티브 경계).
경험적 최적화(`skill-creator` run_loop.py = `claude -p` 5-iter)는 한 줄 힌트 대비 heavy라 보류 — owner 원하면 실행.

**KICS 레인:** 2-lane hard split대로 K-ICS SKILL(`docs/domains/claude-agent-kics.md` + kics-json-validation-rules
+ reference_kics_* 메모리)은 **K-ICS 세션에서 별도** 결정화 — 여기서 손대지 않음.

status: ifrs17 SKILL done (machine-local, gitignored). 경험적 description 최적화 = owner 요청 시 추가.

