# Insurequant TODO

> Last updated: 2026-08-30 · Stage: cross-stage
> Index: CLAUDE.md (5-stage; parser 2-lane since 2026-06-13) · Stage TODOs: TODO_<stage>.md

Pipeline organized as **downloader / parser / validation / publishing / designer** — each stage has its own prompt (`docs/agents/claude-agent-<stage>.md`), TODO (`TODO_<stage>.md`), and changelog (`docs/changelog_<stage>.md`). See `CLAUDE.md` for the full index. This root file carries cross-stage items + project-wide policy only.

## Status

**🟢 2026-08-30 현재 — 게이트 전부 통과, 라이브 배포 정상.** 실측:
`validate_data_contract` RED=0 exit 0 · `validate_kics_disclosure` RED=0 exit 0 ·
`validate_live_artifacts` RED=0 exit 0 · `prepush_check.py` exit 0 · inbox 활성 스레드 **0건**
(위생 위반 0). 2026-08-29~30 에 브랜치 push 3회 + `main` 라이브 배포 1회가 실제로 나갔다.

> **아래 2026-08-21 문단의 "현재 push 는 차단 상태" · "라이브(main) 배포도 이것 때문에 대기중"
> 은 그 시점의 사실이고 지금은 아니다.** `R2_순자산합` IDENTITY_TAUTOLOGY 는 해소됐고,
> main 의 `kics_disclosure.json` 은 브랜치와 **바이트 동일**(2026-08-30 실측: main 이 추적하는
> 39개 파일 중 브랜치와 다른 것은 `.gitignore` · `PL_breakdown.json` · `public_exports/` 3개뿐).
> 이 문단들은 이력으로 남겨 두되 현황으로 읽지 말 것.

> **📊 2026-08-30 듀레이션 공시현황 census (owner 지시: "공시현황부터 체크")**
>
> **결론: 듀레이션 수치는 어느 원천에도 없다. 갭은 유도할 수밖에 없고, 그 유도 입력은
> 96.6% 차 있다.**
>
> | 원천 | 실측 |
> |---|---|
> | DART 사업보고서 본문 (39사 최신 연차) | '듀레이션' 언급 37사인데 **전부 회계정책 서술문**("보장단위 수는 … 예상 듀레이션에 의해 결정됩니다"). 자산·부채 듀레이션 수치 **0사** |
> | K-ICS 정기경영공시 MD (497개) | 언급 66개 파일·28사, **전부 서술만**("듀레이션 갭 한도를 설정하여…"). '`X.X년`' 형태 수치 **0사** |
> | 금리 시나리오별 순자산 (항목41~46) | **완비 226/234 = 96.6%** — 아래 표 |
>
> 시나리오표는 반기·연차에만 공시되므로 짝수분기 6개 × 39사 = 234셀이 모집단이다.
>
> ```
> 분기별 완비(6/6) 회사수: 2023.2Q 37 · 2023.4Q 38 · 2024.2Q 37 · 2024.4Q 38 ·
>                        2025.2Q 37 · 2025.4Q **39/39**
> 구멍 8칸뿐 — AIG손해보험 5칸(2023.2Q~2025.2Q, 2025.4Q부터 적재) ·
>              서울보증보험 3칸(반기 미공시, 연차만 낸다)
> ```
>
> **함정 기록**: 1차 탐지기가 `듀레이션[^<]{0,80}(\d+\.\d+)` 였는데 DART 표는 라벨과 값이
> 서로 다른 `<TD>` 에 있어 **0사**가 나왔다. 태그를 벗기고 다시 재서야 실체(서술문뿐)가
> 확인됐다 — "키워드 0회 = 원문 없음" 으로 결론내지 말 것(이 저장소가 세 번 데인 함정).
>
> **다음 단계**: 유도식은 owner 가 이미 준 형태(base 대비 시나리오별 gap → max(상승,하락)²
> + max(평탄,경사)² 의 제곱합 계열)와 같은 축이고, 그 계산은 이미 `36_irr` 로 구현돼 돌고 있다.
> 남은 것은 그 결과를 **듀레이션 연수로 환산할지, 순자산 민감도 그대로 보여줄지** 의 표현 결정뿐이다.
> owner 지시: **당장 착수하지 말 것.**

### 상시 점검 (날짜 걸린 것)

- [ ] **2026.2Q 정기경영공시 - 8/31(월) 전 라운드 완주.** owner 지시(2026-08-30):
  *"내가 내일 부르면 2시간 간격으로 보험사 경영공시 자료 탐색 & 그 다음 파싱부터 끝까지"*.
  아래가 그날의 실행 순서다. **owner 호출 전에는 시작하지 않는다.**

  **출발점 실측(8/30 기준).** 39사 중 게시 **1사**(하나손해 KR0050) / 미게시 38사 / 미관측 0.
  하나손해는 PDF(`data/disclosure/FY2026_Q2/pdf/`)와 MD(`md_inbox/FY2026_Q2/`)가 이미 있다.
  **마스터 삽입은 계속 보류** - 39사 중 1사만 넣으면 coverage census 가 38 RED 가 된다.
  코리안리는 owner 수동확인으로 미게시 확정(프로브는 unreachable 이었다). KB손해 이력표상
  8/29~31 이 1차 게시창이고 **8/31 이 그 창의 유일한 영업일**이다.

  **1) 탐색 루프 - 2시간 간격, owner 호출로 시작.** 매 회차 두 프로브를 **다** 돌린다
  (손보 17사와 생보 22사는 경로가 다르다). 둘 다 다운로드하지 않고 **행 라벨로만** 판정하므로
  "최신행 셀렉터가 조용히 1Q 를 다시 집는" 침묵 실패를 구조적으로 피한다.

  ```
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/census_q2_disclosure_listings.py
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/census_q2_life_own_sites.py
  ```

  - 판정은 `posted` / `not_posted` / `unreachable`(생보는 `not_observed` 추가).
    **`unreachable` 을 미게시로 읽지 말 것** - 판정 보류하고 다음 회차로 넘긴다.
  - 산출 `data/disclosure/_meta/FY2026_Q2/listing_census.json` 을 회차마다 갱신한다.
  - 정규식을 손대면 **반드시** `census_q2_life_own_sites.py --selftest`(오프라인 1초,
    양성대조 21 / 음성대조 7). **아무것도 매칭 못 하는 탐지기도 "2분기 없음" 이라고 보고한다.**
  - 회차 사이 대기시간에는 2)의 생보 다운로더를 미리 만들어 둔다.

  **2) 수집 - `posted` 로 뒤집힌 회사만.**

  - 손보: `scripts/download_disclosure_2026q2_nonlife.py` (이미 2Q 로 갱신됨. KR0002 / KR0003 /
    KR0004_MG / KR0009 / KR0032 는 XPath 에 분기 라벨이 박혀 있고 2분기로 바뀌어 있다).
  - 생보: **2Q 스크립트가 아직 없다.** `download_disclosure_2026q1_life.py` 를 복제해
    `download_disclosure_2026q2_life.py` 를 만들고 기간 라벨만 올린다.
  - 수집 직후 **무조건** 내용검증을 건다:

  ```
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/verify_q2_disclosure_content.py
  ```

    해시 차이만으로는 수집 증거가 안 된다. (1) 1Q 파일과 SHA256 상이 (2) 본문이 2026 2분기/
    상반기 또는 2026-06-30 기준 (3) K-ICS 정기경영공시 문서형. **셋 다 통과해야** 수집으로 친다.
    전례로 재렌더된 1Q, 2025 결산, DART 사업보고서가 전부 해시는 달랐다.

  **3) 파싱 - PDF -> MD -> `kics_disclosure.json`.**

  ```
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/run_harness.py --stage parse --period FY2026_Q2
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fill_period_to_disclosure.py --period FY2026_Q2
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fill_subitems_to_disclosure.py --period FY2026_Q2
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fill_market_subitems_to_disclosure.py --period FY2026_Q2
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fill_post_transition_to_disclosure.py --period FY2026_Q2
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/recalc_kics_derived.py
  ```

  - **venv 풀패스 필수.** 맨 `python` 은 스토어 3.13 에 걸리고 거기엔 docling 이 없어
    `--stage parse` 가 즉사한다.
  - item27 / item28(기본자본비율)은 원문에 라벨이 안 찍히는 **파생값**이다. MD 에서 찾지 말고
    `recalc_kics_derived.py` 로 산출한다. 빠뜨리면 rule 8 이 RED 로 뜬다.
  - 경과조치 적용 18사는 `값` 과 `값_적용후` 를 **둘 다** 채운다. 적용후가 검증 사각이었다.
  - 하나손해(KR0050)는 8/29 에 진단이 끝나 있다. `scripts/fix_20260829_kr0050_2026q2_onboarding.py`
    가 item28 결측 / items 47-54 부분결측 / continuity 를 **그 회사 그 분기만** 정정한다.
    39사가 다 찬 뒤 마지막에 태운다.

  **4) 검증 - RED=0 까지 간다.**

  ```
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
  ```

  - **RED 이 1건이라도 남으면 push 하지 않는다.** 우회나 면제로 넘기지 말고 고쳐서 0 으로
    만든다. documented exception 은 진짜 추출 불가인 경우뿐이고 그건 owner 승인 사항이다.
  - 커버리지 census 가 1급 게이트다. 39사 x 항목 그리드에 **빈 셀이 있으면 RED** 이며
    SKIP-on-missing 으로 통과시키지 않는다.
  - `8_life` SKIP(항목 29-35 결측)만 게이트를 막지 않는다.

  **5) 마무리 - 마스터 / 화면 / push.**

  - master xlsx 는 **전체 재생성 금지**. 바뀐 시트의 바뀐 행만
    `scripts/sync_master_xlsx_sheet.py` 로 cherry-pick 한다.
  - `build_root_masters.py` 는 `main()` 통짜 실행 금지. `validate_master_tables.py` 를 부를 때는
    **반드시 `--no-build`**(그게 숨은 두 번째 진입점이다).
  - push 게이트는 `.githooks/pre-push` 가 강제한다(현재 `core.hooksPath=.githooks` 설정됨).
    새 워크트리에서 시작하면 `git config --get core.hooksPath` 부터 확인한다.
  - 라이브는 `main` 에만 나간다. **owner GO 없이 `git push origin main` 금지.**

  **owner 에게 올릴 것은 셋뿐이다:** 면제 승인 / 화면 숫자가 바뀌는 변경 / 진짜로 막힌 것.
  나머지는 끝까지 알아서 처리한다. 종전 추적 스레드는 `inbox/_resolved/20260829T1900Z`.

### 최근 종결 (2026-08-30)

- [x] **`assemble()` "미공시 시 0표시" 규칙 — owner 가 option 1 승인, 구현 완료** (`cd79127`).
  회사가 다른 분기에서 실제로 뽑는 항목이면 이번 분기의 0-fill 을 건너뛰고 null 을 남긴다.
  마스터 38칸(+당분기 40칸)이 숫자→null(5사). 억제된 null 은 `data/_derived/pl_intentional_nulls.json`
  로 `_additive_merge` 폴백에서 제외 — 안 그러면 재빌드마다 예전 0 이 되살아난다.
- [x] **`public_exports/` 무검사 해소** (`8c702fc`). 사용자가 내려받는 12개 파일을 어떤 검사기도
  안 읽고 있었다. `validate_live_artifacts` 에 축 신설(15룰, 변이시험 8/8). 같이 발견: 그
  사각을 잡았어야 할 `test_push_gate_wiring` 이 `<script src>` 를 안 따라가서 그 12개를 한
  번도 본 적이 없었다 — 그것도 닫았다.
- [x] **gold 오버레이 무검사 해소** (`93c68db`). gold 를 빌더 소스와 대조하는 게이트·테스트가
  저장소에 0건이었다 = gold 셀 밑에서 빌더가 회귀해도 전 게이트가 clean. 마스크 115칸 원장 등재,
  drift 는 RED.
- [x] **inbox 전건 종결** — answered 28 + open 3 을 검증 후 `_resolved/` 로 이동, 활성 0.


**🔒 2026-08-21 — push 게이트가 이제 git 훅으로 강제된다. 새 클론/워크트리면 먼저 `git config core.hooksPath .githooks`.**
그 전까지 `prepush_check.py` 를 부르는 코드가 0이었다(참조 11곳 전부 문서, CI 없음, 훅 없음) — "배선했다"와
"강제된다"가 달랐다. 훅 체인 = 데이터계약 게이트 + inbox 위생(`scripts/check_inbox_hygiene.py`) +
오프라인 테스트 126개(`tests/test_rule_coverage_manifest.py` 포함), ~84초. 실제 `git push` 차단 확인.
상세: `docs/claude-changelog.md` 2026-08-21.

**🔴 2026-08-21 (2차) — 그 훅이 정작 `validate_kics_disclosure.py` 를 안 불렀다.** 바로 위 문단이
"강제된다"고 선언한 그 커밋이, `CLAUDE.md` 가 **mandatory** 라고 못박은 K-ICS 룰게이트(5.9초)를
빠뜨렸다. 전수확인: `scripts/validate_*.py` **8개 중 훅이 부르던 것은 1개**. 3개는 통과 중인데
미배선, 1개(`validate_csm_waterfall`)는 **실패 중인데 미배선이라 아무도 몰랐다**. 흔적은
`validate_data_contract.py` L305 주석에 남아 있었다 — *"(prepush_check 는 이걸 호출하지 않는다)
여기서 같이 건다"*, 즉 빠진 게이트를 눈치챌 때마다 **룰을 한 개씩 베껴 심고** 있었다.
지금 1b(K-ICS 룰게이트)·1c(도메인 게이트 3종)로 배선했고, **`tests/test_push_gate_wiring.py`**
(12 tests, 훅 묶음에 포함)가 새 `validate_*.py` 는 WIRED 이거나 사유 있는 NOT_A_PUSH_GATE 여야
한다고 강제한다. **현재 push 는 차단 상태** — 원인은 `R2_순자산합` IDENTITY_TAUTOLOGY 2건
(적용전·적용후). parser 가 넘긴 "image-only 24셀이 원인" 가설은 실측 반증됐고(제외해도
excess 1.25→1.23 / 1.43→1.40), 진짜 신호는 회사 단위 이봉분포다(KR0069 9/9 · KR0008 12/13 ·
KR0050 12/13 이 비스캔사 / 반대로 KR0073 은 13칸 중 1칸). 티켓 `inbox/validation/20260821T1830Z`.
**라이브(main) 배포도 이것 때문에 대기중** — main 의 `kics_disclosure.json` 은 2026-07-21 판이라
지난 한 달(적용후 710칸 변경 + 신규 204칸)이 미반영이고, 배포 사본은 `deploy/20260821-json` 준비완료.

