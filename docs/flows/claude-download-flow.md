# 공시 PDF 수집 플로우

## 목표

보험사 공시 사이트에서 지급여력비율 관련 PDF를 표준 구조로 수집합니다.  
**이번 운영 모델에서는 Drive 업로드/Gemini 작업은 코드 밖(MCP + 수동)으로 분리**되며, 코드는 PDF 수집과 manifest 작성까지만 책임집니다.

## 분기 수집 경로 (2026.2Q 라운드 실측, 2026-10-19 확인)

분기 정기경영공시는 **분기별 스크립트**로 받는다. 근거는 `data/disclosure/_meta/FY2026_Q2/` 의 매니페스트와 각 스크립트 docstring 이다.

| 구분 | 현행 경로 | 2026.2Q 증거 |
|---|---|---|
| 손보 17사 | 사별 사이트 스크립트 `scripts/download_disclosure_2026q2_nonlife.py` (분기마다 복제) | `manifest.json` 14 ok·3 fail, `src_url` 호스트가 전부 각 회사 사이트 |
| 생보 22사 | 생보협회 일괄 zip을 `scripts/download_disclosure_2026q2_life.py` 로 받음 (anchor = `fn_quarterfileDown('<q>')`) | `life_bulk_manifest.json` 2026-08-31, zip 42.6MB |
| 생보, 협회보다 먼저 자사 사이트에 올린 회사 | `scripts/download_disclosure_2026q2_life_sites.py` | `life_own_site_download_manifest.json` |

세부 절차와 사별 URL·XPath 는 `docs/agents/claude-agent-downloader.md` Source 1a·1b 가 정본이다.

## 단일 엔진 (협회 핸들러, 분기 수집의 현행 경로는 아님)

- 엔진: `src/solvency/downloader/base.py`의 `DownloaderEngine`
- CLI: `src/solvency/downloader/runner.py`
- 손해보험 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m solvency.downloader.runner --company NONLIFE`
  - 손보협회 통합공시(kpub.knia.or.kr)는 **결산(Q4)만** 싣고 예별(KR0004) 행이 없다. 프로파일도 FY2025_Q4 고정이다.
  - 마지막 기록 = `data/disclosure/_meta/NONLIFE_download_cache.csv` 2026-04-26(FY2025_Q4, 16사). Q4 백필은 `scripts/backfill_nonlife_disclosure_kpub.py`.
- 생명보험 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m solvency.downloader.runner --company LIFE`
  - 프로파일(`profiles/LIFE.yaml`)은 고정 `td[N]` 칸 번호를 쓴다. 2026.2Q 스크립트는 그 번호가 어긋난다는 이유로 onclick anchor 로 바꿨다. 엔진 LIFE 경로는 2026.2Q 에 쓰지 않았고 현재 페이지에서 검증하지 않았다.
- 협회 페이지에서 회사명 추출 → `*_insurer_registry.yaml`로 사코드 매핑
- 핸들러: `src/solvency/downloader/handlers/{nonlife,life}_insurance_association.py`
- `profiles/<KRxxxx>.yaml` (`site_type` = `case_a_direct_pdf` / `case_b_button_click` / `case_c_zip_attachment`)은 skeleton 이다. `runner.py::_placeholder_handler` 가 경고만 남기고 0건을 낸다.

회사명-사코드가 매칭되지 않은 PDF는 `data/disclosure/_unmatched/<period>/`로 분리.

## 자동 검증 통합

다운로드 직후 모든 PDF에 대해 자동으로 다음이 수행됩니다.

1. ACL 정상화 (`takeown` + `icacls`) — 사용자 read 권한 확보
2. `verify_pdf` 다단계 검증 (매직바이트, read, 사이즈, 키워드, pypdf)
3. 실패 시 캐시 무효화 후 최대 2회 자동 재시도
4. manifest에 `verification_level`, `verification_reasons` 기록

상세 명세는 [validation-harness.md의 Stage 8](claude-validation-harness.md#stage-8-pdf-접근성-게이트---stage-pdf) 참조.

## 표준 저장 구조 (quarter-first 레이아웃)

로컬:

- `data/disclosure/<period>/raw/<companyDirname>.pdf`
- `data/disclosure/<period>/parsed/<companyDirname>.{md,xlsx}`
- `data/disclosure/<period>/attachments/<companyDirname>_attachment_<종류>.pdf` (경영공시 별첨, owner 2026-10-11. `raw/` 에 섞지 않음. 목록 = `data/disclosure/_meta/attachments_manifest.json`)
- `data/disclosure/_meta/<period>/manifest.json` (분기 스크립트 manifest)
- `data/disclosure/_meta/<companyCode>_download_cache.csv` (엔진용 멱등성 manifest)

Drive (코드 외부, 수동/MCP):

- `/kics-disclosure/raw-pdf/<period>/<companyDirname>.pdf`
- `/kics-disclosure/logs/<runDate>/download_manifest.csv`

## 명명 규약

- `<period>` : `FY<연도>_Q<분기>` 형식. 예) `FY2025_Q4`
- `<companyDirname>` : 기존 회사 폴더명 그대로(예: `KR1098_카카오페이손해보험`)
- 보완/재공시본은 동일 폴더에 `<companyDirname>_amended.pdf`(또는 `_amended2`, `_amended3` ...)로 저장 — 이는 옛 규약이고 2026-09-12 이후 신규 수집분은 원본을 덮어쓰지 않고 `<companyDirname>_v<YYYYMMDD>.pdf` 로 병존 저장한다(`docs/agents/claude-agent-downloader.md` 'Amended filings coexist')

예시:

- `data/disclosure/FY2025_Q4/raw/KR1098_카카오페이손해보험.pdf`
- `data/disclosure/FY2025_Q1/raw/KR0011_DB손해보험_amended2.pdf`
- `data/disclosure/FY2024_Q4/parsed/KR0008_삼성화재해상보험.md`

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
- 같은 문서의 원본/보완이 공존 → (옛 규약) 보완본을 최종(`amended`)으로만 보관. 2026-09-12 이후 신규 수집분은 원본을 두고 `_v<YYYYMMDD>` 로 병존 저장한다(위 명명 규약 참조)

## 레거시 다운로더와의 관계

- 회사별 레거시 다운로더 4종은 2026-07-21 삭제 (단일 엔진으로 완전 대체)
- 삭제됐으므로 fallback 으로 쓸 수 없다(분기 수집 현행 절차는 `docs/agents/claude-agent-downloader.md`)
- 새 핸들러 작성 시 셀렉터/플로우는 삭제 이전 git 이력에서 이식

## 기존 데이터 마이그레이션 (2026-04, 1회성)

이전 레이아웃(`data/disclosure/<companyDirname>/{pdf,parsed}/...`)에 쌓여 있던 704개 파일을 새 분기-우선 레이아웃으로 이미 옮겼습니다.

- 매칭 성공: 550개 → `FY2023_Q1` ... `FY2025_Q4`
- 미매칭: 154개 → `data/disclosure/_unsorted/<companyDirname>/` (대부분 분기 정보가 없는 회사 루트 통합 파일; 현재 디렉터리는 남아 있지 않다)
- 사용한 1회성 스크립트는 `archive/` 아래 날짜 버킷에 보존 (2026-07-22 기준 `archive/2026-07_unreferenced_scripts/`, `archive/2026-06_csm_nb_reverse_engineering/`, `archive/scratch_scripts/`)
- 새 다운로드는 `src/solvency/downloader/`가 처음부터 새 레이아웃으로 떨어트림
