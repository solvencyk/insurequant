# Agent: IFRS17 DART Disclosure

**목표:** 금감원 DART 분기/반기/사업보고서(비상장·외국계는 감사보고서)에서 IFRS17 관련 주요 재무 테이블 파싱.

> 운영 상세(회사별 함정 포함) = `.claude/skills/ifrs17-parser/SKILL.md`. 현재 커버리지(회사·분기·행수)는 `scripts/status_report.py --fast` 가 정본이다.
> 2026-10-07 정리 전 전문(2026-07-22·08-28·08-29 조사 기록, 2026-05 PoC 결과, Q1–Q9 문답 원문)은 [`claude-agent-ifrs17_history.md`](claude-agent-ifrs17_history.md).

## 운영 규칙 — 손대기 전에 읽을 것

- **PL 빌더는 패키지다.** `scripts/build_pl_breakdown.py`(엔트리: 24항목 `assemble`·`_GOLD_CELL_OVERRIDE`) + `scripts/pl_breakdown/`(`common`·`tier1`·`tier2`·`companies`).
  회사별 주석 대응은 `pl_breakdown/companies.py` 에 함수를 추가하고 파일 끝 `SONBO_HANDLERS` / `LIFE_HANDLERS` 에 **등록**한다(등록 안 하면 죽은 코드).
  의존은 단방향(`companies → tier1/tier2/common`).
- **골든**: PL 빌더·핸들러를 고치면 `RUN_PL_GOLDEN=1 python -m pytest tests/test_pl_breakdown_golden.py`(~95~180초) ·
  `fill_post_transition_to_disclosure.py` 는 `tests/test_post_transition_golden.py` · viz 빌더는 `tests/test_viz_{ifrs17_panels,csm_waterfall}_golden.py`
  (인플레이스로 덮어쓰는 빌더라 골든이 백업·복구한다). 값이 의도적으로 바뀐 경우에만 `--update` + 커밋에 이유.
- **DART FS 캐시 정정공시**: `_fetch_raw` 는 캐시를 만료 없이 신뢰한다. 정정공시가 뜨면 `python scripts/fetch_dart_fs.py --refresh <corp_code> <year>`
  → 마스터 재빌드 → PL 골든 재생성 → 캐시+마스터+골든 함께 커밋(owner 정책: 캐시는 커밋).
- **gold override 는 두 겹이다.** 루트 `PL_breakdown.json` 은 `data/_gold/user_pl_cells.json` 이 빌드 마지막에 UPSERT 해서 보호된다.
  빌더 산출 `pl_breakdown_master.json` 은 `_GOLD_CELL_OVERRIDE` 에 있는 칸만 보호된다 — 원천 결함을 고친 칸은 **두 곳에 다** 넣는다
  (예: KR0083 2024.3Q 항목27/28/30 은 DART FS-API 부호반전 결함이라 둘 다 등재).
- **`build_root_masters.py main()` 통짜 실행 금지** — 개별 `build_pl()`/`build_csm()` 만 호출하고 combo-diff(셀 키 전수)로 손실 0 확인.

### PL 폐쇄식이 원리상 못 보는 항목

`assemble()` 이 잔차로 만드는 항목이 있어서 그 항목을 우변에 갖는 등식은 **산수상 깨질 수가 없다**.

| 항목 | 계산식 | 그래서 무검사가 되는 항목 |
|---|---|---|
| item7 기타생명장기원수손익 | `3 − (4+5+6)` | **5(원수RA) · 6(원수예실차)** |
| item12 기타생명장기재보험손익 | `8 − (9+10+11)` | **9(재보험CSM상각) · 10 · 11** |
| item18 투자이익 | `17 − 19` | **19(보험금융손익)** |
| item21 영업외손익 | `22 − 20` | — |
| item23 법인세 | `22 − 24` | **23(법인세)** |

- **예실차(item6)를 채우거나 고칠 때는 원문 표 재판독(독립 앵커: 보험수익·소계)만이 검증이다.** `3 = 4+5+6+7` 이 닫히는 것은 증거가 아니다.
- **item9 는 대안 축이 없다** — CSM 워터폴은 출재를 배제한다(배제가 옳다: 출재는 보유 재보험계약자산의 별도 워터폴). 만들려면 출재 rollforward 를 별도 마스터로 추출해야 한다.
- item22 는 `validate_master_tables._check_tax22_crosscheck`(게이트 2f, 원천 법인세 계정 대조)가 본다.
- 코드: `validate_master_tables.PL_EQ_EVIDENCE` · `PL_ITEMS_UNCHECKABLE_BY_EQUATION`, 매니페스트 `PL_CONSTRUCTIVE_BLIND` / `PL_CONSTRUCTIVE_GUARDED`.

### 기타포괄손익 항목 25–32