Cross-stage focus (2026-08-20): K-ICS gate **RED=12**, all three offenders already documented below as image/scan-only source (KR0087 동양 2023.2Q ×7 · KR0097 하나생명 2024.2Q ×4 · KR0079 미래에셋 2023.2Q 8_life ×1) → gate contract satisfied. **✅ 닫힘 (parser 2026-08-20, inbox `20260706T0502Z` iter-2):** 적용후 하위 census 결측 4→**0** · 적용후 요구자본 continuity break 34셀/5(회사,분기)→**0** · 적용후 조정항목(22/23) review 17→**5**(전부 사유 기재). Open cross-stage tails: 항목4/12/13 값_적용후 18사 미러링 오염 후속 감사. (**tier2 소진율 분자 정의는 2026-08-20 종결** — DART per-bond 리베이스로 100%+ 0건.) Mid-long-term: duration-gap (MLG-1), K-ICS 시장위험 분해 (MLG-2) blocked on owner decisions.

**🔴 2026-08-21 업데이트 — validation이 면제 근거 raw 재검증으로 위 "gate contract satisfied"를 반증.** `INTERNAL_MODEL_36IRR_EXEMPT`(5건)·`_AFTER_SUBRISK_NOT_DISCLOSED`(5→1)·`_POST_PARENT_NOT_DISCLOSED`(3→1) 등재사유가 raw 대조에서 거짓으로 확인돼 해제됨(상세: 아래 `INTERNAL_MODEL_36IRR_EXEMPT` 항목 갱신분 + `inbox/parser/20260821T1600Z`·`20260821T1620Z`). parser(kics) 처리 결과: **하나생명(KR0097) 2024.4Q item16/17 값_적용후 = 실제 결함으로 확정, raw p281 값으로 fix 완료**(1건 종결). 36_irr 5건은 raw에서 items 41-46 정식 로드했으나(더는 결측 아님) 표준 derive식이 공시 금리위험액을 5.25~25.6% 벗어나 **RED 잔존**(같은 근본원인이 완전성 확보로 `TRANSITION_AFTER_IRR_MISMATCH` 4건도 새로 노출 — 이전엔 41-46후 결측이라 미판정이었을 뿐 통과였던 적이 없음, false-green 아님). 흥국생명(KR0071)×4·흥국화재(KR0005)×1 은 **디스크의 raw가 K-ICS 공시가 아니라 DART 사업보고서임을 validation이 확인**(`inbox/downloader/20260821T1625Z` refetch 대기) — parser 손 안 댐. `validate_data_contract.py` RED: 10(면제 해제 직후 노출분, display-scope) → **13**(TRANSITION_AFTER_IRR_MISMATCH 4건 신규 노출 − 하나생명 1건 종결). RED 증가는 회귀가 아니라 이전에 결측이라 못 보던 동일 결함이 완전성 확보로 드러난 것. 남은 13건 전부 parser 소관 밖 결정 대기 — 36_irr/TRANSITION_AFTER_IRR_MISMATCH 8건(같은 근본원인)=공식·스코프 불일치 owner 검토, 흥국생명·흥국화재 5건=downloader refetch 대기.

**규칙문서 리팩토링 (2026-08-06, 리팩토링 6차 — 상세는 `docs/claude-changelog.md`).** 코드가 아니라 프롬프트·인덱스 층의 context rot을 `claude-md-management` 6축 rubric으로 실측. 고침: ① `CLAUDE.md` 진행도표가 designer/publishing을 "skeleton"으로 오표기(실제론 §5.1~5.5·§5/§9/§10로 종결) → 실측 교체 + 잔여 TBD 정본을 각 프롬프트로 단일화, ② venv 경로 미기재(맨 `python`은 docling 없어 `--stage parse` 즉사) → `## 🐍 실행 환경` 신설, ③ kics 도메인doc 플로우 링크 4개 깨짐 수정. **잔여 2건:**

- [x] **DOC-1 단일소스 위반** — owner 결정(2026-08-06): **문서 재배치 대신 게이트**. keep-list는 이미 `test_docs_agree_with_what_pages_fetch`가 현실과 대조 중이었고(4곳 중 2곳), 무방비였던 골든표에 `test_golden_table_docs_agree_with_tests` 신설 — 신설 골든 누락 + dangling 개명 양방향 차단, mutation 2종으로 실발화 확인. 나머지 사본은 문서로 안 지키고 기계로 지킨다.
- [x] **DOC-2 publishing 프롬프트 자기모순** — §1(L107) "`data/ifrs17/viz` cutover 대기" vs §9(L266) "2026-06-16 LANDED". publishing이 드레인·처리: `git ls-tree -r main` 실측으로 §9가 맞음을 확인(라이브는 `data/dart/viz/*`, `data/ifrs17/viz`는 repo 어디에도 없음) → stale한 §1 Path note 삭제, §9 문구를 실측 근거로 교체, §9 delete-list 예시에서 죽은 경로 제거. orchestrator 독립 재확인 후 `inbox/_resolved/`로 아카이브.

**🟢 소스 교체 (2026-08-19, owner 발견) — 항목5 발주의 전제가 바뀜.** owner: "dart 공시 5. 재무건전성 등 기타 참고사항 부분에 깔끔한 표로 잘 있는데 왜자꾸 삽질해? 기적립액+신규전입액 자시고 할것도 없이 여기 기말 기준 적립액 다 들어가 있잖아". 실측 확인(메리츠 2026.2Q rcpNo 20260814002253): `II. 사업의 내용 → 5. 재무건전성 등 기타 참고사항 → 가.`에 **기말 적립액이 3개 기간치 표**로 있고 단위(백만원)도 명시. 해약환급금준비금 3,536,425 / 2,976,566 / 1,793,089 — 같은 필링 BS의 기적립액 2,976,566 + 예정액 559,859 = 3,536,425로 검산 일치. **이 표가 A(기적립액+전입액 산술)·D-1(6사 주석 추출 실패)·B(역방향 채움)·C(2022년말)를 대부분 없앤다** — 3기간치라 결측이 실값으로 채워지고, FY2024 필링의 전전기 열이 곧 2022년말이다(소급 가정치 아님). 덤: 같은 표에 보험계약자산/부채·재보험계약자산/부채·투자계약부채(항목 14/20/21/22), 바로 아래 "나. 지급여력비율"까지 있다. **함정**: 소제목이 회사마다 다르고(메리츠 "보험계약자산부채 및 준비금현황"/현대해상 "준비금 적립내역"/삼성화재 "보험계약부채 및 자산 현황") 문자열 find()로 절을 찾으면 목차·본문에 오탐한다(오케스트레이터 실측 — 한화생명·삼성생명·교보생명에서 발생). 구조적으로 절 경계를 잡을 것. 커버리지 census 선행. 종결조건(업권 합계 32.2조 ±5%)은 불변. 발주문에 배너로 반영됨.

**🔴 17BS 항목5(해약환급금준비금) 3건 + 2026.2Q 결측 10사 (2026-08-19 owner, 마스터 xlsx 리뷰).** owner가 "17BS" 시트에서 발견. 발주 2건:
> - **downloader** `inbox/downloader/20260819T0116Z__owner__MULTI_2026.2Q__fs_api_halfyear_negative_cache.md` — 2026.2Q가 14사뿐(2026.1Q는 24사). 원인은 파싱이 아니라 **빈 응답이 캐시에 굳은 것**: `_fs_api_cache/<corp>_2026_11012_*.json`이 `status 013(데이터 없음)/0건`인데 mtime이 전부 08-15 새벽 — 반기보고서 접수(08-14) 직후라 API 적재 전에 긁었다. **08-19 라이브 재호출로 메리츠·삼성생명·현대해상 모두 `000 정상` 확인** → 재취득만 하면 된다. 재발방지로 `013`은 캐시에 굳히지 말 것(안 고치면 다음 분기 그대로 재현).
> - **parser/ifrs17** `inbox/parser/20260819T0116Z__owner__MULTI__surrender_reserve_item5_semantics_and_backfill.md` — ① **항목5 = 기적립액 + 당기 전입액**으로 정의 변경(owner 재지시, 과거 중단분 재개). 지금은 기적립액 단독이고 전입액은 다음 FY Q1 롤포워드에만 쓰여 **FY말 값이 그 해 전입액만큼 과소 + 시리즈가 1년 밀린다**(raw 확정: 현대해상 2023년말 3,422,425인데 마스터 2023.4Q=0·2024.1Q=3,422,425. 메리츠·한화손보·롯데·삼성화재 동일 패턴). ② 미공시 분기 **역방향 채움** 추가(현행 순방향만) — 스코프는 FY 내부로 한정(FY 넘으면 삼성생명류가 2026 값으로 과거를 덮는다). ③ **2022년말 = 채워야 한다** (오케스트레이터 2회 오판 후 정정, owner가 기사 2건으로 반박). 폐기된 근거 2개: (1차) "31개 전수 스캔, 비영 0건" → 실제 13개만 매칭·대형생보 전부 미탐, (2차) "기사 23.7조 = 2023년말" → 부분합 16사 + DB손보 부호오류 + 한화생명 `3`으로 만든 23.0조를 잘못 맞춘 것. **21사로 재측정하면 2023년말 28.2조, 누락사 더하면 31조대 = 기사의 32.2조와 일치.** 따라서 23.7조(2022년말)는 별개 실재 수치. 소스는 FY2023 필링의 **준비금 반영후 조정이익 표 전기 열**(`parse_filing()`이 `r[-1]`을 버리는 중) — 성격은 한화생명 각주대로 "전기초부터 적용 가정 산출치"(전기 1,269,282백만). 단 전기 열 수확이 까다롭다(발주자 스캔은 이연법인세 표를 오인해 10.6조로 실패). **수용기준 = 업권 합계 대 보도치: 2022말 23.7조 / 2023말 32.2조 / 2024.6말 38.5조 / 2026.6말 58.1조, ±5% 안에 들 때까지 닫지 말 것.** ④ **2023년말 회사별 census 완료(2026-08-19, owner "2023년말부터는 딱 다 맞아야")** — FY2023 raw 31사 전수: 추출성공 18사 27.7조 vs 기사 32.2조, **차액 4.5조의 출처를 전부 특정.** 값은 있는데 못 뽑은 6사(한화생명 2,504,752=처분계산서에 있음·현재 마스터는 `3` / DB생명 1,633,087 · KB라이프 790,407 · 동양 640,201 · 하나생명 62,137 · 흥국생명 6,257 = 라벨접미사 없는 이익잉여금 내역 표·전입액 표기) → 채우면 33.3조. 진짜 0 2사(삼성생명·교보생명 "적립한 내역은 없습니다" 명시 → 삼성생명 0 오탐 철회). 값 깨진 2사(DB손보 필링 4,278,867 vs 마스터 △2,645,780 부호+값 불일치 / 라이나 2,251,256 = 총자산 대비 과대, 1000배 전례). 미확인 5사(ABL·처브라이프 언급없음 / 엠지·KDB·푸본현대 숫자미발견). **종결조건 = 2023.4Q 합계 32.2조 ±5%, 못 들면 남은 회사 명시.** ⑤ 같은 재빌드에서 항목5 오염 동반 수정(DB손보 부호반전·한화생명 2024.1Q `3`·AIG 2년 밀림·메트라이프 스케일·삼성생명 2025.4Q `0`).
> 선후관계: downloader 재취득 → parser 재빌드(골든 `test_ifrs17_bs_golden.py` `--update`) → xlsx 재생성(**`build_master_xlsx.py`는 파일 전체를 새로 씀** — 현재 시트 9개, changelog가 말하는 "17BS_PIVOT"은 이미 소실된 상태라 owner 확인 후 진행).

**🔴 2026.2Q 반기 + 2026.1Q 정정공시 = 현재 최우선 (2026-08-14 owner).** 오늘이 반기보고서 법정기한 — 한화생명(KR0068)·한화손보(KR0002) 2사만 확보(body XML + FS API `*_2026_11012_*` 둘 다 실측 확인), 나머지 37사는 오늘~내일 순차 제출 예상. 2026.1Q는 **18사가 정정공시**를 냈고 raw는 정정본으로 교체됨(commit `33111fb`) — 라이브 2026.1Q 숫자가 구버전 기준일 수 있어 **정정 재추출이 신규 분기보다 앞선다**. 발주: downloader `20260814T0149Z`(반복 스카우팅 + **body XML과 FS API 캐시를 같이** 받을 것 — equity 마스터는 FS API를 먹는다 + 정정 18사 FS 캐시 stale 여부 확인), parser `20260814T0149Z`(기존 open 2건의 순위 상향: `20260814T0000Z` 정정 18사 → `20260813T0600Z` 한화 2사, 2026.2Q는 CSM/PL/equity 3개 마스터 동시). **BS 세부항목 = 그 다음** — 아래 BS-TACCOUNT로 승계(그 예고 파일명 `..._bs_line_items_full`은 생성된 적 없음).

