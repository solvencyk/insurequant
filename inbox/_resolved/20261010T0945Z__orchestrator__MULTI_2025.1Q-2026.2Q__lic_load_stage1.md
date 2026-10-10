---
from: orchestrator
to: parser
created: 20261010T0945Z
status: resolved
route: feature
company: MULTI
period: 2025.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 승인(2026-10-10): **발생사고요소(LIC) BEL·RA 를 단계 적재**하고, 단일열 공시 회사는 **간접 계산값**을 쓴다(화면에 '계산값' 표시). 정찰 보고서 `data/disclosure/_meta/lic_scout_20261010.md` 가 근거(§6 적재 계획, §6.5 스키마 초안). 이 티켓은 **1단계**다. 2단계(단일열 회사 간접 도출)·3단계(비상장 15사 4Q)는 1단계 보고 후 오케스트레이터가 이어서 발주한다.

### 이미 정해진 결정 (재확인 말고 그대로)
- 값 기준 = **부채 기준**(BS `IFRS17_BS.json` 항목 20 과 닫히는 쪽). 순액(보험계약자산 상계 후)은 2-4 대조용 보조로만 둔다.
- 단일열 회사(삼성생명·교보·흥국생명·동양·미래에셋·KB라이프 등)는 `측정요소별 기말 BEL·RA − 경영공시 2-4 BEL·RA` 간접값을 쓴다 — **2단계**, 이번 티켓 아님. 간접값은 항목 7·8 에만 넣고 직접값과 섞지 않는다.
- 비상장 15사는 4Q 만 적재(나머지 5개 분기는 원천 부재 = 정상 빈칸) — 3단계.
- **★ 정정(owner 2026-10-10, 이 항목이 아래 문구·정찰안보다 우선): 새 마스터 파일을 만들지 않는다.** 기존 `insurance_liability_portfolio.json`(39사 × 2025.1Q~2026.2Q, 같은 필드)에 **항목 10번부터 행을 추가**한다. 새 항목의 `섹션` = `보험부채_발생사고요소`(기존 항목 1~8 은 `보험부채_잔여보장요소`, 9 는 `해지율_예외모형`), 레벨은 정찰 §6.5 와 같게. 정찰 §6.5 의 항목 1~8 을 10~17 로 옮겨 번호만 새로 매긴다(「보험계약부채 합계」는 BS 항목 20 과 비교하는 검산 항목). **단위는 기존 파일에 맞춰 억원**(DART 백만원 ÷ 100, 소수 둘째 자리까지 — 정밀도 손실 없음). 기존 행(항목 1~9)은 수정하지 않는다(P3 현대해상 정정만 예외, 셀 단위 + 옛 값 guard). 삽입은 지난번 병합 때처럼 셀 단위 guard(`ilp_merge2.py` 방식, 이미 있는 키면 중단)로 하고, 쓰기 전에 백업 `data/_derived/ilp_backup_*` 를 만든다. 출처·단위·표 번호·basis(net/liability)는 별도 provenance 파일(`PL_breakdown_provenance.json` 방식)에 둔다. 아래 P1·P5 의 「신규 마스터 `insurance_liability_lic.json`」은 전부 「`insurance_liability_portfolio.json` 새 항목」으로 읽는다. 자체 검산기는 `scripts/validate_insurance_liability_lic.py` 로 따로 두되(포트폴리오 검증기 `validate_insurance_liability_portfolio.py` 는 수정하지 않고, 새 항목이 그 R2 census 를 깨는지만 확인해 보고), 원천 부재 칸은 행 자체를 만들지 않는다.

