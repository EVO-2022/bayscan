# BayScan v2.8.0 - Technical Reference

**Live:** https://bayscan.app | **Location:** Belle Fontaine, Mobile Bay | **Stack:** FastAPI + SQLite + Vanilla JS

---

## Core System

### Version Info
- **Current:** v2.8.0 (Nov 28, 2025)
- **Updates:** Every 15 min (Environment snapshots: 10 min)
- **Database:** SQLite at `/home/evo/fishing-forecast/fishing_forecast.db`

### Species (14 Total)
**Tier 1 (Full Analytics):** Speckled Trout, Redfish, Flounder, Sheepshead, Black Drum
**Tier 2 (Simplified):** Croaker, White Trout, Menhaden, Mullet, Jack Crevalle
**Bait:** Live Shrimp, Menhaden, Mullet, Fiddler Crab

---

## Scoring System

### Formula (Tier 1)
```
BiteScore = SeasonalBaseline (0-90)
          + ConditionMatch (±10)
          + StructureMatch (±10)
          + ClaritySalinity (±7)
          + RecentActivity (0-10)
          + PredatorPenalty (0 to -8)
          + ExternalIndicators (±5)
          + ColdNorthWindPenalty (depth shifts & behavior)
```

### Cold North Wind System (NEW v2.8.0)
**Trigger Conditions:**
- **North-Derived Winds:** N, NNE, NE, NNW, NW
- **Cold Temps:** Air temp ≤ 60°F OR Water temp ≤ 60°F
- **Shallow Location:** Belle Fontaine avg depth 4.5 ft (< 6 ft threshold)

**Strong Penalty (All conditions met):**
- North wind + Wind speed ≥ 10 mph + Cold temps
- **Depth Shift:** +1 to +3 ft deeper (species-dependent)
  - Shallow species (trout, reds, mullet): +3 ft
  - Mid-depth species (white trout, croaker): +2 ft
  - Deep species (drum, flounder): +1 ft
- **Zone Adjustment:** Shallow zones (1, 2) penalized -3/-4 points, deep zones (4, 5) boosted +2/+3 points
- **Summary Text:** "Cold north wind is pushing fish off the shallow flat. Expect them to hold deeper along edges; shallow bite may be slow."

**Moderate Penalty (North wind without strong conditions):**
- North wind + Shallow location (even if warm or light wind)
- **Depth Shift:** +1 ft for shallow species
- **Summary Text:** "Fish are feeding but holding slightly deeper than normal due to north wind."

**Detection Logic:**
- Module: `app/rules/cold_north_wind.py`
- Applied to: Depth behavior, conditions summary, best zones
- Does NOT change base bite scores, only expected behavior and location

### Formula (Tier 2)
```
BiteScore = SeasonalBaseline + SimpleCondition + StructureMatch
```

### Tiers (Display Only)
- **HOT:** 80-100
- **DECENT:** 50-79
- **SLOW:** 20-49
- **UNLIKELY:** 0-19

### Confidence Levels
- **HIGH:** >50 catches (1.0x weight)
- **MEDIUM:** 10-50 catches (0.6x weight)
- **LOW:** <10 catches (0.3x weight)

---

## Zone Geometry (CANONICAL)

### Layout
```
        NORTH
    [Zone 1] [Zone 3]
    ─────WALKWAY─────  [Zone 5]
    [Zone 2] [Zone 4]
        SOUTH
```

### Zone Details
| Zone | Position | Depth | Structure | Features |
|------|----------|-------|-----------|----------|
| 1 | NW | 2-4 ft | Pilings (N edge) | Rubble |
| 2 | SW | 2-4 ft | None | Open water |
| 3 | NE | 3-6 ft | Pilings (N edge) | Most fished |
| 4 | SE | 3-6 ft | Green light | Most fished |
| 5 | E | 5-7 ft | Dual pilings | Strongest structure |

**Structure Rules:**
- All pilings run EAST-WEST
- Zones 1,3,5 have north border pilings
- Zone 5 has additional center piling line
- NO southern pilings in any zone

---

## Species Behavior (Tier 1)

