# ComparePower Electricity Rate Scrape
## Standard Operating Procedure & Process Document

**Document Owner:** Price Comparison Team
**Last Updated:** March 9, 2026
**Version:** 1.0

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
├── 4CHE/                             ← 4Change Energy output files
│   └── ComparePower_4CHE_76051_YYYYMMDD_HHMMam/pm.xlsx
├── TXUE/                             ← TXU Energy output files
│   └── ComparePower_TXUE_76051_YYYYMMDD_HHMMam/pm.xlsx
└── Process Docs/
    └── ComparePower Scrape.md        ← This document
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

### Option B — Run via Claude Code (AI Terminal)

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

*End of Document*
