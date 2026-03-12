-- ============================================================
-- CREATE_NEW_VBB_PRODS_v2_HANA.sql
-- Run directly in SAP HANA Studio or SQL Console.
--
-- Execute all three sections in order:
--   Section 1 — Drop existing table (safe, no error if missing)
--   Section 2 — Build new table with 6-level cascade logic
--   Section 3 — Verify row count and preview results
--
-- New product code structure:
--   Chars  1-2  : TDU prefix       (from TBL100_TDU_PREFIX via NEW_PCRF_VBB.TDSP__C)
--   Chars  3-10 : Core descriptor  (from matched template or CODE_CORE__C if brand new)
--   Char   11   : Hierarchy        (always from NEW_PCRF_VBB.Hierarchy column)
--   Chars 12-13 : Term             (from NEW_PCRF_VBB.TERM__C, zero-padded to 2 digits)
--   Last 2 or 3 : Sequence suffix  (alpha: AA..ZZ | numeric: 001..677)
--
-- Cascade levels:
--   L1: Same TDSP + same name + same term + same hierarchy  → INCREMENT from existing
--   L2: Same TDSP + same name + same term + diff hierarchy  → RESET to AA / 001
--   L3: Same TDSP + same name + 12 or 24 month term        → RESET to AA / 001
--   L4: Any  TDSP + same name + same term                  → RESET to AA / 001 (cross-TDSP)
--   L5: Any  TDSP + same name + 12 or 24 month term        → RESET to AA / 001 (cross-TDSP)
--   L6: CODE_CORE__C populated in NEW_PCRF_VBB             → RESET to AA / 001 (brand new)
--
-- Prerequisites:
--   NEW_PCRF_VBB must have a CODE_CORE__C column (NVARCHAR 8).
--   Populate CODE_CORE__C only for truly brand-new products.
--   Leave NULL for all other rows — cascade derives core automatically.
--   Rows with no cascade match AND no CODE_CORE__C → PRODUCTCODE__C will be NULL.
-- ============================================================


-- ============================================================
-- SECTION 1: Drop existing output table (safe — no error if absent)
-- ============================================================
DO BEGIN
    DECLARE lv_count INT;
    SELECT COUNT(*) INTO lv_count
      FROM SYS.TABLES
     WHERE SCHEMA_NAME = 'XV1S'
       AND TABLE_NAME  = 'CREATE_NEW_VBB_PRODS';
    IF lv_count > 0 THEN
        EXEC 'DROP TABLE "XV1S"."CREATE_NEW_VBB_PRODS"';
    END IF;
END;


