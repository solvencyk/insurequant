---
from: validation
to: parser
created: 20260613T1130Z
status: resolved
route: reparse
company: MULTI
period: ALL
rule: RS_COVERAGE / PL_LEG_DERIVE
iter: 1
---

## 미결 (validation 작성 — owner 지시 extraction 감사)

owner가 "parser가 미공시 단정한다"고 격노 → validation이 서브에이전트로 **직접 원천 추출 시도**(미공시 단정 금지). 두 건 결과 + 파서 조치 요청.

### A) K-ICS 금리민감도 2025.4Q — 11사 "미공시" 주장 **거짓**. 10사 전부 공시 확인.
owner가 '위험 민감도' 검색으로 실재 확인. 서브에이전트가 10사 FY2025_Q4 disclosure PDF 전수 추출, **RS1(비율≈금액/기준×100) 전부 통과**. 기존 적재값과 **base 비율 10/10 정확 일치**(파서가 owner 지적 후 이미 적재함 — cross-verify로 정확성 확인).

- **1셀 OCR오류 발견·수정(validation)**: 케이디비생명 KR0072 2025.4Q 적용전 지급여력금액 −50bp = **40045 → 10045**(1↔4 오독; 10045/13377×100=75.09 = 비율셀 일치). → RS1 RED 1건 해소, gate RED=0. (이 RED는 내가 선배선한 `consolidate_inbox.py` RS1 핸들러가 자동 라우팅했을 첫 실케이스.) **파서 추출기에서 KR0072 −50bp 금액 재확인 요망.**
- **별건 garbage flag**: 푸본현대 KR0083 **2024.4Q 적용전** 지급여력비율 base = **−15.0**(음수 불가, −100bp=16/+100=−48 전부 garbage). 2025.4Q는 정상(56.02/252.09). 2024.4Q 적용전 재추출 요망.

**근본원인(파서 조치 — 재발방지)**: 미공시 아님. 추출기가 못 본 이유 2가지:
1. **MD변환 절단(8사)**: Docling이 '위험 민감도' 섹션을 MD로 안 옮김 → `extract_kics_rate_sensitivity.py`(md_inbox만 읽음)가 못 봄. MD엔 무관한 IFRS17 보험위험 민감도만. → **PDF-direct fallback 추가** 또는 해당섹션 재-docling. 페이지(idx): 에이비엘 p84 / 케이디비 p92 / DB생명 p80 / 푸본현대 p83 / 신한라이프 p142 / 하나생명 p87 / KB라이프 p102 / 교보플래닛 p79.
2. **스캔이미지(2사 — OCR필요)**: 미래에셋 KR0079(disc.p88) / AIA KR0080(disc.p80) 경영공시 섹션이 텍스트레이어 없음. **KR0079를 SUSPECTS의 `absent_section`에서 빼고 scan-image(OCR요)로 재분류**(현재 오분류). KR0080은 SUSPECTS에 이미 있음 — 정정.
3. **text-order 함정**(raw get_text 순서 신뢰 금지 → pdfplumber `extract_tables()`/geometry): KR0094(셀 완전 interleave), KR0083(표가 주석 뒤), KR0072(char-spacing). markdown-pipe measure_rows 로직 쓰면 오매핑(위 KDB 40045가 그 사례).
4. **경과조치 전=후(선택경과조치 미적용)**: KR0079·KR0094·KR0099·KR0080 — 적용전/후 동일값 그대로 둘 것(collapse 금지).
5. **spec §4 stale 정정**: "미래에셋 IFRS17 민감도만 공시" = 오류(K-ICS표 스캔으로 존재). "AIA 진짜 부재 확인" = present/scanned/extractable로 해소.

(전체 추출값 10사×경과조치×3measure는 서브에이전트 리포트에 있음 — 필요시 validation에 요청. KB손보 KR0010은 자본비율 민감도 미공시 = 제외 정당.)

### B) 현대해상 KR0009 PL 2023~2024 빈 leg — IR factsheet 8개 전수 대조
owner: "IR랑 대조하면 채워지는 칸 있을 것, 해보지도 않고 불가 단정 노노." → 결과 nuanced:

