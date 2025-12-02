"""Advanced fishing forecast features.

This module provides:
- Water clarity prediction
- Confidence scoring
- Rig of the Moment recommendations
- Zone recommendations
- Pro tips
- Species behavior cheat sheets
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional
import random
from app.rules.behavior import DOCK_DEPTH_BEHAVIOR, format_depth_range


# Zone mapping - CANONICAL GEOMETRY (Final Spec)
# Walkway runs EAST-WEST dividing north/south
# Zones 1,3 = NORTH of walkway | Zones 2,4 = SOUTH of walkway | Zone 5 = EAST spanning full width
DOCK_ZONES = {
    1: {
        "name": "Zone 1",
        "description": "Northwest quadrant - above walkway",
        "depth_range": (2, 4),
        "position": "north",
        "structure": "old_pilings_north_edge",  # East-west piling line on north border
        "features": ["concrete_rubble"],  # Small rubble piles inside zone
        "lights": False
    },
    2: {
        "name": "Zone 2",
        "description": "Southwest quadrant - below walkway",
        "depth_range": (2, 4),
        "position": "south",
        "structure": "none",  # NO pilings
        "features": [],
        "lights": False
    },
    3: {
        "name": "Zone 3",
        "description": "Northeast quadrant - above walkway",
        "depth_range": (3, 6),
        "position": "north",
        "structure": "old_pilings_north_edge",  # East-west piling line on north border
        "features": [],
        "lights": False
    },
    4: {
        "name": "Zone 4",
        "description": "Southeast quadrant - below walkway",
        "depth_range": (3, 6),
        "position": "south",
        "structure": "green_light_only",  # Single underwater green light at SE dock edge
        "features": ["green_underwater_light"],
        "lights": True
    },
    5: {
        "name": "Zone 5",
        "description": "Eastern zone - full width beyond zones 3&4",
        "depth_range": (5, 7),
        "position": "east",
        "structure": "dual_pilings",  # North edge piling line + center piling line (strongest structure)
        "features": ["north_piling_line", "center_piling_line"],
        "lights": False
    },
}


def get_bite_tier_from_score(bite_score: float) -> str:
    """
    Convert numeric bite score to tier label.

    HOT = 80-100
    DECENT = 50-79
    SLOW = 20-49
    UNLIKELY = 0-19

    Args:
        bite_score: Numeric bite score (0-100)

    Returns:
        Tier string: "HOT", "DECENT", "SLOW", or "UNLIKELY"
    """
    if bite_score >= 80:
        return "HOT"
    elif bite_score >= 50:
        return "DECENT"
    elif bite_score >= 20:
        return "SLOW"
    else:
        return "UNLIKELY"


def get_behavior_tier_from_bite_tier(bite_tier: str) -> str:
    """
    Convert UI bite tier to behavior tier for DOCK_DEPTH_BEHAVIOR lookup.

    HOT/DECENT/SLOW/UNLIKELY -> good/moderate/slow

    Args:
        bite_tier: UI tier ("HOT", "DECENT", "SLOW", "UNLIKELY")

    Returns:
        Behavior tier: "good", "moderate", or "slow"
    """
    if bite_tier == "HOT":
        return "good"
    elif bite_tier == "DECENT":
        return "moderate"
    else:  # SLOW or UNLIKELY
        return "slow"


def predict_water_clarity(wind_speed_mph: float, tide_rate: float, recent_rain: bool = False) -> str:
    """
    Predict water clarity based on environmental conditions.

    Args:
        wind_speed_mph: Wind speed in MPH
        tide_rate: Tide change rate (ft/hr)
        recent_rain: Whether there's been recent rain

    Returns:
        "Clear", "Lightly Stained", or "Muddy"
    """
    # Start with base clarity
    clarity_score = 10  # 0-10 scale, higher = clearer

    # Wind degrades clarity
    if wind_speed_mph > 15:
        clarity_score -= 4
    elif wind_speed_mph > 10:
        clarity_score -= 2
    elif wind_speed_mph > 5:
        clarity_score -= 1

    # Strong tidal movement stirs up bottom
    if abs(tide_rate) > 1.5:
        clarity_score -= 3
    elif abs(tide_rate) > 0.8:
        clarity_score -= 1

    # Recent rain adds runoff
    if recent_rain:
        clarity_score -= 3

    # Convert score to category
    if clarity_score >= 7:
        return "Clear"
    elif clarity_score >= 4:
        return "Lightly Stained"
    else:
        return "Muddy"


def get_clarity_tip(clarity: str) -> str:
    """Get actionable tip based on water clarity."""
    tips = {
        "Clear": "Downsize leader and lures.",
        "Lightly Stained": "Balanced visibility - natural colors work well.",
        "Muddy": "Use scent or noise-based baits."
    }
    return tips.get(clarity, "Normal conditions.")


def calculate_confidence_score(
    pressure_stability: float,
    wind_stability: float,
    tide_predictability: float
) -> str:
    """
    Calculate forecast confidence based on weather/tide stability.

    Args:
        pressure_stability: 0-1, how stable barometric pressure is
        wind_stability: 0-1, how consistent wind is
        tide_predictability: 0-1, how normal tidal patterns are

    Returns:
        "HIGH", "MEDIUM", or "LOW"
    """
    avg_stability = (pressure_stability + wind_stability + tide_predictability) / 3

    if avg_stability >= 0.7:
        return "HIGH"
    elif avg_stability >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def get_rig_of_moment(
    clarity: str,
    wind_mph: float,
    tide_speed: float,
    top_species: str,
    depth_range: Tuple[int, int],
    time_of_day: str
) -> str:
    """
    Generate dynamic rig recommendation.

    Args:
        clarity: Water clarity ("Clear", "Lightly Stained", "Muddy")
        wind_mph: Wind speed in MPH
        tide_speed: Current speed/tide rate
        top_species: Most active species slug
        depth_range: Depth range tuple (min, max) in feet
        time_of_day: "morning", "afternoon", "evening", "night"

    Returns:
        Rig recommendation string
    """
    # Determine chop level
    chop = "heavy" if wind_mph > 12 else "moderate" if wind_mph > 6 else "light"

    # Determine if tide is moving
    moving_tide = abs(tide_speed) > 0.5

    # Species-specific base rigs
    species_rigs = {
        "speckled_trout": {
            "shallow": "popping cork at 18-24 inches with live shrimp",
            "mid": "slow-sink plastic on 1/8oz jighead",
            "deep": "Carolina rig with live bait"
        },
        "redfish": {
            "shallow": "weedless gold spoon or soft plastic",
            "mid": "1/4oz jig with paddle tail",
            "deep": "cut bait on slip sinker rig"
        },
        "flounder": {
            "shallow": "slow drag with live finger mullet",
            "mid": "Carolina rig with mud minnow",
            "deep": "knocker rig with live shrimp"
        },
        "sheepshead": {
            "shallow": "sliding sinker rig with fiddler crab",
            "mid": "drop shot with shrimp near pilings",
            "deep": "tight-line rig at structure"
        },
        "black_drum": {
            "shallow": "slip float with blue crab",
            "mid": "bottom rig with peeled shrimp",
            "deep": "fishfinder rig with cut bait"
        }
    }

    # Determine depth category
    avg_depth = sum(depth_range) / 2
    if avg_depth <= 3:
        depth_cat = "shallow"
    elif avg_depth <= 5:
        depth_cat = "mid"
    else:
        depth_cat = "deep"

    # Get base rig
    if top_species in species_rigs:
        base_rig = species_rigs[top_species].get(depth_cat, "1/4oz jig with soft plastic")
    else:
        base_rig = "1/4oz jig with soft plastic"

    # Adjust for clarity
    if clarity == "Muddy" and "shrimp" not in base_rig.lower():
        clarity_mod = " (add scent)"
    elif clarity == "Clear":
        clarity_mod = " (downsize if needed)"
    else:
        clarity_mod = ""

    # Build recommendation
    if moving_tide:
        action = "Work"
    else:
        action = "Slow-drag"

    return f"{action} {base_rig}{clarity_mod}."


def get_best_zones_now(
    top_species_list: List[Dict],
    tide_state: str,
    clarity: str,
    time_of_day: str = "midday",
    wind_direction: Optional[str] = None,
    wind_speed: Optional[float] = None,
    air_temp_f: Optional[float] = None,
    water_temp_f: Optional[float] = None
) -> List[int]:
    """
    Recommend best zones based on current conditions and structure.

    NEW GEOMETRY:
    - Zone 1 (NW): Pilings + rubble, shallow, 2-4 ft
    - Zone 2 (SW): NO structure, shallow, 2-4 ft
    - Zone 3 (NE): Pilings north edge, mid-depth, 3-6 ft (most fished)
    - Zone 4 (SE): Green light only, mid-depth, 3-6 ft (most fished)
    - Zone 5 (E): Dual pilings (strongest structure), deep, 5-7 ft

    Args:
        top_species_list: List of top species with bite scores/tiers
        tide_state: Current tide state
        clarity: Water clarity
        time_of_day: Time of day (for light bonus)
        wind_direction: Optional wind direction for north wind penalty
        wind_speed: Optional wind speed for north wind penalty
        air_temp_f: Optional air temperature for cold temp check
        water_temp_f: Optional water temperature for cold temp check

    Returns:
        List of zone numbers (1-5) in priority order
    """
    from app.rules.cold_north_wind import has_strong_north_wind_penalty

    zone_scores = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    # Check for cold north wind penalty
    cold_north_penalty = has_strong_north_wind_penalty(wind_direction, wind_speed, air_temp_f, water_temp_f)

    # Base confidence: Zones 3 & 4 are most fished (higher baseline)
    zone_scores[3] += 2
    zone_scores[4] += 2

    # Score zones based on top species and structure match
    for species_data in top_species_list[:3]:  # Top 3 species
        species = species_data.get('key', '')
        tier = species_data.get('tier', 'SLOW')

        # Weight by tier
        weight = 3 if tier == "HOT" else 2 if tier == "DECENT" else 1

        # Species zone preferences based on structure needs
        if species in ['sheepshead', 'tripletail']:
            # Structure-dependent species: Zones 1, 3, 5 (all have pilings)
            zone_scores[1] += weight * 2  # Pilings + rubble
            zone_scores[3] += weight * 3  # Pilings + most fished
            zone_scores[5] += weight * 4  # Dual pilings (strongest)

        elif species in ['flounder', 'black_drum']:
            # Bottom feeders: Prefer rubble (Zone 1) or deeper zones
            zone_scores[1] += weight * 3  # Rubble bonus
            zone_scores[4] += weight * 2
            zone_scores[5] += weight * 2

        elif species == 'speckled_trout':
            # Edges and light structure: Zones 2, 3, 4
            zone_scores[2] += weight * 1  # Open water
            zone_scores[3] += weight * 3  # Structure + most fished
            zone_scores[4] += weight * 2

        elif species == 'redfish':
            # Shallow structure and shoreline: Zones 1, 2, 3
            zone_scores[1] += weight * 3  # Shallow + structure + rubble
            zone_scores[2] += weight * 2  # Shallow
            zone_scores[3] += weight * 2

        elif species in ['white_trout', 'croaker', 'jack_crevalle', 'mackerel', 'shark']:
            # Deeper water species: Zones 4, 5
            zone_scores[4] += weight * 2
            zone_scores[5] += weight * 3  # Deepest + strongest structure

        elif species == 'mullet':
            # Shallow open water: Zones 1, 2
            zone_scores[1] += weight * 2
            zone_scores[2] += weight * 3  # Open water, no structure

        elif species == 'blue_crab':
            # Structure and pilings: Zones 1, 3, 5
            zone_scores[1] += weight * 2
            zone_scores[3] += weight * 3
            zone_scores[5] += weight * 2

        else:
            # Default: mid-depth zones
            zone_scores[3] += weight * 2
            zone_scores[4] += weight * 2

    # Adjust for tide - incoming pushes shallow
    if "rising" in tide_state.lower():
        zone_scores[1] += 3  # Shallow north
        zone_scores[2] += 3  # Shallow south
        zone_scores[3] += 1
    elif "falling" in tide_state.lower():
        zone_scores[4] += 2
        zone_scores[5] += 2  # Fish move deeper

    # Adjust for clarity - clear water = deeper/more cautious
    if clarity == "Clear":
        zone_scores[4] += 1
        zone_scores[5] += 2  # Deep water advantage
    elif clarity == "Muddy":
        zone_scores[1] += 1  # Shallow structure
        zone_scores[3] += 1  # Structure advantage

    # Nighttime bonus for Zone 4 (green light)
    if time_of_day in ["evening", "night"]:
        zone_scores[4] += 4  # Light attracts bait and fish

    # Cold north wind penalty: down-rank shallow zones, up-rank deeper zones
    if cold_north_penalty:
        # Penalize shallow zones (1 & 2) - fish avoid the skinniest water
        zone_scores[1] -= 3  # Shallow zone penalty
        zone_scores[2] -= 4  # Shallowest open water zone penalty

        # Bonus to deeper zones and edges (4 & 5)
        zone_scores[4] += 2  # Mid-depth with good edges
        zone_scores[5] += 3  # Deepest zone with strongest structure

        # Zone 3 stays neutral (mid-depth with structure)

    # Sort zones by score
    sorted_zones = sorted(zone_scores.items(), key=lambda x: x[1], reverse=True)

    return [zone for zone, score in sorted_zones if score > 0][:3]  # Top 3 zones


def get_pro_tip(
    bite_tier: str,
    clarity: str,
    tide_state: str,
    wind_mph: float,
    time_of_day: str
) -> str:
    """
    Generate contextual pro tip.

    Args:
        bite_tier: Current bite tier
        clarity: Water clarity
        tide_state: Tide state
        wind_mph: Wind speed
        time_of_day: Time of day

    Returns:
        Pro tip string
    """
    tips = {
        "HOT_moving_tide": "Fish are aggressive - cover water fast and target edges.",
        "HOT_slack": "Even in slack, active fish will hit. Focus on structure.",
        "DECENT_clear": "Fish can see well - use natural colors and light leaders.",
        "DECENT_muddy": "Compensate for low visibility with vibration and scent.",
        "SLOW_wind": "Choppy water can trigger bites - be patient and vary retrieve.",
        "SLOW_calm": "Stealth is key - long casts and quiet presentations.",
        "morning": "First light often brings a feeding window - be ready early.",
        "evening": "Last light can turn on the bite - stay through dusk.",
    }

    # Build context key
    if bite_tier == "HOT":
        moving = "moving_tide" if "rising" in tide_state or "falling" in tide_state else "slack"
        key = f"HOT_{moving}"
    elif bite_tier == "DECENT":
        key = f"DECENT_{clarity.lower().replace(' ', '_')}"
    elif wind_mph > 10:
        key = "SLOW_wind"
    elif wind_mph < 4:
        key = "SLOW_calm"
    elif time_of_day in ["morning", "evening"]:
        key = time_of_day
    else:
        key = None

    return tips.get(key, "Stay persistent and adjust based on what you're seeing.")


def get_current_strength(tide_rate: float) -> str:
    """
    Classify current strength.

    Args:
        tide_rate: Tide change rate in ft/hr (can be negative)

    Returns:
        "Weak", "Moderate", or "Strong"
    """
    abs_rate = abs(tide_rate)

    if abs_rate < 0.5:
        return "Weak"
    elif abs_rate < 1.2:
        return "Moderate"
    else:
        return "Strong"


def get_moon_tide_window(moon_phase: str, tide_state: str, time_of_day: str) -> str:
    """
    Generate moon/tide window info.

    Args:
        moon_phase: Moon phase description
        tide_state: Current tide state
        time_of_day: Time of day

    Returns:
        Descriptive string about current window
    """
    # Simplify moon phase
    if "new" in moon_phase.lower() or "full" in moon_phase.lower():
        moon_effect = "strong tidal influence"
    else:
        moon_effect = "normal tidal range"

    return f"{moon_phase.title()} moon with {moon_effect}. {tide_state.title()} tide during {time_of_day}."


def get_species_behavior_cheatsheet(species_key: str) -> Dict:
    """
    Generate behavior cheat sheet for a species.

    Args:
        species_key: Species identifier (e.g., 'speckled_trout', 'redfish')

    Returns:
        Dictionary with behavior data:
        - best_depth: Dict with depth info for each tier
        - best_zones: List of recommended zone numbers
        - best_baits: List of best baits
        - best_tide: Description of ideal tide conditions
        - behavior_summary: Plain-language summary
    """
    # Species-specific behavior data
    species_behaviors = {
        "speckled_trout": {
            "best_baits": ["Live shrimp", "Soft plastics (paddle tail)", "Popping cork w/ shrimp", "Small topwater plugs"],
            "best_tide": "Moving tide (rising or falling), especially first 2 hours",
            "best_zones": [2, 3, 4],
            "behavior_summary": "Speckled trout are aggressive feeders during moving tides. Target shallow edges during good bites, deeper structure when slow. Use natural presentations in clear water."
        },
        "redfish": {
            "best_baits": ["Live shrimp", "Cut mullet", "Gold spoons", "Paddle tail jigs"],
            "best_tide": "Rising tide pushing into shallows, or high slack",
            "best_zones": [1, 2, 3],
            "behavior_summary": "Redfish prefer shallow water and structure. They're less tide-dependent than trout. Target shorelines, rocks, and flooded grass. Aggressive hitters in stained water."
        },
        "flounder": {
            "best_baits": ["Live finger mullet", "Mud minnows", "Gulp shrimp", "Slow jigs"],
            "best_tide": "Falling tide or low slack, ambush points",
            "best_zones": [3, 4, 5],
            "behavior_summary": "Flounder are ambush predators that lay on the bottom. Slow presentations work best. Target edges, drop-offs, and dock shadows. Most active when tide is falling."
        },
        "sheepshead": {
            "best_baits": ["Fiddler crabs", "Live shrimp", "Barnacles", "Sand fleas"],
            "best_tide": "Any tide - less tide-dependent, structure-focused",
            "best_zones": [3],
            "behavior_summary": "Sheepshead stay tight to structure (pilings, rocks). They pick at baits delicately - use light line and small hooks. Active year-round but peak in winter."
        },
        "black_drum": {
            "best_baits": ["Blue crab (peeled)", "Cut shrimp", "Clams", "Heavy bottom rigs"],
            "best_tide": "Slack tide, either high or low",
            "best_zones": [4, 5],
            "behavior_summary": "Black drum are bottom feeders that cruise slowly. Less affected by tides and conditions. Target deeper soft bottoms. Patient fishing pays off."
        },
        "white_trout": {
            "best_baits": ["Small jigs", "Shrimp (live or cut)", "Soft plastics", "Spoons"],
            "best_tide": "Moving tide, especially outgoing",
            "best_zones": [4, 5],
            "behavior_summary": "White trout school in deeper water off the dock. Fast strikers - work lures quickly. Most active during strong tidal movement and low light."
        },
        "croaker": {
            "best_baits": ["Shrimp (fresh or frozen)", "Bloodworms", "Small cut bait", "Bottom rigs"],
            "best_tide": "Any tide - steady feeders",
            "best_zones": [3, 4, 5],
            "behavior_summary": "Croaker are reliable bottom feeders. They're less sensitive to conditions. Target sandy/muddy bottoms. Great for beginners - easy to catch."
        },
        "tripletail": {
            "best_baits": ["Live shrimp", "Jigs", "Slow-sinking lures", "Crabs"],
            "best_tide": "Less tide-dependent - focus on structure",
            "best_zones": [3, 4],
            "behavior_summary": "Tripletail suspend near floating debris and structure. Look for them near the surface around pilings. Sight fishing works well. Peak in summer."
        },
        "blue_crab": {
            "best_baits": ["Chicken necks", "Fish heads", "Cast net", "Crab traps"],
            "best_tide": "Rising tide - crabs become more active",
            "best_zones": [2, 3, 4],
            "behavior_summary": "Blue crabs are most active during incoming tides. Use traps or hand lines with bait. Check regulations for size and egg-bearing females."
        },
        "mullet": {
            "best_baits": ["Cast net (no bait needed)", "Small bread balls", "Dough balls"],
            "best_tide": "Any tide - schools move with bait",
            "best_zones": [1, 2],
            "behavior_summary": "Mullet school in shallow water. They're filter feeders, not predators. Cast net is the primary method. Great for bait. Watch for visual schools."
        },
        "jack_crevalle": {
            "best_baits": ["Live bait fish", "Fast-moving lures", "Spoons", "Topwater plugs"],
            "best_tide": "Moving tide with baitfish activity",
            "best_zones": [3, 4, 5],
            "behavior_summary": "Jacks are aggressive predators that chase bait. They appear when baitfish stack up. Fast, powerful fighters. Work lures quickly across the water column."
        },
        "mackerel": {
            "best_baits": ["Small spoons", "Gotcha plugs", "Live bait", "Fast retrieves"],
            "best_tide": "Moving tide with clear water",
            "best_zones": [4, 5],
            "behavior_summary": "Mackerel are fast surface feeders. They run in schools and hit aggressively. Look for diving birds. Fast retrieves and shiny lures work best."
        },
        "shark": {
            "best_baits": ["Large cut bait", "Live fish", "Heavy tackle", "Wire leaders"],
            "best_tide": "Outgoing tide or dusk/night",
            "best_zones": [4, 5],
            "behavior_summary": "Sharks follow bait and scent trails. Use heavy gear and wire leaders. Most active at night or dusk. Know species regulations - many are protected."
        },
        "stingray": {
            "best_baits": ["Cut bait", "Shrimp", "Bottom rigs", "Heavy tackle"],
            "best_tide": "Any tide - consistent bottom dwellers",
            "best_zones": [4, 5],
            "behavior_summary": "Stingrays are bottom feeders that glide over mud/sand. Often bycatch. Strong fighters. Handle carefully - venomous barb in tail. Check regulations."
        }
    }

    # Get behavior data or return defaults
    if species_key not in species_behaviors:
        return {
            "best_baits": ["Live shrimp", "Cut bait", "Artificial lures"],
            "best_tide": "Moving tide",
            "best_zones": [3, 4],
            "behavior_summary": "General behavior data not available for this species.",
            "best_depth": {}
        }

    behavior_data = species_behaviors[species_key]

    # Add depth information from DOCK_DEPTH_BEHAVIOR
    depth_info = {}
    if species_key in DOCK_DEPTH_BEHAVIOR:
        for tier in ["good", "moderate", "slow"]:
            depth_data = DOCK_DEPTH_BEHAVIOR[species_key].get(tier)
            if depth_data:
                depth_info[tier] = {
                    "depth": depth_data["depth"],
                    "range": format_depth_range(depth_data["range_ft"]),
                    "note": depth_data["note"]
                }

    behavior_data["best_depth"] = depth_info

    return behavior_data
