# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit
edit("data/_derived/capsec_reinstate_20261012/s8_patch_forward_kr0050.py", [
('''F._args.bonds_source = man["bonds_source"]
''',
'''F._args.bonds_source = man["bonds_source"]
# the module computed its tier-file paths at import time from the default quarter; use the quarter the deployed forward was built with
F.TIER1_JSON = ROOT / man["tier1_utilization_json"].replace("\\\\", "/")
F.TIER2_JSON = ROOT / man["tier2_utilization_json"].replace("\\\\", "/")
'''),
])
