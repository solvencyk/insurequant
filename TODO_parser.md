# Insurequant Parser TODO (Stage 2)

Last updated: 2026-05-31.

Stage 2 — **parser**: raw artifacts (DART body XML / Docling MD / IR xlsx / FSC bonds raw / KIDI JSON) → structured per-record JSON. The validation subagent rule-checks the result; gathering composes derived viz.

**Stage files**
- Prompt: [`docs/agents/claude-agent-parser.md`](docs/agents/claude-agent-parser.md) (skeleton)
- Changelog: [`docs/changelog_parser.md`](docs/changelog_parser.md)
- This file: open parser work + parser-done archive

Session start: read this file + `claude-agent-parser.md` + relevant domain ref(`docs/domains/claude-agent-{kics,ifrs17,misc}.md`).

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## ▶ IN PROGRESS (2026-06-07 야간 자율) — CSM_waterfall closing 수정 + 누락사 점검

owner 취침 중 자율 진행. 발견:
- **root 마스터 배치 완료**: `PL_breakdown.json`(7727행)·`CSM_waterfall.json`(1794행) = 값(연누계)+값_당분기.
  빌더 `scripts/build_root_masters.py`(YTD 빌더 뒤 실행, 멱등). 유량=YTD차분, 저량(CSM기초/기말)=시점잔액.
- **CSM 'NULL 코드' 4사**: 삼성생명/미래에셋/코리안리/케이비라이프가 CSM_waterfall에 코드=None+이름 불일치로
  존재(IR/별도경로 추정) → "누락"처럼 보임. 코드+이름 정규화 필요. (에이전트 a65ff 분석 중)
- **CSM 진짜 누락**: AIG·라이나·메트라이프·BNP·하나생명·서울보증·신한이지·악사 (소형/외국계, PAA-only 추정). 점검 중.
- **CLOSING_IDENTITY fail 40건**: 에이비엘(9)·KDB(6)·미래에셋(3)·KB라이프(3)·흥국화재(3)·한화생명(2)·동양(1).
  item4(가정경험)=잔차인데 안 닫힘 → 스텝 누락(환율변동 등) 의심. (에이전트 aa0af 분석 중)
- 통합 방식: 에이전트 read-only 레시피 → 메인이 직렬 수정 → 재빌드 → `validate_master_tables.py`
  재검증 → `build_root_masters` 재실행 → 무회귀 확인.

### ✅ 완료 (2026-06-07 야간)
- **CSM 정본 writer = `scripts/build_tidy_exports.py`** (build_csm_waterfall_master는 diag만). reads
  `data/dart/viz/csm_waterfall_history.json`. **빌드 순서: history → build_tidy_exports → build_root_masters(마지막).**
  (build_tidy_exports가 자체 187행 PL_breakdown.json도 쓰므로 build_root_masters를 반드시 뒤에.)
- **NULL 코드 4사 수정**: build_tidy_exports `meta()/base()`에 `DART_NAME_TO_KICS` 역alias 추가
  (삼성생명→삼성생명보험 KR0069, 미래에셋생명→KR0079, 코리안리→KR1000, 케이비라이프생명보험→KB라이프 KR0099).
  → None-코드 0건. PL↔CSM 조인 복구 → **crosscheck 136F→26F, pl_bridge 55F→36F**. 무회귀(정확히 4행만 변경).
- **누락 9사 점검 결과**: 8사 FILLABLE(GMM CSM 변동표 존재, universe 필터 오타로 미수집)=AIG·악사·신한이지·
  라이나·메트라이프·BNP·하나생명·교보라이프플래닛. 서울보증만 NO-GMM(보증보험). → Problem 2(아래) 후속.

### ✅ CSM closing + 누락사 — 해결 (2026-06-07 야간)
- **근본 해결 = diag 승격**: 정본 CSM = `build_csm_waterfall_master.py`(item4=잔차) → `data/dart/viz/
  csm_waterfall_master_diag.json`. `build_root_masters`가 이걸 읽어 당분기+가드 적용 후 root에 출력.
  옛 history-chain(build_tidy_exports, item4=literal+전분기 오블록) 대체. **빌드순서: build_csm_waterfall_master
  → build_root_masters.** (build_tidy_exports CSM 경로는 root에 더 이상 안 쓰임.)
- **결과**: closing **40F→0F (299P/6S)**, crosscheck **136F→9F**, pl_bridge **65F→36F**. **CSM 23→35개사**
  (누락 12사 전부 diag에 이미 있었음 — Problem2 자동해결), NULL코드 0, 당분기 1669/1830.
- **AIG 2025.4Q 단위오류(~1000×) 가드**: `build_root_masters` CSM_ABS_CAP=5e5억 초과 c-q null.

### ⏭ 남은 것 (저우선, 발행 전 점검)
- **closing 6 SKIP**: 5건 라벨변형(KDB 2023.1Q·라이나 2024.4Q·미래에셋 2025.2Q/3Q·하나손해 2024.4Q —
  상각/이자 항목 변동요인별 라벨. aa0af §2b: `viz_build_csm_waterfall.py` STAGE_PATTERNS amortization에
  "현재 서비스와 관련된 변동분"/"제공한 서비스를 반영" append) + AIG 2025.4Q(단위오류 null).
- **메트라이프 2025.4Q ~2.2× 점프**(세그 중복 의심), **KDB 2025.4Q 기초 불연속**(closing은 통과, 시퀀스만) — 발행 전 review.
- pl_bridge 36F 잔존 = bare-closes 오탐(룰 dual-form 권고) + DB생명/동양 2023(FY2023상반기 Tier-1 부재) + DB OLD 재보.
- crosscheck 9F 잔존 = 코리안리 재보험 item4 scope + 소수.

### 직전 완료 (이 세션, 2026-06-07)
- item16 부호 정규화(abs) → bridge fail 7건+한화 골드 해소. item19(보험금융손익) account_nm fallback
  (KB라이프 등 미사용코드) + item17 net 통일(gross→item18 투자이익) → 영업이익=1+17 전사 성립(FS-API 셀).

---

