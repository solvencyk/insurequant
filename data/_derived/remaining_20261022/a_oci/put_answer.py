from pathlib import Path
t = Path("C:/Users/sangwook.cho/Desktop/insurequant/inbox/parser/20261021T1556Z__orchestrator__KR0073_2024.4Q-2025.2Q__oci_latest_comparative.md")
a = Path(__file__).resolve().parent / "answer_text.md"
s = t.read_text(encoding="utf-8")
assert s.count("status: open") == 1 and s.rstrip().endswith("## 답변 (recipient 작성 — 처리 후)")
s = s.replace("status: open", "status: answered")
s = s.rstrip("\n") + "\n" + a.read_text(encoding="utf-8")
t.write_text(s, encoding="utf-8", newline="\n")
print("ok", len(s))
