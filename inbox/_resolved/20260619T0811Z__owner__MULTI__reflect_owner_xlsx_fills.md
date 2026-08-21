---
from: owner
to: parser
created: 20260619T0811Z
status: resolved
route: backlog
company: MULTI
period: 2023.4Q~2026.1Q
lane: kics+ifrs17
iter: 1
---

## 미결 (owner) — owner xlsx 수기 fill을 master diag/JSON에 반영 (review-loop, 소실 방지)

owner가 `insurequant_master_tables.xlsx`에 직접 채운/확인했음. **xlsx에만 있어 다음 `build_root_masters` 빌드에서 소실 위험** → diag/소스에 반영 필수. **값=xlsx, 셀별 검토의견=`data/_derived/problem_cells.csv`의 "검토 의견" 열.**

### A. 반영할 fill (xlsx → diag/JSON)
**KICS 레인:**
- AIA 2025.1Q item2 = **32114** (+ owner: "expected 숫자도 틀렸다" → 같은 식의 다른 항목(item1/item3)도 재확인).
- AIA 2025.4Q 19_market: 주식위험액·외환위험액 수정값.
- 카카오 2023.4Q·2024.4Q: **분기 통째 입력**(MISSING_FILER 해소).
- 카카오 2025.3Q: item21=0, item16 추가.
- 한화생명 2025.2Q 19_market: 주식위험액 수정.

**IFRS17 레인:**
- AIG손해 2025.4Q CSM워터폴 6항목 입력.
- 하나손해 2024.4Q 이자 부리 입력.
- 현대해상 PL 2023.4Q·2024.4Q·2025.1Q·2025.2Q 생명장기 leg — **단 owner: "추정치 많음, 연속성 재검증 필요, 변동성 크면 홈페이지 '추정치' 음영처리"** → 반영하되 estimate 플래그 + designer 음영 바운스.

### B. "0 맞다" 확인분 → 빈칸이 아니라 0으로 박기 (problem에서 제외)
- KB손해 2025.4Q: 자본증권(item2)·자본조정(item4) = 0.
- 미래에셋 2025.4Q: 자본증권·비지배지분·불인정항목 = 0.
- 삼성생명 2023.4Q: 비지배지분 = 0.

### C. owner가 못 푼 것 → raw 재검토
- 동양생명 재보험 leg(재보험 CSM상각·위험조정·기타재보험손익, 2023.4Q~2025.3Q): owner "DART 공시 자체 정합성 의심·연속성 검토 필요". → DART raw 재대조(진짜 소스 결손 vs 추출 갭 판정).

### 주의
- review-loop: diag→root 방향이라 xlsx만 고치면 소실 — 반드시 상류 반영(메모리 `project_master_xlsx_review_loop`). estimate 셀은 provenance/flag로 구분. python 풀패스. `build_csm_waterfall_master.py` 금지.

## 후속 (owner, 2026-06-19) — xlsx fill 확대 + owner가 MOLE도 직접 수정
xlsx fill **총 135셀**(PL 121·CSM 10·K-ICS 4)로 확대, `scripts/sync_owner_fills_to_json.py`로 루트 JSON 동기화됨(7분기 한정·|diff|>2 필터·.bak). **diag 반영 시 이 135셀 전부 반영**(xlsx 재독). 게이트 **RED 34→13**(잔여=tier2 OCR 1529Z·AIA/한화 19market 이미지).

**owner가 직접 정정한 MOLE(0412Z) — 재조사 말고 반영만:**
- 교보생명(KR0073) 원수예실차 0→실값(128048/50690/193163/18254), 기타원수손익 상응조정.
- BNP카디프(KR0075) 2025.4Q 단위오류 정정: 원수CSM상각 6379544→6379.544·위험조정 1768401→1110.537·예실차 −581440→−3826.768.
- 코리안리(KR1000) 2026.1Q 재보험 중복43→실값(−11817 등).
→ 0412Z의 이 항목들 = **owner-resolved**. 남은 MOLE(삼성화재 자동차손익·신한이지 보험금융손익 등)만 parser.

**주의(당분기)**: 연말만 채운 셀은 직전분기 누계 부재로 당분기 None 유지 — `_flow_dangi` 재계산도 동일 한계(분기 누계 없으면 delta 불가). 분기 시리즈 확보돼야 채워짐.

## 후속2 (owner, 2026-06-20) — 카카오 통째결손 2분기 JSON 직접삽입 + 룰7/8 tolerance
- **카카오페이손해(KR1098) 2023.4Q·2024.4Q**: owner가 xlsx에 1~46항목 풀로 채웠으나 `sync_owner_fills`는 기존行만 갱신→**신규 filer-quarter 못 만듦**. `scripts/insert_kakao_missing_quarters.py`로 **89행(2023.4Q 45 + 2024.4Q 44, None인 item10·26만 제외) kics_disclosure.json 직접삽입**(.pre_kakao.bak). **빌드 때 소실되니 parser가 diag/source에 영구 삽입 필수** (이 2분기는 git raw 없음 — xlsx가 SOT).
- 삽입 후 **2023.4Q에서 KICS_7·8 RED** 발생 = 기본요구자본 20억 초소형 분모의 정수반올림 아티팩트(공시 item27/28=4777.18은 정확, 재계산 974/20×100=4870). → **`src/solvency/validation/kics_json_rules.py` 룰7·8에 동적 tolerance 추가**(8_life 선례 동형: `max(eff_tol, exp×0.5/|item14| + 50/|item14|)`). 감사결과 **OLD-fail→NEW-pass 셀은 카카오 2023.4Q 2건뿐, 타사 0건**(진짜오류 마스킹 없음). validation FYI.
- 결과: 게이트 **RED 13→11**(잔여=범위밖 5·손수정 카카오2025.3Q item16=59/AIA2025.1Q 819·tier2 OCR 3·신한이지 scale 1).