### Speckled Trout
- **Temp:** 65-78°F ideal, penalty outside 58-85°F
- **Tide:** Incoming +4, Outgoing +2, Slack -4
- **Clarity:** Clear +5, Muddy -6 (needs clear water)
- **Wind:** SE/S/SW +3, N (post-front) -4
- **Structure:** Pilings +3, Green light night +4
- **Zones:** 2, 3, 4 (especially Zone 4 at night)
- **Cold North Wind:** Depth shifts from 2-4 ft → 5-7 ft (good bite), behavior note changes to "Holding deeper along edges; shallow bite may be slow"

### Redfish
- **Temp:** 65-80°F ideal (tolerant 55-88°F)
- **Tide:** Incoming +5, Outgoing +4, Slack -5 (very tide-driven)
- **Clarity:** Tolerates muddy (only -1 penalty)
- **Structure:** Pilings +5, Rubble +5, Open water -2
- **Zones:** 1, 2, 3 (loves Zone 1 rubble)
- **Cold North Wind:** Depth shifts from 1-3 ft → 4-6 ft, pushed off shallowest flats

### Flounder
- **Temp:** 65-75°F ideal, cold snap -7
- **Tide:** Outgoing +4, Slack -6
- **Clarity:** Clear +6, Muddy -7 (NEEDS clear water)
- **Structure:** Rubble +6 (Zone 1), Pilings +5
- **Zones:** 1, 3, 4, 5 (rubble bonus Zone 1)

### Sheepshead
- **Temp:** 55-70°F ideal (winter species)
- **Tide:** Incoming/Outgoing +3, Slack -3
- **Clarity:** Clear +5, Muddy -4
- **Structure:** Pilings +6, Barnacles +6, Open water -6
- **Zones:** 3, 5 (structure-dependent)
- **Peak:** Dec-Mar

### Black Drum
- **Temp:** 60-75°F ideal (tolerant 50-85°F)
- **Tide:** Less sensitive (Incoming/Outgoing +2, Slack -2)
- **Clarity:** Muddy tolerant (0 penalty)
- **Structure:** Pilings +4, Mud bottom +4
- **Zones:** 1, 3, 5 (prefers Zone 5 deep)
- **Year-round**

---

## Bait Species

### Live Shrimp
- **Zone 4 night:** +10 (green light)
- **Incoming tide:** +5
- **Temp <55°F:** -8 (cold kills activity)
- **Best:** Zone 4 evening/night incoming tide

### Menhaden
- **SE/S/SW wind + structure zones (1,3,5):** +8
- **Current >0.4 + structure:** +5
- **Wind-driven to structure edges**

### Mullet
- **Shallow zones (1,2) + incoming tide:** +8
- **Warm water (≥70°F):** +4
- **Seasonal runs**

### Fiddler Crab
- **Winter (Dec-Mar):** +10
- **Off-season:** -5
- **Structure zones (1,3,5):** +3
- **Correlates with sheepshead availability**

---

## Recent Activity Decay

**Formula:** `BaseValue × (0.75 ^ hours_ago)`
- Base: 4.0 per catch
- Decay: 25% per hour
- Confidence weight applied
- Cap: +10

---

## Predator System

**Prey Species:** Trout, White Trout, Menhaden, Mullet, Shrimp
**Penalty:** -8 base, linear decay over 4 hours
**Triggers:** Jack Crevalle, Shark, Dolphin, Bull Red

---

## File Structure

### Core Logic
- `app/rules/species_tiers.py` - Tier classification
- `app/rules/species_behavior_profiles.py` - Behavior data (417 lines)
- `app/rules/cold_north_wind.py` - Cold north wind detection & penalties (NEW v2.8.0)
- `app/rules/behavior.py` - Depth behavior with cold wind adjustments
- `app/rules/conditions_summary.py` - Summary generation with wind-aware phrasing
- `app/services/hyperlocal_scoring.py` - Main scoring engine (520 lines)
- `app/services/bait_scoring.py` - Bait scoring (317 lines)
- `app/services/confidence_scoring.py` - Data quality scoring
- `app/services/advanced_features.py` - Best zones with cold wind adjustments

### API Endpoints
- `/api/current` - Current conditions + species forecasts
- `/api/forecast` - 24-hour forecast
- `/api/zone-bite-scores?species=X&zone_id=Zone%203` - Zone-specific score
- `/api/bait-forecast` - Bait activity all zones
- `/api/catches` - Log catch
- `/api/bait-logs` - Log bait sighting
- `/api/predator-logs` - Log predator
- `/api/weekly-summary?species=X` - 7-day summary

