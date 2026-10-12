import json, csv, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
recs = {}
for r in json.load(open(REPO + "/kics_disclosure.json", encoding="utf-8")):
    recs[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
rows = list(csv.DictReader(open(REPO + "/data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv", encoding="utf-8-sig")))
blocks = []
for r in rows:
    b = (r["code"], r["quarter"])
    if b not in blocks: blocks.append(b)
def f(x):
    try: return float(x)
    except: return None
out = open(here + "/d1_derived.txt", "w", encoding="utf-8")
bad = 0
for code, q in blocks:
    for col in ("값", "값_적용후"):
        v = {i: f(recs[(code, q, i)].get(col)) if (code, q, i) in recs else None for i in (1, 2, 14, 27, 28)}
        exp27 = v[1] / v[14] * 100 if v[1] is not None and v[14] else None
        exp28 = v[2] / v[14] * 100 if v[2] is not None and v[14] else None
        d27 = None if exp27 is None or v[27] is None else v[27] - exp27
        d28 = None if exp28 is None or v[28] is None else v[28] - exp28
        flag = ""
        for nm, d in (("27", d27), ("28", d28)):
            if d is not None and abs(d) > 0.06: flag += f" **{nm} off {d:+.4f}**"; bad += 1
        out.write(f"{code} {q} {col}: i1={v[1]} i2={v[2]} i14={v[14]} | 27 stored={v[27]} exp={exp27 and round(exp27,5)} | 28 stored={v[28]} exp={exp28 and round(exp28,5)}{flag}\n")
out.write(f"\nbad={bad}\n")
