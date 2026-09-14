# TODO archive — `TODO_validation.md` (Status 이력, 읽기 지연)

> `TODO_validation.md` 의 Status 이력 블록을 2026-09-11 에 **한 글자도 고치지 않고** 옮긴 것(최신순). 세션 시작 시 읽지 않는다 — `docs/changelog_*.md` 처럼 특정 과거 결정의 배경이 필요할 때만 연다. 활성 TODO 의 Status 에서 밀려난 항목은 이 줄 바로 아래에 그대로 잘라 붙인다(최신이 위).

---

**(2026-09-13 후속) UH-18 배선 완료 · UH-19 신규·같은 날 해소 — jp 레인에도 "게이트가 검사하는 파일 = 사용자가 보는 파일"이 걸렸다.** `build_jesr_page_json.py::source_gate_check` 4종(`JP_SOURCE_EXPIRING_HOST`·`JP_SOURCE_URL_DEAD`·`JP_SOURCE_EVIDENCE_STALE`·`JP_SOURCE_EVIDENCE_INCOMPLETE`)이 `self_check` 경유로 **exit 1 에 실제 반영**된다(변이시험: extend 한 줄 제거 시 exit-code 케이스 3개만 정확히 FAIL). 회귀 43케이스 + 이빨 변이 5/5. **네트워크를 안 타는 설계**: 판정은 `check_source_urls.py --all` 이 `source_url_health.json` 에 박제하고 빌더는 박제를 읽는다 — 그래서 `JP_SOURCE_URL_DEAD` 의 이빨은 `JP_SOURCE_EVIDENCE_STALE` 에 전적으로 의존한다(한 쌍, 독립 룰 아님). 오탐억제: RED 로 읽는 분류는 `dead` 하나뿐(254건 실측에서 "ok 아니면 RED" 는 48건 거짓 RED). 예외 등재처 `J-ESR/jp_source_exceptions.json`(0건, fail-closed, 절차 룰 2종은 면제 불가, 등재는 owner 권한). **UH-19**: jp 게이트는 빌더를 돌릴 때만 도는 구조라 census 만 고친 커밋이 검사를 통째로 비껴갔다(실측 사례 `62eed63`) → `tests/test_jp_deploy_matches_census.py` 로 "배포 JSON = census 재빌드 결과" 를 강제, 두 테스트를 `prepush_check.py` offline 묶음 + CLAUDE.md §5 jp 축소범위에 등재해 **훅이 실제로 부른다**. 포스트모템 `PM-2026-09-13` 은 **open 유지** — 사고 3건 중 2건(東京海上HD·かんぽ)은 URL 이 살아 있었고, 그 축(`JP_ESR_NOT_IN_SOURCE`)은 오탐억제 3종의 실측 분포가 선행조건이라 아직 안 걸었다(UH-5·UH-9 선례).

---

**(2026-09-13) jp 레인에서 false-green 3건 — 포스트모템 `PM-2026-09-13` 신설, 룰 4종 정의했으나 **전부 미배선(UH-18)**.** jp 빌더 self-check(범위·형식·합계)는 통과했는데 화면 수치 2건이 2차보도·조정치였고(東京海上HD 238→268 · かんぽ 220→181 · 明治安田生命 208.0→208.7), 출처 URL 1건은 ESR 이 한 줄도 없는 합병 보도자료였다(MS&AD). **메커니즘: self-check 가 census 안에서만 닫히는 자기참조라 "출처가 살아 있나 / 그 문서에 그 숫자가 있나" 축이 없다** — PM-2026-06-16("산술만 검사")의 jp 판. 룰 4종(`JP_SOURCE_URL_DEAD`·`JP_SOURCE_EXPIRING_HOST`·`JP_ESR_NOT_IN_SOURCE`·`JP_ESR_EDINET_MISMATCH`)을 오탐억제까지 정의하고 도구는 만들었으나(`J-ESR/check_source_urls.py`·`edinet_esr_probe.py`) 어느 게이트에도 안 걸려 있다 = honor system. 배선 방향은 **증거 신선도 검사**(`source_url_health.json` 의 `checked_at` 이 census 보다 오래되면 RED) — 네트워크 없이 "점검을 안 돌리고 census 를 고쳤다" 를 잡는 형태. 티켓 `inbox/jp/20260913T1500Z__validation__JP_MULTI__jp_source_gate_wiring.md` / P1.

---

**(2026-09-11) `public_exports/` 변이시험이 실제 배포 파일을 제자리에서 흔들다 끊긴 잔해(가짜 회사 행 1건)가 워킹트리에 남아 prepush 오프라인 테스트를 막았다 — 3번째 재발이라 구조를 바꿨다.** `check_public_exports(fd, out_dir=None)` 로 검사 폴더를 주입 가능하게 하고, `test_mutation_public_export_fires` 는 pytest 임시 폴더에 복사한 사본만 훼손한다. dirty-check·백업·`finally` 복원 코드 삭제(필요 없어짐). 실측: 관련 테스트 149 passed, 변이시험 후 `git status public_exports/` 깨끗, `validate_live_artifacts.py` RED=0. 밀려난 Status 항목(09-01 소급재작성 축)은 `docs/todo_archive_validation.md` 로.

> 📦 **Status 이력은 `docs/todo_archive_validation.md` 로 이동했다** (2026-09-11, 내용 무수정 — (2026-09-01) 판정 사이드카 및 그 이전 항목). 세션 시작 시 읽지 않는다; changelog 처럼 특정 과거 결정의 배경이 필요할 때만 연다. **이 Status 는 최신 5개 항목만 유지**하고, 밀려난 항목은 그 파일 헤더 바로 아래에 그대로 잘라 붙인다.


**(2026-09-02) 마스터 JSON 의 하류 사본이 둘인데 검사기는 하나였다 — `MASTER_XLSX_*` 축을 신설해 닫았다.**

> owner 승인(2026-09-02 "신설한다 — 14개 시트 전수"). 신설:
> `scripts/check_master_xlsx_drift.py`(비교기) · `validate_data_contract.py` CHECK 8
> `check_master_xlsx`(게이트, `run_gate` → `prepush_check.py` §1 → 훅) ·
> `tests/test_push_gate_wiring.py` WIRED 선언 · `tests/test_rule_coverage_manifest.py` 18개 테스트 ·
> `scripts/_probes/probe_20260902_master_xlsx_retrodiction.py`(되돌려 재보기).
>
> - **무엇이 사각이었나.** 루트 마스터의 하류 사본은 둘(`public_exports/` 스냅샷 ·
>   `insurequant_master_tables.xlsx`)인데 검사기는 `PUBLIC_EXPORT_*` 하나뿐이었다 —
>   **마스터 ↔ xlsx 를 대조하는 룰이 0건.** xlsx 만 뒤처져도 RED 가 구조적으로 나올 수 없었다.
>   `sync_master_xlsx_sheet.py` 는 요청받은 시트만 동기화하고 스스로 뒤처짐을 탐지하지 않으므로,
>   정합성이 **"누가 어느 시트를 동기화할지 기억하는 것"** 에 걸려 있었다.
> - **사고 2건.** ① owner 라이브 QA — NH농협손해 2026 기본자본비율 전망이 라이브·마스터 102.77
>   인데 xlsx 만 79.8(그 회사 2026.1Q 값). 38개사 전부 2090칸 중 **1219칸 stale**.
>   ② owner 반문("소진율 2종도 stale 하겠네")으로 13시트 전수 측정 → **가설과 결과가 달랐다**:
>   소진율 2종은 깨끗, 아무도 안 보던 `K-ICS공시` 가 stale(33셀·121행).
>   **어느 시트가 stale 한지 추측하지 말고 전수로 재라.** 데이터 수정은 `d1f1e7f`·`ee11c1d`.
> - **배선 전 시뮬레이션(규율)**: RED=0 · YELLOW=0 확인(13시트 **53,288행** = 워크북 전 데이터 행).
> - **되돌려 재본 실측**: 두 수정 커밋이 xlsx 만 건드렸으므로 그때 워크북을 꺼내 오늘 마스터로
>   대조 → `d1f1e7f~1` **RED=5** · `ee11c1d~1` **RED=2** · `HEAD` **RED=0**. 셀 수가 두 커밋의
>   자체 기록과 **정확히 일치**(1111/169/33/121) — 이 룰이었으면 사람보다 먼저 막았다.
> - **스키마는 import 한다.** 시트목록·평탄화·타입강제는 `build_master_xlsx`, 목표행·비교정규화·
>   행식별키는 `sync_master_xlsx_sheet` 에서 가져온다. 베끼면 빌더가 바뀌는 순간 갈라진다.
>   비교 기준은 동기화와 **정확히 같다** — 느슨하면 값 차이를 놓치고 **엄하면 어떤 도구도 만들 수
>   없는 상태를 요구**해 영원히 못 고치는 RED 이 된다. `'154'` vs `154.0` 은 셀 타입 차이라
>   드리프트가 아니다(양방향으로 테스트에 박아 뒀다).
> - **`요약` 은 행수만 검사한다** — 설명 열은 다른 레인이 손으로 관리하는 문구다(sync L21-22).
>   `MASTERS` 밖 수기 시트는 허용된 설계라 RED 이 아니라 YELLOW census.
> - **변이시험은 워크북을 재저장하지 않는다.** `compare_sheet`/`scan(sheets=...)` 을 순수 함수로
>   분리해 메모리 안에서만 흔든다(openpyxl load+save 는 다른 시트 수식 캐시를 날린다). 픽스처가
>   읽기 전후 바이트 해시로 무변경을 실측한다. 변이 8종 + 사고 재생 1종 전부 발화.
> - 회귀: `--selftest` **57/57 유지** · 게이트 **RED=0 유지**(YELLOW 96→97) · 오프라인 묶음 통과.
>   **실행 비용 +11.9초**(게이트 15.2→27.1초, 훅 17분 33초 대비 +1.1%).
> - 잔여 **UH-15**(하류 사본 매니페스트 부재 — 세 사본이 전부 사고 후에야 검사 대상이 됐다.
>   UH-14 와 같은 뿌리라 합류) · **UH-16**(sync 가 시트 무변경 시 `요약` 행수 미갱신, 현재 무해) ·
>   **UH-17**(워킹트리 기준 대조라 sync 후 커밋 없이 push 하면 안 잡힌다 — 커밋 기준으로 바꾸면
>   정상 sync 중 상시 발화라 오탐억제 설계 전까지 배선 안 함).
>   포스트모템 `docs/postmortems/PM-2026-09-02_master_xlsx_stale_unchecked.md`.

