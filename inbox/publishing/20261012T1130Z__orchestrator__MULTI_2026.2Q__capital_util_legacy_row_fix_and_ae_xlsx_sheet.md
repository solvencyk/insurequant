---
from: orchestrator
to: publishing
created: 20261012T1130Z
status: open
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
### owner 승인 기록 (2026-10-12 채팅)
(가) 메리츠·흥국생명 「기발행 후순위채무」 행: owner 가 「2023 이후 발행분은 기발행에서 제외하고 소진율에 가산한다 = 소진율이 증가한다」 는 설명에 「ㅇㅋ」 로 승인했다. (나) 한화생명·KDB생명·하나손해·농협손해·흥국화재의 신규 신종: owner 가 AskUserQuestion 에서 「현재 유지(권장)」 를 선택했다 = 기본자본 소진율은 회사 공시대로 보완자본형으로 보아 0% 유지(분자에서 제외), 코드 변경 없음. (다) 예실차 xlsx 시트 신설(스키마 변경)은 owner 가 「나머지는 다 승인」 으로 승인했다(`TODO.md` ㉓).

### 해 줄 것
1. **메리츠(KR0001)·흥국생명(KR0071) tier2 분자의 기발행 차감액**: 직전 작업(`c3ebcc3`, 규칙 R2)은 항목 54 「(기발행 후순위채무)」 인쇄값 전체를 기발행으로 빼서 메리츠 0.2%·흥국생명 10.6% 가 됐다. 채권원장(`kics_capital_securities.json`)상 2022년 이전 발행 후순위는 메리츠 5,960억(항목 54 인쇄 15,630.85억)·흥국생명 394.81억(인쇄 4,132.49억)뿐이라 나머지는 2023년 이후 신규채다(`data/_derived/capital_utilization_apply_20261012/a11_legacy_row_overreach_alt.txt`). 두 회사는 **기발행 차감액 = 채권원장 2022년 이전분**(= `exempt = ledger legacy`)으로 바꿔 메리츠 30.8%·흥국생명 37.0% 가 되게 한다(DB생명·미래에셋과 같은 취급 — 신규채는 한도 대상). 규칙 ID·근거를 행 필드에 남기고(`rule`/`rule_basis`), `capital_tier_registry.json` 등 근거 문자열 갱신, 단위시험·변이시험 갱신. **다른 4사(한화생명 74.8·KB손해 20.5·에이비엘 70.4·IBK 76.2)는 이번에 바꾸지 않는다** — 값 변화 목록만 보고(owner 가 일관 적용 여부를 정한다).
2. 재산출 → 기존 방식대로 `kics_tier2_utilization.json`·`kics_forward_capital.json`(신뢰도만 바뀌는지)·`data/bonds/` 파생·xlsx `보완자본소진율`/`자본비율전망` 시트(`scripts/sync_master_xlsx_sheet.py`)·`public_exports/` 재생성·재커밋(`export_public_sheets.py` 는 커밋된 HEAD 를 읽는다). 전후 표(47사 중 바뀐 칸)와 게이트(`validate_data_contract.py`·`validate_live_artifacts.py`·`check_master_xlsx_drift.py`) 비교를 증빙으로 저장. 새 RED 는 덮지 말고 보고.
3. **예실차 xlsx 시트 신설**(스키마 변경 승인됨): 소스 `data/loss_ratio/claims_ae_ratio.json`(보험금 예실차비율 44사, 기준연도 2024·2025 연말 공시; 열은 소스 필드 그대로 — 회사·기준연도·공시분기·사업구분·예상손해율·실제손해율·보험금 예실차비율·플래그·출처 쪽 등). `scripts/build_master_xlsx.py` 의 `MASTERS` 에 항목 1개 추가(시트 이름은 「보험금예실차비율」, 설명 1줄은 기존 문체) → `scripts/sync_master_xlsx_sheet.py "보험금예실차비율"` 로 **그 시트만** 추가(전체 재생성·openpyxl 재저장 금지, 시작 전 백업, 다른 시트 바이트 불변 증명). `public_exports/보험금예실차비율.json` 생성·`manifest.json`·다운로드 목록(`download-survey.js`·`공시보고서.html` 의 시트 목록 등 시트 이름이 나열된 모든 곳 — 새 시트가 목록에 빠지면 사이트 다운로드에 안 보인다; 코드 변경 범위가 HTML 이면 designer 몫이므로 **위치만 보고**)을 확인한다. `check_master_xlsx_drift.py`·`validate_data_contract.py`(MASTER_XLSX_* 0) 통과.
4. 이 결과를 `TODO_publishing.md` Status·`docs/changelog_publishing.md` 에 남긴다.

### 규칙
- `kics_disclosure.json`·다른 마스터 수정 금지. 예외 등재 금지. **HTML 금지**(designer 몫). 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 파일 제외, `.gitignore` 경로를 `git add` 에 넣지 말 것), 끝에 `Co-Authored-By:` 줄(실제 모델명). **push·배포 금지.** 서브에이전트 금지, docling 금지. 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만. 시험·게이트는 한 번에 하나씩 끝까지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~6줄 존댓말)
- 메리츠·흥국생명 전→후, 다른 4사 값 변화 목록, 새 시트 행 수·시트 바이트 불변 증명, 시트 이름이 나열된 위치(designer 용), 게이트 결과, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
