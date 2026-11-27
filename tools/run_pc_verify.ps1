# Afro Samurai: verify machine copies against the generated functions on every comparable call,
# while the broad CPU master and its unrelated kernel/graphics changes stay off.
#   powershell -File tools/run_pc_verify.ps1 [-Seconds 300] [-Name verify1] [-Every 15] [-Script "20:START,24:A"] [-Sticks 240]
param([int]$Seconds = 300, [string]$Name = "verify1", [int]$Every = 15, [string]$Script = "", [int]$Sticks = 0)
$root = Split-Path -Parent $PSScriptRoot
$extra = "--banjo_cpu_enhancements=false --afro_cpu_native_only=true --banjo_cpu_native_bulk=true " +
         "--banjo_cpu_verify=true --banjo_hot_guard_calls=4000 --banjo_hot_guard_period=1"
if ($Script -ne "") { $extra += " --input_script=$Script" }
if ($Sticks -gt 0) { $extra += " --input_script_sticks=$Sticks" }
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "tools\run_pc.ps1") -Seconds $Seconds -Name $Name -Every $Every -Visible -Extra $extra
