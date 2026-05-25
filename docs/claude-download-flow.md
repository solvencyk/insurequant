# 공시 PDF 수집 플로우

## 목표

보험사 공시 사이트에서 지급여력비율 관련 PDF를 표준 구조로 수집합니다.  
**이번 운영 모델에서는 Drive 업로드/Gemini 작업은 코드 밖(MCP + 수동)으로 분리**되며, 코드는 PDF 수집과 manifest 작성까지만 책임집니다.

## 단일 엔진 아키텍처

- 엔진: `src/solvency/downloader/base.py`의 `DownloaderEngine`
- CLI: `src/solvency/downloader/runner.py`
- 메인 운영 단위는 **협회 단위 일괄 다운로드** (개별 회사가 아님)
  - 손해보험: `python -m solvency.downloader.runner --company NONLIFE`
  - 생명보험: `python -m solvency.downloader.runner --company LIFE`
- 협회 페이지에서 회사명 추출 → `*_insurer_registry.yaml`로 사코드 매핑
- 핸들러: `src/solvency/downloader/handlers/{nonlife,life}_insurance_association.py`

새 보험사 추가는 registry YAML에 한 줄 추가만 하면 됨 (코드 수정 불필요).
회사명-사코드가 매칭되지 않은 PDF는 `data/disclosure/_unmatched/<period>/`로 분리.

회사별 단일 사이트가 따로 필요한 경우(레거시 fallback)는 `profiles/<KRxxxx>.yaml`
+ `site_type` (`case_a_direct_pdf` / `case_b_button_click` / `case_c_zip_attachment`)
경로도 유지됩니다.

## 자동 검증 통합

다운로드 직후 모든 PDF에 대해 자동으로 다음이 수행됩니다.

1. ACL 정상화 (`takeown` + `icacls`) — 사용자 read 권한 확보
2. `verify_pdf` 다단계 검증 (매직바이트, read, 사이즈, 키워드, pypdf)
3. 실패 시 캐시 무효화 후 최대 2회 자동 재시도
4. manifest에 `verification_level`, `verification_reasons` 기록

상세 명세는 [validation-harness.md의 Stage 8](claude-validation-harness.md#stage-8-pdf-접근성-게이트---stage-pdf) 참조.

## 표준 저장 구조 (quarter-first 레이아웃)

로컬:

- `data/disclosure/<period>/pdf/<companyDirname>.pdf`
- `data/disclosure/<period>/parsed/<companyDirname>.{md,xlsx}`
- `data/disclosure/_meta/<companyCode>_download_cache.csv` (멱등성용 manifest)
- `data/disclosure/_unsorted/<companyDirname>/...` (마이그레이션이 분기를 추론하지 못한 파일)

Drive (코드 외부, 수동/MCP):

- `/kics-disclosure/raw-pdf/<period>/<companyDirname>.pdf`
- `/kics-disclosure/logs/<runDate>/download_manifest.csv`

## 명명 규약

- `<period>` : `FY<연도>_Q<분기>` 형식. 예) `FY2025_Q4`
- `<companyDirname>` : 기존 회사 폴더명 그대로(예: `KR1098_카카오페이손해보험`)
- 보완/재공시본은 동일 폴더에 `<companyDirname>_amended.pdf`(또는 `_amended2`, `_amended3` ...)로 저장

예시:

- `data/disclosure/FY2025_Q4/pdf/KR1098_카카오페이손해보험.pdf`
- `data/disclosure/FY2025_Q1/pdf/KR0051_신한EZ손해보험_amended.pdf`
- `data/disclosure/FY2024_Q4/parsed/KR0008_삼성화재.md`

## manifest 필드

`data/disclosure/_meta/<companyCode>_download_cache.csv`:

- `run_id`, `company_code`, `company_dirname`, `period`
- `title`, `fiscal_year`, `quarter`, `disclosure_date`
- `source_url`, `local_path`, `sha256`, `status`, `error_message`

## 멱등성

- 캐시 키: `source_url`
- 같은 URL이 캐시에 있고 로컬 파일이 존재하면 다운로드를 생략하고 `status="skipped"` 기록
- 캐시 파일은 append-only로 운영하되, 동일 키 중복 시 최신 항목으로 사용

## 실패 정책

- 다운로드 실패는 최대 3회 재시도(엔진 외부 wrap)
- `bytes == 0` 또는 `sha256` 미생성 → `status="failed"`
- 같은 문서의 원본/보완이 공존 → 보완본을 최종(`amended`)으로만 보관

## 레거시 다운로더와의 관계

- 4종(`legacy/downloaders/*.py`)은 동작 보존을 위해 그대로 유지
- 새 단일 엔진 핸들러가 완성되기 전까지는 회사별 정확도 검증을 위한 fallback
- 새 핸들러 작성 시 이 4종에서 셀렉터/플로우를 이식

## 기존 데이터 마이그레이션 (2026-04, 1회성)

이전 레이아웃(`data/disclosure/<companyDirname>/{pdf,parsed}/...`)에 쌓여 있던 704개 파일을 새 분기-우선 레이아웃으로 이미 옮겼습니다.

- 매칭 성공: 550개 → `FY2023_Q1` ... `FY2025_Q4`
- 미매칭: 154개 → `data/disclosure/_unsorted/<companyDirname>/` (대부분 분기 정보가 없는 회사 루트 통합 파일)
- 사용한 1회성 스크립트는 [archive/migrations/](../archive/migrations/)에 보존되어 있음
- 새 다운로드는 `src/solvency/downloader/`가 처음부터 새 레이아웃으로 떨어트림
