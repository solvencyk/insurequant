p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/vlib.py"
s = open(p, encoding="utf-8").read()
s = s.replace('for m in re.finditer(r"<(/?)(TR|TD|TH|TE)\b[^>]*>|([^<]+)", u):', 'for m in re.finditer(r"<(/?)(TR|TD|TH|TE)\b[^>]*>|<[^>]*>|([^<]+)", u):')
s = s.replace('if m.group(2):', 'if m.group(0).startswith("<") and not m.group(2):\n                    continue\n                if m.group(2):')
open(p, "w", encoding="utf-8").write(s)
