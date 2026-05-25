# Agent: IFRS17 DART Disclosure

**목표:** 금감원 DART 분기/반기/사업보고서에서 IFRS17 관련 주요 재무 테이블 파싱.

## 0. 운영 환경 & 회사 매핑 규칙

- **OpenDART API key**는 `.env`의 `OPENDART_API_KEY`에서 읽음 (코드에 박지 말 것, 로그에도 찍지 말 것).
- **회사 매핑은 그냥 회사명으로 검색.** "메리츠화재" 한 단어 던지면 얼추 나옴. KR0001 ↔ corp_code 8자리 영구 매핑 파일은 만들지 말 것. 사용자의 명시적 지시.

### 0.1 모듈/스크립트 레이아웃 (2026-05-23 부트스트랩)

- 모듈: `src/ifrs17/`
  - `config.py` — `.env`만 읽음 (값/소스 모두 로그 X).
  - `opendart_client.py` — REST 래퍼. 주요 메서드:
    - `ping()` — `status=000` 확인.
    - `find_corp_codes_by_name(query)` — master XML substring 매칭. 첫 호출 시 `data/ifrs17/raw/CORPCODE.xml`을 자동 다운로드 후 캐시.
    - `list_filings(corp_code, bgn_de, end_de)` — 정기공시 목록.
    - `fetch_document_xml(rcept_no, dest)` — filing 본문 zip 다운로드.
  - `csm_extractor.py` — CSM 상각 표 추출기 (semantic scoring, §3.2).
  - `measurement_extractor.py` — §14(4) 측정요소 롤포워드 skim (A1, §2).
  - `liability_extractor.py` — 보험계약부채 구조 skim (B3/P4).
  - `universe.py` — 운영 유니버스·slice 규칙 (Open Q1–Q9).
- 데이터: `data/ifrs17/`
  - `raw/CORPCODE.xml` — 회사명 검색용 마스터 (캐시).
  - `raw/<canonical_corp_name>_<rcept_no>/document.zip + *.xml` — filing 원본.
  - `extracted/<canonical_corp_name>_<rcept_no>_csm.json` — 정규화된 CSM 표 후보.
- PoC 스크립트: `scripts/ifrs17_*.py`
  - `ifrs17_verify_api_key.py` / `ifrs17_smoke_search.py` / `ifrs17_fetch_one_filing.py` / `ifrs17_extract_csm_poc.py` / `ifrs17_batch_poc.py`

### 0.2 회사명 검색 주의사항

- substring 매칭이라 모호한 입력은 자회사가 먼저 잡힘. 예:
  - `"삼성생명"` → 1순위 **삼성생명서비스** (자회사). 진짜 본사는 `삼성생명` (정확 일치).
  - `"삼성화재"` → 1순위 **삼성화재해상보험** (본사). OK.
- `batch_poc`는 `corp_name == query` exact 매치를 우선시하지만, 호출자가 풀네임 (`"삼성생명보험"`, `"한화생명"`, `"교보생명보험"` 등)을 주는 게 안전.

### 0.3 분석 목표 & 범위 (2026-05-23 확정)

**다운스트림 Insight (Product goal):**

- **Earnings quality:** 이 회사 손익이 **CSM release(보험서비스)** 에 기대는지, **투자수익·보험금융손익(IFIE)** 에 기대는지.
- **Forward support:** CSM 변동(기초 → 신계약 → 가정변동 → 상각 → 기말)과 **향후 상각 스케줄**로 “앞으로 수익이 어느 정도 받쳐주는지”.
- **Reinsurance & risk:** 출재 재보험 구조·순원가(마진)·불이행위험이 순손익·CSM에 미치는 영향.
- **Assumption fragility:** 계리적 가정·**민감도** 충격이 LIC/CSM/당기손익에 미치는 규모.

**분석 Slice (보종):**

