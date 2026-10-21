"""Splice the prepared texts (docs_text/) into TODO_parser_ifrs17.md, docs/changelog_parser_ifrs17.md and the validation ticket answer.  Every anchor must match exactly once.
Usage: update_docs_seam.py [--apply]   (default = dry run)
Line endings: these files are LF in the working tree (git ls-files --eol: w/lf); read and written as bytes so nothing else changes.
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
res = json.loads((T / "results.json").read_text(encoding="utf-8"))


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


def once(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit(f"ABORT: anchor not found exactly once ({text.count(old)}) in {label}: {old[:70]!r}")
    return text.replace(old, new)


# ---------------- TODO
todo = rd(TODO)
head14 = "- **2026-10-22 14차: 교보생명 KR0073 PL 최신 비교열 갱신"
new_todo = once(todo, head14, fill((T / "status_15.txt").read_text(encoding="utf-8")).rstrip("\n") + "\n" + head14, "TODO 14차 head")
new_todo = once(new_todo,
                "**tax22_src 282P/0F→278P/4F**(2023.3Q~2024.2Q; 룰이 원 공시 법인세와 대조 — validation 이 이번 라운드에 후속 공시 전기 열 인정으로 수정)",
                "**tax22_src 282P/0F→278P/4F**(2023.3Q~2024.2Q; 룰이 원 공시 법인세와 대조 → validation `9f69ffcf` 가 룰을 고쳐 282P/0F 로 복귀)", "TODO 14차 gates")
new_todo = once(new_todo, "; 2023.3Q 당분기는 1H(정정 전)·3Q 이후(정정 후) 비교열 이음매로 일회성 따라잡기가 몰린다.", "; 2023.3Q 당분기 이음매는 15차에서 28칸을 비웠다.", "TODO 14차 carry-over")
old_rest = [l for l in new_todo.split("\n") if l.startswith("  남은 것: publishing = xlsx `손익분해PL`(KR0073 152셀)")]
if len(old_rest) != 1:
    raise SystemExit("ABORT: 14차 '남은 것' line not found exactly once")
new_todo = new_todo.replace(old_rest[0], "  처리됨: publishing `eea3f61c`(xlsx 두 시트 · NB · 비교/콤보 패널) · `011e0bfc`(public_exports) / validation `9f69ffcf`(`tax22_src` 룰 · 골든 · 지문). 커밋은 메인이 했다.")
old_open = [l for l in new_todo.split("\n") if l.startswith("- [ ] **교보생명 KR0073 PL·CSM 최신 비교열 후속(14차 이월)**")]
if len(old_open) != 1:
    raise SystemExit("ABORT: open item not found exactly once")
o = old_open[0]
o = once(o, " ③ `tax22_src` 4건 FAIL 은 validation 이 룰을 후속 공시 전기 열 인정으로 수정하면 사라진다 ④ publishing/validation 몫은 14차 항목.",
         " ③ **결정 대기(15차)**: 2023.3Q PL 항목 4·5 값_당분기(252,287 · 34,800; 3e53aef8 전에는 109,828 · 34,711)도 비울지 — `data/_gold/user_pl_cells.json` `null_dangi.cells` 에 `[\"KR0073\",\"2023.3Q\",4]`·`[…,5]` 를 더하고 `data/_derived/kyobo_seam_blank_20261022/apply_seam_blank.py` 를 다시 돌리면 된다(합집합 적재, 멱등).",
         "open item tail")
new_todo = new_todo.replace(old_open[0], o)
print(f"TODO: {len(todo.splitlines())} -> {len(new_todo.splitlines())} lines; status entries: {sum(1 for l in new_todo.splitlines() if l.startswith('- **2026-'))}")

# ---------------- changelog
ch = rd(CHLOG)
anchor = "## 2026-10-22 (14차: 교보생명 KR0073 PL 최신 비교열 갱신 + CSM 재작성 기준(R) 적재 — 티켓 20261021T1310Z E1~E4 완결)"
new_ch = once(ch, anchor, fill((T / "changelog_15.txt").read_text(encoding="utf-8")).rstrip("\n") + "\n\n" + anchor, "changelog 14차 heading")
print(f"changelog: +{len(new_ch) - len(ch)} chars")

# ---------------- validation ticket
tk = rd(TICKET)
marker = "## 답변 (recipient 작성 — 처리 후)"
if tk.count(marker) != 1:
    raise SystemExit("ABORT: ticket answer marker not found exactly once")
head = tk[:tk.index(marker)]
head2 = once(head, "\nstatus: open\n", "\nstatus: answered\n", "ticket frontmatter")
new_tk = head2 + fill((T / "ticket_answer_seam.md").read_text(encoding="utf-8"))
print(f"ticket: status open -> answered; answer {len(tk) - len(head)} -> {len(new_tk) - len(head2)} chars")

if apply:
    for p, t in ((TODO, new_todo), (CHLOG, new_ch), (TICKET, new_tk)):
        p.write_bytes(t.encode("utf-8"))
    print("WRITTEN")
else:
    print("(dry run; nothing written)")
