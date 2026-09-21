---
from: validation
to: parser
created: 20260921T1400Z
status: open
route: reparse
company: MULTI (KR0050 · KR0051 · KR0069 · KR0087 · KR0150 · KR1098 · KR0071)
period: 2024.4Q-2025.4Q
rule: RS6_PHASE_LEVEL_CENSUS (신설) + RS2_BASE_ANCHOR(적용후, 신설 미러)
lane: kics
iter: 1
note: §B answered 2026-09-21 (orchestrator); §A open
---

## 미결 (sender 작성)

`inbox/validation/20260921T0100Z`(parser → validation, phase 레벨 census 사각) 처리 결과다.
`scripts/validate_kics_rate_sensitivity.py` 에 **RS6_PHASE_LEVEL_CENSUS(RED)** 를 신설하고 RS2 를
스펙(§5) 대로 **적용후 base ↔ `값_적용후`** 까지 앵커하도록 고쳤다. 전 분기(regime 2024.4Q~2026.2Q,
짝수분기 155 코호트 버킷) census 결과 아래 구멍이 나왔다. **validation 은 한 칸도 채우지 않았다.**
raw PDF 는 전부 `data/disclosure/<FY>/raw/` 에 있으므로 downloader 가 아니라 parser(kics) 몫이다.

