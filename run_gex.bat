@echo off
REM ================================================================
REM GEX Level Calculator - Daily Runner
REM One-click execution for Windows
REM ================================================================

echo.
echo ========================================
echo    GEX Level Calculator v2.0
echo    Friday, October 24, 2025
echo ========================================
echo.

REM Change to project directory
cd /d "G:\My Drive\Trading\GEX_API"

echo [1/3] Fetching live QQQ options data...
echo.
python fetch_options_chain.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to fetch options data!
    echo Try running: python schwab_auth_fixed.py
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo.
echo [2/3] Calculating GEX levels...
echo.
python calculate_gex_v2.1.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to calculate GEX levels!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo.
echo [3/3] Opening results...
echo.
notepad gex_levels_output_v2.txt

echo.
echo ========================================
echo    Done! Results saved to:
echo    gex_levels_output.txt
echo ========================================
echo.
echo Press any key to exit...
pause >nul