**(2026-09-01) item23(기타요구자본) 자식 24/25/26 적용후 결측 227버킷 판정 완료 — 등재부 신설로 SKIP-on-missing 사각을 닫았다.**

> 티켓: `inbox/validation/20260901T1200Z__orchestrator__MULTI__post_transition_item23_children_227_buckets.md`.
> 227버킷 = 196(부모≈0, 등식 0=0+0+0 자명, 원장 불요) + 31(부모 material, 원문대조 필요 —
> 교보생명 18·흥국생명 12·삼성화재/DB손해/한화생명/코리안리 각 1). 이미 오늘 오전 두 커밋
> (`e684f69`·`345b3a4`)이 227의 대부분(196+실제 채운 106칸 등)을 처리했고 `data/_derived/
> item23_children_audit/verdict_group3.json`에 31버킷×3칸=93셀 건별 판정(POST_EQUALS_PRE_LEGIT
> 54·SOURCE_ABSENT 36·UNMEASURED 3)까지 남겨 뒀는데 **게이트가 읽는 자리가 없어** 매 실행
> 미분화 SKIP("추출갭 후보")으로 재발할 상태였다. 이 세션이 KR0071 raw PDF(fitz) 직접 재확인으로
> 독립 검증(2023.2Q 사례 일치) 후 `data/_gold/kics_item23_children_post_absent.json`(31버킷,
> verdict+pin) 신설 + `scripts/validate_kics_disclosure.py::_other_capital_children_sum`(3-tuple
> 반환으로 확장, ledger lookup)·`scripts/validate_data_contract.py`(호출부 동기화 + 등재값 이탈시
> `OTHER_CAPITAL_CHILDREN_LEDGER_DRIFT` RED) 배선. **원장은 finding을 지우지 않는다** — skip
> 집계는 그대로고 태그에 판정만 붙는다, 등재값에서 벗어나면 RED로 승격.
> 검증: gate 전/후 상태카운트 바이트동일(RED=39/YELLOW=1658/GREEN=11102/SKIP=2803, 요구자본 축만
> 재태깅), `validate_data_contract.py` RED=0 유지, pytest 842 passed(BS golden 제외) +
> `_data_contract_selftest.py` 57/57.
> KR0071 2024.4Q(UNMEASURED)는 raw PDF가 정기경영공시가 아니라 DART 사업보고서(538p, K-ICS
> 수치표 0회) — 스캔이 아니라 **잘못된 파일**이라 OCR로 안 풀린다. `inbox/downloader/
> 20260901T1329Z__validation__KR0071_2024.4Q__wrong_document_not_periodic_disclosure.md`로 라우팅.

**(2026-09-01, 이전) 판정 사이드카 2종이 2026.2Q 전체에 대해 스테일이었다 — 게이트가 39사를 조용히 "판정 불가"로 흘리며 exit 0 이었다. 경로·지표·스테일 검사 셋 다 고쳤다.**

