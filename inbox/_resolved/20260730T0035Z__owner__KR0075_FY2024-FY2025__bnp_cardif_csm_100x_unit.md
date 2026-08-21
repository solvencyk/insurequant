---
from: owner
to: parser
created: 20260730T0035Z
status: resolved
route: reparse
company: KR0075
period: FY2024,FY2025
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

**KR0075 비엔피파리바카디프생명보험의 CSM_waterfall 전 항목이 100배 과대**로 마스터에 들어가 있다.
라이브 index.html 헤드라인 KPI `업계 총 기말 CSM`이 **163.8조로 오표시**된다(정상 133.8조 — 이 회사 하나가 30조를 밀어올림).

### 현재 값 (CSM_waterfall.json)

| 공시분기 | 항목 | 현재 값(억) | ÷100 (추정 정답) |
|---|---|---|---|
| 2024.4Q | 6 기말 CSM | 288,755.8 | 2,887.6 |
| 2025.4Q | 1 기초 CSM | 288,755.8 | 2,887.6 |
| 2025.4Q | 2 신계약 CSM | 12,846.5 | 128.5 |
| 2025.4Q | 3 이자 부리 | 5,481.3 | 54.8 |
| 2025.4Q | 4 가정 및 경험 조정 | 56,295.7 | 563.0 |
| 2025.4Q | 5 CSM 상각 | -63,795.4 | -637.9 |
| 2025.4Q | 6 기말 CSM | **299,583.9 (29.96조)** | 2,995.8 |

### 근거 (전수 측정 — 재조사 불필요)

1. **동종 대비 불가능한 규모**: 기말 CSM 29.96조는 삼성생명(13.6조)·삼성화재(14.5조)의 2배. 35사 중 1위.
2. **자체 K-ICS와 모순**: 같은 회사 2026.1Q 지급여력금액 **1,958억**, 지급여력기준금액 882억 (kics_disclosure.json 항목1/14).
3. **35사 전수 이상치 census** — `기말CSM ÷ K-ICS 지급여력금액` (둘 다 억 단위, 35/35 조인 성공):
   - KR0075 = **153.01** ← 유일 이상치
   - 차순위 KR1098 카카오페이손보 = 3.49, KR0076 아이엠라이프 = 1.00, 중위값 ≈ 0.56, 최소 KR0029 AIG = 0.15
   - **÷100 하면 KR0075 = 1.53** → 정상 대역 안으로 정확히 들어온다. 100배 배율 가설 확정.
4. **항등식은 닫혀 있다** (기초+신계약+이자+조정+상각 = 기말). 즉 행 매핑·부호 오류가 아니라 **열 전체 단위 스케일 누락** 시그니처 = 백만원을 억원으로 그대로 기입(1억 = 100백만, ÷100 누락).

### 추적 단서

- `data/dart/extracted/`에 **KR0075 산출물이 없다** (26개사만 존재, BNP 부재). 그런데 마스터에는 2024.4Q·2025.4Q 행이 있다 → 어느 경로로 들어왔는지 추적 필요.
- `data/dart/FY2026_Q1/raw/KR0075_비엔피파리바카디프생명보험/`에는 `meta.json`만 있음.
- `CSM_waterfall_provenance.json` cells: KR0075 2024.4Q·2025.4Q → `source_id: DART`, `item_block: csm_waterfall`.
- **raw XML이 트리에 없으면 `route: refetch`로 downloader에 넘겨라** (git purge로 raw가 날아간 이력 있음 — FY2024 분기 cell 재현불가 전례).

### 요청

1. raw에서 원 단위 확인 → ÷100 정정 (또는 실제 raw 단위에 맞는 정확한 배율).
2. `NB_CSM_multiple.json`의 KR0075 `신계약CSM_연누계`도 **12,846.5로 waterfall 항목2와 동일** → 같은 배율 오류가 전파돼 있다. 동시 정정.
3. `CSM_waterfall.json` 재빌드 후 골든 재생성 필요 시 `--update` + 커밋에 사유 기록 (해시 수기 수정 금지).
4. **회신 요청**: KR0075의 `신계약CSM배수_연누계`가 null인 이유 — 월납초회보험료 미공시인가, 0인가, 추출 누락인가? legit-zero면 owner registry 등재 대상. (같은 질문이 KR1011 IBK연금보험 — NB 마스터에 행 자체가 없음 — 에도 적용된다. 연금사 일시납 구조라 legit인지 추출 누락인지 확인해달라.)

### 연관

- `inbox/designer/20260730T0035Z__owner__MULTI__csm_bubble_annual_filer_estimates.md` — 보조표에 35사 전원을 노출하는 작업이 이 정정을 기다린다. 정정 전까지 designer는 KR0075 수치를 `검증중`으로 가린다.
- 포스트모템 후보: 기말 CSM에 **동종 대비 규모 sanity(예: CSM ÷ 지급여력금액 상한)** 룰이 없어 30조가 게이트를 통과했다. false-green. 정정 후 incident-postmortem 관행에 따라 룰 배선 위치까지 기록할지 판단해달라.