## ▶ TODO (2026-06-07) — 월납월초 → CSM배수 마스터 + 당분기 컬럼 (owner 지시, 착수 보류)

**산출 양식 = `NB_CSM_multiple.xlsx`**: cols = 원보험사코드 / 원수사명 / 티커 / 생손보여부 / 공시분기 /
신계약CSM_연누계 / 월납월초보험료_연누계 / 신계약CSM배수_연누계 / 신계약CSM_당분기 / 월납월초보험료_당분기
/ (신계약CSM배수_당분기). CSM배수 = **원수 기준 신계약CSM ÷ 월납월초보험료**.

### 1) 월납월초보험료 마스터 정제 (per 회사×분기, 2023.1Q~2026.1Q)
- 기존 `data/_derived/nb_premium_wolnap.json`(328항목, 기간라벨 혼재 FY2024/2025.3Q/1Q26…, KIDI+IR+override)
  → 일관 per-(회사,분기) 마스터로 정제. 크롤러: `crawl_kidi_life_premium`/`_longterm`/`crawl_assoc_nb_premium`.
- **scope 정의(owner 2026-06-07)**: 삼성생명·삼성화재 IR 대조 결과 딱 맞는 건 없지만 **≈ 보험계약 > 월납 >
  초회보험료의 합계**. **저축성보험 포함 기준**으로 진행(손보는 저축성 share 미미; 소수1자리 반올림 공시라
  포함/미포함 영향 미미). → **이 기준으로 특이값 나오는 회사 있으면 owner에게 보고할 것.**
- 환산: KIDI/공시가 이미 환산해 제공한 값 사용(내가 일시납÷계수 새로 계산 X) — 확인 필요.

### 2) 당분기(quarterly standalone) 컬럼 추가 — CSM Waterfall + PL breakdown + 월납월초 전부
- 현재 CSM Waterfall·PL breakdown 마스터는 **YTD(연누계) 기준만**. owner: **당분기 컬럼도 따로** 원함.
- 당분기 = 당YTD − 직전분기YTD (Q1은 YTD=당분기). 단 Q4 연차/분기 보고 누계정의 주의.
- **KIDI 다운로드분이 연누계 기준인지 확인**(아마 연누계) → 당분기 환산 필요.
- 최종: 첨부 양식대로 당분기 & 연누계 둘 다 컬럼.

### 결정/메모
- 신계약CSM 분자 = 기존 `CSM_waterfall.json` new_business. CSM배수 검증기 `validate_nb_csm_multiple.py` 재활용.
- (착수 보류 — owner가 PL breakdown/CSM waterfall 마스터 관련 질문 먼저.)

---

## ▶ NEXT (2026-06-06 (b) — Tier-2 대확장 완료, 후속만 남음)

**완료**: 병렬 7에이전트 분석 → 12배치 직렬 통합. master **315 c-q**, self-check **v 160→205**, 주요사
Tier-2 **262/301 분기**, master 0 garbage cells, 골드게이트 무회귀. 상세 → `docs/changelog_parser.md`
**2026-06-06 (b)** 항목. 통합사: 한화손해 1→4/13, KB라이프 0→13/13, NH 누적정합, 코리안리 13/13,
현대 4→10/13, DB·삼성화재·메리츠 풀, 흥국화재 3→11/13, 한화생명 4→13/13, 농협/푸본/흥국생명/ABL/
삼성생명(9/10/11)/KDB/교보(item6) 충원.

**남은 follow-up** (우선순위순, 상세 → changelog 2026-06-06 (b) "남은 follow-up"):
1. [ ] **미래에셋 분기 4/12** — rollforward 원-unit → 백만원 emit 핸들러(현재 sanity cap으로 garbage만 차단).
2. [ ] **한화손해 13/14 퇴직연금** — owner 배분판단 필요(현재 순수 PAA값). + pre-2025.2Q OLD 핸들러(8분기 blank).
3. [ ] **흥국화재 NEW 2025.4Q/2026.1Q** — 연차 단일표 오작동(4/5=0). 별도 수정.
4. [ ] **흥국생명 2026.1Q 더블링** — `_life_comprehensive` dedup이 caption 공백차 중복노트 누적.
5. [ ] **롯데 6/12** — 2024.2Q/3Q·2025.3Q/2026.1Q 컴포넌트노트 미발견(deeper probe 필요).
6. [ ] 교보 반기/분기 3개월 basis(누적 아님) / 한화생명 2023.2Q(x=1, FY2023 outlier).

**검증 명령**: `PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/build_pl_breakdown.py` (재빌드) → `python scripts/_verify_pl_golds.py` (게이트) → `python scripts/_pl_selfcheck.py` (RC matrix).

---

## 🎯 마스터 테이블 현황 (2026-06-02) — CSM waterfall + PL breakdown

기준 방법론 영구기록 → **[`docs/domains/csm-pl-basis-methodology.md`](docs/domains/csm-pl-basis-methodology.md)** (별도/연결, 원수/재보험 히스토리 + PL 24항목 스키마). 반드시 먼저 읽을 것.

### 🔔 2026-06-04 (야간 자율) — PL 전사 전분기 sweep + Tier-1 일반화 (broken 44→0)

사용자 지시: "전분기(2023.1Q~2026.1Q) PL 다 추출. 답지-specify 하드코딩 말고 rule 학습해 응용. 최대한 맞추고 진짜 답지 필요한 것만 몇개." (상세 → changelog_parser 2026-06-04)

