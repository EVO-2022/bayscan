"""SQLAlchemy models for database tables."""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class TideData(Base):
    """Stores tide predictions and observations."""
    __tablename__ = "tide_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    height = Column(Float, nullable=False)  # Tide height in feet
    tide_type = Column(String(10))  # 'H' for high, 'L' for low, or null
    is_prediction = Column(Boolean, default=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class WeatherData(Base):
    """Stores weather observations and forecasts."""
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float)  # Air temperature in Fahrenheit
    water_temperature = Column(Float, nullable=True)  # Water temperature in Fahrenheit (from NOAA)
    wind_speed = Column(Float)  # mph
    wind_direction = Column(String(10))  # N, NE, E, etc.
    wind_gust = Column(Float)  # mph
    pressure = Column(Float)  # millibars or inHg
    pressure_trend = Column(String(10))  # 'rising', 'falling', 'stable'
    humidity = Column(Float)  # percentage
    cloud_cover = Column(String(20))  # 'clear', 'partly_cloudy', 'overcast'
    precipitation_probability = Column(Float)  # percentage
    conditions = Column(String(100))  # Short forecast text
    is_forecast = Column(Boolean, default=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class AstronomicalData(Base):
    """Stores sun and moon data."""
    __tablename__ = "astronomical_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True, unique=True)
    sunrise = Column(DateTime, nullable=False)
    sunset = Column(DateTime, nullable=False)
    moon_phase = Column(Float)  # 0-1, where 0=new, 0.5=full
    moon_phase_name = Column(String(20))  # 'New', 'Waxing Crescent', etc.
    fetched_at = Column(DateTime, default=datetime.utcnow)


class ForecastWindow(Base):
    """Stores 2-hour forecast windows."""
    __tablename__ = "forecast_windows"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    overall_score = Column(Float)  # 0-100 overall bite score
    tide_state = Column(String(20))  # 'rising', 'falling', 'slack'
    tide_height_avg = Column(Float)
    time_of_day = Column(String(10))  # 'night', 'dawn', 'day', 'dusk'
    pressure_trend = Column(String(10))
    wind_speed = Column(Float)
    temperature = Column(Float)  # Air temperature in Fahrenheit
    water_temperature = Column(Float, nullable=True)  # Water temperature in Fahrenheit (from NOAA)
    conditions_summary = Column(Text)
    computed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to species forecasts
    species_forecasts = relationship("SpeciesForecast", back_populates="window", cascade="all, delete-orphan")


class SpeciesForecast(Base):
    """Stores per-species forecast for a time window."""
    __tablename__ = "species_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    window_id = Column(Integer, ForeignKey('forecast_windows.id'), nullable=False)
    species = Column(String(50), nullable=False, index=True)
    is_running = Column(Boolean)  # Is the species seasonally present?
    running_factor = Column(Float)  # 0-1 seasonal factor
    bite_score = Column(Float)  # 0-100
    bite_label = Column(String(20))  # 'Unlikely', 'Slow', 'Decent', 'Hot'

    # Relationship to window
    window = relationship("ForecastWindow", back_populates="species_forecasts")


class Alert(Base):
    """Stores active alerts for hot fishing conditions."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String(50), nullable=False, index=True)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    bite_score = Column(Float)
    message = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    dismissed_at = Column(DateTime, nullable=True)


class Catch(Base):
    """Stores fishing log catches with full environment snapshot."""
    __tablename__ = "catches"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    species = Column(String(50), nullable=False, index=True)

    # Location and depth details (NEW SPEC)
    zone_id = Column(String(20), nullable=False, index=True)  # Zone 1-5
    distance_from_dock = Column(String(20), nullable=True)  # at dock, 50-100 ft, 100-150 ft, 150+ ft
    depth_estimate = Column(String(20), nullable=True)  # shallow, medium, deep
    structure_type = Column(String(50), nullable=True)  # pilings, grass edge, open water, channel edge

    # Size and catch details
    size_length_in = Column(Integer, nullable=True)  # Length in inches
    size_bucket = Column(String(20), nullable=True)  # 'small', 'keeper', 'big'
    quantity = Column(Integer, default=1)  # Number of fish caught (for batch logging)
    kept = Column(Boolean, default=False)  # True=kept, False=released

    # Bait and presentation (NEW SPEC)
    bait_used = Column(String(100), nullable=True)  # Replaces bait_type
    presentation = Column(String(100), nullable=True)  # DEPRECATED - use rig_type
    rig_type = Column(String(50), nullable=True)  # popping_cork, jig, carolina_rig, bottom_rig, free_line, etc.

    # Predator activity flag (NEW SPEC)
    predator_seen_recently = Column(Boolean, default=False)  # Yes/No if predator was seen recently

    notes = Column(Text, nullable=True)

    # Trap-specific field (for crab traps, bait traps, etc.)
    days_since_last_checked = Column(Integer, nullable=True)  # Days between setting and checking trap

    # Full environment snapshot (EXPANDED)
    water_temp = Column(Float, nullable=True)  # Water temperature
    air_temp = Column(Float, nullable=True)  # Air temperature
    humidity = Column(Float, nullable=True)  # Humidity percentage
    barometric_pressure = Column(Float, nullable=True)  # Pressure in millibars
    tide_height = Column(Float, nullable=True)  # Tide height in feet
    tide_stage = Column(String(20), nullable=True)  # incoming, outgoing, slack, high, low
    current_speed = Column(Float, nullable=True)  # Current speed
    current_direction = Column(String(10), nullable=True)  # Current direction
    wind_speed = Column(Float, nullable=True)  # Wind speed mph
    wind_direction = Column(String(10), nullable=True)  # Wind direction
    weather = Column(String(50), nullable=True)  # clear, cloudy, rain, storm
    time_of_day = Column(String(20), nullable=True)  # pre-dawn, morning, midday, evening, night
    moon_phase = Column(Float, nullable=True)  # 0-1 moon phase
    dock_lights_on = Column(Boolean, default=False)  # Whether dock lights were on

    created_at = Column(DateTime, default=datetime.utcnow)


class MarineCondition(Base):
    """Stores marine forecast and safety data."""
    __tablename__ = "marine_conditions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    wave_height = Column(Float, nullable=True)  # Feet
    wave_height_text = Column(String(50), nullable=True)  # Text description if no numeric
    sea_state = Column(String(50), nullable=True)  # 'calm', 'light chop', 'choppy', etc.
    marine_summary = Column(Text, nullable=True)  # NWS marine forecast text

    # Safety scoring
    safety_score = Column(Integer, default=100)  # 0-100
    safety_level = Column(String(20), default='SAFE')  # 'SAFE', 'CAUTION', 'UNSAFE'

    # Hazard flags
    hazard_level = Column(String(20), default='NONE')  # 'NONE', 'CAUTION', 'DANGEROUS'
    small_craft_advisory = Column(Boolean, default=False)
    gale_warning = Column(Boolean, default=False)
    thunderstorm_warning = Column(Boolean, default=False)
    hazard_raw = Column(Text, nullable=True)  # Raw NWS alert text

    # Additional marine data
    wind_gust = Column(Float, nullable=True)
    visibility = Column(Float, nullable=True)  # Nautical miles

    is_forecast = Column(Boolean, default=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class BaitLog(Base):
    """Stores bait catching logs with full environment snapshot."""
    __tablename__ = "bait_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    bait_species = Column(String(50), nullable=False, index=True)  # shrimp, menhaden, mullet, fiddler, pinfish
    method = Column(String(50), nullable=False)  # cast net, trap
    quantity_estimate = Column(String(20), nullable=True)  # none, few, plenty
    zone_id = Column(String(20), nullable=False, index=True)  # Zone 1-5
    structure_type = Column(String(50), nullable=True)  # pilings, grass edge, open water, channel edge
    notes = Column(Text, nullable=True)

    # Trap-specific field (for bait traps - minnow traps, pinfish traps, etc.)
    days_since_last_checked = Column(Integer, nullable=True)  # Days between setting and checking trap

    # Full environment snapshot (matches Catch model)
    water_temp = Column(Float, nullable=True)
    air_temp = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    barometric_pressure = Column(Float, nullable=True)
    tide_height = Column(Float, nullable=True)
    tide_stage = Column(String(20), nullable=True)
    current_speed = Column(Float, nullable=True)
    current_direction = Column(String(10), nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(String(10), nullable=True)
    weather = Column(String(50), nullable=True)
    time_of_day = Column(String(20), nullable=True)
    moon_phase = Column(Float, nullable=True)
    dock_lights_on = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class PredatorLog(Base):
    """Stores predator sighting logs."""
    __tablename__ = "predator_logs"

    id = Column(Integer, primary_key=True, index=True)
    predator = Column(String(20), nullable=False, index=True)  # dolphin, shark
    zone = Column(String(20), nullable=False)  # Zone 1-5
    time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    behavior = Column(String(50), nullable=False)  # cruising, feeding, chasing bait, busting surface
    tide = Column(String(20), nullable=True)  # low, rising, high, falling
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningBucket(Base):
    """Stores learning deltas for species/zone/tide/time combinations."""
    __tablename__ = "learning_buckets"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String(50), nullable=False, index=True)
    zone = Column(String(20), nullable=False, index=True)
    tide_stage = Column(String(20), nullable=False)  # low, rising, high, falling
    time_of_day_block = Column(String(20), nullable=False)  # morning, midday, evening
    delta = Column(Float, default=0.0)  # Adjustment delta (-0.3 to +0.3)
    confidence = Column(Float, default=0.5)  # Confidence score (0-1)
    sample_count = Column(Integer, default=0)  # Number of sessions in this bucket
    last_adjustment = Column(DateTime, nullable=True)  # Last time delta was adjusted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EnvironmentSnapshot(Base):
    """Stores environment snapshots every 5-15 minutes for learning no-bite conditions."""
    __tablename__ = "environment_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Environment data
    water_temp = Column(Float, nullable=True)
    air_temp = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    barometric_pressure = Column(Float, nullable=True)
    tide_height = Column(Float, nullable=True)
    tide_stage = Column(String(20), nullable=True)  # incoming, outgoing, slack, high, low
    current_speed = Column(Float, nullable=True)
    current_direction = Column(String(10), nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(String(10), nullable=True)
    weather = Column(String(50), nullable=True)  # clear, cloudy, rain, storm
    time_of_day = Column(String(20), nullable=True)  # pre-dawn, morning, midday, evening, night
    moon_phase = Column(Float, nullable=True)
    dock_lights_on = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# LAYER 2: DERIVED STATE (CACHED SCORES & LEARNING)
# ============================================================================

class BiteScore(Base):
    """Cached bite scores per species+zone - recalculated on events."""
    __tablename__ = "bite_scores"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String(50), nullable=False, index=True)
    zone_id = Column(String(20), nullable=False, index=True)
    score = Column(Float, nullable=False)  # 0-100
    rating = Column(String(20), nullable=False)  # Poor/Fair/Good/Great/Excellent
    confidence = Column(String(20), nullable=False)  # low/medium/high
    reason_summary = Column(Text, nullable=True)  # Short explanation
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Add unique constraint for species+zone_id
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class BaitScore(Base):
    """Cached bait scores per bait_species+zone - recalculated on events."""
    __tablename__ = "bait_scores"

    id = Column(Integer, primary_key=True, index=True)
    bait_species = Column(String(50), nullable=False, index=True)
    zone_id = Column(String(20), nullable=False, index=True)
    score = Column(Float, nullable=False)  # 0-100 internal
    rating = Column(String(20), nullable=False)  # Poor/Fair/Good/Great/Excellent
    reason_summary = Column(Text, nullable=True)  # Short explanation
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class RigEffect(Base):
    """Tracks which rigs work best per species+zone."""
    __tablename__ = "rig_effects"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String(50), nullable=False, index=True)
    zone_id = Column(String(20), nullable=False, index=True)
    rig_type = Column(String(50), nullable=False, index=True)  # popping_cork, jig, carolina_rig, bottom_rig, free_line
    success_count = Column(Integer, default=0)
    weight = Column(Float, default=0.0)  # 0-3, computed from success_count
    last_used = Column(DateTime, nullable=True)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class ZoneConditionEffect(Base):
    """Tracks condition effectiveness per species+zone."""
    __tablename__ = "zone_condition_effects"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String(50), nullable=False, index=True)
    zone_id = Column(String(20), nullable=False, index=True)
    tide_band = Column(String(20), nullable=False)  # incoming/outgoing/slack
    clarity_band = Column(String(20), nullable=False)  # clean/stained/muddy
    wind_band = Column(String(20), nullable=False)  # favorable/neutral/unfavorable
    current_band = Column(String(20), nullable=False)  # low/medium/high
    success_count = Column(Integer, default=0)
    weight = Column(Float, default=0.0)  # 0-4, computed from success_count

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class RigConditionEffect(Base):
    """Tracks rig effectiveness under specific conditions."""
    __tablename__ = "rig_condition_effects"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String(50), nullable=False, index=True)
    rig_type = Column(String(50), nullable=False, index=True)
    tide_band = Column(String(20), nullable=False)  # incoming/outgoing/slack
    clarity_band = Column(String(20), nullable=False)  # clean/stained/muddy
    success_count = Column(Integer, default=0)
    weight = Column(Float, default=0.0)  # 0-4, computed from success_count

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class SpeciesZoneTip(Base):
    """Auto-generated fishing tips per species+zone."""
    __tablename__ = "species_zone_tips"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String(50), nullable=False, index=True)
    zone_id = Column(String(20), nullable=False, index=True)
    tip_text = Column(Text, nullable=False)  # Human-readable recommendation
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


# ============================================================================
# LAYER 3: SUPPORT / CONFIG
# ============================================================================

class Zone(Base):
    """Static zone metadata - 5 zones at Belle Fontaine dock."""
    __tablename__ = "zones"

    id = Column(String(20), primary_key=True)  # Zone 1, Zone 2, etc.
    name = Column(String(50), nullable=False)
    depth_band = Column(String(20), nullable=False)  # shallow/medium/deep
    has_pilings = Column(Boolean, default=False)
    has_center_pilings = Column(Boolean, default=False)  # True for Zone 5 only
    has_rubble = Column(Boolean, default=False)  # True for Zone 1 only
    has_light = Column(Boolean, default=False)  # True for Zone 4 only
    description = Column(Text, nullable=True)


class Species(Base):
    """Species configuration and metadata."""
    __tablename__ = "species"

    id = Column(String(50), primary_key=True)  # species key like 'speckled_trout'
    name = Column(String(100), nullable=False)  # Display name
    tier = Column(Integer, nullable=False)  # 1 or 2
    category = Column(String(20), nullable=True)  # tier1_full, tier2_simplified, bait
