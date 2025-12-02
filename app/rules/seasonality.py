"""Species seasonality data for Mobile Bay / Gulf Coast.

Running factor scale:
- 0.0 = Essentially absent
- 0.3 = Present but low numbers
- 0.6 = Decent presence
- 1.0 = Peak season
"""
from datetime import datetime
from typing import Dict

# Month indices: 1=Jan, 2=Feb, ..., 12=Dec
# Rating scale: 0.0=N/A, 0.2=poor, 0.4=fair, 0.6=good, 0.8=great, 1.0=excellent
SPECIES_SEASONALITY: Dict[str, Dict[int, float]] = {
    "speckled_trout": {
        1: 1.0,   # Jan - excellent
        2: 0.6,   # Feb - good
        3: 0.8,   # Mar - great
        4: 0.8,   # Apr - great
        5: 1.0,   # May - excellent
        6: 1.0,   # Jun - excellent
        7: 1.0,   # Jul - excellent
        8: 0.6,   # Aug - good
        9: 0.4,   # Sep - fair
        10: 0.6,  # Oct - good
        11: 1.0,  # Nov - excellent
        12: 1.0,  # Dec - excellent
    },
    "redfish": {
        1: 1.0,   # Jan - excellent
        2: 0.6,   # Feb - good
        3: 0.8,   # Mar - great
        4: 0.8,   # Apr - great
        5: 1.0,   # May - excellent
        6: 1.0,   # Jun - excellent
        7: 1.0,   # Jul - excellent
        8: 0.6,   # Aug - good
        9: 0.6,   # Sep - good
        10: 0.8,  # Oct - great
        11: 0.8,  # Nov - great
        12: 0.8,  # Dec - great
    },
    "flounder": {
        1: 0.2,   # Jan - poor
        2: 0.6,   # Feb - good
        3: 0.8,   # Mar - great
        4: 1.0,   # Apr - excellent
        5: 1.0,   # May - excellent
        6: 0.8,   # Jun - great
        7: 0.8,   # Jul - great
        8: 0.6,   # Aug - good
        9: 0.6,   # Sep - good
        10: 1.0,  # Oct - excellent
        11: 1.0,  # Nov - excellent
        12: 0.6,  # Dec - good
    },
    "sheepshead": {
        1: 0.8,   # Jan - great
        2: 0.8,   # Feb - great
        3: 1.0,   # Mar - excellent
        4: 1.0,   # Apr - excellent
        5: 0.8,   # May - great
        6: 0.4,   # Jun - fair
        7: 0.4,   # Jul - fair
        8: 0.4,   # Aug - fair
        9: 0.6,   # Sep - good
        10: 0.8,  # Oct - great
        11: 1.0,  # Nov - excellent
        12: 1.0,  # Dec - excellent
    },
    "mullet": {
        1: 0.4,   # Jan - Present, slower
        2: 0.4,   # Feb - Present, slower
        3: 0.6,   # Mar - Picking up
        4: 0.8,   # Apr - Spring
        5: 0.9,   # May - Active
        6: 1.0,   # Jun - Peak summer
        7: 1.0,   # Jul - Peak summer
        8: 1.0,   # Aug - Peak summer
        9: 1.0,   # Sep - Fall run
        10: 1.0,  # Oct - Fall run (big schools)
        11: 0.8,  # Nov - Slowing
        12: 0.5,  # Dec - Winter slowdown
    },
    "mackerel": {
        1: 0.0,   # Jan - N/A
        2: 0.0,   # Feb - N/A
        3: 0.0,   # Mar - N/A
        4: 0.2,   # Apr - poor
        5: 0.6,   # May - good
        6: 0.8,   # Jun - great
        7: 1.0,   # Jul - excellent
        8: 1.0,   # Aug - excellent
        9: 0.8,   # Sep - great
        10: 0.8,  # Oct - great
        11: 0.4,  # Nov - fair
        12: 0.0,  # Dec - N/A
    },
    "croaker": {
        1: 0.3,   # Jan - Low
        2: 0.3,   # Feb - Low
        3: 0.5,   # Mar - Spring arrival
        4: 0.7,   # Apr - Building
        5: 0.9,   # May - Good numbers
        6: 1.0,   # Jun - Peak summer
        7: 1.0,   # Jul - Peak summer
        8: 1.0,   # Aug - Peak summer
        9: 0.9,   # Sep - Fall, good
        10: 0.7,  # Oct - Slowing
        11: 0.5,  # Nov - Declining
        12: 0.3,  # Dec - Winter low
    },
    "stingray": {
        1: 0.3,   # Jan - Cold, less active
        2: 0.3,   # Feb - Cold, less active
        3: 0.5,   # Mar - Warming up
        4: 0.7,   # Apr - More active
        5: 0.9,   # May - Active
        6: 1.0,   # Jun - Peak warm season
        7: 1.0,   # Jul - Peak warm season
        8: 1.0,   # Aug - Peak warm season
        9: 0.9,   # Sep - Still active
        10: 0.7,  # Oct - Cooling
        11: 0.5,  # Nov - Less active
        12: 0.4,  # Dec - Winter low
    },
    "shark": {
        1: 0.2,   # Jan - Rare, cold water
        2: 0.2,   # Feb - Rare, cold water
        3: 0.3,   # Mar - Rare, but warm fronts can bring them
        4: 0.6,   # Apr - Spring arrival with warming water
        5: 0.8,   # May - More common
        6: 1.0,   # Jun - Peak summer presence
        7: 1.0,   # Jul - Peak summer presence
        8: 1.0,   # Aug - Peak summer presence
        9: 0.9,   # Sep - Still very active
        10: 0.7,  # Oct - Present but declining
        11: 0.3,  # Nov - Mostly gone, cold water
        12: 0.2,  # Dec - Rare, cold water
    },
    "black_drum": {
        1: 0.8,   # Jan - great
        2: 0.6,   # Feb - good
        3: 0.8,   # Mar - great
        4: 0.8,   # Apr - great
        5: 0.8,   # May - great
        6: 0.8,   # Jun - great
        7: 1.0,   # Jul - excellent
        8: 0.6,   # Aug - good
        9: 0.8,   # Sep - great
        10: 1.0,  # Oct - excellent
        11: 1.0,  # Nov - excellent
        12: 1.0,  # Dec - excellent
    },
    "tripletail": {
        1: 0.0,   # Jan - N/A
        2: 0.0,   # Feb - N/A
        3: 0.0,   # Mar - N/A
        4: 0.2,   # Apr - poor
        5: 0.6,   # May - good
        6: 1.0,   # Jun - excellent
        7: 1.0,   # Jul - excellent
        8: 1.0,   # Aug - excellent
        9: 0.8,   # Sep - great
        10: 0.8,  # Oct - great
        11: 0.6,  # Nov - good
        12: 0.0,  # Dec - N/A
    },
    "jack_crevalle": {
        1: 0.0,   # Jan - N/A
        2: 0.0,   # Feb - N/A
        3: 0.0,   # Mar - N/A
        4: 0.2,   # Apr - poor
        5: 0.4,   # May - fair
        6: 0.8,   # Jun - great
        7: 1.0,   # Jul - excellent
        8: 1.0,   # Aug - excellent
        9: 1.0,   # Sep - excellent
        10: 1.0,  # Oct - excellent
        11: 0.6,  # Nov - good
        12: 0.0,  # Dec - N/A
    },
    "white_trout": {
        1: 0.8,   # Jan - great
        2: 0.6,   # Feb - good
        3: 0.6,   # Mar - good
        4: 0.6,   # Apr - good
        5: 0.8,   # May - great
        6: 0.8,   # Jun - great
        7: 1.0,   # Jul - excellent
        8: 0.6,   # Aug - good
        9: 0.8,   # Sep - great
        10: 0.8,  # Oct - great
        11: 0.8,  # Nov - great
        12: 0.8,  # Dec - great
    },
    "blue_crab": {
        1: 0.2,   # Jan - poor
        2: 0.2,   # Feb - poor
        3: 0.4,   # Mar - fair
        4: 0.6,   # Apr - good
        5: 0.8,   # May - great
        6: 1.0,   # Jun - excellent
        7: 1.0,   # Jul - excellent
        8: 1.0,   # Aug - excellent
        9: 0.8,   # Sep - great
        10: 0.6,  # Oct - good
        11: 0.4,  # Nov - fair
        12: 0.2,  # Dec - poor
    },
}