- 항목25(OCI 총계) ≠ sum(26–30) 의 지배적 원인은 "API 불완전" 이 아니라 **우리 5-슬롯이 원천 leaf 전체보다 좁은 것**이었다(확정급여 재측정·해외사업환산·재평가·FVOCI 신용손실·관계기업 OCI 지분 등).
  그래서 **항목32 `기타 포괄손익(미분류)`** 를 catch-all 로 둔다(`fetch_dart_fs.py::_oci32_from_rows`: CIS 의 item25 행 ~ 다음 `ifrs-full_ProfitLoss` 행 사이 leaf 에서
  소계 2종과 26–30 이 claim 한 것을 뺀 나머지). TAGGED 행은 `"OtherComprehensiveIncome" in account_id` 만, UNTAGGED 행은 윈도 위치로 신뢰하되 문자열 소계는 배제.
  `OCI_NM_FALLBACK` nm-매칭은 tagged 여부와 무관하게 적용된다(이중계상 방지).
- **삼성화재 2023.3Q~2025.3Q** 는 FS-API 가 OCI leaf 를 하나도 안 준다 — 항목26–30·32 가 `None` 인 것이 정확하다(채우려면 raw XML 본문표 파싱).
- 교보생명 2025.4Q 는 CF헤지를 비표준 태그 2개로 이중공시해 `pl_bridge_baseline.json` 에 등재돼 있다.

## 0. 운영 환경 & 회사 매핑 규칙

- **OpenDART API key**는 `.env`의 `OPENDART_API_KEY`에서 읽음 (코드에 박지 말 것, 로그에도 찍지 말 것).
- **회사 매핑은 그냥 회사명으로 검색.** KR0001 ↔ corp_code 8자리 영구 매핑 파일은 만들지 말 것(사용자의 명시적 지시).
- 모듈 `src/ifrs17/`: `config.py`(`.env` 만 읽음) · `opendart_client.py`(`find_corp_codes_by_name` · `list_filings` · `fetch_document_xml`) ·
  `{csm,measurement,bs_snapshot,insurance_pl,reinsurance,sensitivity}_extractor.py` · `row_normalizer.py` · `scoring.py` · `universe.py`.
- 데이터: `data/dart/<period>/raw/KR####_<canonical>/` 원본 · `data/dart/extracted/` 추출 · `data/dart/_fs_api_cache/` FS-API 캐시(커밋).

### 0.2 회사명 검색 주의사항

- substring 매칭이라 모호한 입력은 자회사가 먼저 잡힌다. `"삼성생명"` → 1순위 **삼성생명서비스**(자회사). 풀네임(`"삼성생명보험"`, `"교보생명보험"` 등) 또는 exact 매치 우선.
- AIG손해보험의 DART 이름은 `에이아이지손해보험`. KR0004 의 DART 감사보고서 법인은 **엠지손해보험**(2025-09-03 계약·자산부채를 가교사 예별손해보험으로 이전한 잔여법인)이다.

### 0.3 분석 범위

- **Earnings quality**(CSM release vs 투자수익·IFIE) · **Forward support**(CSM 변동 + 상각 스케줄) · **Reinsurance & risk** · **Assumption fragility**(민감도).
- **측정모형**: 대표값은 **`total_csm`**(3열 합산). 공시가 `수정소급법` / `공정가치법` / `그 외 보험계약` 3열이면 조건부 보존. "대부분 공정가치법" 가정 금지.
- **생보는 `장기` 라벨이 없다 → 전사 합계**를 손보 `장기`와 peer 비교 proxy 로 쓴다(`slice_label=whole_company_life`).
- 손익 분해(PL_breakdown)는 손보 LOB 장기/자동차/일반을 전부 싣는다(§4.3 회사별 택소노미 주의).

---

## 1. 키 지표 테이블 (table_id 인덱스)

| Tier | table_id | 주석 절 (메리츠 기준) | slice |
|---|---|---|---|
| **A1** | `measurement_rollforward` | §14 **(4)** 측정요소별 변동내역 | 원수 × **장기** (생보: **전사**) |
| **A2** | `csm_amort_schedule` | §14 **(7)** CSM 향후 상각 | 원수/출재 × **장기** |
| **A3** | `insurance_pl_detail` | §14 **(5)** 보험손익 상세 | **장기** |
| **A4** | `reinsurance_rollforward` | §14 **(3)(4)** 출재 변동·측정요소 | 출재 × **장기만** |
| **B1** | `bs_snapshot` | §14 **(1)** 자산부채 현황 | **장기** |
| **B2** | `new_business_impact` | §14 **(6)** 최초 인식 계약 영향 | **장기** |
| **B3** | `liability_rollforward` | §14 **(3)** 보험부채 변동 (잔여보장/발생사고) | 원수 × **장기** |
| **B4** | `ifie_bridge` | §14 **(8)(9)** + 손익계산서 | 전사 / **장기** where split |
| **B5** | `assumption_sensitivity` | 리스크관리 주석 가정민감도 | **장기** / 원수 잔여보장 |

