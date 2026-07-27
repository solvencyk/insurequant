---
from: owner
to: parser
created: 20260727T0700Z
status: open
route: backlog
company: MULTI
period: ALL
lane: kics
rule: CONTEXT_TRIM
iter: 1
---

## TODO_parser_kics.md `## Status` 섹션 압축 요청 (owner 지시, 컨텍스트 슬림화)

**배경.** 2026-07-27 owner가 세션마다 로드되는 컨텍스트 파일 슬림화를 지시. 오케스트레이터가 `TODO_parser_kics.md`를 **832 → 649줄**로 이미 줄였다(커밋 `d7f2ce2`) — TRANS-18(이름만 Open, 실제 완결) · NEW-2 · TRANS-AFTER-9 · LOCALIZER-FITZ의 **완결 `[x]` 상세**를 압축하고 진짜 open `[ ]`은 100% 보존. 완결 상세는 전부 `docs/changelog_parser_kics.md`에 있어 안전했다.

**남긴 것 = `## Status` 섹션(~500줄).** 오케가 손대지 않았다. 이유: 이 섹션은 ~20개 날짜별 라운드(2026-07-16 ~ 06-14)가 누적됐는데, **완결 이력과 "현재 게이트 상태" 맥락이 섞여** 있어서, 어느 줄이 아직 load-bearing(현재 documented exception 근거 · 현재 RED 처분 설명)인지는 **kics 레인의 자기 맥락으로 판단**해야 안전하다. 오케가 잘못 압축하면 게이트 근거를 잃는다.

**요청.** kics 세션이 다음 호출 시 이 섹션을 압축하라:
1. **최신 라운드(현재 게이트 상태를 서술하는 것)는 유지.** 예: 2026-07-16 전사 스윕 결과(continuity 34셀/5쌍, core RED 12 등)가 현재 게이트 상태와 일치하면 유지.
2. **오래된 완결 라운드(현재 상태와 무관한 과거 fix 서술)는 changelog 참조로 압축.** 각 라운드가 `docs/changelog_parser_kics.md`에 대응 항목이 있는지 대조 후(대부분 있음), "라운드 헤더 + 최종 결과 1줄 + changelog 날짜 참조"로.
3. **절대 보존:** 현재 라이브 게이트(`report_latest.json`)의 RED 처분을 설명하는 문장, documented exception 근거(있다면). 삭제 전 라이브 게이트를 한 번 돌려 현재 RED 목록과 대조하고, Status의 어떤 서술이 그 RED를 설명하는지 확인할 것.
4. 목표: Status ~500줄 → 현재 상태 요약 + 최근 1~2 라운드. 나머지는 changelog.

**검증.** 압축 후 `pytest tests/test_deploy_assets.py`(문서 정합성·BOM 가드) 통과 + 한글 read-back. `TODO_parser_kics.md`는 UTF-8(BOM 없음) 유지.

참고: 오케의 압축 방식·기준은 커밋 `d7f2ce2` 메시지에 상세.
