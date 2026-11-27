@echo off
rem Builds the Switch NRO: app\out\switch\renut.nro
rem Usage: tools\build_switch.bat [extra cmake --build args]
rem   NVK_SDK (env) overrides the Mesa/NVK SDK folder (must contain lib\libvulkan.a).
rem   BUILD_DIR (env) another build folder; CMAKE_EXTRA (env) more configure options for a new folder
rem   (docs/pgo-lto.md of banjo-nx: -DBANJO_PGO=generate, or -DBANJO_PGO=use -DBANJO_SWITCH_LTO=ON).
rem Uses the VS-bundled CMake/Ninja (Windows paths) and devkitA64 GCC via the toolchain file.
if "%VSROOT%"=="" set "VSROOT=C:\Program Files\Microsoft Visual Studio\18\Enterprise"
if "%AFRO_PYTHON%"=="" set "AFRO_PYTHON=python"
set "PATH=%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
if "%DEVKITPRO%"=="" set "DEVKITPRO=C:/devkitPro"
set "ROOT=%~dp0.."
if "%NVK_SDK%"=="" set "NVK_SDK=C:/devkitPro/mesa-switch-main-nfsmw-source/mesa-switch-main/mesa-unified-install/opt/devkitpro/portlibs/switch"
if "%BUILD_DIR%"=="" set "BUILD_DIR=%ROOT%\app\out\switch"
if "%JOBS%"=="" set "JOBS=10"
if not exist "%BUILD_DIR%\CMakeCache.txt" (
  cmake -S "%ROOT%\app" -B "%BUILD_DIR%" -G Ninja -DCMAKE_BUILD_TYPE=Release ^
    "-DCMAKE_TOOLCHAIN_FILE=%ROOT%\tools\switch\cmake\switch-devkitA64.cmake" ^
    "-DREXSDK_DIR=%ROOT%\sdk" "-DREXGLUE_SWITCH_NVK_SDK=%NVK_SDK%" ^
    "-DPYTHON_EXECUTABLE=%AFRO_PYTHON%" "-DPython3_EXECUTABLE=%AFRO_PYTHON%" %CMAKE_EXTRA% || exit /b 1
)
cmake --build "%BUILD_DIR%" -j %JOBS% %*