---

## Deployment

### Service Commands
```bash
sudo systemctl status bayscan.service
sudo systemctl restart bayscan.service
sudo journalctl -u bayscan.service -f
```

### Network
- **IP:** 99.107.152.134 (AT&T Fiber)
- **Ports:** 80→443→8080
- **SSL:** Let's Encrypt auto-renew
- **DNS:** Porkbun (bayscan.app)

### NOAA Data Stations
- **Tide Predictions:** 8735180 (Bayou La Batre, AL)
- **Real-Time Conditions:** 8736897 (Middle Bay Light, AL) - Wind, water temp, air temp, pressure, observed water level

### Database Backup
```bash
cp fishing_forecast.db fishing_forecast.db.backup_$(date +%Y%m%d)
```

---

## Recent Changes (Latest First)

### v2.8.0 (Nov 28, 2025) - COLD NORTH WIND PENALTY SYSTEM
**Intelligent depth behavior adjustments for cold north wind conditions in shallow water**

**Problem Solved:**
- BayScan was saying "fish are pushing shallow" during cold north wind events
- Did not account for fish moving deeper when cold fronts push through
- Zone recommendations prioritized shallow water inappropriately in cold conditions

**Solution - Cold North Wind Detection Module:**
Created `app/rules/cold_north_wind.py` with comprehensive detection logic:
- **North Winds:** N, NNE, NE, NNW, NW
- **Cold Temps:** Air ≤ 60°F OR Water ≤ 60°F
- **Strong Penalty:** North wind + ≥10 mph + Cold temps
- **Moderate Penalty:** North wind in shallow location (Belle Fontaine 4.5 ft avg depth)

**Depth Behavior Adjustments:**
Modified `app/rules/behavior.py` to apply species-specific depth shifts:
- **Shallow species (trout, reds, mullet):** +3 ft deeper under strong penalty, +1 ft under moderate
- **Mid-depth species (white trout, croaker):** +2 ft deeper
- **Deep species (drum, flounder):** +1 ft deeper
- **Example:** Speckled trout "good" bite shifts from 2-4 ft → 5-7 ft
- **Depth notes updated:** "Off the dock edge on the deeper side, not in skinniest water" / "Holding deeper along edges; shallow bite may be slow"

**Conditions Summary Updates:**
Modified `app/rules/conditions_summary.py` to change phrasing based on wind conditions:
- **Before:** "Fish are feeding and pushing shallow" (even in cold north wind)
- **After (Strong):** "Cold north wind is pushing fish off the shallow flat. Expect them to hold deeper along edges; shallow bite may be slow."
- **After (Moderate):** "Fish are feeding but holding slightly deeper than normal due to north wind."
- **Wind description:** Changes from "good surface chop" → "cold north wind"
- **Temperature description:** Never says "ideal" when cold, uses "cold temperatures"
- **Mixed conditions:** "Strong moving tide, but cold north wind and cold temperatures create mixed conditions."

**Best Zones Adjustments:**
Modified `app/services/advanced_features.py` to rerank zones under cold north wind:
- **Shallow zones (1, 2) penalized:** -3 and -4 points respectively
- **Deep zones (4, 5) boosted:** +2 and +3 points respectively
- **Zone 3 neutral:** Mid-depth with structure stays balanced
- **Example result:** Zones [4, 5, 1] instead of [1, 2, 3] under strong penalty

**Integration Points:**
- `app/services/scoring_service.py` - Passes wind/temp data to all behavior functions
- `get_depth_behavior()` - Now accepts wind_direction, wind_speed, air_temp_f, water_temp_f
- `generate_conditions_summary()` - Now accepts same parameters for intelligent phrasing
- `get_best_zones_now()` - Now accepts same parameters for zone reranking

**Test Results (Current Conditions: N wind, 10 mph, 51°F air, 67°F water):**
```
Conditions Summary:
"Steady tide flow, cold north wind, and cold temperatures.
Cold north wind is pushing fish off the shallow flat.
Expect them to hold deeper along edges; shallow bite may be slow."

Best Zones: [4, 5, 1]  (deeper zones prioritized)

Depth Examples:
- Black Drum: 5-7 ft (was 4-7 ft)
  "Off the dock edge on the deeper side, not in skinniest water"
- Speckled Trout: 6-7 ft (was 3-5 ft)
  "Holding deeper along edges; shallow bite may be slow"
```

