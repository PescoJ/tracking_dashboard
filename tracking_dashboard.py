# Inport necessary libraries
import time
from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import altair as alt
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
# Setting the file path and refresh interval
# Setting the file paths
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "NYC_Synthetic_January_Tracking.xlsx"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_FILE = "logo.PNG"

df = pd.read_excel(DATA_FILE, sheet_name="January_Tracking")
# Set refresh interval in milliseconds
refresh_interval = 30_000 #Seconds
# Initialize the Dash app with External Stylesheets theme
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://use.fontawesome.com/releases/v6.4.2/css/all.css",
]
app = Dash(__name__, external_stylesheets=external_stylesheets)
# Load data and show and error if file not found
last_updated = "Unknown"
if DATA_FILE.exists():
    mtime = time.ctime(DATA_FILE.stat().st_mtime)
    last_updated = pd.Timestamp(mtime).strftime("%Y-%m-%d %H:%M")
else:
    last_updated = f"File not found: {DATA_FILE}"
## Defining the functions needed for visualizations
# Crime and Terror Histogram
def crime_terror_histogram(df):
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=df["Crime Tendency"],
            name='Crime Tendency',
               xbins=dict(start=0, 
                        end=100,                            
                        size=10
                        ),
                    opacity=0.75,
                )
            )
    fig.add_trace(
        go.Histogram(
            x=df["Terror Tendency"],
            name='Terror Tendency',
            xbins=dict(start=0, 
                    end=100, 
                    size=10
                    ),
            opacity=0.75,
        )
    )
    fig.update_layout(
        title='Distribution of Crime and Terror Tendencies',
        xaxis_title='Tendency Score',
                yaxis_title='Number of People',
                barmode='group',
                xaxis=dict(
                    tickmode='linear', 
                    dtick=10
                        ),
                legend_title_text='Tendency Type',
                margin=dict(l=40, r=20, t=60, b=40),
            )
    return fig
# Crime vs Terror Scatter Plot
def crime_vs_terror_scatter(df):
    x_col = "Crime Tendency"
    y_col = "Terror Tendency"
    id_col = "ID Number"

    plot_df = df.copy()
    plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors='coerce')
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors='coerce')
    
    fig = px.scatter(
        plot_df,
        x = x_col,
        y = y_col,
        hover_name = id_col,
        hover_data = {x_col: True, y_col: True, id_col: True},
        title="Crime vs Terror Tendency by Person",
    )
    fig.update_layout(
        xaxis_title="Crime Tendency Score",
        yaxis_title="Terror Tendency Score",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig
# MGRS-like Coordinate Parser
def parse_mgrs_like_xy(s: str):
    if pd.isna(s):
        return (None, None)
    nums = re.findall(r"\d+", str(s))
    if len(nums) < 2:
        return (None, None)
    x = int(nums[-2])
    y = int(nums[-1])
    return (x, y)
# Build Long Location DataFrame
def build_long_location_df(df_people):
    day_cols = [c for c in df_people.columns if c.lower().startswith("Location_")]
    if not day_cols:
        raise ValueError("No location columns found in the dataframe.")
    
    id_col = "ID Number"
    crime_col = "Crime Tendency"
    terror_col = "Terror Tendency"

    long_df = long_df.melt(
        id_vars=[id_col, crime_col, terror_col],
        value_vars = day_cols,
        var_name = "day_col",
        value_name = "Location",
    )
    long_df["day"] = long_df["day_col"].str.extract(r"(\d+)").astype(int)

    xy = long_df["Location"].apply(parse_mgrs_like_xy)
    long_df["x"] = xy.apply(lambda t: t[0])
    long_df["y"] = xy.apply(lambda t: t[1])

    long_df = long_df.dropna(subset=["x", "y"]).copy()
    return long_df
# Heat Map of People
def make_heatmap(filtered_long_df, bin_size=5):
    fig = px.density_heatmap(
        filtered_long_df,
        x="x",
        y="y",
        nbinsx=max(5, int((filtered_long_df["x"].max() - filtered_long_df["x"].min()) / bin_size)),
        nbinsy=max(5, int((filtered_long_df["y"].max() - filtered_long_df["y"].min()) / bin_size)),
        title = "Movement Density (Noon Locations)",
    )
    fig.update_layout(
        xaxis_title="X Coordinate",
        yaxis_title="Y Coordinate",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig
@app.callback(
    Output("movement-heatmap", "figure"),
    Input("crime-range-slider", "value"),
    Input("terror-range-slider", "value"),
    Input("day-slider", "value"),
)
def update_heatmap(crime_range, terror_range, day_range):
    cmin, cmax = crime_range
    tmin, tmax = terror_range

    filtered = long_df[
        (long_df["Crime Tendency"].between(cmin, cmax)) &
        (long_df["Terror Tendency"].between(tmin, tmax)) &
        (long_df["day"].between(day_range[0], day_range[1]))
    ]

    if filtered.empty:
        fig = px.scatter(title="No data available for the selected filters.")
        fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))
        return fig
