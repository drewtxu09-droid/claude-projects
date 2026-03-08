"""
Oncor TDU Residential Rate Dashboard
Run: python app.py  →  open http://localhost:8050
"""

import os
import pandas as pd
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output

from scraper import run_scraper, build_rolling_12_months, CHARGE_DEFS

DATA_FILE = "data/rates.csv"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Oncor TDU Dashboard"

COLORS = {
    "bg":       "#1e1e2e",
    "card_bg":  "#2a2a3e",
    "text":     "#e0e0ff",
    "muted":    "#888",
    "fixed":    "#06d6a0",
    "variable": "#00b4d8",
    "header":   "#2a2a4a",
    "section":  "#1a2a3a",
    "palette":  ["#00b4d8", "#f77f00", "#06d6a0", "#a29bfe", "#ff6b9d", "#ffd166", "#b7e4c7"],
}

VARIABLE_CHARGES = [k for k, _, cat, _ in CHARGE_DEFS if cat == "Variable"]
VARIABLE_LABELS  = {k: lbl for k, lbl, cat, _ in CHARGE_DEFS if cat == "Variable"}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_data() -> pd.DataFrame:
    if not os.path.exists(DATA_FILE):
        return run_scraper(DATA_FILE)
    return pd.read_csv(DATA_FILE)


# ---------------------------------------------------------------------------
# Pivot table: charges as rows, months as columns
# ---------------------------------------------------------------------------

def build_pivot(df: pd.DataFrame) -> pd.DataFrame:
    months = df["month"].tolist()
    rows = []

    # Section header — Fixed
    rows.append({"Charge": "FIXED CHARGES", "Unit": "", **{m: "" for m in months}, "_section": True})

    for key, label, category, unit in CHARGE_DEFS:
        if category != "Fixed":
            continue
        row = {"Charge": label, "Unit": unit, "_section": False}
        for _, r in df.iterrows():
            row[r["month"]] = f"${r[key]:.2f}"
        rows.append(row)

    # Total fixed
    row = {"Charge": "Total Fixed", "Unit": "$/mo", "_section": False, "_total": True}
    for _, r in df.iterrows():
        row[r["month"]] = f"${r['total_fixed']:.2f}"
    rows.append(row)

    # Section header — Variable
    rows.append({"Charge": "VARIABLE CHARGES", "Unit": "", **{m: "" for m in months}, "_section": True})

    for key, label, category, unit in CHARGE_DEFS:
        if category != "Variable":
            continue
        row = {"Charge": label, "Unit": unit, "_section": False}
        for _, r in df.iterrows():
            row[r["month"]] = f"{r[key]:.5f}"
        rows.append(row)

    # Total variable
    row = {"Charge": "Total Variable", "Unit": "¢/kWh", "_section": False, "_total": True}
    for _, r in df.iterrows():
        row[r["month"]] = f"{r['total_variable']:.5f}"
    rows.append(row)

    return pd.DataFrame(rows)


def make_pivot_table(df: pd.DataFrame) -> dash_table.DataTable:
    pivot = build_pivot(df)
    months = df["month"].tolist()

    columns = [
        {"name": "Charge",  "id": "Charge"},
        {"name": "Unit",    "id": "Unit"},
    ] + [{"name": m, "id": m} for m in months]

    # Style rules
    section_rows  = [i for i, r in pivot.iterrows() if r.get("_section")]
    total_rows    = [i for i, r in pivot.iterrows() if r.get("_total")]

    style_data_conditional = [
        {"if": {"row_index": i},
         "backgroundColor": COLORS["section"],
         "color": COLORS["text"],
         "fontWeight": "bold",
         "fontSize": "0.75rem",
         "letterSpacing": "1px"} for i in section_rows
    ] + [
        {"if": {"row_index": i},
         "backgroundColor": COLORS["header"],
         "color": "#fff",
         "fontWeight": "bold"} for i in total_rows
    ]

    display_data = pivot.drop(columns=["_section", "_total"], errors="ignore").to_dict("records")

    return dash_table.DataTable(
        id="pivot-table",
        data=display_data,
        columns=columns,
        style_header={
            "backgroundColor": COLORS["header"],
            "color": COLORS["text"],
            "fontWeight": "bold",
            "border": "1px solid #444",
            "textAlign": "center",
        },
        style_data={
            "backgroundColor": COLORS["bg"],
            "color": "#ccc",
            "border": "1px solid #2a2a4a",
        },
        style_data_conditional=style_data_conditional,
        style_cell={
            "textAlign":  "center",
            "padding":    "7px 10px",
            "minWidth":   "80px",
            "fontFamily": "monospace",
        },
        style_cell_conditional=[
            {"if": {"column_id": "Charge"}, "textAlign": "left", "minWidth": "260px", "fontFamily": "sans-serif"},
            {"if": {"column_id": "Unit"},   "minWidth": "60px"},
        ],
        page_action="none",
    )


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_variable_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for i, key in enumerate(VARIABLE_CHARGES):
        nonzero = df[key].sum() > 0
        if not nonzero:
            continue
        fig.add_trace(go.Bar(
            name=VARIABLE_LABELS[key],
            x=df["month"],
            y=df[key],
            marker_color=COLORS["palette"][i % len(COLORS["palette"])],
            hovertemplate="%{y:.5f} ¢/kWh<extra>" + VARIABLE_LABELS[key] + "</extra>",
        ))
    fig.update_layout(
        barmode="stack",
        title=dict(text="Variable Charges by Month (¢/kWh)", font=dict(color=COLORS["text"])),
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, x=0),
        yaxis=dict(title="¢/kWh", gridcolor="#333"),
        xaxis=dict(side="top", gridcolor="#333", tickangle=-30),
        margin=dict(t=120),
        height=420,
    )
    return fig


