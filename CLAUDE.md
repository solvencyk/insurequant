# Insurequant Project Guidelines & Index

Automated data pipeline for Korean insurance financial metrics (K-ICS, IFRS17).
This file contains the core behavioral rules and the documentation index.

## 🔄 Session Handoff (다음 세션을 위한 안내)
이 저장소는 여러 Claude/Cursor 세션이 이어서 작업합니다.
**새 세션은 가장 먼저 `TODO.md`(작업 현황)와 `docs/claude-changelog.md`(변경 이력)를 확인**해서 직전 세션이 무엇을 바꿨는지 파악하세요. 변경·실행이 있을 때마다 **TODO.md와 changelog 맨 위**를 갱신해야 합니다.

## 📂 Agent & Domain Index (작업별 지시서)
작업하려는 도메인에 맞춰 아래 에이전트 가이드라인과 시스템 문서를 숙지하세요.

- **[Agent: K-ICS 파이프라인]** 👉 `docs/claude-agent-kics.md`
  - *Architecture:* `claude-overview.md`, `claude-download-flow.md`, `claude-gemini-flow.md`, `claude-json-build.md`, `claude-validation-harness.md`
  - *Validation rules (authoritative):* `docs/kics-json-validation-rules.md` — synced with `src/solvency/validation/kics_json_rules.py`

## K-ICS validation gate (mandatory)

Before proceeding to the next K-ICS pipeline stage (JSON swap, template sync, HTML deploy, push):

1. Run `python scripts/validate_kics_disclosure.py` on root `kics_disclosure.json`.
2. **RED count must be 0**, unless every remaining RED is a **documented exception** in `TODO.md` (company, quarter, rule id, reason).
3. Any unexpected RED requires **parsing-error review** (MD source, parser scope, row mapping) before continuing.
4. Rule `8_life` **SKIP** (missing items 29-35) does not block the gate; all other rules treat missing inputs as RED.

See `docs/kics-json-validation-rules.md` for formulas, R4/R7 matrices, tolerance, and item-label mapping.

- **[Agent: IFRS17 DART 공시]** 👉 `docs/claude-agent-ifrs17.md`
- **[Agent: 기타 IR/채권 공시]** 👉 `docs/claude-agent-misc.md`

## 🈲 문서·TODO 인코딩 룰 (필수)

**TODO.md, docs/*.md, README 등 모든 문서 파일은 반드시 UTF-8 (BOM 없음)으로 저장한다.**
- 한글이 깨질 환경(PowerShell `Out-File` 기본 UTF-16, Write 도구 일부 환경 등)에서는 **영어로 작성**한다.
- **절대 중국어/일본어/유사 문자로 보이는 깨진 출력을 그대로 두지 말 것.** (실제로는 UTF-16 LE BOM 누락으로 글자 사이 null byte가 들어가 한글이 중국어처럼 보이는 케이스가 빈번.)
- 신규/덮어쓰기 시 반드시: Python `Path.write_text(content, encoding='utf-8')` 또는 PowerShell `Set-Content -Encoding utf8`.
- 작성 후 첫 줄을 즉시 read-back으로 확인. 깨졌으면 영어로 재작성.
- 이 룰은 사용자가 2026-05-24 세션에서 명시적으로 약속을 요구함.

## 🧵 멀티에이전트 병렬처리 규칙 (필수)

이 저장소의 도메인(K-ICS / IFRS17 / 기타 IR)은 **서로 독립**이다. 사용자가
두 도메인 이상에 걸친 작업을 한 번에 요청하면, **반드시 도메인별로 별도
서브에이전트(Agent tool)를 띄워 병렬로 처리한다.** 단일 세션에서 순차로
처리하지 말 것.

- 한 메시지 안에서 `Agent` 호출을 도메인 수만큼 병렬로 발사한다
  (`subagent_type=general-purpose` 또는 `Explore`).
- 각 에이전트에는 본 CLAUDE.md, 해당 `docs/claude-agent-*.md`, 그리고
  관련 architecture 문서 경로를 자기 컨텍스트로 명시적으로 알려준다.
- 메인 세션은 오케스트레이션(계획 조율, 결과 통합, changelog 갱신,
  검증·푸시)만 담당한다. 도메인 코드/MD/JSON 직접 수정은
  서브에이전트가 한다.
- 한 도메인 안에서도 명백히 병렬 가능한 단계(예: 회사별 PDF 파싱)는
  서브에이전트가 자체 판단으로 병렬화한다.

---