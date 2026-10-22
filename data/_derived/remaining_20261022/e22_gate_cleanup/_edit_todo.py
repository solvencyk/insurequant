from pathlib import Path
p = Path(__file__).resolve().parents[4] / "TODO_validation.md"
txt = p.read_bytes().decode("utf-8")
assert not txt.startswith("\ufeff")
nl = "\r\n" if "\r\n" in txt else "\n"
head = "## Status (최신 3개)" + nl + nl
assert txt.count(head) == 1
entry = (
"- **2026-10-23 (32차) 최신 비교열 적재 뒤 죽은 등재 7줄 철거 + `PL_OCI_VS_BS_AOCI` 공란 계수 결함 수정 (티켓 `20261023T0030Z`, 대상 HEAD `62ba44ed`, 미커밋)** — 철거(삭제만): `pl_bridge_baseline` 5줄(게이트 `FIXED?`) · `pl_csm_amort_missing_ledger` 롯데 2023.1Q(`..._LEDGER_INERT`) · `WFY_EXCEPTIONS` 한화생명·메리츠 FY2023(적재 전엔 필요, 지금은 두 소비처 모두 안 걸림, 변이 probe). 전후: master_tables SUMMARY 불변·stale 5->0, data_contract RED 0·YELLOW 169->168, 연속성 불변.\n"
"  결함: 공란(`값_당분기` None) 칸이 「tol 이내」에 섞였다(현재 340 중 108이 공란). 정정 후 비교 258(통과 232·flag 26)·공란 108·BS 결측 8(전부 2023.1Q). 전 버킷 시뮬: flag 집합 불변, 공란 때문에 YELLOW 에서 사라진 행 4(NH농협손해 2023.4Q·농협생명 2024.4Q·동양 2024.4Q·KB손해 2023.4Q). SUMMARY `oci_vs_bs_aoci:26Y/108blank/8bsskip` + 합성 입력 시험 신설(변이 확인) + 골든 `--update`(이 필드만 이동).\n"
"  남은 것(owner): `WFY_EXCEPTIONS` 의 KB라이프 FY2024·교보 FY2024·에이비엘 FY2023·KDB생명 FY2023·현대해상 FY2023 5줄은 적재 전에도 이미 안 걸렸다(철거는 owner 등재 변경). 공란 108칸(4Q 55) 중 누계 차로 재구성되는 17칸 중 6칸은 tol 초과(그림자, 게이트 입력 아님). 증거 `data/_derived/remaining_20261022/e22_gate_cleanup/`.\n"
).replace("\n", nl)
txt = txt.replace(head, head + entry, 1)
txt = txt.replace("> 갱신 2026-10-22 (31차", "> 갱신 2026-10-23 (32차 죽은 등재 철거 + OCI 대 BS AOCI 공란 계수 수정 · 31차", 1)
p.write_bytes(txt.encode("utf-8"))
print("ok")
