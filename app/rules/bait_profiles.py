"""
Bait species profiles and activity scoring.
Centralizes all bait-related data for consistency across features.
"""

# Canonical list of bait species that can be CAUGHT (not purchased/prepared)
BAIT_SPECIES = [
    "live_shrimp",
    "live_fish",
    "mud_minnows",
    "pinfish",
    "menhaden",
    "fiddler_crabs",
]

# Display names for catchable bait species
BAIT_DISPLAY_NAMES = {
    "live_shrimp": "Live Shrimp",
    "live_fish": "Live Bait Fish",
    "mud_minnows": "Mud Minnows",
    "pinfish": "Pinfish",
    "menhaden": "Menhaden (Pogies)",
    "fiddler_crabs": "Fiddler Crabs",
}

# Comprehensive bait profiles with scoring weights and details
BAIT_PROFILES = {
    "live_shrimp": {
        "display_name": "Live Shrimp",
        "description": "The #1 most versatile bait in Mobile Bay. Live shrimp catch nearly every inshore species and are consistently productive year-round.",

        # Scoring weights (0-1 scale for each factor)
        "weights": {
            "tide_movement": 0.30,      # Loves moving water
            "current_strength": 0.25,    # Moderate to strong current
            "clarity": 0.15,             # Works in any clarity
            "time_of_day": 0.15,         # Slightly better at night
            "zone_preference": 0.15,     # Found in multiple zones
        },

        # Activity preferences
        "preferences": {
            "tide_states": ["rising", "falling"],  # Best during moving water
            "current_strength": ["moderate", "strong"],
            "clarity": ["clear", "lightly_stained", "muddy"],  # Works in all
            "time_of_day": ["night", "dawn", "dusk", "day"],  # Better at night/dawn
            "zones": [2, 3, 4],  # Mid-depth areas
        },

        # Where to find
        "zones": [2, 3, 4],
        "zone_notes": "Look around grass beds, dock pilings, and mid-depth areas. Shrimp move with tide into shallows at night.",

        # When active
        "tide_preference": "Moving tide (rising or falling). Shrimp are most active during tidal flow.",
        "time_preference": "Night and dawn are prime time. Use lights to attract shrimp at night.",
        "clarity_notes": "Works in any water clarity. In muddy water, use scent to help fish find them.",

        # How to catch
        "methods": ["cast net", "dip net", "trap"],
        "how_to_catch": [
            "Cast net over grass beds and dock lights at night",
            "Use a dip net under dock lights after dark",
            "Shrimp traps baited with fish heads work well",
            "Look for shrimp \"popping\" on the surface at dusk"
        ],

        # Best for (target fish species)
        "best_for": ["speckled_trout", "redfish", "flounder", "sheepshead", "white_trout", "croaker"],

        # Tips
        "tips": [
            "Keep alive in aerated bucket or livewell",
            "Hook through tail for bottom fishing, head for cork fishing",
            "Use 1/0 to 2/0 circle hooks for best hookups",
            "Change out dead shrimp frequently - live action is key"
        ]
    },

    "live_fish": {
        "display_name": "Live Bait Fish",
        "description": "Live baitfish (finger mullet, mud minnows, pinfish) are deadly for larger predators like big trout, redfish, and flounder.",

        "weights": {
            "tide_movement": 0.25,
            "current_strength": 0.30,
            "clarity": 0.20,
            "time_of_day": 0.15,
            "zone_preference": 0.10,
        },

        "preferences": {
            "tide_states": ["rising", "falling"],
            "current_strength": ["moderate", "strong"],
            "clarity": ["clear", "lightly_stained"],
            "time_of_day": ["dawn", "dusk", "day"],
            "zones": [3, 4, 5],
        },

        "zones": [3, 4, 5],
        "zone_notes": "Live baitfish are found in deeper water around structure. Schools move with current and baitfish activity.",

        "tide_preference": "Moving tide when predator fish are feeding. Strong current activates gamefish.",
        "time_preference": "Dawn and dusk feeding periods are best. Works well during midday too.",
        "clarity_notes": "Best in clear to lightly stained water where predators can see them swimming.",

        "methods": ["cast net", "sabiki rig", "trap"],
        "how_to_catch": [
            "Cast net around dock and shallow areas for mullet",
            "Use sabiki rigs or small hooks for mud minnows and pinfish",
            "Minnow traps baited with bread or crackers",
            "Look for baitfish schools dimpling the surface"
        ],

        "best_for": ["speckled_trout", "redfish", "flounder", "jack_crevalle", "shark"],

        "tips": [
            "Keep in large aerated livewell with frequent water changes",
            "Hook through lips or back for free-lining",
            "Use larger hooks (2/0-4/0) for bigger baits",
            "Match bait size to target species - bigger bait, bigger fish"
        ]
    },

    "mud_minnows": {
        "display_name": "Mud Minnows",
        "description": "Hardy, active baitfish that excel for flounder and trout. They stay alive longer than most live baits and have great action.",

        "weights": {
            "tide_movement": 0.30,
            "current_strength": 0.25,
            "clarity": 0.15,
            "time_of_day": 0.20,
            "zone_preference": 0.10,
        },

        "preferences": {
            "tide_states": ["falling", "slack"],
            "current_strength": ["weak", "moderate"],
            "clarity": ["lightly_stained", "muddy"],
            "time_of_day": ["day", "dusk"],
            "zones": [3, 4, 5],
        },

        "zones": [3, 4, 5],
        "zone_notes": "Mud minnows are found in muddy, grassy bottoms. They burrow in mud during low tide.",

        "tide_preference": "Falling tide or low slack. They're active when tide is dropping.",
        "time_preference": "Daytime and evening. Less effective at night.",
        "clarity_notes": "Prefer stained to muddy water. They're bottom-dwellers.",

        "methods": ["minnow trap", "dip net", "small hook"],
        "how_to_catch": [
            "Use minnow traps in muddy shallows",
            "Dip net around grass edges at low tide",
            "Small hook with tiny piece of shrimp",
            "Check traps after 1-2 hours"
        ],

        "best_for": ["flounder", "speckled_trout", "black_drum"],

        "tips": [
            "Extremely hardy - can survive hours in a bucket",
            "Hook through lips for best action",
            "Slow presentations work best",
            "Great for targeting flounder on bottom"
        ]
    },

    "pinfish": {
        "display_name": "Pinfish",
        "description": "Feisty, aggressive baitfish perfect for larger predators. Their spiny fins and active swimming make them irresistible.",

        "weights": {
            "tide_movement": 0.20,
            "current_strength": 0.25,
            "clarity": 0.25,
            "time_of_day": 0.20,
            "zone_preference": 0.10,
        },

        "preferences": {
            "tide_states": ["rising", "falling"],
            "current_strength": ["moderate", "strong"],
            "clarity": ["clear", "lightly_stained"],
            "time_of_day": ["day", "dusk"],
            "zones": [3, 4],
        },

        "zones": [3, 4],
        "zone_notes": "Pinfish hang around dock pilings, rocks, and structure. They're aggressive and easy to catch.",

        "tide_preference": "Any tide works. Pinfish are consistent biters.",
        "time_preference": "Daytime is best. They slow down at night.",
        "clarity_notes": "Clear to lightly stained water. They're visual feeders.",

        "methods": ["sabiki rig", "small hook"],
        "how_to_catch": [
            "Sabiki rigs around dock pilings are deadly",
            "Small hook (#6-#10) with tiny shrimp piece",
            "Drop near structure and they'll bite immediately",
            "Can catch dozens in minutes"
        ],

        "best_for": ["speckled_trout", "redfish", "flounder"],

        "tips": [
            "Very hardy - survive well in livewells",
            "Hook through back behind dorsal fin",
            "Watch for spines - they'll stick you",
            "Use heavier tackle - they attract big fish"
        ]
    },

    "menhaden": {
        "display_name": "Menhaden (Pogies)",
        "description": "Oily, strong-scented baitfish that drive predators crazy. Best for big trout, redfish, and jacks when schools are present.",

        "weights": {
            "tide_movement": 0.30,
            "current_strength": 0.30,
            "clarity": 0.15,
            "time_of_day": 0.15,
            "zone_preference": 0.10,
        },

        "preferences": {
            "tide_states": ["rising", "falling"],
            "current_strength": ["strong"],
            "clarity": ["clear", "lightly_stained"],
            "time_of_day": ["dawn", "day"],
            "zones": [4, 5],
        },

        "zones": [4, 5],
        "zone_notes": "Pogies school in open water. Look for surface activity and diving birds indicating schools.",

        "tide_preference": "Strong moving tide when schools are feeding.",
        "time_preference": "Dawn and morning hours when schools are most active.",
        "clarity_notes": "Clear to lightly stained water. They're sight feeders.",

        "methods": ["cast net"],
        "how_to_catch": [
            "Look for nervous water and bait balls",
            "Cast net is the only way - schools move fast",
            "Watch for birds diving on bait schools",
            "Early morning is best for catching pogies"
        ],

        "best_for": ["speckled_trout", "redfish", "jack_crevalle", "mackerel"],

        "tips": [
            "Very fragile - die quickly, keep well-aerated",
            "Their oil creates scent trail that attracts fish",
            "Can be cut up for cut bait when they die",
            "Bigger pogies (4-6\") catch bigger fish"
        ]
    },

    "fiddler_crabs": {
        "display_name": "Fiddler Crabs",
        "description": "The absolute best bait for sheepshead. Also works for black drum and redfish around structure.",

        "weights": {
            "tide_movement": 0.15,
            "current_strength": 0.10,
            "clarity": 0.20,
            "time_of_day": 0.25,
            "zone_preference": 0.30,
        },

        "preferences": {
            "tide_states": ["slack", "rising"],
            "current_strength": ["weak", "moderate"],
            "clarity": ["clear", "lightly_stained"],
            "time_of_day": ["day"],
            "zones": [],  # Not found at dock - only on muddy shorelines away from dock
        },

        "zones": [],  # Not at dock zones
        "zone_notes": "NOT found at the dock. Look for them on muddy shorelines and marsh banks away from the dock. Most active during low tide.",

        "tide_preference": "Low tide for catching them. Fish them on rising tide near structure.",
        "time_preference": "Daytime fishing. Crabs are most active during the day.",
        "clarity_notes": "Clear to lightly stained water near structure.",

        "methods": ["hand catch", "scoop"],
        "how_to_catch": [
            "Walk muddy banks at low tide and grab them by hand",
            "Use a small scoop or bucket to corner them",
            "They live in burrows - watch for movement",
            "Best caught 1-2 hours before low tide"
        ],

        "best_for": ["sheepshead", "black_drum", "redfish"],

        "tips": [
            "Keep alive in bucket with damp grass or newspaper",
            "Hook through back shell from side to side",
            "Remove claws for smaller fish",
            "Fish tight to structure - that's where sheepshead are"
        ]
    },
}


def get_bait_display_name(bait_key: str) -> str:
    """Get the display name for a bait species key."""
    return BAIT_DISPLAY_NAMES.get(bait_key, bait_key.replace('_', ' ').title())


def get_bait_profile(bait_key: str) -> dict:
    """Get the full profile for a bait species."""
    return BAIT_PROFILES.get(bait_key, {})
