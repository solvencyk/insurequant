# -*- coding: utf-8 -*-
import json, csv, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
plr = json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in plr}
csmr = json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))
csm = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in csmr}
t = json.load(open("s01_touched.json", encoding="utf-8"))
cq = sorted({tuple(k.split("|")) for v in t.values() for k in v})
cqset = set(cq)
moved = collections.defaultdict(set)
for k, v in t.items():
    if k.startswith("PL"):
        for key, its in v.items():
            moved[tuple(key.split("|"))] |= set(its)
s1 = json.load(open("p1_stmt.json", encoding="utf-8"))
g = json.load(open("p2_generic.json", encoding="utf-8"))
p3 = json.load(open("p3_existing.json", encoding="utf-8"))
p5 = json.load(open("p5_hd.json", encoding="utf-8"))


def lq(q):
    return f"{int(q[:4]) + 1}.{q[5:]}"


KNOWN = {("KR0070", "2024.1Q", "5"), ("KR0070", "2024.2Q", "5"), ("KR0070", "2024.3Q", "5"), ("KR0070", "2024.4Q", "5"), ("KR0070", "2024.4Q", "10"),
         ("KR0070", "2024.1Q", "9"), ("KR0070", "2024.2Q", "9"), ("KR0070", "2024.3Q", "9"), ("KR0070", "2024.1Q", "10"), ("KR0070", "2024.2Q", "10"), ("KR0070", "2024.3Q", "10")}
rows = []
compared = set()


def add(sheet, c, q, it, m, new, cls, conf, filing, line, note, closes="n/a (7/12 residual absorbs; re-derive 7/12 when moved)"):
    d = None if (m is None or new is None) else round(new - m, 3)
    rows.append(dict(sheet=sheet, company=c, quarter=q, item=it, master=m, latest_comparative=None if new is None else round(new, 3), diff_mn=d, cls=cls, confidence=conf,
                     moved_in_bucket=("Y" if moved.get((c, q)) else "N"), block_closes_if_moved=closes, filing=filing, xml_line=line, note=note))


def ids_ok(pv):
    try:
        a = (abs(pv["20"]["val"] - pv["1"]["val"] - pv["17"]["val"]) < 1.5 and abs(pv["22"]["val"] - pv["20"]["val"] - pv["21"]["val"]) < 1.5
             and abs(pv["24"]["val"] - pv["22"]["val"] + pv["23"]["val"]) < 1.5)
        return "Tier1 identities 20=1+17, 22=20+21, 24=22-23 on the latest vector: " + ("YES" if a else "NO")
    except Exception:
        return "n/a"


ART = {("KR0009", i) for i in ("16", "23", "18", "19")}
for k, v in sorted(s1.items()):
    c, q = k.split("|")
    if not v["prior"]:
        continue
    cl = ids_ok(v["prior"])
    for i, d in v["prior"].items():
        if not isinstance(d, dict) or (c, i) in ART:
            continue
        m = pl.get((c, i, q))
        if m is None:
            if abs(d["val"]) >= 0.5 and not d.get("absent"):
                compared.add((c, q, i))
                kn = "KNOWN_DECISION_KB_item16_blank" if (c == "KR0010" and i == "16") else "MASTER_BLANK"
                add("PL", c, q, i, None, d["val"], kn, "high", v["file"], d["line"], "statement prints a value, master cell is empty", cl)
            continue
        compared.add((c, q, i))
        diff = d["val"] - m
        if abs(diff) < 1e-3:
            continue
        if abs(diff) <= 1.0:
            add("PL", c, q, i, m, d["val"], "ROUNDING_PM1", "high", v["file"], d["line"], "|diff|<=1 mn (printed-unit rounding)", cl)
        elif c == "KR0072":
            add("PL", c, q, i, m, d["val"], "HELD_KDB", "high", v["file"], d["line"], "KDB held (consolidated-vs-separate decision pending)", cl)
        elif i == "15":
            add("PL", c, q, i, m, d["val"], "UNVERIFIED_ITEM15_PRESENCE", "low", v["file"], d["line"],
                "master 0.0 (builder default) vs printed 기타영업수익 in the later statement; row may be investment-side; row concept not verified", cl)
        else:
            add("PL", c, q, i, m, d["val"], "VINTAGE_STATEMENT", "high", v["file"], d["line"], "statement line differs", cl)
for x in p3:
    if x["sheet"] == "PL" and "latest" in x:
        compared.add((x["code"], x["q"], x["item"]))
        if x["master"] is None or abs(x["diff"]) < 1e-3:
            continue
        add("PL", x["code"], x["q"], x["item"], x["master"], x["latest"], "ROUNDING_PM1" if abs(x["diff"]) <= 1.0 else "VINTAGE_NOTE", "high", x["src"], x["line"], f"{x['how']} (e21 reader, prior column)")
