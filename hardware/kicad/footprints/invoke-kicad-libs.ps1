# Shared implementation for the setup and teardown PowerShell entry points.
function Invoke-KiCadLibraries {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('setup', 'teardown')]
        [string]$Mode,
        [Parameter(Mandatory = $true)]
        [string]$LibraryRoot,
        [string]$ConfigDir,
        [string]$KiCadVersion = '10.0',
        [switch]$DryRun
    )

    if ([string]::IsNullOrWhiteSpace($ConfigDir)) {
        if ([string]::IsNullOrWhiteSpace($env:APPDATA)) {
            throw 'APPDATA is unavailable. Supply -ConfigDir with the KiCad configuration directory.'
        }
        $ConfigDir = Join-Path (Join-Path $env:APPDATA 'kicad') $KiCadVersion
    }

    # Prefer the Windows Python launcher, then PATH installations.
    $pythonCommand = $null
    $pythonPrefix = @()
    foreach ($candidate in @('py', 'python', 'python3')) {
        $command = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $command) { continue }
        $prefix = @()
        if ($candidate -eq 'py') { $prefix = @('-3') }
        try {
            & $command.Source @prefix -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $pythonCommand = $command.Source
                $pythonPrefix = $prefix
                break
            }
        } catch {
            # Try the next executable if this launcher cannot start Python.
        }
    }
    if ($null -eq $pythonCommand) {
        throw 'Python 3.9 or newer was not found. Install Python and enable its launcher or add it to PATH.'
    }

    $scriptArgs = @(
        (Join-Path $LibraryRoot 'kicad-libs.py'),
        $Mode,
        $LibraryRoot,
        '--config-dir', $ConfigDir
    )
    if ($DryRun) { $scriptArgs += '--dry-run' }
    & $pythonCommand @pythonPrefix @scriptArgs
    # Propagate the backend exit status to the entry point and its caller.
    $global:LASTEXITCODE = $LASTEXITCODE
}
