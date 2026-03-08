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
# Known rate periods (Oncor rates change March 1 and September 1 each year)
# All values: fixed charges in $/month, variable in cents/kWh
# ---------------------------------------------------------------------------
KNOWN_RATE_PERIODS = [
    {
        "effective_date": date(2024, 3, 1),
        "customer_charge":        1.43,
        "metering_charge":        2.80,
        "distribution_cents_kwh": 2.19660,
        "transmission_cents_kwh": 2.08380,
    },
    {
        "effective_date": date(2024, 9, 1),
        "customer_charge":        1.43,
        "metering_charge":        2.80,
        "distribution_cents_kwh": 2.34510,
        "transmission_cents_kwh": 2.22170,
    },
    {
        "effective_date": date(2025, 3, 1),
        "customer_charge":        1.43,
        "metering_charge":        2.80,
        "distribution_cents_kwh": 2.53440,
        "transmission_cents_kwh": 2.35800,
    },
    {
        "effective_date": date(2025, 9, 1),
        "customer_charge":        1.43,
        "metering_charge":        2.80,
        "distribution_cents_kwh": 2.53440,
        "transmission_cents_kwh": 2.35800,
    },
    {
        "effective_date": date(2026, 3, 1),
        "customer_charge":        1.43,
        "metering_charge":        2.80,
        "distribution_cents_kwh": 3.84470,
        "transmission_cents_kwh": 2.35800,
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


# ---------------------------------------------------------------------------
# Rate lookup
# ---------------------------------------------------------------------------

def get_rate_for_month(target_date: date) -> dict:
    """Return the rate period in effect for a given month."""
    applicable = None
    for period in KNOWN_RATE_PERIODS:
        if period["effective_date"] <= target_date:
            applicable = period
    return applicable or KNOWN_RATE_PERIODS[0]


def build_rolling_12_months() -> pd.DataFrame:
    """
    Build a DataFrame covering the rolling 12 months ending this month.
    Months are determined dynamically at runtime.
    """
    today = date.today()
    records = []

    for offset in range(11, -1, -1):
        month_start = (today - relativedelta(months=offset)).replace(day=1)
        rate = get_rate_for_month(month_start)
        records.append({
            "month":                  month_start.strftime("%b %Y"),
            "month_date":             month_start.isoformat(),
            "effective_date":         rate["effective_date"].isoformat(),
            "customer_charge":        rate["customer_charge"],
            "metering_charge":        rate["metering_charge"],
            "distribution_cents_kwh": rate["distribution_cents_kwh"],
            "transmission_cents_kwh": rate["transmission_cents_kwh"],
        })

    df = pd.DataFrame(records)
    df["total_fixed_monthly"]    = df["customer_charge"] + df["metering_charge"]
    df["total_variable_cents"]   = df["distribution_cents_kwh"] + df["transmission_cents_kwh"]
    return df


# ---------------------------------------------------------------------------
# PDF scraping (updates KNOWN_RATE_PERIODS in memory if new data found)
# ---------------------------------------------------------------------------

def _fetch_pdf(url: str) -> BytesIO | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BytesIO(resp.content)
    except Exception as e:
        print(f"  Could not fetch {url}: {e}")
        return None


def _parse_float(pattern: str, text: str) -> float | None:
    m = re.search(pattern, text, re.IGNORECASE)
    return float(m.group(1).replace(",", "")) if m else None


def scrape_latest_rates() -> dict | None:
    """
    Attempt to parse current rates from Oncor/PUCT PDFs.
    Returns a dict of rate values, or None if parsing fails.
    """
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
                "customer_charge":        _parse_float(r'customer\s+charge[^\d]*\$?([\d.]+)', text),
                "metering_charge":        _parse_float(r'metering\s+charge[^\d]*\$?([\d.]+)', text),
                "distribution_cents_kwh": _parse_float(r'distribution[^\d]*([\d]+\.[\d]{3,})', text),
                "transmission_cents_kwh": _parse_float(r'(?:transmission|tcrf)[^\d]*([\d]+\.[\d]{3,})', text),
            }

            # Validate parsed values are in realistic ranges before accepting
            valid = (
                all(v is not None for v in parsed.values())
                and 0.5  <= parsed["customer_charge"]        <= 10.0
                and 0.5  <= parsed["metering_charge"]        <= 10.0
                and 0.5  <= parsed["distribution_cents_kwh"] <= 15.0
                and 0.5  <= parsed["transmission_cents_kwh"] <= 15.0
            )
            if valid:
                print(f"  Parsed from {name}: {parsed}")
                return parsed
            else:
                print(f"  Parsed values out of expected range, skipping: {parsed}")
        except Exception as e:
            print(f"  Error parsing {name}: {e}")

    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_scraper(output_path: str = "data/rates.csv") -> pd.DataFrame:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Try to update the most recent known period with live PDF data
    live = scrape_latest_rates()
    if live:
        KNOWN_RATE_PERIODS[-1].update(live)
        print("Updated latest rate period from PDF.")
    else:
        print("Using known rate data (PDF parse failed or unavailable).")

    df = build_rolling_12_months()
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} months to {output_path}")
    return df


if __name__ == "__main__":
    run_scraper()