- **무답지 self-check** 신설 `scripts/_pl_selfcheck.py` → `docs/pl_selfcheck_matrix.md`. 보편항등식 **22=20+21**만 신뢰(`20=1+17`은 기타영업 구조사에서 비성립 → 정보성). Tier-2 RC는 컨벤션 무관 dual-form.
- **일반 규칙 6종**(회사코드/분기캡션 하드코딩 0): FIX A 우선순위 NI(당기순>계속영업), FIX B 법인세 잔차(=22-24), FIX C 항등식-우선 basis(연결→별도 자동), 각주-ref 가드, Tier-2 단위정합(천원/원 자동), abs-cost fallback. **롯데 Tier-2는 기수/주석번호 하드코딩 제거 → 섹션-워커**(통합/분리표 양형태).
- **RC-게이트**: ΣLOB가 보험손익과 25%↑ 어긋나면 breakdown(2-14) 억제+Tier-1 유지(garbage 미배출). 억제셀=골드후보 자동집계.
- **결과: broken 44→0. self-check G4/v88/i81/~11**(.206=미상장 Q1-Q3 설계 공란). Tier-2 reconcile 103/억제 19/없음 240/partial 91. 골드게이트 무회귀(삼성화재24·메리츠24·삼성생명22[item19 split]·한화생명23).
- **골드후보 6셀/5사 → [`docs/pl_gold_needed.md`](docs/pl_gold_needed.md):** 롯데손해 2024.4Q(중요·item1 다중컬럼 모호)·한화손해 2025.4Q(기존 NB)·하나생명·악사·교보라이프(소형). 분기 억제 13셀(메리츠·현대·삼성화재 Q1-3)=저우선.

### 🔔 2026-06-04 (d) — 한화생명 분기 답지 → 분기 추출 전사 교정 (cq 260→292)

- 사용자 `보험손익 breakdown_한화생명_2025.2Q.xlsx`(별도) + 다운로더 확인("본문에 다 있음, 파서 매칭").
- **두 일반 버그 수정:** ① 분기보고서는 **반기/분기순이익** 라벨(당기순이익 아님) → `NI_LABELS` 확장 (한화생명 분기 0개의 원인). ② 분기 statement는 `[3개월,누적]` → 스키마=YTD이므로 **누적 col 읽기**(`_ytd_col`).
- **파급(교정, 회귀 아님):** 삼성생명/현대/삼성화재 분기가 3개월/전환표상수 garbage→**정확 YTD**. 삼성화재 1627/1627/1627→609<1247<1786<2020.
- **결과:** company-quarters 260→**292**, no_income_statement 149→**60**, self-check **G4/v125/i125/~17/x1/.118**. 한화생명 분기 10개 복구. 연차 골드 6장 무회귀. **Q4 골드후보 1개**(교보라이프뿐).
- 잔여: x=1 한화생명 2023.2Q(첫해 컬럼불균일), 분기 Tier-2 noisy 24셀(RC게이트 억제). 저영향. **상장사 전분기 Tier-1 사실상 완료.**

### 🔔 2026-06-04 (b) — 롯데 PL 답지 통합 (PL 골드 5장, 롯데 RESOLVED)

- 사용자 `보험손익 breakdown_롯데_2024.xlsx` 제공. **근본원인=재작성-영향표 오추출**(추출기가 "소급재작성이 …에 미치는 영향" 표의 2023 재작성치 468,499를 당기 item1로 골랐음; 정답 177,845).
- **일반 규칙(하드코딩 0):** `_is_income_statement`에서 캡션 **"미치는 영향"** 표 제외("재작성" 단독은 정상 statement 각주에도 있어 한정). + **_is-fallback 가드**(보험비용<보험수익10%면 생략→note items 4-11 보존; 교보 2025.4Q 회귀 차단).
- **롯데 2024.4Q 답지 23/24 정확 일치**(유일 불일치 item15 None-vs-0). PL 골드 **5장 무회귀**: 삼성화재24·메리츠24·삼성생명22·한화생명23·롯데2024 23. self-check **G4/v89/i74/~11/x0**.
- 골드후보 Q4 6→**3셀**(교보라이프·악사·한화손해NB = 소형/기존defect). **롯데 완전 해결.**
- ✅ **사용자 액션 완료** — 더 필요한 PL 답지 없음(나머지는 소형/코드수정 영역).

### 🔔 2026-06-03 업데이트 (야간 자율) — CSM gold **8/8**, gold-map 신설

- **CSM 골드 8/8 통과:** 2025.4Q 6사 + **2024.4Q 생보 2사(한화생명 92,384.9·삼성생명 122,473.7 별도)**.
- 핵심 픽스 3건: ① 삼성생명 이자=순금융+환율 ② 한화생명 별도(`_comparable_min` 50%게이트), 삼성생명 상품라인 세그합산(`_segment_min_sum`) ③ `is_prior` 자기-opening 제외 버그 수정(분기 기초≈기말 오판) + "2)전분기" 캡션 제외.
- **회귀 적발/복원:** 직전 blanket MIN fallback이 ~125 q 파괴(garbage)였음을 A/B로 잡아 복원.
- **gold-map → [`docs/csm_coverage_goldmap.md`](docs/csm_coverage_goldmap.md)** (전 27사×13분기 매트릭스 + 분류).
  - **BROKEN(gold/추출기수정 필요):** DB손보 2025(122K→17K)·롯데손보 2025·동양생명 2025.2Q·**삼성생명 2025.1Q**(추출기 캡션잘림→세그합산 미발동).
  - **large-wobble(별도/연결 추정, 검증불가):** 교보·농협생명·미래에셋·푸본현대.
- ⚠️ 삼성생명 2025.1Q 근본수정 = `measurement_extractor`가 "상품라인/출재" 부모캡션을 sub-block에 보존하도록(별도 작업, 추출기 영역).

### 🔔 2026-06-03 (d) — CSM 골드 7장 받아 BROKEN/large-wobble 해소 (게이트 86/90)

- 사용자 CSM 답지 **9장**(농협·롯데·DB손보·동양 2025.2Q·삼성생명 2025.1Q·교보·미래에셋·푸본현대) → 신규 게이트 `scripts/_verify_csm_golds.py`(자동발견, 사망/건강/연금 컬럼 합산).
- 픽스: ① **삼성생명 2025.1Q** `_anchor_segment_sum`(anchor=연초와 일치하는 major 세그합, 출재 잡블록 배제) ② **교보·푸본(KR0073·KR0083)** 연간 무배당+유배당+변액 캡션교차 합산, **미래에셋(KR0079)** 상품별 분해만(배당분해 중복 제거), `pick_combined_agnostic(...,code)`.
- **9사 전원 통과, 기존 8 무회귀, 92/96.** 잔여: 삼성 2024.4Q 이자·2025.1Q 조정(반올림), 한화손보 NB(기존). 교보 골드시트 셀 라벨오기(FILE_OVERRIDE 우회).
- **3색 상태표 → [`docs/csm_status_matrix.md`](docs/csm_status_matrix.md)** (생성기 `scripts/_csm_status_matrix.py`): G16/c231/~48/?1. 2025.4Q 연간컬럼 주요사 G/c, wobble은 2023 과거연도+일부 2025분기.
- PL 농협생명 답지도 24/24. goldmap 재생성: DB손보/롯데/동양/농협 BROKEN 탈출.

