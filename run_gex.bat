@echo off
REM ================================================================
REM GEX Level Calculator - Daily Runner
REM One-click execution for Windows (with Auto Token Refresh)
REM ================================================================

echo.
echo ========================================
echo    GEX Level Calculator v3.0
echo    Auto Token Refresh Enabled
echo ========================================
echo.

REM Change to project directory
cd /d "G:\My Drive\Trading\GEX_API"

echo [1/3] Fetching live QQQ options data...
echo         (Tokens will auto-refresh if needed)
echo.
python fetch_options_chain.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to fetch options data!
    echo.
    echo This usually means you need to authenticate.
    echo Run this command: python schwab_auth_with_refresh.py
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo.
echo [2/3] Calculating GEX levels...
echo.
python calculate_gex.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to calculate GEX levels!
    echo Check that options_chain_raw.json exists.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo.
echo [3/3] Opening results...
echo.
notepad gex_levels_output.txt

echo.
echo ========================================
echo    Done! Results saved to:
echo    gex_levels_output.txt
echo ========================================
echo.
echo Press any key to exit...
pause >nul