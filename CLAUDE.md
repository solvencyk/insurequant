# Insurequant — 룰 & 인덱스

한국 보험사 재무지표(K-ICS·IFRS17) 자동 파이프라인. 이 파일은 **룰만** 담는다. 룰이 생긴 배경·사고 기록은
`docs/claude-md-history.md`(2026-09-12 이전 전문, 필요할 때만 연다).

## 1. 구조 — 5-stage 파이프라인 + jp 레인

| stage | 프롬프트 | 활성 TODO | 이력 |
|---|---|---|---|
| 1 downloader | `docs/agents/claude-agent-downloader.md` (+ `source-catalog.yaml`) | `TODO_downloader.md` | `docs/changelog_downloader.md` |
| 2 parser (2 레인 ∥) | `docs/agents/claude-agent-parser.md` + `docs/domains/claude-agent-{kics,ifrs17}.md` | `TODO_parser_{kics,ifrs17}.md` | `docs/changelog_parser_{kics,ifrs17}.md` |
| 3 validation | `docs/agents/claude-agent-validation.md` | `TODO_validation.md` | `docs/changelog_validation.md` |
| 4 publishing (마스터 JSON·배포, `git push` 는 사람) | `docs/agents/claude-agent-publishing.md` | `TODO_publishing.md` | `docs/changelog_publishing.md` |
| 5 designer (HTML/CSS/차트) | `docs/agents/claude-agent-designer.md` | `TODO_designer.md` | `docs/changelog_designer.md` |
| **jp** (일본 ESR, 2026-09-12 신설) | `docs/domains/claude-agent-jp.md` + 에이전트 `jp-collector` | `TODO_jp.md` | `docs/changelog_jp.md` |

- stage 는 **순차 파이프라인**(downloader→parser→validation→publishing→designer). 4↔5 는 서로 파일을 안 건드린다(publishing = 마스터 JSON, designer = HTML).
- parser 는 kics(`src/solvency/parser/`→`kics_disclosure.json`)·ifrs17(`src/ifrs17/`→CSM/PL/17BS 마스터) 두 레인을 **별도 세션에서 병렬**로. 공유 inbox `inbox/parser/` frontmatter `lane:`.
- **jp 레인은 한국 stage 프롬프트를 읽지 않는다.** 일본 공시는 양식·주기·언어가 다르므로 자기 도메인 문서와 `inbox/jp/` 만 쓴다. designer·publishing 은 공유(각 프롬프트의 jp 절).
- cross-stage 항목은 루트 `TODO.md` + `docs/claude-changelog.md`. 도메인 참고 `docs/domains/`, 흐름도 `docs/flows/`.

## 2. 세션 시작·갱신

1. 읽는 순서: 이 파일 → 루트 `TODO.md` → 자기 stage 의 `TODO_<stage>.md` + 프롬프트(parser 는 레인별 TODO + 공유 프롬프트 + 도메인 문서).
2. **changelog·`docs/todo_archive_*.md`·`docs/claude-md-history.md` 는 읽지 않는다** — 과거 결정의 근거가 필요할 때만 연다.
3. 각 `TODO*.md` Status 는 **최신 5개**만 유지. 밀린 항목은 `docs/todo_archive_<이름>.md` 헤더 바로 아래에 **한 글자도 안 고치고** 잘라 붙인다(최신이 위).
4. 변경·실행 후 **해당 stage TODO 맨 위 갱신 필수**, 완결 항목은 stage changelog 에 기록. cross-stage 면 루트 `TODO.md` + `docs/claude-changelog.md`.

## 3. "뭐가 남았냐" 는 재서 답한다 (필수)

```bash
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/status_report.py --fast
```

TODO·changelog 를 읽어서 답하지 말 것. TODO 는 의도, `status_report` 는 사실 — 어긋나면 TODO 를 고친다. TODO 항목을 인용하려면 그 주장을 먼저 기계로 확인한다.

## 4. 실행 환경

