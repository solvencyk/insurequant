---
from: orchestrator
to: publishing
created: 20261012T1150Z
status: resolved
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): K-ICS 화면의 소진율 도넛 밑 주석을 없애고, 「신종자본증권」·「후순위채」 각각 큼직한 셀 1개씩에 다음을 보여 준다(신종이 기본자본형인지 보완자본형인지는 이 셀에서 다루지 않는다). 화면(HTML)은 designer 가 하고(`inbox/designer/20261012T1155Z…`), 이 티켓은 **그 셀에 들어갈 값을 JSON 에 만드는 일**이다.
- 맨 위 큼직하게: **가장 최근 발행금리**(`x.xx%`)
- **총발행액**: `x,xxx억` (2023년 이후 발행분만 — 인정한도 계산이 2023년 이후분만 세기 때문)
- **콜 상환 도래일**: `20xx-xx-xx (x,xxx억)` — **콜일이 가장 가까운 한 건만**(여러 건 아님)

### 해 줄 것
1. 입력: `data/bonds/capital_securities_fy2026h1.json`(DART 사채 단위, 회사별 `bonds[]` — `tier`(`hybrid`=신종자본증권, `subordinated`=후순위채), `issue_date`, `call_date`, `coupon_pct`, `face_amount_mn`, `outstanding_mn`, `past_call_outstanding`, `as_of`). 현행 소진율 산출(`scripts/apply_disclosure_utilization.py`)이 이미 이 파일을 읽는지 확인하고 같은 경로에서 만든다.
2. `kics_tier1_utilization.json`·`kics_tier2_utilization.json` 의 **회사 행 모두에 같은 값으로** 새 필드 `securities_summary` 를 추가(기존 필드·구조 변경 금지, 새 필드 추가만):
   ```
   securities_summary: {
     as_of: "2026-06-30",
     hybrid:       { latest_coupon_pct, latest_issue_date, issued_since_2023_eok, next_call_date, next_call_eok },
     subordinated: { 같은 5개 필드 }
   }
   ```
   - `latest_coupon_pct`: 잔액이 남은 증권 중 `issue_date` 가 가장 늦은 증권의 `coupon_pct`(2023년 이전 발행이어도 그 증권; 같은 날 여러 건이면 발행액 가중평균이 아니라 **금액이 큰 쪽**). `latest_issue_date` 는 툴팁용.
   - `issued_since_2023_eok`: `issue_date >= 2023-01-01` 인 증권의 `outstanding_mn` 합 ÷ 100(억원, 정수 반올림). 해당 증권 없으면 0.
   - `next_call_date`: `past_call_outstanding` 이 false 이고 `call_date >= as_of` 인 증권 중 **가장 이른 콜일**. `next_call_eok`: 그 콜일 증권의 `outstanding_mn` ÷ 100(같은 날 콜이 여러 건이면 합). 해당 증권이 없으면 둘 다 null.
   - 해당 tier 증권이 하나도 없으면 그 tier 객체 전체를 null(`no_capital_securities` 와 별개 — 한쪽 tier 만 있는 회사가 있다). 외화 증권은 파일의 원화환산 `*_mn` 그대로.
3. 회사 코드는 JSON 키로만(화면 노출 없음, 기존 규약). 47사 전부 값/null 판정표를 증빙으로 저장(`data/_derived/` 새 폴더: 회사·tier·값·근거 증권 이름·5개 필드). 한화생명(KR0068) 신종은 사람이 계산해 검산: 최근 발행 = 2025-06-24 외화 6.30%(파일 기준), 2023 이후 합계, 가장 가까운 콜.
4. 같은 규칙으로 **단위시험 추가**(경계: 2022-12-31/2023-01-01 발행, `past_call_outstanding`, 콜일 동일 다건, tier 없음, 변이시험: 날짜 비교 반대/단위 100 누락이면 실패), xlsx 시트(`기본자본소진율`·`보완자본소진율`)는 기존 방식대로 **이 필드가 행 구성에 들어가는지 먼저 확인** — long-format 시트에 새 항목행을 추가하는 것은 스키마 변경이니 **하지 말고** 값이 시트에 안 실리는 것만 보고(필요하면 owner 결정). `public_exports`·`manifest` 재생성, 게이트(`validate_data_contract.py`·`validate_live_artifacts.py`·`check_master_xlsx_drift.py`) 비교.
5. **순서**: 이 티켓을 **먼저** 하고(designer 가 이 필드를 기다린다), 이어서 직전 티켓 `20261012T1130Z`(메리츠·흥국생명 + 예실차 시트)를 한다. 두 작업이 같은 JSON 을 바꾸니 커밋은 분리하되 재산출은 한 번에 정합하게. 필드 명세는 `docs/changelog_publishing.md` 맨 위에 적는다.

### 규칙
- 마스터 JSON(`kics_disclosure.json` 등)·HTML 수정 금지, 예외 등재 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만. 시험·게이트는 한 번에 하나씩 끝까지(PC 가 매우 느림 — 고아 python3.13 프로세스를 보면 보고). 이 공유 티켓은 고치지 않는다.

### 보고 (3~5줄 존댓말)
- 필드 명세 위치, 47사 판정 요약(null 회사 수), 한화생명 검산 결과, 시트 영향, 게이트 결과, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 ad9dfb6): kics_tier1/tier2_utilization.json 의 47사 행에 securities_summary(한화생명 검산 일치; 신종 null 30곳, 후순위채 null 23곳; 추가 필드 next_call_estimated·balance_as_of — 22사 잔액 기준일 2025-12-31). 필드 명세는 docs/changelog_publishing.md 맨 위. xlsx 시트에는 싣지 않음.
