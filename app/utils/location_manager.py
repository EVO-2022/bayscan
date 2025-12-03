"""Location state manager for BayScan multi-location support."""
import json
from pathlib import Path
from app.utils.location_registry import get_location_ids, is_valid_location

# Valid location IDs (derived from registry)
VALID_LOCATIONS = get_location_ids()

# Path to state file
STATE_FILE = Path(__file__).parent.parent / "data" / "location_state.json"


def get_current_location() -> str:
    """Get the current active location ID."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                return data.get("current_location", "bellfontaine")
    except (json.JSONDecodeError, IOError):
        pass
    return "bellfontaine"


def set_current_location(location_id: str) -> bool:
    """
    Set the current active location.
    
    Args:
        location_id: Must be one of VALID_LOCATIONS
        
    Returns:
        True if successful, False if invalid location
    """
    if not is_valid_location(location_id):
        return False
    
    # Ensure data directory exists
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"current_location": location_id}, f, indent=4)
        return True
    except IOError:
        return False

