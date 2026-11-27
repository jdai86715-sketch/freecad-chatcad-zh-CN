# Chat CAD for FreeCAD（简体中文）

Chat CAD 是 FreeCAD 侧边栏中的 AI 建模插件。你可以用文字描述零件、在 3D 视图中选择面或附加标注图片，让模型通过 FreeCAD 创建或修改参数化零件。

[English](README.md)

> **项目状态：Alpha。** 上游项目在 Windows 11 和 FreeCAD 1.1.4 上测试过。插件支持多个 AI 提供方；本仓库增加了简体中文界面和本地模型的中文提示词。复杂零件生成效果取决于模型，建议先检查模型结果和尺寸。

## 来源、许可与致谢

- **本仓库是上游项目的简体中文本地化版本，不是原创项目。** 上游项目：[Vittuu/freecad-chatcad](https://github.com/Vittuu/freecad-chatcad)，原作者 **Vittuu**。插件的设计、绝大部分代码、界面截图和测试录制文件均来自上游项目。
- **许可证：LGPL-2.1**，与上游一致，见仓库根目录 [LICENSE](LICENSE)。`package.xml` 中的维护者和仓库地址仍指向 上游。
- **本仓库所做的修改**：简体中文界面翻译、本地模型的中文提示词、中文 README、把上游测试中按葡语/英语原文断言的用例同步改为中文断言、恢复上游的 `tests/` 目录结构。功能逻辑未做改动。
- **第三方项目**：[FreeCAD](https://www.freecad.org/) 和 [Ollama](https://ollama.com) 是独立的第三方软件，归各自社区/团队所有；本仓库不包含它们的安装程序，也不包含任何 Ollama 模型文件。
- 如需原版（英文/葡语界面）或向上游反馈问题，请访问上游仓库。

## 功能

- 在 FreeCAD 中使用可停靠的 Chat CAD 面板。
- 通过文字描述创建或修改参数化模型。
- 选择 FreeCAD 中的面、边或点，把选择上下文发送给模型。
- 附加图片、粘贴截图，或在图片和 3D 视图上标注修改位置。
- 使用“建模”模式执行修改，或使用“规划”模式只讨论方案。
- 本地模型通过 Ollama 或 OpenAI 兼容服务运行；本地服务配置下，请求不会发送到云端。

## 环境

### 必需环境

1. FreeCAD 1.0 或更新版本。上游项目的 Windows 测试环境为 FreeCAD 1.1.4。
2. 如需使用本地模型，安装 [Ollama](https://ollama.com)。插件通过本机服务地址 `http://127.0.0.1:11434` 连接 Ollama。
3. 选择支持工具调用的模型。带图片的请求还需要主模型支持视觉，或在 Chat CAD 设置中指定一个视觉模型。

> FreeCAD 和 Ollama 是独立软件，本仓库不包含它们的安装程序。Ollama 模型文件体积较大，也不放入 Git 仓库。

### 本机配置参考

此开发环境使用 Windows 11、FreeCAD 1.1.4、Ollama 和 `qwen3-vl:8b`。该模型标识仅作配置参考；不同硬件、Ollama 版本和模型能力可能影响生成结果。

1. 安装并启动 Ollama。
2. 在 Ollama 中下载模型，例如：

   ```powershell
   ollama pull qwen3-vl:8b
   ```

3. 将本仓库放入 FreeCAD 用户目录的 `Mod` 文件夹。Windows 常见路径为：

   ```text
   %APPDATA%\FreeCAD\v1-1\Mod\freecad-chatcad
   ```

4. 重启 FreeCAD。在 Chat CAD 面板中打开本地 AI 设置，选择 Ollama，确认服务地址，然后检查连接并选择已下载的模型。
5. 上传图片前，确认所选模型支持视觉；否则在设置中选择视觉模型，或改用文字描述图片。

插件的 Ollama 接口直接通过 FreeCAD 内部 HTTP 客户端调用服务，不要求单独安装 Python 包、MCP 插件或 CLI。其它提供方可能有各自的 CLI、账户登录或 MCP 要求，详见英文 [README](README.md)。

## 安装

### 克隆到 FreeCAD 的 Mod 目录

将仓库克隆到对应 FreeCAD 版本的用户 `Mod` 目录，重启 FreeCAD 后，Chat CAD 面板会自动加载。

```text
%APPDATA%\FreeCAD\v1-1\Mod\freecad-chatcad
```

也可以通过 FreeCAD Addon Manager 添加自定义仓库：

```text
https://github.com/Vittuu/freecad-chatcad
```

### 使用 Addon Manager

在 FreeCAD 中打开“编辑 → 首选项 → Addon Manager → 自定义仓库”，添加仓库地址并选择 `main` 分支，然后安装 Chat CAD 并重启 FreeCAD。

## 使用

1. 在面板中选择本地 AI 和已安装的 Ollama 模型。
2. 在输入框描述你要创建的零件，也可以选择工作流卡片或快捷操作。
3. 修改已有零件时，可先在 3D 视图中选择一个面，再输入要求；也可以附加照片或截图，并在图片上标注尺寸和修改位置。
4. 检查生成步骤、模型参数和实体结果。参数通常保存在文档的“参数”表格中。

本地模型的结果质量不一。开始时可尝试简单形状和单个修改；复杂建模任务可能需要多轮调整。项目原始测试结果和各 AI 提供方要求见 [English README](README.md)。

## 仓库内容

- `chatcad_*.py`、`InitGui.py`、`chatcad.qss`：插件实现和界面资源。
- `package.xml`、`LICENSE`：FreeCAD Addon Manager 元数据及许可证。
- `README.md`：英文项目说明。
- `README_zh-CN.md`：简体中文安装和环境说明。
- `tests/`：上游项目测试套件（断言已同步为中文）和录制文件（`tests/fixtures/`）。
- `功能测试步骤_zh-CN.md`、`功能测试结果_虚拟机.md`：本仓库的功能测试步骤与一次在 FreeCAD 1.1.4（Linux）上的实测记录：除真模型端到端外，其余套件共 349 项检查全部通过。

本仓库不保存本机 Ollama 模型、FreeCAD 用户配置、访问令牌或用户模型文件。
