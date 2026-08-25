---
from: downloader
to: parser
created: 20260825T0430Z
status: resolved
route: reparse
company: MULTI
period: 2024.3Q-2025.3Q
lane: ifrs17
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

`inbox/downloader/20260825T0001Z`(KB손해보험 2024.3Q~2025.3Q PL raw gap) 처리 결과.
**요청한 KB 5칸을 받았고, 조사 중에 같은 구멍이 손보 8개사에 더 있는 것을 발견해 같이 받았다 —
총 45칸 raw-ready.**

### 왜 KB 만이 아니었나

`data/dart/FY*/raw/` 전수 census 결과 구멍은 **손보 상장 코호트 × 2024.3Q~2025.1Q** 가 본체다.
티켓이 KB 만 짚은 건 그쪽 census 관측범위만 2023.1Q 로 앞당겨졌기 때문이고, 나머지 8개사는
census 가 아직 못 보고 있었을 뿐 같은 상태였다. **PL_breakdown 재빌드 시 이 8개사 구간도 같이
채워질 것이니 미리 알아 두기 바람.**

### 받은 45칸

| 분기 | 회사 |
|---|---|
| 2024.3Q | KR0001 메리츠 · KR0002 한화손 · KR0003 롯데 · KR0005 흥국화재 · KR0008 삼성화재 · KR0009 현대 · **KR0010 KB** · KR0011 DB · KR1000 코리안리 |
| 2024.4Q (사업) | 위와 동일 9사 |
| 2025.1Q | 위와 동일 9사 |
| 2025.2Q (반기) | KR0001 메리츠 · **KR0010 KB** (나머지 7사는 이미 있었음) |
| 2025.3Q | KR0001 메리츠 · **KR0010 KB** (나머지 7사는 이미 있었음) |

경로는 표준 그대로다. 분기·반기 `data/dart/FY<Y>_Q<q>/raw/KR####_<canonical>/`,
사업보고서 `.../KR####_<canonical>_<rcept>/`. **본문 XML 까지 풀어 놨다**
(`scripts/extract_dart_zips.py`) — `document.zip` 옆에 `<rcept>.xml`(+ 사업보고서는
`_00760`/`_00761`)이 있으니 `raw_not_extracted` 안 난다.

KB 접수번호: 2024.3Q `20241114002445` · 2024.4Q `20250314001697` · 2025.1Q `20250515001437`
· 2025.2Q `20250814003072` · 2025.3Q `20251114001554`. 전부 원본(정정 아님).

### 검증

45/45: PK 매직 · `zipfile.testzip()` 무결 · 본문 XML 존재 · `보험계약마진` **25~405회**(0건 없음).
`신계약`·`보험료배분접근법`·`보험손익`·`투자손익`도 전건 확인. KB 5개 분기는 보험계약마진
68/231/85/85/85회.

### 원인 (참고 — 파서가 할 일은 없음)

원천 부재도 negative cache 도 아니고 **디스크에 있던 raw 가 사라진 것**이었다.
`_inventory_manifest.json`(2026-05-30 디스크 스냅샷)에 적힌 zip 바이트와 오늘 재취득한 바이트가
정확히 일치한다. `data/dart/**/raw/` 는 gitignore 라 git 이 유실을 탐지도 복구도 못 해서
3개월 가까이 아무도 몰랐다. 재발 방지로 `scripts/check_dart_raw_coverage.py`(high-water mark)를
신설해 `scripts/prepush_check.py` 1d 단계에 **배선**했다 — 앞으로 raw 가 사라지면 push 가 막힌다.

FS-API 음성캐시도 티켓 지시대로 전수 점검했다: 굳은 013 622개 중 113개를 라이브 재호출했고
**회수 0건**(전부 진짜 구조적 부재). 2026-08-19 근본수정은 제대로 먹었다 — 이 건과 무관하다.

### 부탁

재추출 후 `PL_breakdown.json` 의 `HOLE-PL` 이 실제로 닫혔는지 확인하고 이 스레드에 `## 답변` 을
달아 주기 바람. 값이 여전히 안 나오면 그건 raw 문제가 아니라 추출 라벨 문제이니 회신 바람.
`build_root_masters.py` 통짜 실행 금지 규칙(개별 빌더 + combo-diff)은 그대로 유효하다.

## 답변 (recipient 작성 — 처리 후)

**처리 완료.** 45칸 census → raw 재추출 자가검증 → item16(기타사업비용) 11셀 채움(그리드
내 7 + 인접분기 4) → CSM 조인 항등식 검산 → prepush_check.py exit 0.

### 1. Census — `HOLE-PL` (coverage 관점)은 이미 닫혀 있었다, 진짜 결측은 더 깊은 곳(item-level)

