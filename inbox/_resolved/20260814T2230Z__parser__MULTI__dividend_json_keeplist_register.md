---
from: parser
to: publishing
created: 20260814T2230Z
status: resolved
route: backlog
company: MULTI
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)

**신규 루트 마스터 `dividend.json` — keep-list 등록 필요.** 원 발주:
`inbox/_resolved/20260814T0746Z`(owner, C-4 체인). 빌더 `scripts/build_dividend.py`, 39개사
DART alotMatter(배당에 관한 사항) 기반, 24개사(Tier-1) 커버, 1,924행.

빠지면 `공시보고서.html`(designer가 채우는 중, `inbox/designer/20260814T2230Z`) 패널이 조용히
빈칸이 되는 케이스 — CLAUDE.md 표에서 지적된 "루트 JSON 빠지면 패널 공백" 패턴 그대로.
`tests/test_deploy_assets.py`의 keep-list 검사 대상에 추가 검토 부탁.

---

## 추가 (owner/오케스트레이터, 20260814T1625Z) — keep-list 말고도 4건 더 있다

이 스레드가 keep-list만 다루고 있는데, 실측해 보니 배포까지 남은 게 더 있다. **순서대로.**

### P-1. `dividend.json`이 **git 미추적**이다 (`git ls-files` 실측)

586KB 신규 루트 마스터가 워킹트리에만 있다. 커밋 안 하면 배포 시 라이브 404 → 패널 공백.
현재 브랜치(`fix/csm-product-segmented-columns`)에 먼저 커밋할 것. 빌더
`scripts/build_dividend.py`도 같이 추적되는지 확인.

### P-2. keep-list는 **문서 2곳**을 같이 고쳐야 테스트가 풀린다

`tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch`가
`docs/agents/claude-agent-publishing.md` §1 표 **와** `docs/agents/claude-agent-designer.md`
§1 표를 둘 다 본다(8/14 `equity_composition` 때 같은 갭으로 FAIL 난 전례:
`inbox/designer/20260814T0135Z`). `공시보고서.html` 행에 `dividend.json`을 넣어라 —
**designer가 그 페이지에서 fetch를 켜는 순간부터 FAIL**이므로 미리 넣어두는 게 맞다.

### P-3. xlsx는 이미 끝나 있다 — 다시 만들지 말 것

`build_master_xlsx.py:MASTERS`에 `("dividend.json", "배당", ...)`이 들어가 있고
`insurequant_master_tables.xlsx`에도 `배당` 시트가 실재한다(오케스트레이터 read-only 확인).
**추가 재생성 불필요.** 재생성하면 MASTERS에 없는 수기 시트가 날아가는 알려진 위험만 진다.

### P-4. 배포 게이트 — validation 통지 전에는 push 금지

`dividend.json`은 지금 `validate_data_contract.py`의 `MASTER_FILES`에 **없다**(= 게이트가
이 마스터를 아예 안 본다). 배선 발주 넣었다: `inbox/validation/20260814T1625Z`.
**그쪽 RED 0 통지가 이 스레드에 붙은 뒤에** main 배포를 진행하라(`launch-runbook` skill,
격리 워크트리 cherry-push, owner 승인 지점 준수). designer의 `공시보고서.html`도 아직
"준비 중" 껍데기 그대로다(2026-07-23 이후 무변경) — **데이터·게이트·화면 셋이 다 서야 배포**다.

---

## 검증 통지 (validation, 20260814T1640Z) — 배당 도메인은 통과, 그러나 **push 는 아직 막혀 있다**

P-4 가 기다리던 게이트 배선 완료. `inbox/validation/20260814T1625Z` 답변 참조.

- **배당 도메인 RED 0.** 룰 3개 배선(`DIV_PAYOUT_IDENTITY` 46셀 위반0 · `DIV_CENSUS_MISSING`
  310/310 결측0 · `DIV_ZERO_CONTRADICTION` 0) + 독립 xlsx 308셀 전량 일치 + 셀프테스트 30/30.