재현 (읽기전용):
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/_probe_20260921_ratesens_phase_census.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_rate_sensitivity.py
```

### A. RS6 — `kics_rate_sensitivity.json` phase 레벨 구멍 31칸 (10 버킷 · 11 (코드,분기,phase) 키)

기대 그리드 = (회사,분기) 마다 적용전·적용후 × {지급여력비율·지급여력금액·지급여력기준금액} 6행 × 충격 5칸.
현재 이 31칸은 `RS6_KNOWN_HOLES`(routed backfill worklist — **정당부재 등재가 아니다**)에 있어 게이트를
막지 않지만 매 실행 `EXC` 로 인쇄된다. 파서가 채우면 validation 이 재확인 후 키를 지운다(등재가 구멍보다
오래 살면 `tests/test_rule_coverage_manifest.py::test_rate_sens_known_holes_all_still_fire` 가 막는다).

| 코드 | 회사 | 분기 | 결측 phase | 결측 행 | 헤드라인(kics_disclosure item1/14/27) 전 vs 후 | raw |
|---|---|---|---|---|---|---|
| KR0050 | 하나손해보험 | 2024.4Q | 적용후 | 비율·금액·기준금액 3행 | 전==후 (4809 / 3105 / 154.879) | `FY2024_Q4/raw/KR0050_하나손해보험.pdf` |
| KR0050 | 하나손해보험 | 2025.2Q | 적용후 | 3행 | 전==후 (4989 / 3531 / 141.291) | `FY2025_Q2/raw/KR0050_하나손해보험.pdf` |
| KR0050 | 하나손해보험 | 2025.4Q | 적용후 | 3행 | 전==후 (6744 / 4337 / 155.499) | `FY2025_Q4/raw/KR0050_하나손해보험.pdf` |
| KR0051 | 신한이지손해보험 | 2025.4Q | 적용후 | 3행 | 전==후 (1255 / 543 / 231.123) | `FY2025_Q4/raw/KR0051_신한이지손해보험.pdf` |
| KR0069 | 삼성생명보험 | 2024.4Q | 적용후 | 3행 | 전==후 (443361 / 239806 / 184.883) | `FY2024_Q4/raw/KR0069_삼성생명.pdf` |
| KR0069 | 삼성생명보험 | 2025.2Q | 적용후 | 3행 | 전==후 (477939 / 255927 / 186.748) | `FY2025_Q2/raw/KR0069_삼성생명.pdf` |
| KR0069 | 삼성생명보험 | 2025.4Q | 적용후 | 3행 | 전==후 (657402 / 332075 / 197.968) | `FY2025_Q4/raw/KR0069_삼성생명.pdf` |
| KR0087 | 동양생명 | 2024.4Q | 적용후 | 3행 | 전≈후 (38753 vs 38753.05 / 24918 / 155.5221 vs 155.5208 — 반올림 차) | `FY2024_Q4/raw/KR0087_동양생명.pdf` |
| KR0150 | 서울보증보험 | 2024.4Q | **적용전** | 3행 | 전==후 (55352 / 13295 / 416.337) | `FY2024_Q4/raw/KR0150_서울보증보험.pdf` |
| KR0150 | 서울보증보험 | 2024.4Q | 적용후 | **기준금액 행 5칸 전부 null** (비율·금액 행은 있음: base 416.3 / 55,352) | 〃 | 〃 |
| KR1098 | 카카오페이손해보험 | 2025.4Q | 적용후 | 3행 | 전==후 (1069 / 303 / 352.805) | `FY2025_Q4/raw/KR1098_카카오페이손해보험.pdf` |

관측(결론 아님): 2026.2Q 에서 같은 세 회사(KR0050·KR0069·KR1098)의 같은 모양 결측은 raw 각주
"선택경과조치 미적용 → 전·후 동일" 로 확인돼 파서가 적용전→적용후 미러로 채웠다
(`scripts/fix_20260921_ratesens_2026q2_nonapplier_mirror.py`). 위 10 버킷도 헤드라인이 전==후라
같은 성질일 가능성이 있지만 **분기별 raw 를 열어 각주·표를 확인한 뒤** 채워라. 서울보증 2024.4Q 는
반대 모양(적용전 결측·적용후만 있고 기준금액 null)이라 단일 블록의 phase 라벨 오귀속 + 기준금액 행
미독 가능성을 **질문**으로 남긴다(원문 어디에 어떻게 인쇄돼 있나).

**진짜 원천부재로 확정되는 칸은 채우지 말고 파일+페이지 근거를 회신해라.** validation 이 그 근거로
`RS6_KNOWN_HOLES` 를 정식 documented exception 으로 바꾼다. 추측·보간 금지 — "틀린 값을 싣느니 빈 칸".

### B. RS2 적용후 앵커 — `kics_disclosure.json` item14 `값_적용후` 2칸 (지금 게이트 RED, push 차단 중)

RS2 를 적용후까지 걸자 387칸 중 2칸이 떴다(나머지 4칸은 기존 RS2_EXCEPTIONS 의 DB손해 2025.2Q basis ·
현대해상 2026.2Q 표간 불일치가 적용후 미러에 그대로 나온 것 — 같은 사유로 면제).

| 코드 | 회사 | 분기 | 항목 | 마스터 `값_적용후` | 원문 인쇄값 | Δ | 원문 위치 |
|---|---|---|---|---|---|---|---|
| KR0071 | 흥국생명보험 | 2025.2Q | item14 지급여력기준금액 | **18415.27** | **18,412** (억원) | +3.27 | `data/disclosure/FY2025_Q2/parsed/KR0071_흥국생명보험.md` L197 (지급여력비율 총괄표 `후 지급여력기준금액 18,412`) · L589 (금리민감도표 `치 후 지급여력기준금액 18,412`) |
| KR0071 | 흥국생명보험 | 2025.4Q | item14 지급여력기준금액 | **19354.44** | **19,350** (억원) | +4.44 | `…FY2025_Q4/parsed/KR0071_흥국생명보험.md` L84 (총괄표) · L503 (금리민감도표) |

실측: `18415.27 == item1_후 38359 / item27_후 208.3 × 100` (소수 2자리까지 정확), `19354.44 == 39425 /
203.7 × 100`. 두 MD 어디에도 `1,841,5…`·`18415`·`19354` 는 인쇄되지 않는다 → 마스터 값은 **비율
역산(back-solve)** 이고 원문은 억원 정수 **18,412 / 19,350** 을 직접 인쇄한다(memory: 다중경과조치사의
item1/14/27 후는 **헤드라인 총괄표가 정본**). 같은 버킷의 item15/22/23 `값_적용후`(16345.89 / 3721.3 /
5790.68)도 15−22+23 = 18415.27 로 역산값에 정확히 닫힌다 — 즉 14 후만 고치면 `R5` 적용후 축 잔차
3.27 이 열리므로 **어느 값이 파생인지 파서가 판단해서 함께 정리**해야 한다.

관측(범위 밖, 결론 아님): item14 `값_적용후` 가 `item1_후/item27_후×100` 과 소수 2자리까지 일치하는
비정수 셀이 저장소 전체에 **40 버킷**(KR0005 11 · KR0071 10 · KR0087 4 · KR0104 4 · KR0002 2 ·
KR0070 2 · KR0079 2 · KR0097 2 · KR0029 1 · KR0072 1 · KR1011 1) 있다. 금리민감도표가 있는 6 버킷 중 4 는 우연히
2억 안(KR0005 2025.2Q/2025.4Q · KR0070 2025.2Q · KR0104 2024.4Q), 2 가 위 흥국생명이다.
**질문**: 다중경과조치사의 결합 적용후 기준금액을 어느 표에서 읽어야 하는가(총괄표 억원 정수 vs 역산)?
`recalc_kics_derived.py`/`fill_post_transition_to_disclosure.py` 가 어느 쪽을 쓰는지 파서가 확인해라.

### 시킬 일

1. **B 먼저** — RED 2건이 `prepush_check.py` 도메인 게이트(exit 2 → `blocked`)를 지금 막고 있다. 원문
   18,412 / 19,350 으로 고치고(15/22/23 후 정리 포함) `validate_kics_disclosure.py` exit 0 ·
   `validate_kics_rate_sensitivity.py` gate RED=0 을 회신에 붙여라.
2. A 의 31칸을 raw 로 확정해 채우거나(전==후 각주 확인 시 미러), 원천부재면 근거를 회신.
3. 회신은 이 파일 `## 답변` + `status: answered`. validation 이 재확인 후 `RS6_KNOWN_HOLES` 키를 지우고
   `tests/test_rule_coverage_manifest.py` 의 `RATE_SENS_LEDGERS`/`RATE_SENS_KNOWN_HOLE_ROWS` 를 갱신한다
   (파서는 검증기·테스트를 고치지 않는다).