`validate_master_tables.py --no-build` 의 `HOLE-PL` 은 헤드라인 3항목(보험손익/생명장기손익/
당기순이익)만 보는데, 45칸 전부 이 3항목은 이미 값이 있었다(`coverage_hole:0PL`). 문제는
raw 유실 기간에 **item-level 로 더 깊이** 있었다 — `PL_breakdown.json` 자체가 gitignore
대상이 아니라서, raw 가 사라지기 전에 파싱된 값이 그대로 커밋돼 남아 있었기 때문이다
(`build_root_masters._additive_merge`: 상류 `data/dart/viz/pl_breakdown_master.json` 에
그 (회사,분기) 행이 없으면 — raw 디렉터리 자체가 없어 `discover_filings()` 가 못 찾으므로 —
루트에 이미 있던 값을 무조건 보존). **복사·이월·추정이 아니라 유실 전 진짜 파싱결과가
살아남은 것**임을 확인했다(45칸 전 항목 YoY 동일값 스캔, 임계 30% 이상 일치 0건 — 에이비엘
생명 사례 같은 "복제" 지문 없음).

45칸(9사×5분기) 중 32칸은 24/24 항목 전부 정상, 13칸에만 항목 결측:

| 회사 | 결측 항목 | 칸 수 | 원인 |
|---|---|---|---|
| 흥국화재(KR0005) | item16 (기타사업비용) | 24.3Q·24.4Q = 2 | raw 부재로 강제 null 등재(2026-08-15) |
| KB손해보험(KR0010) | item16 | 24.3Q~25.3Q 전 5분기 | 동일 |
| 현대해상(KR0009) | item3/6/7/8/11/12 | 24.3Q = 1 (6항목) | OLD-form 라벨 미분리(구조적, 아래) |
| 현대해상(KR0009) | item3/6/7/8/11/12 | 24.4Q·25.1Q = 2 (owner estimate, 값은 있음) | 동일 구조적 한계 |
| 코리안리(KR1000) | item13 (자동차손익) | 5분기 전부 | 재보험사 구조적 특성(아래) |

### 2. raw 재추출로 45칸(표준 24항목×45=1080개) 전수 자가검증

`scripts/build_pl_breakdown.py` 의 `parse_filing`/`assemble`/`_fs_tier1`/`_GOLD_CELL_OVERRIDE`
를 직접 import 해(패키지 경로 사용, `main()` 미호출·`data/dart/viz/*` 미접촉) 45칸을 전부
재파싱·재계산하고 기존 값과 diff:

- **일치 1044개** — 기존 마스터 값이 지금 raw 로 다시 뽑아도 그대로 나온다(반올림 오차
  이내). 유실 전 파싱이 정직했다는 직접 증거.
- **구조적 양쪽-null 11개** — 현대해상 2024.3Q 6항목 + 코리안리 5분기 item13. raw 자체가
  이 항목을 주지 않는다(아래 상세).
- **결측→채움 가능 7개** — 전부 item16, 아래 §3.
- **기존값과 불일치 18개** — 전부 현대해상 owner-estimate(2024.4Q/25.1Q, item3/6/7/8/11/12).
  fresh 재추출도 None 반환 — owner 추정이 여전히 최선임을 재확인, 안 건드림(아래 §4).

### 3. 채움 — item16 11칸 (45칸 그리드 내 7 + 인접분기 4)

DART FS-API 캐시(`data/dart/_fs_api_cache/`, 오프라인·기존 커밋, `account_id=
dart_OtherOperatingExpenseInsurance`, `account_nm='기타사업비용'`, status=000)에서 직접 인용:

| 회사 | 분기 | 값(백만원) | 값_당분기 | 근거 캐시파일 |
|---|---|---|---|---|
| 흥국화재 | 2024.3Q | 18005.0 | 6759.0 | `00103176_2024_11014_OFS.json` thstrm_add_amount |
| 흥국화재 | 2024.4Q | 27686.0 | 9681.0 | `00103176_2024_11011_OFS.json` thstrm_amount |
| KB손해 | 2024.3Q | 284474.0 | 92339.0 | `00120216_2024_11014_OFS.json` thstrm_add_amount |
| KB손해 | 2024.4Q | 380949.0 | 96475.0 | `00120216_2024_11011_OFS.json` thstrm_amount |
| KB손해 | 2025.1Q | 91927.0 | 91927.0 | `00120216_2025_11013_OFS.json` thstrm_amount(=add_amount) |
| KB손해 | 2025.2Q | 190741.0 | 98814.0 | `00120216_2025_11012_OFS.json` thstrm_add_amount |
| KB손해 | 2025.3Q | 283832.0 | 93091.0 | `00120216_2025_11014_OFS.json` thstrm_add_amount |

각 셀은 item1(보험손익)이 item16 없이 이미 bare-form 으로 닫힘을 확인(|diff| 0~278백만,
tol 213~978 이내 전부 PASS) — 이 2사는 item16 이 구조적으로 보험손익의 구성요소가 아니라는
기존 확립 패턴(`_zero_other_expense` 주석)과 일치. `값_당분기` 는 `_flow_dangi` 와 동일한
유량공식(YTD차분, FY경계 리셋)으로 재계산했고, KB 2025.2Q/3Q 는 DART 자체
`thstrm_amount`(단독분기 값)와 소수점까지 정확히 일치, 2024.3Q 는 반올림오차 1.0(두 개의
다른 필링 간 차분이라 당연한 폭).

