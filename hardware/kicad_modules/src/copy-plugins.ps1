$UserName = $env:UserName
$PluginPath = "C:/Users/$UserName/Documents/KiCad/6.0/scripting/plugins"

function CopyToPluginsDirectory([string]$FileName) {
    $FullDstFileName = Join-Path -Path $PluginPath -ChildPath $FileName
    $FullSrcFileName = Join-Path -Path "./src/plugins" -ChildPath $FileName
    Copy-Item -Path $FullSrcFileName -Destination $FullDstFileName -Force
}

CopyToPluginsDirectory(@( "KicadExtensions.py" ))
# CopyPlugins(@( "TriacFetLayoutPlugin.py" ))
CopyToPluginsDirectory(@( "ExportDimensionsPlugin.py" ))