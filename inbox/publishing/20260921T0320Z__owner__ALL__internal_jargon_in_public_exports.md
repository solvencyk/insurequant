---
from: owner
to: publishing
created: 20260921T0320Z
status: answered
route: escalate
company: ALL
period: N/A
rule: USER_FACING_META_TEXT
iter: 1
---

## 미결 (sender 작성)

owner 지적(2026-09-21): **화면·산출물에 내부 작업 문구(메타발언)가 나가면 안 된다.**
IFRS17.html 가정민감도 각주 건은 `354b0f2` 로 고쳤고, 같은 유형이 **다운로드 시트에 하나 더**
남아 있다.

### 무엇이

`public_exports/자본비율전망.json` 의 `비고` 컬럼 **610행**이 게이트 내부 진단 문자열을 달고 있다.
사용자가 이 시트를 내려받으면 그대로 본다.

```
… / 신뢰도 낮음(발행잔액 vs BS 괴리) — T2 face/BS gap +202% (subordinated_eok) — advisory, not in overall
… / 신뢰도 낮음(발행잔액 vs BS 괴리) — T2 FSC gap: BS 298억 but bond DB=0; T2 face/BS gap -100% (numerator_eok_fallback) — advisory, not in overall
… — T1 face/BS gap +106% (tier1_hybrid_issued_eok); …
```

`subordinated_eok` · `tier1_hybrid_issued_eok` · `numerator_eok_fallback` 은 **필드명**이고,
`advisory, not in overall` 은 **게이트 용어**다. 독자에게는 아무 뜻이 없다.

발생원: `scripts/forward_capital_simulation.py:336` 등이 `reasons` 에 진단 문자열을 붙이고,
그게 루트 마스터 `kics_forward_capital.json`(18곳) → `public_exports/자본비율전망.json` 으로 흘러간다.
K-ICS.html 은 이 필드를 렌더하지 않으므로 **대시보드 화면에는 안 보인다** — 다운로드 시트 한정이다.

### 남겨야 할 것 / 지워야 할 것

- 남긴다(사용자에게 뜻이 있는 경고): `콜옵션 미공시 채권 포함 — 콜일자를 발행일+5년/신용등급이력 등으로 추정
  (원문 미기재), 실제 콜상환 시점과 다를 수 있음` · `신뢰도 낮음(발행잔액 vs BS 괴리)` ·
  `자본잠식(가용자본<=0) — 비율 0%로 캡 표시`
- 지운다(내부 진단): `— T1/T2 face/BS gap …%` · `(subordinated_eok)` 류 필드명 ·
  `T2 FSC gap: BS …억 but bond DB=0` · `advisory, not in overall`

### 시킬 일

1. **원천에서 가른다.** 진단은 지우지 말고 **별도 필드**(예: `_diagnostics`)로 옮기고,
   `비고` 에는 사용자 문구만 남긴다. export 단계에서 문자열을 잘라내는 땜질은 하지 말 것 —
   원천이 그대로면 다음 빌드에 또 샌다.
2. 마스터 재생성은 **통짜 실행 금지**. 바뀌는 게 텍스트 필드뿐임을 diff 로 먼저 보이고,
   숫자가 한 칸이라도 움직이면 멈추고 보고한다. `kics_forward_capital_provenance.json` 동반 확인.
3. `public_exports/자본비율전망.json` 재생성은 마스터 커밋 후(그 스크립트는 커밋된 HEAD 를 읽는다).
4. 같은 유형 재발을 막는 검사를 넣을지 validation 과 협의한다 — 배포 산출물의 사용자 문자열에
   필드명·영문 게이트 용어가 섞이면 잡는 검사. (validation 에는 이미 배포 HTML JS 런타임 게이트
   티켓이 열려 있다: `inbox/validation/20260921T0057Z__owner__ALL__deployed_js_runtime_blind_spot.md`)

참고로 아래 두 건은 **내부 용어가 아니라 데이터 단서**라 판단해 건드리지 않았다. 문구를 다듬을지는
owner 판단: `public_exports/가정민감도.json` 비고 `"같은 충격이 이 회사 표에 2벌 있다(재보험 경감
전/후로 추정, 원문 라벨 미확인) — 순번으로 구분"`(10행), `public_exports/자본성증권발행현황.json`
구분 `"… 후순위 명시 라벨 없음, 구조 기반 추정"`(3행).