**BS-TACCOUNT + 배당 탭 (2026-08-14 owner 저녁 발주, cross-stage).** owner 원문: *"OpenDart API 이용해서 BS 추가항목들 좀 추가 (…) 17.html 맨 위로 올리고 재무상태표처럼 왼쪽 자산 & 우상단 부채 & 우하단 자본 (…) + 아이콘 클릭하면 세부"* / *"배당현황도 전부 OpenDart API로 크롤링 & 별도 탭에 게시"*. 발주 3건:
> - **parser/ifrs17** `inbox/parser/20260814T1250Z__owner__MULTI__ifrs17bs_detail_lines_for_taccount.md` — `IFRS17_BS.json` 항목 1-7에 BS 세부계정 추가. **신규 fetch 불필요**(오케스트레이터 실측: `fnlttSinglAcntAll` = 전체 재무제표라 `_fs_api_cache` 261파일/24사 안에 BS account_id 95개가 이미 있음). 스키마 계약 = 기존 8열 + `섹션`(자산|부채|자본|준비금)·`레벨`(1|2), 항목번호 블록 자산10-29/부채30-49/자본50-69. 수용기준 = **섹션별 폐쇄검산**(Σ L2 == L1 총계, 잔차는 명시 항목으로 emit·5% 초과 시 매핑 미완 보고). 최대 함정 = 부모/자식 태그 공존(상각후원가 계열)의 **이중계상**. 세부는 Tier-1 24사만(비상장 15사는 총계뿐 → 문서화 예외).
> - **designer** `inbox/designer/20260814T1250Z__owner__IFRS17__bs_taccount_top_panel.md` — Panel 7을 **최상단**으로 이동 + T자(좌 자산 / 우상 부채 / 우하 자본) + `+` 버튼 2단 드릴다운. **항목번호 하드코딩 금지, 섹션·레벨로 그룹핑** → 파서 랜딩 시 HTML 무수정. `IFRS17.html:172-176`의 "L2/L3는 오케스트레이터 과도주문" 주석은 **오늘 owner 직접 요구로 무효** — 보존된 L2 코드 재사용. 파서 대기 없이 착수 가능.
> - **downloader** `inbox/downloader/20260814T0746Z__...__dividend_disclosure_recurring_onboard.md`(기존 스레드에 스코프 확정 추가) — alotMatter 전사 39사 × FY2023~FY2026 × reprt 4종(owner: 반기 전부 + manageable하면 분기까지 → ~620콜/4-5분으로 전부 확정), raw는 `data/dart/_alotmatter_cache/`에 원본 그대로. **탭은 빈 `공시보고서.html`을 배당으로 채운다**(owner 확정, 새 탭 신설 아님). 체인 진행(2026-08-15 00:30 기준): downloader ✅(raw 624파일) → parser ✅(`dividend.json` 1,924행 · 24사 × 14분기 · `scripts/build_dividend.py` · xlsx `배당` 시트) → **designer 진행중**(`공시보고서.html` 아직 "준비 중" 껍데기) ∥ **publishing 대기**(`inbox/publishing/20260814T2230Z`에 P-1~P-4 추가: dividend.json **git 미추적** · keep-list 문서 2곳 · xlsx 재생성 불필요 · 게이트 통지 전 push 금지) ∥ **validation 신규 발주**(`inbox/validation/20260814T1625Z`: `MASTER_FILES` 미등록 = 게이트가 이 마스터를 안 봄 → 배선 + 룰 3개(payout identity 46셀 / census 336-310=26셀 결측이 013인지 / 항목6 전행 0·항목5 264행 0의 0값 맹점) + 루트 배당 xlsx 교차대사).

**EQUITY-AOCI (신규, 2026-08-13 owner 발주) — 자본구성 마스터 `equity_composition.json`.** 회계법인 발표자료가 K-ICS 비율과 나란히 기타포괄손익누계액(AOCI)을 핵심지표로 쓰는 걸 owner가 보고 발주. **타당성 확인 완료(오케스트레이터 실측)**: 주 소스는 이미 디스크에 있다 — `data/dart/_fs_api_cache/`(DART `fnlttSinglAcntAll.json`)의 BS/SCE에 표준 account_id로 전부 잡힌다(`ifrs-full_AccumulatedOtherComprehensiveIncome`, `dart_SurrenderValueReserve` 등). SCE `account_detail`의 AOCI 컬럼이 **자산측 FVOCI 평가손익 vs 부채측 보험계약순금융손익 미스매치**로 분해되고 BS 스톡과 정확히 닫힌다(흥국화재 2025.4Q 실측). 커버리지: 24개사 × 11분기 즉시 / 15개사 XBRL 부재 → Tier-2(본문 XML) / 2023.1Q·2Q 백필 필요. **분류 정정**: 해약환급금준비금은 AOCI가 아니라 **이익잉여금 내 법정적립금** — 두 축으로 분리해 설계(발주문에 명시). 5개 stage inbox 발주 완료(`inbox/*/20260813T0422Z__owner__MULTI__*`). 순서: downloader(백필·카탈로그) → parser/ifrs17(마스터) → validation(항등식·census·게이트) → publishing(keep-list·xlsx) ∥ designer(패널 목업, 게이트 통과 전 배포 금지).

> **⚠ 범위 정정 (2026-08-14, owner) — 위 발주가 과설정이었다(오케스트레이터 오류).** owner 원문은 "high level 17BS(자산/부채/자본/AOCI)를 **빠르게** OpenDART API로, 가능하면 해약환급금준비금까지 **안되면 pass**"였는데, 발주문이 항목 30개·항등식 6개·census RED·Tier-2 본문XML 폴백·워터폴 패널로 부풀었다. 결과 RED 182 중 **160건이 "안되면 pass"라던 해약환급금준비금(항목10)을 필수 코어로 못박은 탓.** 정정 발주 2건: ① validation `20260814T0035Z` — census 코어를 **[1 자본총계, 6 AOCI, 40 자산총계, 41 부채총계]** 로 축소, 항목 10/11·5·20-31은 optional(YELLOW), ② parser `20260814T0035Z` — **Tier-2 중단**(15개사 본문XML 파싱 취소), Tier-1(FS API) 24개사×11분기로 종결. 이미 만든 마스터·빌더·골든은 **롤백하지 않는다**(같은 API 응답에 딸려온 항목이라 유지비 0).
**owner 2차 결정 (2026-08-13, iter 2 — `inbox/{parser,designer}/20260813T0436Z__*`):** ① **배치 확정 = `IFRS17.html` 신규 섹션 `7) 재무상태표 · 자본의 질`** (신규 페이지·K-ICS.html 아님, 기존 6개 섹션 불변). designer의 "배치안 owner 결정" 질문 종결. ② **범위 = 3단 드릴다운** — L1 자산총계/부채총계(그중 보험계약부채)/자본총계 → L2 자본 구성 6종 → L3-a AOCI 분해(자산측 FVOCI vs 부채측 보험계약순금융손익 미스매치) · L3-b 이익잉여금 내 법정준비금 3종(해약환급금 강조). ③ L1이 비어 있어 **파서에 BS 상위 항목 40~49 추가 발주**(`ifrs-full_{Assets,Liabilities,InsuranceContractsIssuedThatAreLiabilities,...}` — 오케스트레이터가 같은 캐시에서 67/67 실측). 신규 항등식 3개(`40==49`, `40==41+1`, `42<=41`). 마스터 파일명은 `equity_composition.json` 유지(5개 문서 동시수정 회피, DOC-1 패턴). ④ 패널 C(업권 추이)는 이번 범위에서 제외(별건).

**J-ESR (일본 ESR) — 2026-09월말 킥오프 목표 (2026-09-01 owner, 보류 해제).** 기존 보류 사유(개별사 ESR이 EDINET 有価証券報告書 제출기한 전에는 미공개)는 유효했으나, `J-ESR/jesr_pipeline_status.md` 실측상 有報 제출이 6~9월에 몰려있어(최종기한은 2026-10-31이지만) 9월 말이면 이미 다수 사가 제출 완료 상태 — 더 늦출 이유 없음. MVP는 2026-07-21 revert(`167cba1`)됐고, scaffold(EDINET fetch API키 확보·mutual IR-PDF·`jp_insurers.csv` 74사)는 그대로 살아있어 재개 시 처음부터 다시 할 필요 없음. 재개 시 downloader/parser inbox로 신규 발주 — 과거 스레드는 `inbox/_resolved/*jesr*` 4건 참조.

