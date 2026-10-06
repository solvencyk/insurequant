# K-ICS 정기경영공시 분기 라운드 — 실행 순서

> 2026.2Q 라운드(owner 지시 2026-08-30) 때 루트 `TODO.md` 「상시 점검」에 있던 절차를 2026-10-07 **무수정으로** 옮겼다. 그 라운드는 끝났다(2026.2Q 39사 적재).
> 다음 분기에는 기간 라벨과 스크립트 이름(`FY2026_Q2`, `*_2026q2_*`)을 그 분기로 바꿔 쓴다. 게시 현황·날짜 서술은 2026-08-30 기준이다.
> 그 뒤 바뀐 것: 아래 "생보 2Q 스크립트가 아직 없다" 는 해소됐다 — `download_disclosure_2026q2_life.py`(협회 일괄) + `download_disclosure_2026q2_life_sites.py`(자사 사이트에 먼저 올린 회사)를 복제해 쓴다.

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
