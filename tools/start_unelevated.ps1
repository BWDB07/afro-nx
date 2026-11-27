# Start a process with the existing desktop Explorer token. No account or system settings are changed.
param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [string]$Arguments = '',
    [string]$WorkingDirectory = '',
    [switch]$Hidden
)

Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

public static class UserProcess {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct StartupInfo {
        public int cb;
        public string reserved;
        public string desktop;
        public string title;
        public int x, y, xSize, ySize, xCountChars, yCountChars, fillAttribute, flags;
        public short showWindow, reserved2;
        public IntPtr reservedBytes, stdInput, stdOutput, stdError;
    }
    [StructLayout(LayoutKind.Sequential)]
    public struct ProcessInfo {
        public IntPtr process, thread;
        public uint processId, threadId;
    }
    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool DuplicateTokenEx(IntPtr token, uint desiredAccess, IntPtr attributes,
        int impersonationLevel, int tokenType, out IntPtr duplicate);
    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool GetTokenInformation(IntPtr token, int tokenInformationClass,
        out int information, int informationLength, out int returnLength);
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CreateProcessWithTokenW(IntPtr token, uint logonFlags, string application,
        StringBuilder commandLine, uint creationFlags, IntPtr environment, string currentDirectory,
        ref StartupInfo startup, out ProcessInfo info);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GetExitCodeProcess(IntPtr handle, out uint code);
    public static void Fail(string step) {
        throw new Win32Exception(Marshal.GetLastWin32Error(), step);
    }
}
'@

$desktop = Get-Process explorer -ErrorAction Stop | Where-Object { $_.SessionId -eq (Get-Process -Id $PID).SessionId } | Select-Object -First 1
if (-not $desktop) { throw 'No Explorer process in this session' }
$token = [IntPtr]::Zero
if (-not [UserProcess]::OpenProcessToken($desktop.Handle, 0x0B, [ref]$token)) { [UserProcess]::Fail('OpenProcessToken') }
try {
    $elevation = 1
    $returned = 0
    if (-not [UserProcess]::GetTokenInformation($token, 20, [ref]$elevation, 4, [ref]$returned)) {
        [UserProcess]::Fail('GetTokenInformation(TokenElevation)')
    }
    if ($elevation -ne 0) { throw 'Explorer token is elevated; refusing to launch' }
    $primary = [IntPtr]::Zero
    if (-not [UserProcess]::DuplicateTokenEx($token, 0xF01FF, [IntPtr]::Zero, 2, 1, [ref]$primary)) {
        throw "DuplicateTokenEx failed: Win32 error $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    try {
    $startup = New-Object UserProcess+StartupInfo
    $startup.cb = [Runtime.InteropServices.Marshal]::SizeOf([type][UserProcess+StartupInfo])
    if ($Hidden) { $startup.flags = 1; $startup.showWindow = 0 }
    $info = New-Object UserProcess+ProcessInfo
    $command = New-Object System.Text.StringBuilder(('"' + $FilePath + '" ' + $Arguments))
    if (-not $WorkingDirectory) { $WorkingDirectory = Split-Path -Parent $FilePath }
    if (-not [UserProcess]::CreateProcessWithTokenW($primary, 0, $FilePath, $command, 0, [IntPtr]::Zero,
        $WorkingDirectory, [ref]$startup, [ref]$info)) {
        $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
        throw "CreateProcessWithTokenW failed: Win32 error $code"
    }
    [UserProcess]::CloseHandle($info.thread) | Out-Null
    if ([UserProcess]::WaitForSingleObject($info.process, 2000) -eq 0) {
        $exitCode = [uint32]0
        [UserProcess]::GetExitCodeProcess($info.process, [ref]$exitCode) | Out-Null
        [Console]::Error.WriteLine("Started process exited immediately: 0x{0:X8}", $exitCode)
    }
    [UserProcess]::CloseHandle($info.process) | Out-Null
    Write-Output $info.processId
    } finally { [UserProcess]::CloseHandle($primary) | Out-Null }
}
finally { [UserProcess]::CloseHandle($token) | Out-Null }
