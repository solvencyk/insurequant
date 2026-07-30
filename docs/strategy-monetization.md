# Insurequant Monetization Strategy

Last updated: 2026-05-27 (Solvency II research results incorporated)

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

## Solvency II Research Results (2026-05-27)

### Competitive landscape — gap confirmed

No affordable comparison platform exists at the $100–$1,000/month tier.
Existing options are all institutional-grade:

| Platform | Pricing | Gap |
|----------|---------|-----|
| Solvency II Wire Data | Basic free / paid undisclosed | SFCR search only, no structured numeric comparison |
| Insurance Risk Data | Institutional, est. $10K–$100K/yr | Not suitable for mid-market B2B |
| AM Best Solvency II Suite | High-cost institutional bundle | No individual/SMB access |
| LSEG / Refinitiv | Terminal-integrated, institutional | Same |

This is structurally identical to the Korean K-ICS market gap. The
sub-$1K/month SaaS comparison tier is empty in both markets.

### Data access reality

**EU (Solvency II):**
- SFCR (Solvency and Financial Condition Report) is mandatory public
  disclosure — theoretically 2,000+ insurers accessible
- Critical caveat: public SFCRs are **PDF only**. XBRL is mandated only for
  regulatory reporting (to national supervisors), not public disclosure.
- EIOPA aggregate statistics are free but **national-level only** — no
  individual insurer data in free tier
- Technical challenge is identical to Korea: PDF parsing and structuring.
  K-ICS pipeline experience transfers directly.

**K-ICS ↔ Solvency II structural equivalence:**
K-ICS was designed with explicit reference to Solvency II. Concepts map 1:1:
- SCR (Solvency Capital Requirement) = K-ICS 지급여력기준금액
- Own Funds = K-ICS 지급여력금액
- Risk module decomposition = K-ICS 위험액 세부 분해
- SCR ratio = K-ICS 지급여력비율

The same dashboard architecture works for both. This is the core
transferability argument.

### Regional opportunity timeline

| Region | Data availability | Timing | Notes |
|--------|-----------------|--------|-------|
| Japan | ★★★★★ | **Now (2026)** | ESR (Economic Solvency Ratio) live as of March 2026 — data just starting. IFRS17 adopted by major insurers. First-mover window open. Old SMR data also individually disclosed. |
| Singapore | ★★★★☆ | Near-term | RBC2 framework, individual insurer disclosure is structured, English-language market |
| EU | ★★★☆☆ | Medium-term | SFCR PDF mass-parsing challenge, large market, multilingual |
| Hong Kong | ★★★☆☆ | 2026–2027 | HKRBC Pillar 3 public disclosure starts 2026 |
| Malaysia / Taiwan | ★★☆☆☆ | Long-term | Data availability insufficient for near-term |

**Japan is the clearest immediate opportunity.** ESR just launched in March
2026 — data is accumulating now, no incumbent has built the aggregation layer
yet, and the Japanese insurance market is the second largest in Asia.

### Updated conflict-of-interest assessment

Korean Re's reinsurance business is with Korean primary insurers.
Structured solvency data services covering EU/Japan/Singapore insurers have
zero overlap with that business. Standard moonlighting clauses target
"competing with the company's business" — a global financial data service for
non-Korean markets does not meet that definition. Verify exact employment
contract wording, but the structural argument is strong.

---

## Recommended Sequencing

**2026 H2 – 2027: Korea reference customers + Japan pipeline**
- Korea: Close 1–2 paying B2B customers (technical validation, small-scale
  revenue start). Target foreign reinsurers' Korean desks, actuarial advisory.
- Japan: Begin ESR data pipeline build in parallel. March 2026 framework
  launch means data is accumulating now with no incumbent aggregator.
- Conflict-of-interest management: verify moonlighting clause wording,
  disclose proactively to employer, retain all IP personally.

**2027 – 2028: Korea + Japan integrated platform**
- Unified product: "K-ICS & ESR Solvency Dashboard"
- Add Singapore (RBC2) to broaden Asia coverage
- Positioning: "Asia insurer solvency comparison" targeting global reinsurers
  (Munich Re, Swiss Re, Scor) who need Asia primary insurer profiling

**2028+: EU Solvency II pivot**
- Leverage SFCR PDF parsing technology (same skill as K-ICS/ESR pipelines)
  plus Asia reference customer base
- Target global reinsurers using the platform for EU primary insurer profiling
- TAM: ~2,000+ EU insurers vs ~60 in Korea

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

- ~~Existing EU solvency comparison platforms?~~ **Answered: gap confirmed.** No
  affordable ($100–$1K/month) comparison product exists.
- ~~Japan data availability?~~ **Answered: ESR live March 2026, best near-term opportunity.**
- EIOPA QRT: bulk download availability vs. per-filing scrape for individual insurer data?
- Japan ESR: exact disclosure format (PDF vs. structured), publication cadence, insurer universe size?
- Singapore RBC2: individual insurer disclosure schema, MAS publication endpoint?
- Hong Kong HKRBC Pillar 3: first filings expected when exactly?
