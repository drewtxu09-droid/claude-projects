# Scheduled Tasks Monitor — ComparePower 4CHE Every 30 Minutes
## Standard Operating Procedure & Process Document

**Document Owner:** Price Comparison Team
**Last Updated:** March 10, 2026
**Version:** 1.0

---

## 1. Purpose

This document explains how to create and execute `setup_monitor_task.bat`, the batch file that registers a Windows Task Scheduler job to run the ComparePower 4Change Energy **monitor** automatically every 30 minutes.

Unlike the full scrape (which runs 3x daily and always saves an Excel file), the monitor is designed for continuous background checking:

| Condition | What Happens |
|---|---|
| 4Change Energy **IS** #1 | Logs the result. No file saved, no alert sent. |
| 4Change Energy is **NOT** #1 | Saves a timestamped Excel report **and** sends a Teams alert. |

> **This setup only needs to be done once.** After that, the monitor runs every 30 minutes automatically as long as your PC is on.

---

## 2. How the Monitor Differs from the Full Scrape

| | Full Scrape | Monitor |
|---|---|---|
| **Script** | `ComparePower_4CHE_Scrape.py` | `ComparePower_4CHE_Monitor.py` |
| **Runs** | 3x per day (8 AM, 12 PM, 5 PM) | Every 30 minutes |
| **Always saves Excel** | Yes | No |
| **Saves Excel when not #1** | Yes | Yes |
| **Teams alert when not #1** | Yes | Yes |
| **Log file** | `4CHE/scrape_log.txt` | `4CHE/monitor_log.txt` |
| **Setup batch file** | `setup_scheduled_tasks.bat` | `setup_monitor_task.bat` |
| **Task Scheduler name** | `ComparePower 4CHE 8am` / `12pm` / `5pm` | `ComparePower 4CHE Monitor` |

Both automations can run at the same time without conflict.

---

## 3. Prerequisites

Before running the setup, confirm the following:

- [ ] Python is installed and accessible via the `python` command in a terminal
- [ ] `ComparePower_4CHE_Monitor.py` is in `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
- [ ] `run_4CHE_monitor.bat` is in `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
- [ ] `setup_monitor_task.bat` is in `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
- [ ] The `4CHE\` subfolder exists (it is created automatically on first scrape run, but verify)
- [ ] The Power Automate flow is set up and active (see `ComparePower Scrape.md` Section 13)
- [ ] Your PC will be **on and not asleep** during the hours you want it to monitor

---

## 4. How to View `setup_monitor_task.bat` Before Running

It is good practice to review a batch file before running it with admin rights.

1. Open **File Explorer**
2. Navigate to: `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
3. **Right-click** `setup_monitor_task.bat`
4. Click **"Edit"** (opens in Notepad)
5. Confirm the file contains a `schtasks /create` command with `/sc minute /mo 30` pointing to `run_4CHE_monitor.bat`
6. Close Notepad when done reviewing

---

## 5. How to Execute `setup_monitor_task.bat`

> **Administrator rights are required.** The batch file must be run as administrator or Task Scheduler will reject the command.

### Step-by-Step

1. Open **File Explorer**
2. Navigate to: `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
3. Locate **`setup_monitor_task.bat`**
4. **Right-click** the file
5. Click **"Run as administrator"**

   > If a **User Account Control (UAC)** prompt appears asking *"Do you want to allow this app to make changes to your device?"* — click **Yes**

6. A black Command Prompt window will open and display:
   ```
   Registering ComparePower 4CHE Monitor task (every 30 minutes)...
   SUCCESS: The scheduled task "ComparePower 4CHE Monitor" has successfully been created.

   Done! Task registered:
     - ComparePower 4CHE Monitor (runs every 30 minutes)

   To verify: open Task Scheduler and look for "ComparePower 4CHE Monitor"
   Log file:  Price Comparison\4CHE\monitor_log.txt
   ```
7. Press **any key** to close the window

---

## 6. How to Verify the Task Was Registered

### Via Task Scheduler (Visual)

1. Press **Windows key**, type `Task Scheduler`, press **Enter**
2. In the left panel, click **"Task Scheduler Library"**
3. In the center panel, locate **`ComparePower 4CHE Monitor`**
4. Click the task and confirm in the bottom panel:
   - **Status:** Ready
   - **Triggers:** At startup, repeat every 30 minutes
   - **Actions:** Runs `run_4CHE_monitor.bat`

### Via Command Prompt (Quick Check)

1. Open a **Command Prompt** (no admin needed for this step)
2. Run:
   ```
   schtasks /query /tn "ComparePower 4CHE Monitor"
   ```
3. Should return the task name, next run time, and status of **Ready**

---

## 7. How to Test Without Waiting 30 Minutes

To confirm everything works immediately after setup:

**Option A — Run the batch file directly:**
1. Open **File Explorer** → navigate to `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
2. **Double-click** `run_4CHE_monitor.bat`
3. A Command Prompt window opens and runs the monitor (~60–90 seconds)
4. If 4Change is not #1:
   - An Excel file is saved to `4CHE\` with a military time filename (e.g., `ComparePower_4CHE_76051_20260310_1722.xlsx`)
   - A JSON file appears briefly in `OneDrive - Vistra Corp\ComparePower Alerts\` and is deleted once Power Automate picks it up
   - A Teams message arrives within 1–2 minutes
5. If 4Change IS #1: nothing is saved, the window closes cleanly

**Option B — Run the task from Task Scheduler:**
1. Open **Task Scheduler**
2. Find **`ComparePower 4CHE Monitor`** in the list
3. In the right panel under **Actions**, click **"Run"**
4. The task executes immediately (status changes to **Running**, then back to **Ready**)

**Check the log:**
- Navigate to `4CHE\` → open `monitor_log.txt`
- The most recent run output appears at the bottom of the file

---

## 8. Understanding the Log File

The log file at `4CHE\monitor_log.txt` captures all printed output from each monitor run. Each run appends to the same file. Example entries:

**When 4Change is #1:**
```
[2026-03-10 08:30] ComparePower 4CHE Monitor starting...
Opening comparepower.com for zip 76051...
  ...
  Total plans found: 134
  #1 Cheapest: 4Change Energy — 10.20¢/kWh  ($102.00/mo)
  4Change Energy rank: #1 (4Change Simple Rate 12) — 10.20¢/kWh  ($102.00/mo)
  4Change IS #1 — no alert, no file saved.
