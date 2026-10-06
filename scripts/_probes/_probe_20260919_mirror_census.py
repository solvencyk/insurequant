"""READ-ONLY probe: census of item 4/12/13 값_적용후 cells + git provenance of the
2026-07-11 backfill_post_transition_when_not_applied.py run.

Writes JSON to data/_derived/_probe_20260919_mirror_census.json
No master mutation. No build. No network.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "_derived" / "_probe_20260919_mirror_census.json"

K_CODE = "원보험사코드"
K_NAME = "원수사명"
K_ITEM = "항목번호"
K_LABEL = "항목명"
K_Q = "공시분기"
K_V = "값"
K_VA = "값_적용후"

TARGET_ITEMS = (4, 12, 13)


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_git_json(rev, path):
    raw = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=str(ROOT), capture_output=True,
    )
    if raw.returncode != 0:
        return None
    return json.loads(raw.stdout.decode("utf-8"))


def key(r):
    return (r.get(K_CODE), r.get(K_Q), r.get(K_ITEM))


def main():
    cur = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    cur_idx = {key(r): r for r in cur}

    # ---- 1. current census for 4/12/13
    census = {"4": {}, "12": {}, "13": {}}
    cells_present = []
    for r in cur:
        it = r.get(K_ITEM)
        if it not in TARGET_ITEMS:
            continue
        c = census[str(it)]
        c["total"] = c.get("total", 0) + 1
        v, va = num(r.get(K_V)), num(r.get(K_VA))
        if va is None:
            c["after_missing"] = c.get("after_missing", 0) + 1
            continue
        c["after_present"] = c.get("after_present", 0) + 1
        if v is not None and abs(v - va) <= 0.01:
            c["after_eq_pre"] = c.get("after_eq_pre", 0) + 1
        else:
            c["after_ne_pre"] = c.get("after_ne_pre", 0) + 1
        cells_present.append({
            "code": r.get(K_CODE), "name": r.get(K_NAME), "q": r.get(K_Q),
            "item": it, "label": r.get(K_LABEL),
            "pre": r.get(K_V), "post": r.get(K_VA),
            "equal": (v is not None and va is not None and abs(v - va) <= 0.01),
        })

    # ---- 2. git provenance: what did the 2026-07-11 run (e1aa8ae) actually fill?
    prov = {}
    before = load_git_json("e1aa8ae^", "kics_disclosure.json")
    after = load_git_json("e1aa8ae", "kics_disclosure.json")
    if before is not None and after is not None:
        bidx = {key(r): r for r in before}
        filled = []
        for r in after:
            k = key(r)
            b = bidx.get(k)
            va_new = r.get(K_VA)
            va_old = b.get(K_VA) if b else None
            if va_old in (None, "") and va_new not in (None, ""):
                v_new = num(r.get(K_V))
                n_new = num(va_new)
                filled.append({
                    "code": k[0], "q": k[1], "item": k[2],
                    "name": r.get(K_NAME),
                    "pre": r.get(K_V), "post": va_new,
                    "mirror": (v_new is not None and n_new is not None
                               and abs(v_new - n_new) <= 0.01),
                })
        prov["filled_total"] = len(filled)
        prov["filled_mirror"] = sum(1 for f in filled if f["mirror"])
        by_item = {}
        for f in filled:
            if not f["mirror"]:
                continue
            by_item.setdefault(str(f["item"]), 0)
            by_item[str(f["item"])] += 1
        prov["mirror_by_item"] = dict(sorted(by_item.items(), key=lambda kv: int(kv[0])))
        # still standing in current master?
        target_mirror = [f for f in filled if f["mirror"] and f["item"] in TARGET_ITEMS]
        still = []
        for f in target_mirror:
            k = (f["code"], f["q"], f["item"])
            c = cur_idx.get(k)
            if c is None:
                f["now"] = "ROW_GONE"
            else:
                va = num(c.get(K_VA))
                v = num(c.get(K_V))
                if va is None:
                    f["now"] = "REVERTED_BLANK"
                elif v is not None and abs(v - va) <= 0.01:
                    f["now"] = "MIRROR_STANDING"
                else:
                    f["now"] = "CHANGED"
                f["now_pre"] = c.get(K_V)
                f["now_post"] = c.get(K_VA)
            still.append(f)
        prov["target_items_mirrored_at_e1aa8ae"] = len(target_mirror)
        prov["target_status_counts"] = {}
        for f in still:
            prov["target_status_counts"][f["now"]] = prov["target_status_counts"].get(f["now"], 0) + 1
        prov["target_cells"] = still
    else:
        prov["error"] = "git show failed"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "census": census,
        "cells_present_count": len(cells_present),
        "cells_present": cells_present,
        "provenance_e1aa8ae": prov,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("census:", json.dumps(census, ensure_ascii=False))
    print("cells_present:", len(cells_present))
    print("prov summary:", json.dumps({k: v for k, v in prov.items()
                                       if k not in ("target_cells",)}, ensure_ascii=False))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
