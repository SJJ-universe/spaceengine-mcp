Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
function Capture-SE {
    param([string]$Name = "se_capture")
    $outDir = "C:\Users\SJ\Desktop\spaceengine-mcp\test_captures"
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
    $gfx = [System.Drawing.Graphics]::FromImage($bmp)
    $gfx.CopyFromScreen(0, 0, 0, 0, $bmp.Size)
    $path = Join-Path $outDir "${Name}.png"
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $gfx.Dispose(); $bmp.Dispose()
    return $path
}
Write-Host "Capture-SE function loaded"
