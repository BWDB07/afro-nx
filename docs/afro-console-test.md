# Afro Samurai Switch test build

The NRO uses the native deko3d renderer and Afro Samurai's generated ARM code. The original pixel shader is very slow on the console and stalls Ryujinx on a GPU fence while entering `combatintro`. The experimental shader guard crashes before gameplay on the console and is excluded from this handoff. The fast-draw executor reached 100 percent of measured draws with zero verifier differences on the tested route.

## Files and setup

- `AFRO-nx.nro` is the Switch build. `AFRO-nx.elf` is its matching symbol file. `deko3d_shaders.bin` is the matching local cache of 116 precompiled shader variants; copy it beside the NRO so the huge original pixel shaders need not compile during the run. `source.zip` includes the committed source and locally generated guest C++ for line mapping. Keep the ELF and archive together with `manifest.txt` when returning a profile; the archive and shader cache contain game-derived material and are for local use only.
- `renut.toml` is the diagnostic baseline with stack sampling and verification keys on. `renut_play.toml` disables diagnostics for normal play at 460.8 MHz; `renut_play_stock.toml` does the same at the stock GPU tier. `renut_ab.toml` alternates 30-second halves against a do-nothing deko3d control target. `renut_handheld_gpu_profile_304.toml` keeps the 720p picture, disables the GPU boost, and logs GPU time by pixel shader during manual gameplay. The 460.8 MHz profile remains available for a separate comparison. Copy a profile over `renut.toml` for its run.
- Put the NRO, `deko3d_shaders.bin` and a copy of `renut.toml` in the same application folder on the SD card. Place your own extracted disc files in `game_root/` beside them. The bundle does not contain the disc files. Preserve the `default.xex` and folder tree from extraction. No title update or DLC applies.
- The failed experimental guard shader is excluded. Do not copy an older `deko3d_glsl.bin` or `experimental_guard` folder into the application directory.
- `renut_capture_pool_ab.toml` is a separate stock-clock 30-second A/B for renderer capture reuse (target 5). It tests a CPU allocator-lock hotspot measured in Ryujinx. Use it only with the new NRO containing the capture-pool master-gate change; its result must be checked against the normal play config and console GPU profile.
- For the current target, use stock handheld CPU about 1020 MHz, GPU about 307.2 MHz, and memory about 1331 MHz. The requested 304 MHz denotes the stock GPU tier; use the actual logged clock. The default `renut.toml` and `renut_play.toml` still request 460.8 MHz and therefore are not stock-clock measurements. Emulator frame rates are only a proxy for console performance.

## What to collect

1. Launch and wait for the title screen, which appeared between about 75 and 200 seconds in Ryujinx runs. Press Start after the title appears, then try New Game and report the first scene that accepts movement or combat input. Record any missing image region or incorrect colors.
2. Copy the application's `logs/` folder and `logs/rex/rex_profile.log` if present. On Ryujinx, the sampler may instead write `sdmc:/switch/rex_profile.log`, one folder above the application.
3. State the build hash from `manifest.txt`, console clocks, elapsed time, and any scene reached. Keep the matching ELF: an older or newer ELF maps samples to the wrong functions.

The guard test is closed after its pre-gameplay console crash. Do not repeat it. Further console testing waits for a new candidate that has passed local boot and visual checks. The existing `renut_handheld_gpu_profile_304.toml` can profile the original shader, but the original is already measured at up to 354.671 ms/frame in the heavy scene.

`switch_profile_stacks = true` in `renut.toml` enables a stack report roughly every ten seconds. This is sampling for hot-function work, not the PGO instrumented session. No hand-written ARM function will be selected from PC or Ryujinx samples. PGO/LTO stays off until the user explicitly requests it.

## Current verification limits

The PC Xenos Vulkan build reaches visible first gameplay with enhancement masters off; its 195-second capture is the local reference. A 225-second PC check with isolated machine copies reached 679 of 799 and compared 132,657,147 calls with zero confirmed differences; the late capture was black, as in the baseline PC reference, so this is not a visual pass. Native D3D and PM4 callback hooks are active. The deko3d queue supplies 128 KiB scratch per warp, but the original large pixel shader stalls Ryujinx at the gameplay load. The experimental guard reached the tutorial in Ryujinx but crashed before gameplay on the console. Real console GPU profiles measured pixel shader `069459B4C78435DC` at 82.378 to 354.671 ms/frame in the heavy scene. PGO/LTO and hand-written natives remain off.
