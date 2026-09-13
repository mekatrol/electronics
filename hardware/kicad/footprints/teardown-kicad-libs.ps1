# Requires Python 3.9+ and Windows PowerShell 5.1 or PowerShell 7+.
[CmdletBinding()]
param(
    [string]$ConfigDir,
    [string]$KiCadVersion = '10.0',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'invoke-kicad-libs.ps1')
Invoke-KiCadLibraries -Mode teardown -LibraryRoot $PSScriptRoot -ConfigDir $ConfigDir -KiCadVersion $KiCadVersion -DryRun:$DryRun
exit $LASTEXITCODE
