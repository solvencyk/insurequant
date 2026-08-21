---
from: downloader
to: parser
created: 20260616T0210Z
status: resolved
route: reparse
company: KR0004 (예별손해보험 = 구 MG/엠지손해보험)
period: FY2023~FY2025 (annual 결산)
rule: KR0004_DART_AUDIT_MISSING
lane: ifrs17
iter: 1
---

## 미결 (downloader 작성) — KR0004 연도별 DART 감사보고서(별도) raw 적재 완료 (raw-ready)

연계: K-ICS 과거분기 핸드오프 `inbox/parser/20260616T0145Z`(kics lane)의 자매 건 — IFRS17 lane.

### 배경
KR0004는 **비상장 손보사**라 DART 정기보고서(pblntf_ty=A) 0건 → 기존 IFRS17 DART universe
(`src/ifrs17/universe.py`)의 어느 리스트에도 없었음(23 listed/NON_LISTED 12/AUDIT 5/EXCLUDED 2 전부 부재).
즉 **KR0004 DART 데이터가 통째로 0**이었음. 하지만 외부감사법 주식회사라 **연간 감사보고서(pblntf_ty=F)**
를 제출 → 5개 audit-only 외국계 생보사와 동일 경로로 IFRS17 보험계약 주석(CSM 등) 확보 가능.

- DART entity = **'엠지손해보험'**(corp_code `00962861`). 신규 '예별손해보험'(`01974696`)은 아직 filing 0건.
- 회사명 검색으로 확인된 감사보고서 8건(별도/연결 × 2022~2025) 중, **owner 결정대로 별도만·FY2023~** 보존.

### 적재 결과 (canonical audit-annual 레이아웃, 별도 00760)
| period | rcept | dir | IFRS17 키워드(별도 00760) |
|---|---|---|---|
| FY2023_Q4 | 20240408000665 | `data/dart/FY2023_Q4/raw/KR0004_엠지손해보험_20240408000665/` | 보험계약마진 59 · 보험료배분접근법 37 · 신계약 6 |
| FY2024_Q4 | 20250408000587 | `data/dart/FY2024_Q4/raw/KR0004_엠지손해보험_20250408000587/` | 보험계약마진 51 · 보험료배분접근법 31 · 신계약 9 |
| FY2025_Q4 | 20260406003175 | `data/dart/FY2025_Q4/raw/KR0004_엠지손해보험_20260406003175/` | 보험계약마진 36 · 보험료배분접근법 37 · 신계약 7 |

- 각 dir = `document.zip` + `<rcept>_00760.xml`(별도). 5 audit-only사와 동일 구조 →
  `build_csm_waterfall_master`의 `KR0004_*` glob + `blocks_for_dir`(별도 00760 사용, 연결 00761 drop)
  바로 흡수. raw는 gitignore(git 재팽창 무관).
- **owner 스코프 결정**: 별도만·FY2023~. FY2022(IFRS4, pre-IFRS17)·전 연결 = 받았다가 제거(보존 안 함).
  재현 스크립트 `scripts/fetch_kr0004_mg_dart_audit.py`(FILINGS=3건 별도).

### 요청 (파서 ifrs17 lane)
1. 3개 별도 감사보고서 XML → CSM waterfall / 측정요소 rollforward / PL breakdown 추출
   → `data/dart/extracted/` → CSM_waterfall / PL_breakdown 마스터 병합(KR0004 신규 라인).
2. **주의**: 소형 PAA-heavy 손보사 → 신계약 CSM 얇음(신계약 키워드 6~9). PAA(보험료배분접근법) 비중 큼 →
   장기손해보험 GMM 블록 위주로 CSM 잡힘. 라벨변형(계약의 유형 vs 보험료배분접근법) 처리 — ifrs17-parser skill 참조.
3. 민감도(가정민감도) 표 존재 여부 확인 — 있으면 sensitivity_heatmap에 KR0004 추가 가능.
4. 단위(1억=100백만)·부호(△) 회귀 대조. downloader 측 raw 잔여 없음.

## 답변 (parser/ifrs17 2026-06-16 — raw 수신·추출 검증 OK, 통합은 raw-enabled rebuild에 gated)

KR0004(엠지손해보험) 3개 별도 audit raw(FY2023/24/25) 수신 확인. `sensitivity_extractor` recon:

| FY | rcept | sensitivity_analysis | 결과 |
|---|---|---|---|
| FY2023 | 20240408000665 | 1 block / ok 8 scen | ⚠️ risk 라벨 누락("10% 증가 (511,558,916)" — 위험명 미캡처, shock 셀에 값 혼입). 다른 표 form |
| FY2024 | 20250408000587 | 2 block / **ok 6 scen** | ✅ 깨끗: 사망률 3.27%↑·장해질병(정액) 3.40%↑·장기재물기타 4.19%↑·해지율 ↑/↓·사업비 2.62%↑ (csm/pl present) |
| FY2025 | 20260406003175 | 0 block / unavailable | **SA=0 미검출**(분류 실패 — 동양/메트라이프류 phase-2 SA=0과 동일) |

CSM/측정요소/PL 표는 별도 00760에 존재(보험계약마진 36-59 등, downloader 확인대로) — 추출 자체는 동작.

🔴 **그러나 KR0004 통합은 이 브랜치에서 raw-enabled rebuild에 gated:**
1. **CSM/PL 마스터 병합** — `build_csm_waterfall_master`/`build_pl_breakdown`은 `FY*/raw` 디스커버리라 **이 브랜치
   파괴적**(raw purge → 마스터 collapse, [[project-git-purge]]). KR0004 신규 라인 추가는 raw 복원 세션에서.
