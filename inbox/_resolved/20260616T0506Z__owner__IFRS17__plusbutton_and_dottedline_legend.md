---
from: owner
to: designer
created: 20260616T0506Z
status: answered
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (owner 라이브 QA) — IFRS17.html 표시 2건

**G1. 장기재보험 옆 "+" 버튼이 못생김.** IFRS17.html에서 **장기재보험** 옆 확장(+) 토글 버튼의 양식을, **K-ICS.html의 "+" 버튼 양식을 SOT로 미러**해서 동일하게 교체. (K-ICS의 + 버튼 클래스/마크업/호버 상태를 그대로 적용.)

**G2. 점선 시리즈(신계약CSM 시계열)가 안 보임.** 해당 차트의 **점선이 "신계약CSM 시계열"**이라는 게 지금 **코드 주석에만** 있어 화면에서 뭔지 알 수 없음 → **legend(또는 명시 라벨/axis-title/툴팁)에 "신계약CSM 시계열"로 박아** 사용자가 바로 식별하게. 주석이 아니라 렌더되는 legend에 노출이 핵심.

### 제약
- master JSON read-only(데이터 변경은 parser). 
- 확정결정 보존: △세모 · 도넛 100%+ · 현대해상 #F47920 · 모바일 당기만.
- `common.css` §5 규약 준수 + legend 밀도 규칙(≤2 inline / ≥3 top·모바일 tooltip).
- preview 375px/1280px 검증, 콘솔 에러 0. preview flaky 시 Edge `--dump-dom` 대신 preview_eval 정상이면 그걸로(designer 회신상 preview 정상).

## 답변 (designer 2026-06-16 — G1·G2 완료, IFRS17.html)

- **G1 +버튼 K-ICS 미러**: K-ICS `.subtoggle`(+ :hover)를 **common.css로 승격(§5 공유 컴포넌트)**, K-ICS inline에서 제거. IFRS17 장기재보험 토글을 inline-styled `<span>＋`에서 **`<button class="subtoggle">`**(K-ICS와 동일 마크업, `+`/`−`, `aria-expanded`, 이름 뒤 배치)로 교체. 양 페이지가 단일 SOT 공유. 검증(Playwright fresh): 버튼 18px·inline-flex·border=--border (= K-ICS 양식). ※preview는 구 common.css 캐시로 처음 UA버튼처럼 보였으나 fresh 로드는 정상 — **배포 시 cache-bust 필요**(아래).
- **G2 점선 식별**: Panel 2(CSM 시계열) dataset 라벨을 주석→렌더 legend로 노출. 실선=**"기말 CSM 잔액 (실선)"**, 점선=**"신계약 CSM 시계열 (점선)"**. legend+tooltip 동일 라벨이라 (실선)/(점선) 표기로 스와치 색만으론 못 가리던 점 해소. legend 밀도 규칙 부합(2시리즈=top inline). 검증(Playwright): histLabels=["기말 CSM 잔액 (실선)","신계약 CSM 시계열 (점선)"].
- 확정결정 4개 유지, master 무수정. Playwright 하니스에 G1/G2 assert 추가 → **24 assert GREEN**.

**배포 주의(publishing/owner) — cache-busting**: `common.css`를 갱신하면 재방문자 브라우저가 구버전을 캐시해 새 공유 규칙(.subtoggle 등)이 안 먹을 수 있음. 배포 시 `common.css?v=<hash>` 또는 캐시 헤더로 무효화 필요. (신규 방문/하니스는 영향 없음.)

status: answered.
