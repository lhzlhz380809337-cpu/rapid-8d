# Rapid 8D

Rapid 8D 是一款面向制造业质量问题解决的 Windows 桌面应用。它支持逐步引导分析，也能读取完整调查资料并生成 D1–D8 报告草稿。

## 主要能力

- 引导分析：围绕当前阶段的一个问题对话；闲聊不入库，整理本阶段时才改报告，并对照其他阶段已成立的内容。
- 资料成稿：导入 DOCX、PDF、Excel、CSV、TXT 或 Markdown，整理为完整 8D 报告。
- D4 根因分析：独立鱼骨画布、产生根因与逃逸根因、证据和验证记录。
- 研析工作台：深海军蓝与青绿色桌面界面，横向 D1–D8 路径、案例管理和报告中心。
- 本地案例管理：自动保存、历史版本、阶段复核与本地加密密钥。
- 报告交付：导出可编辑 Word 和 PDF，支持中文及中英双语正文。
- 自选模型：连接 Chat Completions 兼容接口，配置保存在本机。

## 下载与使用

克隆本仓库后，双击根目录的 **启动 Rapid 8D.exe**。需要本机已安装 Python 3.11 或 3.12。案例和模型密钥保存在当前用户的本地数据目录。

0.5.0 暂不提供安装包。上一版安装程序仍为 Releases 中的 `Rapid8D-Setup-0.3.1.exe`。

详细说明见 [README_DESKTOP.md](README_DESKTOP.md)，桌面版设计见 [docs/desktop-design.md](docs/desktop-design.md)。

## 开发

程序使用 Python 本地服务和原生 Windows 启动器。运行 `run-dev.ps1` 可启动开发版；运行 `desktop/build.ps1` 和 `desktop/build-setup.ps1` 可生成便携版与安装程序。

当前版本：**0.5.0**
