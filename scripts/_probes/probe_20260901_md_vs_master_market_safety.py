"""Would re-running fill_market_subitems over the re-converted MDs be safe?

Compares extract_mkt_subs(current MD) against the master's items 36-40 for every
FY2026_Q2 company and prints the disagreements. A disagreement means the MD
would OVERWRITE a master value that the 19_market identity currently confirms —
so the answer to "just re-run the fill script" is no.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MD_DIR = REPO / "md_inbox" / "FY2026_Q2"
QUARTER = "2026.2Q"
TOL = 0.02  # relative


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _body(p: Path) -> str:
    t = p.read_text(encoding="utf-8")
    _, _, rest = t.partition("---\n")
    _, _, body = rest.partition("\n---\n")
    return body


def main() -> int:
    mkt = _load("_mkt3", REPO / "scripts" / "fill_market_subitems_to_disclosure.py")
    master = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    keys = list(master[0].keys())
    F = {"code": keys[0], "item": keys[4], "quarter": keys[6], "val": keys[7]}
    cells: dict[tuple[str, int], float] = {}
    for r in master:
        if r.get(F["quarter"]) != QUARTER:
            continue
        try:
            cells[(r[F["code"]], int(r[F["item"]]))] = float(r[F["val"]])
        except (TypeError, ValueError):
            continue

    agree = disagree = absent = 0
    print(f"\n{'code':<9}{'item':>5}{'md(억원)':>16}{'master':>14}{'rel%':>9}")
    print("-" * 56)
    for md in sorted(MD_DIR.glob("*.md")):
        code = md.stem.split("_")[0]
        subs = mkt.extract_mkt_subs(_body(md))
        for item in range(36, 41):
            m = cells.get((code, item))
            if m is None:
                continue
            if item not in subs:
                absent += 1
                continue
            raw, unit = subs[item]
            try:
                v = mkt._to_eok(float(str(raw).replace(",", "")), unit)
            except Exception:  # noqa: BLE001
                continue
            v = float(v)
            rel = abs(v - m) / max(abs(m), 1e-9)
            if rel <= TOL:
                agree += 1
            else:
                disagree += 1
                print(f"{code:<9}{item:>5}{v:>16,.2f}{m:>14,.2f}{rel*100:>8.1f}%")
    print(f"\nagree={agree}  DISAGREE={disagree}  md-absent={absent}")
    print("DISAGREE>0 means a blind re-run of fill_market_subitems would corrupt the master.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
