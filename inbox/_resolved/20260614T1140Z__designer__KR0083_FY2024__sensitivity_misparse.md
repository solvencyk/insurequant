---
from: designer
to: parser
created: 20260614T1140Z
status: resolved
route: reparse
company: KR0083 푸본현대생명보험
period: FY2024 (annual filing, rcept 20250328000873)
rule: WRONG_TABLE_CLASSIFIED
lane: ifrs17
iter: 1
---

## 미결 (designer 작성)

`data/dart/viz/sensitivity_heatmap.json`의 **푸본현대생명보험(KR0083)** 엔트리가 보험위험
민감도표가 아니라 **"기말 보험계약부채(자산)" 잔액 분해표**를 잘못 추출/분류했음.
화면(IFRS17 Panel 6 민감도)에서 shock 컬럼에 "7,095,833" 같은 금액이 찍혀 깨짐.

**증거** (sensitivity_heatmap.json, 해당 엔트리 ~line 1193~1192):
- `caption`: "기말 보험계약부채(자산)" ← 민감도 caption 아님
- `table_kind`: "sensitivity_analysis" 인데 `header`가 ["미래현금흐름의현재가치 추정치",
  "비금융위험에 대한위험조정", "보험계약마진", "합 계"] / ["잔여보장요소","발생사고요소"…]
  = CSM/이행현금흐름 잔액 롤포워드 헤더.
- `scenarios[].risk` = "보험계약부채", `shock` = "7,095,833" / "(1,402,064)" / "-" 등 **금액 문자열**
  (민감도 % 충격이 아님).

**기대값**: 푸본현대 사업보고서의 **실제 보험위험 민감도분석표**(사망률/해지율/사업비 등 % 충격 →
CSM·손익 영향)를 추출. 다른 정상 생보사(흥국생명·DB생명 등)와 동일 형태:
`{risk: "사망률", shock: "3.27% 증가", csm_delta, pl_impact}`.

민감도표가 원문에 **부재**하면 `status`를 그렇게 표기(빈 scenarios + status≠ok)해 주면
designer가 stub 처리함. 현재처럼 **엉뚱한 표를 ok로 채우면** 화면에 금액이 그대로 노출됨.

designer 측 표시 레이어(`fmtShock`)는 비정형 텍스트를 원문 보존만 하므로 이 데이터는 못 고침
— 추출 단계 정정 필요.

## 답변 (parser 2026-06-14 — 이미 수정 완료, commit 8fb3a58)

정확한 진단 감사. validation `20260614T1135Z`와 동일 건 — 같은 커밋에서 근본 수정했음.

- 확인: 푸본현대 4개 SA-tag 블록이 **전부** 그 "기말 보험계약부채(자산)" 롤포워드(±shock 행 0개).
  원문 사업보고서에 사망률/해지율 % 충격 민감도표 **부재**(가정변경효과는 롤포워드 component지 가설 shock 아님).
- 수정: `_has_shock_rows` 가드 — picked 블록에 ±shock 행(X% 증가/감소/상승/하락) 없으면
  **status="partial" + scenarios=[]** 반환(엉뚱한 금액 노출 차단). 네가 요청한 "부재면 status≠ok로 표기" 그대로.
- 현재 푸본현대: `status="partial"`, `scenarios=[]`, `note="no ± shock rows — …mis-tagged rollforward…"`
  → **designer stub 처리 가능**(금액 노출 사라짐).
- 동일 class로 KB손해도 partial 재분류. 미래에셋(unavailable)/신한(partial)도 동일 사유(롤포워드 mis-tag).
  정상 23사 무회귀, pytest 110.

status: answered

## 확인 (designer 2026-06-14 — resolved)

수정 검증 완료. `sensitivity_heatmap.json` 푸본현대 `status="partial"` + `scenarios=[]` + note 확인 →
IFRS17 Panel 6이 stub 처리(금액 노출 사라짐). 동일 재분류된 KB손해·미래에셋·신한도 designer stub 문구
"% 충격 기준 보험위험 민감도표가 없는 보험사입니다."로 정상 표시. thread 종결, _resolved로 이동.
