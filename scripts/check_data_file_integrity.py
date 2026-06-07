"""Cross-source file integrity checker.

Walks data/{ir,disclosure,dart,kidi}/FY*_Q*/raw/ and verifies every
file actually opens as its extension claims. Reports broken files per
source so we can re-download them.

Magic-byte rules:
  - .xlsx  → PK\x03\x04 zip + must contain xl/workbook.xml
  - .xls   → \xd0\xcf\x11\xe0 OLE compound
  - .pdf   → %PDF... + %%EOF in tail
  - .zip   → PK\x03\x04 + zipfile.testzip() returns None
  - .json  → utf-8 parseable
  - .html  → contains '<' early
  - others → just size sanity
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data"
SOURCES = ["ir", "disclosure", "dart", "kidi"]

MIN_BYTES = 512  # any file smaller than this in our universe is suspect


def classify(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "reason": "not a file", "size": 0, "magic": ""}
    size = path.stat().st_size
    if size == 0:
        return {"ok": False, "reason": "zero bytes", "size": 0, "magic": ""}

    head = path.read_bytes()[:8] if size >= 8 else path.read_bytes()
    magic_hex = head.hex()[:16]
    ext = path.suffix.lower()

    if size < MIN_BYTES and ext not in {".json", ".txt"}:
        return {"ok": False, "reason": f"too small ({size}B)", "size": size, "magic": magic_hex}

    if ext == ".xlsx":
        if not head.startswith(b"PK\x03\x04"):
            if head.startswith(b"<") or head.startswith(b"\xef\xbb\xbf<"):
                return {"ok": False, "reason": "html body not xlsx", "size": size, "magic": magic_hex}
            if head.startswith(b"\xd0\xcf\x11\xe0"):
                return {"ok": False, "reason": "OLE saved as xlsx", "size": size, "magic": magic_hex}
            return {"ok": False, "reason": f"bad magic {magic_hex}", "size": size, "magic": magic_hex}
        try:
            with zipfile.ZipFile(path) as zf:
                if "xl/workbook.xml" not in zf.namelist():
                    return {"ok": False, "reason": "no xl/workbook.xml", "size": size, "magic": magic_hex}
                with zf.open("xl/workbook.xml") as fh:
                    body = fh.read(4096)
                    if b"<workbook" not in body:
                        return {"ok": False, "reason": "workbook.xml malformed", "size": size, "magic": magic_hex}
        except zipfile.BadZipFile as e:
            return {"ok": False, "reason": f"bad zip: {e}", "size": size, "magic": magic_hex}
        except Exception as e:
            return {"ok": False, "reason": f"zip read err: {e}", "size": size, "magic": magic_hex}
        return {"ok": True, "reason": "ok", "size": size, "magic": magic_hex}

    if ext == ".xls":
        if not head.startswith(b"\xd0\xcf\x11\xe0"):
            if head.startswith(b"PK\x03\x04"):
                return {"ok": False, "reason": "zip saved as xls", "size": size, "magic": magic_hex}
            if head.startswith(b"<") or head.startswith(b"\xef\xbb\xbf<"):
                return {"ok": False, "reason": "html body not xls", "size": size, "magic": magic_hex}
            return {"ok": False, "reason": f"bad magic {magic_hex}", "size": size, "magic": magic_hex}
        try:
            import xlrd  # type: ignore
            xlrd.open_workbook(str(path))
            return {"ok": True, "reason": "ok (xlrd open)", "size": size, "magic": magic_hex}
        except ImportError:
            return {"ok": True, "reason": "ok (ole header only)", "size": size, "magic": magic_hex}
        except Exception as e:
            return {"ok": False, "reason": f"xlrd open err: {e}", "size": size, "magic": magic_hex}

    if ext == ".pdf":
        if not head.startswith(b"%PDF"):
            if head.startswith(b"PK\x03\x04"):
                return {"ok": False, "reason": "zip saved as pdf", "size": size, "magic": magic_hex}
            if head.startswith(b"<") or head.startswith(b"\xef\xbb\xbf<"):
                return {"ok": False, "reason": "html body not pdf", "size": size, "magic": magic_hex}
            return {"ok": False, "reason": f"bad magic {magic_hex}", "size": size, "magic": magic_hex}
        # Some valid PDFs have trailing padding after %%EOF; search full content
        body = path.read_bytes()
        if b"%%EOF" not in body[-16384:] and b"%%EOF" not in body:
            return {"ok": False, "reason": "missing %%EOF", "size": size, "magic": magic_hex}
        if b"startxref" not in body[-32768:]:
            return {"ok": False, "reason": "missing startxref", "size": size, "magic": magic_hex}
        return {"ok": True, "reason": "ok", "size": size, "magic": magic_hex}

    if ext == ".zip":
        if not head.startswith(b"PK\x03\x04") and not head.startswith(b"PK\x05\x06"):
            return {"ok": False, "reason": f"bad magic {magic_hex}", "size": size, "magic": magic_hex}
        try:
            with zipfile.ZipFile(path) as zf:
                bad = zf.testzip()
                if bad is not None:
                    return {"ok": False, "reason": f"bad member {bad}", "size": size, "magic": magic_hex}
                if not zf.namelist():
                    return {"ok": False, "reason": "empty zip", "size": size, "magic": magic_hex}
        except zipfile.BadZipFile as e:
            return {"ok": False, "reason": f"bad zip: {e}", "size": size, "magic": magic_hex}
        except Exception as e:
            return {"ok": False, "reason": f"zip read err: {e}", "size": size, "magic": magic_hex}
        return {"ok": True, "reason": "ok", "size": size, "magic": magic_hex}

    if ext == ".json":
        try:
            txt = path.read_text(encoding="utf-8")
            json.loads(txt)
            return {"ok": True, "reason": "ok", "size": size, "magic": magic_hex}
        except UnicodeDecodeError as e:
            return {"ok": False, "reason": f"utf-8 decode err: {e}", "size": size, "magic": magic_hex}
        except json.JSONDecodeError as e:
            return {"ok": False, "reason": f"json parse err: {e}", "size": size, "magic": magic_hex}

    if ext == ".xml":
        try:
            txt = path.read_text(encoding="utf-8")
            if "<" not in txt[:1024]:
                return {"ok": False, "reason": "no xml tag in first 1KB", "size": size, "magic": magic_hex}
            return {"ok": True, "reason": "ok", "size": size, "magic": magic_hex}
        except UnicodeDecodeError:
            # try cp949
            try:
                txt = path.read_text(encoding="cp949")
                if "<" not in txt[:1024]:
                    return {"ok": False, "reason": "no xml tag (cp949)", "size": size, "magic": magic_hex}
                return {"ok": True, "reason": "ok (cp949)", "size": size, "magic": magic_hex}
            except Exception as e:
                return {"ok": False, "reason": f"xml decode err: {e}", "size": size, "magic": magic_hex}

    # other extensions
    return {"ok": True, "reason": f"skipped (.{ext.lstrip('.')})", "size": size, "magic": magic_hex}


def walk_source(source: str) -> list[dict[str, Any]]:
    src_root = DATA_ROOT / source
    if not src_root.exists():
        return []
    results: list[dict[str, Any]] = []
    for period_dir in sorted(src_root.glob("FY*_Q*")):
        raw_dir = period_dir / "raw"
        if not raw_dir.exists():
            continue
        for path in sorted(raw_dir.rglob("*")):
            if not path.is_file():
                continue
            # skip non-data
            if "_failures" in path.parts:
                continue
            if path.name in {"_manifest.json", "meta.json"}:
                continue
            # skip .bad backups
            if path.suffix == ".bad" or path.name.endswith(".bad"):
                continue
            # skip Office temp lock files (e.g. "~$FY25 ...xlsx") created while
            # a workbook is open in Excel — not data, and read-locked on Windows.
            if path.name.startswith("~$"):
                continue
            res = classify(path)
            rel = path.relative_to(DATA_ROOT)
            res["path"] = str(rel).replace("\\", "/")
            res["period"] = period_dir.name
            res["source"] = source
            results.append(res)
    return results


def main() -> int:
    all_results: list[dict[str, Any]] = []
    per_source_summary: dict[str, dict[str, int]] = {}
    for src in SOURCES:
        rs = walk_source(src)
        all_results.extend(rs)
        broken = [r for r in rs if not r["ok"]]
        per_source_summary[src] = {"total": len(rs), "ok": len(rs) - len(broken), "broken": len(broken)}

    print("=== SUMMARY ===")
    for src, s in per_source_summary.items():
        print(f"  {src:12s}  total={s['total']:5d}  ok={s['ok']:5d}  broken={s['broken']:5d}")
    total_broken = sum(s["broken"] for s in per_source_summary.values())
    print(f"  TOTAL BROKEN: {total_broken}")
    print()

    broken_all = [r for r in all_results if not r["ok"]]
    if broken_all:
        print("=== BROKEN FILES ===")
        for r in broken_all:
            print(f"  [{r['source']:11s}] [{r['period']}] {r['path']}")
            print(f"      reason: {r['reason']}  size={r['size']}  magic={r['magic']}")
        print()

    report = {
        "summary": per_source_summary,
        "broken_count": total_broken,
        "broken": broken_all,
    }
    out_path = DATA_ROOT / "_integrity_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {out_path.relative_to(ROOT)}")
    return 0 if total_broken == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
