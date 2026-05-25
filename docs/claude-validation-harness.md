# 품질/정합성 검증 하네스 및 CI 로드맵

## 목표

`kics_data.json` 생성 파이프라인의 코드 품질과 데이터 정합성을 자동으로 검증해, 회귀를 조기에 차단합니다.

## 하네스 구성

단일 진입 명령:

- `python scripts/run_harness.py --stage all`
- `python scripts/run_harness.py --stage perf`  : 코드 효율성 게이트
- `python scripts/run_harness.py --stage data`  : 결과물 정합성 게이트
- `python scripts/run_harness.py --stage pdf`   : 다운로드된 PDF 접근성 게이트

세부 스테이지:

- `lint`: 정적 품질 검사
- `unit`: 변환 로직 단위 테스트
- `golden`: 고정 샘플 대비 회귀 테스트
- `schema`: JSON 스키마 유효성 검사
- `rule`: 도메인 정합성 검사(a~g + 확장 규칙)
- `perf`: Memory / I-O / Idempotency
- `data`: schema + rule + 품질 게이트 + 리뷰 큐 검증
- `pdf`: ACL 정상화 + 다단계 PDF 검증 (사용자 read 권한, 매직바이트, 사이즈, 키워드, pypdf)

## Stage 1: 코드 품질

추천 도구:

- `ruff` (lint)
- `black` (format)
- `mypy` (선택, 타입체크)

최소 통과 조건:

- lint error 0건
- format diff 0건

## Stage 2: 단위 테스트

테스트 대상:

- Markdown 파서(Front Matter, 표 섹션, 값 파싱)
- 숫자 정규화 함수
- 스키마 매퍼(레코드 생성)
- 파일명/메타데이터 파서

추천 구조:

- `tests/unit/test_markdown_parser.py`
- `tests/unit/test_normalize_value.py`
- `tests/unit/test_record_mapper.py`

## Stage 3: Golden 테스트

입력:

- `tests/golden/input/*.md`

기대 결과:

- `tests/golden/expected/*.json`

검증 방법:

- 정렬 후 deep equality 비교
- 허용 오차가 필요한 숫자는 필드별 tolerance 테이블 적용

## Stage 4: Schema 검증

스키마 파일:

- `schemas/kics_data.schema.json`

검증 항목:

- 필수 필드 존재
- 타입/범위/enum 일치
- 날짜 포맷(`YYYY-MM-DD`) 준수
- 키 중복 금지

## Stage 5: 정합성 검증(도메인 룰)

**Authoritative K-ICS JSON rules:** [`kics-json-validation-rules.md`](kics-json-validation-rules.md) (synced with `src/solvency/validation/kics_json_rules.py`).

**Pipeline gate:** `python scripts/validate_kics_disclosure.py` must report **RED=0** (or only documented exceptions in `TODO.md`) before JSON swap, template sync, or deploy. Unexpected RED → parsing-error review required.

기존 코드 재사용:

- `disclosure_validation.py`의 규칙 a~g
- `scripts/validate_kics_disclosure.py` — rules 1, 2, 4-8, 8_post, 8_life on root `kics_disclosure.json`; reports under `artifacts/kics_validation/`

확장 권장:

- 비율 재계산 검증: `가 / 나 * 100 ~= 다`
- 기간 연속성 검증(전분기 대비 급변치)
- 회사별 누락 항목 검증
- 음수/비정상값(단위 불일치 포함) 탐지

## Stage 6: 실행 안정성 제약(Memory/I-O/멱등성)

이번 PDF 추출/공시 작업에서는 아래 3가지를 하네스의 필수 게이트로 둡니다.

### 6-1) Memory Leak 게이트

하네스 질문:

- "대형 데이터프레임을 변수에 계속 들고 있나? `del`과 `gc.collect()`가 필요한가?"

자동 점검 항목:

- 배치 처리 중 RSS/Peak 메모리 추적(`start`, `every_n_files`, `end`)
- 파일 N개 연속 처리 후 메모리 증가율 측정
- 루프 종료 시 대형 객체 해제 여부 점검(`del df`, `del tables` 등)
- 주기적 GC 실행 여부 점검(`gc.collect()` 호출 카운트)

