# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
raw = open(R + "insurance_liability_portfolio_provenance.json", "rb").read()
print("bytes", len(raw), "CRLF" if b"\r\n" in raw else "LF", "endsNL" if raw.endswith(b"\n") else "noEndNL")
d = json.loads(raw.decode("utf-8"))
print("top keys:", list(d.keys()))
for c in d["cells"]:
    if c["company_code"] == "KR0100" and c["quarter"] in ("2024.1Q", "2023.1Q", "2025.3Q", "2024.4Q"):
        print("=" * 90)
        print(json.dumps(c, ensure_ascii=False, indent=1))