-- ============================================================
-- SECTION 2: Build CREATE_NEW_VBB_PRODS
-- ============================================================
CREATE TABLE "XV1S"."CREATE_NEW_VBB_PRODS" AS (

WITH

-- ============================================================
-- CTE 1: NEW_PRODS
--   Normalize NEW_PCRF_VBB:
--   - Map abbreviated TDSP__C to SFDC full-name format (NORM_TDSP)
--   - Attach TDU prefix from TBL100_TDU_PREFIX (chars 1-2 of new code)
--   - Assign row number per group (name + TDSP + term + hierarchy)
--     so multiple new products in the same group each get a unique
--     sequence increment
-- ============================================================
NEW_PRODS AS (
    SELECT
        NP.PRODUCT_NAME__C,
        NP.TERM__C,
        NP.HIERARCHY,
        NP.TDSP__C                              AS NEW_TDSP,
        NP.CODE_CORE__C,
        TDUP.TDU_PREFIX                         AS NEW_TDU_PREFIX,
        CASE
            WHEN UPPER(TRIM(NP.TDSP__C)) = 'ONC'  THEN 'ONCOR'
            WHEN UPPER(TRIM(NP.TDSP__C)) = 'CNP'  THEN 'CENTERPOINT'
            WHEN UPPER(TRIM(NP.TDSP__C)) = 'AEPC' THEN 'AEP CENTRAL'
            WHEN UPPER(TRIM(NP.TDSP__C)) = 'AEPN' THEN 'AEP NORTH'
            WHEN UPPER(TRIM(NP.TDSP__C)) = 'TNMP' THEN 'TNMPOWER'
            WHEN UPPER(TRIM(NP.TDSP__C)) = 'LPL'  THEN 'LUBBOCK'
            ELSE UPPER(TRIM(NP.TDSP__C))
        END                                     AS NORM_TDSP,
        ROW_NUMBER() OVER (
            PARTITION BY NP.PRODUCT_NAME__C,
                         NP.TDSP__C,
                         NP.TERM__C,
                         NP.HIERARCHY
            ORDER BY NP.PRODUCT_NAME__C
        )                                       AS INCR_COUNT
    FROM "XV1S"."NEW_PCRF_VBB"       NP
    JOIN "XV1S"."TBL100_TDU_PREFIX"  TDUP
      ON UPPER(TRIM(NP.TDSP__C)) = UPPER(TRIM(TDUP.TDU_AB))
),

-- ============================================================
-- CTE 2: SFDC_PRODS
--   Filtered and normalized view of the SFDC product master:
--   - Brand filter: 4CHE, EXPR, VTRE
--   - Exclude codes starting with S or TNTEXCH
--   - Exclude deleted records
--   - Extract hierarchy char from position 11 of product code
--   - Normalize TDSP and term to VARCHAR for consistent joining
-- ============================================================
SFDC_PRODS AS (
    SELECT
        UPPER(TRIM(PRODUCT_NAME__C))         AS PRODUCT_NAME__C,
        PRODUCTCODE__C,
        UPPER(TRIM(TDSP__C))                 AS TDSP__C,
        CAST(PRODUCT_TERM__C AS NVARCHAR)    AS PRODUCT_TERM,
        SUBSTRING(PRODUCTCODE__C, 11, 1)     AS CODE_HIER
    FROM "SFDC"."CXT_SFDC_PRODUCT_MASTER"
    WHERE BRAND__C IN ('4CHE', 'EXPR', 'VTRE')
      AND PRODUCTCODE__C NOT LIKE 'S%'
      AND PRODUCTCODE__C NOT LIKE 'TNTEXCH%'
      AND ISDELETED = 'false'
),

-- ============================================================
-- CTE 3: MATCHED
--   For each row in NEW_PRODS, run 5 correlated subqueries to
--   find the best existing product code across cascade levels.
--   Each subquery returns MAX(PRODUCTCODE__C) for the match
--   criteria — MAX gives the lexicographically latest code,
--   which represents the most recently created version.
--
--   L1 → same TDSP, same name, same term, same hierarchy (INCREMENT)
--   L2 → same TDSP, same name, same term, diff hierarchy  (RESET)
--   L3 → same TDSP, same name, 12 or 24 month term        (RESET)
--   L4 → any  TDSP, same name, same term                  (RESET, cross-TDSP)
--   L5 → any  TDSP, same name, 12 or 24 month term        (RESET, cross-TDSP)
-- ============================================================
MATCHED AS (
    SELECT
        N.*,

        -- L1: Same TDSP | same name | same term | same hierarchy → INCREMENT
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C = UPPER(TRIM(N.PRODUCT_NAME__C))
            AND E.TDSP__C         = N.NORM_TDSP
            AND E.PRODUCT_TERM    = CAST(N.TERM__C AS NVARCHAR)
            AND E.CODE_HIER       = N.HIERARCHY
        ) AS L1_CODE,

        -- L2: Same TDSP | same name | same term | different hierarchy → RESET
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C = UPPER(TRIM(N.PRODUCT_NAME__C))
            AND E.TDSP__C         = N.NORM_TDSP
            AND E.PRODUCT_TERM    = CAST(N.TERM__C AS NVARCHAR)
            AND E.CODE_HIER      != N.HIERARCHY
        ) AS L2_CODE,

        -- L3: Same TDSP | same name | 12 or 24 month term | any hierarchy → RESET
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C = UPPER(TRIM(N.PRODUCT_NAME__C))
            AND E.TDSP__C         = N.NORM_TDSP
            AND E.PRODUCT_TERM    IN ('12', '24')
        ) AS L3_CODE,

        -- L4: Any TDSP | same name | same term | any hierarchy → RESET (cross-TDSP fallback)
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C = UPPER(TRIM(N.PRODUCT_NAME__C))
            AND E.PRODUCT_TERM    = CAST(N.TERM__C AS NVARCHAR)
        ) AS L4_CODE,

        -- L5: Any TDSP | same name | 12 or 24 month term | any hierarchy → RESET (cross-TDSP fallback)
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C = UPPER(TRIM(N.PRODUCT_NAME__C))
            AND E.PRODUCT_TERM    IN ('12', '24')
        ) AS L5_CODE

    FROM NEW_PRODS N
),

