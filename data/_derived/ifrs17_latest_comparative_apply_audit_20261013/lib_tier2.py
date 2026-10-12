"""Tier-2 (insurance-result notes) recipe discovery by CURRENT-period calibration (own code)."""
import re, itertools, json
from lib_dart import *

def hdr_cols(row):
    names = [c.replace(" ", "") for c in row]
    idx = {}
    for i, n in enumerate(names):
        if n == "장기": idx["장기"] = i
        elif n == "일반": idx["일반"] = i
        elif n == "자동차": idx["자동차"] = i
        elif n in ("합계", "합계"): idx["합계"] = i
    return idx

def note_tables(path):
    """ordered list of tables whose header row has 장기/일반/자동차/합계 (cum column chosen when 3개월|누적 pairs)"""
    out = []
    tabs = load_tables(path)
    for ti, t in enumerate(tabs):
        if not t["rows"]: continue
        h = None
        for ri, r in enumerate(t["rows"][:2]):
            ix = hdr_cols(r)
            if len(ix) == 4: h = (ri, r, ix); break
        if not h: continue
        ri, hrow, ix = h
        nxt = t["rows"][ri + 1] if ri + 1 < len(t["rows"]) else []
        step = 2 if any("누적" in c for c in nxt) else 1
        names_sorted = sorted(ix.items(), key=lambda kv: kv[1])
        pos = {nm: k for k, (nm, _) in enumerate(names_sorted)}
        skip_rows = {ri} | ({ri + 1} if step == 2 else set())
        rows = {}; occ = {}; order = []
        for rj, r in enumerate(t["rows"]):
            if rj in skip_rows: continue
            lab = None; vals = []
            for c in r:
                if lab is None:
                    if c.strip() and not is_num(c): lab = c.replace(" ", "")
                elif is_num(c): vals.append(to_num(c))
                elif c.strip() in ("-", "–", "—"): vals.append(0.0)
            if lab is None or len(vals) < 3: continue
            occ[lab] = occ.get(lab, 0) + 1
            rows[(lab, occ[lab])] = {nm: (vals[k * step + step - 1] if k * step + step - 1 < len(vals) else None) for nm, k in pos.items()}
            order.append((lab, occ[lab]))
        prev = tabs[ti - 1] if ti > 0 else None
        capt = ""
        if prev is not None and len(prev["rows"]) <= 2:
            capt = prev["caption"] + " " + " ".join(" ".join(r) for r in prev["rows"])
        out.append({"idx": t["idx"], "line": t["line"], "rows": rows, "order": order, "cap": capt, "step": step})
    return out

def pairs(nts):
    """group consecutive tables of the same row-label signature into (cur, prior) pairs (caption-checked)"""
    types = []
    i = 0
    while i < len(nts):
        sig = tuple(nts[i]["order"][:2])
        if i + 1 < len(nts) and tuple(nts[i + 1]["order"][:2]) == sig:
            a, b = nts[i], nts[i + 1]
            ca, cb = a["cap"], b["cap"]
            if ("(전)" in ca or "전기" in ca or "전반기" in ca or "전분기" in ca) and ("(당)" in cb or "당기" in cb or "당반기" in cb or "당분기" in cb):
                a, b = b, a
            types.append((a, b)); i += 2
        else:
            types.append((nts[i], None)); i += 1
    return types

def recipe_search(types_cur, target, col, maxterms=3, allowed=None, tol=0.5):
    """all signed combos (up to maxterms) of rows (type_index,label,occ) in column col reproducing target"""
    cand = []
    for ti, (cur, _) in enumerate(types_cur):
        for key, v in cur["rows"].items():
            x = v.get(col)
            if x is None: continue
            if allowed and not re.search(allowed, key[0]): continue
            cand.append(((ti, key[0], key[1]), x))
    res = []
    n = len(cand)
    if abs(target) < tol and False: return res
    for k in range(1, maxterms + 1):
        for combo in itertools.combinations(range(n), k):
            for signs in itertools.product((1, -1), repeat=k):
                s = sum(sg * cand[i][1] for sg, i in zip(signs, combo))
                if abs(s - target) <= tol:
                    res.append(tuple((cand[i][0], sg) for sg, i in zip(signs, combo)))
    return res

def eval_recipe(types, recipe, col, which):
    tot = 0.0
    for (ti, lab, oc), sg in recipe:
        if ti >= len(types): return None
        tb = types[ti][which]
        if tb is None: return None
        v = tb["rows"].get((lab, oc), {}).get(col)
        if v is None: return None
        tot += sg * v
    return tot
