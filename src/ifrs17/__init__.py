"""IFRS17 DART disclosure pipeline.

Subagent-owned domain. Independent of `src.solvency` (K-ICS).
Pipeline stages will land here as PoCs are accepted by the user:

    src/ifrs17/
        config.py                - paths + OpenDART API key resolution
        company_map.py           - KR<->corp_code mapping (single source of truth)
        opendart_client.py       - thin requests wrapper (PoC)
        csm_extractor.py         - boundary-of-context CSM table capture
        liability_table_skim.py  - "Skimming First" structural reporter
"""
