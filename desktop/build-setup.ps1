$ErrorActionPreference='Stop'
$rapidProject=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $rapidProject
$rapidPayload=Join-Path $rapidProject '.build\payload.zip'
$rapidSource=Join-Path $rapidProject 'release\Rapid8D'
if (-not (Test-Path -LiteralPath (Join-Path $rapidSource 'Rapid8D.exe'))) { throw 'Build desktop application first.' }
$rapidCompiler='C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$rapidPackagedLauncher=Join-Path $rapidSource 'Launch Rapid 8D.exe'
& $rapidCompiler /nologo /target:winexe /optimize+ "/out:$rapidPackagedLauncher" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll desktop\QuickLauncher.cs
if ($LASTEXITCODE -ne 0) { throw 'Packaged launcher build failed.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $rapidPayload) { Remove-Item -LiteralPath $rapidPayload }
[IO.Compression.ZipFile]::CreateFromDirectory($rapidSource,$rapidPayload,[IO.Compression.CompressionLevel]::Optimal,$false)
& $rapidCompiler /nologo /target:winexe /optimize+ /out:release\Rapid8D-Setup.exe /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.IO.Compression.dll /reference:System.IO.Compression.FileSystem.dll "/resource:$rapidPayload,rapid8d.payload" desktop\Setup.cs
if ($LASTEXITCODE -ne 0) { throw 'Setup build failed.' }
Get-Item -LiteralPath 'release\Rapid8D-Setup.exe' | Select-Object FullName,Length
