---
from: owner
to: designer
created: 20260614T0712Z
status: answered
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (sender 작성 — owner 라이브 사이트 QA) — HTML/표시 4건

**(1) K-ICS.html 회사 드롭다운 하드코딩 → 10개사+ 선택 불가** [glitch G3 코리안리 + G9 예별손보]
- `K-ICS.html` 회사 select 옵션이 lines ~109-139에 **하드코딩**(현재 29개사). JS 선택 로직(~lines 1393-1410)도 이 목록에서만 검색 → URL 파라미터로도 선택 불가.
- 데이터는 `kics_disclosure.json`에 멀쩡히 있음: 코리안리재보험(KR1000) 238건, 예별손해보험(KR0004, 구 MG) 다수(line ~150571).
- 누락 회사: 코리안리, 예별손보, AIG손해(KR0029), 카카오페이손해(KR1098), 서울보증(KR0150), AIA생명(KR0080), 교보라이프플래닛(KR1010), IBK연금(KR1011), 하나생명(KR0097) 등.
- 권장: 드롭다운을 `kics_disclosure.json`의 원수사명 목록에서 **데이터 기반 생성**(하드코딩 제거)하거나, 최소한 누락 전 회사 옵션 추가. 옵션 value는 json의 실제 "원수사명"과 일치("코리안리재보험" 등).

**(2) 현대해상 키컬러 오류** [glitch G5]
- `IFRS17.html` ~line 362 `KEY_COLORS`에서 현대해상 = `#008A3E`(진한 초록). 실제는 **살짝 주황빛 도는 노란색**. 현대해상 공식 브랜드 컬러로 교체(예: #FFB81C 계열 — 정확값 확인). 적용처: 워터폴 total 막대·라인 주선·select active.

**(3) CSM 민감도 표기 통일 + 흥국 테이블 + 억원 + 모바일** [glitch G4a]
- `IFRS17.html` ~line 949 헤더 "ΔCSM(백만)" → **"ΔCSM(억원)"** (실데이터는 억원).
- shock 컬럼 표기 제각각("3.27% 증가/상승/감소", "(-)3.27%", "10% 상승"…) → **"3.27%↑" / "3.27%↓"** 패턴으로 통일. (값 정규화는 sensitivity_heatmap.json 단계라 parser/ifrs17와 협업 — 그쪽 inbox에 흥국 product-line 행 분리 요청 올림.)
- 흥국생명: shock 컬럼에 건강/연금저축 등 product line이 혼입돼 테이블 깨짐 → parser가 행 분리 후 designer 표 정상화.
- 모바일: `@media(max-width:640px)` th/td 패딩 "4px 6px"(~line 65) → "6px 8px"+; 큰 억원 숫자 `white-space:nowrap; word-break:keep-all`.

**(4) 기본자본 소진율 100%+ 표시 (publishing 연계)** [glitch G2 display]
- `K-ICS.html` ~line 816에서 `Math.min(...,100)`으로 100% 캡 → 초과(예: KR1000 242.5%)가 숨겨짐. publishing이 tier1 overflow→tier2 가산 계산을 넣으면, donut에 "XXX%+" 표시 + "기본자본 초과 XXX억 → 보완자본 가산" 툴팁. publishing inbox와 한 세트.

## 답변 (recipient 작성 — 처리 후)

**designer, 2026-06-14 처리. 디자이너-단독 4건 완료, 상류대기 3건 ack.**

### ✅ (1) K-ICS 드롭다운 누락사 — 완료
- `K-ICS.html` 데이터 로드 `.then` 안에 `fillMissingCompanies()` 추가: 하드코딩 옵션에 없는
  `kics_disclosure.json` 원수사명을 전부 append(가나다순). JS 선택 로직이 `select.options`를
  검색하므로 옵션 추가만으로 URL/수동 선택됨.
- 검증(Edge dump): **옵션 30→48개**. 코리안리재보험·예별손해보험·AIG손해보험·카카오페이손해보험·
  서울보증보험·교보라이프플래닛생명보험 등 선택 가능 확인. 코리안리 URL파라미터 선택+테이블 렌더 OK.
- 하드코딩 전면 제거(완전 데이터화)는 기존 curated 순서 보존 위해 보류 → 후속 P2 cleanup.

### ✅ (2) 현대해상 키컬러 — 완료
- `IFRS17.html` `KEY_COLORS` 현대해상/현대해상화재보험 `#008A3E`(초록) → **`#FFB81C`**(노란주황, owner 제시값).
  밝은 색이라 WCAG 보정 자동 적용(선/축은 `keyColorOf.line`이 32% 어둡게, 막대 면적은 원색).
- 검증: 스와치 rgb(255,184,28), select 링 동일. **정확한 공식 브랜드 hex 있으면 한 줄 교체 가능.**

### ✅ (3a) ΔCSM 헤더 억원 — 완료
- `IFRS17.html` ~line 949 헤더 "ΔCSM(백만)" → **"ΔCSM(억원)"**. (값은 미분할, 헤더 라벨만. owner 라이브 QA 단위 신뢰.)

### ✅ (3d) 모바일 테이블 패딩/nowrap — 완료
- `IFRS17.html` `@media(max-width:640px)` th/td 패딩 `4px 6px`→**`6px 8px`** + `td.num,th.num{white-space:nowrap;word-break:keep-all}`(큰 억원 숫자 줄바꿈 방지).

### ✅ (3c) 흥국생명 product line 혼입 — parser 완료 확인
- parser가 `sensitivity_heatmap.json` 흥국생명보험 시나리오를 6행으로 정리(사망률·해지율·사업비및인플레이션율
  상승/하락) — product line 혼입 사라짐. designer 표 정상 렌더 확인(Edge dump).

### ✅ (3b) shock 컬럼 표기 통일 — designer 완료 (자유텍스트 display 파싱)
- parser가 shock을 구조화하지 않고 자유텍스트 유지("3.27% 증가" 등) → designer가 **display 레이어
  `fmtShock()`**로 통일: `{n}% 증가/상승`→`{n}%↑`, `{n}% 감소/하락`·`(-){n}%`→`{n}%↓`. 복합("2.62% 상승
  /0.26% 상승"→"2.62%↑ /0.26%↑")·비정형(가정변경효과 등)은 원문 보존(안전 degrade).
- 검증(Edge dump, 흥국생명): 사망률 3.27%↑/↓, 해지율 9.16%↑/↓, 사업비 2.62%↑ /0.26%↑. ΔCSM(억원) 헤더 OK.

### ⚠️ 검증 중 발견 → parser handoff (별개 데이터 버그)
- **푸본현대생명보험(KR0083)** sensitivity_heatmap 엔트리가 민감도표가 아니라 "기말 보험계약부채" 잔액표를
  오추출(shock 컬럼에 "7,095,833" 금액). designer 표시레이어로 못 고침 → **parser inbox로 reparse 요청**:
  `inbox/parser/20260614T1140Z__designer__KR0083_FY2024__sensitivity_misparse.md`.

### ⏳ (4) 기본자본 소진율 100%+ 캡 — publishing 대기 (owner 기제출)
- `K-ICS.html` ~line 816 `Math.min(...,100)`는 donut이 >100% 표현 못해서 둔 캡. publishing이 tier1
  overflow→tier2 가산 데이터 주면 designer가 "XXX%+" 도넛+툴팁 구현. owner가 이미 publishing inbox에
  제출(`20260614T0712Z__owner__MULTI__tier1_overflow_cascade.md`) — 그쪽 산출 대기.