# List of all species tracked
SPECIES_LIST = list(SPECIES_SEASONALITY.keys())


def get_running_factor(species: str, date: datetime = None) -> float:
    """
    Get the seasonal running factor for a species on a given date.

    Args:
        species: Species name (use underscores, e.g., 'speckled_trout')
        date: Date to check (defaults to today)

    Returns:
        Running factor from 0.0 to 1.0
    """
    if date is None:
        date = datetime.now()

    species_key = species.lower().replace(' ', '_')

    if species_key not in SPECIES_SEASONALITY:
        return 0.0

    month = date.month
    return SPECIES_SEASONALITY[species_key].get(month, 0.0)


def is_species_running(species: str, date: datetime = None, threshold: float = 0.4) -> bool:
    """
    Check if a species is considered 'running' (seasonally present).

    Args:
        species: Species name
        date: Date to check (defaults to today)
        threshold: Minimum running factor to be considered 'running' (default 0.4 = fair or better)

    Returns:
        True if running factor >= threshold
    """
    return get_running_factor(species, date) >= threshold


def get_species_display_name(species: str) -> str:
    """Convert species key to display name."""
    display_names = {
        "speckled_trout": "Speckled Trout",
        "redfish": "Redfish",
        "flounder": "Flounder",
        "sheepshead": "Sheepshead",
        "mullet": "Mullet",
        "mackerel": "Mackerel",
        "croaker": "Croaker",
        "stingray": "Stingray",
        "shark": "Shark",
        "black_drum": "Black Drum",
        "tripletail": "Tripletail (Blackfish)",
        "jack_crevalle": "Jack Crevalle",
        "white_trout": "White Trout",
        "blue_crab": "Blue Crab"
    }
    return display_names.get(species, species.replace('_', ' ').title())
