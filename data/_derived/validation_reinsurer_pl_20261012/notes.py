# -*- coding: utf-8 -*-
import json
side = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown_provenance.json", encoding="utf-8"))
for k in ("merge_note_20261012_withhold7", "merge_note_20261012_r1", "merge_note_20261012_reinsurer_resweep", "merge_note_20261012_item4_addon"):
    print(k, json.dumps(side[k], ensure_ascii=False)[:1800])
    print()
