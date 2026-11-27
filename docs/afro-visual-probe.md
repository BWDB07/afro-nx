# Switch visual probe after renut_020

The user's photos `Desktop/logs/IMG_5678.JPG` through `IMG_5682.JPG` show a
missing loading-movie image and very dark gameplay surfaces. They are local
evidence, not part of the source package. The console log loaded the matched
161-shader threshold GLSL package and 164 DKSH variants, then reached gameplay.
These defects are not fixed or approved by the shader candidate tests.

`renut_visual_probe.toml` keeps the same NRO, shaders, resolution and GPU
profile. It sets `banjo_renut_store_cards_verify=true`, which hashes textures
whose pages appear unchanged and forces dynamic movie texture uploads. It also
sets `banjo_deko3d_texture_skip=false`, which binds descriptors on each draw.
It also disables deko3d's barrier merge, lean barrier, and Zcull paths for a
conservative hardware image test. These are independent possible causes, not
proven faults. If the picture improves, the next test will isolate which key
made the difference.
The first three 10-second intervals of renut_020 skipped 261, 533 and 587
dynamic texture uploads. That is a possible cause of the missing movie, not
proof. The gameplay black surfaces may have another cause.

To test on Switch, copy this TOML to `/switch/AFRO-nx/renut.toml` while keeping
the same NRO, `deko3d_glsl.bin`, and `deko3d_shaders.bin` used for renut_020.
Run from boot through the same gameplay scene. Save the console log and photos
of the loading screen and dark surfaces. A `[cards] ... changed under clean
cards` line identifies a missed guest write. If the picture changes without
that line, the dynamic upload or descriptor reuse path still needs isolation.
This profile is diagnostic; its extra uploads, barriers and depth work can
reduce FPS. Its result is an image check, not a 30 FPS measurement.

Console runs 023 and 024 with `renut_visual_baseline.toml` restored the picture
per the user's test. The log confirms the non-CPU enhancement master was off.
This config is now copied as the threshold package's `renut.toml`. The combined
probe did not restore the picture, so an inherited enhancement outside its
specific keys is implicated. Isolate it by A/B before enabling it again.
