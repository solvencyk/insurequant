---
from: downloader
to: parser
created: 20260616T0210Z
status: open
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

