"""
RTSPP Extract Tool
Python replacement for CRM_RTSPP_Extract and SaveRTSPP_Extract VBA macros.

Usage:
  python rtspp_extract.py          -> runs the SAP extract
  python rtspp_extract.py save     -> saves the extract to the network share
"""

import win32com.client
import subprocess
import calendar
import time
import sys
import os
from datetime import date

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RTSPP_FILENAME   = "RTSPP_Extract_Tool_DW.xlsm"
SAP_EXE          = r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe"
SAP_SYSTEM       = "01)  TXUE ISU Prod"
SAP_TEMP_FILE    = r"C:\Users\xv1s\AppData\Local\Temp\~SAP{C0C070F9-F809-4A2F-A740-AF95E87C7455}.tmp"
SAVE_PATH_BASE   = r"\\ddcnasshares\c_product\RATE MANAGEMENT\aaaa_LARR_POLR\Annual EFL POLR Filing"

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

# Profiles to extract
# (display_name, profile_id, edm_data_start, edm_data_end_col, rtspp_paste_dest,
#  edm_header_range, rtspp_header_dest)
PROFILES = [
    ("LZ_Houston", "400000003", "D3", "F", "A2", "H1:N3", "H1"),
    ("LZ_North",   "400000000", "F3", "F", "D2",  None,   None),
    ("LZ_South",   "400000001", "F3", "F", "E2",  None,   None),
    ("LZ_West",    "400000002", "F3", "F", "F2",  None,   None),
]

XL_DOWN            = -4121   # xlDown
XL_OPEN_XML        = 51      # xlOpenXMLWorkbook
XL_CALC_MANUAL     = -4135   # xlCalculationManual
XL_CALC_AUTO       = -4105   # xlCalculationAutomatic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_xl():
    """Attach to the running Excel instance."""
    try:
        return win32com.client.GetActiveObject("Excel.Application")
    except Exception:
        raise RuntimeError("Excel is not open. Please open Excel and RTSPP_Extract_Tool_DW.xlsm first.")


def find_workbook(xl, partial_name):
    """Find an open workbook by partial name (case-insensitive)."""
    for wb in xl.Workbooks:
        if partial_name.lower() in wb.Name.lower():
            return wb
    return None


def find_edm_workbook(xl):
    """Find the EDM Profile workbook that SAP opens."""
    for _ in range(10):                        # wait up to 10 s
        for wb in xl.Workbooks:
            if "edm" in wb.Name.lower():
                return wb
        time.sleep(1)
    raise RuntimeError("EDM Profile workbook not found — SAP may not have opened it.")


def format_date(value):
    """Convert Excel date value to MM/DD/YYYY string if needed."""
    if value is None:
        raise ValueError("Date cell is empty.")
    if hasattr(value, "strftime"):
        return value.strftime("%m/%d/%Y")
    return str(value)


# ---------------------------------------------------------------------------
# Populate ReadMe sheet with current-month dates
# ---------------------------------------------------------------------------

def populate_readme(rtspp_wb):
    """
    Determine the current month and write all date fields to the ReadMe sheet.

    ReadMe layout:
      A1  - Last day of month  (e.g. 3/31/2026)       <- ToDate for SAP
      B1  - Month + Year label (e.g. March 2026)
      A2  - YYYY - MM MonthName (e.g. 2026 - 03 March)
      B2  - YYYYMMDD of last day (e.g. 20260331)
      C2  - First day of month  (e.g. 3/1/2026)       <- FromDate for SAP
      E2  - Save filename (e.g. 20260331_RTSPP_Extract.xlsx)
      B3  - Year (e.g. 2026)
    """
    today = date.today()

    # Always target the previous month (this tool runs between the 2nd-5th
    # of a new month to pull the prior month's completed data)
    if today.month == 1:
        year, month = today.year - 1, 12
    else:
        year, month = today.year, today.month - 1

    last_day_n = calendar.monthrange(year, month)[1]   # number of days in month

    first_day  = date(year, month, 1)
    last_day   = date(year, month, last_day_n)

    month_name    = first_day.strftime("%B")            # "March"
    month_num     = first_day.strftime("%m")            # "03"
    last_yyyymmdd = last_day.strftime("%Y%m%d")         # "20260331"

    # Date strings without leading zeros to match existing format
    first_str = f"{month}/1/{year}"                     # "3/1/2026"
    last_str  = f"{month}/{last_day_n}/{year}"          # "3/31/2026"

    readme = rtspp_wb.Sheets("ReadMe")
    readme.Range("A1").Value = last_str
    readme.Range("B1").Value = f"{month_name} {year}"
    readme.Range("A2").Value = f"{year} - {month_num} {month_name}"
    readme.Range("B2").Value = last_yyyymmdd
    readme.Range("C2").Value = first_str
    readme.Range("E2").Value = f"{last_yyyymmdd}_RTSPP_Extract.xlsx"
    readme.Range("B3").Value = year

    print(f"  ReadMe updated: {month_name} {year}  ({first_str} – {last_str})")


# ---------------------------------------------------------------------------
# Main extract
# ---------------------------------------------------------------------------