- **생명·장기 부문만** 집중. 일반·자동차 등 단기 손보 라인은 스크래핑·분석 대상에서 **제외**.
- **손보사:** 주석 14 등에서 **`장기`** 열 (또는 동의어 `생명장기`, `장기손해`).
- **생명보험사:** **`장기` 라벨 없음 → 전사 합계**를 손보 `장기`와 peer 비교 proxy로 사용 (2026-05-24 확정). UI/JSON 메타: `slice_label=whole_company_life`.
- **운영 유니버스 (2026-05-24):** K-ICS 37社 − 비상장 12 − AIG 1 − 서울보증 1 = **실질 23社** (사업보고서 CSM ok). 코드: `src/ifrs17/universe.py`.

**측정모형 (2026-05-24 Q6 확정):**

- 대표값은 **`total_csm`** (3열 합산). “대부분 공정가치법” 가정 **금지**.
- 공시가 **`수정소급법` / `공정가치법` / `그 외 보험계약` 3열**로 분리되어 있으면 **별도 컬럼을 조건부 보존** (material할 때만; downstream은 `total_csm` 우선).
- **VFA(보험료배분접근법):** 1차 로드맵에서 별도 Tier로 두지 않음. §(5) 보험손익 상세에 VFA 블록이 material하면 후속 추가.

**공시 위치 (참고 — 메리츠화재 2024 사업보고서):**

- 별도재무제표 주석 **`14. 보험계약자산부채`** (`*_00760.xml` 등 부속 XML). (1)~(10) 하위 절 + 리스크관리 주석 **가정민감도**.

---

## 1. 키 지표 스크래핑 우선순위 (마스터 인덱스)

| Tier | table_id | 주석 절 (메리츠 기준) | slice | 상태 |
|---|---|---|---|---|
| **A1** | `measurement_rollforward` | §14 **(4)** 측정요소별 변동내역 | 원수 × **장기** (생보: **전사**) | 🔲 PoC (`measurement_extractor.py`) |
| **A2** | `csm_amort_schedule` | §14 **(7)** CSM 향후 상각 | 원수/출재 × **장기** | ✅ PoC (`csm_extractor.py`) |
| **A3** | `insurance_pl_detail` | §14 **(5)** 보험손익 상세 | **장기** | 🔲 미구현 |
| **A4** | `reinsurance_rollforward` | §14 **(3)(4)** 출재 변동·측정요소 | 출재 × **장기만** (일반·자동차 출재 블록 **별도 table_id 저장 안 함** — Q7) | 🔲 미구현 |
| **B1** | `bs_snapshot` | §14 **(1)** 자산부채 현황 | **장기** | 🔲 미구현 |
| **B2** | `new_business_impact` | §14 **(6)** 최초 인식 계약 영향 | **장기** | 🔲 미구현 |
| **B3** | `liability_rollforward` | §14 **(3)** 보험부채 변동 (잔여보장/발생사고) — **§8 multi-index와 동일 테이블** (Q9 통합) | 원수 × **장기** | 🔲 Skimming only |
| **B4** | `ifie_bridge` | §14 **(8)(9)** + 손익계산서 | 전사 / **장기** where split | 🔲 미구현 |
| **B5** | `assumption_sensitivity` | **K-ICS 분기 공시** 가정민감도 (primary); DART 주석은 secondary/future (Q8) | **장기** / 원수 잔여보장 | 🔲 미구현 |

**Minimum viable scrape set (Insight MVP):** A1 + A2 + A3 + **A4** + B1 + B5 (+ 손익계산서 투자·IFIE 라인).

---

## 2. Tier A — CSM / 측정요소 롤포워드 (`measurement_rollforward`)

**CSM 변동분석의 본체.** 사용자 mental model:

> 기초 CSM + 신계약 CSM − CSM 상각 ± (CSM 조정/비조정) 계리적 가정 변동 ≈ 기말 CSM

실제 공시는 IFRS 17 §92 스타일로 더 촘촘함. **CSM 3열 합산** 후 아래 row alias에 매핑.

### 2.1 캡션·위치

