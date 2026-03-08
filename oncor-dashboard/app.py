"""
Oncor TDU Rate Dashboard
Two tabs: Residential  |  Secondary Less Than 10 kW
Run: python app.py  →  open http://localhost:8050
"""

import os
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dash_table, Input, Output
from datetime import date

from scraper import (
    run_scraper, run_scraper_sec,
    CHARGE_DEFS, CHARGE_META, CHARGE_META_SEC,
)

DATA_FILE     = "data/rates.csv"
DATA_FILE_SEC = "data/rates_sec.csv"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Oncor TDU Dashboard"

COLORS = {
    "bg":      "#1e1e2e",
    "card_bg": "#2a2a3e",
    "text":    "#e0e0ff",
    "muted":   "#888",
    "header":  "#2a2a4a",
    "section": "#1a2a3a",
    "total":   "#2a2a4a",
}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_data(path: str, scraper_fn) -> pd.DataFrame:
    if not os.path.exists(path):
        return scraper_fn(path)
    df = pd.read_csv(path)
    # Re-run if stale calendar-year format (single abbreviated month like "Jan")
    if len(str(df["month"].iloc[0])) <= 3:
        return scraper_fn(path)
    return df


# ---------------------------------------------------------------------------
# Pivot table builders
# ---------------------------------------------------------------------------

def _fmt_fixed(val) -> str:
    return f"${val:.2f}"

def _fmt_var(val) -> str:
    return "0" if val == 0 else f"{val:.6f}"

def _fmt_pending(key: str, unit: str, charge_meta: dict) -> str:
    amt = charge_meta.get(key, {}).get("pending_amount")
    if amt is None:
        return ""
    return f"${amt:.2f}" if unit == "$/mo" else f"{amt:.6f}"


def build_pivot(df: pd.DataFrame, charge_meta: dict) -> pd.DataFrame:
    months = df["month"].tolist()
    rows = []

    def make_month_cells(key, fmt_fn):
        return {r["month"]: fmt_fn(r[key]) for _, r in df.iterrows()}

    # ---- Fixed Charges section header ----
    rows.append({
        "SAC04": "", "Charge": "Fixed Charges", "PUC": "", "Notes": "",
        "Pending_Amount": "", "Pending_Date": "", "Pending_Status": "", "Pending_PUC": "",
        **{m: "" for m in months}, "_section": True,
    })

    for key, label, category, unit, sac in CHARGE_DEFS:
        if category != "Fixed":
            continue
        meta = charge_meta.get(key, {})
        rows.append({
            "SAC04":          sac,
            "Charge":         label,
            "PUC":            meta.get("puc_no") or "",
            "Notes":          meta.get("notes") or "",
            "Pending_Amount": _fmt_pending(key, unit, charge_meta),
            "Pending_Date":   str(meta.get("pending_date") or ""),
            "Pending_Status": meta.get("pending_status") or "",
            "Pending_PUC":    str(meta.get("pending_puc") or ""),
            **make_month_cells(key, _fmt_fixed),
            "_section": False,
        })

    # ---- Variable Charges section header ----
    rows.append({
        "SAC04": "", "Charge": "Variable Charges", "PUC": "", "Notes": "",
        "Pending_Amount": "", "Pending_Date": "", "Pending_Status": "", "Pending_PUC": "",
        **{m: "" for m in months}, "_section": True,
    })

    for key, label, category, unit, sac in CHARGE_DEFS:
        if category != "Variable":
            continue
        meta = charge_meta.get(key, {})
        rows.append({
            "SAC04":          sac,
            "Charge":         label,
            "PUC":            meta.get("puc_no") or "",
            "Notes":          meta.get("notes") or "",
            "Pending_Amount": _fmt_pending(key, unit, charge_meta),
            "Pending_Date":   str(meta.get("pending_date") or ""),
            "Pending_Status": meta.get("pending_status") or "",
            "Pending_PUC":    str(meta.get("pending_puc") or ""),
            **make_month_cells(key, _fmt_var),
            "_section": False,
        })

    # ---- Spacer rows before totals ----
    blank = {
        "SAC04": "", "Charge": "", "PUC": "", "Notes": "",
        "Pending_Amount": "", "Pending_Date": "", "Pending_Status": "", "Pending_PUC": "",
        **{m: "" for m in months}, "_section": False, "_spacer": True,
    }
    rows.append(blank.copy())
    rows.append(blank.copy())

    # ---- Totals (both at the bottom) ----
    rows.append({
        "SAC04": "", "Charge": "Fixed Charges (per customer)", "PUC": "", "Notes": "",
        "Pending_Amount": "", "Pending_Date": "", "Pending_Status": "", "Pending_PUC": "",
        **make_month_cells("total_fixed", _fmt_fixed),
        "_section": False, "_total": True,
    })
    rows.append({
        "SAC04": "", "Charge": "Variable Charges (per kWh consumption)", "PUC": "", "Notes": "",
        "Pending_Amount": "", "Pending_Date": "", "Pending_Status": "", "Pending_PUC": "",
        **make_month_cells("total_variable", _fmt_var),
        "_section": False, "_total": True,
    })

    return pd.DataFrame(rows)