-- ============================================================
-- CTE 4: RESOLVED
--   Consolidate cascade results into a single template code and
--   compute the metadata needed to build the final product code:
--
--   TEMPLATE_CODE : first non-null code from L1→L5
--   SUFFIX_MODE   : INCREMENT (L1 matched) or RESET (all others)
--   CORE_CHARS    : chars 3-10 — from CODE_CORE__C if brand new,
--                   else extracted from TEMPLATE_CODE
--   SUFFIX_TYPE   : ALPHA (ends in letter) or NUM (ends in digit)
--   BASE_ORDER    : position in PROD_NAMING_SEQ to increment from
--                   (0 in RESET mode → INCR_COUNT=1 yields AA/001)
-- ============================================================
RESOLVED AS (
    SELECT
        M.*,

        COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                 M.L4_CODE, M.L5_CODE)              AS TEMPLATE_CODE,

        CASE
            WHEN M.L1_CODE IS NOT NULL THEN 'INCREMENT'
            ELSE 'RESET'
        END                                          AS SUFFIX_MODE,

        -- Core chars 3-10
        CASE
            WHEN M.CODE_CORE__C IS NOT NULL
                THEN M.CODE_CORE__C
            WHEN COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                          M.L4_CODE, M.L5_CODE) IS NOT NULL
                THEN SUBSTRING(
                         COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                                  M.L4_CODE, M.L5_CODE), 3, 8)
            ELSE NULL
        END                                          AS CORE_CHARS,

        -- Suffix type from template (defaults to ALPHA for brand-new)
        CASE
            WHEN COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                          M.L4_CODE, M.L5_CODE) IS NOT NULL
             AND SUBSTRING(COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                                    M.L4_CODE, M.L5_CODE),
                           LENGTH(COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                                           M.L4_CODE, M.L5_CODE)), 1)
                 BETWEEN '0' AND '9'
                THEN 'NUM'
            ELSE 'ALPHA'
        END                                          AS SUFFIX_TYPE,

        -- Base sequence order for INCREMENT mode (0 = start for RESET mode)
        CASE
            WHEN M.L1_CODE IS NOT NULL
             AND SUBSTRING(M.L1_CODE, LENGTH(M.L1_CODE), 1)
                 NOT BETWEEN '0' AND '9'
                THEN (SELECT S."ORDER"
                        FROM "XV1S"."PROD_NAMING_SEQ" S
                       WHERE S."CURRENT" = RIGHT(M.L1_CODE, 2))
            WHEN M.L1_CODE IS NOT NULL
             AND SUBSTRING(M.L1_CODE, LENGTH(M.L1_CODE), 1)
                 BETWEEN '0' AND '9'
                THEN (SELECT S."ORDER_NUM"
                        FROM "XV1S"."PROD_NAMING_SEQ" S
                       WHERE S."CURRENT_NUM" = RIGHT(M.L1_CODE, 3))
            ELSE 0
        END                                          AS BASE_ORDER

    FROM MATCHED M
),