Done. Closing browser.
```

**When 4Change is NOT #1:**
```
[2026-03-10 09:00] ComparePower 4CHE Monitor starting...
Opening comparepower.com for zip 76051...
  ...
  Total plans found: 134
  #1 Cheapest: TXU Energy — 9.80¢/kWh  ($98.00/mo)
  4Change Energy rank: #3 (4Change Simple Rate 12) — 10.50¢/kWh  ($105.00/mo)
  4Change is NOT #1. +0.70¢/kWh  (+$7.00/mo vs #1).

  Excel saved to: 4CHE/ComparePower_4CHE_76051_20260310_0900.xlsx
  Alert file written to OneDrive: alert_20260310_090045.json
Done. Closing browser.
```

---

## 9. How to Change the Run Interval

### Option A — Edit in Task Scheduler (Recommended for one-off changes)

1. Open **Task Scheduler**
2. Double-click **`ComparePower 4CHE Monitor`**
3. Click the **"Triggers"** tab
4. Double-click the existing trigger
5. Under **Advanced settings**, find **"Repeat task every"**
6. Change the interval (e.g., from 30 minutes to 15 minutes or 1 hour)
7. Click **OK** → **OK**

### Option B — Re-run `setup_monitor_task.bat` with an Updated Interval

1. **Right-click** `setup_monitor_task.bat` → **"Edit"** (opens in Notepad)
2. Find the `/mo 30` parameter — this sets the repeat interval in minutes
3. Change `30` to your desired interval (e.g., `15` for every 15 minutes, `60` for hourly)
4. Save the file
5. **Right-click** → **Run as administrator** again
   - The `/f` flag forces an overwrite of the existing task, so no duplicates are created

---

## 10. How to Pause or Stop the Monitor

### Pause (Disable) the Task Temporarily

1. Open **Task Scheduler**
2. Right-click **`ComparePower 4CHE Monitor`**
3. Click **"Disable"**
4. To resume: right-click → **"Enable"**

### Remove the Task Permanently

1. Open a **Command Prompt as administrator**
2. Run:
   ```
   schtasks /delete /tn "ComparePower 4CHE Monitor" /f
   ```
3. Confirm by opening Task Scheduler — the task should no longer appear

---

## 11. Troubleshooting

| Issue | Likely Cause | Resolution |
|---|---|---|
| `ERROR: Access is denied` when running setup | Not running as administrator | Right-click → **Run as administrator** |
| Task shows **Status: Disabled** | Task was manually disabled | Open Task Scheduler → right-click → **Enable** |
| Task ran but no log entry appeared | `4CHE\` folder doesn't exist yet | Create the folder manually at `Price Comparison\4CHE\` |
| Task ran but no Excel file saved | 4Change is currently #1 (expected behavior) | Check `monitor_log.txt` — should say "4Change IS #1" |
| Task ran, Excel saved, but no Teams message | Power Automate flow is off or OneDrive not syncing | Check flow is active at make.powerautomate.com; check OneDrive sync status in system tray |
| PC was sleeping at run time | Windows sleep/hibernate | See Section 12 — enable "Wake the computer to run this task" |
| Monitor and full scrape run at the same time | Both tasks scheduled — this is fine | They run independently and log to separate files; no conflict |

---

## 12. Enabling "Wake to Run" (Optional)

If your PC may be asleep during the day, you can configure the monitor task to wake it:

1. Open **Task Scheduler** → double-click **`ComparePower 4CHE Monitor`**
2. Click the **"Conditions"** tab
3. Check **"Wake the computer to run this task"**
4. Click **OK**

> Note: This wakes the PC from **sleep**, not from hibernation or full shutdown. For the monitor to run reliably all day, keep the PC on sleep mode rather than shutting it down.

---

## 13. File Reference

| File | Location | Purpose |
|---|---|---|
| `ComparePower_4CHE_Monitor.py` | `Price Comparison\` | The monitor script |
| `run_4CHE_monitor.bat` | `Price Comparison\` | Runs the monitor; logs to `monitor_log.txt` |
| `setup_monitor_task.bat` | `Price Comparison\` | Registers the Task Scheduler job (run once as admin) |
| `monitor_log.txt` | `Price Comparison\4CHE\` | Auto-generated log of every monitor run |
| `ComparePower Scrape.md` | `Process Docs\` | Main SOP — overview of all tools |
| `Scheduled Tasks Setup.md` | `Process Docs\` | Setup guide for the 3x daily full scrape tasks |

---

*End of Document*