> 수정: `scripts/_disclosure_pdf_paths.py`(신설, raw//pdf/ 단일 해석기) ·
> `scripts/build_kics_source_textlayer.py` · `scripts/extract_transition_applicability.py` ·
> `scripts/validate_kics_disclosure.py`(freshness 경로 + 신규 룰 `SIDECAR_STALE_LATEST_QUARTER`)
>
> - **원인 ① 디렉토리 축.** 13분기 동안 공시 PDF 는 `data/disclosure/<period>/raw/` 에 있었는데
>   **2026.2Q 부터 `pdf/` 로 바뀌었다**(실측 `FY2026_Q2: raw=1 · pdf=39`, 그 전 분기는 전부
>   `raw=38~40 · pdf=0`). `raw/` 만 glob 하던 두 생성기가 2026.2Q 를 통째로 스킵했다. 같은 버그가
>   이 저장소에서 **세 번째**다(`rebuild_combined_transition_after._pdf` · `fill_market_subitems`
>   에 이어). 그래서 개별 패치 대신 해석기 하나로 모았다.
> - **원인 ② 판정 지표(owner 지적).** 판독성을 **문서 전체 평균 chars/page** 로 쟀다. 그 지표는
>   "앞은 스캔·뒤는 감사보고서 텍스트" 문서를 영원히 READABLE 로 부른다(흥국생명 FY2024_Q4:
>   p1-112 이미지인데 전체평균 532.8 → READABLE). 이 오판이 owner 의 옳은 `image-only` 등재를
>   2026-08-21 에 뒤집게 만들었고 처방을 OCR 대신 재수집으로 오라우팅했다. 이제 페이지별 분포 +
>   K-ICS 절 밀도로 재고, 신규 상태 **`SCANNED_SECTION`**(문서는 맞고 절만 이미지 → 처방=OCR)을
>   가른다. 두 판정 중 **엄한 쪽**을 써서 이 지표가 절대 느슨해지지 않게 했다.
> - **원인 ③ 스테일 자체가 무검사.** 사이드카가 최신 분기를 안 담아도 게이트가 통과했다 →
>   신규 RED `SIDECAR_STALE_LATEST_QUARTER` + YELLOW `SIDECAR_COVERAGE_GAP` 배선.
>   역방향 검증: 구 사이드카를 되돌리면 **RED 2건(2026.2Q 39 + 3 버킷)** 으로 정확히 터진다.
>   `prepush_check.py` 는 이미 이 게이트를 부르고 `blocked = ... or n_kics` 로 강제한다(확인함).
> - **실측 이동.** textlayer 486→538셀(2026.2Q 39사 신규) · applicability `NO_RAW_PDF` 8→0 ·
>   게이트 "판정 불가" **57칸/34버킷 → 37칸/20버킷**, `UNMEASURED` **25→0**.
>   사이드카만 A/B 한 결과 blocking RED **1→7**(+6). 값 flip 은 전부 `UNKNOWN→known` 이고
>   기존 판정을 뒤집은 것은 0건.
> - **새 RED 6건은 진짜 결함이었고 같은 라운드에 닫혔다** (KR0009·KR0069·KR0150 2026.2Q ×
>   값/값_적용후): 항목 47~54 가 마스터에 없는데 **원문 MD 에는 숫자가 있고 2026.1Q 에는 적재돼
>   있었다**(커버리지 회귀 `item47` 37/39 → 35/39). parser/kics 발주 → 적재 완료 →
>   **셀 단위로 원문과 대조 확인**(예 KR0069 item47 118,528.22억 = 원문 11,852,822백만 ✅).
>   `item47` 보유 **38/39**, 그 RED **6→0**, blocking RED **7→1**.
>   티켓은 `inbox/_resolved/20260901T0400Z__validation__MULTI_2026.2Q__tier2_tfi_rows_47_54_absent.md`.
> - **잔여 blocking RED 1건은 `19_market` 이고 내 변경과 무관하다** — 사이드카 A/B 양쪽에 똑같이
>   있었다(구 사이드카로 돌려도 나온다). 이 세션에서 원인 규명 안 함.
> - **골든:** `tests/test_kics_rules_golden.py` 는 사이드카 교체 직후 해시가 어긋났으나
>   (구 사이드카로는 PASS 확인 = 내 변경이 원인, 의도된 산출 변경) **손으로 고치지 않았고**,
>   parser 백필 라운드가 재생성하면서 현재 **PASS**. 오프라인 74개 전부 통과.
> - **경고:** `extract_transition_applicability` 의 "표가 있으면 TFI=O" 휴리스틱이 삼성생명 6분기를
>   오판한다(원문은 "공통 및 선택 경과조치를 적용하지 않았습니다"). 일반화 수정("전=후면 X")은
>   **198칸을 O→X 로 뒤집어** blocking RED 을 SKIP 으로 바꾸므로 **기각**했다. 좁은 대안(문서수준
>   부정문 + `외에` 배제)을 시뮬(10버킷 매치 / 6칸 정정 / 대조군 4칸 일치)해 parser 에 발주함.

**(2026-09-01) 미결 — owner 판단이 필요한 것 2건**

> 1. **“분기별 원공시본 기준” 정책이 선언된 적이 없다.** 실측: 가장 가까운 서술은
>    `data/_gold/kics_exemption_provenance.json` KR0032 2024.3Q 엔트리의 “as-disclosed 를
>    그대로 두는 것이 이 저장소의 ‘발행사 기재대로’ 원칙과 일치한다” 인데, **같은 엔트리가
>    ‘as-disclosed 를 유지할지 as-restated 를 채택할지는 owner/parser 정책 결정이고 이
>    세션은 정하지 않았다’ 라고 명시**한다. 관행일 뿐 결정이 아니었다. 게다가 **IFRS17 CSM
>    축에서는 owner 가 반대로 결정했다**(2026-06-20: 후속 분기 비교표에서 재작성값을 pull 해
>    마스터를 재작성 기준으로 통일 — `validate_master_tables.py` L797-799 ·
>    `inbox/_resolved/20260620T0600Z__validation__KR0073__kyobo_csm_priorperiod_pull_from_comparative.md` ·
>    `data/_gold/user_csm_cells.json` “교보 재작성 기준 통일 58,249.2”). 즉 **저장소가 전부
>    as-filed 로 정렬돼 있다는 말은 사실이 아니다** — K-ICS 는 as-filed, CSM 은 일부 셀이
>    as-restated. 새 등재부가 선언하는 것은 **K-ICS 마스터의 기준**이며, 바꾸려면 owner 결정이
>    필요하다.
> 2. **과거 122칸을 등재부에 백필할지.** 지금 등재부는 검증된 2026.1Q 라운드 10칸뿐이다.
>    과거 시뮬레이션 결과는 `_history_probe` 에 **미검증 표시로** 넣어 뒀다(컨트롤 컬럼 대조·
>    잔여셀 육안 판독 안 함, 쌍당 3~9개사 미판독). 검증 없이 박제하면 그 박제 자체가
>    무검사가 된다.

**(2026-09-01) 소급재작성(restatement) 축을 등재·배선했다 — 그때까지 이 축을 재는 검사기가 저장소에 0개였다.**

> 신설: `scripts/detect_kics_restatement.py`(탐지기) · `data/_gold/kics_restatement_ledger.json`(등재부) ·
> `validate_data_contract.py` CHECK 7 `check_kics_restatement`(게이트, `run_gate` → 훅) ·
> `tests/test_push_gate_wiring.py` WIRED 선언 · `tests/test_rule_coverage_manifest.py` 18개 테스트
>
> - **무엇이 사각이었나.** 공시본 `[경과조치 적용 전 지급여력비율 세부]` 표는 **해당·직전·전전분기
>   3열**을 인쇄한다 → 같은 (회사,분기) 값이 두 번 인쇄된다. 발행사가 그걸 다르게 인쇄하면
>   소급재작성인데, **그 두 인쇄값을 대조하는 검사기가 하나도 없었다.** 교보생명(KR0073)
>   2026.1Q 재작성이 분기 변동 분석 중 **손으로** 발견됐다.
> - **39사 전수 재스캔(실측).** 필링 대 필링(1Q본 해당분기 열 vs 2Q본 직전분기 열)으로
>   **830칸 비교 · 미비교 0칸 · 미판독 0개사**. 결과: **재작성 1개사(교보생명) 10칸**,
>   나머지 38사 무변동. 오케스트레이터 1차 손스캔의 오탐(기타포괄손익누계액·신종자본증권)은
>   재현되지 않았다 — 원인 3가지를 전부 막았다(표 특정 / 소수자리를 원 토큰에서 셈 /
>   item27 파생값 제외).
> - **교보 10칸**: item1·2·4·11 각 +1 · item14 +871 · item15 +888 · item16 +445 ·
>   item19 +779 · item20 +553 · item22 +16. 발행사 사유가 원문에 있다(“종속회사 인수에 따른
>   기타요구자본 증가, 감독원 계리적가정 가이드라인 반영”). 파생 item27 은 161.92→160.41.
> - **마스터는 안 건드렸다.** 등재·탐지만 했다. 마스터 2026.1Q 는 34개사 전부에서 1Q
>   원공시본과 **셀 단위로 일치**(`m!=1Q본 = 0`) — K-ICS 마스터가 as-filed 기준이라는 것을
>   추정이 아니라 실측으로 확인했다.
> - **심각도 = YELLOW.** 과거 13개 분기쌍 전수 시뮬레이션: (회사,분기) 재작성 버킷 **37개 ·
>   셀 122칸**, raw 가 갖춰진 2023.4Q 이후로는 **매 분기 1~5개사**. RED 로 내면 거의 매
>   라운드 push 가 막히는데 막아서 고칠 것이 없다. **RED 은 마스터가 원공시본 기준을 벗어날
>   때만** — `MASTER_ADOPTED_RESTATED` / `PIN_DRIFT` / `CELL_MISSING` / 등재부 위생 3종.
> - 게이트 실측: **RED 0 유지**, YELLOW 201 → 203(버킷 1줄 + census 1줄), exit 0.
> - 변이시험 **15/15 검출**(재작성값 채택·제3값·행삭제·값null·근거필드삭제·키불일치·
>   등재부깨짐·등재부부재·스캔stale·미판독), tol 안(+0.4) 변이는 침묵, **등재 밖 200칸 변이
>   신규 RED 0**(오탐 없음). `scripts/_probes/probe_20260901_restatement_rule_simulation.py`
> - **⚠️ 정책이 저장소 어디에도 선언돼 있지 않았다** — 아래 “미결”의 첫 항목.

**(2026-09-01 10:16~10:30 KST) 미종결 inbox 8건 전수 재검증 — 5건 실측 종결, 3건 open 확정.**

> 종결(`_resolved/` 이동, 각 티켓에 명령·수치 기록): downloader `KR0011`·`KR0029` 2026.2Q 재탕 PDF
> (재수집 확인 — sha 교체·MD "26.2Q" 라벨·`validate_disclosure_freshness --period FY2026_Q2`
> RED=0/GREEN=39·게이트 두 회사 RED 0) · validation `KR0029 2025.3Q 2_tier1_bridge`
> (`kics_exemption_provenance.json` L1826~1891 등재 + `validate_kics_disclosure.py` L2442 배선,
> 박제잔차 −58.0 = 실측 −58.0, blocking RED 0) · designer `capsec_numerator_as_of`
> (커밋 `a4bfddf`, `K-ICS.html` L971-979 이 행별 `numerator_as_of` 를 찍음; 둘 다 null 인 14사는
> 전부 발행 0) · parser `KR0008 market_subitem_total_row_labels`
> (`_TOTAL_ROW_CORE_RE`/`_table_risk_item_from_header` 신설, `extract_mkt_subs` 재현 36-40 5건 전부,
> `19_market` 2026.2Q GREEN 38·YELLOW 1·RED 0, 36-40·41-46 결측사 0/39).
>
> **open 확정 3건 (전부 parser/kics lane)** — 각 티켓에 "남은 것 한 줄" 로 명시:
> ① `20260831T0700Z` docling window: 데이터 증상은 소멸했으나 **요청 2(`source_page_ranges` 가드)
> 배선 0** (`grep -rn source_page_ranges --include=*.py scripts/ src/ tests/` = probe 뿐), 세 번째
> 실패양식 원인 미규명, **신규 실측 반례** KR0069 2026.2Q MD 에 금리·주식위험액 절이 여전히 없어
> 마스터와 MD 가 갈라짐. ② `20260831T0800Z`: `compute_tier2_utilization.py` 가 아직 마스터
> item47~54 를 안 읽고(MD_DIR 기본값도 FY2025_Q4) 한도 대조 검산도 없음, `--ocr-scale` 정식화 미답.
> ③ `20260901T0500Z`: `_pdf()` 는 고쳐졌고(39/39 해석) 4버킷도 보존됐으나 **요청 2(스킵 비율 인쇄 +
> 50% 초과 시 non-zero exit) 미반영** — 지금도 스킵이 exit 0 이다.
>
> 신규 발주: `inbox/downloader/20260901T0140Z__validation__MULTI__disclosure_selector_hardening.md`
> (KR0011 위치고정 xpath · KR0029 하드코딩 `pancId` · KR0150 중복 `id="test1"` — 재발 자체는
> `validate_disclosure_freshness` 가 `prepush_check.py` L94·L228 로 push 를 막는다).
> `scripts/check_inbox_hygiene.py` = 활성 5 · 종결보관 369 · **위반 0**.

**(2026-09-01) `TRANSITION_AFTER_MMULT_MISMATCH` 흥국생명(KR0071)·농협생명(KR0104) 4건 = 우리 유도 오류. 원문 정정 완료, 해당 축 RED 0.**

> 처리: `scripts/_probes/fix_20260901_kr0071_kr0104_combined_transition.py --apply` ·
> 라우팅 `inbox/parser/20260901T0500Z__validation__MULTI_2026.2Q__combined_transition_rebuild_skips_pdf_dir.md`
>
> - **판정 = 발행사 자기모순 아님.** 원문은 결합(②+③) 시나리오의 `item15/16/22/23후` 를
>   **인쇄하지 않는다**. 인쇄된 건 헤드라인(1·14·27후)·②표(17후+29~35후)·③표(19후+36~40후)와
>   ②·③ **각각의** 15/22/23후(단일 시나리오)뿐이다. 마스터는 결합 헤드라인 `14후` 에 **②단독**
>   `22후/23후` 를 붙여 `15후` 를 역산해 뒀다 — 22후/23후는 시나리오마다 다르므로(흥국 ② 4,764.60
>   vs ③ 5,930.51) 그 가정이 거짓이고, 그래서 R4 재조합과 어긋났다.
> - **R4 가 발행사 산식이라는 증거**: 같은 문서의 **인쇄된 기본요구자본 8개 컬럼 전부**
>   (2사 × 2분기 × {적용전, ②후, ③후})를 잔차 ≤0.01억 으로 재현한다.
> - 정정은 정본 methodology(`scripts/rebuild_combined_transition_after.py` docstring) 그대로 —
>   `15후=R4(17~20후)+21후` · `14후`는 원문 헤드라인 앵커라 불변 · `23후`는 KR0071 관계회사
>   (KR0005) 환산(비율 0.400607, 14분기 실측 스팬 0.400568~0.400628) / KR0104 0 · `22후`는 잔차 ·
>   `16후=sum(17..21)후−15후`. 정본 검사 4종(적용전 재현·R7/M 재현·단조성·잔차범위) 전부 통과.
> - 실측: 게이트 `validate_data_contract.py` RED **75 → 69**. 이 축 REDs 흥국생명 2건·농협생명
>   2건 소멸, 덤으로 `TRANSITION_AFTER_IDENTITY` 3건(흥국생명 R5·R6, 농협생명 R6)도 소멸.
>   셀 14개만 변경, 범위 밖 변경 0, 행수 25,202 불변, 중복 콤보 0.
> - **남은 사각(보고용, 미배선)**: `mmult15` 축이 **유도값을 검사하는 동어반복**인 버킷이 12개다
>   (`15후`가 R4로 쓰이고 `22후`가 잔차라 두 식이 구성상 닫힌다). 그 12개에서 "적용후 mmult
>   불일치 0" 은 증거가 아니다: KR0032 2024.1Q · KR0068 2026.2Q · KR0071 2023.2Q/2024.4Q/2025.3Q/
>   2026.1Q/2026.2Q · KR0082 2023.1Q · KR0097 2024.4Q · KR0104 2025.3Q/2026.2Q · KR1011 2026.2Q.
>   진짜 독립 검사로 남는 건 `mmult17`(R7×인쇄된 29~35후)·`mmult19`(M×인쇄된 36~40후)·
>   `27후=1후/14후×100`(양쪽 인쇄)·②③ 단일표 대비 단조성 넷이다. 룰 신설은 발주 대기.
> - 골든 2건(`test_kics_rules_golden` · `test_post_transition_golden`) 실패는 **내 변경과 무관**
>   함을 실측 확인: 룰엔진 골든 해시는 정정 전 백업과 **바이트 동일**(84705b8486fd66ec),
>   post_transition 골든은 `값`(적용전)만 읽는다. 둘 다 2026.2Q 데이터 적재로 이미 드리프트 상태.

**(2026-08-30 c) 사용자가 내려받는 `public_exports/` 12개 파일을 어떤 검사기도 읽지 않았다 — 배선했다. 그리고 그 사각을 잡았어야 할 테스트 자신이 못 보고 있었다.**

> 처리: `inbox/_resolved/20260830T1500Z__validation__MULTI__public_exports_uncovered.md` · commit `8c702fc`
>
> - `validate_live_artifacts.py` check 6 `check_public_exports` — 공개 스냅샷을 루트 마스터
>   (`git show HEAD:`, exporter 자신과 같은 기준)와 셀 단위 대조. 룰 15개: DRIFT ·
>   MISSING_CELL · EXTRA_CELL · INTERNAL_COL_LEAKED(`원보험사코드` 유출) · KEY_AMBIGUOUS ·
>   FILE_MISSING · UNREADABLE · SOURCE_UNREADABLE · MANIFEST_* 5종 등.
> - **시트 목록을 베껴 쓰지 않았다** — `export_public_sheets.MASTERS` 를 import 한다. 베끼면
>   13번째 시트가 조용히 무검사가 된다(CLAUDE.md ①b "룰을 한 개씩 베껴 심는" 패턴).
>   `test_rule_coverage_manifest.py` 가 시트 수 대조로 그 결합을 강제한다.
> - **조인 키 함정**: public 쪽엔 `원보험사코드` 가 없다(owner 지시로 드롭). 키가 유일하지
>   않으면 값 비교를 건너뛰지 않고 `KEY_AMBIGUOUS` 로 막는다 — 조용한 전건 미스 경로 제거.
> - 요청받은 `PUBLIC_EXPORT_STALE`(mtime YELLOW)은 **안 넣었다**: exporter 가 워킹트리가 아니라
>   HEAD 를 읽으므로 마스터 mtime 은 스냅샷 신선도와 무관하고(저장만 해도 움직인다) 오탐만
>   만든다. 진짜 낡음은 값 대조가 잡는다.
> - **더 깊은 구멍**: `test_push_gate_wiring._origin_main_fetches` 가 배포 HTML 만 훑고
>   `<script src="download-survey.js">` 를 안 따라가 그 12개 경로를 **한 번도 본 적이 없었다** —
>   "라이브가 fetch 하는 건 전부 검사기 선언이 있어야 한다" 는 테스트가 통과하는 채로 구멍이
>   열려 있었다. 같은 저장소 JS 까지 따라가도록 고치고 접두 선언(`public_exports/`) 형식 도입.
> - 변이시험 8/8 검출(값 1칸·행 삭제·행 추가·내부열 유출·manifest 거짓·파일 삭제·깨진 파일),
>   원본 바이트 복원 확인. 역방향(선언 삭제 시 12개 undeclared) 확인. `prepush_check` L83-93 이
>   이미 이 게이트를 부르므로 배선 즉시 강제된다.
> - **첫 실사용**: 오늘 `PL_breakdown.json` 이 커밋된 뒤 스냅샷을 재생성하지 않았다면 그대로
>   `PUBLIC_EXPORT_DRIFT` RED 였다. 재생성 후 RED=0.

**(2026-08-30 b) gold 오버레이가 115칸을 아무 탐지기 없이 덮고 있었다 — 이제 게이트가 그 숫자를 인쇄하고, 마스크가 벗겨지면 막는다.**

> 처리: `inbox/_resolved/20260830T0710Z__validation__MULTI__gold_overlay_mask_undetected.md`
> → `status: resolved`
>
> **사각의 정체.** `build_root_masters` 의 `_apply_csm_overrides()` / `_apply_pl_overrides()` 는
> gold `set` 의 값을 **비교 없이 UPSERT** 한다. 전 저장소에서 gold 를 빌더 소스와 대조하는
> 게이트·테스트는 **0건**이었다 → **gold 셀 밑에서 빌더가 회귀해도 화면은 옳고 모든 게이트가
> clean 을 찍는다.** KR0079 두 결함이 2025.2Q~2026.1Q 화면에서 안 보였던 이유가 이것이다.
>
> **배선.** `validate_data_contract.py` **CHECK 6 `check_gold_overlay`** 신설(→ `run_gate()`
> → `prepush_check.py` 1) 단계가 그 `run_gate` 를 부른다 = 훅에 걸린다). 룰 7개 —
> `GOLD_OVERLAY_{REDUNDANT(census YELLOW) · DRIFT(RED) · PIN_MOVED · NEWLY_REDUNDANT ·
> LEDGER_STALE · DUPLICATE_KEY · SOURCE_UNREADABLE(RED)}`.
> **티켓 범위를 CSM 하나에서 CSM+PL 두 오버레이로 넓혔다** — PL 도 똑같이 비교 없이 UPSERT 한다.
>
> **비교 기준 = `_additive_merge` 이전의 fresh 소스.** 그 폴백은 루트 마스터(= 직전 실행의
> gold 값)를 되먹이므로 기준으로 쓰면 검사가 자기 자신을 확인한다(ROW_ABSENT/NULL 14칸이 전부
> SAME 으로 보인다). PL 의 `_zero_other_expense` 도 같은 이유로 재현하지 않는다.
>
> **census 실측** — CSM 270칸: SAME_EXACT 28 · SAME_AT_1DP 58 · LOAD_BEARING 170 · ROW_ABSENT 12 ·
> NULL 2 → **마스크 86**. PL 198칸: 26 · 3 · 46 · 0 · 123 → **마스크 29**. 합 **115칸을
> `data/_gold/gold_overlay_ledger.json` 에 셀 단위 박제**(통째 skip 아님, 매 실행 재검산).
> 원 티켓 83 → 86 의 경로 셋: KR0079 parser 정정 +2 · 중복키 제거로 stale 5칸 정리(순증 0) ·
> **경계를 float 잡음이 가르던 것 +2**(`4727.25 vs 4727.2` = 정확히 0.05 인데 0.050000000000181
> 로 계산돼 마스크에서 빠짐 → `round(|Δ|,9)`).
>
> **양방향 전수 시뮬레이션 ALL PASS**(`probe_20260830_val_gold_overlay_simulation.py`):
> 닫힘 **115/115 = 100.0%**(SKIP 0 — 소스가 null 인 1칸도 "값을 얻으면" 을 변이로 삼았다) ·
> tol 안 변이 신규 RED **0**(밴드 아님) · 박제 안 된 216칸 변이 신규 RED **0**(오탐 없음) ·
> 등재부 전삭제 시 RED 0 + NEWLY_REDUNDANT 115(침묵 아님) · **이 축을 뺀 나머지 RED=0 YELLOW=92
> = 종전 baseline 그대로**. 게이트 총계 YELLOW 92 → **94**(오버레이당 census 한 줄), RED **0**.
>
> **배선 중 오탐 14건을 내고 잡았다.** 등재부 키를 `회사|분기|항목` 으로 만들었더니 CSM 과 PL 이
> 그 공간을 **공유해서**(`KR0072 2023.2Q 항목4` 가 양쪽에 있고 값이 전혀 다르다) 한쪽 박제가
> 다른 쪽 셀에 붙었다. 키에 overlay id 를 넣어 고쳤고 회귀 테스트로 박았다.
>
> **곁가지 — gold 중복키 7건 제거**(CSM 6 = KR0076 2025.4Q 항목1~6 · **PL 1 = KR0087 2025.3Q
> 항목11, 티켓이 몰랐던 건**). 둘 다 뒤 엔트리가 앞을 명시적으로 supersede 하고 있었고 적용이
> last-wins 라 **정합성이 리스트 순서에 걸려 있었다**. 적용 전후 last-wins 축약이 동일함을
> 확인하고 앞 엔트리만 삭제(값 변화 0, diff 는 삭제 56줄뿐).
>
> **곁가지 2 — `public_exports/CSM워터폴.json` 은 이미 동기화됐다**(2,172행 · 값 불일치 **0**).
> 다만 **`public_exports/` 를 읽는 검증기가 여전히 0개**다(`validate_live_artifacts.py` 포함
> grep 0건) — 불변식 1번의 미배선 구멍이라 후속 티켓으로 분리:
> `inbox/validation/20260830T1500Z__validation__MULTI__public_exports_uncovered.md`.
>
> **테스트.** `test_rule_coverage_manifest.py` 에 축 등재(룰 id 대조 · **마스크 칸 수 박제**
> `GOLD_OVERLAY_CENSUS={"CSM":(270,86),"PL":(198,29)}` — tol 을 넓히면 마스크가 부풀어 여기서
> 막힌다 · 박제 완전성 0 · 키 네임스페이스 회귀 · 변이시험 4종 · 훅 배선) 10개.
> `test_identity_registry.py` 에 `GOLD_OVERLAY_DRIFT`(IDENTITY, abs 0.05/rel 0.0) 등재 —
> `test_no_undeclared_threshold_constants` 가 **설계대로 먼저 FAIL 해서** 임계 등재를 강제했다.
> `test_mutation_delegation_is_real` 이 `DECLARED_RULES`(K-ICS 전용)만 봐서 이 축의 정당한 위임을
> "회피" 로 오판 → 그 파일이 선언한 **두 계열**을 보도록 고쳤다.
> `test_push_gate_wiring.py` 에 `check_gold_overlay: WIRED` 등재.
>
> **게이트/훅.** 오프라인 묶음 288 → **299 passed / 1 skipped**. `--selftest` **57/57**
> (inject 모드에서 축이 격리돼 합성 케이스를 오염시키지 않는다). 골든 재생성 **불요**
> (`validate_master_tables` SUMMARY·산출 무변동). **`prepush_check.py` exit 0 · gate-clear.**
>
> **이 축이 여전히 못 보는 것(명문화).** ⓐ LOAD_BEARING 216칸 밑의 빌더 이동 — 그 칸은 애초에
> gold 가 정답이고 빌더는 이미 다르므로 박제하면 파서 개선마다 오탐(C 시뮬레이션으로 확인).
> census 줄이 그 숫자를 매 실행 인쇄한다. ⓑ gold 가 유일 소스인 셀(CSM ROW_ABSENT 12 · NULL 2)의
> **원문 재확인 가능성** — 이 축은 "gold 가 유일 소스" 라고 말할 뿐 그 값이 옳은지는 안 본다.

