# NOAA Integration Deployment Guide - BayScan

**Date:** November 21, 2025
**Status:** ✅ Implementation Complete - Ready for Deployment

---

## What Was Implemented

### 1. Water Temperature from NOAA CO-OPS
- **Real water temperature** from NOAA tidal stations (not air temp proxy)
- Primary station: 8737048 (Dauphin Island, AL)
- Backup station: 8735180 (Mobile State Docks)
- 30-minute cache to minimize API calls
- Graceful fallback if NOAA unavailable

### 2. Real-Time Weather Observations from NOAA
- **Observed air temperature** (not forecast)
- **Atmospheric pressure** (barometric pressure in mb)
- **Wind speed and direction** (when available)
- Primary station: 8737048 (Dauphin Island, AL)
- Backup station: 8735180 (Mobile State Docks)
- 15-minute cache

### 3. Database Schema Updates
Added `water_temperature` column to three tables:
- `weather_data` - Historical water temp observations
- `forecast_windows` - Water temp in forecast windows
- `catches` - Water temp at time of catch

### 4. API Response Enhancements
New fields in `/api/current`:
```json
{
  "air_temp_f": 74.3,           // NOAA observed air temp
  "water_temp_f": 68.4,         // NOAA observed water temp
  "wind_direction": "SSW",      // NOAA wind direction (cardinal)
  "wind_gust": 12.5,            // NOAA wind gust speed
  "temperature": 74.3           // Kept for backwards compatibility
}
```

### 5. Improved Fish Bite Scoring
- Now uses **actual water temperature** for species scoring
- Falls back to air temp only if water temp unavailable
- More accurate predictions since fish respond to water temp, not air temp

---

## Files Created/Modified

### New Files
1. `app/services/watertemp_service.py` - Water temperature from NOAA
2. `app/services/weather_observations.py` - Real-time weather obs from NOAA
3. `migrations/add_water_temperature.sql` - Database migration
4. `WATER_TEMP_IMPLEMENTATION.md` - Water temp documentation
5. `NOAA_INTEGRATION_DEPLOYMENT.md` - This file

### Modified Files
1. `app/models/schemas.py` - Added water_temperature columns
2. `app/rules/bite_logic.py` - Updated temperature scoring logic
3. `app/services/scoring_service.py` - Integrated NOAA data sources
4. `app/scheduler.py` - Added NOAA data fetching jobs

---

## Deployment Steps

### Step 1: Verify Database Migration (Already Done ✅)
```bash
sqlite3 fishing_forecast.db "PRAGMA table_info(weather_data);" | grep water_temperature
sqlite3 fishing_forecast.db "PRAGMA table_info(forecast_windows);" | grep water_temperature
sqlite3 fishing_forecast.db "PRAGMA table_info(catches);" | grep water_temperature
```

**Expected output:** Each command should show the new `water_temperature` column.

### Step 2: Restart BayScan Service
```bash
sudo systemctl restart bayscan.service
```

### Step 3: Monitor Logs for NOAA Data Fetching
```bash
sudo journalctl -u bayscan.service -f
```

**What to look for:**
```
Fetching water temperature from NOAA...
Water temperature updated: 68.4°F
Water temperature cached: 68.4°F

Fetching weather observations from NOAA...
Weather observations updated: 74.3°F, Wind: N/A SSW
```

### Step 4: Verify API Response
```bash
curl https://bayscan.app/api/current | jq '{air_temp_f, water_temp_f, wind_direction, wind_gust}'
```

**Expected output:**
```json
{
  "air_temp_f": 74.3,
  "water_temp_f": 68.4,
  "wind_direction": "SSW",
  "wind_gust": 12.5
}
```

**Note:** `wind_direction` and `wind_gust` may be `null` if wind data is unavailable from the NOAA station (this is expected behavior).

---

## Known Limitations

### Wind Data Availability
**Issue:** Station 8737048 (Dauphin Island) does not provide wind observations.

