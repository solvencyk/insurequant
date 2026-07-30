---
from: owner
to: parser
created: 20260616T0007Z
status: resolved
route: backlog
company: KB, 예별손보(구MG), 서울보증, 하나손보
period: 2025.4Q~2026.1Q
lane: kics
iter: 1
---

## 미결 (sender 작성 — owner 라이브 QA 3차) — K-ICS 데이터 4건

**K1. KB 2026.1Q 지급여력비율 그래프 미표시.** `kics_disclosure.json`에 KB 2026.1Q 데이터 존재 여부 확인. 없으면 추출/적재 누락(raw 없으면 downloader 바운스), 있으면 designer 렌더 건으로 바운스.

**K2. 예별손보 K-ICS가 26.1Q만 보임 — 그 이전 = MG손해(구사명).** 사명변경(MG손해보험→예별손해보험) 매핑해서 **과거 분기를 예별 시계열에 병합**. 과거 raw가 없으면 downloader에 MG손보 과거 K-ICS 공시 fetch 바운스.

**K3. 서울보증 25.4Q 파싱 오류.** 생명장기 금액 0인데 하위에 **대재해위험액 5212**가 뜬금없이 출현(행 오정렬/셀 밀림 의심) → 재파싱 + 원인 적시. validation 연계(`…validation…round3`).

**K4. 하나손보 K-ICS 민감도(rate sensitivity) 경과조치 적용후 없음.** 경과조치 미적용사면 **적용후=적용전**이어야 함(메모리: AIA 동일 패턴 — 경과조치 미적용 시 적용전=적용후). 적용후를 적용전으로 채우거나 추출 보강.

**주의**: Windows 인라인 `python -c` 금지. python 풀패스. K-ICS PDF는 `data/disclosure/`(gitignore, 디스크 존재 — purge 무관). `build_csm_waterfall_master.py` 실행 금지.

## 답변 (parser 작성 2026-06-16 — K1·K2·K3·K4 전부 처리)

게이트: RED 21→**19** (회귀 0, raw 검증). 행수 kics_disclosure.json 17,200→**17,239**, sensitivity 495→**516**.

**K1 (KB 2026.1Q 그래프) = 데이터 갭 아님 → designer 바운스.** census 결과 데이터 정상 존재:
KR0010 KB손해 2026.1Q item27=**185.87%**(item1 123,858 / item14 66,638), item28 76.65% 전부 적재.
KR0099 KB라이프도 252.28%. 추출 누락 아님 → 렌더 레이어 건. `inbox/designer/20260616T0050Z…` 발송
(2026.1Q가 최신분기라 차트 분기범위 하드코딩 의심 — KB만인지 전사인지 designer 확인 요청).

**K2 (예별=구MG 시계열) = 2025.4Q 자체 처리 + 그 이전 downloader 바운스.**
- 사실관계 정정: JSON에 "MG/엠지" 명칭 데이터 **0건**(병합할 별도 데이터 없음). KR0004 raw는 디스크에
  **FY2025_Q4+FY2026_Q1만** 존재. FY2026_Q1은 이미 적재(2026.1Q).
- **FY2025_Q4 raw(2.9MB) → 파서가 docling 변환(confidence 0.82) + 추출 완료**: 코어 1-28(28행, item28
  파생) + 하위 29-35(7행, 합/item17 ratio 1.30 정상) + 시장 36-40(5행, 19_market reconcile). **=40행 신규.**
- ⚠️ **예별손해 2025.4Q는 자본잠식**: 지급여력비율 **△8.24%**(적용전)/△9.69%(적용후), 지급여력금액 △714억
  (이익잉여금 △4,697억). 부실보험사 실값(MD △세모 부호 정확 처리). **경과조치 적용사**(TER/TIRR 선택적용
  → 적용후≠적용전; 적용후 leg는 post_capital_legs 워크스트림 소관). 36_irr은 41-46 미공시라 documented 예외.
- **2023.1Q~2025.3Q (11분기) raw 부재** → MG손해 구사명으로 downloader fetch 발주(`inbox/downloader/
  20260616T0055Z…`, 매핑 MG손해→예별 KR0004 명시). 불가 분기는 구조적 결손 등록.

**K3 (서울보증 25.4Q 대재해 오정렬) = 수정 완료(+ 동일 버그 2건 추가 적발).** 원인: 서울보증은 보증보험사라
생명장기위험액(item17)=0인데, **일반손해 분해의 대재해(521,239백만=5212.39억, MD L369 "라.대재해위험액")를
생명장기 1-7 슬롯(item35)에 오매핑**한 셀밀림. 추출기엔 이미 `_is_life_catastrophe_table` 가드가 있어 **현재
로직은 안 뽑음**(dry-run 확인) → JSON의 5212.39는 가드 이전 옛 추출기가 남긴 stale 행. 정의상 parent=0이면
자식 부재여야 하므로 **parent17≤0 & 자식 비0 행 전수 제거 = 3셀**: 서울보증 2025.4Q(5212.39)·**2023.4Q
(5264.37)**·카카오 2023.3Q(4.72). + fill_subitems에 parent-gate 가드 추가(재발 방지). validation 발주서
`…0130Z…parentzero…` 답변 완료, validation 신설 게이트 `_parent_zero_child_nonzero`로 parent-zero=0 확인.

**K4 (하나손보 민감도 적용후) = 채움 완료(+ 동류 4 company-quarter).** `kics_rate_sensitivity.json`에서 하나손해는
적용전만 있고 적용후 결측. MD가 **경과조치 미적용 명시**(공통/선택 해당사항 없음) → 적용후=적용전(AIA 패턴).
전수 스캔으로 "적용전만 있는" 7개 company-quarter 발견, MD로 전부 미적용 확인 후 적용후 복제:
하나손해 2024.4Q/2025.2Q/2025.4Q · 신한이지 2025.4Q · 카카오 2025.4Q · 삼성생명 2025.2Q/2025.4Q = **21행**.
(삼성생명도 MD L259/L639 "전·후 동일" 미적용 확인 — 적용사면 복제 금지였으나 미적용사로 검증됨.)

**잔여**: 19 RED 전부 documented(TODO.md CURRENT 갱신). 비-파서 = owner OCR(KB/한화/흥국/AIA image)·
downloader(MG 과거 11분기)·designer(KB 2026.1Q 렌더). status: resolved.
