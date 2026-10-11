---
from: orchestrator
to: parser
created: 20261011T1130Z
status: open
route: backfill
company: MULTI
period: 2023.1Q-2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11): 「경영공시로 지금 수준 granularity 는 충분히 다 채울 수 있다 — 전부 다시 채워와라.」 1차(`bd64513`)·후속(`c2d36f8`)에서 BS +1,747칸·PL +540칸을 채웠다. 남은 것은 두 덩어리다: **(A) 후속에서 근거까지 만들고 적용은 안 한 정정 제안** 과 **(B) downloader 가 받아 온 별첨·이미지 쪽 원천으로 채울 수 있는 칸**. 같은 런로그 `data/disclosure/_meta/bspl_granularity_runlog.md` 에 이어서 쓴다(맨 위 「중간 결과 — 3차」 신설).

### (A) 정정 제안 적용 — `data/_derived/bspl_followup_20261011/proposed_*.json`
각 제안을 **적용 직전에 한 번 더 원천으로 확인**(제안 파일의 근거 쪽·표를 다시 열어 값 재현)하고, 맞으면 **셀 단위 + 옛 값 guard + 백업**으로 정정, 오버레이/provenance 에 근거를 남긴다. 재현이 안 되면 적용하지 않고 이유를 보고.
1. `proposed_pl_correction_kr0008_item14_2023.2Q.json` — 삼성화재 KR0008 PL 항목 14 2023.2Q: 마스터 354,530백만원 대 DART 표 재계산 161,674. (항목 14 에 걸린 하위·합계 항목(15 등)과 `값_당분기` 도 같이 점검.)
2. `proposed_pl_corrections_kr0072_item10.json` — KDB생명 KR0072 PL 항목 10 4칸: 누계 열 대신 3개월 열이 들어간 결함. `값`(YTD)·`값_당분기` 둘 다 규칙에 맞게. 같은 파일의 `other_companies_checked`·`kr0071_unverified_observation`(KR0071 미검증 관찰)도 이어서 검증하고 필요하면 같은 방식으로.
3. `proposed_bs_corrections_cfs_to_ofs_kr0070_kr0079.json` — ABL생명 KR0070·미래에셋생명 KR0079 2023.1Q·2Q 마스터 총계가 연결 값인 곳을 별도(OFS)로. (BS 마스터는 전사 별도 고정 — `reference_dart_fs_api_bs_basis`.)
4. `proposed_kr1011_item13_cells.json` — IBK연금 KR1011 항목 13.
5. 한화생명 KR0068 항목 10 2023.2Q: 마스터는 틀린 값(DART 별도 요약 BS 와 8-1 이 모두 1,081,513). 정정.
6. BS 항목 10 에 「현금및현금성자산」 대신 「현금및예치금」 이 들어간 칸(KR1000 7개 · KR0001 12개 · KR0071 11개): 마스터 항목 10 의 정의(항목명·다른 분기 계열)를 확인해 **정의에 맞는 라인으로 일관되게** 정정. 계열 정의가 불분명하면 정정하지 말고 근거 표와 함께 보고(owner 결정).
7. DART 별도 요약 BS 로 채울 수 있는 빈 칸 9개(후속 보고): 채운다.
8. 처브라이프 KR0100 항목 20(`kr0100_item20_table.json`): 후속 보고의 권고는 K-IFRS 라인 정의인데 마스터 혼재 10칸의 정정은 **owner 결정 대기이니 하지 않는다**(손대지 말 것).

