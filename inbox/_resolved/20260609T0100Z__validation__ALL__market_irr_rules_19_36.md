---
from: validation
to: validation
created: 20260609T0100Z
status: resolved
route: reparse
company: ALL
period: ALL
rule: 19_market, 36_irr
iter: 1
---

## 미결 (sender 작성)

신규 검증룰 2개 구현 요청 (`8_life` 복제 패턴). 정본: `docs/agents/kics-market-risk-decomposition.md` §6, §7-7, §8.
선행: 파서가 items 36–46 적재 (parser inbox 동 stamp). 적재 전엔 룰 코딩만, 게이트 미반영.

### Rule `19_market` — 시장위험액 하위 (M 분산)
- `item19 = sqrt(V'·M·V)`, V=[36,37,38,39,40] (순서: 금리·주식·부동산·외환·자산집중).
- M (5×5): 대각 1.0; 외환-주식 = **−0.25**; 자산집중 행/열 0(대각 제외); 그 외 비대각 0.25.
- 부분결측 허용(없는 하위=0; 부동산/자산집중 정상 미보유). 5종 전부 결측 or item19 결측 → **SKIP**.
- tolerance: dynamic `max(eff_tol, 0.05*abs(expected))`. 음내적 클램프 후 sqrt(기존 helper).

### Rule `36_irr` — 금리위험액 시나리오 분해 (순자산가치 유도)
- base=item41. R상승=max(41−43,0), R하락=max(41−44,0), R평탄=max(41−45,0), R경사=max(41−46,0), R평균회귀=41−42(signed).
- `item36 = √[max(R상승,R하락)² + max(R평탄,R경사)²] + R평균회귀`.
- prereq: item36 + 41–46 전부 present, 아니면 **SKIP**(RED 아님). tolerance dynamic 동일.
- 옵션 부수체크: item36 == 시장위험 세부표 금리위험(정합성).

### 골든 (FY2025_Q4)
- 흥국화재 유도 금리위험액 157,128 vs 공시 157,127 (diff 1, 반올림).
- 현대해상 322,767 vs 322,767 (diff 0).
- 시장위험 19_market: 169/188 filing 오차<1% (기존 probe).

이미지-only(KR0010, KR0079) 10.0 오버라이드 승계. kics-json-validation-rules.md 라벨매핑 36–46 이미 추가됨.

## 답변 (recipient 작성 — 처리 후)

**구현 완료** (`src/solvency/validation/kics_json_rules.py`, 8_life 복제 패턴).

- **`19_market`**: `MARKET_M` 5×5 행렬(§2 그대로: 대각1.0/외환-주식 −0.25/자산집중 행열 0/그외 0.25) + `_diversified_sqrt(V, MARKET_M)` 재사용. V=[36–40], 부분결측 허용(없는 하위=0; item19 없거나 36–40 전부 결측 → SKIP). dynamic tol `max(eff_tol, 0.05·expected)`. IMAGE_OCR 10.0 승계.
- **`36_irr`**: `√[max(R상승,R하락)² + max(R평탄,R경사)²] + R평균회귀`, R=base(41)−시나리오순자산, 평균회귀 signed. 41–46 중 하나라도 결측 → SKIP.

**골든 3/3 정확 일치**: 19_market 흥국 FY2023_Q1 `sqrt(V'MV)=813,201백만=8,132억` (=item19); 36_irr 흥국 `157,128`(공시 157,127, 반올림) / 현대 `322,767`(공시 일치).

**회귀**: `validate_kics_disclosure.py` RED=2 불변(기존 KR0010 OCR exception). item36–46 미적재라 신규 2룰 전사 SKIP — **게이트 미반영 상태**(inbox 지시대로). 파서 적재 후 자동 활성.

**단위 확인 요망**: 룰은 item36–40을 item19와 **동일 단위(억원)** 가정. 파서가 세부표(백만원) ÷100해 억원 적재하면 그대로 동작. 백만원 적재 시 대조식 조정 필요 — 적재 단위 회신 바람.

코드: `kics_json_rules.py` MARKET_M(행 47–) + run_validation 내 19_market/36_irr 블록(8_life 다음).

## 후속 정정 (2026-06-12 validation)

`19_market` SKIP맹점 적발 → **RED 승격**(부모 present·자식 36-40 전결 = 파서 갭, 게이트 활성, 224 RED). `36_irr`은 동일 SKIP맹점(41-46 결측 시 SKIP)이나, parser가 36-40 backfill 후 데이터 보고 RED승격 판단(현재 보류 — false-RED 홍수 방지). 정정 경위는 `..._market_coverage_phase2_loaded.md` 후속정정 참조. resolved 처리.
