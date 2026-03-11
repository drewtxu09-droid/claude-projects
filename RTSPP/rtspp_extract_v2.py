"""
RTSPP Extract Tool - v2
Fully automated monthly extract from SAP ISU.

Changes from v1:
  - Opens RTSPP_Extract_Tool_DW.xlsm automatically (does not need to be open)
  - Excel runs hidden in the background
  - SAP launches minimized
  - Saves workbook after extract, then makes Excel visible for review
  - Sends a Microsoft Teams notification on success or failure
  - Designed to be run by Windows Task Scheduler on the 2nd of each month

Usage:
  python rtspp_extract_v2.py        -> run the full automated extract
  python rtspp_extract_v2.py save   -> save extract to network share (manual step)

Setup:
  1. Set RTSPP_FILE_PATH below to the full path of your workbook
  2. Set TEAMS_WEBHOOK_URL below (see instructions in that section)
  3. Run setup_scheduled_task.bat once to register the monthly scheduled task
"""

import win32com.client
import subprocess
import calendar
import urllib.request
import urllib.error
import json
import time
import sys
import os
from datetime import date


# =============================================================================
# USER CONFIGURATION — update these before first use
# =============================================================================

# Full path to the RTSPP Excel workbook
RTSPP_FILE_PATH = r"C:\Users\xv1s\path\to\RTSPP_Extract_Tool_DW.xlsm"

# Microsoft Teams Incoming Webhook URL
# To create one:
#   1. Open the Teams channel you want alerts sent to
#   2. Click the "..." next to the channel name → Connectors (or Workflows)
#   3. Search for "Incoming Webhook" → Configure
#   4. Give it a name (e.g. "RTSPP Extract") → Create
#   5. Copy the URL and paste it below
TEAMS_WEBHOOK_URL = "https://your-tenant.webhook.office.com/webhookb2/PASTE-YOUR-URL-HERE"

# =============================================================================
# SYSTEM CONFIGURATION — only change if your environment differs
# =============================================================================

SAP_EXE        = r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe"
SAP_SYSTEM     = "01)  TXUE ISU Prod"
SAP_TEMP_FILE  = r"C:\Users\xv1s\AppData\Local\Temp\~SAP{C0C070F9-F809-4A2F-A740-AF95E87C7455}.tmp"
SAVE_PATH_BASE = r"\\ddcnasshares\c_product\RATE MANAGEMENT\aaaa_LARR_POLR\Annual EFL POLR Filing"

# SAP element paths
TREE_BASE = (
    "wnd[0]/usr"
    "/subFULLSCREEN_SS:SAPLEEDM_DLG_FRAME:0200"
    "/subSUBSCREEN_TREE:SAPLEEDM_TREESELECT:0200"
)
PROFILE_PATH = (
    f"{TREE_BASE}"
    "/tabsSELECTION_TABSTRIP/tabpLPTAB"
    "/ssubLPSS:SAPLEEDM_TREESELECT:0302"
    "/ctxtEEDM_TREE_DATA_FINDER-PROFILE"
)
IMPEXP_TAB = (
    "wnd[0]/usr"
    "/subFULLSCREEN_SS:SAPLEEDM_DLG_FRAME:0200"
    "/subSUBSCREEN_MAIN:SAPLEEDM_PROFHEAD:0300"
    "/tabsTABSTRIP/tabpIMPEXP"
)

# Load zone profiles: (name, profile_id, edm_data_start, edm_data_end_col,
#                      rtspp_paste_dest, edm_header_range, rtspp_header_dest)
PROFILES = [
    ("LZ_Houston", "400000003", "D3", "F", "A2", "H1:N3", "H1"),
    ("LZ_North",   "400000000", "F3", "F", "D2",  None,   None),
    ("LZ_South",   "400000001", "F3", "F", "E2",  None,   None),
    ("LZ_West",    "400000002", "F3", "F", "F2",  None,   None),
]

XL_DOWN       = -4121
XL_OPEN_XML   = 51
XL_CALC_MANUAL = -4135
XL_CALC_AUTO   = -4105


# =============================================================================
# Teams Notification
# =============================================================================

def send_teams_alert(success, month_label=None, from_date=None, to_date=None, error=None):
    """Send a Teams notification card on success or failure."""
    if not TEAMS_WEBHOOK_URL or "PASTE-YOUR-URL" in TEAMS_WEBHOOK_URL:
        print("  [Teams] Webhook URL not configured — skipping notification.")
        return

    if success:
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "28A745",
            "summary": "RTSPP Extract Complete",
            "sections": [{
                "activityTitle": "RTSPP Extract — Ready for Review",
                "activitySubtitle": f"Month: {month_label}",
                "facts": [
                    {"name": "Date Range", "value": f"{from_date}  →  {to_date}"},
                    {"name": "Status",     "value": "Extract complete. Review the Extract sheet, then run the Save step."},
                    {"name": "Workbook",   "value": os.path.basename(RTSPP_FILE_PATH)},
                ],
                "markdown": True
            }]
        }
    else:
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "DC3545",
            "summary": "RTSPP Extract FAILED",
            "sections": [{
                "activityTitle": "RTSPP Extract — FAILED",
                "activitySubtitle": "Manual intervention required",
                "facts": [
                    {"name": "Error",  "value": str(error)},
                    {"name": "Action", "value": "Check the workbook and re-run manually."},
                ],
                "markdown": True
            }]
        }

    try:
        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            TEAMS_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"  [Teams] Notification sent.")
    except Exception as e:
        print(f"  [Teams] Could not send notification: {e}")


