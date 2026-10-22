# -*- coding: utf-8 -*-
"""d10: per-bucket gate effects of the simulated adoptions (read-only, parses the gate_overlay outputs).
Inputs  g_base/, g_pl/, g_csm_a51/, g_csm_chain/, g_csm_full/, g_plbreak_master_tables.txt
Output  d10_effects.json {name|quarter: {"pl_closing": [...], "pl_bridgebreak": [...], "csm_a51": [...], "csm_chain": [...], "csm_full": [...]}}, d10_gate_summary.txt"""
import json, re, sys
from pathlib import Path
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
eff = defaultdict(lambda: defaultdict(list))
summ = []

def lines(p):
    # gate outputs were first written to sub-folders g_<name>/<gate>.txt and then flattened to g_<name>__<gate>.txt
    f = OUT / p
    if not f.exists(): f = OUT / p.replace("/", "__")
    if not f.exists() and p == "g_plbreak_master_tables.txt": f = OUT / "gates_plbreak_master_tables.txt"
    return f.read_text(encoding="utf-8", errors="replace").splitlines() if f.exists() else []

def summary(tag, d):
    ms = [l for l in lines(f"{d}/master_tables.txt") if l.startswith("SUMMARY")]
    dc = [l for l in lines(f"{d}/data_contract.txt") if l.startswith("SUMMARY")]
    cc = [l for l in lines(f"{d}/csm_continuity.txt") if l.startswith("[csm_continuity]")]
    cw = [l for l in lines(f"{d}/csm_waterfall.txt") if "pass=" in l]
    summ.append(f"## {tag}\n  master_tables: {ms[-1] if ms else '-'}\n  data_contract: {dc[-1] if dc else '-'}\n  csm_continuity: {cc[-1] if cc else '-'}\n  csm_waterfall: {cw[-1].strip() if cw else '-'}")

def findings(d):
    out = set()
    rx = re.compile(r"^\s{2}(RED|YELLOW)\s+\[([^\]]+)\]\s+(\S+)\s+(\S+)\s+(\S+)")
    for l in lines(f"{d}/data_contract.txt"):
        m = rx.match(l)
        if m: out.add(m.groups())
    return out

base = findings("g_base")
base_ms = set(l.strip() for l in lines("g_base/master_tables.txt"))
def new_ms_lines(path):
    return [l.strip() for l in lines(path) if l.strip() not in base_ms]

for tag, d in (("base", "g_base"), ("pl_closing", "g_pl"), ("csm_a51", "g_csm_a51"), ("csm_chain", "g_csm_chain"), ("csm_full", "g_csm_full")):
    summary(tag, d)
    if tag == "base": continue
    for sev, sheet, rule, name, q in sorted(findings(d) - base):
        eff[f"{name}|{q}"][tag].append(f"{sev} {rule}")
    # master_tables: csm_amort FAIL lines and NEW-FAIL lines
    for l in new_ms_lines(f"{d}/master_tables.txt"):
        m = re.match(r"FAIL\s+(\S+)\s+(\d{4}\.\dQ)\s+PL=.*잔차=\s*([+-][\d.]+)억", l)
        if m: eff[f"{m.group(1)}|{m.group(2)}"][tag].append(f"CSM_AMORT_IDENTITY FAIL residual {m.group(3)} eok")
        m = re.match(r"YEL\s+(\S+)\s+(\d{4}\.\dQ)\s+ΔBS=\s*([+-][\d.]+)\s+PL당분기=\s*([+-][\d.]+)\s+resid=\s*([+-][\d.]+)", l)
        if m: eff[f"{m.group(1)}|{m.group(2)}"][tag].append(f"YELLOW PL_OCI_VS_BS_AOCI resid {float(m.group(5))/100:+.1f} eok (BS AOCI still original vintage)")
# bridge-break set
for l in lines("g_plbreak_master_tables.txt"):
    m = re.match(r"\s*NEW-FAIL\s+(\S+)\|(\d{4}\.\dQ)\|(.+?)\s+<-", l)
    if m: eff[f"{m.group(1)}|{m.group(2)}"]["pl_bridgebreak"].append("NEW pl_bridge FAIL " + m.group(3)[:40])
# continuity gate lines (csm_continuity.txt) and master_tables CONT lines, new versus the baseline run
base_cont = set(l.strip() for l in lines("g_base/csm_continuity.txt"))
base_pl = set(l.strip() for l in lines("g_base/master_tables.txt"))
for tag, d in (("csm_a51", "g_csm_a51"), ("csm_chain", "g_csm_chain"), ("csm_full", "g_csm_full")):
    for l in lines(f"{d}/csm_continuity.txt"):
        if l.strip() in base_cont: continue
        m = re.match(r"\s*(RED|YELLOW)\s+(KR\d+)\s+(\S+): (\S+) — (FY\d{4} 기초 CSM 변동 [\d~]+)", l)
        if m: eff[f"{m.group(3)}|*"][tag + "_cont"].append(f"{m.group(1)} {m.group(4)} {m.group(5)}")
    for l in lines(f"{d}/master_tables.txt"):
        if l.strip() in base_pl: continue
        m = re.match(r"\s*CONT\s+(\S+)\s+(\d{4}\.\dQ) (.+)", l)
        if m: eff[f"{m.group(1)}|{m.group(2)}"][tag].append("CONT " + m.group(3).strip())
json.dump({k: dict(v) for k, v in eff.items()}, open(OUT / "d10_effects.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
(OUT / "d10_gate_summary.txt").write_text("\n".join(summ) + "\n", encoding="utf-8")
print("\n".join(summ))
