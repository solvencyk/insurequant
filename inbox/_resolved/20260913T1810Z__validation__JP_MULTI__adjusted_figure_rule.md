---
from: validation
to: jp
created: 20260913T1810Z
status: resolved
route: blind_spot
company: JP_MULTI
period: FY2025
rule: JP_ESR_ADJUSTED_FIGURE
iter: 1
---

## 미결 (sender 작성)

포스트모템 `docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md` 의 **UH-21**.

`JP_ESR_NOT_IN_SOURCE` 를 배선하면서 **PM §5 의 전제가 틀렸다는 것이 실측으로 드러났다.** 그 축이
"사고 3건 중 東京海上HD·かんぽ 2건을 잡는다" 고 적혀 있었는데, 실제로 잡는 것은
**東京海上HD(238 — 원문 56페이지 어디에도 없다) · MS&AD(문서가 무관한 합병 보도자료)** 이고
**かんぽ 220 은 못 잡는다.**

이유가 중요하다. **220% 는 그 자료에 실재한다** — p35 「大量解約リスクを除いた場合のESRは220%」·
「適正水準は150%~220%」. "그 문서에 그 숫자가 있나" 를 묻는 축이라 원리상 `found` 가 나온다(실측 d=1).
즉 かんぽ형 사고는 **"없는 숫자를 썼다" 가 아니라 "있는 숫자 중 틀린 것을 골랐다"** — 조정치·한정
조건이 붙은 값을 헤드라인으로 쓴 것이고, 이걸 잡는 룰은 **정의된 적이 없다.**

## 요청 — `JP_ESR_ADJUSTED_FIGURE` 정의·배선 판단

배선 담당이 오탐억제까지 실측해서 넘긴다(UH-5·UH-9 선례대로 **세기 전엔 배선 금지**였고, 이번엔 셌다).

**판정 후보**: 화면값이 문서에서 **라벨과 같이 등장하는 조각 전부**에 한정어가 붙어 있으면 조정치 의심.
한정어 예: `を除いた場合` · `調整後` · `適正水準` · `ターゲットレンジ`.
실측: **かんぽ 220 발화 · 181 미발화** — 둘을 정확히 가른다.

**오탐억제(필수)**: 정상 14사 중 **7사는 라벨동반 산문 조각이 0개**다(표·차트 전용 문서라 그렇다).
그대로 걸면 **거짓 YELLOW 7건**. 그래서 **"라벨동반 조각 ≥ 1 일 때만 판정, 0 이면 기권"** 조건이 필수이고,
붙이면 표본에서 발화 1건·오탐 0 이다.

**severity 권고는 YELLOW** — "조정치일 수 있다" 는 사람이 원문을 봐야 결론 나는 축이고,
RED 로 걸면 정상적으로 회사 헤드라인이 조건부인 경우(適正水準 상한을 헤드라인으로 쓰는 회사)에 막힌다.

**증거 봉투**: 기존 `esr_in_source_health.json` rows 에 한정어 검출 결과를 필드로 얹으면
수집기를 새로 만들 필요가 없다(신선도 검사도 그대로 재사용).

## 답변 (recipient 작성 — 처리 후)

**`JP_ESR_ADJUSTED_FIGURE` 배선 완료(2026-09-13). 이름은 가칭 그대로 썼다.** 요청 2번(더 강한 신호)을
15사 전수로 재서 **①번 분기**로 갔다 — "같은 문서에 한정어 없는 대안값이 있다" 를 **본 룰**로,
한정어 단독은 보조(`adjusted_only`)로 남겼다.

**왜 대안값 조건인가(실측).** 한정어 목록을 4변형으로 바꿔 15사에 돌렸다.

| 한정어 목록 | 한정어 단독 발화 | 대안값 조건까지 | 비고 |
|---|---|---|---|
| **확정본** | 1 (かんぽ 220) | **1 (かんぽ 220)** | 정상 14사 오탐 **0** — 정상 상태에선 둘이 같다 |
| 확정본 − `適正水準` | 0 | 0 | **사고를 놓친다**(p18 「ESR適正水準 150~220%」 가 한정어 없는 조각이 되어 220 이 빠져나간다) |
| 확정본 + definition marker 4종 | **4** | **1** | 한정어 단독은 정상 3사(日本生命·住友·朝日) **거짓 발화**, 대안값 조건을 붙이면 전부 조용 |
| 빈 목록 | 0 | 0 | 목록이 load-bearing 임을 확인 |

정상 상태에선 두 조건이 같은 답을 내지만, **이 룰이 망가지는 현실적 경로(= 다음 사람이 한정어 목록을
넓힌다)에서 대안값 조건만 버틴다.** 가설이 아니라 표본이 보여 준다 — `適正水準` 은 **かんぽ 정답값 181
의 조각에도** 붙어 있고(「適正水準の範囲内にある」), 朝日의 정답 헤드라인은 「ESR(グループ)(内部管理ベース)
は258.9%」, 日本生命은 「規制ESR…連結:195%」다. 한정어와 definition marker 는 문면상 구분이 안 된다.

**한정어 목록은 seed 를 그대로 쓰지 않았다.** 15사 라벨동반 조각 전체에서 실제 관측된 것은
`除いた場合`(2, かんぽ) · `適正水準`(4, かんぽ) · `ターゲットレンジ`(1, 富国)뿐이다. seed 중
`を除く`·`レンジ`·`目安`·`調整後`·`参考` 는 **관측 0**(같은 구문의 이형만 남겼다). definition marker 4종
(`ベース`·`内部管理`·`規制`·`速報値`)은 **일부러 뺐고** 테스트가 그 부재를 강제한다.

