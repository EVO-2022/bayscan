# Fishing Log - Quick Start Guide

## First Time Setup

The Fishing Log is built into BayScan and requires no additional configuration. The new `catches` database table will be created automatically when you start the application.

### Starting BayScan

```bash
# Navigate to the project
cd /home/evo/fishing-forecast

# Activate virtual environment (if not using systemd)
source venv/bin/activate

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Or if running as a service:
```bash
sudo systemctl restart bayscan.service
```

## Accessing the Fishing Log

1. Open BayScan in your browser: `http://localhost:8080` (or your server IP)
2. Click the **"Log"** tab (📝 icon) in the navigation bar
3. You'll see:
   - New Catch form at the top
   - Recent Catches table in the middle
   - Last 30 Days stats at the bottom

## Logging Your First Catch

### Fast Entry (Mobile Optimized)

1. **Tap a species button** - Choose from the 8 large buttons at the top
   - Trout, Redfish, Flounder, Sheepshead, Mullet, Mackerel, Croaker, Stingray

2. **Select details** (all optional except species):
   - **Side of Dock**: N, NE, E, SE, S, SW, W, NW
   - **Length**: Enter size in inches (optional)
   - **Size Category**: Tap Small, Keeper, or Big
   - **Bait Type**: Type in what you used (e.g., "live shrimp")
   - **Method**: Select from dropdown (bottom rig, cork, artificial, etc.)
   - **Kept/Released**: Tap Kept or Released

3. **Tap "Log Catch"**

✓ Done! Your catch is logged with automatic conditions snapshot.

### What Gets Captured Automatically

When you log a catch, BayScan automatically records:
- Exact timestamp
- Current tide state (rising/falling/slack)
- Current tide height
- Temperature
- Wind speed
- Pressure trend
- Weather conditions

This lets you analyze which conditions produce the best catches!

## Viewing Your Catches

### Recent Catches Table

Shows your most recent catches with:
- **Time**: Human-friendly format (e.g., "Today 5:42 PM")
- **Species**: What you caught
- **Side**: Which side of the dock
- **Length**: Size in inches (if entered)
- **Size**: Small/Keeper/Big category
- **Bait**: What you used
- **Status**: Kept (green) or Released (blue)

### Filter by Species

Use the dropdown above the table to show only specific species:
- Select "Speckled Trout" to see only trout catches
- Select "All species" to see everything

### Statistics (Last 30 Days)

Automatically shows:
- **Total catches**: How many fish you've caught
- **Kept vs Released**: Breakdown of what you kept
- **By Species**: Catch counts for each species
- **Top Baits**: Most successful baits by catch count
- **Top Methods**: Most successful methods

## Tips for Best Results

### Consistent Logging
- Log catches immediately while still fresh
- Include as many details as possible (bait, method, size)
- Note dock side - helps identify productive spots

### Use Quick Buttons
- Species buttons auto-fill the dropdown
- Size buttons are faster than typing
- Kept/Released toggle is just one tap

### Analyze Patterns
- Check stats weekly to see what's working
- Compare tide states in your catch history
- Notice which baits catch which species most

### Mobile Usage
- Add BayScan to your phone's home screen
- Keep the Log tab open while fishing
- Log catches without leaving the dock

## Example Workflow

### Scenario: Catching a keeper trout

1. **Open BayScan on phone** (already on Log tab from last time)
2. **Tap "Trout"** button
3. **Tap "NE"** for dock side (current favorite spot)
4. **Type "16"** for length
5. **Tap "Keeper"**
6. **Type "live shrimp"** for bait
7. **Select "cork"** from method dropdown
8. **Tap "Kept"**
9. **Tap "Log Catch"**

✓ **Total time: 8 seconds**

The form remembers:
- Species: Trout (for next catch)
- Dock side: NE (likely catching more here)
- Method: cork (likely using same setup)

So your NEXT catch only needs:
1. Tap species (if different)
2. Enter size
3. Tap Log Catch

Even faster!

## Troubleshooting

### "No catches logged yet" showing
- This is normal on first use
- Log your first catch and it will appear immediately

### Catch not appearing in table
- Check browser console for errors (F12)
- Verify API is accessible: `curl http://localhost:8080/api/catches`
- Check server logs: `sudo journalctl -u bayscan.service -f`

### Stats showing zero
- Stats only count catches from last 30 days
- Log a catch and stats will update immediately

### Form not submitting
- Species is required - make sure it's selected
- Check network connection
- Look for error message above form

## API Access (Advanced)

### Export Your Data

Get all catches as JSON:
```bash
curl http://localhost:8080/api/catches?limit=200 > my_catches.json
```

### Log Catch from Command Line

```bash
curl -X POST http://localhost:8080/api/catches \
  -H "Content-Type: application/json" \
  -d '{
    "species": "redfish",
    "dock_side": "E",
    "size_length_in": 24,
    "bait_type": "live shrimp",
    "kept": true
  }'
```

### Get Today's Catches

```bash
curl "http://localhost:8080/api/catches?limit=50" | jq '.[] | select(.timestamp | startswith("2025-11-19"))'
```

## Privacy & Data

- All catch data is stored **locally** in your SQLite database
- Nothing is sent to external services
- Your catches are **private** to your installation
- Backup your database file regularly: `fishing_forecast.db`

## Next Steps

- **Start logging!** The more data you capture, the better insights you'll get
- **Review stats weekly** to identify successful patterns
- **Adjust your approach** based on what the data shows
- **Track seasonal changes** by comparing monthly stats

Happy fishing! 🎣
