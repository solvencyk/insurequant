"""Read-only dump of KR0073 CSM_waterfall cells: master, gold overlay, provenance.

Usage: python dump_current_state.py [out_txt]
Never writes any master/gold/provenance file.
"""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
CODE = "KR0073"

QORDER = {}
for y in range(2022, 2027):
    for q in range(1, 5):
        QORDER[f"{y}.{q}Q"] = y * 10 + q


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    lines = []

    def emit(s=""):
        lines.append(s)

    master = load(ROOT / "CSM_waterfall.json")
    rows = [r for r in master if r.get("원보험사코드") == CODE]
    emit(f"master rows for {CODE}: {len(rows)} (total master rows {len(master)})")
    by_q = {}
    for r in rows:
        by_q.setdefault(r["공시분기"], {})[r["항목번호"]] = r
    for q in sorted(by_q, key=lambda x: QORDER.get(x, 0)):
        d = by_q[q]
        vals = []
        for i in range(1, 7):
            r = d.get(i)
            if r is None:
                vals.append("None")
            else:
                vals.append(f"{r.get('값')}|{r.get('값_당분기')}")
        emit(f"{q}: " + "  ".join(f"i{i}={v}" for i, v in zip(range(1, 7), vals)))
        extra = sorted({k for r in d.values() for k in r.keys()} - {"원보험사코드", "원수사명", "티커", "생손보여부", "항목번호", "항목명", "공시분기", "값", "값_당분기"})
        if extra:
            emit(f"    extra keys: {extra}")

    emit("")
    emit("=== gold overlay data/_gold/user_csm_cells.json ===")
    gold = load(ROOT / "data/_gold/user_csm_cells.json")
    emit(f"top-level keys: {list(gold.keys())}")
    for k, v in gold.items():
        if isinstance(v, list):
            emit(f"  {k}: list len {len(v)}; first={json.dumps(v[0], ensure_ascii=False)[:300] if v else None}")
        elif isinstance(v, dict):
            emit(f"  {k}: dict len {len(v)}; keys sample={list(v.keys())[:5]}")
        else:
            emit(f"  {k}: {str(v)[:120]}")

    emit("")
    emit("=== provenance KR0073 ===")
    prov = load(ROOT / "CSM_waterfall_provenance.json")
    cells = [c for c in prov["cells"] if c.get("company_code") == CODE]
    emit(f"provenance cells for {CODE}: {len(cells)}")
    for c in sorted(cells, key=lambda c: QORDER.get(c["quarter"], 0)):
        emit("  " + json.dumps(c, ensure_ascii=False))

    text = "\n".join(lines)
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
