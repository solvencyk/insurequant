---
from: owner
to: parser
created: 20260610T0100Z
status: answered
route: reparse
company: ALL
period: ALL
rule: KICS_RATE_SENSITIVITY_NEW
iter: 1
---

## 미결 (sender 작성)

**신규 feature: K-ICS 지급여력 금리민감도 추출** (owner 발주 2026-06-10).
경영공시 `## 6-8. 위험 민감도` → `금리 민감도 분석` 표 (경과조치 × measure × ±50/±100bp).

스펙 정본 (스키마·변형 카탈로그·엣지케이스 전부): `docs/agents/kics-rate-sensitivity-spec.md`

작업:
1. `scripts/extract_kics_rate_sensitivity.py` 작성 — `md_inbox/FY*/*.md` 전 분기 스캔
   (분기당 다중 파일이면 `_amended` 접미사 최다본 사용).
2. 산출: 루트 `kics_rate_sensitivity.json` (스펙 §2 스키마, prefix는 kics_disclosure와 동일)
   + `data/_derived/kics_rate_sensitivity_diag.json` (per-(사,분기) status census, 스펙 §4).
3. 핵심 주의 4가지:
   - **delta 인코딩 (흥국생명·흥국화재 FY2025_Q2)**: shock 셀이 base 대비 변화량(`△11.3`).
     absolute = base + delta 변환 필수 (스펙 §3). 미변환 시 RS1 검증에서 RED.
   - 경과조치 라벨 4변형 (세로분할 `경 과`/`조`/`치 전` 포함) — 공백 제거 후 매칭.
   - 적용후 all-dash/blank → rows 생략 + diag `post_dash`. identical은 그대로 포함.
   - KR1098 OCR char-spacing (`지급여력기 준 금액`, `100 b p △`) + verbatim 행 중복 — 토큰 정규화 + dedup.
4. **절단/오선택 의심 3건 원본 PDF 대조**: AIA(KR0080) MD가 4.5절에서 끝남(섹션 미수록 vs 변환절단?),
   KB손보(KR0010) FY2025_Q4 서브표 부재 주장, BNP(KR0075) FY2025_Q4 IFRS-형식 문서만.
   raw: `data/disclosure/FY*/raw/`. 변환 절단이면 재-docling, raw 문제면 `inbox/downloader/`로 refetch.
5. FY2023~FY2024_Q3 부재는 정상(공시서식 도입 전) — RED 아님, diag `absent_section`로만.

완료 기준: 마스터+diag 생성 → validation에 `answered` 회신 (검증 룰은 별도 메시지로 validation에 발주됨).
추출기 작성 후 **rebuild-diff 게이트 관행 적용** (blast-radius 확인 후 land).

## 답변 (recipient 작성 — 처리 후)

**완료.** `scripts/extract_kics_rate_sensitivity.py` 작성 → `kics_rate_sensitivity.json` (**416행**, 74 사·분기) +
`data/_derived/kics_rate_sensitivity_diag.json` (status census). 기존 마스터 무변경.

**자기검증:** RS1(비율≈금액/기준금액×100) **전 블록 통과(rs1_fail 0)**. RS2(적용전 base vs kics_disclosure
item1/14/27) 전수 **215 OK / 1 diff(KR0011, basis 차이)**. 스키마는 §2 그대로(컬럼 재배열·prefix 복사).

**스펙 4대 주의 처리:**
1. **delta(흥국생명·흥국화재 FY2025_Q2):** absolute 1차 파싱 → RS1 실패 시 `base+delta` 재해석 → 재검증 (스펙 §3 방식). FY2025_Q2/Q4 둘 다 `delta_converted`로 정상 변환. (흥국화재 적용전 비율 base 175.77, △100bp −6.98 → absolute 168.79, RS1 OK.)
2. **경과조치 4변형(세로분할 `경 과/조/치 전` 포함):** 블록 col0 frag 합쳐 norm 후 전/후 판정. 삼성생명 풀라벨·메리츠 세로분할 모두 처리.
3. **적용후 all-dash → rows 생략 + `post_dash`(6건):** 신한이지·하나손보·삼성생명 등. identical(전=후 동일)은 있는 그대로 포함(메리츠).
4. **KR1098 OCR:** char-spacing(`지급여력기 준 금액`,`100 b p △`) norm 매칭 + verbatim 중복블록 dedup. extracted 정상.

**추가 처리:** 동양생명 6컬럼/빈줄분할 표(섹션 내 다음 헤딩까지 전 | 줄 수집으로 수정).

**절단/오선택 3건 raw-PDF 대조 (요청 4):**
- **AIA(KR0080):** PDF 493p에 K-ICS 금리민감도표 **부재**(민감도 페이지는 IFRS17 보험위험 민감도). + AIA는 `kics_disclosure.json`에 회사 자체 부재. → **진짜 부재**(MD 4.5절 절단과 무관 — PDF에도 표 없음). K-ICS 마스터 누락은 별개 이슈로 owner 확인 권장.
- **KB손해(KR0010) FY2025_Q4:** PDF 136p에 "민감도" **0페이지** → **진짜 부재** 확정(서브표 부재 주장 맞음).
- **BNP(KR0075) FY2025_Q4:** PDF **page 75에 "6-8 위험민감도 → 2) 금리 민감도 분석 → △100bp" 표 존재**하나 MD 미반영
  = **변환누락 → 재-docling 필요**. → `inbox/downloader/20260610T0830Z__parser__KR0075_2025.4Q__redocling.md` 발송.
  재-docling 후 동일 스크립트 재실행으로 흡수.

**FY2023~FY2024_Q3 부재:** 정상(서식 도입 전), diag `absent_section`.

**완료 기준 회신:** validation에 마스터 ready + RS1–4 룰 발주 안내 = `inbox/validation/20260610T0830Z__parser__ALL__rate_sensitivity_master.md`.
rebuild-diff 게이트: 신규 마스터(직전 버전 없음)이므로 회귀 대상 무 — RS1/RS2 자기검증으로 갈음.
