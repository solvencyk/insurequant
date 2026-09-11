# InsureQuant 제작·검증 투자 기록 (investment record)

이 문서는 저작권법 제2조 제20호 '상당한 투자' 입증용 내부 기록이다 (데이터베이스제작자의 권리, 제93조·제95조; 부정경쟁방지법 제2조 제1호 파목 병행).

> 측정일 2026-09-11 · 브랜치 `fix/csm-product-segmented-columns` · HEAD `690965f` · 전부 `git`/저장소에서 기계로 잰 값이다. 추정치 없음. 손으로 고치지 말고 아래 갱신 명령으로 다시 잰다.

## 갱신 명령 (분기마다)

```bash
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/measure_investment_record.py
```

마스터 JSON 은 작업트리가 아니라 **커밋된 HEAD**(`git show HEAD:`)에서 읽는다 — 동시 세션이 반쯤 쓴 파일이 숫자를 흔들지 못하게. 원천 파일(data/disclosure, data/dart raw)은 git 미추적이라 **이 PC 디스크 기준**이며, 다른 머신에서 돌리면 0 으로 나올 수 있다(그때는 이 문서의 이전 값이 증거).

## 1. 제작 기간·작업량 (git)

| 항목 | 값 | 측정 방법 |
|---|---|---|
| 첫 커밋일 | 2025-09-15 | `git log --reverse --format=%as \| head -1` |
| 최근 커밋일 | 2026-09-11 | `git log -1 --format=%as` |
| 기여 기간 | 362일 (첫 커밋 ~ 최근 커밋) | 날짜 차이 + 1 |
| 커밋 수 (HEAD 도달) | 561 | `git rev-list --count HEAD` |
| 커밋이 있는 날 수 | 57 | `git log --format=%as \| sort -u \| wc -l` |
| 최초 공개 push | 2026-05-25 (CLAUDE.md 기록) | — |

## 2. 코드 (파이프라인·검증·화면)

| 영역 | 파일 수 | 줄 수 | 비고 |
|---|---:|---:|---|
| `scripts/` (파이프라인·게이트, `_probes/` 제외) | 278 | 84,178 | 다운로드·파싱·검증·빌드 |
| `scripts/_probes/` (1회성 조사 스크립트) | 1295 | 74,288 | 조사 이력 |
| `src/` (파서 엔진·룰 엔진) | 33 | 8,822 | K-ICS Docling MD 파서, IFRS17 DART XML 파서, `kics_json_rules.py` |
| `tests/` | 41 | 10,392 | 골든 + 룰 커버리지 매니페스트 |
| 배포 화면 (HTML/CSS/JS 9개) | 9 | 6,993 | 차트·표·다운로드·제보 위젯 |
| `docs/` (설계·도메인·이력 md) | 57 | 22,875 | 그중 changelog 15,127줄 |

## 3. 검증 체계

| 항목 | 값 | 측정 방법 |
|---|---:|---|
| K-ICS 룰 엔진 rule id 수 | 30 | `tests/fixtures/kics_rules_golden.json` `by_rule` 키 수 |
| K-ICS 룰 엔진 findings (골든 고정) | 16,140 | 같은 파일 `findings`/`by_status` |
| 게이트 validator rule id 수 (`scripts/validate_*.py` 15개) | 123 | `rule="…"` 리터럴 + 룰표 키, 중복 제거 |
| 골든 테스트 파일 | 8 | `tests/test_*_golden.py` |
| 테스트 함수 수 | 266 | `tests/test_*.py` 의 `def test_` |
| push 강제 | `.githooks/pre-push` → `scripts/prepush_check.py` | 데이터계약·K-ICS 룰·anomaly·inbox 위생·오프라인 테스트 |

골든 테스트: `test_dividend_golden.py`, `test_ifrs17_bs_golden.py`, `test_kics_rules_golden.py`, `test_master_tables_golden.py`, `test_pl_breakdown_golden.py`, `test_post_transition_golden.py`, `test_viz_csm_waterfall_golden.py`, `test_viz_ifrs17_panels_golden.py`

