---
from: owner
to: publishing
created: 20260921T0320Z
status: open
route: escalate
company: ALL
period: N/A
rule: USER_FACING_META_TEXT
iter: 1
---

## 미결 (sender 작성)

owner 지적(2026-09-21): **화면·산출물에 내부 작업 문구(메타발언)가 나가면 안 된다.**
IFRS17.html 가정민감도 각주 건은 `354b0f2` 로 고쳤고, 같은 유형이 **다운로드 시트에 하나 더**
남아 있다.

### 무엇이

`public_exports/자본비율전망.json` 의 `비고` 컬럼 **610행**이 게이트 내부 진단 문자열을 달고 있다.
사용자가 이 시트를 내려받으면 그대로 본다.

```
… / 신뢰도 낮음(발행잔액 vs BS 괴리) — T2 face/BS gap +202% (subordinated_eok) — advisory, not in overall
… / 신뢰도 낮음(발행잔액 vs BS 괴리) — T2 FSC gap: BS 298억 but bond DB=0; T2 face/BS gap -100% (numerator_eok_fallback) — advisory, not in overall
… — T1 face/BS gap +106% (tier1_hybrid_issued_eok); …
```

`subordinated_eok` · `tier1_hybrid_issued_eok` · `numerator_eok_fallback` 은 **필드명**이고,
`advisory, not in overall` 은 **게이트 용어**다. 독자에게는 아무 뜻이 없다.

발생원: `scripts/forward_capital_simulation.py:336` 등이 `reasons` 에 진단 문자열을 붙이고,
그게 루트 마스터 `kics_forward_capital.json`(18곳) → `public_exports/자본비율전망.json` 으로 흘러간다.
K-ICS.html 은 이 필드를 렌더하지 않으므로 **대시보드 화면에는 안 보인다** — 다운로드 시트 한정이다.

### 남겨야 할 것 / 지워야 할 것

- 남긴다(사용자에게 뜻이 있는 경고): `콜옵션 미공시 채권 포함 — 콜일자를 발행일+5년/신용등급이력 등으로 추정
  (원문 미기재), 실제 콜상환 시점과 다를 수 있음` · `신뢰도 낮음(발행잔액 vs BS 괴리)` ·
  `자본잠식(가용자본<=0) — 비율 0%로 캡 표시`
- 지운다(내부 진단): `— T1/T2 face/BS gap …%` · `(subordinated_eok)` 류 필드명 ·
  `T2 FSC gap: BS …억 but bond DB=0` · `advisory, not in overall`

### 시킬 일

1. **원천에서 가른다.** 진단은 지우지 말고 **별도 필드**(예: `_diagnostics`)로 옮기고,
   `비고` 에는 사용자 문구만 남긴다. export 단계에서 문자열을 잘라내는 땜질은 하지 말 것 —
   원천이 그대로면 다음 빌드에 또 샌다.
2. 마스터 재생성은 **통짜 실행 금지**. 바뀌는 게 텍스트 필드뿐임을 diff 로 먼저 보이고,
   숫자가 한 칸이라도 움직이면 멈추고 보고한다. `kics_forward_capital_provenance.json` 동반 확인.
3. `public_exports/자본비율전망.json` 재생성은 마스터 커밋 후(그 스크립트는 커밋된 HEAD 를 읽는다).
4. 같은 유형 재발을 막는 검사를 넣을지 validation 과 협의한다 — 배포 산출물의 사용자 문자열에
   필드명·영문 게이트 용어가 섞이면 잡는 검사. (validation 에는 이미 배포 HTML JS 런타임 게이트
   티켓이 열려 있다: `inbox/validation/20260921T0057Z__owner__ALL__deployed_js_runtime_blind_spot.md`)

참고로 아래 두 건은 **내부 용어가 아니라 데이터 단서**라 판단해 건드리지 않았다. 문구를 다듬을지는
owner 판단: `public_exports/가정민감도.json` 비고 `"같은 충격이 이 회사 표에 2벌 있다(재보험 경감
전/후로 추정, 원문 라벨 미확인) — 순번으로 구분"`(10행), `public_exports/자본성증권발행현황.json`
구분 `"… 후순위 명시 라벨 없음, 구조 기반 추정"`(3행).

## 답변 (recipient 작성 — 처리 후)
