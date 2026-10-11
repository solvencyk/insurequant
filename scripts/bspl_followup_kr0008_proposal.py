#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write the proposal file for the suspect PL master cell KR0008|14|2023.2Q (read-only on masters; writes only a proposal JSON)."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "data/_derived/bspl_followup_20261011"
rc = json.loads((W / "kr0008_lob_recompute.json").read_text(encoding="utf-8"))
q2, q3 = rc["2023.2Q"], rc["2023.3Q"]
out = {
 "_note": "PROPOSAL ONLY -- not applied (the 20261011T0900Z ticket allows no PL cell change). Found while explaining the held PL item-1 cell KR0008|1|2023.2Q (step 6).",
 "cell": "KR0008|14|2023.2Q (PL_breakdown.json 항목 14 일반손익, 백만원 누계)",
 "master_value": q2["master_14"],
 "recomputed_from_dart": q2["일반"],
 "difference": round(q2["master_14"] - q2["일반"], 1),
 "method": "DART 2023 반기보고서 XML data/dart/FY2023_Q2/raw/KR0008_삼성화재해상보험/20230814002808.xml table@line %d '(1) 영업규모, 영업실적 (가) 당기 보험종목별 영업규모, 영업실적' : 보험종목별 (보험수익 - 보험서비스비용 + 재보험수익 - 재보험서비스비용) 를 일반손해보험 계열(자동차 제외) / 자동차 / 장기손해보험 계열로 합산" % q2["table_line"],
 "legs_2023.2Q": {"장기(item 2)": {"recomputed": q2["장기"], "master": q2["master_2"]}, "자동차(item 13)": {"recomputed": q2["자동차"], "master": q2["master_13"]}, "일반(item 14)": {"recomputed": q2["일반"], "master": q2["master_14"]}},
 "table_total_check": {"표 합계행(수익-비용+재보험수익-재보험비용)": round(q2["합계_표"][0] - q2["합계_표"][1] + q2["합계_표"][2] - q2["합계_표"][3], 1), "세 레그 합(recomputed)": round(q2["장기"] + q2["자동차"] + q2["일반"], 1)},
 "method_validation_2023.3Q": {"장기": [q3["장기"], q3["master_2"]], "자동차": [q3["자동차"], q3["master_13"]], "일반": [q3["일반"], q3["master_14"]], "note": "same recomputation reproduces the three master legs of 2023.3Q within 1 백만원"},
 "monotonicity": "일반손익 누계: 2023.1Q 65,824 -> 2023.2Q master 354,530 (recomputed 161,674) -> 2023.3Q 224,173. The master value is higher than the nine-month cumulative.",
 "effect": "PL item 1 (보험손익) of this bucket is blank, so the pl_bridge gate does not see the error; the disclosure candidate for item 1 (12,029억) cannot close the bridge while item 14 is wrong.",
}
(W / "proposed_pl_correction_kr0008_item14_2023.2Q.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps(out, ensure_ascii=False, indent=1)[:1800])
