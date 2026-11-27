"""chatcad_dwg 的无头测试：DXF 中间导出、错误处理，以及（设置了
CHATCAD_ODA 时）经 ODA File Converter 的完整 DWG 导出。
运行（隔离 FreeCAD 用户目录）：
  set FREECAD_USER_HOME=<临时目录>  &  set CHATCAD_TESTS=<仓库>/tests
  set CHATCAD_ODA=<ODAFileConverter 程序路径>   （可选，没有则跳过真转换）
  freecadcmd -c "exec(open(r'<仓库>/tests/fc_test_dwg.py', encoding='utf-8').read())"
"""
import os
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.environ["CHATCAD_TESTS"]
sys.path.insert(0, os.path.dirname(HERE))

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402,F401
import chatcad_dwg as D  # noqa: E402

RESULTS = []


def check(name, cond, info=""):
    RESULTS.append((name, bool(cond), info))


def main():
    doc = App.newDocument("DwgTeste")
    box = doc.addObject("Part::Box", "Box")
    box.Length, box.Width, box.Height = 50, 30, 10
    cyl = doc.addObject("Part::Cylinder", "Cyl")
    cyl.Radius, cyl.Height = 5, 10
    cyl.Placement.Base.x = 25
    cyl.Placement.Base.y = 15
    doc.recompute()

    tmp = tempfile.mkdtemp(prefix="chatcad_dwg_test_")
    dxf = os.path.join(tmp, "model.dxf")
    n = D.export_dxf(doc, dxf)
    check("dxf_exported", os.path.isfile(dxf) and os.path.getsize(dxf) > 1000,
          f"n={n} size={os.path.getsize(dxf) if os.path.isfile(dxf) else 0}")
    check("dxf_counts_objects", n == 2, n)
    with open(dxf, encoding="utf-8", errors="replace") as f:
        text = f.read()
    check("dxf_has_geometry", "LINE" in text and "CIRCLE" in text)

    empty = App.newDocument("Vazio")
    try:
        D.export_dxf(empty, os.path.join(tmp, "x.dxf"))
        check("empty_doc_rejected", False, "没有抛错")
    except D.DwgError:
        check("empty_doc_rejected", True)

    try:
        D.convert_to_dwg(os.path.join(tmp, "nao_existe.exe"), dxf, os.path.join(tmp, "x.dwg"))
        check("missing_converter_rejected", False, "没有抛错")
    except D.DwgError as e:
        check("missing_converter_rejected", "ODA File Converter" in str(e), str(e))

    oda = os.environ.get("CHATCAD_ODA", "")
    if oda:
        dwg = os.path.join(tmp, "model.dwg")
        out, n2 = D.export_document_dwg(doc, dwg, oda)
        ok = os.path.isfile(out) and os.path.getsize(out) > 1000
        head = b""
        if ok:
            with open(out, "rb") as f:
                head = f.read(6)
        check("dwg_exported", ok and n2 == 2, f"size={os.path.getsize(out) if os.path.isfile(out) else 0}")
        check("dwg_is_2018_format", head == b"AC1032", head)
    else:
        print("SKIP dwg_exported/dwg_is_2018_format（未设置 CHATCAD_ODA）")


try:
    main()
except Exception:
    RESULTS.append(("crash", False, traceback.format_exc()))

for name, ok, info in RESULTS:
    print(("PASS " if ok else "FAIL ") + name, "" if ok else info)
print(f"\n{sum(1 for _, ok, _ in RESULTS if ok)}/{len(RESULTS)} ok")
