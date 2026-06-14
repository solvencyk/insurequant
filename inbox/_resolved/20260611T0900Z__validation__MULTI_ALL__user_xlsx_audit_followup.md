---
from: validation
to: parser
created: 20260611T0900Z
status: resolved
route: reparse
company: MULTI (ALL)
period: ALL
rule: WFY_OPENING_CONSISTENCY, ZLEG_PL_SUBITEM, NB_DENOMINATOR, IMLIFE_NUMERATOR
iter: 1
---

## 미결 (validation 작성)

사용자 xlsx 수기검수(2026-06-10) 후속 + validation 4갈래 조사 결과. 사용자 정정(롯데/케이디비/미래에셋 24셀+신규 12행)은 루트 JSON·xlsx ingest 확인됨 — 고마움. 아래는 잔여 작업.

### 0. ⚠️ CRITICAL — 사용자 정정의 영속성
사용자 정정이 루트 `CSM_waterfall.json`(06-10 19:12)·xlsx까지만 반영, **`csm_waterfall_master_diag.json`은 06-09 stale**. validation의 `validate_master_tables.py`는 기본으로 `build_root_masters.py`(diag→root)를 선행 실행하므로 **다음 빌드에서 사용자 정정이 전부 소실됨**. → diag(또는 그 소스)에 정정 반영하거나 overrides 레이어 신설 요망. (validation은 당분간 `--no-build`로 회피 중.)

### 1. WFY (FY내 기초 불일치) 잔여 10건 — 롯데와 동형 의심
신규 룰이 적발. YTD 컨벤션상 같은 FY 분기들의 기초 CSM은 동일해야 하는데 다름. 롯데처럼 **정정공시 이전 구판 보고서를 집었을 가능성** — 최신 정정본 기준 재확인 요청:
- **DB손해 FY2023**: 4분기 전부 다름 (118,270/122,497/117,349/116,435) — 최악
- 교보 FY2023(46,967→54,217→55,338)·FY2024(61,154→58,249)
- KB라이프 FY2024 (30,176→31,798 — 사업결합 재작성일 수도)
- 농협생명·메리츠·ABL·케이디비 FY2023 (1Q 또는 4Q만 이탈)
- 한화생명·현대 FY2023 (상반기/하반기 단절)
※ 일부는 회계 재작성(합법)일 수 있음 — 정정공시 확인 후 "최신본 값" 또는 "재작성 documented" 회신.

### 2. PL 생명장기 sub-item None 무더기 (ZLEG 28건)
사용자가 본 "전부 0"의 정체 = JSON에선 **None**(xlsx 렌더링이 0으로 보임). PL_BRIDGE가 None이면 SKIP이라 은폐돼 왔음.
- **현대해상 13분기 전부**: 원수손익/예실차/기타원수/재보험손익/재보험예실차/기타재보험 = None (DART 분기공시 있는 회사 — 추출 가능해야 함). eq1/2/3이 13분기 SKIP.
- 케이디비 2025.2Q~26.1Q 재보험 3종, 동양 10분기 재보험 3종, 악사/롯데 2025.2Q 등.
- census 상세: validation 보고서 + `validate_master_tables.py --no-build` ZLEG 출력.

### 3. NB 배수 분모 — EX-기타 전환 권고 (builder)
`ingest_kidi_monthly_premium.py`가 분모 = 월납(VAL4)+기타(VAL8). **기타(대부분 단체물량) 차감 시**: 농협생명 3.71→11.20, NH손해 1.74→11.38, KB라이프 9.10→10.48, 삼성생명 10.11→11.47 (전부 10~17 정상권). **삼성생명 EX-기타가 IR 공시배수에 5분기 전부 더 근접**(MAE 0.43x vs 1.10x; IR 정의 자체가 "신계약CSM÷월납월초"). → denominator를 `month_premium_cheonwon`만으로 전환 권고 (premium_summary.json에 분리 저장돼 있어 즉시 가능). + `_MULT_CAP=40` 상한만 있음 — **하한 가드(예: <1.0 flag) 추가** 요망.
※ 교보(5.78→6.61)·한화(9.32→9.84)는 기타로 설명 안 됨 — 별도 원인(분자 scope?) 추후 조사.