통과 기준(초기안):

- `peak_memory_mb <= baseline_mb + 1024`
- `end_memory_mb <= baseline_mb + 512`
- OOM/메모리 예외 0건

### 6-2) I/O Bottleneck 게이트

하네스 질문:

- "PDF를 한 장씩 읽고 있나? 비동기(Async) 혹은 병렬로 처리할 수 없나?"

자동 점검 항목:

- `serial` vs `parallel` 처리량 비교(`pdf_per_min`, 평균 처리시간)
- 다운로드/파싱/저장 단계별 시간 분해 측정
- 병렬 처리 시 중복 다운로드/중복 저장 race condition 점검
- 느린 구간(top N slow files) 리포트

통과 기준(초기안):

- 병렬 모드 처리량이 직렬 대비 `>= 1.5x` 또는 동등한 안정성 근거 확보
- 단계별 타임아웃 초과 건수 0건(또는 허용치 이내)

### 6-3) 멱등성(Idempotency) 게이트

하네스 질문:

- "동일한 코드를 두 번 실행했을 때, 결과가 중복되거나 망가지지 않는가?"

자동 점검 항목:

- 동일 입력으로 파이프라인 2회 실행
- 1회차/2회차 산출물(`kics_data.json`) 해시 및 레코드 수 비교
- PDF 단계 skip 정책 검증(이미 처리된 파일은 skip)
- DB 저장 로직 검증(UPSERT: 없으면 insert, 있으면 update)
- 2회차 실행에서 불필요한 insert 발생 여부 점검

통과 기준(초기안):

- `kics_data.json` checksum 동일
- 고유키 기준 중복 레코드 0건
- 2회차 `insert_count == 0` (변경 입력이 없을 때)
- 2회차 `skip_pdf_count`가 기대치와 일치

### 6-4) 권장 테스트 파일

- `tests/perf/test_memory_stability.py`
- `tests/perf/test_io_throughput.py`
- `tests/e2e/test_idempotent_pipeline.py`

### 6-5) 실행 예시

- `python scripts/run_harness.py --stage perf`
- `python scripts/run_harness.py --stage data`
- `python scripts/run_harness.py --stage all`

## Stage 7: 결과물 품질 게이트(Docling + 리뷰 큐)

이번 운영 모델은 Docling을 메인 파서로, Gemini를 수동 리뷰 백업으로 사용합니다.  
하네스는 Docling 산출물의 품질 점수가 미달인 항목을 자동으로 잡아 리뷰 큐에 적재해야 합니다.

### 7-1) 품질 점수 산출

`src/solvency/parser/quality_check.py`:

- 핵심 행 누락 감점: 행 1개당 -0.2
- 단위 표기 누락 감점: -0.15
- `disclosure_date` 누락 감점: -0.1
- 표 셀 수치 정규화 성공률(0~1)을 곱
- 임계치: `score >= 0.7` 이며 핵심 행 0개 누락이면 `accept`, 그 외는 `review`

### 7-2) 리뷰 큐 산출물

- 경로: `artifacts/review_queue/review_queue_<run_id>.csv`
- 컬럼: `md_path`, `company_code`, `score`, `missing_rows`, `has_unit`, `has_disclosure_date`, `numeric_normalisation_rate`, `reason`
- 운영자가 해당 PDF를 Gemini Enterprise에서 다시 파싱한 뒤,
  `md_inbox/<companyCode>/`에 결과 Markdown을 덮어쓰면 다음 빌드부터 자동 반영

### 7-3) 정합성 검증(Stage 5와 연계)

- **K-ICS disclosure JSON:** [`kics-json-validation-rules.md`](kics-json-validation-rules.md) — run `python scripts/validate_kics_disclosure.py`; gate RED=0
- 비율 재계산: `solvency_amount / required_capital * 100 ≈ solvency_ratio` (허용 오차 1.0)
- 스키마 검증: `schemas/kics_data.schema.json`
- 룰 a~g: `src/solvency/validation/rules.py`

