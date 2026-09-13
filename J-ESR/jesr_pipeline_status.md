# J-ESR Pipeline Status
> Track: J-ESR (Japan Economic Solvency Ratio)
> First J-ICS mandatory disclosure cycle: FY2025 (ending 2026-03-31)
> Last updated: 2026-09-13

## Coverage Summary

| Route | Companies | Status | Trigger |
|---|---|---|---|
| HD press / IR (manual 1st pass) | 7 groups | Partial (5 confirmed 2026.3末, 2 prior-Q) | Complete |
| Mutual IR-PDF (`jesr_mutual_irpdf.py`) | 5 companies | Seed only (prior-Q) | May 2026 press PDFs |
| EDINET (`jesr_edinet_fetch.py`) | **17 obligated / 14 filed FY2025** | **Live** — key OK, codes verified, 有報 scanned (2026-09-13) | Done for FY2025 |
| Non-EDINET listed subs | ~20 | URL patterns TBD | Oct 2026 |
| (EDINET 미등록 51사는 이 루트로 영원히 안 온다 — `edinet_code_match.json`) | 51 | 각사 PDF 전용 | — |
| Small/foreign subs | ~40 | Not scoped | Oct 2026+ |

**2026-06-24 total confirmed (2026.3末 as-of):** 5 companies (HD only)

## 2026-09-12 FY2025 disclosure census (79 companies)

Source route corrected (owner 2026-09-12): individual-company ESR lives in each insurer's own disclosure/IR PDFs
(deadline 2026-10-31); EDINET XBRL is secondary (FY2024 probe: 0 ESR elements). Census file:
`J-ESR/fy2025_esr_census_20260912.csv` (`fy2025_esr_status` = posted / not_yet / not_found).

| Status | Total | Life | Non-life | Re | Note |
|---|---|---|---|---|---|
| posted | 15 | 10 | 5 | 0 | 5 HD group + 8 large life (4 mutuals) + 2 small non-life solo |
| not_yet | 62 | 34 | 25 | 2 | 11/13 non-life PDFs state new-basis ratio to be published end of Oct 2026 |
| not_found | 2 | 1 | 1 | 0 | no disclosure page located |

Next: re-run the same census at end of October 2026 (start from rows whose notes say pattern-based).
`jp_insurers.csv` `ir_url` blanks 41 -> 2; the 2 exact-duplicate rows are kept for now (row order preserved).

## October 2026 Checklist

### Pre-October (2026-09-13 라운드에서 전부 닫음)

- [x] EDINET API probe (auth: 401, key required)
- [x] Master company list `jp_insurers.csv` (生保 41 + 損保 31 + 再保険 2 = 74 entries)
- [x] EDINET fetch scaffold `jesr_edinet_fetch.py`
- [x] Mutual IR-PDF route `jesr_mutual_irpdf.py`
- [x] **EDINET Subscription-Key** — 클라우드 환경변수 `EDINET_KEY` 로 주입(저장소 커밋 금지)
- [x] Smoke test: `python J-ESR/jesr_edinet_fetch.py --smoke` → PASS (2026-06-26 기준 1,267건, 보험사 有報 2건 검출)
- [x] 코드 검증 — 공식 EDINETコードリスト(11,389건) 대조. **기재 13개 중 7개가 다른 회사 코드였다**
      (E04979=パーク24 / E04506=九州電力 / E05026·E14905·E06008·E33424·E04678 은 존재하지 않는 코드).
      증거 `J-ESR/edinet_code_match.json`, 도구 `python J-ESR/edinet_codelist.py --apply`
- [x] TBD 62행 해소 — 매칭 27(有報의무 17 / 등록만 9) · **미등록 확정 51** · 판단보류 3
- [x] 판단보류 3사 확정(2026-09-13 2차 라운드, 전부 **2026-04-01 그룹 리브랜딩**이 원인이었다)
      · 第一ネオ生命保険 = ネオファースト生命保険 **E35324**(등록·有報의무 없음)
      · 第一アイペット損害保険 = アイペット損害保険 **E33935**(등록·의무 있음)
      · 大樹生命保険 = **미등록**(구 三井生命 포함 전수검색 0건) + `parent_group` 오기 정정(朝日生命 → 日本生命)