## 답변 (parser/ifrs17 2026-07-30 — 100배 확정, override로 정정 완료, raw는 downloader 발주)

owner 분석(항등식 양쪽 닫힘 + 35사 census KR0075=153.01 유일 이상치) **그대로 확정**. raw XML은 이
브랜치에서 없음(`meta.json` 49바이트뿐, `data/dart/extracted/`에도 산출물 부재) — 재파싱으로 검증
불가하여 산술 근거로 override 정정:

1. **`CSM_waterfall.json`** — `data/dart/viz/csm_manual_overrides.json`에 KR0075 12셀(2024.4Q·2025.4Q ×
   항목1-6) ÷100 override 추가(각 셀 `why`에 근거 전문) → `build_root_masters.py` 재실행으로 반영.
   기말 CSM: 2024.4Q 288,755.8→**2,887.558**억 / 2025.4Q 299,583.9→**2,995.839**억. 항등식 재확인(양쪽
   스케일에서 정확히 닫힘, misparse 아님을 재확증). `validate_csm_waterfall.py` 재실행 — KR0075 fail
   목록에 없음(회귀 없음, 기존 fail 21건은 라이나/메트라이프/AIA/처브/하나생명/IBK — 전부 별건 기지 이슈).
2. **`NB_CSM_multiple.json`** — KR0075 2셀(신계약CSM_연누계 9831.2→**98.312** / 12846.5→**128.465**)
   직접 정정. **배수 null 원인 확정**: 100배 오염 상태에서 신계약CSM÷월납월초 비율이 ~103×로 나와
   `_MULT_CAP=40` 가드에 걸려 null 처리되고 있었던 것 — 추출누락/미공시 아니었음. 정정 후 재계산:
   2024.4Q 배수 **1.0309** / 2025.4Q 배수 **0.8611**(정상 대역). ⚠️ 단, `NB_CSM_multiple.json` 전체
   공식 재빌드(`build_nb_csm_multiple.py`)는 `data/kidi/premium_summary.json`이 로컬에 없어(gitignore
   대상, KIDI raw는 있으나 집계파일 부재) 현재 불가 — 이번 2셀은 기존 파일 직접 patch. IBK연금보험
   (KR1011) 질문 관련: **KR1011은 NB_CSM_multiple.json에 행 자체가 없음**(CSM_waterfall.json엔 3개년
   18행 존재, 2026-07-04 온보딩) — 이건 legit-absent도 추출누락도 아니라 **온보딩 후 NB 빌더 재실행이
   안 됐고, 그 재실행이 premium_summary.json 부재로 현재 막혀 있는 것**(모든 회사 공통 제약, IBK 특정
   아님). 연금사 일시납 구조 여부와 무관 — TODO에 별도 기록.
3. **`CSM_waterfall_provenance.json`** — `scripts/emit_ifrs17_provenance.py` 재실행으로 KR0075 2셀
   `owner_override: true` 자동 반영 확인.
4. **raw 근본 fix** — `inbox/downloader/20260730T0100Z__parser__KR0075_FY2024-FY2025__bnp_cardif_raw_refetch.md`
   로 refetch 발주(FY2024_Q4·FY2025_Q4 연간결산). raw 회신 오면 override를 진짜 재파싱값으로 교체.
5. **포스트모템** — `docs/postmortems/PM-2026-07-30_kr0075_csm_100x_unit.md` 작성(README UH-6 등재).
   결론: `CSM_ABS_CAP=5e5`(절대값 가드)가 이 케이스(최대 34.2만억, cap 미만)를 놓침 — **상대규모
   가드가 없었던 게 근본원인**. `CSM_WATERFALL_PLAUSIBILITY`(기말CSM÷K-ICS지급여력금액, median×20)
   룰 신설을 validation에 발주(`inbox/validation/20260730T0040Z__parser__MULTI__csm_magnitude_plausibility_rule.md`).
6. **master xlsx** — publishing 소관(공식 `xlsx` skill), 이 세션에서 미실행. publishing이 다음 진행 시
   `insurequant_master_tables.xlsx` 재생성 필요.
7. **designer 연관** — `inbox/designer/20260730T0035Z__owner__MULTI__csm_bubble_annual_filer_estimates.md`가
   이 정정을 기다린다고 했음 — 데이터 정정 완료됐으니 designer는 KR0075를 '검증중' 대신 정상 표시로
   전환 가능(단 override 상태임은 유지 — raw 확정 전까지 provisional 뉘앙스 권장, designer 판단).

라이브 반영: `CSM_waterfall.json`/`NB_CSM_multiple.json`/`CSM_waterfall_provenance.json` 3개 root 파일
직접 수정 완료(별도 rebuild 세션 불요 — build_root_masters.py가 diag+override만 읽어 안전).

---

### 종결 (owner status-sweep, 2026-08-20)

KR0075 12셀 ÷100 override + NB 2셀 직접 정정(배수 null이 _MULT_CAP 가드였음을 확정). 3개 root 파일 반영, validate_csm_waterfall 회귀 없음. 항목 1~7 전부 disposition.