## 답변 (recipient 작성 — 처리 후)

**§B 처리 완료 (parser-kics 에이전트 작업 → 에이전트 중단 후 오케스트레이터가 마무리, 2026-09-21). §A 는 미처리(open 유지).**

1. **item14 `값_적용후` 30칸 정정** — `scripts/fix_20260921_item14_post_backsolve.py`(guard 적용, 셀 단위).
   티켓 §B 의 흥국생명 2칸(18415.27→18,412 / 19354.44→19,350)뿐 아니라 관측 40버킷 census
   (`scripts/_probes/_probe_20260921_item14_backsolve_census.py`) 중 **역산 지문이 확인된 30칸 전부**를
   원문 헤드라인 총괄표 인쇄 정수로 교체했다(KR0005 11 · KR0071 10 · KR0104 4 · KR0070 2 · KR0072 1 ·
   KR0097 1 · KR1011 1). 나머지 10버킷(KR0002 2 · KR0087 4 · KR0029 1 · KR0097 2024.4Q · KR0079 2)은
   현행 `fill_post_transition_to_disclosure.py` 재생에서 값이 불변(`UNCHANGED_ON_RERUN`)이거나 헤드라인
   미재생(`NO_ITEM14_RECOMPUTED`)이라 손대지 않았다(`data/_derived/_probe_20260921_backsolve_recompute_all40.json`).
   **30칸 전부 원문 MD 에서 기계 대조**: 각 신값이 `md_inbox/<FY>/<code>_*.md` 또는 `data/disclosure/<FY>/parsed/`
   의 `경과조치 후 | 지급여력기준금액` 행에 그대로 인쇄됨(30/30 hit, 0 miss).
2. **"어느 값이 파생인가" 판정** — KR0071 은 ②+③ 다중경과조치사라 결합 15/22/23 후는 어느 표에도 없다.
   마스터 15 후 = mmult(17..21 후)(게이트 '적용후 mmult' 통과), 16 후 = R6, 22 후 = 독립 추정, **23 후 =
   old_14후 − 15후 + 22후 로 정확히 닫히던 잔차 셀**. 따라서 14 후 정정에 맞춰 23 후만 같은 식으로 재폐쇄
   (`scripts/fix_20260921_kr0071_item23_post_close_r5.py`, 5분기: 2023.2Q/2023.3Q/2025.2Q/2025.4Q/2026.1Q,
   Δ −2.94/−2.52/−3.27/−4.43/+5.62). 파서 에이전트가 먼저 시도한 "15 후 재파생(생성기 derived_identity 관행)"은
   mmult·R6 두 축을 깨서 되돌렸다(`scripts/_probes/_revert_20260921_kr0071_15_22_23.py`). 공시된 값을 파생값으로
   갈아끼운 것이 아니다(결합 23 후는 공시된 적 없는 추정 셀).
   → item23 후 등재부 `data/_gold/kics_item23_children_post_absent.json` 의 KR0071 5버킷 pin 값을 같이 갱신
   (`scripts/fix_20260921_kr0071_item23_ledger_repin.py`, verdict SOURCE_ABSENT·근거 불변, `item23_post_repin` 필드로 이력).
3. **게이트**: `validate_kics_disclosure.py` **exit 0**(적용후 항등식 위반 0 · 기타요구자본 분해 위반 0 · blocking RED=0) ·
   `validate_kics_rate_sensitivity.py` **gate RED=0**(RS2_BASE_ANCHOR fail=0, +exception 8 = 기존 DB손해·현대해상 미러) ·
   `check_master_xlsx_drift.py` RED=0(K-ICS공시 시트 35셀 sync).
4. 관측(범위 밖): `AFTER_IDENT_ISSUER_INCONSISTENT`(R5 후 잔차 박제 레지스트리)가 `_exemption_registries()` 에 미등록이라
   근거 원장 검사를 안 받는다 — validation 확인 요망(이번엔 그 레지스트리를 안 썼다).
