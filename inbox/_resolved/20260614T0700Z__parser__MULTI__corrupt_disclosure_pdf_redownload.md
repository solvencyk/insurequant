---
from: parser
to: downloader
created: 20260614T0700Z
status: resolved
route: redownload
company: KR0011, KR0032
period: FY2024_Q4, FY2025_Q4
rule: PDF_CORRUPT
iter: 1
---

## 미결 (parser 작성) — 손상 disclosure PDF 2건 재다운로드 요청

시장위험 36-40 회수 중 pdfplumber가 아래 2개 disclosure PDF에서 **`PSEOF: Unexpected EOF`**(파일 끝
잘림/손상)로 열기 실패. 추출 불가 → 재다운로드 필요.

- **DB손해보험 KR0011 2024.4Q** — `data/disclosure/FY2024_Q4/raw/KR0011_*.pdf`
- **NH농협손해보험 KR0032 2025.4Q** — `data/disclosure/FY2025_Q4/raw/KR0032_*.pdf`

두 (회사,분기)는 validation 19_market 잔여 RED 21건에 포함(`inbox/parser/20260613T1500Z`). 재다운 후
parser가 시장위험 36-40 재추출 예정. 정상 PDF면 텍스트레이어 있을 것(스캔 아님 추정 — 동일사 타분기는 정상).

## 답변 (close — 2026-06-14, owner/orchestrator)

**Obsolete — 재다운로드 불필요.** PDF는 실제로 안 깨졌고(fitz로 DB손해·NH농협 정상 오픈), 시장위험
localizer의 **pdfplumber 백엔드만 EOF로 죽었던 것**. 파서가 fitz fallback으로 직접 재추출 완료
(NH 2025.4Q 36-40 복구 → 19_market GREEN; DB손해 2024.4Q 등 8셀 추가 clear, 검증 RED 52→42).
downloader 액션 없음. → status: resolved, _resolved/로 이동.
