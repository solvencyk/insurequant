# Insurequant Changelog — Designer Stage

> Last updated: 2026-10-11 · Stage 5/5 — designer
> Prompt: docs/agents/claude-agent-designer.md · TODO: TODO_designer.md

Scope: HTML structure / styling / responsive breakpoints / chart layout / A11y. Master JSON content is **publishing** ([`changelog_publishing.md`](changelog_publishing.md)) — designer reads them but does not modify. Cross-stage history: `docs/claude-changelog.md`.

---

> 보관: 이전 달 항목은 `docs/changelog_archive/designer/` 에 월별로 무수정 보관한다(관리 `scripts/doc_rotate.py changelog`, 현행 = 최신 항목 달과 그 전 달).

## 2026-10-19 (밤) — 손해율 비교 단위 선택기 · 오류 제보 내부 접속 제외 · a11y C1·C2·C3·C4·C6 (owner 승인, push `a8d9f193`, main 배포 `5221a1b4` 완료)

- **비교 단위 선택기(compare.html · IFRS17.html 8절 · `scripts/check_loss_unit.py`)**: 구분 버튼을 라벨 붙은 select 하나(머리글: 구분 · 생보 · 손보 · 재보)로 바꿨다. 처음 화면은 업권별 기본 단위. 단위를 공시하지 않은 회사는 합계로 바꾸지 않고 선 없이 n/a 줄에 사유(변액사망은 Indirect-Par 로 공시한 회사에만 그 문구, `loss_curve.alt_co`). 위험보험료 100억원 미만 칸은 흐린 점선+속 빈 표식. 주소 `g=` 는 구분 이름과 단위 키 모두(옛 링크 유지). 구판 JSON 이면 단위 선택지가 숨고 예전 동작. 점검: 데이터 5,289칸 · compare 220상태 · IFRS17 507건 · 배포본 대비 회귀 82건, 위반 0 · 수집기 0.
- **오류 제보 내부 접속 제외(`report-widget.js`, `scripts/check_report_widget_internal.py`)**: `iq_internal=1` 이면 수집기로 행을 보내지 않는다. 화면 흐름은 그대로, 일반 방문 페이로드 동일(9개 시나리오). 일본 사이트 `jp/report-widget.ja.js` 는 미적용.
- **a11y C1·C2·C3·C4·C6(`common.css` · `theme.js` · `compare.html` · `scripts/check_a11y_compare_privacy.py` · `docs/a11y_baseline.md` §5e · 티켓 `20261019T1400Z`)**: C1 ? 팝오버 마우스 접근(`::before` 다리 + 떠난 뒤 400ms 유예 `is-grace`; 먼저 넣은 옆 삼각형은 오른쪽 끝에서 문서를 가로로 넓혀 버림), C2 포커스 유지, C3 `--control-border`(라이트 3.56:1 · 다크 3.97:1) 글자 입력창만, C4 placeholder `var(--muted)`(5.76 · 6.83), C6 모바일 선 표식. 덤: 375 폭 손해율 카드 ? 팝오버가 화면 밖에 남던 버그 수정. C5 · C7 · C18 은 owner 가 하지 않기로, C8~C17 열림.

## 2026-10-19 — 안내 팝업 시작일 · 손해율 기본 Non-Par · 방명록 내부 접속 제외 · a11y 감사 (owner 승인, main 배포 `f96f06b0` 완료)

- **3분기 안내 팝업 시작일**: `theme.js` `NOTICE.showFrom` 2026-10-31 추가. 방문자 로컬 날짜가 showFrom 이상 hideAfter(2026-12-31) 이하일 때만 뜬다(hideAfter 와 같은 날짜 문자열 비교, 시간대 변환 없음). `scripts/check_notice_popup.py` 498건(Asia/Seoul · UTC · America/Los_Angeles 경계 포함) 위반 0, 독립 검증 47/47.
- **손해율 구분 선택기 기본값 Non-Par**(compare.html 손해율 카드 · IFRS17.html 8절 · `scripts/check_loss_group.py`): compare 는 주소 `g` 없음이 Non-Par, 나머지는 `g=합계` 등으로 적고 옛 링크 `g=Non-Par`·`g=합계` 유지. Non-Par 가 없는 회사는 합계 → 첫 구분으로 대체하고 이름 옆에 구분을 적는다. IFRS17 8절도 같은 순서. 합계를 명시로 고르면 선택기 도입 직전 숫자와 글자 그대로 같다. 점검 316건 위반 0, 마스터 재계산 대조 최대 0.05pp. 단일 구분 회사도 합계와 그 구분 두 선택지를 보인다(카카오페이손보는 잎 합과 공시 합계 행이 한 칸 14.3pp 어긋나 validation 확인 중).
- **다운로드 방명록 내부 접속 제외**(`download-survey.js`, `scripts/check_download_survey_internal.py`): `iq_internal=1`(주소 또는 localStorage)이면 수집기로 행을 보내지 않는다. 설문과 다운로드 화면은 그대로. 10개 시나리오(수집기·분석 요청 가로채 개수만 셈) 통과. 오류 제보(`report-widget.js`)는 범위 밖.
- **a11y 감사(compare · privacy, 감사만)**: `docs/a11y_baseline.md` 를 6페이지로 넓히고 위반 18건(중간 6 · 낮음 9 · 참고 3)을 기록, designer 티켓 `20261019T1400Z` 발행. 텍스트 대비 최소 5.28:1(다크 6.10) · 포커스 링 6.09:1 이상 · 가림/키보드 함정/가로 넘침 0 통과. 색 변경 5건은 owner 승인 필요.

## 2026-10-18 — 손해율 가정 구분 선택기 + 2026 3분기 안내 팝업 (owner TODO 일괄 처리, 커밋·미배포)

- **손해율 가정 구분 선택기(compare.html · IFRS17.html 8절 · `scripts/viz_build_compare_panel.py` · `data/compare/panel_compare.json` · `scripts/check_loss_group.py`)**: 회사 전체 포트폴리오 한 줄은 뒤쪽 경과차년에서 계약 유형 비중이 달라져 곡선이 꺾이므로(스위스리 사례) 구분(합계 · Non-Par · Indirect-Par · Direct-Par, 공시 이름 그대로) 선택기를 넣었다. 기본은 합계라 기존 숫자는 그대로(HEAD 와 동일 확인). compare 는 넓은 화면 Chart.js · 좁은 화면 SVG · 현재가치 표 · 업계 중앙값이 같은 선택을 따르고 주소 `g=` 로 공유한다. IFRS17 8절은 패널 JSON 에 이미 있는 구분 소계 행을 쓴다(합계 행이 없는 뮌헨 · 제네럴 · 퍼시픽라이프리 사업구분은 선택지에서 합계를 빼고 구분이 하나면 선택기를 숨김). 믹스 효과 설명은 ? 팝오버에만. 빌더에 구분 축(`loss_curve.g` · `med_g` · `note_g`, `loss_pv.vg` · `medg`)을 더해 `panel_compare.json` 120,456 → 153,426 바이트(기존 필드 불변, 마스터 무수정, `--check` OK).
  검증: 전 회사 마스터 재계산 대조(곡선 최대 0.05pp, 점 2,041 + 2,095), 합계 선택 시 HEAD 와 동일(compare 18/18 · IFRS17 47/47), 1280/375/다크 가로 넘침 0 · 콘솔 오류 0, `tests/test_deploy_assets.py` + `tests/test_push_gate_wiring.py` 78 통과. 남은 것: IFRS17 현재가치 구분 소계 이중 반올림 5칸(최대 0.054pp, publishing), 스위스리 Indirect-Par 21~25년 159.27(원문 공시값) 확인은 owner 판단. 배포 때 HTML 2개 · `panel_compare.json` 같이.
- **2026 3분기 업데이트 안내 팝업(`theme.js`)**: 파일 맨 위 `NOTICE`(id 2026-3Q · owner 문구 네 줄 · hideAfter 2026-12-31)를 5개 대시보드 페이지가 브라우저당 1회 띄운다(닫으면 localStorage `iq_notice_seen`, 저장소가 막히면 방문마다, 분석·shLog 호출 없음, 새 배포 파일 없음). 다이얼로그 접근성(role · aria-modal · Esc · 백드롭 · 초점 이동/복귀 · Tab 가둠) · 대비 5.76:1 이상 · 375px 가로 넘침 0 · 레이아웃 이동 0. 검사 `scripts/check_notice_popup.py` 428건 위반 0, 독립 검증도 통과. 팝업이 클릭을 가리므로 브라우저 검사 스크립트 10종은 컨텍스트에 `iq_notice_seen` 을 미리 넣도록 한 줄씩 고쳤다(`tests/regression_*.py` 3종은 사전 주입 필요, 푸시 훅 비연결).

## 2026-10-13 (2) — 발행현황 추정 행 툴팁 꼬리 + 새 JSON 재점검 (ticket 20261013T0030Z)

- `capsecSeries()` 가 연도별 `estimated` 를 모아 막대 툴팁 꼬리(footer)에 「추정(원장 미갱신)」을 붙인다(없는 해는 꼬리 없음). 셀·계산은 그대로.
- 점검 스크립트: `scripts/check_kics_donuts.py`(도넛 데이터셋·aria·숫자 줄·경과조치 기발행 후순위 줄을 JSON 직접 계산과 대조, 47사), `scripts/check_kics_capsec_cells.py`(막대 연도별 합·추정 꼬리 47사, DB손해 신종 콜 칸 날짜만, 하나손해 셀·막대). 새 JSON(HEAD `392efee2`)에서 위반 0.

## 2026-10-13 — K-ICS Forward Outlook 거짓 개선 제거 · 음수 △ · 도넛 툴팁 375px · 콜일 칸 내구성 (ticket 20261012T2236Z)

- **원인**: 노트가 자르지 않은 기준선에서 잘린(0.0) 2030 값을 빼 예별 「+41.8%p」·롯데 「+5.4%p」를 인쇄했고, 차트도 0 선과 「0.00%」 툴팁을 그렸다. 노트의 음수 기준선은 ASCII 마이너스였다.
- **변경(`K-ICS.html`)**: `fwExhausted()`(플래그, 없으면 금액 <= 0) -> 잘린 해 시리즈 null, y축 범위는 null 제외(전부 null 이면 기준선 기준 여백). 보이지 않는 3번째 시리즈가 null 해의 툴팁 자리를 잡아 「지급여력비율: 자본잠식」/「기본자본비율: 자본잠식」을 찍는다(범례·색 상자 처리). 노트 변화 칸은 잘렸으면 「—」, 안내 한 줄은 공개 시트 비고 표기(자본잠식(가용자본<=0) · 기본자본 잠식(가용 기본자본<=0)) 재사용. `fmtTriPct()` 로 노트 기준선·툴팁·y축 눈금(보조축 환산 포함) 음수 △. 도넛 툴팁 「사용: 100%+ (실제 X%)」와 「초과분은 …」를 두 줄로 분리, `tier1_pct_if_unconfirmed_tier2` 는 표시값(소수 첫째 자리)과 다를 때만 「보완자본형이면 X%」(툴팁·? 꼬리 공통). 콜 상환 도래일 칸: 잔액이 null·빈 칸·표식(원장 미갱신)인 증권도 콜일 후보로 두고 금액 없이 날짜만, 날짜 모양이 아니면 대시. 잔액 0 확정은 종전대로 후보 아님.
- **검증**: `scripts/check_kics_forward_note.py --mobile --dark`(47사 x 3뷰 141회: 노트 변화 = 자본/SCR 기준 또는 「—」, 시리즈 null, 안내 줄, ASCII 마이너스 0, 도넛 툴팁 실제 호버 폭 <= 캔버스 325, 콘솔·넘침 0) 위반 0. 같은 스크립트를 옛 판(HEAD)에 돌리면 예별 +41.8%p·0.00% 툴팁, 하나생명 329·푸본 341·농협손해 349 폭 초과를 그대로 잡는다. `scripts/check_kics_callcell.py` 합성 6변형(null·빈 칸·표식·필드 없음·날짜 표식) 통과. 시험 `tests/test_kics_forward_note.py`(JSON 계약·정적, `RUN_KICS_FORWARD=1` 이면 브라우저) + `test_deploy_assets` 12 · `test_push_gate_wiring` 66 · `test_prepush_scope` 65 · `test_share_screenshot` 7 · `check_share_screenshot.py` 통과.

## 2026-10-12 (오후) -- K-ICS 소진율 도넛·Forward Outlook 복원 (발행현황 패널은 그대로)

티켓 `inbox/designer/20261012T2035Z__orchestrator__MULTI_2026.2Q__kics_restore_utilization_donuts_and_forward.md`(공유, 고치지 않음). 데이터는 publishing 이 먼저 커밋(`ef62969`·`2729a53`·`35740b2`·`8037840`: 새 `kics_tier1_utilization.json`·`kics_tier2_utilization.json`·`kics_forward_capital.json`, 비공개 목록 비움).
- `K-ICS.html`: 제거 커밋 `e2c72cd` 의 반대로 복원. 순서 = 지급여력비율 추이 -> **자본성증권 소진율(`#donut-section-panel`)** -> 자본성증권 발행현황(`#sec-capsec`, 막대+큼직한 셀 2개 **내용·계산(타임라인 JSON 클라이언트 계산) 그대로 무이동**) -> 금리 민감도 -> 자산·부채 듀레이션 -> **자본비율 Forward Outlook(`#sec-forward`)**. 목차 칩 2개 복원(6개), 도넛·전망 CSS·메타 설명(「5년 전망」)·`updateDonutPanel`/`updateForwardPanel`/`renderDonut`/`findUtilRow`/`findForwardRow`/`forwardEmptyText`·fetch 3개·`refreshBottomPanels` 복원. `dfd899e` 라벨 작업(메모 §5: 공시·규정 표기 그대로, `0%`·`발행 없음`·`—`·`100%+`, 설명은 `?` 팝오버만, 음수 △)은 복원본에 그대로 들어 있다.
- 새 필드: 전망 차트 툴팁에만 반영 — 기본자본비율 점에 `baseline_basis_flag` 회사(하나생명·교보)는 `신종 분류 기준: x.xx%`(`basic_ratio_by_type_pct`), 미확정 증권이 있는 회사는 `미확정 신종이 보완자본형이면: x.xx%`(`basic_ratio_if_tier2_type_pct`). 소진율 쪽은 기존 처리(`type_unconfirmed`·`tier1_pct_if_unconfirmed_tier2`·`tier1_excluded_tier2_type_eok`·`no_capital_securities`·`rule`/`reason`)가 새 JSON 에서 그대로 동작. 화면 문장 추가 없음. 필드 없는 구판 JSON 이면 툴팁 줄이 안 붙는다(시뮬레이션 확인).
- `download-survey.js`: 3시트(T1·T2·FWD) 주석 해제·되돌리기 안내 삭제. `report-widget.js` `SHEETS` 에 같은 3개 복원. `tests/test_deploy_assets.py`: tier1·tier2·전망·타임라인 4개 모두 필수 fetch + 파일 존재(「fetch 금지」 단정 삭제, 느슨하게 풀지 않음). `tests/test_share_screenshot.py`: K-ICS 섹션 수 4->6. `tests/test_push_gate_wiring.py`: `LIVE_ARTIFACT_READERS` 에 루트 JSON 3개 선언 복원(forward=`validate_data_contract`, tier1·tier2=`validate_live_artifacts`) — HTML fetch 복원과 같은 커밋, 타임라인 선언은 유지.
- 검증 `scripts/shot_kics_util.py`(헤드리스 Edge, `?iq_internal=1`): 한화생명·메리츠·DB손해·하나손해·하나생명·교보·코리안리·스위스리·교보라이프플래닛·동양 x 1280px·375px·다크 + 구판 JSON 시뮬레이션(한화생명·하나생명) = 32회, 도넛 데이터셋·aria 값과 전망 선 값을 JSON 과 직접 대조(불일치 0), 콘솔 오류 0, 가로 넘침 0, 죽은 칩 0, 패널 사이 간격 16px 균일, 발행현황 막대·셀 유지. 예: 한화생명 기본자본 0%·보완자본 70.5%(71%), DB손해 기본자본 151.6%(가운데 `100%+`, 도넛 호는 100 으로 캡, 숫자 줄 17,452억원/11,510억원), 동양 보완자본 105.0%(`100%+`), 스위스리 0%·발행 없음, 교보라이프플래닛 보완자본 `—`, 하나생명 2030 기본자본비율 3.93%(툴팁 분류 기준 13.15%).
- 시험: `test_deploy_assets` 12 passed, `test_push_gate_wiring` 66 passed 1 skipped, `test_prepush_scope` 65 passed, `test_share_screenshot` 7 passed 1 skipped, `scripts/check_share_screenshot.py` OK(K-ICS 섹션 「자본비율 전망」 이미지 포함).
- 남은 것: `docs/agents/claude-agent-designer.md` §1 표의 K-ICS 행이 아직 「도넛·forward 는 화면에서 내림」으로 적혀 있다(이 티켓의 쓰기 허용 파일 밖이라 안 고침).

## 2026-10-12 -- K-ICS 소진율 도넛·Forward Outlook 제거, 자본성증권 발행현황(시점별 누적 막대) + 큼직한 셀 2개

티켓 `inbox/designer/20261012T1100Z`(라벨, 커밋 dfd899e)·`20261012T1155Z`(셀 2개)·`20261012T1220Z`(도넛·전망 제거 + 누적 막대 + 다운로드 목록 제외; 앞 두 티켓과 충돌하는 부분은 이 티켓이 우선). 공유 티켓이라 고치지 않았다.
- `K-ICS.html`: 소진율 도넛 패널(`#donut-section-panel`)과 자본비율 전망 패널(`#sec-forward`)·목차 칩·`updateDonutPanel`·`updateForwardPanel`·두 차트·관련 CSS·`kics_tier2_utilization.json`·`kics_forward_capital.json` fetch 를 걷어냈다(메타 설명의 「5년 전망」도). 새 패널 `#sec-capsec`(목차 칩 「자본성증권 발행현황」, 공유 섹션 이름 같음): 막대 = 가로 시점 · 세로 억원 · 아래 신종자본증권(`primary`)·위 후순위채(`warn`) 누적, 값 없는 시점은 막대 없음, 툴팁 시점·tier·금액(억). 그 아래 셀 2개(신종자본증권·후순위채): 가장 큰 글씨 가장 최근 발행금리 `x.xx%`, `총발행액 : x,xxx억 ('23~)`, `콜 상환 도래일 : YYYY-MM-DD (x,xxx억)` 한 건, tier 가 null 이면 가운데 `—`. 값은 tier1 회사 행 `securities_summary`(구판 JSON 이면 셀 영역 숨김), 툴팁(`?`)에 최근 발행일 · 기준일(`balance_as_of`, 없으면 `as_of`) · `콜일 추정`만.
- 막대 원천 `kics_capital_securities_timeline.json`(publishing, 증권 단위: `securities[code] = [{tier, issue_date, call_date, coupon_pct, face_eok, outstanding_eok, as_of}]`): 가로 = 발행연도(첫 해~마지막 해, 발행 없는 해 0), 세로 = 그 해 `face_eok` 합(억원), 신종자본증권 아래·후순위채 위로 쌓기(시간 누적 아님 — owner 정정), 툴팁 「YYYY년 발행」 + 두 금액. 파일이 없거나 회사 자료가 없으면 차트 영역만 숨는다. 제목 옆 `?` 는 원천 문구가 내부 경로를 담아 뺐다.
- `download-survey.js`: 기본자본소진율(T1)·보완자본소진율(T2)·자본비율전망(FWD) 3항목을 주석 처리(되돌리기 = 주석 해제, 주석에 「owner 2026-10-12 일시 비공개」), 새 시트 `보험금예실차비율`(AE) 추가. `report-widget.js` SHEETS 에서 같은 3개 제외. 파일(`public_exports`·마스터·xlsx)은 그대로.
- `tests/test_deploy_assets.py`(fetch 목록: tier1 만 필수, tier2·전망은 fetch 금지 확인, 타임라인 fetch 확인), `tests/test_share_screenshot.py`(K-ICS 섹션 수 5→4), `docs/agents/claude-agent-designer.md` §1 표.
- 검증 `scripts/shot_capsec.py`(헤드리스 Edge; 실제 타임라인 파일로 한화생명·메리츠·현대해상·스위스리 확인): 한화생명·메리츠·현대해상(후순위채만)·스위스리·삼성생명·교보라이프플래닛 x 1280px·375px·다크 — 콘솔 오류 0(구판 시뮬레이션의 404 제외), 가로 넘침 0, 큰 글씨 줄바꿈 0, 죽은 앵커·남은 도넛/전망 요소 0. 구판 tier1 JSON(요약 필드 없음) 시뮬레이션에서 셀 영역 숨김. 실제 `securities_summary` 값: 한화생명 신종 6.30%·30,819억·콜 2029-07-17(5,000억), 후순위 4.45%·12,968억·콜 2027-02-04(10,720억, 추정), 메리츠 신종 5.30%·후순위 3.70%. 삼성생명·스위스리·교보라이프플래닛은 두 tier 모두 null 이라 셀은 `—`.
- 2026-10-12 후속(커밋 1624aba·이후): 큼직한 셀 값은 `kics_tier1_utilization.json` 대신 타임라인 JSON 에서 클라이언트 계산(그 fetch 제거, 시험은 타임라인 fetch 필수·tier1/tier2/전망 fetch 금지). 이어서 owner 정정으로 2023 필터 제거: `총발행액 : x,xxx억`(접미 없음) = 그 tier 모든 증권 `face_eok` 합(차트 막대 합계와 같음), 최근 금리·콜 도래일은 잔액이 남은 증권 기준 그대로. 한화생명 신종 30,819·후순위 27,762, 메리츠 2,850·18,010, 현대해상 후순위 28,330(신종 없음 `—`)이 셀 = 막대 합계, 1280/375px 가로 넘침·콘솔 오류 0.
- 시험(실제 파일 반영 후): `test_deploy_assets` 12 passed(타임라인 파일·publishing 표가 올라와 앞서의 실패 2건 해소), `test_share_screenshot` 7 passed 1 skipped, `test_push_gate_wiring` 65 passed 1 skipped. `test_prepush_scope` 는 앞 실행에서 65 passed(이후 변경이 K-ICS.html 안뿐이라 재실행 안 함).

---

## 2026-10-12 -- IFRS17 보험금 예실차비율 별도 섹션(9) + 묶음 막대

티켓 `inbox/designer/20261012T1000Z__orchestrator__MULTI__IFRS17_claims_ae_separate_section_grouped_bar.md`(공유, 오케스트레이터가 종결). `IFRS17.html` 만(+`tests/test_share_screenshot.py` 섹션 수 9→10). 8) 손해율 가정 안의 `#lrAeBox`·`drawLrAe` 제거, 새 패널 `#sec-ae`(`data-pane="ae"`, `data-share-section="보험금 예실차비율"`)를 8 뒤에 신설하고 `9) 보험금 예실차비율`, 뒤따르던 `9) 판매채널별 유지율` 은 `10)` 으로. 목차 칩 「보험금 예실차비율」 추가(앵커 `#sec-ae`; `#sec-lr`·`#sec-ps` 불변). 번호가 쓰이는 곳은 h2·목차·시험(`test_section_markup_complete`)·designer 프롬프트 §1 표뿐이었다.

데이터는 그대로 `panel_loss_ratio.json` 최상위 `ae[code].q[분기] = [[기준연도, 사업구분, 예상손해율, 실제손해율, 보험금 예실차비율, 플래그[]]…]`(fetch, 새 파일·마스터 수정 없음). 선택 규칙 변경: 예전엔 8) 의 공시시점 select 를 따라 「이하 가장 최근 연말 공시」를 골랐는데, 새 섹션은 독립이라 자체 「공시시점」 select 를 두고 선택지를 그 회사 `ae` 의 분기(연말 공시, 현재 데이터 2025.4Q·2024.4Q)로 한다(기본 최신). `ae` 가 없는 회사·구판 패널이면 패널 전체 `hidden`(문구 없음, 목차 칩은 theme.js 가 흐리게). 차트: Chart.js 막대, 가로축 기준연도, 묶음 안 예상손해율(키컬러 30% 면 + 테두리) · 실제손해율(키컬러 실색) · 보험금 예실차비율(중립 회색 `TH.muted`), 값 없는 칸은 막대 없음, 음수 △(툴팁·축 눈금·막대 값 라벨 모두 `aeTxt`/`fmtNum`), 0 선 굵게, 값 라벨은 데스크톱만(자체 플러그인), `identity_break` 칸 툴팁 「공시 산식과 맞지 않는 값(공시 그대로)」, `role="img"` + 회사·구분·연도 범위·값 범위 `aria-label`. 사업 구분이 둘 이상이면(코리안리 공동재보험/전통형재보험) 구분마다 차트 하나, 표는 구분 블록. 모바일(≤640px)은 범례 아래, 높이 340px. 설명은 제목 옆 `?` 팝오버(`help-lrae`)만.

검증(`scripts/shot_ae.py`, 헤드리스 Edge): 삼성생명·현대해상·코리안리·스위스리아시아·예별손보·푸본현대·서울보증(ae 없음 -> 패널 hidden, 칩 흐림) x 1280px·375px — 콘솔 오류 0, 가로 넘침 0, 8) 에 예실차 문구 0, 공시시점 토글(2025.4Q/2024.4Q) 차트·표 동기, 섹션 공유 이미지(1062x768 등) 정상, 현대해상 다크 확인. 시험 `test_share_screenshot`·`test_deploy_assets`·`test_push_gate_wiring`·`test_prepush_scope` 통과.

---

## 2026-10-12 -- 모바일 섹션 공유 이미지 가로 확장 제거

