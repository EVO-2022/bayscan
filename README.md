# BayScan

**Smart Fishing Forecasts for Mobile Bay**

BayScan is a web application that predicts the best fishing times for your Mobile Bay dock using real-time tide and weather data from NOAA and NWS.

🌐 **Website:** [bayscan.app](https://bayscan.app)

## Features

- **Real-time Tide Data**: Current tide height, direction (incoming/outgoing), and upcoming high/low tides from NOAA
- **Weather Conditions**: Temperature, wind, barometric pressure trends, cloud cover, and forecast conditions
- **Species-Specific Forecasts**: Bite probability scores for 8 popular Gulf Coast species
- **Seasonal Running Models**: Knows when each species is present in Mobile Bay
- **2-Hour Window Forecasts**: 24-hour bite predictions broken into 2-hour windows
- **Smart Alerts**: Automatic notifications when conditions are hot for specific species
- **Fishing Log**: Quick-entry form to log catches with automatic conditions snapshot, recent catches table, and catch statistics
- **Mobile-Friendly Dashboard**: Clean, responsive web interface accessible from any device
- **Automatic Updates**: Fetches fresh data every 15 minutes

## Supported Species

- Speckled/Sea Trout
- Redfish (Red Drum)
- Flounder
- Sheepshead
- Mullet
- Mackerel
- Croaker
- Stingrays

## How It Works

The application combines multiple data sources and uses Gulf Coast fishing knowledge to predict bite times:

1. **Tide Analysis**: Fetches predictions from NOAA for Mobile State Docks station
2. **Weather Data**: Gets hourly forecasts from National Weather Service
3. **Astronomical Data**: Calculates sunrise, sunset, and moon phase
4. **Seasonal Modeling**: Each species has a monthly "running factor" (0-1) indicating presence
5. **Environmental Scoring**: Combines tide state, weather, time of day, and season into bite scores (0-100)
6. **Species Rules**: Each species has specific preferences:
   - Trout: Moving water, dawn/dusk, overcast, pre-front
   - Redfish: Moving water, less picky about conditions
   - Flounder: Falling tide, structure, stable pressure
   - Sheepshead: Slower currents around structure
   - And more...

## Installation

### Prerequisites

- Ubuntu server (18.04 or newer)
- Python 3.8 or higher
- Internet connection for API access

### Quick Setup

1. **Download or clone this project** to your server:
   ```bash
   cd /home/evo
   # If you have the folder, cd into it:
   cd fishing-forecast
   ```

2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```

   This will:
   - Install Python 3 and pip (if needed)
   - Create a Python virtual environment
   - Install all required dependencies

3. **Review configuration** (optional):
   ```bash
   nano config.yaml
   ```

   The default configuration is set for your Mobile Bay dock location. You can adjust:
   - Alert thresholds per species
   - Data refresh intervals
   - Optional email/Telegram alerts

### Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Install Python and pip
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

### Option 1: Run Directly (for testing)

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The application will start and be accessible at:
- From the server: `http://localhost:8080`
- From your phone (on same network): `http://YOUR_SERVER_IP:8080`

To find your server's IP address:
```bash
hostname -I
```

Press `Ctrl+C` to stop the server.

### Option 2: Run as a System Service (recommended for production)

This keeps the application running in the background and starts automatically on boot.

1. **Edit the service file** to match your username and paths:
   ```bash
   nano bayscan.service
   ```

   Update the `User` and `WorkingDirectory` if different from the default (`evo` and `/home/evo/fishing-forecast`).

2. **Install the service**:
   ```bash
   sudo cp bayscan.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable bayscan.service
   sudo systemctl start bayscan.service
   ```

3. **Check status**:
   ```bash
   sudo systemctl status bayscan.service
   ```

4. **View logs**:
   ```bash
   sudo journalctl -u bayscan.service -f
   ```

5. **Stop/restart the service**:
   ```bash
   sudo systemctl stop bayscan.service
   sudo systemctl restart bayscan.service
   ```

## Accessing BayScan

### Production Site
Visit: **[bayscan.app](https://bayscan.app)** for the hosted version

### Local Installation

#### From the Server
Open a web browser and go to: `http://localhost:8080`

#### From Your Phone (Same Network)

1. Find your server's IP address:
   ```bash
   hostname -I
   ```

2. On your phone's browser, go to: `http://YOUR_SERVER_IP:8080`
   - Example: `http://192.168.1.100:8080`

3. Bookmark it for easy access!

### From Outside Your Network (Advanced)

If you want to access the dashboard from anywhere:

**Option 1: SSH Tunnel (Secure, recommended for personal use)**
```bash
ssh -L 8080:localhost:8080 your_username@your_server_ip
```
Then access `http://localhost:8080` on your local device.

**Option 2: Port Forwarding (requires router access)**
- Configure your router to forward port 8080 to your server
- Access via your public IP address
- **Warning**: Ensure you understand the security implications

**Option 3: VPN (Most secure)**
- Set up a VPN to your home network
- Access as if you were on the local network

## Dashboard Overview

The dashboard has four main tabs:

### 1. Now Tab (Current Conditions)
- **Current Conditions**:
  - **Tide**: Current height, direction (rising/falling), next high/low times
  - **Weather**: Temperature, wind speed, pressure trend, conditions
  - **Bite Score**: Overall current fishing quality (0-100)
- **Species Forecast**: Current bite scores for all 8 species
- **Live Bay Currents Map**: Interactive Leaflet map showing current speeds and directions

### 2. 24hr Forecast Tab
- **Upcoming Windows**: 2-hour forecast windows for the next 24 hours
- Each window shows:
  - Overall bite score
  - Tide state, time of day, temperature, wind
  - Top 3 species to target
  - Best windows highlighted in green

### 3. Alerts Tab
- **Active Fishing Alerts**: Grouped by time window
- Shows species with hot bite conditions (score ≥ threshold)
- Alerts are automatically generated and dismissed based on forecasts

### 4. Fishing Log Tab (NEW!)
- **Quick Catch Entry**:
  - Large touch-friendly species buttons
  - Simple form with dock side, size, bait, method
  - Automatic conditions snapshot (tide, weather, etc.)
  - Log a catch in under 10 seconds
- **Recent Catches Table**:
  - View your logged catches
  - Filter by species
  - Shows time, species, location, size, bait, kept/released status
- **Statistics Summary**:
  - Total catches in last 30 days
  - Breakdown by species
  - Top baits and methods by success rate

## Configuration

### Location Settings

To use for a different location, edit `config.yaml`:

```yaml
location:
  name: "Your Location Name"
  latitude: YOUR_LATITUDE
  longitude: YOUR_LONGITUDE
  timezone: "America/Chicago"  # Change if needed
```

### Tide Station

Find the nearest NOAA tide station at: https://tidesandcurrents.noaa.gov/

Update in `config.yaml`:
```yaml
tide:
  station_id: "YOUR_STATION_ID"
  station_name: "Station Name"
```

### Alert Thresholds

Adjust when you receive alerts per species (0-100 scale):

```yaml
alerts:
  speckled_trout: 70  # Alert when trout bite score >= 70
  redfish: 65
  flounder: 60
  # etc...
```

### Data Refresh Interval

Change how often data is fetched:

```yaml
scheduler:
  fetch_interval_minutes: 15  # Default is 15 minutes
```

## API Endpoints

The application provides REST API endpoints if you want to build custom integrations:

- `GET /api/current` - Current conditions and species forecasts
- `GET /api/forecast?hours=24` - Upcoming forecast windows
- `GET /api/alerts` - Active fishing alerts
- `GET /api/tide` - Detailed tide information
- `GET /api/species/{species_key}` - Detailed forecast for one species
- `GET /api/health` - System health check

Example:
```bash
curl http://localhost:8080/api/current
```

### Fishing Log API Endpoints

**POST /api/catches** - Log a new catch
```bash
curl -X POST http://localhost:8080/api/catches \
  -H "Content-Type: application/json" \
  -d '{
    "species": "speckled_trout",
    "dock_side": "NE",
    "size_length_in": 16,
    "size_bucket": "keeper",
    "bait_type": "live shrimp",
    "method": "cork",
    "kept": true,
    "notes": "Caught on incoming tide"
  }'
```

**GET /api/catches** - Get recent catches
```bash
# Get last 50 catches
curl http://localhost:8080/api/catches

# Filter by species
curl http://localhost:8080/api/catches?species=redfish

# Limit results
curl http://localhost:8080/api/catches?limit=20
```

**GET /api/catches/stats** - Get catch statistics
```bash
# Stats for last 30 days
curl http://localhost:8080/api/catches/stats

# Stats for last 7 days
curl http://localhost:8080/api/catches/stats?days=7
```

## Troubleshooting

### Application won't start

1. **Check if port 8080 is already in use**:
   ```bash
   sudo lsof -i :8080
   ```

2. **Check logs**:
   ```bash
   sudo journalctl -u bayscan.service -n 50
   ```

3. **Test manually**:
   ```bash
   source venv/bin/activate
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

### No data showing on dashboard

1. **Check internet connection** - the app needs to reach NOAA and NWS APIs

2. **Wait a few minutes** - first data fetch happens on startup and may take 1-2 minutes

3. **Check logs** for API errors:
   ```bash
   sudo journalctl -u bayscan.service -f
   ```

4. **Verify NOAA stations are working**:
   - Tide Predictions: https://tidesandcurrents.noaa.gov/noaatidepredictions.html?id=8735180
   - Real-Time Conditions: https://tidesandcurrents.noaa.gov/stationhome.html?id=8736897

### Can't access from phone

1. **Verify server and phone are on the same WiFi network**

2. **Check firewall**:
   ```bash
   sudo ufw allow 8080
   ```

3. **Verify server IP**:
   ```bash
   hostname -I
   ```

4. **Test from server first**:
   ```bash
   curl http://localhost:8080
   ```

## Database

The application uses SQLite (file: `fishing_forecast.db`) to store:
- Tide predictions
- Weather forecasts
- Astronomical data
- Computed forecasts
- Active alerts

To reset the database:
```bash
rm fishing_forecast.db
# Restart the application
sudo systemctl restart bayscan.service
```

## Data Sources

- **Tide Predictions**: NOAA CO-OPS API (Bayou La Batre, Station 8735180)
- **Real-Time Bay Conditions**: NOAA CO-OPS API (Middle Bay Light, Station 8736897) - Wind, water temp, air temp, pressure, water level
- **Weather Forecast**: National Weather Service API (NOAA)
- **Sunrise/Sunset**: Calculated using astronomical formulas
- **Moon Phase**: Calculated from lunar cycle

All data sources are free and public. No API keys required.

## Customization

### Adding New Species

Edit `app/rules/seasonality.py` to add monthly running factors, and `app/rules/bite_logic.py` to add scoring logic.

### Adjusting Bite Logic

Species-specific scoring rules are in `app/rules/bite_logic.py`. Each function combines:
- Tide state and movement
- Time of day
- Weather conditions
- Seasonal presence

Adjust the scoring weights and thresholds to match your local knowledge.

### Changing UI

- **HTML**: `app/templates/index.html`
- **CSS**: `app/static/css/style.css`
- **JavaScript**: `app/static/js/dashboard.js`

## Performance

- **Storage**: ~5-10 MB for database
- **Memory**: ~100 MB RAM
- **CPU**: Minimal (updates every 15 minutes)
- **Network**: ~1-2 MB per update cycle

Works great on:
- Raspberry Pi 3 or newer
- Any Ubuntu VPS or home server
- Old laptop running Ubuntu

## Future Enhancements

Possible additions:
- SMS/Email alert notifications
- Historical bite score charts
- Fish catch logging
- Solunar tables
- Water temperature integration
- Barometric pressure graphs

## License

This is a personal fishing tool. Use and modify as you like for personal, non-commercial purposes.

## Credits

**BayScan** - Smart Fishing Forecasts for Mobile Bay

Built with:
- Python 3 & FastAPI
- NOAA CO-OPS & NWS APIs
- SQLAlchemy
- APScheduler

Created for fishing enthusiasts on Mobile Bay.

🌐 Visit us at [bayscan.app](https://bayscan.app)

---

**Tight lines!** 🎣