**Current Behavior:**
- Wind speed and direction fall back to NWS forecast data
- API returns `null` for `wind_direction` and `wind_gust` when NOAA data unavailable
- BayScan continues to function normally using forecast wind data

**Possible Solutions (if wind observations are critical):**
1. Try backup station 8735180 (Mobile State Docks) - may have wind data
2. Find alternative NOAA station in Mobile Bay with wind observations
3. Continue using NWS forecast wind (current approach - works well)

**Test Wind from Backup Station:**
```bash
source venv/bin/activate
python3 << 'EOF'
from app.services.weather_observations import fetch_weather_observations_from_noaa
result = fetch_weather_observations_from_noaa("8735180")  # Mobile State Docks
if result:
    print(f"Station: {result.get('station_id')}")
    print(f"Wind Speed: {result.get('wind_speed_mph')} mph")
    print(f"Wind Direction: {result.get('wind_direction_cardinal')}")
else:
    print("No wind data from backup station either")
EOF
```

---

## Testing Checklist

### ✅ Pre-Deployment (Completed)
- [x] Database migration successful
- [x] Water temperature service fetches from NOAA
- [x] Weather observations service fetches from NOAA
- [x] Scheduler integration complete
- [x] API response includes new fields
- [x] Temperature scoring uses water temp

### 📋 Post-Deployment (To Do After Restart)
- [ ] Service restarts without errors
- [ ] Logs show NOAA data fetching every 15 minutes
- [ ] Water temperature appears in API response
- [ ] Air temperature comes from NOAA observations
- [ ] Wind direction shows (or `null` if unavailable)
- [ ] Air temp and water temp are different values
- [ ] Forecasts compute successfully with water temp

---

## Verification Commands

### Check Service Status
```bash
sudo systemctl status bayscan.service
```

### Watch Live Logs
```bash
sudo journalctl -u bayscan.service -f
```

### Test API Endpoint
```bash
# Full current conditions
curl https://bayscan.app/api/current | jq .

# Just temperatures
curl https://bayscan.app/api/current | jq '{air_temp_f, water_temp_f}'

# Wind data
curl https://bayscan.app/api/current | jq '{wind_speed, wind_direction, wind_gust}'
```

### Manual NOAA Fetch Test
```bash
cd /home/evo/fishing-forecast
source venv/bin/activate

# Test water temperature
python3 << 'EOF'
from app.services.watertemp_service import get_water_temperature, clear_cache
clear_cache()
result = get_water_temperature()
if result:
    print(f"Water Temp: {result['water_temp_f']}°F from station {result['station_id']}")
else:
    print("Failed to fetch water temperature")
EOF

# Test weather observations
python3 << 'EOF'
from app.services.weather_observations import get_weather_observations, clear_cache
clear_cache()
result = get_weather_observations()
if result:
    print(f"Air Temp: {result.get('air_temp_f')}°F")
    print(f"Wind: {result.get('wind_speed_mph')} mph {result.get('wind_direction_cardinal', 'N/A')}")
    print(f"Pressure: {result.get('pressure_mb')} mb")
else:
    print("Failed to fetch weather observations")
EOF
```

---

## Troubleshooting

### Problem: Water temp shows `null` in API
**Causes:**
1. NOAA station offline or not responding
2. Cache hasn't populated yet (wait 15 minutes after restart)
3. Network connectivity issues

**Solutions:**
```bash
# Check logs for NOAA errors
sudo journalctl -u bayscan.service | grep -i "water temperature"

# Manual test
cd /home/evo/fishing-forecast && source venv/bin/activate
python3 -c "from app.services.watertemp_service import get_water_temperature; print(get_water_temperature())"
```

### Problem: Air temp and water temp are the same
**Causes:**
1. Service not restarted yet
2. NOAA integration not active

**Solutions:**
```bash
# Restart service
sudo systemctl restart bayscan.service

# Wait 2 minutes for initial data fetch
sleep 120

# Check API again
curl https://bayscan.app/api/current | jq '{air_temp_f, water_temp_f}'
```

