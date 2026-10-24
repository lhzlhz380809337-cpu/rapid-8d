$ErrorActionPreference = 'Stop'
$rapidProject = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$rapidCompiler = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$rapidOutput = Join-Path $rapidProject '启动 Rapid 8D.exe'
& $rapidCompiler /nologo /target:winexe /optimize+ "/out:$rapidOutput" /reference:System.Windows.Forms.dll (Join-Path $PSScriptRoot 'QuickLauncher.cs')
if ($LASTEXITCODE -ne 0) { throw 'Quick launcher build failed.' }
Get-Item -LiteralPath $rapidOutput | Select-Object FullName,Length
