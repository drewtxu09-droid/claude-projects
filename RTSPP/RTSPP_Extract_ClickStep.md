# RTSPP Extract Tool — Click-Step Guide
**For:** Monthly RTSPP data pull from SAP ISU
**Run:** Between the 2nd and 5th of each month
**Last Updated:** 2026-03-10

---

## Before You Start — Checklist

- [ ] You are running this between the **2nd and 5th** of the month
- [ ] You are connected to the **company network or VPN**
- [ ] You have your **SAP credentials** ready (TXUE ISU Prod)

---

## Part 1 — Run the SAP Extract

### Step 1 — Open the Excel workbook
Open `RTSPP_Extract_Tool_DW.xlsm` in Excel.
> Leave it open. The script needs it to be running in the background.

---

### Step 2 — Run the extract batch file
Navigate to the `RTSPP` folder and **double-click**:
```
run_rtspp_extract.bat
```
A black command window will open and display progress messages.

---

### Step 3 — Log into SAP when prompted
SAP GUI will launch automatically. When the SAP login screen appears:
- Enter your **User ID** and **Password**
- Select **TXUE ISU Prod** if prompted for a system
- Click **Log On**

> The script will continue on its own once it detects SAP is ready.

---

### Step 4 — Let the script run
Do not click anything in SAP or Excel while the script is running.

You will see messages like:
```
Connecting to Excel...
Populating ReadMe dates...
  ReadMe updated: February 2026  (2/1/2026 - 2/28/2026)
Launching SAP...
  Extracting LZ_Houston (profile 400000003)...
  Extracting LZ_North (profile 400000000)...
  Extracting LZ_South (profile 400000001)...
  Extracting LZ_West (profile 400000002)...

Extract complete!
```

When you see **"Extract complete!"** the script is done.

---

### Step 5 — Press any key to close the command window
The window will say `SUCCESS - Extract complete.` — press any key to close it.

---

## Part 2 — Review the Data

### Step 6 — Check the Extract sheet in Excel
Switch to Excel and click on the **Extract** tab.

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

### Step 10 — Save `RTSPP_Extract_Tool_DW.xlsm`
Back in Excel, save the main workbook (`Ctrl + S`) to preserve the updated ReadMe dates.

---

## Done!

---

## If Something Goes Wrong

| What you see | What to do |
|-------------|-----------|
| Command window shows `ERROR:` | Read the error message — the most common issues are listed in the SOP |
| SAP does not launch | Open SAP manually, log in, then re-run the batch file |
| Excel shows `#REF` or blank Extract sheet | Close and reopen Excel, reopen the workbook, and re-run the extract |
| "EDM Profile workbook not found" | SAP was too slow to respond — wait 30 seconds and re-run |
| File not found at network path | Check VPN connection, then re-run the save batch file |

> For SAP errors, refer to the `ReadMe` sheet in `RTSPP_Extract_Tool_DW.xlsm` for the escalation contact.
