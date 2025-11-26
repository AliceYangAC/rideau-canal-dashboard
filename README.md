# Rideau Canal Skateway - Dashboard

The Rideau Canal Dashboard provides real‑time monitoring of skating conditions across three canal locations, with auto‑refreshing location cards, color‑coded safety badges, and system‑wide status updates. It also includes countdown timers for refresh cycles and interactive Plotly trend charts showing ice thickness and surface temperature over the past hour, combining live insights with historical context in a clean UI powered by the native integrations in the Dash (Plotly) framework.

## Technologies Used

- **Dash (Plotly)**: framework for building interactive web dashboards.  
- **Plotly**: generates line charts for historical trends.  
- **Flask (via Dash)**: provides the underlying web server (`server = app.server`).  
- **Azure Cosmos DB SDK**: queries latest aggregated sensor data.  
- **Azure Blob Storage SDK**: retrieves historical JSON records for trend analysis.  
- **Python Standard Libraries**:  
  - `datetime`, `zoneinfo` for time handling and timezone conversion.  
  - `os`, `json` for environment and data parsing.  
- **dotenv**: loads environment variables securely from `.env`.  
- **pandas**: structures historical data into DataFrames for plotting.

## Setup (Local)

### Prerequisites

- ‼️‼️ Ensure you go to [sensor simulation repo](https://github.com/aliceyangac/rideau-canal-sensor-simulation) and follow all the setup there first. **The dashboard can only work with the simulated data pipeline up and running!** ‼️‼️
- **Python 3.13+**
- **pip** for dependency management

### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/aliceyangac/rideau-canal-dashboard.git
cd rideau-canal-dashboard
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` as `.env` and replace the placeholder values with your Azure Cosmos DB and Blob Storage variables:
   ```env
   COSMOS_CONN_STR=your-cosmos-connection-string
   COSMOS_KEY=your-cosmos-key
   BLOB_CONN_STR=your-blob-connection-string
   PORT=8050
   ```
2. In Cosmos DB portal, navigate to **Settings -> Keys** and copy paste the URI into `COSMOS_CONN_STR` and the key into `COSMOS_KEY`.
3. In Storage Account portal, navigate to **Security + networking -> Access keys** and copy paste the connection string of `key1` into `BLOB_CONN_STR`.

### API Endpoints
The dashboard exposes endpoints via the underlying **Flask server** (through Dash). These are primarily used internally by Dash components, but can also be queried directly.

| Endpoint                           | Method                  | Description                                                   | Example Request               | Example Response              |
| ---------------------------------- | ----------------------- | ------------------------------------------------------------- | ----------------------------- | ----------------------------- |
| `/`                                | GET                     | Main dashboard UI                                             | `curl http://localhost:8050/` | HTML page with dashboard      |
| `/location-cards`                  | GET (via Dash callback) | Returns latest status cards for each location                 | Triggered internally by Dash  | JSON array of card components |
| `/ice-thickness-trend-chart`       | GET (via Dash callback) | Returns line chart of average ice thickness (last hour)       | Triggered internally by Dash  | Plotly JSON figure            |
| `/surface-temperature-trend-chart` | GET (via Dash callback) | Returns line chart of average surface temperature (last hour) | Triggered internally by Dash  | Plotly JSON figure            |
| `/system-status`                   | GET (via Dash callback) | Returns overall skating condition status                      | Triggered internally by Dash  | `"SAFE"`                      |

## Setup (Vercel)

### Prerequisite

- Fork the Github [dashboard repo](https://github.com/aliceyangac/rideau-canal-dashboard) to your own account.

### Deploy Web App

1. Create a Vercel account or login.
2. **Add New... -> Project**
3. **Import Git Repository -> Find `rideau-canal-dashboard` in the list -> Import**
4. **Framework Preset -> Flask**
5. **Environment Variables -> Import .env**
6. **Deploy**

### Configuration (Vercel)

If not handled in step 5 of "Deploy Web App":

1. Click your project, likely named `rideau-canal-dashboard`
2. **Settings -> Environment Variables -> Import.env -> Save**

## Dashboard Features  

- **Real‑time Updates**  
  - The dashboard auto‑refreshes every 30 seconds, pulling the latest aggregated sensor data from Cosmos DB.  
  - A countdown timer shows when the next refresh will occur, ensuring users know they’re seeing up‑to‑date skating conditions.  

- **Charts and Visualizations**  
  - Interactive line charts display **average ice thickness** and **average surface temperature** trends over the past hour.  
  - Data is sourced from Blob Storage and plotted with Plotly Express, color‑coded by location (Dow’s Lake, Fifth Avenue, NAC).  
  - Historical context complements real‑time readings for better decision‑making based on historical trends.

- **Safety Status Indicators**  
  - Each location card includes a **color‑coded badge** (green = Safe, orange = Caution, red = Unsafe).  
  - Status is determined by thresholds:  
    - **Safe** → Ice ≥ 30 cm and Surface Temp ≤ –2 °C  
    - **Caution** → Ice ≥ 25 cm and Surface Temp ≤ 0 °C  
    - **Unsafe** → All other conditions  
  - An overall system status summarizes skating conditions across all locations; if any location is not safe, it is declared overall unsafe.

## Troubleshooting

### 1. The dashboard won’t start locally.
- **Cause:** Missing dependencies or virtual environment not activated.  
- **Fix:**  
  ```bash
  source venv/bin/activate   # or venv\Scripts\activate on Windows
  pip install -r requirements.txt
  python app.py
  ```

### 2. I get `KeyError` or `NoneType` errors when querying Cosmos DB.
- **Cause:** Environment variables not set or incorrect connection strings.  
- **Fix:**  
  - Ensure `.env` file exists in the project root.  
  - Verify values for `COSMOS_CONN_STR`, `COSMOS_KEY`, and `BLOB_CONN_STR`.  
  - Confirm Cosmos DB container name is `SensorAggregations` and partition key is `/location`.

### 3. No data appears on the dashboard.
- **Cause:** Sensor simulation not running or Stream Analytics job not configured.  
- **Fix:**  
  - Setup and start the [sensor simulation](https://github.com/aliceyangac/rideau-canal-sensor-simulation).  
  - Verify Stream Analytics job is running and outputs are connected to Cosmos DB and Blob Storage.  
  - Check that the Blob Storage container is named `historical-data` and Cosmos DB container is named `SensorAggregations`.

### 4. Charts show “No historical data available.”
- **Cause:** Blob Storage prefix mismatch or empty data files.  
- **Fix:**  
  - Ensure you configured the Blob Storage container `historical-data` with **Path Pattern** `aggregations/{date}/{time}`
  - Check that blobs contain newline‑delimited JSON records.

### 5. Dashboard loads but shows “Internal Server Error” on Vercel.
- **Cause:** Environment variables not configured in Vercel.  
- **Fix:**  
  - In Vercel dashboard → Project Settings → Environment Variables, add:  
    - `COSMOS_CONN_STR`  
    - `COSMOS_KEY`  
    - `BLOB_CONN_STR`  
  - Redeploy after saving.

### 6. Blob Storage data not rendering on charts.
- **Cause:** Not enough time has passed, JSON parsing errors or malformed blob content.  
- **Fix:**  
  - Make sure you waited for at least 2 tumbling windows, aka 10 minutes; you cannot form a line with just 1 data point.
  - Verify Stream Analytics writes valid JSON lines as ouput to Blob.  
  - Check Logs for `Error reading blob` messages.  
  - Manually inspect blob content in Azure Storage Account portal.
