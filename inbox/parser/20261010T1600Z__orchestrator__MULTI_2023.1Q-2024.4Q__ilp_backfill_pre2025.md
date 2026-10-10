---
from: orchestrator
to: parser
created: 20261010T1600Z
status: open
route: backfill
company: MULTI
period: 2023.1Q-2024.4Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 지적(2026-10-10): 「CSM 은 2023.4Q 부터 있는데 BEL·RA 는 2025.1Q 부터만 공시라는 게 말이 안 된다」. 맞다 — `insurance_liability_portfolio.json`(경영공시 2-4)이 2025.1Q 부터인 것은 **우리 마스터가 그 표만 읽은 한계**이지 공시가 없다는 증거가 아니다. 실제 확인: DB손보 FY2024_Q4 경영공시 PDF p28 에 「4-6-2) 회계모형별, 포트폴리오별 보험부채 현황 <2024년>」(포트폴리오별 일반모형 BEL·RA·CSM·PAA, 단위 억원, 주1 「원수·수재 잔여보장요소, 음수는 잔여보장자산」)이 있고, 삼성생명 FY2024_Q4 p33·p38 에도 4-6 표가 있다. FY2023_Q4 PDF 는 같은 문구가 안 잡혔다(다른 양식이거나 스캔 가능성 — 렌더링으로 확인). 또 DART 사업·반기·분기보고서의 「측정요소별 변동」 주석표(BEL·RA·CSM)와 「잔여보장·발생사고 변동」 주석표는 2023~2024 에도 있을 것이다(`data/dart/extracted/*_measurement.json` 47개는 FY2024 사업보고서 기준 PoC).

IFRS17.html 섹션 3 콤보 차트가 「연도」 모드에서 2023.4Q·2024.4Q 막대를 그리므로(owner 명세) **그 두 시점의 BEL·RA·PAA·발생사고요소 데이터가 필요**하다. 지금 designer 는 이 두 시점을 CSM 만으로 그리는 중이다.

### 작업 (같은 마스터에 행 추가만 — 새 마스터·기존 행 수정 금지)
- **A. 가용성 census 먼저**(회사 39사 × 2023.1Q~2024.4Q 8분기, 우선순위 ① 2024.4Q ② 2023.4Q ③ 나머지 분기): 출처별로 「있음 / 없음 / 스캔본 / 양식 다름」으로 센다 — 경영공시 PDF(4Q 는 4-6-2, 분기는 2-4 에 해당하는 표가 2023~2024 에도 있었는지; 양식·표 번호가 달라졌다면 그 변천), DART XML 측정요소별 변동·잔여보장/발생사고 변동 주석표(2025 LIC 1단계 추출기 `scripts/extract_insurance_liability_lic.py` 와 정찰 헬퍼 `data/disclosure/_meta/lic_scout_20261010/` 재사용). 「없음」 단정은 fitz 키워드 0회로 하지 말고 렌더링으로 확인(`feedback_keyword_absence_is_not_source_absent`). 결과 표를 런로그에 싣는다(owner 가 「2025.1Q 부터만 공시」라는 말을 믿지 않으니 분기별·회사별 증거).
- **B. 적재**: census 에서 「있음」인 셀을 `insurance_liability_portfolio.json` 에 기존 규칙으로 추가한다 — 잔여보장요소 항목 1~8(경영공시 표 기준, 억원, 같은 부호·정의), LIC 항목 10~15(DART 부채 기준, 억원 소수 둘째 자리), 해당하면 9. 이미 있는 키는 건드리지 않는다(셀 단위 + guard, 백업 `data/_derived/ilp_backup_<날짜>_pre_backfill.json`). 우선순위 순서대로 단계적으로 반영하고 단계마다 검산한다: **BS 항목 20(IFRS17_BS.json) 대조**(LRC + LIC = 항목 15 가 BS 와 ±0.1%, 순액 회사는 basis 표시), 항목 8 = 항목 1~7 합, 2-4(경영공시 표) 순 LRC 와 DART LRC 일치. 안 닫히는 셀은 원인 규명 후 처리 규칙을 세우고, 끝까지 안 되면 칸 단위 사유와 함께 미적재 목록에 남긴다(통째로 빼지 않는다).
- **C. 질문에 대한 사실 답**: 보고에 「2023.1Q~2024.3Q·2023.4Q·2024.4Q 각각 BEL·RA 가 공시됐나, 어디에」 를 표로 쓴다.

### 하지 말 것
- 마스터 통짜 read-modify-write 금지, `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 `--no-build`. 기존 행 수정 금지(추가만; 같은 키가 이미 있고 값이 다르면 보고). K-ICS 파일·`reinsurer_*`·게이트·예외 등재부·골든(`--update` 금지)·HTML·xlsx·`public_exports` 금지. 커밋·push 금지. 서브에이전트 금지. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).
- docling 은 꼭 필요할 때만 1개. 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), 맨 `python` 금지(고아 프로세스 사고 전례), `encoding` 명시, UTF-8(BOM 없음). RAM 15.5GB, 다른 에이전트 2개 동시 실행.

### 보고
- census 표(분기×회사 「있음/없음/…」와 증거), 적재 셀 수·단계별 검산 결과, 미적재 셀과 사유, designer 패널 재빌드가 필요한 (회사, 분기) 목록(2023.4Q·2024.4Q 우선). 런로그 `data/disclosure/_meta/ilp_backfill_pre2025_runlog.md`, `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.
- 4Q 두 시점(2023.4Q·2024.4Q)이 먼저 끝나는 대로 오케스트레이터에게 중간 요약을 보내 달라(SendMessage 대신 런로그 맨 위 「중간 결과」 절 갱신으로 충분).

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
