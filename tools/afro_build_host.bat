@echo off
setlocal
call "%~dp0afro_pc_env.bat" || exit /b 1
set "ROOT=%~dp0.."
cmake -S "%ROOT%\sdk" -B "%ROOT%\out\host" -G Ninja -DCMAKE_BUILD_TYPE=Release %REX_CMAKE_COMPILERS% -DREXGLUE_ENABLE_TRACY=OFF -DREXGLUE_ENABLE_FIDELITYFX=OFF -DREXGLUE_USE_D3D12=ON -DREXGLUE_USE_VULKAN=OFF || exit /b 1
cmake --build "%ROOT%\out\host" --target rexglue -j 6
