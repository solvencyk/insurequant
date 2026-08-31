import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

with open(ROOT / "artifacts" / "kics_validation" / "report_latest.json", encoding="utf-8") as f:
    report = json.load(f)


def walk(obj, path=""):
    """Yield (path, obj) for every dict/list node, to locate KR0008 2026.2Q findings
    regardless of the report's exact schema."""
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


hits = []
for path, obj in walk(report):
    if isinstance(obj, dict):
        code = obj.get("원보험사코드") or obj.get("code") or obj.get("company_code")
        quarter = obj.get("공시분기") or obj.get("quarter")
        if code == "KR0008" and quarter == "2026.2Q":
            hits.append((path, obj))

print("top-level keys:", list(report.keys()) if isinstance(report, dict) else type(report))
print("num hits:", len(hits))
with open(ROOT / "scripts" / "_probes" / "_out_kr0008_gate_findings.json", "w", encoding="utf-8") as f:
    json.dump([{"path": p, "obj": o} for p, o in hits], f, ensure_ascii=False, indent=2)
print("wrote", len(hits), "hits")
