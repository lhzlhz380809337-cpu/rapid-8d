# Rapid 8D

Rapid 8D 是一款面向制造业质量问题解决的 Windows 桌面应用。它支持逐步引导分析，也能读取完整调查资料并生成 D1–D8 报告草稿。

## 主要能力

- 引导分析：围绕当前阶段持续对话、澄清事实并形成报告内容。
- 资料成稿：导入 DOCX、PDF、Excel、CSV、TXT 或 Markdown，整理为完整 8D 报告。
- D4 根因分析：鱼骨图、产生根因与逃逸根因、证据和验证记录。
- 本地案例管理：自动保存、历史版本、阶段复核与本地加密密钥。
- 报告交付：导出可编辑 Word 和 PDF，支持中文及中英双语正文。
- 自选模型：连接 Chat Completions 兼容接口，配置保存在本机。

## 下载与使用

在仓库右侧 **Releases** 下载 `Rapid8D-Setup-0.2.0.exe`，双击安装。安装程序会创建桌面和开始菜单快捷方式。

详细说明见 [README_DESKTOP.md](README_DESKTOP.md)，桌面版设计见 [docs/desktop-design.md](docs/desktop-design.md)。

## 开发

程序使用 Python 本地服务和原生 Windows 启动器。运行 `run-dev.ps1` 可启动开发版；运行 `desktop/build.ps1` 和 `desktop/build-setup.ps1` 可生成便携版与安装程序。

当前版本：**0.2.0**
