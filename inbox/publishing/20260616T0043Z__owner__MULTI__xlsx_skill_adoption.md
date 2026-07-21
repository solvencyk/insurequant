---
from: owner
to: publishing
created: 20260616T0043Z
status: answered
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — `xlsx` 공식 skill 지금부터 상시 사용

publishing 스테이지의 master xlsx 작업에 Anthropic 공식 `xlsx` skill을 **지금부터 상시 적용**한다. 별도 평가 단계 없이 바로 디폴트 도구로 채택.

### 적용 대상
1. **`scripts/build_master_xlsx.py`** — master JSON → `insurequant_master_tables.xlsx` 재생성. 마스터 JSON 갱신 시 xlsx 재생성 필수(메모리 `feedback_rebuild_master_xlsx`). 수식/서식/시트 구조 처리에 `xlsx` skill(openpyxl 기반) 사용.
2. **master xlsx 리뷰 루프** — owner가 xlsx **H열 수기정정 → I열 재계산**. I열 수식 재계산을 `xlsx` skill로 안정화. **단 핸드오프는 기존대로**: 정정 결과의 diag 반영은 **parser inbox로** 넘긴다(루트 JSON만 고치면 빌드에서 소실 — 메모리 `project_master_xlsx_review_loop`). 이 분담은 변경 없음.
3. **gold xlsx 게이트** — 루트 `CSM waterfall_*.xlsx` / `data/_gold/` xlsx 읽기·검증(`_verify_csm_golds.py` 경유). xlsx 읽기/대조 시 skill 활용.

### 주의 / 제약
- **데이터 정합성 변경은 여전히 parser 소관.** publishing은 assembly(JSON→xlsx) + push 권고만. xlsx 내용의 도메인 오류는 parser inbox로 바운스.
- ⚠️ **`scripts/build_csm_waterfall_master.py` 실행 금지** — 이 브랜치는 raw가 purge돼 있어 실행 시 committed master(1926행)를 ~12행으로 붕괴시킴(메모리 `project_git_purge`). gold xlsx 다룰 때 이 스크립트는 건드리지 말 것.
- Windows 인라인 멀티라인 `python -c` 금지(워크플로우 서브에이전트 행). python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`.
- (옵션, 나중에) publishing 프롬프트(`docs/agents/claude-agent-publishing.md`)가 아직 skeleton/TBD다. idempotency·schema versioning·xlsx rebuild 절차가 정식화되면 그때 `skill-creator`로 publishing SKILL.md로 결정화 고려. **지금은 보류** — 프로세스부터 채운 뒤.

## 답변 (publishing 2026-06-16 — 채택 + 첫 적용 완료)

**`xlsx` skill 상시 디폴트 채택 확인. 발주 도착 시점에 마침 재생성 룰이 발동돼 있어 #1 대상으로 바로 첫 적용함.**

- **트리거**: 오늘 배포한 master JSON 2건(`kics_disclosure.json` 09:41, `kics_rate_sensitivity.json` 09:42)이 기존 `insurequant_master_tables.xlsx`(6/15 13:59)보다 최신 → `feedback_rebuild_master_xlsx` 룰 발동(stale).
- **조치**: `xlsx` skill 워크플로우 하에 `scripts/build_master_xlsx.py` 실행(풀패스 python). skill 가이드 "Existing template conventions ALWAYS override" 그대로 — 기존 컨벤션(맑은 고딕·헤더 305496·number_format `#,##0.##;(#,##0.##);-`) 유지, 임의 표준화 안 함.
- **결과**(09:53 재생성, 7시트): 요약 + K-ICS공시 17,197 · 금리민감도 516 · **CSM워터폴 1,926**(committed master 그대로, 붕괴 0) · CSM상각 290 · 신계약CSM배수 321 · 손익분해PL 7,727.
- **read-back 검증**: 시트명·헤더·데이터 한글 전부 무결(메리츠화재해상보험/DB생명보험/AIG손해보험 등). 출력은 전부 정적 값(수식 0) → recalc 단계 N/A, formula 에러 불가.
- **금지선 준수**: `build_csm_waterfall_master.py` 미실행(이 스크립트는 `CSM_waterfall.json`을 **읽기만**, raw 의존 없음 → CSM워터폴 1,926행 유지로 입증). 멀티라인 인라인 `python -c` 미사용.
- **배포 영향 없음**: xlsx는 untracked 빌드물(리뷰어 편의 파일), slim-publish keep-list(HTML+master JSON) 비대상 → push 불요. backlog `🔴-3 master xlsx 재생성` 종결.

**적용대상 #2(리뷰 루프 I열 재계산)·#3(gold xlsx 게이트)**: 발생 시 skill 적용 예약. 분담 불변 — 정정 diag는 parser inbox로, 데이터 도메인 오류는 parser 바운스. publishing 프롬프트 결정화(skill-creator)는 owner 지시대로 보류(프로세스 정식화 후).

→ standing-order 확인·첫 적용 완료. status `answered`(상시 정책이라 폴더 유지, owner 검토용).