# =============================================================================
# Helpers
# =============================================================================

def open_excel_hidden():
    """Launch a hidden Excel instance and open the RTSPP workbook."""
    if not os.path.exists(RTSPP_FILE_PATH):
        raise FileNotFoundError(
            f"Workbook not found: {RTSPP_FILE_PATH}\n"
            "Update RTSPP_FILE_PATH in the configuration section."
        )
    xl = win32com.client.Dispatch("Excel.Application")
    xl.Visible        = False
    xl.DisplayAlerts  = False
    xl.ScreenUpdating = False
    wb = xl.Workbooks.Open(RTSPP_FILE_PATH)
    print(f"  Opened (hidden): {os.path.basename(RTSPP_FILE_PATH)}")
    return xl, wb


def find_edm_workbook(xl):
    """Poll until SAP opens the EDM Profile workbook (up to 15 s)."""
    for _ in range(15):
        for wb in xl.Workbooks:
            if "edm" in wb.Name.lower():
                return wb
        time.sleep(1)
    raise RuntimeError("EDM Profile workbook not found — SAP may not have opened it.")


def connect_sap():
    """
    Connect to SAP GUI and return a session, handling three cases:
      1. SAP is not running          -> launch it minimized, then connect
      2. SAP is running, no TXUE ISU connection -> open one
      3. SAP is running with an existing TXUE ISU connection -> create a new child session
    """
    # --- Try to attach to a running SAP GUI instance ---
    sap_gui = None
    try:
        sap_gui = win32com.client.GetObject("SAPGUI")
        print("  SAP already running — attaching...")
    except Exception:
        pass

    # --- SAP not running: launch minimized and wait for it ---
    if sap_gui is None:
        print("  SAP not running — launching minimized...")
        si = subprocess.STARTUPINFO()
        si.dwFlags    |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 6   # SW_MINIMIZE
        subprocess.Popen(SAP_EXE, startupinfo=si)

        for _ in range(10):
            time.sleep(1)
            try:
                sap_gui = win32com.client.GetObject("SAPGUI")
                break
            except Exception:
                pass

        if sap_gui is None:
            raise RuntimeError("SAP GUI failed to launch. Please open it manually and re-run.")

    sap_app = sap_gui.GetScriptingEngine

    # --- Check if a TXUE ISU connection already exists ---
    connection = None
    for i in range(sap_app.Children.Count):
        conn = sap_app.Children(i)
        if "TXUE ISU" in conn.Description:
            connection = conn
            print(f"  Reusing existing TXUE ISU connection.")
            break

    # --- No existing connection: open one ---
    if connection is None:
        connection = sap_app.OpenConnection(SAP_SYSTEM, True)  # True = wait for connection
        time.sleep(2)

    # --- Open a new child session if sessions already exist, else use existing ---
    if connection.Children.Count > 0:
        connection.Children(0).CreateSession()
        time.sleep(2)
        session = connection.Children(connection.Children.Count - 1)
        print(f"  New SAP session created (session {connection.Children.Count}).")
    else:
        session = connection.Children(0)
        print(f"  Using existing SAP session.")

    return session


def populate_readme(rtspp_wb):
    """Write previous-month date fields into the ReadMe sheet."""
    today = date.today()

    if today.month == 1:
        year, month = today.year - 1, 12
    else:
        year, month = today.year, today.month - 1

    last_day_n    = calendar.monthrange(year, month)[1]
    first_day     = date(year, month, 1)
    month_name    = first_day.strftime("%B")
    month_num     = first_day.strftime("%m")
    last_yyyymmdd = date(year, month, last_day_n).strftime("%Y%m%d")
    first_str     = f"{month}/1/{year}"
    last_str      = f"{month}/{last_day_n}/{year}"

    readme = rtspp_wb.Sheets("ReadMe")
    readme.Range("A1").Value = last_str
    readme.Range("B1").Value = f"{month_name} {year}"
    readme.Range("A2").Value = f"{year} - {month_num} {month_name}"
    readme.Range("B2").Value = last_yyyymmdd
    readme.Range("C2").Value = first_str
    readme.Range("E2").Value = f"{last_yyyymmdd}_RTSPP_Extract.xlsx"
    readme.Range("B3").Value = year

    print(f"  ReadMe updated: {month_name} {year}  ({first_str} – {last_str})")
    return f"{month_name} {year}", first_str, last_str


# =============================================================================
# Main extract
# =============================================================================

