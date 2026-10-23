# -*- coding: utf-8 -*-
"""Insert the 23rd-round entries into TODO_parser_ifrs17.md (Status, newest first, <= 5 lines) and docs/changelog_parser_ifrs17.md (before the 22nd-round entry).  Index based, UTF-8 no BOM, LF kept."""
import io
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"

todo_entry = (
    "- **2026-10-24 23차: 이웃 옛 판 칸 점검 2차 적재 — PL 값 90칸(gold 신규 79 · 제자리 교체 11) · 단일분기 114칸 · 이음매 set_dangi +3 / null_dangi +2, 박제·핀·잔차·예외 0 (티켓 `20261024T0300Z`, 미커밋)** — "
    "ABL 35(항목 5 오추출 6 · 9 · 10 · 11 · 파생 7/12) · 동양 6(2024.2Q·3Q 항목 5·6 이 3개월 열 → 누계, 7) · 현대해상 6(2023.1Q·2Q 항목 5·9·10) · 한화생명 19(FY2023 LOB 노트 5·6·9·10·11 + 7/12) · NH농협손보 2023.1Q + DB생명 2023.1Q·2Q OCI 25~32 공란 24칸. 칸마다 필링 줄 번호 독립 재독 1,680 검산 문제 0.\n"
    "  싣지 않은 것: 동양 2024.4Q·2025.1Q(점검 오탐 · owner 손입력 gold) · 미래에셋 2Q·3Q(반올림만) · 흥국화재 항목 16 2칸(마스크 → 새 박제 필요) · NH농협손보 2023.2Q OCI(항목 24 거친 값) · **KB라이프 2024.1Q~3Q CSM = 연쇄가 안 닫힌다**(모의 data_contract RED 2 → 8 = FY경계 3 + CSM_AMORT_IDENTITY 3; 면제·박제 필요 → owner).\n"
    "  게이트: pl_bridge 3787P → 3800P/18F/0NEW 외 SUMMARY 불변 · data_contract RED 2 → 2(MASTER_XLSX_DRIFT 273 = 22차 69 + 이번 204) · 연속성 RED 0 · rule_coverage 104 passed + 2 failed(xlsx 드리프트 + public_exports 드리프트[적재 전에도 실패]) · 골든 `--update` 1줄(master_tables SUMMARY) · PL 골든 통과.\n"
    "  남은 것: ABL 2025.3Q~2026.2Q 항목 5·10 같은 오추출 / 결정 = 흥국화재 항목 16 박제 2건 · 동양 owner gold(2024.4Q·2025.1Q 항목 9·10 부호) · KB라이프 연쇄 면제 / publishing = xlsx `손익분해PL` 270 · `CSM워터폴` 3 · panel · public_exports. 근거·재현 `data/_derived/remaining_20261022/e25_followups/pass2/`(`INDEX.txt`) · changelog 23차.\n"
)

p = f"{ROOT}/TODO_parser_ifrs17.md"
raw = io.open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")
hdr = "## Status (최신 3개)\n\n"
assert s.count(hdr) == 1
i = s.index(hdr) + len(hdr)
s = s[:i] + todo_entry + s[i:]
s = s.replace("> 갱신 2026-10-24 ·", "> 갱신 2026-10-24 ·", 1)
io.open(p, "w", encoding="utf-8", newline="").write(s.replace("\n", "\r\n") if crlf else s)
print("TODO updated; crlf =", crlf)

