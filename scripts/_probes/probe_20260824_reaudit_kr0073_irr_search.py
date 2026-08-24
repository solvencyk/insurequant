# -*- coding: utf-8 -*-
"""Read-only: brute-force search for any variant of the K-ICS IRR derivation that
reproduces 교보생명 2025.2Q disclosed 금리위험액 459,988 (백만원) from the 6 printed NAVs."""
import itertools, math, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

N0 = -5_667_711        # 충격 전
MR = -5_414_904        # 평균회귀
UP = -6_352_338        # 금리상승
DN = -5_586_899        # 금리하락
FL = -5_463_138        # 금리평탄
TW = -5_742_051        # 금리경사
TARGET = 459_988

s = lambda x: N0 - x                      # shock = 충격전 - 시나리오
sh = {"MR": s(MR), "UP": s(UP), "DN": s(DN), "FL": s(FL), "TW": s(TW)}
print("shocks:", {k: f"{v:,}" for k, v in sh.items()})

def variants():
    for floor_leg in (False, True):
        for floor_mr in (False, True):
            for mr_mode in ("add", "sub", "quad", "drop"):
                for pair in (("UP", "DN"), ("UP", "TW"), ("DN", "FL")):
                    for pair2 in (("FL", "TW"), ("DN", "TW"), ("UP", "FL")):
                        if set(pair) & set(pair2):
                            continue
                        yield floor_leg, floor_mr, mr_mode, pair, pair2

best = []
seen = set()
for floor_leg, floor_mr, mr_mode, p1, p2 in variants():
    f = (lambda v: max(0.0, v)) if floor_leg else (lambda v: v)
    a = max(f(sh[p1[0]]), f(sh[p1[1]]))
    b = max(f(sh[p2[0]]), f(sh[p2[1]]))
    mr = sh["MR"]
    if floor_mr:
        mr = max(0.0, mr)
    core = math.sqrt(a * a + b * b)
    if mr_mode == "add":
        val = core + mr
    elif mr_mode == "sub":
        val = core - mr
    elif mr_mode == "quad":
        val = math.sqrt(a * a + b * b + mr * mr)
    else:
        val = core
    key = round(val, 2)
    if key in seen:
        continue
    seen.add(key)
    best.append((abs(val - TARGET), val, floor_leg, floor_mr, mr_mode, p1, p2))

best.sort()
print(f"\nTARGET = {TARGET:,}   ({len(best)} distinct variant values)")
for d, v, fl, fm, mm, p1, p2 in best[:15]:
    print(f"  |Δ|={d:14,.1f}  val={v:14,.1f}  floor_leg={fl!s:5} floor_mr={fm!s:5} mr={mm:5} {p1}/{p2}")

# also: any single/paired combination of the raw NAV differences equal to TARGET?
print("\nany pairwise sqrt(x^2+y^2) (+/- z) hitting TARGET within 1,000?")
keys = list(sh)
hits = 0
for x, y in itertools.permutations(keys, 2):
    core = math.hypot(sh[x], sh[y])
    for z in keys + [None]:
        for sgn in (1, -1):
            v = core + (sgn * sh[z] if z else 0)
            if abs(v - TARGET) <= 1000:
                print(f"   HIT sqrt({x}^2+{y}^2) {'+' if sgn>0 else '-'}{z} = {v:,.1f}")
                hits += 1
print("   hits:", hits)
