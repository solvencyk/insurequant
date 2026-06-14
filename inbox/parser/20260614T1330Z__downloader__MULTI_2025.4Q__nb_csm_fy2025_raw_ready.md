---
from: downloader
to: parser
created: 20260614T1330Z
status: open
route: reparse
company: KR0029, KR1098, KR0097
period: 2025.4Q
rule: NB_CSM_MISSING_LATEST_Q
lane: ifrs17
iter: 1
---

## 미결 (downloader 작성) — FY2025 raw 복원 완료, 추출은 파서 몫

원 건: `inbox/downloader/20260614T0712Z__owner__MULTI_2025.4Q__nb_csm_multiple_latest_quarter.md` (G8).
owner QA: index.html CSM배수가 AIG·카카오페이손해·하나생명에서 2025.4Q 누락 → 24.4Q fallback.

**downloader 진단 결과: 단순 refetch 건이 아니라 파서 추출 이슈였음.** 3사 FY2025 감사보고서 raw가
working tree에서 사라져 있어(추출 후 정리/purge 추정) 일단 라이브 DART에서 재취득해 canonical 위치에
복원했음. 그러나 read-only 추출 스모크(build_csm_waterfall_master.waterfall_for_dir) 결과,
**raw는 멀쩡하고 추출 단계에서 깨짐**. 회사별로 다름:

### 복원된 raw (검증 완료, IFRS17 본문 키워드 OK)
- `data/dart/FY2025_Q4/raw/KR0029_에이아이지손해보험_20260407002104/` (별도 `_00760`, 보험계약마진 55)
- `data/dart/FY2025_Q4/raw/KR0029_에이아이지손해보험_20260407002109/` (연결 `_00761`)
- `data/dart/FY2025_Q4/raw/KR1098_카카오페이손해보험_20260323001537/` (별도 `_00760`, 보험계약마진 26)
- `data/dart/FY2025_Q4/raw/KR0097_하나생명보험_20260325000201/` (별도 `_00760`, 보험계약마진 43)
- `data/dart/FY2025_Q4/raw/KR0097_하나생명보험_20260325000202/` (연결 `_00761`)
- (AIG는 kics명 "AIG손해보험" ↔ DART명 "에이아이지손해보험" 불일치로 annual_raw_dir가 corp_code
  prefix로 떨어졌던 것 → `KR0029_` prefix로 리네임해 빌더 글롭 `KR0029_*`에 걸리도록 정정함.)

### 회사별 추출 진단 (별도 _00760 기준)

1. **KR0029 AIG** — `waterfall_for_dir`가 추출은 하나 **신계약CSM=986,825.6억 (≈2000배 과대)**.
   롤포워드는 닫힘(기초 922,678.5 + 신계약 986,825.6 + 이자 45,812.8 − 가정 904,205.6 − 조정
   123,036.3 = 기말 928,074 ≈ 928,075). src=`combined-agn`. → **단위/테이블 오선택 misparse**
   (과거 마스터 FY2024 = 443.8). FY2024 감사보고서 대비 FY2025 표 구조가 달라 잘못된 표/열을 잡는 것으로 의심.
   현재 마스터엔 2025.4Q 신계약CSM=null(과대값이 sanity에 걸려 버려진 듯).

2. **KR1098 카카오페이손해** — 추출 **신계약CSM=20,187.6억** (현 마스터 stale값과 정확히 동일 →
   이전 빌드도 같은 표를 같은 방식으로 읽었다는 증거). 카카오페이 규모상 2조원대는 비현실 →
   동일 magnitude misparse. build_nb_csm_multiple의 `_MULT_CAP=40`이 배수를 null 처리 중(정상 동작).
   과거 2024.4Q 신계약CSM=18.1.

3. **KR0097 하나생명** — build_csm_waterfall 경로(`extract_measurement_tables`)에선 **no blocks**
   (별도 `_00760`도 0). 하나생명은 `AUDIT_REPORT_ANNUAL`이라 `ifrs17_ingest_audit_annual.py`의
   `extract_csm_tables` 경로로 들어와야 함(2024.4Q=3240.3이 그 경로 산물). → **그 ingest를 FY2025로
   1회 실행**(raw 이미 있음, 멱등) → `data/dart/extracted/하나생명보험_<rcept>_csm.json` 생성 →
   build_root_masters 병합 시 CSM_waterfall에 2025.4Q 행 추가.

### 요청 (파서 ifrs17 lane)
- (1)(2): AIG·카카오페이 FY2025 신계약CSM magnitude/table misparse 교정 (단위 정규화 or 표 선택 로직;
  `combined-agn` 경로가 FY2025 감사보고서 표에서 오작동). 교정 후 build_csm_waterfall_master 재빌드.
- (3): 하나생명 FY2025 audit-annual ingest 실행 → 병합.
- 셋 다 끝나면 `build_nb_csm_multiple.py` 재실행 → NB_CSM_multiple.json 2025.4Q 채움 →
  index.html이 최신분기로 표시(publishing/designer는 그 다음).

downloader 측 잔여 액션 없음(raw 복원·검증·네이밍 정정 완료). 추출 교정만 남음.

## 답변 (recipient 작성 — 처리 후)