**(2026-08-30) 폐쇄식이 양쪽 후보를 다 통과시킨 자리를 원문으로 갈랐다. 그리고 gold 오버레이가
83칸을 아무 탐지기 없이 덮고 있다는 걸 census 로 세웠다.**

> 처리: `inbox/validation/20260830T0400Z__orchestrator__KR0079__gold_vs_fixed_builder_adjudication.md`
> → `status: answered`
>
> **① KR0079 2025.2Q 항목4/5 = raw 채택(-685.50 / -992.07), gold(-886.27/-791.3) 폐기.**
> 두 후보의 **합계가 같아** 폐쇄식(항목6=Σ1~5)은 어느 쪽이든 `+0.00` 으로 닫힌다 — 산수로는
> 판별 불가인 자리다. 원문으로 갈랐다: 같은 필링 안에서 **네 표**(연결/별도 CSM 측정요소표 ×2,
> 연결/별도 보험수익표 ×2), 그리고 **1년 뒤 필링(2026.2Q 반기, rcept 20260814004054)의 전반기
> 비교열 두 표** — 총 **6개 독립 표**가 -685.50/-992.07 을 인쇄한다(소급재작성 없음).
> 행 식별은 캡션이 아니라 **IFRS ACODE** 로 했다(라벨 변형에 안 흔들린다).
> gold 값은 원문 어디에도 없다 — 문자열 0회, 상품별·CSM 하위열별 부분합 전수 조합 불일치,
> 연결/별도 동일, 출재 차감(-38.42억)도 아님. owner 답지(`gold/CSM waterfall_미래에셋생명*.xlsx`)는
> **2025.1Q·2025.4Q 만 있고 2025.2Q 는 없다**(두 답지는 raw 와 완전 일치 재현 확인).
> 소수자리 지문: KR0079 gold 27건 중 **-791.3 만 1자리**, `-1677.57 - (-886.27) = -791.30` —
> 구코드 잔차흡수값을 손으로 가른 **plug** 였다.
> **폐쇄식이 못 보는 축 = 개연성**: raw 채택 시 분기 상각 483.70/508.37/539.14억(완만 상승),
> gold 유지 시 483.70/**307.60**/**739.91**억(급락 후 급등). 게이트 귀결: `CSM_AMORT` 잔차
> `+200.77억(25.372%)` → `0.00억`, 등재부 `미래에셋생명보험|2025.2Q`(WATERFALL_SUSPECT) **삭제 대상**.
> 발주 → `inbox/parser/20260830T0700Z` (소수 **2자리** 유지 필수 — 1자리면 폐쇄식 0.1억 어긋남).
>
> **② gold 19건 = 존치, 단 조건부.** 원 티켓의 "코드가 gold 와 오차 0 재현" 은 부정확하다:
> `csm_waterfall_master_diag.json` 은 소수 1자리, gold 는 2자리라 19건 전부 `SAME_AT_1DP`
> (±0.05억)이고 `SAME_EXACT` 는 0건이다. 제거해도 폐쇄식 게이트는 안 깨진다(허용 max(0.1%, 2.0억)) —
> 즉 정밀도 문제가 아니라 **마스크 대 보호** 문제다.
> **`_apply_csm_overrides()`(build_root_masters.py L198-207)는 무조건 UPSERT 만 하고 소스와
> 비교하지 않는다. 전 저장소에서 gold 를 빌더 소스와 대조하는 게이트·테스트는 0건.**
> 전수 census(276): `SAME_EXACT` 28 · `SAME_AT_1DP` 55 · `LOAD_BEARING` 179 ·
> `ROW_ABSENT_IN_SOURCE` 12 · `NULL_IN_SOURCE` 2 → **마스크 후보 83건 / 9개사**(19건이 아니다).
> "지우면 방어막이 사라진다" 는 절반만 맞다 — gold 는 회귀를 막는 게 아니라 **가린다**(화면만
> 지키고 코드는 깨진 채, gold 없는 다음 분기가 깨진 값을 싣는다). 실제로 KR0079 두 결함이
> 2025.2Q~2026.1Q 화면에서 안 보였던 이유가 이것이다.
> 발주 → `inbox/validation/20260830T0710Z` (`GOLD_OVERLAY_REDUNDANT` census YELLOW +
> `GOLD_OVERLAY_DRIFT` RED 배선). **배선이 거부되면 그때는 제거가 옳다.**
>
> **③ 곁가지 2건.** gold `set` **중복 키 6건**(KR0076 2025.4Q 항목1~6) — 의도된 supersession
> 이지만 last-wins 라 **리스트 순서에 정합성이 걸려 있다**(앞 6건은 `why` 공란, `note` 만).
> `public_exports/CSM워터폴.json` 이 루트 마스터보다 **뒤처짐**(KR0079 2025.2Q 항목1 `값_당분기`
> public 20840.7 vs 루트 20847.3) — 지금 **게이트가 보는 파일 ≠ 사용자가 보는 파일**이다.
>
> **baseline 재현**: `validate_data_contract.py` → **RED=0 YELLOW=93 exit 0**.
> 마스터·gold·등재부 바이트 무변경(판정만, 실행은 발주).
> 재현 스크립트 4종: `scripts/_probes/probe_20260830_val_{raw_csm_table_scan,raw_csm_html_scan,
> kr0079_2025q2_adjudication_sim,gold_vs_source_census}.py`

