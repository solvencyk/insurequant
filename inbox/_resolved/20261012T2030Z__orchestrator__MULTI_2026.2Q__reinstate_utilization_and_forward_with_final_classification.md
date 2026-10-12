---
from: orchestrator
to: publishing
created: 20261012T2030Z
status: resolved
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
### owner 결정 기록 (2026-10-12 채팅)
(가) 신종·후순위 분류 근거가 확정돼 **소진율 도넛과 Forward Outlook 을 다시 살린다**(owner: 「명확해지면 도넛이랑 forward outlook 도 다시 살려도 될 듯」). (나) 정의는 **전체 기준(계정 단위)**: owner 「신종·후순위만의 소진율을 보겠다는 게 아니라 전체 기준 기본/보완의 소진율을 볼 거고, 앞으로 각 보험사가 추가 발행해도 전부 인정 안 될 수 있다는 걸 보여주겠다는 취지」. 따라서 **현행 정의(`scripts/capital_utilization_rules.py`, 해설서 p13 표 각주 ⑴ 「보통주를 제외한 나머지 자본증권(신종자본증권, 우선주 등)」 = 계정 단위)를 그대로 유지**한다 — 기본자본 소진율의 분자는 항목 6 기반(우선주·전환우선주 포함), 보완자본 소진율의 분자는 항목 47 정규화(해약환급금 초과분·기발행 제외 후 나머지 보완자본 전부). 정의를 바꾸지 않는다. (다) 분류 확정(owner 제공 기사·사업보고서·census): DB손보 신종 5건 = 기본자본형(스텝업 없음, 국내 유일 기본자본 요건 충족) · 하나손해 2건(2024-05 1,000억·2026-06 약 1,000억) = 보완자본형(스텝업은 없으나 배당가능이익 없어 기본자본 요건 불충족) · 하나생명 제1회(1,800억, 2023-03-31) = 보완자본형(스텝업 구조) · 푸본현대·농협생명·코리안리 신규 신종 = 보완자본형(사업보고서 스텝업 문구; census 1차) · 교보 2024-11-12 6,000억은 발행조건 스텝업이라 보완자본형이나 발행사 K-ICS 표는 기본자본형 처리(불일치; census 최종본 `data/_derived/capital_securities_classification_census_20261012/census_securities_final.csv` 가 곧 나온다 — 있으면 그것을 따르고 없으면 현행 유지 + 불일치 보고).

