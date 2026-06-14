---
from: owner
to: parser
created: 20260612T0900Z
status: open
route: backlog
company: ALL
period: ALL
rule: BACKLOG_DIGEST
iter: 1
---

## 미결 (sender 작성)

**owner 백로그 다이제스트 (2026-06-12 전수 점검).** 상세는 `TODO_parser.md` + 아래 신규 2건.

### 🔴 신규-1 — 시장위험 하위(item36-40) 추가 backfill (owner xlsx 작업 중 발견)

owner가 md_inbox 전수 스캔(`scripts/_probes/_scan_market_subs_source.py` 실행 재현 가능):
**소스 MD에 5종 세부표(자산집중위험 행) 있는데 JSON 미적재**인 (사,분기) — Phase-2가 놓친 잔여:

- 하나손해(KR0050): 2024.1Q~2025.4Q **8분기** — 표가 `<!-- image -->`로 분단된 레이아웃
  (FY2025_Q4 MD 578~588행: 시장위험액 76,839 | 금리 30,358 / 주식 62,491 / 부동산 2,643 / 외환 12,483 / 자산집중 5,251, 백만원)
- 현대해상(KR0009): 2023.4Q, 2024.2Q, 2024.4Q, 2025.2Q, 2025.4Q (concat-cell 회사)
- 삼성화재(KR0008): 2023.2Q, 2023.4Q, 2024.2Q, 2025.2Q / 메리츠(KR0001): 2023.4Q, 2024.2Q, 2025.2Q
- DB손해(KR0011): 2023.4Q, 2024.2Q, 2025.4Q / 코리안리(KR1000): 2023.4Q, 2024.4Q, 2025.2Q, 2025.4Q
- 악사(KR0049): 2024.2Q, 2024.4Q, 2025.2Q, 2025.4Q / NH농협손보(KR0032): 2023.4Q, 2024.2Q
- AIG(KR0029) 2025.4Q / 신한이지(KR0051) 2025.2Q / 서울보증(KR0150) 2025.4Q / 카카오페이(KR1098) 2023.3Q, 2025.4Q

도구: `fill_market_subs_from_pdf.py`(words-coordinate 전략 추가 = TODO_parser Phase-2 잔여와 동일 축)
또는 MD 분단표 합치기. **게이트: 19_market 행렬합 rel<2%** 통과분만 적재. 생보도 동일 스캔 후 일괄 권장.

### 🔴 신규-2 — 생보 경과조치 적용후 요구자본(item14후/15후) 적재 (owner xlsx #3 블로커)

경과조치 적용사(후 비율≠전 비율 공시)인데 item14후 미적재 + item15후 유도값이 공시 비율과 불일치하는
생보 20건 — **원천 MD [경과조치 전|후] 표에서 item14후(나.지급여력기준금액 후)를 직접 적재**해야 함:
- ABL(KR0070): 2025.1Q/2Q/4Q · 푸본현대(KR0083): 2023.3Q~2025.3Q 9개 분기
- iM라이프(KR0076): 2024.4Q~2025.4Q 4개 분기 · IBK연금(KR1011): 2025.4Q
- 농협생명(KR0104): 2024.4Q, 2025.2Q, 2025.3Q
(이들은 item15후−22+23 유도가 공시 item27후와 5%p+ 어긋남 — 22/23 후값 차이 의심. 검증식:
적재 후 `(2후+3후)/14후×100 ≈ item27후` ±0.6%p.)
추가 확인 6건(적용사인데 14후·15후 둘 다 없음): 한화생명 2025.2Q / 삼성생명 2025.1Q / 동양 2025.2Q /
iM 2023.1Q / 처브 2024.3Q. 완료 시 owner가 xlsx 채움 마무리함.

### 🟠 기존 잔여 (TODO_parser ID 참조)
- V9 큐: 메트라이프 영업이익 등식 2분기 / 코리안리 crosscheck 2F(상각 1y lag 의심) / 동양 2025.3Q zleg /
  현대 예실차 2분기·롯데 2025.2Q·악사 zleg 핸들러 / 아이엠라이프 배수 정식 빌더 핸들러
- V7 큐: 롯데 FY2025 NB 구성요소 표 capture / **history 빌더 off-by-one-year 회귀 수정 후 재빌드** /
  한화손해 2025.1Q NB stale carryover
- PL Tier-2: 동양(2024.x)·케이디비(2025.x) 재보 CSM상각/RA / 하나생명 투자손익 / 교보플래닛 legit-absent 확인
- **FY2026_Q1 K-ICS PDF→MD docling** (`data/disclosure/FY2026_Q1/raw/` → md_inbox) → 금리민감도·시장하위
  추출기 재실행으로 흡수
- 🟢 low: IRR 직접형 15건 별도 스키마 / KB손해 image-only OCR 경로 / 삼성생명 FY23 구판 factsheet 레이아웃

### ⏸ owner 결정 대기 (작업 금지, 재상기용)
- 코리안리(KR1000) FY2025 CSM basis A/B (escalated `20260609T0200Z`)
- MLG-1 듀레이션 유도식 / MLG-2 금리위험액 유도규칙

## 답변 (parser 작성 2026-06-13 — 신규-1 처리, 나머지 큐잉)

- **신규-1 (시장위험 36-40) — 대부분 처리**: `extract_mkt_subs` 전면 재작성(분절표 봉합 + enumerator/액
  변형 + 값셀탐색) + IRR total→item36 저장 버그 수정. **item36 214→281, all-five 90→103.** 하나손해
  8분기(분단표)·삼성생명(라벨변형) 회수. concat-cell 손보(현대/메리츠/삼성화재/DB)는 item36(금리위험액)만
  공시 = G36_ONLY 적재(37-40은 별도 미분해 가능성 — `market_subrisk_pdf_recover.py` PDF 증거 census로
  확정 중). 상세: changelog (t), inbox 20260611T2200Z answered.
- **신규-2 (생보 item14후/15후) — ✅ 완료(2026-06-13)**: fill_post 두 버그 수정(전=후 스킵이 14후 누락 +
  서술문 오분류로 처브 공통표 제외). 경과조치 적용사 코어 {1,2,3,14,27} 동일값도 적재. **검증식 25/25 통과**,
  rule 8_post 해소. inbox 20260613T2030Z. (15후는 이미 적재돼 있었고 14후 부재가 유도불일치 원인이었음.)
- **기존 잔여**: FY2026_Q1 docling은 (s)에서 완료(36/39사). 나머지 V9/V7/PL-T2 큐 유지.
- ⏸ owner 결정대기 건은 작업 안 함.

### 갱신 (2026-06-14) — 신규-1 (시장위험 36-40) 종결

신규-1 잔여 + 짝수분기 19_market/36_irr RED 전수를 reconcile-gated 워크플로우로 재추출(2회전). **파서로 닫히는
RED=0**으로 확정 — 잔여는 전부 비-파서(downloader 손상/no-source/re-docling, owner OCR image-only, 내부모형
narrative, 비표준 IRR, 삼성생명 odd-Q MD불일치). +10행 적재(한화 24.2Q item36+IRR + 검증된 0), 게이트
RED 52→52 무변동. inbox 라우팅 완료(owner 2025.4Q thread resolved, validation 19_market·36_irr answered,
downloader+validation 신규 발주). 상세: changelog_parser_kics 2026-06-14 top.

status: open 유지 (digest — 신규-1 종결, 신규-2 완료(2026-06-13), V9/V7/PL-T2 등 잔여).
