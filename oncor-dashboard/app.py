"""
Oncor TDU Residential Rate Dashboard
Run: python app.py
Then open http://localhost:8050
"""

import os
import pandas as pd
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output

from scraper import run_scraper, build_rolling_12_months

DATA_FILE = "data/rates.csv"

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Oncor TDU Dashboard"

COLORS = {
    "distribution":  "#00b4d8",
    "transmission":  "#f77f00",
    "customer":      "#06d6a0",
    "metering":      "#a29bfe",
    "bg":            "#1e1e2e",
    "card_bg":       "#2a2a3e",
    "text":          "#e0e0ff",
    "muted":         "#888",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> pd.DataFrame:
    """Load from CSV if fresh; otherwise run scraper to regenerate."""
    if not os.path.exists(DATA_FILE):
        return run_scraper(DATA_FILE)
    return pd.read_csv(DATA_FILE)


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def make_variable_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Distribution (¢/kWh)",
        x=df["month"],
        y=df["distribution_cents_kwh"],
        marker_color=COLORS["distribution"],
        hovertemplate="%{y:.5f}¢/kWh<extra>Distribution</extra>",
    ))
    fig.add_trace(go.Bar(
        name="Transmission / TCRF (¢/kWh)",
        x=df["month"],
        y=df["transmission_cents_kwh"],
        marker_color=COLORS["transmission"],
        hovertemplate="%{y:.5f}¢/kWh<extra>Transmission</extra>",
    ))
    fig.update_layout(
        barmode="stack",
        title=dict(text="Variable Delivery Charges by Month", font=dict(color=COLORS["text"])),
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        yaxis=dict(title="¢/kWh", gridcolor="#333"),
        xaxis=dict(gridcolor="#333"),
        margin=dict(t=60),
    )
    return fig


def make_fixed_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name="Customer Charge ($/mo)",
        x=df["month"],
        y=df["customer_charge"],
        mode="lines+markers",
        line=dict(color=COLORS["customer"], width=2),
        marker=dict(size=7),
        hovertemplate="$%{y:.2f}/mo<extra>Customer Charge</extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Metering Charge ($/mo)",
        x=df["month"],
        y=df["metering_charge"],
        mode="lines+markers",
        line=dict(color=COLORS["metering"], width=2),
        marker=dict(size=7),
        hovertemplate="$%{y:.2f}/mo<extra>Metering Charge</extra>",
    ))
    fig.update_layout(
        title=dict(text="Fixed Monthly Charges", font=dict(color=COLORS["text"])),
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        yaxis=dict(title="$/month", gridcolor="#333"),
        xaxis=dict(gridcolor="#333"),
        margin=dict(t=60),
    )
    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def make_metric_card(label: str, value: str, color: str) -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.P(label, className="text-muted mb-1", style={"fontSize": "0.8rem", "textTransform": "uppercase", "letterSpacing": "1px"}),
                html.H4(value, style={"color": color, "fontWeight": "bold"}),
            ]),
            style={"backgroundColor": COLORS["card_bg"], "border": "1px solid #333"},
            className="text-center",
        ),
        width=3,
    )


def build_layout(df: pd.DataFrame) -> html.Div:
    cur = df.iloc[-1]
    last_updated = pd.Timestamp.now().strftime("%B %d, %Y")
    date_range = f"{df['month'].iloc[0]}  →  {df['month'].iloc[-1]}"

    cards = dbc.Row([
        make_metric_card("Customer Charge",     f"${cur['customer_charge']:.2f} / mo",     COLORS["customer"]),
        make_metric_card("Metering Charge",     f"${cur['metering_charge']:.2f} / mo",     COLORS["metering"]),
        make_metric_card("Distribution Rate",   f"{cur['distribution_cents_kwh']:.5f} ¢/kWh", COLORS["distribution"]),
        make_metric_card("Transmission (TCRF)", f"{cur['transmission_cents_kwh']:.5f} ¢/kWh", COLORS["transmission"]),
    ], className="mb-4 g-3")

    table = dash_table.DataTable(
        id="rate-table",
        data=df[[
            "month", "customer_charge", "metering_charge",
            "distribution_cents_kwh", "transmission_cents_kwh",
            "total_fixed_monthly", "total_variable_cents"
        ]].to_dict("records"),
        columns=[
            {"name": "Month",                      "id": "month"},
            {"name": "Customer ($/mo)",            "id": "customer_charge",        "type": "numeric", "format": {"specifier": ".2f"}},
            {"name": "Metering ($/mo)",            "id": "metering_charge",        "type": "numeric", "format": {"specifier": ".2f"}},
            {"name": "Distribution (¢/kWh)",       "id": "distribution_cents_kwh", "type": "numeric", "format": {"specifier": ".5f"}},
            {"name": "Transmission (¢/kWh)",       "id": "transmission_cents_kwh", "type": "numeric", "format": {"specifier": ".5f"}},
            {"name": "Total Fixed ($/mo)",         "id": "total_fixed_monthly",    "type": "numeric", "format": {"specifier": ".2f"}},
            {"name": "Total Variable (¢/kWh)",     "id": "total_variable_cents",   "type": "numeric", "format": {"specifier": ".5f"}},
        ],
        style_header={
            "backgroundColor": "#2a2a3e",
            "color": "#e0e0ff",
            "fontWeight": "bold",
            "border": "1px solid #444",
        },
        style_data={
            "backgroundColor": COLORS["bg"],
            "color": "#ccc",
            "border": "1px solid #333",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#242436"},
            {"if": {"row_index": len(df) - 1}, "backgroundColor": "#2a3a2a", "color": "#fff"},
        ],
        style_cell={"textAlign": "center", "padding": "8px"},
        page_size=12,
    )

    return html.Div(
        style={"backgroundColor": COLORS["bg"], "minHeight": "100vh", "padding": "20px"},
        children=[
            # Header
            html.Div([
                html.H2("Oncor TDU Residential Rate Dashboard",
                        style={"color": COLORS["text"], "textAlign": "center", "marginBottom": "4px"}),
                html.P(f"ERCOT Market · Texas · Rolling 12 Months ({date_range})",
                       style={"color": COLORS["muted"], "textAlign": "center", "marginBottom": "4px"}),
                html.P(f"Residential customers only · Rates sourced from Oncor & PUCT",
                       style={"color": COLORS["muted"], "textAlign": "center", "fontSize": "0.8rem"}),
            ], className="mb-4"),

            dbc.Container([
                # Metric cards
                cards,

                # Variable charges chart
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=make_variable_chart(df), config={"displayModeBar": False}), width=12),
                ], className="mb-4"),

                # Fixed charges chart
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=make_fixed_chart(df), config={"displayModeBar": False}), width=12),
                ], className="mb-4"),

                # Data table
                html.H5("Monthly Rate Detail", style={"color": COLORS["text"], "marginBottom": "12px"}),
                table,

                # Refresh button
                dbc.Row([
                    dbc.Col(
                        dbc.Button("Refresh Data from Oncor / PUCT", id="refresh-btn", color="primary",
                                   outline=True, className="mt-4"),
                        width="auto",
                    ),
                    dbc.Col(
                        html.P(id="refresh-status", className="mt-4",
                               style={"color": COLORS["muted"], "fontSize": "0.85rem"}),
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
# Callback: Refresh button
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
# Initial load
# ---------------------------------------------------------------------------

df = load_data()
app.layout = build_layout(df)


if __name__ == "__main__":
    print("Starting Oncor TDU Dashboard at http://localhost:8050")
    app.run(debug=False, port=8050)
