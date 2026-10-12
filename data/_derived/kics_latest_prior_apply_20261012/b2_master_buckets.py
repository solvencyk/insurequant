"""b2: print, for each surviving candidate block, the master's 값 / 값_적용후 for the changed items + 1,2,3,4,14,27,28 (READ-ONLY)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from pdfcheck import utf8_stdout  # noqa: E402

utf8_stdout()
REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = REPO / "data" / "_derived" / "kics_latest_prior_precedence_dryrun_20261012"
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in rows}
SURV = sys.argv[1].split(",") if len(sys.argv) > 1 else [
    "KR0003_2023.4Q", "KR0003_2025.1Q", "KR0004_2023.1Q", "KR0004_2024.1Q", "KR0009_2023.1Q", "KR0009_2023.2Q",
    "KR0032_2024.3Q", "KR0049_2025.1Q", "KR0049_2026.1Q", "KR0050_2025.3Q", "KR0069_2024.2Q", "KR0070_2024.3Q",
    "KR0071_2024.4Q", "KR0072_2025.2Q", "KR0080_2026.1Q", "KR0095_2024.4Q", "KR0099_2024.3Q"]
for bid in SURV:
    code, q = bid.split("_")
    plan = json.loads((D / "plans" / f"{bid}.json").read_text(encoding="utf-8"))
    items = sorted({e["item"] for e in plan["edits"]} | {1, 2, 3, 4, 12, 13, 14, 27, 28})
    print(f"== {bid}  plan edits: {[(e['item'], e['field'], e['old'], e['new']) for e in plan['edits']]}")
    for it in items:
        r = idx.get((code, q, it))
        if r is None:
            print(f"   item{it:>2}: <no row>")
            continue
        mark = "*" if it in {e["item"] for e in plan["edits"]} else " "
        print(f"  {mark}item{it:>2} 값={r.get('값')!r:>16}  값_적용후={r.get('값_적용후', '<nokey>')!r:>16}  {str(r['항목명'])[:30]}")
