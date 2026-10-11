---
from: orchestrator
to: parser
created: 20261011T1700Z
status: open
route: backfill
company: KR0004 · KR0029 · KR0049 · KR0050 · KR0074 · KR0075 · KR0076 · KR0080 · KR0095 · KR0097 · KR0100 · KR1010 · KR1011 · KR1098 · KR1101 · KR1102 · KR1103 · KR1104 · KR1105 · KR1106 · KR1107
period: 2023.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11): 「현재 작업 중인 라운드가 끝나면, **연 1회만 공시하는 회사들도 경영공시 PDF 를 보면서 CSM 을 분기별로 백필하라.** 그러면 index.html 의 CSM 배수가 추정이 아니라 실제 값으로 보일 수 있다.」 **이 티켓은 현재 라운드(검증·커밋)가 끝난 뒤 발사된다** — 그때 마스터는 확정·커밋 상태다.

### ⚠ 사전조사 결과로 범위 축소 (오케스트레이터 2026-10-11 오후, 아래 본문보다 우선; 발사 전 owner 확인 대기)
읽기 전용 답사 결과(`data/_derived/csm_backfill_survey_20261011/group1·group2/survey.md`): 반기·분기 정기경영공시는 요약본이라 **CSM 변동표·상각 스케줄·가정민감도 표가 없다**(서술 한두 문장 + 2-4 보험부채 현황표의 기말 잔액뿐). 6항목 전체 적재가 가능한 곳은 **라이나 KR0074 하나뿐**(감사 주석 첨부, 2026.2Q·2026.1Q·2025.3Q 항등식·기초 연속성 일치, 상각표 p96). IBK연금 KR1011 은 4항목(이자부리 없음, 잔차 87.2)만. 외국계 9사는 기말 잔액 + 부분 서술(억원 정수, 합산 불일치) → 기말만 안전. 재보사 7곳·카카오페이는 표 없음/서술 불일치로 불가(연말만 공시), 예별은 마스터 2025.4Q 기말 0.0 대 공시 6,227 불일치(검증 라운드에서 보고). 따라서 이 티켓의 실제 범위는 **라이나 6항목 3분기(+상각표) + 필요 시 IBK 4항목**이며 나머지는 제외한다. 기말 CSM 합계는 ILP 마스터(항목 3+6)가 46사 2026.2Q 142.2조를 이미 갖고 있어 백필 없이 해결 가능(홈 KPI 원천 전환은 별도 결정).

### 배경 (오케스트레이터 실측 2026-10-11)
- `CSM_waterfall.json` 에서 2026.2Q 기말 CSM(항목 6)이 있는 회사는 23사(130.4조원). 아래 21사는 DART 에 분기·반기 보고서가 없어 **연말(사업보고서)만** 적재돼 있다(최근 분기 2025.4Q, 일부 2024.4Q): 
  - 있는 분기: 예별 KR0004 · AIG KR0029 · 악사 KR0049 · 하나손보 KR0050 · 라이나 KR0074 · BNP카디프 KR0075 · iM라이프 KR0076 · AIA KR0080 · 메트라이프 KR0095 · 하나생명 KR0097 · 처브 KR0100 · 교보라이프플래닛 KR1010 · IBK연금 KR1011 · 뮌헨 KR1101 · 스위스리아시아 KR1102 · 제네럴 KR1103 · 스코리 KR1106 = 2023.4Q·2024.4Q·2025.4Q / 카카오페이 KR1098 · 퍼시픽라이프리 KR1107 = 2024.4Q·2025.4Q / 하노버 KR1104 · RGA KR1105 = 2023.4Q·2024.4Q. 
  - 각 회사 기말 CSM 최근 분기 합계 약 11조원(메트라이프 2.6 · 라이나 2.4 · AIA 1.6 · RGA 0.9 · iM 0.8 · 하나생명 0.7 · IBK 0.5 · 스코리 0.4 · …).
- 홈(index.html) 「업계 총 기말 CSM」은 회사별 **최신 분기 값의 합**(지금 라이브 37사 139.7조, 새 마스터 44사 141.4조)이라 위 회사의 옛 분기 값이 섞여 있다. 버블맵은 이 회사들을 「연1회 공시사 추정」(직전 마감연도 연누계 ÷2, 배수 이월)으로 회색 별표 처리한다.
- NB CSM 배수 = 신계약 CSM(`CSM_waterfall` 항목 2) ÷ 월납월초(KIDI `data/kidi/premium_summary.json`, 39사 × 14분기 = 546건, 이미 전 분기 커버). 즉 **분기 신계약 CSM 만 채워지면 배수는 `build_nb_csm_multiple.py` 가 실제 값으로 계산**하고, 화면의 「추정」은 데이터 최신성으로 자동 해제된다(KIDI 분모가 없는 재보사·연금은 배수 null 로 남는다 — 정상).