def extract():
    print("Connecting to Excel...")
    xl = get_xl()
    xl.ScreenUpdating = False
    xl.DisplayAlerts  = False

    rtspp_wb = find_workbook(xl, "RTSPP_Extract_Tool_DW")
    if not rtspp_wb:
        raise RuntimeError(f"Could not find '{RTSPP_FILENAME}'. Is it open in Excel?")

    print("Populating ReadMe dates...")
    populate_readme(rtspp_wb)

    readme    = rtspp_wb.Sheets("ReadMe")
    from_date = str(readme.Range("C2").Value)
    to_date   = str(readme.Range("A1").Value)
    print(f"  From: {from_date}  To: {to_date}")

    # Clear extract sheet
    ext = rtspp_wb.Sheets("Extract")
    last_row = ext.Range("A2").End(XL_DOWN).Row
    if last_row >= 2:
        ext.Range(f"A2:F{last_row}").ClearContents()
    ext.Range("H1:M3").ClearContents()
    ext.Range("A2").Select()

    # Launch SAP
    print("Launching SAP...")
    subprocess.Popen(SAP_EXE)
    time.sleep(3)

    # Connect to SAP GUI scripting engine
    sap_gui  = win32com.client.GetObject("SAPGUI")
    sap_app  = sap_gui.GetScriptingEngine
    conn     = sap_app.OpenConnection(SAP_SYSTEM)
    session  = conn.Children(0)

    # Navigate to /NEEDM08
    session.findById("wnd[0]/tbar[0]/okcd").Text = "/NEEDM08"
    session.findById("wnd[0]").sendVKey(0)

    # Select LP tab and set date range
    session.findById(f"{TREE_BASE}/tabsSELECTION_TABSTRIP/tabpLPTAB").Select()
    session.findById(f"{TREE_BASE}/ctxtEEDM_TREE_DATA_FINDER-AB").Text  = from_date
    session.findById(f"{TREE_BASE}/ctxtEEDM_TREE_DATA_FINDER-BIS").Text = to_date

    # Loop through each load zone profile
    for name, profile_id, edm_start, edm_end_col, rtspp_dest, edm_hdr, rtspp_hdr in PROFILES:
        print(f"  Extracting {name} (profile {profile_id})...")

        session.findById(PROFILE_PATH).Text = profile_id
        session.findById(f"{TREE_BASE}/cntlTREE_CONTAINER/shellcont/shell/shellcont[0]/shell").pressButton("REFRESH_TREE")
        session.findById(f"{TREE_BASE}/cntlTREE_CONTAINER/shellcont/shell/shellcont[1]/shell").doubleClickItem("PA        1", "1")
        session.findById(IMPEXP_TAB).Select()

        # Find the EDM Profile workbook SAP opened
        edm_wb    = find_edm_workbook(xl)
        edm_sheet = edm_wb.ActiveSheet

        # Determine last data row (go down from start cell)
        start_cell = edm_sheet.Range(edm_start)
        last_data  = start_cell.End(XL_DOWN).Row

        # Build source range: e.g. "D3:F{last}" or "F3:F{last}"
        start_col = edm_start[0]                          # e.g. "D" or "F"
        src_range = edm_sheet.Range(f"{start_col}3:{edm_end_col}{last_data}")

        # Copy data directly to destination
        src_range.Copy(Destination=ext.Range(rtspp_dest))

        # Copy header block (LZ_Houston only)
        if edm_hdr and rtspp_hdr:
            edm_sheet.Range(edm_hdr).Copy(Destination=ext.Range(rtspp_hdr))

        xl.CutCopyMode = False

        # Save and hide the EDM workbook (matches VBA behavior)
        edm_wb.SaveAs(Filename=SAP_TEMP_FILE, FileFormat=XL_OPEN_XML, CreateBackup=False)
        edm_wb.Windows(1).Visible = False

    # Log out of SAP (two Back presses + confirm)
    session.findById("wnd[0]/tbar[0]/btn[15]").press()
    session.findById("wnd[0]/tbar[0]/btn[15]").press()
    session.findById("wnd[1]/usr/btnSPOP-OPTION1").press()

    xl.CutCopyMode      = False
    xl.ScreenUpdating   = True
    xl.DisplayAlerts    = True

    print("\nExtract complete!")


# ---------------------------------------------------------------------------
# Save extract to network share
# ---------------------------------------------------------------------------

def save_extract():
    print("Connecting to Excel...")
    xl = get_xl()
    xl.Calculation    = XL_CALC_MANUAL
    xl.ScreenUpdating = False
    xl.DisplayAlerts  = False

    rtspp_wb = find_workbook(xl, "RTSPP_Extract_Tool_DW")
    if not rtspp_wb:
        raise RuntimeError(f"Could not find '{RTSPP_FILENAME}'. Is it open in Excel?")

    readme    = rtspp_wb.Sheets("ReadMe")
    save_file = readme.Range("E2").Value
    save_year = readme.Range("B3").Value

    save_path = os.path.join(
        SAVE_PATH_BASE,
        f"{save_year} EFL Filing",
        "Monthly Extracts",
        str(save_file)
    )
    print(f"  Saving to: {save_path}")

    # Copy Extract sheet to a new workbook and save it
    rtspp_wb.Sheets("Extract").Copy()
    new_wb = xl.ActiveWorkbook
    new_wb.SaveAs(Filename=save_path, FileFormat=XL_OPEN_XML, CreateBackup=False)
    new_wb.Close()

    # Return focus to Extract sheet
    rtspp_wb.Sheets("Extract").Select()
    rtspp_wb.Sheets("Extract").Range("A1").Select()

    xl.Calculation    = XL_CALC_AUTO
    xl.ScreenUpdating = True
    xl.DisplayAlerts  = True

    print(f"\nSaved: {save_file} → {save_year} Monthly Extracts folder.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1].lower() == "save":
            save_extract()
        else:
            extract()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
