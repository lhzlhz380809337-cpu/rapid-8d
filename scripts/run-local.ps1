param([int]$Port = 18723)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonExe = if ($env:R8D_PYTHON) {
    $env:R8D_PYTHON
} else {
    Join-Path $env:USERPROFILE '.rapid8d\venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Create the external Python environment first, or set R8D_PYTHON. Default: %USERPROFILE%\.rapid8d\venv\Scripts\python.exe.'
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
    throw 'Set R8D_ADMIN_PASSWORD in .env before starting the local service.'
}
$env:R8D_COOKIE_SECURE = 'false'
$env:R8D_ALLOWED_ORIGINS = 'http://127.0.0.1:18080,http://localhost:18080'
& $pythonExe -m uvicorn backend.main:app --host 127.0.0.1 --port $Port --workers 1 --no-proxy-headers
