@echo off
chcp 65001 >nul
title S7 SCADA - Fork-Integrated Demo
color 0B
echo ======================================================================
echo   🏭 S7 SCADA - Fork-Integrated Industrial Dashboard
echo   Runs THIS repo's compiled snap7.dll on both ends of the wire.
echo ======================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 ( echo ❌ Python not found. & pause & exit /b 1 )

echo ⚙️  Installing UI dependencies (matplotlib only)...
pip install -q -r requirements.txt
echo.

if not exist "..\build\bin\Legacy\win64\snap7.dll" (
    echo ⚠️  Fork snap7.dll not found. Building from THIS repo's sources...
    where make >nul 2>&1
    if errorlevel 1 (
        echo ❌ 'make' not found. Open MSYS2 MinGW64 and run:
        echo    cd build/windows/MinGW64 ^&^& make
        echo    Falling back to UI-only simulation...
        python scada_dashboard.py --simulate
        pause & exit /b 0
    )
    pushd ..\build\windows\MinGW64
    make
    popd
    if not exist "..\build\bin\Legacy\win64\snap7.dll" (
        echo ❌ Build failed. Falling back to UI-only simulation...
        python scada_dashboard.py --simulate
        pause & exit /b 0
    )
    echo ✅ Fork snap7.dll built from patched sources.
    echo.
)

echo 🚀 Starting fork-integrated dashboard...
python scada_dashboard.py
echo.
pause