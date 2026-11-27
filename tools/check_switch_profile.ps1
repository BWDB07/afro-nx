param(
    [string]$LogDirectory = "$env:USERPROFILE\Desktop\logs"
)

$profile = Join-Path $LogDirectory 'rex\rex_profile.log'
$renut = Get-ChildItem $LogDirectory -Filter 'renut_*.log' -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not (Test-Path $profile) -or $null -eq $renut) {
    throw "No ReXGlue hardware log pair found under $LogDirectory"
}

$clockLines = Select-String -Path $profile -Pattern 'clocks: CPU ([0-9.]+) MHz, GPU ([0-9.]+) MHz, memory ([0-9.]+) MHz'
$lastClock = $clockLines | Select-Object -Last 1
$m = [regex]::Match($lastClock.Line, 'CPU ([0-9.]+) MHz, GPU ([0-9.]+) MHz, memory ([0-9.]+) MHz')
if (-not $m.Success) { throw "Could not parse clocks from $profile" }

$cpu = [double]$m.Groups[1].Value
$gpu = [double]$m.Groups[2].Value
$mem = [double]$m.Groups[3].Value
$stock = ($cpu -eq 1020.0 -and $gpu -eq 304.0 -and $mem -eq 1300.0)
$boost = Select-String -Path $renut.FullName -Pattern 'banjo_gpu_boost (ON|off)' |
    Select-Object -Last 1

Write-Output "log: $($renut.Name)"
Write-Output "clocks: CPU $cpu MHz, GPU $gpu MHz, memory $mem MHz"
Write-Output "stock_target: $stock"
if ($boost) { Write-Output "gpu_boost_line: $($boost.Line.Trim())" }

if (-not $stock) {
    Write-Warning 'This run is not valid stock handheld evidence; expected 1020/304/1300 MHz.'
    exit 2
}

$fps = Select-String -Path $renut.FullName -Pattern '10\.0 s: .*?\(([0-9.]+) fps\)'
if (-not $fps) { Write-Warning 'No ten-second FPS intervals found.'; exit 3 }
Write-Output 'stock FPS intervals:'
$fps | ForEach-Object { $_.Line.Trim() }
