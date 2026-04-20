param(
    [switch]$InstallDependencies
)

$ErrorActionPreference = "Stop"
$RepoScript = Resolve-Path (Join-Path $PSScriptRoot "..\..\scripts\build\build_exe.ps1")

if ($InstallDependencies) {
    & $RepoScript -InstallDependencies
} else {
    & $RepoScript
}
