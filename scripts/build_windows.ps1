$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot
python scripts\prepare_runtime_resources.py
python scripts\verify_packaging.py
& packaging\windows\build.ps1
