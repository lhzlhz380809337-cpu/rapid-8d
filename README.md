# Rapid 8D 0.3 — 部署试用候选版

目标：低成本邀请试用的 AI 辅助 8D 报告工具，兼容桌面和手机浏览器，并提供 Capacitor iOS / Android 工程骨架。

**这不是已发布的商店应用。** 当前没有购买云资源、调用付费模型或公开部署。团队协作、订阅支付、商店签名及备案资料仍需后续完成。经营及软件权属由运营者自行确认后再公开发布。

## 已实现

- 独立登录，不依赖外部 Control platform；管理员初始密码由本机 `.env` 配置。
- 管理员创建试用账号，普通用户独立项目、附件及导出目录。
- HttpOnly 会话、密码哈希、登录尝试限制、退出与修改密码撤销会话、普通用户自助删除账号。
- D1–D8 手动填写和保存；没有模型密钥时可使用手动流程。
- AI 服务授权、每日个人/全站及每月全站请求额度；模型服务变更时重新授权。
- 文档上传大小/容量限制；Markdown 内容过滤；报告 HTML 去除脚本、远程资源并隔离预览。
- Word、HTML 及 PDF 导出；缺少 Pango 时 PDF 自动使用文字排版回退。
- 原子文件写入、单工作进程按账号串行处理，修复快速切换步骤时的自动保存错写。
- Docker Compose、可选 Caddy HTTPS、健康检查、持久化卷、备份与校验恢复工具。

## 本地运行（Windows）

建议 Python 3.12、Node.js 22.12 或更高。运行命令前进入本项目目录。默认依赖安装在 `%USERPROFILE%\.rapid8d`，不占用项目源码目录。

```powershell
PowerShell -ExecutionPolicy Bypass -File scripts\setup-external-deps.ps1
powershell -ExecutionPolicy Bypass -File scripts\run-local.ps1
```

启动过程不需要输入密码；先复制 `.env.example` 为 `.env` 并填写管理员密码，另开终端：

```powershell
cd frontend
npm run dev
```

浏览器打开 `http://127.0.0.1:18080`，默认管理员用户名为 `admin`，密码使用 `.env` 中的 `R8D_ADMIN_PASSWORD`。

账号保存在数据目录中的 SQLite 数据库。环境变量中的初始管理员密码不会覆盖已有账号；可在账号页面修改密码。

`.env` 由 Docker Compose 使用。本地脚本不会自动读取 `.env`；本地测试 AI 时需在后端进程环境设置 `R8D_API_KEY`、`R8D_API_BASE`、`R8D_API_MODEL`、`R8D_AI_SERVICE_NAME`。

旧版 `backend/config.yaml` 曾保存过明文模型密钥。仓库中的值已经清除，但密钥本身必须到原模型服务平台撤销并重新生成；新密钥只通过环境变量或服务器密钥管理服务注入。

## Docker 本地验收

1. 复制 `.env.example` 为 `.env`，设置强管理员密码。模型配置可以先空着。
2. 执行 `docker compose up -d --build`。
3. 打开 `http://127.0.0.1:8080`；登录后在“账号”页创建试用账号。
4. 执行 `docker compose ps` 和 `docker compose logs --tail=100 api` 检查健康状态。

数据位于 `rapid8d-data` 命名卷；更换镜像不会删除数据。**不要使用 `docker compose down -v`，该参数会删除数据卷。**

## 公网部署前

- 在运营条件确认后配置域名、备案、运营主体、隐私政策、用户协议、客服方式及真实 AI 服务信息。
- `.env` 设置 `R8D_DOMAIN=你的域名`、`R8D_COOKIE_SECURE=true`、`R8D_ALLOWED_ORIGINS=https://你的域名`。
- DNS 指向服务器，允许 80/443；执行 `docker compose --profile public up -d --build`。Caddy 自动申请证书。
- 仅反向代理对外开放；后端 8723 不映射宿主机端口，8080 默认只绑定回环地址。
- AI 密钥通过环境注入，先在模型平台设置金额预算/余额提醒。应用配额计量的是**请求次数，不是人民币金额**，不能单独保证每月费用。
- 用两个账号实际检查隔离、上传、导出、退出、恢复备份；填好服务名称后让用户确认 AI 数据授权。
- 当前为邀请试用：最多 100 个账号、每账号 50 个项目，默认附件及项目容量检查阈值 100 MB。不是大规模公开注册服务。

