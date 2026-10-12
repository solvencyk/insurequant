# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit
edit("data/bonds/capital_tier_registry.json", [
('{"name": "2026.2Q 신규 신종자본증권(채권원장 미등재)", "issue_date": "2026.2Q", "amount_eok": 999.0, "amount_basis": "2026.2Q 항목 6 증가분",',
 '{"name": "하나손해보험 신종자본증권 (2026-06-29 발행, 추정 행)", "issue_date": "2026-06-29", "amount_eok": 999.0, "amount_basis": "2026.2Q 항목 6 증가분 = 채권원장 추정 행(원장 미갱신, 2026-10-12)",'),
])
