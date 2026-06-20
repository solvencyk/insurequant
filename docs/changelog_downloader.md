# Insurequant Changelog — Downloader Stage

> Last updated: 2026-06-16 · Stage 1/5 — downloader
> Prompt: docs/agents/claude-agent-downloader.md · TODO: TODO_downloader.md

**Scope:** data collection only — raw fetch from external sources (정기경영공시 / DART / FSC bonds / KIDI / IR factbooks).
**Cross-stage history:** `docs/claude-changelog.md` (parser/validation/gathering/pushing/refactor entries).
**This file:** entries scoped to downloader work only, extracted from the root changelog 2026-05-30.

Cross-stage entries that touch downloader as one phase but are primarily parser/gathering/viz (e.g. F11 foreign-affiliate viz integration, IR factsheet 전사 수집 + 손보 NB CSM 배수 파싱, F17 LOB parsing) remain in `docs/claude-changelog.md`. The compressed historical archive (pre-2026-05-25) also remains there.

## 2026-06-17 -- 전체 보험사 2026.1Q DART 분기보고서 + 교보 3개 분기 전기 추출용 raw

**전사 2026.1Q DART fetch** (`ifrs17_batch_historical --all --periods 2026.1Q`):
- 36사 전수 처리: ok 13사 / no_filing 13사(외국계·소형, 구조적) / no_csm_table_found 10사
- 모든 파일 `data/dart/FY2026_Q1/raw/<KR>_<회사명>/document.zip` + `xml/` 저장
- no_csm_table_found: 롯데·미래에셋·삼성생명·삼성화재·에이비엘·코리안리·한화생명·한화손해·현대해상·흥국화재

**교보생명(KR0073) 전기 추출용 3개 분기 raw** (`--pilot KR0073 --periods 2024.4Q,2025.1Q,2025.2Q`):
- 목적: 2023.4Q(←2024.4Q 전기), 2024.1Q(←2025.1Q 전기), 2024.2Q(←2025.2Q 전기) 복구
- 2024.4Q XML 구조 확인: 주석 17-4 등이 "1) 당기" / "2) 전기" 페어 테이블 구조, 전기 333회 출현
- 현재 `csm_extractor.py` period_type 필드 없음 → parser(ifrs17) 발주 `inbox/parser/20260617T1130Z`
- 주의: 2024.4Q에 소급재작성(retrospective restatement) 언급 있음 → 전기 테이블 해석 시 기록 필요

## 2026-06-17 -- 흥국화재 신종자본증권1 콜 미행사 fix + normalize 재실행

`normalize_bond_schedule.py` bug: "5y call assumed exercised" 규칙이 콜 미행사 채권을 잘못 분류.
- **흥국화재 신종자본증권1** (KR60005416C3, 920억, 2016-12-29 발행, call 2021-12-29) — FSC API에 정상 존재, normalize가 `effective_call_date(2021-12-29) <= today` 조건으로 `status=called` 오분류
- 2026.1Q FS appendix(parser `2026q1_per_bond.json`) 에서 920억 잔존 확인 → 실제 콜 미행사
- Fix: `scripts/normalize_bond_schedule.py` 에 `_CALL_NOT_EXERCISED = {"KR60005416C3"}` override 추가 (line 59-64)
- 재실행: `20260616T153258Z` stamp 생성 → KR0005 tier1_hybrid 3,200억 → **4,120억** (FS appendix 일치)
- `emit_bonds_provenance.py` 재실행 → `20260616T153258Z/bonds_provenance.json` 갱신
- `forward_capital_simulation.py` `_latest_bonds_dir()` auto-pick → 재실행 시 자동 반영

## 2026-06-16 -- 자본성증권 in-force per-bond DART fetch + provenance 사이드카 emission

publishing `inbox/downloader/20260616T1200Z`(in-force 자본성증권 FSC vs BS 괴리 해결) 처리.

**FSC API 조사 결과**: 6개 누락사(삼성생명·악사손해·KDB생명·하나손해·AIA·삼성화재) → FSC `GetBondTradInfoService_V2` 전수 0건. 사모발행(프라이빗플레이스먼트) 또는 외국계 모회사 자본 구조 → 공개 등록 없음.
**DART 주요사항보고서** B-type 조사: "자본으로인정되는채무증권발행결정" 공시 = KDB생명 3건·농협생명 4건·교보생명 2건(단 교보 전건 미발행 확인).
**현대해상 재진단**: FSC 4건(26,000억) 모두 2024~2025 신규발행 stale 아님 → FSC 정확, parser `subordinated_eok` 오파싱이 원인.