**Files Created:**
- `app/rules/cold_north_wind.py` - Detection module (197 lines)

**Files Modified:**
- `app/rules/behavior.py` - Added wind/temp params to get_depth_behavior(), depth shift logic
- `app/rules/conditions_summary.py` - Wind-aware phrasing, cold temp detection
- `app/services/advanced_features.py` - Zone penalty/bonus under cold north wind
- `app/services/scoring_service.py` - Passes wind/temp to all modified functions

**Total Changes:** ~500 lines (new module + modifications)

**Note:** Does NOT change base bite scores, only expected depth behavior and summary phrasing

### v2.7.0 (Nov 27, 2025) - UI REDESIGN: UNIFIED LOG CARDS + DETAIL MODALS
**Complete UI overhaul for logging system with two-line card format and interactive modals**

**A) Removed Forecast Confidence Display:**
- Removed "Forecast Confidence" section from Current Conditions panel
- Commented out confidence badge population in dashboard.js (lines 288-296)
- Layout collapses cleanly with no empty space

**B) Unified Log Layouts:**
- Converted Fish Log from table-based to card-based layout
- Replaced `<table class="catches-table">` with `<div id="catchesList" class="catches-list">`
- All three logs (Fish, Bait, Predator) now use same card component family
- Consistent typography, spacing, colors across all log types

**C) Two-Line Card Format:**
Standardized display format across all three logs:
- **Line 1:** `TIME – Zone X` (e.g., "4:14 PM – Zone 2")
- **Line 2:** `QTY Species – Descriptor`
  - Fish Log: descriptor = size class (Small/Keeper/Big)
  - Bait Log: descriptor = method (cast net, trap, etc.)
  - Predator Log: descriptor = behavior (cruising, feeding, etc.)

**D) Entry Detail Modals:**
- **Fish Log Modal:** Date/Time, Zone, Quantity, Length, Bait, Rig, Status (Kept/Released), Notes
- **Bait Log Modal:** Date/Time, Zone, Quantity, Method, Structure, Notes
- **Predator Log Modal:** Date/Time, Zone, Behavior, Tide, Notes
- Click any log entry card to open modal with full details
- Unified modal styling across all three log types
- Added modal HTML structures (lines 860-979 in index.html)

**Files Changed:**
- `app/templates/index.html` - Removed confidence section (lines 244-253), Fish Log table → div (line 535), Added 3 modal structures (lines 860-979)
- `app/static/js/dashboard.js` - Commented out confidence code (lines 288-296)
- `app/static/js/fishing_log.js` - New card rendering with modal functionality (lines 270-369)
- `app/static/js/logging_tabs.js` - Updated Bait/Predator cards with modals (lines 336-509)

**Total Changes:** ~350 lines modified/added

### v2.6.0 (Nov 27, 2025) - LOG SYSTEM OVERHAUL + BAIT CARDS
**Complete log form restructuring, CST timezone handling, and weather-style bait forecast**

**Log System Changes:**
- **Field Order Restructuring:** All three logs (Fish, Bait, Predator) reorganized for mobile-first UX
- **Required Fields:** Species and Zone now required on all logs
- **Removed Fields:** Tide input removed (auto-logged from timestamp), Predator seen removed from Fish Log
- **Renamed Fields:** "Presentation" → "Rig" across all interfaces
- **Auto-Logging:** Tide state automatically captured based on timestamp for all log types

**Timezone Fixes:**
- **CST Native:** All timestamp inputs treated as CST (Central Standard Time)
- **Added `central_to_utc()`:** New utility function converts CST input to UTC for storage
- **Display Consistency:** All displayed times show in CST with proper conversion
- **Fixed Endpoints:** Updated Fish, Bait, and Predator log endpoints for CST handling