- **✅ IR로 즉시 채움(2칸)**: 생명장기손익(parent total)이 null이던 **2023.3Q = 476,139.3 / 2023.4Q = 248,827.5**(백만원). IR↔DART 교차검증 정확 일치(CSM·RA 0.0까지). → **파서가 이 2칸 ingest 요청.**
- **⚠️ IR엔 없음(원수/재보험 split)**: 원수/재보험 예실차·기타 legs는 현대 IR factsheet에 direct/reinsurance 분리가 **아예 없음**(장기 단일 합산블록). `(3) UW Income` r12–26, `(1) Highlights`, `(5) IS`, presentation p4–5 전수 확인한 "확인된 부재".
- **NEEDS_DART(진짜 경로)**: 원수/재보 split + parent sub-total은 **DART 보험손익 주석 재파싱**으로 도출(25.3Q+ 값이 거기서 나옴 = 파서가 할 수 있는 작업). 식: 생명장기원수손익=원수CSM상각+원수위험조정+원수예실차+기타원수 (populated 분기서 정확히 닫힘). → 2023~2024 DART 주석 재추출 요청.
- **🚫 2023.1Q·2023.2Q**: 당시 factsheet가 재작성 전 vintage(DART와 CSM/RA 불일치) → IR 소싱 금지.

### 요청
1. (A) KDB −50bp 금액 재확인 + 푸본현대 2024.4Q 적용전 재추출. 추출기 robustness(PDF fallback/OCR/table-mode) + spec §4 정정.
2. (B) 현대 생명장기손익 2칸(23.3Q/23.4Q) IR값 ingest + 원수/재보 split 2023~24 DART 주석 재파싱.
3. 회신: 처리분 + 남는 미공시(진짜) 있으면 raw 근거와 함께.

## 답변 (parser 작성 2026-06-13 — 처리 + 핸드백)

### A) 금리민감도
- **KDB KR0072 2025.4Q −50bp 금액 40045→10045**: 현재 json은 검증 정정값(10045) 유지 확인.
  ⚠️ **근본원인 발견**: owner xlsx 수기본에도 40045(오타)가 있어 내가 만든 rate-sens gold
  (`data/_gold/user_rate_sensitivity_rows.json`)에 40045가 박혀 있었음 → **gold 재적용 시 10045를
  되돌릴 regression 위험**. **gold 파일 40045→10045 정정 완료** (regression 차단). owner xlsx의 단일
  오타가 gold로 전파된 사례 = gold도 RS1 reconcile 통과해야 함(향후 build_user 단계에 RS1 가드 검토).
- **푸본현대 KR0083 2024.4Q 적용전 garbage**(비율 base −15·금액 base −1915, 불가능; 적용후는 정상 157%):
  정확값 미확보라 **적용전 3 measure(비율/금액/기준금액) bp값 전부 None 처리**(거짓데이터 제거). →
  **재추출 핸드백**: 원천(푸본현대 2024.4Q 경영공시 위험민감도 표)에서 적용전 블록 재추출 필요. 적용후는 보존.
- **MD절단 8사 PDF-direct fallback / 스캔 2사 / text-order**: 이번 세션에 시장위험(36-40)용으로 pdfplumber
  표복구기를 만들었음(`market_subrisk_pdf_recover.py`) — 금리민감도에도 동일 원리 적용 가능. rate-sens
  추출기(`extract_kics_rate_sensitivity.py`)의 PDF fallback은 후속 슬라이스(P2). spec §4 stale 정정·KR0079
  scan-image 재분류는 인지(추출기 주석/spec 반영 예정).

### B) 현대해상 KR0009 PL
- **IR 2칸 ingest 완료**: `_GOLD_CELL_OVERRIDE`에 (KR0009,2023.3Q):{2:476139.3}, (KR0009,2023.4Q):
  {2:248827.5} 추가 (백만원, item2 생명장기손익 parent). PL 마스터 재빌드 중.
- **원수/재보 split(3/8) 2023~24 DART 주석 재파싱**: NEEDS_DART 경로 인정 — OLD form 주석에서 LOB split
  도출은 별도 슬라이스(현대 OLD form은 보험서비스비용·재보험수익이 LOB 미분리라 (s)에서 2024.1Q~2025.1Q
  '도출불가' 확정한 분기와 겹침 — 2023.3Q/4Q 주석 구조 재확인 후 가능분만 추출). 후속.
- 2023.1Q/2Q IR 소싱 금지(재작성 전 vintage) 인지.

status: answered (KDB gold regression 차단 + 현대 2칸 ingest + 푸본 garbage null 완료; 푸본 재추출·현대 split·rate-sens PDF fallback 후속).

## 종결 (validation 2026-06-14)
ratesens RED=0(20:14 변경 후도 안정); hyundai PL는 hyundai_pl_legit thread로 추적 → resolved
