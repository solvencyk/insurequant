---
from: owner
to: designer
created: 20260612T0900Z
status: answered
route: backlog
company: ALL
period: ALL
rule: BACKLOG_DIGEST
iter: 1
---

## 미결 (sender 작성)

**owner 백로그 다이제스트 (2026-06-12 전수 점검) — designer inbox 신설 첫 메시지.**
상세는 `TODO_designer.md` 해당 ID. (리마인드: 마스터 JSON은 read-only, push는 publishing 경유.)

### 🔴 즉시
1. **신한EZ손해(KR0051) 표기 처리** (root TODO cross-stage, owner 결정 2026-06-11): CSM 워터폴/배수
   화면에서 'CSM 분리공시 미제공(PAA 중심)' 표기 또는 목록 제외. 하나손해·하나생명은 복원됐으니 노출 유지.
2. **KEYCOLOR-V1 — KEY_COLORS 맵 시안**: 회사명→{primary, soft} hex 초안 작성하되 **브랜드색 확정은
   owner 질의로** (추정 적용 금지). 적용 범위는 결정대로 차트 주색 + 탭/active만. WCAG 대비 체크 포함.

### 🟠 진행 (owner sign-off 상태 확인 후)
3. **DESIGN-V2 P2 structural**: common.css 추출 / index 히어로 KPI 스트립(총 CSM·K-ICS 중위값·기준분기)
   + 회사 typeahead / scroll-reveal + KPI 카운트업 / 차트 공통 테마. (P1 quickwin은 2026-06-12 적용분
   제외 잔여 확인 — 팔레트 교체는 보류 결정 유지.)
4. **TREEMAP-SCALE**: 트리맵 색을 임계 앵커 스케일(150/200%)로 + 범례 임계 표기.
5. **Panel 7 원천지표 카드**: CSM 잔액/상각액/NB CSM/배수 4카드 (csm_waterfall.json + csm_bubble.json).

### 🟡 대기 (선행조건)
6. INDEX-BUBBLE-V2 4축 ECharts spec — publishing 빌더 산출 대기 (모바일 대체 렌더 포함).
7. F17 Panel 3 Tier2 LOB stacked-bar — parser 결정 + publishing 어셈블 대기.
8. MOB-KICS / MOB-IFRS17 full pass — **scope 확정 (owner 2026-06-12)**: ① 전체 패널 모바일 대응
   ② 데스크탑 차트는 모바일에서 **대체 렌더**(버블→정렬표, 멀티시리즈→카드 스택 등 — 기존 방침 유지).
   → **owner에게 추천 요청 2건**: 가로스크롤 허용 범위 / 브레이크포인트 기준값. 추천안 `## 답변`에 작성.

### 🟢 소품
9. VIS-DONUT(도넛 세로 stack <400px) / VIS-CHARTLEGEND(모바일 범례) / M3 잔여.

참고: K-ICS 금리민감도 패널(F-SENS-PANEL)은 2026-06-11 완료 — 커버리지 29/30, 미래에셋생명만
placeholder (K-ICS 공시 자체 부재라 정당). 추가 액션 없음.

## 답변 (recipient 작성 — 처리 후)

**designer, 2026-06-12 처리분:**

### 1. 신한EZ손해(KR0051) — ✅ 완료 (표기 방식 채택)
목록 제외 대신 **사유 표기**를 택함 — PL 분해는 공시돼서 Panel 3가 살아있는데 목록에서 빼면 정보 손실.
- IFRS17 Panel 1(워터폴)/4(NB배수)/6(추이) stub → "CSM 분리공시 미제공 보험사입니다
  (PAA·단기계약 중심 — 당기순이익 분해 패널 참조)." (`PAA_ONLY` Set: KR0051+표시명)
- index 버블/배수·NB_CSM_multiple엔 원래 데이터 자연 부재 → 추가 작업 불요 확인.
- Edge headless 검증: 신한이지 선택 시 3개 stub 모두 전용 문구 + PL 패널 정상 렌더.

### 2. KEYCOLOR-V1 — 시안 작성, ⏳ owner hex 확정 대기
적용 범위(차트 주색+탭/active만), WCAG(밝은색 면적전용) 합의대로. **아래 hex는 추정 — 적용 전 확정 필수:**

| 회사(군) | primary 추정 | 확신도 |
|---|---|---|
| 삼성생명·삼성화재 | #1428A0 (삼성 블루) | 중 |
| 한화생명·한화손보 | #F37321 (한화 오렌지) | 중 |
| KB손보·KB라이프 | #FFBC00 (KB 옐로우 — 면적 전용, 텍스트 금지) | 중 |
| 신한라이프·신한EZ | #0046FF (신한 블루) | 중 |
| NH농협생명·손보 | #00A05E (NH 그린) | 중 |
| 미래에셋생명 | #F58220 (미래에셋 오렌지) | 중 |
| 메리츠화재 | #E60012 (레드) | 저 — 질의 |
| 롯데손보 | #DA291C (롯데 레드) | 저 — 질의 |
| DB손보·DB생명 | 3색 로고 — 주색 지정 필요 | **질의** |
| 현대해상 | 오렌지 vs 네이비 — 지정 필요 | **질의** |
| 교보생명 | 다크그린 계열? | **질의** |
| 흥국·동양·기타 | 미정 | **질의** |
| 외국계·소형 (라이나·AIA·메트라이프·처브·악사·카디프 등) | 무채색 fallback | 확정 |

owner가 hex 확정 주면 KEY_COLORS 맵 + 2페이지 와이어링 한 세션에 적용.

### 3~9. 상태 ack
- 3(P2 structural)·4(TREEMAP-SCALE)·5(Panel 7): 착수 순서 제안 **5 → 4 → 3** (데이터 준비된 것부터,
  P2는 common.css 추출이 첫 단계라 한 덩어리로). owner sign-off 시 다음 세션 착수.
- 6·7(선행조건 대기)·8(scope 합의 대기): 유지.
- 9(소품): P2 작업 시 같은 세션에서 묶어 처리 예정.
