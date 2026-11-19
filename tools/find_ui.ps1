param(
    [int]$X0 = 0,
    [int]$X1 = 1920,
    [int]$Y0 = 0,
    [int]$Y1 = 1080,
    [string]$Mode = "red"
)

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

Write-Output "SCREEN $($bounds.Width)x$($bounds.Height)"

$hits = @{}
for ($y = $Y0; $y -lt $Y1; $y++) {
    for ($x = $X0; $x -lt $X1; $x++) {
        $c = $bmp.GetPixel($x, $y)
        $match = $false
        switch ($Mode) {
            "red"   { $match = ($c.R -gt 130 -and $c.G -lt 100 -and $c.B -lt 100) }
            "green" { $match = ($c.R -lt 110 -and $c.G -gt 110 -and $c.B -lt 110) }
            "yellow"{ $match = ($c.R -gt 180 -and $c.G -gt 170 -and $c.B -lt 140) }
            "blue"  { $match = ($c.R -lt 110 -and $c.G -lt 110 -and $c.B -gt 140) }
            "dark"  { $match = ($c.R -lt 90 -and $c.G -lt 90 -and $c.B -lt 90) }
            default { $match = $false }
        }
        if ($match) {
            if (-not $hits.ContainsKey($x)) { $hits[$x] = @() }
            $hits[$x] += $y
        }
    }
}

$xs = $hits.Keys | Sort-Object
if ($xs.Count -eq 0) {
    Write-Output "NOMATCH"
    exit
}

# group contiguous x runs
$runs = @()
$start = $null
$prev = $null
foreach ($x in $xs) {
    if ($null -eq $start) { $start = $x; $prev = $x; continue }
    if ($x -le $prev + 2) { $prev = $x; continue }
    $runs += ,@($start, $prev)
    $start = $x
    $prev = $x
}
if ($null -ne $start) { $runs += ,@($start, $prev) }

foreach ($r in $runs) {
    $a = $r[0]; $b = $r[1]
    $ys = @()
    foreach ($x in $hits.Keys) { if ($x -ge $a -and $x -le $b) { $ys += $hits[$x] } }
    $ymin = ($ys | Measure-Object -Minimum).Minimum
    $ymax = ($ys | Measure-Object -Maximum).Maximum
    $w = $b - $a + 1
    $cx = [int](($a + $b) / 2)
    $cy = [int](($ymin + $ymax) / 2)
    $canvasX = [int]($cx * 0.75833)
    $canvasY = [int](10 + $cy * 0.75833)
    Write-Output ("run x={0}..{1} (w={2}) y={3}..{4} center_phys=({5},{6}) canvas=({7},{8})" -f $a, $b, $w, $ymin, $ymax, $cx, $cy, $canvasX, $canvasY)
}

$bmp.Dispose()
$g.Dispose()
