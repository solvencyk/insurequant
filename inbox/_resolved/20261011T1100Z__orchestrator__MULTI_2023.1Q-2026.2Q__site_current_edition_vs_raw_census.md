---
from: orchestrator
to: downloader
created: 20261011T1100Z
status: resolved
route: backfill
company: MULTI
period: 2023.1Q-2026.2Q
rule: RAW_NEWER_EDITION
lane: kics
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11, 밤새 처리): 「다음 round 로 미뤄 둔 거 전부 스윕.」 직전 별첨 수집(`inbox/_resolved/20261011T0830Z…`) 중 11사만 대조했는데도 **사이트 현행본이 우리 raw 와 다른 판**이 3건 나왔다(AXA 2024.3Q 는 옛 판이 K-ICS 「공시 예정」, 신판이 완성본 — 스위스리 2023.4Q 와 같은 유형). 발행사가 나중에 K-ICS 를 채우거나 정정해 다시 올린 판이 **다른 회사·분기에도 있을 수 있다.** 전 회사·전 분기에 대해 사이트 현행본과 raw 를 대조해 달라는 전수 대조 티켓이다.

### 할 일
1. **범위**: 정기경영공시 PDF 가 raw 에 있는 모든 (회사, 분기) — 원수사 39사(KR0001~KR1000, 서울보증 KR0150 은 지난 분기 사이트 삭제라 제외 `NO_RAW_PDF 최종`) + 재보사 8곳(KR1101~KR1108, 이들은 매니페스트 `versions`/`latest` 규칙이 이미 있으니 그 규칙 기준으로 신판만 추가 확인) × 2023.1Q~2026.2Q. 먼저 `data/disclosure/FY*/raw/` 와 각 매니페스트로 대조표(회사×분기: raw 파일명·sha256·쪽수·`_v` 병존 여부)를 만들고, 직전 수집에서 이미 대조한 11사·분기는 결과를 재사용한다(`data/disclosure/_meta/attachments_manifest.json`·`attachments_20261011/`).
2. **대조 방법**: 회사 사이트(`docs/agents/source-catalog.yaml` 해당 항목) 또는 협회 사이트(생보 `pub.insure.or.kr`, 손보 협회)의 현재 게시 파일을 받아 sha256 으로 raw 와 비교. 해시가 다르면 쪽 수·K-ICS 총괄표 쪽의 숫자(지급여력비율·요구자본·가용자본)·「공시 예정」 문구 유무를 비교하고 `_v<날짜>` 로 같은 raw/ 에 **병존 저장**(`save_versioned_pdf`, 기존 raw 는 그대로, `_versions.json` 기록). 사이트가 지난 분기를 내린 회사(`NO_RAW_PDF`, `KR0150`)는 재수집 반복 금지.
3. **분류**: 신판이 (a) K-ICS 가 비어 있던 옛 판의 완성본 (b) 정정판(숫자가 달라짐 — 어느 쪽·몇 칸) (c) 서식/쪽 매김만 다름 (d) 동일 중 어느 것인지, 마스터 `kics_disclosure.json` 에 그 (회사, 분기)가 비어 있거나 면제로 등재돼 있는지(읽기만)를 같이 적는다. (a)·(b) 는 parser(kics) 티켓 1건으로 묶어 발행(목록 JSON 경로, 칸별 옛/새 판 파일명). 변환(docling)·마스터 쓰기는 하지 않는다.
4. 도달성: 회사망에서 외부 443 이 시간대별로 막힌다 — 사이트별 curl(`--ssl-no-revoke`)로 먼저 확인. **go.kr·KIPRIS 는 브라우저·WebFetch 금지.** 막힌 사이트는 사유와 함께 「미대조」 목록으로.

### 규칙
- 마스터 JSON·xlsx·HTML·게이트·예외 등재부 금지. 커밋·push 금지. 서브에이전트 금지, docling 금지. 동시 에이전트 3개이므로 네트워크는 순차·가볍게(사이트당 요청 간격 유지, 병렬 다운로드 금지).
- **공용 Browser pane 을 쓰지 말 것**(내장 브라우저가 꼭 필요하면 한 번에 하나의 탭만, 끝나면 닫을 것). 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python3 -`·`python -`(stdin heredoc) 절대 금지**(고아 CPU 스핀 전례 4회 — 직전 수집에서도 1건 남았다), `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).
- 중간 산출·런로그 `data/disclosure/_meta/site_edition_census_runlog_20261011.md` 맨 위 「중간 결과」 계속 갱신.

### 보고
- 회사×분기 대조 결과표(동일 / 신판 병존 저장 / 미대조+사유), 신판 분류(a~d)와 건수, 발행한 parser 티켓, 받은 파일 수·용량, `TODO_downloader.md` Status + `docs/changelog_downloader.md`.

## 답변 (recipient 작성 — 처리 후)
(downloader, orchestrator 검증·종결 2026-10-11) 전 회사·분기 사이트 현행본 대조 완료: 645칸 중 605칸 대조(동일 558 · 새 판 23 · 바이트만 다름 16 · 서식만 6 · raw가 더 완전 2), 미대조 40(코리안리 11 TLS 차단·서울보증/캐롯 제외·퍼시픽 봇확인창·마이브라운). 새 판 `_v20261011` raw 16개(65MB)·attachments 5개(44MB) 병존 저장, 기존 파일 불변. K-ICS 수치 정정판 7칸(예별 2025.4Q 지급여력비율 △8.24→△13.53 등)은 parser(kics) 티켓 `20261011T1210Z` 로, IFRS17 참고는 `20261011T1215Z` 로 발행. 런로그 `data/disclosure/_meta/site_edition_census_runlog_20261011.md`. 남은 일: 코리안리·생보 회사 사이트 잔여 대조(TODO_downloader).
