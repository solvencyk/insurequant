p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/v03_gold_compact.py"
s = open(p, encoding="utf-8").read()
s = s.replace('def isco(e):', 'def D(e):\n    return e if isinstance(e, dict) else {"공시분기": e[1], "항목번호": e[2], "값": e[3:] }\ndef isco(e):', 1)
s = s.replace('s, e = hs[k]; L.append("REMOVED', 's, e = hs[k]; e = D(e); L.append("REMOVED').replace('s, e = ws[k]; L.append("ADDED', 's, e = ws[k]; e = D(e); L.append("ADDED').replace('s, e = hs[k]; L.append("   KEEP', 's, e = hs[k]; e = D(e); L.append("   KEEP')
open(p, "w", encoding="utf-8").write(s)
