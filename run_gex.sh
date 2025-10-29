#!/bin/bash
# ================================================================
# GEX Level Calculator - Daily Runner
# One-click execution for macOS
# ================================================================

echo ""
echo "========================================"
echo "   GEX Level Calculator v2.0"
echo "   Friday, October 24, 2025"
echo "========================================"
echo ""

# Change to project directory
cd "$HOME/Library/CloudStorage/GoogleDrive-mmenigma@gmail.com/My Drive/Trading/GEX_API"

echo "[1/3] Fetching live QQQ options data..."
echo ""
python3 fetch_options_chain.py
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to fetch options data!"
    echo "Try running: python3 schwab_auth_fixed.py"
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

echo ""
echo "========================================"
echo ""
echo "[2/3] Calculating GEX levels..."
echo ""
python3 calculate_gex_v2.3.py
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to calculate GEX levels!"
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

echo ""
echo "========================================"
echo ""
echo "[3/3] Opening results..."
echo ""
open -a TextEdit gex_levels_output_v2.3.txt

echo ""
echo "========================================"
echo "   Done! Results saved to:"
echo "   gex_levels_output_v2.3.txt"
echo "========================================"
echo ""
echo "Press any key to exit..."
read -n 1 -s
