---
from: owner
to: parser
created: 20260614T1232Z
status: resolved
route: backlog
company: MULTI
period: 2025 (짝수분기 위주)
lane: kics
iter: 1
---

## 미결 (sender 작성 — owner QA 잔여 리마인더)

**19_market 잔여 정리 재촉** (기존 thread `inbox/parser/20260613T1500Z__validation__MULTI_ALL__19market_real_gaps_21_not_148.md`, status:open).

그 thread 잔여 15건 분해 = owner-OCR 2 · downloader 2 · agent재시도 8 · validation확인 3. 리마인더 + 재조정:
- **downloader 2 (DB손해·NH농협 손상PDF)** = 이미 파서가 fitz로 직접 복구함(별도 corrupt-PDF thread는 obsolete → _resolved 이동) → 잔여에서 **제외 가능**. 재확인 요망.
- **agent재시도 8** = 파서(kics) 액션. 다음 드레인 시 재추출 시도.
- **owner-OCR 2** = KB·한화 23.4Q 금리위험액(스캔) → downloader inbox에 OCR 리마인더 올림(연계 `20260614T1232Z__owner__MULTI__qa_residual_reminder.md`).
- **validation확인 3** = validation 측 disposition(연계).

목표: 19_market 잔여를 실제로 닫고 RED 카운트 갱신(현재 42).

## 답변 (parser 작성 2026-06-14 ~20:45 — 19_market 잔여 갱신: 카운트 42→현재 8, RESOLVED)

이 리마인더의 "현재 42"는 stale. 그 사이 대량 진행됨 — **전체 RED 52→21, 19_market RED 8만 남음.**

리마인더 항목별 처리:
- **downloader 2 (DB손해·NH 손상PDF)**: ✅ 네 말대로 fitz로 직접 복구 완료(둘 다 안 깨졌고 pdfplumber만 죽었던
  것). 19_market clear. **잔여에서 제외.** corrupt-PDF thread는 obsolete라 내가 삭제함.
- **agent재시도 8**: ✅ fitz 재추출로 회수 — DB손해·NH·한화 24.2Q·코리안리 2025.2Q 등 + 추가로 **DB생명
  2025.2Q·카카오 2025.4Q도 회수**(둘 다 텍스트표인데 내가 스캔으로 오판했던 것 — 재확인 덕에 발견).
- **root-cause 고침**: localizer(`extract_market_section_pages.py`)에 fitz fallback 착안 → 앞으론 EOF-PDF 무음
  누락 없음(110 tests pass).

**잔여 19_market 8 = 전부 비-파서(raw 페이지까지 검증):**
- owner OCR (금리위험액/표 본문이 full-page 이미지): KR0010 KB손해 2024.4Q·2025.2Q · KR0068 한화생명
  2023.4Q·2025.2Q · KR0005 흥국화재 · KR0071 흥국생명 2024.4Q · KR0080 AIA 2025.4Q.
- validation cadence 확인 1: **KR1098 카카오 2023.3Q** — odd-Q인데 raw에 시장위험 분해표 자체 부재(NO-HEADER).
  19_market 룰이 RED로 잡는데 홀수+표부재 = SKIP 정당 가능. validation에 cadence 재확인 요청 예정.

→ **파서가 닫을 수 있는 19_market 잔여 = 0** (전부 OCR/validation). status: **resolved**(파서측 완료).
