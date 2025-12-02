"""UglyFishing seasonal calendar for Mobile Bay species.

This module maps the existing 0-1.0 seasonal ratings to the UglyFishing scale:
- Poor = 20 (0.2 rating)
- Fair = 40 (0.4 rating)
- Good = 60 (0.6 rating)
- Great = 80 (0.8 rating)
- Excellent = 90 (1.0 rating)
- N/A = 0 (0.0 rating)

These become the seasonal baseline scores that environmental factors modify.
"""
from datetime import datetime
from typing import Dict


def get_seasonal_baseline_score(species: str, date: datetime = None) -> float:
    """
    Get the seasonal baseline score (0-100) for a species using UglyFishing scale.

    Args:
        species: Species name (use underscores, e.g., 'speckled_trout')
        date: Date to check (defaults to today)

    Returns:
        Baseline score from 0-90 based on seasonal rating
    """
    from app.rules.seasonality import get_running_factor

    if date is None:
        date = datetime.now()

    # Get the 0-1.0 running factor
    running_factor = get_running_factor(species, date)

    # Convert to UglyFishing scale
    return running_factor_to_baseline(running_factor)


def running_factor_to_baseline(running_factor: float) -> float:
    """
    Convert 0-1.0 running factor to UglyFishing baseline score.

    UglyFishing Scale:
    - 0.0 (N/A) → 0
    - 0.2 (Poor) → 20
    - 0.3 → 30
    - 0.4 (Fair) → 40
    - 0.5 → 50
    - 0.6 (Good) → 60
    - 0.7 → 70
    - 0.8 (Great) → 80
    - 0.9 → 85
    - 1.0 (Excellent) → 90
    """
    if running_factor <= 0.0:
        return 0.0
    elif running_factor <= 0.2:
        return 20.0
    elif running_factor <= 0.3:
        return 30.0
    elif running_factor <= 0.4:
        return 40.0
    elif running_factor <= 0.5:
        return 50.0
    elif running_factor <= 0.6:
        return 60.0
    elif running_factor <= 0.7:
        return 70.0
    elif running_factor <= 0.8:
        return 80.0
    elif running_factor <= 0.9:
        return 85.0
    else:  # 1.0
        return 90.0


def baseline_to_rating_label(baseline: float) -> str:
    """
    Convert baseline score to rating label.

    Args:
        baseline: Baseline score (0-90)

    Returns:
        Rating label: N/A, Poor, Fair, Good, Great, Excellent
    """
    if baseline <= 0:
        return "N/A"
    elif baseline <= 20:
        return "Poor"
    elif baseline <= 40:
        return "Fair"
    elif baseline <= 60:
        return "Good"
    elif baseline <= 80:
        return "Great"
    else:
        return "Excellent"


# Priority species tiers (for UI display)
TIER_1_SPECIES = [
    "speckled_trout",
    "redfish",
    "flounder",
    "sheepshead",
    "black_drum"
]

TIER_2_SPECIES = [
    "croaker",
    "white_trout",
    "jack_crevalle",
    "mullet"
]

# Bait species (should NOT appear in fish forecast)
BAIT_SPECIES = [
    "live_shrimp",      # Live Shrimp
    "menhaden",         # Menhaden / Pogies
    "live_bait_fish",   # Generic live bait fish
    "pinfish",          # Pinfish
    "fiddler_crab",     # Fiddler Crabs
]


def is_bait_species(species: str) -> bool:
    """Check if a species is a bait species (should not appear in fish forecast)."""
    return species.lower() in BAIT_SPECIES


def is_fish_species(species: str) -> bool:
    """Check if a species is a fish species (should appear in fish forecast)."""
    return not is_bait_species(species)


def get_species_tier(species: str) -> int:
    """
    Get the priority tier for a species (1 or 2).

    Args:
        species: Species name

    Returns:
        1 for priority species, 2 for tier 2, 0 for bait species
    """
    if species in TIER_1_SPECIES:
        return 1
    elif species in TIER_2_SPECIES:
        return 2
    elif species in BAIT_SPECIES:
        return 0  # Bait species
    else:
        return 2  # Default to tier 2