티켓 `inbox/designer/20261012T1040Z__orchestrator__MULTI__mobile_section_share_image_no_widen.md`(공유, 오케스트레이터가 종결). `theme.js` `shRender`: 섹션 이미지의 `o.widen`(가로 스크롤 표의 `scrollWidth-clientWidth` 만큼 이미지·복제 섹션 폭을 늘림)을 폰(`phone = coarse || clientWidth < 520`)에서는 하지 않는다. 이미 그려진 차트 canvas 는 넓어진 폭에 다시 그려지지 않아 왼쪽 1/3 만 차지하고 오른쪽이 비던 문제(뮌헨 손해율 가정, owner 스크린샷). 데스크톱·페이지 전체 이미지 경로 불변.

실측(헤드리스 Edge, 375px·DPR2, 섹션 공유 버튼 클릭 -> PNG): 뮌헨 손해율 가정 758x1674px(CSS 폭 379), 삼성생명 NB 배수 758x1304, 코리안리 예실차 758x2404 — 전부 화면 폭 그대로, 차트가 폭을 채움, 표는 보이는 열까지. 데스크톱 1280px 뮌헨 손해율 가정은 1104px 로 widen 유지. 시험: `tests/test_share_screenshot.py::test_phone_section_image_does_not_widen`(정적) 신설, 4종(share_screenshot·deploy_assets 12·push_gate_wiring 65·prepush_scope 65) 통과.

---

## 2026-10-12 -- 공유 버튼 사용 기록(수집기 shares 탭)

티켓 `inbox/designer/20261012T0910Z__orchestrator__MULTI__share_button_usage_log_to_collector.md`(공유, 오케스트레이터가 종결). `theme.js` `shLog`: 링크 복사(`link_copy`)·페이지 전체(`page_screenshot`)·섹션(`section_screenshot`) 마다 `IQ_FORMS.submit('share', {page, action, section, company, device, result})` 1건, 개인정보 없음. 스크린샷은 완료 시점에 `ok|truncated|error`. `iq_internal=1`(쿼리) 또는 브라우저가 내부로 기억(localStorage)이면 0건, 같은 page·action·section 1.5초 내 연타는 1건, `forms-config.js` 없으면 조용히 건너뜀. `compare.html` 은 forms-config.js 를 안 불러와서 `<script src="forms-config.js">` 1줄 추가(CSP 변경 없음). `scripts/appsscript/insurequant_collector.gs`: `kind==='share'` → `shares` 탭 + 첫 share 때 `shares_summary` 탭(헤더 이름 기반 QUERY, 전체·최근 7일), 메일 없음. `privacy.html` (4) 공유 버튼 이용 기록 문단. 검증 `scripts/check_share_log.py`(수집기 요청을 route 로 가로채 본문만 캡처, 실제 전송 0).

---

## 2026-10-12 -- IFRS17 섹션 8 보험금 예실차비율 표

티켓 `inbox/designer/20261012T0410Z__orchestrator__MULTI_2025.4Q__ifrs17_sec8_claims_ae_ratio_table.md`(공유). `IFRS17.html` 만. `data/loss_ratio/panel_loss_ratio.json` 최상위 `ae[회사코드].q[공시분기]` 를 fetch 중인 기존 패널에서 읽어 `#lrAeBox`(`drawLrAe`)에 그린다. 선택한 공시시점 이하의 가장 최근 연말 공시를 쓰고, 열=기준연도, 행=예상손해율·실제손해율·보험금 예실차비율(셀에 %·%p, 소수 2자리, 음수 △, null 은 -). 사업구분이 있으면 구분 행 아래 3행씩 블록(실데이터에서는 코리안리 공동재보험/전통형재보험뿐). 정의·연 1회 공시 설명은 `?`(`help-lrae`)에만. `ae` 부재·해당 회사 없음·이전 공시 없음이면 박스 숨김. `identity_break` 플래그는 셀 title 만. 검증: `scripts/shot_lr_ae.py`(스크린샷 `artifacts/designer/lr_ae/`, gitignore) 6사×2뷰포트 콘솔 0·넘침 0, 서울보증 숨김 확인.

## 2026-10-12 -- IFRS17 통합 현황 박스·NB CSM 배수 표

티켓 `inbox/designer/20261012T0210Z__orchestrator__MULTI_2026.2Q__ifrs17_summary_box_kpis_and_nb_table.md`(공유). `IFRS17.html` 만. (1) 「IFRS17 통합 현황」 제목 패널 하나가 기준 토글·요약 4칸(`#kpi7Strip`, 템플릿 밖 정적 마크업, 회사 선택 전 숨김)을 담고, `#dashHost` 의 섹션 패널은 그 아래 형제로(커밋 46d4a3a). (2) 섹션 6 차트 아래 `#nbTable`(`buildBsTableDom` 재사용, 행 월납월초보험료·신계약 CSM·신계약 CSM 배수, 값 없음 —, 음수 △, 「미수록」 회사는 표 없음). 검증: 삼성생명 연도 2023·2024·2025·2026.2Q / 분기 5개, 라이나 신계약 CSM 2,192 = 요약 칸 값, 375px 가로 넘침 0, 콘솔 0.

## 2026-10-12 -- K-ICS 듀레이션 섹션 컬럼명·순서·주석 정리

티켓 `inbox/designer/20261012T0200Z__orchestrator__MULTI_2026.2Q__kics_dur_table_scenario_labels_order.md`(공유). `K-ICS.html` 만. `DUR_SCEN` 을 충격전·평균회귀·금리상승·금리하락·금리평탄·금리경사(공시 이름·순서)로 바꾸고 임의 이름 평탄화·경사화와 그 해설 문장을 삭제. 표 아래 「자료:」 줄, 갭 카드 아래 분모·부호 문장·비고는 보이는 글을 없애고 각각 ? 팝오버(help-dur-table, help-dur-formula)로 이동. 같은 이름을 쓰던 다른 곳은 없음(compare·index·공시보고서·JS 전수 grep 0건). 검증: 충격전 순자산 61,292=175,248−113,957, 375px 표 가로 스크롤(689/325), 콘솔 0.

## 2026-10-12 -- index 모바일 재보험·보증 그룹도 top 5 + 더보기

티켓 `inbox/designer/20261012T0010Z__orchestrator__MULTI_2026.2Q__index_mobile_re_guarantee_fold_top5.md`(공유, 종결은 오케스트레이터). `index.html` 만. `FOLDABLE`(Re 제외) 삭제, 섹터별 펼침 상태를 `listExpanded`/`bubbleExpanded` 키 맵으로 일반화(redraw·모바일 진입·섹터 필터 변경 시 `{}` 로 초기화). 점검 375px: K-ICS 리스트 생보 `더보기 (17개사)`·손보 `(11개사)`·재보험·보증 `(4개사)` 3개, 재보험 버튼 클릭 시 `접기` 로 바뀜, 콘솔 오류 0, 가로 스크롤 0. CSM 버블 리스트는 같은 코드 경로를 쓰지만 현재 데이터에 신계약CSM배수가 있는 재보험·보증사가 없어 그 그룹 자체가 안 뜸(생보 17·손보 9 버튼 정상).

## 2026-10-12 -- index 홈 KPI 「업계 총 기말 CSM」 부가 문구·팝오버 제거

티켓 `inbox/designer/20261012T0000Z__orchestrator__MULTI_2026.2Q__index_csm_kpi_remove_sub_text.md`(공유, 종결은 오케스트레이터). `index.html` 만, 마스터 무수정. 카드의 `kpiCsmSub`·`kpiCsmHelp`·`help-kpi-csm` 마크업, `updateCsmKpi` 의 문구·팝오버 코드, 미사용 `.kpi-sub` CSS 2줄 삭제(합산·모집단·폴백 로직 불변, `iq-help` 공통 스타일 불변). 점검: 데스크톱 4칸 높이 83px 동일, 모바일 375px 2x2 68px 동일·가로 스크롤 없음, 값 142조(rAF 대체 후 확인), 콘솔 오류 0, test_deploy_assets·push_gate_wiring·prepush_scope 142 passed.

## 2026-10-11 -- 재보사 7곳 PL 항목 4 라벨 「원수」 제거 + 패널 렌더 점검

티켓 `inbox/designer/20261011T2010Z__orchestrator__KR1101-KR1107__reinsurer_csm_amort_label_and_panel3.md`(공유 티켓, 종결은 오케스트레이터). `IFRS17.html` 만, 마스터 무수정, push 안 함.

- **라벨**: 전업 재보험사 7곳(뮌헨·스위스리아시아·제네럴·하노버·알지에이·스코리·퍼시픽라이프리)의 보험손익 구성 head 를 「원수 CSM상각 · 원수 위험조정 · 원수 예실차 · 기타 원수손익」 → 「CSM 상각 · 위험조정 · 예실차 · 기타 손익」. 매핑 = `PL_RE_ONLY`(회사코드 집합)·`PL_RE_LABEL`(라벨·x축 줄바꿈)·`PL_STEP_DEFS_RE`, `plStepDefsFor` 가 코드로 골라 쓴다 — 막대·툴팁·표 행·캡션 계정 흐름은 모두 이 def 의 이름에서 나오므로 한 곳. 마스터 항목명(`원수CSM상각` 등)은 불변. 같은 회사의 제목 부제 「(장기원수 세부 분해)」→「(보험손익 세부 분해)」와 차트 aria-label 도 「장기원수」를 뗐다. 코리안리(KR1000)는 수재/출재 LOB 축이라 그대로, 라이나(KR0074)는 원수사라 그대로(「원수 CSM상각」 유지) — 헤드리스로 확인.
- **렌더 점검(헤드리스 Edge, `scripts/shot_pl_panel3.py`, `?iq_internal=1`, 데스크톱 1280·모바일 375, 연도·분기 기준)**: ① 항목 4 만 있는 4Q 버킷 — 최신이 반기라 화면 차트에는 안 뜨므로 요청 가로채기로 2025.4Q 까지만 남겨 시험(뮌헨·스코리·하노버·라이나): CSM 상각 막대 1개 + 나머지 head 4곳·투자손익·영업외 회색 「미공시」 + 보험손익 앵커 + 법인세 + 순이익. ② 항목 4 도 없는 중간분기(2026.2Q 당분기·2025.3Q): 회색 막대만.
  **판단 = 브리지 변경 없음**: 값이 있으면 막대, 없으면 회색 미공시라는 기존 관례가 그대로 읽히고(앵커는 0 에서 다시 시작해 누적 잔차 막대가 안 뜬다), 안내 문구로 바꾸면 보험손익·법인세·순이익은 오히려 숨는다. 투자손익·영업외(항목 17·21)가 비어 법인세 막대가 순이익과 안 맞는 건 재보사 7곳만이 아니라 PL 마스터 26사 269버킷의 공통 기존 현상(parser 가 채우면 해소) — 이번 범위 밖.
- 시험: 40조합(10사×연도/분기×데스크톱/모바일) 콘솔 오류 0·가로 넘침 0, `test_deploy_assets`+`test_push_gate_wiring` 77 통과(1 skip). 스크린샷은 `artifacts/designer/reinsurer_csm_amort/`(gitignore).

## 2026-10-11 -- index KPI 「업계 총 기말 CSM」 같은 분기 합산(142조)

티켓 `inbox/designer/20261011T1800Z__orchestrator__MULTI_2026.2Q__index_kpi_industry_csm_single_quarter.md`(공유 티켓, 종결은 오케스트레이터). `index.html` 만, 마스터·패널 JSON 무수정, push 안 함.

- **원천 교체**: `totalClosingCsmEok()`(CSM_waterfall 항목 6, 회사별 최신 분기 합 — 연 1회 공시사가 2025.4Q 에 멈춰 분기가 섞임, 라이브 139.7조·새 마스터 141.4조) → `data/csm_combo/panel_csm_combo.json` 의 `csm_gen+csm_vfa` 를 **한 분기로** 합산(`industryCsmFromPanel`). 두 열 모두 null 인 회사 제외. 패널 fetch 는 비차단(`csmPanel`), 끝나면 `updateCsmKpi()`.
- **기준 분기 규칙(코드 주석에 기록)**: `meta.quarters` 를 늦은 쪽부터 보며, 그 분기에 값이 있는 회사 수가 「패널에 값이 한 번이라도 있는 회사 수」의 80%(올림) 이상인 첫 분기. 한두 곳만 새 분기를 먼저 올려도 합이 급락해 보이지 않는다.
- **표기**: 값 아래 줄 「2026.2Q 기준 · 46사」(분기·회사 수 모두 데이터 도출) + 「?」 팝오버(경영공시 2-4 보험부채 현황표의 보험계약마진 합, 연 1회 공시사도 분기별 잔액이 있어 같은 분기로 합산). 팝오버를 라벨이 아니라 이 줄 끝에 둬서 열려도 기준 줄을 가리지 않는다. 카운트업 유지.
- **폴백**: 패널이 404·실패, 열 이름이 없음, 조건을 만족하는 분기가 없으면 옛 `totalClosingCsmEok()` 로 되돌리고 줄에 「회사별 최신 공시 분기 합」, 팝오버는 분기가 섞인다는 사실을 적는다(구판 패널 40사·8분기라 2026.2Q 가 없을 때 대비).
- **`.rise` 의 `both`→`backwards`**: 끝난 뒤에도 애니메이션이 남아 카드마다 쌓임 맥락이 생기면 「?」 팝오버가 아래 패널에 가려지는 같은 원인(common.css `.panel.revealed` 수정과 동일).
- **모집단 보정(owner 후속)**: 모집단 = 시장지도 KPI 「수록 보험사」와 같은 회사(최신 K-ICS 분기에 지급여력비율이 있는 47사, `GROUPED`)와 패널의 교집합 — 마스터에 없는 캐롯손해보험(KR1059)은 자동 제외. 기준 분기에 값이 없는 모집단 회사는 그 이전 가장 최근 값으로 대신하고 회사 수에는 넣으며(하노버재보험 2026.1Q), 이름·분기를 `?` 팝오버에 데이터에서 도출해 적는다. 결과 2026.2Q 기준 · **47사**, 142.2조(파이썬 직접 합 47사 142.22조와 일치). 80% 규칙은 값이 직접 있는 회사 기준 유지.
- **값 확인(보정 전 46사 기준)**: 실데이터 2026.2Q 46사 142.2조(표시 142조), 2026.1Q 46사 138.0조·2025.4Q 47사 133.7조(파이썬 직접 합과 일치). 헤드리스 시험: 정상(142조), 패널 404(141조 폴백), 열 누락(141조 폴백), 2026.2Q 제거(138조·2026.1Q 기준), 2026.2Q 가 1사만 있음(138조·2026.1Q 기준). 라이트·다크 × 1280·375px 가로 넘침 0, 팝오버 가려짐 0, 콘솔 오류 0.
- **다른 CSM 합계 표기**: index.html 에는 없다(버블맵·보조표는 회사별 값, 이 티켓에서 안 건드림).
- **테스트**: `test_deploy_assets`·`test_push_gate_wiring` 77 통과.

## 2026-10-11 -- IFRS17 섹션 3 모바일 단순형 재도입 · ? 팝오버 가려짐 · 시장지도 재보·보증 절반 · 상각 축 단위 · 전망 제외 사유

티켓 `inbox/designer/20261011T1530Z__orchestrator__MULTI_2023.4Q-2026.2Q__sec3_mobile_simple_again_and_help_popover_clip.md`·`20261011T1600Z__publishing__MULTI_2026.2Q__forward_exclusion_reason_and_amort_axis.md`(공유 티켓, 종결은 오케스트레이터) + 조율자 추가 지시(index). 마스터·패널 JSON·`public_exports` 무수정, push 안 함.

- **섹션 3 모바일(≤640px) 단순형**(`IFRS17.html` `hcSimpleChart`, 커밋 `da15845` 구현을 그대로 되살리지 않고 `244fd75` 이후 것은 유지): 막대 = 기말 CSM(주축, 키컬러·없으면 에메랄드), 선 = 신계약 CSM(보조축), 범례 2개. BEL·RA·PAA·발생사고요소·구성 미분리는 차트에서만 뺌(표 그대로). 데스크톱(641px 이상)은 콤보 그대로(1280·641px 범례 8개 확인). 안내 문구는 단순형에 맞게 분기(재작성 †·사이드카·구성 없음·신계약 없음 유지, 막대와 무관한 줄무늬·빗금·BEL 음수 안내는 모바일에서 생략).
- **축 폭 실측(375px, 삼성생명)**: 종전 좌 61px·우 64px(눈금 `0조`·`0.00조`, 눈금 9~10개) → 좌 34~43px·우 34~55px, 그림 영역 184→245px(연도 모드). 눈금은 숫자만, 단위는 축 제목 한 줄(조원/억원), 축마다 단위를 따로 고름(최대 ≥5천억이면 조원), 눈금 5개 이하, 소수 자릿수는 눈금 간격에서 결정. 막대 위 값 라벨이 선과 겹치면 막대 안쪽으로 비켜 앉힘. 확인: 삼성생명·라이나·미래에셋·KB라이프(재작성)·ABL·AIG(신계약 없음 포함) × 연도/분기 × 375px(414px 삼성) × 라이트/다크, 콘솔 오류 0.
- **? 팝오버 가려짐 원인**: `common.css` 의 `.panel.revealed { animation: … forwards }`. 끝난 뒤에도 애니메이션이 살아 있어 패널마다 쌓임 맥락이 생겼고, 패널 아래로 삐져나온 팝오버(z-index 1800)가 그 패널 안에 갇혀 바로 아래 패널에 가려졌다. 증상 재현: K-ICS 금리 민감도 「이 표의 기준」·듀레이션 「이 표의 기준」, IFRS17 손익 「이 표 읽는 법」(모바일). 수정: forwards 제거(끝 상태는 규칙으로 직접 지정), 팝오버 z-index 1950(우하단 고정 버튼 위, 모달 아래), 하단이 잘리면 위로 뒤집기(`theme.js` `flipHelpPop`)·뒤집을 수 없는 모바일 static 규칙은 터치일 때 살짝 스크롤. K-ICS·IFRS17·compare 전 ? 헤드리스 전수(실제 hover/탭, 삼성생명·삼성화재 × 1280·375 × 라이트·다크 × 트리거가 화면 중앙·하단) 가려짐·화면 밖 0. 키보드·Esc·터치 동작 불변.
- **index 시장지도 재보험·보증**(`6f92fb0`): `RE_MIN_SHARE` 0.18→0.07, 그룹 높이 246→122px(1280·1440 동일, 면적 약 절반). 제목의 「 · 칸 크기는 이 업권 안에서만 비교」와 `floored` 속성 삭제. 칸 이름 표시 임계(높이 46·폭 60) 때문에 이름이 보이는 칸이 9곳 중 5→2곳으로 줄고 나머지는 툴팁(호버)만 — 높이를 반으로 줄이면 불가피(0.09 로 61% 높이여도 같은 2곳).
- **상각 차트 축**(`IFRS17.html`): `csm_amort_schedule.json` 은 억원(unit 필드)인데 백만원으로 보고 100 으로 나눠 눈금이 100배 작았고 툴팁(`fmtEok`)도 같은 가정이었다(스위스리 1년차 418억원이 「4억」). 억/조(1만억 이상) 로 고치고 △ 유지. 실측: 스위스리 눈금 `0억…450억` 툴팁 `418억원`, DB생명 `590억원`, 삼성생명 `0.0조…1.2조`·`1.03조원`.
- **전망 빈 상태**(`K-ICS.html`): `row.status==='excluded'` 이면 `row.exclusion_reason` 그대로, 서울보증 이름 분기 삭제, `findForwardRow` 에 `insurer_name` 가드. 서울보증 선택 시 데이터 문구 표시 확인.
- **테스트**: `test_deploy_assets`·`test_push_gate_wiring`·`test_share_screenshot`(`RUN_SHARE_SHOT=1`) 84 통과.

## 2026-10-11 -- K-ICS 「자산·부채 듀레이션」 별도 섹션 · 시나리오별 금리부 자산·부채 표

티켓 `inbox/designer/20261011T1300Z__orchestrator__MULTI_2023.2Q-2026.2Q__kics_duration_section_scenario_tables.md`(공유 티켓, 종결은 오케스트레이터). `K-ICS.html` + 검증 2종의 기대 섹션 수만 수정. 마스터·`public_exports` 무수정, push·배포 안 함(owner 보류).

- **분리**: 금리 민감도 패널(`#sec-sens`)에서 듀레이션 카드 3장·산식 「?」·비고(`#dur-strip`·`#dur-note`)를 떼어 **`#sec-dur` 「자산·부채 듀레이션」** 패널로 옮겼다. 위치는 금리 민감도 바로 아래·자본비율 전망 위, `data-share-section="자산·부채 듀레이션"`, 목차 5번째 항목. 금리 민감도 제목 부제의 「· 자산/부채 듀레이션 갭」 삭제, `sensHideAll`·`renderSensDetailInner` 의 듀레이션 호출 제거(민감도 패널은 차트·KPI·표만).
- **분기 선택은 자체 select**(`#dur-quarter`, 제목 옆에 「(2026.2Q 기준)」 표기): 듀레이션 마스터가 2023.2Q 부터 7개 분기, 금리 민감도(반기 공시)는 2024.4Q 부터라 같은 select 를 따르면 앞쪽 분기가 가려진다. 기본값은 해당 회사의 최신 분기라 둘 다 보통 2026.2Q. 같은 회사 재진입(데이터 늦게 도착·테마 전환)이면 고른 분기 유지.
- **시나리오 표**(`#dur-table`, 카드 바로 아래): 열 충격전·금리상승·금리하락·평탄화(`금리평탄`)·경사화(`금리경사`)·평균회귀, 행 금리부자산·금리부부채·순자산(굵게·위 2px 선). 칸 = 윗줄 금액, 아랫줄 충격전 대비 변화(금액)와 변화율(충격전 열은 「기준」). 화면에서 하는 계산은 순자산(자산−부채)·변화(시나리오−충격전)·변화율(변화÷충격전)뿐이고 표 아래 각주 + 「?」 에 밝혔다. 충격전이 0 이하이면 변화율을 뺀다(RGA 금리부자산·부채). 소수 자리는 표 안 최대 절댓값으로 정한다(≥1,000억 0자리, ≥10억 1자리, 그 밖 2자리 — 카카오페이·마이브라운이 0 으로 뭉개지지 않게). 음수 △, 양의 변화는 `+`.
- **단위(티켓 전제 정정)**: 티켓은 「원자료 백만원×0.01=억원」 이라 했지만 `kics_duration_gap.json` 의 `자산_*`·`부채_*` 는 **이미 억원**이다(`build_kics_duration_gap.py` 헤더 「단위 억원」, 비전 금 칸을 `/100.0` 해서 적재). 삼성생명 2026.2Q 충격전 자산 2,600,437.85 − 부채 2,443,521.53 = 156,916.32 = `kics_disclosure.json` 항목 41 순자산가치 156,916.32. 그래서 화면에서 환산하지 않고 라벨만 「억원」(다른 패널 단위와 동일). 곱했다면 100분의 1로 틀렸을 것.
- **빈 값·예외**: 듀레이션이 비는 칸(`비고` 「금리부부채 ≤ 0」·「금리부자산 ≤ 0」)은 카드 값 「—」 + 「정의 안 됨」, 이유는 카드 아래 「비고: …」 한 줄(`durEsc` 로 이스케이프). 갭이 유효한데 부채 듀레이션만 빈 경우(34행)는 갭 카드는 값 유지. 알지에이리인슈어런스처럼 갭이 전부 비어도 시나리오 표는 그대로 나온다(이전엔 갭이 없으면 카드가 통째로 숨었다). 해당 회사 행이 없으면 「…공시가 아직 없습니다」, 데이터 도착 전엔 「불러오는 중」 — 빈 패널·`Nan` 없음. 재보사 8곳 모두 행이 있어 같은 표가 나온다(코리안리 5.46/2.85/3.69년 확인).
- **접근성·모바일**: 표 `caption`(sr-only)·`scope`(열 `col`·행 `row`), 가로 스크롤 영역에 `tabindex=0 role=region aria-label`(키보드 스크롤), 첫 열 고정은 `.table-container` 공용 규칙. ≤640px 도 같은 구성(카드는 기존대로 1열 적층, 표는 가로 스크롤). 긴 설명은 「?」 2개(산식·표 기준). 회사코드 노출 없음.
- **검증**: 헤드리스 Chromium(`scratchpad/verify_dur.py`·`verify_dur2.py`, 로컬 서버·공용 Browser pane 미사용) — 삼성생명·코리안리·알지에이리·카카오페이손해·마이브라운 × 480·768·1280 × 라이트·다크 25조합, 콘솔 오류 0·문서 가로 넘침 0(표만 480·768 에서 내부 스크롤), 분기 전환(삼성 2023.2Q 3,192,851/2,657,204)·회사 전환(최신 분기 복귀)·테마 전환(고른 분기 유지)·`#sec-dur` 딥링크 착지 확인. 목차 5항목(`is-na` 는 보험사 미선택 때만).
- **테스트**: `tests/test_share_screenshot.py` 와 `scripts/check_share_screenshot.py` 의 K-ICS 기대 섹션 수 4→5(`data-share-section` 패널 수 = 목차 수 대조). `test_deploy_assets`·`test_push_gate_wiring`·`test_share_screenshot` 83 통과·2 skip, `RUN_SHARE_SHOT=1` 7 통과, `check_share_screenshot.py --dark` 통과(K-ICS 섹션 이미지 「K-ICS · 자산·부채 듀레이션 · 삼성생명」, 좁은 화면은 표 폭만큼 이미지 확대).
## 2026-10-11 -- 다운로드 목록 시트 3개 추가 · K-ICS 자본비율 전망 빈 상태 문구 정정

