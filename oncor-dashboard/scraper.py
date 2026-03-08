"""
Oncor TDU Residential Rate Scraper
Fetches rate data from Oncor and PUCT sources.
Builds a rolling 12-month history based on known rate periods.
"""

import os
import re
import requests
import pdfplumber
import pandas as pd
from io import BytesIO
from datetime import date
from dateutil.relativedelta import relativedelta

# ---------------------------------------------------------------------------
# Known rate periods — all variable charges in ¢/kWh, fixed in $/mo
# Oncor rates change March 1 and September 1 each year
# ---------------------------------------------------------------------------
KNOWN_RATE_PERIODS = [
    {
        "effective_date":   date(2024, 3, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "distribution":     2.19660,
        "dcrf":             0.54270,
        "tcrf":             2.08380,
        "eecrf":            0.11370,
        "mobile_gen":       0.00000,   # only billed in December
    },
    {
        "effective_date":   date(2024, 9, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "distribution":     2.34510,
        "dcrf":             0.54270,
        "tcrf":             2.22170,
        "eecrf":            0.11370,
        "mobile_gen":       0.00000,
    },
    {
        "effective_date":   date(2025, 3, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "distribution":     2.53440,
        "dcrf":             0.57720,
        "tcrf":             2.35800,
        "eecrf":            0.11370,
        "mobile_gen":       0.00000,
    },
    {
        "effective_date":   date(2025, 9, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "distribution":     2.53440,
        "dcrf":             0.57720,
        "tcrf":             2.35800,
        "eecrf":            0.11370,
        "mobile_gen":       0.00000,
    },
    {
        "effective_date":   date(2026, 3, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "distribution":     2.53440,
        "dcrf":             0.57720,
        "tcrf":             2.35800,
        "eecrf":            0.14870,   # EECRF resets each March
        "mobile_gen":       0.00000,
    },
]

PDF_SOURCES = {
    "residential_rates": (
        "https://www.oncor.com/content/dam/oncorwww/documents/partners/rep/"
        "Oncor%20Residential%20Rates.pdf.coredownload.pdf"
    ),
    "puct_monthly": (
        "https://ftp.puc.texas.gov/public/puct-info/industry/electric/rates/tdr/tdu/"
        "Oncor_Rate_Report.pdf"
    ),
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Charge definitions: (column_key, display_label, category, unit)
CHARGE_DEFS = [
    ("customer_charge", "Customer Charge",                          "Fixed",    "$/mo"),
    ("metering_charge", "Metering Charge",                          "Fixed",    "$/mo"),
    ("distribution",    "Distribution System Charge (DIS001)",      "Variable", "¢/kWh"),
    ("dcrf",            "Distribution Cost Recovery Factor (DCRF)", "Variable", "¢/kWh"),
    ("tcrf",            "Transmission Cost Recovery Factor (TCRF)", "Variable", "¢/kWh"),
    ("eecrf",           "Energy Efficiency Cost Recovery (EECRF)",  "Variable", "¢/kWh"),
    ("mobile_gen",      "Mobile Generation (MG)",                   "Variable", "¢/kWh"),
]


# ---------------------------------------------------------------------------
# Rate lookup
# ---------------------------------------------------------------------------

def get_rate_for_month(target_date: date) -> dict:
    applicable = None
    for period in KNOWN_RATE_PERIODS:
        if period["effective_date"] <= target_date:
            applicable = period
    return applicable or KNOWN_RATE_PERIODS[0]


def build_rolling_12_months() -> pd.DataFrame:
    """
    Build a DataFrame covering the rolling 12 months ending this month.
    One row per month, one column per charge component.
    """
    today = date.today()
    records = []

    for offset in range(11, -1, -1):
        month_start = (today - relativedelta(months=offset)).replace(day=1)
        rate = get_rate_for_month(month_start)

        # Mobile gen only billed in December
        mobile = rate["mobile_gen"] if month_start.month == 12 else 0.0

        total_fixed    = rate["customer_charge"] + rate["metering_charge"]
        total_variable = rate["distribution"] + rate["dcrf"] + rate["tcrf"] + rate["eecrf"] + mobile

        records.append({
            "month":           month_start.strftime("%b %Y"),
            "month_date":      month_start.isoformat(),
            "effective_date":  rate["effective_date"].isoformat(),
            "customer_charge": rate["customer_charge"],
            "metering_charge": rate["metering_charge"],
            "distribution":    rate["distribution"],
            "dcrf":            rate["dcrf"],
            "tcrf":            rate["tcrf"],
            "eecrf":           rate["eecrf"],
            "mobile_gen":      mobile,
            "total_fixed":     total_fixed,
            "total_variable":  total_variable,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# PDF scraping
# ---------------------------------------------------------------------------

def _fetch_pdf(url: str):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return __import__("io").BytesIO(resp.content)
    except Exception as e:
        print(f"  Could not fetch {url}: {e}")
        return None


def _parse_float(pattern: str, text: str):
    m = re.search(pattern, text, re.IGNORECASE)
    return float(m.group(1).replace(",", "")) if m else None


def scrape_latest_rates() -> dict | None:
    for name, url in PDF_SOURCES.items():
        print(f"Fetching {name}...")
        pdf_bytes = _fetch_pdf(url)
        if not pdf_bytes:
            continue
        try:
            text = ""
            with pdfplumber.open(pdf_bytes) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"

            parsed = {
                "customer_charge": _parse_float(r'customer\s+charge[^\d]*\$?([\d.]+)', text),
                "metering_charge": _parse_float(r'metering\s+charge[^\d]*\$?([\d.]+)', text),
                "distribution":    _parse_float(r'distribution[^\d]*([\d]+\.[\d]{4,})', text),
                "tcrf":            _parse_float(r'tcrf[^\d]*([\d]+\.[\d]{4,})', text),
            }

            valid = (
                all(v is not None for v in parsed.values())
                and 0.5 <= parsed["customer_charge"] <= 10.0
                and 0.5 <= parsed["metering_charge"] <= 10.0
                and 0.5 <= parsed["distribution"]    <= 15.0
                and 0.5 <= parsed["tcrf"]            <= 15.0
            )
            if valid:
                print(f"  Parsed from {name}: {parsed}")
                return parsed
            else:
                print(f"  Values out of expected range, skipping: {parsed}")
        except Exception as e:
            print(f"  Error parsing {name}: {e}")
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_scraper(output_path: str = "data/rates.csv") -> pd.DataFrame:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    live = scrape_latest_rates()
    if live:
        KNOWN_RATE_PERIODS[-1].update(live)
        print("Updated latest rate period from PDF.")
    else:
        print("Using known rate data (PDF parse unavailable).")

    df = build_rolling_12_months()
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} months to {output_path}")
    return df


if __name__ == "__main__":
    run_scraper()
