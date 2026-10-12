---
from: orchestrator
to: publishing
created: 20261012T0800Z
status: resolved
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅, 직접 선택): K-ICS 자본성증권 인정한도 소진율을 **Opus 조사 결과(`data/_derived/capital_utilization_definition_20261012/definition_memo.md` + `recompute_47.csv/json` + 재현 스크립트 `s1`~`s6`)대로 다시 정의해 반영**한다. owner 선택: 「보완자본 새 정의 반영(권장)」 · 「기본자본도 지금 전부」. owner 결정 사항 ①~⑦ 은 메모 §7 의 **권고안을 그대로 채택**한다: ① tier2 분자 = 경과조치 적용 후 열 + 발행사 관행 정규화 R0~R5 ② DB생명·미래에셋 「(기발행 후순위채무)」 행은 2023년 이후 신규채라 분자에서 빼지 않는다(31.6% / 24.5%), 한화생명은 인쇄값 기준 70.5% ③ tier1 분자에서 보완자본형 신종 제외 + 분모 10%(기발행분만 15%) + 증권별 계층 등재부 신설 ④ 표시: 분자 0 → 「0%」(자본증권이 없으면 「발행 없음」 덧붙임), 원문 부재 → 「—」 + 「경과조치 표 미공시」, 교보라이프플래닛 tier2 는 「산출 불가」 ⑤ 스위스리 tier2 0.0% 확정, 마스터 항목 49 는 채우지 않는다 ⑥ 화면 문구 메모 §5 채택(「공시 인정액」·「(전체)」 삭제) ⑦ 흥국생명 2025.4Q 항목 6(1,020, 앞뒤 2,796)·한화생명 항목 54(17,932 대 채권원장 14,711)는 **별건 점검 대상으로 보고만**.
또한 owner 지시: **화면 이름은 공시·규정 표기 그대로, 의역·설명 덧붙이기 금지**(설명은 `?` 팝오버).

### 해 줄 것 (이 티켓은 **데이터·산식까지**. HTML 은 designer 가 이어서 한다 — 산출 JSON 의 새 필드 명세를 보고에 정확히 적을 것)
1. **tier2 산식 변경**: `scripts/apply_disclosure_utilization.py`(메모 §6 diff 의 대상; `compute_tier2_utilization.py`·`scripts/add_reinsurers_to_capsec_panels.py` 의 관련 경로 포함) 에서 분자를 `값_적용후` 우선 + 규칙 R0~R5(메모 §3.1 표·`s5_final_recompute.py` 에 구현된 그대로, 게이트 `kics_json_rules._tier2_i47_scope_map` 를 **import** 해 항목 47 스코프 대조)로 바꾼다. 분모 = 경과조치 **적용 전** 총요구자본(항목 14)×50%. 47~54 부재 → 값 `null` + `reason="경과조치 표 미공시"`(KR1010 의 옛 `no_bonds` 0.0 경로 제거). 스위스리: 항목 47 인쇄값 0 을 그대로 써 0.0 (`numerator_undisclosed` 제거). 알지에이: 항목 3=0 → 0. 각 회사에 적용한 규칙 ID(R0/R1/…)와 근거를 행의 필드(예: `rule`, `numerator_source`)로 남긴다.
2. **tier1 산식 변경 + 증권별 계층 등재부 신설**: `data/bonds/capital_tier_registry.json`(신설, 증권/회사 단위로 `type`: `tier1`(기본자본형)·`tier2`(보완자본형)·`legacy_tfi`(2022년 이전 기발행, 15%), 근거 문자열(메모 §3.2 시계열 검정 결과·`s6_tier1_type_test.txt`·공개 보도/발행조건)). 메모 §3.2 표대로: 한화생명·KDB생명·하나손해·농협손해 신규 신종 = 보완자본형 → tier1 0.0, 흥국화재 62.4, 교보 70.1(max), 한화손해 53.1(max), DB손해 151.6(10% 한도), 하나생명 238.2, 메리츠·롯데·KB라이프·아이엠라이프 현행과 같음, 삼성화재 0.5 등. 산식: `pct = max( 기발행 신종(항목 53) ÷ (SCR×15%) , 기본자본형 신규 ÷ (SCR×10%) )`. **미정 4사(코리안리·농협생명·푸본현대·흥국생명)**: 먼저 공개 자료(WebSearch 만 — `go.kr`·`law.go.kr`·`kipris` 는 브라우저·WebFetch 금지; DART 증권신고서·IR·신용평가 보고서·보도)와 같은 시계열 X 검정으로 발행조건(스텝업·이자지급 재량)을 확정해 `type` 을 정한다. 끝내 못 정하면 **보수적 상한(신규를 기본자본형으로 보고 분모 10%)** 으로 계산하되 `type_unconfirmed=true` 플래그를 달고 확정 못 한 사유를 등재부에 적는다(owner 보고 대상).
3. **재산출**: `kics_tier1_utilization.json`·`kics_tier2_utilization.json`(2026.2Q 47사) + 이 숫자에 의존하는 파생물(`kics_forward_capital.json`·`data/bonds/capital_securities_forward_outlook.json`·`data/bonds/capital_securities_utilization_20261Q.json` 등 — 실제 의존 여부를 먼저 코드로 확인; 의존하면 같은 규칙으로 정합, 아니면 보고만). 재산출 결과를 메모의 `recompute_47.csv` 와 **47사 전부 대조**(차이 0 이어야 하고, 차이가 나면 이유 보고). 기존 JSON 의 필드 이름·구조는 최대한 보존(새 필드 추가만)해 구판 HTML 이 깨지지 않게. 이전 값과의 전후 표(회사·tier·전→후·규칙)를 증빙으로 저장.
4. **게이트·시험**: 이 숫자를 읽는 게이트(`validate_data_contract.py` 4번 도메인-항등식: 분모=SCR×50%·소진율≤100% 등, `validate_kics_disclosure.py`, `validate_live_artifacts.py`, `tests/` 의 utilization·tier 관련)가 새 값에서 RED 를 내는지 확인. **새 RED 는 예외로 덮지 말고 종류별로 보고**(진짜 한도 초과 발행 DB손해 151.6%·하나생명 238.2%·동양 105.0%·농협손해 103.9% 등은 규정상 정당하니 게이트 쪽 정당 초과 허용 규칙이 필요하면 validation 이 하도록 목록으로 보고). 새 산식·등재부에 대한 단위시험 + 변이시험(규칙을 지우거나 등재부 type 을 바꾸면 결과가 바뀌는지) 추가.
5. **xlsx·공개본**: xlsx `기본자본소진율`·`보완자본소진율` 시트를 `scripts/sync_master_xlsx_sheet.py "<시트>"` 로 동기화(전체 재생성·openpyxl 재저장 금지, 시작 전 백업, 기존 행 변경은 이번엔 의도된 재산출이므로 「행·칸 변경 목록」으로 증명하고 시트 이름·열 구성 변경은 금지; 새 열이 필요하면 보고만), `public_exports/기본자본소진율.json`·`보완자본소진율.json`(`export_public_sheets.py` 는 커밋된 HEAD 를 읽는다 → 마스터·xlsx 를 먼저 커밋한 뒤 실행·재커밋), `scripts/check_master_xlsx_drift.py`·`validate_data_contract.py` (MASTER_XLSX_* 0).
6. **다른 분기**: 메모 §8 — 2026.2Q 만 재현했다. 현재 배포 JSON 도 2026.2Q 단일 분기이므로 이번 범위는 2026.2Q. (과거 분기 계산 지원이 코드에 있으면 같은 규칙이 적용되는지만 보고.)

