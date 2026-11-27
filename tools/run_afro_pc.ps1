param([int]$Seconds = 90, [string]$Name = 'baseline', [string]$InputScript = '',
      [ValidateSet('vulkan','d3d12')][string]$Backend = 'vulkan', [switch]$EnhancementsOff,
      [switch]$CpuOff, [switch]$NonCpuOff, [switch]$Visible, [string]$ExtraArgs = '')
$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root 'app/out/pc/renut.exe'
$game = Join-Path (Split-Path -Parent $root) 'game'
$run = Join-Path $root "out/pc_runs/$Name"
$user = Join-Path $run 'user'
$log = Join-Path $run 'renut.log'
if (-not (Test-Path -LiteralPath $exe) -or -not (Test-Path -LiteralPath (Join-Path $game 'default.xex'))) {
    throw 'PC executable or extracted game is missing'
}
New-Item -ItemType Directory -Path $user -Force | Out-Null
$args = '--game_data_root="{0}" --user_data_root="{1}" --gpu_plugin=xenos --gpu_backend={2} --nfsmw_captura_cada_s=15 --nfsmw_captura_max=40 --log_file="{3}" --log_file_writer=false --window_start_minimized=false --fullscreen=false' -f $game, $user, $Backend, $log
if ($InputScript) { $args += ' --input_script="{0}"' -f $InputScript }
if ($EnhancementsOff -or $CpuOff) { $args += ' --banjo_cpu_enhancements=false' }
if ($EnhancementsOff -or $NonCpuOff) { $args += ' --banjo_noncpu_enhancements=false' }
if ($ExtraArgs) { $args += ' ' + $ExtraArgs }
$style = if ($Visible) { 'Normal' } else { 'Hidden' }
$p = Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory (Split-Path -Parent $exe) -WindowStyle $style -PassThru `
    -RedirectStandardOutput (Join-Path $run 'stdout.txt') -RedirectStandardError (Join-Path $run 'stderr.txt')
Write-Output "Started Afro PC pid $($p.Id) with game $game"
$deadline = (Get-Date).AddSeconds($Seconds)
while ((Get-Date) -lt $deadline -and -not $p.HasExited) { Start-Sleep -Seconds 2 }
$p.Refresh()
if (-not $p.HasExited) {
    Stop-Process -Id $p.Id -Force
    Write-Output "Stopped only this run's pid $($p.Id) after $Seconds s"
} else {
    $p.WaitForExit()
    $p.Refresh()
    Write-Output "Afro PC exited code $($p.ExitCode)"
}
Get-ChildItem -LiteralPath (Join-Path (Split-Path -Parent $exe) 'capturas') -Filter '*.png' -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt $p.StartTime } | Move-Item -Destination $run -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $run -Recurse -File | Select-Object FullName,Length
