# Building AFRO-nx

AFRO-nx uses the Xbox 360 European disc. The tested executable reports title ID `4E4D07D8`. The code generator and shader tools read your own extracted game files.

## Tools

The local build used Windows, Visual Studio Build Tools with CMake and Ninja, LLVM, Python 3, and devkitPro's devkitA64, libnx, and deko3d. For the shader tools you also need a DXC build with SPIR-V support, SPIRV-Cross, and the host build of uam.

## Extract and generate

From the repo root, point the extraction tool at your own disc image.

```powershell
python tools/extract_iso.py "PATH-TO-YOUR-DISC.iso" --output app/assets
python tools/extract_iso.py app/assets/default.xex --info
```

The code generator reads `app/assets/default.xex` through `app/renut_manifest.toml`. Build the host tools with `tools\afro_build_host.bat`. Then use the host `rexglue.exe` to run `codegen` with `app/renut_manifest.toml` and apply `python tools/post_codegen.py` from the repo root. The host build scripts use `VSROOT` and `AFRO_PYTHON` to locate the Windows toolchain and Python.

## Switch build and shaders

Configure the Switch build with `tools/switch/cmake/switch-devkitA64.cmake` and the bundled SDK. The native build enables `AFRO_RENUT_HOOKS` and `BANJO_RENUT_RENDERER` and disables `REXGLUE_SWITCH_NVK`. The output of `tools\build_switch.bat` is `app/out/switch/renut.nro`. Copy it as `AFRO-nx.nro`.

The shader workflow extracts Xbox 360 shader containers from the decoded image using `tools/afro_image_shaders.cpp`. XenosRecomp and `tools/deko3d_shaders.py` translate the containers. `tools/deko3d_shader_package.py` packages the GLSL, and `tools/deko3d_variant_cache.py` can precompile the shader variants to DKSH.

The shader steps still require manual setup. A complete build from a fresh public checkout has not yet been validated. See the [README](../README.md) for the target SD card layout.
