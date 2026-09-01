"""Call build_root_masters.build_pl() ONLY.

Never build_root_masters.main() -- that also runs build_csm(), which on this branch
rebuilds from git-purged raw and has collapsed masters before (7799 -> 2940 rows).
CSM is untouched by this ticket, so it must not be re-derived.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scripts.build_root_masters import PL_OUT, build_pl  # noqa: E402

n = build_pl()
print(f"wrote {PL_OUT} ({n} rows)")
