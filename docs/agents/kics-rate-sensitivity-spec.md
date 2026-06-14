# K-ICS 금리민감도 (지급여력 IR sensitivity) — 추출·스키마·검증 스펙 (정본)

> 2026-06-10 신설. 발주: owner. 근거: 38사 × ~13분기 md_inbox 전수 서베이 (5개 병렬 Explore 에이전트, 2026-06-10).
> 소스 표: 경영공시 `## 6-8. 위험 민감도` → `금리 민감도 분석` (2-key 매트릭스: 경과조치 × measure).

---

## 1. 소스 표 형태 (확정 예 — 메리츠화재 FY2025_Q4)

```
| 구분   | 구분       |    기준금액 |   △100bp |   △50bp |   +50bp |   +100bp |
| 경 과  | 지급여력비율   |  241.33 |   235.67 |  242.03 |  239.35 |   236.65 |
| 조    | 지급여력금액   | 133,506 |  134,356 | 134,312 | 132,471 |  131,500 |
| 치 전  | 지급여력기준금액 |  55,322 |   57,010 |  55,493 |  55,345 |   55,566 |
| 경 ...치 후 | (동일 3행 반복) |
```

- key1 = 경과조치 적용전/적용후, key2 = measure (지급여력비율/지급여력금액/지급여력기준금액)
- 값 컬럼: 기준금액(base), △100bp(=-100bp 하락), △50bp, +50bp, +100bp. **충격세트는 전사 ±50/±100bp 균일** (±150/200 없음).
- 단위: `(단위: %, %p, 억원)` — 비율 %, 금액 억원. **백만원 사례 없음** (코리안리만 단위표기 순서 상이).

## 2. 마스터 스키마 (owner 지정, 2026-06-10)

루트 마스터: **`kics_rate_sensitivity.json`** (long-format 배열). prefix는 타 마스터와 동일.

```json
{ "원보험사코드": "KR0001", "원수사명": "메리츠화재해상보험", "티커": "60", "생손보여부": "손해보험",
  "공시분기": "2025.4Q",
  "경과조치여부": "적용전",
  "measure구분": "지급여력비율",
  "-100bp": 235.67, "-50bp": 242.03, "base": 241.33, "+50bp": 239.35, "+100bp": 236.65 }
```

- 1 row = (사, 분기, 경과조치여부, measure구분). 회사·분기당 최대 6 rows.
- `경과조치여부` ∈ {적용전, 적용후}. `measure구분` ∈ {지급여력비율, 지급여력금액, 지급여력기준금액}.
- 값: 숫자 (비율 %, 금액 억원). 개별 셀 미공시 = `null`.
- **적용후 블록이 전부 dash(`-`)/blank** → 적용후 rows **생략** + diag에 `post_dash` 기록.
  적용후가 **적용전과 동일값**(미적용 명시) → **있는 그대로 포함** (공시 사실 보존).
- 소스 컬럼순서(기준금액 먼저)를 `-100bp, -50bp, base, +50bp, +100bp`로 재배열 저장.
- prefix 필드값(티커·생손보여부)은 `kics_disclosure.json` 동일 회사 row에서 복사.

## 3. 라벨/구조 변형 카탈로그 (서베이 확정)

| 축 | 변형 | 예 |
|---|---|---|
| 섹션 헤더 | `## 2) 금리 민감도 분석` / `##②금리민감도분석` / `## 6-8-2)` / `## 6-8-2.` / `## (2)` | 메리츠 / 삼성생명 / 삼성화재 / NH농협손보 / 한화손보 |
| 하락 표기 | `△100bp`(다수) / `-100bp` / `△ 100bp` 공백 / OCR `100 b p △` | — / 악사·하나손보·코리안리 / 흥국화재 / 카카오페이 |
| 경과조치 라벨 | 세로분할 `경 과`/`조`/`치 전`(3행) / 행별 반복 `경과 조치 전` / 인라인 `경과조치 전` / 공백 `경 과 조 치 전` | 손보 대형 다수 / 삼성생명 / 코리안리 / 서울보증 |
| 적용후 블록 | **real values** / identical / all-dash / blank-cells | 교보·ABL·하나생명·iM·IBK연금·KDB(일부분기)·악사·교보플래닛 / 다수 / 삼성생명 / 신한이지·하나손보 |
| **값 인코딩** | **absolute(다수) vs delta(`△11.3`=base−11.3)** | delta: **흥국생명, 흥국화재(FY2025_Q2)** |
| OCR | char-spacing(`지급여력기 준 금액`) + 행 verbatim 중복 | 카카오페이 KR1098 |

