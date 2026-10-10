---
from: orchestrator
to: designer
created: 20261010T0810Z
status: resolved
route: feature
company: MULTI
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 요청(2026-10-10): index 시장지도(히트맵·순위 리스트)가 지금 **생명보험 / 손해보험 2컬럼**인데, **생명보험 / 손해보험 / 재보험사·보증 3컬럼**으로 나눈다.

### 3번째 컬럼에 들어갈 회사
- **코리안리(KR1000)** — 지금 마스터에 `생손보여부=손해보험` 이라 화면에서 손보에 섞여 있다.
- **서울보증보험(KR0150)** — 같은 이유로 손보에 섞여 있다.
- **외국 재보험사 국내지점 7곳(KR1101~KR1107)** — 이번 K-ICS 스윕으로 `kics_disclosure.json` 에 새로 들어왔다. 마스터의 `생손보여부` 가 생명보험/손해보험으로 제각각이다(스위스리·제네럴·하노버·RGA·스코리·퍼시픽라이프리=생명보험, 뮌헨=손해보험). 분류를 안 하면 라이브에서 생보·손보 컬럼에 잘못 섞여 들어간다.
- **마이브라운반려동물전문보험(KR1108)은 재보험사가 아니다** — 일반 손해보험사(펫보험)라 손보 컬럼에 그대로 둔다.

### 지켜야 할 것
1. **분류는 마스터 셀을 고치지 않고 매핑으로 한다.** 기존 39사 `생손보여부` 셀 변경 금지(재보사 적재 안전 규칙). 매핑 파일/상수 1곳(예: `data/_derived/company_segment.json` 또는 viz 빌더 상수)에 코드→구분(생명·손해·재보험/보증)을 두고, 화면은 그것만 읽는다. 매핑에 없는 새 회사는 기존처럼 `생손보여부` 를 따른다.
2. **회사코드는 화면·주소·다운로드에 노출 금지**(CLAUDE 메모리 `company_codes_internal_only`). JSON 열람은 허용.
3. 모바일(MOB-INDEX-FOLD 생보/손보 각 top 5 + 더보기)과 `maxV` 섹터 독립 스케일, 버블맵·정렬(생보→손보→재보·보증), 범례·필터 드롭다운(`Life/Non-Life` 옵션)까지 3분류로 일관되게. 재보험사·보증 컬럼은 회사 수가 적으니(최대 10곳) 접기 없이 전부 보여도 된다.
4. **새 8곳(KR1101~KR1108)이 `kics_disclosure.json` 을 읽는 모든 페이지에서 어떻게 보이는지 점검**한다: index · `K-ICS.html` · `compare.html` · `IFRS17.html`(IFRS17 데이터가 없는 회사는 어떻게 되는지) · 검색창 추천 · 엑셀 다운로드 시트. 깨지거나 빈 줄이 생기면 고친다. 재보사는 IFRS17 지표가 없고(다음 round 적재), 일부 분기는 버킷 자체가 없다(2023.2Q~ 비공시 등).
5. 코리안리·서울보증이 컬럼을 옮기는 것은 화면 변경이다 — 업계 중앙값(compare.html "같은 유형 중앙값")·평균·순위가 바뀌는 곳을 목록으로 적어 둔다(숫자 자체는 바뀌지 않지만 비교 모집단이 바뀐다).
6. 배포 선행 조건이다: 이 작업이 끝나기 전에는 재보사 8곳이 든 `kics_disclosure.json` 을 라이브에 올리면 안 된다. 끝나면 `TODO_designer.md` 에 "재보사 3분류 반영 완료"를 적어 publishing 이 알 수 있게 한다.

### 이전 세션이 중간에 끊겼다(2026-10-10 17:22)
앞선 designer 에이전트가 owner 의 도구 거절 인터럽트로 중단됐다. 워킹트리에 그 세션의 **미완성·미검증 수정**이 남아 있다: `index.html`(+105/−52) · `K-ICS.html`(+7) · `compare.html`(16행) · `data/compare/panel_compare.json`(1행) · `scripts/viz_build_compare_panel.py`(28행) · 신규 `data/company_segment.json`(매핑 파일). 되돌리지 말고 `git diff` 로 읽어 이어서 완성·검증한다(다른 세션 변경은 위 5개 파일에 없었다 — 시작 시점 git status 기준). 매핑 파일의 구성(Life/Non-Life/Re + 코리안리·서울보증·KR1101~1107)은 이 티켓의 의도와 같다.

### 방법
- 빠른 1차(effort medium): 매핑 + index 3컬럼 + 다른 페이지 점검 목록. 로컬 미리보기는 `?iq_internal=1` 로 진입(GA4 내부 플래그).
- designer 는 push·commit 하지 않는다.
- RAM 15.5GB PC: 서브에이전트 금지, 브라우저 탭은 1개만.

## 답변 (recipient 작성 — 처리 후)
designer 반영 완료(2026-10-10, 미커밋). data/company_segment.json 매핑으로 index 시장지도·compare 3구분(생명/손해/재보험·보증), 새 8곳 점검 완료(TODO_designer.md Status). 배포 전 publishing 이 NEW_FILES 에 매핑 파일 추가 필요. 오케스트레이터 검증: 빌더 --check 동일, test_deploy_assets·test_push_gate_wiring 통과(74 passed). 모델 Sonnet.
