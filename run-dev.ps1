<#
  Rapid 8D 开发启动器 —— 直接从源码运行，界面实时来自 ui/ 与 prompts/。

  改动后如何看到新界面：
    ui/*.js  ui/*.css  ui/*.html   → 在窗口里按 F5 刷新即可（每次请求都重新读盘）
    prompts/*.md                   → 同上，F5 刷新（下一轮分析生效）
    rapid8d/*.py  desktop_entry.py → 重新运行本脚本（会先停掉旧实例再启动）

  打包版 exe（release/Rapid8D/Rapid8D.exe）不会读取这些源码目录，
  改动看不到是正常的；只有 desktop/build.ps1 重新打包后才会反映。

  用法：
    .\run-dev.ps1                       # 启动（先停掉同一数据目录的旧实例）
    .\run-dev.ps1 -KeepRunning          # 已有实例时只打开窗口，不重启
    .\run-dev.ps1 -DataDir <路径>        # 换一个数据目录
    .\run-dev.ps1 -Python <python.exe>  # 指定解释器
#>
param(
    [string]$Python,
    [string]$DataDir,
    [int]$Port = 0,
    [switch]$KeepRunning,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath($PSScriptRoot)
Set-Location -LiteralPath $projectRoot

# 开发实例默认使用仓库内独立数据目录，避免与打包版共享 %LOCALAPPDATA%\Rapid8D：
# 两者的 session.json 分开，才不会误复用旧 exe 起的那个进程。
if (-not $DataDir) { $DataDir = Join-Path $projectRoot '.dev-data' }
$DataDir = [IO.Path]::GetFullPath($DataDir)
if (-not (Test-Path -LiteralPath $DataDir)) { New-Item -ItemType Directory -Path $DataDir -Force | Out-Null }

if (-not $Python) {
    $candidates = @(
        (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe')
    )
    $Python = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $Python -or -not (Test-Path -LiteralPath $Python)) {
    throw "找不到 Python 解释器。请用 -Python <python.exe 路径> 指定一个 Python 3.12。"
}

$entry = Join-Path $projectRoot 'desktop_entry.py'
if (-not (Test-Path -LiteralPath $entry)) { throw "缺少 desktop_entry.py：$entry" }

$sessionPath = Join-Path $DataDir 'session.json'

function Stop-DevInstance {
    if (-not (Test-Path -LiteralPath $sessionPath)) { return $false }
    $info = $null
    try { $info = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json } catch { return $false }
    if (-not $info.port) { return $false }
    $base = "http://127.0.0.1:$($info.port)"
    try {
        Invoke-RestMethod -Uri "$base/api/quit" -Method Post -TimeoutSec 5 `
            -Headers @{ 'X-Rapid-Token' = $info.token; 'Content-Type' = 'application/json' } -Body '{}' | Out-Null
    } catch {
        # 进程可能已不在；继续走下面的等待逻辑。
    }
    # 等服务真正退出，最多 15 秒。
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            Invoke-RestMethod -Uri "$base/health" -TimeoutSec 2 | Out-Null
        } catch {
            return $true
        }
    }
    Write-Warning "旧实例在 15 秒内没有退出；如果端口被占用，请手动结束它。"
    return $false
}

if (-not $KeepRunning) {
    if (Stop-DevInstance) { Write-Host "已停止旧实例，重新从源码启动。" }
} else {
    Write-Host "保留运行中的实例（-KeepRunning）；Python 代码改动不会生效。" -ForegroundColor Yellow
}

# 旧版 .xls 解析需要 xlrd；缺失时不影响启动和界面，仅该格式会报错。
# 用 find_spec 探测：不会抛异常，也就不会往 stderr 写内容——
# PowerShell 5.1 下重定向原生命令的 stderr 会抛 NativeCommandError。
$hasXlrd = & $Python -c "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec('xlrd') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "提示：未安装 xlrd，旧版 .xls 文件无法导入（DOCX/PDF/XLSX 不受影响）。" -ForegroundColor Yellow
    Write-Host "      需要时执行：& `"$Python`" -m pip install xlrd==2.0.2" -ForegroundColor Yellow
}

Write-Host "源码目录：$projectRoot"
Write-Host "数据目录：$DataDir"
Write-Host "界面来源：ui\ 与 prompts\（实时读盘，改完按 F5）"
Write-Host ""

$args = @($entry, '--data-dir', $DataDir)
if ($Port -ne 0) { $args += @('--port', $Port) }
if ($NoBrowser) { $args += '--no-browser' }

# 交棒给 Python 后不再用 Stop：服务自身的 stderr 输出不应中断脚本。
$ErrorActionPreference = 'Continue'
& $Python @args
exit $LASTEXITCODE