- `(4) 원수 및 출재 측정요소별 변동내역` → `1) … 원수 … 보험부채 상세변동내역` (**장기** 블록).
- 헤더 컬럼: `미래 현금흐름의 현재가치 추정치` | `비금융위험에 대한 위험조정` | `보험계약마진(수정소급법)` | `보험계약마진(공정가치법)` | `보험계약마진(그 외 보험계약)` | `합계`.

### 2.2 필수 row keys (정규화 alias)

| alias | 공시 라벨 (예) |
|---|---|
| `opening_net` | `기초 순장부금액` |
| `opening_csm_gmm` / `_fvpa` / `_other` | 기초 행의 CSM 3열 |
| `nb_effect` | `신계약효과` |
| `assumption_adjusts_csm` | `보험계약마진을 조정하는 추정치 변동` |
| `assumption_not_adjusts_csm` | `보험계약마진을 조정하지 않는 추정치 변동` |
| `csm_amort_pl` | `당기손익으로 인식한 보험계약마진 금액` |
| `ra_release` | `위험해제에 따른 위험조정 변동` |
| `experience_adj` | `경험조정` |
| `past_service_cf` | `발생사고의 이행현금흐름 변동` |
| `insurance_service_result` | `보험서비스결과` |
| `insurance_finance_result` | `순보험금융손익` |
| `closing_net` | `기말 순장부금액` |
| `closing_csm_*` | 기말 CSM 3열 |

### 2.3 파서 접근

- **[Skimming First]** §9 legacy와 동일 — 헤더·row stub 먼저 보고, 회사별 YAML 매핑 후 추출.
- **교차검증:** `csm_amort_pl` ≈ §(5) `당기손익으로 인식한 보험계약마진`; 기말 CSM 합 ≈ §(7) 스케줄 `합계`.

---

## 3. Tier A — CSM 향후 상각 스케줄 (`csm_amort_schedule`)

- **타겟:** 회계연도별 보험계약마진 상각 표 (**장기** 행만 정규화).
- **주의사항 (Fuzzy Matching):** 회사마다 공시 명칭이 다름. 하드코딩 정규식 지양, semantic scoring.

### 3.1 관찰된 표 형태 (2026-05-23 PoC)

**Form A — 포트폴리오 × 연도버킷 (예: 삼성화재)**
- 캡션: `② 보험계약마진 상각`
- 헤더: `구분 | 포트폴리오 | 1년 | 2년 | ... | 10년 | 11년~15년 | ... | 30년 이후 | 계`
- 행: Non-Par × N + Indirect-Par × M + 합계

**Form B — 잔여기간 분포 (예: 메리츠화재)**
- 캡션: `(7) 당기말과 전기말 현재 남아있는 보험계약마진의 향후 상각금액은 다음과 같습니다. <당기>`
- 헤더: `구 분 | 1년 미만 | 1~2년 | ... | 30년 이상 | 합 계`
- 행: `발행한 보험계약` / `장기손해` / `보유한 재보험계약` / `장기손해` (4행)

### 3.2 추출기 점수 룰 (`csm_extractor.py`)

| 신호 | 점수 |
|---|---|
| caption에 `보험계약마진` + (`상각` / `예상` / `인식`) | +3 |
| caption에 `보험계약마진`만 | +2 |
| header에 연도 버킷 ≥3개 | +2 |
| header에 `년` 텍스트 (위 조건 미만) | +1 |
| header에 `계` / `합계` | +1 |
| caption에 다른 토픽 + CSM 미언급 | -3 |

기본 임계점수 `min_score=4`.

### 3.3 PoC 결과 (2024 사업보고서)

#### 5-company PoC (2026-05-24 갱신 — 5/5 자동 커버)

| 회사 | 결과 | form_type | 비고 |
|---|---|---|---|
| 메리츠화재 | ✅ 8 tables | unknown | 별도/연결, 본문/부속 중복 |
| 삼성화재 | ✅ 4 tables | A | `② 보험계약마진 상각` |
| DB손해 | ✅ 8 tables | A_rows | 시간버킷이 행에 있음 |
| 한화생명 | ✅ 16 tables | A + unknown | THEAD 없음 → 첫 행 추론 |
| 삼성생명 | ✅ 20 tables | A | `(12) … 기대상각기간별 당기손익인식 예상액` |

