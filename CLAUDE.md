# Rapid 8D — AI 辅助 8D 问题解决报告系统

> 全局规范参见：[`../../CLAUDE.md`](../../CLAUDE.md) | 全栈开发手册：[`../../.claude/DEVELOPMENT_GUIDE.md`](../../.claude/DEVELOPMENT_GUIDE.md)

## 项目定位

面向汽车行业质量工程师，按 8D 标准流程（D1-D8）填写问题描述、分析根因、制定对策，AI 辅助生成正式报告。支持 Electron 桌面应用 + Web 两种方式运行。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Pinia + Vue Router + Vite |
| 后端 | Python FastAPI (端口 8723) |
| 桌面 | Electron |
| LLM | 默认 DeepSeek，也支持 Ollama / Claude / GGUF |
| 存储 | JSON 文件 `backend/data/projects/{uuid}/context_YYYY-MM-DD.json` |
| 报告 | Jinja2 模板 + LLM 生成 + python-docx + Edge headless PDF |

## 目录结构

```
Rapid_8D/
├── frontend/src/
│   ├── pages/           # ChatView, HistoryView, SettingsView, ReportPreview, ReportGenerator
│   ├── components/      # PhaseWorkspace, PhaseChatPanel, StepProgress, VersionHistory,
│   │                    # MermaidRenderer, ExportMenu, ReviewHint, ReportViewer
│   ├── stores/          # chat.ts (核心状态), config.ts
│   ├── api/             # client.ts, chat.ts, session.ts, report.ts, config.ts
│   ├── utils/           # audio.ts
│   ├── i18n.ts          # FOCUS_ZH/EN + UI 文字
│   └── main.ts          # 路由
├── backend/
│   ├── main.py          # FastAPI 入口（端口 8723）
│   ├── config.py / config.yaml
│   ├── i18n.py          # 后端中英文
│   ├── api/             # session, chat, report, upload, voice
│   ├── conversation/    # engine.py + prompts/*.md (每个阶段的 AI 行为)
│   ├── project/         # context.py, manager.py
│   ├── llm/             # factory, openai_compat, claude, ollama, llama_cpp
│   ├── rag/             # RAG 预留
│   ├── report/          # generator.py, validator.py, templates/
│   ├── voice/           # transcriber.py (faster-whisper)
│   └── data/
│       ├── projects/    # 项目 JSON 数据
│       ├── chroma/      # RAG 向量库预留
│       ├── exports/     # 报告导出
│       └── models/      # Whisper 模型
├── tests/               # 单元测试脚本
├── electron/            # main.js, preload.js
├── 启动.vbs             # 无窗口启动器
├── 启动.bat             # 启动脚本
└── .devlogs/            # 开发日志
```

## 8D 步骤体系

| Step | 中文 | English |
|------|------|---------|
| D1 | 组建团队 | Build Team |
| D2 | 问题描述 | Describe Problem |
| D3 | 短期措施 | Short Term Action |
| D4 | 根本原因分析 | Root Cause Analysis |
| D5 | 制定长期措施 | Define Long Term Action |
| D6 | 实施长期措施 | Implement Long Term Action |
| D7 | 措施有效性验证 | Proof of Effectiveness |
| D8 | 标准化与预防 | Prevention |

## 核心架构

### AI 对话流程
```
用户输入 → PhaseChatPanel → POST /api/chat → engine.process_message()
  → 拼接对应步骤 prompt/*.md → LLM 回复 → 存入 JSON → 前端渲染
```

### 数据存储
- 唯一存储: `backend/data/projects/{uuid}/context_YYYY-MM-DD.json`
- 每天自动保存快照，同一天多次保存会覆盖
- 项目列表通过扫描文件系统获取

### 前端 ChatView 三栏布局
- 左侧栏: 步骤进度 + logo + 生成按钮 + 版本历史
- 中间: PhaseWorkspace (关注点 → 上下文编辑 → AI 输出)
- 右侧: PhaseChatPanel (AI 对话)

## shared_auth 引用

`backend/main.py` 中引用控制中心共享鉴权。路径计算：
```python
# main.py 在 Softwares/Rapid_8D/backend/ 下，需要 ×4 parent 到 VB 根
_CONTROL_DIR = str(Path(__file__).resolve().parent.parent.parent.parent / "Control platform")
```

## 启动方式

| 方式 | 命令 | 说明 |
|------|------|------|
| 无窗口启动 | 双击 `启动.vbs` | 推荐日常使用 |
| 调试启动 | 双击 `启动.bat` | 显示终端输出 |
| 仅后端 | `python -m backend.main` | 端口 8723 |
| 仅前端 | `cd frontend && npm run dev` | 端口 5173 |
| 控制中心 | 控制面板点击启动 | 通过 r8d_launcher.py |

## 关键文件

- `backend/config.yaml` — LLM 提供商 / API Key / 语言设置
- `backend/conversation/engine.py` — 对话引擎（prompt 构建、输出解析、上下文审查）
- `backend/conversation/prompts/*.md` — 每个阶段的 AI Prompt
- `frontend/src/stores/chat.ts` — 核心状态管理
- `frontend/src/i18n.ts` — 前端中英文
- `electron/main.js` — Electron 生命周期 + 进程管理

## 测试

运行: `python tests/test_parse_json.py`

覆盖 `_parse_output_json()` 和 `_parse_findings_json()` 两个关键方法。

---

*最后更新：2026-07-24*
