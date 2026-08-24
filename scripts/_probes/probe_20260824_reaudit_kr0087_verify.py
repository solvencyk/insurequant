# -*- coding: utf-8 -*-
"""Read-only: the KR0087 2025.2Q reconciliation, spelled out. All figures 억원 unless noted."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# --- raw p16 TFI (백만원), visually confirmed at 220dpi ---
SM_pre, SM_post = 4_166_224, 4_285_029      # 지급여력금액
T1_pre, T1_post = 1_411_796, 1_756_363      # 기본자본
T2_pre, T2_post = 2_754_428, 2_528_665      # 보완자본
PRECAP_pre, PRECAP_post = 1_210_705, 866_138  # 보완자본 한도 적용 전 (as printed)
LIMIT_pre, LIMIT_post = 1_210_705, 1_210_705  # 보완자본 한도
SURR_pre, SURR_post = 1_543_723, 1_543_723    # 해약환급금 초과분
HYBRID, SUB = 344_567, 0                      # (기발행 신종자본증권) / (기발행 후순위채무)
SCR = 2_421_410
# --- raw p15 headline (억원) ---
i4, i12, i13, i2 = 33_001, 1_188, 18_883, 14_118

print("A. 한도 = SCR x 50% :", SCR * 0.5, "vs printed", LIMIT_pre)
print("B. 적용전 구성행: min(47,48)+49 =", min(PRECAP_pre, LIMIT_pre) + SURR_pre,
      " vs 인쇄 보완자본_전", T2_pre, "-> 닫힘 (cap 이 물리므로 47 의 참값을 결정하지 못한다)")
print("C. 경과조치 = 기발행 신종자본증권의 기본자본 승격:",
      T1_post - T1_pre, "== item53", HYBRID)

# --- derivation 1: TFI 적용후 컬럼만 사용 ---
debt_post = T2_post - SURR_post                 # 적용후 인정 채무성 보완자본
debt_pre  = debt_post + HYBRID + SUB            # 승격분을 되돌린 적용전 채무성 보완자본(한도 적용 전)
excess    = debt_pre - LIMIT_pre
print("\nD1 (TFI 적용후 컬럼): debt_post =", f"{T2_post:,} - {SURR_post:,} = {debt_post:,}")
print("    debt_pre(참 한도적용전) =", f"{debt_post:,} + {HYBRID:,} = {debt_pre:,}",
      f"(인쇄된 47 = {PRECAP_pre:,})")
print("    한도초과 =", f"{debt_pre:,} - {LIMIT_pre:,} = {excess:,} 백만 = {excess/100:.2f} 억")
print("    되짚기: min(debt_pre, limit)+surr =",
      f"{min(debt_pre, LIMIT_pre) + SURR_pre:,} vs 인쇄 {T2_pre:,}  (닫힘)")

# --- derivation 2: 헤드라인 표만 사용 (TFI 를 전혀 안 본다) ---
req = i2 - (i4 - i12 - i13)
print("\nD2 (헤드라인 주1): i2 - (i4 - i12 - i13) =",
      f"{i2} - ({i4} - {i12} - {i13}) = {req}  -> 필요한 한도초과 = {req} 억")

# --- derivation 3: 경과조치 순증 ---
print("\nD3 (경과조치 순증): 지급여력금액", f"{SM_post:,} - {SM_pre:,} = {SM_post - SM_pre:,} 백만",
      f"= {(SM_post - SM_pre)/100:.2f} 억  (한도로 잘려 있던 초과분이 승격으로 풀린 금액)")

# --- 고친 산식이 공시값을 재현하는가 ---
exc_eok = excess / 100.0
recon = i4 - (i12 - exc_eok) - i13
print("\n>>> 고친 산식: item2 == item4 - (item12 - 한도초과) - item13")
print(f"    {i4} - ({i12} - {exc_eok:.2f}) - {i13} = {recon:.2f}   vs 공시 item2 = {i2}")
print(f"    잔차 = {recon - i2:+.2f}  (게이트 tol 2.0)   [현행 룰: 한도초과=0 -> {i4-i12-i13} , 잔차 {i2-(i4-i12-i13):+.2f}]")

# --- 적용후 구성행도 같은 참값으로 닫히는가 ---
print("\n>>> 적용후 구성: min(debt_pre - 승격, 한도) + 해약 =",
      f"{min(debt_pre - HYBRID, LIMIT_post) + SURR_post:,} vs 인쇄 {T2_post:,}",
      f"(인쇄된 47_후 {PRECAP_post:,} 로는 {min(PRECAP_post, LIMIT_post)+SURR_post:,} = 잔차 {T2_post-(min(PRECAP_post,LIMIT_post)+SURR_post):,})")