def make_pivot_table(df: pd.DataFrame, charge_meta: dict, table_id: str) -> dash_table.DataTable:
    pivot  = build_pivot(df, charge_meta)
    months = df["month"].tolist()

    columns = [
        {"name": ["",                "SAC04 Code"],         "id": "SAC04"},
        {"name": ["",                "SAC04 Descriptions"], "id": "Charge"},
        {"name": ["",                "PUC Control #"],      "id": "PUC"},
        {"name": ["",                "Notes"],              "id": "Notes"},
        {"name": ["Pending Changes", "Pending Amount"],     "id": "Pending_Amount"},
        {"name": ["Pending Changes", "Date of Change"],     "id": "Pending_Date"},
        {"name": ["Pending Changes", "Status"],             "id": "Pending_Status"},
        {"name": ["Pending Changes", "PUC Control #"],      "id": "Pending_PUC"},
    ] + [{"name": ["", m], "id": m} for m in months]

    section_rows = [i for i, r in pivot.iterrows() if r.get("_section")]
    total_rows   = [i for i, r in pivot.iterrows() if r.get("_total")]

    # Find Mobile Generation row index and which months have a non-zero charge
    mg_matches  = pivot[pivot["Charge"] == "Mobile Generation (MG)"].index.tolist()
    mg_row_idx  = mg_matches[0] if mg_matches else None
    mg_months   = [r["month"] for _, r in df.iterrows() if r["mobile_gen"] != 0]

    style_data_conditional = [
        {
            "if": {"row_index": i},
            "backgroundColor": COLORS["section"],
            "color": COLORS["text"],
            "fontWeight": "bold",
            "fontSize": "0.62rem",
            "letterSpacing": "1px",
        } for i in section_rows
    ] + [
        {
            "if": {"row_index": i},
            "backgroundColor": COLORS["total"],
            "color": "#fff",
            "fontWeight": "bold",
        } for i in total_rows
    ] + (
        [
            {
                "if": {"row_index": mg_row_idx, "column_id": m},
                "backgroundColor": "#e85d04",
                "color": "#fff",
                "fontWeight": "bold",
            }
            for m in mg_months
        ] if mg_row_idx is not None else []
    )

    display_data = pivot.drop(columns=["_section", "_total", "_spacer"], errors="ignore").to_dict("records")

    return dash_table.DataTable(
        id=table_id,
        data=display_data,
        columns=columns,
        merge_duplicate_headers=True,
        style_header={
            "backgroundColor": COLORS["header"],
            "color": COLORS["text"],
            "fontWeight": "bold",
            "border": "1px solid #444",
            "textAlign": "center",
            "whiteSpace": "nowrap",
            "fontSize": "0.62rem",
            "padding": "4px 5px",
        },
        style_data={
            "backgroundColor": COLORS["bg"],
            "color": "#ccc",
            "border": "1px solid #2a2a4a",
        },
        style_data_conditional=style_data_conditional,
        style_cell={
            "textAlign": "center",
            "padding": "3px 5px",
            "fontFamily": "monospace",
            "fontSize": "0.62rem",
            "whiteSpace": "nowrap",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_cell_conditional=[
            {"if": {"column_id": "Charge"}, "textAlign": "left", "fontFamily": "sans-serif"},
            {"if": {"column_id": "Notes"},  "textAlign": "left", "fontFamily": "sans-serif"},
        ],
        page_action="none",
        style_table={"overflowX": "auto", "fontSize": "0.62rem"},
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def build_layout(df_res: pd.DataFrame, df_sec: pd.DataFrame) -> html.Div:
    current_year  = date.today().year
    last_updated  = pd.Timestamp.now().strftime("%B %d, %Y %I:%M %p")

    return html.Div(
        style={"backgroundColor": COLORS["bg"], "minHeight": "100vh", "padding": "12px 16px"},
        children=[
            html.H2("Oncor Electric Delivery — TDU Rate Dashboard",
                    style={"color": COLORS["text"], "marginBottom": "2px"}),
            html.P(f"Year {current_year}  ·  Rolling 12 Months",
                   style={"color": COLORS["muted"], "marginBottom": "12px", "fontSize": "0.85rem"}),

            dbc.Tabs(
                id="rate-tabs",
                active_tab="residential",
                children=[
                    dbc.Tab(
                        label="Residential",
                        tab_id="residential",
                        children=dbc.Container([
                            html.P("Rate Class: Residential",
                                   style={"color": COLORS["muted"], "fontSize": "0.8rem",
                                          "marginBottom": "8px", "marginTop": "12px"}),
                            make_pivot_table(df_res, CHARGE_META, "pivot-res"),
                        ], fluid=True),
                    ),
                    dbc.Tab(
                        label="Secondary < 10 kW",
                        tab_id="secondary",
                        children=dbc.Container([
                            html.P("Rate Class: Secondary Less Than 10 kW",
                                   style={"color": COLORS["muted"], "fontSize": "0.8rem",
                                          "marginBottom": "8px", "marginTop": "12px"}),
                            make_pivot_table(df_sec, CHARGE_META_SEC, "pivot-sec"),
                        ], fluid=True),
                    ),
                ],
            ),

            html.Br(),
            dbc.Row([
                dbc.Col(
                    dbc.Button("Refresh Data", id="refresh-btn",
                               color="primary", outline=True, size="sm"),
                    width="auto",
                ),
                dbc.Col(
                    html.P(id="refresh-status",
                           style={"color": COLORS["muted"], "fontSize": "0.8rem", "marginTop": "6px"}),
                    width="auto",
                ),
            ], className="mb-3"),

            html.Hr(style={"borderColor": "#333"}),
            html.P(f"Last updated: {last_updated} · Data: Oncor Electric Delivery & PUCT",
                   style={"color": COLORS["muted"], "textAlign": "center", "fontSize": "0.75rem"}),
        ]
    )


# ---------------------------------------------------------------------------
# Callback
# ---------------------------------------------------------------------------

@app.callback(
    Output("refresh-status", "children"),
    Input("refresh-btn", "n_clicks"),
    prevent_initial_call=True,
)
def refresh_data(n_clicks):
    try:
        run_scraper(DATA_FILE)
        run_scraper_sec(DATA_FILE_SEC)
        return "Data refreshed successfully."
    except Exception as e:
        return f"Refresh failed: {e}"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

df_res = load_data(DATA_FILE,     run_scraper)
df_sec = load_data(DATA_FILE_SEC, run_scraper_sec)
app.layout = build_layout(df_res, df_sec)

if __name__ == "__main__":
    print("Starting Oncor TDU Dashboard at http://localhost:8050")
    app.run(debug=False, port=8050)
