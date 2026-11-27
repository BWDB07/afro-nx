@echo off
rem Configure + build the Windows (PC) app against the port SDK (katamari-nx\sdk).
rem Usage: tools\build_pc.bat [extra cmake --build args]
rem   BUILD_DIR (env) defaults to app\out\pc; REXSDK_DIR defaults to this port's sdk.
rem   RENUT (env) = ON builds Renut's renderer; default OFF until Afro's hooks and shader cache are ready.
call "%~dp0afro_pc_env.bat" || exit /b 1
set "ROOT=%~dp0.."
if "%BUILD_DIR%"=="" set "BUILD_DIR=%ROOT%\app\out\pc"
if "%REXSDK_DIR%"=="" set "REXSDK_DIR=%ROOT%\sdk"
if "%RENUT%"=="" set "RENUT=OFF"
cmake -S "%ROOT%\app" -B "%BUILD_DIR%" -G Ninja -DCMAKE_BUILD_TYPE=Release %REX_CMAKE_COMPILERS% -DREXGLUE_ENABLE_TRACY=OFF -DREXGLUE_USE_D3D12=ON -DREXGLUE_USE_VULKAN=ON "-DREXSDK_DIR=%REXSDK_DIR%" -DBANJO_RENUT_RENDERER=%RENUT% -DAFRO_RENUT_HOOKS=OFF || exit /b 1
rem Finish codegen before Ninja checks PCH inputs for the full build.
cmake --build "%BUILD_DIR%" --target renut_codegen -j 6 || exit /b 1
cmake --build "%BUILD_DIR%" -j 6 %*