**(2026-08-29 e) `PL_BRIDGE` 의 pass 절반 이상이 구성상 참이었다 — 이제 게이트가 그 사실을 인쇄한다. item22 는 메웠다.**

> 처리: `inbox/_resolved/20260829T2130Z__validation__MULTI__pl_eqs_constructive_tautology.md`
> → `status: resolved` (owner 가 제안 1·2·3·4 승인)
>
> **문제.** 빌더가 우변의 한 항을 좌변에서 빼서 만들기 때문에(`item7 = 3−(4+5+6)` ·
> `item12 = 8−(9+10+11)` · `item18 = 17−19` · `item21 = 22−20` · `item23 = 22−24`) 그 등식들은
> **산수상 깨질 수가 없다.** `pass=3057` 중 **1,608(52.6%)이 그런 pass** 다. CONSTRUCTIVE
> 변이시험(그 칸을 흔들고 빌더가 계산하는 하류 항을 빌더와 똑같이 재계산) 실측 탐지율:
> item5·6·9·10·11·19·22·23 **전부 0.0%** — `validate_master_tables` + `validate_data_contract`
> 를 다 물려도 신규 RED 0 건이었다.
>
> **① 명문화.** `PL_EQ_EVIDENCE`(등식별 `REAL`/`TAUTOLOGY`/`PARTIAL` **상수** — 주석이 아니라
> 게이트가 읽는 값) 신설 + `_assert_pl_eq_evidence_declared()` 가 import 시점에 판정 없는 등식을
> 죽인다. SUMMARY 인쇄 `pl_bridge:3057P/…` → **`pl_bridge:3057P(진짜1135·구성상1608·부분314)/…`**.
> 본문에 등식×증거력 pass 표와 `NOEQ`(등식으로 영원히 못 보는 항목) 건별 인쇄 추가.
>
> **② item22 배선.** 게이트 2f `TAX22_SOURCE_CROSSCHECK` = `|item22−item24| == |원천 법인세
> 계정|`(`ifrs-full_IncomeTaxExpenseContinuingOperations`). 그 값이 418/418 FS-API 캐시에
> 있는데 `assemble()` 이 곧바로 잔차로 덮어써서 버려지고 있었다. 부호는 안 본다(발행사 관행이
> 갈리고 그게 애초에 plug 를 도입한 이유). **전 버킷 시뮬레이션 선행**: 대조가능 282 · PASS 282 ·
> FAIL 0, 잔차 median=p90=max **0.000백만원**. 배선 후 게이트 `tax22_src:282P/0F/74S` 로 동일.
> 변이시험 탐지율 **0.0% → 100.0%**(282/282).
> **오프라인·결정적**으로 만든 것이 핵심이다 — `resolve_corp()` 는 gitignore 된 30MB
> `CORPCODE.xml` 을 읽고 없으면 **네트워크로 받아** 환경마다 커버리지가 갈린다. 그래서 추적
> 파일만 쓴다(`data/_derived/alotmatter_fetch_census.json` 39/39 + 추적된 `_fs_api_cache/`),
> 두 매핑이 **36/36 일치 · 불일치 0** 임을 실측했다. 캐시 파싱은 `fetch_dart_fs._parse` 를
> **그대로 호출**한다(재구현하면 게이트가 빌더와 다른 값을 본다).
>
> **③ 매니페스트 박제.** `tests/test_rule_coverage_manifest.py` 에 PL 축 신설 —
> `PL_CONSTRUCTIVE_BLIND`(5·6·9·10·11·19·23 무검사) · `PL_CONSTRUCTIVE_GUARDED`(3·4·8·17·20·
> 22·24·25) · `PL_DOWNSTREAM`(빌더 plug 재계산 표, 소스 문자열로 대조). 검사면 = PL 을 읽는
> 차단성 룰 전부(PL_BRIDGE·TAX22·CSM_AMORT·COVERAGE·data-contract RED). **매니페스트 자신의
> 변이시험 3종 전부 발화 확인**(`probe_20260829_pl_manifest_falsifiability.py`) — 선언이 면제가
> 아님을 기계가 증명한다. `-k pl_` 18 passed / 19.5초.
>
> **④ item9 판정 = 대안 축 없음.** `CSM_waterfall.json` 은 2,172행 **6항목 단일 축**이고
> **출재 항목 0** 이다. `build_csm_waterfall_master.py` 가 `_EXCLUDE_KW`·캡션 필터·소수 클러스터
> drop 으로 전 단계에서 배제하고, **그 배제는 옳다**(출재는 보유 재보험계약자산의 별도 워터폴 —
> `원수+재보험` 식은 346버킷 중 245건이 ±1% 밖, `원수+수재`는 20건). 즉 `CSM_AMORT_PL_LEGS` 를
> 넓히는 방식은 답이 아니다. 원문에는 있으므로(캡션 "원수 및 출재 …") **파서가 출재
> rollforward 를 별도 마스터로 추출**해야 하고, 그건 신규 과제라 발주하지 않고 명문화만 했다.
>
> **⑤ `test_identity_tautology.py` 를 PL 에 배선하지 않는다 — 그 결론도 명문화.** 귀무모형이
> 각 항이 등식 단위로 반올림됐다고 가정하는데 PL 마스터는 원÷1e6 이라 **건전한 항등식도 잔차가
> 정확히 0** 이다. 실측 9축 전부 RED 이고 excess 1위(1.93)가 하필 진짜 검산 축인 EQ9 였다.
> "배선을 잊었다"가 아니라 **"이 탐지기는 이 마스터에서 작동하지 않는다"** 가 결론이고, 그 파일
> docstring 에 절로 남겼다.
>
> **골든/게이트.** `master_tables_golden.json` `--update`(SUMMARY 한 줄, exit_code 2 불변).
> `test_identity_registry.py` 에 `tax22_source_crosscheck` 등재 — 그 파일의
> `test_no_undeclared_threshold_constants` 가 **설계대로 즉시 실패해서** 등재를 강제했다.
> `validate_golden_input_fingerprints` **갱신 불요**(RED=0, 6 spec ok — SPECS 의 `code_entries`
> 는 빌더만 추적하고 게이트는 골든이 매 실행 서브프로세스로 재실행해 stale 불가).
> `validate_data_contract` RED=0 YELLOW=92 **불변**. 훅 경로 확인: `validate_master_tables` 는
> `test_master_tables_golden.py` 경유(NOT_A_PUSH_GATE 선언대로), `test_rule_coverage_manifest.py`
> 는 이미 훅 목록 L169.
>
> **잔여(이 티켓 밖).** ⓐ item5·6·9·10·11·19·23 은 여전히 무검사 — plug 제거는 owner 결정
> (2026-06-08) 사안이라 제안까지만. ⓑ 출재 CSM rollforward 추출(parser/ifrs17 신규 과제).
> ⓒ tax22 SKIP 74버킷(FS-API 캐시 없음 56 + 22/24 결측 18)의 item22 무검사.