measure 행 순서는 전사 불변: 비율 → 금액 → 기준금액.

### delta 인코딩 정규화 (필수)
흥국 계열은 shock 셀이 base 대비 **변화량**. 변환: `absolute = base + delta` (△=음수).
검출 휴리스틱: 비율행에서 shock 셀에 부호(△/+) 명시 **그리고** |값| ≪ base (예: <0.5×base) → delta로 간주.
1차 absolute 가정 파싱 → 검증 RS1(비율 항등식) 실패 시 delta 재해석 → 재검증, 순으로도 가능.

## 4. 커버리지 기대치 (절대 단정 금지 — census로 실측)

- 표는 대체로 **FY2024_Q4부터 등장**, FY2025는 Q2/Q4 중심(반기 공시 패턴 의심). FY2023~FY2024_Q3 부재는 **정상**(공시서식 도입 전) — hole 아님.
- 일부는 FY2023부터 보유(NH농협손보·하나손보), 일부는 FY2025_Q4만(AIG).
- **섹션 자체 부재 3사**: 미래에셋(KR0079)·농협생명(KR0104) — IFRS17 민감도만 공시(별개 표, 혼동 금지); **AIA(KR0080)는 MD가 4.5절에서 끝남 = 변환 절단 의심 → 원본 PDF 대조 필수, 진짜 부재인지 확인.**
- 재확인 대상: KB손보(KR0010) FY2025_Q4 서브표 부재 주장, BNP(KR0075) FY2025_Q4 문서가 IFRS-형식만(소스 오선택 의심), KR0010 FY2023_Q4 MD 파일 자체 누락.
- 추출 원칙: **있는 곳 전부 추출 + diag에 per-(사,분기) status 기록** (`extracted / absent_section / absent_subtable / post_dash / delta_converted / suspect_truncation`).

## 5. 검증 룰 (validation 스테이지)

| id | 내용 | tol / severity |
|---|---|---|
| **RS1_RATIO_IDENTITY** | 각 (사,분기,경과조치)·각 컬럼 c: `비율[c] ≈ 금액[c]/기준금액[c]×100` | `max(0.5%p, 0.5%·\|비율\|)` / **RED→reparse** (delta 오변환·행 오매핑 검출기) |
| **RS2_BASE_ANCHOR** | base 컬럼 vs `kics_disclosure.json` 동일 (사,분기): 적용전 base금액≈item1, base기준금액≈item14, base비율≈item27. 적용후는 `값_적용후` 있을 때만 | 금액 2억 / 비율 0.5%p / **RED→reparse** (양쪽 중 한쪽 파싱오류) |
| RS3_DIRECTION_SANITY | 생보: 금리하락 시 비율하락이 통상(부채듀레이션>자산). 역방향은 플래그만 | — / YELLOW (회사별 ALM에 따라 정상일 수 있음) |
| RS4_COVERAGE_CENSUS | 실측 매트릭스. 같은 회사가 인접 분기 보유한데 사이 구멍 → YELLOW. Q2/Q4 반기 regime 확립되면 regime 내 hole만 RED 승격 | — / YELLOW(초기) |

validator 출력 JSON → `scripts/consolidate_inbox.py` `VALIDATORS`에 핸들러 추가 (route: reparse).

## 6. 파이프라인 배선

1. **parser**: `scripts/extract_kics_rate_sensitivity.py` (결정적 스크립트, 에이전트가 작성·iterate) — `md_inbox/FY*/*.md` 스캔 → 루트 `kics_rate_sensitivity.json` + `data/_derived/kics_rate_sensitivity_diag.json`(status census).
2. **validation**: §5 룰 구현 (`scripts/validate_kics_rate_sensitivity.py` 또는 기존 validate 러너 확장) → RED는 inbox loopback (max 5).
3. **publishing**: RED 0 게이트 통과 후 마스터 확정. (site 패널은 designer 후속 — 이번 범위 밖.)
4. FY2026_Q1: md_inbox 미생성(PDF만 입수) — MD 변환 완료 후 동일 스크립트 재실행으로 흡수.

## 7. 변경 이력
- 2026-06-10: 초안. 38사 서베이 → 스키마·변형 카탈로그·RS1–4 codify.
