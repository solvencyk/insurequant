# -*- coding: utf-8 -*-
"""게이트 파일 배선 census — "라이브가 fetch 하는 파일을 누가 읽는가".

불변식 1번("게이트가 검사하는 파일 = 사용자가 보는 파일")을 기계로 대조한다.

  A축: origin/main 의 배포 HTML 4종이 fetch 하는 .json 경로 전수
  B축: scripts/validate_*.py + prepush_check.py 가 **읽는** 파일 전수
       - 문자열 리터럴만 세면 동적 경로 조립을 놓친다 → import 그래프를 1-hop 따라가고
         f-string / os.path.join / Path(...) / % 포맷도 같이 센다.

사용: python scripts/_probes/probe_20260825_gate_file_wiring_census.py
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = ["index.html", "K-ICS.html", "IFRS17.html", "공시보고서.html"]


def git_show(rev: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=str(ROOT),
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace")


def html_fetches(rev: str = "origin/main") -> dict[str, set[str]]:
    """HTML 이 fetch/참조하는 .json 경로."""
    out: dict[str, set[str]] = {}
    for h in HTML:
        src = git_show(rev, h)
        if src is None:
            out[h] = set()
            continue
        found = set()
        # fetch('x.json') / fetch("./data/y.json") / 'z.json' 문자열 전반
        for m in re.finditer(r"""['"`]([^'"`\s]+?\.json)['"`]""", src):
            p = m.group(1).lstrip("./")
            found.add(p)
        out[h] = found
    return out


# ---------------------------------------------------------------------------
# B축: 검사기가 읽는 파일 (AST — 리터럴 + 동적 조립 + import 1-hop)
# ---------------------------------------------------------------------------
class PathVisitor(ast.NodeVisitor):
    def __init__(self):
        self.literals: set[str] = set()
        self.dynamic: list[str] = []

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str) and node.value.endswith(".json"):
            self.literals.add(node.value.replace("\\", "/").lstrip("./"))
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        # f-string: 정적 조각을 이어 붙여 .json 으로 끝나면 동적 경로 후보
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            else:
                parts.append("{?}")
        s = "".join(parts)
        if ".json" in s:
            self.dynamic.append(s)
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        # "%s.json" % x  또는  base + "/x.json"
        try:
            seg = ast.unparse(node)
        except Exception:
            seg = ""
        if ".json" in seg and "{" not in seg:
            self.dynamic.append(seg[:120])
        self.generic_visit(node)


def scan_py(path: Path) -> tuple[set[str], list[str], set[str]]:
    """(json 리터럴, 동적 후보, 로컬 import 모듈명)"""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    v = PathVisitor()
    v.visit(tree)
    imports: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                imports.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
    return v.literals, v.dynamic, imports


def validator_reads() -> dict[str, dict]:
    scripts = sorted((ROOT / "scripts").glob("validate_*.py"))
    scripts.append(ROOT / "scripts" / "prepush_check.py")
    res: dict[str, dict] = {}
    for p in scripts:
        if not p.exists():
            continue
        lits, dyn, imps = scan_py(p)
        # import 1-hop: scripts/ 안의 로컬 모듈이면 그것도 읽은 것으로 친다
        hop: set[str] = set()
        hop_dyn: list[str] = []
        for m in sorted(imps):
            q = ROOT / "scripts" / f"{m}.py"
            if q.exists() and q != p:
                l2, d2, _ = scan_py(q)
                hop |= l2
                hop_dyn += [f"[{m}] {d}" for d in d2]
        res[p.stem] = {
            "literals": sorted(lits),
            "dynamic": sorted(set(dyn)),
            "via_import": sorted(hop),
            "via_import_dynamic": sorted(set(hop_dyn)),
            "imports_local": sorted(m for m in imps
                                    if (ROOT / "scripts" / f"{m}.py").exists()),
        }
    return res


def main() -> int:
    fetches = html_fetches()
    all_fetched: set[str] = set()
    for h, s in fetches.items():
        all_fetched |= s

    reads = validator_reads()
    # 누가 읽는가 역인덱스
    reader_of: dict[str, list[str]] = {}
    for name, d in reads.items():
        for f in d["literals"] + d["via_import"]:
            reader_of.setdefault(f, []).append(name)

    print("=" * 78)
    print("A. 라이브 HTML(origin/main) 이 fetch 하는 .json")
    print("=" * 78)
    for h in HTML:
        print(f"\n[{h}]  {len(fetches[h])}개")
        for f in sorted(fetches[h]):
            exists = (ROOT / f).exists()
            on_main = git_show("origin/main", f) is not None
            rd = sorted(set(reader_of.get(f, [])))
            print(f"   {f:52s} local={'Y' if exists else 'N'} "
                  f"main={'Y' if on_main else 'N'} readers={rd or 'NONE'}")

    print("\n" + "=" * 78)
    print("B. 검사기가 읽는 .json 중 동적 조립(오탐 후보)")
    print("=" * 78)
    for name, d in sorted(reads.items()):
        if d["dynamic"] or d["via_import_dynamic"]:
            print(f"\n[{name}] imports_local={d['imports_local']}")
            for x in d["dynamic"]:
                print(f"   dyn: {x}")
            for x in d["via_import_dynamic"]:
                print(f"   hop: {x}")

    print("\n" + "=" * 78)
    print("C. 판정: 라이브가 쓰는데 아무도 안 읽는 파일")
    print("=" * 78)
    unread = sorted(f for f in all_fetched if not reader_of.get(f))
    for f in unread:
        print(f"   UNREAD  {f}")
    print(f"\n   total fetched={len(all_fetched)}  unread={len(unread)}")

    out = ROOT / "scripts" / "_probes" / "_gate_file_wiring_census_out.json"
    out.write_text(json.dumps(
        {"fetches": {k: sorted(v) for k, v in fetches.items()},
         "reads": reads, "reader_of": reader_of, "unread": unread},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n   -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
