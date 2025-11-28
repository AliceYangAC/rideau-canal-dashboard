from zoneinfo import ZoneInfo
import json
import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from dotenv import load_dotenv
import plotly.express as px
import datetime
import pandas as pd
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient

# Real-time data display (3 location cards)
# Safety status badges
# Auto-refresh (every 30 seconds)
# Historical trend charts (last hour)
# Overall system status

# Load environment variables
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

locations = ["Dow's Lake", "Fifth Avenue", "NAC"]

# ---------------------------------------------
# Azure Cosmos DB Setup & Blob Storage Setup
# ---------------------------------------------

COSMOS_URL = os.getenv("COSMOS_CONN_STR")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "RideauCanalDB"
CONTAINER_NAME = "SensorAggregations"

BLOB_CONN_STR = os.getenv("BLOB_CONN_STR")
BLOB_CONTAINER = "historical-data"

# Helper functions to get Cosmos DB and Blob Storage clients
def get_cosmos_container():
    client = CosmosClient(COSMOS_URL, COSMOS_KEY)
    db = client.get_database_client(DATABASE_NAME)
    return db.get_container_client(CONTAINER_NAME)

def get_blob_container():
    service = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
    return service.get_container_client(BLOB_CONTAINER)

# ---------------------------------------------
# Data Retrieval Functions
# ---------------------------------------------

