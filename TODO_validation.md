# Insurequant Validation TODO (Stage 3)

> Last updated: 2026-09-14 (UH-25 게이트 축 해소 — `JP_ESR_UNVERIFIED_VALUE` 신설: 값 검증 두 축이 동시에 침묵하는 상태를 YELLOW 로 세고 push 묶음이 막는다; 직전 UH-23 정식 해소 — 한정어 정본 §3 표 ↔ `ADJUSTED_QUALIFIERS` 양방향 대조 배선 + TODO 과장 정정; 직전 jp `JP_ESR_ADJUSTED_FIGURE` 배선 — 조정치 축, UH-21 해소 → PM-2026-09-13 `closed`; 직전 jp `JP_ESR_NOT_IN_SOURCE` 배선; 직전 push 범위 판정을 훅에 구현 — CLAUDE.md §5 가 문서로만 있던 규칙을 코드로; 직전 jp false-green 포스트모템·UH-18 등재; 직전 2026-09-02 MASTER_XLSX_* 축 신설 — 마스터 JSON ↔ 마스터 xlsx 13시트 전수 대조를 CHECK 8 로 배선) · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Changelog: docs/changelog_validation.md

Session start: read this file + `claude-agent-validation.md` + domain refs (`docs/domains/claude-agent-{kics,ifrs17}.md`). English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

**(2026-09-14, 9차) UH-25 배선 — `JP_ESR_UNVERIFIED_VALUE` 신설. "이 화면값은 **어떤 축으로든** 판정된 적이 있나" 를 묻는 3번째 축이고, UH-25 가 지적한 비대칭(조정치 축에만 라이브 이빨이 있고 skip 축에는 하나도 없다)을 **대칭으로** 채웠다.** 전제는 8차가 등재만 하고 룰을 안 만든 이유였던 "오탐 억제를 실측할 수 없다" 인데, 오늘 T&D 출처가 목록 페이지 → 統合報告書 PDF 로 바뀌면서 그 점유가 사라져 **발화 0 을 실측으로 증명할 수 있는 창**이 열렸다(UH-5·UH-9 선례의 선행조건 충족).

> - **재측정: 오케스트레이터 숫자 4/4 정확, 단 한 개는 낡았다.** `verdict {'found': 16}` · `adjusted {'abstain_no_prose': 8, 'unqualified': 8}` · `doc_kind {'pdf': 16}` · 값 검증 0축 행 **0사** — 전부 일치. 낡은 것은 **posted 수**: 8차가 적은 15사가 아니라 **16사**(第一ライフグループ 220% 가 posted 로 들어왔다). T&D 222% 는 지금 `found`+`abstain_no_prose`+`pdf` = **1축 검증**이라 새 룰이 안 문다. census ↔ 증거 집합이 정확히 일치(증거에만 있는 행 0 · posted 중 증거 없는 행 0).
> - **배선 후 실데이터 발화 0 재확인**: `[source-gate] … YELLOW 0건 · RED 0건` · `1차 축 판정 분포: found=16` · `값검증 축 census: 판정됨=16 무검증=0 (그중 면제=0)`. **전제가 유지돼서 배선했다** — 깨졌으면 배선 안 하고 보고하는 것이 지시였다.
> - **판정식은 논리곱(=0축)이 아니라 논리합이다.** (a) `verdict ∈ (skip_landing, skip_no_text)` 또는 (b) `adjusted_verdict == not_applicable`. 곱으로 걸면 수집기가 반쪽만 회귀한 상태(한 축만 죽은 행)가 빠져나간다 — 이 저장소가 반복해서 데인 "룰이 순회는 하는데 그 칸은 안 본다" 의 모양이다. 호출 위치도 **verdict 분기보다 앞**이라 회사·verdict 필터 없이 전 행을 돈다.
> - **오탐 억제의 선은 `abstain_no_prose` 를 (b) 에서 뺀 것이고, 그 선이 load-bearing 임을 실측했다.** 그건 PDF 를 실제로 읽고 「라벨동반 산문 조각 0개」 로 판정한 결과(표·차트 전용 문서)라 1차 축이 `found` 로 살아 있다. 변이 M11 — `ESR_ADJUSTED_NOT_JUDGED` 에 `abstain_no_prose` 를 넣고 **증거는 손대지 않은 채** 돌리면 정상 **8사**가 한꺼번에 거짓 발화한다(東京海上HD·MS&AD·SOMPO·T&D·ソニー生命·ライフネット·au損保·明治安田損保).
> - **severity 는 YELLOW, 이빨은 push 묶음.** 조정치 축(`test_live_esr_evidence_has_no_unexempted_adjusted_figure`)과 **같은 모양**으로 맞췄다 — 근거 셋: ① 빌더 RED 로 걸면 기존 `test_skip_verdicts_are_yellow_not_red` 와 정면 모순 ② UH-25 가 적은 구조적 긴장(T&D 의 비-PDF URL 은 만료호스트 회피로 고른 것이라 데이터 오류가 아니다) 에서 정상 재빌드가 막힌다 ③ 비대칭의 근거가 "skip 축에 라이브 대조가 없다" 였으니 그 자리를 채우는 것이 해소다. 기존 테스트와 **역할을 docstring 에 갈라 적었다**: 그쪽은 *빌더 exit code 가 안 바뀐다*(합성), 새 것은 *배포본 증거에 그런 행이 면제 없이 남지 않는다*(실데이터). 모순 아님.
> - **면제 경로는 열려 있고 owner 권한이다.** `JP_ESR_UNVERIFIED_VALUE` 를 `SOURCE_RULE_IDS`+`EXEMPTABLE_RULE_IDS` 와 레지스트리 `_README` 에 등재했다(`exceptions` 는 **0건 그대로**). 10/31 에 정당하게 비-PDF 밖에 없는 회사가 나오면 그 경로로 간다. 등재 전에 먼저 물을 것은 「판정 가능한 1차 문서(PDF·有報)로 바꿀 수 있는가」 라고 레지스트리에 적었다.
> - **UH-25 remedy ② 도 같이 닫았다**: 게이트 요약이 종전에는 조정치 축 분포만 찍고 **1차 축은 안 찍었다**. 이제 `1차 축(JP_ESR_NOT_IN_SOURCE) 판정 분포` + `값검증 축 census(판정됨/무검증/면제)` 를 대칭으로 인쇄한다 — 분포가 skip_* 로 쏠렸는데 RED 0 이면 깨끗한 게 아니라 안 본 것이다.
> - **케이스 16건 추가**(85 → **101 passed**, 새 파일 없이 기존 `tests/test_jp_source_gate.py` 에 얹었다 — 새 파일을 만들면 §0 이 `tests/` 를 전체 게이트로 판정한다).
> - **변이 10/10 발화 + 음성대조 2건**(전부 사본 트리 `uh25_sand/` 에서만. 진짜 증거·census md5 작업 전후 동일: `fe0021bc…` · `ba79154d…`). M1 `verdict→skip_landing` **필드 (a) 단독** · M2 `adjusted_verdict→not_applicable` **필드 (b) 단독** · M3 둘 다(실제 UH-25 모양) · M4 `skip_no_text` · M5 다른 회사(かんぽ) · M8 그 회사 면제 등재 → **조용해진다** · M9 다른 회사 면제 → **여전히 발화**(셀 단위) · M10 다른 룰 면제 → 여전히 발화 · M12 진짜 빌더 엔드투엔드 → **exit 0**(YELLOW 설계대로) + 두 축을 이름으로 적는 발화 + `skip_landing=1 · 무검증=1`.
> - **🔴 중복이 아님을 증명했다(M6).** M3 변이를 남긴 채 **새 라이브 테스트만 삭제**하면 나머지 **100건이 전부 통과**한다(`100 passed`, 실패 0). 즉 기존 85건 + 내 합성 15건 어느 것도 이 상태를 못 잡는다. 반대 방향(M7, 판정식을 `return []` 로 gut)에서는 라이브 테스트가 조용해지고 **합성 6건이 발화**한다 — 라이브는 데이터를, 합성은 판정식을 지킨다(둘 다 필요).
> - **🔴 훅이 실제로 막는지 그 자리에서 실증했다(UH-1 교훈).** 진짜 증거 파일을 T&D 행만 UH-25 모양으로 **일시 변이**(백업 후 trap 복원) → `python3 scripts/prepush_check.py` → `FAILED tests/test_jp_source_gate.py::test_live_esr_evidence_has_no_unexempted_unverified_value` · `1 failed, 257 passed, 2 skipped` · **`offline tests(jp 묶음)=FAIL → BLOCKED (fix or owner-escalate)`**. 복원 후 md5 `fe0021bc…` 동일. 깨끗한 상태에서는 `258 passed, 2 skipped → gate-clear`(축소 전 242 → 258). 새 테스트가 `REDUCED_TEST_BUNDLE`(L111)·전체 묶음(L513) 양쪽에 이미 있는 파일 안이라 매니페스트 수정은 불필요했다.
> - **잔여(이번 범위 밖, UH-25 에 명시)**: **화면 축**. 배포본 `jp/jesr_esr.json` 에서 0축 검증 행과 2축 검증 행의 키 집합 차이가 여전히 공집합이고 `jesr_app.js` L307 이 둘 다 같은 「根拠資料 ↗」 로 그린다 — 게이트는 이제 막지만 **사용자는 여전히 구분 못 한다**. designer·publishing 소관이라 `inbox/jp/20260914T0740Z__validation__JP_MULTI__uh25_screen_axis_residual.md` 로 발주. UH-22(조정치 축 severity 승격)도 10/31 재census 대기로 계속 열려 있다.
> - 검증: `pytest tests/test_jp_source_gate.py -q` **101 passed**(85→101) · 축소 묶음 **258 passed · 2 skipped** · `prepush_check.py --scope-only` = **`REDUCED (jp-scope)`**(변경 3개 전부 jp) · 전체 실행 **`gate-clear`** · inbox 활성 1(내가 방금 낸 것) · 위반 0 · 한국 축은 이 컨테이너에서 미검사(`data/disclosure` 없음).
> - 재현: `python3 -m pytest tests/test_jp_source_gate.py -q` → `python3 /tmp/…/scratchpad/probe_gate.py`(실데이터 게이트, 산출 안 씀) → `python3 /tmp/…/scratchpad/uh25_mutate.py`(사본 변이 12종) → `python3 scripts/prepush_check.py`.

**(2026-09-14, 8차) 第一ライフグループ posted 전환 경로를 **사본으로** 전증 — 6종 전건 반응 실측 + 새 사각 **UH-25** 등재(비-PDF 출처 = 값 검증 2축 동시 침묵).** 진짜 census·`jp/*.json` 은 한 바이트도 안 건드렸다(작업 전후 md5 5개 동일). UH-19 교훈("census 만 고치고 빌더를 안 돌리면 게이트가 한 번도 안 돈다")대로 **경로를 먼저 증명**하고 무엇이 막을지 미리 쟀다.

