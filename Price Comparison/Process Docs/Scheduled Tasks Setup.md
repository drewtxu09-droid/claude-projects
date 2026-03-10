# Scheduled Tasks Setup — ComparePower 4CHE Alert
## Standard Operating Procedure & Process Document

**Document Owner:** Price Comparison Team
**Last Updated:** March 9, 2026
**Version:** 1.0

---

## 1. Purpose

This document explains how to create and execute `setup_scheduled_tasks.bat`, the batch file that registers Windows Task Scheduler jobs to run the ComparePower 4Change Energy scrape automatically three times per day.

Once registered, the scrape runs at **8:00 AM**, **12:00 PM**, and **5:00 PM** daily without any manual action. If 4Change Energy is not ranked #1, a Teams alert is sent automatically via Power Automate.

> **This setup only needs to be done once.** After that, tasks run on their own every day.

---

## 2. What `setup_scheduled_tasks.bat` Does

When executed, this batch file runs three `schtasks` commands that tell Windows Task Scheduler to:

1. Run `run_4CHE_alert.bat` every day at 8:00 AM
2. Run `run_4CHE_alert.bat` every day at 12:00 PM
3. Run `run_4CHE_alert.bat` every day at 5:00 PM

`run_4CHE_alert.bat` in turn launches `ComparePower_4CHE_Scrape.py` and logs all output to `4CHE/scrape_log.txt`.

---

## 3. Prerequisites

Before running the setup, confirm the following:

- [ ] Python is installed and accessible via the `python` command in a terminal
- [ ] `ComparePower_4CHE_Scrape.py` is in `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
- [ ] `run_4CHE_alert.bat` is in `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
- [ ] `setup_scheduled_tasks.bat` is in `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
- [ ] The `4CHE\` subfolder exists (it is created automatically on first scrape run, but verify)
- [ ] The Power Automate flow is set up and active (see `ComparePower Scrape.md` Section 13)
- [ ] Your PC will be **on and not asleep** at the scheduled run times

---

## 4. How to View `setup_scheduled_tasks.bat` Before Running

It is good practice to review a batch file before executing it, especially since it requires admin rights.

1. Open **File Explorer**
2. Navigate to: `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
3. **Right-click** `setup_scheduled_tasks.bat`
4. Click **"Edit"** (opens in Notepad)
5. Confirm the file contains the three `schtasks /create` commands pointing to `run_4CHE_alert.bat`
6. Close Notepad when done reviewing

---

## 5. How to Execute `setup_scheduled_tasks.bat`

> **Administrator rights are required.** The batch file must be run as administrator or Task Scheduler will reject the commands.

### Step-by-Step

1. Open **File Explorer**
2. Navigate to: `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
3. Locate **`setup_scheduled_tasks.bat`**
4. **Right-click** the file
5. Click **"Run as administrator"**

   > If a **User Account Control (UAC)** prompt appears asking *"Do you want to allow this app to make changes to your device?"* — click **Yes**

6. A black Command Prompt window will open and display:
   ```
   Registering ComparePower 4CHE scheduled tasks...
   SUCCESS: The scheduled task "ComparePower 4CHE 8am" has successfully been created.
   SUCCESS: The scheduled task "ComparePower 4CHE 12pm" has successfully been created.
   SUCCESS: The scheduled task "ComparePower 4CHE 5pm" has successfully been created.

   Done! Tasks registered:
     - ComparePower 4CHE 8am   (8:00 AM daily)
     - ComparePower 4CHE 12pm  (12:00 PM daily)
     - ComparePower 4CHE 5pm   (5:00 PM daily)
   ```
7. Press **any key** to close the window (the script ends with `pause`)

---

## 6. How to Verify the Tasks Were Registered

### Via Task Scheduler (Visual)

1. Press **Windows key**, type `Task Scheduler`, press **Enter**
2. In the left panel, click **"Task Scheduler Library"**
3. In the center panel, you should see three tasks:
   - `ComparePower 4CHE 8am`
   - `ComparePower 4CHE 12pm`
   - `ComparePower 4CHE 5pm`
4. Click any task to confirm:
   - **Status:** Ready
   - **Triggers:** Daily at the correct time
   - **Actions:** Runs `run_4CHE_alert.bat`

### Via Command Prompt (Quick Check)

1. Open a **Command Prompt** (no admin needed for this step)
2. Run:
   ```
   schtasks /query /tn "ComparePower 4CHE 8am"
   schtasks /query /tn "ComparePower 4CHE 12pm"
   schtasks /query /tn "ComparePower 4CHE 5pm"
   ```
3. Each should return a line showing the task name, next run time, and status of `Ready`

---

## 7. How to Test Without Waiting for a Scheduled Time

To confirm everything works immediately after setup:

1. Open **File Explorer** → navigate to `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
2. **Double-click** `run_4CHE_alert.bat`
   - A Command Prompt window will open and run the scrape (~60–90 seconds)
   - If 4Change is not #1, a JSON file will appear in `OneDrive - Vistra Corp\ComparePower Alerts\` and you should receive a Teams message within 1–2 minutes
