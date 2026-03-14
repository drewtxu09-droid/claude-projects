# Click-Step Guide — VBB PCRF Product Code Build
**Version:** 2.0
**Date:** 2026-03-13

---

## Before You Start — Checklist

- [ ] `NEW_PCRF_VBB.xlsx` is up to date and uploaded to SAP HANA (schema: XV1S)
- [ ] Every row has matching `PRODUCT_NAME__C` and `Term__C` (e.g., "Basic 12" → Term = 12)
- [ ] Brand-new products (no SFDC match under any TDSP, term, or product family) have `Code_Core` filled in (exactly 8 characters)
- [ ] All other rows have `Code_Core` left **blank** (not the word "NULL")
- [ ] `config-HANA-Prod.yaml` is in `C:\Users\XV1S\Desktop\Claude\`

---

## Step 1 — Run the Build

**Option A — Batch file**
1. Open File Explorer
2. Navigate to: `C:\Users\XV1S\Desktop\Claude\PCRF\`
3. Double-click **`run_build_vbb.bat`**
4. A black terminal window opens — wait for it to finish

**What you'll see in the terminal:**
```
Connecting to vhvcspahdb.sap.txuer.net:30241 as xv1s...
Connected.
Dropped existing table: CREATE_NEW_VBB_PRODS     ← or "does not exist yet"
Executing CREATE_NEW_VBB_PRODS_v2 SQL...
Table built successfully.
Rows created: 612

--- Preview (first 10 rows) ---
PRODUCT_NAME__C  EXISTING_PRODUCTCODE__C  NTDSP  GTDSP  ...
```

5. Press any key to close the terminal when done

**Option B — SAP HANA Studio (direct)**
1. Open SAP HANA Studio and connect to the production system
2. Open `CREATE_NEW_VBB_PRODS_v2_HANA.sql` from `C:\Users\XV1S\Desktop\Claude\PCRF\`
3. Select all (Ctrl+A) and run (F8)
4. The script drops, rebuilds, and verifies the table in one pass

---

## Step 2 — Validate in SAP HANA

1. Open SAP HANA Studio or your HANA query tool
2. Run this query to see all results:
   ```sql
   SELECT * FROM "XV1S"."CREATE_NEW_VBB_PRODS"
   ORDER BY PRODUCT_NAME__C;
   ```

3. Check the **`SUFFIX_MODE`** column:
   - `INCREMENT` → new code continues from an existing one ✓
   - `RESET` → new code starts fresh at AA ✓

4. Look for any rows where **`PRODUCTCODE__C` is NULL**:
   ```sql
   SELECT * FROM "XV1S"."CREATE_NEW_VBB_PRODS"
   WHERE PRODUCTCODE__C IS NULL;
   ```
   - If any exist → go to **Step 3**
   - If none → skip to **Step 4**

5. Spot-check a few codes:
   - Chars 1–2 = correct TDU prefix for that TDSP?
   - Char 11 = matches the `Hierarchy` value for that row?
   - Chars 12–13 = correct term digits (zero-padded)?

---

## Step 3 — Fix NULL Product Codes (if needed)

**If the product is truly brand new (never existed in SFDC under any TDSP, term, or related product family):**
1. Open `NEW_PCRF_VBB.xlsx`
2. Find the row(s) with NULL codes
3. Fill in `Code_Core` with exactly 8 characters (positions 3–10 of the desired code)
4. Re-upload `NEW_PCRF_VBB` to SAP HANA
5. Go back to **Step 1** and re-run

**If it's a name or term mismatch:**
1. Open `NEW_PCRF_VBB.xlsx`
2. Correct `PRODUCT_NAME__C` to exactly match the name in SFDC
3. Correct `Term__C` to match the term in the product name
4. Re-upload and re-run from **Step 1**

---

## Step 4 — Export Results

1. In HANA, right-click `CREATE_NEW_VBB_PRODS` → Export → CSV or Excel
2. Save to your desired location for downstream processing

---

## Quick Reference — TDSP Abbreviations

| Use in NEW_PCRF_VBB | Full name in SFDC | TDU Prefix (chars 1-2) |
|---|---|---|
| ONC | ONCOR | ON |
| CNP | CENTERPOINT | CP |
| AEPC | AEP CENTRAL | TC |
| AEPN | AEP NORTH | TN |
| TNMP | TNMPOWER | NM |
| LPL | LUBBOCK | LB |
| ALL | All | (blank) |

---

## Quick Reference — Cascade Match Summary

| What exists in SFDC | Level | Result |
|---|---|---|
| Same TDSP + same name + same term + same hierarchy | L1 | New code = next in sequence after existing |
| Same TDSP + same name + same term + different hierarchy | L2 | New code = AA (uses same TDSP as template) |
| Same TDSP + same name + 12 or 24 month term | L3 | New code = AA (uses same TDSP as template) |
| Different TDSP + same name + same term | L4 | New code = AA (cross-TDSP template, new TDU prefix applied) |
| Different TDSP + same name + 12 or 24 month term | L5 | New code = AA (cross-TDSP template, new TDU prefix applied) |
| Same TDSP + same product family (e.g., "Basic") + 12 or 24 month term | L6 | New code = AA (family fallback, same TDSP) |
| Any TDSP + same product family + 12 or 24 month term | L7 | New code = AA (family fallback, cross-TDSP) |
| Nothing found + `Code_Core` filled in | — | New code = AA (built from scratch) |
| Nothing found + `Code_Core` blank | — | PRODUCTCODE__C = NULL → manual fix required |
