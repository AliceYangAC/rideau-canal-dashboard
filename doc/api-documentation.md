# API Endpoints

The dashboard exposes endpoints via the underlying **Flask server** (through Dash). These are primarily used internally by Dash components, but can also be queried directly with `curl`.

| Endpoint                           | Method                  | Description                                                   | Example Request               | Example Response              |
| ---------------------------------- | ----------------------- | ------------------------------------------------------------- | ----------------------------- | ----------------------------- |
| `/`                                | GET                     | Main dashboard UI                                             | `curl http://localhost:8050/` | HTML page with dashboard      |
| `/location-cards`                  | GET (via Dash callback) | Returns latest status cards for each location                 | Triggered internally by Dash  | JSON array of card components |
| `/ice-thickness-trend-chart`       | GET (via Dash callback) | Returns line chart of average ice thickness (last hour)       | Triggered internally by Dash  | Plotly JSON figure            |
| `/surface-temperature-trend-chart` | GET (via Dash callback) | Returns line chart of average surface temperature (last hour) | Triggered internally by Dash  | Plotly JSON figure            |
| `/system-status`                   | GET (via Dash callback) | Returns overall skating condition status                      | Triggered internally by Dash  | `"SAFE"`                      |