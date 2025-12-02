# HyperLocal Spec Implementation Status

## Overview
Implementing the comprehensive hyperlocal fishing brain for BelleFontaine Dock as specified. All analytics and bite scores are now zone-specific with the new formula:

**bite_score = seasonal_baseline + environmental_adjustments + recent_activity + predator_decay**

---

## ✅ COMPLETED

### 1. Database Schema Updates

**File: `app/models/schemas.py`**

#### Catch Model (Updated)
Added new required fields:
- `zone_id` (required, indexed) - Zone 1-5
- `distance_from_dock` - at dock, 50-100 ft, 100-150 ft, 150+ ft
- `depth_estimate` - shallow, medium, deep
- `structure_type` - pilings, grass edge, open water, channel edge
- `bait_used` - replaces bait_type
- `presentation` - replaces method (jig, cork, carolina, free-lined)
- `predator_seen_recently` - boolean flag

Expanded environment snapshot fields:
- `water_temp`, `air_temp`, `humidity`, `barometric_pressure`
- `tide_height`, `tide_stage` (incoming/outgoing/slack/high/low)
- `current_speed`, `current_direction`
- `wind_speed`, `wind_direction`
- `weather` (clear, cloudy, rain, storm)
- `time_of_day` (pre-dawn, morning, midday, evening, night)
- `moon_phase`, `dock_lights_on`

#### BaitLog Model (Updated)
- `timestamp` - primary timestamp field
- `bait_species` - shrimp, menhaden, mullet, fiddler, pinfish
- `method` - cast net, trap (required)
- `quantity_estimate` - none, few, plenty
- `zone_id` - Zone 1-5 (required, indexed)
- `structure_type` - same as Catch
- Full environment snapshot (matches Catch model)

#### New: EnvironmentSnapshot Model
Stores snapshots every 5-15 minutes for learning no-bite conditions:
- All environment fields (water temp, air temp, humidity, pressure, tide, current, wind, weather, time, moon, lights)
- Indexed by timestamp

### 2. UglyFishing Seasonal Calendar

**New File: `app/rules/uglyfishing_calendar.py`**

Functions:
- `get_seasonal_baseline_score(species, date)` - Returns 0-90 baseline
- `running_factor_to_baseline(factor)` - Converts 0-1.0 to UglyFishing scale:
  - 0.0 (N/A) → 0
  - 0.2 (Poor) → 20
  - 0.4 (Fair) → 40
  - 0.6 (Good) → 60
  - 0.8 (Great) → 80
  - 1.0 (Excellent) → 90

Constants:
- `TIER_1_SPECIES` - Priority species: speckled_trout, redfish, flounder, sheepshead, black_drum
- `TIER_2_SPECIES` - croaker, white_trout, jack_crevalle, mullet
- `BAIT_SPECIES` - live_shrimp, menhaden, live_bait_fish, pinfish, fiddler_crab

Functions to separate bait from fish:
- `is_bait_species(species)` - Check if bait
- `is_fish_species(species)` - Check if fish
- `get_species_tier(species)` - Get priority tier (1, 2, or 0 for bait)

### 3. Hyperlocal Scoring Engine

**New File: `app/services/hyperlocal_scoring.py`**

Main function:
- `calculate_zone_bite_score(db, species, zone_id, conditions, date)` - Returns dict with:
  - `bite_score` - Final 0-100 score
  - `seasonal_baseline` - 0-90 UglyFishing baseline
  - `environmental_adjustment` - -30 to +10
  - `recent_activity_bonus` - 0-10
  - `predator_penalty` - 0 to -20
  - `breakdown` - Detailed breakdown

Environmental adjustments (-30 to +10):
- Water temperature vs ideal range: -10 to +5
- Tide stage: -8 to +3
- Wind: -5 to +2
- Time of day: -4 to +2
- Barometric pressure: -3 to +1

Recent activity bonus (0-10):
- Catches in last 2 hours: +2 points each (max +6)
- Catches 2-4 hours ago: +1 point each (max +3)
- Catches 4-6 hours ago: +0.5 points each (max +1)

Predator penalty (0 to -20):
- Predator seen in last 1 hour: -20
- 1-2 hours ago: -15
- 2-3 hours ago: -10
- 3-4 hours ago: -5

Includes species-specific ideal ranges:
- Water temp ranges
- Ideal tide stages
- Ideal times of day

