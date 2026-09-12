# -*- coding: utf-8 -*-
"""build_root_masters.build_csm() 만 개별 호출한다 (main() 통짜 실행 금지 규칙 준수)."""
import sys

sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8")

import build_root_masters as brm  # noqa: E402

n, nbad = brm.build_csm()
print(f"wrote {brm.CSM_OUT} ({n} rows; {nbad} unit-error company-quarters nulled)")