# Define the layout of the app
app.layout = dbc.Container(
    [
        # Logo
        dbc.Row(
            [
                dbc.Col(
                    html.Img(
                        src=app.get_asset_url(LOGO_FILE),
                        style={"height": "70px", "width": "auto"},
                            ),
                    width="auto",
                        )
            ],
            align="center",
            style={"marginTop": "12px"},
                ),
        # Banner buttons
        dbc.Row(
            [
                dbc.Col(
                    dbc.ButtonGroup(
                        [
                            dbc.DropdownMenu(
                                label="Manage Projects",
                                id="projects-dropdown",
                                color="primary",
                                className="border shadow-sm fw-semibold",
                                children=[
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-house me-2"), "Home"], id="project-home"),
                                    dbc.DropdownMenuItem(divider=True),
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-1 me-2"), "Project 1"], id="project-one"),
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-2 me-2"), "Project 2"], id="project-two"),
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-3 me-2"), "Project 3"], id="project-three"),
                                        ],
                                        ),
                            dbc.DropdownMenu(
                                label="Manage Tasks",
                                id="tasks-dropdown",
                                color="primary",
                                className="border shadow-sm fw-semibold",
                                children=[
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-table-columns me-2"), "Task Board"], id="manage-task-board"),
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-plus me-2"), "New Task"], id="manage-task-new"),
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-check me-2"), "Completed Tasks"], id="manage-task-completed"),
                                        ],
                                        ),
                            dbc.DropdownMenu(
                                label="Manage Users",
                                id="users-dropdown",
                                color="primary",
                                className="border shadow-sm fw-semibold",
                                children=[
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-user-shield me-2"), "Admins"], id="manage-admin"),
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-user-tie me-2"), "Managers"], id="manage-managers"),
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-user-group me-2"), "Leaders"], id="manage-leaders"),
                                    dbc.DropdownMenuItem([html.I(className="fa-solid fa-user me-2"), "Members"], id="manage-members"),
                                        ],
                                        ),
                        ],
                        className="w-100 gap-3",
                        size="lg",
                ),
                    width=12,
                    )
            ],
            style={
                "marginTop": "10px",
                "marginBottom": "16px",
                "padding": "12px",
                "borderRadius": "10px",
                "backgroundColor": "#f8f9fa",
            },
        ),
# Dashboard Title and Last Updated Info
        dcc.Markdown(f"""
            #### Tracking Dashboard
            **Version:** 0.0.1
            **Last Updated:** {last_updated},"""
        ),
        dcc.Interval(
            id='interval-component',
            interval=refresh_interval,  # in milliseconds
            n_intervals=0
        ),
        dbc.Tabs(
            id="main-tabs",
            active_tab="primary-tab",
            children=[
                dbc.Tab(
                    label="Total Distribution", 
                    tab_id="tab-distribution",
                    children=[
                        dcc.Graph(
                            id="crime-terror-histogram",
                            figure=crime_terror_histogram(df),
                        )
                    ],
                ),
                dbc.Tab(
                    label="Patterns in Crime and Terror",
                    tab_id="tab-patterns",
                    children=[
                        dcc.Graph(
                            id="crime-vs-terror-scatter",
                            figure=crime_vs_terror_scatter(df),
                        )
                    ],
                ),
                dbc.Tab(
                    label="Geographical Analysis",
                    tab_id="tab-geographical",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div("Crime Score Filter"),
                                        dcc.RangeSlider(
                                            id="crime-range-slider",
                                            min=1, max=100, step=1,
                                            value=[1, 100],
                                            tooltip={"placement":"bottom", "always_visible":False},
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        html.Div("Terror Score Filter"),
                                        dcc.RangeSlider(
                                            id="terror-range-slider",
                                            min=1, max=100, step=1,
                                            value=[1, 100],
                                            tooltip={"placement":"bottom", "always_visible":False},
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                    html.Div("Day Selector"),
                                    dcc.RangeSlider(
                                        id="day-slider",
                                        min=1, max=31, step=1,
                                        value=[1, 31],
                                        marks={1: "1", 8: "8", 15: "15", 22: "22", 31: "31"},
                                            ),
                                    ],
                                ),
                            ],
                            md=4,
                            ),
                        ],
                        className="mb-3",
                    ),
                        dcc.Graph(id="movement-heatmap"),
                    ],
                ),
            ],
        )
fluid=True,
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)