**(2026-08-29 d) 어제 신설한 leg-coverage 룰이 코리안리재보험 12분기를 오탐했다 — 데이터가 아니라 **등식**이 틀렸다.**

> 처리: `inbox/_resolved/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md` → `status: resolved`
>
> **오탐 구조.** 룰은 "item13(자동차) 결측이 1,456~53,464백만원을 싣고 있다"고 12분기 내내
> 찍었다. parser 가 전 분기 원문 XML 을 grep 한 결과 **자동차 LOB 자체가 없다**(재무제표 표
> 안에 "자동차" 0회 — 걸린 것은 전부 관계기업 펀드명·임원 이력 문장). 코리안리는 재보험사라
> LOB 이 생명/장기/일반이고, 네 번째 다리인 item`2-1`(장기재보험 손익)이 마스터에 정상
> 발행돼 있는데 **검증 등식만 표준 3슬롯(2/13/14)이 LOB 의 전부라고 가정**했다.
> **빌더의 Tier-2 RC 게이트는 같은 항을 이미 `_extra_lob` 으로 더하고 있었다**
> (`build_pl_breakdown.py` L249-252) — 즉 빌더와 검증기가 서로 다른 등식을 쓰고 있었다.
> 이 저장소의 "게이트가 검사하는 것 ≠ 실제 계약" 사고의 한 변종이다.
>
> **조치(회사 하드코딩 아님).** `load_pl_extra_lob()` 신설 → 항목번호 패턴 `^2-\d+$` 를 ΣLOB
> 에 가산. 회사명으로 박으면 다음 재보험사에서 같은 사각이 조용히 재발한다. 자식
> `3-N`~`12-N` 은 그 다리의 하위 분해라 미가산(이중계상 방지).
>
> **실측(코드 수정 전 356 버킷 전수 시뮬레이션 → 수정 후 게이트, 정확히 일치).**
> `2e LEG-COVERAGE 닫힘 18→30 · 깨짐 34→22 · 좌변없음 18 불변`,
> `pl_bridge 3045P/47F → 3057P/35F` (468S·0NEW 불변). **새로 깨지는 버킷 0건.**
> 코리안리 12분기 잔차 |≤2.8|백만원(lhs 5만~24만 백만원 → 상대 ~0.001%).
> 재현: `scripts/_probes/probe_20260829_extra_lob_simulation.py`.
>
> **하이픈 서브 LOB census (이 라운드의 최대 산출).** 마스터의 하이픈 항목번호는
> **코리안리재보험 단독**, 11종(`2-1`~`12-1`) × 14분기 = **154셀**(루트·viz 동일, 항목명
> 충돌 0). 그런데 **그중 어떤 룰이라도 읽던 것은 `4-1`(수재 CSM상각, `CSM_AMORT_PL_LEGS`)
> 14셀뿐이었다 — 나머지 10종 140셀은 어떤 룰도 순회하지 않았다.** `2-1` 배선 후 남은
> 무검사는 9종 126셀. 재현: `scripts/_probes/probe_20260829_hyphen_lob_census.py`.
>
> **그 126셀의 부모-자식 3식은 일부러 배선하지 않았다 — 동어반복이다.**
> `2-1=3-1+8-1` · `3-1=4-1+5-1+6-1+7-1` · `8-1=9-1+10-1+11-1+12-1` 은 14/14 통과지만
> **잔차가 전건 정확히 0.000000000** 이다. `pl_breakdown/companies.py::leg()` 가 item7·12 를
> plug 로, item2 를 합으로 만들기 때문에 구성상 참이라 영원히 발화하지 않는다. 배선했으면
> 126셀이 GUARDED 로 보이면서 실제로는 아무것도 검증하지 않는 **false-green 을 내 손으로
> 만드는 것**이었다. 무검사로 두되 무검사임을 기록하는 쪽을 택했다(아래 census + 등재부).
> 재현: `scripts/_probes/probe_20260829_hyphen_tautology.py`.
>
> **미지 하이픈 census 배선 + 변이시험.** 등식이 아는 형태(`2-N` 가산 / `3-N`~`12-N` 자식)
> **밖의** 항목번호가 나타나면 2e 가 `LEGUNK` 로 건별 인쇄한다(오늘 0건). "0건" 이 "검사가
> 죽었다"가 아님을 보이려고 변이시험을 붙였다 —
> `scripts/_probes/probe_20260829_legunk_mutation.py` 5케이스 전부 PASS(`2-1` 가산 / 자식
> 미가산 / 가짜 `13-1` 발화 / `2-1`+`2-2` 복수 부모 / 정수 항목번호 무영향).
>
> **baseline.** `data/_gold/pl_bridge_baseline.json` 에서 코리안리 12건 삭제(`_promote` (1),
> 게이트가 `FIXED?` 로 인쇄). entries **47→35**, `등재부에만 남은 것 0`. `_counts` 도 실제
> entries 로 재계산(선언 52 vs 실제 47 로 이미 드리프트해 있었다). 데이터 결함이 아니었으므로
> documented exception 승격이 아니라 **삭제**다.
>
> **골든/지문.** `tests/fixtures/master_tables_golden.json` `--update`(SUMMARY 한 칸,
> exit_code 2 불변). 오프라인 484 passed/1 skipped. `validate_data_contract` RED=0 YELLOW=92
> (불변). **`validate_golden_input_fingerprints.py` 는 갱신 불요** — RED=0, 6 spec 전부 ok.
> 그 게이트의 SPECS 는 **빌더**만 `code_entries` 로 추적하는데 이번에 고친 것은 게이트
> (`validate_master_tables.py`)이고, `test_master_tables_golden.py` 는 매 실행 게이트를
> 서브프로세스로 재실행하므로 구조적으로 stale 해질 수 없다(그래서 SPECS 에 없는 게 맞다).
>
> **잔여 LEGRED 22건** — 전건 baseline 등재(`route: parser/ifrs17`, `deadline: 2026-10-31`,
> 신규 0). 예별손해 2024.4Q·2025.4Q item2(후보 표까지 특정했으나 폐쇄식 불일치로 미확정) ·
> AIG 3분기 · 신한이지 2분기(원문에 LOB 분해 표 자체가 없음, parser 재확인) · 2023 다수
> (사이트 비노출, 미착수).
>
> **곁가지(미조치, 기록용).** 같은 두 식을 **전 회사**로 돌리면 `3=4+5+6+7` 315건 중
> 284건(90.2%) · `8=9+10+11+12` 300건 중 258건(86.0%)이 잔차 정확히 0 이고 최대 잔차가
> 0.35·0.49백만원 = floor(200백만)의 1/400 이다. 이 두 식은 코리안리만이 아니라 저장소
> 전반에서 **거의 동어반복**으로 보인다. `2=3+8` 은 최대 잔차 10,169백만원이라 내용이 있다.
> 별도 조사 대상.

**(2026-08-29 c) 분기 지평 하드코딩 — 게이트가 최신 분기(2026.2Q)를 순회조차 안 했다. `RED=0` 이 "안 봤다"였다.**

> 처리: `inbox/validation/20260829T1910Z__orchestrator__MULTI__qs_ends_at_2026q1.md` → `status: answered`
> 신규 발주: `inbox/parser/20260829T2010Z__validation__KR0005_2026.2Q__pl_lob_legs_missing.md`
> (`lane: ifrs17` · `route: reparse`) — **현재 push BLOCKED (RED=1)**
>
> **원인 = 하드코딩, 그것도 세 곳.** `validate_master_tables.QS` 는 이 파일 **최초
> 커밋(`9243445`)부터** `2026.1Q` 로 끝나는 리터럴이었고 아무도 안 늘렸다. 같은 병이
> `validate_data_contract._DISPLAY_QUARTERS`(census RED 발화 스코프)와
> `validate_kics_rate_sensitivity.ALL_Q`(RS4 census)에도 있었다. `validate_master_tables`
> 안에는 **두 번째 지평**까지 따로 있었다 — `FY_Q["2026"] = ["2026.1Q"]` 라 연속성 검사도
> 2026.2Q 를 안 봤다.
>
> **자물쇠가 직렬 두 개였다.** `_DISPLAY_QUARTERS` 만 열면 델타 **0** — IFRS17 hole 은
> `validate_master_tables.coverage_holes`(→ 그쪽 QS)를 통해 오기 때문이다. 둘 다 열어야
> RED 이 나온다. 게이트 하나만 보고 "열었다"고 하면 안 된다.
>
> **아는 사람이 있었는데 정본을 안 고쳤다.** `validate_data_contract` 안의 두 검사(배당·CSM
> 연속성)는 주석에 "`_DISPLAY_QUARTERS` 는 2026.2Q 를 아직 포함하지 않는다"고 **적어 놓고
> 자기만 스코프를 비켜갔다.** 개별 우회가 재발 구조 자체였다.
>
> **실측(지평에 2026.2Q 넣기 전/후).**
> `validate_master_tables --no-build` SUMMARY: `coverage_hole 0PL→1PL` ·
> `qoq_warn 211Y→235Y` · `oci_vs_bs_aoci 13Y→14Y`. `plausibility`(dup/spike/cont/wfy/zamort)는
> 변화 0. `validate_data_contract` SUMMARY: `RED 0→1` (YELLOW 92 불변).
> 유일한 RED = **`MASTER_HOLE 흥국화재 2026.2Q`** — PL 항목 2/8/12/13/14 결측인데 직전
> 2026.1Q 는 다섯 항목 전부 정상 = 최신 분기 회귀. raw 는 디스크에 있고 라벨 빈도도 2026.1Q
> 와 같다 → refetch 아님, parser(ifrs17) 발주.
>
> **조치 = 파생.** `scripts/_quarter_horizon.py` 신설(하한 `2023.1Q` 고정, 상한은 마스터 5개의
> `공시분기` high-water mark). **여러 마스터의 max 를 쓰는 이유** — 한 마스터에서만 파생하면
> 그 마스터가 최신 분기를 통째로 빠뜨렸을 때 지평도 같이 줄어 결측이 안 보인다(자기참조 사각).
> `display_quarters()` 는 owner 스코프 규칙(연말 전부 + 2025.1Q 이후 전부)을 파생하며
> 종전 7개를 정확히 재현한다(회귀 가드 테스트 있음).
>
> **트립와이어 배선.** `tests/test_quarter_horizon.py` 신설 → `prepush_check.py` 오프라인
> 테스트 목록에 등록(배선 안 하면 또 honor-system). 변이시험 확인: QS 를 옛 리터럴로 되돌리면
> 2건 FAIL(`test_gate_horizon_includes_latest_quarter` + `test_no_gate_retypes_the_quarter_horizon`).
>
> **다른 게이트 census(AST, 주석·독스트링 제외).** 지평형 하드코딩은 위 3곳뿐. 나머지 게이트
> 8개는 데이터 파생(`validate_kics_disclosure` 의 `quarters = sorted(by_q)` 등)이고, 남은 분기
> 리터럴은 전부 **(회사, 분기) 예외 등재부**라 지평이 아니다. `validate_kics_disclosure.SPOT_QUARTER`
> 도 단일 spot-check 앵커. 재현: `scripts/_probes/probe_20260829_gate_horizon_audit.py`.
> 미조치(게이트 아님, 기록용): `scripts/_csm_goldmap.py` L20 · `scripts/_csm_status_matrix.py` L29
> 가 `QS = [q for q in QS if q != "2026.2Q"][:13]` 로 **2026.2Q 를 명시적으로 배제**한다 —
> 리포트 헬퍼라 push 를 막지 않지만, 그 리포트를 근거로 판단할 때는 최신 분기가 빠져 있다.
>
> **골든/지문.** `tests/fixtures/master_tables_golden.json` `--update` 재생성(위 SUMMARY 3칸
> 이동, exit_code 2 불변). `validate_golden_input_fingerprints.py` 는 **갱신 불요** — 빌더를
> 안 건드렸고 실행 결과 RED=0.

