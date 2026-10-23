# -*- coding: utf-8 -*-
"""READ-ONLY (ticket 20261024T0100Z, KR0010 KB손해보험 item 16 기타사업비용): for every KB손보 filing FY2023_Q1..FY2026_Q2 print the separate-basis statement row(s) labelled
기타사업비(용) with cur/prior x cum/3m cells (value, physical xml line), the unit of the statement and the statement section title.
Own use of the e21 statement reader (which reads the 4-2 포괄손익계산서 = separate basis)."""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0010"
FYS = ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4", "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4", "FY2026_Q1", "FY2026_Q2"]
for fy in FYS:
    try:
        st = R.Stmt(CODE, fy)
    except Exception as e:  # noqa: BLE001
        print(f"##### {fy}: cannot read statement: {type(e).__name__}: {e}")
        continue
    print(f"##### {fy} {st.rel} fmt={st.fmt} unit={st.unit} title_line={st.title}")
    hits = [r for r in st.rows if "기타사업비" in r.lab]
    if not hits:
        print("   (no row with 기타사업비)")
    for r in hits:
        out = []
        for role in ("cur", "prior"):
            for kind in ("cum", "3m"):
                c = st.pick_cell(r, role, kind)
                out.append(f"{role}/{kind}=" + ("n/a" if c is None else f"{c['text']}@L{c['line']}"))
        print(f"   row L{r.line} {r.raw!r} oci={r.oci}: " + " | ".join(out))
