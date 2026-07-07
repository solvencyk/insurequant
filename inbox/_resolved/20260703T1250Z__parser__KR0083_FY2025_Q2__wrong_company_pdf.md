---
from: parser
to: downloader
created: 20260703T1250Z
status: resolved
route: refetch
company: KR0083 (푸본현대생명보험)
period: 2025.2Q
lane: kics
iter: 1
---

## 미결 (parser/kics → downloader)

**FY2025_Q2 KR0083 슬롯에 엉뚱한 회사 PDF가 들어가 있음 = KR0075(비엔피파리바카디프생명) 것.**

- 현재 파일 `data/disclosure/FY2025_Q2/pdf/KR0083_푸본현대생명보험.pdf`
  (MD frontmatter: source_sha256 `cac1fc63dd80bdcd9071ed758a5bd50523d8b5c09e256cbaf7604dde9fb0b5bc`, source_size 2,631,258)
  의 내용은 **푸본현대가 아님**:
  - 이 PDF: 총자산 26,319억(2.6조)·보통주 2,763억·특별계정(변액) 11,130억(42%)·지급여력비율 318.16%·SCR 685억.
  - 진짜 푸본현대(25.1Q/25.3Q/25.4Q 및 25.3Q MD의 25.2Q 컬럼): 총자산 **180,009억(18조)**·보통주 15,456억·특별계정 220억·지급여력비율 **−10~56%(자본잠식)**·SCR ~13,000억.
  - 전 항목이 **KR0075 비엔피파리바카디프 25.2Q 데이터와 정확히 일치**(318.25%·보통주 2763·SCR 685). → KR0075 반기보고서가 KR0083 슬롯에 잘못 저장됨.
- KR0075 자체 슬롯(`.../KR0075_...`)은 정상(자기 데이터). KR0083만 오염.

**요청:**
1. **올바른 푸본현대생명(KR0083) 2025.2Q 반기보고서 PDF 재취득** → `data/disclosure/FY2025_Q2/pdf/KR0083_푸본현대생명보험.pdf` 교체(현재 KR0075 것 덮어쓰기). DART 반기보고서 or 정기경영공시 K-ICS 절.
2. 재취득 확인 anchor: 지급여력비율 **≈ −10%(적용전) / ≈ 165%(적용후)**, SCR ≈ 13,039억, 보통주 15,456억, 총자산 ≈ 176,770억이면 올바른 PDF.
3. **점검 요망 — 동일 오슬롯팅이 다른 (회사×분기)에도 있는지**: 이번은 KR0075→KR0083 FY2025_Q2. 2026-06-10 `redocling_bounce`(KR0075, KR1000) 처리 이력과 연관 가능. FY2025_Q2 전후 배치의 KR0075/KR0083 인접 코드 재확인 권장.

**parser 후속(재취득되면):** `run_harness --stage parse --period FY2025_Q2 --companies KR0083` 재docling → `fill_period/subitems/market_subitems/irr` 재실행 → sub-risk 29-46 복원 → 게이트에서 KR0083 25.2Q 19_market RED 해소.

## 답변 (downloader 작성 — 처리 후)

완료 확인. PDF 교체(20260705T0300Z 응답) → parser 재파싱까지 끝난 상태 재확인:
- `kics_disclosure.json` KR0083 2025.2Q에 items 1-46 전부 적재 확인(29-46 sub-risk 포함, item27전=-10.13/후=164.88).
- `scripts/validate_kics_disclosure.py` 재실행 → KR0083 2025.2Q 관련 RED 없음(19_market 등).

`inbox/parser/20260705T0300Z__downloader__KR0083_FY2025_Q2__correct_pdf_ready.md`도 함께 resolved 처리.