**(2026-08-29 b) 보험손익 leg-coverage 신설 — "등식이 없다"가 아니라 "등식이 결측을 만나면 도망갔다".**

> 처리: `inbox/validation/20260829T1500Z__orchestrator__MULTI__insurance_result_closure_missing.md`
> → `status: answered` (**발주 전제를 뒤집었다 — 오케스트레이터 재확인 필요**)
> 신규 발주: `inbox/parser/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md`
> (`lane: ifrs17` · `route: reparse` · 40셀)
>
> **발주 전제는 틀렸다.** `1 = 2+13+14+15−16` 은 `PL_EQS` 밖 dual-form 블록에 **파일 최초
> 커밋(`135e6ff`)부터 있었고**, 그 실패 10건은 이미 `pl_bridge_baseline.json` 에 등재돼 있다.
> KB손해도 "item16 전 분기 None" 이 아니라 14분기 중 6분기만 None 이고, 2025.4Q 잔차는
> 1억이 아니라 **정확히 0.0**(억원 반올림 착시).
>
> **그런데 결론은 맞았다 — 원인이 달랐다.** 진짜 사각은 **결측 시 통째 SKIP**:
> `if bo is None or any(x is None for x in lob): pb_skip += 1` 이 356 버킷 중 **71(19.9%)**
> 을 무검사로 넘겼다. 게다가 coverage census 의 `key_items` 는
> `보험손익/생명장기손익/당기순이익` 셋뿐이라 **13(자동차)·14(일반) 결측은 세지도 않는다** —
> 두 검사가 같은 구멍을 공유했다.
>
> **실측(전 버킷 356).** SKIP 71 을 0-fill 로 재판정: **13 닫힘 / 40 깨짐 / 18 좌변없음**.
> 깨진 40건 잔차 median 43,415 · max 454,352 백만원, **합계 3.4조원이 어떤 룰의 시야에도
> 없었다**(2024+ 22건). 그중 **30건은 coverage census 도 구조적으로 못 잡는다.**
> 대표: **코리안리재보험이 13분기 내내 `item13` 없이 두 검사를 모두 통과**했고(형제 다리
> `item14` 는 정상 추출), 0-fill 로 재보면 2024+ 10분기가 전부 안 닫힌다(최대 4,105억).
>
> **조치 — 새 등식이 아니라 결측 처리 확장.** 등식을 한 벌 더 만들면 같은 식이 두 개가 된다.
> dual-form 의 결측 분기만 고쳐 **결측 LOB 다리를 0 으로 채워 판정**한다:
> 닫히면 PASS(그 다리는 정말 0), 깨지면 FAIL(잔차 = 미검사 금액의 하한).
> 라벨 `보험손익(leg-coverage)`. **결측을 SKIP 도 무조건 RED 도 아닌 "산수로 판정"으로 바꾼
> 것**이 요점이다 — 13건은 실제로 정확히 닫히므로(NH농협손해 12분기 ±1.0 이내) 무조건 RED 는
> 정당한 0 을 결함이라 부르는 두더지가 된다.
> `item1`(좌변) 결측 18건은 등식 성립 불가라 FAIL 로 안 올리되 `NOLHS` 로 건별 인쇄하고,
> 오늘 전건이 2023 분기이므로 **2024+ 가 뜨면 회귀 경고**를 찍는다.
>
> **적용 전 시뮬레이션 = 회귀 0건.** 오늘 검사받던 285 버킷 판정이 한 건도 안 바뀐다
> (`scripts/_probes/probe_20260829_item1_legcoverage_final.py` 가 old/new 대조).
> 0-fill 경로에 기타영업수익/기타사업비용 후보를 **추가하지 않았다**(masking 면 확대 방지,
> 실측상 불필요 — 13건 전부 기존 adj 로 닫힘).
>
> **게이트 실측.** `pl_bridge:3025P/13F/522S/0NEW` → `3038P/53F/469S/0NEW`.
> `exit=2` 는 전후 동일(기존 미종결 실패). 드러난 40건은 `pl_bridge_baseline.json` 에
> **건별** 등재(13→53, 기한 2026-10-31) — 통째 skip 이 아니고 F 로 계속 계상된다.
> 마스터 데이터는 한 셀도 안 건드렸다.
>
> **훅 배선 확인.** `prepush_check.py` 는 `validate_master_tables.py` 를 직접 안 부른다 —
> 강제점은 `tests/test_master_tables_golden.py`(SUMMARY+exit 박제)이고 그것은 훅 `fast`
> 묶음 **L167 에 실제로 있다**. `tests/test_identity_registry.py` 도 **L179 에 있다**(허용오차를
> 몰래 넓히면 `tol_from` 대조에서 막힌다). `test_rule_coverage_manifest.py` 는 K-ICS 전용이라
> PL 축이 없어 손대지 않았다. 지문 게이트는 빌더 전용이라 `--update` 불요(`RED=0 → clear` 확인).
>
> **남은 사각(별도 판단 요망).** `validate_master_tables.QS` 가 `2026.1Q` 에서 끝나 **2026.2Q
> 24버킷**을 `QS` 기반 검사(coverage census · qoq_scan · net_quarterly)가 통째로 안 본다.
> PL_BRIDGE 는 `pl.items()` 를 직접 돌아 무관(그래서 코리안리 2026.2Q 도 잡혔다). `QS` 확장은
> 여러 룰 판정을 동시에 움직여 전 버킷 재시뮬이 필요하므로 이 티켓에서 손대지 않았다.

**(2026-08-29) 골든 입력지문 게이트 배선 완료 — 빌더 재실행 골든 6개 중 훅이 돌리던 것은 1개뿐이었다.**

> 처리: `inbox/validation/20260829T0300Z__orchestrator__MULTI__golden_input_fingerprint_gate.md`
> → `status: answered` (오케스트레이터 확인 필요 — 운영 계약 1건 전파 + 무관 RED 1건 보고)
>
> **사고 배경.** `tests/test_ifrs17_bs_golden.py` 는 빌더를 통째로 재실행해 **실측 492·514초**라
> 훅 예산(~5분)을 넘어 오프라인 묶음에서 빠져 있었다. 그 사각으로 2026-08-26 삼성생명 OFS
> 캐시 정정(8c1666b)이 BS 마스터에 반영 안 된 채 **이틀간 미검출**됐다. `CLAUDE.md` 골든 표의
> "~2분" 추정이 4배 이상 틀렸던 것이 그 제외 결정의 근거였다 —
> `prepush_check.py` 주석에도 같은 오추정이 남아 있어 실측치로 정정했다.
>
> **신설.** `scripts/validate_golden_input_fingerprints.py` — 빌더를 **안 돌리고**
> 입력·코드·산출 3축(+fixture) 지문만 대조해 "마스터가 자기 입력보다 낡았는가"를 판정.
> in-process **3.0~3.15초**. 입력 경로는 추정이 아니라 **런타임 트레이스**로 확정했고
> (`scripts/_probes/probe_20260829_trace_builder_reads.py`, 박제:
> `tests/fixtures/builder_read_traces/`), `tests/test_golden_input_fingerprint.py` 가
> 선언이 관측치를 덮는지 매 push 마다 대조한다. 그 대조가 `src/__init__.py` 와
> `data/ifrs17/table_scoring_keywords.yaml`(import 두 단계 아래 lru_cache) 누락을 실제로 잡았다.
> **무거운 골든은 그대로 둔다 — 지문은 대체가 아니라 층이다.**
>
> **이번에 발견한 구멍.** 지문 게이트는 훅에 걸렸는데 그 **매니페스트 테스트가 오프라인
> 묶음에 없었다.** 게이트만 걸고 매니페스트를 안 돌리면 SPECS 를 좁히는 변경이 무저항
> 통과한다 — "배선했다 ≠ 강제된다"의 재발이다. 묶음에 추가하고,
> `test_this_manifest_itself_runs_in_the_push_hook` 으로 자기 등재를 자기가 검사하게 했다.
>
> **재현.** `data/dart/extracted/` 에 스크래치 파일 1개를 넣어 입력을 현실측으로 흔들었더니
> `git push --dry-run` 이 `골든 입력지문=FAIL` → `PUSH BLOCKED — exit=2` → `error: failed to
> push some refs` 로 막혔다(448초). 삭제 후 `RED=0 → clear`.
>
> **운영 계약(두 파서 레인에 전파 요망).** 마스터를 정당하게 재빌드하면 골든 `--update` 뒤에
> `validate_golden_input_fingerprints.py --update` 도 같이 돌려야 한다. 실제로 이번 세션에
> ifrs17 레인의 동시 재빌드로 `[pl_breakdown] FIXTURE_MOVED` RED 이 났다(정상 동작).
>
> **커밋 `0ebb0ca`** (14 files, +5,126/-4).
>
> **배선 직후 야생에서 첫 건을 잡았다.** 커밋 직후 재실행에서
> `[viz_ifrs17_panels] CODE_MOVED + FIXTURE_MOVED` RED 2건 — 파서 레인이
> `scripts/viz_build_ifrs17_panels.py` 를 고치는 중이다(`inbox/parser/20260829T0200Z...
> csm_amort_asof_placeholder`). **빌더 코드가 움직이면 입력이 그대로여도 마스터는 낡는다** —
> 종전에는 이 축을 보는 것이 8분짜리 골든뿐이라 훅에서 안 돌았다. 남의 in-flight 변경을
> 내가 `--update` 로 축복하면 그게 false-green 이라 **RED 을 일부러 남겨 뒀다.**
>
> **미해결(내 작업과 무관) 2건 — 둘 다 push 를 계속 막는다.**
> ① `[PL_breakdown] PL_YTD_COLLAPSE_TO_ZERO 에이비엘생명보험 2024.4Q`
>   (`inbox/parser/20260828T2100Z...KR0070` 진행 중)
> ② 위 `viz_ifrs17_panels` 지문 RED (그 빌더 변경을 랜딩하는 쪽이 골든 통과 후 지문 `--update`)