### 🔔 2026-06-03 (c) — PL Tier-2 **전사 확장** (답지 없이 self-check) + Tier-1 item1 4건 수정

- 사용자 지적 반영: "답지 달라" 대신 원문 직접 파싱. LOB note 미매칭 12사 + partial 4사 = **16사를 회사별 핸들러로 흡수**, Tier-1 보험손익 reconciliation(gap ≤0.04%)로 답지 없이 검증.
- 회사별 핸들러 12개 추가(`extract_tier2_kb/hyundai/hanwha/db/nh/lotte/koreanre` + 생보 `kyobo/dblife/dongyang` + comprehensive). 단위/컬럼순서/라벨/표형태 회사마다 상이.
- **Tier-1 item1 4건 수정**(현대 809K→396,111, 한화손해 206→206,270 단위버그, 코리안리 226K→223,754, 교보 371K→391,590) — TIER1_HINTS 코드스코프, 골드 byte 불변.
- **골드 게이트(독립 재검증):** 삼성화재/메리츠/삼성생명 불변, **한화생명 19→23/24 개선**. 무회귀. **2025.4Q ok 4→13.**
- 남은 갭(답지 불요): raw_not_extracted(다운로더), no_income_statement(파서확장), 구조적 N/A(NH 6/11·코리안리 13/14·미래에셋 6). 맵 → [`docs/pl_breakdown_coverage.md`](docs/pl_breakdown_coverage.md), 생성기 `scripts/_pl_coverage_map.py`, 회사구조 메모 `scripts/_plprobe_*.py`.
- **다운로더 수정 후 재sweep:** 13사 XML(`_00760`/`_00761`) 추출됨 → 재실행. 파서코드 무변경. **raw_not_extracted 2025.4Q 13→0**, PL 194→260 cq, 골드 무회귀. 잔여 no_income_statement 소형 7사(라이나·IM라이프·메트라이프·처브·IBK연금·카카오페이·KB라이프) = Tier-1 번호식 포맷 확장, **보류**. downloader 재확인: 하나손해 XML 테이블 0개 / BNP파리바 IS 미검출. 비상장사 Q4-only(구조적).

### 🔔 2026-06-03 (b) — PL breakdown 24항목 **구현 완료** + 전사 sweep

- **신규 `scripts/build_pl_breakdown.py`** (기존 `build_net_income_breakdown.py` 무손상) → `data/dart/viz/pl_breakdown_master.json` (4,656행 = 194 cq × 24항목, 백만원). Tier-1 포괄손익(1,15-24, 연결·별도 basis-aware) + Tier-2 발행/재보험 note(4,5,6/9,10,11/13,14), 파생 2,3,7,8,12=항등식.
- **gold 4사(2025.4Q):** 삼성화재 24/24·메리츠 24/24·한화생명 19/24(직접추출 전부 통과, 잔차 null)·삼성생명 22/24(항목18/19 0.67% gold방법론차, 파싱오류 아님). 검증 `scripts/_verify_pl_golds.py`.
- **커버리지 맵 → [`docs/pl_breakdown_coverage.md`](docs/pl_breakdown_coverage.md)** (453 cq: ok 9/partial 161/no_inc_stmt 132/raw_not_extracted 151).
- **gold-needed(2025.4Q, LOB note 미매칭):** 손보 한화손해·롯데손해·현대해상·KB손해·DB손해·NH농협손해·코리안리 / 생보 교보·DB생명·동양·신한라이프·농협생명.
- **파서밖:** no_income_statement(하나손해·KB라이프=파서확장) / raw_not_extracted(2025.4Q 13사=document.zip만 → downloader 갭).
- 야간 보고서 → [`docs/MORNING_REPORT_2026-06-03.md`](docs/MORNING_REPORT_2026-06-03.md).

### A. CSM Waterfall — `build_csm_waterfall_master.py` → `data/dart/viz/csm_waterfall_master_diag.json` (954행)

**공식:** 각 단계 = Σ(그룹별 CSM). 항목4(가정·경험)=residual. **전부 별도·원수 발행** 기준.
**4 추출패턴 (회사 구조 이질성 흡수, 캡션 무관):**
1. `배당합산` — 배당있는/없는 **별도 sub-table 2개** 합산 (메리츠·KB·롯데·흥국). dang+mu 둘 다 필요.
2. `배당칼럼합산` (= 차이조정표 일반화) — **한 표 안 그룹 칼럼**. G = "구성요소별 보험계약 합계" 칼럼 수: 배당2(삼성화재/현대/한화손보), 상품라인3 사망/건강/연금(삼성생명), 단일발행1(한화생명). CSM = 그룹당 idx 2~(stride-2) 합산(전환방법 3-split 포함). 라벨 col0+col1 2칼럼 검사. **별도 선택 = 현재기간 후보 중 min-opening**(본문에 별도·연결 둘 다, 연결≥별도). 원/천원 magnitude 스케일링.
3. `combined`/`combined-agn` — 캡션무관 단일 원수표 (DB·농협·코리안리). 재보험/관계기업 제외, movement 가드.

**커버 = 21사 (손보 10 + 생보 11), 전부 balanced:**
- **GOLD 6/6 항목 정확 (6사): 메리츠·KB·삼성화재·한화손보·한화생명·삼성생명** ✅
- 손보 sane: DB·현대·흥국·롯데(NB=gold 4,121.7)·농협·코리안리
- 생보 sane(gold 無): 신한라이프·교보·KB라이프·농협생명·동양·흥국생명·미래에셋·DB생명·푸본현대

