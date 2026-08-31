# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
raw = 123858/66638*100
print("raw:", repr(raw))
print("round8:", repr(round(raw, 8)))
print("round2:", repr(round(raw, 2)))
raw28 = 51081/66638*100
print("item28 raw:", repr(raw28), "round8:", repr(round(raw28,8)))
