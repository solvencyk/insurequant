# PM-<YYYY-MM-DD> — <사고 한 줄 요약>

> 상태: `open` | `closed` (5칸 전부 채워야 closed)
> 발견 경로: owner 라이브 QA / 게이트 / 적대검증 / 세션 중 발견
> 관련 inbox: `<티켓 파일명>` · 관련 커밋: `<sha>`

## 0. 사실관계 (blameless)

<무슨 일이 언제 어디서. 사람 탓 금지 — 게이트 사각으로 서술. 추측과 확인된 사실을 구분해 표기.>

영향 범위: <회사·분기·항목 / 라이브 노출 여부>

---

## 1. 무엇이 통과했나 (어떤 게이트가 왜 못 잡았나)

- 통과 당시 게이트 상태: <RED=N, 어떤 게이트를 돌렸는지>
- **못 잡은 이유**: <구조적 원인. "SKIP-on-missing" / "적용전만 검사" / "부모 present일 때만 동작" / "산술만 검사" 등>

> false-green이면 그 메커니즘을 반드시 한 문장으로: <…>

## 2. 어떤 룰이었으면 잡았나 (구체 룰 정의)

| 항목 | 내용 |
|---|---|
| 룰 id | `<RULE_NAME>` |
| 입력 | <항목번호·필드(값/값_적용후)·대상 회사 집합> |
| 판정식 | <구체 수식/조건> |
| 임계값 | <tolerance / floor> |
| severity | RED(차단) / YELLOW(비차단) |
| 오탐 억제 | <어떤 정상 케이스를 제외해야 하나 — 이게 없으면 룰이 못 쓰인다> |

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code 반영 |
|---|---|---|---|---|
| K-ICS 게이트 | `<fn>` | `scripts/validate_kics_disclosure.py` | 전분기 / display | ✅ / ❌ |
| **push 게이트** | `<fn 또는 미배선>` | `scripts/validate_data_contract.py` | display 7분기 | ✅ / ❌ |

⚠️ K-ICS 게이트에만 배선 = **push를 못 막음**(`prepush_check.py`는 그 스크립트를 호출 안 함).
push 차단이 필요하면 `check_census`에 lift 필요.

## 4. documented exception

- 있음: <(회사,분기) 목록> — 근거: <raw 부재/구조적 미공시/…> — 등재 위치: `<registry 변수명>` (`<파일>`)
- 없음: "없음"

> exemption 추가는 **owner 권한**. 서브에이전트 자체판단 waiver 금지.

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 티켓 / 우선순위 |
|---|---|---|
| <UH-x 또는 "없음"> | <…> | `<inbox 파일명>` / P1·P2 |

---

## close 체크

- [ ] 1 무엇이 통과했나
- [ ] 2 구체 룰 정의
- [ ] 3 배선 위치 + scope (**push 게이트 별도 확인**)
- [ ] 4 exception 근거·등재 위치
- [ ] 5 미배선 잔여 + 후속 티켓

**5칸 미충족 시 close 불가.** `docs/postmortems/README.md` 색인 갱신 후 종결.
