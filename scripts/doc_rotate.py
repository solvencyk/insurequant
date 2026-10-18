# -*- coding: utf-8 -*-
"""Rotate the long-lived history docs so the active files stay short (CLAUDE.md section 2).

Two jobs, both byte-preserving (bytes in, bytes out; nothing is retyped) and both refuse to write if the
conservation check fails:

  changelog  docs/changelog_<stage>.md and docs/claude-changelog.md: entries ("## YYYY-MM-DD ...") older than the
             previous calendar month (relative to the newest entry of that file) move, untouched, to
             docs/changelog_archive/<stage>/<YYYY-MM>.md.  Undated "## " blocks (the old compressed archives) move to
             docs/changelog_archive/<stage>/undated.md.
  todo       TODO*.md "## Status": entries beyond the newest 3 move, untouched, to the top of
             docs/todo_archive_<name>.md under a dated heading.

Usage (dry run is the default; nothing is written without --apply):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/doc_rotate.py --check
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/doc_rotate.py changelog [--apply]
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/doc_rotate.py todo [--apply]

Run it once a month (changelog) and whenever a Status block grows past 3 entries (todo).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ARCHIVE_DIR = DOCS / "changelog_archive"
KEEP_STATUS = 3
MAX_STATUS_LINES = 5
MARKER = "> 보관:".encode("utf-8")
DATED = re.compile(rb"^## (\d{4})-(\d{2})-(\d{2})")


def stage_key(path: Path) -> str:
    name = path.name
    if name == "claude-changelog.md":
        return "cross_stage"
    return name[len("changelog_"):-len(".md")]


def changelog_files() -> list[Path]:
    files = sorted(DOCS.glob("changelog_*.md")) + [DOCS / "claude-changelog.md"]
    # changelog_parser.md is the frozen pre-split history (2026-06-13): nothing is appended, so nothing rotates.
    return [p for p in files if p.exists() and p.name != "changelog_parser.md"]


def split_blocks(data: bytes) -> tuple[list[bytes], list[list[bytes]]]:
    """Return (preamble lines, blocks); a block is the list of lines from one '## ' heading up to the next.

    Lines keep their trailing '\\r' (if any); '\\n' is the only separator, so b'\\n'.join(...) restores the bytes.
    Headings inside code fences do not start a block.
    """
    lines = data.split(b"\n")
    pre: list[bytes] = []
    blocks: list[list[bytes]] = []
    in_fence = False
    for ln in lines:
        s = ln.lstrip()
        if s.startswith(b"```") or s.startswith(b"~~~"):
            in_fence = not in_fence
        if not in_fence and ln.startswith(b"## "):
            blocks.append([ln])
        elif blocks:
            blocks[-1].append(ln)
        else:
            pre.append(ln)
    return pre, blocks


def block_month(block: list[bytes]) -> str | None:
    m = DATED.match(block[0])
    return f"{m.group(1).decode()}-{m.group(2).decode()}" if m else None


def prev_month(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def plan_changelog(path: Path) -> dict:
    data = path.read_bytes()
    pre, blocks = split_blocks(data)
    months = [block_month(b) for b in blocks]
    dated = [m for m in months if m]
    if not dated:
        return {"path": path, "data": data, "pre": pre, "blocks": blocks, "keep": blocks, "moves": {}, "newest": None, "meta": []}
    newest = max(dated)
    keep_from = prev_month(newest)
    keep, moves, meta = [], {}, []
    line_no = len(pre) + 1
    for b, m in zip(blocks, months):
        label = "undated" if m is None else (m if m < keep_from else None)
        if label is None:
            keep.append(b)
        else:
            moves.setdefault(label, []).append(b)
            meta.append({"file": f"docs/{path.name}", "heading": b[0].decode("utf-8").rstrip(),
                         "old_lines": [line_no, line_no + len(b) - 1],
                         "archive": f"docs/changelog_archive/{stage_key(path)}/{label}.md"})
        line_no += len(b)
    return {"path": path, "data": data, "pre": pre, "blocks": blocks, "keep": keep, "moves": moves,
            "newest": newest, "keep_from": keep_from, "meta": meta}


def archive_header(path: Path, key: str, label: str) -> bytes:
    title = "미분류(옛 압축 보관 절)" if label == "undated" else label
    return (f"# {path.name} 보관 — {title}\n\n"
            f"> `docs/{path.name}` 에서 무수정으로 옮긴 항목(최신이 위). 현행 항목은 원 파일에 있다. 관리: `scripts/doc_rotate.py changelog`.\n\n"
            ).encode("utf-8")


def with_marker(pre: list[bytes], path: Path, key: str) -> list[bytes]:
    if any(ln.startswith(MARKER) for ln in pre):
        return pre
    note = (f"> 보관: 이전 달 항목은 `docs/changelog_archive/{key}/` 에 월별로 무수정 보관한다"
            f"(관리 `scripts/doc_rotate.py changelog`, 현행 = 최신 항목 달과 그 전 달).").encode("utf-8")
    out = list(pre)
    while out and out[-1].strip() == b"":
        out.pop()
    return out + [b"", note, b""]


def apply_changelog(plan: dict, apply: bool) -> str:
    path: Path = plan["path"]
    key = stage_key(path)
    moves = plan["moves"]
    if not moves:
        return f"{path.name}: 옮길 항목 없음"
    n_moved = sum(len(v) for v in moves.values())
    new_pre = with_marker(plan["pre"], path, key)
    new_data = b"\n".join(new_pre + [ln for b in plan["keep"] for ln in b])
    writes: dict[Path, bytes] = {}
    for label, bl in moves.items():
        ap = ARCHIVE_DIR / key / f"{label}.md"
        existing = ap.read_bytes() if ap.exists() else None
        fresh = [b for b in bl if existing is None or b"\n".join(b).rstrip() not in existing]
        if not fresh:
            continue
        body = b"\n".join(ln for b in fresh for ln in b)
        if existing is None:
            writes[ap] = archive_header(path, key, label) + body
        else:  # a later run adds newer blocks right under the archive header
            cut = existing.find(b"\n## ") + 1
            writes[ap] = existing[:cut] + body + b"\n" + existing[cut:] if cut > 0 else existing + b"\n" + body
    # conservation: kept blocks + moved blocks == original blocks (as a multiset of byte strings)
    orig = sorted(b"\n".join(b) for b in plan["blocks"])
    now = sorted([b"\n".join(b) for b in plan["keep"]] + [b"\n".join(b) for v in moves.values() for b in v])
    if orig != now:
        raise SystemExit(f"{path.name}: conservation check failed (blocks differ)")
    # archive round trip: every moved block must be found verbatim in the archive bytes to be written
    for label, bl in moves.items():
        ap = ARCHIVE_DIR / key / f"{label}.md"
        blob = writes.get(ap)
        if blob is None:
            blob = ap.read_bytes() if ap.exists() else b""
        for b in bl:
            if b"\n".join(b).rstrip() not in blob:
                raise SystemExit(f"{path.name}: block missing from archive {ap.name}: {b[0][:60]!r}")
    if apply:
        for ap, blob in writes.items():
            ap.parent.mkdir(parents=True, exist_ok=True)
            ap.write_bytes(blob)
        path.write_bytes(new_data)
    return (f"{path.name}: 최신 {plan['newest']} · 현행 {plan['keep_from']} 이후 · "
            f"옮김 {n_moved}항목 -> {', '.join(f'{k}({len(v)})' for k, v in sorted(moves.items()))} · "
            f"{len(plan['data'])} -> {len(new_data)} bytes{'' if apply else ' (dry run)'}")


# ---------------------------------------------------------------- TODO status

def todo_files() -> list[Path]:
    return sorted(p for p in ROOT.glob("TODO*.md") if p.name != "TODO_parser.md")


def archive_path_for(todo: Path) -> Path:
    stem = todo.stem  # TODO / TODO_designer
    suffix = "root" if stem == "TODO" else stem[len("TODO_"):]
    return DOCS / f"todo_archive_{suffix}.md"


def status_span(lines: list[bytes]) -> tuple[int, int] | None:
    start = next((i for i, ln in enumerate(lines) if ln.startswith(b"## Status")), None)
    if start is None:
        return None
    end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith(b"## ")), len(lines))
    return start, end


def status_entries(lines: list[bytes], span: tuple[int, int]) -> list[tuple[int, int]]:
    """Entry = a '- **' line plus everything up to the next '- **' line (or the section end)."""
    s, e = span
    starts = [i for i in range(s + 1, e) if lines[i].startswith(b"- **")]
    return [(a, b) for a, b in zip(starts, starts[1:] + [e])]


def plan_todo(path: Path) -> dict | None:
    data = path.read_bytes()
    lines = data.split(b"\n")
    span = status_span(lines)
    if span is None:
        return None
    ents = status_entries(lines, span)
    return {"path": path, "data": data, "lines": lines, "span": span, "entries": ents, "excess": ents[KEEP_STATUS:]}


def apply_todo(plan: dict, today: str, apply: bool) -> str:
    path: Path = plan["path"]
    if not plan["excess"]:
        return f"{path.name}: Status {len(plan['entries'])}개 (정상)"
    lines = plan["lines"]
    first, last = plan["excess"][0][0], plan["excess"][-1][1]
    block = lines[first:last]
    while block and block[-1].strip() == b"":
        block = block[:-1]
    kept = lines[:first] + lines[last:]
    # keep one blank line between the Status block and the next section
    if first < len(lines) and kept[first - 1:first] and kept[first - 1].strip() != b"":
        kept.insert(first, b"")
    new_data = b"\n".join(kept)
    arch = archive_path_for(path)
    adata = arch.read_bytes() if arch.exists() else f"# TODO archive — `{path.name}` (Status 이력, 읽기 지연)\n\n".encode("utf-8")
    nl = b"\r\n" if b"\r\n" in adata[:400] else b"\n"
    heading = (f"## {today} 밀린 Status (최신 {KEEP_STATUS}개 밖, 문서 정리로 이동)").encode("utf-8")
    title_end = adata.find(nl + nl)
    title_end = (title_end + 2 * len(nl)) if title_end >= 0 else len(adata)
    moved = b"\n".join(block)
    new_adata = adata[:title_end] + heading + nl + nl + moved + nl + nl + adata[title_end:]
    if moved not in new_adata:
        raise SystemExit(f"{path.name}: moved block missing from the archive bytes")
    # conservation: the non-empty lines of (kept + moved) equal the non-empty lines of the original
    a = sorted(ln for ln in lines if ln.strip())
    b = sorted(ln for ln in kept + block if ln.strip())
    if a != b:
        raise SystemExit(f"{path.name}: conservation check failed (lines differ)")
    if apply:
        arch.write_bytes(new_adata)
        path.write_bytes(new_data)
    return (f"{path.name}: Status {len(plan['entries'])}개 -> {KEEP_STATUS}개, {len(plan['excess'])}개를 "
            f"{arch.name} 맨 위로{'' if apply else ' (dry run)'}")


# ---------------------------------------------------------------- check

def check() -> int:
    bad = 0
    for p in todo_files():
        plan = plan_todo(p)
        if plan is None:
            print(f"[todo] {p.name}: '## Status' 절 없음")
            continue
        ents, lines = plan["entries"], plan["lines"]
        long_entries = [(a, sum(1 for ln in lines[a:b] if ln.strip())) for a, b in ents[:KEEP_STATUS]]
        over = [f"L{a + 1}({n}줄)" for a, n in long_entries if n > MAX_STATUS_LINES]
        msg = []
        if len(ents) > KEEP_STATUS:
            msg.append(f"Status {len(ents)}개 (>{KEEP_STATUS})")
        if over:
            msg.append(f"{MAX_STATUS_LINES}줄 초과 " + ", ".join(over))
        done = [i + 1 for i, ln in enumerate(lines) if re.match(rb"- \[x\]", ln, re.I)]
        if done:
            msg.append(f"완료([x]) 줄 {len(done)}개 L{done[0]}...")
        longest = max((len(ln) for ln in lines), default=0)
        if longest > 1200:
            msg.append(f"한 줄 {longest}자")
        print(f"[todo] {p.name}: " + ("; ".join(msg) if msg else "OK"))
        bad += bool(msg)
    for p in changelog_files():
        plan = plan_changelog(p)
        n = sum(len(v) for v in plan["moves"].values())
        print(f"[changelog] {p.name}: {'옮길 ' + str(n) + '항목 (현행 ' + plan['keep_from'] + ' 이후)' if n else 'OK'} · {len(plan['data']) // 1024} KB")
        bad += bool(n)
    return 1 if bad else 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job", nargs="?", choices=["changelog", "todo"])
    ap.add_argument("--apply", action="store_true", help="write the files (default: dry run)")
    ap.add_argument("--check", action="store_true", help="report what needs rotating; exit 1 if anything does")
    ap.add_argument("--today", default="", help="YYYY-MM-DD used in the archive heading (todo job)")
    ap.add_argument("--manifest", default="", help="changelog job: write a JSON list of every moved entry (old line range -> archive file)")
    args = ap.parse_args()
    if args.check:
        return check()
    if not args.job:
        ap.error("job or --check required")
    if args.job == "changelog":
        manifest: list[dict] = []
        for p in changelog_files():
            plan = plan_changelog(p)
            manifest += plan["meta"]
            print(apply_changelog(plan, args.apply))
        if args.manifest:
            Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"manifest: {len(manifest)} entries -> {args.manifest}")
    else:
        if not args.today:
            ap.error("--today YYYY-MM-DD is required for the todo job")
        for p in todo_files():
            plan = plan_todo(p)
            if plan:
                print(apply_todo(plan, args.today, args.apply))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
