# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("tests/test_private_deploy.py")
b = p.read_bytes().decode("utf-8")
crlf = "\r\n" in b
t = b.replace("\r\n", "\n")
def sub(old, new):
    global t
    assert t.count(old) == 1, old[:60]
    t = t.replace(old, new)

sub('''"""비공개 시트 3종 + 자본성증권발행현황 공개 열 제한 (owner 2026-10-12).
''', '''"""비공개 메커니즘 + 자본성증권발행현황 공개 열 제한 (owner 2026-10-12).

2026-10-12 재공개 라운드(티켓 20261012T2030Z): `기본자본소진율`·`보완자본소진율`·`자본비율전망` 3시트와 루트 JSON 3개를
비공개에서 풀었다 - 지금 `PRIVATE_SHEETS`·`PRIVATE_ROOT_JSONS`·배포 스크립트 `PRIVATE_PATHS` 는 비어 있다. 메커니즘은 그대로
남아 있어 아래 시험은 **합성 비공개 목록**(PRIVATE_SAMPLE)을 주입해 계속 돌린다(다시 내릴 때 시험이 살아 있다는 증거).
''')
sub('''def test_mutation_private_snapshot_present_fires(tmp_path):
    pe = tmp_path / "public_exports"
    shutil.copytree(PE, pe)
    (pe / "자본비율전망.json").write_text("[]", encoding="utf-8")
    assert "PUBLIC_EXPORT_PRIVATE_SHEET_PRESENT" in {r["rule"] for r in _gate_rows(pe)}''',
'''def test_mutation_private_snapshot_present_fires(monkeypatch, tmp_path):
    """합성 비공개 시트 하나를 선언하면 그 시트의 공개 스냅샷 파일 존재가 RED 로 잡혀야 한다(메커니즘 생존 확인)."""
    import export_public_sheets as E
    monkeypatch.setattr(E, "PRIVATE_SHEETS", ("자본비율전망",))
    pe = tmp_path / "public_exports"
    shutil.copytree(PE, pe)
    (pe / "자본비율전망.json").write_text("[]", encoding="utf-8")
    assert "PUBLIC_EXPORT_PRIVATE_SHEET_PRESENT" in {r["rule"] for r in _gate_rows(pe)}


def test_reopened_state_has_no_private_paths_and_public_snapshots_exist():
    """2026-10-12 재공개: 세 시트의 공개 스냅샷이 있고 manifest 에 실려 있다."""
    from export_public_sheets import PRIVATE_SHEETS, PRIVATE_ROOT_JSONS
    assert PRIVATE_SHEETS == () and PRIVATE_ROOT_JSONS == () and _sh_private_paths() == []
    man = json.loads((PE / "manifest.json").read_text(encoding="utf-8"))
    for s in ("기본자본소진율", "보완자본소진율", "자본비율전망"):
        assert (PE / f"{s}.json").exists(), s
        assert s in man["sheets"], s''')
sub('''PRIVATE_SAMPLE = ["public_exports/기본자본소진율.json"''', '''# 합성 비공개 목록(재공개 전 실제 목록과 같게 둔다). _run_deploy 에 주입하는 스크립트의 PRIVATE_PATHS 로 쓴다.
PRIVATE_SAMPLE = ["public_exports/기본자본소진율.json"''')
sub(r'''def _script_text():
    return SCRIPT.read_text(encoding="utf-8").replace("\r\n", "\n")''',
r'''def _script_text():
    """실제 스크립트에 합성 비공개 목록(PRIVATE_SAMPLE)을 주입한 본문 - 실제 목록은 재공개로 비어 있다."""
    text = SCRIPT.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.search(r'^PRIVATE_PATHS="([^"]*)"', text, re.M)
    assert m
    return text.replace(m.group(0), 'PRIVATE_PATHS="' + " ".join(PRIVATE_SAMPLE) + '"')''')
sub('''    # 시험용 PRIVATE_PATHS 는 실제 스크립트의 것 그대로(샘플 경로가 같은지 먼저 확인).
    assert sorted(_sh_private_paths()) == sorted(PRIVATE_SAMPLE)
''', '''    # 시험용 PRIVATE_PATHS 는 _script_text() 가 주입한 합성 목록이다.
    assert sorted(_sh_private_paths(_script_text())) == sorted(PRIVATE_SAMPLE)
''')
p.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
print("ok", "crlf" if crlf else "lf")
