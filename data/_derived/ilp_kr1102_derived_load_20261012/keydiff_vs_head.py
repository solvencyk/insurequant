# -*- coding: utf-8 -*-
"""Read-only: key-level diff of the two files this load touches, working tree vs HEAD (parsed content, so CRLF/LF of the blob does not matter).

  insurance_liability_portfolio.json              key = (원보험사코드, 공시분기, 항목번호): added / removed / value-or-field changed
  insurance_liability_portfolio_provenance.json   top-level sections: lists compared by position (appended entries), the not_loaded record that gained `resolved`

Expected for this load: master added = exactly the eight planned keys (KR1102 2026.1Q items 1-8), removed 0, changed 0; sidecar lrc_model_cells +1, backfills +1,
lrc_model_not_loaded same length with exactly one record changed (only `resolved` added), every other section identical.  Exit 1 on any deviation.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe keydiff_vs_head.py [out.txt]
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
PLAN = [("KR1102", "2026.1Q", n) for n in range(1, 9)]


def head(name: str):
    out = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{name}"], capture_output=True, check=True).stdout
    return json.loads(out.decode("utf-8"))


def wt(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> int:
    lines, bad = [], []
    h, w = head("insurance_liability_portfolio.json"), wt("insurance_liability_portfolio.json")
    key = lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"])
    hm, wm = {key(r): r for r in h}, {key(r): r for r in w}
    assert len(hm) == len(h) and len(wm) == len(w), "duplicate keys"
    added, removed = sorted(set(wm) - set(hm)), sorted(set(hm) - set(wm))
    changed = sorted(k for k in set(hm) & set(wm) if hm[k] != wm[k])
    lines.append(f"master insurance_liability_portfolio.json: HEAD {len(h)} rows, working tree {len(w)} rows")
    lines.append(f"  added {len(added)}: {added}")
    lines.append(f"  removed {len(removed)}: {removed}")
    lines.append(f"  changed {len(changed)}: {changed[:10]}")
    if added != PLAN:
        bad.append("master: added keys differ from the plan")
    if removed or changed:
        bad.append("master: a HEAD row was removed or changed")
    for k in added:
        r = wm[k]
        lines.append(f"    + {k} {r['항목명']} = {r['값']}")

    hp, wp = head("insurance_liability_portfolio_provenance.json"), wt("insurance_liability_portfolio_provenance.json")
    lines.append("sidecar insurance_liability_portfolio_provenance.json:")
    if list(hp) != list(wp):
        bad.append(f"sidecar top-level keys differ: {list(hp)} vs {list(wp)}")
    for sec in hp:
        a, b = hp[sec], wp.get(sec)
        if isinstance(a, list):
            if len(b) < len(a):
                bad.append(f"sidecar {sec}: shorter than HEAD")
                continue
            diff_idx = [i for i in range(len(a)) if a[i] != b[i]]
            extra = len(b) - len(a)
            lines.append(f"  {sec}: HEAD {len(a)} -> {len(b)} (+{extra}); changed existing entries {len(diff_idx)}")
            if sec == "lrc_model_cells" and (extra != 1 or diff_idx):
                bad.append("sidecar lrc_model_cells: expected +1 and no changed entry")
            if sec == "backfills" and (extra != 1 or diff_idx):
                bad.append("sidecar backfills: expected +1 and no changed entry")
            if sec == "lrc_model_not_loaded":
                if extra or len(diff_idx) != 1:
                    bad.append("sidecar lrc_model_not_loaded: expected exactly one changed record")
                else:
                    x, y = a[diff_idx[0]], b[diff_idx[0]]
                    only_resolved = {k: v for k, v in y.items() if k != "resolved"} == x and "resolved" in y and "resolved" not in x
                    lines.append(f"    changed record {x['company_code']} {x['quarter']}: only `resolved` added = {only_resolved}")
                    if not (only_resolved and (x["company_code"], x["quarter"]) == ("KR1102", "2026.1Q")):
                        bad.append("sidecar lrc_model_not_loaded: the changed record is not KR1102 2026.1Q / not only `resolved`")
            if sec not in ("lrc_model_cells", "backfills", "lrc_model_not_loaded") and (extra or diff_idx):
                bad.append(f"sidecar {sec}: unexpected change")
        else:
            lines.append(f"  {sec}: {'identical' if a == b else 'CHANGED'}")
            if a != b:
                bad.append(f"sidecar top-level {sec} changed")
    lines.append("RESULT: " + ("OK (changed cells = planned cells, deletions 0)" if not bad else "DEVIATION: " + "; ".join(bad)))
    txt = "\n".join(lines) + "\n"
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(txt, encoding="utf-8", newline="\n")
    print(txt)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
