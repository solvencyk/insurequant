import json
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")

prov = json.load(open("data/_derived/pl_oci_item32_provenance.json", encoding="utf-8"))
print(f"company-quarters with non-empty item32 provenance: {len(prov)}")

aid_counter = Counter()
aid_by_company = defaultdict(set)
companies = set()
for entry in prov:
    companies.add(entry["원수사명"])
    for c in entry["구성"]:
        aid = c["account_id"] or "(untagged)"
        aid_counter[aid] += 1
        aid_by_company[aid].add(entry["원수사명"])

print(f"distinct companies contributing to item32: {len(companies)}")
print(f"distinct account_id (incl. untagged marker): {len(aid_counter)}")
print()
print("account_id -> occurrence count, company count, sample companies:")
for aid, n in aid_counter.most_common():
    comps = sorted(aid_by_company[aid])
    sample = ", ".join(comps[:5]) + (f" +{len(comps)-5} more" if len(comps) > 5 else "")
    print(f"  [{n:>3}x, {len(comps):>2} companies] {aid}")
    print(f"      {sample}")