주석 번호는 회사마다 다르다 — 캡션·헤더로 찾는다(메리츠는 별도재무제표 주석 `14. 보험계약자산부채`).

---

## 2. Tier A — CSM / 측정요소 롤포워드 (`measurement_rollforward`)

> 기초 CSM + 신계약 CSM − CSM 상각 ± (CSM 조정/비조정) 계리적 가정 변동 ≈ 기말 CSM

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

### 2.3 교차검증

- `csm_amort_pl` ≈ §(5) `당기손익으로 인식한 보험계약마진`; 기말 CSM 합 ≈ §(7) 스케줄 `합계`.

---

## 3. Tier A — CSM 향후 상각 스케줄 (`csm_amort_schedule`)

회계연도별 보험계약마진 상각 표(**장기** 행만 정규화). 회사마다 명칭이 달라 하드코딩 정규식 대신 semantic scoring(`csm_extractor.py`).

### 3.1 표 형태

- **Form A — 포트폴리오 × 연도버킷**(예: 삼성화재 `② 보험계약마진 상각`, 헤더 `1년 … 30년 이후 | 계`).
- **Form A_rows — 시간버킷이 행**(예: DB손해).
- **Form B — 잔여기간 분포 snapshot**(예: 메리츠 `(7) 당기말과 전기말 현재 남아있는 보험계약마진의 향후 상각금액` — `발행한 보험계약`/`장기손해`/`보유한 재보험계약`/`장기손해`).
- 분류 불가는 `unknown`. `form_type` 필드로 저장.

### 3.2 추출기 점수 룰 (`csm_extractor.py`)

| 신호 | 점수 |
|---|---|
| caption에 `보험계약마진` + (`상각` / `예상` / `인식`) | +3 |
| caption에 `보험계약마진`만 | +2 |
| header에 연도 버킷 ≥3개 (행에 있어도 인정) | +2 |
| header에 `년` 텍스트 (위 조건 미만) | +1 |
| header에 `계` / `합계` | +1 |
| caption에 다른 토픽 + CSM 미언급 | -3 |

기본 임계점수 `min_score=4`. 캡션에 `보험계약마진` 이 없으면 score 를 3 으로 cap(IBNR 삼각형 같은 유사 표 배제).

### 3.5 추출기 함정

- **lxml HTMLParser 는 `huge_tree=True`** — 큰 filing(>5MB)에서 기본 tree limit 이 표를 자른다.
- `1) 당기말`, `<당기>` 같은 짧은 enumerator 는 main caption 을 덮어쓰지 않는다(현대해상).
- THEAD 없는 표는 첫 (단위표시 skip 후) body row 가 전부 텍스트면 헤더로 인정(한화생명·흥국화재).
- **DART 숫자 셀은 `<TD>` 가 아니라 `<TE>` 다.** 태그를 확인하기 전에는 0건을 "공시 없음" 으로 읽지 말 것. **키워드 0회 ≠ 원문 없음**(XBRL 축 이름은 영문 토큰).

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

```
csm_dependency     = csm_amort_pl / (insurance_service_result + |ifie_pl| + investment_income)
csm_runway_years   = closing_total_csm / csm_amort_pl
schedule_run_rate  = sum(schedule_buckets_y1_y3) / closing_total_csm
nb_replacement     = nb_effect_csm / csm_amort_pl              # >1 이면 신계약이 상각 상쇄
```

### 4.3 회사별 LOB 택소노미 — 슬롯 이름을 믿지 마라

PL 스키마의 LOB 슬롯(`item2 생명장기` · `item13 자동차` · `item14 일반`)은 공통 서식을 전제하지만 **실제 공시는 회사마다 다르다.**

| 회사 | 원문 LOB 구분 | item13(자동차) 판정 | 근거 |
|---|---|---|---|
| 코리안리재보험 (KR1000) | 생명보험 · 장기보험 · 일반보험 | **미해당(N/A)** — 자동차 컬럼 자체가 없다 | FY2026_Q2 보험수익 분석 공시 컬럼 헤더 |
| 서울보증보험 (KR0150) | 보증 · 해외 · 상해 · 자동차 · 기타 | **실재(값 있음)** — 단 전량 수재 | FY2026_Q1 주석 23: 원수 자동차 `-` / 수재 12,516,475천원 |
| AIG손해보험 (KR0029) | 주석 6-1~6-4 `[장 기|일 반|합 계]` | 자동차 컬럼 없음(공백 유지, `LOB_LEG_NA` 등재는 owner 판정) | FY2024·FY2025 감사보고서 |
| 신한이지손해보험 (KR0051) | 주석 '보험영업손익' 이 LOB 가 아니라 **전환방법**으로 쪼개짐 | 일반모형 → 생명장기 2/3/8, 보험료배분접근법 → 일반 14 (owner 규약) | FY2024·FY2025 |