- python 은 **항상 풀패스** `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` (슬래시 `/`). 맨 `python` 은 스토어 3.13 이라 `docling` 이 없다. 서브에이전트 프롬프트에도 명시.
- 멀티라인 `python -c` 금지(서브에이전트 영구 행). 스크립트 파일로 쓴다. 파일 I/O 는 `encoding` 명시.
- 문서·`.py` 전부 **UTF-8, BOM 없음**. 한글이 깨지는 환경이면 영어로 쓴다. 중국어처럼 보이는 깨진 한글을 남기지 말 것. 쓴 뒤 첫 줄 read-back.

## 5. push 게이트 (훅으로 강제)

새 클론·워크트리는 먼저 `git config core.hooksPath .githooks` (설정은 클론마다 로컬; `git config --get core.hooksPath` 로 확인).
훅 = `scripts/prepush_check.py`(~8분): ① data-contract 하드게이트 ①b K-ICS 룰 게이트(`validate_kics_disclosure.py`) ② anomaly triage ③ inbox 위생(`check_inbox_hygiene.py`)
④ 오프라인 테스트(골든 + `test_rule_coverage_manifest.py` + `test_identity_tautology.py`). `main` 처럼 `scripts/` 없는 slim 트리는 경고만.
**"문서에 mandatory 라고 썼다" ≠ 강제.** 새 게이트는 `prepush_check.py` 에 호출을 넣었는지 그 자리에서 확인. `git push --no-verify` 를 썼으면 커밋에 남긴다.
`test_rule_coverage_manifest.py` 는 룰↔항목 커버리지를 변이시험으로 대조한다 — 룰 추가·개명·삭제 시 매니페스트를 같이 고친다.
**게이트 범위는 변경 범위에 맞춘다(owner 2026-09-12).** 번들 범위 diff 가 `jp/`·`J-ESR/`·docs·inbox·TODO·배포 스크립트뿐이면 한국 마스터 게이트(8분)를 돌리지 않고 `tests/test_deploy_assets.py` + `check_inbox_hygiene.py` 만 돌린다. 루트 마스터 JSON·`scripts/*.py`(배포 스크립트 제외)·루트 HTML 이 하나라도 바뀌면 전체 게이트.

## 6. K-ICS validation gate (필수)

다음 단계(JSON swap·템플릿·HTML 배포·push) 전에 `scripts/validate_kics_disclosure.py` 를 루트 `kics_disclosure.json` 에 실행. **RED=0** 이어야 하고, 예외는 `TODO.md` 에 문서화된 것(회사·분기·룰·사유)만. 예상 밖 RED 는 파싱 리뷰(MD 원문·파서 범위·행 매핑) 후 진행. 룰 `8_life` SKIP 은 차단 아님. 공식·허용오차는 `docs/agents/kics-json-validation-rules.md`.

## 7. 불변식 3개

1. **게이트가 검사하는 파일 = 사용자가 보는 파일.** 다르면 산수가 맞아도 소스가 틀린 통과가 된다.
2. **모든 `.py` 는 BOM 없는 UTF-8.** UTF-8 BOM 은 `ast.parse` 를 깨서 정적 검사에서 투명인간이 된다(`tests/test_deploy_assets.py` 강제).
3. **거대 게이트·빌더는 골든으로 고정돼 있다 — 고치면 반드시 돌려라.** 산출이 의도적으로 바뀌면 손으로 해시 고치지 말고 `--update` 재생성 + 커밋에 이유.

| 골든 테스트 | 고정 대상 | 언제 |
|---|---|---|
| `tests/test_pl_breakdown_golden.py` (`RUN_PL_GOLDEN=1`, ~95초) | `build_pl_breakdown.py` 산출 마스터 바이트 | PL 빌더/핸들러 수정 후 |
| `tests/test_post_transition_golden.py` (~4초) | `_extract_post_values` 적용후 셀 | `fill_post_transition_to_disclosure.py` 수정 후 |
| `tests/test_kics_rules_golden.py` (<1초) | 룰 엔진 findings 매트릭스 | `kics_json_rules.py` 수정 후 |
| `tests/test_master_tables_golden.py` (<1초) | `validate_master_tables` SUMMARY + exit code | 그 게이트 수정 후 |
| `tests/test_viz_ifrs17_panels_golden.py` (~1.5초) | `viz_build_ifrs17_panels.py` 4개 패널 JSON 해시 | 그 빌더 수정 후 |
| `tests/test_viz_csm_waterfall_golden.py` (~1.5초) | `viz_build_csm_waterfall.py` 산출 + 47사 status | 그 빌더 수정 후 |
| `tests/test_ifrs17_bs_golden.py` (**~8분**) | `build_ifrs17_bs.py` 산출 마스터(17BS 유일 마스터) | 그 빌더 수정 후 |
| `tests/test_dividend_golden.py` (<1초) | `build_dividend.py` 산출 마스터 | 그 빌더 수정 후 |
| `tests/test_deploy_assets.py` | keep-list·인라인금지·BOM·삭제경로 참조 + **이 표 자체의 동기화** | HTML fetch/삭제/인코딩 변경 후, 골든 신설·개명 시 |

