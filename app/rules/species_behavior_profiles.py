"""Detailed species behavior profiles for BayScan.

Each Tier 1 species has comprehensive preferences for environmental conditions.
Tier 2 species have simplified profiles.
"""

# TIER 1 SPECIES PROFILES

SPECKLED_TROUT = {
    'tier': 1,
    'name': 'Speckled Trout',
    'peak_months': [3, 4, 5, 6, 7, 8, 9, 10],  # March-October
    'spawn_months': [4, 5, 6, 7, 8, 9],  # April-September

    # Temperature preferences
    'water_temp': {
        'ideal_min': 65,
        'ideal_max': 78,
        'workable_min': 58,
        'workable_max': 85,
        'bonus_in_ideal': 5,
        'penalty_out_of_workable': -4,
    },

    # Tide preferences (ranked by preference)
    'tide_stage': {
        'incoming': 4,   # Strong positive
        'outgoing': 2,   # Positive
        'high': 0,       # Neutral
        'low': 0,        # Neutral
        'slack': -4,     # Strong negative
    },

    # Current speed preferences
    'current_speed': {
        'ideal_min': 0.3,  # ft/s or mph depending on units
        'ideal_max': 1.5,
        'bonus_moving': 3,
        'penalty_slack': -3,
    },

    # Water clarity preferences
    'water_clarity': {
        'clear': 5,              # Strong positive
        'slightly_stained': 2,   # Slight positive
        'stained': -1,           # Slight negative
        'muddy': -6,             # Strong negative
        'chalky': -5,            # Strong negative
    },

    # Wind preferences (direction + speed)
    'wind': {
        'favorable_directions': ['SE', 'S', 'SW', 'E'],
        'unfavorable_directions': ['N', 'NW', 'NE'],  # Especially after cold front
        'light_ideal_max': 12,  # mph
        'bonus_favorable': 3,
        'penalty_unfavorable_strong': -4,  # N wind >15mph post-front
    },

    # Barometric pressure
    'pressure': {
        'falling': 3,        # Positive (pre-front feeding)
        'stable': 1,         # Slight positive
        'rising_slow': 0,    # Neutral
        'rising_fast': -3,   # Negative (post-front spike)
    },

    # Salinity preferences
    'salinity': {
        'preferred_min': 15,  # ppt
        'preferred_max': 30,
        'tolerant': True,
        'penalty_rapid_change': -2,
    },

    # Structure preferences
    'structure': {
        'grass_edges': 4,
        'pilings': 3,
        'drop_offs': 3,
        'current_seams': 4,
        'open_water': -1,
    },

    # Light sensitivity
    'light': {
        'green_light_night_bonus': 4,  # Zone 4 at night
        'requires_decent_clarity': True,  # Light bonus reduced in muddy water
    },

    # Time of day preferences
    'time_of_day': {
        'dawn': 3,
        'morning': 2,
        'midday': 0,
        'afternoon': 1,
        'evening': 3,
        'night': 1,
    },

    # Solunar
    'solunar': {
        'major': 2,
        'minor': 1,
    },
}

