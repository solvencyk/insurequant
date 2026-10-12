# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit
edit("scripts/validate_live_artifacts.py", [
('''CAPTL_FIELDS = {"tier", "issue_date", "call_date", "coupon_pct", "face_eok", "outstanding_eok", "as_of"}
''',
'''CAPTL_FIELDS = {"tier", "issue_date", "call_date", "coupon_pct", "face_eok", "outstanding_eok", "as_of",
                "call_date_unconfirmed", "estimated"}
CAPTL_FLAGS = ("call_date_unconfirmed", "estimated")     # 선택 표지: 있으면 반드시 True (2026-10-12 감사 요청 1·2)
'''),
('''            extra = sorted(set(b) - CAPTL_FIELDS)
''',
'''            badflag = [f for f in CAPTL_FLAGS if f in b and b[f] is not True]
            if badflag:
                fd.add(A, "CAPTL_STRUCTURE", key, f"선택 표지 {badflag} 는 True 일 때만 존재해야 한다(값 {[b[f] for f in badflag]!r})")
                stat["structure_fail"] += 1
            extra = sorted(set(b) - CAPTL_FIELDS)
'''),
])