> **취지 참고 (owner 공유 기사, 2026-09-01) — 일본 금융청 '2026년 보험 모니터링 보고서'.** 출처: [insnews #92437](https://www.insnews.co.kr/news/articleView.html?idxno=92437). ESR 비율 자체보다 넓게, 금융청·시장이 실제 주목하는 축 3개: ① **자산집약형 재보험(AIR) 활용** — 생보 약 절반(주로 외국계·상장사)이 AIR 보유, 활용 목적에 "ESR 개선"이 명시적으로 들어가고 금융청은 재보험사 신용위험 + 특정 자산/지역/재보험사 집중위험을 경고. ② **손보 이상위험준비금(화재보험) 적립 부족** — 2025-03말 기준 화재보험 취급 28사 중 12사에서 부족 확인, 자연재해 빈발로 상시 이슈화. ③ **생보 이익구조 전환** — 이차손익이 금리상승으로 역마진→이익 구조로 전환 중, 예정이율 인상 확산(K-ICS/IFRS17에서 이미 다루는 위험률차손익·이차손익 구조와 대응됨). **지금 스코프(ESR 헤드라인 숫자)를 이 3축까지 넓힐지는 미결 — 재개 시 EDINET 有報에서 실제로 뽑히는지 확인 후 판단.** 지금은 방향성 참고만.

**Stage files:**

- **Downloader** (Stage 1): `TODO_downloader.md` + `docs/changelog_downloader.md` + `docs/agents/claude-agent-downloader.md`
- **Parser** (Stage 2, **2-lane since 2026-06-13**): `TODO_parser_kics.md` · `TODO_parser_ifrs17.md` + `docs/changelog_parser_{kics,ifrs17}.md` (pre-split frozen: `docs/changelog_parser.md`) + shared `docs/agents/claude-agent-parser.md` + domain `docs/domains/claude-agent-{kics,ifrs17}.md`
- **Validation** (Stage 3): `TODO_validation.md` + `docs/changelog_validation.md` + `docs/agents/claude-agent-validation.md`
- **Publishing** (Stage 4, **merged gathering + pushing**): `TODO_publishing.md` + `docs/changelog_publishing.md` + `docs/agents/claude-agent-publishing.md` (**complete** — §5/§9/§10 + launch-runbook skill, 2026-07-21)
- **Designer** (Stage 5, **new — HTML/CSS/responsive**): `TODO_designer.md` + `docs/changelog_designer.md` + `docs/agents/claude-agent-designer.md` (**complete** — §5.1~5.5 design system, 2026-06-16)

Items previously here that have moved out:

- Downloader (F2 done, F7–F10, F14, MISC-BOND-*, MISC-IR-MERITZ, MISC-SEIBRO, decisions #5/#6) → `TODO_downloader.md`
- Parser (KICS-PARSER-SPLIT/REPARSE-Q4/KR0069/KR0097/RED-FIX2/RED-FIX3/SUB/POST/RATIO28/HIST/IMG + IFRS-A1~B5-KICS/B3-UNIFY/NORMALIZE/HIST/SEN-TABLE) → `TODO_parser_{kics,ifrs17}.md`
- Validation (KICS-VALIDATE, IFRS17-NB-RECONCILE) → `TODO_validation.md`
- Publishing (F4 v2, F13, INDEX-IFRS17-BUBBLE, INDEX-BUBBLE-V2, MISC-IR-PROTOTYPE, MISC-IR-NB-DENOM, IFRS17-CSM-BUBBLE, KICS-TIER1/2-UTIL, KICS-FORWARD-CAPITAL, KICS-HTML-SUB, IFRS17-HTML-DASH, F5/F6 data) → `TODO_publishing.md`
- Designer (MOB-KICS, MOB-IFRS17, VIS-DONUT, VIS-CHARTLEGEND, INDEX-C12, F1-HTML, F6-HTML, F17-PANEL3 HTML, M1/M2) → `TODO_designer.md`

**Reorg #2 (2026-05-30j)** — `data/assoc/` → `data/_derived/`; KIDI/DART → `FY####_Q#` 컨벤션 통일. **DART batch script refactor 잔여** → `TODO_downloader.md` REORG2-DART.

Session start: read this root file first, then the relevant stage's `TODO_<stage>.md`.

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## ✅ data-contract gate pending exceptions — **종결 (2026-08-20)**

2026-06-20에 열었던 `RED=4, 전부 tier2(보완자본 소진율)` 건은 **전량 해소됐다.** 실측:

```
validate_data_contract.py     RED=0  YELLOW=276  exit=0
kics_tier2_utilization.json   100% 초과 = 0 / 39사  (data_source: dart_bonds_fy2025_경과조치)
신한이지 분모                  2.68억(오파싱) → 268.0억 = SCR 536 × 50%
```

원인 제거는 **FSC Face → DART per-bond 리베이스**(`_resolved/20260803T0055Z`)가 했다 — 분자를
후순위채 발행잔액으로 교체하는 원래 처방과 같은 방향이었고, 동양생명 240%·KB손해 218%·
미래에셋 126%가 전부 100% 아래로 내려왔다(동양 84.2%). 면제행 OCR도 불필요해졌다.
경위: `inbox/_resolved/20260616T1529Z` · `20260616T0506Z` 종결 노트.

---

## 🔴 K-ICS gate documented exceptions — CURRENT (2026-06-14, parser)

> Supersedes the 2026-06-12 snapshot below. Since then: RED 227→**19** (대량 fitz 회수 + 코어/rule5
> 백필 + round3 K2/K3), AND validation **expanded the validator** (new `36_irr` IRR 41-46 rule + `19_market`
> cadence fix + `_market_tooling_fail` + `_parent_zero_child_nonzero`). The 2026-06-12 "19_market 223" list is
> mostly registered/recovered. Current gate state = **19 RED, ALL verified non-regression** (raw 페이지까지 검증). Characterization:

> **Update 2026-06-16 (round3 K1–K4, parser):** RED 21→**19**. K3 = 서울보증/카카오 orphan item35
> 제거(parent17=0인데 자식 비0 = 일반손해 대재해 오매핑, 3셀) + fill_subitems parent-gate 가드 추가 +
> validation 신설 `_parent_zero_child_nonzero` 게이트(parent-zero=0 확인). K2 = 예별손해(KR0004,
> 구MG) 2025.4Q docling+추출(코어28·하위29-35·시장36-40 적재; **자본잠식 -8.24%** 실값). 카카오
> 2023.3Q 19_market = 소스표 실재 → 36/38 적재로 **GREEN 해소**(cadence-SKIP 불필요, 아래 정정).
> K4(sensitivity 적용후)·K1(designer)은 게이트 무관.

> **Update 2026-07-03 (owner 워크스루 3건, parser/kics):** owner가 사이트에서 눈으로 발견한 kics 3건 처리.
> (1) **KR0083 푸본현대 2025.2Q** — FY2025_Q2 슬롯에 **엉뚱한 회사(KR0075 비엔피파리바카디프) PDF**가 적재돼
>   있었음(자기정합 데이터라 산술 게이트 GREEN 통과 = false-green). items 1-28을 진짜 푸본현대 값(25.3Q MD의
>   25.2Q 컬럼)으로 교정(지급여력비율 318.25%→**−10.13%**, 자본잠식 실값). sub-risk 29-46은 정본 PDF 부재로
>   삭제 → **downloader refetch 발주**(`inbox/downloader/20260703T1250Z...`). **잔여 RED = KR0083 2025.2Q
>   `19_market` 1건**(item19=8559 공시·36-40 결측, 정본 PDF 재취득 대기) = **documented exception, downloader
>   완료 시 해소**. (2) **KR0050 하나손보** 25.3Q #34 사업비 405.11·#35 대재해 44.81 backfill(docling 표뭉갬
>   복구) + 2024.2Q #35 대재해 0.04→40.86(콤마→마침표 오독). (3) **KR0076 아이엠라이프 26.1Q** sub 적용후
>   4개 채움(장수 68.37·해지 1249.87·사업비 433.16·대재해 36.95; 사망/장해질병=비대상, 장기재물=원천 N/A).
>   → 게이트 사각 2건(cross-quarter plausibility·parent-present-child-absent census) validation 발주.

**✅ Identity tautology — documented exception (owner 2026-08-21, 상한 박제형):**

| 축 | 컬럼 | rule id | 사유 | 박제 상한 |
|---|---|---|---|---|
| **R2_순자산합** (item4 = Σitem5..11) | **적용전** | `IDENTITY_TAUTOLOGY` | **셀 값을 바꾸는 RED 가 아니다.** 이 메타룰은 census 를 읽어 findings 만 만들고 `records` 에 쓰는 경로가 없다 — 면제해도 화면·마스터·xlsx 숫자가 한 칸도 안 움직인다. 막고 있던 것은 "이 항등식이 통과해도 증거가 아니다"라는 **검증 품질** 신호인데, 그것 때문에 실제로 검증된 한 달치 데이터가 라이브에 못 올라가고 있었다. **owner 결정: 이번엔 풀고 올린다.** | **excess ≤ 1.35** (등재 1.25 + tol 0.10), n=393 zeros=267 |
| 〃 | **적용후** | 〃 | 〃 (적용후는 미러 182칸이라 적용전 되맞춤을 그대로 물려받는다) | **excess ≤ 1.53** (등재 1.43 + tol 0.10), n=182 zeros=142 |

> **끄기가 아니라 상한 박제다.** `_TAUT_EXEMPT`(scripts/validate_kics_disclosure.py)가 등재시점
> 지표를 들고 있고 게이트가 **매 실행 재측정**한다. 더 되맞춰지면(excess 가 상한 초과)
> `IDENTITY_TAUTOLOGY_PIN_DRIFT` **RED 로 즉시 차단** — 되맞춤 write-path 재유입을 잡는 자리다.
> 허용오차 0.10 은 실측 되맞춤 폭(1.25 → 1.84 = +0.59)을 절대 못 삼키게 잡았고
> `test_tolerance_is_not_wide_enough_to_swallow_a_reintroduced_rewrite` 가 그것을 강제한다.
> **경고는 그대로 찍힌다** — 축별 표·"위반 0" 옆 주석·전용 블록 세 곳 모두. 면제한 것은 push
> 차단이지 경고가 아니다. 축이 수렴해 발화가 멈추면 `IDENTITY_TAUTOLOGY_EXEMPT_UNNECESSARY`
> review 가 "등재를 지워라"라고 알린다(면제의 영구 잔류 방지).
> **✅ 원인 확정 (2026-08-21, parser-kics 원문 대조) — 되맞춤이 아니라 공시서식이다.**
> 상위 7사 raw 가 그 행 라벨을 **`순자산 (1+2+3+4+5+6+7)`** 로 인쇄한다(삼성생명 FY2026_Q1 raw
> p17 직접 확인). 발행사가 총계를 성분의 합으로 **정의**하니 잔차 0 이 정상이고, Irwin–Hall
> 독립반올림 귀무가 이 표본에 구조적으로 안 맞는 것이다. 마스터==원문 100%(9사 23개 (회사,분기)
> 직접 대조 + 442버킷 전수 census, 9사 내 diff 0) · **데이터 수정 0건**. 반대편 꼬리(교보 +1 ·
> 하나생명 −1)도 raw==master 이고, 그 발행사들은 총계를 성분과 독립으로 채운다(같은 라벨이
> 컬럼에 따라 갈린다: 교보 2023.2Q resid=0 vs 2023.1Q resid=−1, 같은 페이지).
> 초기 가설 2개는 **둘 다 반증**됐다 — "image-only 24셀이 원인"(제외해도 1.25→1.23 · 1.43→1.40)
> 과 "우리가 item4 를 덮어썼다"(raw==master).
> **이 축은 저절로 수렴하지 않는다** — 발행사별 총계 산출방식은 영구적 특성이라
> `IDENTITY_TAUTOLOGY_EXEMPT_UNNECESSARY` 는 앞으로도 안 뜬다. **그걸 기다리지 마라.**
> 등재의 남은 역할은 **되맞춤 write-path 재유입 감시** 하나이고 그건 pin drift 가 잡는다.
> 근본 해결은 축을 발행사 서식별로 가르는 것(라벨에 `(1+2+...)` 가 인쇄된 발행사는 정의상
> 닫히므로 제외)이지만 별도 설계 결정이라 지금은 안 한다.
> 기록: `inbox/_resolved/20260821T1830Z` · `scripts/_probes/probe_r2_company_detail.py`.

**✅ Issuer self-inconsistency — documented exception (owner 2026-08-21, 잔차 박제형):**

| company | quarter | rule id | 사유 | 박제 잔차 |
|---|---|---|---|---|
| **KR0079 미래에셋생명** | **2023.2Q** | **`8_life`** (+ 게이트 `_transition_mmult_after` 축 17 적용후) | **발행사가 자기 총괄표와 자기 세부표를 서로 안 맞게 공시했다.** 추출 오류가 아니다 — 양쪽 다 원문 그대로다(validation 2026-08-21, raw 200dpi 렌더링 판독: p11 총괄표 `1.생명장기손해보험위험액 = 17,495` · p15/p16 세부표 백만원값이 마스터 item29~35 와 ÷100 일치). 어느 쪽이 옳은지는 item17 쪽 **독립 확증 4개**(23.2Q p11 · 23.3Q p11 직전분기열 · rule4 잔차 +0.74 · rule6 잔차 +1.00) 대 세부표 쪽 **0개**. item17 을 자체산출값 16,127.60 으로 갈아끼우면 RED 가 1→2 로 늘고 원문 2곳에서 확인된 지급여력비율 209.7 과도 어긋난다. **owner 결정: 원문 기재대로 둔다.** | **±1,367.4050** (적용전·적용후 동일, tol 0.01) |

> **blanket skip 이 아니다.** `_LIFE8_ISSUER_INCONSISTENT`(scripts/validate_kics_disclosure.py)가
> 기대잔차를 값으로 들고 있고 게이트가 **매 실행 마스터에서 재계산**한다. item17 이나 item29~35 중
> 한 칸이라도 바뀌면 `LIFE8_EXEMPTION_RESIDUAL_DRIFT` RED, 결측이 되면 `LIFE8_EXEMPTION_INPUT_MISSING`
> RED 로 **즉시 되살아난다**. finding 자체도 안 지운다(report 의 `exempted_findings` 에 남는다).
> 근거 원장: `data/_gold/kics_exemption_provenance.json` (status `VERIFIED_BY_IMAGE` — 이 PDF 는
> 텍스트레이어가 행 단위로 잘려 있어 `absent_markers` 기계검증이 원리적으로 불가능하다. 게이트가
> 인용 페이지 텍스트밀도를 매 실행 재측정해 그 사유 자체를 검증하고, 매 실행 review 로 인쇄한다).
> **해제 조건**: 발행사가 정정공시를 내거나, 세부표 쪽 독립 확증이 생기면 등재를 푼다.

**✅ Tier2/기본자본다리 issuer self-inconsistency — documented exception (owner 위임 2026-08-24, 잔차 박제형, **18버킷 36 finding**, 2차 위임 갱신):**

**네 계열이다. 사유가 다르므로 섞어 읽지 말 것.** 특히 계열 ④는 나머지 셋과 **근거의 종류가
다르다** — ①~③은 발행사 자기모순을 산수로 증명하지만, ④는 **인과가 규명되지 않은 채 owner
판단으로 서 있다**(원장 status `VERIFIED_BY_OWNER`, 게이트가 매 실행 review 로 인쇄한다).

*계열 ① 두 표가 서로 다른 값을 인쇄 (7버킷 12 finding)*

| company | quarter | rule id | 사유 | 박제 잔차 |
|---|---|---|---|---|
| **KR1000 코리안리** | **2023.2Q** | `3_tier2_composition` | **헤드라인 `[경과조치 적용 전 지급여력비율 세부]` 의 보완자본이 TFI 표의 적용후 컬럼과 같고, TFI 표의 적용전 컬럼은 자기 구성행으로 정확히 닫힌다.** 즉 같은 필링이 '경과조치 적용 전 보완자본' 을 두 값으로 인쇄한다. raw 7분기 전수 word-좌표 확인(validation 2026-08-24). 양쪽 다 원문 그대로라 고칠 셀이 없다. | **−983.43** |
| 〃 | **2023.3Q** | 〃 | 헤드라인 5,114 · TFI 610,272/511,364 (p9) | **−988.72** |
| 〃 | **2023.4Q** | 〃 | 헤드라인 5,470 · TFI 646,944/546,989 (p18/p19). `min(608,179, 999,550) + 38,765 = 646,944` 정확 일치 | **−999.44** |
| 〃 | **2024.1Q** | 〃 | 헤드라인 5,490 · TFI 651,623/548,988 (p9/p10) | **−1,026.23** |
| 〃 | **2024.2Q** | 〃 | 헤드라인 5,444 · TFI 650,396/544,394 (p9/p10) | **−1,059.96** |
| 〃 | **2024.3Q** | 〃 | 헤드라인 5,996 · TFI 707,693/599,602 (p9/p10) | **−1,080.92** |
| **KR1000 코리안리** | **2024.4Q** | `2_tier1_bridge` | **같은 자기모순의 거울상.** 이 분기부터 헤드라인 보완자본(8,953)이 TFI **적용전**(8,953.27)으로 넘어갔는데 같은 표의 `Ⅲ.재분류항목` 7,863 은 TFI **적용후**(7,862.67) 그대로다 — 한 표의 두 행이 서로 다른 기준. `42,723 − 910 − 7,863 = 33,950 ≈ TFI 적용후 기본자본 33,950.12` 인데 공시 기본자본은 32,860 ≈ TFI 적용전 32,859.53. raw FY2024_Q4 p24(두 표가 같은 페이지). | **−1,090.00** |
| **KR0003 롯데손해** | **2026.1Q** | `3_tier2_composition` · `47_tier2_census`(전·후) <br>*(2026-08-24 iter-7: `50_tfi_tier_split`(전·후) 핀 2개 **제거**)* | **발행사가 전기(2025.4Q) TFI 표를 그대로 재게시했다.** raw FY2026_Q1 한 필링 안에서: p21 헤드라인 당분기 `26,955 / (3,962) / 30,918 / 20,432` · 직전분기 `26,058 / (3,875) / 29,934 / 20,671` · p22 TFI 표 `2,605,850 / (387,514) / 2,993,363 / 2,067,069` = **직전분기 열과 소수점까지 일치.** RED 5건이 전부 이 한 원인이다(`TIER2_LIMIT_STALE` 도 item48 = 직전분기 item14×50%). | **+984.36** · census(잔차없음) 2 <br>*(±896.51 핀 제거 — 축 E 의 comparand 가 item1 에서 item52(TFI 표 자신의 지급여력금액 행)로 승격되면서 이 버킷이 그 축에서 **정확히 닫힌다.** 재게시된 전기 표는 자기 안에서는 일관되기 때문이다: item52 26,058.50 = item50 −3,875.14 + item51 29,933.63. 게이트가 `TIER2_EXEMPTION_INERT` review 로 먼저 알렸다. 재게시 사실 자체는 위 두 축이 그대로 잡으므로 사각 없음)* |

| **KR0004 예별손해** | **2025.1Q** | `3_tier2_composition` | **합계는 두 표가 같은데 tier 분할만 다르다.** raw FY2025_Q1 p16 헤드라인(억원) `△1,651 = △2,648 + 997` 은 자기 안에서 닫히고, p17 TFI 표(백만원)는 `지급여력금액 △165,099 = △1,650.99억`(헤드라인과 **일치**)인데 `기본자본 △165,099 · 보완자본 0` 이다 — 보완자본 997억을 기본자본 쪽에 통째로 합쳐 인쇄했다(자본잠식사라 기본자본이 음수인데 tier 를 안 나눴다). **다른 축은 전부 정확히 닫힌다**(다리 `△2,629 − 0 − 19 = △2,648` · TFI 구성식 `0 = min(0, 5,378.68) + 0`). 남는 RED 1건의 잔차가 **정확히 헤드라인 보완자본 997**. 한도 537,868 은 SCR 과 맞는다(item14_전 10,757 × 50%). *(2026-08-24 2차 owner 위임 등재 — iter-7 에 초안만 쓰고 위임 목록 밖이라 보류했던 건)* | **+997.00** |
| **KR0003 롯데손해** | **2023.1Q** | `2_tier1_bridge` · `3_tier2_composition` · `50_tfi_tier_split` | **두 표가 '경과조치 적용 전 보완자본' 을 17,812(헤드라인 p9)와 17,830(TFI p10)으로 다르게 인쇄하고**, 그 위에 TFI 표의 **적용전 컬럼만** 자기 합계행과 안 닫힌다(`8,034 + 17,830 = 25,864` vs 인쇄 `25,846`). **적용후 컬럼은 정확히 닫힌다**(`8,469 + 17,377 = 25,846`) — 같은 행에서 두 컬럼을 같이 읽는데 한쪽만 깨지므로 우리 추출 결함일 수 없다. 세 축이 같은 18~19 를 가리키고 **부호가 정확히 반대**다. 헤드라인 보완자본은 `25,846 − 8,034` 로 역산된 값이다. 순자산 독립 확증(`6,902+454+4,788−10+3,538+6,621 = 22,293`). 계산값 `25,864` 는 문서 전체 검색 **0회**(숨은 행 없음). *(2026-08-24 2차 owner 위임 등재)* | **+19.00 · −19.00 · −18.00** |

*계열 ② 한 표가 자기 구성행과 안 닫힌다 (7버킷 19 finding)*

| company | quarter | rule id | 사유 | 박제 잔차 |
|---|---|---|---|---|
| **KR0003 롯데손해** | **2024.4Q** | `3_tier2_composition` · `51_tfi_tier2_composition` | TFI 표(raw FY2024_Q4 p60)의 **적용전 컬럼만** 301백만원 어긋난다: `869,948 + 1,933,391 = 2,803,339` vs 인쇄 `2,803,038`. 적용후는 정확히 닫힌다(`824,278 + 1,933,391 = 2,757,669` vs `2,757,668`). 대조군: 같은 발행사 2025.1Q 는 정확히 닫힌다. 신종 45,370 + 후순위 822,410 = 867,780 은 잔차를 설명하지 못한다(NH농협과 다른 점). | **−3.39 · −3.01** |
| **KR0003 롯데손해** | **2025.1Q** | `2_tier1_bridge` | 헤드라인표(raw FY2025_Q1 p18) 안에서 `Ⅲ.재분류항목` 만 어긋난다: `15,657 − 8 − 19,202 = −3,553` vs 공시 `−2,348`. Ⅰ순자산 15,657 은 자기 7개 구성행 합과 정확 일치, 기본자본은 TFI 표 p19 `(234,845)/100` 로 재확인. 대조군: 같은 발행사 2024.3Q·2024.4Q·2026.1Q 는 **전부 정확히 닫힌다.** | **+1,205.00** |
| **KR0075 BNP카디프** | **2024.3Q** | `2_tier1_bridge` · `3_tier2_composition` · `47_tier2_census`(전·후) · `51_tfi_tier2_composition` | 〃 `min(31,614, 31,614) + 23,584 = 55,198` vs 인쇄 `33,067`(raw FY2024_Q3 p16, 메모행 둘 다 대시). 헤드라인(p15)은 자기 안에서 닫힌다(`2,069 = 1,738 + 331`). TFI 표의 tier 분할도 정확히 닫힌다(`173,757 + 33,067 = 206,824`) — 깨지는 것은 보완자본 **구성**뿐. **iter-6 에 "증거가 2024.4Q·2025.1Q 와 동일한데 owner 위임 목록 밖" 이라는 이유만으로 RED 로 남겨 뒀던 건이다**(면제를 스스로 넓히지 않는다는 원칙). *(2026-08-24 2차 owner 위임 등재)* | **+15.00 · −220.98 · census 2 · −221.31** |
| **KR0075 BNP카디프** | **2024.4Q** | `2_tier1_bridge` · `3_tier2_composition` · `47_tier2_census`(전·후) · `51_tfi_tier2_composition` | TFI 표 자신의 보완자본 행이 자기 구성행과 안 맞는다: `min(34,678, 34,678) + 32,949 = 67,627` vs 인쇄 `43,353`(raw FY2024_Q4 p50). **표에 숨은 행이 없다** — `(기발행 신종자본증권)`·`(기발행 후순위채무)` 둘 다 대시. **숨은 공식도 아니다**: 잔차/초과분 비율이 6.2%→26.3%→20.1% 로 흔들려 상수가 아니다(3분기 전수). `item47 == item48` 은 채무성 자본이 0인 회사가 한도-체크 두 줄에 같은 숫자를 실제 인쇄한 것(3방법 확인). | **+87.00 · −242.27 · census 2 · −242.74** |
| **KR0075 BNP카디프** | **2025.1Q** | `3_tier2_composition` · `47_tier2_census`(전·후) · `51_tfi_tier2_composition` | 〃 `min(34,759, 34,759) + 30,450 = 65,209` vs 인쇄 `40,878`(raw FY2025_Q1 p20). 이 분기는 다리가 닫혀 `2_tier1_bridge` 를 박제하지 않았다. | **−243.09 · census 2 · −243.31** |
| **KR0087 동양생명** | **2025.2Q** | `2_tier1_bridge` · `47_tier2_census` | **헤드라인표가 자기 각주 주1) 을 어긴다.** 주1) 은 "순자산에서 불인정 항목 … 및 재분류 항목을 차감" 이라 써 놓고 인쇄값은 불인정 1,188 을 안 뺐다: `33,001 − 1,188 − 18,883 = 12,930` vs 공시 `14,118`, `33,001 − 0 − 18,883 = 14,118` 정확 일치. 순자산은 자기 7행 합과 일치, 기본자본은 TFI 표 p16 로 재확인. 대조군: 2025.1Q·2024.4Q(둘 다 item12=0)는 정확히 닫힌다. `TIER2_DUPLICATE_ROW` 도 같은 뿌리(한도적용전 자리에 한도 1,210,705 를 인쇄 → `max(0,47−48)=0`). | **+1,188.00 · census(잔차없음)** |

