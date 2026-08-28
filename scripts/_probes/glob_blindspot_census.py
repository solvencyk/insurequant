"""Reproduce the orchestrator's raw-directory census (inbox/parser/20260829T1600Z):
of data/dart/FY*/raw/KR* company-filing directories, how many have XML ONLY under xml/
(quarterly-report convention), only at top level (annual-report convention), both, or
neither. Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

xml_only_sub = []
top_only = []
both = []
neither = []

for fy_dir in sorted(ROOT.glob("data/dart/FY*/raw")):
    for company_dir in sorted(fy_dir.iterdir()):
        if not company_dir.is_dir() or not company_dir.name.startswith("KR"):
            continue
        top_xml = list(company_dir.glob("*.xml"))
        sub_xml = list((company_dir / "xml").glob("*.xml")) if (company_dir / "xml").is_dir() else []
        if top_xml and sub_xml:
            both.append(company_dir)
        elif sub_xml and not top_xml:
            xml_only_sub.append(company_dir)
        elif top_xml and not sub_xml:
            top_only.append(company_dir)
        else:
            neither.append(company_dir)

print(f"xml/ subdir ONLY (quarterly convention): {len(xml_only_sub)}")
print(f"top-level ONLY (annual convention): {len(top_only)}")
print(f"BOTH top-level and xml/ subdir: {len(both)}")
print(f"NEITHER (no xml at all -- zip-only or empty): {len(neither)}")
print(f"total company-filing dirs: {len(xml_only_sub) + len(top_only) + len(both) + len(neither)}")

print("\n--- xml/-subdir-only dirs (first 20) ---")
for d in xml_only_sub[:20]:
    print(" ", d.relative_to(ROOT))
if len(xml_only_sub) > 20:
    print(f"  ... ({len(xml_only_sub) - 20} more)")

print("\n--- BOTH dirs (all) ---")
for d in both:
    print(" ", d.relative_to(ROOT))

print("\n--- NEITHER dirs (all, if any) ---")
for d in neither:
    print(" ", d.relative_to(ROOT))