#### 37-company batch (K-ICS `원수사명` 전체)

| 상태 | 회사 수 | 비고 |
|---|---|---|
| ok | **23** | CSM 표 자동 추출 성공 |
| no_csm_table_found | 1 | 서울보증보험 (CSM 단어 자체 미존재 — IFRS17/PAA 검증 필요) |
| no_annual_filing | 12 | OpenDART에 사업보고서 미제출 (비상장 보험사) |
| no_corp_match | 1 | AIG손해보험 (DART 매핑 부재 — 외국지점일 가능성) |

**ok 23개사:** DB생명, DB손해, KB라이프, KB손해, NH농협손해, 교보생명, 농협생명, 동양생명, 롯데손해, 메리츠화재, 미래에셋생명, 삼성생명, 삼성화재, 신한라이프, 에이비엘생명, 케이디비생명, 코리안리, 푸본현대생명, 한화생명, 한화손해, 현대해상, 흥국생명, 흥국화재.

**no_annual_filing 12개사:** IBK연금(아이비케이연금), 교보라이프플래닛, 라이나, 메트라이프, 비엔피파리바카디프, 신한이지손해, 아이엠라이프, 악사, 처브라이프, 카카오페이손해, 하나생명, 하나손해. (pblntf_ty=A 정기공시 0건. 외감보고서(pblntf_ty=F) ingest 여부 사용자 결정 필요.)

### 3.4 알려진 한계

- 서울보증보험: 보험계약마진 단어 미존재 (사업 모형 차이 — 보증보험은 PAA 가능).
- AIG손해보험: DART corp_master에 손해보험 본사 매핑 없음.
- 12개 비상장 보험사: 정기공시 의무 미적용. 외감보고서 채널 추가 검토 필요.
- 분기/반기 미실험 (P3 — 사용자 진행 결정 대기).
- form_type=`unknown` 표(메리츠/한화손해 등 16+8): rollforward/snapshot 혼재. P4 보험계약부채 구조 캡처 후 자동 분류 가능.

### 3.5 추출기 강화 이력 (2026-05-24)

`csm_extractor.py` 갱신 — 5개 핵심 룰 추가/수정:

1. **`huge_tree=True`**: lxml HTMLParser가 큰 filing(>5MB)에서 default tree limit으로 표가 잘리는 회귀 방지.
2. **Sub-caption skip**: `1) 당기말`, `2) 2024년 12월 31일 현재`, `<당기>` 같은 짧은 enumerator 라인은 main caption을 덮어쓰지 않음 (현대해상 케이스).
3. **THEAD-less header inference**: THEAD가 없는 표에서도 첫 (또는 단위표시 skip 후) body row가 모두 텍스트면 헤더로 인정 (한화생명/흥국화재).
4. **Body-left-column year buckets**: 시간버킷이 행에 있는 표 (DB손해 `1년, 2년, …` × Non-Par/Indirect-Par) 도 +2 점수.
5. **Hard gate**: 캡션에 `보험계약마진`이 없으면 score를 3으로 cap. DB손해 IBNR development triangle 등 구조적으로 유사하지만 무관한 표 제외.
6. **form_type 분류**: `A` (시간버킷=열), `A_rows` (시간버킷=행), `B` (당기말/전기말 snapshot), `unknown`.

---

## 4. Tier A — 보험손익 상세 (`insurance_pl_detail`)

§14 **(5) 보험손익 상세** — **장기** 열.

### 4.1 필수 row keys

| alias | 공시 라벨 (예) |
|---|---|
| `insurance_revenue` | `보험수익` (하위: `예상보험금 및 보험서비스비용`, `위험해제에 따른 위험조정 변동`, **`당기손익으로 인식한 보험계약마진 금액`**, `보험취득현금흐름의 회수`) |
| `insurance_service_expense` | `보험서비스비용` (하위: `보험금 및 보험서비스비용`, `보험취득현금흐름`, `손실부담계약의 손실 및 환입`) |
| `insurance_service_result` | `총 보험서비스결과` |

