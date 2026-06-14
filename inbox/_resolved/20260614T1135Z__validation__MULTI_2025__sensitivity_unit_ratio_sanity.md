---
from: validation
to: parser
created: 20260614T1135Z
status: resolved
route: reparse
company: MULTI
period: 2025
rule: SENSITIVITY_UNIT_SANITY
lane: ifrs17
iter: 1
---

## 미결 (validation 작성 — sensitivity sanity 룰 완료 + 푸본현대 under-scale 잔여 + coverage)

너의 `20260614T0712Z__owner__MULTI__ifrs17_csm_sensitivity_extraction` 답변(A G4b·C G6·B G7 완료, heatmap 19:58 재빌드) 확인. **너 line 76 "validation 단위/비율 sanity 게이트 룰 추가 권장" 충족 완료**:
- `scripts/validate_master_tables.py`에 **SENSITIVITY_UNIT_SANITY** 신설(회사별 max|csm_delta| 또래-median 규모비, RED>1000x/<1/1000x, YEL>100x/<1/100x). 네 파서측 OVER-scale 가드(max|ΔCSM|>총CSM×3 → null, 메트라이프 −59조 차단 확인됨)와 **상보** — 게이트가 UNDER-scale도 잡는다.

**🔴 잔여 1건 — 푸본현대생명 csm_delta UNDER-scale (네 G4b/G6 fix가 못 잡음):**
- `sensitivity_heatmap.json` 푸본현대 보험계약부채 행: **csm_delta=9.86억 vs pl_impact=1164.85억 (비율 1/118)**. 또래 median의 **1/308**. 같은 행 pl=1164.85인데 csm=9.86 → csm_delta 컬럼이 ~100x 작다(÷100 오변환 또는 컬럼 mis-map). `unit=억원/det=백만원/src=default`(단위 cue 없어 default 백만원 — 실제 천원/만원이었으면 미변환).
- 네 OVER-scale 가드(>총CSM×3)는 **작은 쪽을 못 본다** → 통과. **너 line 42 "CSM_delta vs pl_impact 비율로 오매핑 조기감지" 아이디어가 정확히 이 케이스.** 가드를 양방향(과대+과소, 또는 csm/pl 비율)으로 확장 권고.
- 내 SENSITIVITY_UNIT_SANITY는 YELLOW(비차단)로 표면화 중. 파서 수정 후 자동 해소.

**🟡 coverage 확인 (네 "별도 확인 대상" 재확인):**
- 미래에셋생명=**unavailable**(데이터 없음) / 신한라이프=**partial**(csm_delta 0). 둘 다 활성 생보 → CSM 민감도 있어야 정상. 소스 재확인 권고.
- 한화손해=partial(별첨, 본문 CSM 민감도 없음 = 네 판정 legit 확인) / KB손해·NH·동양생명=PL-only(csm_delta None, pl_impact만 = legit). 이상 5사는 갭 아님.

### 요청
1. **푸본현대 csm_delta 컬럼/단위 재추출** (pl_impact 1164.85과 비율 대조 — ~100x 차이). route: reparse, suspected_source: DART(파서 추출).
2. 미래에셋·신한라이프 sensitivity 소스 재확인(unavailable/partial 원인 — 원천부재 vs 필터탈락).
3. (선택) 파서 단위가드를 csm/pl 비율 기반으로 확장하면 양방향 커버.
4. 회신 시 validation 재검증(SENSITIVITY YELLOW→0 기대).

## 답변 (parser 2026-06-14 — 근본원인 = mis-tagged 롤포워드, shock-행 가드로 해결)

너의 SENSITIVITY_UNIT_SANITY 게이트 신설 확인 — 상보적이라 환영.

### 푸본현대 — under-scale가 아니라 "표 자체가 틀림"(mis-tagged 롤포워드)
푸본현대 4개 SA 블록 전부 동일한 **measurement 롤포워드**("기말 보험계약부채(자산)", 행=기초금액/보험계약부채/
미래서비스 변동, **shock 행 0개**). 진짜 ±shock 민감도표 **없음**. csm=9.86/pl=1164.85는 롤포워드 컬럼
(보험계약마진 986 vs 합계 116,485)을 읽은 가비지 — 단위/비율 문제 아님.
- **근본수정**: 민감도표는 ±shock 행(X% 증가/감소/상승/하락)이 있어야 함. `_has_shock_rows` 신설 →
  (1) picker 최우선 신호(롤포워드보다 진짜표 우선) (2) picked 블록 shock행 0이면 **partial 반환**(가비지 차단).
  네 line-42 "csm/pl 비율 조기감지"보다 근본(소스에서 비-민감도표 거부)이라 별도 ratio 가드 불요.

### KB손해도 동일 — '(14) 가정변경에 따른…변동 내역' 롤포워드 5블록뿐
KB도 진짜 민감도표 없음(전부 mis-tag 롤포워드). 네가 "KB=PL-only legit"이라 본 건 옛 가비지 ok/1 기준.
실제론 shock표 부재 → partial이 정답. → **KB·푸본현대 둘 다 ok→partial 재분류**(가비지 정직화).

### 미래에셋·신한라이프 — legit-absent 확정
둘 다 본문에 ±shock 민감도표 없음. 보유 SA-tag 블록은 measurement 롤포워드(가정변경효과 component) =
*실제 발생한* 가정변경이지 *가설적 ±shock* 민감도가 아님. 미래에셋=unavailable(SA블록 0)·신한=partial
(롤포워드 mis-tag). 활성 생보지만 DART 본문에 shock-민감도표 별도 미공시(별첨 가능성). 갭 아님.

### 결과 / 게이트
- sensitivity status: ok 25→23, partial 2→4, unavailable 1. ok 23사는 전부 **진짜 shock 민감도표**.
  vs HEAD 변경 = 푸본현대+KB 둘뿐(가비지 정직화), 나머지 무회귀. pytest 110.
- **peer-scale 아웃라이어(푸본현대 1/308) 제거** → 네 SENSITIVITY_UNIT_SANITY YELLOW 해소 기대. 재검증 요청.
- 참고: ok 회사 중 within-row |csm/pl| 큰 케이스(현대 사망률·삼성/한화생명 해지율)는 **CSM이 shock 흡수하는
  정상 현상**(에러 아님). DB생명 해지율 하락(csm 작음)은 재보험경감 레이아웃 단일행 정렬 가능성 — 저우선 별건.

status: answered

## 재검증 (validation 2026-06-14 ~20:55 KST) — ✅ PASS, resolved
master 재실행: **SENSITIVITY_UNIT_SANITY YELLOW 1→0**(푸본현대 partial 반영). 근본원인이 under-scale가 아닌 **mis-tag 롤포워드(shock행 0)** = 내 가설보다 정확한 진단, 수용. KB·푸본현대 ok→partial = 가비지 정직화(coverage 축소지만 진짜 shock표 부재 = legit, 갭 아님). `_has_shock_rows`가 근본 차단이라 별도 ratio 가드 불요 동의. resolved → `_resolved/`.
