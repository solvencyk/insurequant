---
from: orchestrator
to: designer
created: 20261012T2035Z
status: resolved
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): 「그게 확실하다면 도넛이랑 forward outlook 도 재산출해서 복원해」. 신종·후순위 분류가 근거와 함께 확정돼(owner 제공 기사·사업보고서·census) 소진율 도넛과 Forward Outlook 을 화면에 되살린다. **정의는 전체 기준(계정 단위) 그대로**: 기본자본 소진율 = 기본자본 자본증권(항목 6 기반, 우선주 등 포함, 보완자본형으로 확정된 증권 제외) 대 인정한도, 보완자본 소진율 = (한도 적용 전 보완자본 − 해약환급금 초과분 − 경과조치 기발행분) 대 보완자본 한도. 데이터 재산출·재공개는 publishing 티켓 `20261012T2030Z` 가 한다(진행 중 — 값이 바뀐 새 `kics_tier1_utilization.json`·`kics_tier2_utilization.json`·`kics_forward_capital.json` 이 곧 커밋된다). **빨리.**

### 해 줄 것 (`K-ICS.html`)
1. **도넛·전망 영역 복원**: 제거 커밋 `e2c72cd` 의 반대로 — `git show e2c72cd^:K-ICS.html` 의 소진율 도넛 패널(기본자본·보완자본)과 Forward Outlook(자본비율 전망) 영역·섹션 칩·fetch(`kics_tier1_utilization.json`·`kics_tier2_utilization.json`·`kics_forward_capital.json`)·CSS 를 되살린다. 그 앞 커밋 `dfd899e` 에서 한 **라벨 작업(메모 `data/_derived/capital_utilization_definition_20261012/definition_memo.md` §5: 「기본자본 자본증권 / 기본자본 자본증권의 인정한도 (총요구자본 × 10%, 기발행분 15%)」·「보완자본 한도 적용 전 / 보완자본 한도 (총요구자본 × 50%)」, 도넛 캡션 「기본자본 자본증권」·「보완자본」, 숫자 줄 「X억원 / 인정한도 Y억원」, `0%`·`발행 없음`·`—`(경과조치 표 미공시)·`100%+` 표시 규칙, `?` 팝오버)** 은 그대로 유지한다. 화면 이름은 공시·규정 표기 그대로, 의역·설명 문장 금지(설명은 `?` 안에만).
2. 자리: 소진율 도넛 → 그 밑에 기존 「자본성증권 발행현황」 누적 막대 + 큼직한 셀 2개(지금 있는 것 유지) → Forward Outlook 순서(복원 전 원래 순서를 따르되 막대·셀이 도넛과 전망 사이에 오게). 큼직한 셀은 타임라인 JSON 계산 그대로(`securities_summary` 로 되돌리지 말 것).
3. **새 필드 반영**: 전망 행의 `baseline_basis_flag`(시작점 기준 불일치 회사)·`type_unconfirmed`(이제 대부분 확정)·소진율 JSON 의 규칙 필드는 publishing 보고·`docs/changelog_publishing.md` 맨 위 명세를 읽어 반영한다(툴팁/`?` 만; 화면 문장 금지). 구판·필드 없음에서도 깨지지 않게 폴백.
4. **다운로드·제보 목록 복원**: `download-survey.js` 의 주석 처리된 3시트(기본자본소진율 T1·보완자본소진율 T2·자본비율전망 FWD)를 되살리고(주석의 되돌리기 안내 문구 삭제), `report-widget.js` 의 `SHEETS` 에 같은 3개를 복원. `tests/test_deploy_assets.py` 의 「tier1·tier2·전망 fetch 금지」 검사를 **다시 필수 fetch 검사로** 되돌린다(정확히 갱신, 느슨하게 풀지 말 것). `tests/test_share_screenshot.py` 의 K-ICS 섹션 수도 맞춘다.
5. `tests/test_push_gate_wiring.py` 의 `LIVE_ARTIFACT_READERS` 에 3개 루트 JSON 선언은 publishing 이 넣는다(HTML 복원 커밋과 같은 단위로 맞추려면 publishing 에게 알려라 — 어긋나면 그 시험이 막는다; 막히면 보고).
6. 점검: 헤드리스(`?iq_internal=1`)로 한화생명·메리츠·DB손보·하나손해·하나생명·교보·코리안리·스위스리(0%/발행 없음)·교보라이프플래닛(`—`)·동양(`100%+`)을 1280/375px·다크에서 확인(도넛 숫자·전망 곡선이 새 JSON 값과 같은지 JSON 직접 대조), 콘솔 오류 0, 섹션 공유 이미지 정상(섹션 수 갱신), 제거했던 영역 복원으로 생긴 빈 간격·죽은 칩 0. 새 데이터가 아직 안 올라왔으면 현재 JSON 으로 구현·점검하고 새 커밋이 올라오면 다시 점검. 시험(`test_deploy_assets`·`test_push_gate_wiring`·`test_prepush_scope`·`test_share_screenshot`)은 한 번에 하나씩 끝까지.

### 규칙
- 쓰는 파일: `K-ICS.html`·`download-survey.js`·`report-widget.js`·관련 시험. 마스터·xlsx·`public_exports/`·JSON 수정 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~5줄 존댓말)
- 복원한 영역·바뀐 줄, 확인한 회사와 JSON 대조 결과, 시험 결과, 커밋 해시. `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
처리 완료: 소진율 도넛·Forward Outlook 복원, 다운로드·제보 목록·시험 복원 (designer 496d359, 47f983ea). 발행현황 패널은 유지. orchestrator 종결 2026-10-13.