**(2026-08-26 b) 🔴 prepush exit 2 · gate RED=1 YELLOW=92 — BLOCKED, 그리고 이게 맞는 상태다.**
**오케스트레이터가 요청한 documented exception 을 등재하지 않았다. 등재했으면 거짓 면제였다.**

> 처리: `inbox/validation/20260826T2000Z__orchestrator__MULTI__pl_amort_crosscheck_blindspot.md`
> → `status: answered` (원 sender 재확인 필요 — 판정을 뒤집었다)
> 신규 발주: `inbox/parser/20260826T2200Z__validation__KR0049_2023.4Q__axa_tier2_header_empty.md`
> (`lane: ifrs17` · `route: reparse`)
>
> ### ① 면제 요청을 반려했다 — "어느 DART 문서에도 없다" 가 틀렸다
>
> 악사손해 2023.4Q `PL_CSM_AMORT_VS_WATERFALL` RED 은 **진짜 추출불가가 아니다.** 값은 이미
> 받아 놓은 감사보고서 첨부 안에 있다 — `20240402002008_00760.xml` 의
> `'(5) 보험손익 상세내역'` 표, `당기손익으로 인식한 보험계약마진 금액 · 장기 = 22,272,512천원`
> = **222.7억** = 게이트가 인쇄하던 그 워터폴 상각액. 2024.4Q 는 같은 표(`'(6) ...'`)로 추출에
> **성공**한다. 선행 티켓들이 판별식으로 쓴 `계약유형별` 은 **양쪽 다 0회**라 애초에 아무것도
> 증명하지 않는 키워드였다(성공하는 2024 필링에도 0회).
>
> 근본원인까지 특정 — `companies.py::extract_tier2_axa` 가 `for hr in note.header:` 로 도는데
> 2023 필링은 `t.header == []` 이고 컬럼 헤더행이 `t.rows[0]` 안에 들어온다 → `col` 이 None →
> `return {}`. 2차 결함: 섹션 라벨 `재보험수익`/`재보험비용`(2023) vs `_AXA_SEC` 의
> `출재보험수익`/`출재보험비용`(2024). parser 티켓에 기대값 13셀 + 정합식 3개를 붙여 발주.
>
> **교훈: 키워드 0회는 원천 부재의 근거가 아니다.** 성공 사례에서 판별기를 먼저 교정하고 세라.
>
> ### ② 사각 12건 — 커버리지 룰 `3z-b` 신설
>
> 룰 3z 가 `for (co,q) in env.pl` 이라 **PL 버킷이 통째로 없으면 방문조차 못 해 완전 침묵**했다.
> `env.wf` 쪽에서도 한 번 더 도는 census 를 배선(`check_cross_source` 3z 바로 뒤). 신규 결손은
> RED, 기존 12건은 `data/_gold/pl_amort_coverage_baseline.json` 에 **건별 열거 + 워터폴 상각
> 박제**로 비차단. 버킷이 생기면 `_INERT`, 박제가 흔들리면 `_DRIFT` RED — 매 실행 재검산한다.
> 전 버킷 시뮬레이션 + 변이 6종 ALL PASS(`probe_20260826_coverage_rule_simulation.py`),
> selftest 57/57(종전 55, `L3`/`L4` 신설 · `M1` 픽스처 격리 보정).
>
> **삼성화재 2023.1Q(워터폴 상각 3,760.4억)는 진짜 구멍으로 확정**했다 — raw 에
> `'(10) … 주요 보종별 보험수익 및 재보험비용의 내역 · 1) 제74(당)기 1분기'` 의
> `보험계약마진 상각 376,038백만원` 이 있다. 나머지 11건은 **판정 보류(`UNADJUDICATED`)** —
> 내 노트 판별기가 대조군 7건 중 5건 위음성이라 "원천에 없다"고 말할 근거가 없다.
>
> ### 다음 행동
>
> parser(ifrs17)가 `extract_tier2_axa` 헤더 폴백을 넣고 PL 골든을 `--update` 로 재생성하면
> RED 이 0 이 된다. 그 뒤 재검증 요청할 것. **그 전에는 push 하면 안 된다.**

## Status (이전 라운드)

**(2026-08-26 a, answered 4건 재확인) 🟢 4건 전부 종결(resolved) · prepush exit 0 ·
RED=0. 마스터 JSON 은 한 셀도 안 고쳤다. 고친 것은 내 소유 게이트 2곳 + 등재부 2종이다.**

> 종결: `inbox/_resolved/20260825T1520Z`(CSM 상각 항등식) · `20260825T1120Z`(PL bridge) ·
> `20260825T0800Z`(단위판별) · `20260825T1415Z`(IR 기준 판정, `escalate` 해제)
> 신규 발주: `inbox/parser/20260826T0500Z`(별도 복원 잔여 3건)
>
> ### 이번에 잡은 것 — 게이트 두 곳이 자기가 잡으라는 것을 못 잡고 있었다
>
> **① IR 교차검증 축은 발화하는데 눈이 멀어 있었다.** 파싱본 6개가 들어와
> `csm_steps_dart_vs_ir` 이 36 step-pair 를 실제로 대조하기 시작했다(종전 "IR JSON 미납품,
> SKIP"). 실측 잔차는 전건 |Δ| ≤ **0.055억**인데 허용오차는 `max(5%, 100억)` — **1,700배**
> 넓었다. 그래서 커밋 `8a3b930` 의 연결 누출(6항목 Δ 69.6~1,043.9억)을 **0/6 으로 놓친다.**
> `max(0.5%, 1.0억)` 로 조였다(live RED 0 · leak 6/6 검출 · worst Δ/tol 0.0188).
> `IR_STEP_TOL_REL`/`IR_STEP_TOL_ABS_EOK` 를 모듈 상수로 빼고 `test_identity_registry.py`
> `tol_from` 에 배선 — 앞으로 몰래 넓히면 테스트가 막는다.
>
> **② PL 생명장기 등식이 발행사 표의 세 번째 다리를 안 보고 있었다.** 교보라플·BNP카디프
> 3건은 데이터가 아니라 룰의 갭이었다. raw(교보라플 `20250328001411_00760.xml`, 단위 원):
> Ⅰ.보험손익 = 보험영업수익 − 보험서비스비용이고 그 비용 안에 **(3)기타사업비용**이 원수·
> 재보험과 나란히 들어 있다 → `item2 = item3+item8−item16` 이 **원 단위까지** 닫힌다.
> `PL_EQ_ADJ` 로 adj 후보를 주고, 전 버킷 시뮬레이션(3 닫힘 · **파손 0** · 잔존 0) 후 반영.
>
> **③ 원장이 두 시간 만에 화석이 됐다.** parser 답변이 박제한 `pinned=22 stale=0` 은
> `b2293c8` 시점 값이고, 같은 레인의 `8c1666b`(PL 별도 정정)가 **11건을 저절로 닫았다**
> — 실측 `pass=335 pinned=11 stale=11`. FIXED 11줄 삭제 + 남은 삼성생명 5분기 note 에
> "고칠 대상은 PL 이다" 명시. YELLOW 96 → 85.
>
> ### 재확인에서 갈라진 판정 (전부 raw 로 직접 잼)
>
> - **삼성생명·신한라이프 84셀 별도 복원 = 확인.** 3-way 대조(8a3b930^ / 8a3b930 / 현재):
>   값 84셀 · 2개사, 한화생명·현대해상 0셀.
> - **교보생명 미복원 = 옳다. 단 사유가 틀렸다.** parser 는 "연결/별도 축이 아니라 당기/전기
>   버그" 라고 했는데 raw 는 정확히 연결/별도다 — `20230515002764.xml` 에서 버린 105,807 은
>   **연결재무제표 주석**(line 19282), 채택한 104,567 은 **재무제표 주석=별도**(line 38283).
>   이 회사는 문서 순서가 연결 먼저라 구코드가 연결을 집고 있었고, **코드가 아니라 gold
>   override 로만** 고쳐졌다 → 픽커는 여전히 이 회사에서 연결을 선호한다.
> - **코리안리 판정불가 = 맞다.** PL 과 맞는 값(70,611 / 92,311)이 연결·별도 **양쪽 절에 같은
>   숫자로** 인쇄돼 있다(재보험사라 이 줄의 연결효과 0). basis 로는 못 가른다.
> - **gold `set` 30셀 제거는 반대.** `csm_waterfall_master_diag.json` 이 **2026-08-17** 로
>   stale 해서 옛 1000배 값(AIG 928,075.0 등)을 그대로 들고 있다. 지금 지우면 다음
>   `build_csm()` 에서 그대로 되돌아간다. diag 재생성(owner 승인) → 삭제 → 산출 동일 확인 순서.
>
> ### 아직 확인 못 한 것 (후속 티켓 `20260826T0500Z`)
>
> ① 삼성생명 item3/item4 **10셀**이 복원 전 값과 다르다(이자부리 최대 +70.1억). item3+item4 가
> 정확히 상쇄돼 항등식은 안 깨지지만 **어느 원천으로도 확인이 안 된다**(워터폴이 3블록 합이라
> 단일 인쇄값 대조 불가, IR 은 그 5분기를 안 덮는다). parser 답변의 "8a3b930^ 와 일치" 는 틀렸다.
> ② 삼성생명 PL **5분기가 아직 연결**(2026.2Q 는 IR 로 확증) — 반기 필링 전부 + FY2024 분기.
> ③ diag stale.
>
> ### 게이트 (2026-08-26 재확인 후)
>
> ```
> validate_master_tables --no-build : pl_bridge 2518P/13F/317S/0NEW · csm_amort_identity 335P/11PIN/0F/0S(stale 0)
> validate_data_contract            : RED=0 YELLOW=85 · DART↔IR 36 step-pairs
> prepush_check.py                  : exit 0 (gate-clear, offline tests 230 passed/1 skipped)
> ```

