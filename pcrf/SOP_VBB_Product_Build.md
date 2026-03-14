# SOP — VBB PCRF Product Code Build
**Version:** 2.1
**Date:** 2026-03-13
**Purpose:** Generate new VBB product codes in SAP HANA by matching new products from NEW_PCRF_VBB against the existing SFDC Product Master using a 7-level cascade logic.

---

## Overview

This process reads new product definitions from `NEW_PCRF_VBB`, finds the best matching existing product code from `CXT_SFDC_PRODUCT_MASTER`, and constructs a new product code following a strict format. The output is written to a new HANA table called `CREATE_NEW_VBB_PRODS`.

### New Product Code Structure

| Position | Length | Source |
|---|---|---|
| 1–2 | 2 chars | TDU prefix from `TBL100_TDU_PREFIX` based on new product's `TDSP__C` |
| 3–10 | 8 chars | Core descriptor extracted from matched template product (or `Code_Core` if brand new) |
| 11 | 1 char | Hierarchy — always taken from `NEW_PCRF_VBB."Hierarchy"` column |
| 12–13 | 2 chars | Term — from `NEW_PCRF_VBB."Term__C"`, zero-padded (e.g., `12`, `24`, `36`) |
| 14–15 | 2 chars | Sequence suffix — alpha (`AA`→`ZZ`) or numeric (`001`→`677`) |

**Example:** `TCVTBASICAA12AA`
- `TC` = AEP Central prefix
- `VTBASICA` = core descriptor (chars 3–10)
- `A` = Hierarchy
- `12` = 12-month term
- `AA` = first in sequence (new product)

---

## Cascade Match Logic

The script searches for an existing product to use as a structural template in this priority order:

| Level | Search Scope | Match Criteria | Suffix Behavior |
|---|---|---|---|
| L1 | Same TDSP | Same name + same term + same hierarchy | Increment from existing (next in sequence) |
| L2 | Same TDSP | Same name + same term + different hierarchy | Reset to AA / 001 |
| L3 | Same TDSP | Same name + 12 or 24 month term + any hierarchy | Reset to AA / 001 |
| L4 | Any TDSP | Same name + same term + any hierarchy | Reset to AA / 001 (cross-TDSP fallback) |
| L5 | Any TDSP | Same name + 12 or 24 month term + any hierarchy | Reset to AA / 001 (cross-TDSP fallback) |
| L6 | Same TDSP | Base-name family + 12 or 24 month term | Reset to AA / 001 (family fallback) |
| L7 | Any TDSP | Base-name family + 12 or 24 month term | Reset to AA / 001 (family cross-TDSP fallback) |

**Base-name family matching (L6/L7):** The script strips the trailing term number from the product name (e.g., "Basic 15" → base name "BASIC") and looks for any existing product whose name starts with that base name followed immediately by a digit. This prevents "Basic" from accidentally matching "Basic Plus" products.

If no level produces a match and `Code_Core` is also null (or blank), the product code output will be NULL — those rows must be reviewed manually.

---

## Prerequisites

### Source Tables (SAP HANA — schema XV1S and SFDC)
| Table | Schema | Purpose |
|---|---|---|
| `NEW_PCRF_VBB` | XV1S | New products to build — input |
| `CXT_SFDC_PRODUCT_MASTER` | SFDC | Existing products — match source |
| `PROD_NAMING_SEQ` | XV1S | Alpha/numeric sequence lookup |
| `TBL100_TDU_PREFIX` | XV1S | TDU name-to-prefix mapping |

### NEW_PCRF_VBB Required Columns
| Column | Notes |
|---|---|
| `PRODUCT_NAME__C` | Must match `PRODUCT_NAME__C` in SFDC master exactly |
| `Term__C` | Authoritative term — must match the term in the product name |
| `TDSP__C` | Abbreviated TDSP (ONC, CNP, AEPC, AEPN, TNMP, LPL, ALL) |
| `Hierarchy` | Single character — becomes char 11 of all new codes |
| `Code_Core` | 8-char core descriptor — populate ONLY for truly brand-new products with no SFDC match; leave blank otherwise |

> **Note:** Column names are case-sensitive in SAP HANA. Use the exact casing shown above (`Term__C`, `Hierarchy`, `Code_Core`) when querying the table directly.

