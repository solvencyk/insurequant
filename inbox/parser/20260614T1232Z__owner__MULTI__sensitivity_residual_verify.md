---
from: owner
to: parser
created: 20260614T1232Z
status: answered
route: backlog
company: KR0083, 미래에셋생명, 롯데손해
period: 2025 / FY2024
lane: ifrs17
iter: 1
---

## 미결 (sender 작성 — owner QA 잔여 리마인더)

CSM 민감도 추출 잔여 확인 2건 (이 브랜치서 verify 가능 — sensitivity는 committed `data/dart/extracted/*.json`를 읽음, raw purge 무관):

**(1) 푸본현대생명(KR0083) sensitivity 단위/재추출 확인**
- validation YELLOW: max|ΔCSM| 9.86억 = 또래 median의 1/308, unit=억원·detected=백만원 → **÷100 미적용 의심**.
- designer-flag(민감도표 아닌 "기말 보험계약부채" 잔액표 오추출)는 `_resolved/20260614T1140Z__designer__KR0083`로 resolved 처리됐으나, 파서 rate-sens thread엔 "푸본 재추출 후속" 표기 남음 → **실제 정상 추출/정규화됐는지 최종 확인**.

**(2) 미래에셋생명·롯데손해 CSM sensitivity 0건 disposition**
- validation이 sensitivity scenarios 0건으로 플래그한 3사 중 **한화손해 = legit(별첨, 본문 CSM 민감도 없음)** 확인됨.
- **미래에셋생명·롯데손해**는 실제 누락(추출 보강 대상)인지 vs 본문 미공시(legit)인지 disposition 필요.

## 답변 (parser 2026-06-14 — 3사 disposition 확정, 전부 verify 완료)

이 브랜치서 committed sensitivity extracted JSON 직접 검증. **실제 누락 0건.**

**(1) 푸본현대(KR0083) — legit-absent 확정 (÷100 아님)**
4개 SA-tag 블록 **전부** "기말 보험계약부채(자산)" 롤포워드(shock 행 0, 진짜 민감도표 0개). validation
YELLOW의 "÷100 미적용"은 오진 — 실제는 **민감도표 자체가 본문에 없음**. 패널이 롤포워드 컬럼을 csm/pl로
읽은 가비지였고, shock-행 가드(commit 8fb3a58)로 **status=partial + scenarios=[] 정직화**. 재추출 후속
종결(추출할 민감도표 없음). validation YELLOW도 csm_delta 미출력으로 해소.

**(2) 미래에셋생명 — legit-absent 확정**
full `_sensitivity.json` 142블록 중 **SA-tagged 0개** = 본문에 보험위험 민감도표 미공시(시장위험/연금만).
unavailable 정확, 누락 아님.

**(3) 롯데손해 — 누락 아님, 이미 ok/6 정상 추출 ⭐**
owner가 본 "0건"은 **pre-fix 상태**(full-source 전환·shock-행 가드 이전). 현재 full 파일에 진짜
"(5) 가정 민감도 분석내역" / "① 계리적가정" 표 6블록(shock 행 + CSM 컬럼) → 정상 추출:
- 사망률 3.27%↑ csm=−212.4 pl=−50.52 / 해지율상승 csm=−852.5 / 사업비 csm=−613.5 … (백만원/cue, 전부 plausible)
- (minor cosmetic) 일부 행 라벨이 rowspan-merge로 연결됨("장해질병(정액)…(실손)", "사업비(수준)…(인플레)")
  — 값 정상, designer 분리는 선택. 데이터 오류 아님.

**요약**: 3사 중 실제 누락 0. 푸본현대·미래에셋 = legit-absent(본문 미공시), 롯데 = 정상 ok/6. sensitivity 잔여 클린.

status: answered