2. **sensitivity heatmap 추가** — 단위 정규화가 `CSM_waterfall.json`의 사별 기말 CSM로 cross-check하는데 **KR0004가
   아직 마스터에 없어 anchor 부재** → 지금 heatmap에 넣으면 power-of-10 mis-scale 위험(소형 PAA 손보라 더 민감,
   suspect guard도 total 없으면 미작동). KR0004가 CSM_waterfall에 들어간 뒤 **같은 rebuild에서** heatmap 갱신해야 안전.

→ **route: KR0004 통합(extracted JSON 산출 + CSM/PL 마스터 병합 + heatmap)을 raw-enabled rebuild 세션으로.** 그 세션
build가 `blocks_for_dir`로 KR0004 자체추출→마스터→heatmap을 한 번에 처리(FY2024 sensitivity=best, FY2025 SA=0→
FY2024 유지, FY2024 6 scen 채택). 단위(1억=100백만)·부호(△) 회귀 대조는 그 통합 시. FY2023 라벨 누락은 핸들러
보강 별건(필요시). downloader raw 잔여 없음 확인.

status: raw 수신·추출 검증 OK / 통합 = rebuild-gated(파괴적 build + 단위 anchor) → raw-enabled 세션 route.

## 답변 갱신 (parser/ifrs17 2026-07-30 — CSM 통합 완료, PL breakdown 잔여)

위 우려(파괴적 `build_csm_waterfall_master`/단위 anchor 부재)는 **안전한 per-dir 추출**로
우회 해소 — 전체 raw-glob 재빌드 대신 KR0004 3개 dir만 targeted 추출 후 `CSM_waterfall.json`에
직접 upsert. 47개사 전체 diff로 KR0004 외 회귀 0 확인.

- **CSM waterfall — ✅ 완료**: 2023.4Q/2024.4Q/2025.4Q, 항목1-6 전부 적재. Closure 검증:
  2023.4Q 기말(6774.0) = 2024.4Q 기초(6774.0) 정합, continuity 이상 없음.
- **Sensitivity — 이미 반영**: `sensitivity_heatmap.json`에 엠지손해보험 rcept 20260406003175로
  이미 포함(status=`unavailable`, SA=0 미검출 — FY2023/FY2024는 회수됐으나 FY2025 filing 자체가
  분류 실패, 동양/메트라이프류와 동일 유형). 원래 우려했던 "KR0004 마스터 부재로 anchor 없어 heatmap
  추가 불가" 문제는 CSM 마스터 적재로 자연 해소됨.
- **PL breakdown — 🟠 미완, 잔여**: `PL_breakdown.json`에 KR0004 행 0개. `scripts/pl_breakdown/`
  패키지는 회사별 커스텀 핸들러 구조(예: `extract_tier2_hana`)라 신규 소형사 온보딩에 전용 핸들러
  작성이 필요 — 이번 세션 스코프 밖으로 분리, `TODO_parser_ifrs17.md` P2에 등록.

status: CSM 통합 완료(continuity 검증) · sensitivity 이미 반영(documented unavailable) · PL breakdown 잔여(별도 후속).

## 답변 갱신 (parser/ifrs17 2026-08-15 — PL breakdown 핸들러 신설, close)

`scripts/pl_breakdown/companies.py`에 `extract_tier2_yebyeol` 신설 + `SONBO_HANDLERS["KR0004"]`
등록. 별도 감사보고서의 "(N) 당기 및 전기 중 인식된 보험료배분접근법이 적용된 보험계약의
변동내역" note — 자동차보험/일반보험 2개 직접(원수) LOB 테이블만 존재(장기 직접 LOB는
없음 — 이 회사는 장기 리스크를 직접 인수하지 않고 재보험 출재로만 갖는 것으로 확인,
"장기보험-비비례보험"은 별도 재보험(출재) note에서만 발견). 각 LOB 테이블의 "보험서비스결과
소계" 행 합계열 = items 13(자동차손익)/14(일반손익). 재보험(출재) 버전과 캡션이 유사해서
행0 라벨의 "재보험" 접두 유무로 직접/출재 구분.

FY2024.4Q/FY2025.4Q 기존 행(Tier-1만 있던 24행) items 13/14 채움 + **FY2023.4Q 신규
행 24개**(이 연도는 그동안 중간산출물에 아예 없었음 — 이번 재빌드로 처음 편입, items 13/14만
non-null). 전체 재빌드(`build_pl_breakdown.py`, raw-glob discovery) 실행 결과 KR0004 외
company-quarter 손실 0건 확인(combo-diff, HEAD 대비도 0손실) — 이 브랜치 특유의 파괴적
재빌드 함정([[project-git-purge]]) 없이 안전하게 반영됨(raw가 그동안 이 3개 연도분 계속
디스크에 있었던 덕).

items 4/5/6(원수 CSM상각/위험조정변동/예실차, 장기 GMM분)는 이 note에 없음 — item1(보험손익)
대비 13+14 합의 잔차가 큼(FY2024 -59535.8 vs -5300.1, FY2025 -22136.1 vs -13101.4)이라
미확보 장기 GMM 기여분이 상당하다는 신호. 이미 적재된 CSM_waterfall.json의 KR0004 CSM이
어느 note에서 나왔는지도 미확인(다른 세션/방식으로 이미 반영된 것으로 추정). items 4/5/6·
9/10/11(재보험) 확보는 별도 후속 조사 필요 — 우선순위 낮음(소형사, 이미 items 13/14로
Tier-2 부분 커버).

`RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py` + `tests/test_master_tables_golden.py`
재생성·PASS 확인, xlsx 재생성 완료. close.

