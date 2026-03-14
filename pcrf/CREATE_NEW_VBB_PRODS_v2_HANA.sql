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

--DROP TABLE QRYBUILDSTEP2;


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
--   - Derive BASE_NAME by stripping the trailing term number (e.g.
--     "Basic 15" → "BASIC"), used for L6/L7 family-fallback lookups
-- ============================================================
NEW_PRODS AS (
    SELECT
        NP.PRODUCT_NAME__C,
        NP."Term__C",
        NP."Hierarchy",
        NP.TDSP__C AS NEW_TDSP,
        NP."Code_Core",
        TDUP.TDU_PREFIX AS NEW_TDU_PREFIX,
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
                         NP."Term__C",
                         NP."Hierarchy"
            ORDER BY NP.PRODUCT_NAME__C
        )                                       AS INCR_COUNT,

        -- Base name: product name with trailing " {term}" stripped
        -- e.g. "Basic 15" (Term=15) → "BASIC" for L6/L7 family-fallback
        CASE
            WHEN LENGTH(UPPER(TRIM(NP.PRODUCT_NAME__C)))
                     > LENGTH(CAST(NP."Term__C" AS NVARCHAR)) + 1
             AND SUBSTRING(UPPER(TRIM(NP.PRODUCT_NAME__C)),
                           LENGTH(UPPER(TRIM(NP.PRODUCT_NAME__C)))
                               - LENGTH(CAST(NP."Term__C" AS NVARCHAR)),
                           1) = ' '
                THEN UPPER(TRIM(SUBSTRING(NP.PRODUCT_NAME__C, 1,
                         LENGTH(UPPER(TRIM(NP.PRODUCT_NAME__C)))
                             - LENGTH(CAST(NP."Term__C" AS NVARCHAR)) - 1)))
            ELSE UPPER(TRIM(NP.PRODUCT_NAME__C))
        END                                     AS BASE_NAME

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
--   L6 → same TDSP, base-name family, 12 or 24 month term (RESET, family fallback)
--   L7 → any  TDSP, base-name family, 12 or 24 month term (RESET, family cross-TDSP)
-- ============================================================
MATCHED AS (
    SELECT
        N.*,

        -- L1: Same TDSP | same name | same term | same hierarchy → INCREMENT
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C = UPPER(TRIM(N.PRODUCT_NAME__C))
            AND E.TDSP__C         = N.NORM_TDSP
            AND E.PRODUCT_TERM    = CAST(N."Term__C" AS NVARCHAR)
            AND E.CODE_HIER       = N."Hierarchy"
        ) AS L1_CODE,

        -- L2: Same TDSP | same name | same term | different hierarchy → RESET
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C = UPPER(TRIM(N.PRODUCT_NAME__C))
            AND E.TDSP__C         = N.NORM_TDSP
            AND E.PRODUCT_TERM    = CAST(N."Term__C" AS NVARCHAR)
            AND E.CODE_HIER      != N."Hierarchy"
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
            AND E.PRODUCT_TERM    = CAST(N."Term__C" AS NVARCHAR)
        ) AS L4_CODE,

        -- L5: Any TDSP | same name | 12 or 24 month term | any hierarchy → RESET (cross-TDSP fallback)
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C = UPPER(TRIM(N.PRODUCT_NAME__C))
            AND E.PRODUCT_TERM    IN ('12', '24')
        ) AS L5_CODE,

        -- L6: Same TDSP | base-name family | 12 or 24 month term → RESET (family fallback)
        --   Extra check: char after base name must be a digit (e.g. 'BASIC 12' yes, 'BASIC PLUS 24' no)
        --   This prevents "Basic" from accidentally matching "Basic Plus" products
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C LIKE N.BASE_NAME || ' %'
            AND SUBSTRING(E.PRODUCT_NAME__C, LENGTH(N.BASE_NAME) + 2, 1) BETWEEN '0' AND '9'
            AND E.TDSP__C         = N.NORM_TDSP
            AND E.PRODUCT_TERM    IN ('12', '24')
        ) AS L6_CODE,

        -- L7: Any TDSP | base-name family | 12 or 24 month term → RESET (family cross-TDSP fallback)
        (SELECT MAX(E.PRODUCTCODE__C)
           FROM SFDC_PRODS E
          WHERE E.PRODUCT_NAME__C LIKE N.BASE_NAME || ' %'
            AND SUBSTRING(E.PRODUCT_NAME__C, LENGTH(N.BASE_NAME) + 2, 1) BETWEEN '0' AND '9'
            AND E.PRODUCT_TERM    IN ('12', '24')
        ) AS L7_CODE

    FROM NEW_PRODS N
),

