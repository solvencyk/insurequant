p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val/b01_abl.py"
s = open(p, encoding="utf-8").read()
s = s.replace('    g = lambda d, k: d[k][i]\n    it = {}', '    def g(d, k):\n        if k not in d:\n            MISSING.add(k)\n            return 0.0\n        return d[k][i]\n    it = {}')
s = s.replace('out = []\nfails = 0', 'out = []\nfails = 0\nMISSING = set()')
s = s.replace('    P("   sub-checks (cum)', '    P("   missing labels so far (treated 0): " + str(sorted(MISSING)))\n    P("   sub-checks (cum)')
open(p, "w", encoding="utf-8").write(s)