### 4. Environment Snapshot Service

**New File: `app/services/environment_snapshot.py`**

Functions:
- `capture_environment_snapshot(db)` - Captures and stores snapshot
- `get_latest_snapshot(db)` - Gets most recent snapshot
- `get_snapshot_as_dict(snapshot)` - Converts to conditions dict
- `map_tide_state_to_stage(state, height)` - Maps state to stage
- `cleanup_old_snapshots(db, days)` - Cleans up old data

Features:
- Checks for duplicates (won't create if one exists within 5 minutes)
- Pulls from NOAA observations when available
- Determines dock lights status based on time of day
- Maps tide state to proper tide stage format

---

## 🔨 IN PROGRESS / TODO

### 5. API Request Models

**File: `app/main.py` - Lines 35-103**

Need to update `CatchCreate` Pydantic model:
```python
class CatchCreate(BaseModel):
    species: str
    zone_id: str  # NEW - required
    distance_from_dock: Optional[str]  # NEW
    depth_estimate: Optional[str]  # NEW
    structure_type: Optional[str]  # NEW
    size_length_in: Optional[int]
    size_bucket: Optional[str]
    quantity: Optional[int] = 1
    bait_used: Optional[str]  # renamed from bait_type
    presentation: Optional[str]  # renamed from method
    predator_seen_recently: bool = False  # NEW
    kept: bool = False
    notes: Optional[str]
    timestamp: Optional[datetime] = None
```

Need to update `BaitLogCreate` model:
```python
class BaitLogCreate(BaseModel):
    bait_species: str  # shrimp, menhaden, mullet, fiddler, pinfish
    method: str  # cast net, trap - REQUIRED
    zone_id: str  # NEW - Zone 1-5, required
    quantity_estimate: Optional[str]  # none, few, plenty
    structure_type: Optional[str]  # NEW
    notes: Optional[str]
    timestamp: Optional[datetime] = None
```

### 6. API Endpoints to Update

#### POST /api/catches
- Accept new CatchCreate model
- Capture full environment snapshot from latest EnvironmentSnapshot
- Store all new fields

#### POST /api/bait-logs
- Accept new BaitLogCreate model
- Capture full environment snapshot
- Store all new fields

#### GET /api/current (Major Update)
- Call new hyperlocal scoring for each species in each zone
- Return zone-specific scores
- Use seasonal baselines + environmental adjustments
- Include recent activity and predator decay
- Return breakdown for transparency

Example response structure:
```json
{
  "timestamp": "2025-11-24T...",
  "zones": {
    "Zone 3": {
      "species": [
        {
          "name": "Speckled Trout",
          "bite_score": 72,
          "seasonal_baseline": 60,
          "environmental_adjustment": 8,
          "recent_activity_bonus": 6,
          "predator_penalty": -2,
          "explanation": "Good (60) + favorable conditions (+8) + recent catches (+6) - predator nearby (-2)"
        }
      ]
    }
  },
  "top_targets": [...],
  "bait_overview": [...]
}
```

#### NEW: GET /api/zone-bite-scores
Query params: species, zone_id
Returns detailed zone-specific bite score with full breakdown

### 7. Scheduler Updates

**File: `app/scheduler.py`**

Add new scheduled job:
- Capture environment snapshot every 10 minutes
- Call `capture_environment_snapshot(db)`

### 8. Frontend Updates Needed

#### Fish Logging Form
**File: `app/static/js/fishing_log.js` or new `logging_tabs.js`**

Update form fields (in order per spec):
1. Species (dropdown)
2. Zone (dropdown) - Zone 1-5 **REQUIRED**
3. Distance from Dock (dropdown) - at dock, 50-100 ft, 100-150 ft, 150+ ft
4. Depth (dropdown) - shallow, medium, deep
5. Structure (dropdown) - pilings, grass edge, open water, channel edge
6. Size (length input + size bucket buttons)
7. Bait Used (dropdown) - renamed from "Bait Type"
8. Presentation (dropdown) - jig, cork, carolina, free-lined - renamed from "Method"
9. Predator Seen Recently? (checkbox/toggle)
10. Quantity (number)
11. Keep/Release (toggle)
12. Notes (textarea)

#### Bait Logging Form
Match fish logging layout exactly:
1. Bait Species (dropdown) - shrimp, menhaden, mullet, fiddler, pinfish
2. Method (dropdown) - cast net, trap **REQUIRED**
3. Zone (dropdown) - Zone 1-5 **REQUIRED**
4. Quantity Estimate (dropdown) - none, few, plenty
5. Structure (dropdown) - pilings, grass edge, open water, channel edge
6. Notes (textarea)

#### Species Forecast Screen
**File: `app/templates/index.html` or `dashboard.js`**

Add tabs INSIDE Species Forecast container (not whole page):
- **Fish** tab - Shows fish species only
- **Bait** tab - Shows bait species only (full-width cards per spec)

Bait cards show:
- Rating (Poor → Excellent using same scale)
- Name
- Short one-liner
- "How to catch" section

#### Home Screen Redesign
**File: `app/templates/index.html` + `dashboard.js`**

New layout:
1. **Top Target Species** section
   - Shows top 3-5 priority species (Tier 1)
   - Bite score + short plain-English explanation
   - Best zone for each

2. **Bait Overview Card**
   - Quick ratings for: shrimp, mullet, menhaden, fiddlers
   - Simple grid or list view

3. **Buttons**
   - "Log Catch" - Opens fish logging form
   - "Log Bait" - Opens bait logging form

### 9. Database Migration

**New File: `migration_hyperlocal_spec.py`**

Need to create migration that:
1. Adds new columns to catches table
2. Adds new columns to bait_logs table
3. Creates environment_snapshots table
4. Handles nullable/required field changes
5. Migrates existing data where possible

SQLAlchemy command:
```python
from app.database import Base, engine
from app.models.schemas import EnvironmentSnapshot
Base.metadata.create_all(bind=engine)
```

For existing data, may need to:
- Set default zone_id for old catches (Zone 3 as default?)
- Convert old bait_type → bait_used
- Convert old method → presentation
- Set default values for new required fields

---

## 🎯 Priority Implementation Order

1. **[DONE]** Database models updated
2. **[DONE]** UglyFishing calendar created
3. **[DONE]** Hyperlocal scoring engine created
4. **[DONE]** Environment snapshot service created
5. **[NEXT]** Update API request models (CatchCreate, BaitLogCreate)
6. **[NEXT]** Update POST /api/catches endpoint
7. **[NEXT]** Update POST /api/bait-logs endpoint
8. **[NEXT]** Update GET /api/current to use hyperlocal scoring
9. **[NEXT]** Add environment snapshot capture to scheduler
10. **[NEXT]** Create database migration script
11. **[NEXT]** Update frontend fish logging form
12. **[NEXT]** Update frontend bait logging form
13. **[NEXT]** Add Fish/Bait tabs to Species Forecast
14. **[NEXT]** Redesign home screen
15. **[TEST]** End-to-end testing

---

## 📋 Key Design Decisions

1. **Zone-Specific Scores**: Every bite score is calculated per zone. No more dock-wide scores.

2. **Bait Separation**: Bait species (shrimp, menhaden, mullet, fiddlers, pinfish) do NOT appear in fish forecast. They have their own "Bait" tab with different card design.

3. **UglyFishing Scale**: Seasonal baselines use 0-90 scale (not 0-100) to leave room for environmental adjustments.

4. **Recent Activity Window**: 4-6 hours for catches, 4 hours for predators.

5. **Environment Snapshots**: Captured every 5-15 minutes regardless of fishing activity, allowing system to learn "no-bite conditions."

6. **Predator Impact**: Predators create temporary penalties in the zone they were seen, decaying over 4 hours.

7. **Species-Specific Ranges**: Each species has ideal ranges for water temp, tide stages, times of day. These drive environmental adjustments.

8. **Migration Strategy**: Old data will need default zone assignments (probably Zone 3 as it's most fished).

---

## 🧪 Testing Checklist

After implementation:

- [ ] Log a catch with all new fields - verify database storage
- [ ] Log bait with new fields - verify database storage
- [ ] Check environment snapshots are being captured every 10 min
- [ ] API /api/current returns zone-specific scores
- [ ] Bite score formula matches spec (baseline + env + activity + predator)
- [ ] Recent catches boost scores correctly
- [ ] Predator sightings create penalties
- [ ] Fish/Bait tabs work and show correct species
- [ ] Home screen shows top targets + bait overview
- [ ] Old data migrated without errors
- [ ] Mobile-first UI works on phone

---

**Last Updated**: November 24, 2025
**Status**: Backend complete, API updates in progress, Frontend pending
