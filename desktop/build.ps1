param(
    [string]$Python = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath $Python)) { throw 'Supply -Python with a Python 3.12 executable.' }
$env:PYTHONPATH = Join-Path $projectRoot '.build-deps'
& $Python -m unittest discover -s desktop_tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $Python -m PyInstaller --noconfirm --onedir --windowed --name Rapid8D --distpath release --workpath .build --specpath desktop --add-data "$projectRoot\ui;ui" --add-data "$projectRoot\prompts;prompts" --hidden-import xlrd --exclude-module numpy --exclude-module pandas --exclude-module scipy --exclude-module matplotlib --exclude-module tkinter --exclude-module IPython --exclude-module notebook --exclude-module pytest --exclude-module cv2 --exclude-module torch --exclude-module cryptography --exclude-module pdfplumber --exclude-module pdfminer desktop_entry.py
if ($LASTEXITCODE -ne 0) { throw 'Desktop build failed.' }
Write-Host 'Portable application ready: release\Rapid8D\Rapid8D.exe'