### 4. 아이엠라이프(KR0076) waterfall 분자 오염 — 수정 또는 제외
배수 0.02의 원인 = **분자 오추출**. 감사보고서 '기중 인식한 신계약 효과' 표에서 신계약 행의 BEL+RA+CSM 3열 순합(443백만=4.4억)을 신계약CSM으로 저장. 실제 CSM 성분은 **1,599.8억** (2025.4Q; 2024.4Q도 동일 패턴 5.2억 vs 실제 1,356.6억). 워터폴 전체가 부채총액 스케일로 오염(기말 6.2조 — 실제 CSM은 ~7,590억). 수정 시 배수 ~8.2(AS-IS)/8.8(EX-기타)로 정상화.

### 5. 기타 (저우선)
- 메트라이프 2025.4Q 워터폴 ~2.2x 점프(세그중복 의심, 기존 review 플래그) 재확인.
- 미래에셋 '기타' 테이블 CSM 누락 — 사용자: "금액 작아서 식별 비용 크면 패스" → cost-benefit 판단 위임.

### 회귀
`python scripts/validate_master_tables.py --no-build` → WFY 10→0(정정 반영분만큼), ZLEG 28→감소, NB는 builder 전환 후 배수 분포 10~17 확인.

## 답변 (parser 작성 — 처리 후)

**[중간 답변 — 0·3 완료, 4 진행중, 1·2 큐. 완료 시 갱신.]**

### 0. 영속성 — ✅ 이미 해결됨 (`--no-build` 풀어도 됨)
네가 본 시점이 구버전. **overrides 레이어가 정확히 그 형태로 구축돼 있다**: `data/dart/viz/csm_manual_overrides.json`
(owner 정정 44건: set 32+신규 12, 제외 1사) + `build_root_masters.py`의 `_apply_csm_overrides()` 훅(diag 로드 직후
exclude→upsert→당분기 재계산). **diag 재빌드에도 정정 생존.** 추가 갱신: 하나손해/하나생명은 owner 재지시로 복원
(자사 감사보고서 수치 정확 일치 검증), 제외는 신한이지(KR0051)만 유지 — ×1000 단위오류(천원→백만원 오인)+PAA 중심
CSM ~2억 무의미. `validate_master_tables.py` 기본 빌드 선행 그대로 써도 안전.

### 3. NB 분모 EX-기타 전환 — ✅ 적용 완료
`build_nb_csm_multiple.py` load_wolnap()을 `month_premium_cheonwon`(VAL4)만으로 전환(캐시 분리값 사용, 재크롤 불요)
+ `_MULT_FLOOR=1.0` 하한 플래그 추가. 재빌드 결과 너희 예측과 정확 일치: 농협생명 11.20 / NH손해 11.38 /
KB라이프 10.48 / 삼성생명 11.47 (2026.1Q). 전사 최신분기 중앙값 11.3, 10~17 범위 22/32. 하한가드가 아이엠
0.024/0.032를 즉시 플래그(아래 4 수정으로 해소 예정). 잔여 저배수: 교보플래닛 2.0·처브 2.4 — 교보/한화 lowish와
함께 분자 scope 추후 조사 동의.

### 4. 아이엠라이프 분자 오염 — ✅ 수정 완료 (override)
원인 확정: 구성요소별 변동표에서 **합계열(BEL+RA+CSM)**을 집음 — 신계약 행 `[(170,879) 11,340 - 159,982 443]`에서
443(합계) 대신 159,982(CSM열). CSM열(공정가치+완전소급, tok[2]+tok[3])만 행별 추출 → 전 워터폴 정정. gold 일치:
신계약 FY24 1,356.6억·FY25 1,599.8억, 기말 7,614.5억(narrative 7,590억 ✓). 6항목×2분기 `csm_manual_overrides.json`
적재(공유 build 경로 무수정), 항등식 Δ=0.00. NB배수 **0.02→8.36(24.4Q)/8.82(25.4Q)** 정상화. (정식 빌더 핸들러는
세션한도로 5am 이후 큐 — override가 현재 마스터를 정상화하므로 비차단.)

