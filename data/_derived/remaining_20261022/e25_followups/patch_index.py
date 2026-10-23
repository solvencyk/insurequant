# -*- coding: utf-8 -*-
p = "INDEX.txt"
s = open(p, encoding="utf-8").read()
a = s[s.index("6) 되돌리는 순서"):]
b = """6) 되돌리는 순서
   a. kr0003_lotte_csm_blank/c02_apply_csm.py --revert --apply   (CSM_waterfall.json · user_csm_cells.json; 적재 직후 해시가 그대로일 때만 동작 — c06 이후 해시는 매니페스트에 갱신돼 있다)
   b. e25_apply.py --revert --apply 는 이제 ABORT 한다: 적재 직후 해시 조건이 깨졌다(tests/test_rule_coverage_manifest.py 에 작업 5 시험이 더해졌다). 안전한 방법 = backup_before_apply/ 의 사본을 같은 상대 경로로 복사:
      PL_breakdown.json · PL_breakdown_provenance.json · data/_gold/user_pl_cells.json (티켓 1~4 적재분)
   c. 코드·시험·fixture 는 같은 방법으로 복사: scripts/build_root_masters.py · tests/test_gold_overlay_survives_rebuild.py · tests/test_rule_coverage_manifest.py · tests/fixtures/master_tables_golden.json · tests/fixtures/builder_input_fingerprints.json
   백업: backup_before_apply/ (적재 직전 30개 파일, SHA256_preload.txt 로 사본 == 원본 확인; 이후 git checkout 으로 되돌리지 말 것 — 작업트리에 다른 미커밋 변경이 있을 수 있다).
"""
s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