### 해 줄 것
1. **원천 확인(먼저, 분기별)**: 각 회사·분기 정기경영공시 PDF(`data/disclosure/FY*/raw/`, 신판이 있으면 `_v*`/`kics_edition_choice.json` 기준 최신 판)에 IFRS17 「계약서비스마진 변동내역」(CSM 기초·신계약·이자부리·가정조정·상각·기말) 표가 **분기마다 있는지** 회사별로 센서스한다. 표가 없는 회사·분기는 칸을 비우고 사유를 보고한다(추정치로 채우지 않는다).
2. **적재**: 표가 있는 칸을 `CSM_waterfall.json`(항목 1~6, `값`=연누계 YTD, `값_당분기`) 에 **셀 단위 + 옛 값 guard + 백업**으로 추가한다. 재보사 선례(커밋 `e8ca3af`, 로더 `load_reinsurer_csm_masters_20261011.py`, 작업물 `data/_derived/reinsurer_ifrs17_csm_20261011/`, 이전 티켓 `inbox/_resolved/20261011T0430Z…reinsurer_csm_masters.md`)와 같은 규칙: 단위(억원), 부호, YTD/당분기 정의, 출처 provenance(`CSM_waterfall_provenance.json`). 같은 경영공시에 상각 스케줄·민감도 표가 있으면 `CSM_amortization.json` · `CSM_sensitivity.json`(그리고 해당 시 `management_indicators.json`)도 같은 방식으로(재보사 선례 범위). 우선순위: 2026.2Q → 2026.1Q → 2025.3Q → 2025.2Q → 2025.1Q → 2024.x → 2023.x(2023.1Q~3Q).
3. **검산(1급)**: 기초 + 신계약 + 이자 + 가정조정 + 상각 = 기말(항등식), **기초 = 직전 분기 기말**(연속성 단절은 소급재작성 사유라도 RED 로 보고 — `feedback_continuity_break_is_red`), YTD 단조성·분기 환산, 분기 신계약 CSM ≥ 0(음수면 4Q 연차 재서술 artifact 인지 확인). 재작성 사이드카가 있는 회사(라이나·미래에셋·KB라이프 계열)는 기존 사이드카 규칙을 따른다. 연말 칸은 이미 사업보고서 값이 있으니 **기존 칸은 바꾸지 않고**, 경영공시 연말 값과 다르면 칸 목록으로 보고만 한다(최신 공시 우선 원칙은 owner 판단).
4. **PL 쪽 연결**: 재보사 CSM 적재 때 `PL_CSM_AMORT_VS_WATERFALL` 17건이 생긴 선례(PL 항목 4 가 경영공시 계보로 안 채워짐 §3d)가 있다. 새 칸에서 같은 유형 RED 가 생기면 되돌리지 말고 목록(등재 후보 JSON, 등재는 owner)으로 보고한다.
5. **NB 배수 영향 점검(읽기만)**: 채운 신계약 CSM 으로 `build_nb_csm_multiple.py` 를 **임시 폴더에서 모의 실행**해(마스터 덮어쓰기 금지) 새로 실배수가 생기는 회사·분기 수, 배수의 범위(이상치: 단위 오류 의심 > 50배 등)를 보고한다. 실제 NB 마스터 재빌드는 뒤따르는 publishing 라운드가 한다.

### 규칙
- 마스터 쓰기는 **셀 단위 + guard + 백업**, 통짜 read-modify-write 금지, `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 반드시 `--no-build`(인자 없이·`--help` 단독 금지). 기존 칸 변경 0 을 적재 전후 HEAD 대조 diff 로 증명.
- 이 티켓이 쓰는 파일: `CSM_waterfall.json` · `CSM_waterfall_provenance.json` · `CSM_amortization.json` · `CSM_sensitivity.json` · `management_indicators.json`(+ 해당 provenance/사이드카) · `data/_derived/*csm*` 작업물. K-ICS·BS·PL·ILP·NB 마스터·xlsx·`public_exports`·HTML·게이트·예외 등재부·골든(`--update` 금지) 금지. 커밋·push 금지(오케스트레이터가 HEAD 대조 후 커밋), 서브에이전트 금지, docling 은 텍스트층이 없는 쪽에만 최대 2프로세스(RAM 15.5GB).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·맨 `python`·stdin heredoc 금지), `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결). 런로그 `data/disclosure/_meta/csm_backfill_annual_filers_runlog_20261011.md` 맨 위에 단계마다 갱신.

### 보고
- 회사×분기 CSM 표 유무 센서스 표, 적재 칸 수(워터폴·상각·민감도·지표), 검산 결과(항등식·연속성·단조성), 연말 칸 불일치 목록, 새 RED·등재 후보, NB 배수 모의 결과, 기존 칸 변경 0 증명, 남은 원천 부재 목록, `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
