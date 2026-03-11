# RTSPP Extract Tool — Standard Operating Procedure
**Version:** 1.3
**Process Owner:** Rate Management
**Run Frequency:** Monthly (automated on the 2nd; manual fallback via batch file)
**Last Updated:** 2026-03-10

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-10 | Initial release — Python replacement for VBA macro |
| 1.1 | 2026-03-10 | Auto-create year and Monthly Extracts folders on network share if missing |
| 1.2 | 2026-03-10 | v2 script: Excel opens/saves hidden, SAP reuses existing connection, Teams alert on completion, Windows Task Scheduler support |
| 1.3 | 2026-03-10 | Replace Teams webhook with OneDrive file-drop → Power Automate flow (no premium Teams required) |

---

## 1. Purpose

This tool automates the monthly extraction of Real-Time Settlement Point Price (RTSPP) data for four ERCOT load zones from SAP ISU. It replaces the manual VBA macro previously run inside `RTSPP_Extract_Tool_DW.xlsm`. The extracted data is used to support the Annual EFL POLR Filing.

---

## 2. What the Tool Does (v2)

### Step 1 — Date Population (automatic)
The script checks today's date and automatically targets the **previous calendar month**. It writes the following fields into the `ReadMe` sheet — no manual date entry is needed.

| Cell | Value Written | Example (run in March 2026) |
|------|--------------|------------------------------|
| A1   | Last day of prior month | 2/28/2026 |
| B1   | Month + Year label | February 2026 |
| A2   | YYYY - MM MonthName | 2026 - 02 February |
| B2   | YYYYMMDD of last day | 20260228 |
| C2   | First day of prior month | 2/1/2026 |
| E2   | Output filename | 20260228_RTSPP_Extract.xlsx |
| B3   | Year | 2026 |

### Step 2 — Excel Opens Automatically (hidden)
The script opens `RTSPP_Extract_Tool_DW.xlsm` on its own — **the workbook does not need to be open beforehand**. Excel runs entirely in the background and is never visible on screen.

### Step 3 — SAP Connection (automatic, handles existing sessions)
The script connects to SAP intelligently:
- **SAP not running** → launches SAP GUI minimized and connects
- **SAP running, no TXUE ISU connection** → opens a new connection
- **SAP running with existing TXUE ISU session** → creates a new child session, leaving your existing work untouched

It then navigates to transaction `/NEEDM08` and pulls RTSPP data for all four load zones:

| Load Zone | SAP Profile ID |
|-----------|---------------|
| LZ_Houston | 400000003 |
| LZ_North   | 400000000 |
| LZ_South   | 400000001 |
| LZ_West    | 400000002 |

For each zone, the script sets the profile and date range, refreshes the tree, opens the EDM Profile export, copies the interval price data into the `Extract` sheet, and hides the temporary SAP workbook.

### Step 4 — Save and Notify (automatic)
After all four zones are extracted:
- The workbook saves automatically in the background
- Excel remains hidden — **it does not pop up on screen**
- A **Microsoft Teams notification** is sent confirming the extract is ready for review
- If an error occurs at any point, a Teams alert is sent with the error details

### Step 5 — Review (manual)
You open `RTSPP_Extract_Tool_DW.xlsm` manually when you receive the Teams notification and review the `Extract` sheet.

### Step 6 — Save to Network Share (manual)
A separate batch file copies the `Extract` sheet into a standalone `.xlsx` file and saves it to:

```
\\ddcnasshares\c_product\RATE MANAGEMENT\aaaa_LARR_POLR\
  Annual EFL POLR Filing\{YEAR} EFL Filing\Monthly Extracts\
```

The filename is auto-generated (e.g., `20260228_RTSPP_Extract.xlsx`). If the year folder or `Monthly Extracts` subfolder does not yet exist on the share, the script creates them automatically before saving.

---

## 3. Prerequisites

