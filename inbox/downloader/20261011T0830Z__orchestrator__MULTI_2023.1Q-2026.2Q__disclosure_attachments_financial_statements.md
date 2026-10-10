---
from: orchestrator
to: downloader
created: 20261011T0830Z
status: open
route: backfill
company: MULTI
period: 2023.1Q-2026.2Q
rule: RAW_ATTACHMENT_ABSENT
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11, 밤새 처리): 경영공시 BS·PL 세부(자산 아래 현금성자산·재보험계약자산, 자본 아래 이익잉여금·자본금 등) 를 전 회사 전 분기 채우라. parser-ifrs17 이 우리 raw 로 채울 수 있는 만큼 채웠고(IFRS17_BS +1,621칸, PL +540칸), **원천이 PDF 안에 없는 칸**은 원문 「Ⅷ. 재무제표 사항은 첨부 파일 참조」 형태로 **재무제표가 별첨 문서로 분리**돼 있어서다(예: 하나손해보험 경영공시 PDF p60). 그 별첨(재무제표 + 주석 PDF 등)을 받아야 한다. 받는 것은 downloader 몫이고, 파싱은 parser 몫이다(변환갭을 downloader 로 보내지 말 것, 반대로 이 건은 raw 자체가 없는 건이다).

### 입력 (기계 목록 — 먼저 읽을 것)
- `data/_derived/bspl_granularity_20261011/attachments_needed_20261011.json` — 회사별 `nofull`(경영공시 PDF 는 있으나 재무제표 전문이 없는 분기, 값은 그 분기에 비는 BS 항목번호 목록, 빈 목록 = 연말 분기라 감사 재무제표가 필요한 경우 포함) / `nodoc`(그 분기 경영공시 PDF 자체가 없음).
- `data/_derived/bspl_granularity_20261011/attachments_needed_by_absent_lines_20261011.json` — 비는 항목 기준 같은 목록.
- 런로그 `data/disclosure/_meta/bspl_granularity_runlog.md` 「원천 부재」 절(렌더링으로 확인한 증거 포함).

### 요약 (회사 × 분기)
- 하나손해보험(KR0050): 2023.1Q·2023.4Q·2024.1Q~2024.4Q·2025.4Q (9분기 안팎, 목록 참조)
- 악사손해보험(KR0049): 2024.3Q·2025.1Q·2026.1Q
- BNP파리바카디프생명(KR0075): 2023.1Q~2024.3Q·2025.1Q·2025.2Q·2026.1Q·2026.2Q 등 (11분기, 목록 참조). **같은 회사 2024.2Q 는 별건 열린 티켓 `inbox/downloader/20261007T1400Z__orchestrator__KR0075_2024.2Q__truncated_disclosure_pdf.md`(잘린 사본, 33쪽에서 끊김)가 있다 — 이번에 같이 처리하고 그 티켓 답변도 쓸 것.**
- 하노버재보험 한국지점(KR1104): 2023.1Q~2024.3Q (6분기). **2025.3Q 는 발행사 미게시로 raw 없음 — 사이트·FSS 공시에 정말 없는지 한 번 더 확인하고 근거를 남길 것.**
- 알지에이재보험(RGA, KR1105): 2023.1Q·2023.3Q·2025.2Q·2026.2Q (4분기)
- 그 밖에 목록에 있는 회사(KR0051·KR0074·KR0080·KR0097·KR0100·KR1098 등)의 해당 분기, 그리고 `nodoc` 분기(퍼시픽라이프리 KR1107 2023.1Q~4Q, 마이브라운 KR1108 2023.1Q~2025.1Q — 회사 설립·영업 개시 이전이면 「해당 없음」으로 근거와 함께 기록)

### 할 일
1. **도달성 먼저**: 회사망에서 외부 443 이 시간대별로 막힌다(CLAUDE.md §10) — 사이트별 curl(`--ssl-no-revoke`) 로 도달성 확인 후 진행. **go.kr·KIPRIS 는 브라우저·WebFetch 금지**(영구 행 전례).
2. 위 목록의 (회사, 분기) 마다 별첨 재무제표 문서(재무제표+주석)를 찾는다 — 출처 후보: 회사 공시 사이트의 경영공시 상세 페이지 첨부파일(`docs/agents/source-catalog.yaml` 해당 회사 항목), 생명보험협회/손해보험협회 공시 사이트 첨부, DART 감사보고서(비상장 외감법인 감사보고서 — DART 본문 `dart_*` 수집 규칙과 `feedback_dart_no_attachment_fetch` 메모는 상장사 사업보고서 얘기이므로 비상장 감사보고서는 별개로 판단). 같은 분기에 파일이 둘이면(옛/새 버전) 둘 다 받고 매니페스트 `versions`/`latest` 규칙을 따른다.
3. 받은 파일은 기존 raw 규칙(`data/disclosure/FY*/raw/`, 파일명에 회사코드·분기·`attachment` 표지 — 기존 경영공시 PDF 와 섞이지 않게)으로 두고 매니페스트를 갱신한다. **기존 raw 는 덮어쓰지 않는다**(교체가 필요하면 `_archive` 로).
4. 못 받는 (회사, 분기)는 **사유별로**(사이트에 없음 / 로그인 필요 / 회사가 내렸음 / 해당 시점 영업 전) 근거(URL·응답·스크린샷 경로)와 함께 목록화. `KR0150` 서울보증처럼 「사이트가 지난 분기를 내림 = NO_RAW_PDF 최종」은 재수집 반복 금지.
5. 완료 시 parser(ifrs17) inbox 에 「별첨 N건 raw 도착, 어느 분기 어느 항목을 채울 수 있는지」 티켓을 떨군다(목록 JSON 경로 포함, 파싱·마스터 쓰기는 하지 않는다). 변환(docling)은 parser 가 한다.

### 규칙
- 마스터 JSON·xlsx·HTML·게이트·예외 등재부 금지. 커밋·push 금지. 서브에이전트 금지, docling 금지(이건 수집 티켓). 동시 에이전트 3개이므로 네트워크·CPU 사용은 가볍게.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python -`(stdin heredoc) 절대 금지**, `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).
- 중간 산출·런로그를 `data/disclosure/_meta/attachments_fetch_runlog_20261011.md` 맨 위 「중간 결과」에 계속 갱신.

### 보고
- (회사, 분기)별 결과표(받음 / 불가 + 사유 + 근거), 받은 파일 수·용량·경로, 매니페스트 변경, parser 로 보낸 티켓, `TODO_downloader.md` Status + `docs/changelog_downloader.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
