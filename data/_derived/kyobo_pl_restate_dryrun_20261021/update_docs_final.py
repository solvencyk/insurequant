"""Splice the prepared texts (docs_text/) into TODO_parser_ifrs17.md, docs/changelog_parser_ifrs17.md and the ticket answer.  Guards: every anchor must match exactly once.
Usage: update_docs_final.py [--apply]   (default = dry run: prints what would change)
"""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "kyobo_pl_restate_dryrun_20261021"
T = EV / "docs_text"
TODO = ROOT / "TODO_parser_ifrs17.md"
CHLOG = ROOT / "docs" / "changelog_parser_ifrs17.md"
TICKET = ROOT / "inbox" / "parser" / "20261021T1310Z__orchestrator__KR0073_2023.1Q-2026.1Q__csm_basis_vintage_fix.md"
sys.stdout.reconfigure(encoding="utf-8")
apply = "--apply" in sys.argv

res = json.loads((T / "results.json").read_text(encoding="utf-8"))


def fill(s):
    for k, v in res.items():
        s = s.replace("@@" + k + "@@", v)
    if "@@" in s:
        raise SystemExit("ABORT: unreplaced placeholder left in text")
    return s


def rd(p):
    t = p.read_text(encoding="utf-8")
    if "\r" in t:
        raise SystemExit(f"ABORT: {p} has CR characters")
    return t


# ---------------- TODO
todo = rd(TODO)
lines = todo.split("\n")
i13 = [i for i, l in enumerate(lines) if l.startswith("- **2026-10-21 13차:")]
i12 = [i for i, l in enumerate(lines) if l.startswith("- **2026-10-13 12차:")]
iopen = [i for i, l in enumerate(lines) if l.startswith("- [ ] **교보생명 KR0073 CSM 2023.1Q~2024.2Q 재작성 기준 적용(owner 결정")]
if len(i13) != 1 or len(i12) != 1 or len(iopen) != 1:
    raise SystemExit(f"ABORT: anchors i13={i13} i12={i12} iopen={iopen}")
i13, i12, iopen = i13[0], i12[0], iopen[0]
if not lines[iopen + 1].startswith("- [ ]"):
    raise SystemExit("ABORT: the old open item spans more than one line; check manually")
new_status = fill((T / "status_14.txt").read_text(encoding="utf-8")).rstrip("\n").split("\n") + (T / "status_13_short.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
new_open = (T / "open_item_kr0073.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
out = lines[:i13] + new_status + lines[i12:iopen] + new_open + lines[iopen + 1:]
for k, l in enumerate(out[:5]):
    if l.startswith("> 갱신 2026-10-21"):
        out[k] = l.replace("> 갱신 2026-10-21", "> 갱신 2026-10-22", 1)
new_todo = "\n".join(out)
print(f"TODO: old {len(lines)} lines -> new {len(out)} lines; status entries now: {sum(1 for l in out if l.startswith('- **2026-'))} (rotate with scripts/doc_rotate.py todo)")

# ---------------- changelog
ch = rd(CHLOG)
anchor = "## 2026-10-21 (13차: 교보생명 KR0073 CSM 워터폴 기준·시점 혼합 정정 — 티켓 20261021T1310Z)"
if ch.count(anchor) != 1:
    raise SystemExit("ABORT: changelog 13차 heading not found exactly once")
old_hdr = "> Last updated: 2026-10-21 · Stage 2/5 — parser (ifrs17 lane)"
if ch.count(old_hdr) != 1:
    raise SystemExit("ABORT: changelog 'Last updated' line not found exactly once")
new_ch = ch.replace(old_hdr, "> Last updated: 2026-10-22 · Stage 2/5 — parser (ifrs17 lane)").replace(anchor, fill((T / "changelog_14.txt").read_text(encoding="utf-8")).rstrip("\n") + "\n\n" + anchor)
print(f"changelog: +{len(new_ch) - len(ch)} chars")

# ---------------- ticket answer
tk = rd(TICKET)
marker = "## 답변 (recipient 작성 — 처리 후)"
if tk.count(marker) != 1:
    raise SystemExit("ABORT: ticket answer marker not found exactly once")
head = tk[:tk.index(marker)]
new_tk = head + fill((T / "ticket_answer_final.md").read_text(encoding="utf-8"))
if "status: answered" not in head:
    raise SystemExit("ABORT: ticket frontmatter is not status: answered")
print(f"ticket: answer replaced ({len(tk) - len(head)} -> {len(new_tk) - len(head)} chars); status stays answered")

if apply:
    for p, t in ((TODO, new_todo), (CHLOG, new_ch), (TICKET, new_tk)):
        p.write_text(t, encoding="utf-8", newline="\n")
    print("WRITTEN")
else:
    print("(dry run; nothing written)")
