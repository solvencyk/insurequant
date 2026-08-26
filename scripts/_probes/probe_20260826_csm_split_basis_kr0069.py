#!/usr/bin/env python3
"""KR0069 2023.4Q: 본문을 별도 경계에서 잘라 연결/별도 각각의 CSM 워터폴을 뽑는다."""
import sys, re, os, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as B
from scripts.pl_breakdown.common import _ofs_line_boundary

STRIP = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
CFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*연결\s*재무(제표|상태표)")
OFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*재무(제표|상태표)\s*$")

def boundary(p):
    b = _ofs_line_boundary(p)
    if b is not None:
        return b
    cfs = False
    with open(p, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if "재무" not in line:
                continue
            t = STRIP(line)
            if CFS_HEAD.match(t):
                cfs = True
            elif cfs and OFS_HEAD.match(t):
                return i
    return None

_orig = B.blocks_for_dir

for q, anchor in [("FY2023_Q4", None), ("FY2024_Q4", None)]:
    rd = sorted((ROOT / "data" / "dart" / q / "raw").glob("KR0069_*"))[0]
    main = [x for x in sorted(rd.glob("*.xml")) if "_007" not in x.name][0]
    b = boundary(main)
    lines = main.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    print("=" * 96)
    print(f"### {q}  {main.name}  경계={b:,}  총 {len(lines):,}줄")
    for tag, part in (("연결(head)", lines[:b - 1]), ("별도(tail)", lines[b - 1:])):
        fh = tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False, encoding="utf-8")
        fh.write("".join(part)); fh.close()
        tmpdir = Path(tempfile.mkdtemp())
        dst = tmpdir / rd.name
        dst.mkdir()
        os.replace(fh.name, dst / main.name)
        try:
            wf, src = B.waterfall_for_dir(dst, "삼성생명", anchor=anchor)
            nb = len(_orig(dst, "삼성생명"))
            print(f"  {tag:11s} blocks={nb:3d}  " +
                  (" ".join(f"{i}={(wf or {}).get(i)}" for i in (1, 2, 3, 4, 5, 6)) if wf else "None")
                  + f"   src={src}")
        finally:
            for f2 in dst.glob("*"):
                f2.unlink()
            dst.rmdir(); tmpdir.rmdir()
