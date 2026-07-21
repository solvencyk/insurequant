"""Dedup + scale-sanity for root kics_disclosure.json (validation stage, owner 2026-06-13).

Owner directive: 컬럼조합(코드·항목번호·공시분기)+값이 모두 같은 중복행은 전삭제;
key 같고 값만 다른 행은 항등식으로 정답 1개를 채택하고 나머지 trash 삭제.

Dedup rules per (원보험사코드, 항목번호, 공시분기) group with >1 row:
  - 값까지 동일(exact dup)         -> 1행으로 축약(가장 정밀한 raw 유지).
  - 값 상이:
      * 비영(non-zero) 후보 1개      -> 그 값 채택(나머지 0은 fill 누출).
      * item 23/24/25/26            -> (code,q) 단위로 23 = 24+25+26 closure 풀어 채택.
      * item 27/28                  -> 정의 항등식(27=item1/14*100, 28=item2/14*100)에 최근접 채택.
      * 그 외 비영 후보 다수          -> 최빈값; 동률이면 FLAG(사람 판단).
Scale-sanity:
  - item2(기본자본) > item1(지급여력금액)는 불가 -> item2 ÷100(스케일오류), item28 = item2/item14*100 재계산.
    (하나손해 2026.1Q 사례. 카카오페이式 고비율은 item2<=item1이라 정상 보존.)

idempotent. backup -> kics_disclosure.json.bak. report -> artifacts/kics_validation/dedup_report_<stamp>.md.
Run: python scripts/dedup_kics_disclosure.py
"""
from __future__ import annotations
import json, sys, itertools
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "kics_disclosure.json"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
REPORT = ROOT / "artifacts" / "kics_validation" / f"dedup_report_{STAMP}.md"


def pv(v):
    s = str(v).replace(",", "").replace("%", "").replace("△", "-").strip()
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return None


def best_raw(chosen, pairs):
    """raw string whose float == chosen (가장 긴=정밀). 없으면 깔끔한 숫자 포맷."""
    matches = [raw for raw, fv in pairs if fv is not None and abs(fv - chosen) < 1e-9]
    if matches:
        return max(matches, key=lambda r: len(str(r)))
    s = f"{chosen:.10f}".rstrip("0").rstrip(".")
    return s if s else "0"


rows = json.loads(SRC.read_text(encoding="utf-8"))
G = defaultdict(list)
for i, r in enumerate(rows):
    G[(r["원보험사코드"], r["항목번호"], r["공시분기"])].append(i)

# candidate floats / pairs per key
cand = {}   # key -> {"floats": set, "pairs": [(raw,float)], "n": rowcount}
for key, idxs in G.items():
    pairs = [(rows[i]["값"], pv(rows[i]["값"])) for i in idxs]
    floats = set(fv for _, fv in pairs if fv is not None)
    cand[key] = {"floats": floats, "pairs": pairs, "n": len(idxs)}

report = {"exact_dup": [], "single_nz": [], "closure": [], "ratio": [], "modal": [], "flag": [], "scale": []}
chosen_raw = {}   # key -> raw string


def code_q_val(code, q, item):
    k = (code, item, q)
    if k in chosen_raw:
        return pv(chosen_raw[k])
    if k in cand and cand[k]["floats"]:
        nz = [v for v in cand[k]["floats"] if v != 0]
        return nz[0] if len(nz) == 1 else (sorted(cand[k]["floats"])[0])
    return None


# ---- pass 1: non-(23-26) groups + provisional ----
for key, info in cand.items():
    code, item, q = key
    floats, pairs = info["floats"], info["pairs"]
    if info["n"] == 1:
        chosen_raw[key] = pairs[0][0]
        continue
    if len(floats) <= 1:                      # exact dup (또는 동값 다정밀)
        v = next(iter(floats)) if floats else 0.0
        chosen_raw[key] = best_raw(v, pairs)
        report["exact_dup"].append((key, info["n"], chosen_raw[key]))
        continue
    nz = [v for v in floats if v != 0]
    if len(nz) == 1:
        chosen_raw[key] = best_raw(nz[0], pairs)
        report["single_nz"].append((key, sorted(floats), chosen_raw[key]))
        continue
    if item in (23, 24, 25, 26):
        continue                              # closure pass
    if item in (27, 28):
        continue                              # ratio pass
    cnt = Counter(fv for _, fv in pairs if fv is not None)
    top = cnt.most_common()
    if len(top) >= 2 and top[0][1] == top[1][1]:
        pick = max(nz, key=abs)
        chosen_raw[key] = best_raw(pick, pairs)
        report["flag"].append((key, sorted(floats), chosen_raw[key]))
    else:
        chosen_raw[key] = best_raw(top[0][0], pairs)
        report["modal"].append((key, sorted(floats), chosen_raw[key]))

# ---- pass 2: closure 23 = 24+25+26 ----
cq = defaultdict(set)
for (code, item, q) in cand:
    if item in (23, 24, 25, 26):
        cq[(code, q)].add(item)
