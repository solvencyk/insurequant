---
from: owner
to: designer
created: 20260814T0232Z
status: resolved
route: backlog
company: MULTI
period: ALL
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

**owner 지시 (2026-08-14): `equity_composition.json`(항목 1-49)을 아카이브한다.**
`IFRS17.html` **Panel 7(재무상태표·자본의 질)** 이 이 파일을 fetch 하고 있어서 그대로 두면 404 난다.

파서 발주 `inbox/parser/20260814T0232Z`, 게이트 `inbox/validation/20260814T0232Z`.
**main 에는 올라간 적 없다** (`git show main:IFRS17.html` 에 참조 0건) — 라이브 영향 없음,
이 브랜치만 고치면 된다.

### 할 일

`IFRS17.html:267` 의 `eqx: [resolveUrl("equity_composition.json")]` 를 **`IFRS17_BS.json`** 으로 바꾸고
Panel 7 을 새 스키마에 맞춰 축소한다.

**새 마스터 스키마** (1,207행 / 37사 / 2022.4Q-2026.2Q, 8열, `값_당분기` 없음 — 전부 스톡):

| 항목번호 | 항목명 |
|---|---|
| 1 | 자산총계 |
| 2 | 부채총계 |
| 3 | 자본총계 |
| 4 | 기타포괄손익 누계액 |
| 5 | 해약환급금준비금적립액 (일부 회사만 — 결측 정상) |
| 6·7 | 비상위험준비금·대손준비금 (파서가 "가능하면" 추가 중, 없을 수 있음) |

**항목번호가 다르다.** 기존 Panel 7 은 40/41/1/6 을 쓰는데 새 마스터는 1/2/3/4 다. 그대로 두면
자산총계 자리에 부채총계가 들어간다 — 반드시 다시 매핑할 것.

### 빠지는 것 (되살리려 하지 말 것)

- **L2 자본구성 드릴다운(항목 2-7: 자본금·자본잉여금·신종자본증권·이익잉여금·자본조정)**
- **L3-a AOCI 워터폴(항목 20-31)** — owner: *"필요한 건 기말 AOCI뿐이라 검증할 등식조차 없다."*
- **L3-b 법정준비금 3종 중 12/14** 는 파서 결과에 따라 있을 수도 없을 수도. **없으면 그 줄을 빼라**
  (0 으로 채우지 말 것).

**오케스트레이터 판단으로 정한 기본값:** 패널을 통째로 지우지 않고 **L1(자산/부채/자본/AOCI +
있으면 해약환급금준비금)만 남긴다.** owner 가 이번 대화 내내 원한 게 정확히 이 4-5개 항목이라
패널 자체는 값이 있다고 봤다. **통째로 빼길 원하면 owner 가 뒤집을 것** — 그때까지 이대로 간다.

### 주의

- **AOCI 는 음수가 정상**이고 화면 음수는 전부 **△(세모)** 표기(프로젝트 상시 룰).
- 항목 5-7 은 **회사마다 결측이 정상**이다. 빈 칸을 0 으로 렌더하지 말 것 — 한화생명 AOCI 가
  "0 처럼 보였던" 게 이번 라운드 혼선의 출발점이었다.
- 데이터를 HTML 에 인라인하지 말 것(프롬프트 §4).
- publishing 에 keep-list 갱신을 따로 발주했다(`inbox/publishing/20260814T0232Z`) —
  **HTML 이 fetch 하는 파일과 keep-list 가 어긋나면 배포 후 404** 다. 파일명 표기를 맞출 것.

### 확인

- 브라우저 콘솔 404 0건, Panel 7 이 37사에서 렌더되는지
- `pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` 통과

## 답변 (recipient 작성)

처리 완료.

- `IFRS17.html:267` `eqx` 경로를 `IFRS17_BS.json`으로 교체, `renderBsSection`의 항목번호를
  40/41/1/6/10 → 1/2/3/4/5(자산/부채/자본/AOCI/해약환급금)로 재매핑. 항목 6·7(비상위험준비금·
  대손준비금)은 L1 타일 스코프 밖(08-14b 결정 유지)이라 렌더에 안 씀 — "빠지는 것" 지시 그대로.
- L2/L3 죽은 코드(코드 보존, 호출 안 함)에 항목번호 재사용 함정 경고 주석 추가 — 새 스키마도
  1-7을 쓰기 때문에 그대로 되살리면 null이 아니라 다른 항목의 값이 엉뚱한 라벨로 뜬다.
- `claude-agent-designer.md` §1에 `IFRS17_BS.json` 추가(기존에 `equity_composition.json`도 한 번도
  없었던 게 애초 갭이었음 — validation 티켓 `20260814T0135Z`도 같이 해소).
- 확인: 로컬서버로 드롭다운 39개사 전부 순회, 콘솔 에러/404 0건. `equity_composition.json`은 이제
  아예 fetch되지 않음. `IFRS17_BS.json` 200. 항등식(KR0001), "미공시" 폴백(KR0004, 항목5 전분기
  없음), no-BS-data 스텁(KR1098) 전부 정상. Browser pane 스크린샷은 08-14b부터 이어지는 세션
  컴포지팅 이슈로 실패해 network log + DOM 텍스트로 대체 검증.
- `pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` — designer 쪽(본 티켓
  스코프)은 통과. **publishing 쪽(`claude-agent-publishing.md`)은 별도 티켓
  (`inbox/publishing/20260814T0232Z`) 미완이라 전체 테스트는 아직 FAIL** — 그건 퍼블리싱 세션 소관.
- push는 여전히 publishing keep-list 교체 + RED=0 게이트 + owner 승인 대기. 이 세션은 실행 안 함.

상세: `docs/changelog_designer.md` 2026-08-14c, `TODO_designer.md` BS-DRILLDOWN 절.
