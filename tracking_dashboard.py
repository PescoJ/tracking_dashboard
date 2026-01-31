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
LOGO_FILE = BASE_DIR / "assets" / "logo.PNG"
refresh_interval = 30_000 #Seconds
# Initialize the Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# Define the layout of the app
app.layout = html.Div([
    html.Img(src = app.get_asset_url('logo.PNG'), style={'width':'100px', 'height':'auto'}),
    dcc.Markdown(f'''
        #### Tracking Dashboard
                 ## Version 0.0.1
                 # Last Updated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")},
    ''')
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)