def make_fixed_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for key, label, cat, _ in CHARGE_DEFS:
        if cat != "Fixed":
            continue
        fig.add_trace(go.Scatter(
            name=label,
            x=df["month"],
            y=df[key],
            mode="lines+markers",
            line=dict(width=2),
            marker=dict(size=7),
            hovertemplate="$%{y:.2f}/mo<extra>" + label + "</extra>",
        ))
    fig.update_layout(
        title=dict(text="Fixed Charges by Month ($/mo)", font=dict(color=COLORS["text"])),
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, x=0),
        yaxis=dict(title="$/month", gridcolor="#333"),
        xaxis=dict(side="top", gridcolor="#333", tickangle=-30),
        margin=dict(t=120),
        height=380,
    )
    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def make_card(label, value, color):
    return dbc.Col(
        dbc.Card(dbc.CardBody([
            html.P(label, className="text-muted mb-1",
                   style={"fontSize": "0.75rem", "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.H5(value, style={"color": color, "fontWeight": "bold", "marginBottom": 0}),
        ]), style={"backgroundColor": COLORS["card_bg"], "border": "1px solid #333"}, className="text-center"),
        width=True,
    )


def build_layout(df: pd.DataFrame) -> html.Div:
    cur = df.iloc[-1]
    date_range = f"{df['month'].iloc[0]}  →  {df['month'].iloc[-1]}"
    last_updated = pd.Timestamp.now().strftime("%B %d, %Y")

    cards = dbc.Row([
        make_card("Customer Charge",    f"${cur['customer_charge']:.2f}/mo",     COLORS["fixed"]),
        make_card("Metering Charge",    f"${cur['metering_charge']:.2f}/mo",     COLORS["fixed"]),
        make_card("Distribution",       f"{cur['distribution']:.5f} ¢/kWh",     COLORS["variable"]),
        make_card("DCRF",               f"{cur['dcrf']:.5f} ¢/kWh",             COLORS["variable"]),
        make_card("TCRF",               f"{cur['tcrf']:.5f} ¢/kWh",             COLORS["variable"]),
        make_card("EECRF",              f"{cur['eecrf']:.5f} ¢/kWh",            COLORS["variable"]),
        make_card("Total Variable",     f"{cur['total_variable']:.5f} ¢/kWh",   "#ffd166"),
    ], className="mb-4 g-2")

    return html.Div(
        style={"backgroundColor": COLORS["bg"], "minHeight": "100vh", "padding": "24px"},
        children=[
            html.H2("Oncor TDU Residential Rate Dashboard",
                    style={"color": COLORS["text"], "textAlign": "center", "marginBottom": "4px"}),
            html.P(f"ERCOT Market · Texas · Rolling 12 Months ({date_range})",
                   style={"color": COLORS["muted"], "textAlign": "center", "marginBottom": "2px"}),
            html.P("Residential customers only · Rates sourced from Oncor & PUCT",
                   style={"color": COLORS["muted"], "textAlign": "center", "fontSize": "0.8rem", "marginBottom": "24px"}),

            dbc.Container([
                cards,

                # Pivot table — charges as rows, months as columns
                html.H5("Rate Detail by Charge Component", style={"color": COLORS["text"], "marginBottom": "10px"}),
                make_pivot_table(df),
                html.Br(),

                # Variable charges chart (months on top x-axis)
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=make_variable_chart(df), config={"displayModeBar": False}), width=12),
                ], className="mb-3"),

                # Fixed charges chart (months on top x-axis)
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=make_fixed_chart(df), config={"displayModeBar": False}), width=12),
                ], className="mb-4"),

                # Refresh
                dbc.Row([
                    dbc.Col(
                        dbc.Button("Refresh Data from Oncor / PUCT", id="refresh-btn",
                                   color="primary", outline=True),
                        width="auto",
                    ),
                    dbc.Col(
                        html.P(id="refresh-status",
                               style={"color": COLORS["muted"], "fontSize": "0.85rem", "marginTop": "6px"}),
                        width="auto",
                    ),
                ], className="mb-4"),

                html.Hr(style={"borderColor": "#333"}),
                html.P(f"Last updated: {last_updated} · Data: Oncor Electric Delivery & PUCT",
                       style={"color": COLORS["muted"], "textAlign": "center", "fontSize": "0.8rem"}),
            ], fluid=True),
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
        return "Data refreshed successfully."
    except Exception as e:
        return f"Refresh failed: {e}"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

df = load_data()
app.layout = build_layout(df)

if __name__ == "__main__":
    print("Starting Oncor TDU Dashboard at http://localhost:8050")
    app.run(debug=False, port=8050)