- [x] `jp_insurers.csv` 갱신(코드·edinet_eligible·근거 노트)
- [x] FY2025 有報 스캔 — 2026-06-01~07-31, **14사 제출·전부 XBRL**
      (`python J-ESR/jesr_edinet_fetch.py --scan` → `raw/edinet/scan_2026-06-01_2026-07-31.json`)
- [x] 有報 본문 ESR 대조 — 15건 전부에서 ESR 서술 검출, 5사 수치 확정
      (`python J-ESR/edinet_esr_probe.py` → `J-ESR/edinet_esr_probe.json`)
- [x] 출처 URL 전수 생존 점검 — 254건/고유 139건
      (`python J-ESR/check_source_urls.py --all` → `J-ESR/source_url_health.json`)

### October 2026 (J-ICS 공시 기한 2026-10-31 직후)

**날짜 두 개를 섞지 말 것.** 有価証券報告書 기한은 결산 후 3개월(3월기 = **2026-06-30**)이고 실제로
14사가 6월에 냈다. **2026-10-31 은 J-ICS(경제가치기준) 공시 기한**이지 有報 기한이 아니다. 종전 이 문서의
"有報 deadline 2026-10-31 / ESR 초등장은 10월 제출분" 은 오해였다(2026-09-13 실측으로 정정).

- [x] ~~Monitor EDINET daily from 2026-06-01~~ → 스캔 완료(14사). 10월엔 `--scan --from 2026-10-01` 로
      訂正有報(130)·半期報告書(140)만 다시 훑는다
- [ ] 10/31 이후 각사 디스클로저 PDF 재census — **`check_source_urls.py --all` 을 먼저 돌린다**
      (2026-09-13 기준 blocked 21 · spa_shell 8 · requires_headers 17 · dead 5 → 헤더 없이 훑으면 46건 오탐)
- [ ] dead 5건 대체 URL: 朝日生命 `company/zaimu/` · キャピタル損害保険 disc PDF · オリックス生命 `company/`
      · 日本生命 `ir_health_url`(구 경로) ×2
- [ ] `edinet_esr_probe.py` 재실행 — 10월 有報 訂正 반영 + 화면 수치 재대조
- [ ] Download mutual company PDFs when available: `jesr_mutual_irpdf.py --download`
- [ ] Run `jesr_mutual_irpdf.py --extract` for 5 mutual companies
- [ ] Validate all records: `eligible_capital / required_capital * 100 ≈ esr_pct ±2%`
- [ ] Assemble `J-ESR/jesr_master.json` (append to 1st-pass 2026.3末 records)
- [ ] Handoff to parser inbox for `jesr_master.json` schema finalization

## Expected Coverage (Oct 2026) — 2026-09-13 실측 반영

| Category | Count | Route | 근거 |
|---|---|---|---|
| EDINET 有報 제출 (FY2025 실제 제출) | **14** | `jesr_edinet_fetch.py --scan` | 6/11~6/30 제출, 전부 XBRL |
| EDINET 有報 의무인데 FY2025 미제출 | 3 | — | アクサ生命·楽天損保(결산월 상이 추정) 등 |
| EDINET 등록·有報 의무 없음 | 9 | 각사 IR PDF | 相互会社 5 + 第一生命保険·大同·太陽·FWD |
| EDINET 미등록 | **51** | 각사 IR PDF 유일 | 코드리스트 11,389건 전수검색 0건 |
| 판단보류(동명 후보 있음) | 3 | 사람 확인 | 第一ネオ生命·大樹生命·第一アイペット損保 |
| **합계(csv 행 기준)** | **81**(실질 79사) | | |

즉 **EDINET 루트의 천장은 17사**다. 화면에 올라간 15사 중 EDINET 으로 교차검증이 되는 회사는
7사(東京海上HD·MS&AD·SOMPO·T&D·ソニーFG·かんぽ·ライフネット)뿐이고, 나머지 8사는 각사 PDF 가 유일 출처다.

## Known EDINET Codes — 2026-09-13 공식 코드리스트로 재확정

**정본은 `jp_insurers.csv` 의 `edinet_code` 열이다.** 아래는 요약이고, 갱신은
`python J-ESR/edinet_codelist.py --apply` 로만 한다(스크립트에 코드 하드코딩 금지).