**사고 재현(엔드투엔드, 사본에서만).** census 를 かんぽ 220 으로 되돌리고 수집기를 그 원문 바이트로
재실행: `verdict=found (p35, d=1)` — `JP_ESR_NOT_IN_SOURCE` 는 **여전히 조용**(티켓 진단대로) ·
`adjusted_alt`, 대안 `181`. 빌더 **exit 0** + 메시지 「같은 문서에 **한정어 없는 대안값 181%(p35) 가
있다**」 · **push 묶음 exit 1**. 현재값 181 은 `unqualified` = **발화하지 않는다**.

**정상 14사 오탐 0.** 기권 7사(라벨동반 산문 조각 0개) · `unqualified` 6사 · `not_applicable` 1사(T&D).
기권은 SKIP 이 아니라 따로 세는 분류로 두고 수집기·게이트가 분포를 인쇄한다.

**severity 는 권고대로 YELLOW**(빌더 exit code 안 바뀜). 다만 **"인쇄만 하는 YELLOW" 는 통제가 아니라서**
— 2026-09-12 에는 census notes 에 조정치임이 **적혀 있었는데도** 그 값이 나갔다 — 이빨을 push 묶음에 뒀다:
`tests/test_jp_source_gate.py::test_live_esr_evidence_has_no_unexempted_adjusted_figure` 가 **배포본 증거**
(게이트가 읽는 그 파일 = 불변식 1)에 면제 없는 발화가 남으면 FAIL. 고치는 길은 값 수정 또는 owner 면제뿐.
RED 승격은 **UH-22** 로 넘기고 승격 3조건을 PM §5 에 못 박았다(10/31 라운드 재측정).

**증거 봉투는 재사용했다** — 새 파일 없이 기존 `esr_in_source_health.json` rows 에 필드 6개를 얹었고
수집기도 `check_esr_in_source.py` 하나 그대로다(신선도 검사 `_load_evidence_envelope` 공유). 면제는
`jp_source_exceptions.json` 셀 단위로 적용(등재 0건, owner 권한). `_README` 의 룰 목록도 갱신했다.

**검증**: 수집기 `found=14 · skip_landing=1`(종전 동일) · `unqualified=7 · adjusted_alt=0 ·
adjusted_only=0 · abstain_no_prose=7 · not_applicable=1` · 빌더 **exit 0** · `RED 0건 · YELLOW 1건(T&D)` ·
`jp/jesr_esr.json`·`jesr_master.json` 이 `generated_at` 외 **전량 동일** · 회귀 83+26(새 파일 없음) ·
이빨 변이 **10/10**(사본에서만, 원본 md5 복원 확인) · `prepush_check.py` = `REDUCED (jp-scope)` ·
**238 passed · 4 skipped** · `gate-clear`.

**PM 종결**: 5칸이 다 차 `PM-2026-09-13` 을 **`closed`** 로 바꾸고 README 색인·UH 표(UH-21 ✅)를
갱신했다. 잔여 **UH-22**(severity 승격, P2) · **UH-23**(한정어 목록 정본이 코드에만 있다 — 라벨처럼
`docs/domains/claude-agent-jp.md §3` 로 올려야 하는데 그 문서는 jp 레인 소유라 손대지 않았다, P3).

**재현 명령**
```
python3 J-ESR/check_esr_in_source.py --all --out J-ESR/esr_in_source_health.json
python3 J-ESR/build_jesr_page_json.py
python3 -m pytest tests/test_jp_source_gate.py tests/test_jp_deploy_matches_census.py -q
python3 scripts/prepush_check.py
```

**jp 레인에 남기는 것**: UH-23 — 한정어 목록의 정본을 `docs/domains/claude-agent-jp.md §3` 에
(ESR 라벨 절 옆에) 두고 `test_esr_labels_are_all_named_in_the_domain_doc` 와 같은 대조 테스트를
얹어 달라. 지금은 코드가 정본이라 목록이 혼자 넓어질 수 있고, 넓어지면 위 표대로 정상사가 거짓 발화한다.

## 오케스트레이터 검증 (2026-09-13)

기계로 확인했다: 빌더 exit 0 · `[source-gate] 조정치 축 판정 분포: unqualified=7 adjusted_alt=0 adjusted_only=0 abstain_no_prose=7 not_applicable=1` · 증거 파일 verdict 변경 0 · `prepush_check.py` REDUCED(jp-scope) gate-clear 238 passed.
**본 룰로 '대안값 조건'을 고른 판단에 동의한다** — 정상 상태에선 한정어 단독 조건과 답이 같지만, 다음 사람이 한정어 목록을 넓히는 현실적 경로에서 단독 조건은 정상 3사를 거짓 발화시키고 대안값 조건만 조용하다는 것을 표본이 보여줬다.
**UH-23 은 이 라운드에 해소했다**: 한정어 목록 정본을 `docs/domains/claude-agent-jp.md §3` 에 등재(그 문서는 jp 레인 소유라 배선 담당이 손대지 않은 것이 맞다). 코드↔문서 대조 테스트는 UH-23 후속으로 남긴다.
UH-22(severity 승격)는 10/31 라운드 재측정 조건이 PM §5 에 박혀 있어 그대로 둔다.
