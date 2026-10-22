import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
for r in csv.DictReader(open(M + "csm_vector_sources.csv", encoding="utf-8-sig")):
    its = r["item_cites"].split(" ; ")
    i1 = next((x for x in its if x.startswith("item1:")), ""); i6 = next((x for x in its if x.startswith("item6:")), "")
    print(r["code"], r["quarter"], r["later_filing"], r["table"], "|", i1[:70], "|", i6[:70])