> - **오케스트레이터 서술 5개 중 4개 맞고 1개 틀렸다.** 6종 룰 id · 증거 2종 봉투(`source_url_health` `2026-09-13T14:30Z` scope=all rows=254 · `esr_in_source_health` `2026-09-13T16:54Z` scope=all rows=15) · census 보다 낡은 증거 = STALE RED · PDF 만 기계검증 — 전부 맞다. **틀린 것**: "비-PDF 는 `not_applicable`". `not_applicable` 은 **`adjusted_verdict`** 값이고, 비-PDF 의 **`verdict`** 는 `skip_landing` 이다. 빌더의 `verdict` 어휘(`ESR_VERDICT_*`)에는 `not_applicable` 이 **없어서** 거기 들어오면 오히려 "모르는 verdict → RED" 로 걸린다. 결론(두 축 다 침묵)은 같지만 **경로가 둘**이라 룰을 설계할 때 갈라 봐야 한다.
> - **사본 드라이런 11 시나리오, 6종 전건 발화 실증**(`/tmp/…/scratchpad/dryrun_driver.py`, 사본 트리에서만). S1 둘 다 미실행 → STALE×2 + INCOMPLETE×2 **exit 1** / S2 URL 수집기만 → STALE×1 + INCOMPLETE×1 **exit 1** / S3 둘 다 실행 → **exit 0 · RED 0** / S4 `release.tdnet.info` → EXPIRING_HOST RED / S5 `classification=dead` → URL_DEAD RED / S6 `verdict=not_found` → NOT_IN_SOURCE RED / S7 `adjusted_alt` → ADJUSTED_FIGURE **YELLOW · exit 0**(이빨은 push 묶음) / S9 `adjusted_*` 필드 누락 → INCOMPLETE RED / S10 `scope=partial` → STALE RED.
> - **🔴 새 사각 UH-25 — S8.** 비-PDF URL 로 posted 하면 `verdict=skip_landing`(인쇄만) + `adjusted_verdict=not_applicable`(기권) 이라 **`JP_ESR_NOT_IN_SOURCE`·`JP_ESR_ADJUSTED_FIGURE` 가 둘 다 침묵**하고 빌더는 **exit 0 · RED 0건**. 배포본에서 **구분이 안 된다** — 0축 검증 행과 2축 검증 행의 **키 집합 차이가 공집합**이고 `jesr_app.js` L307 은 둘 다 같은 「根拠資料 ↗」 로 그린다. 즉 "검증 못 함" 과 "검증 통과" 가 사용자에게 같은 모양이다.
> - **세고 나서 말한다(UH-5·UH-9 선례).** posted 15사 중 `skip_landing`·`not_applicable` = **1사**(0 아님). **T&D 222%** 이고, 그 증거행 evidence 는 「본문에 222 표기가 **안 보인다**」 인데도 게이트는 green — **이미 라이브인 false-green** 이다. 10/31 노출: not_yet 62행의 ir_url 60/62 가 비-PDF, disclosure_url 도 비-PDF 33 · pdf 5. 有報 스윕이 쓰는 EDINET 뷰어 URL 도 **.html**(`…WZEK0040.html?…&S100YC7A` = 第一ライフグループ 근거 docID) 이라 이번 라운드에 2건째가 될 수 있다.
> - **비대칭이 근거다.** 같은 YELLOW 인 조정치 축은 `test_live_esr_evidence_has_no_unexempted_adjusted_figure` 로 push 묶음에 이빨이 있는데, skip 축에는 라이브 대조가 **하나도 없다**(유일한 테스트가 *침묵을 단언한다*). 게이트 요약도 조정치 축만 분포를 찍고 1차 축(found/not_found/skip_*)은 **분포를 안 찍는다** — 「기권은 세지 않으면 사각이 된다」 를 한쪽에만 적용했다.
> - **룰은 안 만들었다.** 필드는 이미 있다(`doc_kind` pdf 14·other 1, `content_type` pdf 52·html 194) 라서 새 수집기 없이 셀 수 있지만, 지금 RED 로 걸면 **데이터 오류가 아닌 T&D 1건이 정상 배포를 막는다**(그 행이 비-PDF 인 이유가 만료호스트 회피라, 고칠 대상이 URL 인지 룰인지 미확정). `docs/postmortems/README.md` **UH-25 / P1** 로 등재만.
> - **덤으로 확인한 것 2개.** ① 2026-09-13 4차가 발주한 census ragged row(第一ライフグループ 16열 헤더에 18열)는 **이미 고쳐져 있다** — 79행 전수에 `None` 키·결측 셀 0. 즉 `JP_CENSUS_SHAPE` 는 이번 전환을 막지 않는다. ② `check_source_urls.py` 모듈 docstring 은 census 대상이 `ir_url/disclosure_url` 이라 적었지만 **코드는 `source_url` 도 읽는다**(`collect_targets` L89) — 문서가 낡은 것이고, 덕분에 "새 URL 을 넣었는데 증거 수집 대상이 아님" 인 교착은 **없다**.
> - 검증: 실트리 md5 5개 불변(census·증거 2종·마스터·배포본) · `git status` 에 내 변경 0 · `prepush_check.py` = **`REDUCED(jp-scope)` … `gate-clear`** · 축소 묶음 **242 passed · 2 skipped** · inbox 활성 1(내 것 아님) · 위반 0.
> - 재현: `python3 /tmp/…/scratchpad/dryrun_driver.py S0 S1 … S10` (사본 트리 `pristine/` 에서 매 시나리오 재구성).

**(2026-09-14, 7차) UH-23 정식 해소 — 한정어 정본(도메인 문서 §3) ↔ 기계본(`ADJUSTED_QUALIFIERS`) **양방향** 대조 배선. 겸해서 TODO 의 과장을 정정했다 — UH-23 은 어제 절반만 닫혀 있었다.** `TODO_jp.md`(28) ③ 은 "한정어 목록 정본을 도메인 문서 §3 에 등재(**UH-23 해소**)" 라고 적었지만, PM 이 요구한 정식 해소는 「§3 절 신설 **+** 코드↔문서 대조 테스트」 둘이고 테스트가 없었다(`tests/test_jp_source_gate.py` 의 코드↔문서 대조는 **ESR 라벨만** 봤다). CLAUDE.md §3 대로 재서 확인했다.

> - **③ 자체도 과장이었다(내 실측).** §3 은 관측 3종(`除いた場合`·`適正水準`·`ターゲットレンジ`)만 산문으로 적고 코드는 **10종**을 들고 있었다. 코드 10종 중 §3 에 문자열로라도 있던 것은 **4종**뿐이고, 그중 `調整後` 는 §3 이 「추측으로 넣지 말 것」 으로 **지목한** 어휘인데 코드가 실제로 들고 있었다 — 정본과 기계본이 **서로 반대를 말하고 있었다**. 즉 UH-23 은 "테스트만 없는" 상태가 아니라 **정본이 기계본과 어긋난** 상태였다.
> - **고친 방향은 "문서를 코드에 맞춘다" 가 아니다.** 10종 전부에 15사 관측수와 채택근거(이형 / PM seed)를 열로 달아 §3 표에 올렸다 — 관측 0인 7종이 **추측 어휘가 아니라 관측된 구문의 이형·공시 관행 표기**임을 문서가 스스로 말하게 했다. 맨 `を除く`·`レンジ`·`目安`·`参考` 같은 **넓은 형태는 여전히 금지**(각주 기호·목차와 충돌)라고 §3 에 남겼고, "늘리려면 §3 표를 먼저 고치고 15사에 다시 돌려 정상사 발화 0 을 확인" 을 정본에 못 박았다.
> - **양방향이어야 하는 이유는 실측이다.** 집합일치를 부분집합(코드⊆문서)으로 약화하면 "코드에서 `ターゲットレンジ` 삭제" 가 **그대로 빠져나간다**(음성대조 M7, `2 passed`). 코드가 넓어지는 쪽만 막으면 *정본이 잡는다고 적힌 것을 코드가 안 잡는* 반쪽이 무검사로 남는다 — `適正水準` 을 코드에서 빼면 かんぽ 220 이 빠져나간다(6차 실측).
> - **기존 테스트와 역할을 갈랐고, 중복이 아님을 변이로 증명했다.** `test_qualifier_list_is_not_empty_and_excludes_definition_markers` 는 4종을 **테스트에 하드코딩한 바닥선**(문서를 고쳐도 안 흔들린다), 새 `test_definition_markers_named_in_the_doc_stay_out_of_the_code_list` 는 **문서를 따라간다**(§3 표에 5번째 정의 표지가 서면 코드 검사가 자동으로 넓어진다). 음성대조 M8 — `規制` 를 §3 정의 표지 표에서 빼 한정어로 승격하면 **새 2건은 조용하고 바닥선만 발화**(`old 83건 rc=1`). 반대로 M4(5번째 정의 표지 `暫定値` 를 코드·표 양쪽에 일관 추가)는 **바닥선이 조용하고 새 것만 발화**. 둘 다 필요하다.
> - **변이 6/6 발화**(사본 트리 `mut/` 에서만 — J-ESR·docs/domains·tests 만 복사, 종료 후 원본 md5 복원 확인: 수집기 `255d643f…` · 도메인 문서 `7a98fe6e…` · 테스트 `678a361e…`): ① 코드에 가짜 한정어 `参考` 추가 ② §3 표에서 `ターゲットレンジ` 행 삭제 ③ 코드에서 `ターゲットレンジ` 삭제 ④ 정의 표지 `暫定値` 를 양쪽에 일관 추가 ⑤ §3 한정어 표 통째 삭제 ⑥ §3 정의 표지 표 통째 삭제. **6건 전부 기존 83건은 침묵** — 새 2건을 deselect 하면 `83 passed`. 즉 중복 테스트가 아니다(이게 "새 테스트를 죽이면 기존으로 못 잡는다" 의 증거다).
> - **🔴 훅이 실제로 부르는지 — 절반만 참이다(UH-1 교훈대로 그 자리에서 확인했다).** 새 테스트는 `tests/test_jp_source_gate.py` 안이고 그 파일은 `prepush_check.py` 의 `REDUCED_TEST_BUNDLE`(L111)과 전체 오프라인 묶음(L513)에 **둘 다** 있다 — 게이트를 돌리면 실제로 돈다(실측 240→**242 passed**). **그러나 이 리눅스 컨테이너에서는 git 훅 자체가 안 돈다**: `.githooks/pre-push` 가 **mode 100644**(실행권한 없음)라 git 이 조용히 건너뛰고(**UH-24**, 같은 날 다른 세션이 루트 `TODO.md` 에 등재), 설령 chmod 해도 훅이 `PY="C:/Users/sangwook.cho/venvs/…/python.exe"` 를 하드코딩해 리눅스에선 `[ ! -f "$PY" ] → exit 1` 로 **게이트를 한 줄도 안 돌리고 죽는다**. 그러니 이 라운드의 정확한 주장은 "**`prepush_check.py` 가 부른다**" 이지 "훅이 강제한다" 가 아니다. 훅 수정은 `.githooks/` = 전체 게이트 경로라 이 컨테이너에서 손대지 않았다(UH-24 에 귀속).
> - **정정한 문서**: `TODO_jp.md`(28) ③④ + "다음" 줄 · `docs/postmortems/README.md` UH-23 행 + PM-2026-09-13 색인행 잔여표기 · PM 본문 §5 표 + 5번 칸 + 종결문. jp 도메인 문서는 jp 레인 소유라 티켓으로 통지: `inbox/jp/20260914T0425Z__validation__JP_MULTI__qualifier_canon_registered.md`.
> - **잔여**: PM-2026-09-13 의 미배선은 **UH-22 하나**(severity 승격 판단 — 10/31 재census 에서 재측정). cross-stage 로 **UH-24**(훅이 리눅스에서 무력) 가 열려 있다.
> - 검증: `pytest tests/test_jp_source_gate.py -q` **85 passed**(83→85) · 축소 묶음 **242 passed · 2 skipped**(그 2건은 `test_push_gate_wiring.py` 의 기존 skip, 내 것 아님) · inbox 활성 0 · 위반 0 · `prepush_check.py` = **`REDUCED(jp-scope)` … `gate-clear`**(한국 마스터 축은 미검사 — 이 컨테이너엔 `data/disclosure` 가 없다).
> - 재현: `python3 -m pytest tests/test_jp_source_gate.py -q` → `python3 scripts/prepush_check.py --scope-only` → `python3 scripts/prepush_check.py`.

