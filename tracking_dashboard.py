# Inport necessary libraries
import time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from pexpect import EOF
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
# Defining a function to create histogram
def crime_terror_histogram(df):
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=df["Crime_Tendency"],
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
            x=df["Terror_Tendency"],
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
            value="primary-tab",
            children=[
                dbc.Tab(
                    label="Total Distribution", 
                    value="tab-distribution",
                    children=[
                        dcc.Graph(
                            id="crime-terror-histogram",
                            figure=crime_terror_histogram(df),
                        )
                    ],
                ),
                dbc.Tab(
                    label="Patterns in Crime and Terror",
                    value="tab-patterns",
                    children=[html.Div("Patterns in Crime and Terror Content")],
                ),
                dbc.Tab(
                    label="Geographical Analysis",
                    value="tab-geographical",
                    children=[html.Div("Geographical Analysis Content")],
                ),
            ],

        ),
    ],
)
fluid=True,
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)