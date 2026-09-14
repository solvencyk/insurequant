# TODO archive — `TODO.md` (Status 이력, 읽기 지연)

> `TODO.md` 의 Status 이력 블록을 2026-09-11 에 **한 글자도 고치지 않고** 옮긴 것(최신순). 세션 시작 시 읽지 않는다 — `docs/changelog_*.md` 처럼 특정 과거 결정의 배경이 필요할 때만 연다. 활성 TODO 의 Status 에서 밀려난 항목은 이 줄 바로 아래에 그대로 잘라 붙인다(최신이 위).

---

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