**(2026-09-13, 6차) jp `JP_ESR_ADJUSTED_FIGURE` 배선 — "있는 숫자 중 틀린 것을 골랐나" 축. UH-21 해소 → PM-2026-09-13 `closed`.** 직전 5차의 `JP_ESR_NOT_IN_SOURCE` 는 "그 문서에 그 숫자가 있나" 만 물어서 かんぽ 220% 를 원리상 못 잡았다(220 은 그 자료 p35 에 **실재**하는 「大量解約リスクを除いた場合」 조정치, 실측 d=1 → `found`). 이번에 판정식을 정의해 같은 수집기·같은 증거 봉투에 얹었다 — `check_esr_in_source.py::scan_adjusted`(판정식 정본) → `esr_in_source_health.json` rows 의 필드 6개 → `build_jesr_page_json.py::_adjusted_figure_check`. **새 증거 파일을 만들지 않아 신선도 검사(`_load_evidence_envelope`)를 그대로 재사용한다.**

> - **본 룰은 "대안값 조건" 이다(이번 라운드의 판단거리).** 판정식 = ① 화면값이 나오는 ESR 라벨동반 **산문 조각**(`。`·개행 분할)이 1개 이상(0개면 **기권**) ② 그 조각이 **전부** 한정어를 달았다 ③ **같은 문서에 한정어 없는 다른 ESR 값이 있다** → `adjusted_alt`. ②까지만이면 `adjusted_only`(보조).
> - **③ 을 본 룰로 고른 근거는 실측이다.** 한정어 목록 4변형 × 15사: 확정본 → ①② 단독 발화 1 · ①②③ 발화 1(둘 다 정상사 오탐 0) / `適正水準` 을 빼면 **사고를 놓친다**(p18 「ESR適正水準 150~220%」 가 한정어 없는 조각이 되어 220 이 빠져나간다) / definition marker 4종(`ベース`·`内部管理`·`規制`·`速報値`)을 넣은 오염판 → **①② 단독은 정상 3사(日本生命·住友·朝日)가 거짓 발화**, ③ 을 붙이면 전부 조용 / 빈 목록 → 0. 즉 정상 상태에선 둘이 같은 답이지만 **룰이 망가지는 현실적 경로(다음 사람이 목록을 넓힌다)에서 ③ 만 버틴다**. 그 경로가 가설이 아닌 이유: `適正水準` 은 かんぽ **정답값 181 의 조각에도** 붙어 있고(「適正水準の範囲内にある」), 朝日의 정답 헤드라인은 「ESR(グループ)(内部管理ベース)は258.9%」다.
> - **한정어 목록은 15사 실측으로 확정**(seed 를 그대로 쓰지 않았다). 라벨동반 조각 전체에서 실제 관측된 것은 `除いた場合`(2, かんぽ) · `適正水準`(4, かんぽ) · `ターゲットレンジ`(1, 富国)뿐이고 `を除く`·`レンジ`·`目安`·`調整後`·`参考` 는 **관측 0**. definition marker 4종은 **일부러 뺐다**(코드 주석에 이유까지).
> - **오탐억제**: 정상 14사 중 **7사가 라벨동반 산문 조각 0개**(표·차트 전용 문서) — 기권 조건 없이 걸면 거짓 YELLOW 7건. 기권은 SKIP 이 아니라 **따로 세는 분류**다(수집기 summary + 게이트 요약이 분포를 인쇄: `unqualified=7 adjusted_alt=0 adjusted_only=0 abstain_no_prose=7 not_applicable=1`).
> - **severity 는 YELLOW 인데 이빨은 push 묶음에 뒀다.** 한정어 목록이 휴리스틱이라 RED 는 오탐 1건이 정상 배포를 막는다(UH-5·UH-9 선례). 하지만 **"인쇄만 하는 YELLOW" 는 통제가 아니다** — 2026-09-12 에는 census notes 에 「特定条件を除いた場合の ESR は 220%」 라고 **적혀 있었는데도** 그 값이 나갔다. 그래서 `test_live_esr_evidence_has_no_unexempted_adjusted_figure` 가 **배포본 증거**(= 게이트가 읽는 파일, 불변식 1)에 면제 없는 발화가 남으면 FAIL 한다. 고치는 길은 값 수정 또는 owner 면제 등재뿐이다.
> - **축이 조용히 사라지는 경로도 막았다.** YELLOW 라 exit code 를 안 바꾸므로 유일한 소멸 경로는 "수집기를 옛 버전으로 돌려 필드가 빠지는 것" → **필드 부재는 RED**(`JP_SOURCE_EVIDENCE_INCOMPLETE`, 면제 불가), 모르는 `adjusted_verdict` 도 RED. 진짜 빌더를 돌려 exit 1 실증(`test_gate_adjusted_axis_missing_changes_exit_code`).
> - **사고 재현(엔드투엔드, 사본에서만)**: census 를 かんぽ 220 으로 되돌리고 수집기를 그 원문 바이트로 재실행 → `verdict=found (p35,d=1)`(NOT_IN_SOURCE 는 여전히 조용) · `adjusted_alt`, 대안 `181` → 빌더 **exit 0** + 메시지 「같은 문서에 **한정어 없는 대안값 181%(p35) 가 있다**」 → **push 묶음 exit 1**. 현재값 181 은 `unqualified` = 발화 안 함.
> - 회귀는 **새 파일 없이** 기존 jp 2종에 얹었다(63→**83** + 26). 이빨 변이 **10/10 발화**(사본에서만, 원본 md5 복원 확인): 한정어 목록 비우기 2 FAIL · 기권 조건 제거 1 · 대안값 조건 제거 1 · 게이트 배선 호출 제거 8 · 룰 no-op 9 · 필드 부재 통과 3 · 모르는 verdict 통과 1 · 발화를 기권으로 강등 4 · 면제가 절차 룰까지 덮게 1 · 배포본 증거에 발화 심기 2.
> - **PM 종결**: 5칸이 다 차 `PM-2026-09-13` 을 **`closed`** 로 바꾸고 README 색인·UH 표를 갱신했다. 잔여는 **UH-22**(severity 승격 판단 — 10/31 라운드 재측정, 승격 3조건을 문서에 못 박음 / P2) · **UH-23**(한정어 목록 정본이 코드에만 있다. 라벨은 `docs/domains/claude-agent-jp.md §3` 이 정본이고 테스트가 대조하는데 한정어는 그 장치가 없다 — 도메인 문서는 jp 레인 소유라 손대지 않았다 / P3).
> - 검증: 수집기 `found=14 · skip_landing=1`(종전 동일) · 빌더 **exit 0** · `RED 0건 · YELLOW 1건(T&D)` · `jp/jesr_esr.json`·`jesr_master.json` 이 `generated_at` 외 **전량 동일** · `prepush_check.py` = `REDUCED (jp-scope)` · **238 passed · 4 skipped** · `gate-clear`.
> - 재현: `python3 J-ESR/check_esr_in_source.py --all --out J-ESR/esr_in_source_health.json` → `python3 J-ESR/build_jesr_page_json.py` → `python3 -m pytest tests/test_jp_source_gate.py tests/test_jp_deploy_matches_census.py -q` → `python3 scripts/prepush_check.py`.


**(2026-09-13, 5차) jp `JP_ESR_NOT_IN_SOURCE` 배선 — "그 문서에 그 숫자가 있나" 축. PM-2026-09-13 의 마지막 미배선 축이었다.** 오프라인/온라인을 갈랐다: 수집기 `J-ESR/check_esr_in_source.py`(신규, 네트워크)가 posted 행의 `source_url` 문서를 열어 `J-ESR/esr_in_source_health.json` 에 박제하고, 빌더는 **박제만 읽는다**(`source_gate_check` → `_esr_in_source_check`). 증거 봉투는 `source_url_health.json` 과 동일해서 신선도 검사를 **같은 함수**(`_load_evidence_envelope`)가 잰다 — 증거가 낡으면 두 룰이 같이 낡는다(한 쌍).

