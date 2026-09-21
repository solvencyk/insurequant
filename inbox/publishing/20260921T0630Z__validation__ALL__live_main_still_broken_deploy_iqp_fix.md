---
from: validation
to: publishing
created: 20260921T0630Z
status: open
route: blind_spot
company: ALL
period: 2026.2Q
rule: DEPLOYED_JS_UNDEFINED_CALL (라이브 감사 · UH-27)
iter: 1
---

## 미결 (sender 작성)

**지금 라이브(`www.insurequant.com` = `origin/main`)의 K-ICS 금리민감도 패널이 깨져 있다.**
designer 복구 커밋 `197d15e` 는 작업 브랜치에만 있고 main 배포가 아직 안 나갔다.

실측(2026-09-21, validation):

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_deployed_js.py --git-ref origin/main
  [DEPLOYED_JS_UNDEFINED_CALL] K-ICS.html:1368  IQP
  [DEPLOYED_JS_UNDEFINED_CALL] K-ICS.html:1369  IQP
  → RED=2  (BLOCK)      # origin/main@8ba15d9
```

- 원인 커밋 `2dbc4ca`(2026-09-20 05:55)가 `function IQP(){…}` 정의 한 줄만 지우고 호출부 2곳을
  남겼다. `renderSensDetail()` 이 `ReferenceError` 로 중단된다.
- 영향(실측): 선택 가능한 138 (회사,분기) 버킷 중 **129**, **기본 화면(최신 분기)에서는 39/39 사
  전부**. 살아남는 9버킷은 적용전만 있어 색상이 리터럴인 경우뿐이다.
- **데이터는 100% 정상이다** — 고칠 마스터 셀 0개. 배포만 나가면 해소된다.
- 워킹트리(복구본)는 같은 게이트에서 **RED=0** 이다. 즉 `197d15e` 를 포함해 배포하면 끝난다.

### 시킬 일

1. `197d15e`(+ 이후 HTML 변경)를 main 격리 워크트리로 cherry-push 하는 통상 배포.
   **owner GO 없이 `git push origin main` 금지**(CLAUDE.md §11) — 승인부터 받을 것.
2. 배포 후 검증은 `public_exports/manifest.json` 의 `build_id` 와 함께 **이 한 줄을 더 돌린다**:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_deployed_js.py --git-ref origin/main
  → RED=0 이어야 배포 성공이다.
```

3. **UH-27 (판단 요청).** 신설 게이트는 push 때 라이브 축을 **인쇄만 하고 막지 않는다**
   (`[라이브 감사 · 비차단] origin/main@<sha> RED=n`). 차단으로 걸면 designer 가 main 을 고칠
   때까지 **무관한 작업의 push 까지 전부 막히기 때문**이다. 대안은 위 2번을 `docs/launch_runbook.md`
   배포 후 검증 절에 상시 박는 것 — publishing 이 판단해 반영하거나 owner 에게 올려 달라.

근거: `docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md` §0·§5 ·
designer 티켓 `inbox/designer/20260921T0057Z__owner__ALL_2026.2Q__kics_sens_IQP_referenceerror.md`

## 답변 (recipient 작성 — 처리 후)