*계열 ③ 발행사가 표 구성을 달리 쓴다 — 우리 식이 짧은 게 아니라 그 발행사만의 관행 (1버킷 2 finding, 2026-08-24 iter-7 신설)*

| company | quarter | rule id | 사유 | 박제 잔차 |
|---|---|---|---|---|
| **KR0032 NH농협손해** | **2025.4Q** | `3_tier2_composition` · `51_tfi_tier2_composition` | **이 발행사는 `보완자본 한도 적용 전`(item47)을 후순위채무 제외 기준으로 인쇄하고 그만큼을 메모행 `(기발행 후순위채무)`(item54)로 따로 적는다.** raw FY2025_Q4 p46: `697,899(47) + 447,254(49) + 94,959(54) = 1,240,112` = 인쇄된 보완자본, 마지막 자리까지 정확. 두 번째 해석도 같은 결론(`697,899 + 94,959 = 792,858 < 한도 801,952`). **iter-6 에는 '우리 식에 항이 빠졌다'고 보고 등재를 거부했는데, item54 가 적재된 뒤 전수 시뮬이 그 판단을 반증했다** — `item51 == min(47,48)+49+item54` 를 전 버킷에 강제하면 **새로 닫힘 1 · 새로 깨짐 218**(대다수 회사는 item47 이 이미 후순위채무를 포함). 공통식이 아니라 이 발행사의 관행이다. **해제조건**: 박제 셀에 item54(949.59)를 넣었으므로 그 값이 움직이거나 결측이 되면 자동 RED. | **+949.47 · +949.59** |

*계열 ④ **인과 미규명 — owner 가 원문을 직접 보고 오차를 용인** (1버킷 1 finding, 2026-08-24 신설)*

> **이 계열은 위 셋과 근거의 종류가 다르다.** ①~③은 "발행사가 같은 개념을 두 값으로 인쇄했다"
> 를 **산수로** 증명한다. ④는 **잔차가 실재하는데 원문 어디에도 그 항목이 없다.** 남는 근거는
> owner 가 raw 를 직접 열어 보고 설명이 없음을 확인한 뒤 원문 그대로 오차를 용인하기로 결정한
> 것뿐이다. 그래서 원장 status 를 `VERIFIED_BY_OWNER` 로 따로 갈랐고, 게이트가 **매 실행**
> `EXEMPTION_STANDS_ON_OWNER_JUDGEMENT` review 로 인쇄한다(조용해지지 않는다).
> **이 status 는 선례가 아니다** — 다른 회사·분기에 같은 사유를 복사하지 말 것.

| company | quarter | rule id | 사유 | 박제 잔차 |
|---|---|---|---|---|
| **KR0068 한화생명** | **2025.2Q** | `2_tier1_bridge` | 각주 주2)의 정의로 다리가 안 닫히는데 **차액에 해당하는 항목이 원문에 없다.** raw FY2025_Q2 p17(억원): `213,475 − 30,921 − 100,874 = 81,680` vs 인쇄된 기본자본 `82,506`(차 826). 헤드라인은 자기 안에서 닫히고(`221,809 = 82,506 + 139,303`) 순자산도 자기 구성행 합과 맞는다(213,476, 반올림 1). p18 TFI 도 마스터와 전부 일치하고 구성식이 닫힌다. **owner 2026-08-24 raw 직접 판독 후 결정**: "차이가 있는 건 사실인데 원문이 그렇게 적혀 있고 별다른 언급은 없다 — 원문대로 오차 용인." | **−30,095.00** ⚠️ |

> ⚠️ **박제값이 owner 에게 제시된 숫자(826)와 다르다 — 고치지 말 것.** 같은 축의 같은 불일치를
> 각주 괄호("보완자본 한도를 초과한 금액을 제외")를 어떻게 읽느냐로 다르게 잰 값이다.
> ① 한도초과 = 0 으로 읽으면 `213,475 − 30,921 − 100,874 = 81,680` vs `82,506` → **+826.00**
> (owner 에게 제시된 숫자) ② 룰이 실제로 쓰는 읽기 `한도초과 = min(item47−item48, item12) =
> min(70,821.29, 30,921) = 30,921` 로 읽으면 `213,475 − 0 − 100,874 = 112,601` vs `82,506` →
> **−30,095.00**(`branch=CAPPED`). **박제는 룰이 emit 하는 값이어야 재검산이 성립한다** —
> 826 을 박으면 등재 즉시 `TIER2_EXEMPTION_RESIDUAL_DRIFT` RED 가 되어 면제가 아예 성립하지
> 않는다(실측 확인). 두 값은 원장 `expected_residual` / `expected_residual_alt_reading` 에 **둘 다**
> 적혀 있고 `test_the_two_readings_of_the_hanwha_residual_are_both_recorded` 가 강제한다.
>
> **미규명 단서(설명이 아니다)**: `item51 후 140,128.28 − 전 139,302.53 = 825.75` 가 ①의 필요
> 잔차 826.00 과 반올림 이내로 같다. **우연일 수 있고 owner 도 원인을 못 찾았다** — 사유로
> 쓰지 않는다. 후속 티켓 `inbox/validation/20260824T0410Z` 는 **열어 둔다**(면제는 push 를 푼
> 것이지 원인을 닫은 것이 아니다). 인과가 규명되면 등재를 재검토한다.
> **해제조건**: 다리 입력 4칸(item2·4·12·13) 중 하나라도 움직이거나 결측이면 자동 RED. 갈래를
> 정하는 item47·48 과 단서 item51(전·후)도 박았다. 갈래가 `CAPPED` 를 벗어나면 flag 대조가 잡는다.

> **blanket skip 이 아니다 — 이 면제는 두 겹이다.** `_TIER2_ISSUER_INCONSISTENT`
> (`scripts/validate_kics_disclosure.py`)가 ① **raw 로 판독한 마스터 셀** 과 ② **그 축이 실제로
> 내는 RED 의 잔차·사유** 를 둘 다 박아 두고 매 실행 재검산한다. 셀이 움직이면
> `TIER2_EXEMPTION_INPUT_DRIFT`, 결측이면 `TIER2_EXEMPTION_INPUT_MISSING`, 잔차·사유가 움직이면
> `TIER2_EXEMPTION_RESIDUAL_DRIFT` RED 로 **즉시 되살아난다**. RED 가 사라지면
> `TIER2_EXEMPTION_INERT` review 로 "등재를 풀어라" 가 찍힌다. ①만 있으면 룰 변화를, ②만 있으면
> 데이터 변화를 못 본다. finding 자체는 안 지운다(report `tier2_issuer_inconsistent_exception.
> exempted_findings`).
> 근거 원장: `data/_gold/kics_exemption_provenance.json` **18건** — 17건 status `VERIFIED`,
> 1건(KR0068) `VERIFIED_BY_OWNER`. **두 status 모두 `present_markers` 마커 검사를 똑같이 받는다**
> — owner 판단은 "이 잔차를 용인한다" 이지 "숫자를 다시 안 봐도 된다" 가 아니다. 게이트가 매 실행
> 그 페이지를 열어 재대조한다(등재 전 18건 전수 기계검증 통과, provenance RED=0).
> 상주 변이시험: `tests/test_tier2_issuer_inconsistent_exemption.py` **47건.**
> **데이터계약 게이트에도 같이 위임했다** — 룰만 위임하고 면제를 안 위임하면 두 게이트가 같은
> finding 을 놓고 다른 대답을 한다(등재 직후 실측: `validate_data_contract.py` RED 25 중 21건이
> 그 divergence였다 → 위임 후 RED 4). 재구현이 아니라 **같은 함수를 부른다**(테스트가 강제).
> **해제 조건**: 발행사가 정정공시를 내면(코리안리·롯데 2026.1Q), 또는 표가 안 닫히는 원인이
> 규명되면(BNP·동양·롯데 2024.4Q/2025.1Q) 등재를 푼다.

