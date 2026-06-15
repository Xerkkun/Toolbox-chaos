$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot
python scripts\prepare_runtime_resources.py
python scripts\verify_packaging.py
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    & scripts\build_windows.ps1
} else {
    Write-Host "Use scripts/build_macos.sh on macOS or scripts/build_linux.sh on Linux."
}
python scripts\bundle_size_report.py
