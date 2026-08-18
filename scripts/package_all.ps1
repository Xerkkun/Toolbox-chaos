$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repoRoot

function Invoke-CheckedPython {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

Invoke-CheckedPython -Arguments @("scripts\prepare_runtime_resources.py")
Invoke-CheckedPython -Arguments @("scripts\verify_packaging.py")
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    & scripts\build_windows.ps1
    if (-not $?) {
        throw "Windows packaging failed."
    }
} else {
    Write-Host "Use scripts/build_macos.sh on macOS or scripts/build_linux.sh on Linux."
}
Invoke-CheckedPython -Arguments @("scripts\bundle_size_report.py")