### (B) 별첨·이미지 쪽 원천으로 채우기
정본 명세는 downloader 티켓 `inbox/parser/20261010T2350Z__downloader__MULTI_2023.1Q-2026.2Q__attachments_raw_ready_bspl.md` 이다(먼저 읽을 것; 그 티켓도 이 건에서 같이 처리하되 종결은 오케스트레이터). 받은 파일은 `data/disclosure/FY*/attachments/`(목록 `data/disclosure/_meta/attachments_manifest.json`, 칸별 결과 `data/disclosure/_meta/attachments_20261011/census_result.json`).
1. **하나손해보험 KR0050 14분기**(별도 재무제표+주석, Q4 감사보고서): 요약표에 없던 항목(10 현금·14 재보험계약자산·15 유형자산·20 보험계약부채·21 재보험계약부채·24 기타부채 등)을 마스터 정의·단위(백만원 계열)에 맞게 채운다. 기존 DART 앵커가 없으니 연말 감사 재무제표 라인이 앵커(1차와 같은 보정 원칙). 신판 2025.4Q(`_v20261010`)의 대출채권 표 정정(p21·22, 예 합계 4,950→5,127)이 BS 항목 13 등에 영향이 있는지 확인(K-ICS 레인 보고 §3.1 참고: `data/disclosure/_meta/kics_editions_runlog_20261011.md`).
2. **신한이지 2칸·카카오페이 2칸**(별첨 수령분) 채움.
3. **이미지 쪽으로 raw 에 이미 있는 25칸**: BNP카디프 KR0075 9 · 하나생명 KR0097 9 · RGA KR1105 4 · AXA KR0049 3 — 표가 텍스트가 아닌 이미지 쪽이라 텍스트층 판독이 놓쳤다. 렌더링(190~240dpi) + 육안/비전 판독으로 8-1·8-2 전체 줄을 읽어 1차와 같은 보정·검산(자산 = 부채 + 자본, 라인 앵커)으로 적재. 판독 불확실한 칸은 적재하지 말고 쪽·사유와 함께 보류 목록으로(틀린 값을 싣느니 빈 칸).
4. **연말 5칸**(라이나 2 · BNP 1 · 하나생명 1 · 처브 1): `data/dart` 에 이미 있는 감사 XML 로 채운다.
5. **발행사가 스캔본을 올린 4칸**(카카오 2024.2Q·3Q · 하노버 2023.3Q · 하나생명 2024.2Q)도 이미지 판독으로 시도. AIA 3분기는 통째 스캔이지만 마스터 빈 항목이 없다 — 확인만. 하노버 2025.3Q 는 발행사 미게시, BNP 2024.2Q 는 원문이 잘려 있음(둘 다 원천 부재로 목록 유지).
6. 위 적재로 풀리는 **보류(HOLD) 칸**이 있는지 다시 평가한다(후속 보고: 남은 보류 378칸 8종 82군, `hold_reasons_5c.md`).

### 규칙
- 마스터 쓰기는 **셀 단위 + guard + 백업**, 통짜 read-modify-write 금지, `build_root_masters.py main()`·`build_ifrs17_bs.py` 통째 실행 금지, `validate_master_tables.py` 는 반드시 `--no-build`(`--help` 포함, 인자 없이 실행 금지). (A) 정정 외 **기존 칸 변경 0** 을 적재 전후 diff 로 증명(정정 칸은 목록으로 따로).
- 이 티켓이 쓰는 파일: `IFRS17_BS.json`, `PL_breakdown*.json`, `data/dart/viz/bs_manual_overrides.json`, `data/_derived/bs_from_disclosure*`, `data/_derived/bspl_*`. K-ICS 파일·ILP·`CSM_*`·게이트·예외 등재부·골든(`--update` 금지)·HTML·xlsx·`public_exports` 금지(다른 에이전트가 ILP 를 쓰는 중, downloader 가 raw 를 받는 중). 커밋·push 금지. 서브에이전트 금지, docling 은 꼭 필요할 때만 1개. 동시 에이전트 3개(RAM 15.5GB).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python3`·`python -`(stdin heredoc) 절대 금지**, `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- (A) 항목별 적용/미적용+사유, 정정 칸 전후 값, (B) 적재 칸 수(회사×분기), 판독 방식, 보류 목록, 새 항등식·게이트(`validate_data_contract`·`validate_master_tables --no-build`) 전후, 기존 칸 변경 0 증명, 남은 원천 부재 목록, `TODO_parser_ifrs17.md` Status + `docs/changelog_parser_ifrs17.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
