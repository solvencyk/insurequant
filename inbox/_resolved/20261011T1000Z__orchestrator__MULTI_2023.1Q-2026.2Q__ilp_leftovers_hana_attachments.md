---
from: orchestrator
to: parser
created: 20261011T1000Z
status: resolved
route: backfill
company: MULTI
period: 2023.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11, 밤새 처리): 「다음 round 로 미뤄 둔 거 전부 스윕」 — `insurance_liability_portfolio.json`(ILP, 보험계약부채 마스터 = 잔여보장요소 LRC + 발생사고요소 LIC) 라운드 3(`data/disclosure/_meta/ilp_backfill_pre2025_runlog.md`, 커밋 완료) 이후 남은 것을 처리한다. downloader 가 하나손해보험 별첨 재무제표(14분기 전부) 등 경영공시 첨부 60건을 받았다(`data/disclosure/FY*/attachments/`, 목록 `data/disclosure/_meta/attachments_manifest.json`, 런로그 `attachments_fetch_runlog_20261011.md`). **이 티켓은 ILP 와 그 사이드카·provenance 만 쓴다.** (BS/PL 마스터는 다른 parser-ifrs17 에이전트가 쓰는 중이니 건드리지 않는다.)

### 작업 (우선순위 순, 단계마다 디스크 저장·런로그 `data/disclosure/_meta/ilp_leftovers_runlog_20261011.md` 맨 위 「중간 결과」 갱신)
1. **하나손보 KR0050 항목 10~15(발생사고요소·DART 부채 기준 합계)**: 경영공시 PDF 는 재무제표를 「첨부 파일 참조」로 둬서 원천이 없었다. 받은 별첨(별도·연결 재무제표 + 주석, Q4 감사보고서)에서 14분기 전부(2023.1Q~2026.2Q) LIC·보험계약부채 합계·LRC 합계를 읽어 ILP 항목 10~15 를 채운다(주석의 「보험계약부채 구성/잔여보장요소·발생사고요소」 표; 마스터 정의·단위는 기존 23사와 동일하게, 하나손보 2-4 가 LIC 를 포함하는지 사이드카 `data/_derived/ilp_includes_lic.json` 규칙도 확인). 별첨 연결/별도 중 마스터 기준(별도) 사용을 확인하고, 하나손보의 기존 BS 앵커(`IFRS17_BS.json` 항목 20)와 대조(읽기만).
2. **3단계 남은 칸**: 라이나 KR0074 PDF 5셀, 처브 KR0100 3셀, 예별 KR0004 2025.4Q — 런로그 라운드 3 「3단계」 절에 칸 목록과 보류 사유가 있다. 새 별첨/새 판(BNP·하나생명·RGA·AXA 이미지 쪽, `attachments_manifest.json` 참조)으로 풀리는 칸이 있으면 풀고, **0 을 지어 넣지 않는다**(예별 2025.4Q 는 선례 그대로).
3. **메트라이프 KR0095 2025.1Q~2026.2Q 6칸(항목 7·8) 정정**: 4-6-2 합계 행에 PAA 가 `0.4`(2026.1Q·2Q 는 `0.5`)억으로 인쇄돼 있는데 마스터는 0.0 이다(옛 추출기가 소수를 0 으로 잘랐다). 라운드 3 §15.5. PDF 로 인쇄값을 다시 확인하고, 확인되면 **셀 단위 + 옛 값 guard + 백업**으로 정정(항목 8 도 같은 크기로 같이). 같은 소수 절단이 다른 회사·분기에도 있는지 마스터 전체를 같은 방식으로 훑는다(추출기 보강 후 재실행 불필요 — 원문 대조 스캔).
4. **현대해상 KR0009 2025.1Q~3Q**: 마스터는 손질된 값이고 생산 추출기는 PAA 열을 VFA BEL 로 읽는다(라운드 3 §15.4 한계 ①). 추출기를 고쳐 재실행 결과가 마스터와 같아지게 한다(footing 이 BAD 로 알려 주는 상태 해소). 마스터 값은 바꾸지 않는다. 추출기 수정은 기존 칸에서 이전에 맞던 결과가 바이트 동일해야 한다(라운드 3 §15.6 회귀 스크립트 `ilp_round3_20261011/t111_extractor_regress.py` 재사용).
5. **포트폴리오 검증기 RED 7**(KR0100 5 · KR0029 1 · 스위스리 2026.1Q 1; 원인·사실 §15.3): **판단·등재는 하지 않는다.** 각 건의 원문 사실과 선택지(정정/예외/정의 결정)를 한 줄씩 정리해 보고에 넣는다(owner 결정용). 새로 풀린 것이 있으면 적재로 해소한다.

### 규칙
- 마스터 쓰기는 **셀 단위 + guard + 백업**, 통짜 read-modify-write 금지, `validate_master_tables.py` 는 `--no-build`. 기존 칸은 3번 정정 외 **변경 0** 을 적재 전후 diff 로 증명. 새 행은 provenance(`insurance_liability_portfolio_provenance.json`)에 basis 와 근거(문서·쪽)를 같이 기록.
- 쓰는 파일: `insurance_liability_portfolio.json`, `insurance_liability_portfolio_provenance.json`, `data/_derived/ilp_*`, 관련 `scripts/load_ilp_*`·`extract_insurance_liability_*`. `IFRS17_BS.json`·`PL_breakdown*`·`CSM_*`·K-ICS 파일·게이트·예외 등재부·골든(`--update` 금지)·HTML·xlsx·`public_exports` 금지. 커밋·push 금지. 서브에이전트 금지, docling 은 꼭 필요할 때만 1개. 동시 에이전트 3개(RAM 15.5GB).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python -`(stdin heredoc) 절대 금지**, `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 단계별 결과(적재 행 수·정정 셀 전후), 하나손보 14분기 표(항목 10~15 값과 BS 앵커 대조), 남은 보류와 사유, RED 7 사실표, 기존 칸 변경 0 증명, 검산기(`validate_insurance_liability_lic.py`·`validate_insurance_liability_portfolio.py`) 전후, `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.

## 답변 (recipient 작성 — 처리 후)
answered by parser-ifrs17 86b055b (2026-10-11): 하나손보 KR0050 11분기 별첨 적재(+66행), 라이나·처브 2023~24 중간분기 +48행, 메트라이프 PAA 소수 12칸 정정, 현대해상 추출기 쪽번호 결함 수정, raw 글롭 7개 배선(테스트 422 passed). 기존 값 변경은 메트라이프 12칸뿐(오케스트레이터가 HEAD 대비 대조 확인). 검산기 RED 전후 동일: LIC 0, 포트폴리오 7(KR0100 5·KR0029 1·KR1102 2026.1Q 1 = owner 결정 대기, 사실표는 런로그 ilp_leftovers_runlog_20261011.md).
