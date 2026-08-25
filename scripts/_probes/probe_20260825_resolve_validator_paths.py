# -*- coding: utf-8 -*-
"""검사기가 **실제로 읽는** 파일 경로를 AST 로 해석한다 (동적 조립 포함).

문자열 리터럴만 세는 census 는 `VIZ / 'csm_waterfall.json'` 같은 조립을 놓쳐 **오탐**을 낸다.
여기서는 모듈 상단의 `ROOT = Path(...)` / `VIZ = ROOT / 'data' / ...` 같은 상수를 먼저 풀고,
`Name / 'a' / 'b.json'` 체인을 저장소 상대경로로 환원한다.

또 **읽기와 쓰기를 구분**한다 — 산출물만 쓰는 것은 그 파일을 검사하는 것이 아니다.
(`json.load(open(p))` / `p.read_text()` / `json.loads(p.read_text())` = 읽기,
 `p.write_text(...)` / `json.dump(..., open(p,'w'))` = 쓰기)

사용: python scripts/_probes/probe_20260825_resolve_validator_paths.py
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]


def _const_str(n: ast.AST) -> str | None:
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


class Resolver:
    """모듈 상단 상수(Path 조립)를 풀어서 저장소 상대경로 문자열로 만든다."""

    def __init__(self, tree: ast.Module):
        self.consts: dict[str, str] = {}
        # 여러 번 돌려 서로를 참조하는 상수(ROOT -> VIZ -> ...)를 수렴시킨다
        for _ in range(4):
            for node in tree.body:
                if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                    continue
                t = node.targets[0]
                if not isinstance(t, ast.Name):
                    continue
                v = self.path_of(node.value)
                if v is not None:
                    self.consts[t.id] = v

    def path_of(self, n: ast.AST) -> str | None:
        """노드를 저장소 상대 posix 경로로. 못 풀면 None."""
        # Path(__file__).resolve().parents[N]  -> 저장소 루트면 ""
        if isinstance(n, ast.Subscript):
            src = ast.unparse(n)
            if "parents[" in src and "__file__" in src:
                return ""  # scripts/x.py 의 parents[1] = ROOT
        if isinstance(n, ast.Name):
            return self.consts.get(n.id)
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            return n.value.replace("\\", "/").lstrip("./")
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            left = self.path_of(n.left)
            right = _const_str(n.right)
            if left is None or right is None:
                return None
            return str(PurePosixPath(left) / right) if left else right
        if isinstance(n, ast.Call):
            # Path("a/b.json") / str(x)
            f = ast.unparse(n.func)
            if f in ("Path", "pathlib.Path") and n.args:
                return self.path_of(n.args[0])
        return None


READ_METHODS = {"read_text", "read_bytes", "open"}
WRITE_METHODS = {"write_text", "write_bytes"}


class Usage(ast.NodeVisitor):
    def __init__(self, r: Resolver):
        self.r = r
        self.reads: set[str] = set()
        self.writes: set[str] = set()

    def visit_Call(self, node: ast.Call):
        f = node.func
        # p.read_text() / p.write_text() / p.open()
        if isinstance(f, ast.Attribute):
            p = self.r.path_of(f.value)
            if p and p.endswith(".json"):
                if f.attr in READ_METHODS:
                    mode = _const_str(node.args[0]) if (f.attr == "open" and node.args) else "r"
                    (self.writes if mode and "w" in mode else self.reads).add(p)
                elif f.attr in WRITE_METHODS:
                    self.writes.add(p)
        # json.load(open(p)) / open(p) / open(p, "w")
        if isinstance(f, ast.Name) and f.id == "open" and node.args:
            p = self.r.path_of(node.args[0])
            if p and p.endswith(".json"):
                mode = _const_str(node.args[1]) if len(node.args) > 1 else "r"
                for kw in node.keywords:
                    if kw.arg == "mode":
                        mode = _const_str(kw.value) or mode
                (self.writes if mode and ("w" in mode or "a" in mode) else self.reads).add(p)
        self.generic_visit(node)


def analyze(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    r = Resolver(tree)
    u = Usage(r)
    u.visit(tree)
    # 함수 인자로 넘어가는 경로(예: load_json(VIZ / "x.json"))도 읽기로 본다
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and \
                n.func.id.startswith(("load", "read", "_load", "_read")):
            for a in n.args:
                p = r.path_of(a)
                if p and p.endswith(".json"):
                    u.reads.add(p)
    return {"reads": sorted(u.reads), "writes": sorted(u.writes),
            "consts": {k: v for k, v in r.consts.items() if v is not None}}


def main() -> int:
    targets = sorted((ROOT / "scripts").glob("validate_*.py"))
    targets.append(ROOT / "scripts" / "prepush_check.py")
    res: dict[str, dict] = {}
    for p in targets:
        if p.exists():
            try:
                res[p.stem] = analyze(p)
            except SyntaxError as e:
                res[p.stem] = {"error": str(e)}

    reader_of: dict[str, list[str]] = {}
    writer_of: dict[str, list[str]] = {}
    for name, d in res.items():
        for f in d.get("reads", []):
            reader_of.setdefault(f, []).append(name)
        for f in d.get("writes", []):
            writer_of.setdefault(f, []).append(name)

    for name, d in sorted(res.items()):
        print(f"\n[{name}]")
        print("   READS :", d.get("reads") or "-")
        print("   WRITES:", d.get("writes") or "-")

    live = ["CSM_waterfall.json", "NB_CSM_multiple.json", "kics_disclosure.json",
            "kics_forward_capital.json", "kics_rate_sensitivity.json",
            "kics_tier1_utilization.json", "kics_tier2_utilization.json",
            "IFRS17_BS.json", "PL_breakdown.json", "dividend.json",
            "data/dart/viz/csm_amort_schedule.json",
            "data/dart/viz/csm_waterfall.json",
            "data/dart/viz/csm_waterfall_history.json",
            "data/dart/viz/insurance_pl_breakdown.json",
            "data/dart/viz/sensitivity_heatmap.json",
            "data/ir/nb_csm_ratio.json"]
    print("\n" + "=" * 72)
    print("라이브 fetch 파일 × 실제 READ 하는 검사기 (동적경로 해석 후)")
    print("=" * 72)
    for f in live:
        rd = sorted(set(reader_of.get(f, [])))
        wr = sorted(set(writer_of.get(f, [])))
        flag = "UNREAD" if not rd else "ok"
        print(f"  {flag:7s} {f:46s} R={rd or '-'} W={wr or '-'}")

    out = ROOT / "scripts" / "_probes" / "_resolve_validator_paths_out.json"
    out.write_text(json.dumps({"per_script": res, "reader_of": reader_of,
                               "writer_of": writer_of}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
