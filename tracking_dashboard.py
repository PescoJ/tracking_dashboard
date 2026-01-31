# Inport necessary libraries
import time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import altair as alt
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
# Setting the file path and refresh interval
# Setting the file paths
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "NYC_Synthetic_January_Tracking.xlsx"

ASSETS_DIR = BASE_DIR / "assets"
LOGO_FILE = ASSETS_DIR / "logo.PNG"
# Set refresh interval in milliseconds
refresh_interval = 30_000 #Seconds
# Initialize the Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# Load data and show and error if file not found
last_updated = "Unknown"
if DATA_FILE.exists():
    mtime = time.ctime(DATA_FILE.stat().st_mtime)
    last_updated = pd.Timestamp(mtime).strftime("%Y-%m-%d %H:%M")
else:
    last_updated = f"File not found: {DATA_FILE}"
# Define the layout of the app
app.layout = dbc.Container(
    [
        html.Div(
            [
                html.Img(
                    src = app.get_asset_url(LOGO_FILE.name), 
                    style={'width':'100px', 'height':'auto'}
                    ),
            ],
        ),
        dcc.Markdown(f"""
            #### Tracking Dashboard
            **Version:** 0.0.1
            **Last Updated:** {last_updated},
    """
        ),
        dcc.Interval(
            id='interval-component',
            interval=refresh_interval,  # in milliseconds
            n_intervals=0
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id='tracking-graph'),
                    width=12
                )
            ]
        )
    ], 
    fluid=True,
)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)