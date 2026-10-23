import json, subprocess
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
work = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
hr = subprocess.run(["git", "-C", ROOT, "show", "HEAD:PL_breakdown.json"], capture_output=True).stdout.decode("utf-8")
head = {(r["공시분기"], r["항목번호"]): r for r in json.loads(hr) if r["원보험사코드"] == "KR0070"}
L = []
def g(d, q, i, f="값"):
    r = d.get((q, i)); return None if r is None else r.get(f)
qs = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"]
for nm, d in (("HEAD", head), ("WORK", work)):
    L.append("== %s" % nm)
    for q in qs:
        v = {i: g(d, q, i) for i in range(1, 33)}
        s = lambda xs: None if any(v[i] is None for i in xs) else sum(v[i] for i in xs)
        f = lambda x: "None" if x is None else "%.3f" % x
        L.append("%s | 1=%s 2=%s 3=%s 4=%s 5=%s 6=%s 7=%s | 8=%s 9=%s 10=%s 11=%s 12=%s | 15=%s 16=%s" % (q, f(v[1]), f(v[2]), f(v[3]), f(v[4]), f(v[5]), f(v[6]), f(v[7]), f(v[8]), f(v[9]), f(v[10]), f(v[11]), f(v[12]), f(v[15]), f(v[16])))
        L.append("   id: 3-(4+5+6+7)=%s  8-(9..12)=%s  2-(3+8)=%s  1-(2+15-16)=%s  1-(2+13+14+15-16)=%s  17-(18+19)=%s  20-(1+17)=%s  22-(20+21)=%s  24-(22-23)=%s  31-(24+25)=%s  25-(26+27+28+29+30+32)=%s" % (
            f(None if s([3,4,5,6,7]) is None else v[3] - (v[4]+v[5]+v[6]+v[7])),
            f(None if s([8,9,10,11,12]) is None else v[8]-(v[9]+v[10]+v[11]+v[12])),
            f(None if s([2,3,8]) is None else v[2]-v[3]-v[8]),
            f(None if s([1,2,16]) is None else v[1]-(v[2]+(v[15] or 0)-v[16])),
            f(None if s([1,2,16]) is None else v[1]-(v[2]+(v[13] or 0)+(v[14] or 0)+(v[15] or 0)-v[16])),
            f(None if s([17,18,19]) is None else v[17]-v[18]-v[19]),
            f(None if s([20,1,17]) is None else v[20]-v[1]-v[17]),
            f(None if s([22,20,21]) is None else v[22]-v[20]-v[21]),
            f(None if s([24,22,23]) is None else v[24]-(v[22]-v[23])),
            f(None if s([31,24,25]) is None else v[31]-v[24]-v[25]),
            f(None if s([25,26,27,28,30,32]) is None else v[25]-(v[26]+v[27]+v[28]+(v[29] or 0)+v[30]+v[32]))))
open(OUT + "v09_bridge.txt", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
