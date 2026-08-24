# -*- coding: utf-8 -*-
"""KR0004 예별손해 3분기: item19후(시장위험액후, ③표 자체 인쇄값) 을 MARKET_M 으로
역산해 '금리위험 기여분=0' 가설과 '금리위험 기여분=전값(unchanged)' 가설 중 어느 쪽이
회사 자신이 인쇄한 시장위험액후 subtotal 을 재현하는지 정밀 대조."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from solvency.validation.kics_json_rules import MARKET_M  # noqa: E402

# (분기, 금리전, 주식후, 부동산후, 외환후, 집중후, raw인쇄된 시장위험액후)  단위 백만원
CASES = [
    ("2023.4Q", 65239, 112644, 3923, 19238, 0, 110677),
    ("2024.1Q", 71606, 118972, 3524, 21282, 0, 116622),
    ("2024.2Q", 56790, 136050, 3916, 15982, 0, 134130),
]

for q, ir_full, eq, re_, fx, cc, printed in CASES:
    v_zero = np.array([0, eq, re_, fx, cc], float)
    v_full = np.array([ir_full, eq, re_, fx, cc], float)
    calc_zero = float(np.sqrt(v_zero @ MARKET_M @ v_zero))
    calc_full = float(np.sqrt(v_full @ MARKET_M @ v_full))
    print(f"{q}: raw인쇄 시장위험액후={printed:,}백만  |  "
          f"금리=0 가설 계산={calc_zero:,.2f}백만 (diff {calc_zero-printed:+.2f})  |  "
          f"금리=전값 가설 계산={calc_full:,.2f}백만 (diff {calc_full-printed:+.2f})")
