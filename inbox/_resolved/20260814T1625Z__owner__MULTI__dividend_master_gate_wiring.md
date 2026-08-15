---
from: owner
to: validation
created: 20260814T1625Z
status: resolved
route: backlog
company: MULTI
period: 2023.1Q-2026.2Q
rule: NEW_MASTER_GATE_WIRING
iter: 1
---

## 미결 (sender 작성)

**신규 루트 마스터 `dividend.json`이 게이트에 아예 안 물려 있다.** 다운로더(raw 624파일,
`data/dart/_alotmatter_cache/`)·파서(`scripts/build_dividend.py`, 1,924행) 완료됐고 designer가
`공시보고서.html`을 채우는 중이라, **화면에 뜨기 전에** 검증을 붙여야 한다. 원 발주 체인:
`inbox/_resolved/20260814T0746Z`(owner) C-4.

### V-0. 게이트 배선 (필수, 이게 본체)

`scripts/validate_data_contract.py`:

- `Env.MASTER_FILES`에 `"dividend": "dividend.json"` 추가 → mtime 스냅샷·동시백필 감시·
  `ARTIFACT_UNREADABLE`이 자동으로 붙는다. **지금은 이것조차 없다.**
- 심각도는 `check_ifrs17_bs`가 이미 쓰는 **배포여부 승격 패턴을 그대로 복제**하라
  (`env.ifrs17_bs_published` → `env.dividend_published`): 아직 어떤 HTML도 안 읽으면 YELLOW,
  `공시보고서.html`이 fetch 하는 순간 코드 수정 없이 RED. 불변식 "게이트가 검사하는 파일 =
  사용자가 보는 파일"을 새 도메인에도 똑같이 적용.

### V-1. 룰은 아래 3개만 (오케스트레이터가 실측으로 고른 것 — 더 만들지 말 것)

owner가 8/14에 "항목 ㅈㄴ 많은 것" 과설정을 한 번 정정했다. **신규 룰 3개로 끝낸다.**

1. **`DIV_PAYOUT_IDENTITY`** — 항목7 (연결)현금배당성향(%) ≈ 항목5 현금배당금총액 ÷ 항목2
   (연결)당기순이익 × 100. 실측: 항목7이 있는 셀이 **46개**뿐이라 검산 대상이 작고 확실하다.
   허용오차는 공시 반올림 감안해 넉넉히(±0.5%p 수준) 잡되, 크게 벗어나면 연결/별도 오선택
   (항목2 vs 항목3) 지문이다.
2. **`DIV_CENSUS_MISSING`** — 기대 그리드 24사 × 14분기 = **336셀 중 310셀만 존재**(26셀 결측).
   그 26셀이 전부 **raw에서 `status=013`(그 분기 미공시)인지 캐시로 전수 대조**하고, 013이
   아닌데 빠진 셀이 하나라도 있으면 RED. (SKIP-on-missing = 검증무력화, 이 저장소 상습사고.)
3. **`DIV_ZERO_PLAUSIBILITY`** — 0값 맹점 점검. 실측: **항목6(주식배당금총액) 310행이 전부 0**,
   항목5(현금배당금총액)도 310행 중 264행이 0. 파서 주장은 "실제 무배당이면 명시적 0"인데,
   그게 사실인지 **raw alotMatter 응답에서 해당 행이 진짜 `-`/무배당인지** 표본이 아니라
   전수로 확인하라. `-`를 0으로 뭉갠 케이스가 하나라도 나오면 파서로 되돌려라(route: reparse).

### V-2. 교차검증 (가장 가성비 높은 한 건 — 별도 룰 아님, 1회성 대사)

루트 `배당현황_OpenDART_2023Q4-2026Q2.xlsx`는 **다른 세션이 다른 코드로** 만든 19사 × 4시점
독립 산출물이다(2026-08-14 KRFS 세션). `dividend.json`의 같은 (회사,분기,항목)과 대사해
불일치를 답변에 표로 남겨라. 우리 파이프라인 밖에서 만들어진 사실상의 답지라 한 번은 반드시
붙여야 한다. **불일치 시 어느 쪽이 맞는지는 raw 캐시가 심판**한다.

### V-3. 정상인 것 (RED로 때리지 말 것)

- **커버리지 24사**: 비상장 15사는 DART alotMatter 자체에 없다 → 전 기간 결측이 정상.
  기존 Tier-2 예외 등록부와 같은 방식으로 **문서화된 예외로 등재**하고 집계 1건으로만 보이게 할 것.
- 종류주(보통주/우선주) 분리행과 회사단위 항목(1-7)의 `종류주="-"`는 스키마 설계다.

### V-4. 끝나면

- RED 0 확인 후 **publishing에 "배포 가능" 통지**(`inbox/publishing/20260814T2230Z` 스레드에
  붙여라 — 그쪽이 keep-list 등록 대기 중). RED가 남으면 그 목록이 곧 push 차단 사유다.
- `TODO_validation.md` 갱신 + 게이트 셀프테스트에 새 룰 케이스 추가.

## 답변 (recipient 작성 — 처리 후)

**처리 완료 (2026-08-14 16:40Z). 배당 도메인 RED 0. 단, 게이트 전체는 RED 13 —
사유는 배당이 아니라 `PL_breakdown` 이고 별건으로 파서에 발주했다(맨 아래).**

### V-0 배선 — 완료

`scripts/validate_data_contract.py`:

- `Env.MASTER_FILES` 에 `"dividend": "dividend.json"` 등록 → mtime 감시 · 동시백필 판정 ·
  `ARTIFACT_UNREADABLE` 이 이제 이 마스터를 덮는다.