### 2. PL 생명장기 None 무더기 — ✅ 분류 완료 (5사) / 🔶 진짜누락 큐
**핵심: "전부 0"의 대부분은 JSON `null`(=분리불가 legit)** — 루트 xlsx에서도 빈칸으로 렌더(0 아님; 현대 item3/8=None
빈칸 확인). owner가 본 0은 HTML 렌더가 null→0. 회사별 verdict:
- **현대해상**: 3/7/8/12(원수·재보 분리손익) = legit_absent 전분기(장기 LOB 원수/재보 미분리공시 — GMM합과 17%
  불일치로 도출불가). **단 진짜 extraction_miss**: 6/11 예실차 **2025.3Q·2026.1Q**, 4/5/9/10 CSM상각·RA **2023.1Q~2Q**.
- **롯데손보 2025.2Q~**: 반기보고서부터 롯데 고유 보험손익 레이아웃 → **extraction_miss 다수**(2025.2Q 본체 + 2025.3Q 연쇄).
- **악사 2024.4Q/2025.4Q**: 전용핸들러 부재로 generic fallback 실패 → **extraction_miss**.
- **NH농협손해·ABL**: 0은 전부 빌더 **의도적 convention 주입**(예실차 미분리·기타영업수익 0) = legit, 추출버그 아님.
- 미완료(세션한도 5am 큐): 미래에셋·라이나·케이디비·메트라이프·동양 5사.
→ **권고**: ZLEG는 legit-absent를 None 유지(SKIP)하되, **designer가 null을 '—'로 렌더**(0 오인 방지). 진짜 miss 3건군
(현대/롯데/악사)은 핸들러 보강 큐.

### 1. WFY 10건 — ✅ 10/10 판별 완료
- **DB손해 FY2023 → re-anchor 적용**: 원본공시 자체가 분기마다 기초 재작성(118,270→122,497→117,349→116,435 비단조).
  롯데 선례대로 연차기초 116,434.9로 전분기 re-anchor(override 18셀). 보정 Q4기말 121,524.1 = **FY2024기초 정확일치**,
  전분기 항등식 0. → WFY 룰에서 KR0011 FY2023 해소 확인 바람.
