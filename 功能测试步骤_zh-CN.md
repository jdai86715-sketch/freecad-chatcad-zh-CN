# Chat CAD（简体中文）Windows 功能测试步骤

环境：Windows 11 + FreeCAD 1.1.4 + Ollama（模型 `qwen3-vl:8b`）。
下文 `<插件目录>` 指插件根目录，`<FreeCAD>` 指 FreeCAD 安装目录（如 `C:\Program Files\FreeCAD 1.1`）。

## 第 0 步：恢复 tests 目录结构（重要）

整合包把测试文件平铺在根目录，但测试脚本按上游的 `tests/` 布局写路径，直接在根目录跑会找不到文件。先在插件目录里新建 `tests\` 和 `tests\fixtures\` 两个文件夹，把文件挪进去：

- 挪到 `tests\`：`fc_test_tools.py`、`live_e2e.py`、`qt_test_agent.py`、`qt_test_backend.py`、`qt_test_ui.py`、`test_llm.py`
- 挪到 `tests\fixtures\`：`ollama_qwen3_4b_thinking_partial.ndjson`、`ollama_qwen3_8b_toolcall.ndjson`、`openai_qwen25_toolcall.sse`

## 第 1 步：不用真模型的自动测试（先跑这三个，最快）

用 FreeCAD 自带的 Python（带 PySide6），不需要打开 FreeCAD 界面。在 PowerShell 里：

```powershell
cd <插件目录>
set QT_QPA_PLATFORM=offscreen
"<FreeCAD>\bin\python.exe" -I tests\qt_test_backend.py
"<FreeCAD>\bin\python.exe" -I tests\qt_test_ui.py
"<FreeCAD>\bin\python.exe" -I tests\qt_test_agent.py
```

通过标准：每个脚本跑完没有 traceback，汇总行全部 ok。`qt_test_agent.py` 用的是假 Ollama 服务器，验证的是智能体循环和 HTTP，不消耗真模型。

再跑纯解析单元测试（用录制好的模型响应回放）：

```powershell
"<FreeCAD>\bin\python.exe" tests\test_llm.py
```

通过标准：unittest 输出 `OK`。

## 第 2 步：FreeCAD 工具层测试（无界面，真 FreeCAD 内核）

```powershell
set FREECAD_USER_HOME=%TEMP%\fc_test_home
"<FreeCAD>\bin\freecadcmd.exe" -c "exec(open(r'<插件目录>\tests\fc_test_tools.py', encoding='utf-8').read())"
```

通过标准：结果汇总全部 ok（脚本会把明细写到结果文件，末行形如 `N/N ok`）。

## 第 3 步：真模型端到端（慢，CPU 约 3–10 分钟）

先确认 Ollama 在运行、模型已拉取：

```powershell
ollama list
ollama pull qwen3-vl:8b
```

然后：

```powershell
set FREECAD_USER_HOME=%TEMP%\fc_test_home
set CHATCAD_TESTS=<插件目录>\tests
set CHATCAD_MODEL=qwen3-vl:8b
"<FreeCAD>\bin\freecadcmd.exe" -c "exec(open(r'<插件目录>\tests\live_e2e.py', encoding='utf-8').read())"
```

默认任务是生成一个带中心孔的圆柱。通过标准：`tests\live_result_qwen3-vl_8b.txt` 里记录生成成功、实体体积正常、无异常堆栈。

## 第 4 步：手动界面冒烟测试

1. 把整个插件目录复制到 `%APPDATA%\FreeCAD\v1-1\Mod\freecad-chatcad`，重启 FreeCAD。
2. 看“报告视图”有没有红色报错；打开 Chat CAD 面板，确认界面是简体中文。
3. 面板设置里选本地 AI → Ollama，点“检查连接”，确认能连上并选中 `qwen3-vl:8b`。
4. “建模”模式输入：`创建一个直径 40mm、高 15mm 的圆柱，中间打一个直径 10mm 的通孔`。确认：3D 视图出现实体、文档里有“参数”表格、尺寸对得上。
5. 在 3D 视图里选中圆柱的一个面，再输入一句修改要求（如“把这个面往外凸出 5mm”），确认模型能带着选面上下文修改。
6. 切到“规划”模式问同一个修改，确认它只讨论、不动模型。
7. （可选）附加一张截图并标注，确认视觉模型能读懂标注。

## 记录结果

每一步把通过/失败和报错原文记下来（或截图），发回给 Muse 汇总。任何一步失败，先保留完整 traceback，不要改代码重试。