> viz 골든 2종은 산출을 인플레이스로 덮어쓰는 빌더라 실행 전 백업·예외 시 복구. 이 표는 `test_deploy_assets.py::test_golden_table_docs_agree_with_tests` 가 검사한다 — 골든을 추가·개명하면 여기도 고쳐야 테스트가 통과한다.

## 8. 마스터 JSON·xlsx 취급

- 마스터 JSON 통째 read-modify-write 금지(동시 세션 수정을 조용히 지운다). 셀 단위 + guard. `build_root_masters.py main()` 통짜 실행 금지, `validate_master_tables.py` 는 반드시 `--no-build`.
- master xlsx 는 전체 재생성 금지 — 바뀐 시트만 `scripts/sync_master_xlsx_sheet.py` 로. openpyxl 로 열어 재저장하면 수식 캐시가 날아간다.
- `scripts/export_public_sheets.py` 는 커밋된 HEAD 를 읽는다: 마스터 커밋 → `public_exports/` 재생성 → 재커밋.

## 9. 스테이지 간 handoff = inbox

정본 `inbox/README.md`. 스테이지끼리 검증·재작업 요청은 `inbox/<stage>/` 에 md 를 떨군다(사람 복붙 금지). 에이전트는 호출될 때 첫 동작으로 자기 inbox 를 드레인. 루프 max 5회, 초과 → 사람 큐. `answered` 는 시키기 전에 매 라운드 오케스트레이터가 검증해 `resolved` 로 `inbox/_resolved/` 이동. 변경 작업은 오케스트레이터가 직접 하지 않고 담당 stage 에 발주(조사는 직접 OK).

## 10. 멀티에이전트

- 독립 작업은 **서브에이전트를 한 메시지에서 병렬 발사**. 병렬 축은 ① stage 내부 fan-out(회사×분기×도메인) ② item 별 파이프라인 중첩. "stage 별 병렬" 은 틀린 프레임(순차 파이프라인).
- 동시 ≤4, 서브-서브에이전트 금지, 각 에이전트에 이 파일 + 자기 stage 프롬프트·TODO 를 명시. 메인 세션은 오케스트레이션(조율·통합·게이트)만.
- 모델은 **티켓 유형으로** 고른다(정의 파일은 Sonnet 5 기본, validation 만 Opus 5): 대량·기계적 `bulk` 는 정의대로, 원인조사·핸들러 설계·릴레이 종합 같은 `investigate` 는 Agent 호출에 `model: opus` 덮어쓰기. 티켓 종결 노트에 모델·토큰·소요시간을 한 줄 남긴다(월 1회 같은 유형 Sonnet/Opus 비교).
- "돌고 있냐" 는 세션 `subagents/agent-<id>.jsonl` mtime + 약속한 산출 파일로 판정(`tasks/<id>.output` 은 placeholder). 에이전트는 중간 산출을 디스크에 저장하며 진행.
- 회사망: go.kr·KIPRIS 는 브라우저·WebFetch 금지(영구 행). 외부 443 은 시간대별로 막히니 발주 전 도달성 확인.

## 11. 배포

라이브 = `main`(GitHub Pages, `CNAME`). 작업 브랜치 push ≠ 라이브. 이 PC 는 `git push` 가 차단되어 업로드는 폰 Termux 번들(`scripts/android_push_and_deploy.sh`). 배포 후 `public_exports/manifest.json` 의 `build_id` 로 라이브 확인. 데이터를 HTML 에 인라인 금지(JSON fetch). 화면 음수는 전부 △.
