#!/bin/bash
# ================================================================
# GEX Level Calculator - Daily Runner
# One-click execution for macOS (with Auto Token Refresh)
# ================================================================

echo ""
echo "========================================"
echo "   GEX Level Calculator v3.0"
echo "   Auto Token Refresh Enabled"
echo "========================================"
echo ""

# Change to project directory
cd "$HOME/Library/CloudStorage/GoogleDrive-mmenigma@gmail.com/My Drive/Trading/GEX_API"

echo "[1/3] Fetching live QQQ options data..."
echo "        (Tokens will auto-refresh if needed)"
echo ""
python3 fetch_options_chain.py
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to fetch options data!"
    echo ""
    echo "This usually means you need to authenticate."
    echo "Run this command: python3 schwab_auth_with_refresh.py"
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

echo ""
echo "========================================"
echo ""
echo "[2/3] Calculating GEX levels..."
echo ""
python3 calculate_gex.py
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to calculate GEX levels!"
    echo "Check that options_chain_raw.json exists."
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

echo ""
echo "========================================"
echo ""
echo "[3/3] Opening results..."
echo ""
open -a TextEdit gex_levels_output.txt

echo ""
echo "========================================"
echo "   Done! Results saved to:"
echo "   gex_levels_output.txt"
echo "========================================"
echo ""
echo "Press any key to exit..."
read -n 1 -s 


