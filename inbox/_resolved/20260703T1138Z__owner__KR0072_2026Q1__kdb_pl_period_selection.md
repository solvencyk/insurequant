---
from: owner
to: designer
created: 20260703T1138Z
status: resolved
route: render
company: KR0072 (케이디비생명보험)
period: 2026.1Q
lane: ifrs17
---

## 미결 (owner site 워크스루) — #5 KDB PL Breakdown 도표가 25.4Q로 조회됨 (26.1Q 나와야) = 렌더 기간선택 이슈, 데이터는 정상

**증상**: IFRS17 사이트에서 KDB(케이디비생명) 당기순이익 분해(PL Breakdown)가 **25.4Q로 조회** — owner는 26.1Q 기대.

**확인 (owner probe) — 데이터 완전, 렌더 문제:**
- **PL_breakdown.json(root)·pl_breakdown_master.json 둘 다 케이디비생명보험 2026.1Q 24항목 전부 채워짐** (보험손익 9539·투자손익 -7079·당기순이익 27834 등). **파서/데이터 이상 없음.**
- Panel 3(당기순이익 분해)는 `PATHS.plx = PL_breakdown.json` 읽음 (IFRS17.html L182·524).
- `plPeriod(name, mode)` (L560): **year 모드**(기본)는 `qs.find(x=>/\.4Q$/)` = 내림차순 첫 4Q = **2025.4Q**를 "최신 FY(연 누계)"로 선택 → KDB만이 아니라 **전사 25.4Q**. **quarter 모드**는 `qs[0]` = 최신분기 = 26.1Q.

**owner 결정 (2026-07-03)**: **year 모드에서 25.4Q(연 누계) 표시는 OK — 의도된 동작.** 위 가설 (a) 채택. 단 **분기(quarter) 모드에서 KDB 26.1Q가 정상 표시되는지만 확인**되면 이 건은 pass.

**요청 (designer) — 축소:**
1. **quarter 모드로 KDB 전환 시 26.1Q가 정상 표시되는지만 확인.** 정상이면 이 건 종결(year 모드 25.4Q는 그대로 둠).
2. 만약 quarter 모드에서도 26.1Q가 안 뜨면 → `plResolve('케이디비생명보험')` name-join 버그이므로 그것만 수정.
3. **데이터·파서는 건드리지 말 것**(정상). year 모드 UX 변경 불필요.

## 답변 (designer, 2026-07-07)

**확인 결과: 정상.** quarter 모드로 KDB(케이디비생명보험) 전환 시 Panel 4(당기순이익 워터폴, PL_breakdown.json)
캡션이 "2026.1Q 당분기"로 정상 표시, 표 마지막 컬럼도 2026.1Q(원수 CSM상각 155·원수 위험조정 45 등) 정상 채워짐.
`plResolve` name-join 버그 없음. 요청 #2(수정) 불필요, 이 건 종결.

year 모드 25.4Q(연 누계) 표시는 owner 결정대로 그대로 유지.
