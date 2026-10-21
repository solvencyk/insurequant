"""Replace the first-step 15th entries (28 cells blanked) by the final text (printed 3-month values) in TODO_parser_ifrs17.md, docs/changelog_parser_ifrs17.md and the validation ticket answer.
Every anchor must match exactly once; the files are LF (read/written as bytes).  Usage: update_docs_seam2.py [--apply]
"""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "kyobo_seam_blank_20261022"
T = EV / "docs_text"
TODO = ROOT / "TODO_parser_ifrs17.md"
CHLOG = ROOT / "docs" / "changelog_parser_ifrs17.md"
TICKET = ROOT / "inbox" / "parser" / "20261021T1655Z__validation__KR0073_2023.3Q__single_quarter_vintage_seam.md"
sys.stdout.reconfigure(encoding="utf-8")
apply = "--apply" in sys.argv
res = json.loads((T / "results2.json").read_text(encoding="utf-8"))


def fill(s):
    for k, v in res.items():
        s = s.replace("@@" + k + "@@", v)
    if "@@" in s:
        raise SystemExit("ABORT: unreplaced placeholder left in text")
    return s


def rd(p):
    b = p.read_bytes()
    if b"\r" in b:
        raise SystemExit(f"ABORT: {p} contains CR bytes (not an LF file)")
    return b.decode("utf-8")


# ---------------- TODO
todo = rd(TODO)
lines = todo.split("\n")
i15 = [i for i, l in enumerate(lines) if l.startswith("- **2026-10-22 15차:")]
i14 = [i for i, l in enumerate(lines) if l.startswith("- **2026-10-22 14차:")]
if len(i15) != 1 or len(i14) != 1 or i15[0] >= i14[0]:
    raise SystemExit(f"ABORT: Status anchors i15={i15} i14={i14}")
new_entry = fill((T / "status_15b.txt").read_text(encoding="utf-8")).rstrip("\n").split("\n")
lines = lines[:i15[0]] + new_entry + lines[i14[0]:]
new_todo = "\n".join(lines)
old = "; 2023.3Q 당분기 이음매는 15차에서 28칸을 비웠다."
if new_todo.count(old) != 1:
    raise SystemExit("ABORT: 14차 carry-over clause not found exactly once")
new_todo = new_todo.replace(old, "; 2023.3Q 당분기 이음매는 15차에서 공시 3개월 열 인쇄값으로 교체했다.")
oi = [i for i, l in enumerate(new_todo.split("\n")) if l.startswith("- [ ] **교보생명 KR0073 PL·CSM 최신 비교열 후속(14차 이월)**")]
if len(oi) != 1:
    raise SystemExit("ABORT: open item not found exactly once")
ol = new_todo.split("\n")
line = ol[oi[0]]
a = line.index(" ③ **결정 대기(15차)**")
b = line.index("(합집합 적재, 멱등).", a) + len("(합집합 적재, 멱등).")
ol[oi[0]] = line[:a] + "." + line[b:]
new_todo = "\n".join(ol)
print(f"TODO: status entries {sum(1 for l in new_todo.splitlines() if l.startswith('- **2026-'))}; open item rewritten (③ removed)")

# ---------------- changelog
ch = rd(CHLOG)
cl = ch.split("\n")
c15 = [i for i, l in enumerate(cl) if l.startswith("## 2026-10-22 (15차:")]
c14 = [i for i, l in enumerate(cl) if l.startswith("## 2026-10-22 (14차:")]
if len(c15) != 1 or len(c14) != 1 or c15[0] >= c14[0]:
    raise SystemExit(f"ABORT: changelog anchors c15={c15} c14={c14}")
new_blk = fill((T / "changelog_15b.txt").read_text(encoding="utf-8")).rstrip("\n").split("\n") + [""]
new_ch = "\n".join(cl[:c15[0]] + new_blk + cl[c14[0]:])
print(f"changelog: {len(ch)} -> {len(new_ch)} chars")

# ---------------- validation ticket answer
tk = rd(TICKET)
marker = "## 답변 (recipient 작성 — 처리 후)"
if tk.count(marker) != 1:
    raise SystemExit("ABORT: ticket answer marker not found exactly once")
head = tk[:tk.index(marker)]
if "\nstatus: answered\n" not in head:
    raise SystemExit("ABORT: ticket frontmatter is not status: answered")
new_tk = head + fill((T / "ticket_answer_seam2.md").read_text(encoding="utf-8"))
print(f"ticket: answer {len(tk) - len(head)} -> {len(new_tk) - len(head)} chars; status stays answered")

if apply:
    for p, t in ((TODO, new_todo), (CHLOG, new_ch), (TICKET, new_tk)):
        p.write_bytes(t.encode("utf-8"))
    print("WRITTEN")
else:
    print("(dry run; nothing written)")
