---
from: owner
to: parser
created: 20260703T1138Z
status: answered
route: reextract
company: KR0068 (한화생명)
period: FY2025
lane: ifrs17
---

## 미결 (owner site 워크스루) — #7 한화생명 IFRS17 민감도: |ΔCSM| < |ΔPL| 뒤집힘 (컬럼 매핑 오류 의심)

**증상**: 사이트 IFRS17 민감도에서 한화생명 CSM 변동규모가 손익변동보다 **작음**. 보통 |ΔCSM| > |ΔPL|인데 반대.

**확인 (owner가 sensitivity_heatmap.json 한화생명 record 조사, status=ok):**
- csm_delta(ΔCSM): 사망 -82.13 / 장해질병정액 -439.99 / 장해질병실손 -25.09 / 해지↑ -79.34 / 해지↓ +82.64 → 전부 |ΔCSM| ≤ 440, 대부분 두자리.
- pl_impact(ΔPL): 사망 -1729.96 / 장해질병정액 -6469.86 / 해지↑ **-11533.08** / 해지↓ +13113.1 → 전부 수천~1.3만.
- 즉 **|ΔPL| >> |ΔCSM|** (해지↑ 기준 11533 vs 79). owner 지적대로 정상은 반대.
- **대조군 DB생명(정상)**: csm_delta 386·1480·2355 vs pl_impact -1.31·-0.64 = **|ΔCSM| >> |ΔPL|** (정상 패턴). → 한화생명만 뒤집힘.
- 한화생명 header가 다열 복잡 구조: 「이행현금흐름 / 보험계약마진」 × 「원수 / 출재」 × 「유배당 / 무배당 / 소계」 + 「당기손익 / 기타포괄손익」. → **큰 당기손익(PL) 컬럼이 pl_impact로, CSM 컬럼 대신 작은 열이 csm_delta로 매핑된 컬럼 오선택/스왑 의심.** 사업비 2행은 csm_delta=None.

**요청 (ifrs17):**
1. 한화생명 FY2025 raw 표 **재파싱** — 보험계약마진(CSM) 변동 컬럼과 당기손익(PL) 컬럼 매핑을 정확히(원수/출재·유배당/무배당/소계 다열에서 CSM열→csm_delta, 당기손익열→pl_impact).
2. 사업비 csm_delta=None 채우기.

**겸사 — sensitivity_heatmap census (owner probe):**
- **n=0(시나리오 자체 없음) 4사 발견: 미래에셋생명·신한라이프·엠지손해보험·한화손해보험.** 신한라이프·미래에셋은 대형사라 민감도 공시 개연성 높음 → 미공시인지 추출갭인지 확인(별도 처리 가능).
- 현대해상(#2)은 n=6이나 값 전부 null(별건) — 기존 발주 **20260626T0850Z** 여전히 open, cross-ref.

## 답변 (ifrs17, 2026-07-03)

**원인 확정 = band-layout 컬럼 매핑 오류 (owner 진단 정확).** 한화생명 표는 그룹당 4컬럼(원수 유배당/무배당/소계 + 출재) × 4그룹(이행CF·보험계약마진(CSM)·당기손익·기타포괄) = 16개 값열. 헤더 최하단행이 유배당/무배당/소계만 12개 나열(출재 열 누락)해서 `viz_build_ifrs17_panels._band_sensitivity_columns`의 columns-per-group가 12/4=3으로 오산 → **csm_delta←col3(이행CF 출재), pl_impact←col6(CSM 원수소계)** 로 잘못 잡힘. owner가 본 스왑의 정체 = "작은 열이 csm, CSM열이 pl".

**정답 컬럼**: csm_delta ← col6(CSM 원수소계), pl_impact ← col10(당기손익 원수소계). 16열 전부 소계=유배당+무배당 항등식으로 검증(실손보상은 유배당 공란=0, 무배당=소계 성립). 10개 시나리오 전부 `|ΔCSM|>|ΔPL|` 정상 복귀:
- 사망률↑ csm△1729.96 / pl△9.98 · 해지율↑ csm△11533.08 / pl△1093.87 · 장해정액↑ csm△6469.86 / pl△1954.21 · 사업비수준↑ csm△2391.17 / pl△633.45.
- req2(사업비 csm_delta=None) 자동 해결 → csm_delta △2391.17 채움.
- (부호: 사망률↓만 csm+/pl△ 반대부호이나, 당기손익=CSM 초과 손실분 정의상 정상. 삼성생명 override에도 동일 패턴 존재 → 파싱오류 아님.)

**적용 방식**: 이 브랜치 파괴적 rebuild 금지(raw git-purge)라 established 패턴대로 처리 —
1. `data/dart/viz/sensitivity_overrides.json`에 한화생명(당기말) 10 시나리오 주입 (rcept 20260316001304, FY2025, as_of 2025-12-31, unit 억원, basis 원수).
2. `viz_build_ifrs17_panels.py` 재빌드 후 heatmap **한화생명 레코드만 surgical 교체** (형제 패널 csm_amort/insurance_pl/bs_snapshot 및 타 회사 전부 unchanged — 커밋본 stale 드리프트 미반영).

**후속(별건, 미차단):**
- 추출기 일반화: `_band_sensitivity_columns`를 4-subcol 그룹(원수 유배당/무배당/소계+출재) + 원수소계 오프셋까지 처리하도록 (현재 override로 커버, follow-up).
- census n=0 4사(미래에셋·신한라이프·엠지손보·한화손보): 기존 0615 reextract phase-2 + weekly-limit로 already tracked, 본건 무관.
- 현대해상(KR0009) 값 all-null: 별도 open 발주 **20260626T0850Z** 미해결 (cross-ref).
- **부수 관찰(FYI publishing)**: (1) 커밋된 viz 패널 csm_amort_schedule/insurance_pl_breakdown가 현재 extracted 데이터 대비 stale — full rebuild 시 다수 회사 드리프트 + 아이비케이연금보험 신규 편입. 본건에선 surgical만 반영, 별도 검토 권장. (2) `data/dart/viz/sensitivity_overrides.json`은 git 미추적(한 번도 커밋 안 됨) — 12사 override 전부 이 working-tree 파일에만 존재. 내 fix는 tracked heatmap에 baked-in돼 라이브 안전하나, 커밋 시 overrides.json도 함께 versioning 권장(안 그러면 다음 full rebuild가 전 override wipe).

status → answered (owner 사이트 재확인).
