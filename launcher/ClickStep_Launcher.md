# Click-Step Guide — Script Launcher Dashboard
**Version:** 1.0
**Date:** 2026-03-11

---

## How to Start the Launcher

1. Open File Explorer
2. Go to: `C:\Users\XV1S\Desktop\Claude\launcher\`
3. Double-click **`run_launcher.bat`**
4. A black terminal window opens — wait for the message:
   ```
   Launcher running at http://localhost:5050
   ```
5. Your browser opens automatically to **http://localhost:5050**

---

## How to Run a Script

1. Find the card for the script you want to run
2. Read the **description** to confirm it's the right one
3. Click the colored **Run** button on the card
4. Watch the status line under the button:
   - **Yellow "Launching..."** → request sent, wait a moment
   - **Green "Launched successfully."** → a new terminal window has opened and the script is running
   - **Red "Error: ..."** → something went wrong, see the SOP troubleshooting section
5. Switch to the new terminal window to monitor progress

---

## Script Quick Reference

| Group | Button Name | What It Does |
|---|---|---|
| Oncor TDU Rate Dashboard | Run Dashboard | Starts Dash app at http://localhost:8050 |
| RTSPP Extract | Run RTSPP Extract v2 | Monthly SAP pull, Teams alert on fail |
| RTSPP Extract | Save RTSPP Extract | Saves data to network share |
| RTSPP Extract | Run RTSPP Extract (Legacy) | Original SAP extract |
| RTSPP Extract | Setup Scheduled Task | Auto-runs extract on 2nd of month at 8 AM |
| Price Comparison — 4CHE | Run 4CHE Scrape & Alert | Scrapes ComparePower, sends price alerts |
| Price Comparison — 4CHE | Run 4CHE Monitor | Logs monitoring data to monitor_log.txt |
| Price Comparison — 4CHE | Setup Alert Scheduled Tasks | Registers daily alert tasks (8 AM, 12 PM, 5 PM) |
| Price Comparison — 4CHE | Setup Monitor Scheduled Task | Registers monitor task every 30 minutes |

---

## How to Stop the Launcher

1. Find the terminal window titled with the launcher path
2. Click it to focus
3. Press **Ctrl+C** or close the window
