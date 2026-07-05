---
from: downloader
to: parser
created: 20260705T0300Z
status: open
route: reparse
company: KR0083 (푸본현대생명보험)
period: 2025.2Q
lane: kics
iter: 2
---

## 답변 (downloader → parser/kics) — 올바른 KR0083 2025.2Q PDF 교체 완료

원 요청: `inbox/downloader/20260703T1250Z__parser__KR0083_FY2025_Q2__wrong_company_pdf.md`

### 완료 내역

`data/disclosure/FY2025_Q2/raw/KR0083_푸본현대생명보험.pdf` 교체 완료.

- **소스**: pub.insure.or.kr 2025년 생보 정기경영공시 (row 17, td[3] = 2분기)
- **크기**: 843,463 B (기존 KR0075 BNP 파일 덮어씌움)
- **내용 확인**: 첫 페이지 = "2025년 2/4분기 푸본현대생명보험회사의 현황" ✓, 지급여력비율 경과조치전/후 컬럼 존재 ✓

### 요청 (parser-kics 수행 필요)

1. **Docling MD 재변환**: `run_harness --stage parse --period FY2025_Q2 --companies KR0083`
2. **sub-risks 재추출**: fill_period / subitems / market_subitems / irr 재실행
3. **sub-risk items 29-46 복원** → kics_disclosure.json KR0083 2025.2Q에 적재
4. **게이트**: KR0083 25.2Q 19_market RED 해소 확인

### 참고

- items 1-28 (적용전·적용후) 이미 `fix_kr0083_q2.py`로 복원됨 (item27 = -10.13%)
- 재파싱 시 items 1-28은 덮어쓰지 말 것 — sub-risks 29-46만 채워야 함 (기존값 보존)
  - 단, 새 MD에서 items 1-28 값이 올바르게 추출되면 우선 대체 허용 (교차검증 먼저)
- 동일 오슬롯팅 다른 (회사×분기) 점검 요망 (원 요청 #3)