### 4.2 Earnings dependency (다운스트림 KPI)

파싱 후 **손익계산서**와 결합:

```
csm_dependency     = csm_amort_pl / (insurance_service_result + |ifie_pl| + investment_income)
csm_runway_years   = closing_total_csm / csm_amort_pl          # §2 × §3
schedule_run_rate  = sum(schedule_buckets_y1_y3) / closing_total_csm
nb_replacement     = nb_effect_csm / csm_amort_pl              # §2; >1 이면 신계약이 상각 상쇄
```

단위·부호는 회사별 P&L 표기에 맞게 후처리 YAML.

---

## 5. Tier A — 출재 재보험 상세 (`reinsurance_rollforward`)

**출재(held reinsurance)는 Tier A.** 금융재보험·대량해지재보험 등은 **`수정소급/공정가치/그 외`** 및 narrative에 섞여 나올 수 있음 — 키워드 `금융재보험` 하드코딩보다 **측정요소·출재 블록 전체 캡처** 우선.

### 5.1 캡션·위치

- §14 **(3)** `출재 … 재보험자산 변동내역` — **장기 출재만** (Q7: 일반·자동차 출재 블록은 slice 규칙과 동일하게 제외, 별도 table_id 없음).
- §14 **(4)** `출재 … 재보험자산 상세변동내역` — FCF / RA / CSM(재보험 순원가) 3열 구조는 원수와 **미러**.

### 5.2 필수 row keys

| alias | 공시 라벨 (예) |
|---|---|
| `opening_reins_asset` / `opening_reins_liab` | `기초 재보험계약자산` / `부채` |
| `premiums_allocated` | `재보험료의 배분` |
| `nb_reins_gmm` / `_fvpa` / `_other` | `신계약효과` (측정모형별) |
| `recoveries` | `재보험자로부터 회수한 금액` |
| `reinsurance_margin` | `재보험 순원가(마진)` |
| `reins_ifie` | `순재보험금융손익` |
| `reinsurer_default_risk` | `재보험자 불이행위험 변동효과` |
| `reins_ifie_other` | `재보험자 불이행위험 외 재보험금융손익` |
| `csm_amort_pl_reins` | `당기손익으로 인식한 보험계약마진 금액` (출재) |
| `closing_reins_asset` / `closing_reins_liab` | `기말 재보험계약자산` / `부채` |

### 5.3 Insight

- **Net reinsurance** = 재보험자산 − 재보험부채 → §(1) `순재보험계약자산`과 reconcile.
- 출재 CSM(순원가) 변동 + **불이행위험** → cedant earnings volatility.
- 원수 CSM roll-forward(§2)와 **페어**로 저장 (`side: direct` | `ceded`).

---

## 6. Tier B — BS 스냅샷·신계약·IFIE

### 6.1 `bs_snapshot` — §14 (1), **장기**

- `보험계약부채`, `순보험계약부채`, `보험계약자산`, `재보험계약자산`, `재보험계약부채`, `순재보험계약자산`.

### 6.2 `new_business_impact` — §14 (6), **장기**

- 최초 인식 시: `미래 현금 유출/유입`, `위험조정`, `보험계약마진` — **`비손실계약` / `손실계약`** split.
- NB economics·적자 신규 비중.

### 6.3 `liability_rollforward` — §14 (3), **장기**

- 컬럼: `잔여보장(비손실요소|손실요소)` | `발생사고` | `합계`.
- **`손실부담계약집합의 손실 및 환입`** — onerous / loss component.
- 파서 난이도 높음 → Skimming First (§9).

### 6.4 `ifie_bridge` — §14 (8)(9) + 손익계산서

- 투자손익 vs **순보험금융손익** 관계; OCI vs P&L IFIE 누적차.
- **투자 의존도** Insight에 필수.

---

## 7. Tier B — 계리적 가정 & 민감도 (`assumption_sensitivity`)

### 7.1 §14 (2) — 현행 추정 가정