**미커버 (정직):** 소형 손보 6사(AIG·악사·하나손해·신한이지·서울보증·카카오페이) = PAA-only, CSM 없음 → none 정답. 소형 외국계 생보 8사 = CSM 미미.

**한화손보 5/6:** 기초/기말/이자/상각 정확, **NB만 손상** (extractor가 중첩 rowspan 오파싱, assumption→NB 혼입). 코어 수정=오버엔지니어링 보류, residual 흡수.

**[x] 해결됨 (2026-06-02 b):** 삼성생명·한화생명 별도 픽스 (연결→별도, min-opening). 삼성생명 detection (G=3 상품라인). `__main__` 가드 + `waterfall_for_dir` 헬퍼.

### B. PL breakdown 24항목 (원수/재보험 분리) — `build_net_income_breakdown.py`

스키마·공식·검산 → basis 노트 §3. 사용자가 measure 확장: CSM상각/RA/예실차/기타를 **원수(4-7)·재보험(9-12) 둘 다 별도 항목**으로 (불일치 해소).
- **Tier1 (전사)**: 10/10 손보 OK 유지.
- **Tier2 (부문)**: 공식 확정, gold 4사(삼성화재·메리츠·한화생명·삼성생명). **24항목 구현 대기.**
  - 부문손익 = 보험수익−보험서비스비용+재보험수익−재보험비용. 원수 예실차 = 발행 기초예상발생 − 실제발생보험금. 재보험 예실차 = 재보험 실제발생 − 재보험 기초예상.
  - 구현: `extract_tier2_lob`에 재보험수익/재보험비용 component + 예실차 component 추가. 생보는 상품세그(사망/건강/연금/변액/기타) 합산, 자동차/일반=0.

### C. 분기 시계열 (사용자 교정)
"분기 표도 결산과 동일" → 구조 문제 아님. 기초=YTD 정상. 불안정은 별도/연결 + 블록선택. **A의 min-opening 별도 픽스가 분기에도 적용됨** → 연도경계 불일치 상당부분 해소 예상(재검증 필요).

### 🔔 GOLD 받아서 검증할 것 (남은 호출)
1. **생보 PL breakdown** — 한화생명·삼성생명 gold 보유. 나머지 생보 gold 필요시.
2. **나머지 손보 PL** — 삼성화재·메리츠 gold 보유. DB·현대·KB·한화·롯데·흥국·농협·코리안리 gold 받아 검증.

### 다음 (gold 불요, 바로)
- [x] **PL 24항목 구현** + 4사 gold 게이트 (삼성화재·메리츠·한화생명·삼성생명) — 2026-06-03(b) 완료, `build_pl_breakdown.py`
- [ ] CSM diag → canonical `CSM_waterfall.json` 통합 (build_tidy_exports 연결, 21사)
- [ ] 분기 시계열 연속성 재검증 (별도 min-opening 적용 후)
- [ ] KDB·ABL 생명 CSM 미커버 구조 확인

---

## Taxonomy correction (this session, 2026-05-31)

LOB axis differs between 손보 CSM decomposition and 손보 P&L decomposition. Do NOT conflate them in the parser.

- **손보 CSM decomposition** = 보장성 / 물보험 / 저축성 (all within 장기보험; 삼성화재 uses this taxonomy)
- **손보 P&L decomposition (보험손익)** = 장기 / 자동차 / 일반 (Tier2 in F17)
- 자동차 / 일반 are PAA contracts → no CSM rollforward; they contribute to P&L only
- 보종별 신계약 CSM multiple is IR-disclosed only for a subset of insurers; do not synthesize from DART for the others

This box should be removed once F17 lands and the prompt §2.2 captures it.

---

## Active — NB CSM + waterfall block selection (2026-06-01 update)

**2026-06-01: 2026-05-31 trade-off 해소 → Option B.** `_disambiguate_basis_period` (`rank_main_blocks` 끝, waterfall+history 공통) 가 전기 copy 제거 + 별도(기초 최소) 선택. 6/28 교정, 전부 residual 0, 22사 무변경. 상세 → `docs/changelog_parser.md` 2026-06-01.

- **DONE — 한화생명** NB 32,361→21,231억 (전환방법별 단일셀) + waterfall balance 닫힘: 별도·당기 측정요소별 (기초 9.24조) 선택, 연결·전기(13.59조) 아님. residual +1.11조 → 0.
- **DONE — 메리츠화재** 16,006 → **13,796억 = IR FY24 정확 일치** (1.160 OVER → 1.000). 전기(FY2023) mis-pick였고 손보 전환표 gap 아님 — leaf-col CSM(그 외) read는 원래 정상. 손보 전용 pattern 불필요.
- **DONE — disambiguation 부수효과:** 에이비엘/케이비라이프 residual → 0; DB생명/교보 전기→당기.
- **롯데손해 — 소계 이중계상 fix DONE** (970,504→485,252; `find_csm_leaf_cols`가 소계 칼럼 drop). 같은 버그 7사 일괄 교정 (한화손보 1,481,978→740,989 등, 전부 ÷2, balance 유지).
- **✅ V7 cohort FY2025 close-out: `python scripts/check_nb_csm_widespread.py 2025` = 7/7** (메리츠 1.008 / 롯데 1.000 / 삼성화재 1.000 / DB 1.049 / 한화생명 1.000 / 삼성생명 1.000 / 미래에셋 1.000). 상세 → changelog_parser 2026-06-01 (d).
- **롯데 FY2025 NB = 412,168 DONE** (`reconciliation_new_business`, 잔여보장 구성요소별 변동 신계약 CSM; 측정요소별 485,252는 IR 과대).
- **FY2025 인프라:** `build_fy2025_waterfall.py` (FY2025는 본문+_00760 중복 → **_00760만 추출** → `extracted_fy2025/` → `csm_waterfall_2025.json`), `check_nb_csm_widespread.py <FY>` 연도 인자. 미래에셋 product 2× = `collect_current_product_blocks` 집계행 드롭 가드. **FY2024 regression 0.**
- **남은 것:** 비-cohort 16사 FY2025 best-effort (IR 미대조, 농협생명 0 등 일부 미해결); FY2025 dashboard 반영(history/bubble) 미실시; FY2024 check 6/7 유지 (롯데 OVER — FY24엔 차이조정 표 없음).
- **한화손해/코리안리 IR-매칭 누락 진단 (2026-06-01, alias 아님 — 회사명 둘 다 일치):**
  - **한화손해(KR0002):** IR series가 **비표준 필드** `nb_csm_eok_ir`/`nb_csm_eok_dart` 사용 (check 도구는 `nb_csm_eok` 읽음) → None → MISSING/NO_IR. + YTD "flag" 파일이라 **2025.4Q 없음**. 단 **소계 ÷2 fix가 이미 parser FY24를 14,820→7,409.9로 교정 = IR 7,410 정확 일치** (IR 파일 `data_quality_flag`가 지적한 "DART=IR 2배" 버그를 잡음). **통합하려면:** IR 파일을 표준 필드(`nb_csm_eok`)로 정규화 + 2025.4Q 값 확보. ⚠️ **필드 fallback만 넣으면 FY2025 7/7 깨짐** (한화손해 2025.4Q 부재 → YTD 합산 오류 → 가짜 UNDER). 데이터 정비가 선행돼야 함.
  - **코리안리(KR1000):** `series: {}` 완전 공백 (koreanre.co.kr IP 차단으로 미다운로드) + `kr` 필드 누락 → matrix에서 "KR null". IR 데이터 자체가 없어 크로스체크 불가. (외부 검색 2025.1Q 661억 참고치만 존재.) **2026-06-01: `kr:"KR1000"` 필드 추가 (KR null 표시 해소).**
