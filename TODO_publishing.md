# Insurequant Publishing TODO (Stage 4)

> 갱신 2026-10-13 · 프롬프트 `docs/agents/claude-agent-publishing.md` · 이력 `docs/changelog_publishing.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_publishing.md` 맨 위에 있다. publishing 은 마스터 JSON 만 쓰고 HTML 은 designer 몫이다.

## Status (최신 3개)

- **2026-10-13 parser-ifrs17 `b8c37fff`(249 셀) 파생 산출물 재생성(커밋 `99c7ead7` · push 보류)** — RED NB_VS_WATERFALL(메리츠 2023.3Q) 해소: `NB_CSM_multiple.json` 12칸(동양 2023.1Q·2Q, 메리츠 2023.3Q·4Q) · `data/compare/panel_compare.json` 69잎(63 = b8c37fff·NB, 6 = 기존 낡음) · `data/csm_combo/panel_csm_combo.json` 8잎 · xlsx `신계약CSM배수` 12칸 · 공개본 `신계약CSM배수`. `viz_build_ifrs17_panels`·`viz_build_csm_waterfall` 은 `data/dart/extracted` 를 읽어 재실행해도 HEAD 와 바이트 동일(변경 없음).
  남은 것: ① validation: viz 골든 2종·IFRS17 골든(이 커밋 뒤에 실행) ② 증빙 `data/_derived/ifrs17_regen_20261013/`.

- **2026-10-13 독립 감사 티켓 `20261012T2235Z` 요청 1·2·3 + owner 결정 8(커밋 `48c7c3ac` + 콜 경과 정정 `10b45d71` + 콜일 기준 정정 `7e6e55d0` · push 보류)** — ① DB손보 제1·2회 콜일 원문 상충(FY2025 둘 다 09-01 / 2026 1Q·반기 09-25·09-01): 타임라인 잔액 null 로 날짜만 표시 + 공개 시트 콜일 비움 ② 하나손해 원장에 2026-06-29 추정 행(999억, 금리·콜일 없음, `estimated`) ③ 기본자본 인쇄 한도: 결속 갈래 없는 33사 15% -> 10%(소진율 47사 불변) ④ 보완자본 분자의 기발행 차감 = 원장 2022-12-31 이전 잔액에서 콜일이 지났는데 상환 안 한 채권(`past_call_outstanding`) 제외(47사 공통, 19사 변동: 메리츠 0.2 -> 37.5 · 흥국생명 10.6 -> 37.0 · 한화생명 70.5 -> 74.8 · 푸본 86.6 -> 73.1 · 농협생명 18.8 -> 21.1 · 롯데 53.5 -> 58.6 · 흥국화재 45.3 -> 53.3 · 악사 2.0 -> 29.2 · 아이엠라이프 49.5 -> 70.4 · KB라이프 0.8 -> 0.8(0.0 거쳐 복귀); 제외 판정은 첫 콜일 <= 분기말; 현대해상·DB손해는 메모 값 유지).
  남은 것: ① owner: 흥국화재(인쇄 신종 2,120 에 콜 경과 920 포함)·악사(인쇄 후순위 345 가 콜 경과 JPY 채권으로 보임)는 발행사가 콜 경과분을 기발행 줄에 넣어 이 정정이 발행사 처리와 반대로 움직임 - 확인 · 아이엠라이프 70.4(원장에 전환우선주 없음, 기준일 2025-12-31; 인쇄 항목 53 을 그대로 빼면 16.0) ② designer: 티켓 `20261013T0030Z`(DB손보 셀 눈 확인, 하나손해 추정 툴팁) ③ 증빙 `data/_derived/capsec_reinstate_20261012/z3·z4·z6·y1`.

- **2026-10-12 발행사 처리 기준 재분류 + 증권별 X 검정(커밋만 · push 보류)** — 티켓 `20261012T2115Z`: 하나생명 제1회·교보 2024-11 `type` tier2 -> tier1(발행사 K-ICS 표가 기본자본형으로 처리), 나머지 tier2 증권 10개사 12건은 발행 분기 X(항목13-49) 검정으로 보완자본형 확인, 판정 불가 3건(푸본 600·농협생명 제5회·코리안리 제6회)은 현 분류 유지(`issuer_check`). 소진율 tier1 은 하나생명 0.0 -> 238.2 만 변경(교보 70.1 불변), tier2·총자본 경로 불변, forward 의 `baseline_basis_flag` 류 필드는 사라짐. `tier1_overflow_into_tier2_eok`(공개 시트 1칸)가 옛 채권원장 추정(하나생명 665.7)으로 낡아 있던 것을 기본자본 소진율과 같은 출처(1,043.6)로 47사 통일 (`dbbffcb5`).
  남은 것: ① owner: 판정 불가 3건의 발행사 처리 확인 필요 시 별도 근거(원문 표 재독)가 필요 ② 증빙 `data/_derived/capsec_reinstate_20261012/x1~x6` ③ 기존 DB손보 5건(기본자본형)은 이번 범위 밖 - 같은 X 검정 미실시.

## 열린 일

- [ ] **자본성증권 후속 3건** — `inbox/publishing/20260923T1130Z` §1 `step_up` 플래그(원문 근거 있는 건만 true) · §2 후순위 `잔액기준일` 이
  2025-12-31 로 두 분기 낡음(공시 주기 문제면 시트 설명에만 적는다) · §3 한화생명 item54 17,932억 vs 인벤토리 14,712억(원문 TFI 표 정의부터 확인).
  §3 참고(2026-10-12): 항목 54 분기 시계열·원장 대조 `data/_derived/capital_utilization_apply_20261012/a2·a3` — 2023.3Q 에 +5,628(신규 후순위 발행 분기) 뒤 2023.4Q -8,439.
- [ ] **공개 다운로드 잔여 내부 문구 4건**(2026-10-06 snake_case 스캔, jargon 룰 4패턴 밖이라 게이트는 통과) — 가정민감도 `비고` 1행 ·
  기본자본소진율 22행(2026-10-12 재정의 후 문서 경로가 남은 100% 초과 행 7행) · 자본성증권발행현황 `비고` 123행·`콜근거` 59행. 고칠지 owner 판단.
- [ ] **듀레이션갭 3개 분기 화면 도달 불가** — 분기 셀렉트가 `kics_rate_sensitivity`(4분기)에서 나와 2023.2Q·2023.4Q·2024.2Q 를 못 고른다.
  셀렉트 소스 확장은 owner 판단(designer 와 같이).

## 휴면 / 보류

F4 v2 forward confidence(Cat C/D 리서치·외국계 분류 helper) · F13 재보험 영업 지표(downloader F8 선행) · F17 Tier2 LOB viz(parser 결정 대기) ·
F18 IR 통합·MISC-IR-NB-DENOM·MISC-IR-PROTOTYPE(IR 파싱 보류) · CAPSEC-SAMO-GAP 사모채 5사 처리 방식 결정(`TODO_downloader.md`).