| alias | 예시 |
|---|---|
| `mortality_morbidity` | `위험률` |
| `lapse` | `해약률` |
| `expense` | `사업비율` |
| `discount_rate` | `할인율` (범위) |
| `ra_confidence` | `비금융위험에 대한 위험조정 신뢰수준` |

### 7.2 리스크 주석 — 가정민감도

- 캡션: `가정민감도`, `보험위험의 민감도 분석` 등 (주석 번호는 회사마다 다름).
- 축: **손해율(위험률) / 해약률 / 사업비** 등 ± shock → **LIC(잔여보장) 변동**, **당기손익 영향**.
- 각주 (메리츠 등): *「당기손익 영향」= 가정변동으로 CSM 장부금액을 초과하는 최선추정부채 증가분* — **CSM runway와 연결**해 해석.

### 7.3 파서 접근 (2026-05-24 Q8 확정)

- **Primary source: K-ICS 분기 공시** (`kics_disclosure` / md_inbox). DART 주석(§14 (2) + 리스크 민감도)은 **secondary / 추후**.
- `sensitivity_extractor.py` DART batch는 skim PoC일 뿐 — B5 정규화 파이프라인의 primary가 **아님** (방향 오류; K-ICS ingest 우선).
- 표 형태: `가정 | 민감도 | LIC 영향 | 당기손익 영향` (회사별 변형). source 필드로 `kics_disclosure` vs `dart_note14` 구분 저장.

---

## 8. 보험계약부채 multi-index (Skimming First — B3 `liability_rollforward`와 통합, Q9)

- **타겟:** §14 (3) 상세 변동 — multi-index header. **B3 `liability_rollforward`와 동일 테이블** — 별도 트릭·table_id 유지하지 않음 (`liability_extractor.py` = §8 P4 구조 캡처).
- **룰:** 즉시 JSON 생성 금지 → 구조 스kim → 사용자/YAML 승인 → 추출.
- **추천 스키마:** Structural-first (헤더 + values) → long format 후처리 (K-ICS docling→md→정규화와 동형).

### 8.1 삼성화재 2024 관찰 (참고)

- 3-row header: VFA 미적용 그룹 × (잔여보장 손실요소제외/손실요소 | 발생사고 FCF/RA).
- 보종별 반복: 장기 / 일반 / 자동차 — **장기 블록만** 매핑.

### 8.2 P4 PoC (2026-05-24): `src/ifrs17/liability_extractor.py`

후보 C 스키마(원본 무손실)로 구조 캡처. 회사별 YAML 매핑 미작성 (정규화는
별도 단계).

| 회사 | tables | kind 분포 | 비고 |
|---|---|---|---|
| 메리츠화재 | 48 | rollforward 48 | 본문 24 + 부속 24 (별도×연결 / 원수×출재 중복) |
| 삼성화재 | **0** | - | 캡션-표 거리(2500+ 줄) 멀어 last_caption lost. caption stack 도입 시 회복 가능 |
| DB손해 | 14 | rollforward 14 | |
| 한화생명 | 32 | rollforward 32 | |
| 삼성생명 | 8 | rollforward 8 | |

산출물: `data/ifrs17/extracted/<dir>_liability.json`,
`data/ifrs17/extracted/_liability_poc_summary.json`.

스코어링 룰 (csm_extractor와 spirit 동일, 회사별 정규식 X):

- 캡션: BS 키워드(보험계약부채/재보험계약자산 등) ≥2 → +2; rollforward
  키워드(잔여보장/발생사고/측정요소/변동내역) ≥1 → +1
- 헤더: BS 키워드 ≥2 → +3, 1 → +1; rollforward 키워드 ≥2 → +3, 1 → +1
- `kind`: rollforward → snapshot_or_partial → bs_snapshot → unknown 우선순위

기본 임계점수 `min_score=4`.

---

## 9. 생명보험사 특수사항 & 확정 설계 결정 (Q1–Q9)

