# -*- coding: utf-8 -*-
"""AMBIGUOUS 숫자마커(인용 페이지에서 2회 이상 등장)를 **행 귀속 마커**로 승격한다.

방법: 게이트 자신의 `_row_anchor_check`(라벨-값 y밴드 3.0pt + 값이 라벨 오른쪽)로,
K-ICS 표의 행 라벨 어휘를 전수 시도해 그 값을 인쇄하는 행을 찾는다.
  · 앵커된 라벨이 여럿이면 **가장 구체적인 것**(다른 라벨의 접두사인 것은 버린다)만 남긴다.
  · 하나도 못 찾으면 승격하지 않고 남긴다 — 게이트가 매 실행 `EXEMPTION_MARKER_UNANCHORED`
    review 로 인쇄하므로 무엇이 남았는지가 사라지지 않는다.
`present_markers` 는 지우지 않는다(부재/문장 근거와 회귀 감시를 겸한다). 등급만 올라간다."""
import importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
spec = importlib.util.spec_from_file_location("vkd", ROOT / "scripts" / "validate_kics_disclosure.py")
vkd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vkd)

# K-ICS 공시표 행 라벨 어휘 (TFI 표 · 헤드라인 세부표 · 요구자본표 · 금리위험액표)
VOCAB = [
    "지급여력비율", "지급여력금액", "지급여력기준금액",
    "보완자본 한도 적용 전", "보완자본 한도", "기본자본", "보완자본",
    "해약환급금", "기발행 신종자본증권", "기발행 후순위채무",
    "순자산", "불인정", "재분류", "기본요구자본", "분산효과",
    "생명", "일반손해", "시장위험액", "신용위험액", "운영위험액",
    "법인세", "기타 요구자본", "금리 위험액", "순자산가치",
]
NUM = re.compile(r"^[\d,.\s()%△▲-]+$")
LED = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"
led = json.loads(LED.read_text(encoding="utf-8"))

promoted = left = 0
for e in led["entries"]:
    if e.get("status") == "CONTRADICTED":
        continue
    v = e.get("verify") or {}
    f, pages = v.get("file"), v.get("pages")
    pres = [m for m in (v.get("present_markers") or []) if m]
    if not f or not pages or not pres:
        continue
    p = ROOT / f
    if not p.exists() or p.suffix.lower() != ".pdf":
        continue
    import fitz
    doc = fitz.open(p)
    flat = "".join("".join(doc[n - 1].get_text().split())
                   for n in pages if 0 <= n - 1 < doc.page_count)
    doc.close()
    rows, still = [], []
    for m in dict.fromkeys(pres):            # 중복 마커 제거
        if not NUM.match(m) or flat.count("".join(m.split())) <= 1:
            continue
        # 값이 실제로 앉아 있는 **행 y** 별로 가장 구체적인 라벨을 고른다.
        # 전역 접두사 제거는 틀린다 — `보완자본` 과 `보완자본 한도 적용 전` 이 **서로 다른 두 행**
        # 에서 같은 값을 인쇄하는 발행사가 있고(코리안리: item51 == item47), 그때 짧은 쪽을 지우면
        # 실재하는 행 하나를 잃는다. 반대로 같은 행에서는 짧은 라벨이 긴 라벨의 앞부분에 불과하므로
        # 지워야 한다.
        hits = {}   # label -> [라벨 y ...]
        for lab in VOCAB:
            ys = vkd._row_anchor_ys(p, pages, lab, m)
            if ys:
                hits[lab] = ys
        keep = []
        for lab, ys in hits.items():
            longer = [(o, oy) for o, oys in hits.items()
                      for oy in oys
                      if len("".join(o.split())) > len("".join(lab.split()))
                      and "".join(o.split()).startswith("".join(lab.split()))]
            own = [y for y in ys
                   if not any(abs(y - oy) <= vkd._ROW_ANCHOR_BAND for _o, oy in longer)]
            if own:
                keep.append(lab)
        if keep:
            rows += [{"row": lab, "value": m} for lab in sorted(keep)]
        else:
            still.append(m)
    if rows:
        v["present_rows"] = rows
        promoted += len(rows)
    left += len(still)
    print(f"-- {e['company']} {e['quarter']} [{e['registry'][:14]}] 승격 {len(rows)} / 미승격 {still}")
    for r in rows:
        print(f"     {r['value']:>14s}  <- 행 '{r['row']}'")

led["_verify_contract"] = (
    (led.get("_verify_contract", "") or "")
    + " **2026-08-24 — `present_rows` 신설(행 귀속 검사).** `[{row, value}]` 형태로 적으면 "
      "게이트가 인용 페이지에서 그 **행 라벨과 값이 같은 행 밴드(y중심 ±3.0pt, 값이 라벨 오른쪽)** "
      "에 있는지 확인한다. 어긋나면 `EXEMPTION_CITATION_CONTRADICTED` RED. "
      "종전 `present_markers` 는 '값이 이 페이지 어딘가 있다' 만 봐서, 원장이 기록하는 명제"
      "('어느 행이 값 V 를 인쇄한다')를 검사하지 못했다 — 실측 155개 마커 중 57개가 인용 페이지에서 "
      "2회 이상 등장했다(검사처럼 보이는 무검사). 캘리브레이션: 참 히트 최대 Δ0.21pt · "
      "거짓 히트 최소 Δ4.63pt (12케이스, 참 9 + 음성대조 3에서 3.0pt 가 12/12 정답). "
      "`present_markers` 는 그대로 둔다 — 부재·문장 근거와 회귀 감시를 겸한다.")

LED.write_text(json.dumps(led, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\n승격 총 {promoted}쌍 · 미승격 {left}개")
