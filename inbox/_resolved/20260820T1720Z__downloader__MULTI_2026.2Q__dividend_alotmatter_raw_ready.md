---
from: downloader
to: parser
created: 20260820T1720Z
status: resolved
route: reparse
company: MULTI
period: 2026.2Q
lane: ifrs17
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

Raw-ready for `inbox/parser/20260820T1540Z` (blocked_on `inbox/downloader/20260820T1600Z`,
now resolved — full answer in `inbox/_resolved/20260820T1600Z__owner__MULTI_2026.2Q__
dividend_alotmatter_negative_cache.md`).

**Root cause confirmed and fixed**: `fetch_dart_alotmatter.py` cached DART `status:013` ("no
data") responses permanently, same trap as `fetch_dart_fs.py` (fixed 2026-08-19). The 2026
half-year batch was fetched on 2026-08-14 — the filing deadline day itself — before DART had
indexed most filings, so 34/39 companies got 013 baked in forever with no way to retry (no
`--refresh` flag existed).

**Fixed**: `fetch_one()` now only persists `status==000`; added `--refresh <year> <reprt>`
(forces live re-fetch for the whole universe at that year/reprt slice, bypassing whatever's on
disk). Ran `python scripts/fetch_dart_alotmatter.py --refresh 2026 11012`.

**Result — `data/dart/_alotmatter_cache/*_2026_11012.json`, 39/39 companies confirmed:**

```
before: 000=5   013=34
after:  000=24  013=15   (19 companies flipped 013→000)
```

19 companies now have real 2026 half-year dividend data where they had none before:
메리츠화재해상보험·롯데손해보험·흥국화재·삼성화재해상보험·현대해상·KB손해보험·DB손해보험·
NH농협손해보험·삼성생명보험·에이비엘생명보험·흥국생명보험·교보생명보험·미래에셋생명보험·
푸본현대생명보험·동양생명·KB라이프생명·농협생명보험·서울보증보험·코리안리재보험.

**The remaining 15 `013`s are NOT a caching artifact — they're structural non-filers**, and
they exactly match the "XBRL 전무 15개사(14+예별)" set independently confirmed during the
2026-08-13 FS-API onboarding (`docs/changelog_downloader.md` 2026-08-13): 예별손해보험·
악사손해보험·하나손해보험·신한이지손해보험·라이나생명보험·비엔피파리바카디프생명보험·
아이엠라이프생명보험·에이아이에이생명보험·메트라이프생명보험·하나생명보험·처브라이프생명보험·
교보라이프플래닛생명보험·IBK연금보험·카카오페이손해보험·AIG손해보험(KR0029, needed a direct
corp_code=`00983606` call — `resolve_corp()` can't find it by name search, same quirk as
always). These companies file only 감사보고서 (audit reports), never a 반기/사업보고서, so
alotMatter — which reads A-type filings — has nothing to return, live-reconfirmed 013 each
time. Treat as legit-absent, not missing, per the zero-vs-missing note already in
`build_dividend.py`.

Existing 2023-2025 permanent-013 caches were **not touched** — `--refresh` is scoped to
exactly the `(year, reprt)` pair you pass.

## 요청

Per your own ticket (`20260820T1540Z`): rebuild `build_dividend.py`, `tests/
test_dividend_golden.py --update` (row count will grow by 19 companies' worth of 2026.2Q
cells), and treat the 15 still-013 companies as legit-absent per your own zero-vs-missing note
rather than re-flagging them as a gap.

## 답변 (recipient 작성 — 처리 후)

**resolved — `dividend.json` 2026.2Q 를 5사 → 24사로 재빌드했다 (1,924 → 2,043행, +119행).**

### 재빌드 전에 한 겹 더 막혀 있었다 — 캐시는 고쳤는데 census 가 안 고쳐졌다

`build_dividend.py` 는 캐시 파일의 `status` 가 아니라 **census
(`data/_derived/alotmatter_fetch_census.json`) 에 복사돼 있던 `status`** 를 읽고 있었다(L99).
`--refresh` 는 census 를 다시 쓰지 않으므로, 디스크 캐시가 013→000 으로 바뀐 19사가 census
에서는 여전히 013 이었다. **그대로 빌더를 돌렸으면 결과는 여전히 5사였다.**

전 16개 slice 를 census 대 캐시파일로 대조한 실측:

| slice | census 000 | 캐시파일 000 | FLIP |
|---|---|---|---|
| 2026/11012 | 5 | 24 | **19** |
| 나머지 15 slice | 일치 | 일치 | 0 |

어긋난 slice 는 2026/11012 하나뿐이다. 2026/11011·11014 가 0/39 인 것은 아직 제출기한 전이라
정상이다.

### 고친 것 — 빌더가 자기 입력 파일을 믿게 했다

`build_dividend.py`: census 는 **(kr, corp_code, year, reprt) 그리드 + 코드매핑에만** 쓰고,
필링 존재 여부는 **실제로 여는 캐시 파일의 `status`** 로 판정한다. `fetch_one` 이 이제 000 만
디스크에 남기므로 "파일 없음 = 필링 없음", "013 파일 = 수정 전에 박힌 negative cache = 필링
없음" 두 갈래로 처리했다. 같은 사실이 두 군데 복사돼 있어서 생긴 stale 함정이 구조적으로 사라진다.

### 검증

- 구/신 diff: **added 119 · removed 0 · changed 0.** 늘어난 행은 전부 2026.2Q, 19사분이다.
- 2026.2Q 148행 24사 — 다른 2Q 와 같은 수준이다(2023.2Q 134 · 2024.2Q 145 · 2025.2Q 142).
- 배당성향 항등식(항목7 = 항목5 / 항목2 × 100) 2026.2Q 전수 검산: **불일치 0**. 배당성향이
  정의되는 회사는 KB라이프(공시 66.40 / 산출 66.39)·서울보증(24.30 / 24.30) 둘뿐이고 둘 다 맞다.
- 나머지 22사 현금배당금총액 = 0 은 원문 대조를 마쳤다. `thstrm="-"` 이므로 **공시된 진짜 0**
  (중간배당 없음)이고, 네 말대로 zero-vs-missing 규칙 그대로다. 예: 삼성화재 2026 반기
  `현금배당금총액 thstrm="-" · frmtrm=828,949`(FY2025 연간). 코리안리는 2023~2025 반기에
  중간배당(52,771 / 79,524 / 91,011)이 있었는데 2026 반기만 `-` 라 0 인데, 이것도 원문 그대로다
  — 패턴이 끊긴 유일한 케이스라 raw 를 직접 열어 확인했다.
- `tests/test_dividend_golden.py --update` 재생성 후 pytest 통과(2,043행 / 24사 / 14분기).
- `scripts/validate_data_contract.py` **RED=0**. 배당 관련 finding 은 `DIV_NO_FILING_COMPANY`
  YELLOW 1건뿐이고, 그 15사는 네가 준 구조적 미제출사 목록과 정확히 일치한다(KR0004 · KR0029 ·
  KR0049 · KR0050 · KR0051 · KR0074 · KR0075 · KR0076 · KR0080 · KR0095 · KR0097 · KR0100 ·
  KR1010 · KR1011 · KR1098). legit-absent 로 처리했고 결측으로 재플래그하지 않았다.

### 너에게 남긴 것 하나

**census 는 아직 stale 이다.** 게이트 `check_dividend` 의 `DIV_CENSUS_MISSING` 은 "있어야 할
셀"을 census 에서 뽑으므로, 지금 2026.2Q 기대치를 24 가 아니라 **5** 로 세고 있다. 빌더는 더
이상 안 막히지만 그 19사가 다시 사라져도 게이트가 못 잡는다. 발주했다:
`inbox/downloader/20260820T1810Z__parser__MULTI_2026.2Q__alotmatter_census_stale_after_refresh.md`
