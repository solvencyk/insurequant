---
from: orchestrator
to: publishing
created: 20261011T0500Z
status: open
route: feature
company: MULTI
period: 2023.4Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11): 「발생사고요소가 발생사고부채(LIC) 말하는 거 맞냐? **걔도 마스터 테이블 만들어야지.**」 — 맞다: 발생사고요소 = 발생사고부채(LIC, 지급준비금 포함), 잔여보장요소(LRC, 잔여보장부채)와 합쳐 **보험계약부채**다. 지금 두 가지 모두 루트 마스터 JSON `insurance_liability_portfolio.json`(ILP: 항목 1~9 = 경영공시 4-6-2/2-4 잔여보장요소 구성·무저해지 예외모형 플래그, 항목 10~15 = 발생사고요소·DART 부채 기준 잔여보장요소 합계·보험계약부채 합계, 곧 16·17 = 단일열 회사 계산값)에 있지만 **마스터 엑셀(`insurequant_master_tables.xlsx`)에 시트가 없고 `public_exports/` 에도 없다** — 사이트 「테이블 다운로드(.xlsx)」에 안 나온다. designer 는 `tests/test_push_gate_wiring.py` 에 이 사실을 `MASTER_SHEET_PENDING`(「시트가 생기면 선언 삭제를 강제」)으로 선언해 두었다. **owner 승인(2026-10-11)으로 새 시트를 만든다**(마스터 엑셀 스키마 변경은 owner 승인 사항이었고 지금 승인됨).

### 해 줄 것
1. **시트 이름·구성**: 시트 이름 **`보험계약부채`**(잔여보장요소 + 발생사고요소를 한 시트에; 항목번호·항목명·섹션(`보험부채_잔여보장요소`/`보험부채_발생사고요소`/`해지율_예외모형`)·레벨 열로 구분). 열은 다른 마스터 시트와 같은 규칙(원보험사코드 등 내부 식별 열은 기존 시트 관행을 따르되 **공개본 `public_exports/` 에는 회사코드를 노출하지 않는다** — 기존 `public_exports/*.json` 이 코드를 어떻게 처리하는지 확인해 같게). 단위는 마스터 그대로(억원, 소수 둘째 자리까지) — 시트 머리말/열 이름에 단위 명시. 값 열 옆에 **기준 표시 열**(provenance 의 `basis`: liability/net/derived/latest_filing_comparative_restatable)과 **재작성 표시**가 필요하면 `insurance_liability_portfolio_provenance.json` 에서 가져온다(없으면 시트에 넣지 않고 이유 보고).
2. **스키마 변경 절차**: `scripts/build_master_xlsx.py`(전체 재생성은 **금지** — 시트 정의만 추가하고 실행은 하지 않는다)에 새 시트 정의를 넣고, 실제 파일 반영은 `scripts/sync_master_xlsx_sheet.py "보험계약부채"` 로 **새 시트만**(기존 16개 시트·수식 캐시 불변: openpyxl 열고 다시 저장 금지, 사후에 `data_only` 로 기존 시트 행 수·값 불변 확인). 시트 수 선언 `tests/test_rule_coverage_manifest.py::test_master_xlsx_sheet_count_matches_builder`(16 → 17)와 관련 선언을 같이 고친다.
3. **공개 스냅샷**: `scripts/export_public_sheets.py` 에 새 시트를 넣고(커밋된 HEAD 를 읽으니 마스터 커밋 후 실행) `public_exports/보험계약부채.json` 을 만든다. 내부 용어·회사코드 유출 게이트(`PUBLIC_EXPORT_INTERNAL_JARGON` 등) 통과, `manifest.json` 갱신, 배포 keep-list/`NEW_FILES` 에 새 파일 추가(`scripts/android_push_and_deploy.sh`, `tests/test_deploy_assets.py`). 사이트의 다운로드 팝업/목록(`IFRS17.html` 등 「테이블 다운로드」)이 `public_exports` 목록을 어떻게 만드는지 확인해 새 시트가 목록에 나오게 필요한 변경(데이터 쪽이면 직접, HTML 쪽이면 designer 몫으로 구체적으로 보고)을 한다.
4. **게이트·테스트 선언 정리**: `tests/test_push_gate_wiring.py` 의 `MASTER_SHEET_PENDING`(`data/csm_combo/panel_csm_combo.json`)을 새 시트로 바꾸고(「시트가 생기면 선언 삭제」 강제 테스트가 이를 요구), `PANEL_DERIVED_FROM` 등 매핑이 맞는지, 데이터계약 게이트의 master-xlsx 대조(`MASTER_XLSX_ROW_MISSING`/`DRIFT`)가 새 시트를 읽도록(`scripts/validate_data_contract.py` 의 시트 목록) 확인하고 필요한 것만 최소 변경. **ILP 가 아직 계속 늘어나는 중이면**(다른 parser-ifrs17 에이전트가 2024.1Q~ 백필·16·17 항목·재보사 4-6-2 를 적재 중) 시트는 **그 적재가 끝난 뒤의 마스터**로 동기화해야 하므로, 시작 전에 `git log -3 -- insurance_liability_portfolio.json`·`inbox/parser/20261011T0320Z…`(ILP 에이전트 티켓)의 상태·런로그 `data/disclosure/_meta/ilp_backfill_pre2025_runlog.md` 맨 위 「중간 결과」를 확인하고, 아직 진행 중이면 **스키마·시트 정의·테스트 선언·공개 스냅샷 코드까지만 만들고 동기화는 마스터 확정 후 한 번 더 한다고 보고**(오케스트레이터가 재발사).

### 규칙
- xlsx 는 전체 재생성·openpyxl 재저장 금지(수식 캐시 소실), 시트 단위 sync 만. 마스터 JSON 셀 수정 금지. 커밋은 자기 파일만(`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`), push·배포 금지. 서브에이전트 금지, docling 금지.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python -`(stdin heredoc) 절대 금지**, `encoding` 명시, UTF-8(BOM 없음). RAM 15.5GB. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 시트 구성(열·단위·기준 표시), 스키마 변경 목록(파일별), 동기화 결과(행 수, 기존 시트 불변 증명), `public_exports/보험계약부채.json` 행 수와 유출 게이트 결과, 다운로드 목록 반영 방식(designer 필요 변경 포함), 테스트·게이트 결과, 남은 일(마스터 확정 후 재동기화 등), `TODO_publishing.md` Status + `docs/changelog_publishing.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