### One-Time Setup
| Requirement | Notes |
|------------|-------|
| Python 3.x | Must be installed and on PATH |
| pywin32 library | Run once: `pip install pywin32` |
| SAP GUI | Must be installed at `C:\Program Files (x86)\SAP\FrontEnd\SAPgui\` |
| SAP GUI Scripting | Enable in SAP GUI Options → Accessibility & Scripting |
| Teams Webhook URL | Set `TEAMS_WEBHOOK_URL` in `rtspp_extract_v2.py` (see Section 5) |
| Workbook path | Set `RTSPP_FILE_PATH` in `rtspp_extract_v2.py` |
| Scheduled Task | Run `setup_scheduled_task.bat` once as Administrator |

### Each Run
| Requirement | Notes |
|------------|-------|
| SAP credentials | Active login for TXUE ISU Prod (script handles login prompt) |
| Network / VPN | Required for SAP connection and saving to the network share |

---

## 4. Files

| File | Purpose |
|------|---------|
| `rtspp_extract_v2.py` | Main automated script (current version) |
| `run_rtspp_extract_v2.bat` | Manually trigger the extract |
| `save_rtspp_extract.bat` | Save the extract to the network share (manual step) |
| `setup_scheduled_task.bat` | Run once as Admin to register the monthly scheduled task |
| `setup_scheduled_task.ps1` | PowerShell called by the setup bat |
| `rtspp_extract.py` | v1 script — preserved for reference |
| `RTSPP_Extract_Tool_DW.xlsm` | Source Excel workbook (not in this repo) |

---

## 5. Teams Alert Setup (one-time, via OneDrive + Power Automate)

Teams alerts do not use a webhook. Instead, the script drops a small JSON file into a OneDrive for Business folder. A Power Automate flow watches that folder, reads the file, posts the Teams message, and deletes the file.

### OneDrive Folder
The script writes to:
```
C:\Users\XV1S\OneDrive - Vistra Corp\RTSPP Alerts
```
This folder is already created. The path is set in `rtspp_extract_v2.py` as `ONEDRIVE_ALERT_FOLDER`.

### Power Automate Flow Steps
| Step | Action | Key Setting |
|------|--------|-------------|
| 1 | When a file is created | Folder: `RTSPP Alerts` |
| 2 | Get file content | File: from trigger |
| 3 | Parse JSON | Content: file content; Schema: see below |
| 4 | Post message in a chat or channel | Message: built from parsed JSON fields |
| 5 | Delete file | File: from trigger |

### Parse JSON Schema
Paste this into the **Parse JSON** step → **Generate from sample** → or directly as the schema:
```json
{
    "type": "object",
    "properties": {
        "status":     { "type": "string" },
        "month":      { "type": "string" },
        "from_date":  { "type": "string" },
        "to_date":    { "type": "string" },
        "workbook":   { "type": "string" },
        "timestamp":  { "type": "string" },
        "error":      {}
    }
}
```

### Suggested Teams Message (Step 4)
**Success:**
> **RTSPP Extract — Ready for Review**
> Month: `[month]` | Range: `[from_date]` – `[to_date]`
> Workbook saved. Open it to review, then run the Save step.
> _(run at `[timestamp]`)_

**Failure** (add a condition on `status` = `"failed"`):
> **RTSPP Extract — FAILED**
> Error: `[error]`
> Manual intervention required. Run `run_rtspp_extract_v2.bat` to retry.

---

## 6. Scheduled Task Setup (one-time)

Right-click `setup_scheduled_task.bat` → **Run as Administrator**.

This registers a Windows Scheduled Task with the following settings:

| Setting | Value |
|---------|-------|
| Task name | RTSPP Monthly Extract |
| Runs on | 2nd of every month at 8:00 AM |
| If PC was off/asleep on the 2nd | Runs automatically on next wake/login |
| Retry on failure | Once, after 10 minutes |

To view or edit the task: open **Task Scheduler** → Task Scheduler Library → `RTSPP Monthly Extract`.

---

## 7. Timing

- Scheduled to run automatically on the **2nd of each month at 8:00 AM**
- If the computer was offline on the 2nd, the task runs on the **next login or wake**
- Data for the prior month is not complete in SAP until the overnight batch filing runs on the 2nd
- Do not run on the 1st — data will be incomplete

---

## 8. Troubleshooting

| Error / Symptom | Likely Cause | Fix |
|----------------|-------------|-----|
| `Workbook not found` | `RTSPP_FILE_PATH` not set correctly | Update the path in `rtspp_extract_v2.py` |
| `SAP GUI failed to launch` | SAP not installed or path wrong | Confirm SAP is installed; update `SAP_EXE` in script if needed |
| SAP login prompt appears | Not logged in | Log into SAP ISU Prod, then re-run |
| `EDM Profile workbook not found` | SAP was slow to export | Re-run; if persistent, increase the `time.sleep` wait in `find_edm_workbook()` |
| Teams notification not received | Webhook URL not set or invalid | Confirm `TEAMS_WEBHOOK_URL` is set correctly in the script |
| `Permission denied` on save | No access to network share | Confirm VPN is connected and share path is accessible |
| Data appears in wrong columns | SAP EDM Profile layout changed | Contact the script owner — column mappings may need updating |
| Scheduled task did not run | Task Scheduler disabled or PC offline | Check Task Scheduler history; run `run_rtspp_extract_v2.bat` manually |

---

## 9. Contact / Escalation

For SAP running errors, see the `ReadMe` sheet in `RTSPP_Extract_Tool_DW.xlsm` — escalation contact is noted there.
