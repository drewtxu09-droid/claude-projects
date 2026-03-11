# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A collection of browser-based web projects (HTML/CSS/JS). No build system, dependencies, or server — all files run directly in the browser.

## Running Projects

Open any `.html` file directly in a browser, or launch via:
```
start <filename>.html
```

## Oncor TDU Rate Dashboard (`oncor-dashboard/`)

A Python + Dash app showing Oncor TDU rates for multiple rate classes.

### Running
```
cd oncor-dashboard
run.bat
```
Opens at http://localhost:8050. Always kill existing Python/py processes before restarting.

### Rate Data Conventions
- All variable charges stored and displayed in **$/kWh** (6 decimal places)
- Fixed charges in **$/mo** (2 decimal places)
- Zero values display as `0` with no decimals
- Rolling 12 months, oldest left → newest (current month) right
- Mobile Generation (MG) is only billed in December — highlight those cells in orange

### Rate Classes
Each rate class has its own `KNOWN_RATE_PERIODS`, `CHARGE_META`, and CSV in `data/`:
- **Residential** → `data/rates.csv`
- **Secondary Less Than 10 kW** → `data/rates_sec.csv`

### Table Layout
Matches `Oncor_Res_example.xlsx` column structure:
`SAC04 Code | SAC04 Descriptions | PUC Control # | Notes | [Pending Changes: Amount, Date, Status, PUC#] | Month columns`

- Pending Amount shows the **proposed new rate** (what it would change to)
- Fixed and Variable totals appear at the **bottom** of the table, separated by two blank rows
- When a charge ends on a known date, include that date in the Notes field (e.g., `Ended 12/15/2025`)

### Adding a New Rate Class
1. Add `KNOWN_RATE_PERIODS_XXX` and `CHARGE_META_XXX` to `scraper.py`
2. Add `run_scraper_xxx()` function calling `build_rolling_12_months(KNOWN_RATE_PERIODS_XXX)`
3. Add a new `dbc.Tab` in `build_layout()` in `app.py`
4. Delete the old CSV so it regenerates on next run

### After Any Changes
- Delete affected CSV(s) in `data/` so data regenerates with correct values
- Kill existing server processes before restarting: `powershell -Command "Get-Process py,python | Stop-Process -Force"`

## Script Launcher (`launcher/`)

A Flask web app at `http://localhost:5050` with buttons to launch all project batch scripts.

### Running
```
cd launcher
run_launcher.bat
```

### Adding New Scripts
**After building any new tool that includes a `.bat` file, always ask the user:**
> "Would you like me to add this to the Script Launcher dashboard? I'll group it under [project name]."

If yes, add a new entry to the `SCRIPTS` list in `launcher/launcher.py` with:
- `id` — unique snake_case identifier
- `group` — matches the existing project group name (or a new one if it's a new project)
- `name` — short button label
- `file` — the `.bat` filename
- `dir` — absolute path using `os.path.join(BASE, "folder")`
- `description` — one sentence explaining what the script does and any requirements
- `color` — use the same color as other cards in the same group for consistency

## Chat History (`chat history/`)

All conversations are saved to `C:\Users\XV1S\Desktop\Claude\chat history\`.

### File Naming
```
YYYY-MM-DD_HHmm_Short-Topic-Name.md
```
Example: `2026-03-11_1831_Launcher-Dashboard-Build.md`

- Date and time use **military time** (24-hour)
- Topic name is a short hyphenated description of what the conversation covered
- When the user says **"new chat"**, start a new file with a fresh timestamp and topic name

### Format
Each file uses this structure:
```
# Chat History — YYYY-MM-DD HH:MM
---
**User:** ...
**Claude:** ...
```

## Git & GitHub

- Remote: https://github.com/drewtxu09-droid/claude-projects
- All changes should be committed and pushed after each feature or fix.
- Keep commit messages clean and descriptive.