- **CSM 상각 표:** 한화생명·삼성생명 PoC ❌ — 캡션·XML 분할·표 임베딩 방식 상이. **A1 롤포워드(§2)가 생보의 primary anchor**일 수 있음 (스케줄 없이도 CSM amort·기말 추출 가능).
- **Slice:** `장기` 없으면 **전사 합계** (2026-05-24 Q5 — `생명`/`보험` 키워드 fallback 사용 안 함). 메타 `slice_label=whole_company_life`.
- **VFA:** 변액·VA 비중 큰 생보만 §(5)에서 VFA sub-block 추가 검토.
- **Q6 CSM 3열:** `total_csm` 대표값 + 3열(수정소급/공정가치/그 외) 조건부 보존 (§0.3).
- **Q7 출재:** 장기 출재만 — 일반·자동차 출재 블록 별도 table_id 없음.
- **Q8 민감도:** K-ICS 분기 공시 primary; DART 주석 secondary/future.
- **Q9 B3 vs §8:** 통합 — `liability_rollforward` = §8 multi-index P4 구조 캡처.

---

## 10. 사용자에게 결정 요청할 항목 (Open Questions)

### 답변 받은 항목 (2026-05-23 ~ 2026-05-24)

- ✅ **CSM 추출 커버리지**: 패턴 추가 자동화 (수동 YAML 룰 없이) → 5/5 + 37사 23/37 자동.
- ✅ **CSM 스키마**: Form A + Form A_rows + Form B + unknown 4종을 `form_type` 필드로 캡처.
- ✅ **보험계약부채**: 후보 C (구조 원본 + 회사별 YAML 후처리).
- ✅ **회사 범위**: K-ICS 37개사 전체 (kics_disclosure.json `원수사명`).
- ✅ **보고서 종류**: 사업 + 반기 + 분기 모두 → P2 사업보고서 23/37 완료. P3 반기/분기 확장은 MVP 이후.
- ✅ **archive 정리**: 메인 세션 처리 완료.
- ✅ **CSM PoC 확장 (A2 vs A1)**: A2 (스케줄) 자동 23/37 달성으로 우선순위 정리됨.
- ✅ **Q1 비상장 12사 (2026-05-24):** Skip — **상장 25개만** 운영. 외감(pblntf_ty=F) ingest 안 함. `universe.NON_LISTED_SKIP`.
- ✅ **Q2 AIG손해보험:** Skip — 분석 대상 제외 (`universe.EXCLUDED_SKIP`).
- ✅ **Q3 서울보증보험:** 분석 대상 제외 — PAA-only / `보험계약마진` 없음.
- ✅ **Q4 P3 반기/분기:** **MVP (A1/A3/A4/B1/B5) 완성 후** 진행. 23사 × 2 ≈ 46회 추가 호출 예상.
- ✅ **Q5 장기 slice (생보):** **무조건 전사 합계** — 손보 `장기`와 peer proxy 비교. `universe.expected_slice_policy()`.
- ✅ **Q6 CSM 3열 (2026-05-24):** **`total_csm` 대표값** + 공시가 3열(수정소급법/공정가치법/그 외)로 분리되어 있으면 **조건부 컬럼 보존**. §0.3 규칙.
- ✅ **Q7 출재 범위 (2026-05-24):** **장기 출재만** capture — life/long-term slice 규칙과 일관. 일반·자동차 출재 블록을 **별도 table_id로 저장하지 않음**.
- ✅ **Q8 민감도 source (2026-05-24):** **K-ICS 분기 공시 우선 (primary)**. DART 주석은 **secondary / 추후**. B5는 OpenDART primary가 **아님** — `sensitivity_extractor.py` DART batch는 misaligned skim PoC.
- ✅ **Q9 B3 vs §8 (2026-05-24):** **통합** — B3 `liability_rollforward` = §8 multi-index P4 구조 캡처. 별도 트릭·table_id 유지하지 않음.

### 미답

_(Q1–Q9 모두 확정. 정규화 단계 잔여: crawl manifest 작성 → 23社 full normalization.)_

---

## 11. Changelog

변경 이력은 `docs/claude-changelog.md` (전사 통합 로그) 참조.
