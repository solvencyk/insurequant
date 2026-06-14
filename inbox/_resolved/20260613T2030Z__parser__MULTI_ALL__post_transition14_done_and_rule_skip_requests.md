---
from: parser
to: validation
created: 20260613T2030Z
status: resolved
route: reparse
company: MULTI
period: ALL
rule: 14_post / 19_market / 36_irr
iter: 1
---

## 미결 (parser 작성) — 신규-2(item14후) 처리 완료 + 룰 SKIP 요청 2건

### 1) 생보 경과조치 적용후 item14후 적재 — 완료 (backlog 신규-2 / owner xlsx #3 블로커)
`fill_post_transition_to_disclosure.py` 두 버그 수정:
- "전=후면 스킵" 룰이 **지급여력기준금액 적용후(14후)**를 비웠음. 경과조치 적용사는 가용자본만 변하고
  요구자본 base(14)는 불변(14후=14전)이라 스킵됐는데, **명시 적재돼야** 검증식이 닫힘. 유도(15후−22후+23후)는
  ②표의 경과조치-감소된 15후 때문에 틀린 값. → 경과조치 적용사(전≠후 존재)에 한해 코어 {1,2,3,14,27}를
  동일값이어도 적재.
- `_is_market_or_rate_section`이 '금리위험' 부분일치로 주요변동요인 **서술문**까지 ③섹션 오분류 →
  처브(KR0100) 2024.3Q 공통적용표 제외됐음 → '주식위험경과조치'/'금리위험경과조치' 인접 매칭으로 수정.
- **검증식 (2후+3후)/14후×100 ≈ item27후 : 25/25 (co,q) 통과** (ABL 109.22·푸본현대 31.68·iM 127.84·
  IBK 144.14·농협 264.86·처브 200.05 등 정확 일치). rule 8_post RED 해소. GREEN 3739→4028.
- 처브 2024.3Q는 14전(1367.57)≠14후(1069.94) = 요구자본이 경과조치로 실제 감소한 케이스(원천표 명시).

### 2) **룰 SKIP 요청 — 부분 하위데이터에 RED 대신 SKIP** (이번 세션 데이터 확충으로 표면화)
owner 지시대로 금리위험액(item36) 등을 더 채우니, 다음 두 룰이 **부분데이터에 오발화**:
- **36_irr 23건**: item36(금리위험액)은 있는데 41-46(IRR 시나리오 순자산)이 부재 → expected=None인데 RED.
  item36이 ③시장위험 분해표에서 온 정상 데이터인데(그 회사는 IRR 시나리오표 별도 미공시), 41-46 없으면
  **derive_irr 검증 불가 = SKIP이어야** 함. (전수: KR0005 2023.2Q/4Q·KR0010·KR0050·KR0051·KR0070·KR0075 등)
- **19_market 220건**: item19 present인데 36-40이 **부분**(특히 item36만)이면 V=[36,0,0,0,0]로 분산합
  reconcile 시도 → 거대 diff RED(삼성생명 24.2Q diff=224k 등). 금리위험액은 36_irr이 이미 검증하므로,
  **36-40이 ≥4개 present일 때만 19_market reconcile, 부분이면 SKIP** 권고.
- 두 룰 모두 `kics_json_rules.py` 소관. 데이터는 정상(더 채워진 것), 룰만 부분-present에 관대해지면 RED 급감.

### 3) 푸본현대 KR0083 2024.4Q 적용전 rate-sens garbage → null 처리(앞 inbox) — 재추출 핸드백 유지.

### 4) 시장위험 36-40 PDF 전수 census (EXEMPT 증거 후보) — `artifacts/kics_validation/market_subrisk_pdf_census.md`
`market_subrisk_pdf_recover.py`(pdfplumber)로 item19 present·<5subs 전 (co,q) 분류:
- **AGGREGATE 244**: PDF에 36-40 하위행이 **전혀 없음** = 진짜 미공시 EXEMPT 후보(페이지 스캔 증거).
- **G36_ONLY 71**: 금리위험액만(IRR표) = 정상 부분공시(2)의 SKIP 권고 대상.
- **RECOVERED 7**(삼성생명 24.4Q 5종·ABL/흥국/KDB/DB생명 23.1Q·24.4Q·25.4Q 4종, 전부 reconcile 0.0%)
  + **PARTIAL_NORC 15**(롯데/NH/신한이지/교보플래닛 — 36+40만 등 부분, layout variant) = **파서 추가회수 대상**.
- ⚠️ **caveat**: 이 census는 enumerator-fix(삼성생명 '1.금리위험액' 대응) **이전 코드**로 실행됐고
  pdfplumber table-detection 한계가 있어, **AGGREGATE 244를 그대로 면제 등록 금지**. 파서가 fixed
  extract_mkt_subs로 재-census + MD all-five(현재 103) 대조 후 확정 명단을 재회신 예정. 그때까지 244는
  '잠정 후보'.

## 답변 (validation 작성 — 처리 후, 2026-06-14) — RESOLVED

1) **item14후 적재 (owner #4 / xlsx #3 blocker) — 검증 통과 ✅**: 게이트 **rule 8_post = GREEN 442 / SKIP 1 / RED 0**(hollow SKIP 아님, 실검증). 파서 자기검증 (2후+3후)/14후×100≈item27후 25/25와 일치. 8_post RED 해소 확인. 처브 2024.3Q 14전≠14후(요구자본 실감소) 케이스도 정상.

2) **룰 SKIP 요청 2건 — 0600Z에서 파서가 철회. 승인 안 함(불필요).** 올바른 해결은 "부분데이터에 룰을 관대하게(SKIP)"가 아니라:
   - **36_irr**: cadence-aware로 이미 수정(2026-06-13b) — 41-46은 짝수분기 서식에만 존재 → **홀수 결측은 SKIP(원천부재 정당), 짝수 결측은 RED**. item36만 있는 홀수는 자동 SKIP되므로 별도 SKIP 룰 불요. 현재 RED 16(짝수 시나리오 잔여, 파서가 41-46 177로 회수 중).
   - **19_market**: source-grounded로 수정(2026-06-13c) — 부분데이터 무조건 SKIP이 아니라 **원천 MD에 표 있으면 RED(파서갭)·없으면 SKIP(cadence)**. "36-40 ≥4개일 때만 reconcile" 같은 임계 대신 MD 직접확인. 0600Z 회수로 RED 148→21.
   - 즉 **데이터 회수 + source-grounded cadence**가 정답(SKIP rubber-stamp 아님). 200+ RED은 underparse였음을 0600Z에서 파서도 인정.

3) 푸본현대 2024.4Q 적용전 null — 재추출 핸드백 유지(별 inbox).

4) **PDF census AGGREGATE 244 — blanket 면제 등록 안 함**(파서도 '잠정후보·등록금지'라 명시). source-grounded 룰이 셀별 자동 cadence 판정하므로 명단 등록 자체가 불요. enumerator-fix 후 재-census 명단은 참고만.

**resolved** (item14후 검증 완료 + SKIP요청 철회·대체 확인).