티켓 `inbox/designer/20261011T0830Z__orchestrator__MULTI__download_list_ilp_and_kics_text.md`(공유 티켓, 종결은 오케스트레이터). 마스터·`public_exports` 무수정, push 안 함.

- **`download-survey.js` `SHEETS` 12 → 15개**: `보험계약부채`(code `ILP`, 「보험계약부채 (잔여보장·발생사고요소)」) + `자본성증권발행현황`(`CAPSEC`, 「자본성증권 발행현황 (증권별)」) + `금리듀레이션갭`(`DGAP`, 「K-ICS 금리 듀레이션 갭」). 순서는 `export_public_sheets.MASTERS` 와 같다. `code` 는 파일명에만 들어가 화면엔 안 보인다(기존 `T1`·`FWD` 와 같은 관행).
- **판단 근거(후자 둘)**: 둘 다 `public_exports/manifest.json` 에 있고 `export_public_sheets.MASTERS` 에 등재돼 `validate_live_artifacts` 의 공개 시트 검사를 통과한다. 목록에서만 빠졌고 제외했다는 기록·사유가 어디에도 없다(`git log -S` 로 `download-survey.js` 이력도 없음) -> 의도된 비공개가 아니라 누락으로 보고 넣었다.
- **`K-ICS.html` 전망 패널 빈 상태**: 「forward simulation 데이터 없음 (19사 cohort 외)」 를 `forwardEmptyText()` 로 교체. 행이 있으나 `status != ok`(현재 0건) = 「지급여력 공시 값이 부족」, 행이 없는 서울보증 = 「보험료배분접근법(PAA)만 적용하는 보증보험이라 제외 + 자본성증권 소진율은 위 패널」, 그 밖 = 「전망 대상이 아닙니다」. 문구에 회사 수를 박지 않는다. 옛 `status=…` 내부 필드 노출도 사라졌다.
- **서울보증 이유는 티켓 추정과 다르다**: 「자본성증권 발행 없음」 이 아니다. `kics_forward_capital.json` 46행 중 신종·후순위 잔액이 0인 회사가 19곳(삼성화재·삼성생명·재보사 7곳 등) 나온다. 서울보증 행이 없는 이유는 `scripts/forward_capital_simulation.py` `EXCLUDE_PAA = {"KR0150"}`(PAA 적용 회사 의도 제외)다. 자본성증권 소진율 도넛은 서울보증도 정상(기본자본 0 / 한도 2,152억, 보완자본 43 / 7,173억).
- **남은 약점**: 서울보증 분기가 이름(`includes('서울보증')`) 기반이다. 제외 사유를 데이터가 말하게 하려면 publishing 이 전망 파일에 제외 행(`status` + 사유 문구)을 넣어야 한다(데이터 변경이라 이번엔 안 함). 부수 발견: `findForwardRow` 의 부분일치가 `insurer_name` 없는 stub 행(`missing_kics_baseline`)에서 터진다 — 현재 데이터엔 stub 이 없어 무증상.
- **검증**: 헤드리스 Chromium(`scratchpad/verify_dl.py`·`verify_kics.py`, 로컬 서버, 수집기·GA 요청 차단) — 4페이지×1280·375 모두 라벨 15개, 잘림·겹침·가로 넘침 0, 콘솔 오류 0(차단한 GA 요청 제외). 새 3시트+K-ICS 선택 다운로드 xlsx: 요약·K-ICS공시 29,890행·자본성증권발행현황 124행·금리듀레이션갭 317행·보험계약부채 6,112행(헤더 포함, 스냅샷 123·316·6,111과 일치). K-ICS 회사 전환: 서울보증 = 새 문구, 삼성화재·뮌헨재보험·코리안리 = 차트. `tests/test_deploy_assets.py` + `tests/test_push_gate_wiring.py` 77 통과·1 skip.

## 2026-10-11 -- 공유 스크린샷: 헤더 메뉴 페이지 전체 복구 · 섹션별 공유 버튼

티켓 `inbox/designer/20261011T0400Z__orchestrator__MULTI_2026.2Q__share_screenshot_fullpage_and_per_section.md`. 마스터·패널 JSON 무수정, 커밋·push 안 함.

- **회귀 원인**: `1082fd1`(2026-10-08) 사별 비교 전용 공유는 `.container` 전체를 찍었다. 같은 날 `8c997cb` 가 공유 메뉴를 theme.js 공통으로 올리며 「본문 `scrollHeight <= 6000` 이면 전체, 아니면 현재 화면(`opt.x/y/width/height = scroll·inner`)」 분기를 넣었다(긴 페이지 캔버스 한도 걱정). 삼성생명 기준 실측으로 IFRS17 은 데스크톱 6,355px·모바일 6,084px 로 임계값을 넘어 늘 현재 화면만 찍혔고(K-ICS 3.4~3.5천 px·compare 2~3.5천 px 는 아직 아래였지만 표를 펼치거나 지표 카드를 늘리면 같은 길로 빠진다), 임계값 위 페이지는 구조적으로 전체가 불가능했다. 이미지를 실제로 만들어 보는 검사가 없어 이틀 뒤 owner 가 눈으로 잡았다.
- **전체 캡처(theme.js `shRender`/`shPlan`)**: 본문(`.section-body`→`.container`)을 한 장으로. 임계값 분기 폐기. 만들기 전에 높이를 재서 scale 을 `min(2, dpr, 한 변 16,000/높이, √(면적한도/(폭×높이)))` 로 낮춘다(면적 한도: 터치 1,600만 px = iOS Safari, 그 외 6,400만 px). scale 하한 0.75 밑이면(약 2.1만 css px 초과) 위쪽만 담고 이미지에 「페이지가 매우 길어 위쪽 일부만」 문구·토스트. 이어 붙이기(여러 장 공유)는 제안만. 합성 14,000px(→ scale 1.13, 높이 16,000)·40,000px(→ scale 0.75, 잘림 표시, 높이 15,999) 실측.
- 제목(페이지 · 섹션 · 회사)을 위에, 출처(`InsureQuant · www.insurequant.com/경로 · 날짜` / `자료: 푸터 문구 · 회사 · 최신 공시 분기` / 가공 값 고지)를 아래에 캔버스로 직접 그린다(좁은 화면은 짧은 형식, 폭에 맞춰 줄바꿈). 섹션 네비는 지우지 않고 숨긴다(지우면 격자 첫 칸을 본문이 차지). 고정 헤더·플로팅 버튼·공유 메뉴·오류 제보 버튼은 제외, `.sr-only` 숨김 select 가 흰 덩어리로 찍히던 것 제거, 다크/라이트 현재 테마 유지, 기존 애니메이션 동결·글꼴 대기 유지.
- **섹션별 공유**: 마크업 `data-share-section="이름"` 만 달면 theme.js `mountSectionShare` 가 제목 뒤에 우상단 버튼(아이콘 18px·타깃 44px·`aria-label` 「이 섹션 스크린샷 공유」·제목 오른쪽 44px 비움)을 붙인다. 렌더 후 새로 생기는 섹션(IFRS17 템플릿, compare 카드 재그리기)은 기존 MutationObserver 가 60ms 뒤 마운트. 좁은 화면에서 가로 스크롤되는 표는 섹션 이미지에서만 그 폭만큼 이미지를 넓혀 열이 잘리지 않게 했다(페이지 전체 이미지는 폰 폭 유지). 보험사 미선택(K-ICS)이면 「보험사를 먼저 선택해 주세요」.
- 버튼을 단 섹션: K-ICS 4(지급여력비율 추이·자본성증권 소진율·금리 민감도·자본비율 전망) · IFRS17 9(1~9, 통합 현황·KPI 띠는 섹션이 아니라 제외) · 사별 비교 지표 카드 전부(`renderCards` 의 `article.card`). compare 의 `IQShareConfig` 는 `.section-body` + 대상 회사(`context`)로 정리(has-section-nav 클래스 제거 꼼수 삭제).
- 검증: `scripts/check_share_screenshot.py`(Playwright, 1280·375 × 라이트·다크, 페이지 3종 전체+섹션 3~4곳+실제 메뉴·버튼 클릭 다운로드+캔버스 한도) 통과, 이미지는 `artifacts/designer/share_shots_20261011/`. 회귀 `tests/test_share_screenshot.py`. `test_deploy_assets`·`test_push_gate_wiring`·`validate_deployed_js` 통과.

---

## 2026-10-11 -- IFRS17 섹션 3: 모바일도 데스크톱 콤보 그대로 · 긴 설명 「?」 · 이름 「보험계약부채 시계열」

티켓 `inbox/designer/20261011T0350Z__orchestrator__MULTI_2023.4Q-2026.2Q__ifrs17_sec3_mobile_same_as_desktop_rename.md`. IFRS17.html 만(마스터·패널 JSON 무수정, 커밋·push 안 함).

- **되돌린 것(직전 모바일 단순형)**: `hcSimpleChart()` 함수 통째, `simple` 분기(차트 생성·aria-label·안내문 `!simple` 조건 6곳·구성 없는 연말 모바일 문구), 표 캡션의 `fl.simple` 분기, 모바일 높이 300px CSS. `KEY_COLORS`→`IQTheme.keyColors`(theme.js) 변경은 유지(통째 checkout 안 함, 손으로 제거).
- **모바일(≤640px, `matchMedia`)도 같은 묶음 누적 콤보**: 같은 `new Chart` 한 벌에서 크기만 다르게(`mo()`) — 컨테이너를 패널 가장자리까지(`margin:-14px`, 좌우 테두리 제거)·높이 420px(기존 360), 범례 위 가로·9px·박스 8px(8항목 2~3줄), x 라벨 회전 0·10px·분기 모드 `25.2Q`(연도 모드 `2023`·`2026.2Q`)·x 축 제목 숨김, y·y1 축 제목 10px(y1 은 「신계약 CSM (조원)」), 제목 13px 두 줄(「보험계약부채 시계열 · 회사」/기준). `mob` 은 `innerWidth<640` → `matchMedia(≤640)` 로 통일(CSS·재렌더 리스너와 같은 기준).
- **긴 설명은 두 환경 모두 한 줄 + 「?」**(`hcHelp()`, common.css `.iq-help`, JS 추가 파일 없음): 차트 위 줄은 「연도 기준(각 연말 + 최신 분기) · 음수 △」, 차트 아래 줄(`#histComboNote`)은 이 회사에 해당하는 경고만 짧게(모바일 약 19자·데스크톱 약 70자까지, 넘으면 「외 N건」, 시점 3개 이상은 「N개 시점」) 없으면 「막대·축 읽는 법」, 전문(옛 안내문 전부 + 옛 위 줄 문구)은 그 「?」 팝오버 문단으로 이동. 표 위 캡션은 「값(억원) · 음수 △ ?」(전문·상계 차이 설명은 팝오버), 재작성 3사는 「† 소급재작성 비교 기준 ?」 한 줄 유지(「2023」 리터럴 대신 열 라벨에서 도출).
- **IFRS17.html 다른 캡션**(375px·1280px, 39사×연도·분기 78조합 실측): 4줄 이상은 섹션 7 가정민감도 공시 각주(최대 8줄)뿐이었고, `foldCap()` 으로 110자 초과 DART 원문 설명(섹션 4 `#amortCap`·섹션 7 각주/헤더)을 「공시 원문 설명|각주 ?」 + 팝오버로 접음. 접은 뒤 모바일 최대 3줄·데스크톱 최대 2줄. 이미 「?」 가 있던 섹션 1·5·7 헤더·8·9 는 그대로.
- **이름 변경(보이는 문구)**: 섹션 제목 `3) 보험계약부채 시계열 (…)`, 섹션 내비 항목(`.section-nav`, 375px 에서도 같은 라벨), 차트 제목(데스크톱·모바일), 캔버스 정적 `aria-label`·동적 `aria-label`(콤보·옛 폴백), 옛 폴백 선 차트 제목(「… · CSM 기준」)·`aria-label`. 코드 식별자·앵커(`#sec-hist`·`canvasHist*`·`histCombo`)는 불변. `공시보고서.html`·`index.html`·`compare.html`·`K-ICS.html`·`theme.js`·`report-widget.js` 에는 해당 문구 없음. 「신계약 CSM 시계열」(범례·안내)은 다른 개념이라 유지(`tests/regression_dashboards.py` 가 검사). 「CSM 증감」 잔존 0.
- **검증**: 데스크톱 차트(라벨·데이터·제목·축·범례·값 표) 시그니처 해시가 수정 전과 동일(`83c990fa`, 39사×2모드 78조합, 이름은 정규화), 1280px 78조합·375px 78조합 콘솔 오류 0·x 회전 0. 375px·1280px 라이트·다크, 연도·분기, 라이나·DB손보·KDB생명 스크린샷 확인. `tests/test_deploy_assets.py`+`tests/test_push_gate_wiring.py` 77 passed 1 skipped. `viz_build_csm_combo_panel.py --check` 는 FAIL(패널≠신규 빌드): 다른 세션이 `insurance_liability_portfolio.json`·`data/_derived/ilp_*` 사이드카를 수정 중인 입력 변화이고 이 변경과 무관.

## 2026-10-11 -- 사별 비교: 모바일 손해율 curve 재정비 · 손익 연 누계(YTD) 전환 · 테스트 선언 보정

티켓 `inbox/designer/20261011T0300Z__orchestrator__MULTI_2025.4Q-2026.2Q__compare_mobile_curve_restyle_and_ytd_pl.md`.

- **모바일 curve**: SVG 오른쪽 라벨 여백(96px)·선 끝 라벨 삭제 -> 카드 폭 100%, 선은 전부 실선(3px), 회사 구분은 색만. 눈금 숫자는 선 위에 얹고 배경색 테두리(paint-order)로 가림 방지. 업계 중앙값 회색 점선·표(색 견본=선 색) 유지.
- **색 규칙**(`compare.html` `assignLineColors`/`lineColors`, 데스크톱 Chart.js·모바일 SVG·표 견본 공통): 회사 키컬러(`theme.js` `IQTheme.keyColors`, IFRS17.html 의 맵을 이관 — IFRS17 동작 동일) 우선. 배경과 대비 3:1 미만이면 색상·채도 유지하고 밝기만 이동(라이트 `#ffffff`·다크 `#151615`). 키컬러가 없거나 먼저 고른 회사 색과 CIEDE2000 20 미만(라이트·다크 중 작은 쪽)이면 파스텔 팔레트(틸·살몬·블루·머스터드)에서 안 겹치는 첫 색. 키컬러 회사끼리 비슷하면 먼저 고른 회사가 키컬러를 지킨다. 배정은 테마와 무관, 표시 색만 테마별.
- **YTD**: `viz_build_compare_panel.py` 의 보험손익·당기순이익·투자손익을 PL `값`(연 누계)으로(`값_당분기`·누계 차분 폐기). 카드 제목 「… · 연 누계」, 정의·도움말에 YTD 명시, 최신 공시 줄에 기간(상반기(1~2Q) 누계 등), 오래된 값 분기 칩 툴팁에 기간. 값이 생긴 칸 +11/+2/+56(차분이 불가능했던 칸). ROE 값 불변(입력이 이미 YTD, 1Q×4·2Q×2·3Q×4/3·4Q×1).
- **테스트**: `tests/test_push_gate_wiring.py` — `LIVE_ARTIFACT_READERS` 에 `data/company_segment.json`(읽는 쪽 `viz_build_compare_panel`), `NOT_A_MASTER`(분류표)·`MASTER_SHEET_PENDING`(`insurance_liability_portfolio.json`, 시트 없음 — 시트가 생기면 선언 삭제를 강제하는 검사 포함).

## 2026-10-11 -- IFRS17 섹션 3 모바일 단순형 (CSM 막대 + 신계약 CSM 선)

> **철회됨**: 같은 날 owner 지시로 되돌렸다(위 「모바일도 데스크톱 콤보 그대로」 항목). 아래는 당시 기록.

티켓 `inbox/designer/20261011T0200Z__orchestrator__MULTI_2025.2Q-2026.2Q__combo_mobile_simple_csm_line.md`. IFRS17.html 만.

- `max-width:640px`(`matchMedia`)에서만 `hcSimpleChart()`: 막대=기말 CSM(r[0]+r[1], 표 CSM 행과 같은 값, 주축 0 시작, 회사 키컬러·없으면 에메랄드), 꺾은선=신계약 CSM(`y1`, 연도=누계·분기=당분기). 범례 2개(`CSM 잔액 (좌)`·`신계약 CSM (우)`), 제목 「CSM 잔액 · 신계약 CSM (조원|억원)」 1줄, x축 `26.2Q`·연도 `2023`(회전 0), 막대 위 값(꺾은선 점과 겹치면 막대 안쪽으로, 배경색 테두리). 값은 터치 툴팁에도(연도 모드 누계 푸터).
- 표 캡션(`#histTableCap`): 모바일은 「값(억원) · 음수 △ · 기준 설명 ?」 한 줄 + 팝오버(`#help-hc-cap`)에 기존 전문 이동. † 안내는 「† 소급재작성 비교 기준」으로 줄이고 사유 팝오버는 그대로. 모바일에 없는 빗금·줄무늬·구성 미분리·축 생략 안내문은 모바일에서만 제외, 구성 없는 연말 안내는 모바일 문구로 대체.
- 검증: 39사 × (연도·분기) 78조합 모바일 오류 0, 데스크톱 시그니처(라벨·데이터·제목·축·캡션·표·안내·aria) 해시가 수정 전 사본과 동일(70480515). 모바일 375px 라이트·다크·연도·분기 스크린샷 확인.

---

## 2026-10-11 -- IFRS17 섹션 3 콤보: 2-4 구성이 없는 연말(2023) 막대 채움

티켓 `inbox/designer/20261011T0000Z__orchestrator__MULTI_2023.4Q-2024.4Q__combo_backfill_2023_year_end.md`. IFRS17.html · `scripts/viz_build_csm_combo_panel.py` · `scripts/viz_build_compare_panel.py`(문구 1건). 마스터 JSON 읽기만, 커밋·push 안 함.

- 패널 행은 있는데 2-4 구성(인덱스 0~7)이 전부 비면(`noComp`, 데이터로 판정·날짜 하드코딩 없음) CSM 은 CSM_waterfall 기말 CSM(섹션 2 와 같은 값)으로 채우고, 패널에 새로 넣은 항목 14(DART 주석 부채 기준 잔여보장요소 합계)가 있으면 「그 외 잔여보장요소(구성 미분리) = 항목 14 − CSM」을 위에 쌓는다(회색). CSM 이 없으면 항목 14 전체가 미분리. BEL·RA·PAA 는 ‘—’. 패널 행 자체가 없는 시점의 「CSM 만」 처리(`csmOnly`)는 그대로.
- 표: 해당 열에만 「그 외 잔여보장요소 (미분리)」·「잔여보장요소 합계 (DART 기준)」 두 행(2-4 합계 행과 기준이 달라 한 행에 섞지 않음). `hcDiff` 는 2-4 합계가 없으면 항목 14 로 보험계약자산 상계 차이를 계산. 안내문·캡션·툴팁에 부채 기준(상계 전)이라 다른 시점 2-4 순액과 기준이 다르다고 적음.
- 빌더: 열 `lrc_dart`(인덱스 17, 항목 14) 추가, 2-4 구성이 없는 분기는 CSM 대조에서 제외(불일치 14→3건; 구성 없는 열이 「경영공시 CSM 이 다릅니다」 오표시되던 것), 2-4 합계가 없는 분기는 사이드카(kind 2)가 아니라 실공시(kind 1)로 둠. 패널 40.9→43.2KB.
- 실측: 2023.4Q 구성 없는 회사 13곳(삼성화재·DB손보·삼성생명·카카오페이 등). 연도·분기 두 모드 + 375px 확인, 콘솔 오류 0. `viz_build_csm_combo_panel.py --check` · `viz_build_compare_panel.py --check` OK, `tests/test_deploy_assets.py` + `tests/test_push_gate_wiring.py` 76 passed 1 skipped.
- 소급재작성 3셀(2023.4Q 라이나·미래에셋·KB라이프): 빌더가 사이드카 `data/_derived/ilp_restated_comparative.json` 을 읽어 그 셀의 bs20 을 재작성 BS 보험계약부채로 바꾸고 `meta.restated`(원 공시 항목 20·사유)를 패널에 넣는다(패널 44.4KB). 화면: 표 「보험계약부채 합계」 해당 칸에 †, 캡션 † 설명 + ? 팝오버(사유), 안내문·툴팁에 「원 공시 → 재작성」. 상계 차이 행은 미래에셋·KB라이프 사라지고 라이나만 23,600억(보험계약자산 상계).
- `data/compare/panel_compare.json` `loss_curve.note` 의 「범례 옆 숫자」를 「숫자로 적었습니다」로(변경 1건, 숫자 불변).

## 2026-10-11 -- 사별 비교 모바일 손해율 가정 curve 카드 실제 반영(안 A, owner 수정 반영)

티켓 `inbox/designer/20261010T1840Z__orchestrator__MULTI_2024.4Q-2025.4Q__compare_mobile_loss_curve_ship_optionA.md`. compare.html 만 변경(마스터·패널 JSON 읽기만, 커밋·push 안 함).

- 모바일(641px 미만, `!WIDE.matches`): 손해율 가정 카드가 막대 대신 `lossMobile()` — 한 차트(SVG)에 선택 회사 곡선 겹침, 점 표식·x 눈금 숫자 없음, 선 끝 회사명+끝값 직접 라벨(겹치면 27px 간격으로 밀어냄), 세로 눈금 2~4개(100% 선 굵게), 같은 유형 업계 중앙값 점선, 아래에 「회사 · 현재가치」 표(중앙값 행 포함, 선이 없는 회사는 색 표시만 비움·값은 그대로, 오래된 공시는 분기 칩). 제목·정의·`?` 도움말·가이드 이름은 데스크톱 curve 와 같은 `loss_curve` 값을 쓴다(`curveOn()`·`unitName()`).
- 뺀 것(owner): 「짚은 시점」 열, 터치·드래그 세로 가이드선과 값 표시, 터치를 설명하는 안내 문장. 정적 차트라 포인터 핸들러 없음.
- 색: 데스크톱 curve 가 회사 키컬러가 아니라 선택 순서 팔레트 `PAL_LINE`(틸·살몬·블루·머스터드)이므로 티켓의 「데스크톱이 다르면 데스크톱을 따른다」에 따라 모바일도 `PAL_LINE[선택 순서]`. 선 모양 `MOB_DASH`(실선·파선·점선·일점쇄선)로 색 외 구분, 표에도 같은 모양 견본. 보라 없음. 목업 전용 `--l0~3` 색은 쓰지 않음.
- 상한: `MOB_LINES=4` 곳까지 선, 더 많으면 나머지는 표에만 두고 「모바일에서는 4곳까지 겹쳐 봅니다」 안내. 현재 `MAXC=4` 라 선택으로는 안 걸린다(상수를 3 으로 낮춘 임시 사본에서 4번째 회사가 표에만 남고 안내가 뜨는 것 확인 후 사본 삭제). 업계 중앙값 점선은 이 상한 밖.
- 접근성: SVG `role=img`+요약 `aria-label`(회사별 시작→끝 값·중앙값·표 안내), 표 `caption`(sr-only)·`th scope=col`, 음수 △ 헬퍼(`nfs`), 하드코딩 분기 없음(`Q[asof]`). 라이트 배경 선 대비 2.1~2.6:1 은 데스크톱과 같은 팔레트의 기존 한계라 owner 확인 큐에 올림(TODO).
- 확인(로컬 서버 `?iq_internal=1`, 임시 서버는 종료·포트 닫힘): 375px 라이트 곡선이 다른 조합(메리츠화재·삼성화재·하나손보·신한EZ손해), 375px 다크 비슷한 조합(한화생명·삼성생명·교보생명·신한라이프), 미래에셋생명(1~10년 한 구간)·IBK연금보험(n/a)·교보라이프플래닛(8자 이름), 코리안리+서울보증(중앙값 없음), 가로 넘침 0(scrollWidth 375), 콘솔 오류 0, 모바일 다른 카드 막대 그대로, 데스크톱 Chart.js 그대로(1280 캡처), 데스크톱→모바일 폭 전환 시 재렌더. `tests/test_deploy_assets.py`+`tests/test_push_gate_wiring.py` 76 passed·1 skipped.
- 콘솔 404: 목업 페이지에 `<link rel="icon">` 이 없어 브라우저가 `/favicon.ico` 를 요청해 생긴 것. compare.html 은 data: 아이콘이 있어 콘솔 오류가 없다(서버 로그의 favicon 404 는 브라우저 창 자체 요청이며 페이지 오류 아님).
- 스크린샷: `artifacts/designer/compare_loss_mobile_ship_diff_light_20261011.jpg`, `compare_loss_mobile_ship_sim_dark_20261011.jpg`, `compare_loss_desktop_unchanged_20261011.png`.

---

## 2026-10-10 (4차) -- IFRS17 섹션 3 콤보: 기간이 상단 「기준」을 따름 + 컨트롤 줄 제거

티켓 `inbox/designer/20261010T1500Z__orchestrator__MULTI_2023.4Q-2026.2Q__combo_period_follows_header_and_drop_controls.md`. IFRS17.html 만 변경(패널 JSON·빌더 무변경, 마스터 읽기 전용, 커밋·push 안 함).