### Problem: Wind direction still doesn't show
**Expected Behavior:** This is normal. Station 8737048 doesn't provide wind observations.

**Current Behavior:**
- API returns `"wind_direction": null`
- System uses NWS forecast wind instead
- No impact on functionality

**Optional:** Test backup station for wind data (see "Known Limitations" section)

### Problem: Scheduler not fetching NOAA data
**Check scheduler logs:**
```bash
sudo journalctl -u bayscan.service | grep -E "(Fetching water temperature|Fetching weather observations)"
```

**Should see these messages every 15 minutes:**
```
Fetching water temperature from NOAA...
Water temperature updated successfully
Fetching weather observations from NOAA...
Weather observations updated successfully
```

---

## Data Sources Summary

| Data Point | Source | Update Frequency | Cache Duration |
|------------|--------|------------------|----------------|
| Water Temperature | NOAA CO-OPS Station 8737048 | Every 15 min | 30 min |
| Air Temperature | NOAA CO-OPS Station 8737048 | Every 15 min | 15 min |
| Wind Speed | NWS Forecast (NOAA obs unavailable) | Every 15 min | 15 min |
| Wind Direction | NWS Forecast (NOAA obs unavailable) | Every 15 min | 15 min |
| Barometric Pressure | NOAA CO-OPS Station 8737048 | Every 15 min | 15 min |
| Tides | NOAA CO-OPS Predictions | Every 15 min | Database |
| Weather Forecast | NWS Mobile, AL | Every 15 min | Database |
| Moon Phase | Astronomical calculation | Daily | Database |

---

## Success Criteria

After deployment, verify:

✅ **Service Health**
- BayScan service running without errors
- No exceptions in logs related to NOAA fetching

✅ **Data Fetching**
- Water temperature fetched from NOAA every 15 minutes
- Weather observations fetched from NOAA every 15 minutes
- Logs confirm successful updates

✅ **API Response**
- `/api/current` returns both `air_temp_f` and `water_temp_f`
- Water temp is populated (not `null`)
- Air temp and water temp have different values
- Wind direction included (or `null` if unavailable)

✅ **Forecast Accuracy**
- Fish bite scores now based on water temperature
- Forecasts compute successfully with NOAA data
- No errors in forecast generation

---

## Rollback Plan (If Needed)

If deployment causes issues, rollback is simple:

1. **Restore previous code:**
   ```bash
   cd /home/evo/fishing-forecast
   git checkout HEAD~1  # If using git
   ```

2. **Restart service:**
   ```bash
   sudo systemctl restart bayscan.service
   ```

3. **Database rollback (optional):**
   ```bash
   sqlite3 fishing_forecast.db << 'EOF'
   ALTER TABLE weather_data DROP COLUMN water_temperature;
   ALTER TABLE forecast_windows DROP COLUMN water_temperature;
   ALTER TABLE catches DROP COLUMN water_temperature;
   EOF
   ```

**Note:** Dropping columns is optional since they're nullable and won't break old code.

---

## Contact & Support

**Implementation Date:** November 21, 2025
**Tested:** Water temp (✅), Air temp (✅), Pressure (✅), Wind (⚠️ unavailable)
**Status:** Ready for production deployment

For issues or questions, check:
1. Service logs: `sudo journalctl -u bayscan.service -f`
2. NOAA CO-OPS status: https://tidesandcurrents.noaa.gov/
3. This deployment guide

---

## Next Steps

1. **Restart service:** `sudo systemctl restart bayscan.service`
2. **Monitor logs:** Watch for NOAA fetching messages
3. **Test API:** Verify water_temp_f is populated
4. **Monitor for 1 hour:** Ensure scheduled fetching works
5. **Optional:** Investigate wind data from alternative stations if needed

**All code changes are complete and tested. Ready to deploy! 🚀**
