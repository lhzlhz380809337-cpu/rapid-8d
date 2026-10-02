$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = if ($env:R8D_PYTHON) {
    $env:R8D_PYTHON
} else {
    Join-Path $env:USERPROFILE '.rapid8d\venv\Scripts\python.exe'
}
$frontendRoot = Join-Path $projectRoot 'frontend'
if (-not (Test-Path -LiteralPath $pythonExe) -or -not (Test-Path -LiteralPath (Join-Path $frontendRoot 'node_modules\vite\bin\vite.js'))) {
    throw 'Install the external Python environment and frontend dependencies first. See README.md.'
}
$nodeExe = (Get-Command node.exe -ErrorAction Stop).Source
foreach ($port in @(18723,18080)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. This script will not stop another process."
    }
}
if (-not $env:R8D_ADMIN_PASSWORD) {
    $envFile = Join-Path $projectRoot '.env'
    if (Test-Path -LiteralPath $envFile) {
        $passwordSetting = Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^R8D_ADMIN_PASSWORD=' } | Select-Object -First 1
        if ($passwordSetting) {
            $env:R8D_ADMIN_PASSWORD = ($passwordSetting -split '=', 2)[1].Trim()
        }
    }
}
if (-not $env:R8D_ADMIN_PASSWORD) {
    throw 'Set R8D_ADMIN_PASSWORD in .env before starting the preview.'
}
$env:R8D_COOKIE_SECURE = 'false'
$env:R8D_ALLOWED_ORIGINS = 'http://127.0.0.1:18080,http://localhost:18080'
$logDir = Join-Path $projectRoot 'backend\data\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$apiProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','18723','--workers','1','--no-proxy-headers') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir 'api.out.log') -RedirectStandardError (Join-Path $logDir 'api.err.log')
$webProcess = Start-Process -FilePath $nodeExe -ArgumentList @('node_modules/vite/bin/vite.js','--configLoader','runner','--host','127.0.0.1','--port','18080','--strictPort') -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir 'web.out.log') -RedirectStandardError (Join-Path $logDir 'web.err.log')
Write-Host "API PID: $($apiProcess.Id); Web PID: $($webProcess.Id)"
Write-Host 'Local preview: http://127.0.0.1:18080. Logs: backend/data/logs.'
