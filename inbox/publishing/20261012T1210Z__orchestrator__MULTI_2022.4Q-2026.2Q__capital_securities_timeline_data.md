---
from: orchestrator
to: publishing
created: 20261012T1210Z
status: open
route: feature
company: MULTI
period: 2022.4Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 결정(2026-10-12 채팅): K-ICS 화면의 소진율 도넛과 Forward Outlook 을 내리고(designer 티켓 `20261012T1220Z`), 그 자리에 **시점별 자본성증권 발행현황 누적 막대(아래 신종자본증권 + 위 후순위채)** 를 둔다. 분류 판단(기본자본형/보완자본형)이 들어가지 않는 **건조한 잔액**만 쓴다. 이 티켓은 그 그래프의 데이터를 만드는 일이다.

### 해 줄 것
1. **시점별 잔액 JSON 신설**: 회사 × 시점 × tier(`hybrid`=신종자본증권, `subordinated`=후순위채) 잔액(억원). 시점 = DART 정기보고서 사채/자본증권 발행현황 표가 있는 모든 기간(원문은 `data/dart/FY2022_Q4`…`FY2026_Q2` raw 에 있다; 사업보고서·반기보고서에 표가 있고 분기보고서에는 없을 수 있다 — 있는 시점만). 추출은 기존 `scripts/build_capital_securities_fy2026h1.py`·`build_capital_securities_recognition.py`·`data/dart/capital_securities_issuance.json` 등 기존 경로를 재사용(동일 규칙: `outstanding` 잔액, 원화환산). 각 시점은 **그 시점 보고서의 잔액**을 쓴다(상환된 증권을 놓치는 생존 편향 방지: 현재 시점 파일에서 과거를 역산하지 않는다). 교차검산: 신종 잔액을 같은 시점 `kics_disclosure.json` 항목 6(보통주 이외 자본증권, BS 계상액)과 비교해 큰 괴리(예: 20% 초과)는 목록으로 보고.
2. 파일 위치·이름은 기존 규약대로(배포 JSON 은 루트, 예: `kics_capital_securities_timeline.json`; 배포 keep-list `tests/test_deploy_assets.py` 와 `scripts/` 의 배포 목록 등록 포함 — HTML 은 건드리지 않는다). 필드 명세(회사 코드는 JSON 키로만, 시점 표기 `YYYY.nQ`, 단위 억원, 누락 시점 처리, `source`·`as_of`)를 `docs/changelog_publishing.md` 맨 위에 적는다. 회사코드는 화면 노출 금지 규약.
3. **분류 없음**: tier 는 증권의 `tier` 필드(`hybrid`/`subordinated`)만 쓰고 기본자본/보완자본 판단 필드를 넣지 않는다.
4. 단위시험(경계: 상환·신규 발행 시점, 외화 환산, 표 없는 시점), 게이트(`validate_data_contract.py`·`validate_live_artifacts.py`) 비교, 새 RED 는 덮지 말고 보고. 이 JSON 이 xlsx 시트로 나갈지는 owner 결정 전이니 **시트 신설하지 말고** 보고만.
5. **순서**: 이 티켓은 `1150Z`(큼직한 셀용 요약 필드) 직후, 나머지 `1130Z` 항목들보다 **먼저**.

### 규칙
- 마스터 JSON(`kics_disclosure.json` 등)·HTML 수정 금지, 예외 등재 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지, docling 금지(DART XML 은 docling 불필요). 파이썬은 풀패스·스크립트 파일만. 시험·게이트는 한 번에 하나씩 끝까지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~5줄 존댓말)
- 파일 이름·시점 범위·회사 수, 항목 6 대비 큰 괴리 목록, 게이트 결과, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
