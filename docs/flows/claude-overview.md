# KICS 파이프라인 개요

## 목적

PDF 수집 → Docling 파싱 → 마스터 JSON 적재까지의 전 과정을 일관된 용어로 정의합니다.

## 산출물 명칭 매핑

- `kics_disclosure.json`: 단일 표준 산출물(루트, K-ICS.html이 직접 읽음). 게이트 = `scripts/validate_kics_disclosure.py`
- `kics_rate_sensitivity.json`: 금리민감도 마스터
- 2026-07-21 제거: `kics_data.json` / `insurance_data.json` / `kics_disclosure.csv` — 초기 MD→JSON·CSV→JSON 경로의 산출물로, 코드·문서 모두에서 삭제됨

## 전체 흐름

```mermaid
flowchart LR
  disclosureSite[보험사공시사이트] --> downloader[PDF다운로드]
  downloader --> aclVerify[ACL정상화_및_PDF검증]
  aclVerify -->|"failed"| retry[자동재시도]
  retry --> downloader
  aclVerify -->|"verified"| pdfStore[로컬PDF저장소]
  pdfStore --> doclingParser[Docling파싱]
  doclingParser --> qualityGate[품질평가]
  qualityGate -->|"품질OK"| mdInbox[md_inbox폴더]
  qualityGate -->|"품질NG"| reviewQueue[Gemini수동리뷰큐]
  reviewQueue -->|"수동수정후"| mdInbox
  mdInbox --> fillScripts[fill_period/subitems/market_스크립트]
  fillScripts --> kicsJson[kics_disclosure.json]
  kicsJson --> gate[validate_kics_disclosure_게이트]
  gate --> githubPost[GitHub포스팅_수동]
```

## 모듈 책임 분리(현재 코드 기준)

### 1) 다운로드 계층

- 단일 엔진: `src/solvency/downloader/base.py` + `runner.py`
- 협회 단위 핸들러:
  - `handlers/nonlife_insurance_association.py` (KNIA 손보협회, 16개 일괄)
  - `handlers/life_insurance_association.py` (생명보험협회)
- 회사명 → 사코드 매핑은 `*_insurer_registry.yaml`로 분리
- 다운로드 직후 ACL 정상화 + `verify_pdf` 자동 호출, 실패 시 자동 재시도

### 2) PDF 검증 계층 (신규)

- ACL 정상화: `src/solvency/verification/acl.py`
  - `takeown` + `icacls /reset` + `icacls /grant *S-1-1-0:(R)` + `chmod`
- 다단계 검증: `src/solvency/verification/pdf_check.py`
  - 등급: `failed | verified_basic | verified_full`
  - basic: 매직바이트(%PDF-) + user read 권한 + 사이즈 > 0
  - full: basic + `지급여력비율` 키워드 + pypdf 첫 페이지 파싱
- 다운로더 엔진에 자동 통합 + 하네스 `--stage pdf`로 일괄 검증 가능
- 사용자가 더블클릭으로 못 여는 ACL 차단 케이스를 게이트화

### 3) 파서 계층

- 메인: `src/solvency/parser/docling_parser.py` (Docling 기반 PDF → Markdown)
- 품질 게이트: `src/solvency/parser/quality_check.py` (점수 산출 + 리뷰 큐 작성)
- 회사별 예외: `src/solvency/parser/company_handlers.py`

### 4) 적재 계층 (MD → 마스터 JSON)

- `scripts/fill_period_to_disclosure.py` → `fill_subitems_to_disclosure.py` → `fill_market_subitems_to_disclosure.py`
- 경과조치 적용후: `scripts/fill_post_transition_to_disclosure.py`
- 상세 순서·회사별 함정은 `.claude/skills/kics-parser/` SKILL 참조

### 5) 정합성 검증 계층

- 도메인 룰: `src/solvency/validation/kics_json_rules.py` (R1~R8 · 8_life · 19_market)
- 게이트: `scripts/validate_kics_disclosure.py` (RED=0), 배포 전 `scripts/validate_data_contract.py`
- 하네스: `scripts/run_harness.py` (`--stage quality|pdf|parse`)

## 운영 모델

- 메인 경로: `PDF 다운로드 → Docling 파싱 → JSON 변환 → GitHub 포스팅(수동)`
- 코드는 `md_inbox/` 폴더만 본다
- Docling 결과 품질이 임계치 미달인 경우만 `artifacts/review_queue/`로 분리 → 사용자에게 "Gemini로 수동 검사하세요" 권고
- Drive 업로드/Gemini 파싱은 품질 미달 시 보조 경로로만 사용 (코드 밖 수동 운영)

## 디스크 레이아웃 (quarter-first)

```
data/disclosure/
  FY2025_Q4/
    pdf/
      KR1098_카카오페이손해보험.pdf
    parsed/
      KR1098_카카오페이손해보험.md
  FY2025_Q1/
    pdf/
      KR0051_신한EZ손해보험.pdf
      KR0051_신한EZ손해보험_amended.pdf
  _meta/
    KR1098_download_cache.csv
  _unsorted/
    <companyDirname>/...   # 분기 추론 실패한 레거시 파일
```

## 문서화 원칙

- Docling 경로가 유일한 운영 경로 (2026-07-21 레거시 camelot/CSV 경로 삭제)
- 다운로드는 "보험사별 스크립트"가 아닌 "case 기반 단일 엔진"을 목표로 기술
- 파일명/필드명/에러 정책을 문서에서 먼저 확정
- 자동 검증 하네스에서 문서 계약을 강제
