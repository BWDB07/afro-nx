param(
    [string]$Output = 'out/console_package/AFRO-nx'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $root
$free = (Get-PSDrive C).Free
if ($free -lt 1GB) { throw 'Less than 1 GB free on C:; package stopped without deleting files.' }
$dirty = @(git status --porcelain)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) { throw 'Commit source changes before packaging an ELF/source pair.' }
$hash = (git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Could not read commit hash.' }
$nro = Join-Path $root 'app/out/switch-native/renut.nro'
$elf = Join-Path $root 'app/out/switch-native/renut'
if (!(Test-Path -LiteralPath $nro) -or !(Test-Path -LiteralPath $elf)) { throw 'Matching Switch NRO/ELF missing.' }
$shaderCache = Join-Path $root 'out/deko3d_shaders/afro_raw_generic_shaders.bin'
if (!(Test-Path -LiteralPath $shaderCache)) { throw 'Original-shader DKSH cache missing; package stopped.' }
$dest = Join-Path $root $Output
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$destFull = [System.IO.Path]::GetFullPath($dest).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
foreach ($name in @('experimental_guard', 'experimental_guard_ready')) {
    $oldDir = [System.IO.Path]::GetFullPath((Join-Path $destFull $name))
    if (!$oldDir.StartsWith($destFull + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a folder outside the package: $oldDir"
    }
    if (Test-Path -LiteralPath $oldDir -PathType Container) {
        Remove-Item -LiteralPath $oldDir -Recurse -Force
    }
}
# Older generated test configs in this output folder use scripted input timings
# or an unvalidated resolution ladder. Keep them out of the console handoff.
$oldProfiles = @(
    'renut_handheld_30fps.toml', 'renut_handheld_360p.toml',
    'renut_handheld_extreme_30fps.toml', 'renut_handheld_performance.toml',
    'renut_handheld_stock_interactive_30fps.toml',
    'renut_static_360p_startspam.toml', 'renut_timed_360p.toml',
    'renut_timed_bounded_360p.toml', 'renut_timed_gameplay_360p.toml',
    'renut_timed_late_360p.toml', 'renut_timed_robust_360p.toml',
    'renut_timed_startspam_360p.toml',
    'renut_timed_startspam_dynamic_30fps.toml',
    'renut_timed_startspam_extreme_30fps.toml'
)
foreach ($name in $oldProfiles) {
    $old = Join-Path $dest $name
    if (Test-Path -LiteralPath $old -PathType Leaf) {
        Remove-Item -LiteralPath $old -Force
    }
}
$oldGlsl = Join-Path $dest 'deko3d_glsl.bin'
if (Test-Path -LiteralPath $oldGlsl -PathType Leaf) {
    Remove-Item -LiteralPath $oldGlsl -Force
}
Copy-Item -LiteralPath $nro -Destination (Join-Path $dest 'AFRO-nx.nro') -Force
Copy-Item -LiteralPath $elf -Destination (Join-Path $dest 'AFRO-nx.elf') -Force
Copy-Item -LiteralPath $shaderCache -Destination (Join-Path $dest 'deko3d_shaders.bin') -Force
foreach ($name in @('renut.toml','renut_play.toml','renut_play_stock.toml','renut_ab.toml',
                   'renut_handheld_gpu_profile_304.toml',
                   'renut_handheld_gpu_profile_460.toml',
                   'renut_capture_pool_ab.toml',
                   'renut_handheld_boosted_interactive_30fps.toml')) {
    Copy-Item -LiteralPath (Join-Path $root "dist/switch/AFRO-nx/$name") -Destination (Join-Path $dest $name) -Force
}
Copy-Item -LiteralPath (Join-Path $root 'docs/afro-console-test.md') -Destination (Join-Path $dest 'README_TESTING.md') -Force
$snapshot = Join-Path $dest 'source.zip'
& git archive --format=zip --output=$snapshot HEAD
if ($LASTEXITCODE -ne 0) { throw 'Source snapshot failed.' }
# The generated guest C++ is intentionally ignored by Git, but its line numbers
# are needed to interpret the matching ELF's sampled addresses.
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$generated = Join-Path $root 'app/generated'
$archive = [System.IO.Compression.ZipFile]::Open($snapshot, [System.IO.Compression.ZipArchiveMode]::Update)
try {
    foreach ($file in Get-ChildItem -LiteralPath $generated -File -Recurse) {
        $relative = $file.FullName.Substring($generated.Length + 1).Replace('\', '/')
        $entry = "app/generated/$relative"
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $file.FullName, $entry, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
} finally {
    $archive.Dispose()
}
$nroHash = (Get-FileHash -LiteralPath (Join-Path $dest 'AFRO-nx.nro') -Algorithm SHA256).Hash
$elfHash = (Get-FileHash -LiteralPath (Join-Path $dest 'AFRO-nx.elf') -Algorithm SHA256).Hash
$shaderHash = (Get-FileHash -LiteralPath (Join-Path $dest 'deko3d_shaders.bin') -Algorithm SHA256).Hash
$manifest = @(
    "commit=$hash"
    "nro_sha256=$nroHash"
    "elf_sha256=$elfHash"
    "deko3d_shaders_sha256=$shaderHash"
    'status=original shader is very slow on console; experimental guard crashes before gameplay on current console test and is not a boot fix'
    'game_data=not included; local extracted disc files stay outside Git'
    'source_zip=committed source plus locally generated guest C++ (not committed)'
)
[System.IO.File]::WriteAllLines((Join-Path $dest 'manifest.txt'), $manifest)
Get-ChildItem -LiteralPath $dest | Select-Object Name,Length