> **⚠️ 일부러 등재하지 않은 것 — 이 면제는 넓히지 않았다(`test_the_exemption_is_narrow_...` 가 강제):**
> - ~~KR0032 NH농협손해 2025.4Q~~ — **2026-08-24 (iter-7) 에 계열 ③ 으로 등재됐다**(위 표).
>   iter-6 의 "우리 식에 항이 빠졌다" 는 판단이 전수 시뮬로 반증됐다(새로 닫힘 1 · 새로 깨짐 218).
> - ~~KR0004 예별손해 2025.1Q~~ · ~~KR0075 BNP카디프 2024.3Q~~ · ~~KR0003 롯데손해 2023.1Q~~ —
>   **2026-08-24 2차 owner 위임으로 전부 등재됐다**(위 표). 셋 다 raw 확증은 이미 끝나 있었고
>   1차 위임 목록에 없다는 이유만으로 두 라운드를 RED 로 버텼다.
> - ~~KR0068 한화생명 2025.2Q~~ — **2026-08-24 owner 가 raw 를 직접 열어 보고 등재를 결정했다**
>   (계열 ④). **인과는 여전히 미규명**이고 후속 티켓은 열려 있다.
> - **KR0032 NH농협손해 2024.3Q** — 다리 잔차 −522. **미조사**라 RED 유지. 조사 전 등재는 근거가
>   아니라 추측이다. 다음 라운드.
> - **KR0008 삼성화재 2025.3Q** — **면제 대상이 아니다.** owner 2026-08-24 결정: "자기모순이
>   자명하니 우리가 올바른 숫자로 고쳐서 올린다" → parser 정정 중(`inbox/parser/20260824T0400Z` §G).
>   등재하면 고쳐진 뒤에도 죽은 핀이 남아 "그 축은 면제됐다" 로 오독된다.
>   (`test_the_exemption_is_narrow_...` 가 이 두 버킷을 기계로 막는다.)

**🔴 신규 blocking RED 18건 (2026-08-24 iter-7) — documented exception 아님, parser 발주 중.**

item52/53/54 에 룰을 배선하자 **GREEN 이던 18칸이 RED 로 뒤집혔다.** 전부 raw PDF 로 원인을
확정했고 `inbox/parser/20260824T0400Z__validation__MULTI__item52_54_load_defects.md` 로 발주했다.
배선 전에는 이 항목들을 보는 룰이 하나도 없어서 조용히 통과하고 있었다(47/48/49 때 1,285칸이
통과한 것과 같은 형태).

| 버킷 | RED | 성격 | 조치 |
|---|---|---|---|
| KR1098 카카오페이 2023.1Q~2024.1Q (5) | 10 | **item52 가 100배** — 로더의 `ALL_ZERO_TRIVIAL` 스케일 단축이 47/48/49/51 이 전부 대시라 "스케일 무관"으로 판정했는데 같은 표의 item52 는 0 이 아니었다. 같은 버킷 item50 은 다른 로더가 실어서 정확 | parser 수정 |
| KR0100 처브라이프 2023.1Q | 1 | item54=840.06 인데 **원문은 대시** — 없는 값 | parser 수정(→ 0.0) |
| KR0104 농협생명 2024.3Q | 1 | item53/54 **적용후 값이 원문에 없다**(메모행이 적용전 칸에만 인쇄됨) | parser 수정(적용후 삭제) |
| KR0083 푸본현대 2024.3Q | 1 | **컬럼 오배정** — 적용전 값 40,000/505,185 가 적용후 칸에 들어감 | parser 수정 |
| KR0003 롯데 2026.1Q · KR0087 동양 2024.1Q · KR0097 하나생명 2025.2Q | 3 | **행 유실** — 롯데는 라벨이 `(기발행 신〮자본증권)`(U+302E 혼입), 하나생명은 대시 미인식, 동양은 미상 | parser 수정 |
| KR0087 동양생명 2024.3Q | 1 | item54 유무를 페이지 텍스트로 확정 못 함 | **parser raw 재판독 회신 대기** — 공란 확정되면 validation 이 레지스트리 등재 |
| KR0008 삼성화재 2025.3Q | 1 | **발행사 자릿수 전치** — raw p16 `28,650,195 / 28,605,195` 인데 같은 표 비율 275.92/275.92 불변 + 각주가 전후 동일. 28,605,195/10,383,339 = 275.49% ≠ 275.92% | **owner 2026-08-24 결정: 면제 아님, 고친다.** "자기모순이 자명하니 올바른 숫자로 우리가 고쳐서 올리자" → **parser 정정 중.** 고쳐지면 이 축이 저절로 닫힌다 — **면제 등재 금지** |

**A~G 를 고치면 blocking RED 19 → 1**(NH농협 2024.3Q 미조사 1건만 남는다).

> **2026-08-24 2차 owner 위임 등재 후 실측:** blocking RED **29 → 19**
> (예별손해 2025.1Q 1 · BNP카디프 2024.3Q 5 · 롯데손해 2023.1Q 3 · 한화생명 2025.2Q 1 = **10건 면제**).
> 남은 19 = 위 표의 parser 발주분 18 + NH농협 2024.3Q 1.
> `validate_data_contract.py` RED **7 → 5**(전부 위 표의 parser 발주분, display 분기 필터 통과분만).

**✅ Derivation not reproducible — documented exception (owner 2026-08-21, 잔차 박제형):**

| company | quarter | rule id | 사유 | 박제 잔차 (적용전=적용후) |
|---|---|---|---|---|
| **KR0073 교보생명** | **2025.2Q** | `36_irr` + 게이트 `TRANSITION_AFTER_IRR_MISMATCH` | 표준 도출식이 공시 금리위험액을 재현 못 함. item36·41-46 **둘 다 원문 그대로**(FY2025_Q2 raw p21: 순자산가치 6열 `-5,667,711 … -5,742,051` · Ⅳ.금리위험액 `459,988` = 마스터와 백만원↔억원 정확 일치). item36 은 `item19 = sqrt(36~40·MARKET_M)` 축에서 상대잔차 −0.0000% 로 닫힌다. **하한 위반**: 금리상승 단일 충격량 684,627 백만원 > 공시 459,988 → 어떤 합성식으로도 닫힐 수 없다(같은 기준의 표가 아님). 원인 `UNEXPLAINED`. | **+241.4374** (+5.25%, tol 0.01) |
| **KR0094 신한라이프** | **2024.2Q** | 〃 | raw p22 순자산가치 6열 · Ⅳ `750,104` 정확 일치. p23 주2 = 2024년 작성기준 변경 명시. 원인 `UNEXPLAINED` (아래). | **+1,287.8296** (+17.17%) |
| **KR0094 신한라이프** | **2024.4Q** | 〃 | raw p144 순자산가치 6열 · Ⅳ `633,214` 정확 일치. 같은 페이지 주2. | **+1,622.0506** (+25.62%) |
| **KR0094 신한라이프** | **2025.2Q** | 〃 | raw p28 · Ⅳ `931,833` 정확 일치. **주2 없음**인데 잔차 잔존. | **+698.1840** (+7.49%) |
| **KR0094 신한라이프** | **2025.4Q** | 〃 | raw p131 · Ⅳ `578,999` 정확 일치. **주2 없음**인데 잔차 잔존. 2026-08-21 에 `INTERNAL_MODEL_36IRR_EXEMPT` 에서 해제된 건(그 등재사유는 거짓이었다). | **+863.8221** (+14.92%) |

> **식도 허용오차도 안 바꿨다.** owner 제안(평균회귀 충격량 0 절단)을 41-46 완비 **226버킷 전수**로
> 재측정: 현행 signed 식 **221/226(97.8%)** vs 0절단 **123/226(54.4%)**, 갈리는 102건 중 100건이
> 현행만 통과(0절단만 통과하는 2건 = 이 면제 대상 신한 25.2Q·25.4Q). **평균회귀 이익 상계가 실제
> 서식이다.** 잔차가 5~26% 라 tol 로도 못 덮는다. **룰은 다른 모든 (회사,분기)에서 RED 그대로 —
> owner 가 YELLOW 강등을 명시적으로 거부했다.**
>
> **원인은 `UNEXPLAINED` 로 기록한다. "스코프 때문"이라고 단정하지 말 것.** 신한 24.2Q/24.4Q 주2
> ("2024년부터 … 금리위험에 직·간접적으로 노출된 자산 및 부채를 대상으로 작성")는 작성기준 변경을
> 명시하지만 잔차를 기계적으로 설명하지 못한다 — 금리 비민감 항목은 충격전·5시나리오 **모든 열에
> 동일 금액**으로 들어가 열 간 차이(=충격량)에서 상쇄된다. 게다가 그 주2 가 **없는** 25.2Q·25.4Q 에도
> 잔차가 남는다(+7.49% · +14.92%).
>
> **blanket skip 이 아니다.** `IRR_DERIVE_ISSUER_INCONSISTENT`(src/solvency/validation/kics_json_rules.py)
> 가 기대잔차를 들고 있고, **적용전(룰엔진 `36_irr`)·적용후(`_transition_irr_after`) 두 축이 각각**
> 매 실행 재계산한다. item36 이나 41-46 중 한 칸이라도 바뀌면 `IRR_EXEMPTION_RESIDUAL_DRIFT`,
> 결측이 되면 `IRR_EXEMPTION_INPUT_MISSING` 으로 **양쪽 다 RED 복귀**. 잔차가 반대로 룰 허용오차
> 안으로 들어오면 `IRR_EXEMPTION_INERT` review 로 "등재를 풀어라"가 찍힌다.
> 근거 원장: `data/_gold/kics_exemption_provenance.json` 5건, **status `VERIFIED`**(이 PDF 들은
> 텍스트레이어가 정상 — 인용 페이지 1,829~3,093자/p 로 image-only 반증 임계 800자/p 를 크게 넘어
> `VERIFIED_BY_IMAGE` 를 쓸 이유가 없다). `present_markers` 에 원문 수치 자체를 넣어 게이트가 매
> 실행 그 페이지를 열어 재대조한다.
> 상주 변이시험: `tests/unit/test_irr_pin_exemption.py` 9건(pre-push 훅에 포함).
> **해제 조건**: 발행사가 재현 가능한 표를 내거나, 재현 불일치의 원인이 규명되면 등재를 푼다.

**✅ Structural non-disclosure — documented exceptions (parser-confirmed; image/scan/micro, 추출 불가):**
- **36_irr × 12** (item36 공시인데 순자산가치 6시나리오표 추출불가):
  - KR0010 KB손해 2023.4Q·2024.2Q·2025.4Q — 금리위험액 현황표가 **full-page 이미지**(p75-76 imgs=1,text=0; "금리는 내부모형" 주석). owner OCR.
  - KR0051 신한이지 2023.4Q·2024.2Q·2024.4Q — micro-insurer, 순자산가치 **억원-coarse 정수**라 derive ±99% 불안정(원천 한계).
  - **KR0004 예별손해(구MG) 2023.2Q·2023.4Q·2024.2Q·2024.4Q·2025.2Q·2025.4Q (짝수 6분기)** — item36(금리위험액) 공시이나 **충격시나리오별 순자산가치(41-46) 표 미공시**(소형 부실사; MD 전체에 평균회귀/금리상승 라벨 부재, fill_market_irr 회수 0). IRR detail 결측 = legit-absent.
- **19_market × 7** (item19 공시인데 36-40 분해 추출불가):
  - KR0005 흥국화재 2024.4Q·KR0071 흥국생명 2024.4Q — raw에 시장위험 분해표 NO-HEADER(이미지/미공시).
  - KR0010 KB손해 2024.4Q·2025.2Q — 금리위험액 이미지(주식/부동산/외환만 텍스트, 5종 reconcile 불가).
  - KR0068 한화생명 2023.4Q·2025.2Q — 금리위험액 현황 표 본문 이미지(헤더만 텍스트; 2025.2Q diff=60,815 = 금리 결측 탓).
  - KR0080 AIA 2025.4Q — scan-only(아래 documented).
  - **KR0083 푸본현대 2025.2Q (TEMPORARY, wrong-PDF)** — FY2025_Q2 PDF가 KR0075(BNP파리바카디프)와 sha256 동일(오파일). 코어 1-28은 25.3Q MD 직전분기컬럼서 교정(318%→−10.13), subs 36-40은 정본 PDF 대기 → downloader `20260703T1250Z`. **정본 재파싱 시 해소(구조적 미공시 아님).** 상세=위 2026-07-03 owner 워크스루 (1).
