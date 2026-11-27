@echo off
rem Local, offline toolchain. Overrides remain possible for another machine.
if not defined VSROOT set "VSROOT=C:\Program Files\Microsoft Visual Studio\18\Enterprise"
call "%VSROOT%\VC\Auxiliary\Build\vcvars64.bat" >nul || exit /b 1
set "PATH=%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;%VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;C:\Program Files\LLVM\bin;%PATH%"
if not defined AFRO_PYTHON set "AFRO_PYTHON=python"
set REX_CMAKE_COMPILERS="-DCMAKE_C_COMPILER=C:/Program Files/LLVM/bin/clang.exe" "-DCMAKE_CXX_COMPILER=C:/Program Files/LLVM/bin/clang++.exe" -DCMAKE_C_COMPILER_TARGET=x86_64-pc-windows-msvc -DCMAKE_CXX_COMPILER_TARGET=x86_64-pc-windows-msvc -DCMAKE_LINKER_TYPE=LLD "-DCMAKE_RC_COMPILER=C:/Program Files/LLVM/bin/llvm-rc.exe" "-DCMAKE_AR=C:/Program Files/LLVM/bin/llvm-ar.exe" "-DCMAKE_C_FLAGS=-march=x86-64-v2" "-DCMAKE_CXX_FLAGS=-march=x86-64-v2" "-DPYTHON_EXECUTABLE=%AFRO_PYTHON%" "-DPython3_EXECUTABLE=%AFRO_PYTHON%" -DFETCHCONTENT_FULLY_DISCONNECTED=ON
set "REXGLUE_DUMP_IMAGE=%~dp0..\out\renut_image.bin"
