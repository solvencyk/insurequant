---
from: validation
to: validation
created: 20260921T0630Z
status: open
route: blind_spot
company: ALL
period: N/A
rule: (미배선) UH-26 DEPLOYED_JS_RUNTIME_SMOKE
iter: 1
---

## 미결 (sender 작성)

**UH-26 — 배포 페이지의 "런타임 전용" 실패는 아직 어느 게이트도 안 본다.**

2026-09-21 에 신설한 `scripts/validate_deployed_js.py`(훅 §1f)는 **정적 축**이다. 판정은
"이 이름이 페이지의 어떤 스크립트에도 바인딩되지 않는다" 하나뿐이고, 그래서
`ReferenceError`(이번 `IQP` 사고)는 잡지만 아래는 **구조적으로 못 잡는다**:

1. `TypeError: a.b is not a function` — 객체는 있는데 메서드가 없다(라이브러리 버전 변경·
   `theme.js` API 개명).
2. `document.getElementById('…')` 가 null 인데 바로 `.style`/`.value` 접근 — HTML 에서 id 를
   바꾸고 JS 를 안 고친 경우. **배포 4종에 id 참조가 많아 이 부류가 가장 그럴듯하다.**
3. 차트 옵션 스키마 오류(Chart.js·ECharts 가 조용히 빈 캔버스를 그리는 형태).
4. fetch 응답 모양 변화 — 마스터 스키마가 바뀌었는데 화면이 옛 키를 읽는 경우. 데이터 게이트는
   마스터만 보고, 정적 축은 문자열 키를 안 본다.
5. **스코프 오류** — 안쪽(IIFE·함수) 에서 정의하고 바깥에서 부르는 형태. 정적 축은 `defined` 를
   페이지 전체의 평평한 합집합으로 과대추정하므로 못 본다. 실측: `function NAME(` 전수 변이
   183건 중 **9건이 이 이유로 미검출**(`shortName`×4 · `render` · `boot`×2 · `q` · `val` —
   전부 같은 이름이 `download-survey.js`/`theme.js` 의 IIFE 안에도 있다).

### 왜 이번에 안 배선했나 (판단 근거 — 되풀이 금지)

헤드리스 브라우저를 **차단 축**으로 쓰려면 선행조건이 둘이고, 둘 다 지금 없다.

- **(가) 오프라인.** 배포 4종은 CDN 4종(chart.js · chartjs-plugin-annotation · echarts · xlsx)
  을 로드한다. 훅은 오프라인에서도 돌아야 하므로 스텁이 필요한데, 스텁을 쓰는 순간 검사 대상이
  "사용자가 보는 그 페이지" 가 아니게 된다(불변식 1번과 정면으로 부딪힌다). 대안은 SRI 가 박힌
  그 자산을 로컬에 캐시해 같은 해시로 먹이는 것 — 그러면 진짜 페이지다.
- **(나) 브라우저 없는 클론에서의 fail-open.** 리눅스 컨테이너·Termux 클론에는 브라우저가
  없다. 거기서 SKIP 으로 떨어지면 **"안 돌렸다"가 "통과했다"로 읽힌다** — 이 저장소가 반복해서
  데인 바로 그 형태다(`docs/postmortems/README.md` 전체가 그 기록). 설계에 "브라우저 없음 =
  이 축은 미검사임을 verdict 에 찍는다" 가 들어가야 한다.
- 이 머신에서 헤드리스 반복 실행이 행으로 죽은 전례가 있다(우회는 Edge headless `--dump-dom`).

### 시킬 일 (다음 라운드)

1. **타당성 먼저, 배선은 그다음.** (가)(나)의 해법을 한 장으로 정리하고 실측:
   CDN 로컬 캐시 4개 SRI 일치 확인 · 브라우저 유무 판정 · 4페이지 로드 시간.
2. 범위 제안: 페이지당 **회사 셀렉터 전수 순회는 하지 말 것**(39사 × 4페이지 = 게이트 예산
   초과). 회사 3개(대형 생보·손보·마이크로) × 최신 분기 + 분기 셀렉터 1회 변경으로 시작하고,
   **그 표본이 무엇을 못 보는지 게이트가 인쇄**하게 한다.
3. 판정은 `uncaught error 0` 만이 아니라 **console.error 0 + 주요 패널 DOM 가시성**까지.
   이번 사고는 예외가 나도 화면 절반이 그려져 있었다.
4. 배선하면 `tests/test_push_gate_wiring.py` `WIRED` 등재 + 변이시험(브라우저 축은
   "고의로 깨진 페이지 fixture" 로) + `docs/postmortems/README.md` UH-26 해소 기재.

근거·실측: `docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md` §2·§5.
재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_deployed_js.py`

## 답변 (recipient 작성 — 처리 후)
