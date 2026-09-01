# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "scripts"))
import fill_market_subitems_to_disclosure as F
import glob
g = glob.glob(str(REPO / "md_inbox" / "FY2026_Q2" / "KR0099_*.md"))
text = Path(g[0]).read_text(encoding="utf-8")
subs = F.extract_mkt_subs(text)
print("subs:", subs)
