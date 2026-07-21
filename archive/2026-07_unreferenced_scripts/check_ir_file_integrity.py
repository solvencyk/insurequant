"""IR file integrity checker.

Walks data/ir/FY*_Q*/raw/ and verifies that every xlsx/xls/pdf actually
opens as the format its extension claims. Reports a structured result so
the orchestrator can decide which files to re-download.

Checks:
  - xlsx: must be a zip archive containing xl/workbook.xml
  - xls:  must start with OLE compound header \xd0\xcf\x11\xe0
          AND have a workbook stream (try xlrd if available)
  - pdf:  must start with %PDF
  - Any text/HTML body (server error page saved as .xlsx) flagged broken
  - 0-byte or <1KB files flagged
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
IR_ROOT = ROOT / "data" / "ir"

MIN_BYTES = 1024  # anything smaller than 1KB is suspect


def classify(path: Path) -> dict[str, Any]:
    """Return dict with keys: ok (bool), reason (str), size, magic."""
    if not path.is_file():
        return {"ok": False, "reason": "not a file", "size": 0, "magic": ""}

    size = path.stat().st_size
    if size == 0:
        return {"ok": False, "reason": "zero bytes", "size": 0, "magic": ""}
    if size < MIN_BYTES:
        head_bytes = path.read_bytes()[:32]
        return {
            "ok": False,
            "reason": f"too small ({size} bytes)",
            "size": size,
            "magic": head_bytes.hex()[:16],
        }

    head = path.read_bytes()[:8]
    magic_hex = head.hex()[:16]
    ext = path.suffix.lower()

    # xlsx = zip
    if ext == ".xlsx":
        if not head.startswith(b"PK\x03\x04"):
            # might be html error page or OLE
            if head.startswith(b"<") or head.startswith(b"\xef\xbb\xbf<"):
                return {"ok": False, "reason": "html/text body, not xlsx", "size": size, "magic": magic_hex}
            if head.startswith(b"\xd0\xcf\x11\xe0"):
                return {"ok": False, "reason": "OLE file (xls) saved as .xlsx", "size": size, "magic": magic_hex}
            return {"ok": False, "reason": f"unexpected magic {magic_hex}", "size": size, "magic": magic_hex}
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                if "xl/workbook.xml" not in names:
                    return {"ok": False, "reason": "zip but no xl/workbook.xml", "size": size, "magic": magic_hex}
                # try to actually read workbook.xml
                with zf.open("xl/workbook.xml") as fh:
                    body = fh.read()
                    if not body or b"<workbook" not in body[:4096]:
                        return {"ok": False, "reason": "workbook.xml empty/malformed", "size": size, "magic": magic_hex}
        except zipfile.BadZipFile as e:
            return {"ok": False, "reason": f"bad zip: {e}", "size": size, "magic": magic_hex}
        except Exception as e:
            return {"ok": False, "reason": f"zip read error: {e}", "size": size, "magic": magic_hex}
        return {"ok": True, "reason": "ok", "size": size, "magic": magic_hex}

    # xls = OLE compound
    if ext == ".xls":
        if not head.startswith(b"\xd0\xcf\x11\xe0"):
            if head.startswith(b"PK\x03\x04"):
                return {"ok": False, "reason": "zip (xlsx) saved as .xls", "size": size, "magic": magic_hex}
            if head.startswith(b"<") or head.startswith(b"\xef\xbb\xbf<"):
                return {"ok": False, "reason": "html/text body, not xls", "size": size, "magic": magic_hex}
            return {"ok": False, "reason": f"unexpected magic {magic_hex}", "size": size, "magic": magic_hex}
        # try xlrd to make sure it's a real workbook
        try:
            import xlrd  # type: ignore
            xlrd.open_workbook(str(path))
            return {"ok": True, "reason": "ok", "size": size, "magic": magic_hex}
        except ImportError:
            # no xlrd, just trust OLE header
            return {"ok": True, "reason": "ole header only (xlrd unavailable)", "size": size, "magic": magic_hex}
        except Exception as e:
            return {"ok": False, "reason": f"xlrd open failed: {e}", "size": size, "magic": magic_hex}

    # pdf
    if ext == ".pdf":
        if not head.startswith(b"%PDF"):
            if head.startswith(b"PK\x03\x04"):
                return {"ok": False, "reason": "zip saved as .pdf", "size": size, "magic": magic_hex}
            if head.startswith(b"<") or head.startswith(b"\xef\xbb\xbf<"):
                return {"ok": False, "reason": "html/text body, not pdf", "size": size, "magic": magic_hex}
            return {"ok": False, "reason": f"unexpected magic {magic_hex}", "size": size, "magic": magic_hex}
        # spot check footer for %%EOF
        try:
            tail = path.read_bytes()[-64:]
            if b"%%EOF" not in tail and b"EOF" not in tail:
                return {"ok": False, "reason": "missing %%EOF marker", "size": size, "magic": magic_hex}
        except Exception:
            pass
        return {"ok": True, "reason": "ok", "size": size, "magic": magic_hex}

    # other extensions (txt, json, html) - just sanity check size
    return {"ok": True, "reason": f"skipped (.{ext.lstrip('.')})", "size": size, "magic": magic_hex}


def main() -> int:
    if not IR_ROOT.exists():
        print(f"IR root not found: {IR_ROOT}")
        return 1

    results: list[dict[str, Any]] = []
    for period_dir in sorted(IR_ROOT.glob("FY*_Q*")):
        raw_dir = period_dir / "raw"
        if not raw_dir.exists():
            continue
        for path in sorted(raw_dir.rglob("*")):
            if not path.is_file():
                continue
            # skip failures dump
            if "_failures" in path.parts:
                continue
            # skip manifest JSON
            if path.name == "_manifest.json":
                continue
            rel = path.relative_to(IR_ROOT)
            res = classify(path)
            res["path"] = str(rel).replace("\\", "/")
            res["period"] = period_dir.name
            results.append(res)

    broken = [r for r in results if not r["ok"]]
    ok_count = len(results) - len(broken)
    print(f"Total files: {len(results)}")
    print(f"OK         : {ok_count}")
    print(f"BROKEN     : {len(broken)}")
    print()

    if broken:
        print("=== BROKEN FILES ===")
        for r in broken:
            print(f"  [{r['period']}] {r['path']}")
            print(f"      reason: {r['reason']}  size={r['size']}  magic={r['magic']}")
        print()

    # write JSON report
    report_path = ROOT / "data" / "ir" / "_integrity_report.json"
    report_path.write_text(
        json.dumps(
            {"total": len(results), "ok": ok_count, "broken_count": len(broken), "broken": broken, "all": results},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"report written: {report_path.relative_to(ROOT)}")

    return 0 if not broken else 2


if __name__ == "__main__":
    sys.exit(main())
