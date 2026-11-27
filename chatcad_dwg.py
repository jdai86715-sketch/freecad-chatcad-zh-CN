"""DWG 导出：把当前 FreeCAD 文档导出为 DWG 文件。

FreeCAD 本身不能写 DWG（格式专有）。这里采用社区通行做法：
先用 FreeCAD 自带的 DXF 导出（importDXF）把模型写成 DXF，
再调用外部免费工具 ODA File Converter 把 DXF 转成 DWG。

导出的 DWG 内容与 FreeCAD 的 DXF 导出一致：模型的边线几何
（直线、圆弧等），不是 ACIS 实体。DWG 版本默认 ACAD2018——
AutoCAD 2019 至 2026 都使用这一版 DWG 格式（AC1032）。

本模块不依赖 Qt，可在 freecadcmd 中单独测试（见 tests/fc_test_dwg.py）。
"""
import glob
import os
import shutil
import subprocess
import tempfile

VERSIONS = ("ACAD2018", "ACAD2013", "ACAD2010", "ACAD2007", "ACAD2004", "ACAD2000")
DEFAULT_VERSION = "ACAD2018"
DOWNLOAD_URL = "https://www.opendesign.com/guestfiles/oda_file_converter"


class DwgError(Exception):
    """带中文说明的 DWG 导出错误，面板直接把 str(e) 提示给用户。"""


def find_converter(saved_path=""):
    """按顺序找 ODAFileConverter：用户设置 → 环境变量 → PATH → 常见安装位置。

    找到返回程序路径，找不到返回 ""。
    """
    cands = []
    if saved_path:
        cands.append(saved_path)
    env = os.environ.get("ODA_FILE_CONVERTER", "")
    if env:
        cands.append(env)
    w = shutil.which("ODAFileConverter")
    if w:
        cands.append(w)
    pats = [
        r"C:\Program Files\ODA\ODAFileConverter*\ODAFileConverter.exe",
        r"C:\Program Files (x86)\ODA\ODAFileConverter*\ODAFileConverter.exe",
        os.path.expanduser(r"~\AppData\Local\ODA\ODAFileConverter*\ODAFileConverter.exe"),
        "/usr/bin/ODAFileConverter*",
        "/usr/local/bin/ODAFileConverter*",
        os.path.expanduser("~/.local/bin/ODAFileConverter*"),
    ]
    for p in pats:
        cands.extend(sorted(glob.glob(p)))
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return ""


def _shape_objects(doc):
    objs = []
    for o in doc.Objects:
        shape = getattr(o, "Shape", None)
        if shape is None or shape.isNull():
            continue
        vo = getattr(o, "ViewObject", None)
        if vo is not None and not vo.Visibility:
            continue
        objs.append(o)
    return objs


def export_dxf(doc, dxf_path):
    """用 FreeCAD 自带的 importDXF 把文档对象导出为 DXF，返回导出的对象数。"""
    objs = _shape_objects(doc)
    if not objs:
        raise DwgError("当前文档里没有可导出的模型对象。")
    import importDXF
    importDXF.export(objs, dxf_path)
    if not os.path.isfile(dxf_path):
        raise DwgError("DXF 导出失败：没有生成中间文件。")
    return len(objs)


def convert_to_dwg(converter, dxf_path, dwg_path, version=DEFAULT_VERSION):
    """调用 ODA File Converter 把 DXF 转成 DWG，成功返回 dwg_path。"""
    if version not in VERSIONS:
        version = DEFAULT_VERSION
    if not converter or not os.path.isfile(converter):
        raise DwgError("未找到 ODA File Converter 程序。DWG 导出需要先安装它"
                       f"（免费下载：{DOWNLOAD_URL}），或在面板“更多”菜单的"
                       "“DWG 转换器设置…”中指定程序位置。")
    with tempfile.TemporaryDirectory(prefix="chatcad_dwg_") as td:
        in_dir = os.path.join(td, "in")
        out_dir = os.path.join(td, "out")
        os.makedirs(in_dir)
        os.makedirs(out_dir)
        shutil.copyfile(dxf_path, os.path.join(in_dir, "model.dxf"))
        try:
            r = subprocess.run([converter, in_dir, out_dir, version, "DWG", "0", "1", "*.DXF"],
                               capture_output=True, text=True, timeout=180)
        except OSError as e:
            raise DwgError(f"无法启动 ODA File Converter：{e}")
        except subprocess.TimeoutExpired:
            raise DwgError("ODA File Converter 转换超时（180 秒）。")
        made = os.path.join(out_dir, "model.dwg")
        if not os.path.isfile(made):
            tail = (r.stderr or r.stdout or "").strip().splitlines()
            hint = tail[-1] if tail else f"退出码 {r.returncode}"
            raise DwgError(f"DWG 转换失败：{hint}")
        os.makedirs(os.path.dirname(os.path.abspath(dwg_path)), exist_ok=True)
        shutil.copyfile(made, dwg_path)
    return dwg_path


def export_document_dwg(doc, dwg_path, converter="", version=DEFAULT_VERSION):
    """一步完成：文档 → DXF → DWG。返回 (dwg_path, 导出的对象数)。"""
    if not converter:
        converter = find_converter()
    with tempfile.TemporaryDirectory(prefix="chatcad_dxf_") as td:
        dxf = os.path.join(td, "model.dxf")
        n = export_dxf(doc, dxf)
        convert_to_dwg(converter, dxf, dwg_path, version)
    return dwg_path, n
