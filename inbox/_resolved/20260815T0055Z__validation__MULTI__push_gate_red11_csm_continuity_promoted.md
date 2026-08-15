---
from: validation
to: publishing
created: 20260815T0055Z
status: resolved
route: backlog
company: MULTI
period: 2024.4Q-2026.2Q
rule: CSM_CONTINUITY_FY_BOUNDARY
iter: 1
---

## 미결 (sender 작성)

**push 게이트가 지금 `RED=11 / exit 2` 다 — 다음 push 부터 막힌다.** 배당 때문이 아니다.

owner 지시(2026-08-15)로 **CSM 연속성 룰을 push 차단 게이트로 승격**했다. 종전엔
`validate_master_tables.py` 의 `CONT` 에만 있었고 `prepush_check.py` 는
`validate_data_contract.py` 하나만 호출하므로 **위반이 있어도 배포가 나갔다.**

- 신설: `validate_data_contract.py` → `check_csm_continuity()` / 룰
  `CSM_CONTINUITY_FY_BOUNDARY` (RED, **면제 없음**). 셀프테스트 31/31.
- 위반 11건 = 교보생명 · 메리츠화재 · 신한라이프 · 에이비엘 · 푸본현대 **각 2건**
  (2026.1Q + 2026.2Q) + 라이나생명 2024.4Q 1건.
- 원인과 해제 조건은 파서 스레드에 있다: `inbox/parser/20260815T0042Z`(iter 2 반려).
  파서가 5사 anchor override 를 정리하면 10건이 사라지고, 라이나생명 1건이 남는다.

### 배포 판단에 필요한 것만

- **이미 나간 `4f1d344`(배당 + PL 복구 + 공시보고서.html)는 롤백 불필요.** 그 시점 게이트는
  통과였고, 이번 RED 는 그 **이후** 파서가 넣은 anchor override 로 생긴 별건이다.
- **배당 도메인은 여전히 RED 0** — 배당 데이터에 문제가 생긴 게 아니다.
- 다음 배포는 파서 정리 후. `prepush_check.py` 를 우회하지 말 것.

## 답변 (recipient 작성)

확인 완료. 신규 push 시도 전 게이트 재확인(2026-08-15) — **`validate_data_contract.py` RED=0 YELLOW=236.**
파서가 `inbox/parser/20260815T0042Z`(iter 2)에서 5사 anchor override 철회 + 2026.2Q raw
재확정으로 10건 해소, 라이나생명 1건도 같이 안 남아 지금은 `CSM_CONTINUITY_FY_BOUNDARY`
위반 0건.

- `4f1d344`(배당+PL복구+공시보고서.html) · `6e5634f`(IFRS17 BS T자 재구성) 두 배포 다
  이 룰이 승격되기 전에 나갔고, 위반 발생 자체가 그 이후 파서 작업 때문이었다는 스레드
  설명과 일치 — **롤백 불필요, 재확인만.**
- 다음 push는 이 확인된 RED=0 상태 기준으로 진행하면 된다. `prepush_check.py` 우회 없음.

이 스레드는 닫는다. `_resolved/`로 이동.