> - **증거 키는 (url, esr_pct).** url 만으로 잡으면 값만 고치고 수집기를 안 돌린 상태가 옛 값의 `found` 를 그대로 물려받는다 — 그게 정확히 2026-09-12 의 사고 모양이다.
> - **분포 실측이 PM §4c-pre-실측 과 정확히 일치**: posted 15사 전수 `found=14 · not_found=0 · skip_landing=1(T&D) · skip_no_text=0`. 최소거리 0~72 로 전부 `text_window` 안. `ソニー生命` 은 파이썬 TLS 악수 실패라 curl 폴백(UA 는 `jesr_http.UA_BROWSER` 그대로 — 헤더 기본값은 한 군데에만).
> - **초안 규격을 되돌려 재봤다**: "같은 문장" 으로 걸면 `found=7/14` = **거짓 RED 7건**(PM 예고치와 정확히 같다). 확정 규격(±200자 / 같은 표 행)은 14/14·거짓 RED 0.
> - **사고 재현 — 잡히는 것과 안 잡히는 것을 실측으로 갈랐다.** ① 東京海上HD 238 → `JP_ESR_NOT_IN_SOURCE` RED(exit 1). 238 은 56페이지 **어디에도 없다**(문턱을 100,000자로 풀어도 not_found) — 즉 200자 문턱은 사고 탐지가 아니라 **거짓 RED 억제**가 전부인 파라미터다. ② MS&AD 를 사고 당시 URL(합병 보도자료)로 되돌려도 RED — 그 URL 은 지금도 `ok_requires_headers`(살아 있음)라 **먼저 배선한 4종으로는 못 잡는다**. ③ **かんぽ 220 은 못 잡는다** — 그 자료 p35 에 「大量解約リスクを除いた場合のESRは220%」로 실재해 `found` 다. 값만 고치고 수집기를 안 돌린 상태에서는 `JP_SOURCE_EVIDENCE_INCOMPLETE` 로 걸리지만, 수집기까지 돌리면 통과한다.
> - **PM 의 주장이 틀렸음을 기록에 남겼다.** PM §5 는 "이 축이 東京海上HD·かんぽ 2건을 잡는다" 고 적고 있었다. 실제로 잡는 2건은 **東京海上HD·MS&AD** 이고 かんぽ 는 원리상 못 잡는다. PM 상태는 **`open` 유지**하되 사유를 3번 칸(배선)에서 **2번 칸(룰 정의)**으로 옮겼다 — かんぽ형을 잡을 룰이 정의된 적이 없다(**UH-21 신규 / P1**).
> - **UH-21 의 오탐억제까지 실측해 뒀다**(배선은 안 함, UH-5·UH-9 선례): 한정어(`を除いた場合`·`調整後`·`適正水準`·`ターゲットレンジ`) 없는 라벨동반 등장이 0개면 조정치 후보 → かんぽ 220 발화 / 181 미발화로 둘을 가른다. **단 정상 14사 중 7사는 라벨동반 산문 조각이 0개**(표·차트 전용 문서)라 "라벨동반 조각 ≥ 1 일 때만 판정" 조건이 필수 — 붙이면 표본 발화 1건·오탐 0.
> - 오탐억제: RED 로 읽는 verdict 는 `not_found` 하나. `skip_landing`(1사)·`skip_no_text`(**0사**, 방어용)는 YELLOW 인쇄만. `skip_no_text` 문턱은 **공백 제외 0자** — "몇 자 안 나오니 SKIP" 으로 올리면 그게 SKIP-on-missing 이다. 문서를 못 받으면 판정이 아니라 `fetch_failed` 로 적고 게이트가 절차 룰(면제 불가)로 잡는다.
> - **라벨 정본은 `docs/domains/claude-agent-jp.md §3`**, 코드는 기계본이고 테스트가 한 줄씩 대조한다. 구기준 단독 `ソルベンシー・マージン比率` 는 ESR 이 아니라 같은 페이지에 신기준 표지(`所要資本`·`適格資本`·`UFR`)가 있을 때만 라벨로 친다 — 이 조건이 없으면 au損保·明治安田損保의 5개년 구기준 표가 라벨로 읽혀 **거짓 통과**가 난다.
> - **fixture 가 게이트를 덮고 있던 것도 같이 고쳤다.** `tests/test_jp_deploy_matches_census.py` 의 10/31 flip 시뮬레이션(1·30·62사)은 census 만 뒤집고 선행 단계를 안 돌린 라운드를 흉내 내고 있어 새 룰에 전부 걸렸다 — **거짓 RED 가 아니라 게이트가 제 일을 한 것**(아무도 원문을 확인한 적 없는 posted 행). 게이트를 안 풀고 fixture 를 완성(`_synthetic_esr_evidence`)한 뒤, fixture 가 게이트를 덮지 않았음을 음성대조군(`test_flipped_census_without_fresh_esr_evidence_is_red`)으로 못 박았다.
> - 회귀는 **새 파일 없이** 기존 jp 2종에 얹었다(63 + 26). 이빨 변이 **8/8 발화**(사본에서만, 원본 md5 복원 확인): 배선 호출 제거 9 FAIL · 룰 no-op 9 · `not_found` YELLOW 강등 1 · 모르는 verdict 통과 1 · 증거 키 느슨화 2 · YELLOW 에 not_found 끼워넣기 3 · 봉투 신선도 무력화 6 · `fetch_failed` 통과 1. 수집기 쪽: 라벨 목록을 비우면 정상 문서가 무너져 거짓 RED — 그래서 목록 비어있지 않음을 테스트가 강제.
> - 검증: 빌더 **exit 0** · `RED 0건 · YELLOW 1건(T&D)` · `jp/jesr_esr.json`·`jesr_master.json` 이 `generated_at` 외 **전량 동일** · `prepush_check.py` = `REDUCED (jp-scope)` · **218 passed · 4 skipped** · `gate-clear`.
> - 재현: `python3 J-ESR/check_esr_in_source.py --all --out J-ESR/esr_in_source_health.json` → `python3 J-ESR/build_jesr_page_json.py` → `python3 -m pytest tests/test_jp_source_gate.py tests/test_jp_deploy_matches_census.py tests/test_deploy_assets.py -q`.

## 🔴 Open — P1

### V19 — 사고 포스트모템 관행 도입 + 기존 4건 소급 (owner `20260721T0233Z`, 2026-07-21)
"포스트모템이 게이트 룰로 종결되지 않으면 같은 부류가 재발한다" → 5칸(무엇이 통과/어떤 룰이면 잡았나/
지금 배선됐나/exception 근거·등재위치/미배선 잔여+후속티켓) 미충족 시 close 불가인 관행 신설.
- [x] **구현형태 = 로컬 스킬** (`.claude/skills/incident-postmortem/`). 외부 스킬 미채택 — 5칸이 이
  저장소의 게이트 파일·registry 변수명·display-scope를 직접 지목해야 강제력이 생기는데 범용 스킬은 불가.
  기존 로컬스킬(`kics-parser`·`ifrs17-parser`) 패턴 + 금융데이터.
- [x] 정본 `docs/postmortems/README.md` + `_TEMPLATE.md`, 스테이지 프롬프트 §5.1에서 링크.
- [x] **소급 4건 기록**: PM-2026-06-16(두 달 글리치, closed) · PM-2026-07-07(적용후 사각, **open**) ·
  PM-2026-07-08(V17 가짜복사, **open**) · PM-2026-07-15(부모 census, closed).
- [x] **소급의 실질 산출물 = 미배선(UH) 적발 → P1 2건 즉시 배선(owner 승인 2026-07-21)**:
  - [x] **UH-1 해소**: 적용후 검증 7종(`_transition_ratio_after_capture`/`_transition_mmult_after`/
    `_transition_identities_after`/`_parent_present_child_incomplete_after`/`_diversification_negative`/
    `_item12_equals_item1`/`_ratio_series_spikes`)을 `validate_data_contract.py` `check_census`
    **1b(iv)** 로 lift(display 7분기 scope). 6종 RED + spikes만 YELLOW(휴리스틱 단독차단 금지).
    **주입 테스트 검증**: scope를 2023.1~3Q 임시확장 시 baseline RED 0 → lifted RED 4건 방출 =
    함수→`_emit`→`res.add` 경로 작동. 배선 후 실 push 게이트 **RED=0 유지**(현 findings 전부 non-display).
  - [x] **UH-2 해소**: push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·
    `triage_anomaly_candidates.py`) **git 등재**. gitignore가 아니라 단순 미추가였고 나머지 의존성
    (`validate_kics_disclosure.py`·`validate_master_tables.py`·`kics_json_rules.py`)은 이미 tracked.
  - [x] **도메인 경계 명문화(owner)**: 경과조치=K-ICS 전용(적용전/후 이중공시). **IFRS17엔 대응 개념
    없음**(전환방법=도입시점 측정방법, 이중컬럼 아님) → 복사할 짝 자체가 없으므로 `TRANSITION_AFTER_*`
    IFRS17 유사룰 금지. 상위 패턴("presence만 검사→세탁")만 도메인 무관(IFRS17은 기존 plausibility/
    impossible-0가 담당). postmortems README·SKILL에 기록.
  - [x] **UH-4 해소 (2026-07-21)**: `scripts/_data_contract_selftest.py` 신설 — `Env(inject=)` 합성
    mutation suite **14/14 PASS**. 기존 spec §5 회귀 + **1b(iv) lift 5종(F1~F5) 회귀 보호**.
    **이빨 검증**: `_item12_equals_item1`·`_post_transition_parent_census`를 monkeypatch로 죽이면
    해당 케이스 미검출→FAIL 확인. 이후 신규 룰은 여기 케이스 추가 필수.
  - [x] **UH-3 부분강화 (2026-07-21)**: sidecar 부재가 `notes`(비집계)로 조용히 통과하던 것을 집계되는
    **YELLOW `MISSING_PROVENANCE_SIDECAR`**로 승격. **RED 전환은 발행 후** — 지금 RED면 미발행 마스터
    전부 red-out으로 push 영구차단. **진행: sidecar YELLOW 4→1** — publishing(`faa34cd`)이
    forward_capital·tier1·tier2 발행 → 3종 Phase-2 strict 전환. **sensitivity_heatmap만 잔여**
    (parser(ifrs17) `20260721T0530Z__…sensitivity_heatmap_provenance` 발주 대기). 4종 전부 발행 후
    no-sidecar=RED 보편룰 활성화.
  - [x] **UH-5 종결 (owner 승인 2026-07-21, premise-refined)**: 선행조건이던 FSS 2023-03-20 붙임-1
    (`trend20230320_3.pdf` p6, 회사별 경과조치 종류)을 좌표추출 전수 복원(총계 검증 4/19/12/8 일치)
    → `_TRANSITION_KIND` registry(`scripts/validate_kics_disclosure.py`) 등재. **전제 falsify**:
    "TAC형(가용자본만)" 회사 = **0사**(가용자본 신청 4사 전부 요구자본 보험리스크도 신청, elective
    18사 전원 요구자본 경과조치사). **실측 78 "부모후=전" 셀** = A(subrisk후≠전·부모후=전 모순) **0**
    [기존 `_transition_mmult_after`가 이미 강제] + C(item14후 다름·부모후=전) 52 **전부 item19(시장위험)**
    [주식/금리 미신청사 정당 + 신청 3사도 조건부 미발동 가능·내부정합] + D(subrisk후 부재) 26 [census
    소관]. **진짜 미검출 0** → 부모 COPY 룰은 item17=mmult 중복·item19=오탐 52 → **신설 불요.**
    owner Socratic 지적("subrisk 다르면 상위도 달라야")이 결론 핵심 — 참이며 이미 mmult가 강제(A=0).
    postmortem README 3차 종결 기록.

