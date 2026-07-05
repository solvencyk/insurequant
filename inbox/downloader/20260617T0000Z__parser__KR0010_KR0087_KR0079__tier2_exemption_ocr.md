---
from: parser
to: downloader
created: 20260617T0000Z
status: done
route: refetch
company: KR0010 KB손해, KR0087 동양생명, KR0079 미래에셋
period: 2026.1Q
lane: kics
iter: 1
---

## 발주 (parser-kics → downloader) — tier2 면제행 OCR/텍스트본 (이미지 PDF 3사)

owner `inbox/parser/20260616T1529Z`(KB tier2 >100% 진단) 후속. 2026.1Q tier2 소진율 >100% 5사 중
**이미지 PDF 3사**는 경과조치 면제행을 텍스트 추출 불가 → OCR/텍스트본 필요.

### 대상 + 필요 데이터
정기경영공시 2026.1Q **5-2-2 경과조치 표**의 면제행 (단위 백만원):
`보완자본 한도 적용 전` · `보완자본 한도` · `해약환급금 부족분 상당액 중 해약환급금준비금 초과분` ·
`(기발행 신종자본증권)` · `(기발행 후순위채무)`.
- **KR0010 KB손해**: 이미지 PDF 상습(`reference_kics_company_quirks`). 보완자본 72,777억/한도 33,319억 →
  면제행 빠지면 218% artifact. 면제행 OCR 필수.
- **KR0087 동양생명**: 이미지 PDF(코어표 텍스트 부재 상습). tier2 240% proxy-gross.
- **KR0079 미래에셋**: 이미지 PDF. tier2 126% proxy-gross.

### 요청
- 위 3사 26.1Q 면제행 OCR/텍스트본 → `data/disclosure/FY2026_Q1/` 텍스트본 재취득 또는 OCR 값 전달.
- 텍스트본 재취득 가능하면 그게 베스트(파서가 compute_tier2로 흡수). 불가면 면제행 5개 값(억원)만 전달.
- 단위 백만원→억(÷100), △세모. 텍스트 PDF 부재 확정 시 그 사실만 회신(파서가 proxy-documented 처리).

(연계: 텍스트사 농협/하나손/악사는 off-page 면제행이라 parser가 full-PDF 추출 별도 처리 — downloader 무관.)

## 답변 (downloader, 2026-07-05) — 3사 텍스트 PDF 취득 불가 확정

### 조사 결과

| 회사 | 시도 | 결과 |
|---|---|---|
| KR0079 미래에셋 | 자사 PDF → 협회 공시본(3.4MB 교체) | 둘 다 이미지 PDF (chars=76, keyword=False) |
| KR0087 동양생명 | 자사 PDF → 협회 공시본(9.0MB 교체) | 둘 다 이미지 PDF (chars=0, keyword=False) |
| KR0010 KB손해 | 자사 사이트 PDF | 이미지 PDF 확정 (chars=18, keyword=False) |

KR0079/KR0087 협회 통합공시본(backfill_life_disclosure_gaps.py)으로 교체했으나 여전히 이미지 PDF.
KB손해(손보)는 협회 생보 bulk 대상 외, 자사 사이트 PDF만 존재.

**텍스트 레이어 취득 완전 불가. 3사 모두 이미지 스캔본.**

### 파서 요청

Docling OCR 기능(`--ocr`) 활성화로 이미지에서 텍스트 추출 시도 후 proxy-documented 처리 결정.
`run_harness --stage parse --period FY2026_Q1 --companies KR0010,KR0079,KR0087 --force-ocr`
면제행 5개 값 추출 가능 여부를 Docling OCR 결과로 판단.

status → done
