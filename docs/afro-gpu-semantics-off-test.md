# Renderer-side enhancement A/B

Use the visually restored `experimental_threshold/` NRO, GLSL package and
DKSH cache. After restoring those three files and its `renut.toml`, copy only
`renut_gpu_semantics_off_probe.toml` over `/switch/AFRO-nx/renut.toml`.

This profile turns on the non-CPU enhancement master but explicitly leaves
shader semantics, variant, depth-only and linked-stage changes off. It keeps
720p and the same captures. The previous all-on profile caused a missing
loading image and black gameplay surfaces, while the all-off profile restored
them. This profile tests whether renderer-side work can be retained safely.

Run from boot into the same heavy gameplay scene. Check the loading image,
geometry textures and 10-second FPS/GPU intervals. If either image defect
returns, restore `experimental_threshold/renut.toml` immediately. This is a
diagnostic, not a proven 30 FPS or pixel-identical setting.
