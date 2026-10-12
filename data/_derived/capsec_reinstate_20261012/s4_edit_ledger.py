# -*- coding: utf-8 -*-
"""Requests 1 + 2: ledger data/bonds/capital_securities_fy2026h1.json (CRLF preserved) + registry issue_date.

1) KR0011 DB손해보험 제1.2회 신종: the issuer's filings disagree on which bond is called 2030-09-01 vs 2030-09-25 -> keep the
   H1 values (forward/utilization are year-level and unchanged) but mark call_date_unconfirmed.
2) KR0050 하나손해보험: ledger not updated for the 2026-06-29 issuance (no H1 filing on disk) -> estimated row, marked estimated.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_util import edit

L = "data/bonds/capital_securities_fy2026h1.json"

NOTE_DB = ("제1회(발행 2025-09-01)·제2회(발행 2025-09-25)의 최초 콜일이 공시마다 다르다: FY2025 3Q·사업보고서는 두 회차 모두 2030-09-01, "
           "FY2026 1Q·반기보고서는 제1회 2030-09-25·제2회 2030-09-01(발행일+5년이면 제1회 09-01·제2회 09-25). 원문으로 확정 못 해 "
           "회차별 콜일-금액 짝을 화면에 싣지 않는다(근거 data/_derived/capsec_reinstate_20261012/y1_db_call_dates_all_filings.txt)")

edit(L, [
('''          "name": "제1회 신종자본증권 (공모)",
          "tier": "hybrid",
          "issue_date": "2025-09-01",
          "legal_maturity": "2055-09-01",
          "call_date": "2030-09-25",
          "call_source": "disclosed",
''',
f'''          "name": "제1회 신종자본증권 (공모)",
          "tier": "hybrid",
          "issue_date": "2025-09-01",
          "legal_maturity": "2055-09-01",
          "call_date": "2030-09-25",
          "call_source": "conflicting_filings",
          "call_date_unconfirmed": true,
          "call_date_candidates": ["2030-09-01", "2030-09-25"],
          "call_date_note": "{NOTE_DB}",
'''),
('''          "name": "제2회 신종자본증권 (사모)",
          "tier": "hybrid",
          "issue_date": "2025-09-25",
          "legal_maturity": "2055-09-25",
          "call_date": "2030-09-01",
          "call_source": "disclosed",
''',
f'''          "name": "제2회 신종자본증권 (사모)",
          "tier": "hybrid",
          "issue_date": "2025-09-25",
          "legal_maturity": "2055-09-25",
          "call_date": "2030-09-01",
          "call_source": "conflicting_filings",
          "call_date_unconfirmed": true,
          "call_date_candidates": ["2030-09-01", "2030-09-25"],
          "call_date_note": "{NOTE_DB}",
'''),
# ---- KR0050 estimated row (+ company total)
('''          "as_of": "2025-12-31",
          "source_file": "data/dart/FY2025_Q4/raw/KR0050_하나손해보험_20260325000538/20260325000538_00760.xml (한영회계법인 감사보고서, 별도; notes only, main report XML absent)"
        }
      ],''',
'''          "as_of": "2025-12-31",
          "source_file": "data/dart/FY2025_Q4/raw/KR0050_하나손해보험_20260325000538/20260325000538_00760.xml (한영회계법인 감사보고서, 별도; notes only, main report XML absent)"
        },
        {
          "name": "하나손해보험 신종자본증권 (2026-06-29 발행, 추정 행 - 원장 미갱신)",
          "tier": "hybrid",
          "issue_date": "2026-06-29",
          "legal_maturity": null,
          "call_date": null,
          "call_source": "estimated_no_filing",
          "coupon_pct": null,
          "face_amount_mn": 99900,
          "outstanding_mn": 99900,
          "past_call_outstanding": false,
          "as_of": "2026-06-30",
          "estimated": true,
          "source_file": "kics_disclosure.json 2026.2Q 항목 6 증가분 +999억 (data/dart/FY2026_Q2/raw/KR0050_하나손해보험 에는 반기보고서가 없음 - meta.json no_filing)",
          "notes": "추정 행: 원장이 2025-12-31 기준으로 멈춰 있어 2026.2Q 신종 증가분(항목 6 1,000 -> 1,999)을 한 건으로 적음. 발행일은 census(보도 + owner 발췌)의 2026-06-29. 금리·콜일·만기는 원문 확인 전이라 비워 둠(forward 에서 콜 이벤트로 잡히지 않음). 반기보고서가 게시되면 이 행을 실제 증권으로 교체한다."
        }
      ],'''),
('''      "total_hybrid_outstanding_mn": 100000,
      "total_subordinated_outstanding_mn": 0,
      "confidence": "high",
      "bonds": [
        {
          "name": "하나손해보험 제1회 신종자본증권(사모)",''',
'''      "total_hybrid_outstanding_mn": 199900,
      "total_subordinated_outstanding_mn": 0,
      "confidence": "high",
      "bonds": [
        {
          "name": "하나손해보험 제1회 신종자본증권(사모)",'''),
])