### 규칙
- `kics_disclosure.json`·다른 마스터 수정 금지. 예외 등재 금지(owner 승인 사항은 보고만). **HTML 금지**(designer 몫). 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json` 제외, `.gitignore` 경로를 `git add` 에 넣지 말 것), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`(Opus 로 돌면 모델명은 실제 모델로). **push·배포 금지**. 서브에이전트 금지, docling 금지.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·맨 `python`·stdin heredoc 금지), `encoding` 명시, UTF-8(BOM 없음). 인자를 모르는 스크립트를 `--help` 로 실행하지 말 것. PC 는 느리니 무거운 일은 한 번에 하나씩, 풀 훅·전체 pytest 금지. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고 (3~6줄 존댓말 + 파일 경로)
- 47사 전/후 요약(바뀐 회사 수·큰 변화), 메모 대조 결과(차이 0 여부), 미정 4사 분류 결과(확정/미확정+플래그), 새 JSON 필드 명세(designer 용: 필드 이름·값 의미·`null`/`reason` 규칙·`type_unconfirmed`·`rule`), 게이트 새 RED 종류별 목록, 시험 결과, 별건 점검 대상(⑦), 커밋 해시. `TODO_publishing.md` Status + `docs/changelog_publishing.md`.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 c3ebcc3·00bab2a·bd69673·3fe9a53·267241b, Opus). 소진율을 규정 근거로 재정의해 47사 재산출(메모 재현표와 차이 0): tier2 23사 변경(한화생명 222.4->70.5, 메리츠 55.4->0.2, 미래에셋 112.4->24.5, 교보라이프플래닛 null+「경과조치 표 미공시」, 스위스리 0.0), tier1 14사 변경(한화생명 136.3->0, 하나손해 284.9->0, DB손해 101.1->151.6, 하나생명 158.8->238.2). 신설 data/bonds/capital_tier_registry.json, scripts/capital_utilization_rules.py, 단위시험 25(+변이 3종 전부 포착). 미정 4사: 흥국생명 기본자본형 확정(81.4), 코리안리·농협생명·푸본현대 미확정(type_unconfirmed, 상한 205.1·72.7·42.1 / 보완자본형이면 94.0·48.5·17.3). 새 JSON 필드 명세는 docs/changelog_publishing.md 맨 위. data-contract RED 0, 보완자본 100% 초과 YELLOW 2건(농협손해 103.9·동양 105.0). owner 결정 남음: 메리츠·흥국생명 「기발행 후순위채무」 행 처리(메모 0.2·10.6 대 원장 30.8·37.0), 별건 흥국생명 2025.4Q 항목 6 · 한화생명 항목 54 점검.
