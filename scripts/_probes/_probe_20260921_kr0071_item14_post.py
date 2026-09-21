"""Read-only probe: inspect KR0071 item14/15/22/23 rows for 2025.2Q and 2025.4Q.

Ticket: inbox/parser/20260921T1400Z__validation__MULTI_2024.4Q-2025.4Q__ratesens_phase_level_holes.md SS B.
No writes to kics_disclosure.json here.
"""
import json
import sys

MASTER = "kics_disclosure.json"
TARGET_QUARTERS = {"2025.2Q", "2025.4Q"}
TARGET_ITEMS = {1, 14, 15, 22, 23, 27}


def main():
    with open(MASTER, encoding="utf-8") as f:
        data = json.load(f)

    rows = [
        r
        for r in data
        if r.get("원보험사코드") == "KR0071"
        and r.get("공시분기") in TARGET_QUARTERS
        and r.get("항목번호") in TARGET_ITEMS
    ]
    rows.sort(key=lambda r: (r.get("공시분기"), r.get("항목번호")))

    out = []
    for r in rows:
        out.append(
            {
                "quarter": r.get("공시분기"),
                "item_no": r.get("항목번호"),
                "item_name": r.get("항목명"),
                "value": r.get("값"),
                "value_post": r.get("값_적용후"),
            }
        )

    with open(
        "data/_derived/_probe_20260921_kr0071_item14_post.json", "w", encoding="utf-8"
    ) as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    for row in out:
        print(row)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