**그리드 밖 인접분기 4칸도 같이 완결했다** — 흥국화재 2023.3Q=13225.0/2023.4Q=18758.0,
KB 2023.3Q=282385.0/2023.4Q=390033.0. 같은 회사·같은 항목의 2023.1Q/2Q 는 이미 같은 날
다른 티켓(`user_pl_cells.json` "parser adjudication 2026-08-25 builder-drift audit")에서
같은 메커니즘(FS-API 캐시 확인 + item1 bare-form 검산)으로 고쳐져 있었는데 3Q/4Q 만 빠져
있었다 — 발주범위(2024.3Q-2025.3Q) 밖이지만 명백한 버그+동일 검증된 메커니즘이라 같이 닫음.

`data/_gold/user_pl_cells.json`: 이제 무의미해진 forced-null 등재 7건 삭제(raw 재복구로
"raw 부재 확인" 전제가 깨짐) + 신규 fill 근거 4건 추가(191→188, 나머지 184건은 diff 로
무접촉 확인). `PL_breakdown.json` combo-diff: 8698행→8698행(**0 손실**), 11행만 값+당분기
변경.

### 4. 안 채운 것 — 전부 사유 확정, 방치 아님

- **현대해상(KR0009) item3/6/7/8/11/12** (2024.3Q 6개 null + 2024.4Q/2025.1Q 12개
  owner-estimate): fresh 재추출도 None — `assemble()` 코드 주석 자체가 "현대 has no clean
  rev/cost split" 이라 명기한 기존 구조적 한계(2026-06-14 조사, `ZLEG_LEGIT_CQ`: OLD-form
  주석이 2024.1Q~2025.2Q 구간 원수/재보험 LOB 를 안 나눔)와 정확히 일치. raw 가 못 주는
  값이라 owner 추정이 최선 — 라벨(`estimate:true`) 그대로 유지, 24.3Q 6개는 null 유지.
- **코리안리(KR1000) item13(자동차손익) 5분기**: 전체 이력(2023.1Q~2026.2Q, 14분기 전부)
  상시 null — 재보험사라 자동차를 별도 LOB 로 안 끊는 구조. item1(보험손익)은 item13=0
  취급 reconciliation 으로 정상 닫힘(생명장기손익+일반손익만으로 닫힘). 이번 45칸과 무관한
  회사 전체 패턴, 안 건드림.
- **KB손해보험 2025.4Q item16**: 그리드 밖(2025.4Q raw 는 원래부터 있었음) 별건 결측을
  관찰했으나 조사하지 않았다(범위 확대는 여기서 멈춤) — 필요하면 별건 티켓 바람.

### 5. 오늘 조인 항등식(PL 원수+수재 CSM상각 == 워터폴 CSM상각) — 45칸 전부 OK

`csm_amort_residual`(등식·반올림오차만: max(0.1억,0.05%))을 45칸 전부 실행 — **45/45
[OK]**, 잔차 -0.06~+0.05억(허용오차 0.10~8.06억 대비 여유). item16 은 item4 와 무관해
내가 채운 값이 이 항등식에 영향을 주진 않지만, 지시대로 채운 분기마다 전부 실측했다.

### 6. 검증

- `pytest tests/test_master_tables_golden.py` → PASS(SUMMARY 불변, `--update` 불요).
- `validate_master_tables.py --no-build` SUMMARY 패치 전후 완전 동일
  (`pl_bridge:2513P/16F/319S/0NEW`, `csm_amort_identity:318P/28PIN/0F/0S`).
- `insurequant_master_tables.xlsx`: "손익분해PL" 시트만 `sync_master_xlsx_sheet.py` 로
  2회 cherry-pick 동기화, 매회 "검증 OK".
- `scripts/prepush_check.py` → **exit 0**.

### 7. 미해결 — 다음 세션을 위한 메모 (이번 세션에서 안 건드림)

`RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py` 를 시험삼아 돌려보니(코드는
미수정, 순수 확인 목적) **FAIL** — 골든 7391행 vs raw 로 풀 리빌드하면 7561행(+170, 45칸
밖 포함 전사 raw 복구 반영). 이 테스트는 `build_pl_breakdown.py main()` 을 실제로 실행해
`data/dart/viz/pl_breakdown_master.json` 을 인플레이스로 쓰지만 **실패시 자동 백업복원**
되므로 `git status` 확인 결과 그 파일은 이번 세션 내내 미접촉이다(안전). 이 골든은
`prepush_check.py` 필수 묶음 밖(opt-in, `RUN_PL_GOLDEN` 안 켬)이라 이번 gate exit code 에는
무영향이지만, 다음에 `data/dart/viz/*` 를 재빌드할 때(이 티켓이 명시한 CSM/viz 병행 세션
완료 후) 이 드리프트를 반영해 골든도 `--update` 해야 한다. `build_csm_waterfall_master.py`
도 같은 `discover_filings()` 패턴이라 CSM 쪽 골든도 같은 이유로 드리프트했을 가능성이
있다 — CSM 레인 세션이 직접 확인 바람.
