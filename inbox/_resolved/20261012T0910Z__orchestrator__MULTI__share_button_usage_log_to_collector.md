---
from: orchestrator
to: designer
created: 20261012T0910Z
status: resolved
route: feature
company: MULTI
period: MULTI
iter: 1
---

## 미결 (sender 작성)
owner 질문(2026-10-12 채팅): 「각 섹션별로 공유 버튼 만들어 둔 것(INDEX 전체화면 공유 포함)도 insurequant collector 워크시트에 기록·집계되게 할 수 있나?」 → 가능하다. 조사 결과:
- 백엔드는 `scripts/appsscript/insurequant_collector.gs`(owner 구글 계정의 Apps Script 웹 앱, 시트 `insurequant_collector` id `16nOU-VVS1k8qxaZ81srd8akI_N1P3bEzj_lmPdMf0Z8`). `doPost` 가 payload 키대로 헤더를 자동 확장하고, `kind` 가 `report` 면 `reports` 탭(+메일), **그 외 모든 값은 `downloads` 탭**으로 보낸다 — 공유 이벤트를 그냥 보내면 방명록(`downloads`)에 섞인다. 그래서 `kind: "share"` → **`shares` 탭** 분기를 스크립트에 추가해야 하고, 스크립트는 owner 가 구글에서 **새 버전으로 다시 배포**해야 반영된다(코드는 저장소 파일을 고쳐 두고 owner 가 붙여넣기; URL 은 「배포 관리 > 수정 > 새 버전」이면 그대로).
- 사이트 쪽: `forms-config.js` 의 `window.IQ_FORMS.submit(kind, values)` 가 이미 전 페이지(`index`·`K-ICS`·`IFRS17`·`compare`·`공시보고서`·`privacy`)에서 쓰인다. 공유 메뉴·섹션 공유 버튼은 `theme.js`(공유 메뉴 ~446행~, `shCopyLink`·전체 스크린샷·`mountSectionShare` 섹션 버튼)에 있다. CSP `connect-src` 에는 `script.google.com`·`script.googleusercontent.com` 이 이미 있다.

### 해 줄 것
1. **`theme.js`**: 공유 동작마다 이름·이메일 등 개인정보 **없이** 익명 이벤트 하나를 `IQ_FORMS.submit('share', {...})` 로 보낸다(`forms-config.js` 가 없거나 미설정이면 조용히 건너뜀, 공유 동작 자체는 절대 지연·실패시키지 않는다 — 전송은 fire-and-forget, 예외 삼킴). 필드(키는 영어 소문자·스네이크, 시트 헤더가 자동 확장): `page`(파일명: index/K-ICS/IFRS17/compare/…), `action`(`link_copy` | `page_screenshot` | `section_screenshot`), `section`(섹션 공유일 때 `data-share-section` 값, 아니면 빈칸), `company`(공유 컨텍스트의 대상 회사 — 스크린샷 제목에 쓰는 `context()`/`#company` 값, 없으면 빈칸), `device`(`touch`|`pointer`), `result`(`ok`|`truncated`|`error` — 가능하면 스크린샷 완료 시점에 채움). **`iq_internal=1` 로 진입한 세션(owner 내부 확인)은 전송하지 않는다**(GA4 와 같은 규칙, 집계 오염 방지). 같은 동작의 연타(1.5초 이내 동일 page·action·section)는 한 번만 전송.
2. **`scripts/appsscript/insurequant_collector.gs`**: `doPost` 에 `kind === 'share'` 분기를 추가해 `shares` 탭에 쌓는다(기존 `download`·`report` 동작·헤더 자동 확장은 **그대로**). 집계를 위해 첫 `share` 제출 때 (없으면) **`shares_summary` 탭을 만들어 `QUERY` 수식**으로 `page`·`section`·`action` 별 건수를 자동 집계하게 한다(예: `=QUERY(shares!A:J, "select B, D, C, count(A) where A is not null group by B, D, C label count(A) '횟수'", 1)` — 실제 열 위치는 헤더 자동 확장 결과에 맞춰 헤더 이름 기반으로 구성하거나, 열 위치에 의존하지 않도록 `ARRAYFORMULA`/`FILTER` 를 쓰는 등 견고하게; 최근 7일 건수 칸 포함). 건마다 메일은 보내지 않는다. 스크립트 상단 주석에 owner 재배포 절차(2~3줄)와 `shares` 탭 열 설명을 적는다. **이 스크립트는 저장소 파일일 뿐 이 PC 에서 배포되지 않는다** — 보고에 「owner 가 해야 할 일: 구글 Apps Script 편집기에서 이 파일 내용으로 교체 → 배포 관리 → 새 버전」을 한국어 3줄로 적는다.
3. **`privacy.html`**: 수집 항목 문단에 「공유 버튼 이용 기록(페이지·섹션·공유 종류·대상 회사·기기 종류, 개인 식별 정보 없음)」을 **기존 문체·구조에 맞춰 한 줄** 추가(방명록·오류 제보 설명과 같은 자리). 법적 문구를 새로 지어내지 말고 기존 문장을 따라 쓰고, 보관·이용 목적은 기존 서술과 같게(이용 현황 파악).
4. **점검**: `?iq_internal=1` 없이(실제 전송 경로) 로컬/스테이징에서 공유 버튼 3종(링크 복사·페이지 전체·섹션)을 눌러 `IQ_FORMS.submit` 이 올바른 페이로드(키·값)로 한 번씩만 호출되는지 확인한다 — **실제 구글로 전송해 시트를 오염시키지 않도록** 테스트 때는 `fetch` 를 가로채(콘솔 후킹/헤드리스 스텁) 페이로드만 캡처한다. `iq_internal=1` 에서는 호출이 0 인지, 연타 디바운스, `forms-config.js` 미로딩 페이지에서 오류 없음, 공유 동작 자체(저장·복사)가 그대로 되는지, 모바일 375px 확인. `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py`·(있으면 `tests/test_share_screenshot.py`) 통과, `scripts/compute_sri.py`/CSP 와 충돌 없음.

### 규칙
- 이름·이메일·IP·정확한 위치 등 개인정보는 **수집·전송 금지**(`ua` 는 스크립트 쪽 기존 동작 그대로). 데이터 인라인 금지. 화면 문구는 공시 표기·기존 문체(설명 덧붙이기 금지). 마스터 JSON·xlsx 수정 금지. 커밋은 자기 파일만(명시 경로, `git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json` 제외·다른 에이전트 미커밋 파일 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push 금지**. 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결). PC 가 느리니 시험은 한 번에 하나씩 기다릴 것(시험을 건너뛰지 말 것).

### 보고 (3~5줄 존댓말)
- 변경 위치(줄), 전송 페이로드 예시 1건, 점검 결과, owner 가 해야 할 재배포 절차, 커밋 해시. `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 b3a2ae2). theme.js shLog(익명 이벤트 fire-and-forget, iq_internal=1 제외, 1.5초 디바운스), insurequant_collector.gs share 분기(shares 탭 + shares_summary QUERY 탭), privacy.html 문단, compare.html 에 forms-config.js 로드 1줄. 가로챈 fetch 로 페이로드만 확인(실전송 0), 시험 4종 통과. owner 재배포: Apps Script 코드 교체 -> 배포 관리 -> 새 버전(스크립트를 사이트보다 먼저).
