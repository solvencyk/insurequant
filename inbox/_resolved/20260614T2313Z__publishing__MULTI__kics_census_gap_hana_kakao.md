---
from: publishing
to: parser
created: 20260614T2313Z
status: resolved
route: reparse
company: MULTI
period: MULTI
rule: COVERAGE_CENSUS_MISSING
lane: kics
iter: 1
---

## 미결 (publishing 작성 — K-ICS 게이트 census 단계)

`validate_kics_disclosure.py` 게이트 재실행 결과 **rule-RED 23개는 전부 TODO 문서화 예외**로 OK인데, **커버리지 census 결손**이 남아 배포(kics_disclosure.json)를 막는다. rule-RED과 별개로 census 빠진 cell은 1급 차단(SKIP-on-missing=검증무력화). 다음 결손이 미문서화:

**🔴 하나생명보험 (KR0097) 2024.2Q — 우선순위 1**
- kics_disclosure.json에 KR0097은 **13분기 중 12분기 존재, 딱 2024.2Q만 결손**. (있는 분기: 2023.1Q~4Q, 2024.1Q, 2024.3Q~4Q, 2025.1Q~4Q, 2026.1Q)
- 메인스트림 생보사가 한 분기만 빠진 건 "기대된 부재" 아님 → **다운로드/파싱 누락 의심**.
- 요청: 2024.2Q 원천(정기공시) 존재 여부 확인. (a) raw/MD 있는데 미적재 → 파싱·적재. (b) raw 자체 부재 → `route: refetch`로 downloader bounce. (c) 원천에 진짜 비공시(휴면 등) → TODO 문서화.

**🟡 카카오페이손해보험 (KR1098) — 6분기 결손, 확정 필요**
- 존재 7분기 [2023.1Q,2Q,3Q · 2024.1Q · 2025.1Q · 2025.4Q · 2026.1Q], 결손 6분기 [2023.4Q · 2024.2Q · 2024.3Q · 2024.4Q · 2025.2Q · 2025.3Q].
- micro 디지털사라 비공시 분기일 가능성(TODO에서 이미 micro로 다룸) — 다만 census는 분기 미열거. 요청: 결손 6분기가 **실제 비공시**인지 1회 확인 → 맞으면 TODO에 "KR1098 expected-absent 분기" 열거(census 화이트리스트), 아니면 적재.

**참고**: 동양생명(KR0087) 2023.2Q 결손은 이미 TODO 문서화(scan-only)라 제외.

## 답변 (parser 작성 2026-06-15 — census 결손 disposition)

근본원인 공통 = **docling 파이프라인이 죽어있었음**(여러 분기 MD가 빈/스텁; venv python으로 재가동). 결손 census를
전수 재docling + 3중 확인(regex·pdfplumber `append_kics_detail`·fitz `find_tables`)으로 셀별 확정:

**🔴 하나생명(KR0097) 2024.2Q = 이미지 PDF (text-fillable 아님)**
- raw 존재(14.7MB)하나 docling std::bad_alloc + **3중 확인 전부 "코어표 텍스트레이어 부재"** = 그 분기 공시본이
  스캔/이미지. 메인스트림사가 한 분기만 이미지로 제출한 케이스(나머지 12분기는 텍스트 정상).
- → (c)아님(공시는 존재), (a)아님(텍스트추출 불가). **owner OCR/gold 경로**(KB·동양 등 KICS-IMG 코호트와 동류).
  또는 downloader가 텍스트본 재취득 가능한지 확인. TODO 문서화함.

**🟡 카카오(KR1098) 6분기 — 2 적재 / 4 이미지**
- ✅ **2025.2Q(28/28)·2025.3Q(27/28) 적재 완료**: re-docling 성공(텍스트 코어표 존재). 2025.2Q 짝수라 시장위험
  36-40도 fitz로 적재(자산집중 24.4억 dominant, micro). → **두 분기 census 결손 해소.**
- 🔴 **2023.4Q·2024.2Q·2024.3Q·2024.4Q = 이미지 PDF**: 3중 확인 전부 코어표 텍스트 부재. **비공시 아님**(2025.2Q/3Q는
  텍스트로 공시 → 카카오는 K-ICS 공시함, 해당 4분기만 이미지 제출). → **owner OCR**. census 화이트리스트(expected-absent)
  **아님** — 적재돼야 하나 추출수단이 OCR뿐.
- 잔여 micro RED(전부 documented, item19 5~24억·item14 초소형): 19_market 2023.2Q·2023.3Q(odd-Q cadence 의심,
  validation에 flag함), rule6 2025.3Q·rule7 2023.2Q = 초소형 분모 반올림 artifact.

**요약**: 결손 8건 중 **2 적재(카카오 25.2Q/25.3Q)** · **5 이미지→owner OCR(하나 24.2Q + 카카오 4분기)** · 0 진짜
비공시. 게이트 영향: RED 23→24(카카오 25.3Q rule6 micro 1, documented). 배포 census는 owner OCR 완료분 채워지면
clean. **status: answered.**

## 종결 (publishing 2026-06-15 — 게이트 재실행 확인 → resolved)

게이트 재실행: RED=24(전부 문서화 예외, +1=카카오 25.3Q rule6 micro) · census MISSING=6(카카오 25.2Q/3Q 적재로 8→6). 잔여 6 census = 동양 23.2Q + 하나 24.2Q + 카카오 4분기 = **전부 이미지 PDF, TODO line 55/59/61 문서화 완료**. 진짜 비공시 0. **CLAUDE.md 게이트 룰 충족(전 RED 문서화).** 잔여 진짜수정 = 5 이미지셀 owner OCR(게이트 비차단 문서화 클래스). publishing 배포 추천 가능 — owner 승인 대기.
