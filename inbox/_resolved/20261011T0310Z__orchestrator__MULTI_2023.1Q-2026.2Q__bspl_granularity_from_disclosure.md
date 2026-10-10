---
from: orchestrator
to: parser
created: 20261011T0310Z
status: open
route: backfill
company: MULTI
period: 2023.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 지적(2026-10-11, 밤새 처리 지시): 2026-10-08~09 에 경영공시를 보고 **BS·PL 빈칸을 백필**한 결과(커밋 ba32077·718a710, 이전 티켓 `inbox/_resolved/…bspl_blank_cells_from_disclosure`)가 **하나손해보험은 자산·부채·자본 총계 3칸만 채웠다**. owner: 「사별 경영공시를 보면 **지금 마스터 수준의 granularity 는 충분히 다 채울 수 있다**(자산 아래 현금성자산·재보험계약자산 등, 자본 아래 이익잉여금·자본금 등). **전부 다시 채워와라.**」

### 범위
- **대상 회사**: DART 재무제표(FS-API)로 BS 가 안 채워지는 **경영공시 전용 회사 전부** — 비상장 15사(KR0004·0029·0049·0050·0051·0074·0075·0076·0080·0095·0097·0100·1010·1011·1098, 분기 5개는 DART 공시 자체가 없음) + **재보사 8곳(KR1101~KR1108, 경영공시 PDF 97건)**. 그리고 같은 문제(총계만 채움)가 다른 회사·분기에도 있는지 **census 로 전수 확인**(`IFRS17_BS.json` 의 (회사, 분기, 항목) 중 비어 있는 칸과, PL_breakdown 43항목 중 비어 있는 칸).
- **대상 마스터·항목**: `IFRS17_BS.json`(현재 항목 전체: 자산·부채·자본 총계, 현금·금융자산, 재보험계약자산/부채, 보험계약부채, 법정준비금 4종, AOCI, 자본 세부 등 — 마스터에서 항목표를 직접 읽어라)과 `PL_breakdown.json`(43항목). **마스터가 가진 granularity 만큼**(새 항목을 만들 필요는 없고, 비어 있는 기존 항목을 채운다).
- **원천**: 각 회사·분기 경영공시 PDF(`data/disclosure/FY*/raw/`) — 요약 재무상태표(2-2/4-2 류)·재무제표 절(8-x 재무상태표·손익계산서, 주석)·준비금 현황(3-x/5-x)·요약 PL(2-1/3-2). 표 위치·양식은 연도별로 바뀌니(2024.4Q 부터 4-x 신설) 분기별로 특정한다. **하나손보(KR0050)를 첫 대상으로 삼아 「어느 표에서 어떤 항목까지 나오는지」 항목×원천 매핑표를 만들고**, 같은 방식을 전 회사에 적용한다. 정찰 `data/disclosure/_meta/reinsurer_ifrs17_scout_20261010.md` §2 에 재보사 8곳의 표 센서스가 있다(요약 손익·요약 BS 14분기 등).
- **원천이 PDF 에 정말 없는 칸**(예: 하나손보 p60 은 「Ⅷ. 재무제표 사항은 첨부 파일 참조」 — 별첨 재무제표 PDF 가 우리 raw 에 없다)은 **렌더링으로 확인한 증거와 함께 목록**(회사·분기·필요한 별첨 문서)으로 보고한다 — 별첨을 받는 것은 downloader 몫이니 오케스트레이터가 발주한다. 「PDF 가 별첨 참조라서 없다」고 단정하기 전에 같은 PDF 의 다른 절(요약표·주석·준비금·경영지표)에 항목이 있는지 먼저 찾는다.

### 규칙
- 이미 들어 있는 값은 **수정하지 않는다**(새 칸 채움만. 같은 키의 기존 값과 새 값이 다르면 덮지 말고 충돌 목록으로 보고 — owner 규칙 R1 「최신 공시 전기 칸」은 기존 39사에 자동 적용이 아니다). 단위(억원/백만원/천원)는 마스터 단위로 변환하고 회사별 단위 표식을 확인(배율 오류 전례 다수).
- **셀 단위 + 옛 값/빈칸 guard**, 시작 전 백업(`data/_derived/…backup_<날짜>`), 마스터 통짜 read-modify-write 금지, `build_root_masters.py main()`·`build_ifrs17_bs.py` 통째 실행 금지(`validate_master_tables.py` 는 `--no-build`). 지난 백필 때 만든 도구(`scripts/extract_pl_g5_disclosure_20261008.py`·`merge_pl_backfill_disclosure_20261008.py`·`fix_pl_backfill_followup_20261009.py`·`data/_derived/bs_from_disclosure*.json`·`pl_from_disclosure*`)와 검증 결함 티켓(`inbox/parser/20261009T0330Z…r1_defects`·`…T0700Z…r2_defects`, 열린 상태)을 먼저 읽고 같은 결함(총계 항등식·부호·단위·누계/당분기 혼동)을 반복하지 않는다.
- **검산**: 항등식(자산 = 부채 + 자본, 세부 합 = 총계, 준비금 4종 합, PL 항등식 `1 = 2+13+14+15−16` 류)을 채운 칸마다 돌리고 안 닫히면 원인 규명(미채움 칸이 있으면 정상일 수 있음)·보고. 모든 단계에서 기존 칸 변화 0 증명(적재 전후 diff). `scripts/validate_master_tables.py --no-build`·`scripts/validate_data_contract.py` 결과를 보고(골든 `--update` 는 하지 않는다 — validation 몫; 골든이 어긋나면 사실만 보고).
- 회사별 우선순위: ① 하나손보 ② 나머지 비상장 14사 ③ 재보사 8곳(마이브라운 KR1108 은 일반 손보) ④ 그 밖에 census 에서 나온 구멍. 단계마다 디스크에 중간 산출·런로그 저장.

### 하지 말 것
- K-ICS 파일·`insurance_liability_portfolio*`·`CSM_*`(다른 에이전트가 쓴다), 게이트·예외 등재부·골든·HTML·xlsx·`public_exports` 금지. 커밋·push 금지. 서브에이전트 금지, docling 은 꼭 필요할 때만 1개(동시 ≤2는 전 에이전트 합산 기준이니 1개로). RAM 15.5GB, 다른 에이전트 2개 동시 실행.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python -`(stdin heredoc) 절대 금지**(고아 CPU 스핀 전례 3회), `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고 (끝났을 때, 가능하면 중간 결과를 런로그 맨 위에 계속 갱신)
- 항목×원천 매핑표, census(회사×분기별 채움/구멍), 채운 칸 수와 검산 결과, 충돌 목록, 원천 부재 칸(별첨 필요 목록 포함), 게이트 전후. 런로그 `data/disclosure/_meta/bspl_granularity_runlog.md`, `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
