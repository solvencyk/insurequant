---
from: validation
to: parser
created: 20260617T0030Z
status: resolved
route: reparse
company: 예별손해보험(KR0004), 흥국화재(KR0005)
period: 2023.2Q~2025.4Q
lane: kics
iter: 1
---

## 미결 (validation, owner xlsx 검토 루프) — OCR K-ICS 행 적재 + 가용자본 적용후 결측

owner가 OCR로 못 파싱했던 K-ICS 행을 `insurequant_master_tables.xlsx` 'K-ICS공시' 시트에 수기 입력
(값=원수치). validation이 **값_적용후 집계항목을 R4 분산효과+더하기빼기로 계산해 채움**
(`기본요구자본 = sqrt([생장·일반·시장·신용]·R4) + 운영`, 적용전 데이터로 공식 검증 정확). owner 확정.

### 적재 요청 (xlsx → kics_disclosure.json)
아래 (회사,분기)는 **kics_disclosure.json에 부재**(OCR 미파싱) → xlsx의 값+값_적용후를 적재:
- 예별손해(KR0004): 2023.2Q · 2023.4Q · 2024.2Q · 2024.4Q · 2025.2Q · 2025.4Q
- 흥국화재(KR0005): 2024.4Q
- validation 계산분(값_적용후): item14(지급여력기준금액)·15(기본요구자본)·16(분산효과) 전 분기 + item27·28(2024.2Q·2024.4Q만). 2024.4Q 기준금액후는 owner OCR 9228.71이 아니라 **R4 재산출 8656.64로 통일**(owner 확정).

### 🔴 결측 8셀 → 가용자본 적용후 OCR 필요
item27(지급여력비율후)·item28(기본자본비율후)는 **가용자본 적용후**(item2 기본자본후·item3 보완자본후)가 있어야
계산 가능. 다음 5개 분기는 그게 OCR 안 돼 빈칸:
- 예별 2023.4Q·2025.2Q·2025.4Q, 흥국화재 2024.4Q (각 item27후·28후 = 2셀씩 = 8셀)
→ 원본 이미지에서 **기본자본 적용후·보완자본 적용후**(또는 지급여력비율 적용후 직접) OCR. 들어오면 validation이 `27후=가용자본후/기준금액후×100`로 채움.

### 주의
- 적재 후 `validate_kics_disclosure.py` RED 재확인(부모-자식·census). 루트 JSON만 고치면 빌드에서 소실 → 정본 경로로.

## 답변 (validation 2026-06-17 — 자체 처리, parser 불요)

owner: 가용자본 적용후=적용전이라 8셀은 결측 아님(공란 의도)·JSON 적재는 validation이 직접.
- 27후·28후 14셀 = 가용자본 적용후=적용전(값)/R4 기준금액으로 채움(2023.2Q disclosed도 R4로 통일).
- **established gold 파이프라인으로 적재**: `build_user_kics_gold.py`(xlsx↔JSON diff 캡처) → `apply_user_kics_gold.py`(upsert) → `recalc_kics_derived.py`(27/28 재계산). **152행 추가**(KR0004 예별·KR0005 흥국 + KB·신한이지·한화생명·흥국생명 OCR gold 동반). 게이트 RED 다수→5(예별/흥국 RED 0).
status: resolved (parser 작업 없음).
