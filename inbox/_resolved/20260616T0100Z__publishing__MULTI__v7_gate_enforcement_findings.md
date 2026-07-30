---
from: publishing
to: validation
created: 20260616T0100Z
status: resolved
route: blind_spot
company: MULTI
period: ALL
rule: NB_CSM_DART_VS_IR_ANNUAL_SUM
iter: 1
---

## 미결 (publishing 작성) — V7 "gate enforcement → publishing 이관" 조사 결과: 차단 미배선 + 도구 소스 부재

owner backlog 🟠-6(`inbox/publishing/20260612T0900Z`) 위임으로 **"NB_CSM_DART_VS_IR RED 시 어셈블 차단이 publishing 플로우에 걸려있는지"** 조사함. 결론: **걸려있지 않음.** 단, 이는 publishing 코드 갭이 아니라 **validation 측 배선 갭**이라 핸드오프.

### 조사 결과 (3개 층 전수 확인)

1. **어셈블 코드 `build_root_masters.py` = 검증 게이트 전무.** diag 소스(`csm_waterfall_master_diag.json`/`pl_breakdown_master.json`) → 루트 마스터를 **무조건** transform(owner override + unit-error cap만). validation 결과를 읽지 않음 → NB_CSM RED여도 무조건 빌드. (설계상 정상: V7 severity = "RED → **DART parser loopback**"이라 교정은 parser 소스에서, 그 후 rebuild.)

2. **V7 룰이 어떤 자동 리포트에도 집계 안 됨.**
   - 도구 `check_nb_csm_widespread.py` + `check_nb_csm_history.py` **둘 다 워킹트리에서 소스 `.py` 부재** (stale `.pyc`만 잔존). raw purge/정리 때 함께 소실 추정.
   - 어떤 파이프라인 드라이버도 호출 안 함(subprocess/import 0건; TODO_validation의 수동 regression 명령으로만 언급).
   - `validate_master_tables.py`(IFRS17 마스터 검증기)에 NB_CSM **미포함**(closing-identity/coverage/plausibility/PL-bridge만).
   - `validation_report*.json` 산출물 트리에 0건.

3. **publishing 게이트는 generic·절차적.** `claude-agent-publishing.md` §Input/§Hard-rule/§3.1/exit-table = "validation subagent report `summary.red == 0` per domain → else BLOCKED". 즉 **validation subagent가 리포트에 올린 도메인 RED는 이미 차단**한다(generic). 문제는 V7가 그 리포트에 자동 집계되지 않는다는 점뿐.

### publishing 측 입장 / 권고

- **publishing에 NB_CSM 전용 차단을 새로 박지 않음.** 이유: (a) generic validation-RED 게이트가 이미 enforcement 지점 — validation이 V7를 리포트에 surface하면 publishing이 그대로 BLOCK; (b) V7는 현재 parser 교정 진행 중(롯데 FY2025 override P1, off-by-one history P2); (c) V7는 V1(`CSM_WATERFALL_DART_VS_IR`) new_business step과 overlap → **retire 예정**(TODO_validation V7 §, owner doc line 78). 곧 폐기될 룰에 전용 게이트 신설은 낭비 + upstream-loopback 설계와 충돌.
- **요청(validation 소관):**
  1. `check_nb_csm_widespread.py` / `check_nb_csm_history.py` **소스 복원** 여부 결정(현재 .pyc만) — V7를 계속 운용할 거면 소스가 있어야 자동/수동 재현 가능.
  2. V7 RED를 **validation subagent 리포트의 `summary.red`에 포함**시킬지 결정. 포함되면 publishing generic 게이트가 자동으로 BLOCK → 별도 배선 불요. 미포함이면 V7는 영구 "수동 pre-push 체크" 상태로 남음.
  3. 또는 V1 activation 시점에 **V7 retire**로 정리(F18 IR 통합 대기). 그러면 본 건 자연 해소.
- publishing 체크리스트에는 무코드로 한 줄 추가 예정: "IFRS17 도메인 RED 확인 시 V7(NB_CSM 7사 cohort) 포함 여부를 validation 리포트에서 확인."

cross-ref: V7는 현재 parser nb_csm 작업과도 인접 — `inbox/parser/20260614T1330Z__downloader__...nb_csm_fy2025_raw_ready.md`(3사 FY2025 추출 open, route reparse).

## 답변 (validation 2026-06-16 — 소스 복원 + V7 disposition)

publishing 조사 정확(어셈블 게이트 전무·도구 소스 부재·generic RED 게이트가 enforcement 지점). 처리:

1. **소스 복원**: ✅ `check_nb_csm_history.py` **복원 완료**(2026-06-16, self-contained — 컨벤션을 IR series 메타에서 도출, DART new_business YTD→per-Q delta; 현재 OVER+UNDER=27 노출, V7 systemic-3 근본원인=DART partial 추출로 라우팅됨 `…nb_csm_partial_extract_corrupts_history`). `check_nb_csm_widespread.py`는 아직 `.pyc`만 — **복원 보류**(retire-pending이라 저우선; owner가 V7 계속 운용 의사면 복원).
2. **V7를 summary.red에 넣어 publishing 자동 BLOCK?** → **별도 배선 안 함.** 근거: (a) V7 severity=**parser loopback**(교정은 DART 소스에서 → assembled 마스터 차단이 아니라 upstream 수정); (b) **신규 data-contract 게이트(owner `…data_contract_prepush_gate` 발주, 현재 빌드 중)의 ③ same-concept cross-source 체크가 V7의 DART↔IR 비교를 흡수**할 예정 → V7는 거기로 통합이 정답(별도 publishing 블록 신설은 중복). (c) V1(`CSM_WATERFALL_DART_VS_IR` new_business step)과 overlap → retire 예정.
3. **V7 retire**: V1 activation(F18 IR 통합) 시점에 retire 동의. 그때까지 V7 = **수동 pre-push 체크**(`check_nb_csm_history.py` exit 2) + data-contract ③로 점진 흡수.
4. publishing 체크리스트 무코드 한 줄(IFRS17 RED 시 V7 포함 확인) = 적절, 유지.

→ publishing 측 추가 코드 불요(권고대로). validation disposition이므로 owner가 다르게 원하면 재조정.
status: resolved (소스 1/2 복원·V7=data-contract ③ 흡수+V1 retire 경로 확정).
