# -*- coding: utf-8 -*-
"""build_root_masters.build_pl() 만 개별 호출한다 (main() 통짜 실행 금지 규칙 준수)."""
import sys

sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8")

import build_root_masters as brm  # noqa: E402

n = brm.build_pl()
print(f"wrote {brm.PL_OUT} ({n} rows)")
