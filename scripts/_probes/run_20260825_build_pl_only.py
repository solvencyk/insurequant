# -*- coding: utf-8 -*-
"""build_root_masters.py::build_pl() 단독 호출(main() 미실행 — CSM 쪽 미접촉).
CLAUDE.md 절대금지 조항: build_root_masters.py 의 main() 통짜 실행 금지, 개별 빌더만
호출하고 전후 combo-diff 로 셀 손실 0 을 확인한다.

usage:
    python scripts/_probes/run_20260825_build_pl_only.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import build_root_masters as brm  # noqa: E402

n = brm.build_pl()
print(f"build_pl() wrote {n} rows to {brm.PL_OUT}")
