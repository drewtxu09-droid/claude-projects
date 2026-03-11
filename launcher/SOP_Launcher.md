# SOP — Script Launcher Dashboard
**Version:** 1.0
**Date:** 2026-03-11
**Purpose:** Provide a single web-based control panel to launch all project batch scripts without navigating folders.

---

## Overview

The Script Launcher is a local Flask web app (`launcher.py`) that serves a dashboard at **http://localhost:5050**. Each card on the dashboard represents one batch script. Clicking **Run** opens the script in a new terminal window.

Scripts are grouped by project:
- **Oncor TDU Rate Dashboard** — starts the Dash rate dashboard
- **RTSPP Extract** — SAP data extraction and scheduling
- **Price Comparison — 4CHE** — ComparePower scraping, alerts, and scheduling

---

## Prerequisites

- Python 3 installed and on PATH
- Flask (`pip install flask`) — installed automatically by `run_launcher.bat`
- All dependent scripts and their requirements must already be set up

---

## Starting the Launcher

1. Navigate to `C:\Users\XV1S\Desktop\Claude\launcher\`
2. Double-click **`run_launcher.bat`**
3. A terminal window opens, Flask installs if needed, and your browser opens to `http://localhost:5050`
4. The dashboard loads showing all script cards

---

## Using the Dashboard

- Each card shows:
  - **Script name** — what the button does
  - **Description** — what the script runs and any requirements
  - **Filename** — the `.bat` file being called
  - **Run button** — click to launch the script
- After clicking **Run**, the card shows:
  - `Launching...` (yellow) — request in progress
  - `Launched successfully.` (green) — terminal window opened
  - `Error: <message>` (red) — something went wrong (see Troubleshooting)

---

## Stopping the Launcher

Close the terminal window that opened when you ran `run_launcher.bat`. This stops the Flask server.

---

## Adding New Scripts

When Claude builds a new tool with a `.bat` file, it will ask whether to add it to the launcher. If yes, Claude will add a new entry to the `SCRIPTS` list in `launcher.py` with the correct group, name, description, file path, and color.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Browser doesn't open | Manually go to http://localhost:5050 |
| "File not found" error on a card | Verify the `.bat` file exists at the path shown |
| Flask not found | Run `pip install flask` manually in a terminal |
| Port 5050 already in use | Close other launcher instances or change `port=5050` in `launcher.py` |
| Script launches but immediately closes | Open the `.bat` file directly to see the error output |
