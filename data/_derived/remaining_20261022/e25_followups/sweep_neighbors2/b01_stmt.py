# -*- coding: utf-8 -*-
"""Part 2, statement items. Read-only. Fixes: (a) KR0005 2025 statements carry contexts without 'SeparateMember' and drop empty cells (missing cell = blank, reported as 0 with flag);
(b) KR0099 label variants (names_extra); (c) KR0009 expense lines printed with a minus sign (neg_expense: magnitudes)."""
import json, sys, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e23_read as X
import e21_read as R
import e21_life as L
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
S2 = ROOT + "/data/_derived/remaining_20261022/e25_followups/sweep_neighbors2/"
unc = {tuple(x) for x in json.load(open(S2 + "uncovered.json", encoding="utf-8"))}
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}

BLANK = {"n": 0}
_orig = R.Stmt.pick_cell
AMBIG = set()
def pick_cell(self, row, role, kind):
    nums = row.cells
    if not any(R.RE_CTX.match(c["ctx"] or "") for c in nums):
        from collections import Counter
        if not hasattr(self, "_modal"):
            cnt = Counter(sum(1 for c in r.cells if c["val"] is not None or c["text"].strip() == "-") for r in self.rows if r.cells)
            self._modal = cnt.most_common(1)[0][0] if cnt else 0
        nv = sum(1 for c in nums if c["val"] is not None or c["text"].strip() == "-")
        if kind == "cum" and self._modal == 4 and nv == 3:
            for c in nums:
                AMBIG.add(c["line"])
    r = _orig(self, row, role, kind)
    if r is None and (not nums or any(R.RE_CTX.match(c["ctx"] or "") for c in nums)):
        # ctx-mode row where the wanted column is an empty printed cell (Stmt drops empty cells) -> blank
        BLANK["n"] += 1
        return dict(text="(blank cell)", val=0.0, line=row.line, ctx="BLANK")
    return r
R.Stmt.pick_cell = pick_cell
_orig_norm = R.norm
def norm2(label):
    s = (label or "").replace("　", "").replace(" ", "").replace(" ", "")
    s = re.sub(r"^[XIVⅠ-ↈ]+\.", "", s)   # mixed ASCII/roman numerals such as 'XⅡ.'
    return _orig_norm(s)
R.norm = norm2

def later(q): return f"FY{int(q[:4]) + 1}_Q{q[5]}"
targets = []
for (c, q, i) in sorted(unc):
    if c in ("KR0099", "KR0005", "KR0009", "KR0032") and not i.startswith("CSM"):
        targets.append((c, q))
targets = sorted(set(targets))
CFG = {"KR0099": dict(names_extra={1: ["보험영업손익"], 17: ["투자영업손익"]}), "KR0009": dict(neg_expense=True)}
out = {}
for c, q in targets:
    if c == "KR0032" and q != "2024.4Q": continue  # other KR0032 quarters are read by sweep 1
    rec = {"items": {}, "file": None, "err": None}
    try:
        st = R.Stmt(c, later(q)); rec["file"] = st.rel; rec["unit"] = st.unit
        BLANK["n"] = 0
        AMBIG.clear()
        t1 = X.read_tier1(st, "prior", "cum", CFG.get(c))
        for i, v in t1.items():
            if isinstance(i, int):
                rec["items"][str(i)] = dict(val=v["val"], line=[p["line"] for p in v["parts"]], printed=[p["printed"] for p in v["parts"]], absent=bool(v.get("absent")),
                                            ambiguous=any(p["line"] in AMBIG for p in v["parts"]))
        p15 = X.presence_015(st, "prior", "cum", insurance_only=(c == "KR0099"))
        rec["items"]["15"] = dict(val=p15["val"], line=[p["line"] for p in p15["parts"]], printed=[p["printed"] for p in p15["parts"]], absent=not p15["present"])
        if c in L.SPEC:
            lr = L.life_is_items(c, later(q), "prior", "cum", st=st)
            for i in (2, 3, 8):
                rec["items"][str(i)] = dict(val=lr[i]["val"], line=[p["line"] for p in lr[i]["parts"]], printed=[p["printed"] for p in lr[i]["parts"]], absent=False)
        rec["blank_cells"] = BLANK["n"]
        # calibration: current column vs master at quarter+4
        BLANK["n"] = 0
        cal = X.read_tier1(st, "cur", "cum", CFG.get(c))
        mq = f"{int(q[:4]) + 1}.{q[5:]}"
        okc = tot = 0
        for i in (1, 17, 20, 22, 24, 31):
            m = pl.get((c, str(i), mq))
            if m is None: continue
            tot += 1; okc += abs(cal[i]["val"] - m) <= 1.0
        rec["calib"] = f"{okc}/{tot}"
        rec["blank_cells_cur"] = BLANK["n"]
    except Exception as e:
        rec["err"] = f"{type(e).__name__}: {str(e)[:300]}"
    out[f"{c}|{q}"] = rec
    print(c, q, rec.get("calib"), rec["err"], len(rec["items"]), "blank", rec.get("blank_cells"), flush=True)
json.dump(out, open(S2 + "b01_stmt.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