- **KDB생명 (KR0072)**: 신종자본증권 2건 — 2,160억(2023.05.19 issue, call 2028.05.19) + 250억(2024.12.26 issue, call 2029.12.26) = 2,410억. BS 신종 2,403억과 일치.
- **농협생명 (KR0104)**: 신종자본증권 2건 — 2,500억(2022.09.28, call 2027.09.28) + 2,500억(2022.12.26, call 2027.12.26) = 5,000억. FSC Face 5,000억과 일치.
- **교보생명 (KR0073)**: DART 2023 미발행(시장 불확실성). 별도 데이터 없음.
- **산출물**: `data/bonds/disclosure/2026q1_capital_securities.json` + `disclosure_bonds_provenance.json`
- **스크립트**: `scripts/fetch_capital_securities_dart.py`
- **publishing 핸드오프**: `inbox/publishing/20260616T1300Z` (FSC/DART per-bond 데이터 ready + 현대해상/농협생명 후순위 오파싱 parser 발주 권고)

**Phase 2 provenance 사이드카 emission** (owner `0616T1242Z` + validation `0616T1250Z`):
- `data/bonds/normalized/20260616T060817Z/bonds_provenance.json` (24개사, source_id=FSC_BONDS, as_of=2026-03-31, effective_filtered=true)
- `data/bonds/disclosure/disclosure_bonds_provenance.json` (2개사 DART supplement)
- 스크립트: `scripts/emit_bonds_provenance.py`
- 잔여: DART raw provenance(23사×13분기 source_file+as_of) = 다음 세션

## 2026-06-16 -- CSM 워터폴 연속성(전기 기말≠당기 기시) 복구용 DART raw 재취득 (33셀)

validation `inbox/downloader/20260616T0600Z`(owner: 2026.1Q 기시 CSM 전사 misparse, 정답=직전 2025.4Q 기말)
+ 사용자 지시("26.1Q 전부 말고 5사 먼저, 24.4Q/25.1Q는 continuity break만"). `data/dart/FY2026_Q1/`는
git-purge로 통째 부재(0 dirs) → 재추출 불가 → DART 재취득. `ifrs17_batch_historical.py --skip-extract`(fetch-only).

- **우선 5사 2026.1Q**: 교보(KR0073)·메리츠화재(KR0001)·신한라이프(KR0094)·에이비엘(KR0070)·푸본현대(KR0083) = 5/5.
- **continuity 전수 점검**(`validate_csm_continuity.py`): break는 **24.4Q/25.1Q 경계 아님** — 실제 = 코리안리
  2023.4Q기말 8032≠2024.1Q기초 10641(Δ32.5%) FY경계 + FY2023 기초드리프트(현대·에이비엘·KDB·교보) +
  FY2024 드리프트(KB라이프·코리안리). → **FY2023 Q1-Q4**(현대·에이비엘·KDB·교보·코리안리, 20셀) +
  **FY2024 Q1-Q4**(KB라이프·코리안리, 8셀) 동반 재취득.
- **합계 33/33 fetched, CSM 블록 결손 0**(보험계약마진 48~382 전수 존재). 회사명 검색(영구매핑 없음).
  Q4=사업보고서(A001)·Q1-3=분기/반기. raw gitignore(origin/data 재팽창 아님 — 원천 DART 신규 fetch).
- **핸드오프**: parser/ifrs17 raw-ready(`inbox/parser/20260616T0640Z`, continuity 진단표+owner 정답값 포함).
  파서 재추출 → 2026.1Q 기시=2025.4Q 기말 정상화 + 드리프트/경계 수렴 → `validate_csm_continuity.py` RED 수렴.
  ⚠️ 마스터 rebuild은 복원분+기존 raw 범위 내(전체 부재 시 파괴적). status: resolved, `_resolved/` 이동.

## 2026-06-16 -- 자본성증권 발행현황 검증·수정 (owner 0506Z #2 선제) — registry bare-stem 오수집 fix

owner `inbox/parser/20260616T0506Z` #2(K-ICS tier 패널 신뢰도 점검 — 발행현황 크롤링 검증, data.go.kr
`15059611`)를 downloader가 선제 수행(조건부 바운스 대기 대신). **live 데이터 대체로 정확하나 실오수집 1·누락 1 발견·수정.**

- **근본원인**: `src/solvency/downloader/{nonlife,life}_insurer_registry.yaml`의 **짧은 그룹 약칭**이 FSC bond
  API substring 쿼리로 나가 계열사 채권을 보험사로 오태깅. `--max-pages` 키우자 메리츠 1.77조→**19.6조**,
  iM라이프 0.27→10조, 미래에셋 0.3→9.2조 폭증(메리츠캐피탈/증권/지주, 아이엠뱅크, 미래에셋증권 등).
- **수정**: bare-stem alias **4개 제거** — `"메리츠"`(KR0001)·`"아이엠"`(KR0076)·`"미래에셋"`(KR0079)·
  `"카카오"`(KR1098). specific 약칭은 유지. IBK/AIG/AXA/처브/푸본은 영문스템/고유명이라 무오염 확인(미수정).
- **재크롤+정규화**(clean: raw `20260616T060238Z` / normalized `20260616T060817Z`, as_of 2026-06-16):
  - **24사 중 22사 live 5/25와 동일** → big-3 Face는 live가 정확했음(page-cap이 deep 오염 우연 차단).
  - 🔴 **KR1098 카카오페이 3,202억→0**(live가 카카오 그룹 채권을 가짜로 적재; 카카오페이손보 자본성증권 미발행).
  - 🟢 **KR0099 KB라이프 0→1,200억**(live가 놓친 진짜 신종자본/후순위; 사명 전수 검증).
  - 🟡 KR0011 DB손해 −890억(3주 정상 call/만기 delta).
