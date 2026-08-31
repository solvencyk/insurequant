# -*- coding: utf-8 -*-
import sys, io
sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from solvency.validation.kics_json_rules import R4, _diversified_sqrt
import numpy as np

# stored (already in master) post-transition values
item17_post = 2956.51
item18_post = 0.0
item19_post = 2818.26
item20_post = 900.0
item21_post = 328.0
item15_post_stored = 5253.39

V = np.array([item17_post, item18_post, item19_post, item20_post], dtype=float)
expected_item15 = _diversified_sqrt(V, R4) + item21_post
print(f"expected item15_post (via R4 formula) = {expected_item15:.4f}")
print(f"stored item15_post                    = {item15_post_stored}")
print(f"diff = {expected_item15 - item15_post_stored:.4f}")

# rule 6: item16 = sum(17..21) - item15
item16_post = (item17_post + item18_post + item19_post + item20_post + item21_post) - item15_post_stored
print()
print(f"item16_post (Sigma(17:21) - item15_stored) = {item16_post:.4f}")

# cross-check via rule5 backward: item15 = item14 + item22 - item23  (headline exact)
item14_post = 5073.0
item22_post = 180.0
item23_post = 0.0
item15_via_rule5 = item14_post + item22_post - item23_post
print()
print(f"item15_post via rule5 backward (14+22-23, headline-exact) = {item15_via_rule5}")
print(f"diff vs stored item15_post = {item15_via_rule5 - item15_post_stored:.4f}")