### 1단계 작업
- **P1. BEL·RA 를 회사가 직접 나눠 공시하는 A1·A2 101셀 적재.** 대상은 census(§3.1)의 A1·A2 셀. 소스는 이미 디스크에 있다(`data/dart/FY*/raw/*.xml`) — downloader 작업 없음. 추출기는 정찰 헬퍼(`data/disclosure/_meta/lic_scout_20261010/xmltab.py`·`licx.py`)를 출발점으로 정식 스크립트(`scripts/extract_insurance_liability_lic.py` 등)로 만든다. 4Q·2025.1Q 는 `<TE ACODE…ACONTEXT…>` 태그로 결정적으로 읽고, 2026.1Q·2Q 는 격자 파싱.
- **P2. BS 항목 20 과 안 닫히는 셀은 원인을 규명해 처리 규칙을 세워 넣는다(칸을 그냥 빼지 않는다).** 정찰의 추정 원인: DB생명·KDB생명·메트라이프 4Q 는 연결+별도 이중 합산(별도만 취함), 악사·신한EZ·IBK연금 4Q 는 단위 표식 누락, 한화손보·현대해상·코리안리 2025.1Q 는 표 일부 누락, 푸본현대 6셀은 일부 표 누락, 서울보증 2026.2Q 는 재보험 오분류. **KB손보 6셀은 표에 순액 행뿐**이라 부채 기준을 만들 수 없다 — 순액으로 적재하되 provenance 에 `basis=net` 을 표시하고 BS 와의 차이(보험계약자산 상계)를 기록한다(게이트 예외 등재는 owner 몫이니 후보 목록으로만 보고). 끝까지 못 닫으면 칸 단위로 사유와 함께 미적재 목록에 남긴다.
- **P3. 현대해상(KR0009) 경영공시 2-4 `insurance_liability_portfolio.json` 2025.1Q~2025.3Q 의심 셀 확인.** 정찰 §5: PAA 성격 금액이 항목 4(VFA BEL 35,579 등)·항목 6 에 있고 항목 7(PAA)=0, 2025.4Q 부터는 같은 성격 금액이 항목 7 에 있다. PDF 원표(쪽 확인, 렌더링)로 컬럼 매핑을 검증해 틀렸으면 **셀 단위 + 옛 값 guard** 로 정정하고 정정 셀 목록을 보고한다(백업 `data/_derived/ilp_backup_*`). 맞으면 근거만 기록.
- **P4. 2-4 가 LIC 를 포함한 합계인 회사(ABL·KDB생명·푸본현대)를 사이드카로 기록.** `data/_derived/ilp_includes_lic.json`(회사코드·분기·근거: 항목 8 ≈ BS 항목 20 ±0.002%, ABL 은 DART T667~T673 대조). designer 가 이 3사의 왼쪽 막대에 LIC 가 섞여 있음을 화면에 안내하는 데 쓴다. 마스터 셀은 고치지 않는다.
- **P5. 자체 검산기** `scripts/validate_insurance_liability_lic.py`(push 게이트 아님, `validate_insurance_liability_portfolio.py` 선례): R-LIC1 항목6 = BS 항목 20 ±0.1%, R-LIC2 `2-4 항목8×100 ≈ 순 LRC` 또는 위 사이드카 판정, R-LIC3 항목 2+3+4 = 항목 1, census(기대 칸 대비 적재 칸, 원천 부재 칸은 별도 표기). 결과 표를 런로그에 싣는다.

### 하지 말 것
- **마스터 통짜 read-modify-write 금지**(기존 마스터 `insurance_liability_portfolio.json`·`IFRS17_BS.json` 은 셀 단위 + guard). `build_root_masters.py main()` 통짜 실행 금지. `validate_master_tables.py` 는 `--no-build`.
- 새 마스터를 루트에 쓰는 것까지가 이 티켓이다. **xlsx 동기화·`public_exports`·배포·HTML 은 하지 않는다**(publishing·designer 몫). 게이트(`validate_kics_disclosure.py`·push 훅) 수정 금지, 골든 재생성 금지(해당 시 보고만).
- 재보사 KR1101~KR1107 은 범위 밖(다음 round). KR1000 코리안리는 범위 안(A1).
- docling 불필요(XML 작업). 서브에이전트 금지, 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), 모든 파일 I/O 에 `encoding` 명시, 문서·`.py` 는 BOM 없는 UTF-8. RAM 15.5GB PC — 큰 XML 은 스트리밍/부분 읽기, 중간 산출을 디스크에 저장하며 진행.
- 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고 (끝났을 때)
- 적재 셀 수 / 미적재 셀과 사유 표, R-LIC1~3 결과(통과·불일치 셀 목록), P3 정정 셀 목록, P4 사이드카 대상.
- 런로그 `data/disclosure/_meta/lic_load_runlog_stage1.md`, `TODO_parser_ifrs17.md` Status(최신 3개·항목당 3줄) + `docs/changelog_parser_ifrs17.md` 기록.
- 2단계(단일열 간접 도출 화이트리스트 판정 기준)와 3단계 착수에 필요한 선결 사항.

## 답변 (recipient 작성 — 처리 후)
1단계 완료(2026-10-10, parser-ifrs17 Sonnet, 약 110분, 토큰 100k). 오케스트레이터 재측정: 포트폴리오 마스터에 항목 10~15 832행 추가(기존 행 변경은 KR0009 2025.1Q~3Q 12칸 정정뿐), 검산기 RED 0·YELLOW 8. 후속: IBK연금 2-4 정정 48칸·KR0011 중복 9행 제거·예별 PL 빈칸(inbox/parser/20261010T1330Z__*), 2단계(단일열 간접 도출)·3단계(비상장 4Q·라이나·처브)는 별도 발주. 런로그 data/disclosure/_meta/lic_load_runlog_stage1.md.
