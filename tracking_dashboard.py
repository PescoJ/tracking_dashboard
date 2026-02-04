# Inport necessary libraries
import time
from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import altair as alt
from dash import Dash, dcc, html, Input, Output, State, no_update
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
external_stylesheets = [dbc.themes.BOOTSTRAP,
                        "https://use.fontawesome.com/releases/v6.4.2/css/all.css",
]
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
# Load data and show and error if file not found
last_updated = "Unknown"
if DATA_FILE.exists():
    mtime = time.ctime(DATA_FILE.stat().st_mtime)
    last_updated = pd.Timestamp(mtime).strftime("%Y-%m-%d %H:%M")
else:
    last_updated = f"File not found: {DATA_FILE}"
df.columns = df.columns.str.strip()
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
def parse_mgrs_like_xy(s):
    if pd.isna(s):
        return (None, None)
    text = str(s)
    nums = re.findall(r"\b(\d{4,6})\b", text)
    if len(nums) >= 2:
        x = int(nums[0])
        y = int(nums[1])
        return (x, y)
    # Alternative pattern
    nums2 = re.findall(r"\d{8,12}", text)
    if nums2:
        token = nums2[-1]
        if len(token) >= 10:
            tail = token [-10:]
            x = int(tail[:5])
            y = int(tail[5:])
        return (x, y)
    return (None, None)