当前数据结构保留 JSON 项目文件以兼容原项目，账号/会话/额度使用 SQLite。**必须单副本、单 Uvicorn worker 运行**，禁止直接增加 worker 或多实例共用目录。团队并发编辑版本需进一步迁移为事务化项目存储。

## 备份与恢复

停止 API 后执行备份，避免项目文件和账号库处于不同时间点。不要把备份放在数据目录里面。

```powershell
python scripts/backup.py backup backend/data backups/rapid8d-日期.zip
python scripts/backup.py restore restored-data backups/rapid8d-日期.zip
```

恢复工具校验 SHA-256，并拒绝覆盖非空目录。恢复验收后将 `R8D_DATA_DIR` 指向恢复目录再启动。Docker 使用同一工具时，可将脚本挂载进停止业务写入的维护容器；或停 API 后从卷完整复制数据到本地再备份。建议保留 7 天备份，定期人工验证恢复，备份包含密钥配置和用户资料，应限制访问。

账号删除会删除在线数据及会话；备份按保留期限清理。恢复旧备份可能恢复已删除账号，恢复后必须先核对并处理删除记录，再开放服务。

旧版 `backend/data/projects`、`backend/data/shared` 和原始 `backend/config.yaml` **不会自动分配给新账号或上传到服务器**。如要迁移，先备份，再确认项目所属用户后离线复制到对应账号目录。容器镜像排除原始数据、密钥配置及旧术语资料。

## iOS / Android

已提供 `frontend/capacitor.config.ts`，并保留 `frontend/android` 和 `frontend/ios` 原生工程；后续的应用 ID、权限、图标和签名配置需要随工程版本化。首次重新生成时可执行：

```powershell
cd frontend
npm run build
npx cap add android
npx cap add ios
npm run mobile:sync
```

已有目录时跳过 `cap add`。后续用 Android Studio / Xcode 打开工程，设置正式应用 ID、图标、签名和后端地址。

**原生包目前是工程骨架，未验收原生环境的账号会话、上传、下载及系统分享。** 当前 cookie 方案按同源网页版设计；不能只填写跨域 API 地址就假定 iOS WebView 会话正常。正式移动版需完成原生安全会话/凭据存储方案、设备测试、权限说明、隐私材料和商店审核，当前不提供已签名 APK/IPA。

## 报告与 AI 的已知边界

- AI 测试采用模拟模型，没有使用原配置中的密钥，真实模型响应质量、延迟和费用需运营者选定服务后验收。
- 页面步骤中的 Mermaid 图表可渲染；导出报告按安全静态文档处理，禁止模型提供的脚本。鱼骨 JSON 转为根因表格，其他 Mermaid 在报告导出中可能以源文本呈现。
- Word/PDF 基于确认的各阶段内容生成；AI 整篇报告提供单独的 HTML 保存/下载，尚未将其任意 HTML 精确转换为 Word。
- 首版只保留文字与附件输入，并通过云端 API 提供 AI 辅助；本地大模型、语音转写、RAG 和 Electron 桌面端已经移除。
- 当前仅添加了 AI 辅助标识和数据授权流程，不能代替正式发布所需的全部标识规范、隐私政策与备案验收。

## 验证

```powershell
& "$env:USERPROFILE\.rapid8d\venv\Scripts\python.exe" -m pip install pytest
& "$env:USERPROFILE\.rapid8d\venv\Scripts\python.exe" -m pytest tests -q
cd frontend
npm run build
```

测试结果及尚未完成的环境验收见 `RELEASE_STATUS.md`。

正式发布材料草案：

- [`docs/PRIVACY_POLICY_DRAFT.md`](docs/PRIVACY_POLICY_DRAFT.md)：隐私政策草案。
- [`docs/USER_AGREEMENT_DRAFT.md`](docs/USER_AGREEMENT_DRAFT.md)：用户协议草案。
- [`docs/STORE_SUBMISSION_CHECKLIST.md`](docs/STORE_SUBMISSION_CHECKLIST.md)：中国大陆应用商店提交清单。

所有方括号内容必须按实际运营信息补齐后才能发布。