### Software Requirements
- Python 3.12 at `C:\Users\XV1S\AppData\Local\Programs\Python\Python312\`
- `hdbcli` and `pyyaml` packages (auto-installed by bat file)
- `config-HANA-Prod.yaml` present in `C:\Users\XV1S\Desktop\Claude\`

---

## Process Steps

### Step 1 — Prepare NEW_PCRF_VBB
1. Open `NEW_PCRF_VBB.xlsx` in the `PCRF/` folder
2. Verify every row has consistent `PRODUCT_NAME__C` and `Term__C` (e.g., "Basic 12" should have `Term__C = 12`)
3. For any truly brand-new products (no existing SFDC match expected under any TDSP, term, or product family):
   - Populate `Code_Core` with exactly 8 characters representing positions 3–10 of the desired new code
   - Leave `Code_Core` blank for all other rows
4. Upload / refresh `NEW_PCRF_VBB` in SAP HANA schema `XV1S`

### Step 2 — Run the Build Script

**Option A — Via batch file (recommended for most users)**
1. Navigate to `C:\Users\XV1S\Desktop\Claude\PCRF\`
2. Double-click `run_build_vbb.bat`
3. The script will:
   - Install `hdbcli` and `pyyaml` if not present
   - Connect to SAP HANA at `vhvcspahdb.sap.txuer.net:30241`
   - Drop the existing `CREATE_NEW_VBB_PRODS` table if it exists
   - Execute `CREATE_NEW_VBB_PRODS_v2_HANA.sql`
   - Print row count and a 10-row preview

**Option B — Direct execution in SAP HANA Studio**
1. Open SAP HANA Studio and connect to the production system
2. Open `CREATE_NEW_VBB_PRODS_v2_HANA.sql` from `C:\Users\XV1S\Desktop\Claude\PCRF\`
3. Select all (Ctrl+A) and execute (F8)
4. The script drops, recreates, and verifies `CREATE_NEW_VBB_PRODS` in a single run

### Step 3 — Validate Output
1. In SAP HANA, query `CREATE_NEW_VBB_PRODS`:
   ```sql
   SELECT * FROM "XV1S"."CREATE_NEW_VBB_PRODS" ORDER BY PRODUCT_NAME__C;
   ```
2. Check the `SUFFIX_MODE` column:
   - `INCREMENT` = new code continues from an existing code (L1 match)
   - `RESET` = new code starts at AA/001 (L2–L7 match)
3. Check for NULL `PRODUCTCODE__C` — these rows have no template and no `Code_Core`; they require manual review
4. Verify char 11 of every `PRODUCTCODE__C` matches the `Hierarchy` column value
5. Verify chars 1–2 match the expected TDU prefix for each TDSP

### Step 4 — Handle NULL Codes (if any)
1. For each NULL row, determine whether it is truly brand new or a data mismatch
2. If brand new: add `Code_Core` to `NEW_PCRF_VBB` for that row (8 characters) and re-run
3. If data mismatch: correct `PRODUCT_NAME__C` or `Term__C` in `NEW_PCRF_VBB` to align with SFDC master, then re-run

### Step 5 — Export Results
1. Export `CREATE_NEW_VBB_PRODS` from SAP HANA to Excel as needed for downstream use

---

## Troubleshooting

| Problem | Likely Cause | Resolution |
|---|---|---|
| `ModuleNotFoundError: hdbcli` | Package not installed | Run `run_build_vbb.bat` which installs it automatically |
| `Connection failed` | HANA host/credentials issue | Verify `config-HANA-Prod.yaml` is in the Claude root folder and credentials are current |
| `Table not found` error | Source table missing in HANA | Re-upload the missing table to the correct schema |
| NULL product codes in output | No template found at any cascade level and `Code_Core` is blank | Populate `Code_Core` for brand-new rows or fix name/term mismatch |
| Wrong TDU prefix on new code | `TDSP__C` in `NEW_PCRF_VBB` not matching `TBL100_TDU_PREFIX.TDU_AB` | Check abbreviation format (ONC, CNP, AEPC, AEPN, TNMP, LPL, ALL) |
| Sequence jumps unexpectedly | Multiple rows share same name+TDSP+term+hierarchy | Expected — `ROW_NUMBER()` assigns each row its own increment |
| Short codes (7 chars instead of 15) | `Code_Core` column contains empty strings from Excel import | Leave `Code_Core` blank (not the word "NULL") — the script treats blank as no value |
| Two products get the same core chars | Base-name family match crossing product families (e.g., "Basic" matching "Basic Plus") | The digit-check guard in L6/L7 prevents this; verify product names are distinct |
