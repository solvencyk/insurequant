---
from: owner
to: parser
created: 20260616T1029Z
status: answered
route: backlog
company: KR0002 한화손해보험
period: 2026.1Q
lane: ifrs17
iter: 1
---

## 미결 (owner 라이브 QA) — 한화손보 CSM 상각 스케줄 status=partial

IFRS17.html에서 **한화손해보험(KR0002) CSM 상각 스케줄이 조회 안 됨 (status=partial)**. 원인 진단 요청.

### 어디를 볼지
- `csm_amort_schedule` (Tier A2, `csm_extractor.py`) 추출 결과. **한화손보는 ifrs17 도메인doc §3.3에서 `form_type=unknown`**(16+8 tables, rollforward/snapshot 혼재)로 분류된 사 — 스케줄표 인식이 부분 실패해 일부 버킷만 잡혔을 가능성.
- `status=partial`의 정확한 의미 추적: (a) 추출이 연도버킷 일부만 잡음(form_type unknown·THEAD-less 등), (b) 소스에 향후 상각 스케줄 자체 미공시/이미지, (c) 패널 status 매핑/렌더 문제 — 셋 중 무엇인지.

### 라우팅
- **parser-ifrs17 본건.** 추출 갭이면 재추출(semantic scoring 보강). 
- **소스에 스케줄이 진짜 없으면**(이미지/미공시) → status=partial이 정당한지 **designer inbox로 표기 협의 바운스**(미제공 메시지 vs partial).
- 26.1Q raw: **owner가 지금 26.1Q 재다운로드/파싱 중** → raw 들어오면 그걸로 검증. (FY2025_Q4=2025연간 raw는 디스크 존재.)

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. `build_csm_waterfall_master.py` 실행 금지(raw purge 붕괴).

## 답변 (recipient 작성 — 처리 후)

진단 2026-06-20 (parser-ifrs17, 미해소·open 유지): 한화손해 csm 추출=16블록(rollforward 등)이나 **연차별 CSM 상각 스케줄 표 미캡처**. 한화손해 form_type=unknown(16+8 혼합표)이라 해당 표 인식 부분실패=추출갭(a) 유력(IFRS17상 예상인식시기 공시 의무라 소스엔 있을 듯). 단 unknown-form 자동재추출 난이도 높음→semantic scoring 보강 후속 or designer 'partial 정당' 협의. 라이브 raw(20260310003000) 디스크 존재.

---

## 해결 (ifrs17, 2026-07-04) — 추출갭(a) 확정 + 한화손해 surgical fix, 광역 추출기버그는 별건 라우팅

**원인 확정 = 추출갭(a) (소스엔 실재).**
- FY2025 raw(20260310003000, 3개 xml)에 상각 스케줄표 **실재**: `(2)...보험계약마진이 당기손익으로 인식될 것으로 기대되는 시점` = Form A, 헤더 `[구분, 포트폴리오, 1년…10년, 11년~15년, 16년~20년, 21년~25년, 26년~30년, 30년 초과, 계]` × 상품행(Non-Par/Indirect-Par 무배당상해·질병·재물·연금저축·기타) + `합 계`행. `(3)...출재보험계약...`은 재보험(음수) 별도.
- 기존 partial 원인 2겹: ① **FY2025 csm 추출 자체가 없었음**(FY2025는 sensitivity만 batch됨) → 패널이 FY2024 filing(20250311001216) 사용, 그 추출은 measurement 변동내역표 16블록뿐(연차버킷 없음) → picker가 그걸 잡아 buckets={} = partial. ② FY2025 raw를 extract_csm_tables에 태우니 상각표가 정상 추출됨(추출갭 확정, 원천부재 아님).

**추출기 버그 3종 발견** (extract_amort_schedule, viz_build_ifrs17_panels.py) — FY2025 raw를 넣어도 이것들 때문에 오답:
- (a) 총계행 `합 계`(전각 공백)이 hit_labels `합계`에 substring 매칭 안 됨 → 총계 대신 첫 상품행 폴백.
- (b) `_pick_amort_block` 동점 tiebreak=line_no 최댓값 → 당기말(먼저) 대신 **전기말**(나중) 블록 선택.
- (c) `_RANGE_TILDE_RE ^(\d+)~(\d+)년$`가 `11년~15년`(첫 숫자 뒤 "년")을 못 받음 → 10년초과 tail 4열 드롭, yearly 합≠total.

**정답값(당기말 원수, 천원)**: total **4,069,381,701**(=40,694억, 기말 CSM ≈4조와 정합) · y1 253,134,608 … y10 103,998,949 · y10plus 2,514,719,640. yearly 합 = coarse 합 = total(내부정합). 단위=천원(현대해상·하나생명·라이나와 동일, 패널은 사별 raw 미정규화).

**적용 = 한화손해 surgical만 (owner 결정 2026-07-04).**
- 위 3버그는 **공유 코드**라 고치면 라이브 csm_amort **24개사 파급**(틸드 수정이 `_bucket_columns_count`→picker 흔들어 ~16사 total flip; 내부정합만으론 당기/전기·원수/재보험 회귀 판별 불가 — 한화손해 자신이 전기말 오선택 반례). 미검증 광역변경 회피 위해:
- 추출기 코드 **HEAD로 원복**, FY2025 추출본 미잔존, `csm_amort_schedule.json`의 **한화손해 레코드만** 검증값으로 surgical 교체(status partial→ok, rcept 20260310003000). csm_amort diff = 한화손해 단건(29사 유지, drift 0).

**후속(별건, 검증 필요 — 라우팅):** extract_amort_schedule 3버그 일반화 수정. 순수개선 ~8사(DB손해·KB손해·삼성화재·교보·케이비라이프·코리안리·흥국화재·미래에셋: total 불변, buckets 합=total 복구)이나, ~16사(DB생명·농협생명·신한라이프·메트라이프·하나생명·라이나·롯데손해·동양·케이디비·에이비엘·에이아이에이·처브·푸본현대·흥국생명·NH농협손해·한화손해)는 선택 블록이 바뀌어 **CSM_waterfall 기말 CSM 교차 + 당기말·원수·완전성 1사씩 검증** 후에야 shipping 가능. 전용 검증 패스 권장.

**downstream FYI(designer)**: 한화손해 상각 단위=천원(raw, 미정규화). 원수(발행) 기준, 출재는 별도 음수표. 음수 △.

status → answered (owner 사이트 재확인).