for (code, q), items in cq.items():
    if 23 not in items:
        for it in items:                      # 23 없으면 closure 불가 -> 개별 처리
            key = (code, it, q)
            if key not in chosen_raw:
                fl = cand[key]["floats"]; nz = [v for v in fl if v != 0]
                pick = nz[0] if len(nz) == 1 else (max(nz, key=abs) if nz else 0.0)
                chosen_raw[key] = best_raw(pick, cand[key]["pairs"])
        continue
    sets = {}
    for it in (23, 24, 25, 26):
        key = (code, it, q)
        sets[it] = sorted(cand[key]["floats"]) if (key in cand and cand[key]["floats"]) else [0.0]
    # cross product (작음) — residual 최소, 동률이면 |합| 최소(garbage 회피)
    best, bestkey = None, None
    for v23, v24, v25, v26 in itertools.product(sets[23], sets[24], sets[25], sets[26]):
        resid = abs(v23 - (v24 + v25 + v26))
        tie = abs(v23) + abs(v24) + abs(v25) + abs(v26)
        if best is None or (resid, tie) < bestkey:
            best, bestkey = (v23, v24, v25, v26), (resid, tie)
    for it, vv in zip((23, 24, 25, 26), best):
        key = (code, it, q)
        if key in cand:
            chosen_raw[key] = best_raw(vv, cand[key]["pairs"])
    if cand.get((code, 23, q), {}).get("n", 1) > 1 or any(
        len(cand.get((code, it, q), {"floats": set()})["floats"]) > 1 for it in (24, 25, 26)
    ):
        report["closure"].append(((code, q), best, bestkey[0]))

# ---- pass 3: ratio 27/28 ----
for key, info in cand.items():
    code, item, q = key
    if item not in (27, 28) or key in chosen_raw:
        continue
    i14 = code_q_val(code, q, 14)
    base = code_q_val(code, q, 1 if item == 27 else 2)
    rec = (base / i14 * 100) if (base is not None and i14) else None
    floats, pairs = info["floats"], info["pairs"]
    if rec is not None:
        pick = min(floats, key=lambda v: abs(v - rec))
    else:
        nz = [v for v in floats if v != 0]
        pick = max(nz, key=abs) if nz else 0.0
    chosen_raw[key] = best_raw(pick, pairs)
    report["ratio"].append((key, sorted(floats), chosen_raw[key], rec))

# ---- pass 4: scale-sanity item2>item1 ----
qkeys = set((c, q) for (c, _, q) in cand)
for (code, q) in qkeys:
    i1 = code_q_val(code, q, 1)
    k2 = (code, 2, q)
    if k2 not in chosen_raw:
        continue
    i2 = pv(chosen_raw[k2])
    if i1 and i2 and i2 > i1 * 1.2 and (i2 / 100) <= i1:
        new2 = i2 / 100.0
        chosen_raw[k2] = f"{new2:.10f}".rstrip("0").rstrip(".")
        i14 = code_q_val(code, q, 14)
        fix28 = None
        k28 = (code, 28, q)
        if i14 and k28 in chosen_raw:
            new28 = new2 / i14 * 100
            chosen_raw[k28] = f"{new28:.8f}".rstrip("0").rstrip(".")
            fix28 = new28
        report["scale"].append((code, q, i2, new2, fix28))

# ---- rebuild rows (one per key, first-occurrence order) ----
seen, out = set(), []
for r in rows:
    key = (r["원보험사코드"], r["항목번호"], r["공시분기"])
    if key in seen:
        continue
    seen.add(key)
    nr = dict(r)
    nr["값"] = chosen_raw[key]
    out.append(nr)

# ---- write backup + output + report ----
(ROOT / "kics_disclosure.json.bak").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
SRC.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

REPORT.parent.mkdir(parents=True, exist_ok=True)
L = [f"# kics_disclosure dedup/scale report {STAMP}", "",
     f"rows {len(rows)} -> {len(out)} (removed {len(rows) - len(out)})", ""]
L.append(f"## exact dup collapsed: {len(report['exact_dup'])} keys")
L.append(f"## single non-zero (0=leak): {len(report['single_nz'])} keys")
L.append(f"## closure 23=24+25+26: {len(report['closure'])} (code,q)")
for (cq_, combo, resid) in report["closure"]:
    L.append(f"  - {cq_}: 23={combo[0]} 24={combo[1]} 25={combo[2]} 26={combo[3]} (resid {resid:.2f})")
L.append(f"## ratio 27/28 identity-picked: {len(report['ratio'])} keys")
for (k, fl, ch, rec) in report["ratio"]:
    L.append(f"  - {k}: {fl} -> {ch} (recomputed {rec})")
L.append(f"## modal-picked: {len(report['modal'])} keys")
for (k, fl, ch) in report["modal"]:
    L.append(f"  - {k}: {fl} -> {ch}")
L.append(f"## scale-fixed (item2>item1 ->/100): {len(report['scale'])}")
for (code, q, old2, new2, fix28) in report["scale"]:
    L.append(f"  - {code} {q}: item2 {old2}->{new2}; item28->{fix28}")
L.append(f"## FLAGGED ambiguous (tie, 사람 판단 필요): {len(report['flag'])} keys")
for (k, fl, ch) in report["flag"]:
    L.append(f"  - {k}: {fl} -> provisional {ch}")
REPORT.write_text("\n".join(L), encoding="utf-8")

print(f"rows {len(rows)} -> {len(out)} (removed {len(rows)-len(out)})")
for k in ("exact_dup", "single_nz", "closure", "ratio", "modal", "scale", "flag"):
    print(f"  {k}: {len(report[k])}")
print(f"report: {REPORT.relative_to(ROOT)}")
print(f"backup: kics_disclosure.json.bak")
