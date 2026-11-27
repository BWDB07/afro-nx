# Rejected two-shader gameplay FPS A/B

Do not use this as the play build. Console `renut_025.log` loaded the 180-variant
cache, and the user reported black textures. Its 36 ten-second intervals had a
28.35 FPS median and a 17.27 FPS minimum; the shorter visually correct run 024
had a 29.3 FPS median. The scenes and durations differ, so this does not prove
a speed loss, but it gives no reliable gain to justify the visual regression.
Restore all four files from `experimental_threshold/` together.

This package kept the same NRO, 720p and
visually restored `renut.toml` (non-CPU enhancements off). Only the GLSL package
and matching DKSH cache differ from `experimental_threshold/`.

The two changed pixel shaders, `608ED747D8FC6BFD` and `4997278A08C8E6CC`,
cost about 19 ms/frame together in the prior heavy gameplay GPU profile.
Compiler instruction counts fell by 66-69 per alpha-specialized variant, but
GPR counts did not change. Ryujinx reached gameplay with zero runtime shader
compiles. No console visual or FPS gain is proven.

The next shader investigation must isolate the two hashes and validate each on
the console before any optimized variant becomes a default.