- **History 빌더 13Q (2026-06-01 (e)):** 재빌드로 shared fix 상속 확인 (별도 주입 불필요). **음수-NB 가드 추가 → DB손해 부호반전 해소 (OVER/UNDER 3→0).** ⚠️ **진짜 fix 미완 (고위험, 별도 세션):** `find_csm_leaf_cols`가 반기/3분기 다층헤더 전환방법별-split 양식에서 `[0]`=BEL 오인 → 음수 NB. 보강하면 미래에셋 교대·삼성화재/메리츠 분기 OVER/UNDER 회복 가능하나 함수가 전 곳 사용 → 전체 재검증 필수. 회귀: `python scripts/check_nb_csm_history.py`.
- **Pre-existing imbalance (block-selection과 무관, 별개 원인):** NH농협손해 (regulatory basis), 메트라이프 +150,053, 처브 −54,917.
- **다음 할 일:** `viz_build_csm_waterfall_history.py` (13Q) + csm_bubble/nb_csm_multiple 재빌드 (한화·메리츠 별도 shift 반영); FY2025_Q4 extraction (파이프라인 아직 FY2024).
- 삼성화재/DB: parser 정상 (check 도구 4Q-SUM-on-cumulative 이슈, validation 세션 소관).

---

## In-flight — F17 Tier2 LOB 9/11사 (2026-05-31)

Tier2 LOB (장기/자동차/일반 보험손익) 4사 → **9/11 손보** OK (reconciliation gate). Report: `output/lob_underwriting_income_cross_check_20260531T103915Z.md`.

**DART source가 회사마다 다름** (재보험 포함 여부가 IR 격차 원인):
- 발행보험 by 계약유형 (**재보험 미포함**): 삼성화재/현대/DB/한화
- 보험손익 상세내역 (재보험 포함, IFRS17 행): KB (별첨 `_00760.xml`)/하나 (천원)
- 보종별 사업실적표 (regulatory): 메리츠/NH/코리안리
- 롯데 = single-segment (DART 부문손익 표 없음, IR 필요); 흥국 = unreliable parse

**IR cross-check 3사:** 메리츠 clean (+5~10%, 사업비 미차감 구조적). 삼성화재 일반 +246% / DB 자동차 부호뒤집힘 = DART note(발행보험) vs IR(재보험 포함) 차이 — 재보험 누락 가설 확정이나 DART에 부문별 수재/출재 분해표 없음 (구조적).

**Decision pending:** (1) 9/11 commit + 2 gap을 documented exception / (2) 삼성·DB debug / (3) IR-clean 회사만.

---

## Open parser work

### F12 — K-ICS 시장위험 하위위험액 전체 파싱 (parser side)

Parser + validation cross-stage. 금리·주식·부동산·외환·자산집중 등 하위위험액 + 분산효과 행 추출 (화면 노출 X, 데이터 신뢰용). The validation half is V3 in [`TODO_validation.md`](TODO_validation.md).

- [ ] 시장위험 하위 5개 + 분산효과 row 추출 추가
- [ ] 금리위험액 (+5쇼크 순자산 민감도 = 듀레이션갭) display-ready 필드 분리
- [ ] 출력 schema에 `market_risk_breakdown` 신설 → validation R11 sqrt 정합성 룰의 입력

### F15 — CSM 시계열 분기 결측 (remaining gaps after 2026-05-29 fixes)

대부분의 결측은 2026-05-29 `<TE>` data-cell fix + product-segmented column 식별 + 압축 헤더 dedup 으로 복구됨. **잔여 honest gaps:**

- [ ] **삼성생명 2023.1Q** — early-2023 different layout, parser miss
- [ ] **미래에셋 2023.1Q / 2023.3Q / 2026.1Q** — same family of early-2023 layouts plus a 2026.1Q anomaly
- [ ] **동양생명 2025.2Q ~ 2026.1Q** — 잔액(기초/기말) row 모두 0으로 추출됨; 재다운로드 검토는 `TODO_downloader.md` F15-DL
- [ ] **손보 일부 전사-vs-세그먼트 pick** — reject guard 적용 후 gap 처리; 회사별 disambiguation matrix 필요

### F16 — Panel 5 흥국생명 민감도 (product-as-rows layout)

흥국생명 sensitivity 표는 별도 양식: 상품(사망 / 건강 / 연금) = 행, 당기말 / 전기말 × CSM / 손익효과 / 자본효과 = 컬럼. 영문 'CSM' + '손익 효과' 라벨 사용. 기존 3-path band parser 미적용 → 행 어긋남.