-- ============================================================
-- CTE 4: RESOLVED
--   Consolidate cascade results into a single template code and
--   compute the metadata needed to build the final product code:
--
--   TEMPLATE_CODE : first non-null code from L1→L5
--   SUFFIX_MODE   : INCREMENT (L1 matched) or RESET (all others)
--   CORE_CHARS    : chars 3-10 — from Code_Core if brand new,
--                   else extracted from TEMPLATE_CODE
--   SUFFIX_TYPE   : ALPHA (ends in letter) or NUM (ends in digit)
--   BASE_ORDER    : position in PROD_NAMING_SEQ to increment from
--                   (0 in RESET mode → INCR_COUNT=1 yields AA/001)
-- ============================================================
RESOLVED AS (
    SELECT
        M.*,

        COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                 M.L4_CODE, M.L5_CODE,
                 M.L6_CODE, M.L7_CODE)              AS TEMPLATE_CODE,

        CASE
            WHEN M.L1_CODE IS NOT NULL THEN 'INCREMENT'
            ELSE 'RESET'
        END                                          AS SUFFIX_MODE,

        -- Core chars 3-10
        CASE
            WHEN M."Code_Core" IS NOT NULL AND M."Code_Core" <> ''
                THEN M."Code_Core"
            WHEN COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                          M.L4_CODE, M.L5_CODE,
                          M.L6_CODE, M.L7_CODE) IS NOT NULL
                THEN SUBSTRING(
                         COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                                  M.L4_CODE, M.L5_CODE,
                                  M.L6_CODE, M.L7_CODE), 3, 8)
            ELSE NULL
        END                                          AS CORE_CHARS,

        -- Suffix type from template (defaults to ALPHA for brand-new)
        CASE
            WHEN COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                          M.L4_CODE, M.L5_CODE,
                          M.L6_CODE, M.L7_CODE) IS NOT NULL
             AND SUBSTRING(COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                                    M.L4_CODE, M.L5_CODE,
                                    M.L6_CODE, M.L7_CODE),
                           LENGTH(COALESCE(M.L1_CODE, M.L2_CODE, M.L3_CODE,
                                           M.L4_CODE, M.L5_CODE,
                                           M.L6_CODE, M.L7_CODE)), 1)
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
                       WHERE LPAD(CAST(S."CURRENT_NUM" AS NVARCHAR), 3, '0') = RIGHT(M.L1_CODE, 3))
            ELSE 0
        END                                          AS BASE_ORDER

    FROM MATCHED M
),

-- ============================================================
-- CTE 5: BUILT
--   Assemble the final product code:
--     NEW_TDU_PREFIX  (chars 1-2)
--     CORE_CHARS      (chars 3-10)
--     "Hierarchy"     (char 11)  ← always from NEW_PCRF_VBB."Hierarchy"
--     LPAD(TERM,2,'0')(chars 12-13)
--     SEQUENCE SUFFIX (chars 14-15 alpha or 14-16 numeric)
--       looked up in PROD_NAMING_SEQ at position BASE_ORDER + INCR_COUNT
--
--   NULL PRODUCTCODE__C means no template was found and
--   Code_Core was not provided — requires manual resolution.
-- ============================================================
BUILT AS (
    SELECT
        R.PRODUCT_NAME__C,
        R."Term__C",
        R.NEW_TDSP                                  AS NTDSP,
        R.NORM_TDSP                                 AS GTDSP,
        R."Hierarchy",
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
                  || R."Hierarchy"
                  || LPAD(CAST(R."Term__C" AS NVARCHAR), 2, '0')
                  || (SELECT S."CURRENT"
                        FROM "XV1S"."PROD_NAMING_SEQ" S
                       WHERE S."ORDER" = R.BASE_ORDER + R.INCR_COUNT)

            -- Numeric suffix (e.g., 001, 002, ... 677)
            ELSE
                 R.NEW_TDU_PREFIX
              || R.CORE_CHARS
              || R."Hierarchy"
              || LPAD(CAST(R."Term__C" AS NVARCHAR), 2, '0')
              || LPAD(CAST((SELECT S."CURRENT_NUM"
                              FROM "XV1S"."PROD_NAMING_SEQ" S
                             WHERE S."ORDER_NUM" = R.BASE_ORDER + R.INCR_COUNT)
                    AS NVARCHAR), 3, '0')
        END                                         AS PRODUCTCODE__C

    FROM RESOLVED R
)

-- ============================================================
-- Final SELECT
--   SUFFIX_MODE, "Hierarchy", "Term__C", INCR_COUNT are diagnostic
--   columns included to aid first-run validation.
-- ============================================================
SELECT
    B.PRODUCT_NAME__C,
    B.EXISTING_PRODUCTCODE__C,
    B.NTDSP,
    B.GTDSP,
    B."Hierarchy",
    B."Term__C",
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
    B."Term__C",
    B."Hierarchy",
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
    "Term__C",
    "Hierarchy",
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
    "Term__C",
    "Hierarchy",
    INCR_COUNT;
