"""
efl_parser.py
Parses Electricity Facts Label (EFL) PDFs from a folder and exports
all extracted fields to Excel.

Usage:
    py efl_parser.py                  # reads from ./EFLs, writes efl_data.xlsx
    py efl_parser.py "path/to/folder" # custom folder

Dependencies:
    pip install pdfplumber pandas openpyxl
"""

import os
import re
import sys

import pdfplumber
import pandas as pd

# ── Configuration ──────────────────────────────────────────────────────────────
DEFAULT_FOLDER = "EFLs"
OUTPUT_FILE    = "efl_data.xlsx"

TDU_MAP = {
    "AEP TEXAS CENTRAL COMPANY": "AEPTCC",
    "AEP TEXAS NORTH COMPANY":   "AEPTNC",
    "CENTERPOINT ENERGY":        "CNP",
    "ONCOR ELECTRIC DELIVERY":   "ONCOR",
    "LUBBOCK POWER AND LIGHT":   "LPL",
    "TEXAS-NEW MEXICO POWER":    "TNMP",
}


# ── Low-level helpers ──────────────────────────────────────────────────────────

def pdf_text(pdf) -> str:
    """Concatenate text from every page."""
    return "\n".join(page.extract_text() or "" for page in pdf.pages)


def first_price_in(line: str):
    """
    Return the first dollar ($X.XX) or cent (X.XXXX¢) value in a line,
    or None if neither is present.
    """
    m = re.search(r'\$[\d,]+\.?\d*', line)
    if m:
        return m.group()
    m = re.search(r'[\d.]+¢', line)
    if m:
        return m.group()
    return None


def parse_num(s: str):
    """Strip non-numeric characters and return float, or None on failure."""
    if not s:
        return None
    try:
        return float(re.sub(r"[^\d.]", "", s))
    except ValueError:
        return None


# ── Field extractors ───────────────────────────────────────────────────────────

def find_tdu(text: str):
    upper = text.upper()
    for name, code in TDU_MAP.items():
        if name in upper:
            return code
    return None


def find_base(text: str):
    """
    Base Charge.
    TXU:      "Base Charge: | Per Month ($) | $7.90"  — value on same or next line
    4Change:  "Base Charge: $0.00 Per billing cycle"  — value on same line
    Strategy: find the Base Charge line; return the first $X.XX seen on that
              line or the immediately following line.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.search(r'base charge|cargo base', line, re.IGNORECASE):
            for check in [line] + (lines[i + 1:i + 2] if i + 1 < len(lines) else []):
                price = first_price_in(check)
                if price and "$" in price:
                    return price
    return None


def find_ec1(text: str):
    """
    Energy charge per kWh.
    TXU:      dedicated "All kWh  16.5000¢" sub-row
    4Change:  value on the "Energy Charge: 14.2000¢ Per kWh" row itself
    """
    lines = text.splitlines()

    # TXU path — "All kWh" row
    for line in lines:
        if re.search(r"all kwh|todos los kwh", line, re.IGNORECASE):
            p = first_price_in(line)
            if p and "¢" in p:
                return p

    # 4Change path — value on the Energy Charge label row
    for i, line in enumerate(lines):
        if re.search(r"energy charge|cargo de energ", line, re.IGNORECASE):
            for check in [line] + (lines[i + 1:i + 2] if i + 1 < len(lines) else []):
                p = first_price_in(check)
                if p and "¢" in p and parse_num(p) is not None:
                    return p
    return None


def find_sv(text: str):
    """
    Shopping values — three prices from the "Average Price per kWh" row.
    Returns a list of three floats (or Nones for unmetered EFLs showing "NA").
    """
    for line in text.splitlines():
        if re.search(r"average price per kwh|precio promedio por kwh", line, re.IGNORECASE):
            # Prefer ¢-delimited values; this naturally excludes "500 kWh" tier numbers
            nums = re.findall(r"([\d.]+)¢", line)
            if len(nums) >= 3:
                return [float(n) for n in nums[:3]]
            # Fallback: bare numbers that look like prices (< 100), not usage tiers
            nums = [
                float(n) for n in re.findall(r"[\d.]+", line)
                if "." in n and float(n) < 100
            ]
            if len(nums) >= 3:
                return nums[-3:]
    return [None, None, None]


def find_product_code(text: str):
    """
    TXU:     "Version:" ends one line; the product code is the last ALL-CAPS
             token on the very next line (which also contains the P.O. Box address).
             Example:
               "...REP Certificate No. 10004 Version:"
               "P.O. Box 650764, Dallas, TX 75265-0764 ALBIZFLXVALAQ"
    4Change: Code is the last ALL-CAPS token on the "(855)784-2426" phone line.
             Example:
               "(855)784-2426 (7A-8P M-F, 8A-5P Sat CST) CP4CFCMTMCH00AF"
    """
    lines = text.splitlines()

    # TXU path — find the line ending with "Version:" then grab last token of next line
    for i, line in enumerate(lines):
        if re.search(r"Versi[oó]n?:\s*$", line.strip(), re.IGNORECASE):
            if i + 1 < len(lines):
                tokens = lines[i + 1].split()
                for tok in reversed(tokens):
                    if re.match(r"^[A-Z0-9]{6,}$", tok):
                        return tok

    # 4Change path — last ALL-CAPS token on the phone line
    for line in lines:
        if "784-2426" in line:
            for tok in reversed(line.split()):
                if re.match(r"^[A-Z0-9]{8,}$", tok):
                    return tok
    return None


def find_renew_content(text: str):
    """Renewable content as an integer percent."""
    for line in text.splitlines():
        if re.search(r"renewable content|contenido renovable", line, re.IGNORECASE):
            m = re.search(r"(\d+)%", line)
            if m:
                return int(m.group(1))
            # "This product is 3% renewable" — % may trail the number
            m = re.search(r"(\d+)", line)
            if m:
                return int(m.group(1))
    return None


def find_state_renew(text: str):
    """Statewide average renewable % (integer)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"statewide average|state average|promedio.*estado", line, re.IGNORECASE):
            # % may sit on the same line or the very next line
            for check in [line] + (lines[i + 1:i + 2] if i + 1 < len(lines) else []):
                m = re.search(r"(\d+)%", check)
                if m:
                    val = int(m.group(1))
                    if 0 <= val <= 100:
                        return val
    return None


