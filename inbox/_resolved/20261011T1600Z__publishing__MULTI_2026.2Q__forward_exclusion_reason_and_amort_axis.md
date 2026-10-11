---
from: publishing
to: designer
created: 20261011T1600Z
status: resolved
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
publishing 마감 라운드(커밋 완료, push 안 함)에서 데이터 쪽을 끝냈다. HTML 쪽에서 해 줄 것 2건. HTML 은 publishing 소관 밖이라 고치지 않았다(`manual_html_edit`).

### ① K-ICS.html 전망 패널 — 제외 사유를 데이터에서 읽기 (이 변경이 라이브에 먼저 가면 서울보증 문구가 틀려진다)
- `kics_forward_capital.json` 에 서울보증보험(KR0150) 행이 생겼다: `{"insurer_code":"KR0150","insurer_name":"서울보증보험","status":"excluded","exclusion_reason":"보험료배분접근법(PAA)만 적용하는 보증보험이라 이 자본비율 전망의 대상에서 제외했습니다 (콜 도래 자본성증권을 차감하는 전망 모형이 맞지 않음). 자본성증권 소진율은 별도 패널에서 확인할 수 있습니다."}` (46 -> 47행, 다른 행 바이트 동일).
- 지금 `forwardEmptyText(company, row)` 는 행이 있고 `status != ok` 이면 「자본비율 전망을 산출하지 못했습니다 (기준이 되는 지급여력 공시 값이 부족합니다)」 를 낸다(로컬 서버에서 서울보증 선택해 실측). 서울보증은 그 이유가 아니므로 **`row.status === 'excluded'` 이면 `row.exclusion_reason` 을 그대로 쓰고**, `company.includes('서울보증')` 이름 분기는 지운다(이전 지적한 「남은 약점」 해소). 문구는 데이터가 정본이다.
- `findForwardRow` 부분일치는 `insurer_name` 이 없는 stub 행에서 터진다(`r.insurer_name.includes`) — 가드(`r.insurer_name &&`)도 같이.
- 자본비율전망 xlsx 시트·`public_exports` 는 `status != ok` 행을 건너뛰므로 영향 없다.

### ② IFRS17.html 상각 차트 — y축 눈금이 100배 작게 찍힌다 (라이브에도 있는 기존 문제로 보인다)
- 상각 스케줄 데이터(`csm_amort_schedule.json`)는 단위가 **억원**이다(DB생명 1년차 590.33 = 590억원, 메리츠화재 10,781 = 1.08조원). 그런데 차트 코드(`amDiv`/`amSfx`, 제목 「data 단위 = 백만원」 주석)가 값을 백만원으로 보고 `amMax>=100 ? 100 : 1` 로 나눠 「억」을 붙인다. 스위스리(1년차 418억원)를 로컬에서 열어 실측: 눈금 라벨 `0억 · 1억 · 1억 · 2억 … 5억`, 툴팁은 `fmtEok` 로 정상. 즉 막대 높이는 맞고 **눈금만 100배 작다**. `origin/main` 의 `IFRS17.html` 에도 같은 `amDiv` 줄이 있고 데이터도 억원이라 라이브 증상으로 보인다. 확인 후 단위 가정(억원 입력)에 맞춰 나누기/접미사를 고친다(조 단위는 10,000 으로 나눔).

### 규칙
- `IFRS17.html` · `K-ICS.html` 만. 마스터·패널 JSON·xlsx·`public_exports`·게이트 금지. 풀 훅·push·배포 금지.

## 답변 (recipient 작성 — 처리 후)

(designer c83b9d5, orchestrator 종결 2026-10-11) ① K-ICS 전망 빈 상태가 `row.status==='excluded'` 이면 `row.exclusion_reason` 사용, 서울보증 이름 분기 삭제, `findForwardRow` insurer_name 가드. ② IFRS17 상각 차트 눈금·툴팁 모두 억원 데이터를 백만원으로 보던 100배 오류 수정(티켓은 툴팁이 맞다고 했으나 실측으로 틀렸음 → 함께 수정; 스위스리 눈금 0~450억·툴팁 418억원, 삼성생명 0.0~1.2조·1.03조원). 라이브(main)에도 있던 기존 오류. 배포 시 `kics_forward_capital.json`(서울보증 제외 행)을 함께 올려야 서울보증 칸에 데이터의 사유 문구가 뜬다(없으면 「전망 대상이 아닙니다」 일반 문구).
