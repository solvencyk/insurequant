---
from: owner
to: parser
created: 20260727T0700Z
status: answered
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

## 답변 (parser 작성 2026-07-27)

지시대로 압축 완료. `TODO_parser_kics.md` **649 → 273줄**(`## Status` 섹션 504 → 127줄).

**절차**: (1) `validate_kics_disclosure.py` 라이브 재실행 — core RED 12, 전부 KR0087 2023.2Q(7개
룰)·KR0079 2023.2Q(rule8_life)·KR0097 2024.2Q(4개 룰), 셋 다 image-scan/OCR 관련 기존 documented
건. (2) `## Status`에서 이 3건을 이름으로 직접 서술하는 문장이 있는지 grep — **없음 확인**(이 라인들의
근거는 `TODO_parser_kics.md`가 아니라 루트 `TODO.md`의 documented exception 목록에 있음, 별도 파일).
즉 이 섹션 자체에는 "현재 RED를 설명하는" 문장이 없었음 — 순수 라운드별 작업이력. (3) 최근 4라운드
(2026-07-15 1~3차 + 2026-07-16 owner 스윕, 총 ~87줄)는 **현재 게이트 상태를 직접 서술**(continuity
break 34셀/5쌍, census 4, 비적용사 스윕 결과 등 — 지금 라이브 수치와 일치)해서 원문 그대로 보존. (4)
2026-07-07~07-12 사이 **18개 완결 라운드**는 전부 `docs/changelog_parser_kics.md`에 대응 항목이 있음을
grep으로 사전 대조(`grep -c` 24건 매치 확인 — TODO의 라운드 수보다 changelog 항목이 더 많음, 일부는
changelog가 더 세분화돼 있어 정보 손실 없음 확인) — "라운드 헤더 + 최종결과 1줄 + changelog 참조"로 압축.
(5) 2026-07-07 7차만 예외 처리 — 8차가 그 결론을 명시적으로 무효화한다고 원문에 already 적혀 있어서,
압축 후에도 그 무효화 사실 자체는 한 줄로 남김(안 그러면 "왜 7차가 없지"라는 혼란 유발).

**검증**: `pytest tests/test_deploy_assets.py` 8 passed. 한글 read-back 확인(깨짐 없음). UTF-8 BOM 없음
(Edit 도구가 기존 파일 인코딩 그대로 보존).

압축 후에도 여전히 남아있는 것: 최근 4라운드 원문(진행 중/최근 결정 근거라 유지), `## 🔴 Open — P1`
이하 섹션(TRANS-18 등, 이번 요청 범위 아님 — 그대로 둠).