| Company | EDINET | 종전 기재 | 有報의무 | FY2025 有報 |
|---|---|---|---|---|
| 東京海上ホールディングス | **E03847** | ~~E05026~~ (없는 코드) | yes | S100YLS8 (06-26) |
| MS&ADインシュアランスグループHD | **E03854** | ~~E14905~~ (없는 코드) | yes | S100YNCJ (06-30) |
| SOMPOホールディングス | **E23924** | ~~E04979~~ (=パーク24) | yes | S100YC6Z (06-17) |
| 第一生命ホールディングス → **第一ライフグループ** | **E06141** | ~~E04506~~ (=九州電力) | yes | S100YC7A (06-16) |
| T&Dホールディングス | **E03851** | ~~E06008~~ (없는 코드) | yes | S100Y9UP (06-11) |
| ソニーフィナンシャルグループ | **E05714** | ~~E33424~~ (없는 코드) | yes | S100YCL0 (06-17) |
| かんぽ生命保険 | **E31755** | ~~E04678~~ (없는 코드) | yes | S100YD29 (06-18) |
| 東京海上日動火災保険 | E03823 | 일치 | yes | S100YLTM (06-26) + 訂正 S100YQZZ |
| 三井住友海上火災保険 | E03824 | 일치 | yes | S100YN6S (06-30) |
| 損害保険ジャパン | E03827 | 일치 | yes | S100YC6H (06-17) |
| あいおいニッセイ同和損害保険 | E03833 | 일치 | yes | S100YN5G (06-30) |
| 共栄火災海上保険 | E03850 | 일치 | yes | S100YK13 (06-25) |
| トーア再保険 | E03842 | (신규) | yes | S100YH0E (06-24) |
| ライフネット生命保険 | E26327 | ~~TBD~~ | yes | S100YC7R (06-16) |
| アクサ生命保険 | E03845 | ~~TBD~~ | yes* | **15개월 제출 0건** (아래 주) |
| 楽天損害保険 | E03835 | ~~TBD~~ | yes* | **15개월 제출 0건** (아래 주) |
| 日新火災海上保険 | ~~E03829~~ → none | 코드리스트에 없음 | no | — |

***\*** **アクサ生命保険·楽天損害保険 — "결산월이 달라서" 가 아니다(2026-09-13 실측으로 가설 기각).**
코드리스트의 決算日 필드가 두 회사 다 `3月31日` 이고, FY2024·FY2025 두 결산기(2025-06~09, 2026-06~09)를
직접 스캔해도 有報·訂正·半期·臨時 **전부 0건**, 금융청 제출기한 연장 승인 목록에도 없다. 제출자 구분은
아직 의무자로 남아 있으나 행동은 비의무 9사와 같다 — **의무 실효 가능성**(법적 사유 미확정, 10월 과제).

**第一生命ホールディングス 는 2026-04-01 부로 「株式会社第一ライフグループ」 로 상호가 바뀌었다**(2025-06-23
주총 결의). 有報 S100YC7A 표지 원문 「旧会社名：第一生命ホールディングス株式会社」 로 확인. EDINET 코드는
E06141 불변. 같은 날 ネオファースト生命 → 第一ネオ生命, アイペット損害保険 → 第一アイペット損害保険 이
함께 개명된 **그룹 리브랜딩**이다. csv 표시명 교체는 owner 판단 대기.

**등록은 있으나 有報 제출의무 없음(9사)** — 相互会社 5(日本生命 E06125 · 住友生命 E06134 ·
明治安田生命 E06369 · 富国生命 E06327 · 朝日生命 E06130) + 第一生命保険 E32692 · 大同生命 E03846 ·
太陽生命 E03848 · FWD生命 E34445. 업종 라벨이 `内国法人・組合（有価証券報告書等の提出義務者以外）` 다.
**이 회사들의 ESR 은 EDINET 에 오지 않는다.**

**EDINET 미등록 51사**(ソニー生命·アフラック·メットライフ·AIG損保·au損保 …): 코드리스트 11,389건 전수
검색에 이름이 없다. 매칭 실패가 아니라 실측 결과다 — 각사 디스클로저 PDF 가 유일한 경로.

## EDINET API Setup (2026-09-13 재실측)

