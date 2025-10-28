# How to Run GEX Calculator on Windows - Step by Step Guide

## 🎯 QUICK START (Run These 3 Commands)

### Step 1: Open Command Prompt
1. Press `Windows Key + R`
2. Type: `cmd`
3. Press Enter

### Step 2: Navigate to Your Project Folder
```cmd
cd "G:\My Drive\Trading\GEX_API"
```

### Step 3: Run the Scripts
```cmd
python schwab_auth_fixed.py
python fetch_options_chain.py
python calculate_gex_v2.py
```

---

## 📋 DETAILED WALKTHROUGH

### Before Market Opens (8:45 AM Daily Routine)

#### 1. Open Command Prompt
- **Method 1:** Press `Windows Key + R`, type `cmd`, press Enter
- **Method 2:** Search "Command Prompt" in Windows search
- **Method 3:** Press `Windows Key + X`, select "Command Prompt" or "PowerShell"

#### 2. Navigate to Your Folder
```cmd
cd "G:\My Drive\Trading\GEX_API"
```

**What this does:** Changes directory to where your Python scripts are stored

**If you get an error:**
- Make sure the path is correct
- Use quotes around the path if it has spaces
- Verify folder exists in Google Drive

#### 3. Authenticate with Schwab (if tokens expired)
```cmd
python schwab_auth_fixed.py
```

**What happens:**
1. Script will open a browser window
2. Login to Schwab if needed
3. You'll be redirected to a URL starting with `https://127.0.0.1/?code=...`
4. **COPY THE ENTIRE URL** from browser address bar
5. Paste it into the command prompt when asked
6. Press Enter

**Output you should see:**
```
✅ Authentication successful!
✅ Tokens saved to tokens.txt
```

**Note:** Tokens last 30 minutes. If you get auth errors later, run this again.

#### 4. Fetch Options Data
```cmd
python fetch_options_chain.py
```

**What this does:**
- Connects to Schwab API using your tokens
- Downloads QQQ options chain (all strikes, all expirations)
- Saves raw data to `options_chain_raw.json`

**Output you should see:**
```
🚀 Starting options chain fetch...
✅ Successfully fetched QQQ options chain
   Found X expirations
   Saved to: options_chain_raw.json
```

**If you get errors:**
- `401 Unauthorized` → Run step 3 again (re-authenticate)
- `Connection error` → Check internet connection
- `File not found` → Make sure you're in the right folder

#### 5. Calculate GEX Levels
```cmd
python calculate_gex_v2.py
```

**What this does:**
- Reads the options data from step 4
- Fetches live QQQ and NQ prices for dynamic ratio
- Calculates the 5 GEX levels
- Converts to NQ prices
- Displays results and saves to file

**Output you should see:**
```
🚀 Starting GEX Level Calculator v2.0

🔄 Fetching live prices for dynamic ratio...
   QQQ Price: $610.58
   NQ Price: 25,253.00 (from /NQ)
   ✅ Dynamic Ratio: 41.36

📂 Loading options chain data...
📊 Processing expiration: 2024-10-24
   Filtered 45 call strikes (OI ≥ 100)
   Filtered 52 put strikes (OI ≥ 100)

🔢 Calculating GEX levels...

======================================================================
🎯 GEX LEVELS FOR NQ TRADING - v2.0
======================================================================

📊 Current Prices:
   QQQ: $610.58
   NQ:  25,253
   Ratio: 41.36
   Net GEX: 2,481K

📍 GEX LEVELS:
----------------------------------------------------------------------
1. 🔵 Call OI      QQQ $608.00 → NQ 25,150
2. 🟢 Pos GEX      QQQ $612.00 → NQ 25,300
3. 🟠 Zero Gamma   QQQ $611.00 → NQ 25,250
4. 🔴 Neg GEX      QQQ $610.00 → NQ 25,225
5. 🟣 Put OI       QQQ $602.00 → NQ 24,900
----------------------------------------------------------------------

✅ Results saved to: gex_levels_output.txt
✅ Done! Ready for trading.
```

---

## 🔧 TROUBLESHOOTING