# Function to get latest aggregated status for a location from Cosmos DB
def get_latest_status(location: str, minutes: int = 60):
    container = get_cosmos_container()
    now = datetime.datetime.now(datetime.timezone.utc)
    start_time, end_time = (
        (now - datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        now.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    query = """
        SELECT TOP 1
            c.id,
            c.location,
            c.timestamp,
            c.avg_ice_thickness,
            c.min_ice_thickness,
            c.max_ice_thickness,
            c.avg_surface_temperature,
            c.min_surface_temperature,
            c.max_surface_temperature,
            c.max_snow_accumulation,
            c.avg_external_temperature,
            c.reading_count
        FROM c
        WHERE c.location = @location
          AND c.timestamp >= @startTime
          AND c.timestamp <= @endTime
        ORDER BY c.timestamp DESC
    """
    params = [
        {"name": "@location", "value": location},
        {"name": "@startTime", "value": start_time},
        {"name": "@endTime", "value": end_time}
    ]
    items = list(container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True
    ))
    return items[0] if items else None

# Function to get historical data from Blob Storage for the last hour
def get_historical_data(last_minutes=60):
    blob_container = get_blob_container()
    now = datetime.datetime.now(datetime.timezone.utc)
    prefix = f"aggregations/{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}/"
    blobs = blob_container.list_blobs(name_starts_with=prefix)

    records = []
    for blob in blobs:
        try:
            blob_client = blob_container.get_blob_client(blob.name)
            data = blob_client.download_blob().readall().decode("utf-8")
            for line in data.splitlines():
                if line.strip(): 
                    records.append(json.loads(line))
        except Exception as e:
            print(f"Error reading {blob.name}: {e}")
            continue

    return pd.DataFrame(records) if records else pd.DataFrame()

# ---------------------------------------------
# Dash App Setup
# ---------------------------------------------

# Initialize Dash app
app = dash.Dash(__name__)

# Expose Flask server for deployment
server = app.server 

# Used AI to enhance the dashboard's visual design and user experience in the assets/style.css file.
app.layout = html.Div(
    className="app-container",
    children=[
        dcc.Interval(id="interval", interval=30*1000, n_intervals=0),
        dcc.Interval(id="countdown-interval", interval=1000, n_intervals=0),

        html.H1("Rideau Canal Dashboard", className="dashboard-title"),

        html.Div(id="countdown-display", className="countdown-display"),

        html.Div(id="location-cards", className="location-cards"),

        html.Div(id="system-status", className="system-status"),

        html.Div(
            className="trend-charts",
            children=[
                dcc.Graph(id="ice-thickness-trend-chart", className="trend-graph"),
                dcc.Graph(id="surface-temperature-trend-chart", className="trend-graph")
            ]
        ),
    ]
)

# Callback to update dashboard components described above
@app.callback(
    [Output("location-cards", "children"),
     Output("ice-thickness-trend-chart", "figure"),
     Output("surface-temperature-trend-chart", "figure"),
     Output("system-status", "children")],
    [Input("interval", "n_intervals")]
)
def update_dashboard(n):
    # Real-time data display (3 location cards)
    cards = []
    statuses = []
    for loc in locations:
        metrics = get_latest_status(loc)
        if metrics:
            # Safety status badges
            # Safe: Ice ≥ 30cm AND Surface Temp ≤ -2°C
            # Caution: Ice ≥ 25cm AND Surface Temp ≤ 0°C
            # Unsafe: All other conditions

            safe = metrics["avg_ice_thickness"] and metrics["avg_ice_thickness"] > 30 \
                   and metrics["avg_surface_temperature"] and metrics["avg_surface_temperature"] < -2
            caution = metrics["avg_ice_thickness"] and metrics["avg_ice_thickness"] >= 25 \
                      and metrics["avg_surface_temperature"] and metrics["avg_surface_temperature"] <= 0
            if safe:
                status = "Safe"
            elif caution:
                status = "Caution"
            else:
                status = "Unsafe"
            statuses.append(status)
            if status == "Safe":
                badge_color = "green"
            elif status == "Caution":
                badge_color = "orange"
            else:
                badge_color = "red"


            ts = metrics.get("timestamp")
            if ts:
                # Parse ISO string into UTC datetime
                dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))

                # Convert to Ottawa's timezone
                dt_cst = dt.astimezone(ZoneInfo("America/Toronto"))

                # Format as yyyy-MM-DD hh:mm:ss AM/PM
                formatted_ts = dt_cst.strftime("%Y-%m-%d %I:%M:%S %p")
            else:
                formatted_ts = "N/A"

            # Display cards for each location
            cards.append(
                html.Div(
                    [
                        html.H3(loc, className="card-title"),
                        html.H4(f"Last Update: {formatted_ts}", className="card-timestamp"),
                        html.Span(status, className="status-badge", style={"backgroundColor": badge_color}),
                        html.Ul([
                            html.Li(f"Avg Ice Thickness: {metrics['avg_ice_thickness']:.2f} cm"),
                            html.Li(f"Min/Max Ice Thickness: {metrics['min_ice_thickness']:.2f} / {metrics['max_ice_thickness']:.2f} cm"),
                            html.Li(f"Avg Surface Temp: {metrics['avg_surface_temperature']:.2f} °C"),
                            html.Li(f"Min/Max Surface Temp: {metrics['min_surface_temperature']:.2f} / {metrics['max_surface_temperature']:.2f} °C"),
                            html.Li(f"Max Snow Accumulation: {metrics['max_snow_accumulation']:.2f} cm"),
                            html.Li(f"Avg External Temp: {metrics['avg_external_temperature']:.2f} °C"),
                            html.Li(f"Readings: {metrics['reading_count']}")
                        ], className="card-list")
                    ],
                    className="lofi-card"
                )
            )
        else:
            cards.append(html.Div([html.H3(loc), html.Span("No Data")]))
    
    # Historical trend charts for ice thickness (last hour)
    ice_thickness_df = get_historical_data()
    if not ice_thickness_df.empty:
        ice_thickness_df = ice_thickness_df.rename(columns={"timestamp": "Timestamp", "location": "Location"})
        ice_thickness_fig = px.line(ice_thickness_df, x="Timestamp", y="avg_ice_thickness", color="Location",
                                    color_discrete_sequence=["#B6D032", "#349CBC", "#e62828"],
              title="Avg. Ice Thickness Trends (last hour)")
    else:
        ice_thickness_fig = px.line(title="No historical data available")
        
    # Historical trend charts for surface temperature (last hour)
    surface_temperature_df = get_historical_data()
    if not surface_temperature_df.empty:
        surface_temperature_df = surface_temperature_df.rename(columns={"timestamp": "Timestamp", "location": "Location"})
        surface_temperature_fig = px.line(surface_temperature_df, x="Timestamp", y="avg_surface_temperature", color="Location",
                color_discrete_sequence=["#B6D032", "#349CBC", "#e62828"],
              title="Avg. Surface Temperature Trends (last hour)")
    else:
        surface_temperature_fig = px.line(title="No historical data available")

    # Collect unsafe/caution locations
    problem_locs = [loc for loc, s in zip(locations, statuses) if s in ("Unsafe", "Caution")]

    if statuses and all(s == "Safe" for s in statuses):
        overall = "SAFE"
    else:
        if problem_locs:
            overall = html.Div([
                html.Div("UNSAFE SKATING LOCATION(S):"),
                html.Div(", ".join(problem_locs))
            ])
        else:
            overall = "UNSAFE SKATING CONDITIONS"


    return cards, ice_thickness_fig, surface_temperature_fig, overall

# Callback to update countdown display
@app.callback(
    Output("countdown-display", "children"),
    [Input("countdown-interval", "n_intervals"),
     Input("interval", "n_intervals")]
)
def update_countdown(countdown_ticks, refresh_ticks):
    # Each refresh resets the countdown
    seconds_since_refresh = countdown_ticks % 30
    remaining = 30 - seconds_since_refresh
    return f"Next refresh in {remaining} seconds"

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv("PORT", 8050)), host='0.0.0.0')