### V18 — 적용후 요구자본 **부모** census blind spot 정정 (owner `20260715T0801Z`, 2026-07-15)
07-12 V17 census(`_parent_present_child_incomplete_after`)는 **부모후가 present일 때** 자식후 결측만 봄 →
**부모(15~21) 자체가 통째 결측이면 census/identity/mmult 전부 skip = false-green.** 2026.1Q 5적용사
(한화생명·교보·하나·롯데손해·농협) 요구자본 부모후 결측인 채 push 게이트 통과사고.
- [x] **게이트 신설 `_post_transition_parent_census`** (scripts/validate_kics_disclosure.py): 적용후 공시
  회사의 부모 15~21(코어)·22/23(조정) 값_적용후 **continuity break**(직전분기 present인데 당분기 결측 +
  이후재출현=SANDWICHED/최신=TRAILING) = RED. onset·항구적중단 flag 안 함(오탐억제). 22/23 단독=review(비차단).
  **적용사 판정=continuity 자체**(18사 하드코딩 아님) → 공통경과조치사 한화생명(KR0068)·삼성생명(KR0069)도
  포착(기존 18사룰 사각). 면제 registry `_POST_PARENT_NOT_DISCLOSED`=비어있음(owner "오면제 금지").
- [x] **양쪽 배선**: K-ICS 게이트(전분기 exit2) + **push 게이트 `validate_data_contract.py check_census`
  (display 분기만 차단)** ← "push 게이트가 통과"의 정정 지점. 두 스크립트 compile OK, 기존검사 무회귀.
- [x] **2026.1Q 라이브 해소 확인**: 병행 parser 세션이 5사 15~23 값_적용후 UPSERT(mtime 17:32) →
  2026.1Q census RED=0 + mmult/항등식/분산효과후 0 통과(fill 정합). **게이트가 갭→RED, fill→통과 검증.**
- [x] **parser 발주 `20260715T0835Z` 처리+적대검증 완료 (2026-07-16, resolved)**: push 게이트 census
  RED **47→4**. parser fill(삼성생명 2025.1Q·동양생명 4분기·한화생명 2025.2Q/3Q·흥국생명 17~21) 검증:
  - **미러fill(후=전) 정당성 PASS** — 삼성/동양/한화는 공통경과조치사(요구자본 후=전, 가용자본 item1만
    2025.2Q Δ실효과). V17 가짜복사 아님. 무회귀(mmult/항등식/ratio COPY/분산효과 전부 0).
- [🔴→👤] **잔여 push-block 2건 = owner escalate (raw 도출불가, `_POST_PARENT_NOT_DISCLOSED` 결정 필요)**:
  - **흥국생명(KR0071) 2024.4Q [15,16,22]**: image PDF + TIR+TER 다중경과조치 R4 재현불가(역산 item15
    14,747 vs 헤드라인 16,987, Δ2,240 비반올림). parser 비전판독 17~21은 채움, 15/16/22 결합불명.
  - **하나생명(KR0097) 2024.4Q [16]**: 비표준 공시(감사보고서 재무상태표, 이미 `_AFTER_SUBRISK_NOT_DISCLOSED`).
    item16후 산술파생 가능(=1369.09)이나 입력 item17후=1757.32가 raw page(2001.90) 불일치(partial-mmult
    아티팩트 의심) → 파생값 불신. owner 택일: item16 파생채움 vs 부모후 exemption.
  - **owner 결정 대기** — 둘 다 `_POST_PARENT_NOT_DISCLOSED`(scripts/validate_kics_disclosure.py) 등재
    또는 parser 재추출 지시. validation 자체 waiver 안 함.
- non-display 비차단 워크리스트(push 무관): 코리안리 KR1000 3분기·악사 2024.3Q·처브 2024.3Q·IBK연금
  2023.2Q(다중경과 결합불가 기지)·하나손/하나생 2023.2Q. git-purge raw, 저우선.
- 완료기준: 게이트 `post_transition_parent_census.red` display분 = 0 (현 4, owner 2셀 처리 시 0).
- [x] **건2 `8_post` dynamic tol (publishing `20260712T0219Z`)**: 이미 코드반영(07-12) 확인 —
  KR1098 2023.4Q 8_post=YELLOW(diff -92.82 tol내), `7_post` 룰 부재(누락 없음). resolved.