### Problem: "Python is not recognized"
**Solution:** 
1. Check if Python is installed: `python --version`
2. If not, you said Python 3.13 is already installed, so try: `py` instead of `python`
3. Or use full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe`

### Problem: "No module named 'requests'"
**Solution:**
```cmd
pip install requests
```
or
```cmd
python -m pip install requests
```

### Problem: Tokens expired (401 error)
**Solution:**
```cmd
python schwab_auth_fixed.py
```
Then re-run the other scripts.

### Problem: "options_chain_raw.json not found"
**Solution:**
You need to run `fetch_options_chain.py` before `calculate_gex_v2.py`

### Problem: Can't see the output (scrolls too fast)
**Solution:**
Results are saved to `gex_levels_output.txt` - open this file in Notepad

---

## 📝 DAILY WORKFLOW CHECKLIST

**Every trading morning at 8:45 AM:**

- [ ] Open Command Prompt
- [ ] Navigate to folder: `cd "G:\My Drive\Trading\GEX_API"`
- [ ] Run: `python schwab_auth_fixed.py` (if needed)
- [ ] Run: `python fetch_options_chain.py`
- [ ] Run: `python calculate_gex_v2.py`
- [ ] Open `gex_levels_output.txt` to see results
- [ ] Compare with GEXstream to validate
- [ ] Enter levels into ThinkorSwim study

**Time required:** ~1-2 minutes

---

## 💡 PRO TIPS

### Tip 1: Create a Batch File (One-Click Execution)
Create a file called `run_gex.bat` in your folder with this content:
```batch
@echo off
cd "G:\My Drive\Trading\GEX_API"
echo Fetching options data...
python fetch_options_chain.py
echo.
echo Calculating GEX levels...
python calculate_gex_v2.py
echo.
echo Done! Check gex_levels_output.txt
pause
```

Then just double-click this file each morning!

### Tip 2: Keep Command Window Open
Add `pause` at the end of the batch file so window stays open

### Tip 3: View Results in Notepad
```cmd
notepad gex_levels_output.txt
```

### Tip 4: Quick Re-run
Press `↑` arrow key in Command Prompt to see previous commands

---

## 🎓 UNDERSTANDING THE OUTPUT

### The 5 Levels Explained:

1. **🔵 Call OI** (Call Open Interest)
   - Strike with most call contracts
   - Upper resistance area
   
2. **🟢 Pos GEX** (Positive GEX - MOST IMPORTANT)
   - Highest positive gamma exposure
   - Major support/resistance wall
   - Price tends to pin here
   
3. **🟠 Zero Gamma** (Regime Line)
   - Where gamma flips from positive to negative
   - Critical pivot level
   - Above = low volatility, Below = high volatility
   
4. **🔴 Neg GEX** (Negative GEX)
   - Highest negative gamma exposure
   - Danger zone for price acceleration
   - Support that can fail quickly
   
5. **🟣 Put OI** (Put Open Interest)
   - Strike with most put contracts
   - Lower support area

---

## 📊 COMPARING WITH GEXSTREAM

After running the calculator, compare your results with GEXstream:

1. Log into GEXstream.com
2. Look at the right panel
3. Compare the 5 strikes:

**Your API Output:**
```
1. Call OI:    QQQ $608.00 → NQ 25,150
2. Pos GEX:    QQQ $612.00 → NQ 25,300
3. Zero Gamma: QQQ $611.00 → NQ 25,250
4. Neg GEX:    QQQ $610.00 → NQ 25,225
5. Put OI:     QQQ $602.00 → NQ 24,900
```

**GEXstream:**
```
Call OI:    @ 608
Pos GEX:    @ 612
Zero Gamma: 611.24
Neg GEX:    @ 611
Put OI:     @ 602
```

**Goal:** Within 5 points for most levels, within 10 points for all levels

---

## 🚨 WHEN TO RE-AUTHENTICATE

You need to run `schwab_auth_fixed.py` again if:
- You see "401 Unauthorized" errors
- It's been more than 30 minutes since last auth
- You're starting a new session

---

## 📞 QUICK REFERENCE COMMANDS

```cmd
# Navigate to folder
cd "G:\My Drive\Trading\GEX_API"

# Re-authenticate (if needed)
python schwab_auth_fixed.py

# Fetch options data
python fetch_options_chain.py

# Calculate GEX levels
python calculate_gex_v2.py

# View results
notepad gex_levels_output.txt

# Check Python version
python --version

# Install requests library (if needed)
pip install requests
```

---

**Last Updated:** October 24, 2025
**Version:** 2.0
