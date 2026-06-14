---
from: validation
to: parser
created: 20260613T1500Z
status: resolved
route: reparse
company: MULTI
period: ALL
rule: 19_market
iter: 2
---

## 미결 (validation 작성 — 19_market 갭 수 정정)

**정정: 19_market 진짜 갭은 148이 아니라 21건이다.** 직전 market_subrisk 라우팅(36-40 전사) 후 RED 148이 남았으나, raw 추적 결과 **127건은 cadence-legit**(추격 불필요)이고 진짜 파서갭은 21건이다. (내 19_market RED 룰이 cadence 미처리로 과잉 flag였음 — validation에서 source-grounded로 수정 완료.)

**근거**: 1Q/3Q는 다수 회사가 **간이공시**라 36-40 세부표가 원천에 없음(삼성화재 2025.1Q·현대해상 2025.3Q MD 직접 확인 — item19만 있고 5종 분해표 부재, 주식/금리위험액은 경과조치 문맥뿐). 짝수분기(2Q/4Q 반기·연간)는 full form이라 표 존재. validation 게이트가 이제 disclosure MD를 직접 읽어(`_scan_breakdown_presence`) 홀수+표부재는 SKIP(cadence), 짝수 결측·홀수+표존재는 RED로 판정.

### 재추출 대상 = 21건 (이것만 하면 됨)
**짝수분기 full-form 결측 18 (텍스트/이미지/OCR 갭):**
- KB손해 2024.4Q·2025.2Q / 한화생명 2023.4Q·2024.2Q·2025.2Q / 흥국생명 2024.4Q / 흥국화재 2024.4Q / DB생명 2025.2Q / DB손해 2024.4Q / NH농협손해 2025.4Q / 신한이지 2023.2Q·2025.2Q·2025.4Q / 처브라이프 2024.4Q·2025.2Q·2025.4Q / AIA 2025.4Q / 카카오페이 2025.4Q

**홀수분기인데 MD에 표 존재(텍스트, 파서 누락) 3:**
- 삼성생명 2023.3Q·2024.1Q·2024.3Q (MD에 5종 세부표 distinct≥3 확인 — 추출 가능)

### 추격 불필요 (cadence-legit, 127건)
생보 9사(삼성생명 일부·한화생명·라이나·DB생명·미래에셋·동양·신한라이프·KB라이프·AIA) + 삼성화재·서울보증·AIG·메리츠·현대·KB손해·DB손해·NH·악사·처브·신한이지·하나손해·한화손해·롯데·코리안리·흥국·카카오의 **홀수분기** = 간이공시라 36-40 원천부재. validation이 SKIP 처리(MARKET_BREAKDOWN_EXEMPT 등록 불필요 — 룰이 자동 cadence 판정).

### 요청
1. 위 21건만 재추출(짝수 full-form은 이미지/OCR 가능성, 삼성생명 odd 3은 텍스트표).
2. 짝수분기인데 원천에도 표가 진짜 없는 회사 있으면 raw 근거로 회신 → MARKET_BREAKDOWN_EXEMPT 등록.
3. (참고) 36_irr 41-46 짝수분기 갭 23→16은 별도 inbox `..._irr_scenario_41_46_evenq_gaps.md`.

## 답변 (parser 작성 2026-06-14 — 21건 확인, 회수는 별개 43건이었음)

뒤늦게 확인(이 노트 놓쳤었음). 정정 수치(진짜 갭 21, cadence-legit 127) 동의 — 내 "odd-Q 103 EXEMPT 후보"와
일치하고, `_scan_breakdown_presence` 자동 cadence-SKIP이 더 나은 해법(수동 EXEMPT 불요) 확인.

**중요**: 이번 대량 회수(146 all-five, RED 148→21)는 이 **21건을 포함하지 않았다**. 대조 결과 21건 전부
아직 <5 (even-Q 18: 0/18, 삼성생명 odd 3: 0/3). 즉 회수된 +43은 별개의 쉬운 셀(깨끗한 '현황' 섹션)이었고,
이 21건이 hard residual로 남음. 근본원인: 내 Phase-0 국소화가 **raw PDF**에서 떴는데 21건은—

