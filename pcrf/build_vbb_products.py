"""
build_vbb_products.py
Connects to SAP HANA, drops the existing CREATE_NEW_VBB_PRODS table if present,
then runs CREATE_NEW_VBB_PRODS_v2.txt to rebuild it from scratch.

Credentials are read from config-HANA-Prod.yaml in the Claude root folder.
"""

import os
import sys
import yaml
from hdbcli import dbapi

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(ROOT_DIR, "config-HANA-Prod.yaml")
SQL_PATH    = os.path.join(SCRIPT_DIR, "CREATE_NEW_VBB_PRODS_v2.txt")
OUTPUT_TABLE = "CREATE_NEW_VBB_PRODS"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit(f"ERROR: Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def connect(cfg):
    h = cfg["hana"]
    print(f"Connecting to {h['host']}:{h['port']} as {h['username']}...")
    conn = dbapi.connect(
        address=h["host"],
        port=int(h["port"]),
        user=h["username"],
        password=h["password"],
    )
    print("Connected.")
    return conn


def drop_table(cursor, table):
    try:
        cursor.execute(f'DROP TABLE "{table}"')
        print(f"Dropped existing table: {table}")
    except Exception:
        print(f"Table {table} does not exist yet — skipping drop.")


def load_sql():
    if not os.path.exists(SQL_PATH):
        sys.exit(f"ERROR: SQL file not found at {SQL_PATH}")
    with open(SQL_PATH, "r") as f:
        return f.read()


def run():
    cfg    = load_config()
    conn   = connect(cfg)
    cursor = conn.cursor()

    try:
        drop_table(cursor, OUTPUT_TABLE)

        print("Executing CREATE_NEW_VBB_PRODS_v2 SQL...")
        sql = load_sql()
        cursor.execute(sql)
        print("Table built successfully.")

        cursor.execute(f'SELECT COUNT(*) FROM "{OUTPUT_TABLE}"')
        count = cursor.fetchone()[0]
        print(f"Rows created: {count:,}")

        # Preview first 10 rows
        cursor.execute(f'SELECT * FROM "{OUTPUT_TABLE}" LIMIT 10')
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        print(f"\n--- Preview (first {len(rows)} rows) ---")
        print("  ".join(cols))
        print("-" * 80)
        for row in rows:
            print("  ".join(str(v) if v is not None else "NULL" for v in row))

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    run()
