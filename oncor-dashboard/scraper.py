"""
Oncor TDU Rate Scraper
Supports Residential and Secondary Less Than 10 kW rate classes.
All variable charges in $/kWh, fixed charges in $/mo.
"""

import os
import re
import requests
import pdfplumber
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# ---------------------------------------------------------------------------
# RESIDENTIAL — Known rate periods
# Rates change March 1 and September 1 each year
# ---------------------------------------------------------------------------
KNOWN_RATE_PERIODS = [
    {
        "effective_date":   date(2024, 3, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021966,
        "ndc":              0.000199,  # zeroed Dec 15, 2025
        "dcrf":             0.005427,
        "mobile_gen":       0.000000,  # only billed in December
        "tcrf":             0.020838,
        "eecrf":            0.001137,
    },
    {
        "effective_date":   date(2024, 9, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.023451,
        "ndc":              0.000199,
        "dcrf":             0.005427,
        "mobile_gen":       0.000000,
        "tcrf":             0.022217,
        "eecrf":            0.001137,
    },
    {
        "effective_date":   date(2025, 3, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.025344,
        "ndc":              0.000199,
        "dcrf":             0.005772,
        "mobile_gen":       0.000000,
        "tcrf":             0.023580,
        "eecrf":            0.001137,
    },
    {
        "effective_date":   date(2025, 9, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.025344,
        "ndc":              0.000199,
        "dcrf":             0.005772,
        "mobile_gen":       0.000000,
        "tcrf":             0.023580,
        "eecrf":            0.001137,
    },
    {
        "effective_date":   date(2025, 12, 15),  # NDC zeroed
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.025344,
        "ndc":              0.000000,  # NDC ended
        "dcrf":             0.005772,
        "mobile_gen":       0.000000,
        "tcrf":             0.023580,
        "eecrf":            0.001137,
    },
    {
        "effective_date":   date(2026, 3, 1),
        "customer_charge":  1.43,
        "metering_charge":  2.80,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.025344,
        "ndc":              0.000000,
        "dcrf":             0.005772,
        "mobile_gen":       0.000000,
        "tcrf":             0.023580,
        "eecrf":            0.001487,  # EECRF resets each March
    },
]

# ---------------------------------------------------------------------------
# SECONDARY LESS THAN 10 kW — Known rate periods
# Base rates from Docket 53601 (effective May 1, 2023)
# TCRF resets March 1 and September 1; DCRF updated as filed; EECRF resets March 1
# ---------------------------------------------------------------------------
KNOWN_RATE_PERIODS_SEC = [
    {
        "effective_date":   date(2024, 3, 1),
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000130,  # zeroed Dec 15, 2025
        "dcrf":             0.002411,  # eff Dec 28, 2023
        "mobile_gen":       0.000519,  # only billed in December; Dec 2024 rate
        "tcrf":             0.014368,  # eff Mar 1, 2024
        "eecrf":            0.000036,  # eff Mar 1, 2024
    },
    {
        "effective_date":   date(2024, 7, 1),
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000130,
        "dcrf":             0.003573,  # eff Jul 1, 2024
        "mobile_gen":       0.000519,
        "tcrf":             0.014368,
        "eecrf":            0.000036,
    },
    {
        "effective_date":   date(2024, 9, 1),
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000130,
        "dcrf":             0.003573,
        "mobile_gen":       0.000519,
        "tcrf":             0.018422,  # eff Sep 1, 2024
        "eecrf":            0.000036,
    },
    {
        "effective_date":   date(2024, 12, 8),
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000130,
        "dcrf":             0.004811,  # eff Dec 8, 2024
        "mobile_gen":       0.000519,
        "tcrf":             0.018422,
        "eecrf":            0.000036,
    },
    {
        "effective_date":   date(2025, 3, 1),
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000130,
        "dcrf":             0.004811,
        "mobile_gen":       0.000606,  # Dec 2025 rate (eff Dec 1, 2025)
        "tcrf":             0.018606,  # eff Mar 1, 2025
        "eecrf":            -0.000196, # eff Mar 1, 2025 — credit (over-recovery)
    },
    {
        "effective_date":   date(2025, 5, 10),
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000130,
        "dcrf":             0.006411,  # eff May 10, 2025
        "mobile_gen":       0.000606,
        "tcrf":             0.018606,
        "eecrf":            -0.000196,
    },
    {
        "effective_date":   date(2025, 9, 1),
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000130,
        "dcrf":             0.006411,
        "mobile_gen":       0.000606,
        "tcrf":             0.018157,  # eff Sep 1, 2025
        "eecrf":            -0.000196,
    },
    {
        "effective_date":   date(2025, 12, 15),  # NDC zeroed
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000000,  # NDC ended
        "dcrf":             0.006411,
        "mobile_gen":       0.000606,
        "tcrf":             0.018157,
        "eecrf":            -0.000196,
    },
    {
        "effective_date":   date(2026, 3, 1),
        "customer_charge":  2.26,
        "metering_charge":  4.61,
        "isr":              0.000000,
        "transmission":     0.000000,
        "rces":             0.000000,
        "distribution":     0.021251,
        "ndc":              0.000000,
        "dcrf":             0.006411,
        "mobile_gen":       0.000606,
        "tcrf":             0.018157,
        "eecrf":            0.000055,  # eff Mar 1, 2026 — resets each March
    },
]

# ---------------------------------------------------------------------------
# Charge definitions (shared by both rate classes)
# (column_key, display_label, category, unit, sac04_code)
# ---------------------------------------------------------------------------
CHARGE_DEFS = [
    ("customer_charge", "Customer Charge",                                    "Fixed",    "$/mo",   "BAS001"),
    ("metering_charge", "Metering Charge",                                    "Fixed",    "$/mo",   "BAS003"),
    ("isr",             "Interest Savings Refund",                            "Variable", "$/kWh",  "RRR008"),
    ("transmission",    "Transmission System Charge",                         "Variable", "$/kWh",  "TRN001"),
    ("rces",            "Rate Case Expense Surcharge",                        "Variable", "$/kWh",  "MSC049"),
    ("distribution",    "Distribution System Charge",                         "Variable", "$/kWh",  "DIS001"),
    ("ndc",             "Nuclear Decommissioning Charge (NDC)",               "Variable", "$/kWh",  "MSC025"),
    ("dcrf",            "Distribution Cost Recovery Factor (DCRF)",           "Variable", "$/kWh",  "MSC042"),
    ("mobile_gen",      "Mobile Generation (MG)",                             "Variable", "$/kWh",  "MSC057"),
    ("tcrf",            "Transmission Cost Recovery Factor (TCRF)",           "Variable", "$/kWh",  "TRN002"),
    ("eecrf",           "Energy Efficiency Cost Recovery Factor (EECRF)",     "Variable", "$/kWh",  "MSC041"),
]

# ---------------------------------------------------------------------------
# Charge metadata — Residential
# ---------------------------------------------------------------------------
CHARGE_META = {
    "customer_charge": {
        "puc_no": "38929", "notes": None,
        "pending_amount": 1.48,     "pending_date": "May 2026",  "pending_status": "Proposed", "pending_puc": "58306",
    },
    "metering_charge": {
        "puc_no": "38929", "notes": None,
        "pending_amount": 2.58,     "pending_date": "May 2026",  "pending_status": "Proposed", "pending_puc": "58306",
    },
    "isr": {
        "puc_no": "49314", "notes": "Expired 12/21/2022; last refund issued 12/2023",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "transmission": {
        "puc_no": "38929", "notes": None,
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "rces": {
        "puc_no": "53601", "notes": "Expired 2/24/25",
        "pending_amount": 0.000086, "pending_date": "May 2026",  "pending_status": "Proposed", "pending_puc": "58306",
    },
    "distribution": {
        "puc_no": "38929", "notes": None,
        "pending_amount": 0.036043, "pending_date": "May 2026",  "pending_status": "Proposed", "pending_puc": "58306",
    },
    "ndc": {
        "puc_no": "23921", "notes": "Ended 12/15/2025",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "dcrf": {
        "puc_no": "48231", "notes": "Applications up to 2x each year",
        "pending_amount": None,     "pending_date": "May 2026",  "pending_status": "Proposed", "pending_puc": "58306",
    },
    "mobile_gen": {
        "puc_no": "48231", "notes": "Collected only during December billing period",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "tcrf": {
        "puc_no": "39940", "notes": "Resets every Mar 1 & Sept 1",
        "pending_amount": 0.019046, "pending_date": "3/1/2026?", "pending_status": "Proposed", "pending_puc": "59046",
    },
    "eecrf": {
        "puc_no": "39375", "notes": "Resets each March",
        "pending_amount": 0.001487, "pending_date": "3/1/2026",  "pending_status": "Approved", "pending_puc": "58182",
    },
}

# ---------------------------------------------------------------------------
# Charge metadata — Secondary Less Than 10 kW
# ---------------------------------------------------------------------------
CHARGE_META_SEC = {
    "customer_charge": {
        "puc_no": "53601", "notes": None,
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "metering_charge": {
        "puc_no": "53601", "notes": None,
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "isr": {
        "puc_no": "47675", "notes": "Semi-annual variable credit; amount set by PUCT compliance filing",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "transmission": {
        "puc_no": "53601", "notes": None,
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "rces": {
        "puc_no": "53601", "notes": "Currently zero",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "distribution": {
        "puc_no": "53601", "notes": None,
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "ndc": {
        "puc_no": "23921", "notes": "Ended 12/15/2025",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "dcrf": {
        "puc_no": "55525", "notes": "Applications up to 2x each year",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "mobile_gen": {
        "puc_no": "48231", "notes": "Collected only during December billing period",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "tcrf": {
        "puc_no": "39940", "notes": "Resets every Mar 1 & Sept 1",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
    "eecrf": {
        "puc_no": "39375", "notes": "Resets each March; may be positive or negative (credit)",
        "pending_amount": None,     "pending_date": None,        "pending_status": None,       "pending_puc": None,
    },
}

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

def get_rate_for_month(target_date: date, rate_periods: list) -> dict:
    applicable = None
    for period in rate_periods:
        if period["effective_date"] <= target_date:
            applicable = period
    return applicable or rate_periods[0]


def build_rolling_12_months(rate_periods: list) -> pd.DataFrame:
    """
    Build a DataFrame covering the rolling 12 months ending this month.
    One row per month, one column per charge component.
    """
    today = date.today()
    records = []

    for offset in range(11, -1, -1):
        month_start = (today - relativedelta(months=offset)).replace(day=1)
        rate = get_rate_for_month(month_start, rate_periods)

        mobile = rate["mobile_gen"] if month_start.month == 12 else 0.0

        total_fixed    = rate["customer_charge"] + rate["metering_charge"]
        total_variable = (
            rate["isr"] + rate["transmission"] + rate["rces"] +
            rate["distribution"] + rate["ndc"] + rate["dcrf"] +
            mobile + rate["tcrf"] + rate["eecrf"]
        )

        records.append({
            "month":           month_start.strftime("%b %Y"),
            "month_date":      month_start.isoformat(),
            "effective_date":  rate["effective_date"].isoformat(),
            "customer_charge": rate["customer_charge"],
            "metering_charge": rate["metering_charge"],
            "isr":             rate["isr"],
            "transmission":    rate["transmission"],
            "rces":            rate["rces"],
            "distribution":    rate["distribution"],
            "ndc":             rate["ndc"],
            "dcrf":            rate["dcrf"],
            "mobile_gen":      mobile,
            "tcrf":            rate["tcrf"],
            "eecrf":           rate["eecrf"],
            "total_fixed":     total_fixed,
            "total_variable":  total_variable,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# PDF scraping (residential only)
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
# Main entry points
# ---------------------------------------------------------------------------

def run_scraper(output_path: str = "data/rates.csv") -> pd.DataFrame:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    live = scrape_latest_rates()
    if live:
        KNOWN_RATE_PERIODS[-1].update(live)
        print("Updated latest rate period from PDF.")
    else:
        print("Using known rate data (PDF parse unavailable).")

    df = build_rolling_12_months(KNOWN_RATE_PERIODS)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} months to {output_path}")
    return df


def run_scraper_sec(output_path: str = "data/rates_sec.csv") -> pd.DataFrame:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = build_rolling_12_months(KNOWN_RATE_PERIODS_SEC)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} months to {output_path}")
    return df


if __name__ == "__main__":
    run_scraper()
    run_scraper_sec()
