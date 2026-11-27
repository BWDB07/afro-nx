param([string]$Output = 'out/console_package/AFRO-nx')

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $root
if ((Get-PSDrive C).Free -lt 1GB) { throw 'Less than 1 GB free on C:; package stopped.' }
if (@(git status --porcelain).Count -ne 0) { throw 'Commit source changes before packaging.' }

$glsl = Join-Path $root 'out/threshold_candidate/package/deko3d_glsl.bin'
$cache = Join-Path $root 'out/threshold_candidate/deko3d_shaders_full.bin'
if (!(Test-Path -LiteralPath $glsl) -or !(Test-Path -LiteralPath $cache)) {
    throw 'The locally generated threshold shader package or cache is missing.'
}
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'package_afro_switch.ps1') -Output $Output | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Base NRO/ELF/source package failed.' }

$base = Join-Path $root $Output
$dest = Join-Path $base 'experimental_threshold'
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $base 'AFRO-nx.nro') -Destination (Join-Path $dest 'AFRO-nx.nro') -Force
Copy-Item -LiteralPath $glsl -Destination (Join-Path $dest 'deko3d_glsl.bin') -Force
Copy-Item -LiteralPath $cache -Destination (Join-Path $dest 'deko3d_shaders.bin') -Force
Copy-Item -LiteralPath (Join-Path $root 'dist/switch/AFRO-nx/renut_visual_baseline.toml') -Destination (Join-Path $dest 'renut.toml') -Force
Copy-Item -LiteralPath (Join-Path $root 'dist/switch/AFRO-nx/renut_play_stock.toml') -Destination (Join-Path $dest 'renut_play_stock.toml') -Force
Copy-Item -LiteralPath (Join-Path $root 'dist/switch/AFRO-nx/renut_visual_probe.toml') -Destination (Join-Path $dest 'renut_visual_probe.toml') -Force
Copy-Item -LiteralPath (Join-Path $root 'dist/switch/AFRO-nx/renut_visual_baseline.toml') -Destination (Join-Path $dest 'renut_visual_baseline.toml') -Force
Copy-Item -LiteralPath (Join-Path $root 'dist/switch/AFRO-nx/renut_gpu_semantics_off_probe.toml') -Destination (Join-Path $dest 'renut_gpu_semantics_off_probe.toml') -Force
Copy-Item -LiteralPath (Join-Path $root 'docs/afro-threshold-console-test.md') -Destination (Join-Path $dest 'README_TESTING.md') -Force
Copy-Item -LiteralPath (Join-Path $root 'docs/afro-visual-probe.md') -Destination (Join-Path $dest 'README_VISUAL_PROBE.md') -Force
Copy-Item -LiteralPath (Join-Path $root 'docs/afro-gpu-semantics-off-test.md') -Destination (Join-Path $dest 'README_GPU_SEMANTICS_OFF.md') -Force

# Optional shader-only A/B: the two largest gameplay pixel-shader costs were
# optimized with safe GLSL passes. Keep it separate from the visual baseline.
$fastGlsl = Join-Path $root 'out/threshold_candidate/top_shader_package/deko3d_glsl.bin'
$fastCache = Join-Path $root 'out/threshold_candidate/top_shader_cache.bin'
if ((Test-Path -LiteralPath $fastGlsl) -and (Test-Path -LiteralPath $fastCache)) {
    $fast = Join-Path $base 'performance_top2'
    New-Item -ItemType Directory -Path $fast -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $dest 'AFRO-nx.nro') -Destination (Join-Path $fast 'AFRO-nx.nro') -Force
    Copy-Item -LiteralPath $fastGlsl -Destination (Join-Path $fast 'deko3d_glsl.bin') -Force
    Copy-Item -LiteralPath $fastCache -Destination (Join-Path $fast 'deko3d_shaders.bin') -Force
    Copy-Item -LiteralPath (Join-Path $dest 'renut.toml') -Destination (Join-Path $fast 'renut.toml') -Force
    Copy-Item -LiteralPath (Join-Path $root 'docs/afro-top2-console-test.md') -Destination (Join-Path $fast 'README_TESTING.md') -Force
    $fastManifest = @("commit=$((git rev-parse HEAD).Trim())", 'status=REJECTED on Switch: black textures in renut_025; restore experimental_threshold files')
    foreach ($name in @('AFRO-nx.nro', 'deko3d_glsl.bin', 'deko3d_shaders.bin', 'renut.toml')) {
        $fastManifest += "$($name)_sha256=$((Get-FileHash -LiteralPath (Join-Path $fast $name) -Algorithm SHA256).Hash)"
    }
    [System.IO.File]::WriteAllLines((Join-Path $fast 'manifest.txt'), $fastManifest)
}

$manifest = @("commit=$((git rev-parse HEAD).Trim())", 'status=Switch gameplay visuals restored with non-CPU enhancements off; 30 FPS is not stable in heavy scenes')
foreach ($name in @('AFRO-nx.nro', 'deko3d_glsl.bin', 'deko3d_shaders.bin', 'renut.toml')) {
    $manifest += "$($name)_sha256=$((Get-FileHash -LiteralPath (Join-Path $dest $name) -Algorithm SHA256).Hash)"
}
[System.IO.File]::WriteAllLines((Join-Path $dest 'manifest.txt'), $manifest)
Get-ChildItem -LiteralPath $dest -File | Select-Object Name,Length