- **rule 2 × 1**: KR0080 AIA 2025.1Q (diff=−789) — scan-only(아래 documented).
- **rule 1 × 1**: KR0004 예별손해 2024.2Q (item1 3,572 ≠ item2 498 + item3 3,085 = 3,583, diff 11) — **소스 충실**(MD L268-270 그대로). 부실사 보완자본 한도초과/억원 반올림으로 지급여력금액이 단순합과 불일치 = 공시 자체 특성, 파싱오류 아님. 인접 분기는 diff<tol이라 미발화.
- **rule 8_life × 1**: KR0079 미래에셋 2023.2Q — scan-only. **8_life는 SKIP=게이트 비차단**.
- **경과조치 적용후 요구자본(15-23) × 1(회사,분기) = KR0049 악사손해 2024.3Q (2026-08-20, parser)** —
  그 분기 공시서에 **지급여력비율 섹션이 통째로 없다**: "지급여력비율은 2024년 12월말 공시 예정임
  (보험업감독규정 부칙 제3조)" (raw p3 주요경영지표 건전성 행 공란 · p9 4-2 본문 한 줄 · p11 비례성원칙).
  JSON의 2024.3Q 값은 전부 **FY2024_Q4 공시서의 '당분기-1분기' 컬럼**에서 온 것이고, 그 공시서에서
  경과조치 적용에 관한 사항 표(p41-43)는 **당분기 전용**이며 과거분기 경과조치후를 싣는 건
  [지급여력비율 총괄](p36) 하나뿐인데 거기엔 비율·지급여력금액·지급여력기준금액 **세 줄만** 있다.
  → items 15-23 값_적용후는 어느 raw에도 존재하지 않음. 가용자본측 item3후는 TIR 단독 적용(p39
  적용여부표 TAC=X·TER=X·TIRR=X) + 4Q 서술 "지급여력금액 증감은 경과조치 전과 동일" → 전=후로
  확정해 채움. 게이트 등재 = `validate_kics_disclosure.py` `_POST_PARENT_NOT_DISCLOSED`.
  **staleness 재확인(2026-08-22, parser, `inbox/parser/20260821T1425Z` iter-7)**: "공시예정" 지문은
  2024.3Q 시점 것이고 지금은 2026-08 라 owner 의심대로 유예가 끝났을 가능성을 재점검했다 — 실제로
  item1/2/14/27/28은 이미 그 유예 종료 후 필링(FY2024_Q4)에서 복구돼 있다(2026-07-07,
  `inbox/_resolved/20260707T0050Z`). 그런데 **15-23후 자체는 여전히 어느 필링에도 없다**:
  FY2024_Q4(p41-42)·FY2025_Q1(raw 재확인)·FY2025_Q4(raw 재확인) 전부 [지급여력비율의 경과조치
  적용에 관한 사항] 표를 "경과조치 적용 전/후" 2열만 인쇄하고(당해 분기 자체의 전후 비교이지
  분기간 이력비교가 아님), 이 표는 KR0001 메리츠화재 FY2024_Q4에서도 동일하게 2열 구조라
  회사 특이 아니라 서식 자체의 구조적 제약. 즉 **staleness 재검토 결과는 "이미 반영됨"** — 신규
  결측 아님, 등재 유지가 맞다.
  **같은 원인이 신규 항목 47-49(보완자본 한도 적용전/한도/해약환급금 초과분, 2026-08-21 신설)에도
  동일 적용**: 15-23후와 정확히 같은 이유(section-absent 원본 + 당분기-only 복구표)로 AXA
  2024.3Q 의 47/48/49 전·후 6셀도 raw 어디에도 없다. `kics_disclosure.json`엔 12/13분기만 있고
  2024.3Q만 결측(정상). 신규 로드 대상 아님 — 위와 동일한 `_POST_PARENT_NOT_DISCLOSED` 사유로
  묶어 문서화만 해 둔다(별도 셀 적재 스크립트 없음, 로드할 값 자체가 없다).
- **2023.2Q 백필 잔여 (2026-06-15, docling 부활)**:
  - KR0087 동양생명 2023.2Q — 코어표 **이미지 전용**(텍스트 부재) → scan-only(KR0079/0080/0087 동류), census 갭.
  - KR1098 카카오 2023.2Q rule7 + 19_market — **micro-insurer**(item19=5억·item14=15억·천원 스케일): 비율 derive가
    초소형 분모 반올림으로 62%p 어긋남(공시 item27=2155.62 정확) + 36-40 nn=2 → micro artifact(신한이지류). documented.
- **census 결손 → owner OCR (2026-06-15, publishing `20260614T2313Z` 처리, docling 부활)**:
  - **KR0097 하나생명 2024.2Q** — 그 분기 공시본이 **이미지 PDF**(14.7MB; regex·pdfplumber·fitz 3중 확인 코어표
    텍스트 부재). 나머지 12분기 텍스트 정상. owner OCR/gold (downloader 텍스트본 재취득 가능성 확인).
  - **KR1098 카카오 2023.4Q·2024.2Q·2024.3Q·2024.4Q** — 이미지 PDF(동일 3중 확인). 2025.2Q/3Q는 텍스트로 적재됨
    = 비공시 아님, 이미지라 OCR뿐. **expected-absent 화이트리스트 아님.**
  - 카카오 2025.3Q rule6 = micro 반올림 artifact(documented).
  - ✅ **적재 완료**: 카카오 2025.2Q(28/28)·2025.3Q(27/28) 코어 + 2025.2Q 시장위험.
- **서울보증(KR0150) 과거 interim = expected-absent (census 화이트리스트, 2026-06-15)**:
  2023.1Q/2Q/3Q · 2024.1Q/2Q/3Q · 2025.2Q/3Q **= refetch 불가 구조적 gap**. 서울보증 자체 공시실(sgic.co.kr)은
  **연간(Q4)+최근분기만** 노출, 과거 Q1-3 PDF 롤오프(서버 부재). 미상장이라 DART도 없음. downloader가
  2026-06-01 `SGI_QUARTERLY_STRUCTURAL`로 등록(audit_all_periods.py:39-43) + 2026-06-15 재확인 resolved.
  present = 2023.4Q·2024.4Q·2025.1Q·2025.4Q·2026.1Q(연간+최근) 정확. **K-ICS census도 이 8분기 결손은 무시.**

**🔴 INTERNAL_MODEL_36IRR_EXEMPT — 2026-06-14 owner 승인분 전건 해제됨 (2026-08-21, 등재사유 raw 대조 결과 거짓).**
- **원 사유(2026-06-14)가 틀렸다.** "내부모형사라 시나리오별 금리위험액을 직접 공시, 그 값을 표준식에
  넣으면 정확 일치" — validation이 5건 전부 raw(fitz 텍스트+240dpi 렌더링)를 재확인한 결과 **두 전제 모두
  거짓**: ① 5건 전부 표준서식 `[② 금리위험액 현황]` 표를 그대로 싣고(순자산가치 6-시나리오 행 완비,
  즉 항목41-46 원천이 실재 — 마스터에 없던 건 추출갭이지 원천부재가 아니었음) ② `Ⅳ.금리위험액`은
  시나리오별로 안 쪼개진 단일 병합셀 ③ KR0094는 스스로 "표준모형사"라고 명시(FY2025_Q4 raw p135).
  `kics_json_rules.py`의 `INTERNAL_MODEL_36IRR_EXEMPT`를 validation이 빈 frozenset으로 해제(코드 주석에
  전체 근거 인용 보존).
- **parser(kics) 2026-08-21 후속** (`inbox/parser/20260821T1600Z`·`20260821T1620Z`, `scripts/fix_20260821_
  36irr_and_hana_post.py`): 5건 전부 raw에서 items 41-46(금리위험 순자산가치 6-시나리오)을 **당기(현재
  분기) 컬럼**으로 직접 로드 — 오케스트레이터 최초 조사가 신한 2025.4Q에서 전기(비교)열을 당기로 오독한
  실수를 발견/정정(같은 페이지에 당기/전기 두 표가 붙어 있어 값이 2배 가까이 다름), 2개 필링(신한
  2024.4Q·2025.4Q)은 같은 문서 안 별도 섹션(B.2.1, 천원 단위)의 독립된 표로 교차검증.
  값: KR0073 25.2Q(raw p21) · KR0094 24.2Q(p22)·24.4Q(p101/144)·25.2Q(p28)·25.4Q(p95/131) — 5건 전부
  기존 item36과 이미 일치(변경 없음), 항목41-46 30셀 신규 삽입(값=값_적용후, 두 회사 모두 이 축 미신청/
  비적용이라 후=전이 정의상 정상).
- **여전히 GREEN 안 됨 — 별개의, 진짜 미해결 질문.** 게이트의 36_irr derive식(item41 base, sqrt(max(상승,
  하락)²+max(평탄,경사)²)+평균회귀)으로 재현하면 공시 금리위험액과 **5.25%~25.6%** 벗어난다(교보25.2Q
  +5.25%·신한24.2Q +17.17%·24.4Q +25.62%·25.2Q +7.49%·25.4Q +14.92%, `run_validation` 실측). 유력 원인
  후보: KR0094 raw p144 주2 "2024년부터 금리위험액 현황의 자산 및 부채는 금리위험에 직·간접적으로 노출된
  자산 및 부채를 대상으로 작성"(스코프가 전체 자산부채가 아니라 금리노출분 한정) — 단 **미확정**, 값을
  억지로 맞추지 않았다(추측·보간 금지 원칙). **현재 상태: 5건 모두 RED**(신한24.2Q는 `_DISPLAY_QUARTERS`
  밖이라 push 게이트 비차단, 나머지 4건은 차단) + 완전성 확보의 부수효과로 `TRANSITION_AFTER_IRR_MISMATCH`
  4건도 새로 노출(item36후=item36 mirror이므로 같은 잔차가 후 컬럼에도 나타남 — 새 결함 아니라 이전엔
  41-46후 결측이라 미판정이었을 뿐). **owner 결정 대기**: 새 면제(예: 노출자산부채 한정 스코프 인정) 등록
  여부 또는 허용오차 조정 — parser·validation 둘 다 임의 등재 안 함(계약).

**✅ RESOLVED 2026-06-16 (카카오 2023.3Q 19_market — cadence-SKIP 아니었음):**
- 이전엔 "odd-Q NO-HEADER → validation cadence SKIP"으로 분류했으나 **틀렸다**(validation 0130Z 정정).
  `data/disclosure/FY2023_Q3/parsed/KR1098_…amended.md` L177-186에 시장위험 분해표 **실재**(시장 248/금리 15/
  부동산 244, 백만원). 파서가 item36(0.15)·item38(2.44) 적재 → 19_market **GREEN**. cadence-SKIP 불필요.
  (단 36_irr은 41-46 미공시라 별도 — 카카오 2023.3Q는 36_irr RED 아님: item36 near-0라 미발화.)

**요약 (2026-06-16, 예별 13분기 백필 후)**: **24 RED** = 구조적(documented: 36_irr 12·19_market 7·rule1 1·
rule2 1·8_life 1·rule6 1·rule7 1). +5 net = 예별 KR0004 36_irr×5(IRR 미공시) + rule1×1(예별 2024.2Q 한도/반올림),
−1 카카오 2023.3Q→2Q 19_market GREEN. ~~내부모형 0(KR0073·KR0094×4 = validation INTERNAL_MODEL_36IRR_EXEMPT
SKIP 등록)~~ **← 2026-08-21 반증·해제, 위 `INTERNAL_MODEL_36IRR_EXEMPT` 최신 항목 참조 — 이 스냅샷은 그
시점(06-16)에서만 유효했다.** census MISSING 6(동양/하나/카카오 image cells, documented). **전부 documented
→ CLAUDE.md 게이트 rule 충족(당시 기준, 2026-08-21 재검증으로 5건 재노출).** push는 owner 권한 — parser
self-approve 안 함.

**✅ 항목4/12/13(Ⅰ.건전성감독기준 순자산·Ⅱ.불인정항목·Ⅲ.보완자본재분류) 값_적용후 결측 — documented exception (2026-07-21, owner+designer/parser)**

- **대상**: 가.지급여력금액(항목1)의 세부 3항목(항목4/12/13). 값_적용후가 raw 정기경영공시 PDF에 **애초에 별도 컬럼으로 존재하지 않음**(공통적용 경과조치 표에는 항목1·2·3·14만 있고 4/12/13 행 자체가 없음 — 4개사 raw 전문 grep으로 확인, `inbox/_resolved/20260712T0704Z__designer__MULTI_2026.1Q__capital_breakdown_after_missing.md`). 2026.1Q 기준 39개사 중 21개사(DB생명·IBK연금·NH농협손해·교보라이프플래닛·교보생명·농협생명·롯데손해·아이엠라이프·악사손해·에이비엘생명·예별손해·처브라이프·케이디비생명·푸본현대생명·하나생명·한화생명·한화손해·흥국생명·흥국화재 등)에서 3개 항목 전부 결측.
- **왜 backfill 불가**: 나머지 18개사는 `값=값_적용후`로 채워져 있으나, 이건 실제 공시가 아니라 `scripts/backfill_post_transition_when_not_applied.py`가 항목1/14/27(총액/기준금액/비율) 일치를 근거로 **미러링한 추정값**. 이 스크립트 자체 docstring에 **2026-07-16 KNOWN BUG**로 명시: 항목1/14/27이 일치해도 항목2/3(기본자본/보완자본) tier 배분은 공통 TFI 경과조치로 별도로 움직일 수 있어(**기본자본비율이 5~15%p까지 이동 가능**), 이 방식으로 **KB라이프생명 2024.2Q·동양생명 2024.1Q 항목12/13이 실제로 오염**됐다가 `fix_20260716_revert_wrong_item1213_mirror.py`로 되돌린 전례 있음.
- **owner 재확인 사례 (2026-07-21)**: **KR1000 코리안리재보험 2024.4Q** — 항목1(41,813→41,812.79)·14(21,812=21,812)·27(191.697%=191.697%)는 사실상 동일한데, **항목2 기본자본 32,860→33,950(+1,090)·항목3 보완자본 8,953→7,863(−1,090)·항목28 기본자본비율 150.65%→155.65%(+5.0%p)**로 정확히 위 KNOWN BUG 패턴 재현 확인. 이 분기는 실제로 항목1 diff(0.21)가 스크립트 tolerance(0.01)를 넘어 안전-미러링 대상에서 이미 제외돼 있었음(값_적용후 결측 상태 유지) — **정상 동작 확인**, 버그 아님.
- **결론**: 항목4/12/13 값_적용후는 raw에 근거가 없고, 안전한 backfill 방법도 없음(항목1/14/27만으로는 항목2/3/4/12/13의 tier 재배분을 보증 못함). **owner 승인 하에 fix 보류 — K-ICS.html은 이 결측을 "미공시"로 명시 표시**(`NO_POST_TRANSITION_DISCLOSURE = {4,12,13}`, designer 2026-07-12 배선). 18개사의 기존 미러링값(항목1/14/27만 근거)도 코리안리와 같은 패턴으로 오염됐을 가능성 있음 — **후속 감사 필요**(범위 밖, 별도 티켓 권장).

---

> 2026-06-12 스냅샷(RED=227 = 19_market 223 + KR0049 4)은 위 CURRENT 블록이 대체함. 이력은
> `docs/changelog_validation.md` / `docs/changelog_parser_kics.md` 참조. (2026-07-21 TODO에서 제거 — 항상 로드되는 파일에 이력 중복 보관 안 함.)

