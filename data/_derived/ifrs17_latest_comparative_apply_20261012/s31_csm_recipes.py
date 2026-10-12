"""Read-only per-block recipes that rebuild the planned CSM 6-vector (억원) from PRINTED rows of the later filing, with XML line numbers.
Own code (xmltab.py); sums over the CSM columns where the rollforward prints 수정소급법 / 공정가치법 / 그 외 (or 완전소급법 / 공정가치법 / 이외) columns.
Output evidence_csm_recipes.json / .txt
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

ROOT = X.ROOT
DRY = ROOT / "data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012"
ov = json.loads((DRY / "cand/csm_adopt_overlay.json").read_text(encoding="utf-8"))
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}


def norm(s):
    return re.sub(r"\s+", "", s or "")


def num(c):
    v = X.printed_to_float(c)
    return 0.0 if v is None else v


def xml_of(kr, fy_q):
    d = sorted((ROOT / "data/dart" / fy_q / "raw").glob(f"{kr}_*"))[0]
    return sorted(d.glob("*.xml"), key=lambda p: p.stat().st_size, reverse=True)[0]


def tbl(xml, idx):
    for t in X.load_tables(str(xml)):
        if t.index == idx:
            return t
    raise KeyError(idx)


def row(t, label, nth=1, exact=True):
    k = 0
    for r in t.rows:
        if r.cells and ((norm(r.cells[0]) == norm(label)) if exact else (norm(label) in norm(r.cells[0]))):
            k += 1
            if k == nth:
                return r
    return None


def csm_sum(r, cols):
    parts = [r.cells[c] if c < len(r.cells) else "" for c in cols]
    return sum(num(p) for p in parts), parts


RECIPES = {
    # key -> dict(xml (kr, fyq), tables [(idx, csm_cols)], rows: item -> list of labels (summed))
    "KR0069|2023.2Q": dict(kr="KR0069", fyq="FY2024_Q2", tables=[(421, (3, 4, 5)), (423, (3, 4, 5)), (425, (3, 4, 5))],
                           rows={1: ["보험계약 순부채(자산)(기초)"], 2: ["당기 최초 인식 계약"], 3: ["보험계약의 순 금융손익", "환율변동효과 등"],
                                 4: ["보험계약마진 추정의 변경"], 5: ["제공한 서비스에 대해 인식한 보험계약마진"], 6: ["보험계약 순부채(자산)(기말)"]}),
    "KR0082|2023.1Q": dict(kr="KR0082", fyq="FY2024_Q1", tables=[(574, (3, 4, 5))],
                           rows={1: ["전기초보험계약부채"], 2: ["최초인식계약"], 3: ["당기손익인식 보험금융비용"], 4: ["보험계약마진에 반영된 추정치 변동"],
                                 5: ["보험계약마진상각"], 6: ["전분기말보험계약부채"]}),
    "KR0001|2023.3Q": dict(kr="KR0001", fyq="FY2024_Q3", tables=[(513, (3, 4, 5))],
                           rows={1: ["기초 순장부금액"], 2: ["신계약효과"], 3: ["순보험금융손익"], 4: ["보험계약마진을 조정하는 추정치 변동"],
                                 5: ["당기손익으로 인식한 보험계약마진 금액"], 6: ["분기말 순장부금액"]}),
}


def main():
    lines = []
    out = {}
    for key, rc in RECIPES.items():
        kr, q = key.split("|")
        xml = xml_of(rc["kr"], rc["fyq"])
        vec = {i: 0.0 for i in range(1, 7)}
        toks = {i: [] for i in range(1, 7)}
        for (idx, cols) in rc["tables"]:
            t = tbl(xml, idx)
            for item, labels in rc["rows"].items():
                for lab in labels:
                    r = row(t, lab)
                    if r is None:
                        continue
                    s, parts = csm_sum(r, cols)
                    vec[item] += s
                    toks[item].append({"table": idx, "line": r.line, "label": r.cells[0], "printed_csm_cols": parts, "sum_won_unit": s})
        planned = {int(k): v for k, v in ov[key].items() if v is not None}
        lines.append(f"=== {key} <- {xml.name} (tables {[i for i, _ in rc['tables']]})")
        out[key] = {"xml": str(xml.relative_to(ROOT)).replace("\\", "/"), "items": {}}
        for i in range(1, 7):
            v_eok = vec[i] / 100.0
            if i in (5,):
                v_eok = -abs(v_eok)
            p = planned.get(i)
            lv = live.get((kr, i, q))
            ok = p is not None and abs(abs(v_eok) - abs(p)) <= 0.06 and (v_eok >= 0) == (p >= 0)
            lines.append(f"  item {i}: printed-derived {v_eok:>12,.2f}억  plan {p}  live-old {lv}  {'OK' if ok else 'DIFF'}  tokens={[(x['table'], x['line'], x['printed_csm_cols']) for x in toks[i]]}")
            out[key]["items"][i] = {"derived": round(v_eok, 3), "plan": p, "live_old": lv, "ok": ok, "tokens": toks[i]}
        # closing identity on the printed rows
        resid = vec[6] / 100 - (vec[1] / 100 + vec[2] / 100 + vec[3] / 100 + vec[4] / 100 - abs(vec[5]) / 100)
        lines.append(f"  closing identity on printed rows: closing - (open+new+int+assump-amort) = {resid:+.3f}억")
        out[key]["closing_identity_resid"] = round(resid, 3)
    (HERE / "evidence_csm_recipes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (HERE / "evidence_csm_recipes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))


main()
