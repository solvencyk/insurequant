---
from: owner
to: designer
created: 20260616T0007Z
status: answered
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (sender 작성 — owner 라이브 QA 3차) — 표시/HTML 10건

**D1. CSM 민감도 표에 기준시점(as-of) 표기.** sensitivity_heatmap 각 사 entry에 rcept_no/period 있음(현재 대다수 FY2024 사업보고서=2024-12-31). 표 헤더/캡션에 "기준: FYxxxx 사업보고서(YYYY-MM-DD)" 명시.

**D2. 삼성생명 shock 이름 표준화 누락.** `fmtShock`가 삼성생명 "3.27%^" 류 형식을 못 잡아 표준화(↑/↓) 안 됨 → 패턴 보강(삼성생명 케이스 포함 재검).

**D3. CSM 민감도 테이블 소숫점 2자리 제거 → 억 단위 정수 반올림.** 음수 △(세모) 유지.

**D4. 현대해상 키컬러 더 주황으로.** 현재 `#FFB81C`가 너무 노람 → 주황 톤(예 #F47920/#FF7A00 계열, designer 판단). [이전 0712Z 건 후속.]

**D5. CSM waterfall — 분기공시 미제공사 처리.** 아이엠라이프 등 '분기' 선택 시 그래프 생략하고 **"분기공시 미제공사" 메시지만**. (미제공 판정 = master에 해당 사 분기 데이터 부재. master는 read-only로 판정만.)

**D6. CSM 시계열 그래프도 동일.** 위 미제공사는 **연 단위 그래프만**.

**D7. 시계열 축 윈도잉.** CSM시계열·신계약CSM배수: 상단 '분기' 선택 → **직전 5개분기**만, '연도' 선택 → **2023/2024/2025/2026.1Q**만 표시.

**D8. CSM 상각액 테이블 5년 초과 버킷 숨기기.** 큰 값 혼자 우뚝 서서 의미 희박 → 5년초과분 미표시.

**D9. 모바일: waterfall 등은 당년도/당분기만.** time series 너무 길어 모바일서 안 보임 → 모바일 뷰는 최신 1개 시점만.

**D10. IFRS17.html 진입 로딩 지연.** K-ICS.html은 무로딩인데 IFRS17.html만 약간 로딩 → 원인 진단(데이터 페이로드/렌더 차이)·경감.

검증: preview flaky → Edge headless `--dump-dom`+URL파라미터. master JSON read-only(데이터 변경은 parser 소관).

## 답변 (designer 2026-06-16 — 10건 전부 완료, IFRS17.html)

전부 표시 레이어(HTML/CSS/JS)만 수정, master·viz JSON 무수정. node --check 통과 + 헬퍼 단위테스트 + preview 라이브 검증(삼성생명·현대해상·아이엠라이프, 콘솔 에러 0).

- **D1** `asOfFromRcept(rcept_no)` 추가 → senCap "기준: FY2024 사업보고서 (2024-12-31)". 공시 각주(긴 caption)는 표 아래 muted로 보존. ※ 데이터 `period`/`as_of`가 null이라 rcept 제출월로 파생 — parser inbox `20260616T0030Z__…sensitivity_period_asof_null.md`로 정식 채움 요청(채우면 자동 fallback). 검증: 삼성생명 "기준: FY2024 사업보고서 (2024-12-31)".
- **D2** `fmtShock` 보강 — 부호·방향어 없는 선두 "3.27%"(상향충격)→**3.27%↑**, ^▲→↑/▼→↓. 검증: 삼성생명 "3.27%↑/↓", "3.40%↑(실손보상 2.62%)", "9.16%↑/↓".
- **D3** senTable `fmtNum(,0)`(0||2=2자리 버그) → **`samo()`**(정수 반올림+△). 검증: △3,765 / 3,298 / △10,684 (소수 제거, 음수 △).
- **D4** 현대해상 키컬러 `#FFB81C` → **`#F47920`**(주황). 검증: 스와치 rgb(244,121,32).
- **D5** 분기 미제공사(4Q-only, 데이터기반 11사: AIG·아이엠라이프·하나생명 등): 분기 모드 → waterfall 생략 + "분기 공시 미제공 보험사입니다…" 메시지. 검증: 아이엠라이프 분기모드 메시지 표시.
- **D6** 동(同) 미제공사 시계열은 연 단위 fallback(selectPeriods 연 분기).
- **D7** `selectPeriods` — CSM시계열·NB배수: 분기→직전 5분기, 연도→연말(4Q→연표기)+최신부분. 검증: 연도=[2023,2024,2025,2026.1Q], 분기=[2025.1Q..2026.1Q].
- **D8** 상각 차트: bucket 'y5_plus(5년 초과)' 제거 + yearly maxY 10→5. 검증: 삼성생명 amort=[1년이내,1–3년,3–5년].
- **D9** 모바일(≤640px): waterfall=최신 1버킷, 시계열=최신 1시점(selectPeriods isMobile 분기). 검증: 0폭 preview에서 hist 1시점.
- **D10** boot 9개 JSON 직렬 await → **Promise.all 병렬** + "데이터 불러오는 중…" 힌트. (원인=직렬 9 round-trip; K-ICS는 1파일이라 무지연.)

push 안 함(designer는 추천만). status: answered.
