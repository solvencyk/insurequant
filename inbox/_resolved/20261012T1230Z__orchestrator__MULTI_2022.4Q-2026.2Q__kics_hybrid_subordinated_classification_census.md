---
from: orchestrator
to: parser
lane: kics
created: 20261012T1230Z
status: resolved
route: feature
company: MULTI
period: 2022.4Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): 소진율 도넛·Forward Outlook 은 화면에서 내리지만, **내부적으로는 점검한다** — 「신종자본 & 후순위채 발행 현황 쭉 돌아보면서 뭐로 분류되고 있는지 전수조사는 해.」 화면에 나가지 않는 **내부 증빙 작업**이다(`data/_derived/` 와 `data/bonds/capital_tier_registry.json` 의 근거 갱신만).

### 해 줄 것
1. **전수 목록**: 47사의 모든 신종자본증권·후순위채(각 시점의 DART 발행현황 표 — `data/bonds/capital_securities_fy2025.json`·`capital_securities_fy2026h1.json`·`disclosure/2026q1_per_bond.json`·`data/dart/**` 사채 발행현황, 원문 XML)를 회사·증권 단위로 한 표에 모은다: 회사·증권명·tier(`hybrid`/`subordinated`)·발행일·콜일·만기·금리·잔액·현재 `capital_tier_registry.json` 의 `type`(legacy_tfi/tier1/tier2/미확정)과 근거.
2. **분류 확정도**를 증권마다 3단계로 적는다: ⓐ **원문 확정**(발행사 증권신고서·투자설명서·사업보고서 주석·신용평가 보고서에 「기본자본으로 인정」/「보완자본으로 인정」/스텝업 유무가 직접 적혀 있음 — 문구와 출처 인용) ⓑ **시계열 추정**(항목 6·항목 13 − 항목 49 움직임 검정, `data/_derived/capital_utilization_definition_20261012/s6_tier1_type_test.txt` 방식) ⓒ **불명**. 후순위채는 원칙적으로 보완자본이지만 예외(기본자본 인정 후순위, 경과조치 구분)가 있는지 한 줄씩 확인. 증권신고서·투자설명서 문구는 **WebSearch 로 공개 자료**(DART 공시 본문 인용·보도·신평사 보고서)에서 찾는다 — `go.kr`·`law.go.kr`·KIPRIS 는 브라우저·WebFetch 금지(영구 행). DART 에 직접 접속이 되는 경로(기존 로컬 raw 파일)는 사용 가능.
3. 이미 판단이 들어간 약 14개사(보완자본형 추정: 한화생명·KDB생명·하나손해·농협손해·흥국화재 신규·교보 2023 발행분 / 기본자본형 판단: DB손해·하나생명·한화손해 일부·흥국생명·삼성화재 소액·교보 2024.4Q / 미확정: 코리안리·농협생명·푸본현대)를 먼저 원문 확정(ⓐ)으로 올릴 수 있는지 시도하고, 못 올린 것은 사유와 함께 남긴다. 신규 확정이 기존 `type` 과 다르면 **등재부를 고치지 말고** 불일치 목록으로 보고(화면에 안 나가지만 owner 가 본다).
4. 산출: `data/_derived/capital_securities_classification_census_20261012/`(전수 표 csv, 증권별 근거·인용, 확정도 요약, 불일치 목록, 재현 스크립트). 요약은 회사별 한 줄(분류·확정도) + 전체 집계(ⓐ/ⓑ/ⓒ 건수).

### 규칙
- 마스터 JSON·xlsx·HTML·`public_exports/` 수정 금지, 예외 등재 금지. docling 금지(필요 없음). 동시 에이전트 사정상 무거운 일은 한 번에 하나씩. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만(멀티라인 `-c`·stdin heredoc 금지; 고아 python3.13 프로세스를 만들지 말 것). 이 공유 티켓은 고치지 않는다. **이 티켓은 `20261012T1030Z`(퍼시픽·악사·뮌헨 K-ICS 칸) 뒤에 한다.**

### 보고 (3~6줄 존댓말)
- 전수 건수(회사·증권), 확정도 집계(ⓐ/ⓑ/ⓒ), 기존 분류와 불일치 목록, 분류가 가장 갈리는 회사, 증빙 경로, 커밋 해시. `TODO_parser_kics.md` Status + `docs/changelog_parser_kics.md`.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 3ac68b4·f08e0c8). 신종자본증권·후순위채 분류 전수조사: 채권 목록 133건(신종 46·후순위 87, 27사)+목록 밖 16건 = 149행(census_securities.csv), 확정도 ⓐ 원문 확정 126·ⓑ 시계열 추정 16·ⓒ 불명 7. 등재부 18사 중 신종 채권이 있는 17사에서 14사는 채권 전부 ⓐ. 등재부와 다른 증권 8건은 등재부를 고치지 않고 census_mismatch.csv 로만 보고: DB손보 2026년 3건(발행사 표가 보완자본형을 가리킴 -> 151.6% 가 약 75% 로 달라질 수 있음), 교보 2024-11-12 6,000억(발행조건 스텝업=보완자본형인데 발행사 표는 기본자본형 처리), 푸본·농협생명·코리안리 4건(사업보고서 스텝업 문구로 보완자본형 확정). 아이엠라이프의 설명되지 않던 1,517억은 2022년 발행 전환우선주로 특정. 남은 일: owner 의 등재부 8건 결정(화면 비노출이라 급하지 않음), 증권신고서·사모 계약서 원문 확보 시 ⓑ 6건 승급, 후순위 예외 후보 4건 판정. 산출 data/_derived/capital_securities_classification_census_20261012/.
