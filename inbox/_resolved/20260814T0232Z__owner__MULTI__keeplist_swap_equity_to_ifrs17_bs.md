---
from: owner
to: publishing
created: 20260814T0232Z
status: resolved
route: backlog
company: MULTI
period: ALL
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

**owner 지시 (2026-08-14): `equity_composition.json`(항목 1-49)을 아카이브한다.**
17BS 정본은 **`IFRS17_BS.json`**(항목 1-5) 한 벌. 배포 배선 두 곳을 갈아끼우면 된다.

관련: 파서 `inbox/parser/20260814T0232Z` · 게이트 `inbox/validation/20260814T0232Z` ·
Panel 7 `inbox/designer/20260814T0232Z`.

**`equity_composition.json` 은 main 에 push 된 적이 없다** — 라이브 되돌릴 것 없음.

### 할 일

1. **keep-list 교체.** `docs/agents/claude-agent-publishing.md` §1 표(69행)와 §9 배포목록(279행 부근)에서
   `equity_composition.json` · `equity_composition_provenance.json` 을 빼고 **`IFRS17_BS.json`** 을 넣어라.
   74·78행의 "아직 push 대상 아님" 단서도 같이 정리(이력 서술은 남기되 현재 상태와 안 어긋나게).
   `pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` 가 이 표를
   HTML 이 실제 fetch 하는 것과 대조한다 — **designer 작업과 파일명이 맞아야 통과**한다.
2. **마스터 xlsx `17BS` 시트 소스 재조준.** `scripts/build_master_xlsx.py:18` 이
   `("equity_composition.json", "17BS", ...)` 로 걸려 있다 → **`IFRS17_BS.json`** 으로.
   열이 9개→8개로 준다(`값_당분기` 없음, 전부 스톡). 항목번호 체계도 다르다(1-5 = 자산/부채/자본/
   AOCI/해약환급금준비금). 시트 이름 `17BS` 는 그대로.
3. 재생성은 상시 디폴트대로 **공식 `xlsx` skill** 로. 마스터를 openpyxl 로 load+save 하지 말 것
   (값열 수식 캐시가 통째로 날아간다 — 기존 사고 전례).

### 순서

파서가 아카이브를 끝내고 `IFRS17_BS.json` 을 OFS 기준으로 재빌드한 **뒤에** xlsx 를 재생성하라.
지금 파일엔 삼성생명 2025.1~3Q 자산총계가 stale CFS 값(318,858,553 3분기 동일)으로 들어가 있다
(`inbox/parser/20260814T0216Z` P-1). 먼저 만들면 틀린 답지를 배포한다.

### 확인

- `pytest tests/test_deploy_assets.py` 통과
- `python scripts/prepush_check.py` / `validate_data_contract.py` RED 수
- push 는 **RED=0 + owner 승인 후.** 평소대로 보고·권고만 하고 `git push` 는 실행하지 말 것.

## 답변 (recipient 작성)

처리(2026-08-14, publishing) — 3개 할 일 전부 완료, 파서의 OFS 재빌드(16:35 KST, 1,637행) 이후 진행:

1. **keep-list 교체 완료.** `docs/agents/claude-agent-publishing.md` §1 fetch표에 `IFRS17.html` 행 → `IFRS17_BS.json` 추가, §9 keep-list 스냅샷에 `IFRS17_BS.json`을 "NOT on main yet" 주석과 함께 추가(RED=0 후 반영 예정 명시). §1에 `equity_composition.json` 아카이브 + 대체 경위 설명 단락 신설. §0 "Current live" 라인을 실측(2026-08-14, RED=42, `[IFRS17_BS] BS_CENSUS_MISSING_ITEM`, 이미 parser로 라우팅됨)으로 갱신. `pytest tests/test_deploy_assets.py` 10 passed(`test_docs_agree_with_what_pages_fetch` 포함).
2. **`build_master_xlsx.py:18` 소스 재조준 완료.** `("equity_composition.json", "17BS", ...)` → `("IFRS17_BS.json", "17BS", ...)`로 교체(MASTERS 리스트 최상단). 시트명 `17BS` 유지.
3. **재생성 완료.** 공식 `xlsx` skill 워크플로우로 진행 — 기존 xlsx에 owner 수기 피벗(`17BS_PIVOT`, 해약환급금준비금 기적립액 검토용)이 있어 owner에게 확인받고(해당 보정 로직은 이미 `build_ifrs17_bs.py`에 코드로 이식됨 — 흥국생명 값 재검증 일치) `.bak_20260814_prepivotloss` 백업 후 재생성. 17BS 시트 8열(값_당분기 없음, 전부 스톡) · 1,637 데이터행, `IFRS17_BS.json`(mtime 16:35) 보다 xlsx가 최신(mtime 16:51) 확인.

**확인 결과:**
- `pytest tests/test_deploy_assets.py` — 10 passed.
- `python scripts/validate_data_contract.py` — **RED=42**(전량 `[IFRS17_BS] BS_CENSUS_MISSING_ITEM`, 6개사 Tier-2 본표 부분추출) / YELLOW=219. 이 RED는 parser 소관(`inbox/parser/20260814T0620Z`, status: open, iter 2) — publishing이 고칠 대상 아님, xlsx/keep-list 작업과 무관하게 이미 라우팅돼 있음.
- **push는 보류.** RED=42라 `prepush_check.py` exit 2 — 지시대로 push는 실행하지 않음, RED=0 + owner 승인 전까지 §9 실제 배포(main 반영)는 안 함. keep-list 문서 갱신은 "표=현재 fetch 실태 반영"이 목적이라 RED와 무관하게 지금 반영.

**남은 것:** parser가 6개사(AIG손보·하나손보·신한이지손보·메트라이프·IBK연금·비엔피파리바카디프) Tier-2 본표 추출을 고치면(`inbox/parser/20260814T0620Z`), publishing이 재확인 후 RED=0 시 §9 실제 push 진행. 이 티켓 자체(keep-list+xlsx)는 완결 — `_resolved/`로 이동.
