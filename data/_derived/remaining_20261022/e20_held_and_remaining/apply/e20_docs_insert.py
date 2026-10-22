#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 docs step (documentation only, no master is touched): insert the 19th-round text into
 - TODO_parser_ifrs17.md        (Status item above the 18th-round item + rewrite of the 'other companies, same type' open item)
 - docs/changelog_parser_ifrs17.md (19th-round block above the 18th-round block)
 - inbox/parser/20261022T1800Z__...latest_comparative_held_and_remaining.md (STEP 1 answer under '## 답변')
The three files are BOM-free with ONE newline convention each (measured with s21_eol.py: plain LF); this script detects it
per file, keeps it byte-exact and is idempotent (refuses to run twice).  Originals are copied to <scratchpad>/e20_backup/docs_pre/ first.
Usage: python e20_docs_insert.py --check | --apply     (stdin /dev/null)
"""
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
SP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad")
TODO = ROOT / "TODO_parser_ifrs17.md"
CHLOG = ROOT / "docs" / "changelog_parser_ifrs17.md"
TICKET = ROOT / "inbox" / "parser" / "20261022T1800Z__orchestrator__MULTI_2023.1Q-2025.2Q__latest_comparative_held_and_remaining.md"
BACKUP = SP / "e20_backup" / "docs_pre"

A18_TODO = "- **2026-10-22 18차:"
OPEN_START = "- [ ] **다른 회사 같은 유형(최신 비교열 미반영)"
A18_LOG = "## 2026-10-22 (18차:"
PLACEHOLDER = "(처리 전)"
ANSWER_HEAD = "## 답변 (recipient 작성 — 처리 후)"

NEW_OPEN = (
    "- [ ] **다른 회사 같은 유형(최신 비교열 미반영) — 닫히는 버킷은 전부 적재 완료(18차 19 · 19차 21), 남은 것 = 안 닫히는·확인불가 55버킷"
    "(owner 미결정; 원인·읽기 수정안은 티켓 `20261022T1800Z` 단계 2)** — 측정 `data/_derived/remaining_20261022/d_census/`"
    "(`d_census_table.csv` 51 · `d_census_addl.csv` 53) 대비 남은 것: A51 STAY 22(블록 불닫힘·미확인) + 부속 33(FY 형제 20 · CSM-only 10 · OCI만 3; "
    "CSM-only 는 PL4 읽기 없이 CSM 만 바꾸면 `CSM_AMORT_IDENTITY` 가 깨진다)이고, 적재할 게 없는 A51 9는 그대로다"
    "(`data/_derived/remaining_20261022/e20_held_and_remaining/apply/s19_scope_check.txt`). "
    "같은 뿌리의 단일분기 어긋남 4곳(메리츠 2023.1Q~2Q · 한화생명 2023.1Q~2Q · KB라이프 2023.1Q~3Q · 롯데손보 2024.1Q~3Q)은 CSM·PL 을 같은 판으로 함께 갱신하면 "
    "닫히는 것을 원문으로 확인(`c_singleq/` 의 `per_bucket`); 롯데·ABL·KB라이프는 두 번 재작성돼 연속성 RED 3 이 남는다. "
    "19차가 남긴 공란: 푸본현대 2024.4Q 단일분기 8칸(2024.4Q 누계를 채택하면 복원) · 2025.3Q 26칸(FY2026 3분기 보고서 제출 뒤 재계산) · "
    "KDB생명 2024.4Q 항목 17·18(표시 분리, 마스터에 기타영업손익 칸이 없다)."
)


def read_uniform(p):
    """Return (text with '\\n' newlines, newline string of the file). Refuses BOM / mixed newlines."""
    b = p.read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):
        raise SystemExit(f"ABORT: BOM in {p}")
    t = b.decode("utf-8")
    n_crlf, n_lf, n_cr = t.count("\r\n"), t.count("\n"), t.count("\r")
    if n_crlf == 0 and n_cr == 0:
        return t, "\n"
    if n_crlf == n_lf == n_cr:
        return t.replace("\r\n", "\n"), "\r\n"
    raise SystemExit(f"ABORT: {p} has mixed newlines (CRLF {n_crlf}, LF {n_lf}, CR {n_cr})")


def draft(name):
    t = (SP / name).read_text(encoding="utf-8")
    if "\r" in t:
        raise SystemExit(f"ABORT: draft {name} has CR")
    return t.rstrip("\n")


def plan():
    out = {}
    # TODO
    t, nl = read_uniform(TODO)
    if "- **2026-10-22 19차:" in t:
        raise SystemExit("ABORT: TODO already has the 19th-round item")
    if t.count("\n" + A18_TODO) != 1:
        raise SystemExit(f"ABORT: anchor '{A18_TODO}' count {t.count(chr(10) + A18_TODO)}")
    status = draft("todo_status_19.md")
    n_lines = len(status.split("\n"))
    if n_lines > 5:
        raise SystemExit(f"ABORT: Status item has {n_lines} lines (max 5)")
    t2 = t.replace("\n" + A18_TODO, "\n" + status + "\n" + A18_TODO, 1)
    if t2.count("\n" + OPEN_START) != 1:
        raise SystemExit("ABORT: open item anchor not unique")
    i = t2.find("\n" + OPEN_START) + 1
    j = t2.find("\n", i)
    old_line = t2[i:j]
    t2 = t2[:i] + NEW_OPEN + t2[j:]
    out[TODO] = (t, t2, nl, f"status lines {n_lines}; open item {len(old_line)} -> {len(NEW_OPEN)} chars")
    # changelog
    c, nl = read_uniform(CHLOG)
    if "## 2026-10-22 (19차" in c:
        raise SystemExit("ABORT: changelog already has the 19th-round block")
    if c.count("\n" + A18_LOG) != 1:
        raise SystemExit("ABORT: changelog anchor not unique")
    entry = draft("changelog_entry_19.md")
    c2 = c.replace("\n" + A18_LOG, "\n" + entry + "\n\n" + A18_LOG, 1)
    out[CHLOG] = (c, c2, nl, f"entry {len(entry.splitlines())} lines")
    # ticket
    k, nl = read_uniform(TICKET)
    if k.count(ANSWER_HEAD + "\n\n" + PLACEHOLDER) != 1:
        raise SystemExit("ABORT: ticket answer placeholder not found exactly once (someone wrote the answer already?)")
    if "status: open" not in k.split("\n---\n")[0]:
        raise SystemExit("ABORT: ticket status is not open")
    ans = draft("ticket_answer_step1.md")
    k2 = k.replace(ANSWER_HEAD + "\n\n" + PLACEHOLDER, ANSWER_HEAD + "\n\n" + ans, 1)
    out[TICKET] = (k, k2, nl, f"answer {len(ans.splitlines())} lines")
    return out


def enc(text, nl):
    return (text if nl == "\n" else text.replace("\n", nl)).encode("utf-8")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    P = plan()
    for p, (old, new, nl, note) in P.items():
        print(f"{p.relative_to(ROOT)}: {len(enc(old, nl))} -> {len(enc(new, nl))} bytes; newline {'CRLF' if nl == chr(13) + chr(10) else 'LF'}; {note}")
    if mode != "--apply":
        print("(--check only; nothing written)")
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    for p, (old, new, nl, _n) in P.items():
        b = BACKUP / p.name
        if not b.exists():
            b.write_bytes(enc(old, nl))
        if p.read_bytes() != enc(old, nl):
            raise SystemExit(f"ABORT: {p} changed between read and write")
        p.write_bytes(enc(new, nl))
    print("written; originals in", BACKUP)


if __name__ == "__main__":
    main()