1. **스캔이미지(OCR=owner gold)**: AIA 2025.4Q·카카오 2025.4Q. 파서 불가 → owner OCR 큐.
2. **even-Q full-form 결측 16** (KB손해 24.4Q·25.2Q / DB손해 24.4Q / NH 25.4Q / 신한이지 23.2Q·25.2Q·
   25.4Q / 처브 24.4Q·25.2Q·25.4Q / 흥국생명·흥국화재 24.4Q / DB생명 25.2Q / 한화생명 23.4Q·24.2Q·25.2Q):
   재localize 재추출 대상. 단 한화생명은 내부모형사(740p, 앞선 진단서 분해가 서술형뿐일 가능성) — 표 부재면
   raw 근거로 회신.
3. ⚠️ **삼성생명 odd 3 (23.3Q/24.1Q/24.3Q) 불일치 flag**: validation은 "MD에 5종 표 distinct≥3"이라는데,
   현재 `data/disclosure/FY2023_Q3/parsed/KR0069_삼성생명.md` grep 시 **시장위험액(parent, line230=205,717)
   + 경과조치 라인만** 검출, 5종 분해 라벨(금리/주식/부동산/외환/자산집중 위험액) 행이 안 보임. docling 재렌더
   차이나 라벨변형 의심 — validation이 본 MD 버전/라인번호 공유해주면 즉시 재추출. (현 MD엔 안 보임.)

**계획**: 위 16(+삼성 3 확인되면)을 parsed-MD 소스로 재localize + reconcile-gate 워크플로우 재실행. 스캔 2는
owner OCR. 처리분 회신 예정. status: open(21건 작업 중).

### 갱신 (2026-06-14, partial_reconcile 수정 후) — 21 중 6 회수, all-five 146→264
원인 추가규명: 21건은 localization 문제가 아니라 **분류 게이트 버그**였음. 소형사(처브·신한이지)는 부동산/
자산집중위험액이 진짜 ~0이라 agent가 3종만 추출 → 초기 `nonNull>=4` 게이트가 PARTIAL로 오분류(rel은 0%인데).
**rel<2%면 누락분 0으로 채워 저장**하도록 수정 → 신한이지 23.2Q/25.2Q/25.4Q·처브 24.4Q/25.2Q/25.4Q **6건 회수**.
부수적으로 전체 all-five **146→264** (264/264 reconcile, 0 fail), 41-46 = 177 (0 fail). gold 2382 재생성.

**잔여 15 (분류):**
- **owner OCR (2)**: AIA 2025.4Q·카카오 2025.4Q = 스캔이미지(텍스트레이어 없음).
- **downloader 재다운 (2)**: DB손해 2024.4Q·NH농협손해 2025.4Q = **PDF 손상(pdfplumber Unexpected EOF)**.
  → `TODO_downloader` 재다운로드 필요(별도 inbox 예정).
- **agent 타깃 재시도 (~8)**: KB손해 24.4Q·25.2Q / 한화생명 23.4Q·24.2Q·25.2Q / 흥국생명·흥국화재 24.4Q /
  DB생명 25.2Q. artifact엔 분해표 존재 확인(KB손해 현황 6p·처브식 구조)인데 1차 agent가 놓침 → 워크플로우
  타깃 재실행으로 회수 가능(다음 슬라이스). 단 한화생명은 내부모형사라 표 부재 가능성 — 그땐 raw 근거 회신.
- **validation 확인대기 (3)**: 삼성생명 23.3Q/24.1Q/24.3Q — 현 parsed MD엔 5종 분해 라벨 부재(시장위험액 parent+
  경과조치만). validation이 본 MD 버전/라인 공유 요망.

status: open (6/21 회수 + all-five 264; 잔여 15 = owner-OCR 2·downloader 2·agent재시도 8·validation확인 3).

### 최종 disposition (2026-06-14, agent 재추출 워크플로우 2회전 후) — 19_market RED=15 분류 완료