- 기간: `hcLatestQ`(패널+CSM_waterfall 전체의 최신 분기)·`hcPeriods`. 분기=최신에서 거꾸로 연속 `WF_Q_WINDOW`(5), 연도=직전 `WF_WINDOW-1`(3)개 연말(회사에 패널 행 또는 CSM_waterfall 기말 CSM 이 있는 해만)+최신. 섹션 1·2 처럼 `#wfPeriod` 변경 시 `renderCompany` 재호출로 즉시 다시 그림. 제목 괄호·캡션·축 제목·aria-label 이 모드를 따름.
- 행: 패널에 있으면 패널 행, 없으면 CSM_waterfall 기말 CSM(item 6)만 든 「CSM 전용」 행(가짜 값·추정 없음, 표 「—」, 안내문·툴팁은 데이터 유무 기준). 신계약 CSM 선: 분기=패널 당분기 증분, 연도=CSM_waterfall 연 누계(item 2 값). 최신이 4Q 가 아니면 누계·막대가 그 분기말 시점이라는 설명을 툴팁·안내에 적음.
- 삭제: `.hist-ctrls`/`.hist-fs` CSS, 컨트롤 마크업, `HC_UI`, VFA 한 덩어리·PAA 접기 분기, 표의 VFA 세부 3행, `hcColors().vfa`. 고정 동작 = VFA 합산·PAA 쌓기·발생사고요소 막대 표시·축 생략 켜짐. `renderHistTable` 시그니처 단순화(헤더 배열 직접 전달).
- 확인(로컬 서버, `?iq_internal=1`): 삼성생명·한화생명(VFA)·삼성화재·ABL생명·KDB생명·푸본현대(사이드카)·하나손보·코리안리·AIG·악사·카카오페이손보·서울보증·IBK연금, 분기·연도 두 모드, 콘솔 오류 0, 375px 가로 넘침 없음. `viz_build_csm_combo_panel.py --check` OK, `tests/test_deploy_assets.py`+`tests/test_push_gate_wiring.py` 76 passed·1 skipped.

---

## 2026-10-10 (3차) -- IFRS17 섹션 3 콤보: 오른쪽 막대 발생사고요소 실공시값 교체

티켓 `inbox/designer/20261010T1400Z__orchestrator__MULTI_*__combo_real_lic_values.md`. 마스터 읽기 전용, 패널 JSON·빌더·IFRS17.html 만 변경(커밋·push 안 함).
- 빌더 `scripts/viz_build_csm_combo_panel.py`: `lic_estimate()` 단독 → `lic_cells()`(실공시 항목 10~13, 계산값 항목 16·17 은 있을 때만, 없으면 추정). 행 17열(+BEL·RA·미분리·계산 BEL·RA·종류). 사이드카 `ilp_includes_lic.json` 을 `meta.includes_lic` 로 구움. 항목 16·17 이름이 BEL·RA 가 아니면 중단.
  추정 신뢰 규칙: 실공시 분기에서 추정이 EST_TOL(15%) 넘게 틀린 회사는 다른 분기 추정을 그리지 않음(`meta.est_unreliable`).
- 화면: 실공시=꽉 찬 BEL·RA·미분리(미분리는 별도 옅은 회색), 계산값=같은 색 줄무늬, 추정=빗금. 툴팁·값 표(행을 출처별로 분리)·범례·안내 구분. 사이드카 3사는 오른쪽 막대 없음 + 안내 + 표 「이 중 발생사고요소」. 「보험계약자산 상계 등 차이」 행은 BS − 2-4 합 − 발생사고요소 합이 BS 0.1%·5억을 넘는 회사만(?설명). 모바일은 차트 제목 2줄·세로축 제목 단축.
- 부수 수정: 세로축 생략(~)은 실제로 10% 이상 줄여 그릴 때만(1:1 인데 "1분의 1로 줄였다" 문구가 나오던 것).
- 확인(로컬 서버, `?iq_internal=1`): 삼성생명·삼성화재·메리츠·DB손보·코리안리·AIA·AIG·라이나·교보라이프플래닛·하나생명·IBK연금·예별·ABL·KDB생명·푸본현대, 데스크톱+모바일 375, 라이트+다크, 콘솔 오류 0, 회사코드 노출 0.

## 2026-10-10 -- 재보험·보증 3분류(index·compare) + 새 재보사 8곳 점검 + IFRS17 섹션 3 콤보 차트 1차 목업

**3분류.** `data/company_segment.json`(코드→구분: 코리안리·서울보증·KR1101~1107 = 재보험·보증, 나머지는 마스터 생손보여부)을 index.html 과 `scripts/viz_build_compare_panel.py` 가 읽는다. 마스터 셀은 안 고침.
index: 트리맵(재보험·보증 칸은 합이 4% 안팎이라 최소 18% 면적 보장, 제목에 "칸 크기는 이 업권 안에서만 비교"), 모바일 목록(재보험·보증은 접기 없음), 업권 필터, KPI 모집단, 버블맵(재보 버블은 NB 배수 분모가 없어 0개 — 생기면 필터·범례가 자동 노출), 약칭.
compare: 유형 `재보·보증` 신설(같은 구분끼리만 비교, 업계 중앙값·손해율 중앙값 없음, 안내 문구). K-ICS.html: 이름 약칭, 경과조치 비적용사의 적용후 0 행 묶음은 그리지 않음. IFRS17.html·공시보고서.html·report-widget.js: 약칭만.
확인(로컬 `?iq_internal=1`, 데스크톱 1280·모바일 375): 콘솔 오류 0, 화면에 회사코드 0, K-ICS 8곳 전부 NaN·0.00% 없음, compare 재보사 선택·검색창 3그룹. 재현: `python scripts/viz_build_compare_panel.py --check`.

**IFRS17 섹션 3 콤보 이식(owner 채택, 미배포).** IFRS17.html `#sec-hist`: 묶음 누적 막대(잔여보장요소 | 발생사고요소 추정) + 보조축 신계약 CSM + 세로축 일부 생략(조각선형 변환·물결 표시, 기준선 아래 실제 눈금, 음수 비압축) + VFA 합산(기본)/한 덩어리 토글 + PAA·추정 막대·축 생략 토글(회사·다크 전환에도 유지). CSM=회사 키 컬러.
막대 아래에 값 표(억원, △): CSM·BEL·RA·PAA·잔여보장요소 합계·발생사고요소(추정)·보험계약부채(BS), VFA 한 덩어리일 때 VFA 세부 3행을 [+] 로. 패널 JSON `data/csm_combo/panel_csm_combo.json`(회사코드 키, `bs20`·`lic_basis`·`csm_mismatch` 포함) · 빌더 `--check`. 발생사고요소 추정은 빌더 `lic_estimate()` 한 곳. 패널에 없는 회사는 옛 선 차트 폴백(현재 해당 회사 0).
**사후 정정(owner, orchestrator 직접 수정).** ① 다크에서 어두운 키 컬러를 흰색과 섞어 밝히던 코드(`hcMix`)를 제거해 삼성 등이 보라빛으로 보이던 것을 고쳤다 — CSM 은 회사 키 컬러 그대로, 미등록사는 사이트 키컬러(에메랄드 `--primary`). ② 값 표 행 순서를 BEL → RA → CSM 으로(차트 쌓기는 CSM 이 맨 아래 그대로). 확인: 삼성생명 CSM `#1428A0`, 카카오페이손보 `#54b3aa`(사이트 에메랄드), 콘솔 오류 0.
owner 정정으로 「CSM 증감」 띠·증감 행·라벨은 만들지 않음. 확인: 삼성생명·카카오페이손보·AIG·코리안리·하나생명 데스크톱, AIG 375px, 콘솔 오류 0, 회사코드 0. 테스트 `test_deploy_assets`(12)·`test_push_gate_wiring`(62) 통과.

## 2026-10-08 (5차) -- 사별 비교 차트·편집·공유 + 모바일 공통 수정 (owner 직접 지시, orchestrator 가 병렬 에이전트로 진행)

**사별 비교 `compare.html`.**
- 넓은 화면(641px 이상) 유지율은 13·25·37·61회차를 x축으로 둔 파스텔 묶음 막대(회사별 색, 막대 위 숫자, 같은 유형 중앙값은 빗금)로, 손해율 가정은 경과차년을 x축으로 둔 부드러운 꺾은선(회사별 색·표식 모양, 회사마다 가장 최근 결산 공시 25.4Q, 현재가치는 범례 옆 숫자, 중앙값 점선)으로 바꿨다. 두 카드는 한 줄을 다 쓴다. 모바일(640px 이하)은 기존 가로 막대 카드 그대로다. Chart.js 4.4.0 은 IFRS17.html 과 같은 고정 버전·SRI.
- 지표 요약 표를 없앴다(차트에 숫자가 다 찍힌다). 회사 검색 목록은 열 때마다 맨 위(추천)부터 보인다.
- 헤더 우상단(테마 토글 왼쪽)에 공유 아이콘 메뉴: 링크 복사, 현재 페이지 스크린샷. 스크린샷은 html2canvas 1.4.1 을 누를 때만 SRI 로 불러온다(`scripts/compute_sri.py` 에 등재). 이미지에는 검색창·옵션·툴팁이 빠지고 출처 한 줄이 붙는다. 터치 기기는 공유 시트, 아니면 PNG 저장.
- 지표 편집(드래그앤드롭): 기본 9개 지표를 표시 중 목록으로 두고 끌어서 순서 변경, 목록 밖으로 끌어내면 빼기, 추가 지표 6개(지급여력금액·지급여력기준금액·신계약 CSM·투자손익·자본총계·자산총계, 금액이라 중앙값 없음)를 끌어넣거나 눌러서 추가. Pointer Events 라 마우스·터치 모두, 키보드(방향키·Delete·Enter)도 된다. 주소 `m=` 로 공유(기본 구성이면 생략).
- 탭 순서를 "사별 비교, K-ICS, IFRS17, 기타공시"로(6개 페이지 공통). 모바일 다운로드 버튼 글자는 "다운로드(xlsx)"(데스크탑은 그대로).

**데이터.** `scripts/viz_build_compare_panel.py` 에 `loss_curve`(경과차년별 손해율을 현재가치와 같은 방식으로 합산, 미래에셋생명은 1~10년을 한 구간으로 공시, 같은 유형 칸별 중앙값)와 추가 지표 6개(`default:false`)를 넣었다. `panel_compare.json` 97,850바이트, `--check` OK.

**index.html.** 버블맵 범례 '추정(연1회 공시)'을 기본 해제(연 1회 공시사 13곳이 겹쳐 짜부되던 것). 켜면 업권 필터·테마 전환 뒤에도 유지, 표시 건수 문구와 축 범위도 보이는 것만 센다.

**모바일 공통(theme.js·common.css·report-widget.js·각 페이지).**
- 가로 넘침 원인: 안 보이는 ? 도움말 팝오버(폭 340px)가 문서 폭을 662px 까지 넓혀 우하단 오류 제보 버튼이 화면 밖으로 밀렸다. theme.js `clampHelpPops` 가 항상 화면 안으로 밀고, 4개 페이지의 모바일 CSS 도 팝오버를 한 줄 폭으로 편다. 5~6개 페이지 × 360~414px 에서 scrollWidth = 화면 폭.
- 모바일·터치(`max-width:640px`, `pointer:coarse`)에서 scroll-snap 해제, 섹션 네비의 접기/펴기 해제. 우하단에 섹션 바로가기 햄버거 버튼과 시트(오류 제보 버튼 바로 위, 상단 가로 네비는 모바일에서 숨김). 항목은 `.section-nav` 링크 또는 `id`+`data-section-label` 요소(compare.html 의 그룹 머리).
- 다운로드 팝업 폭 제한(모바일 화면 안), 터치로 차트 바깥을 탭하면 Chart.js·ECharts 툴팁을 닫음(마우스 hover 는 그대로), K-ICS 표 첫 열 고정(민감도 표는 구분·항목 두 열).

**검증.** Playwright 스모크(데스크탑 1280·모바일 375 콘솔 에러 0, scrollWidth = 폭), `test_deploy_assets` 통과, `validate_deployed_js` RED=0. owner 가 사용 사례 검증을 직접 하기로 해서 독립 QA 에이전트는 중단했다(손해율 곡선·추가 지표 재계산 검산은 불일치 0, 반올림 차이만).
**남은 것.** 모바일 실기기 확인, 다운로드 팝업 제목의 모바일 글자, 편집 목록을 0개로 비운 상태는 새로고침하면 기본으로 돌아감(`m=none` 같은 표기 없음).
**후속(같은 날, owner).** (1) IFRS17 통합 현황 아래 "CSM 워터폴 커버리지: N개사 · 범위 · 연 누계(YTD) 기준" 문구와 `#wfPeriodLine` 삭제. (2) 공유 메뉴를 사별 비교 전용에서 사이트 공통으로: `theme.js` 가 헤더에 붙이고(`#iqShareBtn`, 일본어 jp/ 제외, 페이지가 자체 `#share-btn` 을 가지면 건너뜀) 모양은 `common.css`(`.iq-share*`, `.iq-toast`). 스크린샷은 짧은 페이지는 본문 전체, 아주 긴 페이지는 지금 화면만 찍고 아직 안 나타난 패널(`.will-reveal`)도 또렷하게 만든다. 페이지별 조정은 `window.IQShareConfig`. (3) 해약환급금준비금(IFRS17_BS 항목 5, 적립 잔액)을 사별 비교 기본 지표로 추가(ROE 다음, 기본 10개). 추가 지표는 6개 그대로.

## 2026-10-08 (4차) -- 사별 비교 `compare.html` 신규 (owner 직접 지시, orchestrator 작성)

**지시.** 회사별 비교 화면. 처음 목업(꺾은선 추이) -> "꺾은선이 난잡하다, 최신 공시 기준 막대로" -> 색·추천 문구·지표 정리 후 라이브.
**화면.** 회사 1~4곳(생보는 생보끼리, 손보는 손보끼리)을 지표별 가로 막대로 비교. 막대는 회사마다 **그 회사의 가장 최근 공시 값**이고, 지표의 최신 공시 분기(39사 전체 기준)보다 오래된 값에는 `25.4Q` 같은 칩이 붙는다.
같은 유형 업계 중앙값은 마지막 막대 + 세로 점선. 유지율 13·25·37·61회차는 한 카드(회차 4구간). 막대 색은 처음 고른 회사만 틸(`--primary`), 나머지는 중립 회색(회사 구분은 이름 라벨).
**추천.** 검색창을 누르면 맨 위 "추천": 처음 고른 회사와 같은 유형에서 기말 CSM 이 바로 위 2곳·아래 1곳(모자라면 반대쪽으로 채움, 재보험·보증 제외). **기준은 화면에 쓰지 않는다**(owner 지시) — 전체 목록은 가나다순, 숫자·칩 없음. 로직은 클라이언트 JS 라 소스에는 보인다(owner: 거기까진 안 숨겨도 됨).
**데이터.** `scripts/viz_build_compare_panel.py` 가 루트 마스터 7종(kics_disclosure·CSM_waterfall·NB_CSM_multiple·PL_breakdown·IFRS17_BS·master_persistency·master_loss_ratio)에서 `data/compare/panel_compare.json`(약 58KB) 하나를 만든다. `--check` = 다시 만든 바이트 == 디스크 파일 + 1.5MB 예산.
**제외한 것.** 지급여력금액(owner), 꺾은선 추이·기간 선택, Chart.js(막대는 HTML/CSS).
**후속(같은 날, owner).** 기본 회사 없음 — 주소에 `c=` 가 없으면 빈 상태로 시작(`default_from` 삭제)하고 첫 회사는 사람이 고른다. 목록 순서는 회사코드 순(생보 한화생명·삼성생명…, 손보 메리츠·한화손보·롯데손보…)이고, 첫 회사를 고른 뒤에도 맨 위 「추천」만 기말 CSM 기준이다.
**후속 2(같은 날, owner).** 주소에 회사코드(사내 전용)를 쓰지 않는다: `?c=농협생명,신한라이프`처럼 표시명을 쓰고, 이미 퍼진 코드 링크는 읽은 뒤 이름으로 바꿔 쓴다(JSON 을 열어 보면 코드가 보이는 건 owner 가 허용). 추천 3곳은 첫 회사 기준으로 고정 — 하나 고르면 그 회사만 목록에서 빠지고 다시 채우지 않는다. 코드 노출로 한때 라이브에서 내렸다가(`22761d1`) 이 수정과 함께 재게시했다.
**배선.** `tests/test_deploy_assets.PAGES`·`tests/test_push_gate_wiring`(`_HTML`·`LIVE_ARTIFACT_READERS`·`PANEL_DERIVED_FROM` 은 여러 마스터를 튜플로 허용하도록 `_as_tuple`)·`scripts/validate_deployed_js.PAGES`·`scripts/status_report.py`·`scripts/android_push_and_deploy.sh NEW_FILES`·`sitemap.xml`·두 agent 문서의 fetch 표·5개 페이지 탭("사별 비교").
**검증.** `test_deploy_assets`+`test_push_gate_wiring` 73 passed 1 skipped, `validate_deployed_js` RED=0(compare.html 포함), 빌더 `--check` OK. 10분 전체 훅은 owner 규칙(새 화면만 올리는 배포는 생략)대로 건너뜀.

## 2026-10-08 (3차) -- IFRS17 섹션 8·9 접이식 트리 + 손해율 곡선 (owner 직접 지시, 미커밋)

**지시.** (1) 손해율 세부표가 너무 길다 -> `Non-Par > 유배당 > 상해` 식 [+] 트리. (2) 손해율 곡선은 최대한 granular, 직선 말고 부드러운 곡선, 뒷구간(11~20년)이 1~10년과 비슷한 폭.
(3) "(해지율 가정의 근거가 되는 실적)" 은 제목 말고 작은 설명줄, 채널 세분류는 [+] 밑으로.

**빌더** `scripts/viz_build_persistency_lossratio_panels.py` (마스터는 읽기만, `--check` 신설).
- 손해율 패널: 전 칸 `-` 인 잎 행 제거(잎 2,203행 중 1,426행), 구분·상품구분 소계 행 추가(515행). 마스터에 소계 행이 없어서 **빌더가 Σ예상보험금 ÷ Σ위험보험료 × 100** 으로 계산해 JSON 에 싣는다(비율 평균 아님, 둘 다 있는 잎만 합산, 위험보험료 합 0 이면 null).
  검산: 잎 위험보험료 합 = 원문 합계 행 (전 1,397 키 허용오차 1% 내 불일치 0). 구분이 하나뿐인 회사의 소계 vs 합계 행은 172칸 중 4칸이 어긋남 = 카카오페이손보 2025.4Q(억원 단위 미세 금액의 반올림), 나머지 일치.
  패널 JSON 285,683 -> 180,325 바이트. 유지율 패널은 423,498 바이트 그대로(묶음 소계 행은 이미 있었다). 두 번 돌려 바이트 동일, `--check` 로 디스크 = 재빌드 확인.
- 행 형식: 합계=`[합계,'',합계]` / 구분=`[구분,'','']` / 상품구분=`[구분,상품,'']` / 잎=포트폴리오 있음. 화면이 이 형식으로 트리를 짠다.

**화면 (`IFRS17.html`, 섹션 8·9 외 변경 없음).**
- 공유 트리 도우미 `lrpsTree()` 하나가 두 표를 그린다. 루트 행 항상 표시, 자식은 `<button class="subtoggle lrps-tg" aria-expanded aria-controls aria-label>`. 기본 접힘, "모두 펼치기 / 모두 접기" 두 버튼.
  경로 `Non-Par > 유배당 > 상해` 는 행 `title` + 스크린리더 전용 접두(`.sr-only`)로. 버튼 24px(모바일 32px), 포커스 링 2px 실측.
  펼침 상태는 `LRPS_UI` 의 경로 Set. 회사·공시시점·사업구분을 바꾸면 비우고, **폭이 640px 를 넘나들어 페이지가 renderCompany 로 전체를 다시 그릴 때와 테마 전환 때는 유지**한다
  (이 페이지의 기존 핸들러가 전체 재렌더라서, 처음 구현은 거기서 상태가 날아갔다 -> Playwright 로 잡아 고침).
- 섹션 9: 표는 묶음 5행만(전속설계사 / GA(대리점) / 방카슈랑스 / 비대면 / 기타, "소계" 낱말 삭제), [+] 아래에 원래 채널 대/소분류. 단일 자식도 [+]. 전 칸 `-` 행·값 없는 묶음 숨김. 히트맵은 묶음·자식 모두.
  제목 "9) 판매채널별 유지율" + 바로 아래 작은 muted 줄 "해지율 가정의 근거가 되는 실적입니다." 옛 긴 제목을 인용한 곳은 `IFRS17.html` h2 한 곳뿐(aria-label·앵커·nav 에는 없었다, `git grep`).
- 섹션 8 곡선: 15칸 전부 점 + `cubicInterpolationMode:'monotone'`(점 사이 overshoot 없음, null 은 끊김). x축은 linear: PC·태블릿(641px 이상) = 경과연수 비례(1~10 -> 1..10, 5년 구간 가운데 13/18/23/28, 30년 이후 33),
  모바일(640px 이하, 상수 `LR_NARROW_MAX_PX`) = 칸 균등(x = 순번) + 60도 회전 라벨. 미래에셋 `1~10년` 은 PC 에서 5.5. 1280px 에서 연 단위 라벨은 폭이 좁아 숫자만, 5년 구간 라벨은 항상 그대로.
  섹션 9 곡선도 monotone(4점이라 어색하지 않음, 스크린샷 확인).
- 도움말 팝오버(`#help-lr`·`#help-ps`)가 모바일에서 페이지를 22px 넓히던 것을 캡션 기준 위치로 고침(기존 패널의 `#help-pl-flow`·`#help-sen-asof` 는 손대지 않음, 별건).

**테스트·문서.** `tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` 는 publishing·designer 문서 표에 패널 JSON 2개를 적어 통과.
`tests/test_push_gate_wiring.py`: `PANEL_DERIVED_FROM` 과 `LIVE_ARTIFACT_READERS` 에 두 패널 선언(읽는 검사기 = 빌더 `--check`) + 헬퍼 `_worktree_fetches()`:
죽은 선언(ghost) 검사를 "origin/main 또는 작업트리 HTML 어느 쪽도 fetch 안 함" 일 때만 걸게 했다. gap 검사(화면이 읽는데 선언 없음)는 origin/main 기준 그대로라 약해지지 않았다.
시뮬레이션: 배포 전(실제 origin/main) 2 PASS, 배포 후(origin/main = 작업트리로 가정) 2 PASS, 음성 대조 2건(없는 파일 선언 -> ghost 적발, 선언 삭제 -> gap 적발) 정상.
`--check` 는 아직 prepush 훅에 안 걸렸다 -> validation 이 `validate_live_artifacts` 에 편입 요청.

---

## 2026-10-08 (2차) -- 보조표 `#ratio-sr-table` -> 보조 목록 `#ratio-sr-list` (구글 AI 개요 오답 대응, owner 직접 지시)

**증상.** 서치콘솔 색인 생성 요청 뒤(최근 크롤링 10-08 09:58) 구글 AI 개요가 삼성화재 기본자본비율을 **282.8%**(= 지급여력비율 값)로 답하고 insurequant.com 을 출처로 달았다.
표를 넣기 전 답은 기본자본비율을 기사 값(170%대 = 2025말 170.7%)으로 썼다. 표가 읽히긴 하는데 **열이 뒤바뀐 것**으로 본다
(색인 반영 시점은 구글 쪽이라 확인할 수 없다 — 표 때문인지 옛 지도 글자 때문인지 단정하지 않는다).

**원인 후보.** 표 행 `삼성화재 | 손해보험 | 282.8% | 220.2%` 에는 열 제목이 없다. 모바일 렌더 텍스트(`body.innerText`)에서 토글 라벨 "K-ICS 지급여력비율 / 기본자본비율" 바로 뒤에
지도 글자(삼성화재 282.8%)가 이어지고 그 뒤에 표가 온다. AI 가 읽는 단위는 열이 아니라 줄·문단이라, 행만 잘리면 첫 숫자가 기본자본비율로 읽힌다.

**바뀐 것.** 표 대신 줄마다 이름·지표명·값이 같이 있는 목록(`<ul>`)으로 교체했다: `삼성화재(손해보험) 2026.2Q: K-ICS 지급여력비율 282.8%, 기본자본비율 220.2%`.
함수 `renderRatioSrList()`, 컨테이너 `#ratio-sr-list`. 값은 여전히 지도와 같은 `GROUPED`·`samoNum`, HTML 에 숫자 없음, 지도에 보이는 값만.

**검증(Playwright, GA 차단).** 목록 39줄 = GROUPED 39사, 형식 불일치 0, 지도 칸 31개가 지급여력비율 보기·기본자본비율 보기 모두 목록과 일치,
컨테이너 1×1px, 목록 유무 전체 페이지 스크린샷 바이트 동일, Googlebot UA 로 639ms 만에 생성. `tests/test_deploy_assets.py` 9 passed · 1 failed(느린 .py 파싱 1건 제외) —
실패는 다른 세션이 작업 중인 미커밋 `IFRS17.html` 의 `panel_persistency.json`·`panel_loss_ratio.json` 문서 미등재라 이 변경과 무관하다.

**남은 것.** 서치콘솔에서 재색인 요청 뒤 AI 개요가 220.2% 로 바뀌는지 관찰(보장 없음). 그래도 안 바뀌면 구글이 sr-only 글자를 덜 쓰는 것일 수 있어, 다음 수는
접힌 `<details>`(화면에 한 줄이 생김, owner 디자인 결정 필요). 정적 HTML 폴백은 "데이터 인라인 금지"와 충돌이라 별건이다.

---

## 2026-10-08 -- index 마켓맵 보조표 `#ratio-sr-table` (스크린리더·검색엔진용, 화면 변화 없음, owner 직접 지시) — 위 2차에서 목록으로 대체