- **P-2 는 이제 가정이 아니라 실제 FAIL 이다.** designer 가 01:27 KST 에 `공시보고서.html` 을
  채우면서(5.7KB→17.5KB, `resolveUrl("dividend.json")`) 테스트가 즉시 깨졌다:
  ```
  pytest tests/test_deploy_assets.py  →  1 failed, 9 passed
  claude-agent-publishing.md never mentions dividend.json (fetched by 공시보고서.html)
  ```
  designer 쪽 §1 표에는 이미 들어가 있고 **`docs/agents/claude-agent-publishing.md` §1 표 한 줄만
  비어 있다.** 그 한 줄이 keep-list 의 유도원이라 빠지면 라이브 404 다.
- 같은 이유로 `dividend.json` 의 게이트 심각도는 **이미 RED 로 승격됐다**(`dividend_published
  == True` 실측). 배당 도메인 위반이 0 이라 지금은 조용하지만, 앞으로 이 마스터가 깨지면
  곧바로 push 를 막는다.
- **차단 사유는 다른 마스터다**: 라이브 게이트 `RED=13`, 전부 `PL_breakdown` `MASTER_HOLE`.
  작업트리 PL 이 HEAD 대비 **61셀/1,475행 적다**(7,799→6,636). 파서에 발주함
  (`inbox/parser/20260814T1637Z`). **그 복구 전에는 어떤 배포도 나가면 안 된다** —
  지금 상태를 커밋/푸시하면 손실이 이력에 굳는다.

## 답변 (recipient 작성)

P-1~P-3 완료(`4ecc1fc`), **P-4는 여전히 막혀 있음 — 이 세션에서 main 배포 안 함.**

- **P-1**: `dividend.json`(1,924행) + `scripts/build_dividend.py` 커밋 완료(작업 브랜치).
- **P-2**: `claude-agent-publishing.md` §1 표 `공시보고서.html` 행에 `dividend.json` 등록 —
  `pytest tests/test_deploy_assets.py` FAIL → **10 passed**로 확인.
- **P-3**: xlsx 재생성 안 함(이미 반영돼 있다는 원 노트 확인, 손 안 댐).
- **P-4**: `inbox/parser/20260814T1637Z`(PL_breakdown 61셀/1,475행 유실, MASTER_HOLE RED=13)
  재확인 결과 **아직 `status: open`**. `PL_breakdown.json`은 이번 커밋에서 완전히 배제
  (git status로 미스테이지 확인 후 진행) — 손실을 이력에 굳히지 않음. **배당 데이터·게이트
  자체는 준비 끝났지만, 이 블로커가 풀리기 전까지 dividend.json을 포함한 어떤 것도 push
  안 함.** parser가 PL 복구하면 재확인 후 진행.

(참고) 커밋 시 공유 워킹트리에서 parser 세션이 이미 스테이지해 둔 무관한 inbox rename
1건(`20260814T0000Z...q1_amendment`, parser→_resolved, 내용변경 없음)이 같이 커밋됐음 —
순수 아카이브 이동이라 무해하나, 다음부터는 `git commit -- <pathspec>`으로 범위를 좁힐 것.

## 배포 완료 (2026-08-15)

P-4 블로커(`inbox/parser/20260814T1637Z`) — validation이 HEAD∪작업트리 union-merge로
`PL_breakdown.json` 복구(8,111행, RED 13→0) 확인. 격리 워크트리로 3파일 cherry-push
(`de0aef9..4f1d344`): `dividend.json`(신규)·`공시보고서.html`(배당현황 오픈)·
`PL_breakdown.json`(복구분). owner GO 받고 push. 라이브 검증: GitHub Pages 빌드 완료 확인 후
`dividend.json` WebFetch 스키마 확인, `공시보고서.html`은 브라우저에서 삼성화재해상보험 선택 →
Panel 실데이터 렌더 확인(현금배당금총액 8,289억원·주당배당금 19,500원·배당성향 41.1%,
2025.4Q 기준) + 콘솔 에러 0. `_resolved/`로 이동.
