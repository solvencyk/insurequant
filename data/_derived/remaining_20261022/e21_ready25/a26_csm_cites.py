"""a26_csm_cites: print ready_csm_cells.csv (READY CSM cells) with their cite column (READ-ONLY)"""
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_csm_cells.csv"
with open(p, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        print(r["code"], r["quarter"], "i", r["item"], "old", r["old"], "new", r["new"], "|", r["later_filing"], r["source_table"], "|", r["cite(label|line|text)"], "|", r["how"][:60])