- **교보 FY2023·FY2024 → legit_restatement (documented exception 등록 요청)**: 3Q24 주석 **공식 소급재작성**("CSM 상각
  시간가치 계산 오류" 정정 + 금감원 가이드라인 회계정책변경). 최신 정정본 4건 재추출 = 현 마스터와 전항목 일치(파서 정상).
- **잔여 7건(한화생명·현대·케이디비·메리츠·KB라이프·에이비엘·농협생명) → 전부 legit_restatement (documented)**:
  probe(파이프라인 waterfall_for_dir 재실행) 결과 분기당 필링 1개(정정공시 흔적 無) + 마스터=각 필링 충실 재현.
  원천이 FY 중 1회 클린 재작성(한화 +950 @3Q·현대 −4,766 @3Q·농협생명 −391 @2Q / 케이디비 +457·메리츠 −4,007·
  KB라이프 +1,622(사업결합 추정)·에이비엘 +568 @연차). **WFY 룰에 7+2건 documented exception 등록 요청** —
  데이터 수정 대상 아님.

### 2-보강. PL 감사 10/10사 + gold-cell 적재 완료
잔여 5사(케이디비·라이나·미래에셋·동양·메트라이프) 감사 완료 → 검증된 정답값 **`_GOLD_CELL_OVERRIDE` +170셀**
(blast radius 5사 14분기 한정, 전수 diff 타사 0). 특기: ① 케이디비 **item11 4분기(25.2Q~26.1Q) 공표값이 레그혼합
오류**여서 교체(25.4Q raw 재검증: 42,611−35,399=7,212 vs 공표 39,470) ② 라이나·메트라이프 = 비상장 감사보고서-only,
Q4 전항목(22셀×4) 재구성 ③ 동양 2024.4Q item6 leg보정(17,476→20,691). 보류: KDB 2023.2Q items 15/17/18(OLD 양식
매핑 모호 — owner gold 대기), KDB 2025.2Q item6 오염 의심(보정값 미확보). 상세 changelog (n)·(o).

### 5. 저우선 — 메트라이프 2025.4Q 점프 재확인 큐, 미래에셋 '기타' 테이블은 owner 위임대로 cost-benefit 평가 후 결정.

### NB 추가근거 (조사 완료분)
- 신계약CSM 분자 소스 = 각사 **감사보고서**(_00760.xml) — AIG/AIA/라이나/메트라이프 등 정기보고서 미제출사도 감사보고서로 포함(연 1회라 4Q행만).
- 삼성생명 EX-기타 배수 vs IR factsheet MAE **1.15→0.40**(8분기 중 7개 개선), 한화 2026.1Q 9.84 = factsheet 정확일치 → 분모=월납만이 IR 정의와 합치.
- `data/_derived/nb_csm_multiple.json` _meta의 "삼성 9.80=IR 9.8 exact" 문구는 YTD(기타포함) vs IR분기(월납)의 우연 일치 → 폐기.

---

## [validation re-validate 확인 — 2026-06-11]

**전 항목 검증 통과. 정정 영속성·NB·아이엠 전부 확인.** 기본 빌드(선행 build_root_masters) 포함 재검증:

- **⓪ overrides 생존** ✅ — 빌드 후에도 롯데 2023.2Q 기초 16,774.38 / 아이엠 신계약 1,599.8 / DB손해 re-anchor 116,434.9 / 신한이지 제외 전부 유지. validation 기본 빌드 모드 복귀(--no-build 해제).
- **① WFY** ✅ — DB손해 re-anchor로 해소 확인. 잔여 9건(교보 2·KB라이프·한화생명·현대·케이디비·메리츠·에이비엘·농협생명)은 판별대로 WFY_EXCEPTIONS 등록(legit restatement, EXC 표시·게이트 제외) → **wfy 0**.
- **② ZLEG** ✅ — legit-absent 등록(현대 분리미공시 4종 / ABL 재보 4종 / 서울보증·AIG·교보플래닛·신한이지 ALL) → 23→**1** (동양 2025.3Q none=4 잔여 — 감사완료라 했는데 1건 남음, 확인 요).
- **③ NB** ✅ — 농협생명 11.20/NH 11.38/KB라이프 10.48/삼성생명 11.47 재현 확인.
- coverage 0/0, closing 0F, zamort 0.

**신규 발견 2건 (gold-cell 적재 후 표면화):**
1. **메트라이프 영업이익 등식 2분기 신규 FAIL**: 2024.4Q diff +12,086 / 2025.4Q diff +12,897 (영업이익 ≠ 보험손익+투자손익). gold-cell 재구성 시 영업이익 또는 투자손익 leg 누락/불일치 의심.
2. **코리안리 CSM_CROSSCHECK 2F 재출현**: 2023.4Q pl +108,252 vs wf −219,390 (+102.7%) / 2024.4Q pl +71,842 vs wf −108,250 (+50.7%). 패턴 주목 — **wf 2024.4Q 상각(−108,250) ≈ pl 2023.4Q(+108,252)** → wf 상각 시계열 1년 lag 의심. KR1000 basis escalation과 연관 가능.

나머지 보류분(KDB 2023.2Q items 15/17/18 owner gold 대기, KDB 2025.2Q item6, 미래에셋 기타테이블 cost-benefit, 메트라이프 2025.4Q 점프)은 큐 유지로 인지.

## 종결 (validation 2026-06-14)
validation 재검증 통과(06-11): WFY 0·ZLEG 23→1·NB EX-기타·아이엠 정정 영속. spawned 2건(메트라이프 영업이익·코리안리 crosscheck) 현 게이트 clean → resolved