- [ ] product-row × period-band-column 4번째 path 신설 (`viz_build_ifrs17_panels.py` 또는 sensitivity_extractor)
- [ ] 다른 회사 회귀 zero check
- [ ] Panel 5 caption 갱신 (가능한 회사 명시)

### F17 — Tier1 (전사) + Tier2 (LOB) 당기순이익 분해 (parser body)

Tier1 10사 OK 유지. Tier2는 위 in-flight 박스 참조. **남은 parser gap:**

- [ ] **KB / 메리츠 / NH농협** — FY2025 사업보고서가 FS를 **별첨 감사보고서**로 분리, body XML에 LOB 없음. (별첨 fetch는 사용자 결정상 안 함; 회사별 label 매트릭스 + 본문 내 다른 표 찾기로 해결 필요)
- [ ] **DB / 한화 / 흥국** — 회사별 disambiguation (다중후보표 중 picker가 오선택)
- [ ] **삼성화재 Tier2** — taxonomy 가 보장성/물보험/저축성 → 현 파서가 장기/자동차/일반만 기대해 미스 (taxonomy correction box 참조)
- [ ] **코리안리** — 재보험사 LOB N/A, 영구 SKIP
- [ ] FY2024 LOB — 사업보고서에 존재 (감사보고서 X). 필요 시 fetch 대상 분리

### F18 — IR factsheet 정형화 (DART↔IR cross-validation 활성화)

Parser + gathering. Validation 룰 3개는 추가됨 (V1 in [`TODO_validation.md`](TODO_validation.md)); 활성화 대기.