def extract():
    xl = None
    month_label = from_date = to_date = None

    try:
        print("Opening Excel (hidden)...")
        xl, rtspp_wb = open_excel_hidden()

        print("Populating ReadMe dates...")
        month_label, from_date, to_date = populate_readme(rtspp_wb)

        # Clear extract sheet
        ext      = rtspp_wb.Sheets("Extract")
        last_row = ext.Range("A2").End(XL_DOWN).Row
        if last_row >= 2:
            ext.Range(f"A2:F{last_row}").ClearContents()
        ext.Range("H1:M3").ClearContents()

        print("Connecting to SAP...")
        session = connect_sap()

        session.findById("wnd[0]/tbar[0]/okcd").Text = "/NEEDM08"
        session.findById("wnd[0]").sendVKey(0)

        session.findById(f"{TREE_BASE}/tabsSELECTION_TABSTRIP/tabpLPTAB").Select()
        session.findById(f"{TREE_BASE}/ctxtEEDM_TREE_DATA_FINDER-AB").Text  = from_date
        session.findById(f"{TREE_BASE}/ctxtEEDM_TREE_DATA_FINDER-BIS").Text = to_date

        for name, profile_id, edm_start, edm_end_col, rtspp_dest, edm_hdr, rtspp_hdr in PROFILES:
            print(f"  Extracting {name} (profile {profile_id})...")

            session.findById(PROFILE_PATH).Text = profile_id
            session.findById(f"{TREE_BASE}/cntlTREE_CONTAINER/shellcont/shell/shellcont[0]/shell").pressButton("REFRESH_TREE")
            session.findById(f"{TREE_BASE}/cntlTREE_CONTAINER/shellcont/shell/shellcont[1]/shell").doubleClickItem("PA        1", "1")
            session.findById(IMPEXP_TAB).Select()

            edm_wb    = find_edm_workbook(xl)
            edm_sheet = edm_wb.ActiveSheet
            last_data = edm_sheet.Range(edm_start).End(XL_DOWN).Row
            start_col = edm_start[0]
            src_range = edm_sheet.Range(f"{start_col}3:{edm_end_col}{last_data}")

            src_range.Copy(Destination=ext.Range(rtspp_dest))

            if edm_hdr and rtspp_hdr:
                edm_sheet.Range(edm_hdr).Copy(Destination=ext.Range(rtspp_hdr))

            xl.CutCopyMode = False
            edm_wb.SaveAs(Filename=SAP_TEMP_FILE, FileFormat=XL_OPEN_XML, CreateBackup=False)
            edm_wb.Windows(1).Visible = False

        # Log out of SAP
        session.findById("wnd[0]/tbar[0]/btn[15]").press()
        session.findById("wnd[0]/tbar[0]/btn[15]").press()
        session.findById("wnd[1]/usr/btnSPOP-OPTION1").press()
        print("  SAP session closed.")

        # Save the workbook and keep Excel hidden
        xl.CutCopyMode   = False
        xl.DisplayAlerts = False
        rtspp_wb.Save()
        print(f"  Workbook saved.")

        print("\nExtract complete — Teams notification sent.")
        send_teams_alert(True, month_label, from_date, to_date)

    except Exception as e:
        print(f"\nERROR: {e}")
        send_teams_alert(False, month_label, from_date, to_date, error=e)
        if xl:
            xl.DisplayAlerts = True
        sys.exit(1)


# =============================================================================
# Save extract to network share (manual step)
# =============================================================================

def save_extract():
    try:
        xl = win32com.client.GetActiveObject("Excel.Application")
    except Exception:
        raise RuntimeError("Excel is not open. Open the workbook and review it before running the save step.")

    xl.Calculation    = XL_CALC_MANUAL
    xl.ScreenUpdating = False
    xl.DisplayAlerts  = False

    rtspp_wb = None
    for wb in xl.Workbooks:
        if "RTSPP_Extract_Tool_DW" in wb.Name:
            rtspp_wb = wb
            break
    if not rtspp_wb:
        raise RuntimeError("Could not find RTSPP_Extract_Tool_DW workbook in Excel.")

    readme    = rtspp_wb.Sheets("ReadMe")
    save_file = readme.Range("E2").Value
    save_year = readme.Range("B3").Value

    save_dir  = os.path.join(
        SAVE_PATH_BASE,
        f"{save_year} EFL Filing",
        "Monthly Extracts"
    )
    save_path = os.path.join(save_dir, str(save_file))

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"  Created folder: {save_dir}")

    print(f"  Saving to: {save_path}")

    rtspp_wb.Sheets("Extract").Copy()
    new_wb = xl.ActiveWorkbook
    new_wb.SaveAs(Filename=save_path, FileFormat=XL_OPEN_XML, CreateBackup=False)
    new_wb.Close()

    rtspp_wb.Sheets("Extract").Select()
    rtspp_wb.Sheets("Extract").Range("A1").Select()

    xl.Calculation    = XL_CALC_AUTO
    xl.ScreenUpdating = True
    xl.DisplayAlerts  = True

    print(f"\nSaved: {save_file} → {save_year} Monthly Extracts folder.")


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "save":
        save_extract()
    else:
        extract()
