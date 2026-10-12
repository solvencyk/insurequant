---
from: orchestrator
to: validation
created: 20261013T0010Z
status: resolved
route: fix
company: MULTI
period: 2023.1Q-2026.1Q
iter: 1
---

## 미결 (sender 작성)
parser-kics 가 owner 승인(2026-10-12 「확실히 검산 닫히는 것만 최신 공시로 덮어쓰기」)으로 K-ICS 마스터에 「최신 공시 직전 컬럼」 값을 적용했다(커밋 `74a415bf`, 티켓 `20261012T2200Z`): **16블록 65칸**(전 33 · 적용후 미러 22 · 파생 27·28 10) 적용, **10블록 보류**(후속 공시 둘이 서로 다른 값 9 + ABL생명 2024.3Q 항목 22 1), 예외 해제 2건(롯데손해 2025.1Q 항목 13: 19,202→17,997 · NH농협손해 2024.3Q 항목 13: 8,867→9,390; `_TIER2_ISSUER_INCONSISTENT` 22→20), 게이트 K-ICS RED 56→54. 재작성 장부 `data/_gold/kics_restatement_ledger.json` 에 29칸 `as_restated` 등재. 산출: `data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv`·`held_blocks.csv`. 이 마스터를 그대로 라이브에 올릴 것이므로 **독립 검수 + 골든 정리**를 한다.

### 해 줄 것
1. **독립 검수(65칸 전부)**: `applied_blocks.csv` 의 모든 칸을 parser 의 증거를 믿지 말고 원본 공시 PDF(`data/disclosure/**/raw`)에서 직접 다시 읽어 ① 새 값이 최신 공시의 직전/전전 컬럼 인쇄값과 같은지 ② 자기 공시(원 분기) 인쇄값과 다른 이유가 후속 정정인지(자기 공시 값과 마스터가 달랐던 오류 5칸 포함) 확인한다. 쪽 번호·인쇄값을 표로 저장. 스캔/이미지 쪽은 240dpi 렌더링(키워드 0회로 부재 단정 금지). 하나라도 어긋나면 그 칸을 목록으로 올려 parser-kics inbox 에 되돌림 티켓(직접 수정 금지).
2. **보류 10블록 타당성 확인**: `held_blocks.csv` 에서 보류 사유가 맞는지(특히 「후속 공시 둘이 다른 값」 9블록이 정말 서로 다른지, ABL 2024.3Q 항목 22 가 `recalc_kics_derived.py` 가 0 으로 되돌리는 문제인지) 표본이 아니라 10블록 전부 확인.
3. **게이트 전 구간 한 번에 하나씩**: `validate_kics_disclosure.py`(RED 54 가 맞는지, 새 RED 0), `validate_data_contract.py`, `validate_master_tables.py --no-build`, `scripts/check_master_xlsx_drift.py`, `tests/test_rule_coverage_manifest.py`, `tests/test_identity_registry` 계열.
4. **골든·지문 정리**: parser 가 건드리지 않고 남긴 `test_kics_rules_golden`(finding 31건 이동), 입력 지문 4건(`INPUTS_MOVED`), 시험 4건을 원인(이 적용으로 인한 의도된 변화인지)을 확인한 뒤 `--update` 로 재생성하고 커밋 메시지에 이유. 의도하지 않은 변화(적용 범위 밖 셀·회사)가 하나라도 있으면 갱신하지 말고 보고.
5. IFRS17 레인(parser-ifrs17 이 지금 별도 적용 중)·`public_exports/`·HTML 은 건드리지 않는다. 그쪽 골든은 이후 별도 티켓.

### 규칙
- 구현·마스터·등재부 수정 금지(골든 `--update` 제외). 감사 스크립트는 `data/_derived/` 새 폴더(예: `kics_latest_prior_apply_audit_20261013/`)에만. 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`·스크립트 파일만(멀티라인 `-c`·stdin heredoc 금지), 고아 프로세스 즉시 종료. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트의 미커밋 파일 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 65칸 독립 검수 결과(일치/불일치), 보류 10블록 타당성, 게이트 결과, 골든 갱신 내역과 이유, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
처리 완료: 65칸 독립 검수 일치, 보류 10블록 타당, 게이트 K-ICS RED 54, 골든·지문 갱신, 재작성 장부 시험 10→39 (validation 6e02aa67). orchestrator 종결 2026-10-13.
