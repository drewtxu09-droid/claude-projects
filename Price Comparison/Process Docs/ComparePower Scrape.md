# ComparePower Electricity Rate Scrape
## Standard Operating Procedure & Process Document

**Document Owner:** Price Comparison Team
**Last Updated:** March 9, 2026
**Version:** 2.0

---

## 1. Purpose

This document outlines the standard operating procedure for running automated electricity rate scrapes from [comparepower.com](https://www.comparepower.com) for zip code **76051**. The scrape tools collect all available electricity plans, sort them by monthly bill estimate (1,000 kWh usage), and produce formatted Excel reports that highlight a specific provider's pricing position relative to the market.

Two scrape tools are maintained:

| Tool | Provider Focus | Highlight Color | Output Folder |
|---|---|---|---|
| `ComparePower_4CHE_Scrape.py` | 4Change Energy | Light Purple | `4CHE/` |
| `ComparePower_TXUE_Scrape.py` | TXU Energy | Yellow | `TXUE/` |

---

## 2. System Requirements

Before running either scrape tool, confirm the following are installed and up to date:

- **Python 3.x** — installed at `C:/Users/XV1S/AppData/Local/Programs/Python/Python314/`
- **Google Chrome** — must be installed and up to date
- **ChromeDriver** — managed automatically via Selenium
- **Python Packages:**
  - `selenium`
  - `pandas`
  - `openpyxl`

To verify packages are installed, open a terminal and run:
```
pip show selenium pandas openpyxl
```

---

## 3. File & Folder Structure

```
Price Comparison/
├── ComparePower_4CHE_Scrape.py       ← 4Change Energy scrape script
├── ComparePower_TXUE_Scrape.py       ← TXU Energy scrape script
├── run_4CHE_alert.bat                ← Batch file to run 4CHE scrape (used by Task Scheduler)
├── setup_scheduled_tasks.bat         ← Run once (as admin) to register daily scheduled tasks
├── 4CHE/                             ← 4Change Energy output files
│   ├── ComparePower_4CHE_76051_YYYYMMDD_HHMMam/pm.xlsx
│   └── scrape_log.txt                ← Auto-generated log of all scheduled runs
├── TXUE/                             ← TXU Energy output files
│   └── ComparePower_TXUE_76051_YYYYMMDD_HHMMam/pm.xlsx
└── Process Docs/
    └── ComparePower Scrape.md        ← This document

OneDrive - Vistra Corp/
└── ComparePower Alerts/              ← Trigger files written here when 4Change is NOT #1
    └── alert_YYYYMMDD_HHMMSS.json   ← Picked up by Power Automate → Teams alert sent
```

---

## 4. How the Scrape Works

### Step-by-Step Automation Flow

1. **Launch headless Chrome** — The browser runs invisibly in the background (no window appears).
2. **Navigate to comparepower.com** — The tool opens the homepage automatically.
3. **Enter zip code 76051** — The tool locates the zip code input field and types the zip code.
4. **Click "Click to Compare"** — Submits the zip code to retrieve available plans.
5. **Select "All Plans"** — Handles the plan-type prompt that appears, selecting all plan types.
6. **Wait for plans to load** — Waits for the Quasar/Vue plan cards to render fully.
7. **Scroll through the page** — Scrolls to ensure all lazy-loaded content is captured.
8. **Scrape all plan cards** — Extracts provider, plan name, price (¢/kWh), monthly bill estimate ($), and contract length from each card.
9. **Build and save Excel report** — Sorts, ranks, and formats results into a timestamped Excel file.

### Data Extracted Per Plan

| Field | Description |
|---|---|
| Rank | Position after sorting by monthly bill estimate (lowest = #1) |
| Provider | Electricity provider name (from provider logo) |
| Plan Name | Name of the specific plan |
| Price (¢/kWh) | Effective rate in cents per kilowatt-hour |
| Bill Est. ($) | Estimated monthly bill at 1,000 kWh usage |
| Contract | Contract length (e.g., 12 months, Month-to-month) |
| vs #1 Price (¢/kWh) | How much more/less per kWh vs the cheapest plan |
| vs #1 Bill ($) | How much more/less per month vs the cheapest plan |

---

## 5. Running the Scrape Tools

### Option A — Run via Terminal (Recommended)

1. Open a **Command Prompt** or **PowerShell** window.
2. Navigate to the Price Comparison folder:
   ```
   cd "C:\Users\XV1S\Desktop\Claude\Price Comparison"
   ```
3. Run the desired scrape tool:

   **4Change Energy:**
   ```
   python ComparePower_4CHE_Scrape.py
   ```

   **TXU Energy:**
   ```
   python ComparePower_TXUE_Scrape.py
   ```

   **Both at once (sequential):**
   ```
   python ComparePower_4CHE_Scrape.py && python ComparePower_TXUE_Scrape.py
   ```

### Option B — Run via Batch File

Double-click `run_4CHE_alert.bat` in the `Price Comparison` folder. This runs the 4CHE scrape and logs all output to `4CHE/scrape_log.txt`. This is the same method used by the scheduled tasks.

### Option C — Run via Claude Code (AI Terminal)

Open Claude Code and paste the run command into the chat terminal. Claude can execute both scripts and report results directly.

### Expected Runtime

Each scrape takes approximately **60–90 seconds** to complete from launch to saved file.

---

## 6. Understanding the Output File

### File Naming Convention

```
ComparePower_[PROVIDER]_[ZIP]_[DATE]_[TIME].xlsx
```

**Example:**
```
ComparePower_4CHE_76051_20260309_650pm.xlsx
```

| Segment | Meaning |
|---|---|
| `4CHE` or `TXUE` | Provider focus of the scrape |
| `76051` | Zip code scraped |
| `20260309` | Date run (YYYYMMDD) |
| `650pm` | Time run (no leading zero, am/pm) |

### Excel Formatting

| Color | Meaning |
|---|---|
| **Dark Blue header** | Column headers |
| **Green row** | The #1 cheapest plan overall |
| **Yellow row** (TXUE file) | All TXU Energy plans |
| **Light Purple row** (4CHE file) | All 4Change Energy plans |

### Column G — vs #1 Price (¢/kWh)

Shows how many cents per kWh more (or less) this plan costs compared to the #1 cheapest plan.
- `0¢` = this plan IS the cheapest
- `+6.10¢` = costs 6.10¢/kWh more than #1

### Column H — vs #1 Bill ($)

Shows the estimated monthly dollar difference vs the #1 cheapest plan at 1,000 kWh usage.
- `$0.00` = same monthly cost as #1
- `+$61.86` = costs $61.86/month more than #1

---

## 7. Sorting Logic

Plans are sorted by **monthly bill estimate (1,000 kWh)** — the same sort order shown on comparepower.com. This is the most customer-relevant metric because it accounts for fixed fees and tiered rates, not just the per-kWh price alone. Two plans with the same ¢/kWh rate may have different monthly bill estimates due to base charges.

---

## 8. Changing the Zip Code

To run either scrape for a different zip code:

1. Open the desired script in a text editor.
2. Find line near the top:
   ```python
   ZIP_CODE = "76051"
   ```
3. Replace `76051` with the new zip code.
4. Save the file and run normally.

Note: The output file name and comparison URL will update automatically to reflect the new zip code.

---

## 9. Troubleshooting

| Issue | Likely Cause | Resolution |
|---|---|---|
| `No plans extracted` | Site layout changed or slow load | Re-run the script; if persistent, notify the developer |
| `ChromeDriver error` | Chrome updated but ChromeDriver is stale | Update Chrome or run `pip install --upgrade selenium` |
| `Permission denied` on Excel file | Output file is currently open in Excel | Close the file in Excel and re-run |
| `ModuleNotFoundError` | Missing Python package | Run `pip install [package-name]` |
| Fewer plans than expected (e.g., <100) | "All Plans" prompt not clicked in time | Re-run; if persistent, check comparepower.com manually |
| Plan counts change between runs | comparepower.com updated their listings | Normal — provider plans change regularly |

---

## 10. Maintenance Notes

- **Scripts are tied to comparepower.com's current page structure.** If the site undergoes a major redesign, selectors may need to be updated by the developer.
- **Each run creates a new timestamped file.** Old files are not overwritten or deleted automatically — archive or delete old reports periodically.
- **Provider logos drive provider name detection.** If a new provider appears with an unrecognized logo slug, the name may appear abbreviated. This can be corrected by adding an entry to the `PROVIDER_SLUG_MAP` dictionary in the script.

---

## 11. Contact / Support

For script issues, changes to zip codes, new provider tracking, or additional report formats, contact the developer or submit a request through Claude Code.

---

## 12. Automated Scheduling & Alerts (4CHE Only)

The 4Change Energy scrape is configured to run automatically **three times per day** via Windows Task Scheduler, and send a **Microsoft Teams alert** whenever 4Change is not the #1 ranked provider.

### Scheduled Run Times

| Task Name | Time |
|---|---|
| ComparePower 4CHE 8am | 8:00 AM daily |
| ComparePower 4CHE 12pm | 12:00 PM daily |
| ComparePower 4CHE 5pm | 5:00 PM daily |

### How the Alert Works

1. The scrape runs at each scheduled time via `run_4CHE_alert.bat`
2. If 4Change Energy is **not ranked #1**, the script writes a JSON file to:
   ```
   C:\Users\XV1S\OneDrive - Vistra Corp\ComparePower Alerts\
   ```
3. Power Automate detects the new file via an **OneDrive for Business** trigger
4. Power Automate posts a Teams message to `drew.wilburn@txu.com` via Flow bot with:
   - 4Change's current rank, plan name, price, and estimated bill
   - The #1 provider's name, price, and estimated bill
   - Timestamp of the check
5. Power Automate deletes the trigger file after sending

If 4Change **is** #1, no alert is sent and no file is written.

### Setting Up the Scheduled Tasks (One-Time)

1. Navigate to `C:\Users\XV1S\Desktop\Claude\Price Comparison\`
2. **Right-click** `setup_scheduled_tasks.bat` → **Run as administrator**
3. Three tasks will be registered in Windows Task Scheduler automatically
4. To verify: open **Task Scheduler** → check under Task Scheduler Library for the three `ComparePower 4CHE` tasks

### Viewing the Run Log

All scheduled runs append output to:
```
C:\Users\XV1S\Desktop\Claude\Price Comparison\4CHE\scrape_log.txt
```
Check this file to confirm the scrape ran and see what rank 4Change received.

### Changing the Schedule

To update run times or add/remove runs:
1. Open **Task Scheduler** (search in Start menu)
2. Find the task under Task Scheduler Library
3. Double-click → **Triggers** tab → edit the time
4. Or delete and re-run `setup_scheduled_tasks.bat` after editing the times in that file

---

## 13. Power Automate Flow Setup — Step-by-Step Guide

This section documents how to build or rebuild the Power Automate flow that sends the Teams alert. Follow these steps exactly.

### Prerequisites

- Access to [make.powerautomate.com](https://make.powerautomate.com) with your Vistra/TXU credentials
- The folder `C:\Users\XV1S\OneDrive - Vistra Corp\ComparePower Alerts\` must exist (create it if not)

---

### Step 1 — Create a New Flow

1. Go to [make.powerautomate.com](https://make.powerautomate.com)
2. In the left sidebar, click **"My flows"**
3. Click **"+ New flow"** at the top
4. Select **"Automated cloud flow"**
5. In the dialog:
   - **Flow name:** `ComparePower 4CHE Alert`
   - **Search for a trigger:** type `when a file is created`
   - Select **"When a file is created (OneDrive for Business)"**
6. Click **"Create"**

---

### Step 2 — Configure the Trigger

You are now in the flow editor. The first step is the OneDrive trigger.

1. Click on the **"When a file is created (OneDrive for Business)"** trigger card to expand it
2. Click the **Folder** field
3. Click the folder icon that appears to the right of the field
4. Browse and select: **ComparePower Alerts**
5. Leave all other settings as default

---

### Step 3 — Add "Get File Content"

1. Click **"+ New step"** below the trigger
2. In the search bar, type: `get file content`
3. Under **OneDrive for Business**, select **"Get file content (OneDrive for Business)"**
4. Click the **File** field
5. In the dynamic content panel that appears on the right, click **"Path"** (listed under the trigger)
   - The field will show `Path` as a blue dynamic content pill

---

### Step 4 — Add "Parse JSON"

1. Click **"+ New step"**
2. Search for: `parse json`
3. Select **"Parse JSON"** (Data Operations)
4. Click the **Content** field
5. Click **"Expression"** tab (next to "Dynamic content" tab) in the panel on the right
6. Paste this expression exactly:
   ```
   base64ToString(body('Get_file_content')?['$content'])
   ```
7. Click **"OK"**
8. Click the **Schema** field and paste this entire block:
   ```json
   {
     "type": "object",
     "properties": {
       "rank": {"type": "integer"},
       "plan": {"type": "string"},
       "price": {"type": "number"},
       "bill": {"type": "number"},
       "leader": {"type": "string"},
       "leader_price": {"type": "number"},
       "leader_bill": {"type": "number"},
       "timestamp": {"type": "string"}
     }
   }
   ```

---

### Step 5 — Add the Teams Message

1. Click **"+ New step"**
2. Search for: `post message in a chat`
3. Select **"Post message in a chat or channel (Microsoft Teams)"**
4. Set the fields as follows:

   | Field | Value |
   |---|---|
   | Post as | Flow bot |
   | Post in | Chat with Flow bot |
   | Recipient | `drew.wilburn@txu.com` |

5. Click in the **Message** field and build the message by typing text and inserting dynamic content fields (click the **Dynamic content** tab, then click the field name to insert it as a pill):

   ```
   ⚠️ 4Change Energy is NOT #1 on ComparePower (76051)

   Rank: #[rank]
   Plan: [plan]
   Price: [price]¢/kWh | Est. Bill: $[bill]/mo

   Currently #1: [leader] at [leader_price]¢/kWh ($[leader_bill]/mo)
   Checked: [timestamp]
   ```

   Replace each `[bracketed]` item with the matching dynamic content pill from the **Parse JSON** section.

---

### Step 6 — Add "Delete File" (Cleanup)

1. Click **"+ New step"**
2. Search for: `delete file`
3. Under **OneDrive for Business**, select **"Delete file (OneDrive for Business)"**
4. Click the **File** field
5. In the dynamic content panel, click **"Path"** (from the trigger, not Parse JSON)
   - This ensures the trigger file is deleted after the alert is sent

---

### Step 7 — Save and Test

1. Click **"Save"** in the top right
2. To test manually:
   - Copy any small `.json` file into `C:\Users\XV1S\OneDrive - Vistra Corp\ComparePower Alerts\`
   - Wait ~30–60 seconds for OneDrive to sync and the flow to trigger
   - Check your Teams chat with Flow bot for the message
   - Check the folder — the file should be deleted automatically
3. Alternatively, run `run_4CHE_alert.bat` when 4Change is not #1 and wait for the alert

---

### Troubleshooting the Flow

| Issue | Likely Cause | Resolution |
|---|---|---|
| Flow doesn't trigger | File didn't sync to OneDrive cloud | Check OneDrive sync status in system tray; ensure sync is not paused |
| "Expression invalid" error | Typo in the base64 expression | Re-paste: `base64ToString(body('Get_file_content')?['$content'])` |
| Teams message not received | Wrong recipient or Flow bot not accepted | Confirm `drew.wilburn@txu.com` is correct; open Teams and accept the Flow bot chat if prompted |
| File not deleted | Delete step not configured with trigger Path | Ensure Delete file uses Path from the trigger (Step 1), not Parse JSON |
| Flow ran but message is blank | Dynamic content fields not linked | Re-open the Teams step and re-link each field to Parse JSON dynamic content |

---

*End of Document*
