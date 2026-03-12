# Chat History — 2026-03-11 22:06
# Topic: VBB PCRF Product Build

---

**User:** This chat should be called VBB PCRF product build. In the Claude folder, I created a folder called pcrf with several files and a text file that is SAP HANA code. I want to determine existing product codes and create new ones. I gave you all of the tables and would like you to review and improve the code. It's not using the Hierarchy column. The channel column is represented by the 11th character of the product code. The new product code should use the letter in the Hierarchy column of NEW_PCRF_VBB. When searching for an existing product code it should first look for same product with same term and hierarchy. If none exists, the new product code should become the AA version based on Product_Naming_Sequence, then search for same term but different hierarchy. If that doesn't exist, search for same product name with 12 or 24 month term and any hierarchy.

**Claude:** Reviewed all 6 files in pcrf/:
- `CREATE_NEW_VBB_PRODS.txt` — original SAP HANA SQL (CREATE TABLE AS SELECT)
- `CREATE_NEW_VBB_PRODS.xlsx` — 612 rows, current output
- `CXT_SFDC_PRODUCT_MASTER.xlsx` — 15,752 rows, 80 columns, existing SFDC products
- `NEW_PCRF_VBB.xlsx` — 612 rows, new products to build
- `PRODUCT_NAMING_SEQUENCE.csv` — 677 rows, alpha/numeric sequence lookup (AA→AB→...→ZZ→AAA)
- `TBL100_TDU_PREFIX.xlsx` — 10 rows, TDU name-to-prefix mapping

Asked 5 clarifying questions before rewriting.

---

**User (Q&A round 1):**
1. Hierarchy column in NEW_PCRF_VBB = `Hierarchy`, value = `A` (all new products get char 11 = A)
2. Term column = `TERM__C` (double underscore). Product_Name__C and Term__C should be consistent — acknowledged data issue to fix.
3. "AA version" = sequence order 1 (first in PRODUCT_NAMING_SEQUENCE)
4. New code structure: new TDU prefix (chars 1-2) + core chars 3-10 from template + Hierarchy char 11 + term + new suffix. Cross-TDSP example: Oncor Basic 12 "AF" exists but building AEPTCC version → prefix=TC, char11=A, suffix=AA
5. PRODUCT_NAME__C format matches exactly between both tables

---

**User (Q&A round 2 — cross-TDSP and brand new):**
1. When no match for that TDSP at all → look at different TDSP, but use new product's TDSP__C for code structure
2. Term matching: use TERM__C from NEW_PCRF_VBB against PRODUCT_TERM__C in SFDC master
3. Truly brand new products: add one column `CODE_CORE__C` (8 chars) to NEW_PCRF_VBB — non-null = brand new flag + provides chars 3-10 directly

**Claude:** Proposed and confirmed 6-level cascade:
| Level | Scope | Match | Suffix |
|---|---|---|---|
| L1 | Same TDSP | Same name + term + hierarchy | INCREMENT |
| L2 | Same TDSP | Same name + term + diff hierarchy | RESET AA |
| L3 | Same TDSP | Same name + 12/24 month term | RESET AA |
| L4 | Any TDSP | Same name + same term | RESET AA |
| L5 | Any TDSP | Same name + 12/24 month term | RESET AA |
| L6 | Brand new | CODE_CORE__C provided | RESET AA |

---

**User (Q&A round 3 — final confirmation):**
1. One-column approach confirmed (`CODE_CORE__C`)
2. Term: TERM__C is authoritative for both product name and code
3. INCR_COUNT must now partition by name + TDSP + term + hierarchy (e.g., 4 Oncor Basic 12 with hierarchy B increment independently from 2 with hierarchy D)

---

**Claude:** Wrote `pcrf/CREATE_NEW_VBB_PRODS_v2.txt` — full rewrite using 5 CTEs:
- CTE 1 `NEW_PRODS`: normalize TDSP, attach TDU prefix, ROW_NUMBER partitioned by name+TDSP+term+hierarchy
- CTE 2 `SFDC_PRODS`: filtered SFDC master, extracts char 11 as CODE_HIER
- CTE 3 `MATCHED`: 5 scalar subqueries (L1–L5) per row
- CTE 4 `RESOLVED`: COALESCE to best template, determine SUFFIX_MODE/CORE_CHARS/SUFFIX_TYPE/BASE_ORDER
- CTE 5 `BUILT`: constructs final code as NEW_TDU_PREFIX + CORE_CHARS + HIERARCHY + LPAD(TERM,2) + sequence lookup

Committed and pushed.

---

**User:** I want the Python code to log on to SAP HANA. I will provide a YAML with credentials. Keep original table names. YAML is in the Claude folder titled config-HANA-Prod.yaml.

**Claude:** Read YAML structure: `hana.username`, `hana.password`, `hana.host` (vhvcspahdb.sap.txuer.net), `hana.port` (30241).

Built:
- `pcrf/build_vbb_products.py`: reads config-HANA-Prod.yaml, connects via hdbcli, drops + rebuilds CREATE_NEW_VBB_PRODS, prints row count and 10-row preview
- `pcrf/run_build_vbb.bat`: installs hdbcli + pyyaml, runs the Python script
- Added `config-HANA-Prod.yaml` to `.gitignore` to protect credentials

Committed and pushed.

---

**User:** Yes (add to launcher), and don't forget to add all of this to our Chat History.

**Claude:** Added `Build VBB Products` card to launcher under new **PCRF** group (red, database icon). Saved this chat history file. Committed and pushed everything.