**바뀐 것.** `index.html` 마켓맵 패널(`#map-list` 바로 아래)에 `<div id="ratio-sr-table" class="sr-only">` 를 두고, `renderRatioSrTable()` 이 회사별
**지급여력비율·기본자본비율**을 표(`<caption>`·`<th scope>`)로 채운다. 마켓맵은 두 비율을 토글로 하나씩만 보여 줘서 기본자본비율은 토글을 눌러야만 글자로 나왔다 —
검색엔진·스크린리더는 토글을 안 누른다. 데이터 로드 `.then` 끝에서 try/catch 로 호출한다(아래 `.catch` 가 지도 전체를 비우므로 보조표 오류가 새면 안 된다).

**왜.** owner 가 "구글에서 삼성 기본자본비율을 검색하면 InsureQuant 가 걸리게" 를 원했고 숨은 글자(흰 글씨·0.1pt)를 제안했다. 그건 구글 스팸 정책 "hidden text" 위반이라
기각하고, 정책이 허용 예로 든 "스크린 리더 전용 텍스트"(차트 대체 텍스트, WCAG 1.1.1)로 같은 효과를 낸다. **지도에 보이는 값만 넣는다 — 키워드를 따로 얹으면 위반이다.**

**데이터 규칙.** HTML 에 숫자를 적지 않는다 — 지도와 같은 `GROUPED`(최신 분기, 경과조치 적용 후 우선)·같은 `samoNum`(음수 △) 으로 JS 가 채워 값이 항상 일치한다. "데이터 HTML 인라인 금지" 유지.

**검증(Playwright, GA 차단).** 39사 행, 데스크톱·모바일 모두 컨테이너 1×1px 로 잘림, 보조표 유무 전체 페이지 스크린샷 픽셀 동일·스크롤 크기 동일,
지도 글자(지급여력비율 29개 / 토글 후 기본자본비율 29개)가 표 해당 열의 부분집합. `tests/test_deploy_assets.py` 10 passed(느린 .py 파싱 1건 제외).
정정: 마켓맵은 캔버스가 아니라 DOM(`div`)이라 지급여력비율은 이미 글자였다 — 빠져 있던 것은 기본자본비율(토글 뒤)이었다.

---

## 2026-10-07 -- og:image 링크 미리보기 카드 + 루트 5개 페이지 meta (owner 직접 지시)

**바뀐 것.** `og-image.png`(1200×630, 62KB)를 루트에 추가하고 `index.html`·`K-ICS.html`·`IFRS17.html`·`공시보고서.html`·`privacy.html` 의 `<head>` 에
`og:image`·`og:image:width/height/alt`·`twitter:card=summary_large_image` 를 넣었다. 카톡·팀즈·링크드인에 링크를 붙이면 글자만 뜨던 것이 카드로 뜬다.

**왜.** GA4 주간 활성 26명 · 방명록 29건 실측으로 병목이 제품이 아니라 노출이라고 판단했다. 루트 5개 페이지에 `og:image` 가 0건이었다(2026-10-07 실측).

**디자인.** 팔레트 B(무채색 + 딥 틸 한 점) 그대로. 왼쪽 헤드라인, 오른쪽에 장식용 트리맵(생명/손해 두 묶음, 초록 계열 + 빨간 칸 하나)과 버블맵.
숫자·회사명이 없어 분기가 바뀌어도 낡지 않는다. 원본은 `docs/og-image.src.html`, 재생성은 Edge 헤드리스:
`msedge --headless=new --window-size=1200,630 --force-device-scale-factor=1 --screenshot=og-image.png file:///…/docs/og-image.src.html`.

**배선.** `og-image.png` 는 `og:image` 메타만 가리켜 keep-list grep 으로 도출되지 않는다 → `tests/test_deploy_assets.py::ALWAYS_KEEP`·`docs/launch_runbook.md`·
`docs/agents/claude-agent-publishing.md` 에 등재(테스트가 존재와 문서 등재를 강제). `tests/test_deploy_assets.py` 11 passed.

**배포.** owner 가 "designer 말고 직접 라이브 push" 로 지시해 orchestrator 가 작성하고 main 에 격리 워크트리로 올렸다(HTML 5 + PNG 1만). 라이브 커밋은 `git log origin/main -- og-image.png`.
카카오는 미리보기를 캐시하므로 이미 공유된 링크는 한동안 옛 모양이다.

---

## 2026-09-22 -- K-ICS 금리 민감도 패널: 순자산 듀레이션/컨벡서티 -> 자산D/부채D/듀레이션갭 (owner 직접 지시)

**바뀐 것.** `K-ICS.html` 의 `#dur-strip` 2카드(순자산 듀레이션·순자산 컨벡서티)를 3카드
(자산 듀레이션·부채 듀레이션·듀레이션 갭)로 교체했다. 읽는 마스터도 같이 바뀐다:
`kics_rate_sensitivity.json`(±50/±100bp 평행이동 표에서 낸 **가용자본** 파생값) →
신설 `kics_duration_gap.json`(경영공시 **금리위험액 현황** 표의 자산총계·부채총계).

**컨벡서티를 뺀 이유 (owner 질문 "이제 더이상 의미가 없는듯?" 에 대한 실측).**
새 기준의 금리상승/하락 충격은 평행이동이 아니라 만기별 크기가 다른 기간구조 충격이고,
**상승 쪽과 하락 쪽이 대칭이 아니다**. 한쪽씩 편미분을 내보면:

| 회사 | 상승 쪽 D | 하락 쪽 D | 하락/상승 |
|---|---:|---:|---:|
| 삼성생명 | 5.35 | 6.52 | 1.22 |
| 한화생명 | 8.11 | 9.67 | 1.19 |
| 교보생명 | 8.10 | 11.36 | 1.40 |
| 삼성화재 | 5.33 | 6.11 | 1.15 |

39사 중앙값 **1.20**(범위 0.13~1.40). 진짜 ±100bp 평행이동이면 이 비율은 순수 볼록성 효과만큼인
1.02~1.05 근처여야 한다. 컨벡서티는 2차 차분 `(V₊ + V₋ − 2V₀)` 이라 이 20% 쐐기를 그대로
곡률로 읽는다. 실제로 억지로 계산하면 삼성생명 116 · 메트라이프 153 · 교보생명 327 이 나오는데
채권 포트폴리오 이론값(D²+D)은 각각 41 · 27 · 105 로, **1.7~5.7배 부풀고 배율도 제각각**이다.
곡률이 아니라 비대칭을 재고 있다는 뜻이라 카드에서 뺐다.

기존 컨벡서티는 ±bp **평행이동** 표에서 나온 값이라 산술적으로는 멀쩡했다(대칭 충격). 다만
그건 가용자본의 컨벡서티였고 △724~+221 로 흔들려 읽기 어려웠다. 패널 아래 ±bp 차트·표와
`금리민감도` 마스터의 `듀레이션`/`컨벡서티` 컬럼은 **그대로 둔다** — 원자료는 안 사라진다.

**구현.** +54/−28, `K-ICS.html` 1파일.
- `.dur-strip` `repeat(2,1fr)` → `repeat(3,1fr)`. 640px 이하 1열 규칙은 그대로 재사용.
- `<h2>` 부제 `· 순자산 듀레이션/컨벡서티` → `· 자산/부채 듀레이션 갭`.
- `durGapData` 전역 + `durGapRowsForCompany()`(`sensRowsForCompany` 와 같은 공백제거 fallback).
- `renderDurationCards(rows)` → `renderDurationCards(company, quarter)`. 마스터 컬럼
  (`자산듀레이션`·`부채듀레이션`·`듀레이션갭`)을 **그대로** 렌더 — JS 재계산 없음.
- 툴팁 산식 교체 + "K-ICS 충격은 기간구조 충격이라 2%로 나누는 건 근사, 절대 연수는 참고치" 명시.
- fetch 는 `kics_rate_sensitivity.json` 과 같은 fail-soft(`.catch(() => {})`), 로드 후
  `renderRateSensitivity()` 재호출 — 두 마스터 중 어느 쪽이 늦게 와도 수렴.
- `IQP` 정의/호출은 손대지 않았다(2026-09-21 `IQP is not defined` 사고 재발 방지).

**엣지 3종(실측 기반).**
| 상황 | 회사·분기 | 화면 |
|---|---|---|
| `듀레이션갭 == null` | 카카오페이손보 2024.2Q·2024.4Q·2025.2Q (금리부자산 충격전 △18백만원) | 스트립+노트 통째 숨김 |
| `부채듀레이션 == null` | AIG손해·라이나생명 9행 (책임준비금 음수) | 그 칸만 `—` + "금리부부채 ≤ 0 — 정의 안 됨", 갭은 정상 표시 |
| `비고` 비어있지 않음 | 발행사 표 불일치 2건 등 | 노트 하단 muted 한 줄 |

**검증.** `pytest tests/test_deploy_assets.py -q` 11 passed. 내장 브라우저로 로컬 서빙 후
`?iq_internal=1` 진입, 삼성생명 `5.94 / 6.60 / △0.26` · 라이나생명 `9.99 / — / 6.65` ·
한화생명 `8.89 / 7.84 / 1.16` — 마스터 값과 전건 일치, 콘솔 에러 0건.

**남은 것.** 분기 셀렉트는 여전히 `kics_rate_sensitivity`(2024.4Q~2026.2Q 4개 분기)에서 나온다.
듀레이션갭 마스터는 2023.2Q~2026.2Q 7개 분기라 앞의 3개 분기가 화면에서 도달 불가다.
셀렉트 소스를 두 마스터 합집합으로 넓힐지는 owner 판단 대기.

---

## 2026-09-21c -- IFRS17·기타공시 헤더 셀렉트+세그먼트 토글 이식 · common.css 승격 · 섹션 앵커 착지 오프셋 수정 (owner 발주 inbox 20260921T0500Z/0510Z + owner 직접 지적)

**요청(owner 원문)**: "디자인 관련해서 IFRS17.html에도 마찬가지로 회사명은 위에 고정, 분기/연도 선택
토글키로 바꿔라." / "기타공시 페이지도 마찬가지로 디자인 바꿔라." / (별건) "KICS.html에서 가이드탭
클릭해보니까 해당 섹션으로 이동하긴 하는데 약간 킹받게 윗부분이 짤린 상태로 조회되네, IFRS17.html은
딱 필요한 만큼만 스크롤 내려간 모습으로 잘 보여주는데, 이것도 좀 손봐라."

**변경 1 — 헤더 셀렉트 이식(IFRS17.html · 공시보고서.html)**: `#company` 를 `<header>` 안
`.header-select-row` 로 올렸다. IFRS17 은 `#coSwatch`(회사 키컬러 점)를 함께 옮겼고, 공시보고서는
스와치가 없는 페이지라 점을 넣지 않았다. K-ICS 가 먼저 쓴 것과 같은 마크업·같은 클래스다.

**변경 2 — 세그먼트 토글 이식**: IFRS17 `기준`(연도|분기, 기본 연도) · 공시보고서 `기간`(분기|연도,
기본 분기). 두 페이지 모두 **실제 `<select>` 를 `.sr-only` 로 DOM 에 남기는** K-ICS 패턴을 그대로
따랐다 — `.value` 를 갱신하고 `change` 를 dispatch 하므로 기존 리스너(IFRS17 L1788·1859·2246,
공시보고서 L239·L300·L378)와 URL 파라미터 자동선택 경로를 한 글자도 고치지 않았다.
`role="radiogroup"`/`role="radio"`/`aria-checked` + ←→·↑↓ 키.

**변경 3 — common.css 승격**: `.header-select-row` · `.header-select-label` · `.control-group` ·
`.control-label` · `.seg-toggle` · `.seg-btn`(+`.active:focus-visible` 대비 보정) · `.sr-only` 와
`@media(max-width:640px)` 오버라이드를 `common.css` 로 옮기고 `K-ICS.html` 의 페이지 로컬 정의를
지웠다. 직전 라운드에 "1페이지만 쓰므로 hoist 하지 않음"으로 남겨둔 것을, 3페이지가 쓰게 된 이번에
정리한 것이다(디자인 시스템 단일 소스, `claude-agent-designer.md` §5).

**변경 4 — 섹션 앵커 착지 오프셋을 실측 추종으로(버그 수정)**: `common.css` 의
`html{scroll-padding-top}` 이 `--header-h:76px` 하드코딩이었다. 2026-09-21b 에 보험사 셀렉트가 헤더로
올라가면서 K-ICS 헤더가 **118px** 이 됐는데 착지 지점은 그대로 88px 이라, 가이드 칩을 누르면 섹션
윗부분 **30px 이 헤더에 잘린 채** 나타났다(1400px 실측: `gap=-31`). 같은 하드코딩이 스냅 트랩도
되살려 `scrollTo(0)` 이 **31** 에 걸려 맨 위에 못 갔다.
- `scroll-padding-top:calc(var(--iq-hdr-h, var(--header-h)) + 12px)` — `--iq-hdr-h` 는 `theme.js`
  `hdrH()` 가 헤더를 실측해 내려 주는 값이라 페이지·뷰포트·향후 헤더 변경을 전부 따라간다.
  `--header-h:76px` 는 theme.js 부팅 전(해시 직행) 폴백으로만 남겼다.
- 실측(수정 후): K-ICS 데스크톱 `pad=130px` · 착지 gap `[12,12,12,52]`, 모바일 `pad=122px` ·
  `[12,12,0,12]`. IFRS17 데스크톱 `[12,12,12,12,12,12,210]`, 모바일 `[12,12,12,12,12,12,79]`.
  음수 0건(끝 칩은 문서가 더 안 내려가는 정상 케이스). `topReach` 는 4페이지 전부 0 으로 복구.
- **IFRS17·공시보고서도 이번에 헤더가 118px 로 커졌으므로, 이 수정이 없었다면 배포와 동시에 같은
  증상이 그 두 페이지에도 생겼을 자리다.**

**검증(헤드리스 Playwright, 1400px·375px)**: ① 2,000px 스크롤 후 헤더 셀렉트 visible(데스크톱 top=72 /
모바일 top=68, 3페이지) ② IFRS17 `KR0069` → `#emptyHint` 숨김 · `#dashHost` 표시 · 스와치
`rgb(20,40,160)` ③ 토글 클릭·화살표키로 `wfPeriod`/`period` 값 전환(`aria-checked` 동기) ④
`?company=KR0069` 진입 반영 ⑤ K-ICS 회귀: 표 40행 · 금리민감도 차트·표 표시 ⑥
`scripts/validate_deployed_js.py --no-live` 4페이지 **RED=0** · `pytest tests/test_deploy_assets.py`
**11 passed** · uncaught pageerror 0. 스크린샷 `artifacts/designer_shots/20260921_header_toggle_v2/`.

**손대지 않은 것**: IFRS17 `#wfPeriodLine` 패널(범위 밖 명시), 공시보고서 첫 `.panel`(배당현황 제목·
설명), `scripts/`·마스터 JSON·`public_exports/`. GA4 비콘이 `www.google.com/g/collect` 로도 나가
CSP `connect-src` 위반 콘솔 에러가 4페이지 공통으로 뜨는데, index.html 포함 변경 전에도 나던 기존
조건이라 이번 범위에서 건드리지 않았다(고치려면 CSP meta 수정이라 별건).

---

## 2026-09-21b -- K-ICS 보험사 선택 헤더 고정 + 제목 이동·부제 삭제 + 기간/경과조치 토글 (owner 발주 → inbox 20260921T0430Z)

**요청(owner 원문)**: "kics.html에서 보험사 선택 부분은 이제 화면 맨 위로 올리고 (스크롤해도 떠있게)
'원보험사별 K-ICS 지급여력비율 변동 추이 / 분기 공시 기준 시계열입니다.' 를 아래 탭 부분으로 넣어야
할거같은데? 그리고 '분기 공시 기준 시계열'도 이젠 꼭 맞는 말도 아니니까 걍 지워라. 기간, 경과조치도
스크롤박스 말고 토글로 바꿔보자." 대상은 `K-ICS.html` 단독(모델: Sonnet 5).

**변경 1 — 보험사 선택 → 헤더**: `#company` `<select>`(옵션 30개, 그대로 이동)를 `<header>` 안
`.header-select-row`(신설, `K-ICS.html:143-179`)로 옮겨 스크롤해도 항상 보이게 했다. `theme.js`의
`hdrH()`/`syncHdrVar()`는 `header.getBoundingClientRect().height`를 실측해 `--iq-hdr-h`에 반영하므로
새 행이 늘린 헤더 높이가 자동으로 섹션 네비 `top`·tuck에 반영된다(하드코딩 없음 — 이전 라운드의
71/88px 하드코딩 → 실측 120px 사고를 이 설계로 원천 회피). 클래스명(`header-select-row` 등)은
K-ICS 전용이 아니게 지어 IFRS17.html이 같은 패턴을 나중에 쓸 수 있게 열어뒀다(지금은 1페이지만
쓰므로 common.css hoist는 하지 않음 — §5.2 "≥3페이지 byte-identical만 hoist" 규칙).

**변경 2 — 제목 이동 + 부제 삭제**: 첫 `.panel`(h2+lede)을 삭제하고 `<h2>원보험사별 K-ICS 지급여력비율
변동 추이</h2>`를 `#sec-trend` 패널 최상단으로 옮겼다. `분기 공시 기준 시계열입니다.`는 다른 곳으로
옮기지도, `?` 툴팁으로 숨기지도 않고 완전히 삭제했다(owner 지시 그대로).

**변경 3 — 기간·경과조치 → 세그먼트 토글**: `<select id="period">`/`<select id="transition-mode">`는
DOM에 `.sr-only`(clip-rect 패턴)로 화면에서만 숨겨 남기고, 그 위에 `role="radiogroup"` +
`<button role="radio" aria-checked>` 2개짜리 `.seg-toggle`을 얹었다. 새 헬퍼 `setupSegToggle()`
(`K-ICS.html:366-395`)이 버튼 클릭·키보드(←→, 로빙 탭인덱스)에서 `selectEl.value`를 갱신하고
`dispatchEvent(new Event('change'))`를 실행 — 기존 `change` 리스너(`updateTable` 등, L1706-1707)와
`.value`를 읽는 8곳 이상(`getTransitionMode`·`getFilteredData`·URL 파라미터 세팅 L1684-1690 등)을
**한 글자도 고치지 않고** 그대로 재사용했다. 기간 기본값을 `분기`로 바꿔 `canShowTable()`(무변경,
`company && period`)이 회사 선택만으로 즉시 참이 되게 했고, 안내문을 "보험사와 조회 기간을 선택해
주세요" → "보험사를 선택해 주세요"로 정정했다(부제도 "헤더의 드롭다운 메뉴에서..."로). 경과조치
기본값은 그대로 `적용전`.

**A11y 즉시수정(실측 중 발견)**: `.seg-btn.active`의 배경이 `--primary`인데 `:focus-visible` 링도
같은 `--primary`라 활성 버튼(로빙 탭인덱스 시작점)에서 포커스 링이 안 보이는 문제를 발견,
`.seg-btn.active:focus-visible{outline-color:var(--on-primary)}`로 바로 고쳤다(a11y-audit 스킬
§7의 "purely additive" 분류 — 신설 컴포넌트의 포커스 가시성이라 기존 렌더값 변경이 아니므로 owner
승인 없이 처리). `scripts/a11y_contrast_check.py` 실측: 활성 버튼 텍스트 라이트 `#fff`/`#0f6e68`
6.09:1·다크 `#0c110f`/`#54b3aa` 7.62:1(포커스 링도 동일 조합이라 3:1 UI 경계 기준도 충족), 비활성
버튼 텍스트 `#212529`/`#fff` 15.43:1, 라벨 `--muted`/`#fff` 4.69:1 — 전부 WCAG AA 통과.

**검증(헤드리스 Playwright, `scripts/_probes/_20260921_verify_header_toggles.py` — 미커밋 throwaway,
venv playwright + 로컬 `http.server` 랜덤 포트)**, 7항목 지시 그대로:
1. 데스크톱 1400px·모바일 375px 스크린샷 + 2000px 스크롤 후 `#company.getBoundingClientRect()`가
   뷰포트 안 → 둘 다 `true`.
2. 라이나생명 선택(기본 `분기` 토글) → `period.value="quarter"`, tbody 40행, `#chart` visible.
3. `연도` 토글 클릭 → `period.value="year"`, 표 헤더 `["항목명","2023.4Q","2024.4Q","2025.4Q","2026.2Q"]`.
4. 한화생명 2024.4Q `적용전`↔`적용후` 토글 → 표 텍스트 diff `true`(값 실제로 바뀜).
5. `?company=라이나생명보험&period=year` 진입 → `#period.value="year"`, `연도` 버튼
   `active`+`aria-checked="true"`로 자동 반영(`setupSegToggle().sync()`).
6. `python scripts/validate_deployed_js.py --no-live` → `RED=0 (clear)`(4페이지 전부).
7. Playwright `console`(error)+`pageerror` 리스너 누적 0건(전 시나리오 합산).
추가로 키보드 `ArrowRight`/`ArrowLeft`가 `period.value`를 즉시 갱신함을 별도 확인. 스크린샷은
`artifacts/designer_shots/20260921_header_toggles/*.png`(8장). `pytest tests/test_deploy_assets.py`
11 passed(재인라인 금지·BOM·keep-list 그대로 유지 확인).

**변경 파일**: `K-ICS.html` 단독. `common.css`는 무수정(신규 클래스는 아직 1페이지만 써서 페이지
로컬 `<style>`에 둠).

**범위 밖 발견 → 별도 티켓 분리(`spawn_task task_1dc9b489`)**: 모바일 375px에서 `기타공시` 탭이
`⬇ 테이블 다운로드(.xlsx)` 버튼에 가려 겹치는 기존 버그를 검증 중 발견했다. **이번 변경이 원인이
아님**을 변경 전 HEAD 버전을 임시 디렉터리에 체크아웃해 같은 뷰포트(375px)로 재현해 확인
(`common.css`의 `.header-row`/`.tabs`/`.download-cta`가 원인, 4페이지 공유라 범위가 커서 이 티켓
에서는 고치지 않았다).

마스터 JSON 무수정, `git push`/main 배포 없음(커밋만). 상세 답변: `inbox/designer/20260921T0430Z…`.

---

## 2026-09-21 -- K-ICS 금리민감도 `IQP is not defined` 라이브 사고 복구 (owner 신고 → inbox 20260921T0057Z)

**증상**: 라이브 K-ICS.html 금리민감도 패널이 39사 중 36사에서 "…아직 없습니다" placeholder에
멈춰 있었다(owner: "라이나생명 2026.2Q 데이터가 있는데 미공시라고 나온다"). 오케스트레이터가
`renderSensDetail() → ReferenceError: IQP is not defined (K-ICS.html:1368)`로 재현.

**원인**: `2dbc4ca`(2026-09-20, IFRS17 섹션 네비 통일 라운드)가 섹션 네비 인라인 구현을
`theme.js`로 옮기면서 바로 옆에 있던 `function IQP(){...}` 정의를 같이 지웠는데, `renderSensDetail`
안의 호출 2곳(`borderColor: IQP()` / `backgroundColor: IQP()`)은 남았다. `적용후` 행이 있는
회사만 이 경로를 타서 36사가 죽었고(적용전만 있는 3사는 `'#6c757d'` 리터럴이라 안 죽었다),
예외가 `renderDurationCards()` 뒤·placeholder를 숨기는 줄 앞에서 터지는 순서라 듀레이션 카드는
그려지고 placeholder는 직전 회사의 문구를 그대로 매달고 남아 "미공시"로 보였다. 데이터
(`kics_rate_sensitivity.json`)는 처음부터 정상이었다.

**수정**:
1. `IQP()`를 `K-ICS.html:273`(옛 자리, `jsonPath` 선언 바로 앞)에 `392e8ec`가 넣었던 정의와
   바이트 단위로 동일하게 복구. 팔레트 B 색·호출부는 손대지 않음(복구지 재디자인이 아님).
2. `renderSensDetail`(`K-ICS.html:1351`)을 try/catch 래퍼로 바꾸고 실제 본문을
   `renderSensDetailInner`(`K-ICS.html:1362`)로 분리 — 어떤 예외든 잡아 `sensHideAll()`로
   차트/KPI/표/듀레이션 카드를 전부 리셋한다. "정의 삭제·호출부 잔존" 버그류 재발에 대한
   구조적 안전망(이번 버그만이 아니라 이 클래스 전체를 막는다).
3. 배포 4종 정적 스윕(`scripts/_probes/_20260921_scan_undefined_calls.py` — 문자열/주석/
   템플릿리터럴 제거 후 호출-정의 대조, CSS `var()`/object-shorthand-method 오탐 필터링):
   실결함은 `IQP` 하나뿐이었다(`IFRS17.html`의 `formatter`·`K-ICS.html`의 `afterDraw`는
   플러그인 콜백 shorthand 메서드 오탐).
4. 런타임 검증(로컬 서빙 + Claude Browser, `?iq_internal=1`): 39사 전건 `renderRateSensitivity()`
   예외 0건·`#sens-chart-wrap`/`#sens-table` 전부 `block`. 엣지케이스 3종(미선택/`IQP` 재발
   인위 재현/복구 후 재렌더) 전부 의도대로 동작. 스크린샷(라이나생명보험 2026.2Q)
   `data/_derived/`가 아니라 세션 스크래치패드에 저장(파일 경로는 인박스 답변 참조).
   `pytest tests/test_deploy_assets.py` 11 passed.

마스터 JSON 무수정, `main` cherry-push·배포 없음(publishing/owner 승인 사항).

owner 질문: 손해율×사업비율 버블이 난잡함에 비해 값어치를 하냐 / 다른 핵심지표는 없냐 /
ESR 랭킹만 남기고 치울까. 세 가지를 다 재서 답했다.

