"""Alabama saltwater fishing regulations (July 2025).

Size and creel limits for recreational fishing in Alabama coastal waters.
Data from Alabama Marine Resources Division official creel sheet.
"""

# Species regulations configuration
SPECIES_REGULATIONS = {
    "speckled_trout": {
        "name": "Spotted Seatrout",
        "size": {
            "min_inches": 15,
            "max_inches": 22,
            "measure": "TL"
        },
        "creel": {
            "per_person": 6,
            "per_vessel": None,
            "notes": "One oversized fish allowed in addition to slot fish."
        },
        "special_rules": []
    },
    "redfish": {
        "name": "Red Drum (Redfish)",
        "size": {
            "min_inches": 16,
            "max_inches": 26,
            "measure": "TL"
        },
        "creel": {
            "per_person": 3,
            "per_vessel": None,
            "notes": "Slot only—fish must be within 16–26 inch range."
        },
        "special_rules": []
    },
    "sheepshead": {
        "name": "Sheepshead",
        "size": {
            "min_inches": 12,
            "max_inches": None,
            "measure": "FL"
        },
        "creel": {
            "per_person": 8,
            "per_vessel": None,
            "notes": None
        },
        "special_rules": []
    },
    "tripletail": {
        "name": "Tripletail (Blackfish)",
        "size": {
            "min_inches": 18,
            "max_inches": None,
            "measure": "TL"
        },
        "creel": {
            "per_person": 3,
            "per_vessel": None,
            "notes": None
        },
        "special_rules": []
    },
    "flounder": {
        "name": "Flounder",
        "size": {
            "min_inches": 14,
            "max_inches": None,
            "measure": "TL"
        },
        "creel": {
            "per_person": 5,
            "per_vessel": None,
            "notes": None
        },
        "special_rules": [
            "Taking or possession of flounder is prohibited from Nov. 1–Nov. 30."
        ]
    },
    "mackerel": {
        "name": "King Mackerel",
        "size": {
            "min_inches": 24,
            "max_inches": None,
            "measure": "FL"
        },
        "creel": {
            "per_person": 3,
            "per_vessel": None,
            "notes": None
        },
        "special_rules": []
    },
    "mullet": {
        "name": "Mullet",
        "size": {
            "min_inches": None,
            "max_inches": None,
            "measure": None
        },
        "creel": {
            "per_person": None,
            "per_vessel": None,
            "notes": "No size or creel limit (except seasonal shoreline rule)."
        },
        "special_rules": [
            "Oct 24–Dec 31: 25 mullet per person from the shoreline OR 25 per boat.",
            "During that period, no mullet may be taken by cast net or snagging in Theodore Industrial Canal, Dog River, Fowl River, and their tributaries."
        ]
    },
    "stingray": {
        "name": "Skates and Rays",
        "size": {
            "min_inches": None,
            "max_inches": None,
            "measure": None
        },
        "creel": {
            "per_person": 3,
            "per_vessel": None,
            "notes": "No size limit."
        },
        "special_rules": [
            "Full retention allowed when using bow, spear, or gig.",
            "It is unlawful to remove the tail from any released skate or ray."
        ]
    },
    # Species without specific regulations in the creel sheet
    "croaker": {
        "name": "Atlantic Croaker",
        "size": {
            "min_inches": None,
            "max_inches": None,
            "measure": None
        },
        "creel": {
            "per_person": None,
            "per_vessel": None,
            "notes": "No size or creel limit."
        },
        "special_rules": []
    },
    "shark": {
        "name": "Sharks",
        "size": {
            "min_inches": None,
            "max_inches": None,
            "measure": None
        },
        "creel": {
            "per_person": None,
            "per_vessel": None,
            "notes": "Varies by species. Check current regulations."
        },
        "special_rules": []
    },
    "black_drum": {
        "name": "Black Drum",
        "size": {
            "min_inches": None,
            "max_inches": None,
            "measure": None
        },
        "creel": {
            "per_person": None,
            "per_vessel": None,
            "notes": "No size or creel limit."
        },
        "special_rules": []
    },
    "jack_crevalle": {
        "name": "Jack Crevalle",
        "size": {
            "min_inches": None,
            "max_inches": None,
            "measure": None
        },
        "creel": {
            "per_person": None,
            "per_vessel": None,
            "notes": None
        },
        "special_rules": []
    },
    "white_trout": {
        "name": "White Trout",
        "size": {
            "min_inches": None,
            "max_inches": None,
            "measure": None
        },
        "creel": {
            "per_person": None,
            "per_vessel": None,
            "notes": "No size or creel limit."
        },
        "special_rules": []
    },
    "blue_crab": {
        "name": "Blue Crab",
        "size": {
            "min_inches": 5,  # 5 inches point-to-point
            "max_inches": None,
            "measure": "Point-to-point"
        },
        "creel": {
            "per_person": None,
            "per_vessel": None,
            "notes": "Recreational crabbing allowed with proper gear."
        },
        "special_rules": [
            "Minimum size: 5 inches point to point across carapace.",
            "No egg-bearing females may be taken."
        ]
    }
}


def get_size_limit_display(species_key: str) -> str:
    """
    Get formatted size limit string for display.

    Args:
        species_key: Species key (e.g., 'speckled_trout')

    Returns:
        Formatted string like "15\"-22\"" or "18\"-N/A" or "N/A"
    """
    if species_key not in SPECIES_REGULATIONS:
        return "N/A"

    reg = SPECIES_REGULATIONS[species_key]
    size = reg["size"]

    min_size = size.get("min_inches")
    max_size = size.get("max_inches")

    if min_size is None and max_size is None:
        return "N/A"

    min_str = f'{min_size}"' if min_size is not None else "N/A"
    max_str = f'{max_size}"' if max_size is not None else "N/A"

    return f"{min_str}-{max_str}"


def get_creel_limit_display(species_key: str) -> str:
    """
    Get formatted creel limit string for display.

    Args:
        species_key: Species key (e.g., 'speckled_trout')

    Returns:
        Formatted string like "6 per person" or "N/A"
    """
    if species_key not in SPECIES_REGULATIONS:
        return "N/A"

    reg = SPECIES_REGULATIONS[species_key]
    creel = reg["creel"]

    per_person = creel.get("per_person")
    per_vessel = creel.get("per_vessel")

    if per_person is not None:
        return f"{per_person} per person"
    elif per_vessel is not None:
        return f"{per_vessel} per vessel"
    else:
        return "N/A"


def get_regulations(species_key: str) -> dict:
    """
    Get full regulations for a species.

    Args:
        species_key: Species key (e.g., 'speckled_trout')

    Returns:
        Dictionary with size_display, creel_display, and full regulation data
    """
    if species_key not in SPECIES_REGULATIONS:
        return {
            "size_display": "N/A",
            "creel_display": "N/A",
            "regulations": None
        }

    return {
        "size_display": get_size_limit_display(species_key),
        "creel_display": get_creel_limit_display(species_key),
        "regulations": SPECIES_REGULATIONS[species_key]
    }
