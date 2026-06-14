---
from: parser
to: validation
created: 20260610T0830Z
status: resolved
route: reparse
company: ALL
period: ALL
rule: RS1_RATIO_IDENTITY, RS2_BASE_ANCHOR, RS3_DIRECTION_SANITY, RS4_COVERAGE_CENSUS
iter: 1
---

## 미결 (parser 작성)

**K-ICS 금리민감도 마스터 적재 완료 — RS1–4 검증룰 구현 요청.** (owner 발주 feature, 스펙
`docs/agents/kics-rate-sensitivity-spec.md` §5.)

- 마스터: 루트 `kics_rate_sensitivity.json` (**423행**, 74 사·분기). 스키마 §2.
  (416→423: 사용자 검토로 FY2025_Q2 비율행 `%` 미파싱 버그 수정 — 현대·신한이지·KB라이프 등 비율 복구.)
- diag: `data/_derived/kics_rate_sensitivity_diag.json` (per-사·분기 status).
- 추출기: `scripts/extract_kics_rate_sensitivity.py`.

**parser-side 자기검증 (구현 참고):**
- **RS1(비율≈금액/기준금액×100):** 705개 컬럼검증 전부 통과(rs1_fail 0). tol `max(0.5%p, 0.5%·|비율|)` 사용.
- **RS2(적용전 base vs kics_disclosure item1/14/27):** 전수 215 OK / **1 diff = KR0011 DB손해 2025.2Q**.
  → 이건 파싱오류 **아님**: 금리민감도표가 **주4) 별도 재무제표 기준**(200,558/90,447/221.74), 헤드라인은 연결
  (item1/14/27=209,192/98,079/213.29). **basis 차이**라 RS2 RED 떠도 reparse 대상 아님 = documented exception 처리 요망.
  diag `rs2_base_diff`로 표시함.

**diag status 분포:** extracted 63 / post_dash 6 / delta_converted 4 / suspect_truncation 2 / rs2_base_diff 1.
- `post_dash`: 적용후 블록 미공시(전=후 미적용) — 적용전만 검증, 적용후 rows 없음(정상).
- `delta_converted`: 흥국화재·흥국생명 FY2025_Q2/Q4 (delta→absolute 변환 후 저장, RS1 통과).
- `suspect_truncation`: KR0010 FY2025_Q4·KR0075 FY2025_Q4 = MD 섹션부재. raw-PDF 대조결과 KR0010=진짜 부재(SKIP 정당),
  **KR0075=PDF엔 존재→재-docling 진행중**(downloader inbox); 재반영 후 추가 적재 예정.

### 요청
1. RS1–4 룰 구현(`scripts/validate_kics_rate_sensitivity.py` 또는 기존 러너 확장), 마스터에 실행.
2. RS2 KR0011 2025.2Q는 basis 차이 → documented exception(게이트 블록 금지).
3. RS4 커버리지: FY2023~FY2024_Q3 부재는 정상(서식 도입 전), hole 아님. Q2/Q4 반기 regime 내 hole만 의심.
4. 결과 RED 있으면 parser inbox로 회신(max 5 loop).

## 답변 (validation 작성 — 처리 후)

**RS1–RS4 구현·검증 완료 — RESOLVED.** `scripts/validate_kics_rate_sensitivity.py` (423행 / 74 사·분기). 결과 → `data/_derived/kics_rate_sensitivity_validation.json`.

| 룰 | 결과 |
|---|---|
| **RS1_RATIO_IDENTITY** | **0 RED** (705 컬럼 항등식 전부 통과 — parser 자기검증 일치) |
| **RS2_BASE_ANCHOR** | **0 RED** + KR0011 DB손해 2025.2Q 3 measure **documented exception**(별도/연결 basis 차이 — 요청대로 게이트 블록 안 함) |
| RS3_DIRECTION_SANITY | 28 YELLOW (생보 −100bp 비율 상승 = 역방향. 회사 ALM 따라 정상 가능, 플래그만) |
| RS4_COVERAGE_CENSUS | **1 YELLOW** = 코리안리재보험 2025.2Q (2025.4Q 보유한데 2Q hole). cadence 인식(반기 회사 1Q/3Q 부재는 정상)으로 손보 1Q/3Q 과탐 40→1 정리. |

**gate RED=0.** RS2 KR0011 exception 코드 반영(`RS2_EXCEPTIONS`). 룰표 `claude-agent-validation.md` §1.1 등재.

**확인 요청 1건 (YELLOW, 비차단)**: 코리안리 2025.2Q 금리민감도 — 반기(2Q/4Q) 회사인데 2Q만 빠짐. 원천 부재면 정상, 누락이면 적재. RS3 28건은 ALM상 정상 추정이라 차단 안 함.

## 후속 (parser 작성 — RS4 코리안리 2025.2Q 확인 결과)

**진짜 누락 맞음 — 원인은 MD 변환누락(원천은 존재).** 직접 확인:
- `md_inbox/FY2025_Q2/KR1000_*.md` **파일 자체 부재** (그래서 추출기가 skip, diag 항목도 없었음).
- raw PDF `data/disclosure/FY2025_Q2/raw/KR1000_코리안리.pdf` **page 27에 표 존재**, 숫자 기계판독 가능
  (base 비율 204.45 / 금액 44,902 / 기준금액 21,963, ±50/±100bp 풀세트, 전=후 동일. RS1 사전검증
  44,902/21,963×100=204.44 ✓).
- 조치: owner 스펙 처방(변환절단→재-docling)대로 **downloader 핸드오프**
  `inbox/downloader/20260610T1510Z__parser__KR1000_2025.2Q__md_missing_redocling.md`. MD 생성되면
  `extract_kics_rate_sensitivity.py` 재실행으로 자동 흡수 → RS4 YELLOW 해소 예정. 그때까지 YELLOW 유지가 맞음.
- **[종결 2026-06-10]** downloader 반송(docling=파서 소관) → 파서가 직접 재파싱(`docling_partial_v4`: 민감도 키워드 +
  캡 20). KR1000 2025.2Q + KR0075 2025.4Q 적재(435행), RS 재검증 **RS4 hole=0 / gate RED 0**. YELLOW 해소 확인 바람.
  상세: `inbox/parser/20260610T1545Z__downloader__MULTI_2025__redocling_bounce.md` 답변.
