# -*- coding: utf-8 -*-
from decimal import Decimal
for v in (5695.95, 5695.9, 384.11, 42.25, -116.41, 1173.06, 83.04, -245.09):
    print(v, Decimal(v), "round1:", round(v, 1), "f'{:.1f}':", f"{v:.1f}")
