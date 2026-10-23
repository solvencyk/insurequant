# -*- coding: utf-8 -*-
import re
G = ("**게이트·테스트(티켓 4건 + 작업 5 합산, 적재 전 → 후; `gates/gates_compare_all.txt` · `gates/tests_final/`)**: master_tables SUMMARY 는 pl_bridge 3783P(진짜 1351 · 구성상 2089 · 부분 343)/18F/2629S/0NEW → "
     "3787P(1351 · 2093 · 343)/18F/2625S/0NEW 한 필드뿐이다(ABL 항목 6 이 채워져 `3 = 4+5+6+7` 4버킷이 검사받기 시작; 기존 18 FAIL 목록 동일, 새 실패 0, pl_bridge_baseline 무변경). "
     "data_contract 는 RED 0 → 2 = MASTER_XLSX_DRIFT `손익분해PL` 66칸 · `CSM워터폴` 3칸으로 바뀐 칸 수와 정확히 같고(publishing 이 xlsx 동기화) YELLOW 168 은 동일하다. 연속성 flagged 1/RED 0 · 워터폴 41 pass · nb_csm 5/5 · live_artifacts RED 0 불변. "
     "테스트: master_tables 골든은 SUMMARY 한 줄만 `--update`(사유 = 위 pl_bridge 한 필드), 입력 지문은 viz_ifrs17_panels 한 줄만 `--update`(CSM_waterfall.json 51,368,530 → 51,368,526 바이트; viz 골든 산출은 그대로 통과), "
     "PL 골든 1 passed(276초), 규칙 커버리지 105 passed + 1 failed(`test_master_xlsx_clean_state_has_no_red`, 위 xlsx 드리프트와 같은 원인), gold_overlay 10 · identity 14 · tautology 10 · viz 골든 2종 · dividend · deploy_assets 12 · push_gate_wiring 66 통과.")
REVERT = "되돌리기: `e25_followups/backup_before_apply/` 의 사본을 같은 상대 경로로 복사한다(INDEX.txt 6절; `e25_apply.py --revert` 는 작업 5 가 같은 시험 파일을 바꿔 ABORT 한다)."
FILES = "**변경 파일(4건 공통 1회 적재 + 작업 5)**: `PL_breakdown.json` · `PL_breakdown_provenance.json` · `data/_gold/user_pl_cells.json` · `CSM_waterfall.json` · `data/_gold/user_csm_cells.json` · `scripts/build_root_masters.py` · `tests/test_rule_coverage_manifest.py` · `tests/test_gold_overlay_survives_rebuild.py` · `tests/fixtures/master_tables_golden.json` · `tests/fixtures/builder_input_fingerprints.json`. 원장(`gold_overlay_ledger.json`) 박제 변경 0, 제거한 박제 0."

def edit(name, repl_pairs, append):
    s = open(name, encoding="utf-8").read()
    for a, b in repl_pairs:
        assert s.count(a) == 1, (name, a[:60])
        s = s.replace(a, b)
    s = s.rstrip("\n") + "\n\n" + append + "\n"
    open(name, "w", encoding="utf-8", newline="\n").write(s)

# KB라이프: drop the draft gate paragraph, use the common one
s = open("kr0099_kblife.md", encoding="utf-8").read()
i = s.index("**게이트(티켓 4건 + 작업 5 합산 전→후")
j = s.index("**남은 것**")
s = s[:i] + G + "\n\n" + s[j:]
s = s.replace(" 되돌리기: `e25_followups/e25_apply.py --revert --apply` 또는 `backup_before_apply/` 복사.", " " + REVERT)
s = s.rstrip("\n") + "\n\n" + FILES + "\n"
open("kr0099_kblife.md", "w", encoding="utf-8", newline="\n").write(s)

edit("kr0070_abl.md", [(" 되돌리기: `e25_followups/e25_apply.py --revert --apply`.", " " + REVERT)], G + "\n\n" + FILES)
edit("kr0104_nhlife.md", [(" 되돌리기: `e25_followups/e25_apply.py --revert --apply`.", " " + REVERT)], G + "\n\n" + FILES)
edit("kr0010_kbsonbo.md", [(" 되돌리기: `e25_followups/e25_apply.py --revert --apply`.", " " + REVERT)], G + "\n\n" + FILES)
print("ok")
