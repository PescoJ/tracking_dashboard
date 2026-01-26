# Inport necessary libraries
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import altair as alt
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Markdown('''
        #### Tracking Dashboard
    ''')
    ])

if __name__ == "__main__":
    app.run_server(debug=True)