## 답변 (recipient 작성 — 처리 후)

**처리 완료 (publishing, Sonnet 5, 2026-09-21).**

### 1. 원천 재확인 — "발생원"은 forward_capital_simulation.py가 아니라 build_master_xlsx.py였다

`scripts/forward_capital_simulation.py`의 `compute_confidence()`(L320-373, append 지점
8곳)가 만드는 `reasons` 리스트는 **루트 마스터 `kics_forward_capital.json`에 그대로
저장된다** — 이 파일에는 `비고` 필드 자체가 없다(`confidence.reasons`만 있음, 코드 38사
전수 확인). `비고` 텍스트는 마스터 데이터가 아니라 **flatten(long-format 변환) 시점의
파생값**이고, 그 조립 지점이 `scripts/build_master_xlsx.py::_flatten_forward_capital()`
L309-311이었다:
```python
if conf.get("level") == "low":
    reasons = "; ".join(conf.get("reasons") or [])
    notes.append(f"신뢰도 낮음(발행잔액 vs BS 괴리) — {reasons}" if reasons else "신뢰도 낮음")
```
`export_public_sheets.py`는 이 함수를 `FLATTEN` 딕셔너리로 **import해서** 쓰므로(자체
재구현 없음), xlsx 시트와 공개 다운로드가 같은 지점에서 같이 샌다 — 그래서 원천을 여기서
갈랐다. `forward_capital_simulation.py`는 손대지 않았다(내부 진단으로서 `reasons` 자체는
정상 — 문제는 그걸 사용자 컬럼에 그대로 join하던 조립부였다).

**따라서 `kics_forward_capital.json`(루트 마스터)과 `kics_forward_capital_provenance.json`은
이번 수정에서 전혀 건드리지 않았다** — `git status`로 무변경 확인(diff 0, 숫자는 애초에
움직일 여지가 없었다).

### 2. 수정 (커밋 `44ae5fb`)

`scripts/build_master_xlsx.py::_flatten_forward_capital()`:
- `비고`에는 `"신뢰도 낮음(발행잔액 vs BS 괴리)"`만 남기고 `reasons` 원문 join 제거.
- 신설 컬럼 `row["_diagnostics"]`에 `"; ".join(conf.get("reasons") or [])` 보존(내부
  검토용, 삭제 아님 — 매 행에 항상 존재, 값 없으면 빈 문자열).
- `scripts/export_public_sheets.py`의 `_DROP_COLS`에 `_diagnostics` 추가(원보험사코드와
  같은 취급) — 공개 다운로드에서만 빠지고, 내부 `insurequant_master_tables.xlsx`에는 남는다.
  `비고`는 그대로 유지(드롭 안 함 — 지시대로).

### 3. 셀 단위 diff 증명 (숫자 이동 0)

`_flatten_forward_capital()` 재실행 검증 (수정 전/후):
- 총 행수 2090 → 2090 (변화 없음)
- 비고에 남아있던 jargon 행: **660행 → 0행** (owner 추정 610행보다 조금 많았음 — 실측)
- `_diagnostics` 비어있지 않은 행: 1980행 (신설 컬럼, 내부용)

`sync_master_xlsx_sheet.py --dry-run` 및 별도 프로그램적 대조(비고를 제외한 식별키로
재매칭):
```
변경 셀 1320 · 추가 행 770 · 삭제 행 770 (시트 2090행 → 목표 2090행)
edits_by_col: {'_diagnostics': 1320}   # '값' 컬럼 EDIT 0건
value-continuity check (비고 제외 키로 재매칭): checked 2090, mismatches 0
```
770 삭제+770 삽입은 숫자 이동이 아니라 **`비고`가 행 식별키 컬럼이라 텍스트가 바뀐 행이
delete+insert로 나타난 것**(사전에 알던 기존 설계 — `TEXT_COLS`에 `비고` 포함). 1320개
EDIT는 전부 신설 `_diagnostics` 채움(값 컬럼 EDIT 0건). 코리안리(KR1000) 등 12개사·
770행의 '값' 컬럼을 비고 제외 키로 재매칭해 전수 대조 — 불일치 0.

