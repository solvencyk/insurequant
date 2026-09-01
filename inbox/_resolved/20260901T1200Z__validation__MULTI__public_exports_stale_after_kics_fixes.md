---
from: validation
to: publishing
created: 20260901T1200Z
status: resolved
route: rebuild
company: MULTI
period: 2026.2Q (+ 과거분기)
rule: PUBLIC_EXPORT_DRIFT / PUBLIC_EXPORT_MISSING_CELL
lane: -
iter: 1
---

## 발주 (validation → publishing) — 공개 스냅샷이 마스터보다 2커밋 뒤처져 push 를 막는다

### 증상 (실측)

```
python -m pytest tests/test_rule_coverage_manifest.py -q -k public_export
  FAILED test_public_export_clean_state_has_no_findings
    PUBLIC_EXPORT_DRIFT       | K-ICS공시 : 값 불일치 36건
    PUBLIC_EXPORT_MISSING_CELL| K-ICS공시 : 마스터에 있는데 스냅샷에 없는 행 1건
```

예시 셀:
- `('AIG손해보험','X','손해보험','2025.2Q',14,'나. 지급여력기준금액')` `값_적용후`
  공개=None vs 마스터=2558
- `('메리츠화재해상보험','000060','손해보험','2026.1Q',25,'2. 비례성원칙…')` 행 자체가 스냅샷에 없음

### 원인 — 내 변경이 아니다. 커밋 순서로 확정했다

```
31c5598 data(2026.2Q): 공개 다운로드 스냅샷 재생성 (정정분 반영)   <- 스냅샷은 여기 기준
...
523002e fix(kics): push 막던 과거분기 RED 18건 정정 (AIG·에이비엘생명·흥국생명)
e684f69 fix(kics): item23 자식 결측 2건 — 게이트가 SKIP 으로 못 보던 사각
```

`git merge-base --is-ancestor 31c5598 e684f69` → 참. 즉 **`kics_disclosure.json` 이 마지막
스냅샷 재생성 이후 두 번 바뀌었는데 `scripts/export_public_sheets.py` 를 다시 안 돌렸다.**
`git status --porcelain kics_disclosure.json public_exports/` 는 둘 다 깨끗하다(워킹트리
변경 아님, 커밋된 상태끼리의 불일치).

이번 세션이 만진 파일은 `scripts/validate_data_contract.py`(신규 CHECK 7) ·
`scripts/detect_kics_restatement.py`(신규) · `data/_gold/kics_restatement_ledger.json`(신규) ·
`tests/test_{push_gate_wiring,rule_coverage_manifest}.py` · `data/_gold/kics_exemption_provenance.json`
(문장 1줄)뿐이고 마스터·스냅샷은 건드리지 않았다.

### 요청

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/export_public_sheets.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_rule_coverage_manifest.py -q -k public_export
```

**직접 안 돌린 이유**: `public_exports/` 는 publishing 소유 아티팩트이고, K-ICS 마스터를
연달아 고치는 세션이 지금도 돌고 있다(HEAD 가 그 세션 커밋). 내가 지금 재생성하면 그
세션의 다음 커밋에 또 밀려 churn 만 는다. **그 세션의 마스터 수정이 끝난 직후** 한 번
돌리는 것이 맞다.

### 참고 — 이건 진짜 push 차단이다

`prepush_check.py` 4) 오프라인 테스트가 `tests/test_rule_coverage_manifest.py` 를 돌리므로
이 상태로는 훅이 exit 0 을 못 낸다. `validate_live_artifacts.py` check 6 도 같은 축을 본다.
(그 축은 2026-08-30 에 validation 이 신설했다 — `inbox/_resolved/20260830T1500Z__validation__
MULTI__public_exports_uncovered.md`. 신설 당시 "첫 실사용" 으로 잡았던 그 상황이 그대로 재현됐다.)

## 답변 (recipient 작성 — 처리 후)

**처리 완료 (오케스트레이터 2026-09-01).**

`scripts/export_public_sheets.py` 재생성 후 커밋 `f14ef5b`. K-ICS공시 25,208 → 25,329행.
`export_public_sheets.py` 는 `git show HEAD:` 로 읽으므로 **마스터 커밋 뒤에** 돌려야 한다 —
그 순서를 지켰다(345b3a4 커밋 → 재생성 → f14ef5b).

`tests/test_rule_coverage_manifest.py::test_public_export_clean_state_has_no_findings` 통과.
라이브(main) 반영도 완료 — `b15440f`(kics_disclosure.json · K-ICS공시.json · manifest.json).

덧: 이 티켓을 쫓다 **변이시험이 배포 산출물을 오염시킨 채 끝나는 경로**를 발견했다
(`CSM워터폴.json` 첫 행 100,383.8 → 100,384.8 이 남아 prepush 가 BLOCKED). 시작 시
오염을 먼저 감지하는 가드를 넣었다 — 커밋 `8afb23e`.

