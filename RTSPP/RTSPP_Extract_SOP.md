# RTSPP Extract Tool — Standard Operating Procedure
**Version:** 1.1
**Process Owner:** Rate Management
**Run Frequency:** Monthly (2nd – 5th of each month)
**Last Updated:** 2026-03-10

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-10 | Initial release — Python replacement for VBA macro |
| 1.1 | 2026-03-10 | Auto-create year and Monthly Extracts folders on network share if missing |

---

## 1. Purpose

This tool automates the monthly extraction of Real-Time Settlement Point Price (RTSPP) data for four ERCOT load zones from SAP ISU. It replaces the manual VBA macro previously run inside `RTSPP_Extract_Tool_DW.xlsm`. The extracted data is used to support the Annual EFL POLR Filing.

---

## 2. What the Tool Does

### Step 1 — Date Population (automatic)
The script checks today's date and automatically targets the **previous calendar month**. It writes the following fields into the `ReadMe` sheet of the Excel workbook — no manual date entry is needed.

| Cell | Value Written | Example (run in March 2026) |
|------|--------------|------------------------------|
| A1   | Last day of prior month | 2/28/2026 |
| B1   | Month + Year label | February 2026 |
| A2   | YYYY - MM MonthName | 2026 - 02 February |
| B2   | YYYYMMDD of last day | 20260228 |
| C2   | First day of prior month | 2/1/2026 |
| E2   | Output filename | 20260228_RTSPP_Extract.xlsx |
| B3   | Year | 2026 |

### Step 2 — SAP Data Extract (automatic)
The script launches SAP GUI, connects to **TXUE ISU Prod**, and navigates to transaction `/NEEDM08`. It then pulls RTSPP data for the following four load zone profiles in sequence:

| Load Zone | SAP Profile ID |
|-----------|---------------|
| LZ_Houston | 400000003 |
| LZ_North   | 400000000 |
| LZ_South   | 400000001 |
| LZ_West    | 400000002 |

For each zone, the script:
- Sets the profile ID and date range in SAP
- Refreshes the data tree and opens the EDM Profile export
- Copies the interval price data from the SAP-opened Excel file into the `Extract` sheet of `RTSPP_Extract_Tool_DW.xlsm`
- Hides the temporary SAP workbook

### Step 3 — Review (manual)
The user reviews the `Extract` sheet to confirm the dates and data look correct before saving.

### Step 4 — Save to Network Share (semi-automatic)
A second batch file copies the `Extract` sheet into a standalone `.xlsx` file and saves it to:

```
\\ddcnasshares\c_product\RATE MANAGEMENT\aaaa_LARR_POLR\
  Annual EFL POLR Filing\{YEAR} EFL Filing\Monthly Extracts\
```

The filename is auto-generated (e.g., `20260228_RTSPP_Extract.xlsx`). If the year folder or `Monthly Extracts` subfolder does not yet exist on the share, the script creates them automatically before saving.

---

## 3. Prerequisites

### Software Required
| Requirement | Notes |
|------------|-------|
| Python 3.x | Must be installed and on PATH |
| pywin32 library | Install once via: `pip install pywin32` |
| SAP GUI | Must be installed at `C:\Program Files (x86)\SAP\FrontEnd\SAPgui\` |
| SAP GUI Scripting | Must be enabled in SAP GUI Options → Accessibility & Scripting |
| Microsoft Excel | Must be open with `RTSPP_Extract_Tool_DW.xlsm` loaded |
| Network access | Must have access to `\\ddcnasshares\...` for the save step |

### SAP Access Required
- Active login credentials for **TXUE ISU Prod**
- Access to transaction `/NEEDM08`

---

## 4. Files

| File | Location | Purpose |
|------|----------|---------|
| `rtspp_extract.py` | `RTSPP\` | Main Python script |
| `run_rtspp_extract.bat` | `RTSPP\` | Runs the SAP extract |
| `save_rtspp_extract.bat` | `RTSPP\` | Saves the extract to the network share |
| `RTSPP_Extract_Tool_DW.xlsm` | User's working folder | Source Excel workbook (not in this repo) |

---

## 5. Timing

- Run between the **2nd and 5th of each month**
- Data for the prior month is not complete in SAP until the overnight batch filing runs on the 2nd
- Do not run on the 1st — data will be incomplete

---

## 6. Troubleshooting

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `Excel is not open` | Workbook not loaded | Open Excel and `RTSPP_Extract_Tool_DW.xlsm` before running |
| `Could not find RTSPP_Extract_Tool_DW` | Wrong filename or not open | Confirm exact filename matches |
| `EDM Profile workbook not found` | SAP did not export in time | SAP may be slow — re-run; increase `time.sleep` in script if persistent |
| SAP login prompt appears | Not logged into SAP | Log into SAP ISU Prod manually before running the batch file |
| `Permission denied` on save | No access to network share | Confirm VPN is connected and share path is accessible |
| Data appears in wrong columns | SAP EDM Profile layout changed | Contact the script owner — column mappings may need updating |

---

## 7. Contact / Escalation

For SAP running errors, see the `ReadMe` sheet in `RTSPP_Extract_Tool_DW.xlsm` — escalation contact is noted there.
