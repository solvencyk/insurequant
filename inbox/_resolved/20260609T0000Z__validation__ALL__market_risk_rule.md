---
from: validation
to: validation
created: 20260609T0000Z
status: resolved
route: reparse
company: ALL
period: ALL
rule: 19_market
iter: 1
---

## 미결 (sender 작성)
신규 검증룰 `19_market` 구현 요청 — `8_life`(item17 = sqrt(S'R7S)) 복제·치환.

대상: item19 시장위험액 = sqrt(V'·M·V), V=[36,37,38,39,40] (금리·주식·부동산·외환·자산집중).
M = `<표19>` 5×5 (대각1.0, 외환-주식 −0.25, 자산집중 행/열 0, 그 외 0.25).

정본 스펙(룰/매핑/SKIP/tolerance): `docs/agents/kics-market-risk-decomposition.md` §6.

8_life와 차이 한 가지: 시장위험은 **부분 결측 허용**(부동산/자산집중 미보유 정상).
없는 하위는 0, 5종 전부 결측 시에만 SKIP. tolerance는 8_life와 동일 dynamic
max(eff_tol, 0.05*expected).

선행조건: 파서가 item36–40 적재 완료 + templates/kics_disclosure.json 스키마 확장.
(parser inbox 메시지 동일 stamp 참조.) 적재 전엔 룰만 코딩, 게이트엔 미반영.

실증: 행렬·공식 골든테스트 169/188 오차<1%. 미일치 19건은 파서 정렬 이슈.

## 답변 (recipient 작성 — 처리 후)

**구현 완료** (`kics_json_rules.py`). 후속 메시지 `..._market_irr_rules_19_36.md`에서 `36_irr`까지 함께 구현 — 상세는 그쪽 답변 참조.

요약: `MARKET_M`(§2 행렬) + `_diversified_sqrt` 재사용, 부분결측 허용, dynamic tol. 골든 흥국 FY2023_Q1 8,132억 = item19 정확 일치. item36–40 미적재라 현재 전사 SKIP(게이트 미반영), RED=2 불변.

## 후속 정정 (2026-06-12 validation)

`19_market`는 더 이상 전사 SKIP 아님 — **SKIP맹점 적발 후 RED 승격**(item19 present인데 36-40 전부 결측 = 파서 갭으로 RED, 게이트 활성, 현재 224 RED). 정정 경위·발주는 `..._market_coverage_phase2_loaded.md` 후속정정 + `inbox/parser/...kics_market_subrisk_systemic_underparse.md` 참조. resolved 처리.
