# Console visual evidence, 2026-11-17

The user's local `Desktop/logs/IMG_5678.JPG` through `IMG_5682.JPG` and
`IMG_5683.MOV` document the threshold package used by `renut_020.log`. These
media files stay outside the repository and package.

The stills show the loading text without the expected head image. Two gameplay
stills show very dark nearby buildings and geometry despite visible sky and
lights. The video was decoded locally with VLC. Its menu frames render normally;
later loading frames remain blank behind the text, and gameplay frames show
purple sky and distant buildings while large nearby geometry appears almost
black. The earliest video frame is white, which is a transient and not evidence
of the main defect.

For comparison, the Ryujinx threshold capture at
`out/emu_runs/threshold_local_01/captura_009_0138s.png` has textured village
walls and character clothing. It is a different camera/time, so this comparison
establishes a console-specific symptom, not pixel identity or the faulty path.

The first three console intervals skipped 261, 533, and 587 dynamic texture
uploads under store-card checks; later gameplay intervals skipped zero. This
timing makes the movie and gameplay symptoms potentially separate. The visual
probe forces those uploads, checks store-card assumptions, and disables texture
binding reuse and lean deko3d barriers/Zcull. The enhancement-off visual control
tests the larger inherited GPU enhancement set. Neither is a verified fix until
console images and logs are returned.

The user ran the combined visual probe in `Desktop/logs/renut_022.log` and
reported that neither symptom improved. Its 10-second intervals show zero
dynamic upload skips, zero deko3d descriptor skips, Zcull off, and zero texture
or copy hashes changed under clean store cards. It still reached gameplay; the
last complete interval was 22.78 FPS, 43.67 ms GPU and 36.25 ms render-thread
time. This rules out the combined probe as a visual remedy. It does not prove
each setting independently correct, but the store-card verification gives no
evidence of missed guest texture writes. The enhancement-off control remains
the next console image test.

The user then tested that enhancement-off control in `renut_023.log` and
`renut_024.log` and reported that the visuals were restored. Both logs confirm
the CPU and non-CPU enhancement masters were off, with the same 164-variant
shader cache and deko3d device. Run 024 includes 29.62, 28.95, 36.78 and
38.74 FPS intervals, plus heavier intervals at 21.11, 24.55, 26.33 and
27.48 FPS. Its 21.11 FPS interval had 47.09 ms GPU time. This is a working
visual baseline, not stable 30 FPS. An inherited non-CPU enhancement outside
the combined probe's keys is implicated; the specific key remains unknown.
The later two-shader package `performance_top2/` used the same enhancement-off
config but changed PS 608ED747D8FC6BFD and 4997278A08C8E6CC. Console
`renut_025.log` loaded its 180-variant cache, and the user reported black
textures. Ryujinx had shown normal textured gameplay with this candidate, so
the emulator image check was insufficient. The two shader changes need to be
isolated individually on hardware; the combined package is rejected.

