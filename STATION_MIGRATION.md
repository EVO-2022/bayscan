# NOAA Station Migration - December 2, 2025

## Overview
BayScan has been updated to use a **two-station approach** for improved data accuracy and separation of concerns:

1. **Tide Predictions** → NOAA Station 8735180 (Bayou La Batre, AL)
2. **Real-Time Conditions** → NOAA Station 8736897 (Middle Bay Light, AL)

## Previous Configuration
- **Single Station**: 8737048 (Dauphin Island, AL)
- Used for ALL tide and weather data

## New Configuration

### Station 8735180 - Bayou La Batre (Tide Predictions)
- **Purpose**: Tide predictions ONLY
- **Data Products**:
  - Predicted tide heights (MLLW datum)
  - High/low tide times
  - Tide stage (rising/falling/slack)
- **Update Interval**: Predictions fetched every 15 minutes (covers 48 hours ahead)
- **Used By**:
  - `app/services/tide_service.py` - All tide prediction logic
  - Bite score calculations requiring tide phase
  - "Next 24 Hours" tide curve
  - Main page tide info

### Station 8736897 - Middle Bay Light (Real-Time Conditions)
- **Purpose**: Live bay observations ONLY
- **Data Products**:
  - Water temperature (observed)
  - Air temperature (observed)
  - Wind speed and direction (observed)
  - Wind gusts (observed)
  - Atmospheric pressure (observed)
  - Water level deviation from predicted (observed)
- **Update Interval**: Observations cached for 15-30 minutes
- **Used By**:
  - `app/services/watertemp_service.py` - Water temperature
  - `app/services/weather_observations.py` - Wind, air temp, pressure
  - Bite score condition refinements
  - Current conditions displays

## Files Modified

### Configuration
- **config.yaml**:
  - Changed `tide.station_id` → `tide.prediction_station_id: "8735180"`
  - Added `tide.realtime_station_id: "8736897"`

- **app/config.py**:
  - Added `tide_prediction_station_id()` property
  - Added `realtime_conditions_station_id()` property
  - Maintained `tide_station_id()` for backwards compatibility (returns prediction station)

### Services
- **app/services/tide_service.py**:
  - Uses `config.tide_station_id` (points to 8735180)
  - No code changes needed (uses config property)

- **app/services/watertemp_service.py**:
  - Updated primary station to 8736897 (Middle Bay)
  - Updated backup station to 8735180 (Bayou La Batre)
  - Uses `config.realtime_conditions_station_id()` via helper functions

- **app/services/weather_observations.py**:
  - Updated primary station to 8736897 (Middle Bay)
  - Updated backup station to 8735180 (Bayou La Batre)
  - Uses `config.realtime_conditions_station_id()` via helper functions

### Documentation
- **README.md**:
  - Updated data sources section
  - Updated troubleshooting links

- **BAYSCAN.md**:
  - Added NOAA Data Stations section

- **app/templates/index.html**:
  - Updated footer to show both stations

## Data Flow

### Tide Predictions (8735180)
```
NOAA API (8735180) → tide_service.py → Database (TideData table) → API endpoints → UI
```

### Real-Time Conditions (8736897)
```
NOAA API (8736897) → watertemp_service.py/weather_observations.py → Cached in memory → Scoring services → UI
```

## Verification Checklist

✅ No references to 8737048 remain in code
✅ Configuration uses 8735180 for tide predictions
✅ Configuration uses 8736897 for real-time conditions
✅ Tide service uses prediction station
✅ Water temp service uses realtime station
✅ Weather observations service uses realtime station
✅ UI footer shows both stations
✅ Documentation updated

## Testing After Deployment

1. **Verify tide predictions load**:
   ```bash
   curl http://localhost:8080/api/current | jq '.tide'
   ```
   Should show tide data from 8735180

2. **Verify water temperature loads**:
   ```bash
   curl http://localhost:8080/api/current | jq '.conditions.water_temp_f'
   ```
   Should show water temp from 8736897 (or backup 8735180)

3. **Check logs for station confirmation**:
   ```bash
   sudo journalctl -u bayscan.service -f | grep "station"
   ```
   Should see:
   - "Retrieved water temp from station 8736897"
   - "Weather observations cached from station 8736897"
   - Tide queries use 8735180 implicitly

4. **Verify UI displays correct sources**:
   - Visit https://bayscan.app
   - Check footer shows: "NOAA Tides (8735180 Bayou La Batre), NOAA Real-Time Conditions (8736897 Middle Bay)"

## Rollback Procedure (If Needed)

If issues occur, revert to single-station mode:

1. Edit `config.yaml`:
   ```yaml
   tide:
     prediction_station_id: "8737048"
     realtime_station_id: "8737048"
   ```

2. Restart service:
   ```bash
   sudo systemctl restart bayscan.service
   ```

## Station Information

### 8735180 - Bayou La Batre, AL
- **Location**: 30.4033°N, 88.2483°W
- **NOAA Page**: https://tidesandcurrents.noaa.gov/stationhome.html?id=8735180
- **Products Available**: Predictions, Water Level, Water Temp, Air Temp, Wind, Air Pressure
- **Distance from Belle Fontaine**: ~15 miles south

### 8736897 - Middle Bay Light, AL
- **Location**: 30.4550°N, 87.9917°W
- **NOAA Page**: https://tidesandcurrents.noaa.gov/stationhome.html?id=8736897
- **Products Available**: Water Level, Water Temp, Air Temp, Wind, Air Pressure, Currents
- **Distance from Belle Fontaine**: ~5 miles east (IN Mobile Bay, closest real-time station)

## Notes

- Station 8736897 (Middle Bay Light) is a NOAA PORTS station providing real-time observations
- Station 8735180 (Bayou La Batre) provides both predictions and observations
- Backup logic ensures system continues working if primary station is unavailable
- Tide predictions remain accurate as they are computational forecasts
- Real-time conditions are more representative of actual bay conditions at Belle Fontaine

---

**Migration Date**: December 2, 2025
**BayScan Version**: 2.8.0+
**Status**: ✅ Complete
