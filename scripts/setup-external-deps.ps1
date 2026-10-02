param(
    [string]$RuntimeRoot = (Join-Path $env:USERPROFILE '.rapid8d')
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $RuntimeRoot 'venv'
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'
$projectNodeModules = Join-Path $projectRoot 'frontend\node_modules'
$externalNodeModules = Join-Path $RuntimeRoot 'frontend\node_modules'
$npmCache = Join-Path $RuntimeRoot 'npm-cache'

New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null

if (-not (Test-Path -LiteralPath $pythonExe)) {
    $py = Get-Command py.exe -ErrorAction Stop
    & $py.Source -3.12 -m venv $venvPath
}
& $pythonExe -m pip install -r (Join-Path $projectRoot 'requirements.txt')

if (-not (Test-Path -LiteralPath $externalNodeModules)) {
    if (Test-Path -LiteralPath $projectNodeModules) {
        $existing = Get-Item -LiteralPath $projectNodeModules
        if (-not $existing.LinkType) {
            throw 'frontend\node_modules already exists. Confirm it has no required content before removing it and retrying.'
        }
    }
    Push-Location (Join-Path $projectRoot 'frontend')
    try {
        npm ci --cache $npmCache --no-audit
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $externalNodeModules) | Out-Null
        Move-Item -LiteralPath $projectNodeModules -Destination $externalNodeModules
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $projectNodeModules)) {
    New-Item -ItemType Junction -Path $projectNodeModules -Target $externalNodeModules | Out-Null
}

Write-Host "Python environment: $venvPath"
Write-Host "Frontend dependencies: $externalNodeModules"
