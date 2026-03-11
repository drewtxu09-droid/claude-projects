"""
RTSPP Extract Tool
Python replacement for CRM_RTSPP_Extract and SaveRTSPP_Extract VBA macros.

Usage:
  python rtspp_extract.py          -> runs the SAP extract
  python rtspp_extract.py save     -> saves the extract to the network share
"""

import win32com.client
import subprocess
import time
import sys
import os

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

    readme  = rtspp_wb.Sheets("ReadMe")
    from_date = format_date(readme.Range("C2").Value)
    to_date   = format_date(readme.Range("A1").Value)
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
