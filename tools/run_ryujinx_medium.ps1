param(
  [Parameter(Mandatory=$true)][string]$Ryujinx,
  [Parameter(Mandatory=$true)][string]$DataRoot,
  [Parameter(Mandatory=$true)][string]$Nro
)
$shortcut = Join-Path $env:TEMP ("afro-ryujinx-" + [guid]::NewGuid().ToString() + ".lnk")
$wsh = New-Object -ComObject WScript.Shell
$link = $wsh.CreateShortcut($shortcut)
$link.TargetPath = $Ryujinx
$link.Arguments = "-r `"$DataRoot`" `"$Nro`""
$link.WorkingDirectory = Split-Path $Ryujinx
$link.Save()
Start-Process -FilePath "$env:WINDIR\explorer.exe" -ArgumentList $shortcut
Start-Sleep -Seconds 3
Remove-Item -LiteralPath $shortcut -Force -ErrorAction SilentlyContinue
