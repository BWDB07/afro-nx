# AFRO-nx

An unofficial native Nintendo Switch port of the Xbox 360 version of **Afro Samurai**. The port uses static recompilation with ReXGlue and reNut's Direct3D renderer on deko3d.

## v0.1.0 release

[Release notes](https://github.com/BWDB07/afro-nx/releases/tag/v0.1.0)

The release uses original game timing and a 30 FPS cap at stock clocks. Frame rate can dip below the cap. In the prologue, one side of Afro's bandana can render dark. The experimental 60 FPS mode is disabled because a reported combat barrier can remain after enemies are defeated.

## Install

Open the [browser installer](https://bwdb07.github.io/afro-nx/installer/?v=6) in desktop Chrome or Edge and choose your European Xbox 360 disc ISO. Select **Create Switch ZIP**. The installer includes the NRO and creates the shaders from your disc in the browser. Extract `AFRO-nx.zip` to the root of your SD card.

```text
switch/AFRO-nx/
  AFRO-nx.nro
  renut.toml
  deko3d_glsl.bin
  deko3d_shaders.bin
  game_root/
    default.xex
    ...
```

The ZIP includes the [30 FPS configuration](dist/switch/AFRO-nx/renut.toml). Launch the Homebrew Menu in title takeover mode by holding **R** while starting an installed title, then select AFRO-nx. To build manually, see the [build guide](docs/building.md).

## Bug reports

Include the build version, chapter or checkpoint, and reproduction steps. A screenshot helps with visual bugs. For runtime issues, include the relevant `switch/AFRO-nx/logs/` files if available.

## Credits and license

AFRO-nx is maintained by **BWDB07**.

AFRO-nx adapts the Beautiful Katamari Switch port and its inherited renderer and tooling. Thanks to the ReXGlue, reNut, XenosRecomp, deko3d, and upstream port contributors. See the [license](LICENSE) and [third-party notices](THIRD_PARTY_NOTICES.md) for licensing and attribution.
