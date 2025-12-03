"""Location registry for BayScan multi-location support.

Defines all available fishing locations with their metadata.
This is the single source of truth for location definitions.
"""
from typing import Dict, List, Any

# Location registry - all supported fishing locations
LOCATIONS: Dict[str, Dict[str, Any]] = {
    "bellfontaine": {
        "id": "bellfontaine",
        "label": "Bellfontaine Dock",
        "region": "Mobile Bay – West Shore",
        "coords": {
            "latitude": 30.488192,
            "longitude": -88.102113
        },
        "status": "active",
        "description": "Private dock on Mobile Bay west shore with 5 fishing zones",
        "timezone": "America/Chicago",
        # NOAA station configuration
        "noaa": {
            "tide_prediction_station": "8735180",  # Bayou La Batre, AL
            "realtime_station": "8736897",         # Middle Bay Light, AL
            "marine_zone": "AMZ250"                # Coastal waters zone
        },
        # Zone count for this location
        "zone_count": 5
    },
    "river_landing": {
        "id": "river_landing",
        "label": "River Landing",
        "region": "Perdido River – Mid Section",
        "coords": {
            "latitude": 30.4500,   # Placeholder coordinates
            "longitude": -87.4500  # Placeholder coordinates
        },
        "status": "coming_soon",
        "description": "Freshwater fishing spot on Perdido River",
        "timezone": "America/Chicago",
        # NOAA station configuration (TBD)
        "noaa": {
            "tide_prediction_station": None,
            "realtime_station": None,
            "marine_zone": None
        },
        # Zone count for this location
        "zone_count": 0
    }
}


def get_location(location_id: str) -> Dict[str, Any]:
    """
    Get full metadata for a location.
    
    Args:
        location_id: Location identifier (e.g., 'bellfontaine')
        
    Returns:
        Location metadata dict, or None if not found
    """
    return LOCATIONS.get(location_id)


def get_all_locations() -> Dict[str, Dict[str, Any]]:
    """Get all locations in the registry."""
    return LOCATIONS


def get_active_locations() -> List[Dict[str, Any]]:
    """Get only locations with status 'active'."""
    return [loc for loc in LOCATIONS.values() if loc["status"] == "active"]


def get_location_ids() -> List[str]:
    """Get list of all valid location IDs."""
    return list(LOCATIONS.keys())


def is_valid_location(location_id: str) -> bool:
    """Check if a location ID exists in the registry."""
    return location_id in LOCATIONS


def is_location_active(location_id: str) -> bool:
    """Check if a location is active (not coming_soon)."""
    loc = LOCATIONS.get(location_id)
    return loc is not None and loc["status"] == "active"