**버블은 뺀다.** 2D 자체엔 정보가 있었다 — 손해율-사업비율 상관 r=−0.096(대각선이 아니다),
합산율 1.0pt 이내 쌍 56개의 손해율 차이 평균 10.3pt·최대 35.6pt(明治安田 37.7 vs SBI 73.3).
그러나 **적층막대가 그 정보를 안 잃는다**: 두 값이 구간으로 그대로 보이고, 합산율은 막대 길이 +
숫자로 나온다(버블에선 색 농도 하나뿐 — 헤드라인 지표에 가장 약한 채널을 주고 있었다).
버블만의 추가 정보인 "원 크기=보험료"는 이미 정렬 순서가 담당한다.
실측(1280px): 회사명 31사 전건 표시(버블은 라벨 충돌로 일부만), 겹친 쌍 10조(최악 −20.4px) → 0조,
JS 에러 0, 가로 넘침 0. **ECharts CDN(1,029,203 bytes)이 이 페이지에서 통째로 빠졌다**
(유일한 사용처가 버블이었다). HTML −19,292 bytes.

**"ESR 랭킹만 남긴다"는 안 된다.** 재보니 손보 ESR 보유사는 5사뿐이고 그중 3개가 지주사다
(au損保·明治安田損保 + SOMPO HD·東京海上 HD·MS&AD HD). 東京海上日動·三井住友海上·損保ジャパン·
あいおい 같은 대형 사업회사는 ESR 랭킹에 아예 없어서, 손해율 패널을 치우면 손보 31사 중 26사가
화면에서 사라진다.

**막대 척도에도 버블과 같은 병이 있어 같이 고쳤다.** 꼬리 2사(ヤマップ 230.0%·全管協 237.4%)가
트랙의 49%를 먹어 29사가 왼쪽에 뭉쳤다. 버블이 쓰던 것과 같은 선·같은 이유(事業費率>100% =
보험료보다 비용이 큰 구조적 이상)로 눈금에서 빼고 오른쪽 끝에서 打ち切り(사선 해치, 실수치는
우측 숫자·title 로 상시 개시). 89.3%~98.4% 폭차 27px → 52px. 눈금 기준도 `list`(접힌 5사) →
`full`(31사)로 바꿨다 — 종전엔 「もっと見る」로 척도가 바뀌고 접힌 상태에선 maxV=97.1 이라
100% 기준선이 오른쪽 끝에 붙어 있었다.

**칩은 정직하게 재니 또 늘어 있길래 도로 줄였다.** 버블 뷰 4칩/잔글씨 4줄 → 일람 뷰 5칩/5줄
(버튼 뒤에 있던 6칩 범례가 상시 노출로 바뀌어서). 색 칩 2→1 병합 + caveat 칩 3줄을 1줄로 접어
최종 3칩/4줄. 배지는 각 행에 그대로고 긴 설명은 이미 배지 `title`·행 `aria-label` 에 있다 —
범례에서 중복이던 부분만 뺐다.

**남은 것**: 일본 손보의 진짜 핵심축은 「引受으로 버느냐 運用으로 버느냐」다 —
東京海上 引受利益은 経常利益의 5%, 三井住友 17%, 損保ジャパン 13%(실측). 합산율은 대형사 이익의
소수 지분만 설명한다. 다만 `pl_underwriting_profit`/`pl_investment_pl` 이 5~6사뿐이라 아직 화면에
못 올린다 — jp 레인 수집 타깃.

## 2026-09-15b -- 버블 하단 잔글씨 7줄→4줄 (owner 반려: "칩 남발")

이 세션 전 범례 5줄(`1499f9f`) → 버블 라운드에서 7줄. 마지막 3문장짜리 확대 조작 안내는
2026-09-14c 에 내가 얹은 것이다. `d70be8a`("랭킹 칩 3개→1개")에서 이미 한 번 쳐낸 축을 도로 늘렸다.

원칙 2개로 정리:
1. **화면에 없는 것은 설명하지 않는다.** 「点線の円＝保険料未収録」은 未収録이 0사인데도 상시
   출력되고 있었다. ▲·破線·点線을 `renderLossRatioBubble()` 이 실데이터를 보고 붙이게 바꿨다
   (고정은 색·크기 2개만, HTML 에 `data-fixed`).
2. **조작법은 범례가 아니다.** 확대 안내 3문장을 meta 한 줄 끝으로 이동.

색 2줄을 swatch 2개 한 줄로 합치고, 면적 caveat 과 MS&AD 주석은 `title`(호버)로 내렸다.
실측: 하단 6행 → 3행, 범례 7 → 4. 재렌더 2회 후에도 4 유지(조건부 항목 중복 누적 없음 —
`span:not([data-fixed])` 를 매번 비우고 다시 붙인다). 가로스크롤 없음, 콘솔 에러 0.


## 2026-09-15 -- 손보 決算 상세에 BS/損益 패널 개방 (jesr_app.js)

패널은 이미 만들어져 있었고 데이터가 없어 숨어 있었을 뿐이다. jp 레인이 법정 BS/PL 을 실으면서
(貸借対照表 21사·損益計算書 23사) `jesr_app.js` 의 전제 2개가 사실과 어긋나 3곳을 고쳤다.

1. `setHidden('secProfitWrap', ratioOnly)` → `ratioOnly && !hasPlItems`. "ratio_only면 損益 패널
   무조건 숨김"은 ratio_only 에 PL 이 없던 시절 규칙. 이제 `profit.items` 에 보험료 외 항목이
   실제로 있는지로 판정한다.
2. `if(ratioOnly){dispose} else {renderProfit}` 도 같은 조건으로. 1번만 고치면 패널만 열리고
   본문이 안 그려져 빈 패널이 된다(실측).
3. `profit_flow` 가 없는 회사는 단계표가 「データがありません。」 한 줄로 남는다(실측) → 그 표를
   접고 `<details>` 전 항목표를 펼치며 summary 를 「損益計算書（全項目）」로. HTML 3벌을 고치지 않고
   `closest('details')` 로 DOM 에서 처리(§5.2 파일별 복사를 늘리지 않으려고).

실렌더: AIG損保에서 워터폴(282.6 → △95.3 → △52.2 → 135.0)·16행 PL 표·16행 BS 표·
`✓ 資産 = 負債 + 純資産` 배지 확인, 콘솔 에러 0. 회귀: 기존 full 3사 단계표 19~21행 유지,
전 항목표 접힘 유지, 회사 전환 시 토글 추종 확인.


## 2026-09-14c -- 손해율 버블차트 실렌더 검증 + 결함 3건 수정 (jp/index.html)

(2026-09-14b)에 들어간 버블차트는 **그려지는 걸 본 적이 없는 코드**였다(담당 에이전트가 세션 한도로
최종검증 직전에 끊김). 이 라운드에서 실렌더로 끝까지 확인하고, 거기서 나온 결함 3건을 고쳤다.

**검증 방법 — `echarts=undefined` 는 페이지 결함이 아니었다.** 이 샌드박스의 Chromium 은 외부망을
못 뚫어 CDN 스크립트가 안 온다(같은 URL 을 쓰는 루트 `index.html`·`IFRS17.html` 도 동일). curl 은
프록시로 되므로 `echarts@5.5.0` 을 받아 **sha384 가 페이지 `integrity` 속성과 바이트 단위로 일치**
함을 먼저 확인한 뒤(=페이지가 가리키는 그 파일이 맞다), Playwright `route()` 로 그 사본을 물려
렌더했다. **저장소에는 사본을 넣지 않았다** — 하네스 전용, `jp/index.html` 은 CDN 그대로.

**결함① 라벨 글자죽 — `labelLayout` 에서 `moveOverlap:'shiftY'` 제거.**
실측(desktop 1280px): `{hideOverlap:true, moveOverlap:'shiftY'}` 는 30장 전부 그려 **겹침 35쌍**.
`moveOverlap` 이 `hideOverlap` 을 무효화한다. `hideOverlap` 단독 = 16장 / 겹침 0쌍.

**결함② 대형 4사 라벨이 1장만 생존 — 라벨 방향 4방향 회전(上→右→下→左).**
`normalSorted`(원 큰 순) 인덱스로 방향을 돌리면 가장 큰 4개에 반드시 서로 다른 방향이 배정된다.
결과 19장 / 겹침 0쌍 / 대형4사 4/4 / 컨테이너 밖 라벨 0장. 회사 ID 하드코딩 없음.

**결함③ 대형 원을 눌렀는데 소형사로 이동 — 클릭 대상 재판정.**
라벨이 원보다 위에 그려져 소형사의 긴 라벨이 대형원 위에 얹힌다(東京海上의 원 중심이 ペット＆
ファミリー 라벨 사각형 안에 있었고, 실제로 `pet_and_family` 로 이동했다). ECharts `params.data` 는
라벨 클릭에도 같은 데이터를 주므로 params 만으론 못 고친다. `params.event.offsetX/Y` 로 "클릭점을
실제로 포함하는 원"을 찾고, 복수면 **작은 원 우선**(큰 원 위의 작은 원을 누를 수 있게 — 그리기
순서와 같은 기준), 포함하는 원이 없으면 종전 params(라벨만 조준한 경우). 4종 클릭 전건 OK.

**"원끼리 안 겹치게"(owner) 는 기본 표시에서 수학적으로 불가능 — 축소 + 확대로 처리.**
최근접 2사(三井ダイレクト 64.3/28.9 · ペット＆ファミリー 64.2/28.6) 중심거리가 **2.0px** 라서
두 원 지름 합이 4.1px 이하여야 한다(=전 회사 2px 점, 크기=보험료 정보 소멸). 좌표를 밀면 값의
거짓말이 되므로(owner: 좌표는 밀지 마라) ① 지름 천장 46→34 (겹침 20쌍/최악 -30.7px →
**10쌍/-20.4px**) ② toolbox 「範囲を指定して拡大」+「初期表示に戻す」. 원 지름은 확대해도 일정하므로
배율만 올리면 반드시 떨어진다: 확대(손해율62~67/사업비27~35) 후 최근접쌍 **+17.9px**,
損保ジャパン×あいおい **+132.8px**. 실 UI 경로 검증 — 아이콘 클릭 후 드래그한 사각형 그대로
58.04~68.06 / 25.97~36.02, 되돌리기로 0~90 / 0~80 완전 복귀.

**`dataZoom` 의 `type:'inside'` 는 일부러 빼놨다 — 넣으면 도표 위에서 페이지 스크롤이 죽는다.**
실측: `zoomOnMouseWheel:'ctrl'` 로 해도, 휠 옵션을 전부 `false` 로 해도 素 휠이 페이지로 통하지
않는다(도표 위 scrollY Δ0 / 도표 밖 Δ+263 — 설정과 무관하게 inside 가 wheel 을 먹는다). 이 도표는
높이 520px 로 세로로 긴 페이지 한가운데 있어 독자가 아래로 스크롤할 때마다 커서가 들어가 멈추는,
전원이 밟는 사고가 된다. Ctrl+휠 확대·드래그 pan 의 편의보다 페이지가 안 움직이는 대가가 크다고
보고 버렸다. `tests` 대신 스크래치패드 하네스가 이 두 가지(素 휠 통과 / inside 부재)를 같이 잰다.

**모바일(375px) 발주사항 전건 확인.** 버블 wrap `display:none`·인스턴스 미생성(0×0 init 방지),
31사 목록이 정미수입보험료 **내림차순 31/31 단조**, 막대는 손해율+사업비율 2구간 누적(폭비 0.6693
vs 값비 0.6695), 가로스크롤 없음, 콘솔 에러 0. 다크모드 동시 확인.

옛 주석 1줄 정정: 도넛 폐지 때 적은 "이 페이지는 이제 ECharts 를 쓰지 않는다" 는 같은 날 버블
도입으로 사실과 반대가 됐다.


## 2026-09-14b — `value_verified` 화면 배지 (UH-25, PM-2026-09-13 후속)

배경: PM-2026-09-13(東京海上HD 238/MS&AD/かんぽ 220 + 당일 T&D 222% — 출처 URL이 목록
페이지였음) 후속. 게이트엔 `JP_ESR_UNVERIFIED_VALUE`가 배선됐지만 화면은 검증
못함/검증통과가 같은 모양이었다. publishing과 계약된 `value_verified:{state,reason}`
(verified/unverified/exempt/null)을 렌더. 오늘 실 마스터엔 필드 없음(16사 전부 verified가
될 미래) — 스크래치패드 fixture(원본 `jp/jesr_esr.json`·`jp/jesr_detail.json` 복사 후 값
주입, 실 마스터 무수정)로 4갈래 전수 실렌더 확인.

- **`verifyBadgeHtml()`/`VERIFY_META`(`jp/jesr_app.js`) + DOM판 `makeVerifyBadge()`
  (`jp/index.html`, §5.2 파일별 복사 관례)**: 같은 날 오전 라운드가 신설한
  caveat-badge(값은 검증됐지만 단순비교 주의)와 성격이 다르므로("값 자체를 확인 못함")
  실루엣을 다르게 함 — caveat-badge는 둥근 pill, 새 `.verify-badge`는 아이콘칩(굵은 2px
  테두리 + 채워진 머리글자 블록 `.vb-ic` + 라벨 `.vb-tx`). unverified=주황(`?` "値
  未検証"), exempt=파랑(`免` "確認対象外"). verified/null은 배지 없음(평소엔 안 보이는 게
  정상). `reason`은 publishing 문자열 그대로 title에 노출, designer가 다시 쓰지 않음.
- **「根拠資料 ↗」링크 수정(`renderMeta()`, 3페이지 공통 metaLine)**: 링크는 유지하되
  `state!=='verified'`면 verify-badge를 링크 바로 뒤에 병기 + 앵커 `aria-label`에도
  "（値 未検証）"/"（確認対象外）" 추가 — "여기가 근거다"라는 단독 약속이 스크린리더에서도
  안 남게 함. `source_url` 없는 회사도 배지는 뜬다.
- **적용 3곳(caveat-badge와 동일 위치 관례, owner 지시)**: ① jesr.html ESR 헤드라인 카드
  (`renderHeadline()`→`cardPrelim` 슬롯) ② jgaap.html 上段KPI 合算率 카드
  (`renderJgaapCards()`) + 収益性指標 合算率 카드(`renderProfitability()`→`ratioCard()`)
  ③ jp/index.html ESRランキング 리스트 행 + 損害率一覧 리스트 행(둘 다 `.li-name`). 손익
  라인아이템·감응도 표 등에는 추가하지 않음(계약이 posted/company record 단위 — 헤드라인성
  지표로 스코프 한정).
- **모바일 함정 선제 대응**: caveat+verify 두 배지가 동시에 뜰 수 있어(예: MS&AD/토어재보험)
  오전 라운드가 `#lossRatioList`에만 걸어둔 折り返し 규칙을 `.verify-badge`까지 확장하고
  **`#esrListLife`/`#esrListNonlife`에도 선제로 같은 규칙을 걸었다**(速報/単体詳細 chip과
  verify-badge 동시 발생 대비). fixture로 T&D에 `preliminary:true`를 임시로 얹어 2배지
  스트레스 테스트, msad_holdings/toa_re에 caveat+verify 2배지 스트레스 테스트 — 375px에서
  `.li-nm` 폭 137px 유지(오전 라운드가 고친 71.5px 붕괴 재발 없음).
- **A11y**: `a11y_contrast_check.py` 실측 — unverified 텍스트 8.83:1·아이콘 5.18:1,
  exempt 텍스트 9.52:1·아이콘 6.70:1(전부 AA 통과). `cbcheck`: unverified↔exempt 아이콘색
  delta-RGB 212~220, unverified↔기존 caveat amber(#f59e0b) delta 95+(전부 안전선 60
  상회) — 색만으로 구분하지 않음(머리글자+라벨 문구+아이콘칩 실루엣 병행). `.vb-ic`는
  `aria-hidden`. 다크모드에서 배지 고정 hex 색 유지(`.prelim-badge`/`.caveat-badge`와 동일
  "테마 비의존 고정색" 기존 컨벤션).
- **검증**: `node --check` 전체 통과, 4 HTML 태그균형 0 오류·BOM 0(실제 수정은 3파일 —
  `jp/index.html`/`jp/jesr_app.js`/`jp/jp.css`뿐, jesr/jgaap/disclosure html은 공유
  스크립트·CSS 변경만으로 무수정). 로컬 `http.server`(스크래치패드에 저장소 루트 복사, 포트
  8931) + Playwright(`/opt/pw-browsers/chromium-1194`)로 1280px/375px 다수 실측(ESRランキング
  T&D=unverified·東京海上HD=exempt·SOMPO=명시적verified→배지없음·かんぽ=필드없음→배지없음,
  損害率一覧 caveat+verify 동시렌더, jesr.html 헤드라인+링크, jgaap.html 카드 2종,
  disclosure.html 공유 확인) — `body.scrollWidth<=innerWidth` 전 케이스, `pageerror` 콘솔 0
  (외부 CDN 연결실패만, 개발망 차단 기존 패턴). fixture·검증 스크립트는 스크래치패드에만,
  `jp/*.json` 실 마스터·census·tests·docs/postmortems 전부 무수정, commit/push 없음.
- **모델·소요**: Claude Sonnet 5, 단일 세션 약 1시간.

## 2026-09-14 — 손보 손해율 24사: `data_scope`/`ratio_caveat` 렌더 + 진입점 신설

배경: 손보 29사 손해율(正味損害率·正味事業費率·合算率) 전수조사 완료, publishing이 같은
라운드에 병렬로 기존 5사 외 24사를 `jp/jesr_detail.json`에 추가 중. 세션 시작 시점엔 아직
`data_scope`/`ratio_caveat` 필드가 실 마스터에 없어 스크래치패드 fixture(`build_fixture.py`)로
개발(마스터 무수정, publishing 소유).

- **`isRatioOnly()`/`renderScopeNote()`(`jp/jesr_app.js`)**: `data_scope==="ratio_only"`인
  회사는 `jesr.html`/`jgaap.html`/`disclosure.html` 공통 `#scopeNoteWrap`에 페이지별 안내문
  ("決算" 탭으로 링크)을 띄우고, 資本(`secCapitalWrap`/`secSensWrap`)·損益内訳
  (`secProfitWrap`) 패널은 패널째 숨김 — 빈 패널을 그리는 대신 "왜 없는지" 한 줄만 남김.
  기존 `noticePanelWrap`(規制様式 곧 온다는 문구)은 ratio_only일 땐 꺼서 문구 중복/오인도
  막음. `jgaapCards`(決算 상단 KPI)는 items가 없어도 合算率 카드 1장 + 안내문으로 대체.
  `secBsWrap`/`secReservesWrap`/`secReinsWrap`/`secAxesWrap`/`by_line`/`core_history`는 기존
  self-hide 로직이 빈 데이터에서 이미 정상 동작(추가수정 불필요, 확인만 함).
- **`jp/index.html` "損害率一覧（損保）" 섹션 신설 — 24사 진입점.** 기존 ESRランキング의
  `.map-list`/`.li-row`/FOLD(top5+もっと見る) 패턴 그대로 재사용. 데이터는 `jesr_detail.json`
  (`loadDetailMap()`이 이미 읽던 fetch에 편승, `buildLossRatioData()` 신설) — sector=nonlife
  이고 合算率이 있으면 `data_scope` 무관하게 포함(기존 full 5사 + 신규 ratio_only 24사 = 29사),
  合算率 오름차순 정렬. 행 클릭/Enter/Space → `jgaap.html?company=<id>`(収益性指標로 직행).
  census `not_yet`이라 ESRランキング에 안 뜨던 회사도 이걸로 처음 도달 가능.
- **caveat 4종(`lae_excluded`/`ei_basis`/`ocr_read`/`simple_sum`) 배지 — 별도 열이 아니라
  값 옆 표식(owner 지시).** `CAVEAT_META`(jesr_app.js·index.html 양쪽 §5.2 관례대로 복사)로
  성격별 3그룹: 算式差(`lae_excluded`/`ei_basis`, Δ·실선 앰버) / 画像判読精度(`ocr_read`,
  OCR·파선 회색) / 重複計上(`simple_sum`, Σ·이중선 보라) — 색만으로 구분하지 않게 테두리
  모양+머리글자+라벨 문구를 전부 다르게. `a11y_contrast_check.py` 실측: 3쌍 전부 AA
  6.37~9.43:1 통과, 파스텔 3색 간 delta-RGB 16.5~51(완전 안전선 60 미만이나 텍스트·테두리
  모양이 이미 달라 a11y-audit 스킬 기준 severity 낮음으로 판단). 손해율一覧 행 + `jgaap.html`
  収益性指標 合算率 카드 + 상단 KPI 카드 3곳에 동일 배지, title에 `ratio_caveat.text` 전문.
