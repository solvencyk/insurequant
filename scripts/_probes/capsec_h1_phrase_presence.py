# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "dart" / "FY2026_Q2" / "raw"
census = json.loads((ROOT / "data" / "_derived" / "_probe_capsec_h1_census.json").read_text(encoding="utf-8"))
targets = [r["code"] for r in census if r["h1_filing_status"].startswith("FILED") and r["fy25_has_capsec"]]
for code in targets:
    d = next((p for p in RAW_DIR.iterdir() if p.name.startswith(code + "_")), None)
    xml = next(d.glob("*.xml"), None) if d else None
    text = xml.read_text(encoding="utf-8", errors="replace")
    has_phrase = "자본으로 인정되는 채무증권" in text
    has_hybrid_balance_title = "신종자본증권 미상환 잔액" in text or "신종자본증권미상환잔액" in text
    idx = text.find("자본으로 인정되는 채무증권")
    print(f"{code:7} phrase={has_phrase!s:5} idx={idx:8} hybrid_balance_title={has_hybrid_balance_title!s:5}")