- `validate_master_tables.py` 의 `lob_na` 축이 "미해당" 과 "추출 실패" 를 구별한다(`NA`=등재된 미해당, `BAD`=등재됐는데 값이 실재). **미해당을 `0` 으로 채우지 마라.**
- 코리안리는 생명 → items 2~12, 장기 → items `2-1`~`12-1`, 일반 → item14(`extract_tier2_coreanre`). 마스터 항목명 "생명장기 손익" 은 이 회사에서 실제로 **생명보험**이다 —
  화면은 `PL_LOB_DISPLAY`(IFRS17.html)로 라벨을 덮는다.

---

## 5. Tier A — 출재 재보험 상세 (`reinsurance_rollforward`)

**출재(held reinsurance)는 Tier A.** 금융재보험 등은 측정요소·narrative 에 섞여 나올 수 있으니 키워드 하드코딩보다 **측정요소·출재 블록 전체 캡처** 우선.

### 5.1 캡션·위치

- §14 **(3)** `출재 … 재보험자산 변동내역` — **장기 출재만**(일반·자동차 출재 블록은 별도 table_id 없음).
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

- **Net reinsurance** = 재보험자산 − 재보험부채 → §(1) `순재보험계약자산` 과 reconcile. 원수 CSM roll-forward 와 **페어**로 저장(`side: direct` | `ceded`).

### 5.4 금융재보험(공동재보험·대량해지) 분리 가능성 — 실측 2026-08-31

**결론: 볼륨·예실차 지표는 분리 공시되지만 손익(PL)과 CSM은 분리되지 않는다.**

- 코리안리 FY2025 사업보고서(rcpNo 20260319001095)에 XBRL 축 `전통형재보험 / 공동재보험`(`CoReinsuranceMember`) 값 셀 996개 — measure 는 **예실차 계열 6종뿐**
  (예상보험금 / 위험보험료 / 보험금 예실차비율 · 예상유지비 / 예정유지비 / 유지비 예실차비율), 하위 축 생명보험·장기손해보험 × 포트폴리오 × 만기구간.
  일반손해보험에는 없다(공동재보험은 item2·item2-1 에만 섞인다).
- 보험손익·CSM·보험수익에는 이 축이 **붙지 않는다**. **대량해지재보험은 키워드 0회**로 불가.
- **연 1회, 사업보고서에만** 있다(FY2023·FY2024 0셀, FY2025 996셀, 2026 분기·반기 0셀).
- 부수 정보: 자산유보형 공동재보험 유보금 잔액 2,243억(2026.2Q 반기 매출채권 주석) · 담보 약정 표 `약정의 유형 = 공동재보험` · 해약환급금준비금 출재비율 산출(감독규정 제7-12조 ①3).

---

## 6. Tier B — BS 스냅샷·신계약·IFIE

- **`bs_snapshot`** — §14 (1): `보험계약부채`, `순보험계약부채`, `보험계약자산`, `재보험계약자산`, `재보험계약부채`, `순재보험계약자산`.
- **`new_business_impact`** — §14 (6): 최초 인식 시 `미래 현금 유출/유입`, `위험조정`, `보험계약마진` — **`비손실계약` / `손실계약`** split.
- **`liability_rollforward`** — §14 (3): `잔여보장(비손실요소|손실요소)` | `발생사고` | `합계`, `손실부담계약집합의 손실 및 환입`. multi-index 헤더라 **즉시 JSON 생성 금지 → 구조 skim → 매핑 승인 → 추출**(삼성화재 3-row header, 보종별 반복 중 장기 블록만).
- **`ifie_bridge`** — §14 (8)(9) + 손익계산서: 투자손익 vs **순보험금융손익**, OCI vs P&L IFIE 누적차.

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

- 캡션: `가정민감도`, `보험위험의 민감도 분석` 등(주석 번호는 회사마다 다름). 축: 위험률 / 해약률 / 사업비 ± shock → **CSM 영향**, **당기손익 영향**.
- 각주(메리츠 등): *「당기손익 영향」= 가정변동으로 CSM 장부금액을 초과하는 최선추정부채 증가분* — CSM runway 와 연결해 해석.
- **현행 파이프라인(2026-06-16~)**: `src/ifrs17/sensitivity_extractor.py` → `scripts/viz_build_ifrs17_panels.py` → `data/dart/viz/sensitivity_heatmap.json` → `IFRS17.html`.
  흥국생명은 상품=행 × 기간 밴드=열 양식이라 별도 경로(`_extract_heungkuk_product_rows`).

---

변경 이력은 `docs/changelog_parser_ifrs17.md`.
