# -*- coding: utf-8 -*-
"""e21 plan library: independent per-bucket PL reads (Tier-1 statement + life IS lines + 손보 LOB notes + PL4 notes) with printed-cell citations.
Every value is built from printed cells only (value = sum of sign * printed / scale, optionally |sum|) plus, for the derived residual items 7 / 12 of life companies, explicit operands
(the HEAD master value or, for PL4 of 한화 / 미래에셋, the PL4 value of the same plan) -- no value is copied from the measure-phase candidates (they are only compared with)."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_csm as C  # noqa: E402
import e21_csm2 as C2  # noqa: E402
import e21_life as L  # noqa: E402
import e21_read as R  # noqa: E402
import e21_t2 as T  # noqa: E402
import e21_t2b as T2  # noqa: E402

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e21_ready25"
MEAS = ROOT / "data" / "_derived" / "remaining_20261022" / "e20_held_and_remaining" / "measure"
TIER1 = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
UNIT_DIV = {"원": 1e6, "천원": 1e3, "백만원": 1.0}


def head_bytes(rel):
    return subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout


def head_json(rel):
    return json.loads(head_bytes(rel).decode("utf-8"))


def later_fy(q):
    return f"FY{int(q[:4]) + 1}_Q{q[5]}"


def orig_fy(q):
    return f"FY{int(q[:4])}_Q{q[5]}"


def num_of(t):
    t = (t or "").replace(",", "").strip()
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    return -float(t) if neg else float(t)


def pdict(p, unit=None):
    """normalise a part (Part object or dict) to the plan citation format"""
    d = p.d() if hasattr(p, "d") else dict(p)
    d.setdefault("abs", False)
    if unit is not None and not d.get("unit"):
        d["unit"] = unit
    d["contribution_mn"] = round(d["contribution_mn"], 6)
    return d


def flip(p):
    d = dict(p)
    d["sign"] = -p["sign"]
    d["contribution_mn"] = round(-p["contribution_mn"], 6)
    return d


def cell(val, parts, formula, src, operands=None, kind="sum", unit=None, abs_of_sum=False):
    return dict(val=round(val, 6), parts=[pdict(p, unit) for p in parts], formula=formula, src=src, operands=operands or [], kind=kind, abs_of_sum=abs_of_sum)


def value_of(c):
    s = sum(p["contribution_mn"] for p in c["parts"])
    if c.get("abs_of_sum"):
        s = abs(s)
    return s + sum(o["sign"] * o["value"] for o in c["operands"])


def tier1_cells(st, vec, role):
    out = {}
    for i in TIER1:
        v = vec[i]
        val = sum(p.sign * p.val_mn for p in v["parts"])
        out[i] = cell(val, v["parts"], "statement line" if len(v["parts"]) == 1 else "derived from statement lines (production definition)", f"{st.rel} {role}/cum unit {st.unit}", unit=st.unit)
        out[i]["absent"] = bool(v.get("absent"))
    out[25]["leaf_all_sum"] = round(vec["_leaf_all_sum"], 6)
    return out


def derive_2_7_12(r, master, code, q, extra_ops):
    """items 2 / 7 / 12 from a reader result r ({item: {val, parts, src}}).  Operands of 7 (4,5,6) / 12 (9,10,11) come from r when the reader reads them,
    else from `extra_ops` (plan values) else from the HEAD master."""
    out = {}
    if 3 in r and 8 in r:
        out[2] = cell(r[3]["val"] + r[8]["val"], r[3]["parts"] + r[8]["parts"], "3 + 8", r[3]["src"], kind="derived")
    for tgt, base, ops in ((7, 3, (4, 5, 6)), (12, 8, (9, 10, 11))):
        if base not in r:
            continue
        parts = list(r[base]["parts"])
        operands = []
        val = r[base]["val"]
        ok = True
        for o in ops:
            if o in r:
                parts += [flip(p) for p in r[o]["parts"]]
                val -= r[o]["val"]
            else:
                mo = extra_ops.get(o)
                src = "plan"
                if mo is None:
                    mo = master.get((code, o, q))
                    src = "master HEAD"
                if mo is None:
                    ok = False
                    break
                operands.append(dict(item=o, sign=-1, value=mo, source=src))
                val -= mo
        if ok:
            out[tgt] = cell(val, parts, f"{base} - ({'+'.join(str(o) for o in ops)})", r[base]["src"], operands=operands, kind="derived")
    return out


def read_bucket(code, q, kind, master, role="prior"):
    """-> dict(meta, items={item: cell}) for one (company, quarter) from the LATER filing"""
    fy = later_fy(q)
    st = R.Stmt(code, fy)
    vec = R.read_vector(st, role, "cum")
    meta = dict(code=code, quarter=q, kind=kind, later_fy=fy, file=st.rel, unit=st.unit, fmt=st.fmt, role=role, rcept=Path(st.rel).stem)
    items = tier1_cells(st, vec, role)
    p15 = L.presence_015(st, role, "cum")
    items[15] = cell(p15["val"], p15["parts"], p15["formula"], p15["src"], unit=st.unit)
    items[15]["present"] = p15["present"]
    extra_ops = {}
    r = {}
    if kind == "kb":
        r = T.kb_read(code, q)
    elif kind == "lotte":
        r = T.lotte_combined_read(code, q) if q in ("2023.1Q", "2023.2Q", "2024.1Q") else T2.lotte_split_read(code, q)
    elif kind == "meritz":
        r = T.meritz_read(code, q)
    elif kind in ("life", "kblife_fix"):
        lr = L.life_is_items(code, fy, role, "cum", st=st)
        r = {3: lr[3], 8: lr[8]}
        if code == "KR0068":
            n = C.hanwha_note_pl4(q)
            p = n["part"]
            part = dict(label=p["label"], line=p["line"], printed=p["printed"], sign=1, abs=False, unit=p["unit"], contribution_mn=round(num_of(p["printed"]) / UNIT_DIV[p["unit"]], 6))
            items[4] = cell(abs(part["contribution_mn"]), [part], "|보험수익 note: 서비스제공에 따른 보험계약마진의 변동, 합계(누적)|", n["src"], abs_of_sum=True)
            extra_ops[4] = items[4]["val"]
        elif code == "KR0079" and q in ("2024.1Q", "2024.2Q", "2024.3Q"):
            n = C2.mirae_q1() if q == "2024.1Q" else C2.mirae_wide(q)
            parts = []
            for pp in n["pl4_parts"]:
                v = num_of(pp["printed"]) if pp["printed"].strip() not in ("", "-") else 0.0
                parts.append(dict(label=pp["label"], line=pp["line"], printed=pp["printed"], sign=1, abs=False, unit=pp["unit"], contribution_mn=round(v / UNIT_DIV[pp["unit"]], 6)))
            val = abs(sum(p["contribution_mn"] for p in parts))
            items[4] = cell(val, parts, "|sum of the CSM-amortisation cells of the later filing's prior block (production Era-1: 합계 col of the 5 product tables; Era-2: whole-row sum)|", n["src"], abs_of_sum=True)
            extra_ops[4] = items[4]["val"]
    if kind in ("life", "kblife_fix"):
        for k in (3, 8):
            items[k] = cell(r[k]["val"], r[k]["parts"], r[k]["formula"], r[k]["src"])
        items.update(derive_2_7_12(r, master, code, q, extra_ops))
        return dict(meta=meta, items=items, reader=r)
    for k, v in r.items():
        if isinstance(k, int):
            items[k] = cell(v["val"], v["parts"], v["formula"], v["src"])
    items.update(derive_2_7_12({k: v for k, v in r.items() if isinstance(k, int)}, master, code, q, extra_ops))
    return dict(meta=meta, items=items, reader=r)
