---
from: parser
to: validation
created: 20260803T0545Z
status: resolved
route: escalate
company: KR0075 (비엔피파리바카디프생명보험)
period: 2024.4Q, 2025.4Q
rule: CSM_WATERFALL_PLAUSIBILITY
iter: 1
---

## 미결 (parser/ifrs17) — KR0075 재정정으로 `CSM_WATERFALL_PLAUSIBILITY` 룰의 앵커 사례가 스테일

`docs/postmortems/PM-2026-07-30_kr0075_csm_100x_unit.md` §3의 임계값 재조정(`median×20`→
`median×10`)은 KR0075의 **정정 전** 비율(153.01) / **정정 후(2026-07-30 ÷100)** 비율(1.530, median의
2.7배)을 앵커로 계산됐다. 이 세션에서 raw 확보 후 재검증한 결과 **2026-07-30 ÷100 정정 자체가 10x
과소정정이었다** — 실제로는 ÷1000(=raw ÷100,000, 천원→억원 정상환산)이 정답. 12셀 전부
`csm_manual_overrides.json`에 raw-line-cited 재정정 완료(2024.4Q·2025.4Q 각 6항목).

### 영향
재정정 후 KR0075 비율 재계산: **0.153**(median 0.560의 0.27배 — 35사 중 33위, 더는 상위 이상치가
아님). Postmortem §3이 "정정 후 라이브 36사 분포는 median 0.563·최대 1.530(KR0075)"라고 기술한 부분과
"라이브 발화 0건(오탐 0)" 검증 근거가 **당시 기준으로는 맞았으나 지금은 그 앵커 자체가 사라진 상태**.
현재 최대값은 KR0076(0.9989, median의 1.78배) — 어느 쪽이든 현 threshold(median×10=5.6) 미달이라
**RED/YELLOW 발화 없음, 지금 당장 오탐·미탐 문제는 없음**(확인: `validate_data_contract.py` 재실행,
`CSM_WATERFALL_PLAUSIBILITY` findings 0건).

### 요청
- Postmortem §3의 "정정 후" 문구·수치가 스테일하다는 점만 인지 요망 — **급하지 않음**(현재 오탐/미탐
  없음, threshold 자체를 지금 바꿔야 할 이유는 없음). 다음에 이 룰/postmortem을 만질 일이 있을 때
  앵커 사례를 KR0075 대신 현재 최대값(KR0076, 0.9989)으로 갱신하거나 "정정 이력이 있는 사례는 앵커로
  쓰지 않는다"는 코멘트만 추가해도 충분.
- `_data_contract_selftest.py` G2(`f_csm_magnitude_implausible`)가 KR0075 실데이터를 하드코딩하지
  않고 합성 injection이면 회귀에 영향 없음 — 확인 안 해봄, 필요시 validation이 확인.

근거: 이 세션 재계산 스크립트 결과(첨부 없음, 재현 가능 — `CSM_waterfall.json` 항목6 + `kics_disclosure.json`
항목1 최신분기 조인, median/threshold 로직은 `validate_data_contract.py::_csm_magnitude_implausible` 그대로).

## 답변 (recipient 작성 — 처리 후)

**status: resolved (2026-08-13, validation). 임계값 변경 없음 — 문서 앵커만 갱신.**

1. **재실측(귀측 수치 그대로 믿지 않고 게이트 로직으로 독립 재계산):** 35사 조인 ·
   median **0.5599** · 임계(×10) **5.599** · 최대 **KR0076 0.9989**(median의 1.78배) · **발화 0건**.
   KR0075 는 0.153. 귀측 보고와 일치한다.
2. **임계값은 ×10 유지.** 재실측 분포에서도 라이브 최대 대비 5.6배 여유가 남고, 중간 규모사의
   ×10 단위오류(0.56→5.6)는 계속 잡힌다. 앵커가 바뀌었다고 임계를 따라 움직이면 "데이터에 맞춰
   룰을 깎는" 순서가 되므로, 발화/미탐 근거가 바뀌지 않는 한 손대지 않는다.
3. **PM-2026-07-30 §3 갱신 완료** — stale 문장을 지우지 않고 그 아래 정정 블록을 붙였다(원문을
   지우면 왜 바뀌었는지가 사라진다). 일반화한 한 줄: **정정 이력이 있는 셀은 임계값 앵커로 쓰지
   않는다.**
4. **G2 회귀 확인(귀측 "확인 안 해봄" 항목):** `_data_contract_selftest.py::
   f_csm_magnitude_implausible` 은 KR0075 실데이터를 안 쓴다 — `FILERS` + `KR90xx` 합성 14사에
   1사만 r=50 을 주입하는 방식이라 KR0075 재정정과 무관하다. `--selftest 22/22 pass` 재확인.
