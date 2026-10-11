from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/scripts/viz_build_persistency_lossratio_panels.py")
t = p.read_bytes().decode("utf-8")
crlf = "\r\n" in t
t = t.replace("\r\n", "\n")
old = "    data/loss_ratio/master_loss_ratio.json   -> data/loss_ratio/panel_loss_ratio.json\n"
new = old + "    data/loss_ratio/claims_ae_ratio.json     -> same panel, top-level `ae` block (actual-vs-expected claims ratio)\n"
assert old in t
t = t.replace(old, new, 1)
p.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
print("crlf", crlf)