### 해 줄 것
1. **등재부 갱신**(`data/bonds/capital_tier_registry.json`): 위 분류를 증권 단위 `type`·근거 문자열(출처 인용)로 반영, `type_unconfirmed` 는 확정된 증권에서 제거. census 최종본이 있으면 그 목록과 대조. 소진율 값을 박제한 시험(`tests/unit/test_capital_utilization_rules.py` 의 메모 재현 등)은 **이 재분류가 이유**임을 적고 갱신(느슨하게 풀지 말 것), 변이시험 유지.
2. **소진율 재산출**(`scripts/apply_disclosure_utilization.py` 현행 경로): `kics_tier1_utilization.json`·`kics_tier2_utilization.json`(2026.2Q 47사) + 전후 표(47사×tier1/tier2 전→후·사유)를 증빙으로 저장. 기대 변화: 하나생명 tier1 등. 변화 원인이 재분류인지 확인.
3. **Forward Outlook 모델 갱신**(`scripts/forward_capital_simulation.py`; 취소된 티켓 `inbox/_resolved/20261012T1200Z…forward_outlook_follow_tier_types.md` 의 정의를 그대로 쓴다): 채권을 등재부 증권별 `type`(legacy_tfi 15% / tier1 10% / tier2) 으로 취급. owner 요구: **상환 시 인정한도가 리셋되는 것까지 감안해 기본자본·보완자본이 빠지는 순서를 고려** — 매 연말 SCR 로 한도(기본자본 자본증권 10%·경과조치분 15%·보완자본 50%)를 다시 계산하고, 콜 도래일에 맞춰 잔액을 줄이며, 차감 순서는 기존 규칙(owner 2026-06-15: 한도 초과로 보완자본에 재분류된 부분 먼저, 그다음 기본자본; 후순위채는 보완자본에서 잔존만기 체감 포함)을 따르되 기본자본형 신종이 한도 안일 때 콜은 기본자본을 직접 깎는다. 보완자본형 신종·후순위채 콜은 총자본에서만 빠지고 기본자본은 불변. **기준시점이 회사 공시 기본자본이므로 우리 분류가 발행사 실제 처리와 다르면 콜 차감 계정이 어긋난다** → 분류와 발행사 K-ICS 표(항목 6·13−49)가 어긋나는 회사(하나생명·교보 등)는 전망 행에 `baseline_basis_flag`(시작점 기준 불일치) 필드를 달고 그 회사는 시작점 처리 방식을 한 줄 근거로 적는다(기본자본 경로를 실제 처리 기준으로 계산하는지 우리 분류 기준인지 명시). 총자본(지급여력비율) 경로는 분류와 무관해야 한다(콜 차감은 tier 무관) — 바뀌면 이유 보고. 전후 표(47사×연도×기본자본비율·지급여력비율)와 한화생명·DB손보·하나손해·하나생명·교보·메리츠 손계산 검산을 증빙으로 저장. 단위시험·변이시험 추가.
4. **재공개**: ⓐ `scripts/export_public_sheets.py` 의 `PRIVATE_SHEETS`·`PRIVATE_ROOT_JSONS` 와 `scripts/android_push_and_deploy.sh` 의 `PRIVATE_PATHS` 에서 기본자본소진율·보완자본소진율·자본비율전망 및 루트 JSON 3개(`kics_tier1_utilization.json`·`kics_tier2_utilization.json`·`kics_forward_capital.json`)를 뺀다(비공개 메커니즘 자체는 남긴다) ⓑ `public_exports` 3시트 재생성·`manifest.json` 갱신·재커밋 ⓒ 배포 keep-list·신규 파일 목록(`NEW_FILES`)에 필요한 항목 추가 ⓓ `tests/test_push_gate_wiring.py` 의 `LIVE_ARTIFACT_READERS` 에 3개 루트 JSON 선언을 **designer 가 K-ICS.html fetch 를 복원하는 커밋에 맞춰** 다시 넣는다(`783b7a6` 에서 죽은 선언으로 지웠다; 선언과 fetch 는 같은 커밋 단위 — designer 티켓 `20261012T2035Z` 와 순서를 조율: 먼저 이 티켓의 데이터·재공개를 커밋하고 designer 가 HTML 을 복원한 뒤 선언을 넣는다). ⓔ `download-survey.js` 주석 해제·`report-widget.js` 목록은 designer 몫.
5. 게이트·시험(`validate_data_contract.py`·`validate_live_artifacts.py`·`check_master_xlsx_drift.py`·`tests/unit/test_capital_utilization_rules.py`·`tests/test_private_deploy.py`·`tests/test_push_gate_wiring.py`·`tests/test_deploy_assets.py`·`tests/test_rule_coverage_manifest.py`) 한 번에 하나씩 끝까지. 새 RED 는 덮지 말고 종류별 보고. xlsx `기본자본소진율`·`보완자본소진율`·`자본비율전망` 시트는 `sync_master_xlsx_sheet.py` 로 기존 방식대로(시트 이름·열 구성 변경 금지). `TODO_publishing.md` Status + `docs/changelog_publishing.md`(새 필드·재공개 방법·되돌리는 방법).

### 규칙
- 정의(분자·분모)를 바꾸지 않는다. `kics_disclosure.json`·다른 마스터·HTML 수정 금지, 예외 등재 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만(고아 프로세스 즉시 종료). 이 공유 티켓은 고치지 않는다. owner 가 기다리니 빨리.

### 보고 (3~6줄 존댓말)
- 등재부 변경(증권 수), 소진율 전후 요약(바뀐 회사), 전망 모델 변경 요약(한화생명 기본자본비율 경로 전후, 총자본 경로 불변 여부, `baseline_basis_flag` 회사), 재공개 결과, 게이트·시험, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
처리 완료: 등재부 갱신·소진율 재산출·전망 모델·재공개 (publishing ef62969, 2729a53, 35740b2, 8037840). orchestrator 종결 2026-10-13.
