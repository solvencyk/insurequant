# Markdown 산출물 운영 모델

> **요약**: Docling이 메인 파서. Gemini는 Docling 품질 미달 시에만 진입하는 수동 보조 경로.

## 목표

PDF에서 지급여력 관련 표를 추출한 Markdown을 안정적으로 확보하고,  
이후 단계가 사용할 수 있도록 표준 폴더(`md_inbox/`)에 정리합니다.

## 메인 경로: Docling (로컬, 무료)

- 모듈: `src/solvency/parser/docling_parser.py`
- 입력: 회사별 PDF 디렉토리(`data/disclosure/<companyCode>/pdf/`)
- 출력: `md_inbox/<companyCode>/<docId>.md`
- 멱등성: 입력 PDF의 sha256/size/mtime이 동일하면 변환 생략
- 메모리: 변환 후 Docling 객체 명시적 해제 + `gc.collect()`
- 병렬: `parse_parallel(items, workers=N)`로 process pool 사용

## 보조 경로: Gemini 수동 리뷰 큐

- 트리거: `parser/quality_check.py`가 임계치(score < 0.7 또는 핵심 행 누락) 미달 판정 시
- 산출물: `artifacts/review_queue/review_queue_<run_id>.csv`
- 운영자가 해당 PDF 목록을 Gemini Enterprise에서 다시 파싱
- 결과 Markdown을 `md_inbox/<companyCode>/`에 덮어쓰면 다음 빌드부터 자동 반영

## Markdown 입력 계약

파일 경로: `md_inbox/<companyCode>/<docId>.md`

Front Matter 필수 키:

- `run_id`
- `company_code` (예: `KR0008`)
- `fiscal_year` (예: `FY24`)
- `quarter` (예: `Q4`)
- `disclosure_date` (`YYYY-MM-DD`)
- `source_pdf`
- `source_sha256` / `source_size` / `source_mtime`
- `parser` (`docling` | `gemini`)
- `parser_version`
- `parse_confidence`

본문에는 최소한 다음 행이 표 형식으로 포함되어야 합니다.

- `가. 지급여력금액`
- `나. 지급여력기준금액`
- `다. 지급여력비율`

## 품질 게이트 결정 로직

`parser/quality_check.py`가 점수 산출:

- 핵심 행 1개 누락 시 -0.2
- 단위 표기(`억원`, `%` 등) 누락 시 -0.15
- `disclosure_date` 누락 시 -0.1
- 표 셀 수치 정규화율(0~1)을 곱

`score >= 0.7` 이며 핵심 행이 모두 존재해야 `accept`. 그렇지 않으면 `review`.

## Drive 업로드/관리

- 코드는 Drive에 직접 접근하지 않음
- Cursor의 Google Drive MCP 또는 사용자가 수동으로 업로드/공유
- 운영 가이드:
  - `/kics-disclosure/raw-pdf/<year>/<companyCode>/...pdf`
  - `/kics-disclosure/parsed-md/<year>/<companyCode>/...md`

## Gemini Enterprise 수동 사용 시 권장 프롬프트

- "지급여력 관련 표만 추출"
- "표 제목, 단위, 기준일을 반드시 반환"
- "수치 셀은 원문/정규화 값(숫자형) 둘 다 반환"
- "누락/판독불가 셀은 빈 문자열이 아니라 `null`"
- "출력은 Markdown + YAML Front Matter 형식"

## 레거시 대체 관계

- 기존 Camelot 기반 `legacy/camelot_parser.py`가 하던 PDF 표 추출 역할을 Docling이 담당
- Camelot 경로는 사이트 구조 급변 또는 Docling 사용 제한 시의 fallback으로만 유지
- Selenium 기반 Gemini 자동화는 채택하지 않음(UI 변경 취약, 멱등성 보장 어려움)