SKIP_GENERIC = {"KR0001", "KR0003", "KR0010", "KR0009", "KR0099"}
EXCL = {("KR0070", "5")}
for k, rec in sorted(g.items()):
    c, q = k.split("|")
    if c in SKIP_GENERIC or "prior" not in rec:
        continue
    for it in ("4", "5", "9", "10"):
        pr = rec["prior"].get(it)
        cu = rec.get("cur", {}).get(it)
        mlater = pl.get((c, it, lq(q)))
        if not pr:
            continue
        j = None
        if cu and mlater is not None:
            for idx, x in enumerate(cu):
                if abs(abs(x["val"]) - abs(mlater)) < 0.5:
                    j = idx
                    break
        sign = 1 if it in ("4", "5") else -1
        if j is not None and j < len(pr):
            val = sign * abs(pr[j]["val"])
            cal = "CAL"
        elif len(pr) == 1:
            val = sign * abs(pr[0]["val"])
            cal = "UNCAL1"
            j = 0
        else:
            continue
        if (c, it) in EXCL:
            continue
        m = pl.get((c, it, q))
        compared.add((c, q, it))
        if m is not None and abs(m - val) < 1.0:
            continue
        key = (c, q, it)
        if key in KNOWN:
            cls = "KNOWN_ABL"
        elif c == "KR0072":
            cls = "HELD_KDB_UNVERIFIED_ROW"
        elif key == ("KR0070", "2025.1Q", "5"):
            cls = "UNVERIFIED_ROW_CONCEPT"
        elif c == "KR0087" and it == "10":
            cls = "VINTAGE_NOTE_AND_SIGN"
        elif m is None:
            cls = "MASTER_BLANK"
        elif abs(val - m) <= 3 and c == "KR0070":
            cls = "VINTAGE_NOTE_SMALL"
        else:
            cls = "VINTAGE_NOTE"
        conf = "medium" if cal == "CAL" else "low"
        add("PL", c, q, it, m, val, cls, conf, rec["file"], pr[j]["line"],
            f"generic label reader ({cal}: current column reproduces master {lq(q)} item {it}); printed {pr[j]['printed']} label {pr[j]['label'][:40]}")
seen = {}
for q, it, sect, m, v, d, ln, ts in p5:
    seen[(q, it)] = seen.get((q, it), 0) + 1
    ii = it if seen[(q, it)] == 1 else (9 if it == 4 else 10)
    val = abs(v) * (1 if ii in (4, 5) else -1)
    mm = pl.get(("KR0009", str(ii), q))
    compared.add(("KR0009", q, str(ii)))
    if mm is None or abs(val - mm) < 1.0:
        continue
    add("PL", "KR0009", q, str(ii), mm, val, "VINTAGE_NOTE", "high", f"data/dart/FY{int(q[:4]) + 1}_Q{q[5]}/raw/KR0009_현대해상 (table@L{ts})", ln, "HD prior-period cumulative table (e23 caption rule), 장기 column")
for x in p3:
    if x["sheet"] == "CSM" and "raw" in x:
        vec = x["raw"].get("vec_exact") or x["raw"].get("vec")
        for i in range(1, 7):
            compared.add((x["code"], x["q"], "CSM" + str(i)))
            m = csm.get((x["code"], str(i), x["q"]))
            if m is None or abs(m - vec[i - 1]) <= 0.06:
                continue
            add("CSM", x["code"], x["q"], str(i), m * 100, vec[i - 1] * 100, "VINTAGE_CSM", "high", x["raw"]["src"], "", "CSM waterfall prior-period table (separate basis); eok converted to mn; PL item 4 vs CSM item 5 identity would also break unless PL4 moves together")
rows.sort(key=lambda r: -abs(r["diff_mn"] or 0))
cols = ["sheet", "company", "quarter", "item", "master", "latest_comparative", "diff_mn", "cls", "confidence", "moved_in_bucket", "block_closes_if_moved", "filing", "xml_line", "note"]
with open("mismatches.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
master_cells = {(c, q, i) for (c, i, q), v in pl.items() if (c, q) in cqset and v is not None and i.isdigit()}
csm_cells = {(c, q, "CSM" + i) for (c, i, q), v in csm.items() if (c, q) in cqset and v is not None and i.isdigit()}
allc = master_cells | csm_cells
comp_in = {x for x in compared if x in allc}
print("touched company-quarters", len(cq), "| master PL cells present", len(master_cells), "| CSM cells", len(csm_cells))
print("compared (present in master and read)", len(comp_in), f"= {100 * len(comp_in) / len(allc):.1f}%")
byc = collections.defaultdict(collections.Counter)
for r in rows:
    byc[r["company"]][r["cls"]] += 1
for c in sorted(byc):
    print(c, dict(byc[c]))
real = [r for r in rows if r["cls"] != "ROUNDING_PM1" and r["diff_mn"] is not None]
print("rows", len(rows), "non-rounding with a diff", len(real))
print("by class", dict(collections.Counter(r["cls"] for r in rows)))
for r in real[:15]:
    print(r["company"], r["quarter"], r["item"], r["master"], r["latest_comparative"], r["diff_mn"], r["cls"], r["confidence"])
cc = collections.defaultdict(lambda: [0, 0])
for (c, q, i) in allc:
    cc[c][0] += 1
for (c, q, i) in comp_in:
    cc[c][1] += 1
print({c: f"{v[1]}/{v[0]}" for c, v in sorted(cc.items())})
