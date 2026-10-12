---
from: orchestrator
to: validation
created: 20261012T1010Z
status: resolved
route: fix
company: MULTI
period: 2023.4Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
### owner 승인 기록 (이 티켓이 승인 근거 — 챗 승인만으로는 등재하지 않는 규칙에 따라 여기에 원문을 남긴다)
owner(sangwook.cho)는 2026-10-12 채팅에서 오케스트레이터가 정리한 「결정 필요 항목 + 제안」 목록(`TODO.md` 「owner 결정 대기」 ①~㉕)에 대해 다음과 같이 답했다: 「4는 웬만하면 생명보험 장기손해보험 … 으로 분류 표준화 / 18은 … / **나머지는 다 승인**」. 즉 아래 항목의 오케스트레이터 제안안을 **그대로 승인**했다. (이 승인은 아래 나열한 등재/면제 항목에 한하며, 다른 면제로 확대하지 않는다.)

### 해 줄 것 (등재·면제는 이 티켓의 항목만; 데이터 셀은 고치지 않는다 — 데이터는 parser 몫)
1. **재보사 「인쇄된 0」 7칸**(투자손익/영업외손익, 마스터에서 보류 중): 칸 목록은 `data/_derived/reinsurer_resweep_20261012/collapse7_state.json`. 원문이 0 을 인쇄했음이 확인된 칸이므로 `data/_gold/user_pl_confirmed_cells.json`(owner-확정 레지스트리)에 7칸을 등재하고, `PL_YTD_COLLAPSE_TO_ZERO`(및 같은 칸을 잡는 다른 룰)가 등재 뒤 이 칸을 면제하는지 **읽는 쪽 분기**를 확인한다(등재부만 있고 룰이 안 읽으면 다음 라운드에 샌다). 복원(`scripts/reinsurer_resweep_pl_followup.py --restore7 --apply`)은 parser-ifrs17 이 한다 — 등재가 끝났다고 보고에 적는다.
2. **서울보증(KR0150) PL 2024.2Q·2024.3Q 통째 구멍**: 사이트가 지난 분기 공시를 내렸고(`NO_RAW_PDF` 최종) 원천이 없다. `_PL_SOURCE_ABSENT` 등재(기존 등재 형식·근거 문자열 규약을 따른다; `PL_SOURCE_ABSENT_LEDGER_DISAGREE` 가 안 걸리게 registry 와 원장 양쪽 일치). 마스터테이블 게이트 `MASTER_HOLE` 해소 확인.
3. **마이브라운 `TIER2_LIMIT_STALE` 5칸**: 거짓 양성으로 등재(근거: 직전분기 SCR 기준 한도 표기 사정 — `scripts/validate_stale_quarter_tables.py` 머리말·기존 `TIER2_LIMIT_STALE` 등재 방식과 같게). 룰이 등재부를 읽는 분기를 확인.
4. **뮌헨(KR1101) 2026.2Q 항목 50·52**: 원문(PDF 텍스트 캐시 `_pdf_text_cache.py`)에 실제로 없는지 먼저 확인한다. 원문에 **없으면** 원천부재 등재(해당 K-ICS 룰의 기존 source-absent 등재 방식), **있으면** 등재하지 말고 보고(parser-kics 가 채움).
5. **CSM 워터폴 대 ILP 기준 차이**(교보·KB라이프·하나생명·롯데: 재작성(restatement) 때문에 기준이 다름): 현재 게이트가 내는 해당 줄(회사·분기·룰)을 먼저 `scripts/validate_data_contract.py`/`validate_master_tables.py --no-build` 최근 출력에서 뽑아 목록으로 적고, owner 승인 사유 「재작성 기준 차이」로 기존 규약대로 등재한다. 예별(KR0004) 2025.4Q 0.0 대 6,227 은 **등재하지 않는다**(parser 가 원문 재확인).
6. 각 등재마다 `docs/kics_gate_exceptions.md`(K-ICS 룰) 또는 해당 레지스트리에 「owner 2026-10-12 승인, 이 티켓」을 근거로 남기고, 등재 직전·직후 게이트 출력 비교(해소된 줄 / 새로 생긴 줄)를 증빙으로 저장(`data/_derived/` 아래 새 폴더). 새 RED 가 생기면 등재로 덮지 말고 보고.

### 규칙
- 등재부·룰의 읽는 쪽 코드만 수정(필요 시 시험 추가·변이시험). 마스터 JSON·xlsx·HTML 수정 금지. 목록에 없는 면제 추가 금지. 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만, `encoding` 명시, 인자를 모르는 스크립트에 `--help` 금지. 시험·게이트는 **한 번에 하나씩 끝까지**(PC 부하; 건너뛰지 말 것). 커밋은 자기 파일만 명시 경로(루트 개인 문서·`data/_derived/qoq_warn.json` 제외·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고 (3~6줄 존댓말)
- 등재 건수(항목별), 읽는 쪽 분기 확인 결과, 해소/신규 줄 비교, 새 RED(있으면 종류별), 커밋 해시. `TODO_validation.md` Status + `docs/changelog_validation.md`.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 f0535af). 등재: 재보사 인쇄된 0 7칸(user_pl_confirmed_cells + 읽는 쪽 PL_YTD_COLLAPSE_CONFIRMED_PENDING), 서울보증 PL 2024.2Q·3Q(_PL_SOURCE_ABSENT, HOLE-PL 2 -> 0), 마이브라운 TIER2_LIMIT_STALE 5칸(TIER2_STALE_FALSE_POSITIVE). 미등재: 뮌헨 2026.2Q 항목 50·52 는 원문 p17 에 인쇄돼 있어 parser-kics 가 채움(51=0 도출 필요 — 원문이 51 을 「-」로 인쇄하면 0), CSM 워터폴 대 ILP 기준 차이는 대조 룰이 코드에 없어 등재할 줄이 없음(룰 설계 선행; 칸 목록은 data/_derived/validation_registrations_20261012/csm_wf_vs_ilp_basis_diff_cells.md; 롯데 2024.3Q -23억 잔차는 별도 분류 필요). 새 RED 0, 골든 master_tables 1종 --update, selftest 102/102.
