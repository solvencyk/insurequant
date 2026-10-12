# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.loads(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/reinsurer_csm_resweep_20261012/spec_wf_vision.json", "rb").read().decode("utf-8"))
print(type(d), list(d.keys())[:10] if isinstance(d, dict) else len(d))
s = json.dumps(d, ensure_ascii=False, indent=1)
i = s.find("KR1107")
print(s[max(0, i - 400): i + 3500])