**Bait Forecast Enhancement:**
- **Weather-Style Cards:** Full-width cards with tier badges (Excellent/Good/Fair/Poor)
- **Bait Species:** Focused on 5 species: Menhaden, Shrimp, Pinfish, Mud Minnows, Fiddler Crabs
- **Card Layout:** Left side (tier badge + name), Right side (condition line + how-to-catch)
- **Modal Details:** Tap cards to open detailed modals with: Overview, Where to Find, How to Catch, Best Use, Tips
- **JavaScript:** New `bait_forecast.js` with card rendering and modal system

**Database Migrations:**
- **bait_logs Schema:** Updated to match new spec (timestamp, zone_id, method, quantity_estimate)
- **Environment Snapshot Fields:** Added full environment tracking to bait_logs (tide, weather, etc.)
- **Migration Script:** `migrate_bait_logs.py` for safe schema updates

**Files Changed:**
- `app/templates/index.html` - Log form restructuring (Fish: 373-511, Bait: 581-659, Predator: 680-732)
- `app/static/js/bait_forecast.js` - New bait card rendering and modals
- `app/static/js/logging_tabs.js` - Updated form handlers for new fields
- `app/static/css/style.css` - Weather-style bait card CSS
- `app/main.py` - Updated all log endpoints (lines 649-653, 923-927, 1058-1062)
- `app/utils/timezone.py` - Added `central_to_utc()` function
- `app/services/tide_service.py` - Added `get_tide_state_for_timestamp()`
- `migrate_bait_logs.py` - Database migration script

**Total Changes:** ~800 lines

### v2.5.0 (Nov 25, 2025) - BEHAVIOR SPEC
**Complete species behavior system with tier-based scoring**

**New Files:**
- `species_tiers.py` - Tier classification
- `species_behavior_profiles.py` - Comprehensive profiles (417 lines)
- `confidence_scoring.py` - Data quality scoring

**Rewritten:**
- `hyperlocal_scoring.py` - Full behavior spec formula (520 lines)
- `bait_scoring.py` - Enhanced bait scoring (317 lines)

**Key Features:**
- Tier 1 species: Full analytics (7 components)
- Tier 2 species: Simplified scoring
- Species-specific environmental preferences
- 25% hourly decay on recent activity
- Confidence-weighted scoring (LOW/MED/HIGH)
- Predator penalty system (-8 base, 4hr decay)
- Enhanced bait scoring with zone/light bonuses

**Total Changes:** ~1,500 lines

### v2.4.1 (Nov 25, 2025) - CANONICAL ZONE GEOMETRY
**Final zone layout with structure-aware scoring**

**Changes:**
- Walkway orientation: EAST-WEST
- Zone positions: 1,3 North | 2,4 South | 5 East
- Structure details: Pilings (Zones 1,3,5), Rubble (Zone 1), Light (Zone 4)
- Zone-specific structure bonuses by species
- Nighttime Zone 4 light bonus (+3-4)
- Flounder/drum rubble bonus Zone 1 (+4)
- Confidence levels by zone (3,4 HIGH | 5 LOW)

### v2.4.0 (Nov 24, 2025) - HYPERLOCAL SPEC
**Zone-specific bite scores with UglyFishing baseline**

**Changes:**
- Seasonal baseline from UglyFishing calendar (0-90)
- Environmental adjustments (-35 to +15)
- Recent activity with decay (0-10)
- Predator penalties (0 to -20)
- Zone-specific tracking for all modifiers

### v2.3.0 (Nov 23, 2025) - LEARNING LAYER
**Adaptive system with bucket-based deltas**

**Features:**
- Catch data bucketing by conditions
- Daily decay on learned adjustments
- Bucket-specific modifiers
- Confidence thresholds (≥5 catches)

### v2.2.0 (Nov 21-22, 2025) - UI/UX OVERHAUL
**Dark theme + advanced features**

**Changes:**
- Tier system (HOT/DECENT/SLOW/UNLIKELY)
- Zone 1-5 system (replaced compass directions)
- Dark theme by default
- Behavior cheat sheets
- Weekly summaries
- Advanced features: clarity, confidence, rig recommendations
- Pro tips system

---

## Key Contacts

**Server:** evooffice (Ubuntu, AT&T Fiber)
**Location:** Belle Fontaine, Mobile Bay (30.488192, -88.102113)
**GitHub:** (if tracking in git)

---

**Last Updated:** November 28, 2025
**Version:** 2.8.0
**Status:** Production - Cold North Wind Penalty System Active