REDFISH = {
    'tier': 1,
    'name': 'Redfish',
    'peak_months': list(range(1, 13)),  # Year-round
    'spawn_months': [8, 9, 10, 11],

    'water_temp': {
        'ideal_min': 65,
        'ideal_max': 80,
        'workable_min': 55,
        'workable_max': 88,
        'bonus_in_ideal': 4,
        'penalty_out_of_workable': -2,  # More tolerant than trout
    },

    'tide_stage': {
        'incoming': 5,   # VERY tide-driven
        'outgoing': 4,   # Also good
        'high': 1,       # Slight positive (can push shallow)
        'low': -1,       # Slight negative
        'slack': -5,     # Strong negative
    },

    'current_speed': {
        'ideal_min': 0.4,
        'ideal_max': 2.0,  # Tolerates stronger current
        'bonus_moving': 4,
        'penalty_slack': -4,
    },

    'water_clarity': {
        'clear': 3,
        'slightly_stained': 3,  # Actually GOOD for redfish
        'stained': 1,           # Still okay
        'muddy': -1,            # Very small penalty
        'chalky': -2,
    },

    'wind': {
        'favorable_directions': ['SE', 'S', 'SW'],
        'unfavorable_directions': [],  # Less wind-sensitive
        'light_ideal_max': 15,
        'bonus_favorable': 2,
        'penalty_unfavorable_strong': -1,  # Minimal penalty
    },

    'pressure': {
        'falling': 2,
        'stable': 1,
        'rising_slow': 0,
        'rising_fast': -1,  # Less affected than trout
    },

    'salinity': {
        'preferred_min': 10,
        'preferred_max': 35,
        'tolerant': True,
        'penalty_rapid_change': -1,
    },

    'structure': {
        'pilings': 5,      # LOVES structure
        'rubble': 5,       # LOVES rubble
        'cuts': 4,
        'drains': 4,
        'grass_edges': 3,
        'open_water': -2,
    },

    'light': {
        'green_light_night_bonus': 2,
        'requires_decent_clarity': False,
    },

    'time_of_day': {
        'dawn': 3,
        'morning': 3,
        'midday': 1,
        'afternoon': 2,
        'evening': 3,
        'night': 2,
    },

    'solunar': {
        'major': 2,
        'minor': 1,
    },

    # Special: current + structure intersection
    'current_structure_bonus': 3,  # Extra bonus when both present
}

FLOUNDER = {
    'tier': 1,
    'name': 'Flounder',
    'peak_months': [4, 5, 6, 7, 8, 9, 10],  # April-October
    'spawn_months': [10, 11, 12],

    'water_temp': {
        'ideal_min': 65,
        'ideal_max': 75,
        'workable_min': 58,
        'workable_max': 82,
        'bonus_in_ideal': 5,
        'penalty_out_of_workable': -5,  # Very temperature sensitive
        'penalty_cold_snap': -7,  # Hard cold snap is devastating
    },

    'tide_stage': {
        'incoming': 3,
        'outgoing': 4,   # Slight preference for outgoing
        'high': -1,
        'low': 0,
        'slack': -6,     # VERY negative for slack
    },

    'current_speed': {
        'ideal_min': 0.3,
        'ideal_max': 1.2,
        'bonus_moving': 4,
        'penalty_slack': -5,
    },

    'water_clarity': {
        'clear': 6,              # NEEDS clear water
        'slightly_stained': 2,
        'stained': -2,
        'muddy': -7,             # Major negative
        'chalky': -6,
    },

    'wind': {
        'favorable_directions': ['SE', 'S', 'SW'],
        'unfavorable_directions': ['N', 'NW'],
        'light_ideal_max': 10,
        'bonus_favorable': 2,
        'penalty_unfavorable_strong': -5,
    },

    'pressure': {
        'falling': 3,
        'stable': 2,
        'rising_slow': 0,
        'rising_fast': -4,  # Very negative post-front
    },

    'salinity': {
        'preferred_min': 18,
        'preferred_max': 32,
        'tolerant': False,  # Less tolerant
        'penalty_rapid_change': -3,
    },

    'structure': {
        'rubble': 6,           # LOVES rubble (Zone 1)
        'sand_mud_transitions': 5,
        'piling_bases': 5,
        'drop_offs': 4,
        'open_water': -3,
    },

    'light': {
        'green_light_night_bonus': 3,
        'requires_decent_clarity': True,
    },

    'time_of_day': {
        'dawn': 4,
        'morning': 3,
        'midday': 0,
        'afternoon': 1,
        'evening': 4,
        'night': 2,
    },

    'solunar': {
        'major': 2,
        'minor': 1,
    },
}

