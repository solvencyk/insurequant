---
from: orchestrator
to: parser
created: 20261010T0830Z
status: resolved
route: scout
company: MULTI
period: 2025.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
**읽기 전용 정찰.** 마스터·스크립트·문서는 고치지 않는다(보고서 1개만 쓴다).

owner 요청(2026-10-10): IFRS17.html 섹션 3 콤보 차트에 **발생사고요소(LIC, 지급준비금)의 BEL · RA 구분**을 넣고 싶다. 지금 `insurance_liability_portfolio.json`(경영공시 2-4, 억원, 2025.1Q~2026.2Q)은 **잔여보장요소(LRC)만**이다(검증기 `scripts/validate_insurance_liability_portfolio.py` docstring). BS 보험계약부채(`IFRS17_BS.json` 항목 20, 백만원)는 LRC + LIC 다.

### 알고 싶은 것
1. **LIC 의 BEL(미래현금흐름 현재가치 추정치)·RA(위험조정)를 분기·회사별로 어디서 얻을 수 있나.** 후보 출처: (a) DART 사업·반기·분기보고서 XML 의 보험계약부채 주석(구성 내역·증감표의 "발생사고요소" 행, PAA 적용/미적용 구분) — `data/dart/` (b) 경영공시 PDF 의 다른 표(2-4 외 구성·증감표) (c) KIDI 등 `source-catalog.yaml` 에 선언된 5개 출처 전체(기본 체크리스트). 기존 파서 마스터(`CSM_waterfall.json`·측정요소 rollforward·`IFRS17_BS.json` 항목 17~25 근처)에 이미 있는 LIC 관련 항목도 먼저 확인한다.
2. **분기별 가용성**: 1Q·3Q 보고서에 그 표가 있나, 반기·연간만 있나. 회사별 census(39사 × 2025.1Q~2026.2Q 6분기를 우선, CSM 시계열 범위 전체는 부차)를 만들어 "있음/없음/스캔본/구조 다름" 으로 센다. 빈 곳은 "원천 부재" 와 "우리가 못 뽑음" 을 구분한다(fitz 키워드 0회로 부재 단정 금지 — 렌더링 확인).
3. **항등식 시험(5개사)**: 대형 생보 1·대형 손보 1·PAA 비중 큰 손보 1·VFA 큰 생보 1·BS 와 가장 크게 어긋났던 회사(예: KB손보, 미래에셋생명)에서 **LRC(2-4 항목 8) + LIC = BS 보험계약부채(항목 20)** 가 닫히는지. 안 닫히면 차이가 보험계약자산(순자산 포트폴리오) 상계 때문인지 확인한다(2-4 합계는 포트폴리오별 순액이라 음수 BEL 행이 섞여 있다).
4. 위가 닫힌다면 **LIC = BS 항목 20 − LRC 로 총액만이라도 추정 가능한 범위**와 그 오차 크기.
5. 적재 계획 제안: 어느 출처·어느 표, 예상 작업량(회사×분기 수), 위험(단위·표 구조 변형), 우선순위. 마스터 신설이 필요하면 스키마 초안.

### 제약
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일로만(멀티라인 `python -c` 금지), 인코딩 명시. 맨 `python` 금지.
- **docling 사용 금지, 서브에이전트 금지**(RAM 15.5GB PC, 어제 5시간 멈춤 사고). 큰 파일은 스트리밍/부분 읽기.
- go.kr·KIPRIS 를 브라우저·WebFetch 로 열지 않는다.
- 보고서: `data/disclosure/_meta/lic_scout_20261010.md` (표 + 5개 질문에 대한 답 + 근거 파일·쪽). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

## 답변 (recipient 작성 — 처리 후)
정찰 완료(2026-10-10, parser-ifrs17 Sonnet, 토큰 536k·약 61분). 보고서 data/disclosure/_meta/lic_scout_20261010.md. 요지: 출처=DART XML 잔여보장·발생사고 변동 주석표(직접 159셀 중 123셀 BS 일치), 단일열 회사는 측정요소별 BEL·RA − 2-4 로 간접 도출, 비상장 15사 5분기 75셀은 원천 부재, BS−2-4 총액 추정은 DB손보·롯데·메리츠·하나손보 등에서 못 씀. 적재 티켓은 owner 결정(§6.6) 후 별도 발주.