## 4. 데이터베이스 규모 (커밋된 마스터 JSON, HEAD)

| 시트 | 파일 | 행 | 회사 수 | 분기 수 |
|---|---|---:|---:|---:|
| 17BS | `IFRS17_BS.json` | 7,042 | 39 | 16 |
| K-ICS공시 | `kics_disclosure.json` | 25,458 | 39 | 14 |
| 금리민감도 | `kics_rate_sensitivity.json` | 789 | 39 | 4 |
| CSM워터폴 | `CSM_waterfall.json` | 2,172 | 37 | 14 |
| CSM상각 | `CSM_amortization.json` | 390 | 39 | 1 |
| 가정민감도 | `CSM_sensitivity.json` | 195 | 32 | 1 |
| 신계약CSM배수 | `NB_CSM_multiple.json` | 362 | 37 | 14 |
| 손익분해PL | `PL_breakdown.json` | 11,930 | 39 | 14 |
| 배당 | `dividend.json` | 2,043 | 24 | 14 |
| 기본자본소진율 | `kics_tier1_utilization.json` | 390 | 39 | 1 |
| 보완자본소진율 | `kics_tier2_utilization.json` | 546 | 39 | 1 |
| 자본성증권발행현황 | `kics_capital_securities.json` | 123 | 27 | 1 |
| 자본비율전망 | `kics_forward_capital.json` | 2,090 | 38 | 5 |
| **합계** | 13개 마스터 | **53,530** | 합집합 39 | 합집합 16 (2021.4Q ~ 2026.2Q) |

행 = (회사 × 분기 × 항목) 셀 단위. 각 셀은 원문 PDF/XML 에서 자동 추출 → 룰 게이트 → 필요 시 owner 수기 검토(gold)를 거쳤다.

## 5. 원천 자료 (이 PC 디스크, git 미추적)

| 원천 | 파일 수 | 비고 |
|---|---:|---|
| 정기경영공시 PDF (`data/disclosure/**/*.pdf`) | 550 | 분기 폴더 14개 (FY2023_Q1 ~ FY2026_Q2) → Docling MD → 파서 |
| DART raw (`data/dart/**/raw/**`) | 1,297 | 분기 폴더 15개, XML/zip 원문 |
| KIDI 통계 (`data/kidi/`) | 548 | 월별 보험료 통계 |
| IR 자료 (`data/ir/`) | 130 | 팩트시트·시리즈 JSON (xlsx 는 2026-09-11 부터 git 미추적) |

## 6. 사람 검토 루프

| 항목 | 값 | 비고 |
|---|---:|---|
| owner 답지 xlsx (`gold/`) | 44 | 손으로 검증한 정답지, git 추적 |
| 셀 단위 정정 레지스트리 (`data/_gold/*.json`) | 22 | owner 확정 셀·예외 등재 |
| 스테이지 간 처리 완료 티켓 (`inbox/**/_resolved/*.md`) | 386 | 검증→파서 재작업 왕복 기록 |
| 포스트모템 (`docs/postmortems/PM-*.md`) | 10 | 게이트가 놓친 사고의 룰 배선 기록 |

## 7. 이 기록의 쓰임

- 데이터베이스제작자의 권리(저작권법 제93조)는 등록 없이 제작 완료 시 생기지만, 분쟁에서 "소재의 수집·검증·갱신에 인적·물적으로 상당한 투자"를 한 쪽이 입증한다. 위 표가 그 1차 증거다.
- 저작권 등록(한국저작권위원회)이나 상표 출원 시 첨부 자료로도 쓴다. 배경: `artifacts/legal/ip_protection_report_20260911.md`.
- 분기 라운드가 끝날 때마다 갱신 명령을 돌리고 이 파일을 커밋한다 (publishing 스테이지).
