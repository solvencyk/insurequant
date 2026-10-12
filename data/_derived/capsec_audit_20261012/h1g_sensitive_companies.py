# -*- coding: utf-8 -*-
"""h1g: explain the companies whose 보완자본 소진율 moves most under the new rule (coordinator's list: 흥국화재, 악사, 아이엠라이프; plus the three bonds whose ledger
past-call flag disagrees with the numerator date: 메리츠, KB라이프).  For each: previous published value (dbbffcb5), new published value, my recompute of the
spec (ledger flag), the variants, and the printed 53/54 against the ledger deduction.   Output h1g_sensitive_companies_<rev>.txt"""
import json
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

REV = audit_io.resolved_rev()
rows = {x["code"]: x for x in json.load(open(HERE + "h1_tier2_recompute_47_%s.json" % REV, encoding="utf-8"))}
old2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json", "dbbffcb5")["results"]}
new2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
L = ["PIN rev=%s (previous audited state dbbffcb5)" % REV]
for code in ("KR0005", "KR0049", "KR0076", "KR0001", "KR0099"):
    x, o, n, r = rows[code], old2[code], new2[code], inp[code]
    lim = x["limit_mine"]
    L.append("== %s %s: previous published %s -> new published %s ; my spec recompute %s (numerator %s of limit %s)" % (code, x["name"], o["utilization_pct"], n["utilization_pct"], x["pct_mine"], x["N2_mine"], lim))
    L.append("   issuer-printed item 53/54 = %s / %s (kept as *_printed_eok) ; ledger deduction (pre-2023, past-call excluded) hybrid / subordinated = %s / %s" % (
        x["printed53_master"], x["printed54_master"], x["ledger_hybrid_mine"], x["ledger_sub_mine"]))
    L.append("   item 47 pre/post = %s / %s ; item 49 = %s ; item 3 = %s ; rule/scope published %s/%s" % (r["i47_pre"], r["i47_post"], r["i49_pre"], r["i3_pre"], x["rule_pub"], x["scope_pub"]))
    L.append("   variants: past-call decided at 2026-06-30 -> %s ; min(printed, ledger) -> %s ; sub 잔존만기 체감 -> %s" % (x["pct_variant_date"], x["pct_variant_min"], x["pct_variant_haircut"]))
    if x["pastcall_excluded"]:
        L.append("   ledger bonds excluded as past-call (flag): %s" % x["pastcall_excluded"])
    if code == "KR0005":
        L.append("   mechanism: the issuer's printed item 53 (2,120) contains 제1회 신종 920억 (issued 2016-12-29, first call 2021-12-29, still outstanding) which the issuer deducted in its post column;")
        L.append("              the new rule does not deduct a bond past its first call, so the numerator rises by 920 (= +%.1f pp of the limit) - it moves AGAINST the issuer's printed value." % (920 / lim * 100))
    if code == "KR0049":
        L.append("   mechanism: the issuer's printed item 54 (344.66) is the JPY subordinated bond (no issue date in the ledger, call date set to 'now' = conservative estimate, flag past_call_outstanding=true);")
        L.append("              the new rule deducts nothing for it (past call / unknown vintage) -> numerator = item 47 pre-TFI column %.2f instead of the issuer's post column %.2f. The 29.2%% rests on that exclusion" % (r["i47_pre"], r["i47_post"]))
        L.append("              (an ESTIMATED call date, source PDF not read); deducting the printed 345 would give %.1f%%." % (max(0.0, r["i47_pre"] - r["i54_pre"]) / lim * 100))
    if code == "KR0076":
        pre = r["i47_pre"]
        L.append("   mechanism: ledger as_of 2025-12-31 and it lacks the 전환우선주: printed item 53 (2,465.98) = 신종 948.8 (ledger) + about 1,517 전환우선주 (not a bond, not in the ledger).")
        L.append("              deduction by ledger = 948.8 + 500 (사모사채 2021-05-07, call 2026-05-07 derived = already past at 2026-06-30 but flag false because the row is dated 2025-12-31)")
        L.append("              readings: published (ledger, flag) %.1f%% ; sub 500 treated as past-call %.1f%% ; deduct printed 53 + ledger sub (전환우선주 included) %.1f%% ; deduct printed 53 only %.1f%%" % (
            x["pct_mine"], x["pct_variant_date"], max(0.0, pre - 2465.98 - 500) / lim * 100, max(0.0, pre - 2465.98) / lim * 100))
    if code == "KR0001":
        L.append("   mechanism: the 제7회 후순위 (issued 2021-04-12, derived call 2026-04-12, 2,100억, still outstanding at 2026-06-30 per the H1 report) is in the ledger row dated 2026-06-30 with")
        L.append("              past_call_outstanding=false - the flag was computed at 2025-12-31 and not refreshed; by the coordinator's own rule it should be excluded -> %.1f%% instead of %.1f%%." % (x["pct_variant_date"], x["pct_mine"]))
    if code == "KR0099":
        L.append("   mechanism: 제1회 후순위 (issued 2021-05-31, derived call 2026-05-31, 1,299.7억) in a ledger row dated 2025-12-31: flag false at that date, past call at the numerator date 2026-06-30.")
open(HERE + "h1g_sensitive_companies_%s.txt" % REV, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