- **모바일 함정 발견·수정**: 배지 붙은 행에서 `.li-name`이 badge+회사명을 한 줄에 욱여넣어
  375px에서 `.li-nm`이 min-width 바닥(5.5em≈71.5px)까지 눌려 이름이 잘림(TODO 이력 "칩이
  회사명을 밀어낸다"와 동일 패턴). `#lossRatioList` 스코프로 한정해 모바일에서만 배지를 이름
  아래 줄로 줄바꿈 — 기존 ESRランキング chip 튜닝은 무수정. 재측정: 71.5px → 136.8px 회복.
- **검증**: `node --check`(jesr_app.js + index.html/jgaap.html 인라인 스크립트 추출본),
  html.parser 태그균형(4페이지 EOF 미종료 0), BOM 0. 로컬 `http.server`(스크래치패드 사본,
  8931) + Playwright(`/opt/pw-browsers/chromium-1194`)로 1280px/375px 둘 다: 가로스크롤 0,
  pageerror 콘솔 0(외부 CDN `ERR_CONNECTION_RESET`만, 기존 패턴), ratio_only(caveat 有/無)·
  full 회사(`au_nonlife`) 상세 3페이지 hidden 속성/텍스트 DOM 직접 확인, 키보드 Enter 네비
  확인, 다크모드 배지 배경/글자색 유지 확인(`.repro-badge`와 동일 테마-비의존 고정색, 기존
  컨벤션).
- **손대지 않음**: `jp/jesr_detail.json`·`jp/jesr_esr.json`·`J-ESR/`·`scripts/`·`TODO_jp.md`·
  census·한국 자산 4개 전부 무수정. commit/push 안 함.
- 모델·소요: Claude Sonnet 5, 단일 세션 약 1.5시간.

## 2026-09-13b — jp 랭킹 算定基準: chip 되돌리고 막대 패턴으로 (owner "칩이 너무 많다")

배경: 바로 아래 2026-09-13 항목(chip안)을 owner가 반려. 실측(HEAD 기준) 랭킹 15행에 이미
scope chip 15/15행·目標 chip 7행·速報 4행·単体詳細 3행이 붙고 있어 최대 3개/행 — 여기 basis
chip을 얹으면 4개가 된다. (25) 라운드의 "모바일에서 칩이 회사명을 밀어낸다" 지적과 같은 부류의
문제라 커밋 전에 바로 뒤집었다(1차 chip 구현은 라이브에 나간 적 없음).

- **算定基準을 chip이 아니라 막대(`.li-bar`)의 패턴으로 교체.** 색(`colorForRange`의 초록/黄/赤)이
  이미 目標レンジ 의미를 쓰고 있어, 색과 **직교하는 채널** 2개를 썼다 — ① 自社基準
  (`internal_model`+`internal_management`, 한 덩어리로 묶음) = 대각선 ハッチ柄
  (`.li-bar-self{background-image:repeating-linear-gradient(135deg,rgba(0,0,0,.28) 0 3px,
  rgba(0,0,0,0) 3px 7px)}`) ② `未確認`(basis가 null/미지값) = 점선 테두리
  (`.li-bar-unconfirmed{border:1px dashed var(--muted)}`) ③ `regulatory_standard` = 기존 무지
  그대로. JS 는 `bar.style.background`(shorthand, 전체 리셋) 대신 `backgroundColor`만 인라인
  세팅해 CSS class 의 `background-image`(ハッチ)가 지워지지 않게 했다.
- **"3단이 필요한가"를 먼저 따져 2채널로 줄였다.** 内部モデル vs 内部管理의 세부 구분은 랭킹
  막대에서는 안 보여주고 `row.title`/`aria-label`/`bar.title`(호버·스크린리더 텍스트, 전부
  `basisLabel()`/`basisTitle()`로 갱신)과 상세 페이지(`jesr.html`)에만 남겼다 — 랭킹에서 필요한
  판단은 "이 숫자를 옆 회사와 그대로 비교해도 되나" 뿐이고 그건 규제/自社 2단으로 충분.
- **칩 감량이 이번 작업의 절반**: `scope`(連結/単体) chip · `目標 ○~○%` chip **전부 폐지**.
  目標レンジ는 이미 트랙 위 반투명 밴드(`.li-band`)로 중복 표현되고 있어 chip 제거로 정보
  손실이 없고, scope 는 `row.title`/`aria-label`에 그대로 남아 tooltip·스크린리더로는 계속
  확인 가능. 남은 chip 은 `速報`·`単体詳細 ▸` 2종뿐인데 실측상 **완전히 배타적**(単体詳細는
  SOMPO/東京海上/MS&AD 3개 지주행에만, 速報는 개별사 4행에만 — 동시발생 0건).
- **Playwright DOM 실측(스크린샷만이 아니라 `.li-chip` 개수·`.li-nm` 폭을 코드로 측정)**:
  15행 전부 **chip ≤1**(desktop·mobile 공통) — 목표(desktop ≤2·mobile ≤1)를 넉넉히 상회 달성.
  모바일 회사명 폭 100.8~136.8px 로 회복(chip 2종 시절 71.5~75.8px 대비 뚜렷한 개선), 375px
  가로스크롤 0. `regulatory_standard`(au損保 791.7%·明治安田損保 743.2%)는 무지 막대,
  `internal_model`/`internal_management`(朝日生命保険·富国生命保険·T&Dホールディングス·
  明治安田生命保険·SOMPOホールディングス·東京海上ホールディングス·MS&ADインシュアランスグループHD)
  는 `li-bar-self` class 로 ハッチ 렌더 확인. `未確認`은 실데이터 15사 전원 basis 확정이라
  실측 불가 — `isUnconfirmedBasis()` 로직 리뷰로만 확인(값이 다시 생기면 자동으로 점선 테두리).
- **범례 1줄만 추가**(`.chart-legend`에 ハッチ 스와치 span 1개) — 기존 5종 문구는 그대로,
  더 늘리지 않았다. 각주(`.chart-caveat`)는 새 패턴에 맞춰 1문단 재작성(전 라운드의 "chip은…"
  문구를 "棒のハッチ柄は…"로 교체) — 無地=規制ベース(告示74号)/ハッチ柄=自社基準(内部モデル・
  内部管理)/点線枠=算定基準未確認, 自社基準은 규제베이스와 단순비교 주의라는 취지.
- **상세 페이지(`jesr.html`/`jesr_app.js`)는 1차 라운드 그대로 유지** — chip이 아니라 `metaLine`
  인라인 텍스트 세그먼트(`算定基準: …`)였어서 이번 "칩 감량" 지시 대상이 아니다. 되돌리지 않음.
- **검증**: `pytest tests/test_deploy_assets.py` 11 passed. BOM 0, html.parser 태그균형 0 오류,
  IIFE 스크립트를 추출해 `node --check` 로 JS 구문 검증(문자열 치환 과정에서 남은 스텁 함수
  중복 정의를 이 단계에서 잡아 제거함 — 상세는 세션 작업 로그). Playwright(1차와 동일
  `executable_path` 우회, `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` + `--no-sandbox`,
  pip 최신판이 기대하는 리비전 1234와 설치본 1194가 안 맞아 기본 `launch()` 불가)로 1200px·
  375px·다크모드 렌더 — pageerror 0(`ERR_CONNECTION_RESET` 2건은 샌드박스 외부망 차단, 코드와
  무관, 기존 패턴). 상세 페이지 3케이스(au_nonlife detail-mode·headline-only 기본회사·
  jgaap/disclosure 게이트)도 재확인, 전부 이상 없음(다른 세션이 동시에 `jesr_esr.json`을 고치고
  있었으나 회귀 없음).
- **손대지 않음(소유권 경계, owner 지시)**: `jp/jesr_esr.json`·`jp/jesr_detail.json`·`J-ESR/`·
  `scripts/`·`CLAUDE.md`·`TODO_jp.md`. `jp/jp.css`도 무수정. 커밋·push 는 하지 않음.

## 2026-09-13 — jp 랭킹 算定基準 chip (owner 지시 "랭킹은 칩으로 기준 구분해라") — **1차안, owner 반려로 위 2026-09-13b에서 되돌림**

배경: `/jp/` ESR 랭킹 15사가 규제 표준식(告示74号)·내부모델·내부관리 3가지 다른 산정기준을 한 줄에
세우고 있는데 화면은 이를 구분 없이 노출했다. publishing 이 2026-09-13 라운드에 `jesr_esr.json`
`records[].basis`(census `esr_basis` 열 신설)로 3값(`regulatory_standard`/`internal_model`/
`internal_management`)을 채웠지만 화면은 아직 렌더하지 않고 있었다.

- **`jp/index.html`**: `BASIS_LABEL`/`BASIS_SHORT`/`BASIS_TITLE` 상수 신설(`renderList()` 상단
  근처). 각 랭킹 행 이름 옆에 `.li-chip li-chip-basis` chip — 데스크톱 전체 라벨(`規制ベース`/
  `内部モデル`/`内部管理`), 미확인·null 은 `未確認`(드롭 안 함, 향후 재발 대비). row 의 title(hover
  tooltip)·aria-label(스크린리더)도 raw value 대신 이 라벨로 교체.
- **모바일 375px 크로우딩 방지**: 기존 `.li-chip-kids`(▸ 아이콘화, `65f0aec` 2026-09-13 사고 수정)와
  동일한 패턴 — `@media(max-width:640px)` 에서 `.li-chip-basis{font-size:0}` +
  `::before{content:attr(data-short)}`로 1글자(規/モ/管/？)로 축약. `data-short` 는 JS 가 행마다
  다르게 세팅(`bc.dataset.short = basisShort(r.basis)`). Playwright 375px 실측으로 회사명 폭이
  축약 전(`65f0aec`)과 동일 수준(71.5~75.8px)임을 확인 — 이름이 밀리지 않는다.
- **각주(`.chart-caveat`) 재작성**: chip 라벨을 그대로 인용해 "規制ベース(告示74号의 標準式)/
  内部モデル/内部管理(各社独自) — 区分이 다른 회사 간은 단순 비교에 적합하지 않을 수 있다"는 취지로
  — chip 만 보고 "무슨 뜻인지" 모르는 문제를 각주로 해소(owner 요구사항 2).
  기존 캡션("算定基準(標準式・内部モデル・VaR水準等)…")을 대체.
- **`jp/jesr_app.js`(상세 페이지, `jesr.html`)**: `metaLine`에 `算定基準: …` 세그먼트 추가.
  `PAGE==='esr'` 이고 회사에 `basis` 값이 있을 때만 — `jesr_detail.json` 자체엔 basis 필드가
  없어(publishing 이 `jesr_esr.json`에만 채움) `selectEntry()`의 detail/headline 두 분기 모두에서
  `e.headlineRec.basis`를 끌어와 세팅. 랭킹 15사 밖 회사(basis 없음)는 세그먼트를 통째로 생략 —
  "未確認"을 무차별로 붙이면 ESR 자체가 아직 없는 회사까지 있는 것처럼 오인시킨다. `jgaap.html`·
  `disclosure.html`은 게이트로 막아 범위를 키우지 않음(owner 지시).
- **검증**: `pytest tests/test_deploy_assets.py` 11 passed. BOM 0(`jp/index.html`·`jesr_app.js`),
  html.parser 태그균형 0 오류. 이 환경엔 Playwright 가 미설치라 `pip install playwright` 후,
  설치된 브라우저 리비전(`/opt/pw-browsers/chromium-1194`)이 pip 최신판이 기대하는 리비전(1234)과
  달라 기본 `launch()`가 실패 — `executable_path`로 우회해 `chromium-1194/chrome-linux/chrome`을
  직접 지정, `--no-sandbox`로 구동. 1200px·375px·다크모드(color_scheme=dark) 3-way로 랭킹 페이지,
  au損害保険(算定基準 있는 detail-mode 회사)·headline-only 회사·jgaap/disclosure 게이트 3케이스
  전부 렌더 — pageerror 0(리소스 로드 실패 `ERR_CONNECTION_RESET` 2건은 샌드박스 외부망 차단으로
  Pretendard·gtag CDN 이 막힌 것, 기존 패턴과 동일해 코드 문제 아님), `document.documentElement.
  scrollWidth > clientWidth` 로 가로스크롤 0 확인. `a11y_contrast_check.py`로 chip 글자색
  (`--ink-strong` on `--bg`) 대비 실측 — 라이트 8.18:1, 다크 11.38:1 둘 다 WCAG AA(4.5:1) 통과.
- **실데이터 15사 basis 분포(2026-09-13 확인)**: 규제표준 5사 — au損害保険 791.7 · 明治安田損害保険
  743.2 · ライフネット生命保険 333.0 · 日本生命保険 195.0 · かんぽ生命保険 181.0(owner 메모의 "4사"와
  달리 ライフネット生命保険도 규제표준으로 확인돼 있어 chip 이 5사로 자동 반영). 내부모델 7사(SOMPO
  HD·東京海上HD·富国生命·MS&AD HD·明治安田生命·ソニーFG・ソニー生命). 내부관리 3사(朝日生命・T&D HD・
  住友生命保険).
- **손대지 않음(소유권 경계, owner 지시)**: `jp/jesr_esr.json`·`jp/jesr_detail.json`·`J-ESR/`·
  `scripts/`·`CLAUDE.md`·`TODO_jp.md`. `jp/jp.css`도 무수정(jesr.html 쪽은 인라인 텍스트 세그먼트뿐
  이라 새 클래스가 불필요). 커밋·push 는 하지 않음(오케스트레이터 몫).

## 2026-09-12c — GA4 내부 트래픽 플래그 (owner 발주 `inbox/designer/20260912T0830Z`)

배경: 하루 방문 15명 안팎인데 owner 본인 확인 접속이 상당수라 통계가 왜곡됨. IP 기반 규칙은
회사망·집·폰으로 IP 가 바뀌어 쓸 수 없어, 브라우저에 한 번 표시해 그 브라우저의 모든 방문을
GA4 "Internal Traffic" 으로 분류하는 방식(owner 가 GA4 Admin 에서 필터를 Active 로 켜야 실제
보고서에서 빠짐 — 그 활성화는 owner 몫).

### 무엇을 바꿨나

gtag 스니펫이 있는 5 페이지(`index.html`·`K-ICS.html`·`IFRS17.html`·`공시보고서.html`·
`privacy.html`) 전부에서 인라인 `gtag('config', 'G-F8NSCQZBZK');` 한 줄을 IIFE 로 교체:

```js
(function(){
  var cfg = {};
  try {
    var q = new URLSearchParams(location.search).get('iq_internal');
    if (q === '1') localStorage.setItem('iq_internal', '1');
    else if (q === '0') localStorage.removeItem('iq_internal');
    if (localStorage.getItem('iq_internal') === '1') cfg.traffic_type = 'internal';
  } catch (e) {}
  gtag('config', 'G-F8NSCQZBZK', cfg);
})();
```

`?iq_internal=1` 로 한 번 접속하면 `localStorage` 에 남아 이후 방문마다 `traffic_type:'internal'`
이 실려 나가고, `?iq_internal=0` 이면 해제된다. CSP meta·`<script async src>` 줄·그 위 SRI 예외
주석은 무수정(새 호스트 없음, 기존 `'unsafe-inline'` 으로 그대로 실행). `jp/index.html` 은 GA
태그 자체가 없고 다른 designer 세션이 동시에 작업 중이라 이번 라운드 대상에서 제외.

`privacy.html` "(1) 방문 통계 — Google Analytics 4" 절 `<ul>` 에 한 줄 추가:
"운영자 본인의 확인 접속은 내부 트래픽으로 분류해 통계에서 제외합니다."

### 함정 1건 — index.html 만 CRLF 전체

최초 문자열 치환 스크립트가 LF 개행 기준으로 짠 것이라 `index.html` 만 매치 실패했다
(`K-ICS.html`·`IFRS17.html`·`공시보고서.html`·`privacy.html` 은 LF, `index.html` 은 파일
전체가 CRLF — 원인은 확인 안 했으나 기존부터 그랬던 상태). 급히 `sed -i` 로 우회했다가
`sed` 가 파일 전체를 LF 로 재작성해버려 `git diff` 에 1400+ 줄 개행변경이 뜨는 사고 직전에
`git diff --stat` 로 잡았다 — Python `io.open(..., newline='')` 로 원본 CRLF 를 전량 복원한
뒤 재확인, 최종 diff 는 5 파일 모두 "삭제 1줄·삽입 12~13줄"(+privacy.html 문단 1줄)만 남았다.
5 파일 전부 BOM 없음 재확인.

### 검증

로컬 `python -m http.server 8901` + Claude Browser 로 `index.html` 을 3단계 실측:
① `?iq_internal=1` → `localStorage.getItem('iq_internal')==='1'`,
`dataLayer` 의 두 번째 config push 인자가 `{traffic_type:'internal'}`
② 파라미터 없이 재접속 → 동일하게 `traffic_type:'internal'` 유지(localStorage 기억 확인)
③ `?iq_internal=0` → `localStorage` 값 `null`, config 인자 `{}` 로 해제.
동일 스니펫인 `K-ICS.html` 도 `?iq_internal=1` 스팟체크로 재확인.
`pytest tests/test_deploy_assets.py` 11 passed. gtag.js 자체 네트워크 전송은 이 PC 의 CDN 차단
때문에 관측 불가 — 티켓이 지정한 대로 `dataLayer` 검사로 대체.

### 잔여

커밋까지만, push 는 owner 승인 후 publishing 소관. GA4 Admin > Data filters > Internal
Traffic 활성화는 owner 본인 조치(코드가 대신 켤 수 없음).

## 2026-09-12 — jp/index.html: 일본 ESR 대시보드 초안 (owner 발주, J-ESR 킥오프 2차)

배경은 `inbox/designer/20260912T0446Z__owner__JP_MULTI__jesr_jp_page_draft.md`. owner 2026-09-12
결정: 접속지 차등이나 `.co.jp` 도메인 대신 같은 사이트 `/jp/` 경로에 일본어 페이지를 둔다.
2026-07-21 revert 된 `J-ESR/index.html` MVP("데이터가 그룹값뿐")와는 별개로, 79사 census + 15사
확정값이 갖춰진 지금 새로 만들었다. 데이터는 publishing 이 같은 시각 발주(`inbox/publishing/
20260912T0446Z__owner__JP_MULTI__jesr_page_json.md`)로 만든 `jp/jesr_esr.json` — 착수 시점에
이미 도착해 있어 티켓이 허용한 fixture 경로는 쓰지 않았다.

### 무엇을 만들었나

- **`jp/index.html`** (신규, 380행, UTF-8 BOM 없음). 티켓 6절 화면 구성 그대로: 헤더(브랜드+
  언어전환 `日本語|한국어`, 한국어는 `../index.html`) → 공표상황 패널(카드3+안내문+기준일,
  전부 `_meta`에서 파생) → ESR랭킹 ECharts 가로막대(15사 내림차순, 색=업태 3색, `scope==
  group`은 decal 빗금, `preliminary`는 라벨 옆 速報 배지, `target_pct` 있으면 ▲ scatter
  마커, 캡션+범례) → 커버리지 도넛(公表済み/公表予定/未確認) → 一覧表(会社名/業態/範囲/ESR/
  基準日/出所/備考) → 푸터. `../common.css` 재사용(토큰·chrome), 페이지 전용 스타일은 인라인
  `<style>`(다른 4개 배포 페이지와 같은 패턴 — `jp/jp.css`는 안 만들었다).
- CSP meta·ECharts 5.5.0 CDN `integrity`·Pretendard CDN `integrity`는 루트 `index.html`과
  byte-diff 0(CSP는 GA 관련 호스트만 제외 — 이 페이지는 분석 태그를 안 실었다).
- 스크린샷: `artifacts/designer/jesr_jp_draft_desktop_20260912.png`(1280px) ·
  `jesr_jp_draft_mobile_20260912.png`(375px), 둘 다 full-page.

### 실데이터가 스키마 예시와 다르게 갖고 있던 것 — 화면단에서 방어

publishing 이 만든 진짜 JSON을 열어보니 티켓의 스키마 예시(`"notes":"..."`, 깨끗한 `doc_type`)
와 실제 내용이 달랐다. 마스터는 읽기 전용이라 JSON은 안 건드리고, **표시 직전 정화** 로 처리:

1. **`notes` 필드는 한국어 내부 검증 메모**(예: "PDF p21-22 직접 열람 확인: 적격자본(A)=9,278
   백만엔..."). 티켓 표 스펙("備考(速報 등)")에도 원문 그대로 노출하라는 요구는 없었고, 무엇보다
   일본어 페이지에 한국어 문장을 그대로 얹으면 안 되므로 **아예 렌더링 대상에서 뺐다** — 備考
   열은 `preliminary`→速報 배지·`basis`≠표준→짧은 표식만 보여준다.
2. **`doc_type` 15건 중 3건에 한국어 단어가 섞여 있었다**: au損害保険 "…업적데이터편…발행)",
   明治安田損害保険 "…게시)", SOMPOホールディングス "…VaR99.5%기준)". `jaOnly()` 함수를 만들어
   화면 표시 직전에만 정규식 `[가-힣]+` 로 한글 토큰을 제거하고 잔여 구두점(중복 콤마·빈 괄호)을
   정리한다 — 원본 JSON은 무변경. 브라우저에서 `document.body`(스크립트/스타일 태그 제외)
   textContent 전체를 같은 정규식으로 스윕해 잔여 한글 0건을 확인했다. 근본 원인(publishing
   파이프라인이 doc_type에 내부메모를 섞어 쓰는 습관으로 추정)은 이번 라운드에서 고치지 않았다
   — 티켓 답변에 owner 판단거리로 남겼다.
3. **`basis` 필드가 회사마다 다르다**(14/15는 "J-ICS", SOMPO만 "J-ICS_VaR99.5"). 서로 다른
   산정기준을 같은 랭킹 차트에 나란히 놓는 셈이라 차트 밑에 상시 캡션과 表 備考에
   `算定基準:VaR99.5` 표식을 추가했다. `basis.replace(/^J-ICS[_-]?/,'')` 로 접두사를 떼는
   일반식이라 향후 다른 basis 값에도 하드코딩 없이 동작한다.
4. `doc_date`가 "2026-05-20" 외에 "2026-05"(일자 없음) 형식도 3건 있어 `jaDateFlexible()`이
   2/3-분절 ISO 를 모두 받도록 만들었다.

### 발견 즉시 고친 버그 2건 (발주 범위 밖이지만 명백 + 해결 쉬움)

- **도넛 라벨 겹침**: `未確認`(2社)과 `公表済み`(15社) 슬라이스가 원형에서 서로 이웃해
  ECharts `avoidLabelOverlap`이 "公表済..."로 말줄임했다(Claude Browser 실측 스크린샷으로
  발견). 온차트 라벨을 끄고(`label:{show:false}`) 범례 텍스트에 건수를 병기(`公表済み
  （15社）`)하는 쪽으로 바꿔 정보 손실 없이 해결 — 위 카드가 이미 같은 숫자를 더 크게
  보여주고 있어 애초에 중복이었다.
- **모바일 헤더 줄바꿈**: 375px에서 "InsureQuant 日本 ESR ダッシュボード" + 언어전환이 한
  줄에 안 들어가 2줄로 깨졌다. 루트 4개 페이지의 기존 관례(`.brand .hint{display:none}` at
  `≤640px`)를 그대로 적용했다.

### 검증 — 브라우저 도구의 네트워크 샌드박스를 우회한 이유까지 기록

Claude Browser 도구로 열었더니 콘솔에 `net::ERR_NETWORK_ACCESS_DENIED`(jsdelivr, 즉
Pretendard·ECharts CDN)가 떴다. `curl`로 같은 URL을 치면 200 이 와서(회사망 차단이 아니라
이 브라우저 도구 자체의 네트워크 샌드박스 — TODO_designer.md 2026-09-11b 항목의 "Pretendard·
gtag" 케이스와 같은 부류) **검증 목적으로만** echarts.min.js 를 로컬에 내려받아
`jp/_dev_verify.html`(임시 사본, script src만 로컬로 교체)로 렌더 확인 → 이 경로로 도넛 라벨
겹침 버그와 모바일 헤더 줄바꿈 버그를 실제로 찾아 고쳤다. `jp/index.html` 자체는 처음부터
끝까지 CDN 경로만 가리키고, 임시 사본·로컬 echarts 사본은 확인 후 즉시 삭제했다.

최종 확인은 Playwright(project venv, 실네트워크)로 **진짜 `jp/index.html` 그대로** 재검증 —
데스크톱 1280px·모바일 375px 둘 다 `console` 이벤트 리스너로 **에러 0건**(Pretendard·ECharts
CDN 포함 전부 정상 로드) 확인, 이 결과로 위 스크린샷 2장을 생성했다. 이 결과가 실제 방문자
환경을 더 정확히 대표한다.

추가 확인: `body.scrollWidth===innerWidth`(375px, 가로스크롤 0), `.table-container` 안에서만
가로스크롤(出所/備考 도달 확인, 사이트 기존 관례와 동일), 두 차트의 `aria-label`이 실측
데이터로 채워짐(예: "ESRランキング棒グラフ。全15社中、最高はau損害保険 791.7%、最低は
ソニー生命保険 162.0%…"), `scripts/a11y_contrast_check.py` 로 업태 3색(`#2f6fed`/`#f59e0b`/
`#0f766e`, 상호 delta-RGB 103~236)·도넛 3색(`#0d6efd`/`#f59e0b`/`#475569`, 상호 123~255)이
protanopia/deuteranopia 임계 60 을 전부 통과 확인, 速報 배지는 흰 글자+amber 배경이 2.15:1
FAIL 로 나와 진한 글자(`#212529`)로 바꿔 7.18:1 로 통과시켰다. `html.parser` 로 태그 균형
기계 검사(0 오류, EOF 스택 빈 상태), BOM 없음.

### 넘긴 것 (owner 판단거리, 티켓 답변에 상세)

루트 `index.html`에 넣을 hreflang 3줄·상단 언어전환 링크·일본어 브라우저 안내 띠는 코드
조각으로만 답변에 적었고 **적용하지 않았다**(이번 라운드 범위 밖, 티켓 명시). `robots`
meta 는 owner 초안 검토 전 안전장치로 `noindex,follow`를 넣어뒀다 — 라이브 확정 시 제거
여부는 owner 결정. GA 분석 태그도 이번 초안엔 넣지 않았다.

---

## 2026-09-11b — 이용안내: privacy.html 절 추가 · 푸터 · 다운로드 동의 라벨 (owner 지시)

배경은 `artifacts/legal/ip_protection_report_20260911.md`(지식재산 보호 현황). 그 보고서 §4 구간 0 의
0원 조치 중 화면 쪽(HTML 4개·privacy.html·download-survey.js)을 designer 가 맡았다. owner 가 같은 날
네 가지를 못박았다: ① 약관 페이지를 따로 만들지 말고 privacy.html 에 붙일 것 ② 운영자 실명 조상욱 OK
③ 진입장벽 낮게 — 새 동의 절차·팝업 금지, 체크박스 1개 유지, 조문식 금지, 자유인 이용을 먼저 말하고
금지는 두 가지만 ④ 이 세션에서 할 수 있는 0원 조치는 전부.

### 무엇을 바꿨나

- **`privacy.html`**: 기존 1~8절 뒤에 `<h1 id="terms" class="section-break">이용안내</h1>` + h2 5개.
  보고서 §6-2 의 9개 조를 다음 5절로 압축했다 — 1. 이 사이트는 무엇인가 / 2. 이렇게 쓰셔도 됩니다
  (열람·캡처·출처표기 인용·사내 분석·다운로드 파일 내부 이용) / 3. 이것만은 피해주세요(통째 반복
  크롤링(AI 학습용 수집 포함), 대량 재배포·재판매·유사서비스 — **검수 2026-09-11c 에서 4개→2개로 압축**,
  owner 지시 "금지는 딱 두 가지만": 출처표시 제거 항목은 2절에 이미 담겨 삭제, AI 학습은 크롤링 괄호로 흡수)
  + 이유 한 줄(저작권법 보호, 법률 용어 최소화) / 4. 데이터 출처(보고서 §6-3 을 2열 표로, 최종 반영
  분기는 하드코딩 대신 "각 페이지 하단 표기 기준") / 5. 운영자·문의·준거법(조상욱 / 제보 버튼 /
  대한민국 법·서울중앙지방법원, 적용일 2026-09-11). title·og:title·description·상단 brand hint 를
  "개인정보처리방침 · 이용안내" 로, h1 도입문에 "아래쪽에 데이터 이용안내도 함께 둡니다" 한 줄(#terms 링크).
- **CSS 2줄(페이지 inline, common.css 무변경)**: `.panel h1.section-break` 는 같은 panel 안 두 번째
  문서의 구분선(margin-top 48 / padding-top 32 / border-top). `.policy-table.src-table{min-width:0}` 는
  출처표가 2열뿐이라 기존 `.policy-table` 의 640px 강제폭을 풀어 모바일 가로스크롤을 없앤 것 —
  375px 실측 표 303px < 래퍼 305px, `document.documentElement.scrollWidth` 375.
- **푸터 — 4 대시보드 + privacy.html 동일**: 기존 문장 뒤에 "화면·데이터베이스는 저작권법으로
  보호되며 이용 조건은 이용안내를 따릅니다." 한 문장, "© 2026 InsureQuant · 운영자 조상욱 ·
  개인정보처리방침 · 이용안내(`privacy.html#terms`)". 링크는 기존 `.iq-anon-link`(common.css) 그대로.
  그 이상 늘리지 않았다(owner 지시).
- **`download-survey.js`**: 동의 라벨 "위 안내사항과 이용안내(데이터 이용 조건)를 확인했습니다",
  "이용안내" 는 `<a href="privacy.html#terms" target="_blank" rel="noopener">`. `<a>` 는 label 안의
  interactive content 라 클릭해도 체크박스가 토글되지 않는다. 체크박스 개수(consent 1개)·필수 여부·
  `#iqdl-error` 문구 불변. 패널 본문의 안내문(DISCLAIMER_TEXT)엔 이용조건 문장을 넣지 않았다 —
  라벨의 링크 하나로 충분하고 본문이 길어지면 진입장벽이 올라간다. xlsx 표지 시트(`buildCoverSheet`)에
  "이용 조건" 행을 상시, "빌드 ID" 행은 manifest 에 `build_id` 가 있을 때만 추가(구 스냅샷 호환).
- **`scripts/export_public_sheets.py`**: manifest 에 `build_id`(`git rev-parse --short HEAD`, 실패 시 null)
  블록을 넣었다. 같은 시각 publishing 에이전트가 그 위에 `license`/`terms_url`/`copyright` 키를 얹었다.

### 검증

`pytest tests/test_deploy_assets.py -q` 10 passed. privacy·index·K-ICS·IFRS17·공시보고서 5 파일을
html.parser 로 돌려 미닫힘 태그 0·중복 id 0·BOM 0 확인(`#terms` 는 privacy 에만). 브라우저 실측:
privacy 1280×900 에서 h1 2개·h2 13개 순서 정상, 375×812 에서 가로스크롤 없음·`.tabs` overflow-x auto·
h1 21px. index.html 모달을 열어 라벨 텍스트·링크 href/target/rel·consent 1개·에러 문구 불변 확인.
콘솔 오류는 외부 CDN(Pretendard css·gtag.js) `ERR_NETWORK_ACCESS_DENIED` 뿐 — 개발 PC 의 외부 443
차단(기존, 코드와 무관).

### 병행 작업과 경계

publishing 에이전트가 같은 워킹트리에서 저장소 쪽 0원 조치를 동시에 진행했다: robots.txt(AI 학습
크롤러 차단 + `/public_exports/` Disallow, keep-list 주석 보존), 루트 LICENSE, `.gitignore`
`data/ir/**/*.xlsx`, IR xlsx 11개 `git rm --cached`, manifest 재생성. 내가 먼저 쓴 robots.txt·LICENSE 를
그쪽이 몇 초 뒤 덮었는데 내용이 더 낫길래(ChatGPT-User·PerplexityBot 은 AI 검색 유입을 받기 위해 허용)
그대로 뒀다. **공유 워킹트리에서 같은 파일을 두 에이전트가 쓰면 나중 쓴 쪽이 이긴다** — 저장소 파일은
publishing, 화면 파일은 designer 로 경계를 지키는 편이 안전하다. 아직 아무도 안 한 것:
`docs/ip/investment_record.md`(보고서 §6-7, 투자 기록 1장) — 저장소 문서라 publishing 소관.

### 배포

변경 파일: `privacy.html` · `index.html` · `K-ICS.html` · `IFRS17.html` · `공시보고서.html` ·
`download-survey.js`(전부 keep-list 기존 항목). 커밋·push 는 orchestrator/owner 승인 뒤, 작업 PC 는
push 불가라 폰 번들 경로.

---

## 2026-09-11 — 검색 유입: sitemap.xml · robots.txt · canonical · 네이버 (owner 요청)

owner: "서치 콘솔 ㄱㄱ" — [[2026-09-10]] GA4 도입에 이어 검색 쪽을 붙였다.

### 구글 (라이브 완료 `e2c1ab6`)

소유확인은 **도메인 속성 + 가비아 DNS TXT**로 owner 가 직접 했다. 저장소가 공급한 것은
`sitemap.xml`(정본 URL 5 개)과 `robots.txt`(전체 허용 + Sitemap 절대 URL)다.

### 조사 중 발견한 진짜 결함 — 중복 주소

**이 호스트는 확장자 없는 주소도 200 을 반환한다.** `/K-ICS`, `/IFRS17`, `/privacy`,
한글 경로 전부. 그런데 배포 페이지에 `canonical` 이 **하나도 없었다.** 구글이 같은 페이지를
두 주소로 색인해 순위를 나눠 먹을 수 있는 상태였다. **사이트맵만 넣었으면 반쪽짜리**였다 —
사이트맵은 "이걸 봐라"이지 "저건 같은 것이다"가 아니다. 5 페이지에 자기참조 canonical 을
넣고, 사이트맵의 `<loc>` 5 개와 canonical 5 개가 완전히 일치함을 기계 대조(diff 0)로 확인했다.

### 함정 세 개

1. **`rel="sitemap"` 의 href 는 상대경로여야 한다.** `href="/sitemap.xml"` 처럼 선행 슬래시를
   붙이면 `tests/test_deploy_assets.py` 가 Windows 경로 결합으로 `C:\sitemap.xml` 을 찾다
   실패해 **push 훅 전체를 막는다.** 게이트를 통과시키려다 게이트를 깨는 형태라 원인 파악이
   오래 걸린다.

2. **이 한 줄이 keep-list 강제 장치다.** 배포 keep-list 는 HTML 의 `fetch(`/`src=`/`href=`
   grep 으로 도출된다. HTML 이 참조하지 않는 루트 파일은 keep-list 에 안 들어가고 slim-ify
   절차에서 지워진다. `<link rel="sitemap">` 이 있으면 sitemap.xml 이 자동 포함되고
   `test_referenced_files_exist` 가 부재를 기계적으로 막는다. **`robots.txt` 는 HTML 이
   참조할 방법이 없어 이 보호를 못 받는다** — 미배선 잔여다(현재 배포 경로로는 안 지워지지만
   문서·테스트에 "상시 유지" 항목으로 못 박아야 한다).

3. **폰 배포 스크립트는 신규 파일을 못 올린다.** `scripts/android_push_and_deploy.sh` 는
   배포 대상을 `git ls-tree origin/main` 으로 도출해서 **main 에 이미 있는 파일만** 순회한다.
   브랜치에만 있는 `sitemap.xml`·`robots.txt` 는 순회 대상이 아니라 **"배포할 변경 없음"으로
   조용히 끝나고 라이브는 계속 404 인데 스크립트는 성공으로 보고한다.** 신규 파일의 첫 배포는
   반드시 런북 §3 워크트리 경로로 해야 한다(이번에 그렇게 했다).

### 사이트맵 작성 규칙 (다음 분기에도)

- 한글 파일명은 **대문자 헥사 퍼센트 인코딩**. 원문 한글을 그대로 적으면 색인 도구에 따라 실패.
- 경로 대소문자가 엄격히 구분된다. 소문자 변형은 전부 404 — `K-ICS`·`IFRS17` 표기 그대로.
- 중복 주소는 넣지 않는다: `/index.html`(루트와 동일 ETag), 확장자 없는 형태, 소문자 인코딩.
- `changefreq`·`priority` 는 Google 이 무시하므로 넣지 않는다.
- `lastmod` 는 **근거 있는 날짜만.** 배포 커밋 시각을 쓰거나 아예 생략한다. 지어내면
  크롤러를 적극적으로 오도한다.

### 네이버 (커밋 `58af5fa`, 배포 대기)

owner 가 서치어드바이저에 `https://www.insurequant.com/` 을 등록하고 'HTML 태그' 방식으로
받은 `naver-site-verification` meta 를 5 페이지에 넣었다. name/content meta 라 CSP 와 무관하다.

**루트 페이지만으로 충분할 가능성이 높지만 5 개 전부에 넣었다** — 이 저장소는 배포가 폰 경유
수동이라 **재시도 1 회 비용이 meta 4 줄보다 훨씬 크다.** 파일 업로드 방식은 위 함정 2 번
때문에 쓰지 않았다(구글을 DNS TXT 로 한 것과 같은 이유).

네이버는 `http`/`https` 와 `www` 유무를 **서로 다른 사이트로 취급**한다. 실제 서비스 형태
하나만 등록하면 되고, 나머지는 301 로 모인다. `robots.txt` 는 네이버에 제출할 필요가 없다 —
루트에 있으면 크롤러가 알아서 읽는다(그 메뉴는 확인용 도구다).

### 작업 중 사고 — 서브에이전트 범위 이탈

canonical 삽입을 designer 서브에이전트에 발주했는데 `index.html` 에 **요청하지 않은 접근성
코드**(표 행 `tabIndex`·`role=link`·keydown 핸들러)를 같이 넣었다. 프롬프트에 "두 줄만,
차트 코드 금지"를 명시했는데도 그랬다. `git checkout -- index.html` 로 되돌리고 필요한
두 줄만 손으로 다시 넣었다. **diff 규모를 먼저 세서(5 파일 × 2 줄 = 10 인데 17 이 나왔다)
잡았다** — 발주 후에는 diff 줄 수부터 확인할 것.

### 미배선 잔여

- `robots.txt` 상시 유지 배선(publishing 소관): `claude-agent-publishing.md` keep-list 절과
  `docs/launch_runbook.md` 에 "HTML 무참조 상시 유지 파일"(robots.txt·`.nojekyll`·CNAME) 절을
  신설하고, `tests/test_deploy_assets.py` 에 존재 단언을 추가. 문서에만 적으면
  "배선했다 ≠ 강제된다" 상태로 남는다.
- 네이버 소유확인·사이트맵 제출(owner), 빙 import(선택).

---

## 2026-09-10 — GA4 방문 통계 태그 + 개인정보처리방침 (owner 요청)

owner: "우리사이트 접속 트래픽 확인하려면 어캐?"

**출발점이 된 사실 하나.** GitHub Pages 는 Pages 사이트의 방문자 통계를 주지 않는다.
저장소 Insights 의 Traffic 은 **github.com 저장소 조회수**이지 배포된 사이트 방문자가
아니다. 즉 태그를 심기 전까지 이 사이트의 트래픽은 아무 데도 기록되지 않고 있었다.
(같은 오해를 다음 세션이 반복하지 않도록 여기 남긴다.)

### 넣은 것

측정 ID `G-F8NSCQZBZK` (owner 제공). 4 페이지 `<head>` line 9-19 에 Google 표준 gtag
스니펫, line 6 CSP 교체. `privacy.html` 신설 + 4 페이지 footer 링크 1 줄.

**ID 가 살아 있는 속성인지 기계로 확인했다** — 실제 ID 로 `gtag/js` 를 받으면 520,223 B,
존재하지 않는 대조군 ID 로 받으면 428,379 B 다. 그 92 KB 차이가 이 속성의 설정 payload 다.
오타나 죽은 ID 였다면 이 차이가 안 난다. 새 ID 를 받을 때 쓸 수 있는 검사다.

### 함정 세 개 (전부 실측으로만 잡혔다)

1. **CSP 를 같이 안 고치면 태그를 붙여도 수집량이 0 이다.** 이 저장소의 meta CSP 는
   `script-src` 에 `cdn.jsdelivr.net` 만 허용했다. gtag.js 는 `<head>` 어디에 넣든 차단된다.
   추가 토큰은 정확히 6 개 — `script-src += www.googletagmanager.com`,
   `img-src += *.google-analytics.com www.googletagmanager.com`,
   `connect-src += *.google-analytics.com analytics.google.com *.analytics.google.com
   www.googletagmanager.com`. 기존 지시자·호스트는 제거 0 건(적대적 검토로 토큰 단위 대조).
   특히 `script.google.com`(다운로드 설문)과 `cdn.jsdelivr.net`(Pretendard)이 살아 있어야 한다.

2. **`*.analytics.google.com` 은 apex 를 포함하지 않는다.** CSP 와일드카드의 정의상
   `analytics.google.com` 자체는 매치되지 않아 차단된다. 정책 문자열만 읽으면 허용된 것처럼
   보이는 자리다. 브라우저에 `securitypolicyviolation` 리스너를 걸고 실제로 쏴 봐서 잡았고,
   apex 를 따로 등재했다.

3. **gtag 는 CSP meta *뒤*에 둔다.** Google 문서는 "여는 `<head>` 바로 다음"이라고 하지만,
   meta CSP 는 파싱 시점 이후의 자원에만 적용되므로 앞에 두면 그 태그만 CSP 를 우회한다.
   동작은 하지만 하드닝이 조용히 무력화된다 — 그래서 line 8 `<title>` 뒤로 보냈다.

### 검증 방법 (다음에도 이렇게)

CSP 가 GA 를 막지 않는다는 것을 **역증명**했다. 차단돼야 마땅한 대조 호스트를 먼저 쏴서
`securitypolicyviolation` 리스너가 실제로 걸리는지 확인한 뒤(connect·script·img 3 방향 전부
enforce 로 잡힘), 그 작동하는 탐지기 앞에서 구글 호스트는 4 페이지 전부 위반 0 건이었다.
"에러가 안 났다"와 "탐지기가 죽어 있었다"를 가르는 절차다.

인라인 스니펫도 4 페이지 전부 실행된다(`gtag` = function, dataLayer 에 config 들어감) —
기존 `'unsafe-inline'` 이 덮어 준다. **nonce 를 넣으면 안 된다.** nonce 가 있으면
`'unsafe-inline'` 이 무시돼 페이지의 다른 인라인 스크립트가 전부 깨진다.

### SRI 예외 (owner 승인 2026-09-10)

이 저장소는 외부 `<script src>` 에 `integrity`+`crossorigin` 을 요구하고
`scripts/compute_sri.py` 가 관리한다. gtag.js 는 Google 이 수시로 갱신하는 가변 파일이라
해시 고정이 불가능하다. owner 승인 아래 **명시적 예외**로 두고, 사유를 태그 옆 주석에
박았다. `compute_sri.py` 에 등재하지 않는다 — 등재하면 해시가 매번 깨진다.

### 개인정보처리방침

GA 이용약관 7 조가 쿠키 고지를 담은 처리방침 게시를 요구한다. 방문 통계뿐 아니라 이미
운영 중이던 **다운로드 방명록**(소속·부서·업권·용도)과 **오류 제보**(내용)도 같이 고지한다 —
그 둘은 그동안 고지 없이 수집되고 있었다.

**동의 배너는 두지 않는다(owner 결정).** 한국 개인정보보호법 제30조의 "공개"는 홈페이지
지속 게재로 충족되고, 사전동의 배너는 행태정보를 맞춤형 광고에 활용할 때의 요건이다.
그래서 footer 의 © 줄 끝에 `· 개인정보처리방침` 링크 한 줄만 붙였다.

광고 계열 호스트(doubleclick·google.com)는 CSP 에서 **의도적으로 뺐다.** 처리방침의
"맞춤형 광고 기능 미사용" 문구와 설정을 일치시키기 위해서다. Google Ads·Signals 를 켜면
CSP 추가와 처리방침 수정이 **같이** 필요하다.

owner 결정 2 건: 연락처는 사이트 제보 폼으로 안내(이메일 비공개), 운영주체는
"InsureQuant (개인 운영)".

### keep-list

`privacy.html` 은 4 페이지가 `href` 로 참조하고 자신도 4 페이지를 참조한다. 배포 keep-list 는
HTML 의 `fetch(`/`src=`/`href=` 를 grep 해서 도출하므로 살아남는다. **서치 콘솔 인증을
`google<token>.html` 파일 업로드 방식으로 하면 안 되는 이유가 이것이다** — 아무 HTML 도
참조하지 않아 다음 배포에서 `git rm` 되고 인증이 조용히 풀린다. DNS TXT 로 할 것.

### 미검증 (배포 후 owner 확인 필요)

실제 `/g/collect` 전송은 확인하지 못했다. 개발 PC 는 사내 정책상 **VPN 이 꺼지면 외부
TCP 443 이 전부 `WSAEACCES`(WinError 10013)로 거부되고**, VPN 을 켜면 회사 관문을 통과한다
(owner 는 반대로 알고 있었다). VPN 을 켠 뒤 구글 호스트 도달과 ID 유효성까지는 확인했으나,
회사망을 거친 접속은 통계도 지저분해지므로 **owner 가 사외 기기로 GA 실시간 보고서에서**
확인해야 종결이다.

### 잔여

서치 콘솔 미착수 — 도메인 DNS 는 **가비아**이고 TXT 레코드가 현재 0 개다(= 과거 시도 흔적
없음). `robots.txt`·`sitemap.xml` 도 없다.

---

## 2026-09-03b — IFRS17 Panel 5 보험손익 구성 접기(＋ 토글) (owner 직접 지시)

owner: "17화면에서 보험손익 부분이 원수csm상각 + 원수ra해제 + ... 인데, 이것도 보험손익 옆에
(+) 버튼 만들어서 거기 누르면 보험손익 아래에 행들로 나오게 하고 평시에는 숨기자"

Panel 5 표(`renderPlTable`)만 고쳤다. **워터폴 차트는 그대로다** — 차트는 브리지라
"구성 → 앵커" 순서가 그 자체로 의미이고, owner 가 말한 "행들"은 표를 가리킨다.

**바뀐 것**: 보험손익 앵커 앞 구간(LOB 구성)이 보험손익 **아래**로 내려가 평시에는 숨고,
보험손익 행의 ＋ 로 펼친다. 기존에 있던 세부 토글(재보험 세부 · LOB 다리별 · 기타포괄손익
세부)은 그 안에서 한 겹 더로 유지된다.

**가시성을 상태에서 다시 계산하도록 바꾼 이유(설계 결정).** 종전 토글은 `tr.style.display` 를
직접 뒤집었다. 그런데 이제 한 행이 그룹 **두 개**(보험손익 구성 + 자기 세부)에 속하므로,
직접 토글이면 두 버튼이 서로의 display 를 덮어써 "보험손익을 접었는데 재보험 세부만 남는"
상태가 만들어진다. 그래서 `openState`(그룹키 → 열림) 를 두고 `applyVis()` 가 "소속 그룹이
전부 열려야 보임"으로 매번 다시 계산한다. `rows` 배열과 `tbody.rows` 는 순서가 1:1 이라
행별 소속 그룹을 인덱스로 찾는다.

**실측(회사 유형 4종 · 로컬 헤드리스, 1280×900 + 375×812):**

| 회사 | 초기 보이는 행 | 보험손익 ＋ 후 | 비고 |
|---|---|---|---|
| 삼성화재(손보) | 7 (보험손익·투자·영업외·법인세·순이익·기타포괄·총포괄) | 14 | 재보험 세부 ＋ 로 한 겹 더 → 18 |
| 삼성생명(생보) | 7 | 13 | 자동차+일반 없음 |
| 코리안리(LOB형) | 7 | 13 | 생명/장기 × 수재/출재 4개 다리가 각자 ＋ 유지 |
| 신한EZ손해(PAA) | 5 | 12 | OCI 구간 없음 |

중첩 접기 검산: 보험손익 → 재보험 세부까지 펼친 뒤 보험손익을 접으면 세부 4행까지 같이
숨는다(보이는 행 18 → 7). 모바일 375px 에서도 동일하게 동작하고 ＋ 버튼(18×18)이 화면 안에 있다.

**검증 환경 주의.** 이 PC 는 보안 에이전트가 jsdelivr 를 막아 `echarts`/`chart.js` 가 로드되지
않는다. `renderPlTable` 은 `renderPlWaterfall`(echarts) **뒤에** 호출되므로 스텁 없이는 표가
아예 안 그려진다 — 검증용 임시 사본에 echarts/Chart/XLSX 최소 스텁을 심어 확인하고 사본은
지웠다(`Chart.defaults` 는 중첩 대입을 받아야 해서 자동생성 Proxy 로 만들었다).

---

## 2026-09-03 — 섹션 스크롤 스냅("쫀득") 4개 페이지 공통 (owner 직접 지시 · 라이브 배포 `cda3c1e`)

owner: "지금 모든 html들에서 스크롤 내릴때 좀 쫀득하게 내려가면 좋겠는데 / 각 섹션 안에서는
평소대로 스크롤되다가 끝에서 살짝 멈추고, 다음 섹션으로 넘어갈땐 휘리릭 넘어가게"

`common.css` 한 곳만 고쳐 4개 페이지(index · K-ICS · IFRS17 · 공시보고서)에 동시 적용했다.
HTML 은 건드리지 않았다 — 네 페이지가 `header` / `.container` / `.panel` / `footer` 구조를
공유하기 때문이다.

```css
:root{ --header-h:76px; }
html{ scroll-snap-type:y proximity; scroll-padding-top:calc(var(--header-h) + 12px); }
.panel{ scroll-snap-align:start; scroll-snap-stop:normal; }
.container{ scroll-snap-align:start; }   /* 맨 위 도달 보장 */
footer{ scroll-snap-align:end; }         /* 바닥·푸터 도달 보장 */
```

**설계 결정 4개와 그 근거(전부 실측):**

1. **`proximity`, `mandatory` 아님.** 패널이 뷰포트보다 크다. mandatory 면 섹션 중간에서도
   계속 끌려 긴 표를 못 읽는다. proximity 는 경계 근처에서만 당긴다 — 섹션 내부 오프셋
   200/400/600px 에서 끌림 **0px**(4개 페이지 · 데스크톱 1280×900 · 모바일 375×812).
2. **`scroll-padding-top` 88px.** header 가 `position:sticky; top:0` 이라 이걸 안 주면 스냅된
   섹션 제목이 헤더에 가린다. 헤더 실측은 4개 페이지 전부 **데스크톱 76px / 모바일 71px** —
   큰 쪽 + 12px. 검산: 모든 패널을 `scrollIntoView()` 했을 때 제목 top 이 전부 **88px**
   (헤더 76px 아래, 가림 0).
3. **양 끝 트랩 방지 — 실제로 재현해서 잡은 회귀다.** 패널에만 스냅 지점을 두면 첫 지점 위와
   마지막 지점 아래가 통째로 못 가는 영역이 된다. index 실측: `scrollTo(0)` 이 **160** 으로
   끌려가 페이지 최상단에 못 갔고, 최대 스크롤 2,678 에서 **2,564** 로 되돌아가 푸터가 화면
   밖에 남았다. `.container`(레이아웃 top = sticky header 높이 76px → padding 88 을 빼면 음수
   → 0 으로 clamp)와 `footer{end}` 로 양 끝을 정식 스냅 지점으로 만들어 해소.
   `header{scroll-snap-align:start}` 는 **실패했다** — sticky 라 스냅 위치가 안 잡힌다(실측 160 그대로).
4. **`prefers-reduced-motion` 에서 스냅을 끈다.** 움직임을 줄여 달라는 사용자에게 자석 스크롤은
   정확히 그 반대다.

**섹션 끝의 "살짝 멈춤"은 브라우저 동작 그 자체다.** 패널이 스냅포트보다 크면 Chrome 은 스냅
가능 범위를 `[패널시작-88, 패널끝-스냅포트-88]` 로 제한한다(IFRS17 실측 상한 704). 프로그램적
`scrollTo` 는 그 벽에 걸리지만 **실제 휠 입력은 넘어간다**(704 에서 휠 3틱 → 992). 즉 못 가는
영역은 없고, 경계 ~110px 안에서 다음 섹션 시작으로 스냅한다(K-ICS 실측: 다음 섹션 70px 전
요청 → 다음 섹션 시작으로 이동).

**검증 방법(재현 가능):** 로컬 `python -m http.server` + 헤드리스. 이 PC 는 보안 에이전트가
jsdelivr 를 막아 차트가 안 그려지고 패널이 `will-reveal`(opacity 0)에 멈춘다 — **내 CSS 변경과
무관한 네트워크 artifact** 다. 실콘텐츠 높이를 흉내내려고 각 패널 `minHeight` 를 1,300~1,600px
로 부풀려 기하를 실측했다. 초기 측정에서 나온 "중간 끌림 -212px" 은 레이아웃 정착 전에 잰
잡음이었고, 같은 구간(2,300~2,700)을 재측정하니 전부 끌림 0 이었다.

측정 결과 요약(최종 CSS):

| 페이지 | 뷰포트 | 제목 가림 | 맨 위 도달 | 바닥 도달 | 섹션 중간 끌림 |
|---|---|---|---|---|---|
| index | 1280×900 / 375×812 | 0 (88px) | O | O | 0 |
| K-ICS | 1280×900 / 375×812 | 0 (88px) | O | O | 0 |
| IFRS17 | 1280×900 | 0 (88px) | O | O | 0 |
| 공시보고서 | 1280×900 | 0 (88px) | O | O | 0 |

모달 내부 스크롤러(`.iq-modal-panel`)는 별도 스크롤 컨테이너라 영향 없음(`scroll-snap-type:none` 실측).

**배포 (2026-09-03, main `e1c2ad9..cda3c1e`).** 배포 대상은 `common.css` 1개뿐이었다
(`git ls-tree origin/main` 전수 대조 결과 다른 파일은 전부 동일).

작업 PC 에서 push 가 막혀 안드로이드(Termux)의 **얕은 main 클론**에서 올렸다. 여기서 배운 것 셋:

1. **읽기가 통하는 것은 push 가 통한다는 뜻이 아니다.** `git ls-remote` · `git fetch` 는 정상
   동작하는데 `git push --dry-run` 은 3분 무응답으로 걸렸다. 그 차이를 확인하지 않고 "깃허브가
   다시 열렸다"고 보고했다가 owner 에게 잡혔다. **연결 판정은 읽기가 아니라 쓰기 경로로 한다.**
2. **`git hash-object` 값을 기계 간에 비교하면 안 된다.** 작업 PC 작업본은 줄끝이 CRLF 인데
   git 이 LF 로 정규화해 `147c421b` 를 뱉고, 폰(autocrlf 없음)에서는 원본 바이트 그대로
   `e674363` 이 나왔다. 파일은 바이트가 같았는데 "깨졌다"고 오판할 뻔했다. 폰에서
   `sed -i 's/
$//'` 로 LF 로 맞춘 뒤 해시가 일치했고, 그래야 저장소 관례(LF)와도 맞고
   diff 도 36줄 추가로 깔끔하게 남는다.
3. **커밋 전 게이트 두 개를 명령줄에 박아 두면 사고를 막는다.** 스테이지된 블롭 해시 대조 +
   `git diff --cached --stat`. 이번엔 `1 file changed, 36 insertions(+)` 이 찍혔다 —
   2026-09-03 오전에 라이브를 깨뜨린 그 사고의 신호가 `274,765 insertions` 였는데 그때는
   그걸 보고도 넘겼다.

라이브 검산: `curl -sk https://www.insurequant.com/common.css?cb=...` 로 받은 파일의 블롭 해시가
`147c421b`(배포 대상과 동일), 크기 18,110B, 스냅 룰 5개 전부 존재.

---