## 답변 (parser-kics 2026-06-20 — KICS 몫 review-loop 영속화 + stale-gold 클로버 차단)

**핵심: owner가 sync/insert로 루트 JSON에만 넣은 image-OCR fill이 durable gold에 없어 rebuild 소실 직전이었고,
기존 gold엔 owner 수정을 되돌릴 stale 셀이 1건 있었다. 둘 다 fix — live JSON은 일절 안 건드림.**

### A. KICS fill을 durable gold(`data/_gold/user_kics_cells.json`)에 영속화 (+90셀)
review-loop 정본 경로 = gold(rebuild 체인 `fill_period→fill_market→apply_user_kics_gold→recalc`가 재적용).
`build_user_kics_gold`는 **xlsx≠JSON diff만** 캡처 → owner가 sync 후엔 diff 소실 → AIA·카카오가 gold 누락
(provenance 직접 확인: md_inbox에 MD 있으나 **카카오=이미지사**라 파서 재현 불가, AIA도 apply docstring상 OCR사).
`scripts/append_owner_image_fills_to_gold.py`(additive, 기존 gold 불변)로 캡처:
- **카카오 KR1098 2023.4Q(43)+2024.4Q(42)** = HEAD-absent 순수 owner 추가(이미지·xlsx SOT) → apply가 행까지 재생성.
- 카카오 2025.3Q owner 편집 = it12(불인정항목 1241→0)·it16(분산효과 59 신규).
- **AIA KR0080** owner 수정 = 2025.1Q it4(순자산 32144→32114)·it8(자본조정 819→0)·2025.4Q it37(주식위험액 →4371.32).
  (owner note의 "item2/item21"은 항목번호 오기 — 실제 변경셀은 it4/it12, 데이터 기준 캡처.)

### B. 🔴 stale-gold 클로버 차단 (네 "숫자 덮어쓰지 마" caveat의 실제 위험)
기존 gold에 **한화생명 KR0068 2025.2Q it37 주식위험액 = 45096.51 (옛값)** 잔존 — owner가 0811Z에서 수정한
값(xlsx/JSON = **58590.96**)과 13,494 차이. rebuild 체인이 돌면 **owner 수정을 옛값으로 덮어쓸** 상태였음.
`scripts/reconcile_gold_to_xlsx.py`로 gold를 owner xlsx(SOT)에 정합화 → 58590.96. (예별 KR0004 2024.2Q it3은
gold=xlsx=3081.95로 이미 정상, current JSON 3082.02가 0.07 drift = gold가 rebuild서 owner값 복원.)

### 검증 (전부 copy/메모리, live JSON 무변경)
- **no-clobber**: gold→current 적용 시 실질 변경 0(잔여는 32114 vs 32114.0 int/float 표기차 3건뿐).
- **rebuild-survival**: 카카오 2분기 삭제+AIA를 HEAD로 되돌린 뒤 apply → **85행 재생성·AIA 복원 확인**.
- **게이트 무회귀**: `validate_kics_disclosure.py` RED=1(8_life KR0079 미래에셋 2023.2Q)+census-missing 4 =
  **전부 TODO.md 기등록 documented exception**(이미지/scan-only, OCR 불가, 비차단). 내 작업 영향 0.

### 처분 / 라우팅
- **KICS-A·B = ✅ DONE.** (카카오·AIA·한화생명 19market·"0 맞다"분은 owner sync로 JSON 반영됨 + 이제 gold 영속.)
- ⚠️ **systemic 후속(parser)**: 내 life-subrisk backfill(+155셀)·시장하위 backfill은 rebuild 체인 밖 스크립트라
  gold/체인에 미편입 — 현재 커밋엔 있으나 from-scratch rebuild 시 미재현. backfill 스크립트를 체인에 편입 or
  gold 캡처 = 별 슬라이스(아래 TODO).
- **IFRS17 몫(AIG손해 CSM 6항목·하나손 이자·현대 PL 생명장기 leg estimate+음영·동양 재보 raw 재대조)** = ifrs17
  세션(2-lane hard split). 이 답변은 KICS측 종결.

status: **KICS 몫 종결** (gold 영속 +90셀, stale-gold 클로버 1건 차단, 게이트 무회귀). ifrs17 몫 open(별 세션).

✅ DONE 2026-06-20 (ifrs17 분담). owner root fill을 durable override로 캡처(빌드 소실 방지): PL 121셀 → 신규 **data/dart/viz/pl_manual_overrides.json** + build_root_masters._apply_pl_overrides (_zero_other_expense 後 적용=owner값 최종). CSM 10셀(AIG손해 KR0029 2025.4Q 6항목·하나손해 KR0050 이자부리/조정 4) → csm_manual_overrides.json 추가. 재빌드 시 owner root 값 정확 재현(**값 변경 0건 검증**, 값_당분기만 정밀도 재계산), 무클로버. 현대해상 26셀은 estimate 플래그(provenance/designer 음영). NB: kics 분담(AIA·카카오·한화 19market·카카오 89행 직접삽입)은 kics 레인 소관.
