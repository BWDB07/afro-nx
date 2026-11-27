# Afro Samurai threshold shader candidate

This is an **experimental** deko3d shader candidate. The previous ordered-guard shader crashed before gameplay on the Switch and is excluded. This candidate uses a different control-flow form. It ran for 240 seconds in Ryujinx and reached combat. Console run renut_020 reached gameplay but had a missing loading image and very dark surfaces. Runs renut_023 and renut_024 restored the picture with non-CPU enhancements off; this is now the package's default `renut.toml`. Run 024 includes both near-30 FPS intervals and heavy intervals down to 21.11 FPS, so stable 30 FPS is not yet reached.

## Install for one console test

Copy these four files from `experimental_threshold/` together to `sd:/switch/AFRO-nx/`, replacing the matching names: `AFRO-nx.nro`, `deko3d_glsl.bin`, `deko3d_shaders.bin`, and `renut.toml`. Keep your existing `game_root/` and save data. Do not mix either shader file with an older package. The matching `AFRO-nx.elf` and `source.zip` are in the parent package folder for mapping a console profile; they do not go on the SD card.

The included `renut.toml` captures a frame every 15 seconds and profiles GPU passes by pixel shader. Leave the controller manual. If the application crashes, do not retry the same files; retain the Switch error code and copy `logs/` and `capturas/` from the application directory. `rex_crash.log` is append-only, so its last entry may predate this run.

The default profile is now the visually restored baseline. `renut_visual_probe.toml` is retained as a failed diagnostic control. The separate `performance_top2/` folder has a shader-only A/B candidate for the two largest measured gameplay shader costs; its console picture and FPS remain unverified. Keep each folder's NRO, GLSL and cache together.