def find_print_date(text: str):
    """
    4Change:  "Issue Date: February 01, 2026"  →  extract after the colon
    TXU EN:   "March 01, 2026"                 →  regex month pattern
    TXU ES:   "01 marzo 2026"                  →  same regex (Spanish months)
    """
    # 4Change
    m = re.search(r"Issue Date:\s*(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # TXU — English and Spanish month names
    months = (
        r"(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December|"
        r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
        r"septiembre|octubre|noviembre|diciembre)"
    )
    m = re.search(
        rf"({months}\s+\d{{1,2}},?\s+\d{{4}}|\d{{1,2}}\s+{months}\s+\d{{4}})",
        text, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return None


def find_version(text: str):
    """V20XXXXXX stamp — TXU only; returns None for 4Change (no version field)."""
    m = re.search(r"\b(V20\d{6})\b", text)
    return m.group(1) if m else None


# ── Top-level parser ───────────────────────────────────────────────────────────

def parse_efl(pdf_path: str) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf_text(pdf)

    sv = find_sv(text)
    return {
        "Filename":      os.path.basename(pdf_path),
        "TDU":           find_tdu(text),
        "ProductCode":   find_product_code(text),
        "Base":          find_base(text),
        "EC1":           find_ec1(text),
        "SV1":           sv[0],
        "SV2":           sv[1],
        "SV3":           sv[2],
        "Renew_Content": find_renew_content(text),
        "State_Renew":   find_state_renew(text),
        "Print_Date":    find_print_date(text),
        "Version":       find_version(text),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FOLDER
    if not os.path.isdir(folder):
        print(f"ERROR: folder not found: {folder}")
        sys.exit(1)

    pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
    if not pdfs:
        print(f"No PDF files found in: {folder}")
        sys.exit(1)

    records = []
    for fname in pdfs:
        path = os.path.join(folder, fname)
        print(f"  Parsing: {fname}")
        try:
            records.append(parse_efl(path))
        except Exception as exc:
            print(f"    ERROR: {exc}")
            records.append({"Filename": fname, "Error": str(exc)})

    df = pd.DataFrame(records)
    df.to_excel(OUTPUT_FILE, index=False)

    print(f"\n{len(records)} EFL(s) written to {OUTPUT_FILE}\n")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
