"""Species tier classification for BayScan.

TIER 1: Full analytics - main focus species with detailed scoring
TIER 2: Light analytics / support / bait with simplified scoring
"""

# Species tier definitions
TIER_1_SPECIES = [
    'speckled_trout',
    'redfish',
    'flounder',
    'sheepshead',
    'black_drum',
]

TIER_2_SPECIES = [
    'croaker',
    'white_trout',
    'menhaden',
    'mullet',
    'jack_crevalle',  # Primarily as predator event
    'blue_crab',  # Always present at dock
]

# Bait species (subset of Tier 2)
BAIT_SPECIES = [
    'menhaden',
    'mullet',
    'live_shrimp',
    'fiddler_crab',
]

# Predator species that trigger bite penalties for prey
PREDATOR_SPECIES = [
    'jack_crevalle',
    'shark',
    # Dolphins and bull reds logged via PredatorLog table
]


def get_species_tier(species_key: str) -> int:
    """
    Get tier number for a species.

    Args:
        species_key: Species identifier

    Returns:
        1 for Tier 1 (full analytics), 2 for Tier 2 (simplified)
    """
    if species_key in TIER_1_SPECIES:
        return 1
    elif species_key in TIER_2_SPECIES:
        return 2
    else:
        # Default to Tier 2 for unknown species
        return 2


def is_bait_species(species_key: str) -> bool:
    """Check if species is primarily a bait species."""
    return species_key in BAIT_SPECIES


def is_predator_species(species_key: str) -> bool:
    """Check if species triggers predator penalties."""
    return species_key in PREDATOR_SPECIES


def should_use_full_scoring(species_key: str) -> bool:
    """Check if species should use full detailed scoring."""
    return get_species_tier(species_key) == 1