SHEEPSHEAD = {
    'tier': 1,
    'name': 'Sheepshead',
    'peak_months': [12, 1, 2, 3, 4],  # Winter through early spring
    'spawn_months': [3, 4, 5],

    'water_temp': {
        'ideal_min': 55,
        'ideal_max': 70,
        'workable_min': 48,
        'workable_max': 78,
        'bonus_in_ideal': 4,
        'penalty_out_of_workable': -3,
    },

    'tide_stage': {
        'incoming': 3,
        'outgoing': 3,
        'high': 1,
        'low': 1,
        'slack': -3,  # Negative but not as severe as others
    },

    'current_speed': {
        'ideal_min': 0.2,
        'ideal_max': 1.0,  # Moderate current
        'bonus_moving': 3,
        'penalty_slack': -2,
    },

    'water_clarity': {
        'clear': 5,
        'slightly_stained': 2,
        'stained': -1,
        'muddy': -4,
        'chalky': -4,
    },

    'wind': {
        'favorable_directions': [],  # Less wind-dependent
        'unfavorable_directions': [],
        'light_ideal_max': 20,  # Tolerates wind well
        'bonus_favorable': 1,
        'penalty_unfavorable_strong': -1,
    },

    'pressure': {
        'falling': 2,
        'stable': 1,
        'rising_slow': 1,
        'rising_fast': -1,  # Less affected
    },

    'salinity': {
        'preferred_min': 15,
        'preferred_max': 32,
        'tolerant': True,
        'penalty_rapid_change': -1,
    },

    'structure': {
        'pilings': 6,          # HEAVILY structure-dependent
        'barnacles': 6,
        'vertical_structure': 6,
        'rubble': 4,
        'open_water': -6,      # Avoid open water completely
    },

    'light': {
        'green_light_night_bonus': 1,  # Minimal
        'requires_decent_clarity': False,
    },

    'time_of_day': {
        'dawn': 3,
        'morning': 3,
        'midday': 2,
        'afternoon': 2,
        'evening': 2,
        'night': 0,
    },

    'solunar': {
        'major': 1,
        'minor': 1,
    },

    # Special: current around structure
    'current_structure_bonus': 4,
}

BLACK_DRUM = {
    'tier': 1,
    'name': 'Black Drum',
    'peak_months': list(range(1, 13)),  # Year-round
    'spawn_months': [3, 4, 5],

    'water_temp': {
        'ideal_min': 60,
        'ideal_max': 75,
        'workable_min': 50,
        'workable_max': 85,
        'bonus_in_ideal': 3,
        'penalty_out_of_workable': -2,  # Tolerant
    },

    'tide_stage': {
        'incoming': 2,
        'outgoing': 2,
        'high': 1,
        'low': 1,
        'slack': -2,  # Mild negative
    },

    'current_speed': {
        'ideal_min': 0.2,
        'ideal_max': 1.2,
        'bonus_moving': 2,
        'penalty_slack': -2,
    },

    'water_clarity': {
        'clear': 2,
        'slightly_stained': 2,
        'stained': 1,
        'muddy': 0,      # NO penalty - tolerates muddy
        'chalky': -1,
    },

    'wind': {
        'favorable_directions': [],
        'unfavorable_directions': [],
        'light_ideal_max': 18,
        'bonus_favorable': 1,
        'penalty_unfavorable_strong': 0,
    },

    'pressure': {
        'falling': 1,
        'stable': 1,
        'rising_slow': 0,
        'rising_fast': 0,  # Barely affected
    },

    'salinity': {
        'preferred_min': 12,
        'preferred_max': 35,
        'tolerant': True,
        'penalty_rapid_change': 0,
    },

    'structure': {
        'pilings': 4,
        'mud_bottom': 4,
        'rubble': 4,
        'deep_holes': 3,
        'open_water': -1,
    },

    'light': {
        'green_light_night_bonus': 1,
        'requires_decent_clarity': False,
    },

    'time_of_day': {
        'dawn': 2,
        'morning': 2,
        'midday': 2,
        'afternoon': 2,
        'evening': 2,
        'night': 1,
    },

    'solunar': {
        'major': 1,
        'minor': 1,
    },

    # Prefers deeper zones
    'depth_preference': 'deep',  # Zone 5 advantage
}

