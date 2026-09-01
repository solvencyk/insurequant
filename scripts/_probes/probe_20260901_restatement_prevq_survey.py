# -*- coding: utf-8 -*-
"""STEP 1 — 2026.2Q 공시본의 '적용 전 지급여력비율 세부' 표 헤더 전수 조사.

목적: 39사 각각에서 (a) 그 표가 있는지 (b) 헤더가 직전분기 컬럼을 어떻게 부르는지
(c) 컬럼이 몇 개인지 를 실측한다. 라벨 매칭을 느슨하게 하면 다른 단위(백만원) 표를
긁어 오탐이 난다 — 그래서 표를 먼저 정확히 특정한다.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "parsed"

HEAD_RE = re.compile(r"경과조치\s*적용\s*전\s*지급여력비율\s*세부")


def md_tables(text: str):
    """(start_line, header_cells, rows) 목록. rows = [(label, [cells...])]"""
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.lstrip().startswith("|") and ln.rstrip().endswith("|"):
            j = i
            block = []
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                block.append(lines[j])
                j += 1
            if len(block) >= 2:
                def cells(s):
                    return [c.strip() for c in s.strip().strip("|").split("|")]
                header = cells(block[0])
                body = []
                for b in block[1:]:
                    c = cells(b)
                    if all(set(x) <= set("-: ") for x in c):
                        continue
                    body.append(c)
                out.append((i + 1, header, body))
            i = j
        else:
            i += 1
    return out


def main():
    for f in sorted(MD_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()
        heads = [k for k, ln in enumerate(lines) if HEAD_RE.search(ln)]
        tabs = md_tables(text)
        print("=" * 100)
        print(f"{f.stem}   heading_hits={len(heads)} at lines {[h+1 for h in heads]}")
        # 헤딩 직후 첫 표를 보여준다
        for h in heads:
            cand = [t for t in tabs if t[0] > h]
            if not cand:
                print("   (no table after heading)")
                continue
            ln0, header, body = cand[0]
            print(f"   L{ln0} header={header}")
            print(f"   nrows={len(body)}  first={body[0] if body else None}")
            print(f"   last={body[-1] if body else None}")
        if not heads:
            # 헤딩이 없는 회사: '지급여력금액' 을 첫 열에 가진 표를 전부 인쇄
            for ln0, header, body in tabs:
                if body and any("지급여력금액" in (r[0] or "") for r in body[:4]):
                    print(f"   [noheading] L{ln0} header={header} nrows={len(body)}")
                    print(f"      first={body[0]}")


if __name__ == "__main__":
    sys.exit(main())