`insurequant_master_tables.xlsx` 자체 사후검증도 통과: "검증 OK — 자본비율전망 2090행
× 9열 마스터와 완전 일치, 나머지 시트 값 동일". `scripts/check_master_xlsx_drift.py`:
`대조 시트 13 · 대조 행 56381 · 드리프트 셀 0`.

**도구 확장 1건**: `sync_master_xlsx_sheet.py`는 원래 "새 시트 생성"만 지원하고 "기존
시트에 컬럼 신설"은 REFUSE했다(`_diagnostics` 추가가 여기 걸림). 순수 추가(기존 컬럼이
목표 컬럼의 앞부분과 정확히 일치할 때만) 케이스를 새로 지원하도록 최소 확장, 그 외 불일치는
계속 REFUSE(커밋 `a61c8b2`).

### 4. public_exports 재생성 (커밋 `c130062`)

마스터 xlsx 커밋 뒤 `export_public_sheets.py` 재실행(커밋된 HEAD 읽음). 재생성 결과:
- `자본비율전망.json`: 2090행 유지, 키셋(원수사명·티커·생손보여부·공시분기·항목명) 동일
  (누락 0·추가 0), 공유 키의 '값' 불일치 0.
- `subordinated_eok` · `numerator_eok_fallback` · `tier1_hybrid_issued_eok` ·
  `advisory, not in overall` · `face/BS gap` · `FSC gap` — 전부 0건 확인(재검색).
- `_diagnostics` 컬럼은 export에 없음(드롭 확인).
- `manifest.json`은 `generated_at_utc`·`build_id`만 변경, 나머지 12개 시트 파일은
  `git status`상 무변경(바이트 동일).

### 5. K-ICS.html 렌더 여부 확인

`grep -n "비고\|reasons\|confidence" K-ICS.html` — 0건. index.html에 "비고" 매치가
있으나 CSM 수록 현황 표의 자체 비고 칼럼(무관). 대시보드 어디도 이 필드를 렌더하지
않는다는 티켓의 claim, 확인됨.

### 6. 골든/지문

`tests/fixtures/builder_input_fingerprints.json`·`scripts/validate_golden_input_fingerprints.py`
어디에도 `forward_capital_simulation` / `build_master_xlsx`가 등재돼 있지 않다(grep 0건) —
해당 없음, 갱신 불필요.

### 7. 게이트

- `scripts/validate_live_artifacts.py`: `SUMMARY live_artifacts RED=0 YELLOW(baselined)=17`
  (전부 이 변경과 무관한 기존 baseline). `PUBLIC_EXPORT_DRIFT`/`PUBLIC_EXPORT_MISSING_CELL`
  findings 0건.
- `scripts/validate_data_contract.py`: `SUMMARY RED=0 YELLOW=123`(전부 기존 baseline).
  `MASTER XLSX` 체크 `RED=0 YELLOW=1`(census만, 드리프트 셀 0).

### 8. validation 협의 티켓 (4번 지시)

`inbox/validation/20260921T0335Z__publishing__ALL__public_export_jargon_check_proposal.md`
신설 — 정규식 후보 4개(`advisory, not in overall` / `_eok` 필드명 패턴 / `T[12] face/BS|FSC
gap` / `limit breach`) + 두 false-positive 케이스(가정민감도 비고, 자본성증권발행현황
구분)를 **직접 매칭 테스트해 0건임을 확인**한 뒤 첨부. 구현은 하지 않음(제안만, validation
판단 대기).

### 커밋

- `44ae5fb` fix(publishing): 자본비율전망 비고에서 내부 게이트 진단 문구 분리 (build_master_xlsx.py, export_public_sheets.py)
- `a61c8b2` chore(publish): 자본비율전망 시트 sync — _diagnostics 컬럼 신설 반영 (sync_master_xlsx_sheet.py, insurequant_master_tables.xlsx)
- `c130062` chore(publish): public_exports 재생성 (public_exports/자본비율전망.json, manifest.json)

브랜치 `fix/csm-product-segmented-columns`. **push는 안 했다** — main 배포 여부는 오케스트레이터/owner
판단. main에 올라갈 필요가 있다면 이 3커밋(스크립트 2개 + xlsx + public_exports 2파일)이 대상.

### 못 닫은 것

없음. 4단계 지시 전부 처리, 게이트 RED=0, 데이터 마스터 무변경 증명 완료.
