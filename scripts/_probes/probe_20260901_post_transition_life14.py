"""Enumerate POST_TRANSITION_PARENT_MISSING / POST_TRANSITION_CHILD_MISSING RED findings
for the 16 life-insurer companies, 2026.2Q only. Read-only probe, no writes.

Usage: venv python scripts/_probes/probe_20260901_post_transition_life14.py
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_data_contract import Env, run_gate  # noqa: E402

MY_CODES = {
    "KR0068": "한화생명", "KR0069": "삼성생명", "KR0070": "에이비엘", "KR0071": "흥국생명",
    "KR0072": "케이디비", "KR0080": "에이아이에이", "KR0082": "DB생명", "KR0083": "푸본현대",
    "KR0087": "동양생명", "KR0094": "신한라이프", "KR0097": "하나생명", "KR0099": "KB라이프",
    "KR0100": "처브라이프", "KR0104": "농협생명", "KR1010": "교보라이프플래닛", "KR1011": "IBK연금",
}

TARGET_RULES = {"POST_TRANSITION_PARENT_MISSING", "POST_TRANSITION_CHILD_MISSING"}

env = Env()
res = run_gate(env)

mine = [f for f in res.findings
        if f.rule in TARGET_RULES and f.company in MY_CODES and f.quarter == "2026.2Q"]

print(f"Total findings: {len(res.findings)}  RED: {len(res.red)}  YELLOW: {len(res.yellow)}")
print(f"My-scope (16 life x 2026.2Q x {TARGET_RULES}): {len(mine)}")
print()

by_company = {}
for f in mine:
    by_company.setdefault(f.company, []).append(f)

for code in MY_CODES:
    items = by_company.get(code, [])
    print(f"=== {code} {MY_CODES[code]} : {len(items)} finding(s) ===")
    for f in items:
        print(f"  [{f.severity}] {f.rule} | {f.message}")
    print()

# also: any of MY_CODES with these rules but OTHER quarters, for context
other_q = [f for f in res.findings if f.rule in TARGET_RULES and f.company in MY_CODES and f.quarter != "2026.2Q"]
print(f"--- Same companies, other quarters (context only, not in scope): {len(other_q)} ---")
for f in other_q:
    print(f"  {f.company} {f.quarter} [{f.severity}] {f.rule} | {f.message}")
