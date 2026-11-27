# -*- coding: utf-8 -*-
"""
建筑平面图模板生成器（A3 图框 + 140×32 标题栏 + 轴线/墙/柱平面图）

用法：
    python plan_template.py [参数文件.json]        （默认读同目录 params.json）

改参数文件里的数字和文字，运行后在输出目录得到三件套：
    <学号+姓名>.dxf / .dwg / .pdf

- DXF：R2018 格式，CAD 直接打开。
- DWG：经 ODA File Converter 转换（需先安装，免费）；找不到转换器时跳过并提示。
- PDF：A3 页面渲染，用于提交/预览；缺少 matplotlib 时跳过并提示。

参数说明见同目录《使用说明.md》。全程本地运行，不调用任何 AI。
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import date as _date

# ---------------------------------------------------------------- 参数

DEFAULTS = {
    # 标题栏
    "name": "戴锦源",
    "student_id": "2025310205",
    "college": "智能建造学院",
    "class_text": "2025建电2班",
    "date": "auto",                # "auto" = 今天，格式 YY.MM.DD；也可写死如 "26.11.27"
    "sheet_total": "共1张",
    "sheet_no": "第1张",
    "drawing_title": "建筑平面图",
    # 平面（单位 mm，图纸比例 1:scale）
    "x_spans": [6000],             # 横向每跨宽度，跨数 = len
    "y_spans": [6000],             # 纵向每跨进深
    "wall_thickness": 240,
    "column_size": 400,
    "scale": 100,
    "center_square_mm": 600,       # 平面中心小方块边长，0 = 不画
    "center_lines": True,          # 是否画穿过平面中心的十字线
    # 输出
    "out_dir": "输出",
    "basename": "",                # 空 = 学号+姓名
    "oda_path": "",                # ODAFileConverter 路径，空 = 自动查找
}


def load_params(path):
    p = dict(DEFAULTS)
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            p.update(json.load(f))
    if p["date"] == "auto":
        t = _date.today()
        p["date"] = f"{t.year % 100:02d}.{t.month:02d}.{t.day:02d}"
    return p


# ---------------------------------------------------------------- DWG 转换

def find_oda(saved=""):
    import glob
    import shutil
    cands = []
    if saved:
        cands.append(saved)
    for env in ("CHATCAD_ODA", "ODA_FILE_CONVERTER"):
        if os.environ.get(env):
            cands.append(os.environ[env])
    w = shutil.which("ODAFileConverter")
    if w:
        cands.append(w)
    for pat in (r"C:\Program Files\ODA\ODAFileConverter*\ODAFileConverter.exe",
                r"C:\Program Files (x86)\ODA\ODAFileConverter*\ODAFileConverter.exe",
                "/usr/bin/ODAFileConverter*",
                "/usr/local/bin/ODAFileConverter*"):
        cands.extend(sorted(glob.glob(pat)))
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return ""


def dxf_to_dwg(dxf_path, dwg_path, oda):
    with tempfile.TemporaryDirectory(prefix="plan_dwg_") as td:
        in_dir = os.path.join(td, "in")
        out_dir = os.path.join(td, "out")
        os.makedirs(in_dir)
        os.makedirs(out_dir)
        import shutil
        shutil.copyfile(dxf_path, os.path.join(in_dir, "plan.dxf"))
        r = subprocess.run([oda, in_dir, out_dir, "ACAD2018", "DWG", "0", "1", "*.DXF"],
                           capture_output=True, text=True, timeout=180)
        made = os.path.join(out_dir, "plan.dwg")
        if not os.path.isfile(made):
            raise RuntimeError(f"ODA 转换失败（退出码 {r.returncode}）")
        shutil.copyfile(made, dwg_path)


# ---------------------------------------------------------------- 绘图

def build_drawing(p):
    import ezdxf
    from ezdxf.enums import TextEntityAlignment

    doc = ezdxf.new("R2018")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    for name, color in (("FRAME", 7), ("TITLE", 7), ("WALL", 7), ("AXIS", 1), ("TEXT", 7)):
        doc.layers.add(name, color=color)
    if "CENTER" not in doc.linetypes:
        doc.linetypes.add("CENTER", pattern=[13.0, 10.0, -1.5, 0.0, -1.5],
                          description="Center line")
    doc.styles.add("HZ", font="simhei.ttf")

    def line(p1, p2, layer="FRAME", lw=None, lt=None):
        a = {"layer": layer}
        if lw is not None:
            a["lineweight"] = lw
        if lt is not None:
            a["linetype"] = lt
        msp.add_line(p1, p2, dxfattribs=a)

    def rect(x0, y0, x1, y1, layer="FRAME", lw=None):
        a = {"layer": layer}
        if lw is not None:
            a["lineweight"] = lw
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs=a)

    def text(s, cx, cy, h=5.0, layer="TEXT", width=None):
        a = {"style": "HZ", "height": h, "layer": layer}
        if width is not None:
            a["width"] = width
        t = msp.add_text(s, dxfattribs=a)
        t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
        return t

    # ---- A3 图框（420×297，左装订边 25，其余 10） ----
    rect(0, 0, 420, 297, "FRAME", lw=25)
    rect(25, 10, 410, 287, "FRAME", lw=100)

    # ---- 标题栏 140×32，右下角，原点 (270,10) ----
    OX, OY = 270.0, 10.0
    X = lambda r: OX + r
    Y = lambda r: OY + r
    rect(OX, OY, X(140), Y(32), "TITLE", lw=50)
    line((OX, Y(8)), (X(140), Y(8)), "TITLE")
    line((OX, Y(16)), (X(140), Y(16)), "TITLE")
    line((X(65), Y(24)), (X(140), Y(24)), "TITLE")
    line((X(15), OY), (X(15), Y(16)), "TITLE")
    line((X(40), OY), (X(40), Y(16)), "TITLE")
    line((X(65), OY), (X(65), Y(32)), "TITLE")
    line((X(80), Y(16)), (X(80), Y(32)), "TITLE")
    line((X(105), OY), (X(105), Y(32)), "TITLE")
    line((X(120), Y(16)), (X(120), Y(32)), "TITLE")

    def cell(s, rx0, rx1, ry0, ry1, h=5.0, width=None):
        text(s, X((rx0 + rx1) / 2), Y((ry0 + ry1) / 2), h=h, layer="TITLE", width=width)

    cell("材料", 65, 80, 24, 32)
    cell("数量", 65, 80, 16, 24)
    cell("比例", 105, 120, 24, 32)
    cell("制图", 0, 15, 8, 16)
    cell("学号", 0, 15, 0, 8)
    cell(f"1:{p['scale']}", 120, 140, 24, 32)
    cell(p["sheet_total"], 105, 120, 16, 24, h=4.5)
    cell(p["sheet_no"], 120, 140, 16, 24, h=4.5)
    cell(p["name"], 15, 40, 8, 16)
    cell(p["date"], 40, 65, 8, 16, h=4.0)
    cell(p["college"], 65, 105, 8, 16, h=4.5)
    cell(p["student_id"], 15, 40, 0, 8, h=3.5, width=0.8)
    cell(p["class_text"], 105, 140, 0, 8, h=4.0)

    # ---- 平面：轴线网格 ----
    scale = float(p["scale"])
    xs = [0.0]
    for s in p["x_spans"]:
        xs.append(xs[-1] + s / scale)
    ys = [0.0]
    for s in p["y_spans"]:
        ys.append(ys[-1] + s / scale)
    plan_w, plan_h = xs[-1], ys[-1]

    # 可用区域：内框内、标题栏上方（标题栏顶 y=42，留白到 48）
    ax0, ay0, ax1, ay1 = 31.0, 48.0, 404.0, 281.0
    need_w = plan_w + 2 * 24          # 两侧轴号圆（外伸 20 + 半径 4）
    need_h = plan_h + 2 * 24 + 12     # 下方还要放图名
    if need_w > (ax1 - ax0) or need_h > (ay1 - ay0):
        print(f"提醒：平面在 1:{p['scale']} 下放不进 A3 图框（需要 {need_w:.0f}×{need_h:.0f} mm，"
              f"可用 {(ax1 - ax0):.0f}×{(ay1 - ay0):.0f} mm），请改小跨度或改大比例分母。")
    ox = ax0 + ((ax1 - ax0) - plan_w) / 2
    oy = ay0 + ((ay1 - ay0) - plan_h) / 2 + 6
    gx = [ox + v for v in xs]
    gy = [oy + v for v in ys]
    ccx, ccy = ox + plan_w / 2, oy + plan_h / 2

    # 墙（外圈 + 内圈）
    wt = p["wall_thickness"] / scale
    rect(gx[0], gy[0], gx[-1], gy[-1], "WALL", lw=50)
    rect(gx[0] + wt, gy[0] + wt, gx[-1] - wt, gy[-1] - wt, "WALL", lw=50)
    # 柱（每个轴线交点）
    cs = p["column_size"] / scale / 2
    for px in gx:
        for py in gy:
            rect(px - cs, py - cs, px + cs, py + cs, "WALL", lw=50)
    # 中心方块与十字线
    if p["center_square_mm"]:
        h = p["center_square_mm"] / scale / 2
        rect(ccx - h, ccy - h, ccx + h, ccy + h, "WALL", lw=40)
    if p["center_lines"]:
        line((gx[0] - 15, ccy), (gx[-1] + 15, ccy), "WALL")
        line((ccx, gy[0] - 12), (ccx, gy[-1] + 12), "WALL")

    # 轴线与轴号
    def bubble(cx, cy, label):
        msp.add_circle((cx, cy), radius=4, dxfattribs={"layer": "AXIS"})
        text(label, cx, cy, h=5.0, layer="TEXT")

    for i, ax in enumerate(gx):
        line((ax, gy[0] - 16), (ax, gy[-1] + 16), "AXIS", lt="CENTER")
        bubble(ax, gy[0] - 20, str(i + 1))
        bubble(ax, gy[-1] + 20, str(i + 1))
    import string
    for j, ay in enumerate(gy):
        line((gx[0] - 16, ay), (gx[-1] + 16, ay), "AXIS", lt="CENTER")
        lab = string.ascii_uppercase[j] if j < 26 else f"A{j - 25}"
        bubble(gx[0] - 20, ay, lab)
        bubble(gx[-1] + 20, ay, lab)

    # 图名
    text(f"{p['drawing_title']}  1:{p['scale']}", ccx, gy[0] - 34, h=5.5)
    return doc


# ---------------------------------------------------------------- PDF

def render_pdf(doc, pdf_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import ColorPolicy, Configuration
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    # 字体回退：HZ 样式指定 SimHei（Windows 自带）；本机解析不到时，
    # 换用 ezdxf 能按文件名解析到的中文字体。只影响 PDF 渲染，不改已保存的 DXF。
    try:
        from ezdxf.fonts import fonts as _ezfonts

        def _resolves(fn):
            try:
                return _ezfonts.font_manager.get_font_face(fn).filename.lower() == fn.lower()
            except Exception:
                return False

        if not _resolves("simhei.ttf"):
            for _fn in ("NotoSansCJK-Regular.ttc", "NotoSerifCJK-Regular.ttc",
                        "NotoSansSC-Regular.otf", "msyh.ttc", "simsun.ttc"):
                if _resolves(_fn):
                    doc.styles.get("HZ").dxf.font = _fn
                    break
    except Exception:
        pass

    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    Frontend(RenderContext(doc), MatplotlibBackend(ax),
             config=Configuration(color_policy=ColorPolicy.BLACK)).draw_layout(doc.modelspace(), finalize=True)
    fig.savefig(pdf_path, dpi=200, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- 主流程

def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = argv[1] if len(argv) > 1 else os.path.join(here, "params.json")
    p = load_params(cfg_path)
    base = p["basename"] or f"{p['student_id']}{p['name']}"
    out_dir = p["out_dir"]
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(here, out_dir)
    os.makedirs(out_dir, exist_ok=True)

    doc = build_drawing(p)
    dxf = os.path.join(out_dir, base + ".dxf")
    doc.saveas(dxf)
    print(f"DXF 已生成：{dxf}")

    oda = find_oda(p["oda_path"])
    dwg = os.path.join(out_dir, base + ".dwg")
    if oda:
        try:
            dxf_to_dwg(dxf, dwg, oda)
            print(f"DWG 已生成：{dwg}")
        except Exception as e:
            print(f"DWG 未生成：{e}")
    else:
        print("DWG 未生成：未找到 ODA File Converter（安装后重跑，或在 params.json 里填 oda_path）。")

    pdf = os.path.join(out_dir, base + ".pdf")
    try:
        render_pdf(doc, pdf)
        print(f"PDF 已生成：{pdf}")
    except ImportError:
        print("PDF 未生成：缺少 matplotlib（pip install matplotlib 后重跑）。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
