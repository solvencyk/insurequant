# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit
edit("scripts/capital_utilization_rules.py", [
("""        post_is_gross = gross and (close(p1, i3) or close(p1, p0))
        d1 = (p1 - l49) if post_is_gross else p1
        src_post = "항목 47 적용후" + (" - 항목 49" if post_is_gross else "")
        src_pre = "항목 47 적용전" + (" - 항목 49" if gross else "")
        if post.get(47) is None:
            src_post = src_post.replace("적용후", "적용후(미인쇄 -> 적용전 값)")
""",
"""        src_pre = "항목 47 적용전" + (" - 항목 49" if gross else "")
"""),
])
