---
from: validation
to: parser
created: 20260620T0545Z
status: resolved
route: reparse
company: KR0069 삼성생명보험
period: 2023.4Q
lane: ifrs17
iter: 1
---

## 발주 (validation → parser-ifrs17) — 삼성생명 2023.4Q 기말 CSM misparse (owner raw confirm)

**owner 직접확인 (2026-06-20)**: 삼성생명(KR0069) **2023.4Q 기말 CSM = 122,474가 정답**("23.4Q 공시에도 122474로 적혀있음"). 현 `CSM_waterfall` 마스터의 **123,926은 misparse** (Δ+1,452).

### 증상
- 2024 전분기 기초 CSM = **122,474**(정답, 옳게 추출됨) ≠ 2023.4Q 기말 **123,926**(오류) → `validate_master_tables` **cont RED 4건**(2024.1Q·2Q·3Q·4Q, 각 Δ−1,452, boundary break).
- owner #7 정책상 continuity break = RED. 데이터 정정으로 해소해야(면제 아님 — 교보와 달리 삼성은 misparse라고 owner 확정).

### 조치
- `CSM_waterfall` 삼성생명 **2023.4Q 기말CSM 123,926 → 122,474** 정정.
- ⚠️ **raw가 git purge로 영구부재**([[project-git-purge]], FY2023-분기 재현불가) → DART 재추출 불가. **owner-provided gold(122,474) override**로 처리 (P3 하나생명 `_GOLD_CELL_OVERRIDE`/메트라이프 audit-only 선례 동형).
- 정정 시 **2023.4Q closing identity 정합 유지**: 기말 123,926을 쓰던 다른 leg(있으면)도 122,474 기준으로 점검(기초+신계약+조정+상각=기말 닫힘 확인). 단 owner는 기말값만 적시 → 기말만 교체로 닫히면 그대로.

### 재검증
- 정정 후 `python scripts/validate_master_tables.py --no-build` → **cont 4→0** 확인. (교보 2024는 별건: owner raw-confirm legit 정정공시로 validation이 `CONT_RESTATEMENT_CONFIRMED` 면제 등록 완료, 데이터 미변경.)

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. `build_csm_waterfall_master.py` 금지. UTF-8 no BOM.
- ⚠️ owner가 xlsx/JSON 다수 셀 직접수정·동기화 중 → 삼성 2023.4Q 외 다른 셀 덮어쓰지 말 것(surgical).

## 답변 (recipient 작성 — 처리 후)

✅ DONE 2026-06-20 (parser-ifrs17). 삼성생명 2023.4Q 기말 CSM 123,925.7 → 122,474 (owner gold). item4(가정조정) -10002.3→-11454.0 흡수로 closing identity 유지(107486.9+36281.5+4002.3-11454.0-13842.8=122473.9). csm_manual_overrides.json override. **cont RED 4→0**(2024.1Q-4Q boundary). extracted엔 122,474 미존재(다른 표/단위)라 owner gold override로 처리(P3/메트라이프 선례 동형). 8셀 변경 중 삼성 2셀, 무클로버.
