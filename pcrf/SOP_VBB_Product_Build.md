# SOP — VBB PCRF Product Code Build
**Version:** 1.0
**Date:** 2026-03-11
**Purpose:** Generate new VBB product codes in SAP HANA by matching new products from NEW_PCRF_VBB against the existing SFDC Product Master using a 6-level cascade logic.

---

## Overview

This process reads new product definitions from `NEW_PCRF_VBB`, finds the best matching existing product code from `CXT_SFDC_PRODUCT_MASTER`, and constructs a new product code following a strict format. The output is written to a new HANA table called `CREATE_NEW_VBB_PRODS`.

### New Product Code Structure

| Position | Length | Source |
|---|---|---|
| 1–2 | 2 chars | TDU prefix from `TBL100_TDU_PREFIX` based on new product's `TDSP__C` |
| 3–10 | 8 chars | Core descriptor extracted from matched template product (or `CODE_CORE__C` if brand new) |
| 11 | 1 char | Hierarchy — always taken from `NEW_PCRF_VBB.Hierarchy` column |
| 12–13 | 2 chars | Term — from `NEW_PCRF_VBB.TERM__C`, zero-padded (e.g., `12`, `24`, `36`) |
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
| L6 | Brand new | `CODE_CORE__C` populated in `NEW_PCRF_VBB` | Reset to AA / 001 |

If no level produces a match and `CODE_CORE__C` is also null, the product code output will be NULL — those rows must be reviewed manually.

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
| `TERM__C` | Authoritative term — must match the term in the product name |
| `TDSP__C` | Abbreviated TDSP (ONC, CNP, AEPC, AEPN, TNMP, LPL, ALL) |
| `Hierarchy` | Single character — becomes char 11 of all new codes |
| `CODE_CORE__C` | 8-char core descriptor — populate ONLY for truly brand-new products with no SFDC match; leave NULL otherwise |

### Software Requirements
- Python 3.12 at `C:\Users\XV1S\AppData\Local\Programs\Python\Python312\`
- `hdbcli` and `pyyaml` packages (auto-installed by bat file)
- `config-HANA-Prod.yaml` present in `C:\Users\XV1S\Desktop\Claude\`

---

## Process Steps

### Step 1 — Prepare NEW_PCRF_VBB
1. Open `NEW_PCRF_VBB.xlsx` in the `PCRF/` folder
2. Verify every row has consistent `PRODUCT_NAME__C` and `TERM__C` (e.g., "Basic 12" should have `TERM__C = 12`)
3. For any truly brand-new products (no existing SFDC match expected under any TDSP or term):
   - Populate `CODE_CORE__C` with exactly 8 characters representing positions 3–10 of the desired new code
   - Leave `CODE_CORE__C` blank for all other rows
4. Upload / refresh `NEW_PCRF_VBB` in SAP HANA schema `XV1S`

### Step 2 — Run the Build Script
1. Navigate to `C:\Users\XV1S\Desktop\Claude\PCRF\`
2. Double-click `run_build_vbb.bat`
3. The script will:
   - Install `hdbcli` and `pyyaml` if not present
   - Connect to SAP HANA at `vhvcspahdb.sap.txuer.net:30241`
   - Drop the existing `CREATE_NEW_VBB_PRODS` table if it exists
   - Execute `CREATE_NEW_VBB_PRODS_v2.txt`
   - Print row count and a 10-row preview

### Step 3 — Validate Output
1. In SAP HANA, query `CREATE_NEW_VBB_PRODS`:
   ```sql
   SELECT * FROM "XV1S"."CREATE_NEW_VBB_PRODS" ORDER BY PRODUCT_NAME__C;
   ```
2. Check the `SUFFIX_MODE` column:
   - `INCREMENT` = new code continues from an existing code (L1 match)
   - `RESET` = new code starts at AA/001 (L2–L6 match)
3. Check for NULL `PRODUCTCODE__C` — these rows have no template and no `CODE_CORE__C`; they require manual review
4. Verify char 11 of every `PRODUCTCODE__C` matches the `Hierarchy` column value
5. Verify chars 1–2 match the expected TDU prefix for each TDSP

### Step 4 — Handle NULL Codes (if any)
1. For each NULL row, determine whether it is truly brand new or a data mismatch
2. If brand new: add `CODE_CORE__C` to `NEW_PCRF_VBB` for that row and re-run
3. If data mismatch: correct `PRODUCT_NAME__C` or `TERM__C` in `NEW_PCRF_VBB` to align with SFDC master, then re-run

### Step 5 — Export Results
1. Export `CREATE_NEW_VBB_PRODS` from SAP HANA to Excel as needed for downstream use

---

## Troubleshooting

| Problem | Likely Cause | Resolution |
|---|---|---|
| `ModuleNotFoundError: hdbcli` | Package not installed | Run `run_build_vbb.bat` which installs it automatically |
| `Connection failed` | HANA host/credentials issue | Verify `config-HANA-Prod.yaml` is in the Claude root folder and credentials are current |
| `Table not found` error | Source table missing in HANA | Re-upload the missing table to the correct schema |
| NULL product codes in output | No template found and `CODE_CORE__C` is null | Populate `CODE_CORE__C` for brand-new rows or fix name/term mismatch |
| Wrong TDU prefix on new code | `TDSP__C` in `NEW_PCRF_VBB` not matching `TBL100_TDU_PREFIX.TDU_AB` | Check abbreviation format (ONC, CNP, AEPC, AEPN, TNMP, LPL, ALL) |
| Sequence jumps unexpectedly | Multiple rows share same name+TDSP+term+hierarchy | Expected — `ROW_NUMBER()` assigns each row its own increment |
