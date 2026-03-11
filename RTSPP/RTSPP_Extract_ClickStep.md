# RTSPP Extract Tool — Click-Step Guide
**For:** Monthly RTSPP data pull from SAP ISU
**Run:** Automated on the 2nd of each month — or manually via batch file
**Last Updated:** 2026-03-10

---

## One-Time Setup (do this before first use)

### Setup Step 1 — Set the workbook path
Open `rtspp_extract_v2.py` in a text editor and update this line:
```python
RTSPP_FILE_PATH = r"C:\Users\xv1s\path\to\RTSPP_Extract_Tool_DW.xlsm"
```
Change it to the actual full path of your workbook.

---

### Setup Step 2 — Set the Teams webhook URL
In the same file, update:
```python
TEAMS_WEBHOOK_URL = "https://your-tenant.webhook.office.com/..."
```
To get the URL:
1. Go to your Teams channel → click `...` → **Connectors** (or **Workflows**)
2. Search **Incoming Webhook** → Configure → give it a name → **Create**
3. Copy the URL and paste it above

---

### Setup Step 3 — Register the scheduled task
Right-click `setup_scheduled_task.bat` → **Run as Administrator**

This registers a task that runs automatically on the **2nd of every month at 8:00 AM**.
If your PC is off or asleep on the 2nd, it will run the next time you log in.

> You only need to do this once. After that, the extract runs on its own.

---

## Normal Monthly Flow (automated)

On the 2nd of each month, the task runs automatically in the background. You do not need to do anything until you receive the Teams notification.

---

## If You Need to Run It Manually

### Step 1 — Make sure you are on the network or VPN
The script needs network access to reach SAP and the file share.

---

### Step 2 — Run the extract batch file
Navigate to the `RTSPP` folder and **double-click**:
```
run_rtspp_extract_v2.bat
```
A black command window will open. **You do not need to open Excel first** — the script opens the workbook on its own in the background.

---

### Step 3 — Log into SAP if prompted
SAP will launch minimized. If a login screen appears:
- Enter your **User ID** and **Password**
- Select **TXUE ISU Prod** if asked
- Click **Log On**

> If SAP is already open with a TXUE ISU session, the script will create a new child session automatically — your existing work will not be affected.

---

### Step 4 — Let the script run
Do not click anything while the script is running.

You will see messages like:
```
Opening Excel (hidden)...
  Opened (hidden): RTSPP_Extract_Tool_DW.xlsm
Populating ReadMe dates...
  ReadMe updated: February 2026  (2/1/2026 - 2/28/2026)
Connecting to SAP...
  SAP already running — attaching...
  Reusing existing TXUE ISU connection.
  New SAP session created (session 2).
  Extracting LZ_Houston (profile 400000003)...
  Extracting LZ_North (profile 400000000)...
  Extracting LZ_South (profile 400000001)...
  Extracting LZ_West (profile 400000002)...
  SAP session closed.
  Workbook saved.

Extract complete — Teams notification sent.
```

---

### Step 5 — Wait for the Teams notification
When the extract finishes you will receive a Teams message in the configured channel:

> **RTSPP Extract — Ready for Review**
> Month: February 2026
> Date Range: 2/1/2026 → 2/28/2026
> Status: Extract complete. Review the Extract sheet, then run the Save step.

> If you see a red **RTSPP Extract — FAILED** message instead, check the error details in the notification and refer to the Troubleshooting section below.

---

## Part 2 — Review the Data

### Step 6 — Open the workbook
Open `RTSPP_Extract_Tool_DW.xlsm` from its saved location and click the **Extract** tab.

Verify:
- [ ] Column A contains dates starting on the **1st of the prior month** (e.g., 2/1/2026)
- [ ] Columns C, D, E, F contain numeric price values for Houston, North, South, West
- [ ] Cells **H2** and **J2** show the correct From-Date and To-Date
- [ ] The data runs through the **last day of the prior month**

> If anything looks wrong, do not proceed to Part 3. Contact the process owner.

---

## Part 3 — Save the Extract File

### Step 7 — Run the save batch file
Navigate to the `RTSPP` folder and **double-click**:
```
save_rtspp_extract.bat
```

---

### Step 8 — Let the save run
The script will:
1. Copy the Extract sheet into a new standalone Excel file
2. Create the `{YEAR} EFL Filing\Monthly Extracts` folder on the network share if it does not already exist
3. Save the file to that folder
4. Display the save path and filename

You will see a message like:
```
Saving to: \\ddcnasshares\...\2026 EFL Filing\Monthly Extracts\20260228_RTSPP_Extract.xlsx

Saved: 20260228_RTSPP_Extract.xlsx -> 2026 Monthly Extracts folder.
```

---

### Step 9 — Confirm the file was saved
Navigate to the Monthly Extracts folder on the network share and confirm the file is there with the correct name and date.

---

## Done!

---

## If Something Goes Wrong

| What you see | What to do |
|-------------|-----------|
| Red Teams alert — FAILED | Read the error in the notification; refer to SOP troubleshooting section |
| No Teams notification received | Check that `TEAMS_WEBHOOK_URL` is set in `rtspp_extract_v2.py` |
| Command window shows `ERROR: Workbook not found` | Update `RTSPP_FILE_PATH` in `rtspp_extract_v2.py` |
| SAP does not launch | Open SAP manually, log in, then re-run the batch file |
| `EDM Profile workbook not found` | SAP was slow — wait 30 seconds and re-run |
| Scheduled task did not run | Open Task Scheduler, find `RTSPP Monthly Extract`, run it manually |
| File not found at network path on save | Check VPN, then re-run `save_rtspp_extract.bat` |

> For SAP errors, refer to the `ReadMe` sheet in `RTSPP_Extract_Tool_DW.xlsm` for the escalation contact.