# TIER 2 SPECIES (SIMPLIFIED PROFILES)

CROAKER = {
    'tier': 2,
    'name': 'Croaker',
    'tide_stage': {
        'incoming': 3,   # Feed strongly when tide starts
        'outgoing': 3,
        'slack': -2,
    },
    'structure': {
        'mud_bottom': 3,
        'current_edges': 3,
    },
}

WHITE_TROUT = {
    'tier': 2,
    'name': 'White Trout',
    'time_of_day': {
        'evening': 4,
        'night': 5,      # Night-focused
        'dawn': 2,
    },
    'light': {
        'green_light_night_bonus': 6,  # STRONGLY attracted to Zone 4 light
        'requires_decent_clarity': True,
    },
    'water_clarity': {
        'clear': 4,
        'slightly_stained': 2,
        'muddy': -4,
    },
}

# BAIT SPECIES

MENHADEN = {
    'tier': 2,
    'name': 'Menhaden',
    'type': 'bait',
    'wind': {
        'surface_driven': True,
        'favorable_directions': ['SE', 'S', 'SW'],
    },
    'structure': {
        'push_to_edges': True,
        'with_current': True,
    },
    'predator_indicator': True,  # Big schools = predator lift
}

MULLET = {
    'tier': 2,
    'name': 'Mullet',
    'type': 'bait',
    'tide_stage': {
        'incoming': 4,  # Push shallow
    },
    'water_temp': {
        'warm_positive': True,
    },
    'seasonal_runs': True,
}

LIVE_SHRIMP = {
    'tier': 2,
    'name': 'Live Shrimp',
    'type': 'bait',
    'light': {
        'green_light_night_bonus': 8,  # HEAVILY stack under Zone 4 light
    },
    'tide_stage': {
        'incoming': 5,
    },
    'water_temp': {
        'ideal_min': 65,
        'cold_kills_activity': True,
    },
}

FIDDLER_CRAB = {
    'tier': 2,
    'name': 'Fiddler Crab',
    'type': 'bait',
    'peak_months': [12, 1, 2, 3],  # Winter presence
    'correlates_with': 'sheepshead',  # Their availability = sheepshead bite
}

# PREDATOR SPECIES

JACK_CREVALLE = {
    'tier': 2,
    'name': 'Jack Crevalle',
    'type': 'predator',
    'behavior': 'aggressive',
    'bait_school_attack': True,
    'causes_prey_evacuation': True,
    'penalty_to_prey': -6,  # Applied to trout, white trout, bait species
}

# Master dictionary
SPECIES_PROFILES = {
    'speckled_trout': SPECKLED_TROUT,
    'redfish': REDFISH,
    'flounder': FLOUNDER,
    'sheepshead': SHEEPSHEAD,
    'black_drum': BLACK_DRUM,
    'croaker': CROAKER,
    'white_trout': WHITE_TROUT,
    'menhaden': MENHADEN,
    'mullet': MULLET,
    'live_shrimp': LIVE_SHRIMP,
    'fiddler_crab': FIDDLER_CRAB,
    'jack_crevalle': JACK_CREVALLE,
}


def get_species_profile(species_key: str) -> dict:
    """
    Get behavior profile for a species.

    Args:
        species_key: Species identifier

    Returns:
        Profile dictionary or empty dict if not found
    """
    return SPECIES_PROFILES.get(species_key, {})


def is_prey_species(species_key: str) -> bool:
    """
    Check if species is prey (affected by predator penalties).

    Prey species: trout, white trout, bait species
    """
    prey_list = ['speckled_trout', 'white_trout', 'menhaden', 'mullet', 'live_shrimp']
    return species_key in prey_list
