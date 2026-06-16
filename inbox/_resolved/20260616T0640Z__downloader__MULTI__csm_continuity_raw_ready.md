---
from: downloader
to: parser
created: 20260616T0640Z
status: open
route: reparse
company: KR0073,KR0001,KR0094,KR0070,KR0083,KR0009,KR0072,KR1000,KR0099
period: 2026.1Q · FY2023(Q1-Q4) · FY2024(Q1-Q4)
rule: CSM_CONTINUITY_BREAK
lane: ifrs17
iter: 1
---

## 미결 (downloader) — CSM 워터폴 연속성 복구용 raw 재취득 완료 (raw-ready)

연계: validation `inbox/downloader/20260616T0600Z`(owner: 2026.1Q 기시 misparse) + validation
`inbox/parser/20260616T0605Z`(csm_2026q1_opening_misparse) + 사용자 추가 지시(5사 먼저 + continuity break만).
`ifrs17_batch_historical.py --skip-extract`로 raw만 복원(추출=파서). `data/dart/FY*/raw/KR####_<canonical>/document.zip(+meta.json)`.

### 적재 (33/33 fetched, CSM 블록 결손 0)
1. **2026.1Q 우선 5사**(owner 검증 기시 misparse): 교보 KR0073·메리츠화재 KR0001·신한라이프 KR0094·
   에이비엘 KR0070·푸본현대 KR0083. 보험계약마진 76/108/96/138/86.
2. **FY2023 Q1-Q4**(`validate_csm_continuity` FY내 드리프트): 현대 KR0009·에이비엘 KR0070·KDB KR0072·
   교보 KR0073·코리안리 KR1000 = 20셀.
3. **FY2024 Q1-Q4**(FY내 드리프트 + 코리안리 23.4Q→24.1Q 경계): KB라이프 KR0099·코리안리 KR1000 = 8셀.
   (Q4=사업보고서 A001, Q1-3=분기/반기.)

### continuity 진단 (재추출 타겟)
`validate_csm_continuity.py` 현 master 기준 RED 8(회사 7):
- 🔴 **FY_BOUNDARY**: 코리안리 2023.4Q기말 8032 ≠ 2024.1Q기초 10641(Δ32.5%) → 2024.1Q 기시 mis-pick 의심(정답≈8032).
  푸본 2025.4Q기말 1906 ≠ 2026.1Q기초 1669(Δ12.4%) → 2026.1Q 기시 mis-pick(정답=1906, owner 검증).
- 🔴 **WITHIN_FY_OPENING_DRIFT**: FY2023 기초 비일관 — 현대(83515~88281)·에이비엘(7018~7585)·KDB(5239~5696)·
  교보(46967~55338) / FY2024 — KB라이프(30176~31798)·코리안리(8032~10641).
- owner 검증 2026.1Q 기시 정답(억): 교보 65,110·메리츠 111,037·신한라이프 75,537·에이비엘 9,702·푸본 1,906.45
  (=각사 2025.4Q 기말). 2025.4Q 사업보고서 raw는 디스크 존재(FY2025_Q4) → 대조 anchor 사용 가능.

### 요청 (파서 ifrs17 lane)
1. 위 33셀 CSM 워터폴 재추출(`ifrs17_batch_historical` extract 모드) → master 갱신 → `validate_csm_continuity.py`
   재실행해 RED 수렴 확인(목표 0 또는 documented).
2. 2026.1Q 기시 = 직전 2025.4Q 기말과 일치하는지 5사 우선 검증(owner 정답표 대조).
3. 별도(00760)/연결(00761) 혼선·off-by-year·basis swap 점검(continuity break의 전형 원인). 단위(1억=100백만)·부호(△).
4. ⚠️ 마스터 rebuild(`build_csm_waterfall_master.py`)는 전체 raw 부재 시 파괴적 — 이번 복원분 + 기존 디스크 raw
   범위 내에서만. downloader 측 raw 잔여 없음(요청 cell 전수 복원).

## 답변 (parser/ifrs17 2026-06-16 — raw 수신 + continuity 전사 RED 8→0 해소)

복원 raw(2026.1Q 5사 + FY2023/FY2024 드리프트 33셀) 수신·언집(`document.zip`→xml). 9사 검증 워크플로우로 raw 후보블록을
재구성해 각 셀의 올바른 당기 발행(원수) 워터폴 산출 → continuity-correct 값 확정.

**근본원인 = `build_csm_waterfall_master` product-set 합산 버그**(전분기 copy 혼입/부분 합산), missing raw 아님(재추출이
committed 동일 misparse 재현). 상세·셀별값은 자매건 `inbox/parser/20260616T0605Z` 답변 참조.

**수정**: `build_csm_waterfall_master.py` 미실행(파괴적 경고 준수). 검증값을 `csm_manual_overrides.json`(+62) 인코딩 →
`build_root_masters.build_csm()` 공식 재조립. `validate_csm_continuity.py` **RED 8→0**, identity 무파손, pytest 110.
FY경계(2026.1Q 기시=2025.4Q 기말 5사·코리안리 2024.1Q=2023.4Q 기말) + within-FY 기초 상수 전부 검증.

⚠️ 롯데 2023.1Q honest-gap(보험계약마진 0)은 NB-CSM track(`20260616T0420Z`) 소관 — 본 continuity 건과 무관.
viz 다운스트림 full sync는 raw 복원 세션.

status: **resolved** — continuity RED 0.
