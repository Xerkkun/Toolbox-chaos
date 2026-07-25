[CmdletBinding()]
param(
    [string]$ToolboxRoot = $env:TOOLBOX_CHAOS_ROOT,
    [string]$OutputDir,
    [switch]$CheckOnly,
    [switch]$AllowAppOnly
)

$common = Join-Path $PSScriptRoot "run_windows_common.ps1"
$profile = Join-Path $PSScriptRoot "windows-asus-tuf.json"
$parameters = @{
    MachineProfile = $profile
    CheckOnly = $CheckOnly
    AllowAppOnly = $AllowAppOnly
}
if ($ToolboxRoot) {
    $parameters.ToolboxRoot = $ToolboxRoot
}
if ($OutputDir) {
    $parameters.OutputDir = $OutputDir
}

& $common @parameters
exit $LASTEXITCODE
