# -*- coding: utf-8 -*-
"""Run parse_filing for one (code, FYdir) and print t1/t2 dicts (incl hidden _jang keys)."""
import sys
import glob
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
import scripts.build_pl_breakdown as P  # noqa: E402

CODE, FYDIR = sys.argv[1], sys.argv[2]
is_life = sys.argv[3] == "life" if len(sys.argv) > 3 else False
dirs = glob.glob(f"data/dart/{FYDIR}/raw/{CODE}_*")
t1, t2 = P.parse_filing(dirs, is_life, code=CODE)
print(f"{CODE} {FYDIR} life={is_life}")
print("t1:", {k: v for k, v in (t1 or {}).items() if not str(k).startswith('_')})
print("t1 hidden:", {k: v for k, v in (t1 or {}).items() if str(k).startswith('_')})
print("t2:", t2)