- [ ] **Delivery 계약**: `data/ir/<period>/parsed/<KR>.json` 정형 JSON. Schema: [`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md) §1.4. 모든 값 억원
- [ ] **출발 cohort 9사**: 메리츠 · 삼성화재 · 현대 · KB · DB · 한화생명 · 삼성생명 · 미래에셋 · 동양
- [ ] IR 미공시 회사 (교보 · KDB · 외국계 · 카카오페이손해 등) auto-SKIP 명시
- [ ] 생보 `segment_insurance_income` 키 셋 (보장성 / 저축성 / 연금 / 변액 후보) 확정 필요 — validation V1 참조

### IFRS-NORMALIZE — 23-co full normalization (extend B3-UNIFY coverage)

- [ ] `row_aliases.yaml` 확장 (현재 PoC 930 / 2956 tagged)
- [ ] K-ICS sensitivity 잔여 empty FY2025_Q4 생보사 normalize

### KICS-IMG — image-only PDF manual OCR

- [ ] **KR0010 KB손해** rule 2 x2 (validation gate 잔여 RED 1건의 root cause)
- [ ] KR0079 미래에셋생명
- [ ] KR0080
- 정책: parser는 image-only PDF 만나면 escalate; OCR 즉흥 금지 ([claude-agent-parser.md](docs/agents/claude-agent-parser.md) §2.1)

---

## Done — recent (parser-scoped)

| ID | Task | Done | Notes |
|----|------|------|-------|
| ~~F11-WF~~ | Foreign-affiliate life 5사 waterfall-builder safe fixes | 2026-05-29 | Magnitude unit fallback by largest-magnitude stage / 직접 block always outranks ceded / 보고기간말 label + guarded net-row patch. 23-co zero regression |
| ~~F15-TE~~ | `<TE>` data-cell parser fix (the real F15 root cause) | 2026-05-29 | `csm_extractor._iter_tables_with_context` now recognizes `<te>` as a data cell. Recovered 한화 all 13Q, 교보 all quarters, 삼성화재 2025.2Q/3Q, 현대해상, 케이디비, 코리안리 |
| ~~F15-LEAF~~ | `find_csm_leaf_cols` 6-row multi-level header fallback | 2026-05-29 | Was only inspecting rows 0–2; now scans all header rows and maps 보험계약마진 to the right index |
| ~~F15-PICKER~~ | Picker hardening (consolidation filter + continuity all-candidates + FY-anchor) | 2026-05-29 | Exclude 관계기업/종속기업/요약재무정보/지분 tables; continuity searches all candidates not top-5; FY-anchor 45% guard with ≤35% fallback |
| ~~F15-SEG~~ | 삼성생명·미래에셋 product-segment column id + 압축 헤더 dedup | 2026-05-29 | `find_product_segmented_csm_cols` + `collect_current_product_blocks` + 7 safety gates. FY anchor: 삼성 13.08조 / 미래 2.08조 / 동양 2.54조. Per-product split (사망/건강/연금/저축/기타) now summed correctly; `소계`/`합계` no longer double-counted |
| ~~F16-RS~~ | Panel 5 sensitivity rowspan + header-aware parse | 2026-05-29 | `_band_sensitivity_columns` + `_extract_sensitivity_band` (rowspan-elided continuation rows inherit risk). Fixed 한화 / 교보 / 케이디비 / DB생명. 삼성생명 unchanged. **흥국생명은 별도 layout** → F16 잔여 |
| ~~F17-T1~~ | Tier1 (전사) 당기순이익 분해 — 10/10 손보 | 2026-05-30 | `scripts/build_net_income_breakdown.py` → `data/dart/viz/net_income_breakdown.json`. 매그니튜드 자동추론 + 보험손익+투자손익≈영업이익 일관성 + 자릿수 concatenation guard |
| ~~F17-T2v1~~ | Tier2 LOB 1사 (현대) → 4사 검증 (삼성화재 / 현대 / DB / 한화손보) | 2026-05-30 (b) | position-based 컬럼 식별 + rollforward 표 제외 + 보험수익(LOB) = max(합계행, 컴포넌트 합) + 단위 factor = Tier1 anchor + 연결 우선 |
| ~~NB-SAMSUNG~~ | Samsung Life 사망 NB CSM regex misparse fix | 2026-05-29 | rfind("사망") + cap-filtered `\d+\.\d+` scan. Death now [7.6, 10.0, 7.6, 7.2, 5.1] (was 520/471/488 absolute amounts read as multiples). Validation gate side is changelog_validation 2026-05-29 |
| ~~CSM-DECONTAM~~ | Panel 6 prior-period contamination + per-quarter new-business | 2026-05-29 | `pick_main_block._period_affinity` penalty for 전분기/전반기 + bonus for 당분기/당반기 (guarded for combined captions). `add_nb_increments` chains across unobserved quarters. 한화 2025.1Q 13,362,336 → 12,994,325 (caption "1) 당분기"); 0 regressions on FY28 |
| ~~CSM-CONT~~ | History builder continuity tiebreak (한화 2023.4Q dip) | 2026-05-29 | `rank_main_blocks` exposed + guarded 25%/5% continuity tiebreak. 한화 9.24조 → 13.30조; 롯데 2025.4Q 0.03→4.92조; 메리츠 2026.1Q 0.05→11.1조; 신한 14.7조 / 케비 3.4조. FY waterfall 0 regression |
| ~~IR-DISCLOSED~~ | 손보 disclosed/derived NB CSM 배수 (삼성화재 / DB / 한화손보 / 현대) | 2026-05-30 | 삼성화재 13Q disclosed (factsheet CSM sheet); DB 13Q derived (component-based, KIDI-consistent); 한화손보 DART numerator ~2x overstatement flagged (no multiple emitted); 현대 single-point |
| ~~IR-MULTIPLES~~ | `build_ir_disclosed_multiples.py` aggregation | 2026-05-30 | DISCLOSED_KEYS / DERIVED_KEYS 추가 → `data/ir/disclosed_csm_multiple.json` 9사 |
| ~~IFRS-A1~~ | Measurement rollforward extractor | done | 23/23 MVP |
| ~~IFRS-A2~~ | CSM amort schedule extractor | done | 23/23 |
| ~~IFRS-A3~~ | Insurance P&L extractor | done | 23/23 MVP |
| ~~IFRS-A4~~ | Reinsurance rollforward extractor | done | 23/23 MVP |
| ~~IFRS-B1~~ | BS snapshot extractor | done | 23/23 MVP |
| ~~IFRS-B5~~ | Sensitivity DART skim extractor | done | 23/23 MVP (PoC) |
| ~~IFRS-B5-KICS~~ | B5 K-ICS primary ingest | done | FY2025_Q4 13/23 nonempty, 30 tables. KR0073 4 + KR0069 3 after IFRS keyword MD reparse |
| ~~IFRS-B3-UNIFY~~ | B3 = section8 long-format normalizer | done | `src/ifrs17/row_normalizer.py` + `scripts/ifrs17_normalize_liability.py`; PoC 5 → `*_liability_normalized.json` (930/2956 tagged) |
| ~~IFRS-HIST~~ | Historical 13Q ingest 2023.1Q ~ 2026.1Q | done v2 | parser side: `scripts/ifrs17_promote_history_to_measurement.py` (294 → 293 ok). Combined with `<TE>` + leaf-col + picker fixes (F15 series), 257 ok + 2 partial + 34 no_csm + 5 err. 2026-05-29 v2 = prior-period decontamination + per-quarter new-business |
| ~~IFRS17-SEN-TABLE~~ | sensitivity heatmap panel table load | done | sensitivity_heatmap 14/23 ok |
| ~~KICS-PARSER-SPLIT~~ | Parser split-table + row scope fix | done | KR0005 FY2025_Q4 golden test |
| ~~KICS-REPARSE-Q4~~ | FY2025_Q4 parse refresh | done | parse 30/38 ok; JSON 10028→10454 |
| ~~KICS-KR0069~~ | Samsung Life all-quarters parser fix | done | bullet-section start patterns; 0 RED all 12 quarters |
| ~~KICS-KR0097~~ | Hana Life parse fix | done | RED 18→2 |
| ~~KICS-RED-FIX2~~ | User-verified RED pass 1 (parser-side fixes) | done | RED 419→311 (Rule 2 label/alias fixes, MetLife reverse, item4 reconcile) |
| ~~KICS-RED-FIX3~~ | Missing RED reparse + item27/28 recalc | done | RED 311→217 |
| ~~KICS-SUB~~ | Sub-items 29-35 parser | done | image-only KR0010/KR0079 → KICS-IMG (above, jurisdiction = parser escalate) |
| ~~KICS-POST~~ | `값_적용후` historical reparse | done | Auto-fill across periods |
| ~~KICS-RATIO28~~ | item28 basic-capital post-transition | done | 133 rows `값_적용후` |
| ~~KICS-HIST~~ | Historical reparse 9 periods | done | BATCH_END 2026-05-24T11:08:19Z |
| ~~UNIT-HINT~~ | Unit-hint mismatch auto-detect (parser) | done | 23 insurer-quarter latent bugs (3× ×100, 20× ÷100), 56 post values corrected. Rule 8_post pre/post bug fixed at parser layer |
| ~~B5-APPENDIX~~ | IFRS17 B5 K-ICS sensitivity appendix headings + multi-period batch | 2026-05-25 | `kics_sensitivity_extractor.py` recognizes appendix wording (보험위험 + 민감도 without contiguous 가정민감도); default `min_score=3`; `--all-periods` batch. 49 tables across 12 quarter folders; FY2025_Q4 11 insurers / 23 tables |

---

## Reading order for parser subagent

When invoked, read in this order:

1. This file (`TODO_parser.md`) — current state, in-flight decision points, taxonomy box
2. [`docs/changelog_parser.md`](docs/changelog_parser.md) — history (what prior sessions did)
3. [`docs/agents/claude-agent-parser.md`](docs/agents/claude-agent-parser.md) — master prompt + per-domain contract
4. Domain ref(s): [`docs/domains/claude-agent-{kics,ifrs17,misc}.md`](docs/domains/) for label variants and known company-specific quirks
5. Root [`TODO.md`](TODO.md) only for cross-stage items (F12 / F17 / F18) — full detail lives here

---

## Hand-off to validation

After parser produces a normalized JSON, validation is invoked per [`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md) §3 (retry loop, max 5). On RED, validation calls back the parser with the failing rule + suspected source.