3. Check the log file to confirm it ran:
   - Navigate to `4CHE\`
   - Open `scrape_log.txt` — the latest run output should appear at the bottom

---

## 8. How to Change the Scheduled Run Times

### Option A — Edit in Task Scheduler (Recommended for one-off changes)

1. Open **Task Scheduler**
2. Click **"Task Scheduler Library"** in the left panel
3. Double-click the task you want to change (e.g., `ComparePower 4CHE 8am`)
4. Click the **"Triggers"** tab
5. Double-click the existing trigger
6. Change the **Start time** to the desired time
7. Click **OK** → **OK**

### Option B — Re-run `setup_scheduled_tasks.bat` with Updated Times

1. Open `setup_scheduled_tasks.bat` in Notepad (**right-click → Edit**)
2. Find the three `/st` parameters (start times) and update them:
   ```
   /st 08:00   ← 8:00 AM
   /st 12:00   ← 12:00 PM
   /st 17:00   ← 5:00 PM
   ```
   Use 24-hour format (e.g., 9:30 AM = `09:30`, 3:00 PM = `15:00`)
3. Save the file
4. **Right-click → Run as administrator** again
   - The `/f` flag in the commands forces an overwrite of existing tasks with the same name, so no duplicates are created

---

## 9. How to Remove the Scheduled Tasks

To stop the automated scrape from running:

1. Open a **Command Prompt as administrator**
2. Run:
   ```
   schtasks /delete /tn "ComparePower 4CHE 8am" /f
   schtasks /delete /tn "ComparePower 4CHE 12pm" /f
   schtasks /delete /tn "ComparePower 4CHE 5pm" /f
   ```
3. Confirm by opening Task Scheduler — the tasks should no longer appear

---

## 10. Troubleshooting

| Issue | Likely Cause | Resolution |
|---|---|---|
| `ERROR: Access is denied` | Not running as administrator | Right-click → **Run as administrator** |
| `ERROR: The system cannot find the file specified` | Path to `run_4CHE_alert.bat` is wrong | Open `setup_scheduled_tasks.bat` in Notepad and verify the path matches the actual file location |
| Task shows **Status: Disabled** | Task was manually disabled | Open Task Scheduler → right-click the task → **Enable** |
| Task ran but no Excel file was created | Python error during scrape | Check `4CHE\scrape_log.txt` for the error message |
| Task ran but no Teams alert received | 4Change may actually be #1, or Power Automate flow is off | Check the log for "4Change Energy IS the cheapest provider!" or verify the flow is active at make.powerautomate.com |
| PC was asleep at run time | Windows sleep/hibernate | Task Scheduler does not wake the PC by default — enable "Wake the computer to run this task" in the task's **Conditions** tab, or ensure the PC is on at run times |

---

## 11. Enabling "Wake to Run" (Optional)

If your PC may be asleep at 8 AM, 12 PM, or 5 PM, you can configure each task to wake it:

1. Open **Task Scheduler** → double-click the task
2. Click the **"Conditions"** tab
3. Check **"Wake the computer to run this task"**
4. Click **OK**
5. Repeat for each of the three tasks

> Note: This wakes the PC from sleep, not from hibernation or shutdown. Keep the PC on sleep (not shutdown) for this to work.

---

*End of Document*