### 7-4) 통과 기준

- 스키마 위반 0건
- 도메인 룰 위반 0건
- `review_queue` 항목은 존재 가능. 단, 운영자에게 명시적 알림 출력 필요

## Stage 8: PDF 접근성 게이트 (`--stage pdf`)

다운로드된 PDF가 코드만 통과하는 게 아니라 **사용자가 더블클릭해서 열리는 상태**여야 합니다.
도메인 계정(MS+sangwook.cho)으로 받아 일반 세션이 못 여는 ACL 차단 사례를 막기 위해
하네스가 자동으로 ACL 정상화 + 다단계 검증을 수행합니다.

### 8-1) ACL 정상화

`src/solvency/verification/acl.py`:

- `takeown /F <path>` — 소유권을 현재 사용자로 이전 (BUILTIN\\Administrators 제거)
- `icacls <path> /reset /C /Q` — 명시 ACE 제거 후 부모 ACL 상속
- `icacls <path> /grant *S-1-1-0:(R) /C /Q` — Everyone read 안전망
- `os.chmod(path, 0o644)` — 마무리

POSIX에서는 모두 no-op (`sys.platform == "win32"` 가드).

### 8-2) 다단계 PDF 검증

`src/solvency/verification/pdf_check.py`:

| 등급 | 통과 조건 |
|---|---|
| `failed` | basic 중 하나라도 실패 |
| `verified_basic` | 매직바이트 `%PDF-` + `Path.open("rb")` 성공 + 사이즈 > 0 |
| `verified_full` | basic + `지급여력비율` 키워드 + pypdf 첫 페이지 파싱 |

### 8-3) 통과 기준

- `failed == 0`
- `verified_basic`은 정상 케이스로 인정 (image-only PDF, 텍스트 추출 불가)
- 사용자가 `verified_basic` 회사 명단을 인지하고 있어야 함

### 8-4) 다운로더 자동 통합

`src/solvency/downloader/base.py::DownloaderEngine._fetch_one`이 다운로드 직후
ACL 정상화 + verify_pdf 자동 실행. 검증 실패 시 `_fetch_with_retry`가
캐시 무효화 후 최대 2회 재시도. manifest CSV의 `verification_level`,
`verification_reasons` 컬럼에 결과 기록.

### 8-5) 실행 예시

- `python scripts/run_harness.py --stage pdf` (기본 FY2025_Q4)
- `python scripts/run_harness.py --stage pdf --period FY2024_Q4`
- `python scripts/run_harness.py --stage pdf --pdf-root /custom/path`

### 8-6) 출력

- 콘솔: 회사별 결과 표 (`[OK] / [BASIC] / [FAIL]`)
- 리포트: `artifacts/reports/harness_pdf_<run_id>.json`

## 실패 리포트 표준

하네스는 아래를 출력해야 합니다.

- `run_id`
- 실패 stage
- 실패 파일/회사코드/분기
- 실패 규칙명
- 실제값/기대값/차이
- 재현 커맨드

권장 파일:

- `artifacts/reports/harness_perf_<run_id>.json`
- `artifacts/reports/harness_data_<run_id>.json`

## CI 로드맵

### 1단계(즉시)

- 로컬에서 하네스 스크립트 고정
- 팀 공통 실행 명령 문서화

### 2단계(단기)

GitHub Actions 도입:

- Trigger: PR, push(main)
- Job:
  - setup python
  - install deps (`pip install -r requirements.txt`)
  - run `python scripts/run_harness.py --stage all`
  - artifacts 업로드: `artifacts/reports/`, `artifacts/review_queue/`

### 3단계(중기)

- 실패 리포트 아티팩트 업로드
- 데이터 샘플 변경 시 golden 업데이트 PR 의무화
- main 브랜치 머지 조건으로 하네스 통과 강제

## 운영 체크리스트

- 새 회사코드 추가 시 샘플/스키마/룰 테스트 함께 추가
- Gemini 출력 포맷 변경 시 계약 테스트 먼저 업데이트
- `kics_data.json` 배포 전 하네스 결과 보고서 보관
