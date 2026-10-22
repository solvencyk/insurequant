"""Read-only. Single-quarter (값_당분기) analysis under the merged vector, emulating build_root_masters.build_pl (_flow_dangi) + gold null/set_dangi."""
import json, io, os, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EVD = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
X = json.loads((EVD / "KR0005_s7_xml.json").read_text(encoding="utf-8"))
CMP = json.loads((EVD / "KR0005_s8_compare.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
nm = {}; M = {}; D = {}
for r in pl:
    if r["원보험사코드"] == "KR0005":
        nm[r["항목번호"]] = r["항목명"]; M[(r["공시분기"], r["항목번호"])] = r.get("값"); D[(r["공시분기"], r["항목번호"])] = r.get("값_당분기")
nd = {(c[1], int(c[2])) for c in gold["null_dangi"]["cells"] if c[0] == "KR0005"}
sd = {(c[1], int(c[2])) for c in gold["set_dangi"]["cells"] if c[0] == "KR0005"}
ADOPT = {q: {int(k) for k, c in CMP[q].items() if "DIFF" in c["flags"] and c["later_xml"] is not None} for q in CMP}
NEW = dict(M)
for q, ks in ADOPT.items():
    for k in ks:
        NEW[(q, k)] = CMP[q][str(k)]["later_xml"]
PREV = {"2023.2Q": "2023.1Q", "2023.3Q": "2023.2Q", "2023.4Q": "2023.3Q", "2024.2Q": "2024.1Q", "2024.3Q": "2024.2Q", "2024.4Q": "2024.3Q"}
def dangi(V, q, k):
    cur = V.get((q, k))
    if cur is None: return None
    p = PREV.get(q)
    if p is None: return cur
    pv = V.get((p, k))
    return None if pv is None else round(cur - pv, 6)
def printed3m(q, k):
    e = X.get(f"later|{q}")
    if not e or "items3m" not in e: return None
    return e["items3m"].get(str(k))
def cite3m(q, k):
    e = X[f"later|{q}"]; c = e["cites3m"].get(str(k))
    return c
ITEMS = [1, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
txt, seam, side, nochange = [], [], [], []
for q in ("2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"):
    for k in ITEMS:
        if NEW.get((q, k)) is None and M.get((q, k)) is None: continue
        affected = (k in ADOPT.get(q, set())) or (PREV.get(q) and k in ADOPT.get(PREV[q], set()))
        old_e, new_e, stored = dangi(M, q, k), dangi(NEW, q, k), D.get((q, k))
        if not affected:
            continue
        pp = printed3m(q, k) if q in ("2023.3Q", "2024.2Q", "2024.3Q") else None
        dv = None if (pp is None or new_e is None) else round(new_e - pp, 6)
        line = f"{q} item {k:2d} {nm[k][:16]:16s} cum {M.get((q,k))!s:>11}->{NEW.get((q,k))!s:>11} prev-cum {NEW.get((PREV.get(q),k))!s:>11}  dangi stored {stored!s:>11} emul-old {old_e!s:>11} emul-new {new_e!s:>11} printed3m {pp!s:>11} new-printed {dv!s:>9}"
        txt.append(line)
        if q == "2023.3Q" and new_e is not None and dv is not None and abs(dv) > 1.0:
            seam.append({"quarter": q, "item": k, "name": nm[k], "old_dangi_stored": stored, "old_dangi_emulated": old_e, "derived_if_unfixed": new_e,
                         "proposal": "set_dangi", "value": pp, "unit": "백만원", "xml_file": X["later|"+q]["file"], "xml_line": cite3m(q, k)[0][1],
                         "xml_label": cite3m(q, k)[0][0], "derived_minus_printed": dv,
                         "second_source": "restatement note 41 table '3개월 수정 후' in the same filing (FY2024 Q3 report)",
                         "reason": "operands straddle bases: 9M cumulative adopted from the FY2024 Q3 report (post-correction), 6M cumulative kept as printed in the FY2024 Q2 report (pre-correction, 2023.2Q is not restated anywhere); the difference is off by the never-published first-half correction"})
        elif q == "2023.3Q" and new_e is None:
            nochange.append({"quarter": q, "item": k, "name": nm[k], "reason": "prior cumulative (2023.2Q) is blank in the master, single quarter stays blank before and after"})
        else:
            side.append({"quarter": q, "item": k, "name": nm[k], "old_dangi_stored": stored, "old_dangi_emulated": old_e, "new_dangi": new_e, "printed_3m_later": pp, "new_minus_printed": dv,
                         "operand_vintages": "both post-correction (B)" if q != "2023.3Q" else "n/a"})
(EVD / "KR0005_s11_seam.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
(EVD / "KR0005_s11_seam.json").write_text(json.dumps({"seam": seam, "side_effects": side, "blank_before_and_after": nochange}, ensure_ascii=False, indent=1), encoding="utf-8")
print("seam:", [(s["quarter"], s["item"], s["value"]) for s in seam])
print("max |new-printed| over side effects with printed:", max([abs(s["new_minus_printed"]) for s in side if s["new_minus_printed"] is not None] or [0]))
