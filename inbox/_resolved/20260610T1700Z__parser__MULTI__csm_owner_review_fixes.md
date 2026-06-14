---
from: parser
to: validation
created: 20260610T1700Z
status: resolved
route: reparse
company: MULTI (KR0003, KR0072, KR0079 / 제외: KR0050, KR0097, KR0051)
period: ALL
rule: CSM_CONTINUITY, AMORT_ZERO_NEW
iter: 1
---

## 미결 (parser 작성)

**owner xlsx 수동검토 정정 반영 완료 — CSM 마스터 재조립 + 신규 검증룰 1건 요청.**
(owner가 너희한테도 별도 통지했다고 함 — 이 메시지가 parser측 반영분 정본.)

### 1. 반영 내용 (CSM_waterfall.json 1926→1908행)

owner 수기정정은 **`data/dart/viz/csm_manual_overrides.json`**으로 영속화 — `build_root_masters.py`가
diag 로드 직후 적용(upsert 32 + 신규행 12 + 회사제외 3)하고 값_당분기는 항상 재계산. **diag 재빌드에도 생존.**

- **롯데(KR0003) 2023.1Q 신규 + 2023.2Q 정정**: 기초 18004.6→16774.38 등 전항목. root cause = 롯데 다중
  정정공시 중 구공시 채택(XML 공시 이전 시기). 기존 inbox 건(`...KR0003_FY2023__continuity`, justified_restatement
  verdict)은 **owner가 뒤집음** — 재진술이 아니라 구공시 오채택. 해당 verdict 폐기 바람.
- **케이디비(KR0072) 2023.1Q/2Q**: 상각 공란→-111.25/-234.15, 조정·기말 동반 정정.
- **미래에셋(KR0079) 2023.1Q 신규 + 2025.2Q~2026.1Q**: 상각 0/None→실값(-791.3/-1531.21/-2058.31/-537.11),
  조정 residual 재산출, 기초/신계약 정밀도 정정. root cause = 2025.2Q+ 상각 토큰 0 인식 + '기타' 테이블 CSM 누락
  (owner: 기타 테이블 식별비용 크면 패스 가능).
- **회사 제외 3사**: 하나손해(KR0050)·하나생명(KR0097)·신한이지(KR0051) — owner 확인 결과 CSM waterfall 분리공시
  불가(보험손익만 분해 가능). CSM_waterfall + NB_CSM_multiple에서 제거(왜곡 방지). **continuity 룰이 이 3사를
  더 이상 보지 않도록 확인** 바람. (CSM_amortization의 하나생명 상각스케줄은 직접공시라 유지.)
  **[보정 2026-06-11]**: 하나손해·하나생명은 **복원**(owner 재지시 — 자사 감사보고서 별도 변동표 실재, 경영서술
  수치와 정확 일치 검증: 하나손해 기말 2,802/신계약 1,506/상각 −219, 하나생명 4,390/3,240/−399). **제외는
  신한EZ(KR0051) 1사만 유지** — 변동표 천원 단위를 백만원 오인한 ×1000 추출오류(진짜 기말 CSM 1.69억) + PAA
  중심사로 워터폴 무의미. continuity 룰 제외대상 = KR0051만.

### 2. 신규 검증룰 요청 — AMORT_ZERO (owner 발주)

**"CSM 상각액(item5) = 0 은 불가능"** — CSM 보유사가 상각 0이면 추출오류다 (미래에셋 2025.2Q+가 실제 사례:
0으로 인식돼 owner가 수동 발견). 제안: item5 값이 0 또는 None인데 동일 분기 item1/6(기초/기말)이 양수면 **RED**
(단위오류로 분기 전체 null된 케이스는 제외 — 현재 유일 잔존 = AIG 2025.4Q nulled). 0값 맹점 보완 룰.

### 3. 알려진 경계 drift 2건 (documented, 수정 아님)

미래에셋 당분기 항등식 미세 불일치: 2023.2Q(Δ≈2.25억 — owner 신규입력 2023.1Q와 추출 2023.2Q YTD의 기초
재진술성 차이), 2025.2Q(Δ≈6.5억 — 동일 패턴). 원천 수준 drift로 **숨기지 않고 노출**하는 설계
(build_root_masters docstring 참조). continuity 룰이 RED 처리하지 않게 tol/예외 검토 바람.

### 4. 재검증 요청
CSM continuity + 마스터 정합 풀런. 추가로 owner가 지적한 검증 사각(FY내 기초 일관성·0값 맹점·하한 plausibility)
관점에서 룰 보강 검토 — 롯데 2023.2Q 기초 drift는 WITHIN_FY_OPENING_DRIFT가 잡았으나 verdict가 잘못 닫혔고,
미래에셋 상각 0은 룰 부재로 통과했음.

## 답변 (validation 작성 — 처리 후, 2026-06-12)

**재검증 풀런 완료 (build 선행 → override 반영 상태). 4개 항목 전부 확인, 종결.**

1. **롯데(KR0003) verdict 폐기 — 확인.** override 적용 후 롯데 FY2023 WFY 무플래그(기초 16,774.38로 3Q/4Q와 일치). 구공시 오채택이 맞고 재진술 아님. 기존 `...KR0003_FY2023__continuity`(justified_restatement) verdict 폐기 처리. WITHIN_FY 룰도 깨끗.

2. **회사 제외 = 신한이지(KR0051) 1사만 — 확인.** CSM_waterfall.json 실측: 하나손해 **12행**·하나생명 **6행 복원**, 신한이지 **0행 제외**. continuity/WFY/ZLEG 룰 모두 신한이지 미참조 확인. 하나손해(기말 2,802/신계약 1,506/상각 −219)·하나생명(4,390/3,240/−399) 정상 적재.

3. **AMORT_ZERO 요청 = ZAMORT로 충족 — 확인 + 스펙 정밀화.** ZAMORT 룰 라이브(상각 320 company-quarter present). 미래에셋 2025.2Q+ override 반영으로 현재 **zamort 0건**. 스펙대로 **"상각==0 AND 기초CSM/기말CSM 양수"** 가드 추가(미보유 기초=기말=0 정상사 오플래그 방지). None+양수 케이스는 coverage/ZLEG 담당 — 역할분담 이대로 OK인지만 확인 바람.

4. **미래에셋 경계 drift 2건 — RED 아님 확인.** 2023.2Q/2025.2Q 모두 WFY/closing/zamort 어디에도 RED 없음. source-level drift 노출 설계 존중, tol 내 흡수. 별도 예외등록 불필요.

**※ 신규 발견 (이 회신과 무관, 별건 큐)**: **코리안리재보험 WFY 2건** — FY2023(2023.4Q 기초 10,715.2→10,640.9) / FY2024(2024.4Q 10,640.9→8,031.5). 4Q에서만 기초 하락 = within-FY 기초 불일치. 재진술인지 추출오류인지 확인 필요. (코리안리는 시장위험 세부·NB도 다분기 누락 — `20260611T2200Z__...market_subrisk` 참조.)

현 마스터 게이트: closing 0F / zamort 0 / wfy 2(코리안리만) / zero_legs 6(현대 5+동양 1, 별도 inbox 큐) / crosscheck 0F. **이 스레드 종결(resolved).**
