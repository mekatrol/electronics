param(
    [string]$KiCadVersion = "10.0"
)

$PluginPath = Join-Path $HOME "Documents/KiCad/$KiCadVersion/scripting/plugins"
$PluginSource = Join-Path $PSScriptRoot "../plugins"

New-Item -ItemType Directory -Path $PluginPath -Force | Out-Null

function CopyToPluginsDirectory([string]$FileName) {
    $FullDstFileName = Join-Path -Path $PluginPath -ChildPath $FileName
    $FullSrcFileName = Join-Path -Path $PluginSource -ChildPath $FileName
    Copy-Item -Path $FullSrcFileName -Destination $FullDstFileName -Force
}

CopyToPluginsDirectory "KicadExtensions.py"
# CopyToPluginsDirectory "TriacFetLayoutPlugin.py"
CopyToPluginsDirectory "ExportDimensionsPlugin.py"
