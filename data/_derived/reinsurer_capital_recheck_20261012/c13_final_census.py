"""Final census: 8 reinsurers x 14 quarters x items (6,13,47,48,49,53,54), print vs master, every cell classified."""
import re, io, sys, json, csv, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = "data/_derived/reinsurer_capital_recheck_20261012/"
codes = [f"KR11{n:02d}" for n in range(1, 9)]
qs = [f"{y}.{q}Q" for y in (2023,2024,2025,2026) for q in (1,2,3,4) if not (y==2026 and q>2)]
items = [6, 13, 47, 48, 49, 53, 54]
rows = json.load(open("kics_disclosure.json", encoding="utf-8"))
M = {}; bucket = set()
for r in rows:
    if r["원보험사코드"] in codes:
        M[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r.get("값")
        bucket.add((r["원보험사코드"], r["공시분기"]))
comp = json.load(open(D + "c3_composition_census.json", encoding="utf-8"))
tfi = json.load(open(D + "c9_tfi_prints.json", encoding="utf-8"))

def num(s):
    s = (s or "").strip()
    if s == "": return ("BLANK", None)
    if s in ("-", "−", "—", "- -"): return ("DASH", 0.0)
    t = s.replace(",", "").replace(" ", "")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try: v = float(t)
    except ValueError: return ("TEXT", None)
    return ("NUM", -v if neg else v)

def same(pv, mv):
    mvf = float(mv)
    return any(abs(pv / f - mvf) <= max(0.51, abs(mvf) * 0.0006) for f in (1, 100, 100000))

# prints[(code,q,item)] = list of (doc, col, raw)
prints = collections.defaultdict(list)
for r in comp:
    for ci, q in enumerate(r["qs"]):
        if q is None: continue
        for item in (6, 13):
            raw = r["got"].get(str(item))
            if raw and ci < len(raw):
                prints[(r["code"], q, item)].append((r["docq"], "own" if ci == 0 else f"prior-{ci}", raw[ci]))
for code, q, st, got in tfi:
    if st != "OK" or not got: continue
    for k, v in got.items():
        k = int(k)
        if k in (47, 48, 49, 53, 54) and v:
            prints[(code, q, k)].append((q, "own", v[0] if k in (53, 54) else v[-1] if False else v[0]))

# manual classification of buckets/cells (evidence in runlog)
KNOWN_RESTATED = {("KR1102", "2024.4Q", 13): "스위스리 2024.4Q: 2025.1Q·2025.2Q 문서 전기 열이 재작성(보완자본 0)했으나 owner 단계 7 결정으로 원공시(52) 유지(runlog 7 §3)",
                  ("KR1102", "2025.3Q", 13): "스위스리 2025.3Q: 2025.4Q·2026.1Q 문서 전기 열은 951, 자기 분기 문서·경과조치 표는 850; 단계 7 §P2 로 자기 분기 값(850) 되돌림(TFI 표 항등식)"}
NO_DOC = {("KR1107", "2023.1Q"): "퍼시픽 2023.1Q 자기 문서 미수집(수집 정책; 2023.3Q 이전은 비율만 인쇄) - 단계 13 §7 NO_BUCKET",
          ("KR1107", "2023.2Q"): "퍼시픽 2023.2Q 자기 문서 미수집(수집 정책)",
          ("KR1102", "2023.3Q"): "스위스리 2023.3Q 자기 문서 「12월말 공시 예정」(K-ICS 표 없음). 후속 문서 전기 열에는 값이 있으나 버킷 적재는 새 RED 2 로 owner 결정 대기",
          ("KR1104", "2023.4Q"): "하노버 2023.4Q 자기 문서 「4월말 공시 예정」. 후속 문서 전기 열 값 있음, 버킷 적재는 owner 결정 대기",
          ("KR1104", "2024.1Q"): "하노버 2024.1Q 사이트 부재/미수집. 후속 문서 전기 열 값 있음, 버킷 적재는 owner 결정 대기",
          ("KR1104", "2025.3Q"): "하노버 2025.3Q 사이트 미게시. 후속 문서 전기 열 값 있음, 버킷 적재는 owner 결정 대기",
          ("KR1105", "2023.2Q"): "알지에이 2023.2Q 자기 문서 「공시 예정」. 후속 문서 전기 열 값 있음, 버킷 적재는 owner 결정 대기"}
for q in qs[:8]:
    NO_DOC.setdefault(("KR1108", q), "마이브라운 설립 2024.3·영업 2025.1 이전 - 해당 분기 K-ICS 자체가 없음(2025.2Q 문서 전기 열은 대시)")
NO_DOC[("KR1108", "2025.1Q")] = "마이브라운 2025.1Q 공시 없음(owner 확인); 2025.2Q·3Q 문서 전기 열은 대시"
HELD = {("KR1107", "2025.3Q", "tfi"): "퍼시픽 2025.3Q 경과조치 표: 「공통적용 경과조치 해당사항 없음」 서식에 전 칸 0 인쇄(머리글 지급여력금액 2,043억과 모순하는 서식 채움) - 빈 칸 유지, 적재는 owner 판단",
        ("KR1107", "2026.2Q", "tfi"): "퍼시픽 2026.2Q 동일(머리글 1,781억) - 빈 칸 유지, owner 판단",
        ("KR1101", "2026.2Q", "tfi"): "뮌헨 2026.2Q 경과조치 표는 지급여력금액·기본자본(271,642백만)만 인쇄, 나머지 행은 공란(대시도 아님) - 50·52 만 싣기는 게이트 TFI_TIER_PARTIAL_ROWS RED 2",
        ("KR1108", "2025.3Q", "tfi"): "마이브라운 2025.3Q 경과조치 표 47·48·49·53·54 는 대시(=0) 인쇄지만 적재하면 47_tier2_census TIER2_LIMIT_STALE RED 2(소액 오탐) - 게이트 보류"}
MANUAL_READ = {}
for it, ln in ((6, 484), (13, 513)):
    MANUAL_READ[("KR1103", "2023.4Q", it)] = f"md_inbox/FY2023_Q4/KR1103_제네럴재보험.md L{ln}: 대시(=0), 표가 쪼개져 추출기가 헤더를 못 찾았음. 마스터 0 과 일치"
MANUAL_READ[("KR1103", "2024.1Q", 6)] = "md_inbox/FY2024_Q1/KR1103_제네럴재보험.md L213: 대시. 마스터 0 과 일치"
MANUAL_READ[("KR1103", "2024.1Q", 13)] = "md_inbox/FY2024_Q1/KR1103_제네럴재보험.md L219: 당분기 칸 공란(전기 열은 대시) = 0. 마스터 0 과 일치"
for it, ln in ((6, 163), (13, 169)):
    MANUAL_READ[("KR1106", "2023.1Q", it)] = f"md_inbox/FY2023_Q1/KR1106_스코리재보험.md L{ln}: 대시. 마스터 0 과 일치"
for it, ln in ((6, 268), (13, 275)):
    MANUAL_READ[("KR1108", "2026.2Q", it)] = f"md_inbox/FY2026_Q2/KR1108_마이브라운반려동물전문보험.md L{ln}: 대시. 마스터 0 과 일치"
MANUAL_READ[("KR1107", "2024.3Q", 53)] = "md_inbox/FY2024_Q3/KR1107_퍼시픽라이프리.md L339: 49 행과 53 행 라벨이 한 칸에 합쳐진 표, 값 「- -」 = 둘 다 대시(=0). 마스터 0 과 일치"
for it in (6, 13, 47, 48, 49, 53, 54):
    MANUAL_READ[("KR1104", "2023.3Q", it)] = "FY2023_Q3 PDF 32쪽 이미지 전용(텍스트층 0) - 단계 7 §6 비전 판독 p12(4-2-2: 자본증권 -, 재분류 빈칸)·p13(공통적용 경과조치 표: 한도 관련 3행 -, 기발행 2행 -). 순자산 항등식 등 교차검증 통과. 마스터 0 과 일치(이번 라운드에 다시 렌더링하진 않음)"
out = []
counts = collections.Counter()
for code in codes:
    for q in qs:
        for item in items:
            mv = M.get((code, q, item))
            ps = prints.get((code, q, item), [])
            parsed = [(d, c, s, *num(s)) for d, c, s in ps]
            status = None; note = ""
            in_bucket = (code, q) in bucket
            if mv is not None:
                nums = [x[4] for x in parsed if x[4] is not None]
                if not ps:
                    status, note = "MASTER_ONLY_NO_PRINT_LOCATED", "마스터에만 있음(추출기가 인쇄 칸을 못 찾음; 상위 단계가 PDF 에서 적재)"
                    mk = (code, q, item)
                    if mk in MANUAL_READ:
                        status, note = "MATCH_MANUAL_READ", MANUAL_READ[mk]
                elif all(same(v, mv) for v in nums) if nums else all(x[3] in ("BLANK", "DASH") for x in parsed) and float(mv) == 0:
                    blank = [x for x in parsed if x[3] in ("BLANK",)]
                    status = "MATCH" if not blank else "MATCH_BLANK_AS_ZERO"
                    if status == "MATCH" and nums and all(x[3] == "DASH" for x in parsed): status = "MATCH_DASH_AS_ZERO"
                else:
                    key = (code, q, item)
                    if key in KNOWN_RESTATED: status, note = "DECIDED_RESTATEMENT_KEPT", KNOWN_RESTATED[key]
                    else:
                        status, note = "MISMATCH_REVIEW", "; ".join(f"{d}/{c}={s}" for d, c, s, *_ in parsed)
            else:
                if (code, q) in NO_DOC:
                    status, note = "ABSENT_BUCKET_" + ("PRINT_IN_LATER_DOC" if ps else "NO_PRINT"), NO_DOC[(code, q)] + (" | later-doc prints: " + "; ".join(f"{d}/{c}={s}" for d, c, s in ps) if ps else "")
                elif (code, q, "tfi") in HELD and item in (47, 48, 49, 53, 54, 50, 51, 52):
                    status, note = "ABSENT_HELD", HELD[(code, q, "tfi")]
                elif not in_bucket:
                    status, note = "ABSENT_BUCKET_UNCLASSIFIED", ""
                elif item in (47, 48, 49, 53, 54) and code == "KR1102" and q == "2023.2Q":
                    status, note = "ABSENT_SOURCE_DOC_LACKS_TFI", "스위스리 2023.2Q 값은 2023.4Q 완성본 전기 열에서만 적재; 경과조치 표(47~54)는 전기 열이 없어 원천 부재"
                elif item in (47, 48, 49, 53, 54) and code == "KR1107" and q in ("2023.3Q", "2023.4Q"):
                    status, note = "ABSENT_NO_OWN_DOC", "퍼시픽 2023.3Q·4Q 의 47~54: 자기 문서 미수집(2024.1Q 문서 전기 열로 1~46 만 적재)"
                elif item in (47,48,49,53,54) and code == "KR1104" and q == "2023.3Q":
                    status, note = "ABSENT_SOURCE_MD_TRUNCATED", "하노버 2023.3Q md_inbox MD 31행(변환 잘림) - 마스터 47~54 는 있음"
                else:
                    status, note = "ABSENT_UNCLASSIFIED", ""
            counts[status] += 1
            out.append(dict(code=code, quarter=q, item=item, master=mv, prints=" | ".join(f"{d}/{c}={s}" for d, c, s in ps), status=status, note=note))
with open(D + "c13_final_census.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
json.dump(out, open(D + "c13_final_census.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "cells")
for k, v in sorted(counts.items()): print(f"{v:5d}  {k}")
for r in out:
    if r["status"] in ("MISMATCH_REVIEW", "ABSENT_UNCLASSIFIED", "ABSENT_BUCKET_UNCLASSIFIED", "MASTER_ONLY_NO_PRINT_LOCATED"):
        print(r["code"], r["quarter"], r["item"], r["master"], r["status"], r["prints"][:140], r["note"][:80])