- **함의**: big-3 Face 정확 → owner T2 BS −11.6%는 **Face(downloader) 아님 → BS시가(parser #1)** 주원인 추정.
  단 KR1098 tier 패널은 0 반영 필요. clean normalized = `_latest_bonds_dir` auto-pick, 오염 intermediate 제거.
- **핸드오프**: parser-kics `inbox/parser/20260616T0615Z`(검증결과+수정+#1 BS시가 포인터). 재빌드는 publishing/parser gate.

## 2026-06-16 -- NB CSM 시계열 오염 복구용 interim DART raw 재fetch (10사 × 3분기, fetch-only)

parser/ifrs17 발주(`inbox/downloader/20260616T0400Z`; validation `20260616T0230Z`가 DART CSM_waterfall
partial 추출이 NB CSM YTD 시계열 오염 확정 — 롯데 2025.2Q YTD→0 등). git-purge로 해당 분기 raw 부재 →
파서 재추출 불가 → downloader가 반기/분기보고서 본문 raw 재취득.

- `scripts/ifrs17_batch_historical.py --skip-extract`(**fetch-only**; 파괴적 `build_csm_waterfall_master.py`
  미실행 — 발주 경고 준수) → **10사 × {2025.2Q 반기·2025.3Q 분기·2023.1Q 분기} = 30셀, 30/30 fetched.**
  대상: 롯데(KR0003)·미래에셋(KR0079)·한화생명(KR0068)·현대해상(KR0009)·삼성화재(KR0008)·DB손해(KR0011)·
  동양(KR0087)·코리안리(KR1000)·한화손해(KR0002)·흥국화재(KR0005). 회사명 검색(영구매핑 없음).
- canonical `data/dart/FY{Y}_Q{n}/raw/KR####_<canonical>/document.zip(+meta.json)`. raw gitignore.
- **CSM 블록 검증(zip 본문 보험계약마진 count): 29/30 존재** → 재추출 가능. 우선 7셀 전부 OK
  (롯데 2025.2Q NB=0.0 최악건 포함). **🔴 honest gap 1**: 롯데 2023.1Q(20230515002687) 보험계약마진 0
  (도입초 분기보고서 §14 축약 추정, 소스 부재; 우선셀 아님) → census whitelist 권장.
- **핸드오프**: parser/ifrs17 raw-ready(`inbox/parser/20260616T0420Z`, rcept·키워드 표 포함). 파서가
  `ifrs17_batch_historical.py` extract 모드로 재추출 → validation `check_nb_csm_history.py` 수렴 확인.
  마스터 rebuild은 raw 전체 복원 세션에서(이번 interim은 부분 rebuild 금지). status: resolved, `_resolved/` 이동.

## 2026-06-16 -- 예별손해(KR0004, 구 MG=엠지손해) DART 연간 감사보고서(별도) FY2023~FY2025 적재

위 K-ICS 11분기 건의 후속(owner): "예별/MG DART 공시도 전기간 받았나? 비상장이라 없으면 회기말 감사보고서라도."
조사 결과 **KR0004는 DART 데이터 통째로 0** — 비상장 손보사라 정기보고서(A) 미제출 → IFRS17 DART
universe(`src/ifrs17/universe.py`) 어느 리스트에도 부재. 단 외부감사법 주식회사라 **연간 감사보고서(F)** 제출.

- **DART entity = '엠지손해보험'**(corp_code `00962861`; 신규 '예별손해보험' `01974696`은 filing 0건).
  회사명 검색으로 감사보고서 8건 발견(별도/연결 × 2022~2025).
- **owner 스코프**: **별도만·FY2023~** (IFRS17 effective 2023; FY2022=IFRS4 제외, 연결 제외 —
  `build_csm_waterfall_master`는 별도 00760 사용). 8건 중 **3건 보존**, 5건(FY2022 별도/연결, 각 연결) 제거.
- 적재(5 audit-only 외국계 생보사와 동일 경로·레이아웃): `data/dart/FY<year>_Q4/raw/KR0004_엠지손해보험_<rcept>/`
  = `document.zip` + `<rcept>_00760.xml`(별도). FY2023=20240408000665 · FY2024=20250408000587 · FY2025=20260406003175.
- **IFRS17 주석 확인**(별도 키워드 카운트): 보험계약마진 36~59 · 보험료배분접근법 31~37 · 신계약 6~9 →
  CSM waterfall 추출 가능. 소형 PAA-heavy 손보사라 신계약 CSM 얇음(예상).
- 재현 스크립트 `scripts/fetch_kr0004_mg_dart_audit.py`(FILINGS=3 별도) + probe `scripts/_probes/_kr0004_dart_probe.py`.
- **핸드오프**: parser/ifrs17 raw-ready(`inbox/parser/20260616T0210Z`). 파서가 CSM/PL 추출 → 마스터 KR0004 라인 병합.
  raw는 gitignore(git 재팽창 무관).

## 2026-06-16 -- 예별손해(KR0004, 구 MG) 과거 11분기 K-ICS 정기경영공시 raw 전수 적재

parser(kics lane) → downloader bounce(`inbox/downloader/20260616T0055Z`, owner round3 K2):
예별 K-ICS가 26.1Q 1분기만 적재 → 그 이전 = 구 MG손해 명의. 사명변경 매핑해 과거 분기 시계열 병합.
파서 조사: kics_disclosure.json KR0004=2026.1Q 단건, 디스크 raw=FY2025_Q4+FY2026_Q1만 →
**2023.1Q~2025.3Q 11분기 raw 자체 부재** → downloader fetch.

- **소스 = 회사 자체 정기경영공시 페이지** `yebyeol.co.kr/PB021010DM.scp?menuId=MN0802001`
  (예별=구 MG 동일 법인). 이 페이지에 **2013~2026 전 분기 아카이브**가 한 화면에
  `<a id="quarter{N}_{YYYY}" href="javascript:fn_download(ID)">`로 노출. 매핑: quarter1→Q1 ·
  quarter2(상반기/반기보고서)→Q2 · quarter3→Q3 · quarter4(결산/연간)→Q4.
- **kpub.knia.or.kr(손보협회 통합공시)는 무용**: 결산(Q4)만 carry + MG/예별 row 자체 부재
  (`backfill_nonlife_disclosure_kpub.py` NAME_TO_KR에 KR0004 없음) → 회사 사이트가 유일 소스.
- **11/11 OK, 결손 0** (서울보증식 honest gap 없음). 회기말 Q4 2개(2023·2024 결산) 포함 전수.
- **구 MG 명의 확정**: 결산 ZIP 내부 본문 파일명 = "[엠지손해보험] 2023년 결산 경영공시 최종.pdf" /
  "2024년 엠지손해보험 현황_F.pdf" → 동일 법인 과거 공시. ZIP은 감사/재무제표 동봉 → 룰대로
  **경영공시 본문 PDF만** 추출(`extract_disclosure_pdf` kpub 로직 재사용).
- **text-layer 전수 OK**(6p 텍스트 1.9k~3.3k자, 지급여력·경과조치·K-ICS 키워드 존재) →
  **OCR 불필요**, docling 바로 가능. scan-only 아님(OCR-MARKETRISK 류 함정 회피).
- 파일명 `KR0004_예별손해보험.pdf`(기존 stem 컨벤션, parser glob `KR0004_*` 매칭).
  기존 FY2025_Q4·FY2026_Q1 미변경 → KR0004 = **2023.1Q~2026.1Q 13분기 연속** 확보.
  raw는 gitignore → git 재팽창 무관.
- 신규 스크립트 `scripts/backfill_kr0004_mg_quarters.py`(재사용; TARGETS만 수정해 타 분기 추가) +
  probe `scripts/_probes/_yebyeol_disclosure_probe.py`(2013~ 전 분기 fn_download ID 매핑).
- **핸드오프**: parser/kics raw-ready(`inbox/parser/20260616T0145Z`). 파서가 docling MD →
  core items 1-28 추출 → kics_disclosure.json 예별 시계열 병합 + 게이트 census 확장.
  status: resolved, `_resolved/` 이동.

## 2026-06-15 -- IFRS17 CSM 민감도 FY2025 raw 28사 전수 적재 (sensitivity FY2024→FY2025 갱신용)

owner 요청(`inbox/downloader/20260615T0435Z`): 사이트 CSM 민감도가 FY2024(24.4Q)에 고정 → 전 IFRS17
대상사 FY2025 사업/감사보고서 raw 다운로드(파서가 sensitivity 재추출). universe = DART sensitivity JSON
보유 28사(`data/dart/extracted/<canonical>_<rcept>_sensitivity.json`; `KR####_FY..._kics`=별개 K-ICS 분기 민감도라 제외).

- **fetch**: 회사명 검색(영구매핑 금지) → `/api/list.json` FY2025(2026-03~04 제출) 사업보고서(23 listed) +
  감사보고서(5 audit-only: 라이나·메트라이프·AIA·하나생명·처브) → `/api/document.xml` fetch+extract →
  canonical `data/dart/FY2025_Q4/raw/<KR>_<name>_<rcept>/`. **32 filings, 28/28 공시, 실패 0, 미공시 0.**
  raw-only(추출은 파서). data/dart raw는 gitignore → git 재팽창 무관(신규 HTTP fetch).
- **네이밍**: 전부 `KR####_` prefix 통일. KB라이프·코리안리는 kics명↔DART명 불일치로 annual_raw_dir가
  corp_code prefix(`00160393_`/`00113191_`)로 떨궈서 → `KR0099_`/`KR1000_`로 정정(G8 AIG와 동일 패턴).
  하나생명·AIA는 G8에서 받은 것 idempotent 재확인.
- **파일럿 흥국생명**(KR0071_흥국생명보험_20260331004251) raw sanity: 민감도 25·사망률 8·보험계약마진 114.
  리터럴 "장해질병"/"실손"=0이나 장해6·질병6·정액19 존재 → 라벨 변형(파서 추출에서 확인, 다운로드 갭 아님).
- **핸드오프**: parser/ifrs17 raw-ready(`inbox/parser/20260615T0520Z`). 파서가 sensitivity 재추출 +
  흥국생명 부호/행 파일럿 검증 → heatmap 재빌드. status: resolved, `_resolved/` 이동.

## 2026-06-15 -- 서울보증(KR0150) 8분기 raw 부재 재바운스 — 구조적 honest gap 재확인 (refetch 불가)

parser(kics lane, docling census) → downloader: 서울보증 8분기 disclosure raw 부재로 refetch 요청
(`inbox/downloader/20260615T0100Z`). **신규 누락 아님** — 요청 8분기(2023.Q1-3·2024.Q1-3·2025.Q2-3)가
`audit_all_periods.py:39-43` `SGI_QUARTERLY_STRUCTURAL` 집합과 정확히 일치. 2026-06-01 NONLIFE-Q123에서
이미 probe·판정·등록 완료. 사유: SGI 공시실(sgic.co.kr SPA)은 연간+최신분기만 보존(과거 롤오프) +
DART 미상장(IPO 철회) → 양쪽 미취득, 사용자 결정("걍 버려")=won't-fix. → census expected-absent로 처리하라
회신(파서 census가 `SGI_QUARTERLY_STRUCTURAL`+`DART_DROP` 예외표 참조 권장). status: resolved, `_resolved/` 이동.
다운로더 액션 없음(물리적으로 받을 원천 부재). present raw = 2023.4Q·2024.4Q·2025.1Q·2025.4Q·2026.1Q.

## 2026-06-14 -- G8: NB CSM배수 25.4Q 누락 3사 — FY2025 감사보고서 raw 복원 (추출은 parser로 라우팅)

owner QA(G8, `inbox/downloader/20260614T0712Z`): index.html CSM배수가 AIG(KR0029)·카카오페이손해
(KR1098)·하나생명(KR0097)에서 2025.4Q 누락 → 24.4Q fallback. inbox 프레이밍은 "DART refetch 3건"이었으나
**진단 결과 단순 refetch 건이 아니었음.**

- **원인 분리**: NB CSM배수 분자(신계약 CSM)는 `CSM_waterfall.json` 항목2(=파서 마스터) → 다운로더 산출물
  아님. 3사 FY2025 감사보고서 raw가 working tree에서 사라져 있었음(추출 후 정리/purge 추정; data/dart raw는
  gitignored). 인벤토리 `_inventory_manifest.json`(raw_annual)이 rcept를 기록 중이라 라이브 DART 재취득 가능.
- **복원(downloader 액션)**: 라이브 `/api/list.json`(회사명 검색, 영구매핑 없음) → FY2025 감사/연결보고서
  rcept 확정 → `/api/document.xml` fetch + extract, canonical `data/dart/FY2025_Q4/raw/<KR>_<name>_<rcept>/`:
  - KR0029 AIG: `20260407002104`(별도) + `20260407002109`(연결). annual_raw_dir가 kics명 "AIG손해보험" ↔
    DART명 "에이아이지손해보험" 불일치로 corp_code prefix(`00983606_`)로 떨궈서 → **빌더 글롭 `KR0029_*`에
    걸리도록 `KR0029_` prefix로 리네임 정정.**
  - KR1098 카카오페이: `20260323001537`(별도). KR0097 하나생명: `20260325000201`(별도)+`000202`(연결).
  - 검증: 보험계약마진 26~55회/신계약 3~12회 (IFRS17 본문 OK).
- **추출 스모크(read-only, 마스터 미변경)로 진짜 원인 확정** → 파서 이슈:
  - AIG: 신계약CSM=986,825.6억(≈2000배 과대, 롤포워드는 닫힘) magnitude/table misparse. (과거 FY2024=443.8)
  - 카카오페이: 신계약CSM=20,187.6억(현 마스터 stale값과 동일 → 이전 빌드도 같은 표를 같은 방식으로 읽음).
    배수는 build_nb_csm_multiple `_MULT_CAP=40`이 정상 null 처리 중.
  - 하나생명: build-waterfall 경로 no blocks → AUDIT_REPORT_ANNUAL이라 `ifrs17_ingest_audit_annual.py`
    (extract_csm_tables) 경로 필요(2024.4Q=3240.3이 그 산물).
- **핸드오프**: parser/ifrs17 inbox에 route:reparse 작성
  (`inbox/parser/20260614T1330Z__downloader__MULTI_2025.4Q__nb_csm_fy2025_raw_ready.md`).
  파서가 magnitude 교정 + 하나생명 audit-annual ingest → CSM_waterfall 재빌드 → build_nb_csm_multiple 재실행.
- G8 원 스레드 → `_resolved/` 이동(status: resolved). downloader 잔여 액션 없음.
- **미결(별개)**: `20260614T1232Z` qa_residual item(2) — KB/한화손해 2023.4Q 금리위험·카카오 2025.4Q
  시장위험 스캔-only(텍스트레이어 없음) OCR. downloader OCR 경로 부재 → owner 결정 대기, 메시지 open 유지.

## 2026-06-09 -- AIA 식별자 마이그레이션: 리터럴 "AIA" → KR0080 (코드+데이터 코디네이션)

AIA생명(에이아이에이생명보험)은 kics_disclosure 로스터에 없는 audit-only 외국계라 일부 스크립트가 코드 대신 리터럴 `"AIA"`를 식별자로 써왔고 → `AIA_*` 파일/폴더가 KR####_ 컨벤션을 깨고 있었음. KR0080은 이미 registry/_dart_path_helpers/_kr_map 등에서 AIA 정본 코드라, 누락분을 KR0080으로 통일.

- **코드 4스팟**(식별자로 쓰던 곳만): `ingest_kidi_monthly_premium.py:71` 키, `crawl_assoc_nb_premium.py:66` 키, `report_collection_status.py:68/123/142` 로스터 → `"AIA"`→`"KR0080"`.
- **유지(건드리면 안 됨)**: `ifrs17_find_missing.py`(=DART corp-name 검색 쿼리), `extract_dart_zips.py` INSURER_PREFIXES(백워드-compat), `audit_all_periods.py` alias, `one_off_reorg2_canonical.py`(1회성).
- **데이터 17경로 리네임** `AIA_`→`KR0080_`: KIDI 13(`data/kidi/FY*/raw/AIA_<yyyymm>.json`) + DART raw 3폴더(FY2024_Q4·FY2025_Q4) + disclosure 1(FY2026_Q1). `_archive`는 제외.
- **파생 JSON 코드필드** `"AIA"`→`"KR0080"` (JSON-aware, 이름 보존): premium_summary 13 + kidi_life_premium 13 + nb_csm_multiple 1.
- **검증**: `report_collection_status.py` exit 0, AIA→KR0080 "전체자료 입수 완료"; `_archive` 외 AIA_ 잔여 0; 파생 JSON bare "AIA" 0. 네트워크 크롤 미실행.
- **주의**: 데이터만 리네임하면 ingest가 "AIA" 키로 읽어/써서 깨짐 → 코드+데이터 동시 변경이 필수였음.

## 2026-06-04 -- KIDI 신계약 월납초회보험료 FY2026_Q1(202603) 재수집

사용자 재확인 요청 → 라이브 KIDI INCOS 엔드포인트 probe 결과 **2026.1Q(202603)이 그새
발표됨** (5/31 fetch 시점엔 항목 라벨만 있고 ITEM_VAL 비어있던 게, 이제 값 채워짐).
3개 크롤러 풀 리빌드(전 기간, 202603 포함):
- `crawl_kidi_life_premium.py` → `kidi_life_premium.json`: 264 → **286 records** (생보 22사 × 202603 추가)
- `crawl_kidi_longterm_premium.py` → `kidi_longterm_premium.json`: 184 → **200 records** (손보장기 16사)
- `ingest_kidi_monthly_premium.py` → raw per-company + `premium_summary.json`: **507 entries** (39사×13), errors 0

검증(202603 월납초회 실측): 삼성생 739.63억 / 한화생 621.18억 / 교보생 390.7억 /
삼성화재 455.89억 / DB손 417.66억 / 메리츠손 348.33억 / 현대손 298.75억. 전부 1Q 누계로 정합.

`audit_all_periods.py`: `KIDI_NOT_RELEASED`에서 FY2026_Q1 제거(빈 set) — 이제 실제 체크해도
KIDI REAL GAPS **0**. → KIDI 13분기 전수 수집 완료(구조적 0: 코리안리(재보험)·서울보증(보증, 미매핑)).

## 2026-06-04 -- 한화생명(KR0068) 분기 IFRS17 본문/별첨 확인 (parser 질의)

파서가 한화생명 분기 Tier-1 NO 보고 ("분기/반기보고서가 요약재무정보만 노출, 보험손익 분해
IFRS17 표 미수록(포맷 상이)") → downloader에 본문 vs 별첨 확인 요청.

**확인 결과: 전부 본문(body XML)에 있음. 별첨 아님. 재다운로드 불필요.**
- 분기 dir 구조: 단일 main XML(`<rcept>.xml`), document.zip 멤버도 1개뿐 (연간과 달리
  `_00760`/`_00761` 별첨 없음). 즉 받을 추가 문서 자체가 없음.
- 본문 term-scan (FY2025_Q1 분기, 4.9MB/913 tables): 보험수익=80, 보험서비스비용=68,
  보험금융=86, 보험계약마진=117, 보험서비스=112, 포괄손익계산서=11회, 영업부문=7.
  반기(Q2)·연간은 더 풍부. → IFRS17 보험손익 분해 데이터는 본문에 물리적으로 존재.
- 파서가 "요약만"으로 본 이유: 본문 **헤드라인 포괄손익계산서가 레거시 요약 워터폴**
  (매출액/영업이익/법인세차감전순이익/당기순이익/기타포괄손익) 포맷이라 first-match가 이걸 잡음.
  실제 IFRS17 보험손익 분해는 본문 뒤쪽 상세표/주석에 있고, 표준 `<TABLE>/<TD>`가 아닌
  비표준 markup(`<TE>` wide-table 또는 서술형 추정)이라 추출이 어려운 것 → **파서측 매칭 이슈**,
  다운로드 갭 아님. (한화생명 1사 한정, 파서 세션이 보류 중인 항목과 일치.)

## 2026-06-03 -- DART document.zip 미추출 수정 (parser raw_not_extracted unblock)

파서 세션이 `status=raw_not_extracted`(document.zip만 있고 본문 XML 없음)을 보고.
원인 + 수정:

**원인 (2가지 결합):**
1. 해당 dir들은 fetch-only 단계에 남아 있었음 — `document.zip`는 받았으나 unzip(extractall)이
   실행 안 됨. (batch 스크립트의 추출 로직 자체는 정상 `extractall`; --skip-extract 실행분이거나
   Reorg #2가 미추출 dir을 그대로 옮긴 케이스로 추정.)
2. 비상장·외국계 보험사의 공시는 standalone 감사보고서라 zip 내부에 main `<rcept>.xml`이 없고
   `<rcept>_00760.xml`(연결)/`_00761.xml`(별도)만 들어있음 → main xml만 찾는 점검은 "빈 dir"로 오판.
   IFRS17 공시(보험계약마진/포괄손익/부문)는 이 _0076x 멤버 안에 그대로 존재.

**수정:** 신규 `scripts/extract_dart_zips.py` — idempotent. `data/dart/FY*_Q*/raw/*/document.zip`를
스캔, 본문 xml(`*.xml`/`xml/*.xml`/`extracted*/*.xml`)이 없는 dir만 in-place로 extractall (메리츠 등
정상 dir과 동일 레이아웃). 보험사 prefix(KR / AIA)만 대상; 지주(corp_code) dir은 제외(--include-all로 포함).
네트워크 재다운로드 없음 — 이미 받아둔 zip을 풀기만.

**결과:** 보험사 dir 42개 추출(46 xml members), idempotent 재실행 0건. parser 좌표 기준
bucket A(zip有/xml無) 40 → **0**. spot-check: AIG `_00760` 보험계약마진=55, AIA=49, 메트라이프=124.
기존 파서가 `*.xml` glob으로 자동 인식 → raw_not_extracted 해소 예상(파서 측 코드 변경 불필요).

**부수 발견 (별개 이슈, bucket C = 빈 dir/zip無 121건):** 110건은 비상장사 Q1-3 = DART 분기보고서
구조적 미제출(정상, gap 아님). 11건은 비상장 11사의 **FY2023_Q4 연간 감사보고서 미다운로드**(이들의
FY2024_Q4·FY2025_Q4는 위에서 추출 완료). 비상장 감사보고서 fetch 여부는 사용자 결정 사항(과거
"비상장사 감사보고서 불필요" 결정 ↔ parser의 PL/CSM 요청 충돌) → 사용자에게 질의.

## 2026-06-02 -- Housekeeping: archived early IR auto-discovery probes

Archived `scripts/_probes/` (45 files, ~2,600 lines) to
`data/_archive/20260602T150745Z_downloader_ir_probes/_probes/` (git rename, not
deleted; README in that dir maps each probe family to its canonical replacement).

These were exploratory DOM-inspection / URL-discovery scripts from the early
"find and download everything yourself" IR phase (iterative `_*_probe`,
`_*_probe2` ... `_hi_ir_probe11`). They learned each insurer's IR board / click /
download mechanism but never wrote into the data tree; the working recipes were
folded into the config-driven `scripts/crawl_ir_*.py` crawlers (kept). Verified
nothing imports `_probes` and no doc references it; `report_collection_status`
still imports clean after the move. Kept (not deleted) as reference for onboarding
foreign insurers later.

Not touched: `scripts/dl_lotte_ir.py` — a clean but superseded one-off (Lotte
only, replaced by `crawl_ir_lotte_koreanre.py`). Flagged for the user to decide;
left in place.

## 2026-06-01 -- NONLIFE-Q123 종료: 손보 6사 분기공시 26셀 backfill (자체사이트)

손보 6사 분기(Q1-Q3) 정기경영공시를 각 사 자체사이트에서 사별 병렬 에이전트로 수집. 34셀 중 **26셀 수집, 8셀(서울보증) 구조적 미발행** → disclosure 실질 gap **0**. 무결성 2,041/2,041 OK, audit disclosure REAL GAPS 0.

신규 스크립트(사별): `scripts/backfill_q123_{aig,axa,shinhanez,sgi,koreanre,kakaopay}.py`. 저장: `data/disclosure/FY{Y}_Q{N}/raw/KR####_<name>.pdf` (기존 네이밍 일치).

사별 결과·사이트 구조:
- **AIG손해(KR0029)** 9/9: 사이트 cadence = `1분기/상반기/3분기/결산` (**별도 2분기 없음** → 상반기 누적으로 Q2 채움). list page `dpwom012.html?curPage=N`에 제목 anchor 옆 직접 다운로드 href(`downLoadFiles.do?fileId=`) — detail page 불필요.
- **악사(KR0049)** 4/4 (FY2023 Q1·Q3, FY2025 Q1·Q3): 표가 **FY행 1개 + 분기별 td 셀** 구조 → 셀별 `N/4분기` 라벨로 매핑(naive "행첫 a"는 Q1만 잡힘). 전체(결산)셀은 ZIP.
- **신한EZ(KR0051)** 4/4 (FY2023 Q1-Q3, FY2024 Q1): 카디프→신한EZ 개명에도 FY2023 풀 보존(페이지네이션 목록). Q2 라벨 = "상반기".
- **서울보증(KR0150)** 0/8 = **구조적 미발행**: SPA(`CCGIRI010101F01_listTmpl`)가 **연간 경영공시 + 최신 1분기만** 노출(과거 분기 롤오프), DART 미상장 → 양쪽 모두 미수집 불가. audit에 `SGI_QUARTERLY_STRUCTURAL` 예외 등록.
- **코리안리(KR1000)** 6/6 (FY2024·FY2025 Q1-Q3): `ir_03_1.asp` 단일 표에 전 연도 행, 셀 href가 직접 PDF(`/pdf/gyungyoung/<year>_<q>.pdf`). 파일 stem `KR1000_코리안리.pdf` 사용.
- **카카오페이(KR1098)** 3/3 (FY2024 Q2, FY2025 Q2·Q3): 정적 SPA 표 직접 href. 정정/KICS포함본 우선(FY2024_Q2는 5.1MB KICS본). Q2=상반기.

**Parser 핸드오프**: AIG/신한EZ/카카오 FY{Y}_Q2 = 반기(상반기) 누적(1.1~6.30), standalone 분기 아님 — validation에서 누적-반기로 해석 필요. (TODO_downloader Status에도 기재.)

서울보증 DART 8셀(`SEOULBO-DART`): 사용자 결정("걍 버려")으로 **drop (won't-fix)**. 미상장(IPO 철회) → DART 미공시 = 구조적. audit `DART_DROP` 등록 → **전 source REAL GAPS 0** 달성.

## Archive (pre-2026-06) — 2026-05-25 → 2026-05-31 (FY2026.1Q 수집 + Reorg)

> 1줄 요약. 전문은 git log/blame. 회사별 URL/XPath 정본은 source-catalog.yaml.

- 2026-05-31 (O~S) -- 데이터 수집 완결: 전수 audit + disclosure 28셀 backfill
- 2026-05-30 (N) -- DART batch script canonical-path refactor
- 2026-05-30 (M) -- File-integrity 검사기 + 현대해상 IR 재다운로드
- 2026-05-30 (L) -- Collection-Status Report step + 양식 추가
- 2026-05-30 (j) -- Reorg #2: DART/KIDI/assoc 마저 정리 (canonical 일관 적용)
- 2026-05-30 (i) -- Downloader workflow 정리 완료 (5 source audit + canonical reorg + master prompt)
- 2026-05-30 (h) -- DART raw 100% audit + gap fill (KPI "전부 다 성실하게" 달성)
- 2026-05-30 (g) -- DART 별첨 fetch 진단 철회 (본문에 다 있음, 회사별 라벨 변형 처리 필요)
- 2026-05-30 (f) -- FY2026.1Q 생보 22사 경영공시 일괄 다운로드 완료 (세션 file ingest A-Z 마무리)
- 2026-05-30 (e) -- FY2026.1Q IR 자료 13 source 다운로드 완료 + 한화손보 IR mis-classified 정리
- 2026-05-30 (d) -- FY2026.1Q 손보 17사 경영공시 PDF 다운로드 완료
- 2026-05-30 (c) -- F2 v3 KIDI ML01/MN07 crawler DONE — NB CSM 분모 6→328 entries, computed multiple 6→27/28
- 2026-05-25 -- IFRS17 historical 13Q ingest + CSM 시계열 panel (push #2)
- 2026-05-25 -- Bond tier `(신종)` fix + FSC bond normalize refresh

---

## Compressed historical archive (pre-2026-05-25)

The compressed one-liner archive in root `docs/claude-changelog.md` ("## Historical archive (compressed)") contains a few downloader-relevant lines, kept inline there for compactness:

- FSC bond ingest client `src/bonds/` + `scripts/ingest_fsc_bonds.py` (MISC-BOND-INGEST)
- FSC schedule API per-insurer full pull: 1720 rows / 19 insurers
- Bond calendar v3: 5y Call rule for ALL bonds, 3-status outstanding/called/matured
- FSC schedule API 15059611 [승인] confirmed

These remain in the root changelog rather than being re-extracted, since they're already condensed.
