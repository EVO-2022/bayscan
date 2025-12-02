# BayScan Hyperlocal Spec - Quick Start Guide

## 🎯 What's Ready to Use

✅ **New Scoring Engine** - Zone-specific bite scores with UglyFishing scale
✅ **Environment Snapshots** - Automated capture system
✅ **Database Schema** - Updated with all new required fields
✅ **Migration Script** - Safe database upgrade path
✅ **Documentation** - Full implementation details

## 🚀 Quick Deploy (If You Want to Test What's Built)

### 1. Back Up Your Database
```bash
cd /home/evo/fishing-forecast
cp app/bayscan.db app/bayscan.db.backup.$(date +%Y%m%d_%H%M%S)
```

### 2. Run Migration
```bash
python3 migrate_hyperlocal_spec.py
```

Type "yes" when prompted. This will:
- Create environment_snapshots table
- Add new columns to catches and bait_logs
- Migrate existing data safely
- Set default zones for old records

### 3. Restart Service (After Migration)
```bash
sudo systemctl restart bayscan.service
sudo journalctl -u bayscan.service -f
```

## 📊 Testing New Scoring Engine

You can test the new hyperlocal scoring engine directly in Python:

```python
from app.database import SessionLocal
from app.services.hyperlocal_scoring import calculate_zone_bite_score
from datetime import datetime

db = SessionLocal()

# Test conditions
conditions = {
    'water_temperature': 68.0,
    'tide_stage': 'incoming',
    'current_speed': 0.6,
    'wind_speed': 8.0,
    'wind_direction': 'NE',
    'time_of_day': 'morning',
    'barometric_pressure': 1015.0
}

# Calculate score for Speckled Trout in Zone 3
result = calculate_zone_bite_score(
    db=db,
    species='speckled_trout',
    zone_id='Zone 3',
    conditions=conditions,
    date=datetime.now()
)

print(f"Bite Score: {result['bite_score']}")
print(f"Seasonal Baseline: {result['seasonal_baseline']}")
print(f"Environmental Adjustment: {result['environmental_adjustment']}")
print(f"Recent Activity Bonus: {result['recent_activity_bonus']}")
print(f"Predator Penalty: {result['predator_penalty']}")
print(f"Breakdown: {result['breakdown']}")

db.close()
```

## 📋 What's NOT Yet Implemented

❌ API endpoints don't use new scoring yet (still use old system)
❌ Frontend forms don't have new fields yet
❌ Environment snapshots aren't being captured automatically yet
❌ Fish/Bait tab separation not in UI yet

**The new backend is built but not connected to the live API/UI.**

## 📁 Key Files

### Documentation
- `IMPLEMENTATION_SUMMARY.md` - High-level overview of what's done
- `HYPERLOCAL_SPEC_IMPLEMENTATION.md` - Detailed technical specs
- `QUICK_START.md` - This file

### New Backend Code
- `app/rules/uglyfishing_calendar.py` - Seasonal baseline calculator
- `app/services/hyperlocal_scoring.py` - New scoring engine
- `app/services/environment_snapshot.py` - Snapshot capture service

### Migration
- `migrate_hyperlocal_spec.py` - Database migration script

### Updated
- `app/models/schemas.py` - Database models with new fields

### Need Updates (Next Session)
- `app/main.py` - API endpoints
- `app/scheduler.py` - Add snapshot capture
- `app/templates/index.html` - UI updates
- `app/static/js/fishing_log.js` - Form updates

## 🧪 Verify Migration Worked

After running migration, check the database:

```bash
sqlite3 app/bayscan.db "PRAGMA table_info(catches);" | grep -E "zone_id|bait_used|presentation"
```

Should show the new columns.

Check environment_snapshots table exists:
```bash
sqlite3 app/bayscan.db "SELECT name FROM sqlite_master WHERE type='table' AND name='environment_snapshots';"
```

Should return: `environment_snapshots`

## 💡 Key Concepts

### Zone-Specific Scores
Every bite score is now for a specific zone:
- "Speckled Trout in Zone 3" gets its own score
- Recent catches in Zone 3 boost Zone 3 scores only
- Predators in Zone 4 only affect Zone 4 scores

### UglyFishing Scale
Seasonal baselines use this scale:
- N/A = 0
- Poor = 20
- Fair = 40
- Good = 60
- Great = 80
- Excellent = 90

Environmental factors can add up to +10 or subtract up to -30.

### Time Decay
Recent catches boost scores with decay:
- Last 2 hours: +2 points each
- 2-4 hours ago: +1 point each
- 4-6 hours ago: +0.5 points each

Predators create penalties with sharp decay:
- Last hour: -20 points
- 1-2 hours: -15 points
- 2-3 hours: -10 points
- 3-4 hours: -5 points

### Bait vs Fish
Bait species are separated:
- Fish: speckled_trout, redfish, flounder, sheepshead, black_drum, etc.
- Bait: live_shrimp, menhaden, pinfish, fiddler_crab, mullet (for catching)

## 🔧 If You Want to Continue Implementation

Next logical step is updating the API in `app/main.py`:

1. Update `CatchCreate` model with new fields
2. Update `POST /api/catches` to capture environment snapshot
3. Update `GET /api/current` to use hyperlocal scoring
4. Update scheduler to capture snapshots every 10 minutes

Then move to frontend forms.

## ❓ Questions?

Read the detailed docs:
- `IMPLEMENTATION_SUMMARY.md` - What's done and what's next
- `HYPERLOCAL_SPEC_IMPLEMENTATION.md` - Full technical details

---

**Status**: Backend infrastructure complete, ready for integration
**Safe to Deploy**: Yes, migration is safe and backs up data
**Ready to Use**: Not yet - needs API/UI integration to go live
