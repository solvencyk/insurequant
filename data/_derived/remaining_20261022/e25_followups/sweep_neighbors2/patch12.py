s = open("p20_compile.py", encoding="utf-8").read()
s = s.replace('"csm": "VINTAGE_CSM"}[src.split(":")[0]]', '"csm": "VINTAGE_CSM", "derived": "VINTAGE_DERIVED"}[src.split(":")[0]]')
s = s.replace('"note:" + r["source"], conf=r.get("confidence", "high")', '("stmt:" if r["source"].startswith("stmt") else "note:") + r["source"], conf=r.get("confidence", "high")')
open("p20_compile.py", "w", encoding="utf-8").write(s)