# Build Long Location DataFrame
def build_long_location_df(df_people):
    day_cols = [c for c in df_people.columns if c.lower().startswith("location_")]
    if not day_cols:
        raise ValueError(f"No location columns found. Columns: {df_people.columns.tolist()}")
    
    id_col = "ID Number"
    crime_col = "Crime Tendency"
    terror_col = "Terror Tendency"

    long_df = df_people.melt(
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
# Build the long format DataFrame for locations
long_df = build_long_location_df(df)
# Precompute global min and max for x and y
xmin, xmax = long_df["x"].quantile([0.01, 0.99]).tolist()
ymin, ymax = long_df["y"].quantile([0.01, 0.99]).tolist()
# Heat Map of People
def make_heatmap(filtered_long_df, xmin, xmax, ymin, ymax, nbins=75):
    fig = go.Figure(
        data=go.Histogram2d(
            x=filtered_long_df["x"].astype(float),
            y=filtered_long_df["y"].astype(float),
            nbinsx=nbins,
            nbinsy=nbins,
        )
    )
    fig.update_layout(
        title = "Movement Density (Noon Locations)",
        height = 650,
        margin=dict(l=40, r=20, t=60, b=40),
        xaxis=dict(title="Eastrange (40000m to 50000m)", range=[xmin, xmax], type="linear"),
        yaxis=dict(title="Northrange (50000m to 65000m)", range=[ymin, ymax], type="linear"),
    )
    return fig
# Callbacks for interactive components
@app.callback(
    Output("day-state", "data"),
    Input("day-slider", "value"),
    State("day-mode", "value"),
    State("day-state", "data"),
    prevent_initial_call=True,
)
# Store day value based on mode
def remember_day_value(day_value, day_mode, data):
    data = data or {"single": 1, "range": [1, 31]}
    if day_mode == "single":
        try:
            data["single"] = int(day_value)
        except Exception:
            pass
    else:
        if isinstance(day_value, (list, tuple)) and len(day_value) == 2:
            data["range"] = [int(day_value[0]), int(day_value[1])]
    return data
# Adjust day slider based on mode
@app.callback(
    Output("day-slider-container", "children"),
    Input("day-mode", "value"),
    State("day-state", "data")
)
def render_day_slider(day_mode, data):
    data = data or {"single": 1, "range": [1, 31]}
    single_day = int(data.get("single", 1))
    day_range = data.get("range", [1, 31])

    if day_mode == "single":
        return dcc.Slider(
            id="day-slider",
            min=1, max=31, step=1,
            value=single_day,
            marks={1: "1", 8: "8", 15: "15", 22: "22", 31: "31"},
            tooltip={"placement":"bottom", "always_visible":False},
        )
    if not (isinstance(day_range, (list, tuple)) and len(day_range) == 2):
        day_range = [1, 31]

    return dcc.RangeSlider(
        id="day-slider",
        min=1, max=31, step=1,
        value=[int(day_range[0]), int(day_range[1])],
        marks={1: "1", 8: "8", 15: "15", 22: "22", 31: "31"},
        tooltip={"placement":"bottom", "always_visible":False},
    )
# Callback to update the heatmap based on filters and day mode
@app.callback(
    Output("movement-heatmap", "figure"),
    Output("point-count", "children"),
    Input("crime-range-slider", "value"),
    Input("terror-range-slider", "value"),
    Input("day-slider", "value"),
)
def update_heatmap(crime_range, terror_range, day_value):
    try:
        cmin, cmax = crime_range
        tmin, tmax = terror_range

        crime_col = "Crime Tendency"
        terror_col = "Terror Tendency"

        if isinstance(day_value, (list, tuple)) and len(day_value) == 2:
            day_min, day_max = map(int, day_value)
            day_mask = long_df["day"].between(day_min, day_max)
            day_label = f"Days: {day_min}-{day_max}"
        else:
            d = int(day_value)
            day_mask = (long_df["day"] == d)
            day_label = f"Day: {d}"

        filtered = long_df[
            (long_df[crime_col].between(cmin, cmax)) &
            (long_df[terror_col].between(tmin, tmax)) &
            day_mask
        ].copy()

        filtered["x"] = pd.to_numeric(filtered["x"], errors='coerce')
        filtered["y"] = pd.to_numeric(filtered["y"], errors='coerce')
        filtered = filtered.dropna(subset=["x", "y"])

        count_text = f"Points shown {len(filtered)} | {day_label}"

        if filtered.empty:
            fig = px.scatter(title="No data available for the selected filters.")
            fig.update_layout(
                height=650,
                xaxis=dict(range=[xmin, xmax]),
                yaxis=dict(range=[ymin, ymax]),              
                margin=dict(l=40, r=20, t=60, b=40),
            )
            return fig, count_text
        
        fig = make_heatmap(filtered, xmin, xmax, ymin, ymax, nbins=75)
        fig.update_layout(height=650)
        return fig, count_text
    
    except Exception as e:
        fig = px.scatter(title=f"Heatmap error: {type(e).__name__}: {e}")
        fig.update_layout(
            height=650,
            margin=dict(l=40, r=20, t=60, b=40))
        return fig, count_text
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
            **Version:** 0.1.2
            **Last Updated:** {last_updated},"""
        ),
        dcc.Interval(
            id='interval-component',
            interval=refresh_interval,  # in milliseconds
            n_intervals=0
        ),
        dbc.Tabs(
            id="main-tabs",
            active_tab="tab-distribution",
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
                                            marks={1: "1", 25: "25", 50: "50", 75: "75", 100: "100"},
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
                                            marks={1: "1", 25: "25", 50: "50", 75: "75", 100: "100"},
                                            tooltip={"placement":"bottom", "always_visible":False},
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                    dcc.Store(id="day-state", data={"single": 1, "range": [1, 31]}),
                                    html.Div("Day Selector"),
                                    html.Div(
                                        id="day-slider-container",
                                        children=dcc.RangeSlider(
                                            id="day-slider",
                                            min=1, max=31, step=1,
                                            value=[1, 31],
                                            marks={1: "1", 8: "8", 15: "15", 22: "22", 31: "31"},
                                            tooltip={"placement":"bottom", "always_visible":False},
                                        )
                                    ),
                                    html.Div("Mode", style={"marginTop": "10px"}),
                                    dcc.RadioItems(
                                        id="day-mode",
                                        options=[
                                            {"label": "Single Day", "value": "single"},
                                            {"label": "Cumulative Range", "value": "range"},
                                        ],
                                        value="range",
                                        inline=True,
                                        inputStyle={"marginRight": "6px", "marginLeft": "12px"},
                                        ),
                                        html.Div(id="point-count", style={"fontWeight": "600", "marginTop": "8px"}),
                                    ],
                                    md=4
                                ),
                            ],
                            className="mb-3",
                        ),
                        dcc.Graph(id="movement-heatmap", style={"height": "650px"}),
                    ],
                ),
            ],
        ),
    ],
    fluid=True
)    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)