-- ============================================================
-- CTE 5: BUILT
--   Assemble the final product code:
--     NEW_TDU_PREFIX  (chars 1-2)
--     CORE_CHARS      (chars 3-10)
--     HIERARCHY       (char 11)  ← always from NEW_PCRF_VBB.Hierarchy
--     LPAD(TERM,2,'0')(chars 12-13)
--     SEQUENCE SUFFIX (chars 14-15 alpha or 14-16 numeric)
--       looked up in PROD_NAMING_SEQ at position BASE_ORDER + INCR_COUNT
--
--   NULL PRODUCTCODE__C means no template was found and
--   CODE_CORE__C was not provided — requires manual resolution.
-- ============================================================
BUILT AS (
    SELECT
        R.PRODUCT_NAME__C,
        R.TERM__C,
        R.NEW_TDSP                                  AS NTDSP,
        R.NORM_TDSP                                 AS GTDSP,
        R.HIERARCHY,
        R.TEMPLATE_CODE                             AS EXISTING_PRODUCTCODE__C,
        R.SUFFIX_MODE,
        R.INCR_COUNT,

        CASE
            -- No core available: output NULL, review manually
            WHEN R.CORE_CHARS IS NULL
                THEN NULL

            -- Alpha suffix (e.g., AA, AB, ... ZZ)
            WHEN R.SUFFIX_TYPE = 'ALPHA'
                THEN R.NEW_TDU_PREFIX
                  || R.CORE_CHARS
                  || R.HIERARCHY
                  || LPAD(CAST(R.TERM__C AS NVARCHAR), 2, '0')
                  || (SELECT S."CURRENT"
                        FROM "XV1S"."PROD_NAMING_SEQ" S
                       WHERE S."ORDER" = R.BASE_ORDER + R.INCR_COUNT)

            -- Numeric suffix (e.g., 001, 002, ... 677)
            ELSE
                 R.NEW_TDU_PREFIX
              || R.CORE_CHARS
              || R.HIERARCHY
              || LPAD(CAST(R.TERM__C AS NVARCHAR), 2, '0')
              || (SELECT S."CURRENT_NUM"
                    FROM "XV1S"."PROD_NAMING_SEQ" S
                   WHERE S."ORDER_NUM" = R.BASE_ORDER + R.INCR_COUNT)
        END                                         AS PRODUCTCODE__C

    FROM RESOLVED R
)

-- ============================================================
-- Final SELECT
--   SUFFIX_MODE, HIERARCHY, TERM__C, INCR_COUNT are diagnostic
--   columns included to aid first-run validation.
-- ============================================================
SELECT
    B.PRODUCT_NAME__C,
    B.EXISTING_PRODUCTCODE__C,
    B.NTDSP,
    B.GTDSP,
    B.HIERARCHY,
    B.TERM__C,
    B.SUFFIX_MODE,
    B.INCR_COUNT,
    B.PRODUCTCODE__C
FROM BUILT B
ORDER BY
    B.PRODUCT_NAME__C,
    CASE
        WHEN B.NTDSP = 'ONC'  THEN 1
        WHEN B.NTDSP = 'CNP'  THEN 2
        WHEN B.NTDSP = 'AEPC' THEN 3
        WHEN B.NTDSP = 'AEPN' THEN 4
        WHEN B.NTDSP = 'TNMP' THEN 5
        WHEN B.NTDSP = 'LPL'  THEN 6
        WHEN B.NTDSP = 'ALL'  THEN 7
        ELSE 8
    END,
    B.TERM__C,
    B.HIERARCHY,
    B.INCR_COUNT

);


-- ============================================================
-- SECTION 3: Verify results
-- ============================================================

-- Total row count
SELECT COUNT(*) AS TOTAL_ROWS
FROM "XV1S"."CREATE_NEW_VBB_PRODS";

-- Rows where code could not be built (need manual review)
SELECT
    PRODUCT_NAME__C,
    NTDSP,
    TERM__C,
    HIERARCHY,
    EXISTING_PRODUCTCODE__C,
    SUFFIX_MODE
FROM "XV1S"."CREATE_NEW_VBB_PRODS"
WHERE PRODUCTCODE__C IS NULL
ORDER BY PRODUCT_NAME__C, NTDSP;

-- Full results
SELECT *
FROM "XV1S"."CREATE_NEW_VBB_PRODS"
ORDER BY
    PRODUCT_NAME__C,
    CASE
        WHEN NTDSP = 'ONC'  THEN 1
        WHEN NTDSP = 'CNP'  THEN 2
        WHEN NTDSP = 'AEPC' THEN 3
        WHEN NTDSP = 'AEPN' THEN 4
        WHEN NTDSP = 'TNMP' THEN 5
        WHEN NTDSP = 'LPL'  THEN 6
        WHEN NTDSP = 'ALL'  THEN 7
        ELSE 8
    END,
    TERM__C,
    HIERARCHY,
    INCR_COUNT;
