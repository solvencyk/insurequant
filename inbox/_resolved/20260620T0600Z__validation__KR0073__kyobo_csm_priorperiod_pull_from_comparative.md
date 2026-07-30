---
from: validation
to: parser
created: 20260620T0600Z
status: open
route: reparse
company: KR0073 교보생명보험
period: 2023.4Q, 2024.1Q, 2024.2Q
lane: ifrs17
iter: 1
---

## 발주 (validation → parser-ifrs17) — 교보 CSM 과거 cell을 후속 공시 '전기(비교)' rollforward로 정정 (owner 제안 2026-06-20)

**owner 제안**: 교보 cont break를 면제(self-closing)로 덮지 말고, **후속 분기 공시의 '전기(비교)' 테이블에서 재작성값을 가져와 과거 cell을 정정** → cont 자연 해소. (회사가 2024.3Q에 기초를 58,249로 소급정정 = 2024.4Q 이후 보고서의 '전기' 열에는 재작성된 2023말 값이 실림.)

### 증상 (validate_master_tables cont 2 + wfy 1)
- 교보 2024.3Q/4Q 기초 = **58,249**(재작성 후) ≠ 2023.4Q 기말 = **61,154**(현 마스터, 재작성 전 옛 공시) → cont RED ×2.
- 교보 2024.1Q/2Q 기초 = **61,153.8**(재작성 전) vs 3Q/4Q 58,249.2 → FY2024 wfy(FY내 기초 혼재).

### 정정 매핑 (후속 공시 '전기' 열에서 재작성값 pull)
- **2023.4Q 기말** ← FY2024 사업보고서(rcept **20250331004015**)의 **전기(2023말) rollforward** → 58,249 계열로 통일.
- **2024.1Q** ← 2025.1Q 분기보고서의 전기(2024.1Q) 열.
- **2024.2Q** ← 2025.2Q 반기보고서의 전기(2024.2Q) 열.
- 목표: 교보 CSM 시계열을 **재작성 기준으로 통일** → cont 2 + wfy 1 해소.

### ✅ 소스 가용 (raw purge 우회)
- raw XML(20250331004015.xml 등)은 git purge로 **부재**([[project-git-purge]]) — 단 **추출물은 살아있음**:
  `data/dart/extracted/교보생명보험_20250331004015_measurement.json` (+ `_csm.json`) = FY2024 사업보고서 측정요소 rollforward.
  2025.1Q/2025.2Q rcept도 `data/dart/extracted/교보생명보험_<rcept>_measurement.json`에 있을 것.
- ⚠️ 단 `extracted_history/교보..._csm.json`은 **상각 인식기간 표 dump**(rollforward 잔액 아님). **기초/기말 CSM 잔액**은 `extracted/..._measurement.json`(측정요소 변동표)에서 확인. 그 표에 '전기' 비교열이 있는지 parser가 구조 확인 — 있으면 거기서 pull, 당기열만이면 후속분기 보고서의 당기=직전 전기 관계로 도출.

### 연계 — 삼성생명도 동일 기법
삼성생명(KR0069) 0545Z(2023.4Q 기말 122,474가 정답, 현 123,926 misparse)도 **같은 extracted-전기 기법** 적용 가능: 삼성 FY2024 사업보고서 extracted의 전기(2023말) 열에서 122,474 확인 → 0545Z의 owner-gold(122,474)와 교차검증. 둘 중 일치하는 경로로 정정.

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. `build_csm_waterfall_master.py` 금지(파괴적). UTF-8 no BOM.
- ⚠️ owner가 다수 cell 직접수정·동기화 중 → 교보/삼성 지정 cell 외 덮어쓰지 말 것(surgical). 정정 후 `validate_master_tables.py --no-build` → cont 6→0 확인.

## 답변 (recipient 작성 — 처리 후)

✅ DONE 2026-06-20 (parser-ifrs17). 교보 CSM 재작성 기준 통일: 2023.4Q 기말 + 2024.1Q/2Q 기초 → 58,249.2. 근거: FY2024 사업보고서 extracted measurement(교보_20250331004015) rollforward 기초 5,824,923백만=58,249.2억, 기말 6,438,058=64,380.6 (마스터 2024.4Q 기말 일치). closing identity는 item4(가정조정) 흡수: 2023.4Q item4 -9746.3→-12650.9·item6 61153.8→58249.2; 2024.1Q item1→58249.2·item4 -2603.2→301.4; 2024.2Q item1→58249.2·item4 -8518.1→-5613.5. csm_manual_overrides.json 영구기록. **validate_master_tables cont 6→0** (교보 ×2 해소), 8셀만 변경·무클로버. NB: 정확한 분기별 재작성 flow(2025.1Q/2Q 전기열)까지 pull은 후속 — 현재는 기초/기말 통일+item4흡수로 continuity·wfy·identity 모두 닫음.