```
# 1. 키: 환경변수 EDINET_KEY (클라우드 세션에 주입). J-ESR/edinet_key.txt 는 gitignore.
#    스크립트 기본값이 env 라 --key 없이 그냥 돈다.

# 2. 호스트: https://api.edinet-fsa.go.jp/api/v2   <- 정본
#    disclosure.edinet-fsa.go.jp/api/v2 는 301 -> disclosure2… -> 302 로 튕긴다(홉 낭비).
# 3. 인증: 헤더 Ocp-Apim-Subscription-Key / 쿼리 Subscription-Key 둘 다 200.
#    *** 키 없이 부르면 HTTP 200 인데 본문이 {"StatusCode": 401} 이다. 상태코드만 보면 속는다. ***

# 4. Smoke (2026-09-13 PASS):
python J-ESR/jesr_edinet_fetch.py --smoke
# -> HTTP 200 / EDINET status=200 / count=1267 / 보험사 有報 2건(E03847 東京海上HD, E03823 東京海上日動)

# 5. FY2025 有報는 이미 나와 있다 — 2026년 6월 제출(FY 종료 3개월 내가 기한).
#    "ESR 초등장 = 2026년 10월 제출" 은 오해였다. 10/31 은 J-ICS 공시 기한이지 有報 기한이 아니다.
python J-ESR/jesr_edinet_fetch.py --scan --from 2026-06-01 --to 2026-07-31 --doc-types 120,130,140
# -> 14사 15건(訂正 1 포함), xbrlFlag=1

# 6. XBRL 태그에 ESR: 여전히 없음. 그러나 *본문 iXBRL htm 에는 서술로 있다*.
python J-ESR/edinet_esr_probe.py
# -> 15건 전부 ESR 문장 검출. 수치 확정 5사:
#    東京海上HD 268% / T&D 222% / SOMPO 270% / ライフネット 333% / かんぽ 181%
#    (나머지는 자회사 有報라 그룹 ESR 을 싣지 않거나 도표 이미지)

# 7. EDINET 뷰어 딥링크(WEEK0040.html?docId=…)는 세션 기반이라 "Document Moved" 로 튕긴다.
#    사용자에게 보여줄 根拠資料 링크로 쓰지 말 것. docID 는 census notes 에만.
```

## Data Contract Rules (same as Korea pipeline)

- `as_of_consistent`: must be `true` (2026-03-31) for comparison charts
- Records with `as_of_consistent: false` → flagged, shown with date label, not in main ranking
- `esr_pct` plausible range: 80-600% (outside → validation flag)
- Math check: `eligible_capital / required_capital * 100 ≈ esr_pct ±2%` (when both available)
- Missing data → `null` (never imputed)
- Negative values → △ prefix (Korean accounting convention, consistent with KR pipeline)

## Files

| File | Purpose |
|---|---|
| `jp_insurers.csv` | Master company list (EDINET codes, IR URLs, category) |
| `jesr_edinet_fetch.py` | EDINET XBRL fetcher (listed companies) |
| `jesr_mutual_irpdf.py` | Mutual company IR-PDF downloader + extractor |
| `jesr_sources_2026Q1.csv` | 1st pass manual collection (11 HD/group, June 2026) |
| `raw/jesr_sources_raw.json` | 1st pass raw records |
| `raw/edinet/` | XBRL downloads (after key obtained) |
| `raw/mutual/` | Mutual company PDFs |
| `jesr_master.json` | Assembled master (parser output, schema TBD) |
| `probe_edinet.py` | API probe (confirmed auth=401 without key) |
| `jesr_http.py` | **공용 HTTP 헬퍼** — 브라우저 헤더·meta refresh 추적·SPA/봇차단/TLS 분류 |
| `check_source_urls.py` | 출처 URL 전수 생존 점검 (census 전 선행 단계) |
| `source_url_health.json` | 그 산출 — 254건/고유 139건 (2026-09-13) |
| `edinet_codelist.py` | 공식 코드리스트 대조 → `jp_insurers.csv` 코드 갱신 |
| `edinet_code_match.json` | 그 증거(회사별 매칭 방법·후보·오답 정정 내역) |
| `edinet_esr_probe.py` | 有報 본문 ESR 추출·화면 수치 대조 |
| `edinet_esr_probe.json` | 그 산출 (有報 15건) |