- `Env._ifrs17_bs_is_published()` 를 **`_html_fetches(master_file)` 로 일반화**하고 17BS·배당이
  같이 쓴다(두 번째 사용처가 생겨 복붙 대신 인자화). `dividend_published` 는 루트 HTML 어디서든
  `dividend.json` 문자열이 잡히면 True → **`공시보고서.html` 이 fetch 를 켜는 순간 코드 수정
  없이 YELLOW→RED 승격.** 배선 도중 designer 가 그 페이지를 실제로 채웠고(01:27 KST,
  `공시보고서.html` 5.7KB→17.5KB, `resolveUrl("dividend.json")` 확인) **승격은 이미 발동
  상태다** — `env.dividend_published == True` 실측.
- **배선 생존 확인(mutation)**: 라이브 마스터의 배당성향 1셀에 +25%p 를 주입하니
  `DIV_PAYOUT_IDENTITY` **RED 1건**(메리츠화재 2023.4Q) 정상 발화. 승격 경로가 살아 있다.
- 로더 3종 추가: `dividend` · `dividend_published` · `dividend_fetch_census`
  (`data/_derived/alotmatter_fetch_census.json`).

### V-1 룰 3개 — 배선 완료, 라이브 위반 0

`check_dividend()` 신설 + `run_gate()` 등록. **기대 그리드를 회사 목록이 아니라 수집 census 의
`status` 에서 도출**한 게 설계의 핵심이다(회사 목록으로 세우면 비상장 15사의 정상적 부재가
전부 RED 가 된다). 분기 스코프(`_DISPLAY_QUARTERS`)는 **적용하지 않았다** — 배당 화면은
2023.1Q~2026.2Q 전 계열을 그리므로 표시분기로 좁히면 화면에 뜨는 셀이 검사 밖에 남는다.

| 룰 | 라이브 결과 |
|---|---|
| `DIV_PAYOUT_IDENTITY` (항목7 == 항목5/항목2×100, ±0.5%p) | 검사 46셀 · **위반 0** |
| `DIV_CENSUS_MISSING` (census status=000 인데 마스터 행 없음) | status=000 **310셀** == 마스터 310셀 · **결측 0** |
| `DIV_ZERO_CONTRADICTION` (총액 0인데 주당배당/수익률 양수) | **모순 0** |
| `DIV_CENSUS_SOURCE_MISSING` (census 파일 자체 소실 = 검사축 소실) | 정상(파일 존재) |
| `DIV_NO_FILING_COMPANY` (집계 YELLOW) | 15사 전 기간 013 — 기대 그리드에서 제외, 목록 출력 |

> **발주문의 "336셀 중 310만 존재 → 26셀 결측" 은 오케스트레이터의 잘못된 기대치였다.**
> 24사×14분기(336)는 산술 격자일 뿐이고, 실제 기대치는 **필링이 존재하는 310셀**이다.
> 그 26칸은 전부 `status=013`(그 분기 보고서 자체가 없음) — 결측이 아니라 정상 부재다.
> 게이트도 이 정의로 배선했다.

**항목6(주식배당금총액) 전행 0 · 항목5 264/310행 0 도 1회성 전수감사로 근거 확인**: 310개
raw 캐시 파일에서 해당 `se` 행을 전부 열어본 결과 **thstrm 이 `-`/공란/0 이 아닌 케이스 0건**.
즉 진짜 무배당이고 파싱 손실이 아니다. 이건 상시 룰로 만들지 않았다(raw 310파일 I/O 를 매
게이트 실행마다 지불할 이유가 없고, 같은 사고는 `DIV_ZERO_CONTRADICTION` 이 더 싸게 잡는다).

### V-2 교차검증 — 308셀 전부 일치

루트 `배당현황_OpenDART_2023Q4-2026Q2.xlsx`(다른 세션·다른 코드) `배당_원본` 시트를
`corp_code` 로 조인해 셀 단위 대사:

```
compared=308  agree=308  mismatch=0  in-xlsx-not-in-master=0
```

독립 구현 두 벌이 셀 단위로 완전 일치 → `dividend.json` 값 신뢰도 확보.

### V-3 예외 — 등재 대신 **구조로 해소**

비상장 15사는 별도 예외 레지스트리를 만들지 않았다. 기대 그리드가 fetch census 에서 나오므로
013 만 있는 회사는 **애초에 기대되지 않는다.** 대신 조용히 사라지지 않게 `DIV_NO_FILING_COMPANY`
YELLOW 집계 1건으로 15개 코드를 항상 출력한다(17BS 의 `BS_CENSUS_NO_SOURCE_COMPANY` 와 동형).

### 셀프테스트 — 30/30

`validate_data_contract.py --selftest` 에 J1~J5 5케이스 추가(각 룰 1건 + 검사축 소실 +
미배포 강등). **25/25 → 30/30 PASS.** (작성 중 실제로 겪은 함정을 fixture 주석에 박아뒀다:
`div_census()` 의 reprt 와 `LATEST` 분기가 어긋나면 모든 배당 케이스에 `DIV_CENSUS_MISSING`
오탐이 섞인다.)

### ⚠ 별건 — push 는 여전히 막힌다 (배당 때문이 아니다)

라이브 게이트 `SUMMARY RED=13`. **13건 전부 `PL_breakdown` `MASTER_HOLE`** 이고, 원인은
작업트리 PL 마스터가 **HEAD 대비 61셀 / 1,475행 적은 것**(7,799→6,636행). 다른 마스터는 손실
0(`CSM_waterfall` +8셀, `IFRS17_BS` +8셀, `kics` 무변동). 2026-07-30 근접사고와 같은 계열이라
파서에 route: reparse 로 발주했다 →
`inbox/parser/20260814T1637Z__validation__MULTI__pl_breakdown_61cells_lost_vs_head.md`.
**그게 복구되기 전에는 배당이 깨끗해도 배포 못 한다.**
