---
from: orchestrator
to: parser
created: 20261011T0320Z
status: resolved
route: backfill
company: MULTI
period: 2023.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11, 「이 round 끝나면 나머지 시점도 백필 전부」·「다음 round 로 미뤄 놨던 거 전부 스윕」·「재보사 IFRS17 지표도 경영공시에 있다」, 밤새 처리). **`insurance_liability_portfolio.json`(ILP) 전담 작업**(다른 parser-ifrs17 에이전트가 `IFRS17_BS.json`·`PL_breakdown.json` 을 동시에 쓰니 이 에이전트는 ILP·provenance·사이드카만 만진다). 이전 작업 런로그 `data/disclosure/_meta/ilp_backfill_pre2025_runlog.md`(§2 census·§5 미적재 사유·§6 다음 라운드·§9~§10 재작성 3셀), `lic_load_runlog_stage1.md`·`stage1b.md`, 정찰 `lic_scout_20261010.md`·`reinsurer_ifrs17_scout_20261010.md` 가 출발점이다.

### 작업 (우선순위 순, 각 단계마다 검산·디스크 저장·런로그 중간 결과 갱신)
1. **ILP 나머지 분기 백필**: 2024.1Q~3Q(약 1일, DART 69셀 닫힘 + 2025.1Q~3Q 경영공시의 전년동기 표 25~26사) · 2023.1Q~3Q(약 0.5일, DART 69셀 중 8셀 셀별 처리, 경영공시 항목 1~8 은 원천 없어 빈칸이 정답). 규칙은 직전 백필과 동일(추가 행만, 억원, BS 항목 20 대조, 재작성 기준 표시).
2. **LIC 2단계**: 단일열 공시 회사의 LIC BEL·RA 간접 계산값(항목 16·17 = 측정요소별 기말 BEL·RA − 2-4 의 BEL·RA; owner 승인 「계산값 사용」) — 사전시험 105셀 중 28셀 통과, 71셀은 회사별 표 선택이 필요, 6셀(ABL 3 포함)은 탈락(2-4 가 LIC 포함). 판정 기준: 「직접 단일열(항목 13)과 max(500백만원, 0.05%) 안에서 같은 셀만」 + 화이트리스트 관리. 화면에 계산값으로 표시되므로 provenance 에 `basis=derived` 표시.
3. **LIC 3단계**: 라이나 PDF 5셀(천원 단일열)·처브 PDF 2025.1Q~3Q 3셀·하나손보 별첨(raw 없음 → 수집 필요 목록으로 보고)·예별 2025.4Q 는 **0 을 지어 넣지 않는다**(보고만). 비상장 15사 4Q 적재 확인.
4. **재보사 8곳(KR1101~KR1108) ILP 항목 1~8(4-6-2 회계모형별·포트폴리오별 보험부채)**: 경영공시 4-6-2 는 2024.4Q(결산)부터 신설이라 **2024.4Q 이후 분기**(재보사 문서에 있는 만큼, 정찰 §2 표 참조) 적재. 재보사는 포트폴리오 구성이 다르다(수재 일반모형 등) — 마스터 항목 의미(일반모형 BEL/RA/CSM·VFA·PAA)에 맞춰 매핑하고 매핑 규칙을 런로그에 기록, 맞지 않는 칸은 보고. LIC(항목 10~15)는 재보사는 DART 가 없으므로 경영공시/감사보고서에서 나오는 만큼만(없으면 빈칸).
5. **검산기·정리**: LIC 검산기(`scripts/validate_insurance_liability_lic.py`, push 게이트 아님)가 재작성 3셀(`data/_derived/ilp_restated_comparative.json`)에서 원문 BS 대신 사이드카 재작성 값을 앵커로 쓰게 분기(지금 R-LIC1 RED 3 은 의도된 결과). 포트폴리오 검증기 RED 4(KR0100 R3 3·KR0029 2024.4Q 「10배 규칙」 1)는 **원인 확인·사실 보고만**(예외 등재는 owner). 롯데손보 2026.2Q 항목 9=1(및 2025.1Q~2026.1Q 항목 9 빈칸) 확인 — PDF 로 확인해 마스터 선례와 맞게 보고(고칠 값이면 셀 단위 + guard). 추출기 공통 결함 7개(pdfplumber 단독·헤더 위치·5자리 공백 분리·단위 머리말·이미지 헤더 등, `ilp_gap_runlog_textlayer_20261010.md`)는 가능한 만큼 보강(추출기 변경은 2025.1Q~2026.2Q 159셀 재실행이 기존과 동일해야 함 — 직전 백필에서 한 방식).

### 규칙
- **추가 행만**, 이미 있는 키는 건드리지 않는다(충돌은 보고). 셀 단위 + guard, 시작 전 백업 `data/_derived/ilp_backup_<날짜>_pre_<단계>.json`, 통짜 read-modify-write 금지, `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 `--no-build`. K-ICS 파일·`IFRS17_BS.json`·`PL_breakdown*`·`CSM_*`·게이트·예외 등재부·골든(`--update` 금지)·HTML·xlsx·`public_exports`·`data/csm_combo/` 금지(디자이너가 패널을 다시 빌드할 대상 (회사, 분기) 목록만 보고). 커밋·push 금지. 서브에이전트 금지, docling 은 꼭 필요할 때만 1개.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python -`(stdin heredoc) 절대 금지**(고아 CPU 스핀 전례 3회), `encoding` 명시, UTF-8(BOM 없음). RAM 15.5GB, 다른 에이전트 2개 동시 실행. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).
- 단계마다 런로그(`data/disclosure/_meta/ilp_backfill_pre2025_runlog.md` 뒤에 절 추가) 맨 위 「중간 결과」를 갱신(밤새 돌아가므로 중간에 끊겨도 어디까지 됐는지 남게).

### 보고
- 단계별 적재 셀 수·검산·미적재 사유, 재보사 매핑 규칙과 적재 결과, 별첨/원천 필요 목록, owner 결정 필요 사항, 패널 재빌드 필요 (회사, 분기), `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.

## 답변 (recipient 작성 — 처리 후)
ILP 전담 작업 완료(2026-10-11, parser-ifrs17 Sonnet, 약 4.4시간, 토큰 823k): 마스터 3,835→6,111행(+2,276, 기존 행 바이트 동일). 1단계 2024.1Q~3Q·2023.1Q~3Q +1,348행, 2단계 LIC 계산값 항목 16·17 125셀(+250행), 3단계 라이나 8·처브 3셀(+50행), 4단계 재보사 항목 1~8 62셀(+538행)·LIC 14셀(+84행), 5단계 롯데손보 항목 9 6칸 정정(PDF 7건 근거)·추출기 보강. owner 결정 대기: 스위스리 2026.1Q 행합계 파생·하노버 2026.2Q BS 대조 149억·KR0100 R3 5건·메트라이프 PAA 소수점 6칸·국내 항목 9 빈 55칸. downloader: 하나손보 별첨 11회차·하노버 2025.3Q PDF. designer: 348셀 패널 재빌드. 런로그 data/disclosure/_meta/ilp_backfill_pre2025_runlog.md §11~§16.