cl_entry = """## 2026-10-24 (23차: 이웃 옛 판 칸 점검 2차 — PL 값 90칸 · 단일분기 114칸, 박제·핀·잔차·예외 0 — 티켓 20261024T0300Z)

커밋 안 함, push 안 함. 서브에이전트·docling 안 씀. `build_root_masters.main()`·`build_ifrs17_bs`·xlsx 동기화·panel·public_exports·NB·원장(박제)·핸들러·CSM 파일 미접촉. 증거 `data/_derived/remaining_20261022/e25_followups/pass2/`(`INDEX.txt` · 답변 원문 `answer_ticket.md` · 게이트/테스트 `gates/`).

- **범위(오케스트레이터 점검 2회 증거 `sweep_neighbors*/mismatches*.csv`)**: ① ABL KR0070 ② 동양 KR0087 ③ 현대해상 KR0009 ④ 한화생명 KR0068 ⑤ 미래에셋 KR0079 · 흥국화재 KR0005 ⑥ NH농협손보 · DB생명 OCI 공란 ⑦ KB라이프 KR0099 CSM 연쇄 판정(2023.4Q 불가침) ⑧ KDB 보류. 점검 값은 후보일 뿐이라 칸마다 필링 XML 물리 줄에서 다시 읽었다(점검 오탐 4군데: 동양 2024.4Q 는 당기(2025) 표 · 한화 2023.1Q 항목 5 는 2024.1Q 당기 열 · 미래에셋 2Q·3Q 는 다른 정의 행 · 동양 2025.1Q 는 owner gold 와 부호 정의가 다름).
- **방법**: 읽기 스크립트가 후속 필링의 전기·전분기·전반기 누적 열(별도)을 읽어 JSON(물리 줄 포함)을 만들고 `p01_build_plan.py` 가 적용 계약 `p2_plan.json` 을 만든다. 표 소계 = 행 합 · 롤포워드 대조 · 파생 7·12 = 나머지 행 합 · 단일분기 = 인쇄 3개월 열을 모두 통과한 칸만 실었다. 독립 재독 `x01_verify_p2.py`(표준 라이브러리만, 표 첫 줄에서 표를 다시 파싱; 1,680 검산 문제 0, 변이 줄/값/열 394/38/559건 검출). 적재는 e25 적용기에서 `make_apply_p2.py` 로 생성한 `p2_apply.py`(`--snapshot-drift` · `--check` · `--apply` · `--verify`)가 실제 `build_pl()` 을 임시 사본에 돌려 달라지는 칸만 셀 단위로 쓴다. 적재 전 `b01_backup_preload.py` 로 28개 파일을 백업하고 sha256 으로 사본 == 원본을 확인했다.
- **결과**: gold set 1408 → 1487(신규 79 + 제자리 교체 11: 낡은 정적 파생 gold 항목 7·12), null_dangi 121 → 123, set_dangi 37 → 40, 값 90칸 · 단일분기 114칸(회사별 값: ABL 35 · 동양 6 · 현대해상 6 · 한화생명 19 · NH농협손보 8 · DB생명 16), 출처표 33블록 교체. 모두 빌더 소스와 달라 마스크 칸이 아니다(PL 센서스 (1408, 22) → (1487, 22), 박제 0, 원장 바이트 동일). 이음매: 한화생명 2023.2Q 항목 5·6·7 = 인쇄 3개월(`set_dangi`; FY2024 반기보고서가 자기 1분기 비교열을 한 번 더 재작성해 누계 차분 30,976 · 10,213 이 인쇄 30,951 · 5,793 과 어긋남), ABL 2025.3Q 항목 5·7 = 빈칸(`null_dangi`; 2Q 는 최신 노트 열, 3Q 누계는 아직 옛 오추출 열).
- **판정 메모**: ABL 항목 5 옛 값은 재보험 RA(2024.1Q~3Q 196/369/578 = 재보험비용 구간 위험조정변동) 또는 구성내역 (4) 표의 위험조정 변동분(*) 열(2024.4Q 12,282 · 2025.1Q 3,059 · 2Q 6,034)이며 원 공시와 최신 비교열이 같아 판 변경이 아니다. 동양 2024.2Q·3Q 항목 5·6 은 `[3개월, 누적]` 열 중 첫 숫자(3개월)를 집은 것이고 항목 6 은 티켓 목록 밖 형제 칸이지만 항목 7 이 닫히려면 함께 옮겨야 한다(수익·비용 행 합 = 인쇄 합계). 현대해상 장기 열 행 합 = 인쇄 합계, 단일분기 = 인쇄 3개월 천원 단위 일치. OCI 는 마스터·빌더 소스 모두 공란이었고 후속 공시가 유일한 원천이다.
- **싣지 않은 것(칸 단위 사유는 티켓 답변)**: 동양 2024.4Q 항목 4·5·9·10(오탐) · 2025.1Q 항목 9·10(owner 손입력 gold) · 미래에셋 2024.2Q·3Q 항목 5(다른 정의 행, 같은 정의는 반올림 차) · 흥국화재 항목 16 2024.3Q/4Q(빌더 소스와 같아 마스크 → 새 박제 필요) · NH농협손보 2023.2Q OCI(항목 24 거친 값) · KB라이프 2024.1Q~3Q CSM(모의 적재 `kr0099_kblife/c01_chain_sim.py`: 임시 사본을 `gate_overlay.py` 로 게이트에 먹임 → data_contract RED 2 → 8 = `CSM_CONTINUITY_FY_BOUNDARY` 3 [경계 1,621.9억 = 5.37% 대 허용 150.9억] + `CSM_AMORT_IDENTITY_BREAK` 3, 면제·박제 필요 → owner) · KDB 보류.
- **게이트·테스트(적재 전 → 후)**: master_tables pl_bridge 3787P → 3800P/18F/0NEW · oci_vs_bs_aoci 101blank/11bsskip → 97blank/13bsskip, 그 밖의 SUMMARY 필드와 18 FAIL 목록 동일 · data_contract RED 2 → 2(MASTER_XLSX_DRIFT `손익분해PL` 270 + `CSM워터폴` 3 = 22차 잔여 69 + 바뀐 칸 204), YELLOW 168 동일 · 연속성 flagged 1/RED 0 · 워터폴 41 pass · nb_csm 5/5 · live_artifacts RED 2/YELLOW 25 불변 · 골든 `--update` 1줄(master_tables SUMMARY) · rule_coverage 104 passed + 2 failed(xlsx 드리프트, public_exports 드리프트 — 후자는 적재 전 live_artifacts RED 2 로 이미 실패) · PL 골든 · viz 골든 2종 · gold_overlay 10 · identity 24 통과.
- **프로세스 기록**: 현대해상 2023.1Q·2Q `contract_notes` 의 손으로 쓴 IR 팩트시트 계보 항목이 샌드박스 방출기에 지워져 백업에서 원문 그대로 되살렸다(`fix_prov_ir_factsheet.py`; `--verify` 가 curated 출처표 5블록[현대해상 4 · NH농협손보 1]을 방출기 재현 불가로 표시하는 것은 선행 상태). `python3 -` 표준입력 호출 1회가 멈춰 내가 만든 PID 23752 만 `taskkill //F //T` 로 끝냈다. `git push`/`git add -A` 없음.
- **남은 것**: publishing = xlsx `손익분해PL` 270 · `CSM워터폴` 3 동기화, panel/public_exports / 결정 = 흥국화재 항목 16 박제 2건 · 동양 owner gold(2024.4Q·2025.1Q 항목 9·10 부호) · KB라이프 연쇄 면제 / parser = ABL 2025.3Q~2026.2Q 항목 5·10 같은 오추출(마스터 8,826/8,346/1,953/3,770 대 노트 7,271/9,587/2,248/4,081) · 동양 2024.2Q·3Q 항목 9~12 · KB라이프 2024.1Q~2Q PL 재무제표 항목 옛 판 · KDB `1255Z`.

"""
p = f"{ROOT}/docs/changelog_parser_ifrs17.md"
raw = io.open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")
marker = "## 2026-10-24 (22차:"
assert s.count(marker) == 1
j = s.index(marker)
s = s[:j] + cl_entry + s[j:]
io.open(p, "w", encoding="utf-8", newline="").write(s.replace("\n", "\r\n") if crlf else s)
print("changelog updated; crlf =", crlf)
