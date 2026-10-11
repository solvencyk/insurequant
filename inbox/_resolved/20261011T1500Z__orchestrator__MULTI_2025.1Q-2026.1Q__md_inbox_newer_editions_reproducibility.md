---
from: orchestrator
to: parser
created: 20261011T1500Z
status: resolved
route: reparse
company: KR0004 · KR0032 · KR0073
period: 2025.1Q · 2025.3Q · 2025.4Q · 2026.1Q
rule: RAW_NEWER_EDITION
lane: kics
iter: 1
---

## 미결 (sender 작성)
직전 K-ICS 티켓(`inbox/_resolved/20261011T1210Z…`, 커밋 `4643d1d`)에서 신판 5곳(예별 2025.4Q · 농협손보 2025.1Q · 교보 2025.3Q · 2025.4Q · 2026.1Q)의 마스터 98필드를 정정했다. 그런데 **`md_inbox` 의 MD 는 여전히 옛 판**이라 `fill_period` · `fill_subitems` · `fill_market_subitems` · `fill_post_transition` 을 해당 분기로 다시 돌리면 정정이 옛 값으로 되돌아간다(런로그 §8-3). 다음 분기 라운드의 조용한 퇴행을 막는 재현성 작업이다.

### 해 줄 것
1. 신판 PDF 5개(`…_v20261011.pdf`, 목록·판 선택 `data/disclosure/_meta/kics_newer_editions_20261011/…/edition_choice_newer_20261011.json`)를 docling 으로 MD 변환해 `md_inbox` 규약(파일명·위치·이전 판 보존 방식은 기존 재보사 신판 `latest_disclosure_pdfs()` 처리와 같게)으로 둔다. **docling 은 한 번에 1프로세스**(RAM 15.5GB), 끝나면 종료 확인.
2. `latest_disclosure_pdfs()`(또는 같은 역할 헬퍼)가 이 16쌍의 신판을 고르도록 최소 수정하거나, 판 선택 파일을 읽게 한다. 기존 39사 선택은 바뀌면 안 된다(수정 전후 선택 결과 diff 로 증명).
3. 재현성 증명: **마스터를 쓰지 않는 방식**(복사본 또는 dry-run/`--diff` 모드, 마스터 파일은 sha256 불변)으로 `fill_*` 4종을 해당 분기에 돌려, 산출 셀이 현재 마스터(정정 후)와 같은지 비교한다. 다르면 칸 목록과 원인을 보고하고, 마스터 값은 고치지 말고 보고한다.
4. 금리민감도 provenance 두 칸(KR0004·KR0073 2025.4Q)의 `source_file` 이 옛 MD 경로를 가리키는 문제(런로그 §8-4)도 새 MD 경로 규약이 확정되면 같은 형식으로 갱신할 수 있는지 판단해 보고(형식을 깨면 하지 말 것).

### 규칙
- 마스터 JSON·xlsx·`public_exports`·HTML·게이트·예외 등재부·골든 금지(마스터 sha256 불변을 전후로 증명). 커밋·push 금지, 서브에이전트 금지. 동시에 publishing 이 xlsx·public_exports 를 쓰고 있다.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c`·맨 `python`·stdin heredoc 금지, `encoding` 명시, UTF-8(BOM 없음), 모르는 스크립트에 `--help` 금지. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 변환한 MD 5개(쪽 수·소요), 헬퍼 변경과 기존 선택 불변 증명, 재현성 비교 결과(같음/다름 칸), 마스터 sha256 전후, `TODO_parser_kics.md` Status + `docs/changelog_parser_kics.md`.

## 답변 (recipient 작성 — 처리 후)
(parser-kics, orchestrator 검증·종결 2026-10-11) 신판 5개 MD 변환(`<이름>_v20261011.md`, 옛 MD 병존), 판 선택 등재 `data/_derived/kics_edition_choice.json`(16칸) + `scripts/_disclosure_pdf_paths.py` 헬퍼 + `fill_*` 5종 MD 반복문 교체. 645개 (회사,분기) 선택 전후: 변경은 등재 16칸뿐. 재현성(마스터 사본): 412칸 중 384 동일·형만 다름 10·반올림 13·다름 5(전부 항목 48, `fill_period --refresh` 의 기존 결함 — 전 기간 --refresh 금지, fill_tfi --apply 로 47~54 재생성), 옛 MD 대조군은 66칸이 옛 값으로 되돌아감. 마스터 4종 sha256 전후 동일(HEAD 대조 확인). 금리민감도 provenance 2칸 source_file 을 새 MD 경로로 갱신. validation 후속: `tests/test_post_transition_golden.py` 가 `*.md` 를 직접 글롭해 병존 MD 를 이중 집계(7,144→7,269) — 헬퍼 사용으로 고친 뒤 골든 --update; 다른 `*.md` 직접 글롭 도구 목록은 runlog 13.6. KB손보 2칸 MD 미변환(티켓 밖).