reconcile-gated 추출 워크플로우(localized page + full parsed MD, sqrt(V'MV)≈item19 게이트, adversarial
re-read)를 19_market RED 짝수분기 전수에 돌림. 결과 = **"agent 재시도 8"은 대부분 회수 불가**(소스 자체 한계)로
판명. 현 RED 15의 정확한 사유별 분류:

- **회수(1)**: 한화생명 2024.2Q — item36(금리위험액 9,385억)+IRR 41-46 적재(self-reconcile rel0.6%). 단
  내부모형사라 37-40(주식/부동산/외환/자산집중)은 표준형 미분해 → **19_market은 여전히 RED(5종 중 1종만)**.
  → 한화생명은 internal-model `MARKET_BREAKDOWN_EXEMPT` 대상(아래).
- **downloader 재다운(2)**: KR0011 DB손해 2024.4Q·KR0032 NH농협손해 2025.4Q = **PDF 손상(fitz/pdfplumber
  EOF, localization ERR)**. `inbox/downloader/` 발주함.
- **re-docling(2)**: KR0010 KB손해 2024.2Q·2025.4Q = parsed MD가 **keyword_window 부분파싱**이라 6-4 시장위험
  섹션 자체가 캡처 안 됨(frontmatter `parse_scope: keyword_window` 확인). full re-docling 필요 → downloader inbox.
- **owner OCR / image-only(4)**: KR0010 KB손해 2024.4Q·2025.2Q = **금리위험액 현황이 raw PDF 120p/64p 전체에
  텍스트로 없음**(주식/부동산/외환은 p76-77 텍스트로 존재 → 금리위험액만 이미지). KR0080 AIA 2025.4Q·KR1098
  카카오 2025.4Q = 스캔. → owner OCR 큐.
- **MARKET_BREAKDOWN_EXEMPT 후보 — 단 raw 확인 필요(3)**: KR0068 한화생명 2023.4Q·2025.2Q, KR0071 흥국생명
  2024.4Q, KR0005 흥국화재 2024.4Q = parsed source에 **숫자 위험액 전무, 서술형만**(예: 한화 "금리/주식/부동산/
  외환/자산집중 5개 하위위험으로 구분합니다" 텍스트뿐). 내부모형/이미지 가능성 → blanket exempt 전에 raw page
  근거 확인 권고. (현 소스 기준으론 추출 불가.)
- **삼성생명 odd-Q 3 (23.3Q/24.1Q/24.3Q) — 여전히 불일치**: validation은 "MD에 5종 분해표 distinct≥3"이라는데
  현 parsed MD엔 시장위험액 parent+경과조치만, 5종 라벨 부재. **validation이 본 MD 버전/라인번호 공유 요망**(재확인 3건).

→ 즉 **agent 재추출로 닫히는 19_market RED는 0건**(소스 한계 = downloader/OCR/내부모형). 회수된 한화 2024.2Q도
19_market은 못 닫음. **status: answered** (잔여 15 전부 비-파서 라우팅 or owner 결정; 파서측 추가 작업 없음).

### ⚠️ 정정 (2026-06-14 후속) — 위 "0건" 결론 틀렸음. fitz 재localize로 3건 clear

위 결론은 **localizer pdfplumber 무음실패**에 기인한 오판이었음. pdfplumber가 EOF로 죽은 PDF(DB손해·NH 등)를
**fitz로 다시 떠서 find_tables 구조표로 재추출** → **19_market 3건 clear: DB손해 2024.4Q(5/5)·NH농협손해
2025.4Q(4/5)·한화생명 2024.2Q(4/5)**. 19_market RED 15→12. (한화는 round-1 item36 + round-2 37-39 합쳐 4/5.)
잔여 12: KB손해 4분기·한화 23.4Q 금리위험액 = full-page 이미지(owner OCR), 신한라이프 등 내부모형, 흥국 image,
삼성생명 odd-Q MD불일치. root-cause = localizer fitz 교체(TODO 등록).

## 재검증 (validation 2026-06-14 ~20:55 KST) — ✅ resolved (dedup)
**삼성생명 odd-Q 3 = 내 `_scan_breakdown_presence` clean-cell fix로 해소** — MD L174(산문)/L184·185(경과조치 compound)/L230(parent)이 distinct≥3 substring을 거짓충족했던 것, 진짜 5종 분해표 부재 = SKIP 정당(네 판단 옳음). 잔여(KB손해 OCR·내부모형·흥국 image·DB손해/NH downloader)는 v2 `irr_exempt_register` + inbox/downloader로 consolidated. 19_market RED 현 10(전부 owner/parser 활성). 중복 → `_resolved/` 이관.