### V17 — 🚨 경과조치 "적용후" 전수 재추출 (owner 전수건 21/22 미처리, 2026-07-05 재발주)
owner `20260703T1138Z`(경과조치 적용후 컬럼 구조적 유실, 22 적용사) = **여전히 open, IBK연금 1개만 처리.** 이번 라운드 최대 미완건. validation 라이브 실측 후 최우선 재발주.
- [🔴] **parser "복사버그 정정" = 가짜수정 적발·반려 `20260705T2150Z`**: 파서가 커밋 5건(31bcead 등)으로 처리 주장했으나 검증 결과 **적용후 = round(적용전) 복사**(exact-identical만 피한 위장). item27 22적용사 285셀 중 **164 가짜/결측**(복사139+결측19+역전6), 진짜 후>전 121뿐(정상마진 50~190%p). → 진짜 raw 재추출 강력 반려.
- [x] **게이트 하드룰 신설 `_transition_ratio_after_capture`** (owner #6): 적용사(owner 22 seed ∪ 동적) item27 적용후 ≤ 적용전+1%p(복사/반올림) OR 결측 OR 역전 = **RED, exit 2 차단**. IBK연금만 0=정상재추출 통과(오탐0). self-test 7/7. 재검툴 `scratchpad/verify_item27.py`·`adversarial.py`.
- [🔴] **2차 적대적 검증 → 파서 회피 재적발 `20260706T0434Z`**: 파서 재수정(168→112) 후 적대검증 = 두 회피. **(A) "진짜동일 재확인" 5사(한화생명·코리안리·신한라이프·KB라이프·동양) 거짓** — 동양 2025.2Q 후>전 실재(172→177)로 반증, 나머지 유실. 게이트 seed로 63셀 RED 유지=재분류 거부. **(B) item27만 패치·금액(item1/14)후 미수정 정합붕괴 9건**(한화손해 item27후283≠도출190). → **게이트 AMT_MISMATCH 검사 추가**(item27후≠item1후/item14후×100 >2%p=RED). 현 **121 RED**(COPY50·MISSING19·LOWER43·AMT_MISMATCH9). iter3, 다음 회피 owner escalate.
- [x] **선택 경과조치 적용사 정본 확정(2026-07-06) = 18사**: owner가 **FSS 2023-03-20 보도자료 붙임-1**(`trend20230320_3.pdf` p6, 원수사별 신청현황) 제공 → 22-seed·그간 추정 전부 폐기. **생보 12**(ABL·흥국생명·케이디비·교보생명·아이엠라이프[=구DGB]·DB생명·푸본현대·하나생명·처브·교보라플·IBK·농협생명) **+ 손보 6**(AXA·한화손보·롯데손보·예별손보[=구MG]·흥국화재·NH손해). SCOR재보험=데이터부재. 나머지=공통(TFI) 후=전 정상. 코리안리·메리츠·한화생명·신한라이프=미적용 확정(오탐 해소).
- [x] **게이트 item27+item28 이중검사 + AMT_MISMATCH**: 18사 하드코딩, 두 비율 후≤전+1%p OR 결측 OR 항등식붕괴=RED exit2. 현 **139셀**(item27 68·item28 71; 케이디비·하나생명 최다=전량유실). self-test 7/7. 정본 발주 `20260706T0502Z`(2150Z·0434Z supersede).
- ⚠️ **publish = 보류 확정**: 적용후=화면 표시값. 18사 item27·28 적용후 진짜 재추출(item1·2·14 정합) + 게이트 139→0 전엔 불가.
- [x] **(2026-07-12 c) 전수 헤드라인 대조 + 파서 IBK fix 반려**: 18적용사×전분기 raw '경과조치 후' vs item27후(anchor 오탐0) → 110정합·**예별손해 KR0004 2023.1Q/2Q/3Q 불일치**(item27후=②표단독 74.67 vs 헤드라인 82.56, IBK동형 혼합)·119 자동파싱불가. **파서 IBK fix(0430Z) 반려**: item1후를 TAC단독 8241.63으로=**공통TFI 누락**(정답 9164.38=원래값, item14후 5179.08). 발주 `20260712T0700Z`(IBK반려+예별3+per-company 재조정). 케이디비 2025.4Q=내 오탐(데이터 205.7 정상).
- [x] **(2026-07-12 b) 파서 census-fill 적대검증 + 분산효과 부호 sanity**: parser 322→2 fill(a797681) 독립검증 = **견고**(item18=0이월·carry·mmult·한화손해 item19후=전 raw확인·롯데/교보 2026.1Q exemption raw정당). **단 적대스윕이 파서무관 기존오류 1건 적발**: IBK연금 2023.2Q 적용후가 ②표(시장불변)·③표(시장감소) 혼합→분산효과 -246.66(음수)+item27후 135.19≠헤드라인 176.95. **`_diversification_negative` 신설**(전·후 전체회사 item16<0/Σ(17~21)<15, RED blocking). parser 발주 `20260712T0430Z`. 현 게이트 분산효과음수 1(IBK) 차단.
- [x] **(2026-07-12) 적용후 요구자본 census 신설 = blind spot 정정**: owner가 아이엠라이프 2025.4Q 적용후 신용·분산효과 결측 지적 → 적용후 게이트가 mmult(item17/19 leaf)만 보고 **요구자본 구성(15→16~21) census 부재** 확인(항등식 R6은 결측셀 skip → 양쪽 샘). **`_parent_present_child_incomplete_after` 신설**(적용전 census 미러, 부모맵 15/17/19, RED blocking, exit-code 배선). **적발 322 항목셀(149 부모·분기)**: DERIVE 96(분산효과=Σ(17~21후)−15후)·CARRY 206(신용/운영/시장하위 후=전)·EXTRACT 20(raw재추출 14 회사·분기). 분류 `data/_derived/after_census_gaps.json`. parser 발주 `20260712T0230Z__…__after_requirement_census_322cells.md`. **현 게이트 census 149 RED 정상차단, parser fill 후 0 확인→재publish.** (owner가 앞서 현버전 라이브 push함 — 이 부분충전은 요구자본 detail, headline 지급여력비율후는 정상.)

### V16 — parser IFRS17 재빌드 검증 + IBK연금 무재보험 false-positive 해소 (2026-07-05, owner "cell 등록")
parser IFRS17 레인 재빌드(viz+마스터) 후 게이트 전수 검증. 코어 무손상 확인 + push RED 오탐 1종 해소.
- [x] **코어 정합성 검증**: closing 324P/0F · crosscheck 0F · cont 0 · dup 0 유지. tier2 data-contract RED **4→0**(소진율/분모 이슈 해소).
- [x] **IBK연금 재보험손익=0 ×4 = 오탐 확정**: 순수 연금사 무재보험(재보험 5 leg 전부 0 + 원수분해 정확히 닫힘). owner "cell 등록" → `user_pl_confirmed_cells.json` 4셀 + `validate_data_contract._pl_impossible_zero_leg` registry 존중 배선 + 마스터게이트 `IMPOSSIBLE_ZERO_EXEMPT`/`ZLEG_LEGIT` 면제. **prepush RED=1, 마스터 impossible0 0/zero_legs 3**.
- [x] **KR0083 2025.2Q 19_market 해소 (2026-07-05 b)**: downloader 오슬롯 PDF 교체(KR0075 BNP가 덮던 것) → parser 재추출(subs 29-46 복원, 19_market reconcile ✓). **prepush RED 1→0 = GATE-CLEAR**, K-ICS RED 9→8(전부 documented: KR0079 8_life SKIP + KR0087 동양 2023.2Q 이미지전용).
- [x] **parser 0745Z 처리 완료(2026-07-05 c)**: PARTIAL 14→3·FULL_ABSENT 14→2. 시계열 검증으로 잔여 판정 — 진짜갭 2건(교보 item35·BNP item37) 재발주 `0805Z`, 카카오 micro-0 수용, 신한이지 LTC는 floor 1.0→5.0 자체정리, KR0104·KR1010 legit-absent 수용.
- [x] **전건 해소 (2026-07-05 d): PARTIAL 14→0.** 교보 item35 백필·BNP item37/38 genuinely-0 적재(파서 MD근거 "변액주식 139억 감소"=내 통계추론 오판 인정)·카카오 item40 0.0 적재·신한이지 floor 자체정리. `0805Z` resolved. 잔여 = FULL_ABSENT 2(KR0104·KR1010 legit-absent 비차단) + census-missing 3(documented).
- [→] **follow-up: prepush에 `_parent_present_child_incomplete` 배선** — 지금은 PARTIAL 0이라 무영향이나, 향후 push 권위 게이트가 이 축을 정직하게 강제하도록 배선 권장.
- 참고: `_data_contract_selftest.py` 부재(pre-existing purge) — 게이트 정상, 회귀는 라이브 실측 대체. 메모리 [[owner-confirmed-registry]].

### V15 — 게이트 사각 2종 신규룰 (parser blind_spot 0703): 부모-자식 census + 지급여력비율 스파이크
owner 워크스루가 게이트 RED=0 통과분에서 잡은 2부류를 parser가 blind_spot으로 이관 → 룰 강화(데이터는 parser 수정 완료). 둘 다 `scripts/validate_kics_disclosure.py` 구현, self-test 7/7.
- [x] **`_parent_present_child_incomplete` (RED)**: 부모(item17/19)>0인데 회사별 self-census상 '평소 유의미 보고' 자식(29-35/36-40) 결측=행누락. 기대=과반present&중앙값≥1억(회사유형 아님 — 손보 장수리스크 실보고사 DB손해/코리안리/삼성화재 검출유지; 구조적0 LTC 제외). **PARTIAL만 RED(14)**, FULL_ABSENT even-Q(16, 2023.2Q 도입초 클러스터)는 원천확인 review 비차단. 역방향(`_parent_zero_child_nonzero`는 부모0·자식≠0만) 사각 닫음.
- [x] **`_ratio_series_spikes` (YELLOW)**: item27 인접 2분기 양방 이탈 단일분기=소스오염(부호역전 자체는 자본잠식사 정상이라 flag 안 함). 라이브 0, 옛 KR0083 25.2Q +318 주입 발화 확인. item27 중복행 dedup.
- [→] **parser 백필 발주**: PARTIAL 14 RED(KR0050 34·35 등) + FULL_ABSENT 16 review → `inbox/parser/20260704T0745Z…parent_child_census_gaps`. 재파싱 후 게이트 재확인.
- 부수발견(동봉): item27 중복행(삼성생명·메트라이프 이중정밀도), 세션중 kics_disclosure.json 재작성(parser 활성). blind_spot 0703 + owner 1529Z → `_resolved/`. 메모리 [[coverage-census-mandatory]]·[[validation-blind-spots]].

### V10 — KICS gate coverage census + 19_market SKIP blind spot (2026-06-12 owner 적발)
Root cause: gate didn't census "cells that should exist" + treated SKIP as pass. RED=292 after fix.
- [x] **19_market 과잉 RED 수정** (2026-06-13c, source-grounded cadence): 내 06-12 RED 승격이 cadence 미처리로 홀수 간이공시를 과잉flag. `_scan_breakdown_presence()`(disclosure MD 직접확인) + 짝수=항상RED·홀수=MD표유무로 판정. **RED 148→21**(EVEN 18 + 삼성생명 odd 3 = 진짜갭), cadence-SKIP 127(전부 홀수 간이공시). raw 확증(삼성화재/현대 홀수 MD에 세부표 부재).
- [→] **parser 재추출 (19_market 진짜갭 21건만)**: 짝수 full-form 결측 18(KB손해2024.4Q/2025.2Q·한화생명2023.4Q/2024.2Q·흥국생명/흥국화재2024.4Q·DB생명2025.2Q·DB손해2024.4Q·NH2025.4Q·신한이지3·처브3·AIA2025.4Q·카카오2025.4Q) + 삼성생명 odd 3(2023.3Q/2024.1Q/2024.3Q, MD에 표 있음). gold: 하나손해·삼성생명 2025.4Q(이미 GREEN). 148→21로 정정 inbox 발송.
- [→] **2026.1Q 항목 절단 (parser)**: 30사 적재됐으나 전 회사 항목 1–28까지만, 29–46 전무 → backfill.
- [→] **census 미싱셀 28건 (parser)**: 미래에셋(7분기)·코리안리(6분기)·동양·하나생명 등 MD는 parsed인데 JSON 추출 누락.
- [x] **`36_irr` SKIP맹점 폐쇄** (2026-06-13): cadence-aware RED 승격 — item36 공시·41–46 결측이 **짝수분기(2Q/4Q)면 RED**(시나리오표는 2Q/4Q 서식에만 존재, 실증: 41–46 전 분기 짝수에만 적재), **홀수분기는 SKIP**(원천부재 정당). `IRR_SCENARIO_EXEMPT` 면제셋(빈값). 결과: RED 23(전부 짝수, 홀수 false 0). 19_market 동형. → parser 41–46 재추출(아래 23건, market_subrisk inbox 후속).
- [x] **`report_latest.json` fresh-write** (2026-06-13): 게이트가 매실행 `artifacts/kics_validation/report_latest.json` 덮어쓰게 함 → stale glob 함정 제거(소비자 코드 0, orphan 5/25본이 문제였음).
- inbox: `20260611T2200Z__validation__MULTI_ALL__kics_market_subrisk_systemic_underparse.md`. 메모리: `coverage-census-mandatory`.

### V12 — CSM 민감도 전수 재추출(25.4Q 경영공시 기준) + direction sanity (2026-06-15, parser 대기)
owner: IFRS17.html 흥국생명 CSM 민감도 이상 지적. 진단 = 현 소스가 FY2024 DART 사업보고서(1년 stale·비전수), parser 추출 자체는 정확.
- [→] **parser(ifrs17) 전수 재추출 발주**: `sensitivity_heatmap.json`을 25.4Q 경영공시(`data/disclosure/FY2025_Q4`) 기준으로. inbox `20260615T0415Z__validation__MULTI_2025.4Q__csm_sensitivity_refill_disclosure_basis`. risk 전수(사망/해지/사업비/장해질병 정액·실손/…), 당기말만, csm_delta=CSM·pl_impact=손익효과, 억원 정규화, unavailable 정직표기. 미다운로드면 downloader bounce.
- [x] **SENSITIVITY_DIRECTION_SANITY 룰 신설**(`validate_master_tables.py` 5b): sign(csm_delta)≠sign(pl_impact) YELLOW. fill 후 재검증 시 sign-opposition 전수 triage(real vs 파싱오류).
- 참고: 흥국 해지율 역행=source-faithful(건강보험 견인), 장해질병 누락=FY2024 사업보고서 부재 → 경영공시로 해결. recency는 사업보고서≈경영공시(둘다 2025.12.31), 전수·granular가 경영공시 우위.

### V13 — 부모-자식 정합 룰 + INTERNAL_MODEL_36IRR 등록 + 카카오 cadence 정정 (2026-06-16, owner 라이브 QA 3차)
owner SGI 게이트 사각 + parser INTERNAL_MODEL 승인 inbox 드레인.
- [x] **`_parent_zero_child_nonzero` 룰 신설**(`validate_kics_disclosure.py`): 부모 위험액 present&≈0인데 하위 비0 = 구조상 불가능 RED(게이트 차단). item17→29-35, item19→36-40 명시매핑. 전수 3셀: 서울보증 2025.4Q(item35=5212)·2023.4Q(5264)·카카오 2023.3Q(4.72) 전부 대재해 오정렬.
- [x] **parser 발주(3셀 재파싱) → ✅ RESOLVED (2026-06-20 게이트 재확인)**: `Parent-zero / nonzero-child: 0` 실측. parser round3 K3가 서울보증/카카오 orphan item35 제거(parent17=0 가드) → 게이트 parent-zero 0 수렴. (`inbox/parser/20260616T0130Z__validation__MULTI__parentzero_catastrophe_plus_kakao_19market`.)
- [x] **INTERNAL_MODEL_36IRR_EXEMPT 등록**(owner 승인 2026-06-15): `kics_json_rules.py` frozenset 5셀(KR0073 2025.2Q·KR0094 ×4) RED→SKIP. **36_irr RED 11→6**. pytest 110 passed.
- [→] **카카오 2023.3Q 19_market 재특성화**: parser "cadence SKIP" 제안 = 부적절(MD L177-186에 분해표 실재 = 19_market RED 참). micro 억원-coarse라 카카오 2023.2Q 동류 artifact. 처분(파서 적재 후 micro / owner micro exception) = owner 결정. TODO.md(root) line 79-80 카카오 cadence 분류 정정 필요(owner 갱신).

### V14 — backlog #6/#7/#8/#9 (2026-06-16, owner "전부다 진행", 4-에이전트 Workflow)
- [x] **#6 삼성화재 FY2024 IR benchmark RESOLVED**: `validate_nb_csm_multiple.py` `load_fy2024_ir_anchors`(IR series 2024.4Q.multiple_derived_ytd) + 삼성화재 PREFERRED_SCOPE monthly_avg_from_ytd → computed 14.76/IR 15.16 rel 0.026 fallback_used=False. **fallback_pass 2→1**.
- [x] **#6 현대해상 = 영구 fallback 확정 (owner 2026-06-16: "현대해상 IR은 CSM배수 없어 패스")**: 현대 IR이 신계약 CSM 배수를 아예 미공시 → benchmark 불가, fallback(2025.2Q=18.9)이 정상·영구. fetch 불요. V2 line 87 "현대 IR multiple 부재→영구 fallback"과 일치. fallback_pass=1은 이 1건(현대)으로 고정.
- [x] **#7 CONT 면제 → REVERT (owner 2026-06-16)**: 한때 CONT에 documented-재작성 면제를 넣었으나 owner 지시로 즉시 되돌림 — **continuity break(기시≠직전기말)는 무조건 RED, "소급재작성"이라 면제 금지**. cont=15 유지(면제 0), WFY 면제만 존치. pytest 110. 메모리 [[continuity-break-is-red]] + [[route-by-raw-availability]] 저장.
- [→] **#7 2026.1Q boundary = 파싱오류 (정정 2026-06-16, owner 원본검증; 내 #7 오진 시인)**: 5사 2026.1Q 기시 CSM이 misparse — 정답은 직전 2025.4Q 기말(교보 65,110·메리츠 111,037·신한라이프 75,537·에이비엘 9,702·푸본현대 1,907.45). self-closing identity는 opening 검증 못 함(오진 원인). **재작성 아님 = RESTATEMENT_EXCEPTIONS 등록 금지, CONT RED 유지.** `data/dart/FY2026_Q1/` 부재(purge) → downloader raw 복원(`inbox/downloader/…restore_fy2026q1_dart_raw`) → parser/ifrs17 재추출(`inbox/parser/…csm_2026q1_opening_misparse`). 복원 후 재검증.
- [i] **#7 저배수 4사 = scope 오류 아님**(framing 정정): 교보 6.61/한화 9.84=2026.1Q Q1 계절저점 YTD(한화는 IR FY 7.6 초과), 교보플래닛 2.0·처브 2.4=micro 실제 저배수. 분자 전부 waterfall item2 일치. **조사 종결, 액션 없음.**
- [x] **#8 verify_parser_change.py 신설**: snapshot/diff(blast-radius, kics cell-diff)/validate(6검증기 일괄)/all. 추출기 변경 회귀 1커맨드. 통합 validate 검증 완료.
- [x] **#9 QoQ yaml loader = 이미 배선**: `validate_master_tables.py:84` 이미 `yaml.safe_load(config/qoq_thresholds.yaml)`. backlog 항목 stale, no-op.

### V11 — 2026-06-14 (b) 정합성 전수검증 후속 (라우팅 발주 + owner 예외 결정 대기)
근본원인 검증 Workflow(8 에이전트 raw 대조) 후 비-시장 등식 RED 4종 disposition:
- [x] **메리츠 KR0001 rule5 reparse → ✅ RESOLVED**: parser가 item23+item25 12분기 적재(항등도출=공시값 일치). 재검증 **rule5 12 RED→0**. `_resolved/` 이관.
- [x] **코리안리 KR1000 2025.2Q reparse → ✅ RESOLVED**: parser가 코어 1-28 + item28 파생(156.19) + 시장37-40 fitz 적재. 재검증 **7 RED + 19_market→0**. `_resolved/` 이관.
- [x] **푸본현대 sensitivity (ifrs17 발주) → ✅ RESOLVED**: parser 근본원인=mis-tag 롤포워드(shock행0), `_has_shock_rows` 가드로 KB·푸본현대 ok→partial 정직화. 재검증 **SENSITIVITY YELLOW 1→0**. `_resolved/` 이관.
- [x] **(종결 2026-08-20) AIA KR0080 2025.1Q rule2** — owner 예외 등재 **이미 완료**: `TODO.md` L115 *"rule 2 × 1: KR0080 AIA 2025.1Q (diff=−789) — scan-only(아래 documented)"*. 게이트 계약 충족.
- [x] **(종결 2026-08-20) 미래에셋 KR0079 8_life** — owner 예외 등재 **이미 완료**: `TODO.md` L117 *"rule 8_life × 1: KR0079 미래에셋 2023.2Q — scan-only. 8_life는 SKIP=게이트 비차단"*. 게이트 계약 충족.
- [ ] **(owner 결정) parser irr_exempt v2 잔여**: INTERNAL_MODEL_36IRR = **신한라이프 KR0094×4 + 교보 KR0073 2025.2Q = 5건만**(IBK KR1011은 parser fitz로 41-46 적재·derive rel 0.0% GREEN → 면제 불요, 2026-06-14 정정) + OCR(KB/한화생명/흥국×2) + micro(신한이지 KR0051×3) EXEMPT — 전부 owner 권한. inbox/validation answered 참조.
- [x] **scan false-positive fix**: `_scan_breakdown_presence` clean-cell화 → 삼성생명 odd-Q 3 false RED 제거(19_market 15→10). parser D 종결.
- [x] **SENSITIVITY_UNIT_SANITY 룰 신설**(owner 0712Z claim2): `validate_master_tables.py` RED>1000x/YEL>100x. 640배 회귀가드. 푸본현대 YEL 1(÷100 미정규화 의심) + 미래에셋·롯데·한화손해 sensitivity 0건 → parser/ifrs17.
- [x] **TOOLING_FAIL census 배선 완료**(2026-06-14, owner "AB go"): `validate_kics_disclosure.py._market_tooling_fail()` — nonok.json을 현 데이터와 대조해 여전히-갭 셀만 're-localize' 노출(stale 제외, 비차단). 현 0건. parser fitz-fallback 안착분 이행.
- [x] **hyundai_pl ZLEG 등록 완료**(KR0009): 현대 2024.1Q~2025.2Q `ZLEG_LEGIT_CQ` 등록 → zero_legs 6→1. thread 종결.
- [→] **KR0083 푸본현대 2026.1Q continuity**: FY_BOUNDARY 2025.4Q기말 1906≠2026.1Q기초 1669(Δ12.4%) 현 RED + sensitivity flagged = 실데이터 의심, 잔여 유지.

### V7 — NB CSM cross-source + 시계열 전수 (parser P1/P2 회귀 잔여)
Rule `NB_CSM_DART_VS_IR_ANNUAL_SUM` codified (§1.2, RED, tol max(5%·|IR|, 100억)). Tools: `check_nb_csm_widespread.py` (FY24 snapshot, 6/7 OK) + `check_nb_csm_history.py` (13Q×9사 baseline). FY24 widespread: 롯데 1.233 (+23%, FY25 의존), 나머지 ~1.00 OK.
- [→] **Parser P1**: 롯데 FY2025 구성요소별 차이조정 표 capture + NB override (412,168 = IR FY25 일치). Raw: `data/dart/FY2025_Q4/raw/KR0003_롯데손해보험_20260319001293/_00760.xml:27375`.
- [x] **🚨 Parser P2 회귀 = 재확인 완료 (2026-06-16)**: off-by-one-year **해소 확정**(현 `data/ir/series/` Q1 YTD-reset 정합, 삼성화재 6782.7→14426→...→2024.1Q 8855.5 리셋). `check_nb_csm_history.py` **복원**(self-contained, 컨벤션 series 메타 도출) + `nb_csm_history_check.json` 갱신. **systemic-3 = 실재(정렬 아티팩트 아님), 근본원인 = DART CSM_waterfall partial/no_csm_block 추출**: 롯데 2025.2Q partial→NB_YTD=0→delta −1098.5(음수 불가) / 미래에셋 2025.2Q·3Q partial→collapse-then-catchup spike(=↑↓ 교대) / 2025.2Q cohort-wide 동일. DB 부호반전은 DB DART 2025.2Q+ 부재로 재현 안 됨. 삼성생명 2025.2Q OVER(+26%)=status ok=진짜 scope 차이(별건). → parser/ifrs17 `20260616T0230Z__...nb_csm_partial_extract_corrupts_history` 발주.
- [→] **한화손해 stale carryover** (별도 parser 버그): 2025.1Q DART NB가 2024.1Q 값 그대로 복제됨. 한화손해 IR note에 기록.
- [ ] (passive) V1 활성화 시 `CSM_WATERFALL_DART_VS_IR` new_business step과 overlap → retire 검토.
- Regression cmds (parser P1+P2 후): `check_nb_csm_widespread.py` → ok=7/7; `check_nb_csm_history.py` → OVER/UNDER 0 수렴.
- Gate enforcement는 publishing stage 측(사용자가 publisher에 전달).

## 🟠 Open — P2

### V8 — DART 자기완결 정합성 (CSM_waterfall 도메인 잔여)
PL_BRIDGE + CSM_CROSSCHECK 소비자 코드 구현 완료(2026-06-07). 빌드→검증 통합(`validate_master_tables.py`가 `build_root_masters.py` 자동 선행, idempotent; `--no-build`로 끔). 회귀 명령: `python scripts/validate_master_tables.py`. 현재 dup:0 spike:1 cont:12 crosscheck:0F closing:0F.
- [→] **데이터 채움 (parser/수집)**: 미래에셋 CSM상각 2025.2Q·3Q·2026.1Q 누락(2025.1Q는 있음), 롯데 생명장기손익 2025.2Q 누락(1Q·3Q는 있음). closing/pl_bridge가 skip하던 진짜 hole.
- [x] **cont 6건 = 둘 다 데이터 정정 → ✅ RESOLVED·검증완료 (2026-06-20)**: boundary break 2종 모두 후속 공시 '전기(비교)' rollforward로 과거 cell 정정 → cont 자연 해소. **parser 처리 완료, validation 재검증 `cont 6→0` 확인**.
  - **교보생명 2024(cont 2 + wfy 1) = legit 소급정정**. owner: "24.3Q부터 회사가 기초 58249로 소급정정 → 2024.4Q+ 보고서 '전기'열에 재작성 2023말값". **처음엔 면제(`CONT_RESTATEMENT_CONFIRMED`) 등록했으나 owner가 데이터정정 방식 제안 → 면제 코드 원복, 정정 발주로 전환**(더 정확, 시계열 통일). parser `inbox/parser/20260620T0600Z__validation__KR0073__kyobo_csm_priorperiod_pull`. raw XML purge지만 **extracted 살아있음**(`data/dart/extracted/교보생명보험_<rcept>_measurement.json`).
  - **삼성생명 2024(cont 4) = misparse**. owner: "2023.4Q 기말 122474 정답, 현 123926 오류". parser `0545Z`(owner-gold + 동일 extracted-전기 기법 교차검증).
  - 둘 다 정정 후 **cont 6→0**. 케이디비 spike(2024.1Q→2Q +58%)는 별건 잔여.
- [→] **PL 잔여 14F**: (1) 2023 분기 사이트 비노출 → 넘어감. (2) 소액 잔차(흥국 2025.1Q +714·KB라이프 +1,136·악사 +3,483) — 종목합산 기타비 내재 또는 미세, 지나감. (3) bare로 닫히는 분기(흥국 2024.4Q 등)는 정상.
- 참고: dual-form은 의도된 설계(사용자 확인) — bare 통과 분기 flag 안 함. 과잉진단 금지(§1.5). 단위: pl 백만원 / waterfall 억원 (cross-check ×100 정렬).

### V9 — 사용자 xlsx 수기검수 후속 (룰 3종 WFY/ZAMORT/ZLEG, parser 대기)
영속성 해결(`csm_manual_overrides.json` + `_apply_csm_overrides()` 훅, 빌드 생존). WFY 10/10 판별 완료(wfy 0). ZLEG 23→1(동양 2025.3Q 잔여). 메모리 `validation-blind-spots`·`master-xlsx-review-loop`.
- [ ] 교보(6.61)·한화생명(9.84)·교보플래닛(2.0)·처브(2.4) 저배수 별도 원인 조사(분자 scope?).
- [→] **신규 (parser)**: 메트라이프 영업이익 등식 2분기 FAIL(+12,086/+12,897) + 코리안리 crosscheck 2F(wf 상각 1년 lag 의심) + 동양 2025.3Q zleg 1건.
- [→] **현대해상 PL 8분기 재추출 (parser, 경고 inbox)**: 생명장기원수/기타원수/재보험손익/기타재보 — legit_absent 오판, 답지 anchor. 2025.2Q 패스.
- inbox: `20260611T0900Z__validation__MULTI_ALL__user_xlsx_audit_followup.md`.
- 참고: 보험손익 잔차 = LOB 별도/연결 기준 오선택부터 의심(§1.5). 신계약 CSM은 pl_breakdown_master에 구조상 없음 → V7 NB_CSM_DART_VS_IR + closing identity가 검증 담당.

### V1 — DART↔IR cross-source 2개 룰 활성화 (segment 폐기로 3→2)
룰 [§1.2 + §1.4]. RED → DART parser loopback. **현재 IR-side 정형 JSON 부재로 전사 SKIP.** (segment 룰 폐기 → V8 대체)
- [ ] **IR parser delivery 대기**: `data/ir/<period>/parsed/<KR>.json` (root TODO F18). 도착 cohort 9사: 메리츠·삼성화재·현대·KB·DB·한화생명·삼성생명·미래에셋·동양. 도착 즉시 룰 자동 ON. ⚠️ **2026-08-20 실측: 1년째 미도착.** `data/ir/**/parsed/` 전체에 파일이 **1개뿐**(KR0087 동양생명 FY2026_Q2, 2026-07-30). 9사 cohort는 오지 않았다 — 재개하려면 IR 파서 레인을 별도 발주해야 한다.

> **⚠ 2026-08-30 실측 정정 — "미도착"이 아니라 "미파싱"이다.** `data/ir/` 에 raw IR
> 자료가 **130개 파일** 있다: 현대해상 13분기 · 한화생명 13분기 · 미래에셋생명 13분기 ·
> DB손해 11분기 · KB금융(_groups) 14분기 + 삼성화재·삼성생명·롯데손해·코리안리·동양생명
> 각 1분기. 없는 것은 **`parsed/<KR>.json` 산출물**뿐이고(2개 분기 6개 파일만 존재),
> 즉 수집이 안 된 게 아니라 파싱 단계를 아무도 돌리지 않았다. owner 2026-08-30: IR 은
> 파싱 검증용 보조 소스이니 **꼭 필요할 때만** 착수할 것.
- [ ] **Threshold v1 튜닝**: 활성화 후 실제 diff 분포 보고 조정. v1: `CSM_WATERFALL_DART_VS_IR` max(5%·|IR|,100억)/step; `CSM_BREAKDOWN_DART_VS_IR` max(5%·|IR|,100억)/item (메리츠는 보종 비교 영구 SKIP — 측정요소별 표만, total만). ⚠️ **2026-08-20 실측: 1년째 미도착.** `data/ir/**/parsed/` 전체에 파일이 **1개뿐**(KR0087 동양생명 FY2026_Q2, 2026-07-30). 9사 cohort는 오지 않았다 — 재개하려면 IR 파서 레인을 별도 발주해야 한다.
- IR factsheet NB CSM multiple 가용성: 부재(현대해상·KB손해); 간접 산출 가능(DB손해 = 신계약 CSM + 월납보험료 derive).

### V2 — IFRS17-NB-RECONCILE 정합성 (한화 fallback retire 완료)
`validate_nb_csm_multiple.py` period-aware denominator + fallback flagging. 한화 fallback retire 완료(2026-06-12 재검증, `fallback_used=False`). 결과: tested 5 / pass 5 / fallback_pass 2(삼성화재·현대).
- [ ] 삼성화재 IR annual benchmark 보강 — 잔여 fallback 1건 해소. 2026-06-12 재확인: aligned FY2024 행 실패 → 2025.3Q fallback(rel 0.244=tol 0.25 턱밑, tolerance-loophole 경고). FY2024 연간 IR 분모 소싱 필요. (현대는 IR multiple 부재 → fallback 영구 유지.)

### V3 — K-ICS 시장위험 분산효과 validation (F12 cross-stage)
validation 룰 2개 구현 완료(2026-06-09b, `kics_json_rules.py`): `19_market`(item19=sqrt(V'·M·V), V=[36–40], MARKET_M 5×5) + `36_irr`(금리위험액 시나리오 분해). 정본 `docs/agents/kics-market-risk-decomposition.md`. 골든 3/3 일치. 화면 노출 X.
- [→] parser stage가 item36–46 적재(시장위험 세부표 5종 + 금리 시나리오 순자산가치 6종) — 진행 중. (V10 재추출과 동일 작업축.)
- [ ] 적재 단위(억원 vs 백만원) parser 회신 확인 → 백만원이면 대조식 ×100 조정. 적재 후 게이트 RED=0 확인.

### V4 — QoQ threshold registry
`config/qoq_thresholds.yaml` §2 + `QOQ_DELTA_WARN` 소비자 코드 구현 완료(2026-06-09, `validate_master_tables.py` 4번). CSM 항목 대상(누적→YoY / 시점→QoQ, floor 50억), PL 손익 제외. 193 YELLOW, 진짜 의심=이자부리 부호반전 3건(동양·교보·코리안리) → parser inbox. 전체 `data/_derived/qoq_warn.json`.
- [ ] (잔여 미구현) yaml loader precedence(item→domain→global) + prior-snapshot fetch + 누적 net-quarterly 변환 + finding emit(YELLOW, summary 기록, loopback 안 함). 진입점: K-ICS는 `validate_kics_disclosure.py` hook, IFRS17은 `validate_csm_waterfall.py` / 별도 스크립트 결정 필요.

## 🟡 Open / waiting

### V5 — 누적 항목 등록 목록 확장
§2.3 등록: IFRS17 `new_business_csm`, `csm_amortization`, `insurance_revenue`. 신규 누적 항목 발견 시 등록 + net 분기 기준 비교로 자동 전환.
- [ ] (운영 중 발견 시 갱신)

### V6 — KR0010 KB손해 OCR 잔여 RED 2건
K-ICS rule 2 OCR 미정확 (KR0010, KR0079도 image-only). 사용자 owned (`TODO.md` `KICS-IMG`). validation gate는 documented exception 처리 중.
- [x] **(종결 2026-08-20) 수기 OCR → RED 2→0** — 무효. 현재 게이트는 **RED=12이고 전건 `TODO.md` documented exception**이라 계약을 이미 충족한다(RED 2라는 전제 자체가 stale). OCR은 owner가 2026-08-15 *"됐어 패스"*로 **명시 보류** — 재요청 전 미착수(`TODO_downloader.md` OCR-MARKETRISK 행이 정본).

## ✅ Done (archive)
완결 항목(V10 census·V-RS 금리민감도 RS1–RS4·V8 PL_BRIDGE/CSM_CROSSCHECK/CSM_PLAUSIBILITY/MASTER_COVERAGE·V9 WFY/ZAMORT/ZLEG·V2 한화 fallback retire·V7 history check·V4 QoQ v1, 2026-05-31~06-12). 각 항목의 날짜별 상세는 `docs/changelog_validation.md`(당시 이미 `(changelog MM-DD)`로 인덱싱됨) + git log.

## 🛡️ Documented exception 관리
운영자(사용자)만 `TODO.md`에 `(도메인, 회사코드, 분기, rule_id, 사유)` 추가 가능. 서브에이전트가 자체 RED waiver 쓰지 말 것. `escalate_to_human` 단계에서만 "재파싱 5회 실패" 사유 기록.

현재 활성 exception:
- KR0010 KB손해 / KICS rule 2 / image-only PDF OCR 미정확 (V6)
- KR0079 미래에셋생명 / KICS rule 2 / image-only PDF OCR 미정확
- KR0097 하나생명 2024.4Q(item30·35)·2026.1Q(item35) / 적용후 세부위험 mmult / **적용후 세부 미공시**(raw는 phase-in 인식비율 10%만, 실값 부재→도출불가) — owner 확정 2026-07-12. 게이트 `_AFTER_SUBRISK_NOT_DISCLOSED`로 추출갭 제외.
- KR0104 농협생명 2023.1Q / 적용후 세부위험 / **다중 경과조치(①②③) 결합공식 불명**(개별표 어느것도 헤드라인과 불일치, 파서 재파싱해도 도출불가) — owner 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0100 처브 2024.3Q / 적용후 세부위험 / **②표 값이 행별로 다른 컬럼 착지**(일반화 규칙 없음) — owner 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0005 흥국화재 2024.4Q / 적용후 세부위험 mmult / **image-only PDF**(텍스트레이어0, 재수집=같은이미지) — owner GOLD-SCAN 대기, 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0097 하나생명 2024.2Q / KICS rule 2·4·5·6 / **스캔이미지 PDF**(items 1-26 미추출, item27/28만 OCR) — OCR 재처리 후속. documented.
- KR0002 한화손해 2024.2Q / KICS rule 9 / **4억(0.015%) 반올림 비물질**(tolerance-too-tight, 카카오 8_post 동류) — documented, 무해.
- (fixed, 예외아님) 카카오 2023.4Q 8_post: item14후=20억 coarse 반올림 → **8_post에 rule8 dynamic tol 배선(2026-07-12)**으로 통과. prepush RED 1→0.

## 📞 Loopback contract
§3. **max 5회**. RED packaging에 `suspected_source: "DART" | "IR" | "internal"` 명시. cross-source 룰은 항상 `"DART"`.

| 조건 | next_action | exit |
|---|---|---|
| RED=0 | `pass` | 0 |
| YELLOW만 (RED=0) | `pass` | 0 |
| loop_iteration==5 & RED>0 | `escalate_to_human` | 2 |

## 🔗 참조 룰셋 / 코드
- 권위 doc: [`docs/agents/kics-json-validation-rules.md`](docs/agents/kics-json-validation-rules.md) (R1–R10 formulas, tolerance, R4/R7 matrices, item-label mapping)
- K-ICS 구현: [`src/solvency/validation/kics_json_rules.py`](src/solvency/validation/kics_json_rules.py)
- 러너: K-ICS `python scripts/validate_kics_disclosure.py` · IFRS17 CSM `scripts/validate_csm_waterfall.py` · NB CSM multiple `scripts/validate_nb_csm_multiple.py` · reconcile loop `scripts/run_ifrs17_csm_reconcile_loop.py`
- Output: `artifacts/validation/<domain>_<timestamp>.json`
