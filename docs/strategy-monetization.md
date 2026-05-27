# Insurequant Monetization Strategy

Last updated: 2026-05-27

## Context

insurequant is a data pipeline and analytics platform covering Korean insurance
financial metrics (K-ICS, IFRS17). The platform has demonstrated working
product (public K-ICS + IFRS17 dashboards) and established technical moat in
parsing non-standard disclosures. Next step: converting this into recurring
revenue.

Target customer: reinsurance sales / underwriting teams (Korean and global),
investment analysts, and actuarial advisory firms who need structured,
comparable insurer financial data.

---

## Three Paths Assessed

### Path 1: Internal (in-company) commercialization — REJECTED

- IP ownership transfers to employer
- Revenue goes to company; personal upside is limited to possible salary bump
- Decision-making follows org logic, not product logic
- Prior data point: FSA award brought no compensation change — org reward
  structure is already revealed
- Conclusion: disclosing existence to employer for conflict-of-interest
  compliance is appropriate, but handing over IP and economics is not.

### Path 2: Solo launch vs. salary uplift — comparison

Conservative solo ARR trajectory (70%+ margin business):

| Year | Est. ARR | Net (70% margin) |
|------|----------|-----------------|
| Y1   | KRW 50M–100M | KRW 35M–70M |
| Y2   | KRW 200M–300M | KRW 140M–210M |
| Y3   | KRW 500M–800M | KRW 350M–560M |

Realistic salary uplift from internal leverage (FSA + K-ICS platform +
team transfer): ~KRW 5M–15M/year incremental.

Comparison is asymmetric. The personal variable is timing risk given life
circumstances (expecting first child). Manage by keeping infra costs near
zero and targeting first paying customer before Y1 ends.

### Path 3: Global pivot (Solvency II / IFRS17 multi-jurisdiction) — PREFERRED MEDIUM-TERM

This is the highest-value path for three compounding reasons:

**1. Conflict-of-interest problem disappears.**
Korean Re transacts reinsurance with Korean primary insurers.
Selling structured solvency data on UK/German/Japanese insurers has no
overlap with that business. Standard moonlighting clauses prohibit
"competing with the company's business" — a global financial data service
for EU/Japan markets does not compete. (Verify exact wording of employment
contract regardless.)

**2. Addressable market is 50x larger.**

| Dimension | Korea (K-ICS) | EU (Solvency II) |
|-----------|--------------|-----------------|
| Primary insurers | ~60 | ~3,000+ |
| Data format | PDF, fragmented | XBRL QRT (more structured) |
| Existing affordable comparison platform | None | None (gap confirmed) |
| Customer willingness to pay | Unknown | Strong data subscription culture |
| Language barrier | None | English/German/French (manageable) |

Solvency II has been live since 2016 — data is mature, but no affordable
dashboard-style comparison product exists. Bloomberg/Fitch Connect charge
institutional rates (KRW tens of millions/year). The sub-KRW 5M/year SaaS
tier is empty.

**3. Korea is the technical proof-of-concept; EU is the scale play.**

Japan IFRS17 went live 2025. Data is just starting to accumulate — early
mover advantage still available. Japan FSA disclosure structure is well-organized.

EIOPA (European Insurance and Occupational Pensions Authority) publishes
QRT (Quantitative Reporting Templates) under Solvency II — these are more
machine-readable than Korean PDF disclosures, meaning the extraction
pipeline cost is lower per insurer once the schema is mapped.

---

## Recommended Sequencing

**2026–2027 (near-term): Korea B2B reference customers**
- Close 1–2 paying B2B customers using existing Korean K-ICS + IFRS17 platform.
- Position as "public-data-only" service — zero proprietary data, zero
  conflict. Document this clearly.
- Disclose existence to employer proactively; frame as public-data service,
  not competing business.
- Keep infra cost near zero (current static site + pipeline approach).
- Target: reinsurance brokers (Aon/Guy Carpenter Korea desks), actuarial
  advisory (Milliman, Willis Towers Watson Korea), or foreign reinsurers'
  Korean offices (Munich Re, Swiss Re, Scor Korea).

**2028+ (medium-term): EU Solvency II pivot**
- Use global reinsurance market exposure (Korean Re) to validate which EU
  insurer profiles global reinsurers actually need.
- Munich Re / Swiss Re / Scor need EU primary insurer profiling today;
  current tools are either expensive or manual.
- Korea platform proves the pipeline architecture; EU is the TAM expansion.
- Japan can run in parallel once IFRS17 data accumulates (2026–2027 filings).

---

## Key Metrics That Drive Reinsurance Customer Value

Reinsurance sales teams need to identify which primary insurers have latent
demand for specific reinsurance structures. The platform's value is in
mapping insurer financial signals to likely reinsurance solutions:

| Financial signal | Reinsurance solution implication |
|------------------|----------------------------------|
| High lapse risk capital (해지위험액) | Mass-lapse reinsurance need |
| High mortality/disability risk capital | YRT demand |
| High market risk / duration gap | Coinsurance / ALM reinsurance |
| High P&C catastrophe risk capital | Cat XL demand |
| Low cession rate by line | Headroom to expand reinsurance |
| Declining persistency (13th/25th month) | Rising sensitivity to lapse assumptions |
| Large pre/post-transition K-ICS gap | Medium-term capital pressure → reinsurance demand |
| High onerous contract ratio | Quota share reinsurance need |
| Ceded CSM negative | Existing reinsurance structure losing economically |

This mapping is the core intellectual property of the platform — not just
the data pipeline, but the translation from raw disclosure numbers to
actionable reinsurance intelligence.

---

## Data Gaps to Address (Prioritized)

### Already collected, needs UX surface
- K-ICS risk capital sub-components with reinsurance solution mapping view
- Pre/post-transition K-ICS ratio gap column
- Insurance service result vs. insurance finance result split (IFRS17)
- Ceded CSM (reinsurance contract asset) as standalone KPI
- Credit risk capital (K-ICS Item 20)

### Needs new collection pipeline (경영공시 — structured, lower cost)
1. Policy persistency: 13th-month and 25th-month retention rates
2. Reinsurance premiums ceded / cession rate by line of business

### Needs new collection pipeline (DART notes — higher cost, higher moat)
3. APE protection/savings split — systematic IR scrape
4. Risk Adjustment confidence level per company
5. Onerous contract proportion trend
6. CSM experience variance vs. assumption change breakdown
7. Interest rate sensitivity / duration gap (financial risk note)

Items 3–7 are the hardest to collect and therefore the highest defensibility
— "platform's core value-add zone" per domain feedback.

---

## Open Research Questions

- EIOPA QRT actual data accessibility: bulk download vs. per-filing scrape?
- Existing EU solvency comparison platforms: confirmed gap or overlooked incumbents?
- Japan FSA IFRS17 disclosure format: XBRL or PDF? Quarterly cadence?
- Singapore MAS / Hong Kong IA solvency disclosure structure?

These will be validated via research agent runs before committing EU/Japan
pipeline development resources.