---

## 🚧 CROSS-STAGE — CSM waterfall 신한EZ 제외 후속 (owner xlsx 검토 2026-06-10, 보정 06-11)

~~3사 제외~~ → **하나손해(KR0050)·하나생명(KR0097)은 복원**(자사 감사보고서 별도 변동표 실재 — 경영서술 수치와
정확 일치 검증, owner 재지시 2026-06-11). **신한이지(KR0051)만 제외 유지**: 감사보고서 변동표가 천원 단위인데
백만원 오인(×1000 인플레) + PAA 중심사로 일반모형 CSM ~2억 = 워터폴 무의미. override `data/dart/viz/csm_manual_overrides.json`.

- [x] **designer**: 완료 확인 2026-08-20 — `IFRS17.html` L604에 `PAA_ONLY = new Set(["KR0051", "신한이지손해보험"])`(코드+표시명 양쪽) 배선됨. 마스터에도 KR0051 행이 0이라 렌더 대상 자체가 없다.
- [x] **publishing**: 인지 완료. 단 **경로가 바뀌었다** — 2026-08-20 gold-overlay 통일(`71914c3`)로 `data/dart/viz/csm_manual_overrides.json` → **`data/_gold/user_csm_cells.json`**(PL은 `user_pl_cells.json`). 훅 자동 적용은 그대로.

---

## 🚧 CROSS-STAGE — K-ICS 금리민감도 신규 feature (2026-06-10 발주 → 06-12 publishing만 잔여)

경영공시 `6-8. 위험 민감도` → 금리민감도 표(경과조치 × measure × ±50/±100bp)를 신규 루트 마스터 `kics_rate_sensitivity.json`으로. 38사 서베이 완료, 스펙 정본 `docs/agents/kics-rate-sensitivity-spec.md`.

- [x] parser: 추출 스크립트 + 마스터(435행)/diag — RS1·RS2 자기검증 통과 (2026-06-10)
- [x] validation: RS1–RS4 룰 구현, 게이트 RED=0 (consolidate_inbox 핸들러 배선만 후속 잔여) (2026-06-10)
- [x] **publishing: 커밋 번들 + master xlsx 재생성** — 완료 확인 2026-08-20. xlsx 4개 시트가 마스터와 행수 일치(17BS 6,855 · 손익분해PL 8,650 · CSM워터폴 2,136 · 배당 2,043), 수식 캐시 정상. 원 inbox 티켓도 종결(`_resolved/20260612T0900Z`).
- [x] designer: K-ICS.html 민감도 패널 (F-SENS-PANEL, 커버리지 29/30) (2026-06-11)

---

## 📬 2026-06-12 — 전 스테이지 backlog digest 발송 (owner 전수 점검)

5개 스테이지 inbox에 `20260612T0900Z__owner__ALL__backlog_digest.md` 발송 (publishing/designer inbox 신설,
`inbox/README.md` layout + route `backlog` 추가). 각 스테이지는 다음 호출 시 자기 다이제스트 드레인.

---

## 중장기 목표 (Mid-long-term goals) — 신규 마스터 테이블 (cross-stage)

(2026-06-06 owner 제안. 착수 전 단계 — 소스 위치만 슥 확인. 우선순위/일정 미정.)

### MLG-1. 듀레이션갭 (Duration Gap) 지표 마스터
- **목표**: 자산·부채 듀레이션 및 듀레이션갭(금리리스크 ALM) 전사·전분기 마스터 테이블.
- **소스 확인 결과**: 정기경영공시 MD(`data/disclosure/FY*/parsed/*.md`)에 "듀레이션" 단어 **0회**(삼성화재/삼성생명/DB 확인) → 표준 경영공시엔 없음. **소스 추가 조사 필요**:
  - 1순위 후보: DART 사업보고서 주석의 **금리위험 민감도 / 자산·부채 듀레이션** 표 (사별 상이, K-ICS 금리위험액 산출 부속).
  - 2순위: 사별 IR 자료 / K-ICS 공시 부속서.
- **다음 스텝(대략)**: (a) DART 사업보고서 1~2개사(삼성화재·한화생명) 금리위험 주석에서 듀레이션 표 존재 확인 → (b) 있으면 parser 시그니처 추가, 없으면 IR 소스로 전환. PL/CSM 마스터와 동일 8-field 스키마 재사용.
- **[조사완료 2026-06-07 야간]** DART 본문(한화생명/삼성생명 주석 50)에 **듀레이션갭 서술 + 만기사다리(16버킷) + 100bp 금리민감도(손익/OCI)** 존재하나 **자산/부채 듀레이션 숫자·갭 자체는 없음**(만기+할인곡선 유도 필요). 손보(삼성화재/DB)는 sparse. → **owner 결정 필요**: (i) 100bp 민감도만 추출(직접 가능), (ii) 듀레이션 유도식 정의(만기가중/할인). 다세션 작업. 상세 → `changelog_parser.md` (j).

### MLG-2. K-ICS 요구자본 세부 도해 (시장위험액→금리위험 / 해지위험액 세부)
- **목표**: 지급여력기준금액 중 **시장위험액 하위(금리/주식/부동산/외환/자산집중)**, **해지위험액 세부**를 분해한 마스터/도해.
- **소스 확인 결과**: `kics_disclosure.json`은 top-level만 캡처(`3. 시장위험액`, `1-5. 해지위험액` 등). **하위 분해 미캡처**. 단 경영공시 MD(`data/disclosure`)에 **"금리위험"·"주식위험" 텍스트 존재**(삼성화재·DB·삼성생명 확인) → **기존 데이터에서 parser 확장으로 추출 가능 (답지 불요)**.
- **다음 스텝(대략)**: (a) K-ICS 요구자본 detail 섹션 표 확인(시장위험액 하위행: 금리/주식/부동산/외환/자산집중) → (b) 기존 K-ICS parser에 하위 항목번호(예 `3-1` 금리위험…) 추가 — 코리안리 `2-1` 시리즈처럼 문자 항목번호 패턴 재사용 → (c) validation gate에 합산검증(Σ하위 = 시장위험액) 추가.
- **[조사완료 2026-06-07 야간]** `fill_subitems_to_disclosure.py`(생명장기 1-1~1-7 파서)가 템플릿이나, 시장위험은 **통합 ①시장위험액 현황 표 부재** + 하위가 사별·위험별 **이질 표**(금리=충격전후 shock표 → 위험액 *유도* 필요·모호, 주식=헤더 embed, 부동산=합계행). clean disclosed 총액 사별 불일치(삼성화재 금리·주식만, 삼성생명 금리만, DB손해 전무). → **PL-Tier2급 사별 핸들러 다수 + 금리위험액 유도규칙 owner 결정 필요.** R11(Σ=시장위험액)은 금리 확정 후. 다세션. 상세 → `changelog_parser.md` (j).

---

## 🔀 Cross-stage follow-ups (multi-stage; detail in stage files)

| # | Task | Stages involved | Detail location |
|---|------|-----------------|-----------------|
| F12 | K-ICS 시장위험 하위위험액 전체 파싱 + 분산효과 validation | parser + validation | `TODO_parser.md` F12 + `TODO_validation.md` V3 |
| F17 | 당기순이익 분해 (Tier1 전사 + Tier2 손보 LOB) | parser + publishing (+ designer for Tier2 panel) | `TODO_parser.md` F17 (body) + `TODO_publishing.md` F17 viz + `TODO_designer.md` F17 Tier2 |
| F18 | IR factsheet 정형화 + DART↔IR cross-validation | parser + validation + publishing | `TODO_parser.md` F18 + `TODO_validation.md` V1 + `TODO_publishing.md` F18 viz |
| F13 | 재보험 영업 지표 세트 | downloader (F8) + parser + publishing | `TODO_downloader.md` F8 + `TODO_publishing.md` F13 |

## 📋 Policy / User decisions (cross-stage)

| # | Decision | Date |
|---|----------|------|
| 1 | K-ICS skip cohort: KR0029 AIG, KR0150 SGI permanent skip. KR0051 / KR0074 partial-coverage by design | 2026-05-24 |
| 2 | Meritz IR source: Meritz Financial Group factsheet xlsx (replaces Meritz Hwajae standalone). AIG IR: skip low-priority | 2026-05-24 |
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료**. IR PDF for 6 cos; assoc crawl (KIDI/KLIA/KNIA) for 23-co computed multiple | 2026-05-24 |
| 4 | First HTML viz: CSM Movement Waterfall (IFRS17 A1 23-co) | 2026-05-24 |
| 5 | API keys: repo root `.env` only (gitignored). Never commit/log key values | 2026-05-24 → `TODO_downloader.md` D5 |
| 6 | Bond Call rule: issue + 5y for ALL bonds. Past 5y = assume `called` | 2026-05-24 → `TODO_downloader.md` D6 |
| 7 | Pushing: subagent **reports + recommends only**. Human runs `git push` | 2026-05-30 |
| 8 | DART attachments (별첨/감사보고서 zip): **don't fetch**. Body XML has all IFRS17 disclosures | 2026-05-30 → `TODO_downloader.md` DL-NOATTACH |

## 🌐 Universe (cross-stage)

- **K-ICS**: 38 insurers (`kics_disclosure.json` `원수사명`); skip cohort KR0029/KR0150
- **IFRS17**: 28 insurers (`src/ifrs17/universe.py`) — 23 listed + 5 foreign-affiliate life via audit reports (F11, `AUDIT_REPORT_ANNUAL`, annual-only). Historical 13Q cohort = 23 listed.
- **K-ICS↔IFRS17 mismatch**: AIA (에이아이에이생명보험) is in IFRS17 universe but NOT in `kics_disclosure.json`. Cohort joins must handle this.

## ✅ Done — cross-stage anchors

| ID | Task | Notes |
|----|------|-------|
| ~~F1~~ | index.html → IFRS17 cross-nav | `fcdd544`. ECharts on('click') → URL param + auto-select. Data hook = publishing; HTML = designer |
| ~~F3~~ | CSM 상각 schedule 전수 조사 | `4b06492`. 19/24 → 22/24 ok |
| ~~F5~~ | No-bond insurer forward sim 추가 | `b02e24d`. 24 → 37 cohort |
| ~~F6~~ | CSM 상각 schedule yearly granularity | 2026-05-28. 16 yearly / 6 coarse / 2 no-data |
| ~~F11~~ | 외국계 생보 5사 IFRS17 추가 | DONE 2026-05-29. 23→28 (생보 13→18). corp_codes: 라이나 00504232 / 메트라이프 00171104 / AIA 01295517 / 하나생명 00187123 / 처브 00203102. universe.py `AUDIT_REPORT_ANNUAL`. NOTE: AIA not in kics_disclosure.json |
| ~~IFRS-Q~~ | Open Q1-Q9 | done. All 9 confirmed |

## 📚 Long-term / roadmap

> 📈 **중장기 제품·수익화·전략 로드맵 → `docs/roadmap.md`** (2026-05-26 신설)

Active long-term tracks now live in their respective stage TODOs:

- **IFRS17 bubble + market map evolution** → `TODO_publishing.md` (data) + `TODO_designer.md` (HTML)
- **Forward solvency simulation** → `TODO_publishing.md` (KICS-FORWARD-CAPITAL done v3 archive)
- **Roadmap §1A-2 priority 6 추가지표** (요구자본 위험액 분해 / RA / P&L 보험·투자 분해 / 출재율 / 유지율 / 운용자산이익률) → distributed across parser + publishing
- **Roadmap §1E 규제 뉴스 피드** → `TODO_downloader.md` F14

## 🧾 Meta

- Encoding rule: `CLAUDE.md` "Document/TODO Encoding Rule" added 2026-05-24
- .gitignore: `data/dart/raw/`, `data/dart/reports/` excluded
- 2026-05-25 doc trim: changelog 124KB→11KB (latest 5 entries detailed + historical archive 1-liners)
- git: initialized + pushed to github.com/solvencyk/insurequant (main). GitHub Pages → solvencyk.github.io/insurequant
- 2026-05-26: `docs/roadmap.md` 신설
- 2026-05-28 HTML single-source refactor (P1+P4): templates/*.html 4개 삭제. ⚠️ 데이터 JSON 중복 남음 (P2)
- 2026-05-28 모바일 반응형 M1/M2 적용
- 2026-05-28 IFRS17 패널 정리: 파생 KPI 카드 + BS 스냅샷 제거 → `docs/archived_metrics.md`
- 2026-05-30j Reorg #2: `data/assoc` → `data/_derived`, KIDI/DART → `FY####_Q#`. DART batch script refactor 잔여 → `TODO_downloader.md`
- 2026-05-30k 5-stage workflow split (downloader/parser/validation/gathering/pushing 초안)
- 2026-05-31 Stage 2/3/4/5 split fully populated: parser/validation TODO+changelog (오전), publishing(=gathering+pushing 머지)+designer(MOB/VIS HTML 별도 stage) TODO+changelog (오후). Root TODO is now genuinely cross-stage only

## ✓ MVP checklist (IFRS17)

- [x] A1 A2 A3 A4 B1 B5 all 23/23 MVP (B5 K-ICS primary ingest done FY2025_Q4)

## 🎯 Next priorities (cross-stage)

1. **KICS-IMG manual OCR** (user-owned): KR0010 KB Sonhae rule 2 ×2 — only remaining RED. Parser policy → `TODO_parser.md`; validation gate exception → `TODO_validation.md` V6
2. **F17 decision**: 9/11 손보 Tier2 LOB commit vs debug 삼성·DB vs IR-clean only. Parser detail → `TODO_parser.md`. Tier2 panel rendering → `TODO_designer.md` after decision
3. **F18 activation**: parser delivers IR JSON → V1 validation rules activate → publishing assembles cross-source viz
4. **REORG2-DART**: 3 batch scripts canonical-layout refactor → `TODO_downloader.md`
5. **Stage prompts 마무리**: parser / publishing / designer prompts still skeleton (TBD bodies); validation + downloader prompts are owner-authored complete
